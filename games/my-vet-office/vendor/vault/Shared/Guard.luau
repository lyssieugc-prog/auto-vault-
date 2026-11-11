--[[
	Guard — remote argument validation + per-player rate limiting (token bucket).

	local limiter = Guard.rateLimiter({ rate = 5, burst = 10, now = os.clock })
	if not limiter:allow(player.UserId, "BuyEgg") then return end
	if not Guard.integer(eggCount, 1, 3) then return end
	if not Guard.oneOf(eggName, EggConfig.names) then return end

	Every RemoteEvent / RemoteFunction handler must validate ALL arguments with these helpers
	before touching game state. Clients can send anything.
]]

local Guard = {}

function Guard.number(value: any, min: number?, max: number?): boolean
	if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then
		return false
	end
	if min and value < min then
		return false
	end
	if max and value > max then
		return false
	end
	return true
end

function Guard.integer(value: any, min: number?, max: number?): boolean
	return Guard.number(value, min, max) and value % 1 == 0
end

function Guard.string(value: any, maxLength: number?): boolean
	return type(value) == "string" and #value <= (maxLength or 200)
end

function Guard.boolean(value: any): boolean
	return type(value) == "boolean"
end

function Guard.oneOf(value: any, allowed: { any }): boolean
	return table.find(allowed, value) ~= nil
end

-- Array of strings (e.g. item uids) with a max length and no duplicates.
function Guard.stringList(value: any, maxCount: number, maxLength: number?): boolean
	if type(value) ~= "table" or #value > maxCount then
		return false
	end
	local count = 0
	local seen = {}
	for k, v in value do
		count += 1
		if type(k) ~= "number" or not Guard.string(v, maxLength or 50) or seen[v] then
			return false
		end
		seen[v] = true
	end
	return count == #value
end

local Limiter = {}
Limiter.__index = Limiter

function Guard.rateLimiter(config)
	config = config or {}
	return setmetatable({
		rate = config.rate or 5, -- tokens per second
		burst = config.burst or 10, -- bucket size
		now = config.now or os.clock,
		buckets = {},
	}, Limiter)
end

function Limiter:allow(userId, key: string?): boolean
	local id = tostring(userId) .. ":" .. (key or "*")
	local t = self.now()
	local bucket = self.buckets[id]
	if not bucket then
		bucket = { tokens = self.burst, at = t }
		self.buckets[id] = bucket
	end
	bucket.tokens = math.min(self.burst, bucket.tokens + (t - bucket.at) * self.rate)
	bucket.at = t
	if bucket.tokens >= 1 then
		bucket.tokens -= 1
		return true
	end
	return false
end

function Limiter:removePlayer(userId)
	local prefix = tostring(userId) .. ":"
	for id in self.buckets do
		if string.sub(id, 1, #prefix) == prefix then
			self.buckets[id] = nil
		end
	end
end

return Guard
