--[[
	Boosts — timed, server-clock multipliers (onboarding reward, 15-min products, reward chests).

	local boosts = Boosts.new({
		defs = {
			CashX2 = { multiplier = 2, label = "x2 Cash" },
			LuckX2 = { multiplier = 2, label = "x2 Luck" },
		},
		maxSeconds = 4 * 3600, -- remaining time never exceeds this (stacking cap)
		now = os.time,         -- server UTC seconds; injectable
	})
	local state = Boosts.newState()          -- stored in the profile (profile.boosts)
	boosts:grant(state, "CashX2", 600)       -- adds 10 min (stacks on top of any remaining time)
	boosts:multiplier(state, "CashX2")       -- 2 while active, 1 otherwise
	boosts:remaining(state, "CashX2")        -- seconds left (0 when expired)
	boosts:list(state)                       -- { { name, label, multiplier, remaining } } for the HUD
	boosts:prune(state)                      -- drops expired boosts, returns their names

	Expiry is stored as absolute server time, so leaving and rejoining does not pause or extend a
	boost, and the client clock is never consulted.
]]

local Boosts = {}
Boosts.__index = Boosts

function Boosts.new(config)
	assert(type(config) == "table" and type(config.defs) == "table", "Boosts.new: defs required")
	local self = setmetatable({}, Boosts)
	self.defs = {}
	for name, def in config.defs do
		assert(type(def.multiplier) == "number" and def.multiplier >= 1, "Boosts.new: " .. name .. " needs multiplier")
		self.defs[name] = { multiplier = def.multiplier, label = def.label or name }
	end
	self.maxSeconds = config.maxSeconds or 6 * 3600
	self.now = config.now or os.time
	return self
end

function Boosts.newState()
	return { active = {} }
end

function Boosts:has(name: any): boolean
	return type(name) == "string" and self.defs[name] ~= nil
end

function Boosts:remaining(state, name: string): number
	local expires = state.active[name]
	if type(expires) ~= "number" then
		return 0
	end
	return math.max(0, expires - self.now())
end

function Boosts:isActive(state, name: string): boolean
	return self:remaining(state, name) > 0
end

-- Adds `seconds` of boost time. Returns the new remaining time, or nil + error.
function Boosts:grant(state, name: string, seconds: number): (number?, string?)
	if not self:has(name) then
		return nil, "unknown"
	end
	if type(seconds) ~= "number" or seconds ~= seconds or seconds <= 0 or seconds == math.huge then
		return nil, "invalid"
	end
	local remaining = math.min(self:remaining(state, name) + seconds, self.maxSeconds)
	state.active[name] = self.now() + remaining
	return remaining, nil
end

function Boosts:multiplier(state, name: string): number
	if self:isActive(state, name) then
		return self.defs[name].multiplier
	end
	return 1
end

function Boosts:prune(state): { string }
	local expired = {}
	for name in state.active do
		if not self:has(name) or self:remaining(state, name) <= 0 then
			table.insert(expired, name)
		end
	end
	for _, name in expired do
		state.active[name] = nil
	end
	table.sort(expired)
	return expired
end

function Boosts:list(state)
	local out = {}
	for name, def in self.defs do
		local remaining = self:remaining(state, name)
		if remaining > 0 then
			table.insert(out, { name = name, label = def.label, multiplier = def.multiplier, remaining = remaining })
		end
	end
	table.sort(out, function(a, b)
		return a.name < b.name
	end)
	return out
end

return Boosts
