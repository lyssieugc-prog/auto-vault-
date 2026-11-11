--[[
	Upgrades — leveled upgrades and tiered unlock ladders.

	local upgrades = Upgrades.new({
		upgrades = {
			WalkSpeed = { currency = "Cash", baseCost = 50, growth = 1.6, maxLevel = 10,
				effect = function(level) return 16 + level * 2 end },
			-- Tier ladder: x2 -> x1,250 like the house-style Upgrades screen.
			CashMulti = { currency = "Gems", costs = { 10, 50, 200, 1000, 5000, 25000 },
				values = { 1, 2, 5, 25, 100, 500, 1250 } },
		},
	})
	upgrades:load(userId, saved)
	upgrades:buy(userId, "WalkSpeed", currency)
	upgrades:value(userId, "CashMulti")  -- current effect
	upgrades:cost(userId, "WalkSpeed")   -- next cost or nil at max

	`values[level + 1]` is the value at a level (values[1] = level 0), `costs[level + 1]` is the
	price of the next level. Curves use baseCost * growth ^ level.
]]

local Upgrades = {}
Upgrades.__index = Upgrades

function Upgrades.new(config)
	assert(type(config) == "table" and type(config.upgrades) == "table", "Upgrades.new: upgrades required")
	local self = setmetatable({}, Upgrades)
	self.defs = {}
	for key, def in config.upgrades do
		assert(type(def.currency) == "string", "Upgrades.new: " .. key .. " needs currency")
		local maxLevel = def.maxLevel
		if def.costs then
			maxLevel = maxLevel or #def.costs
		end
		assert(type(maxLevel) == "number", "Upgrades.new: " .. key .. " needs maxLevel or costs")
		assert(def.costs or def.baseCost, "Upgrades.new: " .. key .. " needs costs or baseCost")
		if def.values then
			assert(#def.values >= maxLevel + 1, "Upgrades.new: " .. key .. " values must cover level 0..max")
		end
		self.defs[key] = {
			currency = def.currency,
			maxLevel = maxLevel,
			costs = def.costs,
			baseCost = def.baseCost,
			growth = def.growth or 1.5,
			effect = def.effect,
			values = def.values,
		}
	end
	self.levels = {}
	return self
end

function Upgrades:_def(key: string)
	local def = self.defs[key]
	if not def then
		error("Upgrades: unknown upgrade '" .. tostring(key) .. "'", 3)
	end
	return def
end

function Upgrades:load(userId, saved: { [string]: number }?)
	local levels = {}
	for key, def in self.defs do
		local lvl = saved and tonumber(saved[key]) or 0
		levels[key] = math.clamp(math.floor(lvl), 0, def.maxLevel)
	end
	self.levels[userId] = levels
end

function Upgrades:serialize(userId): { [string]: number }
	return table.clone(self.levels[userId])
end

function Upgrades:unload(userId)
	self.levels[userId] = nil
end

function Upgrades:level(userId, key: string): number
	self:_def(key)
	return self.levels[userId][key]
end

function Upgrades:isMaxed(userId, key: string): boolean
	return self:level(userId, key) >= self:_def(key).maxLevel
end

function Upgrades:cost(userId, key: string): number?
	local def = self:_def(key)
	local lvl = self:level(userId, key)
	if lvl >= def.maxLevel then
		return nil
	end
	if def.costs then
		return def.costs[lvl + 1]
	end
	return math.floor(def.baseCost * def.growth ^ lvl)
end

function Upgrades:valueAt(key: string, lvl: number): any
	local def = self:_def(key)
	if def.values then
		return def.values[lvl + 1]
	elseif def.effect then
		return def.effect(lvl)
	end
	return lvl
end

function Upgrades:value(userId, key: string): any
	return self:valueAt(key, self:level(userId, key))
end

function Upgrades:buy(userId, key: string, currency): (boolean, string?)
	local def = self:_def(key)
	local price = self:cost(userId, key)
	if not price then
		return false, "maxed"
	end
	if not currency:spend(userId, def.currency, price, "upgrade:" .. key) then
		return false, "funds"
	end
	self.levels[userId][key] += 1
	return true, nil
end

function Upgrades:reset(userId, keys: { string }?)
	for key in self.defs do
		if keys == nil or table.find(keys, key) then
			self.levels[userId][key] = 0
		end
	end
end

return Upgrades
