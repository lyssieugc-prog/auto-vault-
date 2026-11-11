--[[
	AnimalMind — emotion + personality model. Pure (no Roblox APIs).

	Eight attributes, all 0..1: fear, trust, stress, pain, energy, curiosity, comfort, sociability.
	  • A breed temperament sets the baselines; the patient's condition (illness) shifts pain/energy.
	  • Stimuli (petting, treats, loud barking, being picked up, a cold stethoscope …) push
	    attributes; their effect depends on the current state (a terrified, untrusting dog does
	    NOT relax from being petted — it pulls away and gets more stressed).
	  • tick(dt) relaxes everything back toward baseline at per-attribute rates, while stress
	    is pulled toward a level implied by fear, pain and (lack of) comfort.
	  • derive() turns the state into animation parameters (tail wag speed/height, ear pose,
	    tremble, panting, breath rate, blink interval, gait speed, limp, head height) and
	    behaviour parameters (cooperation, wants to hide, will approach).

	The server owns the mind (it decides whether an exam step succeeds); clients only receive
	derived params as replicated attributes and animate from them.

	local mind = AnimalMind.new(breed.temperament, { pain = 0.3, energy = -0.3 })
	AnimalMind.stimulus(mind, "Pet", 1)
	AnimalMind.tick(mind, dt)
	local params = AnimalMind.derive(mind)
]]

local AnimalMind = {}

AnimalMind.ATTRIBUTES = { "fear", "trust", "stress", "pain", "energy", "curiosity", "comfort", "sociability" }

-- Relaxation rate toward baseline (fraction of the gap closed per second).
local RELAX = {
	fear = 0.04,
	trust = 0.005, -- trust earned in a visit mostly sticks
	stress = 0.06,
	pain = 0.02,
	energy = 0.01,
	curiosity = 0.05,
	comfort = 0.03,
	sociability = 0.01,
}

local function clamp01(x: number): number
	return if x < 0 then 0 elseif x > 1 then 1 else x
end

local function lerp(a: number, b: number, t: number): number
	return a + (b - a) * t
end

function AnimalMind.new(temperament, conditionMods)
	local baseline = {}
	for _, key in AnimalMind.ATTRIBUTES do
		baseline[key] = clamp01((temperament[key] or 0.5) + ((conditionMods and conditionMods[key]) or 0))
	end
	local state = {}
	for key, value in baseline do
		state[key] = value
	end
	-- Arriving at a vet is mildly scary for everyone.
	state.fear = clamp01(state.fear + 0.1)
	state.stress = clamp01(state.stress + 0.1)
	return { state = state, baseline = baseline, lastStimulus = nil }
end

-- Apply a change to one attribute with clamping.
local function add(mind, key: string, delta: number)
	mind.state[key] = clamp01(mind.state[key] + delta)
end

-- How receptive the animal is right now to friendly handling (0 = will reject, 1 = loves it).
function AnimalMind.receptivity(mind): number
	local s = mind.state
	return clamp01(0.55 + s.trust * 0.6 + s.sociability * 0.2 - s.fear * 0.7 - s.stress * 0.35 - s.pain * 0.25)
end

--[[
	Stimuli. intensity defaults to 1. Returns a reaction tag the behaviour/animation layer can
	play (e.g. "Lean", "PullAway", "Startle", "Flinch", "Purr", "Hiss", "Eat").
]]
local STIMULI = {}

function STIMULI.Pet(mind, k)
	local r = AnimalMind.receptivity(mind)
	if r < 0.35 then
		add(mind, "stress", 0.08 * k)
		add(mind, "fear", 0.03 * k)
		add(mind, "trust", 0.01 * k) -- even rejected gentleness counts a little
		return "PullAway"
	end
	add(mind, "trust", 0.04 * k)
	add(mind, "comfort", 0.06 * k)
	add(mind, "stress", -0.07 * k)
	add(mind, "fear", -0.05 * k)
	return if r > 0.7 then "Lean" else "Accept"
end

function STIMULI.Comfort(mind, k) -- soft voice / slow approach / crouching
	add(mind, "fear", -0.06 * k)
	add(mind, "stress", -0.06 * k)
	add(mind, "trust", 0.02 * k)
	return "Calm"
end

function STIMULI.Treat(mind, k)
	if mind.state.pain > 0.7 or mind.state.fear > 0.85 then
		add(mind, "trust", 0.01 * k)
		return "Ignore"
	end
	add(mind, "trust", 0.07 * k)
	add(mind, "comfort", 0.05 * k)
	add(mind, "fear", -0.08 * k)
	add(mind, "stress", -0.05 * k)
	add(mind, "curiosity", 0.05 * k)
	return "Eat"
end

function STIMULI.Brush(mind, k)
	local tag = STIMULI.Pet(mind, k * 0.8)
	if tag ~= "PullAway" then
		add(mind, "comfort", 0.03 * k)
	end
	return tag
end

function STIMULI.LoudNoise(mind, k)
	add(mind, "fear", 0.12 * k * (1.2 - mind.state.comfort))
	add(mind, "stress", 0.1 * k)
	return "Startle"
end

function STIMULI.Bark(mind, k) -- another animal barking nearby
	local sensitivity = 0.4 + mind.state.fear
	add(mind, "fear", 0.06 * k * sensitivity)
	add(mind, "stress", 0.05 * k * sensitivity)
	add(mind, "curiosity", 0.04 * k)
	return if mind.state.fear > 0.5 then "Startle" else "LookToward"
end

function STIMULI.OwnerNear(mind, k)
	add(mind, "fear", -0.02 * k)
	add(mind, "stress", -0.02 * k)
	add(mind, "comfort", 0.02 * k)
	return nil
end

function STIMULI.OwnerAway(mind, k)
	add(mind, "stress", 0.03 * k * (0.5 + mind.state.sociability))
	add(mind, "comfort", -0.02 * k)
	return "LookForOwner"
end

function STIMULI.StrangerApproach(mind, k)
	local s = mind.state
	if s.sociability > 0.7 and s.fear < 0.4 then
		add(mind, "curiosity", 0.05 * k)
		return "Greet"
	end
	add(mind, "fear", 0.04 * k)
	add(mind, "stress", 0.04 * k)
	return if s.fear > 0.6 then "BackAway" else "Wary"
end

function STIMULI.PickedUp(mind, k)
	local r = AnimalMind.receptivity(mind)
	add(mind, "stress", (0.1 - r * 0.12) * k)
	if r < 0.3 then
		add(mind, "fear", 0.05 * k)
		return "Struggle"
	end
	return "Settle"
end

-- A medical touch. k = how invasive (stethoscope 0.3, thermometer 0.6, otoscope 0.7, wound 0.9).
function STIMULI.Procedure(mind, k)
	local s = mind.state
	add(mind, "stress", 0.05 * k * (1.3 - s.trust))
	add(mind, "fear", 0.02 * k * (1 - s.trust))
	if s.pain > 0.5 and k > 0.6 then
		add(mind, "stress", 0.05 * k)
		return "Flinch"
	end
	return if AnimalMind.receptivity(mind) < 0.3 then "PullAway" else "Tolerate"
end

function STIMULI.PainfulTouch(mind, k)
	add(mind, "stress", 0.12 * k)
	add(mind, "fear", 0.05 * k)
	add(mind, "trust", -0.02 * k)
	return "Yelp"
end

function STIMULI.Relief(mind, k) -- a treatment that actually helps
	add(mind, "pain", -0.35 * k)
	add(mind, "stress", -0.12 * k)
	add(mind, "comfort", 0.12 * k)
	add(mind, "trust", 0.05 * k)
	-- the condition is resolving, so its baseline moves too
	mind.baseline.pain = clamp01(mind.baseline.pain - 0.35 * k)
	mind.baseline.energy = clamp01(mind.baseline.energy + 0.1 * k)
	return "Relax"
end

function STIMULI.Reunite(mind, k)
	add(mind, "stress", -0.25 * k)
	add(mind, "fear", -0.2 * k)
	add(mind, "comfort", 0.2 * k)
	return "Excited"
end

AnimalMind.STIMULI = {}
for name in STIMULI do
	AnimalMind.STIMULI[name] = true
end

function AnimalMind.stimulus(mind, kind: string, intensity: number?): string?
	local fn = STIMULI[kind]
	if not fn then
		error("unknown stimulus " .. tostring(kind))
	end
	local tag = fn(mind, intensity or 1)
	mind.lastStimulus = kind
	return tag
end

function AnimalMind.tick(mind, dt: number)
	local s, b = mind.state, mind.baseline
	for key, rate in RELAX do
		local t = 1 - math.exp(-rate * dt)
		s[key] = lerp(s[key], b[key], t)
	end
	-- Stress is also driven by fear, pain and discomfort.
	local implied = clamp01(s.fear * 0.6 + s.pain * 0.5 + (1 - s.comfort) * 0.2)
	s.stress = lerp(s.stress, math.max(s.stress, implied), 1 - math.exp(-0.15 * dt))
	-- Being stressed is tiring; resting while comfortable restores energy slowly.
	s.energy = clamp01(s.energy - s.stress * 0.002 * dt)
end

--[[
	Derived animation + behaviour parameters. All smooth functions of state so that blending
	on the client never pops.
	  tailWag       0..1   wag speed (0 = still)
	  tailHeight   -1..1   tucked .. high
	  earPose      -1..1   flat/back .. forward/alert
	  tremble       0..1
	  pant          0..1
	  breathRate    breaths/min multiplier (1 = resting normal)
	  blinkInterval seconds between blinks (stressed animals blink less)
	  gaitScale     0.4..1.1 multiplier on chosen gait speed
	  limp          0..1   (from pain, only when injuredLeg is set by the case)
	  headHeight   -1..1   low/lowered .. proud
	  cooperation   0..1   chance-weight that a procedure step goes smoothly
	  wantsHide     bool
	  willApproach  bool
	  purr          0..1   (cats)
]]
function AnimalMind.derive(mind)
	local s = mind.state
	local positive = clamp01(s.comfort * 0.6 + s.trust * 0.4 + s.sociability * 0.3 - s.fear * 0.6 - s.pain * 0.4)
	local p = {}
	p.tailWag = clamp01(positive * (0.4 + s.energy * 0.8))
	p.tailHeight = math.clamp(positive * 1.4 - s.fear * 1.2 - s.pain * 0.4, -1, 1)
	p.earPose = math.clamp(s.curiosity * 0.8 + positive * 0.4 - s.fear * 1.3 - s.pain * 0.3, -1, 1)
	p.tremble = clamp01((s.fear - 0.5) * 2)
	p.pant = clamp01(s.stress * 0.9 + (s.energy > 0.8 and 0.2 or 0) - 0.15)
	p.breathRate = 1 + s.stress * 0.8 + s.pain * 0.3 - (1 - s.energy) * 0.15
	p.blinkInterval = 3 + s.stress * 4 - s.comfort * 1.2
	p.gaitScale = math.clamp(0.45 + s.energy * 0.6 - s.pain * 0.3, 0.4, 1.1)
	p.limp = clamp01(s.pain * 1.3 - 0.1)
	p.headHeight = math.clamp(s.energy * 0.8 + positive * 0.5 - s.pain * 0.6 - s.fear * 0.5 - 0.3, -1, 1)
	p.cooperation = clamp01(AnimalMind.receptivity(mind) * 0.8 + s.comfort * 0.2)
	p.wantsHide = s.fear > 0.65 and s.trust < 0.5
	p.willApproach = s.fear < 0.5 and (s.sociability + s.curiosity) * 0.5 > 0.45
	p.purr = clamp01((s.comfort - 0.55) * 2.5 - s.fear)
	p.sleepy = clamp01((0.35 - s.energy) * 3 - s.stress)
	return p
end

-- Compact snapshot for replication (rounded to 2 dp to keep attribute churn down).
function AnimalMind.snapshot(mind)
	local out = {}
	for key, value in mind.state do
		out[key] = math.floor(value * 100 + 0.5) / 100
	end
	return out
end

return AnimalMind
