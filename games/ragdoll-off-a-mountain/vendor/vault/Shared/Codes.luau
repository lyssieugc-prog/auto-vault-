--[[
	Codes — server-validated promo codes, one redemption per user (standards: redeemable codes).

	local codes = Codes.new({
		codes = {
			SNAP = { reward = { currency = "Cash", amount = 1000 } },
			LAUNCH = { reward = { currency = "Gems", amount = 10 }, expiresAt = 1893456000 },
		},
		now = os.time,
	})
	local state = Codes.newState()         -- profile.codes
	codes:redeem(state, "  snap ")         -- reward or nil, "invalid" | "expired" | "redeemed"

	Policy: case-insensitive, surrounding whitespace ignored, letters/digits only, max 24 chars.
	Real codes are owner-approved CONFIG values; never invent live codes.
]]

local Codes = {}
Codes.__index = Codes

local MAX_LENGTH = 24

function Codes.normalize(input: any): string?
	if type(input) ~= "string" or #input > 64 then
		return nil
	end
	local trimmed = string.gsub(input, "^%s+", "")
	trimmed = string.gsub(trimmed, "%s+$", "")
	local code = string.upper(trimmed)
	if #code == 0 or #code > MAX_LENGTH or string.find(code, "[^%w]") then
		return nil
	end
	return code
end

function Codes.new(config)
	assert(type(config) == "table" and type(config.codes) == "table", "Codes.new: codes required")
	local self = setmetatable({}, Codes)
	self.codes = {}
	for name, def in config.codes do
		local key = Codes.normalize(name)
		assert(key ~= nil, "Codes.new: invalid code name " .. tostring(name))
		assert(type(def.reward) == "table", "Codes.new: code " .. name .. " needs a reward")
		self.codes[key] = { reward = def.reward, expiresAt = def.expiresAt }
	end
	self.now = config.now or os.time
	return self
end

function Codes.newState()
	return { redeemed = {} }
end

function Codes:redeem(state, input: any)
	local key = Codes.normalize(input)
	local def = key and self.codes[key]
	if not key or not def then
		return nil, "invalid"
	end
	if def.expiresAt and self.now() >= def.expiresAt then
		return nil, "expired"
	end
	state.redeemed = state.redeemed or {}
	if state.redeemed[key] then
		return nil, "redeemed"
	end
	state.redeemed[key] = true
	return def.reward, nil
end

return Codes
