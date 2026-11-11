--[[
	Inventory — per-player item storage with unique ids, equip slots and trade locks.

	local inventory = Inventory.new({ capacity = 200, equipSlots = 3 })
	inventory:load(userId, saved)                     -- saved = inventory:serialize(userId)
	local uid = inventory:add(userId, { id = "Shark", rarity = "Epic", mutation = "Gold" })
	inventory:equip(userId, uid)
	inventory:setEquipSlots(userId, 5)                -- e.g. +2 Pet Equip gamepass
	inventory:remove(userId, uid)

	Items are plain tables (must be DataStore-serializable). Server-only mutations.
]]

export type Item = { [string]: any }

local Inventory = {}
Inventory.__index = Inventory

function Inventory.new(config)
	config = config or {}
	local self = setmetatable({}, Inventory)
	self.capacity = config.capacity or 100
	self.defaultEquipSlots = config.equipSlots or 0
	self.bags = {}
	self.listeners = {}
	return self
end

function Inventory:onChanged(callback): () -> ()
	table.insert(self.listeners, callback)
	return function()
		local i = table.find(self.listeners, callback)
		if i then
			table.remove(self.listeners, i)
		end
	end
end

function Inventory:_emit(userId, action: string, uid: string, item: Item?)
	for _, listener in self.listeners do
		listener(userId, action, uid, item)
	end
end

function Inventory:_bag(userId)
	local bag = self.bags[userId]
	if not bag then
		error("Inventory: not loaded for " .. tostring(userId), 3)
	end
	return bag
end

function Inventory:load(userId, saved)
	local bag = {
		items = {},
		equipped = {},
		locked = {},
		nextId = 1,
		equipSlots = self.defaultEquipSlots,
		count = 0,
	}
	if type(saved) == "table" then
		for uid, item in saved.items or {} do
			if type(uid) == "string" and type(item) == "table" then
				bag.items[uid] = item
				bag.count += 1
			end
		end
		for _, uid in saved.equipped or {} do
			if bag.items[uid] and not table.find(bag.equipped, uid) then
				table.insert(bag.equipped, uid)
			end
		end
		bag.nextId = math.max(tonumber(saved.nextId) or 1, 1)
	end
	self.bags[userId] = bag
end

function Inventory:serialize(userId)
	local bag = self:_bag(userId)
	local items = {}
	for uid, item in bag.items do
		items[uid] = table.clone(item)
	end
	return { items = items, equipped = table.clone(bag.equipped), nextId = bag.nextId }
end

function Inventory:unload(userId)
	self.bags[userId] = nil
end

function Inventory:count(userId): number
	return self:_bag(userId).count
end

function Inventory:isFull(userId): boolean
	return self:_bag(userId).count >= self.capacity
end

function Inventory:get(userId, uid: string): Item?
	return self:_bag(userId).items[uid]
end

function Inventory:has(userId, uid: string): boolean
	return self:_bag(userId).items[uid] ~= nil
end

-- Returns { [uid] = item } (read-only copy).
function Inventory:list(userId): { [string]: Item }
	local out = {}
	for uid, item in self:_bag(userId).items do
		out[uid] = table.clone(item)
	end
	return out
end

-- Returns uid or nil, "full" / "invalid".
function Inventory:add(userId, item: Item): (string?, string?)
	if type(item) ~= "table" or type(item.id) ~= "string" then
		return nil, "invalid"
	end
	local bag = self:_bag(userId)
	if bag.count >= self.capacity then
		return nil, "full"
	end
	local uid = "i" .. tostring(bag.nextId)
	while bag.items[uid] do
		bag.nextId += 1
		uid = "i" .. tostring(bag.nextId)
	end
	bag.nextId += 1
	bag.items[uid] = table.clone(item)
	bag.count += 1
	self:_emit(userId, "add", uid, bag.items[uid])
	return uid, nil
end

-- Removes and returns the item. Locked items (in a trade) need force = true.
function Inventory:remove(userId, uid: string, force: boolean?): (Item?, string?)
	local bag = self:_bag(userId)
	local item = bag.items[uid]
	if not item then
		return nil, "missing"
	end
	if bag.locked[uid] and not force then
		return nil, "locked"
	end
	bag.items[uid] = nil
	bag.locked[uid] = nil
	bag.count -= 1
	local i = table.find(bag.equipped, uid)
	if i then
		table.remove(bag.equipped, i)
	end
	self:_emit(userId, "remove", uid, item)
	return item, nil
end

function Inventory:setLocked(userId, uid: string, locked: boolean): boolean
	local bag = self:_bag(userId)
	if not bag.items[uid] then
		return false
	end
	bag.locked[uid] = if locked then true else nil
	return true
end

function Inventory:isLocked(userId, uid: string): boolean
	return self:_bag(userId).locked[uid] == true
end

function Inventory:setEquipSlots(userId, slots: number)
	local bag = self:_bag(userId)
	bag.equipSlots = math.max(0, math.floor(slots))
	while #bag.equipped > bag.equipSlots do
		local uid = table.remove(bag.equipped)
		self:_emit(userId, "unequip", uid, bag.items[uid])
	end
end

function Inventory:equipSlots(userId): number
	return self:_bag(userId).equipSlots
end

function Inventory:equipped(userId): { string }
	return table.clone(self:_bag(userId).equipped)
end

function Inventory:equip(userId, uid: string): (boolean, string?)
	local bag = self:_bag(userId)
	if not bag.items[uid] then
		return false, "missing"
	end
	if table.find(bag.equipped, uid) then
		return true, nil
	end
	if #bag.equipped >= bag.equipSlots then
		return false, "slots_full"
	end
	table.insert(bag.equipped, uid)
	self:_emit(userId, "equip", uid, bag.items[uid])
	return true, nil
end

function Inventory:unequip(userId, uid: string): boolean
	local bag = self:_bag(userId)
	local i = table.find(bag.equipped, uid)
	if not i then
		return false
	end
	table.remove(bag.equipped, i)
	self:_emit(userId, "unequip", uid, bag.items[uid])
	return true
end

-- Moves an item between players atomically. Returns new uid or nil, reason.
function Inventory:transfer(fromId, toId, uid: string, force: boolean?): (string?, string?)
	if fromId == toId then
		return nil, "same_player"
	end
	if not self:has(fromId, uid) then
		return nil, "missing"
	end
	if self:isFull(toId) then
		return nil, "full"
	end
	local item, err = self:remove(fromId, uid, force)
	if not item then
		return nil, err
	end
	local newUid = self:add(toId, item)
	return newUid, nil
end

return Inventory
