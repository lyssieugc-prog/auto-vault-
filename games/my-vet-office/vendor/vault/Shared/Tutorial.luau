--[[
	Tutorial — linear onboarding step machine (server tracks, client renders arrows/text).

	local tutorial = Tutorial.new({
		steps = {
			{ id = "collect", text = "Tap the glowing coins!", target = "CoinPile" },
			{ id = "egg", text = "Buy your first egg!", target = "EggStand" },
			{ id = "equip", text = "Equip your pet!", ui = "PetsButton" },
		},
	})
	local state = profile.tutorial -- { index = 1, done = false }
	tutorial:complete(state, "collect") -- only advances when the id matches the current step
]]

local Tutorial = {}
Tutorial.__index = Tutorial

function Tutorial.new(config)
	assert(type(config) == "table" and type(config.steps) == "table", "Tutorial.new: steps required")
	local self = setmetatable({}, Tutorial)
	self.steps = config.steps
	self.indexById = {}
	for i, step in config.steps do
		assert(type(step.id) == "string", "Tutorial.new: step.id required")
		self.indexById[step.id] = i
	end
	return self
end

function Tutorial.newState()
	return { index = 1, done = false }
end

function Tutorial:current(state)
	if state.done or state.index > #self.steps then
		return nil
	end
	return self.steps[state.index]
end

function Tutorial:isDone(state): boolean
	return state.done or state.index > #self.steps
end

-- Returns the next step (or nil when finished) and whether anything changed.
function Tutorial:complete(state, stepId: string)
	local step = self:current(state)
	if not step or step.id ~= stepId then
		return self:current(state), false
	end
	state.index += 1
	if state.index > #self.steps then
		state.done = true
	end
	return self:current(state), true
end

function Tutorial:skip(state)
	state.done = true
	state.index = #self.steps + 1
end

function Tutorial:progress(state): (number, number)
	return math.min(state.index - 1, #self.steps), #self.steps
end

return Tutorial
