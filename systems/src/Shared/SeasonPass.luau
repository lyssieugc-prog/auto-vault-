--[[
	SeasonPass — N-tier battle pass with free + premium tracks (standards: 50 tiers, explicit claims).

	local pass = SeasonPass.new({
		seasonId = "S1",
		tiers = 50,
		baseXp = 100, xpGrowth = 20,   -- tier n needs baseXp + xpGrowth * (n - 1) XP
		free = { [1] = { currency = "Cash", amount = 500 }, ... },
		premium = { [1] = { currency = "Gems", amount = 10 }, ... },
	})
	local state = pass:ensure(profile.season)  -- creates / resets the state when the season changes
	pass:addXp(state, 25)                       -- returns the list of tiers just reached
	pass:claim(state, "free", 3)                -- reward or nil, "locked" | "claimed" | "premium" | "none" | "invalid"
	pass:setPremium(state, true)                -- after a verified purchase only
	pass:status(state)                          -- { tier, xp, xpIntoTier, xpForNext, premium, claimable }

	Rewards are returned, never granted here: the game grants them (Currency/Inventory/Boosts).
	The season end date and premium price are CONFIG_REQUIRED values in the game Config.
]]

local SeasonPass = {}
SeasonPass.__index = SeasonPass

local TRACKS = { free = true, premium = true }

function SeasonPass.new(config)
	assert(type(config) == "table" and type(config.seasonId) == "string", "SeasonPass.new: seasonId required")
	local self = setmetatable({}, SeasonPass)
	self.seasonId = config.seasonId
	self.tiers = config.tiers or 50
	self.baseXp = config.baseXp or 100
	self.xpGrowth = config.xpGrowth or 0
	self.rewards = { free = config.free or {}, premium = config.premium or {} }
	-- cumulative[n] = total XP needed to reach tier n (cumulative[0] = 0)
	self.cumulative = { [0] = 0 }
	for n = 1, self.tiers do
		self.cumulative[n] = self.cumulative[n - 1] + self:xpForTier(n)
	end
	return self
end

function SeasonPass:xpForTier(n: number): number
	return self.baseXp + self.xpGrowth * (n - 1)
end

function SeasonPass:newState()
	return { season = self.seasonId, xp = 0, premium = false, claimed = { free = {}, premium = {} } }
end

-- Returns a valid state for the current season (fresh one if missing or from an older season).
function SeasonPass:ensure(state)
	if type(state) ~= "table" or state.season ~= self.seasonId then
		return self:newState()
	end
	state.xp = tonumber(state.xp) or 0
	state.claimed = state.claimed or { free = {}, premium = {} }
	state.claimed.free = state.claimed.free or {}
	state.claimed.premium = state.claimed.premium or {}
	return state
end

function SeasonPass:tierAt(xp: number): number
	local tier = 0
	for n = 1, self.tiers do
		if xp >= self.cumulative[n] then
			tier = n
		else
			break
		end
	end
	return tier
end

function SeasonPass:tier(state): number
	return self:tierAt(state.xp)
end

function SeasonPass:addXp(state, amount: number): { number }
	if type(amount) ~= "number" or amount ~= amount or amount <= 0 or amount == math.huge then
		return {}
	end
	local before = self:tier(state)
	state.xp = math.min(state.xp + amount, self.cumulative[self.tiers])
	local reached = {}
	for n = before + 1, self:tier(state) do
		table.insert(reached, n)
	end
	return reached
end

function SeasonPass:setPremium(state, owned: boolean)
	state.premium = owned == true
end

function SeasonPass:claim(state, track: any, tier: any)
	if type(track) ~= "string" or not TRACKS[track] then
		return nil, "invalid"
	end
	if type(tier) ~= "number" or tier % 1 ~= 0 or tier < 1 or tier > self.tiers then
		return nil, "invalid"
	end
	local reward = self.rewards[track][tier]
	if reward == nil then
		return nil, "none"
	end
	if track == "premium" and not state.premium then
		return nil, "premium"
	end
	if self:tier(state) < tier then
		return nil, "locked"
	end
	local key = tostring(tier)
	if state.claimed[track][key] then
		return nil, "claimed"
	end
	state.claimed[track][key] = true
	return reward, nil
end

function SeasonPass:status(state)
	local tier = self:tier(state)
	local claimable = 0
	for n = 1, tier do
		local key = tostring(n)
		if self.rewards.free[n] and not state.claimed.free[key] then
			claimable += 1
		end
		if state.premium and self.rewards.premium[n] and not state.claimed.premium[key] then
			claimable += 1
		end
	end
	local maxed = tier >= self.tiers
	return {
		season = self.seasonId,
		tier = tier,
		tiers = self.tiers,
		xp = state.xp,
		xpIntoTier = state.xp - self.cumulative[tier],
		xpForNext = if maxed then 0 else self:xpForTier(tier + 1),
		premium = state.premium,
		claimable = claimable,
	}
end

return SeasonPass
