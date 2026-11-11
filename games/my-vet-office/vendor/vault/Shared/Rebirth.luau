--[[
	Rebirth — reset progress for a permanent multiplier.

	local rebirth = Rebirth.new({
		currency = "Cash",          -- paid with this currency
		baseCost = 1e6, growth = 2.5,
		multiplierPerRebirth = 0.5, -- x1.5, x2, x2.5 ...
		resetCurrencies = { "Cash" },
		onReset = function(userId) tycoon:reset(userId); upgrades:reset(userId, { "WalkSpeed" }) end,
	})
	rebirth:load(userId, savedCount)
	rebirth:rebirth(userId, currency)
	currency:setMultiplier(userId, "Rebirth", rebirth:multiplier(userId))
]]

local Rebirth = {}
Rebirth.__index = Rebirth

function Rebirth.new(config)
	assert(type(config) == "table" and type(config.currency) == "string", "Rebirth.new: currency required")
	assert(type(config.baseCost) == "number", "Rebirth.new: baseCost required")
	local self = setmetatable({}, Rebirth)
	self.currency = config.currency
	self.baseCost = config.baseCost
	self.growth = config.growth or 2
	self.multiplierPerRebirth = config.multiplierPerRebirth or 0.5
	self.maxRebirths = config.maxRebirths or math.huge
	self.resetCurrencies = config.resetCurrencies or { config.currency }
	self.onReset = config.onReset
	self.counts = {}
	return self
end

function Rebirth:load(userId, saved: number?)
	self.counts[userId] = math.max(0, math.floor(tonumber(saved) or 0))
end

function Rebirth:serialize(userId): number
	return self.counts[userId]
end

function Rebirth:unload(userId)
	self.counts[userId] = nil
end

function Rebirth:count(userId): number
	return self.counts[userId] or 0
end

function Rebirth:cost(userId): number
	return math.floor(self.baseCost * self.growth ^ self:count(userId))
end

function Rebirth:multiplierAt(count: number): number
	return 1 + count * self.multiplierPerRebirth
end

function Rebirth:multiplier(userId): number
	return self:multiplierAt(self:count(userId))
end

-- For the "next goal" banner: { cost, progress 0..1, nextMultiplier }.
function Rebirth:nextGoal(userId, currency)
	local price = self:cost(userId)
	local balance = currency:get(userId, self.currency)
	return {
		cost = price,
		progress = math.clamp(balance / math.max(price, 1), 0, 1),
		nextMultiplier = self:multiplierAt(self:count(userId) + 1),
	}
end

function Rebirth:rebirth(userId, currency): (boolean, string?)
	if self:count(userId) >= self.maxRebirths then
		return false, "max"
	end
	local price = self:cost(userId)
	if not currency:canAfford(userId, self.currency, price) then
		return false, "funds"
	end
	if not table.find(self.resetCurrencies, self.currency) then
		currency:spend(userId, self.currency, price, "rebirth")
	end
	for _, name in self.resetCurrencies do
		currency:set(userId, name, 0, "rebirth")
	end
	self.counts[userId] += 1
	if self.onReset then
		self.onReset(userId, self.counts[userId])
	end
	return true, nil
end

return Rebirth
