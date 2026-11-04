--[[
	Tycoon — purchase graph (buttons that unlock droppers, walls, floors, upgraders).

	local tycoon = Tycoon.new({
		items = {
			{ id = "Floor1", cost = 0, currency = "Cash" },
			{ id = "Dropper1", cost = 100, currency = "Cash", requires = { "Floor1" }, income = 5 },
			{ id = "Dropper2", cost = 400, currency = "Cash", requires = { "Dropper1" }, income = 15 },
			{ id = "VIPRoom", cost = 0, currency = "Cash", requires = { "Floor1" }, gamepass = "VIP" },
		},
	})
	tycoon:load(userId, savedOwnedList)
	tycoon:available(userId)                        -- ids whose buttons should be visible
	tycoon:buy(userId, "Dropper1", currency, flags) -- flags = { VIP = true } for gamepass gates
	currency:setIncome(userId, "Tycoon", "Cash", tycoon:income(userId))
]]

local Tycoon = {}
Tycoon.__index = Tycoon

function Tycoon.new(config)
	assert(type(config) == "table" and type(config.items) == "table", "Tycoon.new: items required")
	local self = setmetatable({}, Tycoon)
	self.items = {}
	self.order = {}
	for _, item in config.items do
		assert(type(item.id) == "string", "Tycoon.new: item.id required")
		assert(self.items[item.id] == nil, "Tycoon.new: duplicate item " .. item.id)
		assert(type(item.cost) == "number" and item.cost >= 0, "Tycoon.new: bad cost for " .. item.id)
		self.items[item.id] = item
		table.insert(self.order, item.id)
	end
	for _, item in config.items do
		for _, req in item.requires or {} do
			assert(self.items[req], "Tycoon.new: " .. item.id .. " requires unknown item " .. req)
		end
	end
	self.owned = {} -- [userId] = { [itemId] = true }
	self.listeners = {}
	return self
end

function Tycoon:onPurchased(callback): () -> ()
	table.insert(self.listeners, callback)
	return function()
		local i = table.find(self.listeners, callback)
		if i then
			table.remove(self.listeners, i)
		end
	end
end

function Tycoon:load(userId, saved: { string }?)
	local owned = {}
	for _, id in ipairs(saved or {}) do
		if self.items[id] then
			owned[id] = true
		end
	end
	self.owned[userId] = owned
end

function Tycoon:serialize(userId): { string }
	local out = {}
	for _, id in self.order do
		if self.owned[userId][id] then
			table.insert(out, id)
		end
	end
	return out
end

function Tycoon:unload(userId)
	self.owned[userId] = nil
end

function Tycoon:owns(userId, itemId: string): boolean
	local owned = self.owned[userId]
	return owned ~= nil and owned[itemId] == true
end

function Tycoon:_requirementsMet(userId, item): boolean
	for _, req in item.requires or {} do
		if not self:owns(userId, req) then
			return false
		end
	end
	return true
end

-- Item ids that are unlocked for purchase but not owned (show these buttons).
function Tycoon:available(userId): { string }
	local out = {}
	for _, id in self.order do
		local item = self.items[id]
		if not self:owns(userId, id) and self:_requirementsMet(userId, item) then
			table.insert(out, id)
		end
	end
	return out
end

function Tycoon:canBuy(userId, itemId: string, currency, flags: { [string]: boolean }?): (boolean, string?)
	local item = self.items[itemId]
	if not item then
		return false, "unknown"
	end
	if self:owns(userId, itemId) then
		return false, "owned"
	end
	if not self:_requirementsMet(userId, item) then
		return false, "locked"
	end
	if item.gamepass and not (flags and flags[item.gamepass]) then
		return false, "gamepass"
	end
	if item.cost > 0 and not currency:canAfford(userId, item.currency, item.cost) then
		return false, "funds"
	end
	return true, nil
end

function Tycoon:buy(userId, itemId: string, currency, flags: { [string]: boolean }?): (boolean, string?)
	local ok, reason = self:canBuy(userId, itemId, currency, flags)
	if not ok then
		return false, reason
	end
	local item = self.items[itemId]
	if item.cost > 0 and not currency:spend(userId, item.currency, item.cost, "tycoon:" .. itemId) then
		return false, "funds"
	end
	self.owned[userId][itemId] = true
	for _, listener in self.listeners do
		listener(userId, itemId, item)
	end
	return true, nil
end

-- Sum of income from owned items (per second, before currency multipliers).
function Tycoon:income(userId): number
	local total = 0
	for id in self.owned[userId] or {} do
		total += self.items[id].income or 0
	end
	return total
end

function Tycoon:progress(userId): (number, number)
	local owned = 0
	for _ in self.owned[userId] or {} do
		owned += 1
	end
	return owned, #self.order
end

function Tycoon:reset(userId, keep: { string }?)
	local owned = {}
	for _, id in ipairs(keep or {}) do
		if self.items[id] then
			owned[id] = true
		end
	end
	self.owned[userId] = owned
end

return Tycoon
