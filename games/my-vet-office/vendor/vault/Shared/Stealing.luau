--[[
	Stealing — steal-and-protect mechanics for brainrot/base games.

	local stealing = Stealing.new({
		stealDuration = 2.5,   -- seconds holding the prompt before you grab the item
		lockDuration = 60,     -- base lock length when the owner presses LOCK
		lockCooldown = 30,     -- seconds after a lock ends before it can be used again
		thiefCooldown = 5,     -- seconds between steal attempts per thief
		now = os.clock,        -- injectable clock
	})
	stealing:lockBase(ownerId)
	stealing:startSteal(thiefId, ownerId, itemUid)
	stealing:completeSteal(thiefId)  -- thief reached own base -> returns { ownerId, itemUid }
	stealing:cancelSteal(thiefId)    -- thief was hit / died / left
	stealing:setShield(ownerId, seconds) -- purchased protection

	The game script moves the item with Inventory:transfer after completeSteal succeeds,
	and validates distance (thief at owner pedestal / at own base) before each call.
]]

local Stealing = {}
Stealing.__index = Stealing

function Stealing.new(config)
	config = config or {}
	local self = setmetatable({}, Stealing)
	self.stealDuration = config.stealDuration or 2.5
	self.lockDuration = config.lockDuration or 60
	self.lockCooldown = config.lockCooldown or 30
	self.thiefCooldown = config.thiefCooldown or 5
	self.now = config.now or os.clock
	self.locks = {} -- [ownerId] = { untilTime, readyAt }
	self.shields = {} -- [ownerId] = untilTime
	self.active = {} -- [thiefId] = { ownerId, itemUid, startedAt, grabbed }
	self.lastAttempt = {} -- [thiefId] = time
	return self
end

function Stealing:isProtected(ownerId): boolean
	local t = self.now()
	local lock = self.locks[ownerId]
	if lock and t < lock.untilTime then
		return true
	end
	local shield = self.shields[ownerId]
	return shield ~= nil and t < shield
end

function Stealing:protectionRemaining(ownerId): number
	local t = self.now()
	local remaining = 0
	local lock = self.locks[ownerId]
	if lock then
		remaining = math.max(remaining, lock.untilTime - t)
	end
	local shield = self.shields[ownerId]
	if shield then
		remaining = math.max(remaining, shield - t)
	end
	return remaining
end

-- Owner presses LOCK. Returns ok, reason.
function Stealing:lockBase(ownerId, duration: number?): (boolean, string?)
	local t = self.now()
	local lock = self.locks[ownerId]
	if lock and t < lock.readyAt then
		return false, if t < lock.untilTime then "already_locked" else "cooldown"
	end
	local length = duration or self.lockDuration
	self.locks[ownerId] = { untilTime = t + length, readyAt = t + length + self.lockCooldown }
	-- Locking kicks out anyone mid-steal (not already carrying).
	for thiefId, steal in self.active do
		if steal.ownerId == ownerId and not steal.grabbed then
			self.active[thiefId] = nil
		end
	end
	return true, nil
end

function Stealing:setShield(ownerId, seconds: number)
	local t = self.now()
	local current = self.shields[ownerId]
	local base = if current and current > t then current else t
	self.shields[ownerId] = base + seconds
end

function Stealing:isItemTargeted(ownerId, itemUid: string): boolean
	for _, steal in self.active do
		if steal.ownerId == ownerId and steal.itemUid == itemUid then
			return true
		end
	end
	return false
end

function Stealing:startSteal(thiefId, ownerId, itemUid: string): (boolean, string?)
	if thiefId == ownerId then
		return false, "own_base"
	end
	if self.active[thiefId] then
		return false, "busy"
	end
	local t = self.now()
	local last = self.lastAttempt[thiefId]
	if last and t - last < self.thiefCooldown then
		return false, "cooldown"
	end
	if self:isProtected(ownerId) then
		return false, "protected"
	end
	if self:isItemTargeted(ownerId, itemUid) then
		return false, "taken"
	end
	self.lastAttempt[thiefId] = t
	self.active[thiefId] = { ownerId = ownerId, itemUid = itemUid, startedAt = t, grabbed = false }
	return true, nil
end

-- Called when the hold prompt finishes. Thief now carries the item.
function Stealing:grab(thiefId): (boolean, string?)
	local steal = self.active[thiefId]
	if not steal then
		return false, "none"
	end
	if self.now() - steal.startedAt < self.stealDuration then
		return false, "too_fast"
	end
	steal.grabbed = true
	return true, nil
end

-- Thief reached their own base while carrying. Returns { ownerId, itemUid } or nil, reason.
function Stealing:completeSteal(thiefId)
	local steal = self.active[thiefId]
	if not steal then
		return nil, "none"
	end
	if not steal.grabbed then
		return nil, "not_grabbed"
	end
	self.active[thiefId] = nil
	return { ownerId = steal.ownerId, itemUid = steal.itemUid }, nil
end

function Stealing:cancelSteal(thiefId): boolean
	if self.active[thiefId] then
		self.active[thiefId] = nil
		return true
	end
	return false
end

function Stealing:carrying(thiefId)
	local steal = self.active[thiefId]
	if steal and steal.grabbed then
		return steal
	end
	return nil
end

-- Clean up when a player leaves (cancel their steals and steals against them).
function Stealing:removePlayer(userId)
	self.active[userId] = nil
	for thiefId, steal in self.active do
		if steal.ownerId == userId then
			self.active[thiefId] = nil
		end
	end
	self.locks[userId] = nil
	self.shields[userId] = nil
	self.lastAttempt[userId] = nil
end

return Stealing
