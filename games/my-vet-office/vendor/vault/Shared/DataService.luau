--[[
	DataService — player profiles with schema versioning, template reconcile, session locking,
	retries and safe release. Storage is injected so it is testable outside Roblox.

	local data = DataService.new({
		store = DataStoreAdapter.new("PlayerData_v1"), -- see Server/DataStoreAdapter
		template = { version = 1, currency = {}, inventory = {}, rewards = {} },
		version = 2,
		migrations = { [2] = function(profile) profile.newField = 0 end }, -- runs for v1 -> v2
		sessionId = game.JobId,
		lockTimeout = 1800,           -- seconds before a crashed server's lock is considered dead
		now = os.time,
		retries = 3, wait = task.wait,
	})
	local profile, err = data:load(player.UserId)  -- nil, "locked" if another server holds it
	data:save(player.UserId)                        -- autosave every ~60-120s
	data:release(player.UserId)                     -- PlayerRemoving + BindToClose

	Store interface: store:update(key, function(old) return new end) -> (value, err)
	Returning nil from the transform cancels the write (Roblox UpdateAsync semantics).
]]

local DataService = {}
DataService.__index = DataService

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local out = {}
	for k, v in value do
		out[k] = deepCopy(v)
	end
	return out
end

-- Fills keys missing from `data` with copies from `template` (recursive, never overwrites).
local function reconcile(data, template)
	for k, v in template do
		if data[k] == nil then
			data[k] = deepCopy(v)
		elseif type(data[k]) == "table" and type(v) == "table" and next(v) ~= nil and #v == 0 then
			reconcile(data[k], v)
		end
	end
end

DataService.deepCopy = deepCopy
DataService.reconcile = reconcile

function DataService.new(config)
	assert(type(config) == "table" and config.store and config.template, "DataService.new: store + template required")
	local self = setmetatable({}, DataService)
	self.store = config.store
	self.template = config.template
	self.version = config.version or 1
	self.migrations = config.migrations or {}
	self.sessionId = config.sessionId or "local"
	self.lockTimeout = config.lockTimeout or 1800
	self.now = config.now or os.time
	self.retries = config.retries or 3
	self.wait = config.wait or function() end
	self.keyPrefix = config.keyPrefix or "u_"
	self.profiles = {}
	return self
end

function DataService:_key(userId): string
	return self.keyPrefix .. tostring(userId)
end

function DataService:_withRetry(fn)
	local lastErr
	for attempt = 1, self.retries do
		local ok, a, b = pcall(fn)
		if ok and b == nil then
			return a, nil
		end
		lastErr = if ok then b else a
		if lastErr == "locked" then
			return nil, lastErr
		end
		if attempt < self.retries then
			self.wait(2 ^ (attempt - 1))
		end
	end
	return nil, tostring(lastErr)
end

function DataService:_migrate(profile)
	local v = profile.version or 1
	while v < self.version do
		v += 1
		local migration = self.migrations[v]
		if migration then
			migration(profile)
		end
	end
	profile.version = self.version
end

function DataService:load(userId)
	if self.profiles[userId] then
		return self.profiles[userId], nil
	end
	local key = self:_key(userId)
	local lockedBy = nil
	local value, err = self:_withRetry(function()
		lockedBy = nil
		return self.store:update(key, function(old)
			local record = old or { data = nil, lock = nil }
			local lock = record.lock
			if lock and lock.session ~= self.sessionId and self.now() - lock.time < self.lockTimeout then
				lockedBy = lock.session
				return nil -- cancel write
			end
			record.lock = { session = self.sessionId, time = self.now() }
			return record
		end)
	end)
	if lockedBy then
		return nil, "locked"
	end
	if err or value == nil then
		return nil, err or "load_failed"
	end
	local profile = value.data
	if type(profile) ~= "table" then
		profile = deepCopy(self.template)
		profile.version = self.version
	end
	self:_migrate(profile)
	reconcile(profile, self.template)
	self.profiles[userId] = profile
	return profile, nil
end

function DataService:get(userId)
	return self.profiles[userId]
end

-- Saves the cached profile. release = true clears the session lock.
function DataService:save(userId, release: boolean?): (boolean, string?)
	local profile = self.profiles[userId]
	if not profile then
		return false, "not_loaded"
	end
	local lostLock = false
	local snapshot = deepCopy(profile)
	local _, err = self:_withRetry(function()
		lostLock = false
		return self.store:update(self:_key(userId), function(old)
			local record = old or {}
			if record.lock and record.lock.session ~= self.sessionId then
				lostLock = true
				return nil
			end
			record.data = snapshot
			record.lock = if release then nil else { session = self.sessionId, time = self.now() }
			return record
		end)
	end)
	if lostLock then
		return false, "lost_lock"
	end
	if err then
		return false, err
	end
	return true, nil
end

function DataService:release(userId): (boolean, string?)
	local ok, err = self:save(userId, true)
	self.profiles[userId] = nil
	return ok, err
end

function DataService:saveAll(release: boolean?)
	local results = {}
	for userId in self.profiles do
		results[userId] = self:save(userId, release)
	end
	if release then
		self.profiles = {}
	end
	return results
end

return DataService
