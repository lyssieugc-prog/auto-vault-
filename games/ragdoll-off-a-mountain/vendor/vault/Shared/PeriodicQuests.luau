--[[
	PeriodicQuests — daily + weekly quests that reset on UTC boundaries (standards: daily + weekly).

	local quests = PeriodicQuests.new({
		periods = {
			daily = { length = 86400 },                      -- resets 00:00 UTC
			weekly = { length = 604800, offset = 345600 },   -- resets Monday 00:00 UTC
		},
		quests = {
			{ id = "d_bones", period = "daily", stat = "bones", goal = 100, reward = { currency = "Cash", amount = 1000 } },
			{ id = "w_bones", period = "weekly", stat = "bones", goal = 5000, reward = { currency = "Gems", amount = 50 } },
		},
		now = os.time,
	})
	local state = PeriodicQuests.newState()       -- profile.periodicQuests
	quests:progress(state, "bones", 12)           -- server events only; returns ids that just completed
	quests:claim(state, "d_bones")                -- reward or nil, "unknown" | "incomplete" | "claimed"
	quests:list(state)                            -- UI rows with value/goal/claimed/secondsUntilReset

	Progress is kept per period index, so a stale period silently resets the next time it is touched.
	(The Unix epoch began on a Thursday; offset 345600 = 4 days moves week boundaries to Monday.)
]]

local PeriodicQuests = {}
PeriodicQuests.__index = PeriodicQuests

function PeriodicQuests.new(config)
	assert(type(config) == "table" and type(config.periods) == "table", "PeriodicQuests.new: periods required")
	local self = setmetatable({}, PeriodicQuests)
	self.periods = {}
	for name, period in config.periods do
		assert(type(period.length) == "number" and period.length > 0, "PeriodicQuests.new: bad period " .. name)
		self.periods[name] = { length = period.length, offset = period.offset or 0 }
	end
	self.quests = config.quests or {}
	self.byId = {}
	for _, quest in self.quests do
		assert(type(quest.id) == "string" and type(quest.goal) == "number", "PeriodicQuests.new: bad quest")
		assert(self.periods[quest.period], "PeriodicQuests.new: quest " .. quest.id .. " has unknown period")
		assert(self.byId[quest.id] == nil, "PeriodicQuests.new: duplicate quest id " .. quest.id)
		self.byId[quest.id] = quest
	end
	self.now = config.now or os.time
	return self
end

function PeriodicQuests.newState()
	return {}
end

function PeriodicQuests:periodIndex(name: string): number
	local period = self.periods[name]
	return (self.now() - period.offset) // period.length
end

function PeriodicQuests:secondsUntilReset(name: string): number
	local period = self.periods[name]
	local nextStart = (self:periodIndex(name) + 1) * period.length + period.offset
	return nextStart - self.now()
end

-- Current bucket for a period (resets when the period index changed).
function PeriodicQuests:_bucket(state, name: string)
	local index = self:periodIndex(name)
	local bucket = state[name]
	if type(bucket) ~= "table" or bucket.index ~= index then
		bucket = { index = index, stats = {}, claimed = {} }
		state[name] = bucket
	end
	return bucket
end

function PeriodicQuests:progress(state, stat: string, amount: number?): { string }
	local add = amount or 1
	if type(add) ~= "number" or add ~= add or add <= 0 or add == math.huge then
		return {}
	end
	local completed = {}
	local touched = {}
	for _, quest in self.quests do
		if quest.stat == stat then
			local bucket = self:_bucket(state, quest.period)
			if not touched[quest.period] then
				touched[quest.period] = (bucket.stats[stat] or 0)
				bucket.stats[stat] = touched[quest.period] + add
			end
			local before = touched[quest.period]
			if before < quest.goal and bucket.stats[stat] >= quest.goal and not bucket.claimed[quest.id] then
				table.insert(completed, quest.id)
			end
		end
	end
	return completed
end

function PeriodicQuests:status(state, questId: string)
	local quest = self.byId[questId]
	if not quest then
		return nil
	end
	local bucket = self:_bucket(state, quest.period)
	local value = bucket.stats[quest.stat] or 0
	return {
		id = quest.id,
		period = quest.period,
		value = math.min(value, quest.goal),
		goal = quest.goal,
		complete = value >= quest.goal,
		claimed = bucket.claimed[quest.id] == true,
		secondsUntilReset = self:secondsUntilReset(quest.period),
		reward = quest.reward,
		text = quest.text,
	}
end

function PeriodicQuests:claim(state, questId: any)
	if type(questId) ~= "string" then
		return nil, "unknown"
	end
	local status = self:status(state, questId)
	if not status then
		return nil, "unknown"
	end
	if status.claimed then
		return nil, "claimed"
	end
	if not status.complete then
		return nil, "incomplete"
	end
	self:_bucket(state, status.period).claimed[questId] = true
	return self.byId[questId].reward, nil
end

function PeriodicQuests:list(state)
	local out = {}
	for _, quest in self.quests do
		table.insert(out, self:status(state, quest.id))
	end
	return out
end

return PeriodicQuests
