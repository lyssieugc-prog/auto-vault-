--[[
	Rarity — weighted rolls with luck, pity and mutations.

	local roller = Rarity.new({
		tiers = {
			{ name = "Common", weight = 600 },
			{ name = "Uncommon", weight = 250 },
			{ name = "Rare", weight = 100 },
			{ name = "Epic", weight = 40 },
			{ name = "Legendary", weight = 9 },
			{ name = "Mythic", weight = 0.9 },
			{ name = "Secret", weight = 0.1 },
		},
		luckStartsAt = "Rare",                      -- luck multiplies this tier and rarer
		pity = { threshold = 75, minTier = "Legendary" }, -- guaranteed Legendary+ on roll #75
		mutations = { { name = "Gold", chance = 0.05, multiplier = 2 } },
		rng = function() return math.random() end,   -- inject Random:NextNumber in Roblox
	})
	local tier = roller:roll(luck, pityState)       -- pityState = { count = 0 } persisted per player

	Pure module. Server is the only caller that may roll for rewards.
]]

export type Tier = { name: string, weight: number }
export type Mutation = { name: string, chance: number, multiplier: number }
export type PityState = { count: number }

local Rarity = {}
Rarity.__index = Rarity

local function indexOf(tiers: { Tier }, name: string): number
	for i, tier in tiers do
		if tier.name == name then
			return i
		end
	end
	error("Rarity: unknown tier '" .. tostring(name) .. "'", 3)
end

function Rarity.new(config)
	assert(type(config) == "table" and type(config.tiers) == "table", "Rarity.new: config.tiers required")
	assert(#config.tiers > 0, "Rarity.new: need at least one tier")
	for _, tier in config.tiers do
		assert(type(tier.name) == "string", "Rarity.new: tier.name must be a string")
		assert(type(tier.weight) == "number" and tier.weight >= 0, "Rarity.new: tier.weight must be >= 0")
	end
	local self = setmetatable({}, Rarity)
	self.tiers = config.tiers
	self.rng = config.rng or function()
		return math.random()
	end
	self.luckStartIndex = if config.luckStartsAt then indexOf(config.tiers, config.luckStartsAt) else 1
	if config.pity then
		self.pityThreshold = config.pity.threshold
		self.pityMinIndex = indexOf(config.tiers, config.pity.minTier)
	end
	self.mutations = config.mutations or {}
	return self
end

-- Effective weights after luck. luck = 1 means base odds.
function Rarity:weights(luck: number?, minIndex: number?): { number }
	local l = math.max(luck or 1, 0)
	local out = {}
	for i, tier in self.tiers do
		local w = tier.weight
		if i >= self.luckStartIndex then
			w *= l
		end
		if minIndex and i < minIndex then
			w = 0
		end
		out[i] = w
	end
	return out
end

-- Odds as percentages (for the odds strip UI). Returns { {name, percent} }.
function Rarity:odds(luck: number?): { { name: string, percent: number } }
	local weights = self:weights(luck)
	local total = 0
	for _, w in weights do
		total += w
	end
	local out = {}
	for i, tier in self.tiers do
		table.insert(out, { name = tier.name, percent = if total > 0 then weights[i] / total * 100 else 0 })
	end
	return out
end

function Rarity:_pick(weights: { number }): number
	local total = 0
	for _, w in weights do
		total += w
	end
	assert(total > 0, "Rarity: all weights are zero")
	local target = self.rng() * total
	local acc = 0
	for i, w in weights do
		acc += w
		if target < acc then
			return i
		end
	end
	-- Floating point edge: return the last tier with weight.
	for i = #weights, 1, -1 do
		if weights[i] > 0 then
			return i
		end
	end
	return 1
end

-- Rolls a tier name. If pityState is given and pity is configured, it is updated in place.
function Rarity:roll(luck: number?, pityState: PityState?): string
	local minIndex = nil
	if pityState and self.pityThreshold then
		if pityState.count + 1 >= self.pityThreshold then
			minIndex = self.pityMinIndex
		end
	end
	local index = self:_pick(self:weights(luck, minIndex))
	if pityState and self.pityThreshold then
		if index >= self.pityMinIndex then
			pityState.count = 0
		else
			pityState.count += 1
		end
	end
	return self.tiers[index].name
end

-- Rolls left until pity triggers (for "guaranteed in 75" UI).
function Rarity:pityRemaining(pityState: PityState): number?
	if not self.pityThreshold then
		return nil
	end
	return math.max(self.pityThreshold - pityState.count, 1)
end

-- Rolls at most one mutation (checked in config order). Returns name, multiplier or nil, 1.
function Rarity:rollMutation(chanceMultiplier: number?): (string?, number)
	local m = chanceMultiplier or 1
	for _, mutation in self.mutations do
		if self.rng() < mutation.chance * m then
			return mutation.name, mutation.multiplier
		end
	end
	return nil, 1
end

function Rarity:tierIndex(name: string): number
	return indexOf(self.tiers, name)
end

-- Generic weighted pick from { {value, weight} } lists (eggs, loot tables).
function Rarity.pickWeighted(entries: { { value: any, weight: number } }, rng: (() -> number)?): any
	local r = rng or math.random
	local total = 0
	for _, e in entries do
		total += e.weight
	end
	assert(total > 0, "Rarity.pickWeighted: total weight is zero")
	local target = r() * total
	local acc = 0
	for _, e in entries do
		acc += e.weight
		if target < acc then
			return e.value
		end
	end
	return entries[#entries].value
end

return Rarity
