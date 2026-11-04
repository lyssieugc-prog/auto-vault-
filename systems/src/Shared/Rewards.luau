--[[
	Rewards — quests, 7-day daily rewards and playtime rewards.

	local rewards = Rewards.new({
		quests = {
			{ id = "hatch10", stat = "eggsHatched", goal = 10, reward = { currency = "Cash", amount = 500 } },
		},
		daily = { -- 7 entries; day 7 is the big prize
			{ currency = "Cash", amount = 100 }, ..., { item = "SecretPet" },
		},
		playtime = { { seconds = 300, reward = { currency = "Gems", amount = 5 } }, ... },
		now = os.time, -- UTC seconds; injectable
	})

	State is one plain table per player stored in the profile (profile.rewards):
		{ stats = {}, claimedQuests = {}, daily = { lastDay = nil, streak = 0 }, playtimeClaimed = {} }
	The module returns reward tables; the game grants them (currency:add / inventory:add).
]]

local Rewards = {}
Rewards.__index = Rewards

local DAY = 86400

function Rewards.new(config)
	config = config or {}
	local self = setmetatable({}, Rewards)
	self.quests = config.quests or {}
	self.questById = {}
	for _, quest in self.quests do
		assert(type(quest.id) == "string" and type(quest.goal) == "number", "Rewards.new: bad quest")
		self.questById[quest.id] = quest
	end
	self.daily = config.daily or {}
	self.playtime = config.playtime or {}
	self.now = config.now or os.time
	return self
end

function Rewards.newState()
	return { stats = {}, claimedQuests = {}, daily = { lastDay = nil, streak = 0 }, playtimeClaimed = {} }
end

-- Quests -----------------------------------------------------------------------------------------

-- Adds to a stat. Returns ids of quests that just became claimable.
function Rewards:progress(state, stat: string, amount: number?): { string }
	local before = state.stats[stat] or 0
	local after = before + (amount or 1)
	state.stats[stat] = after
	local completed = {}
	for _, quest in self.quests do
		if quest.stat == stat and before < quest.goal and after >= quest.goal and not state.claimedQuests[quest.id] then
			table.insert(completed, quest.id)
		end
	end
	return completed
end

function Rewards:questStatus(state, questId: string)
	local quest = self.questById[questId]
	if not quest then
		return nil
	end
	local value = state.stats[quest.stat] or 0
	return {
		value = math.min(value, quest.goal),
		goal = quest.goal,
		complete = value >= quest.goal,
		claimed = state.claimedQuests[questId] == true,
	}
end

function Rewards:claimQuest(state, questId: string)
	local status = self:questStatus(state, questId)
	if not status then
		return nil, "unknown"
	end
	if status.claimed then
		return nil, "claimed"
	end
	if not status.complete then
		return nil, "incomplete"
	end
	state.claimedQuests[questId] = true
	return self.questById[questId].reward, nil
end

-- Daily rewards ----------------------------------------------------------------------------------

function Rewards:_today(): number
	return self.now() // DAY
end

-- { day = 1..7 (the day that would be claimed), canClaim, secondsUntilNext, streak }
function Rewards:dailyStatus(state)
	local today = self:_today()
	local last = state.daily.lastDay
	local streak = state.daily.streak or 0
	local canClaim = last == nil or today > last
	local nextStreak
	if last ~= nil and today == last + 1 then
		nextStreak = streak + 1
	elseif last ~= nil and today == last then
		nextStreak = streak
	else
		nextStreak = 1
	end
	local count = math.max(#self.daily, 1)
	return {
		day = ((nextStreak - 1) % count) + 1,
		canClaim = canClaim,
		secondsUntilNext = if canClaim then 0 else (today + 1) * DAY - self.now(),
		streak = streak,
	}
end

function Rewards:claimDaily(state)
	local status = self:dailyStatus(state)
	if not status.canClaim then
		return nil, "claimed_today"
	end
	local today = self:_today()
	local last = state.daily.lastDay
	if last ~= nil and today == last + 1 then
		state.daily.streak = (state.daily.streak or 0) + 1
	else
		state.daily.streak = 1
	end
	state.daily.lastDay = today
	return self.daily[status.day], status.day
end

-- Playtime rewards (per session; sessionSeconds measured on the server) ---------------------------

function Rewards:playtimeStatus(state, sessionSeconds: number)
	local out = {}
	for i, entry in self.playtime do
		table.insert(out, {
			index = i,
			claimed = state.playtimeClaimed[i] == true,
			ready = sessionSeconds >= entry.seconds,
			remaining = math.max(0, entry.seconds - sessionSeconds),
		})
	end
	return out
end

function Rewards:claimPlaytime(state, index: number, sessionSeconds: number)
	local entry = self.playtime[index]
	if not entry then
		return nil, "unknown"
	end
	if state.playtimeClaimed[index] then
		return nil, "claimed"
	end
	if sessionSeconds < entry.seconds then
		return nil, "not_ready"
	end
	state.playtimeClaimed[index] = true
	return entry.reward, nil
end

-- Call when a new session starts (playtime rewards reset every session).
function Rewards.resetPlaytime(state)
	state.playtimeClaimed = {}
end

return Rewards
