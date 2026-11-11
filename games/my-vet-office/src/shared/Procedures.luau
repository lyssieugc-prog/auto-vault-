--[[
	Procedures — every exam and treatment as a sequence of PHYSICAL steps. Pure + server-side.

	No loading bars and no "hold E": each step needs the player to do something specific, and the
	server checks it with its own clock:
	  open     open a cabinet / drawer / fridge (target)
	  take     pick up a specific tool
	  approach stand close to the patient (server-measured distance)
	  pose     the patient must be settled in a pose (vet asks; PoseGraph animates it)
	  place    put the instrument on landmark points and HOLD it there (stethoscope, thermometer)
	  scan     magnified view: pan to find abnormal spots (otoscope, coat check)
	  stroke   rub/clean an area until enough of it is covered (wound, ear canal)
	  wrap     wind a bandage around the limb N turns
	  pull     slow, steady pull (tick removal) — too fast fails
	  dose     set the right amount on a syringe / dropper (weight-based target)
	  wait     a real timer (thermometer beep, lab run)
	  record   write the findings into the patient chart
	The animal is never frozen: every touch is a stimulus to AnimalMind, and an uncooperative
	animal PULLS AWAY (progress on the current point resets) until the player calms it.

	local run = Procedures.start("Stethoscope", { patient = patient, now = clock, rng = rng })
	local r = Procedures.input(run, "open", { target = "EquipmentCabinet" }, ctx)
	-- r = { ok, event?, message?, step, progress, done, reading? }
	ctx = { mind, vetDist, pose, now }
]]

local function import(name: string)
	if script then
		return require(script.Parent:WaitForChild(name))
	end
	return require("./" .. name)
end

local AnimalMind = import("AnimalMind")
local Cases = import("Cases")

local Procedures = {}

-- Regions for stroke/scan steps in normalised body coords (see Cases.landmarks).
local function regionAround(landmark: string, size: number)
	local l = Cases.landmarks[landmark]
	return { u0 = l.u - size, u1 = l.u + size, v0 = l.v - size, v1 = l.v + size, side = l.side }
end

Procedures.defs = {
	VisualCheck = {
		steps = {
			{ kind = "approach", maxDist = 10 },
			{ kind = "wait", seconds = 2, label = "Watch how the patient stands and moves" },
			{ kind = "record" },
		},
	},
	Stethoscope = {
		steps = {
			{ kind = "open", target = "EquipmentCabinet" },
			{ kind = "take", tool = "Stethoscope" },
			{ kind = "approach", maxDist = 5 },
			{ kind = "place", points = { "Heart", "LungL", "LungR" }, hold = 2.5, invasive = 0.3 },
			{ kind = "record" },
		},
	},
	Thermometer = {
		steps = {
			{ kind = "open", target = "Drawer" },
			{ kind = "take", tool = "Thermometer" },
			{ kind = "approach", maxDist = 5 },
			{ kind = "pose", pose = "Stand" },
			{ kind = "place", points = { "Flank" }, hold = 1, invasive = 0.6 },
			{ kind = "wait", seconds = 5, label = "Wait for the beep", keepPlaced = true },
			{ kind = "record" },
		},
	},
	Otoscope = {
		steps = {
			{ kind = "take", tool = "Otoscope" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "pose", pose = "Sit" },
			{ kind = "scan", source = "Otoscope", sides = { "L", "R" }, minCoverage = 0.55, invasive = 0.7 },
			{ kind = "record" },
		},
	},
	FurCheck = {
		steps = {
			{ kind = "open", target = "Drawer" },
			{ kind = "take", tool = "Comb" },
			{ kind = "approach", maxDist = 5 },
			{ kind = "scan", source = "FurCheck", sides = { "L", "R" }, minCoverage = 0.5, invasive = 0.2 },
			{ kind = "record" },
		},
	},
	Palpate = {
		steps = {
			{ kind = "approach", maxDist = 4 },
			{ kind = "pose", pose = "Stand" },
			{ kind = "place", points = { "Abdomen" }, hold = 2, invasive = 0.5 },
			{ kind = "record" },
		},
	},
	Vaccinate = {
		steps = {
			{ kind = "open", target = "Fridge" },
			{ kind = "take", tool = "Vaccine" },
			{ kind = "dose", target = 1.0, tolerance = 0.1, unit = "ml" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "place", points = { "Scruff" }, hold = 1, invasive = 0.6 },
			{ kind = "record" },
		},
	},
	CleanEar = {
		steps = {
			{ kind = "open", target = "MedCabinet" },
			{ kind = "take", tool = "EarCleaner" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "pose", pose = "Sit" },
			{ kind = "stroke", region = "Ear", coverage = 0.8, invasive = 0.6 },
			{ kind = "record" },
		},
	},
	EarDrops = {
		steps = {
			{ kind = "take", tool = "EarDrops" },
			{ kind = "dose", target = 4, tolerance = 0, unit = "drops", integer = true },
			{ kind = "place", points = { "Ear" }, hold = 1, invasive = 0.4 },
			{ kind = "stroke", region = "Ear", coverage = 0.5, invasive = 0.2, label = "Massage the ear base" },
			{ kind = "record" },
		},
	},
	SpotOn = {
		steps = {
			{ kind = "take", tool = "SpotOn" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "place", points = { "Scruff" }, hold = 1.5, invasive = 0.2 },
			{ kind = "record" },
		},
	},
	Administer = {
		steps = {
			{ kind = "open", target = "MedCabinet" },
			{ kind = "take", tool = "Medicine" },
			{ kind = "dose", weightBased = true, mlPerLb = 0.1, tolerance = 0.15, unit = "ml" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "place", points = { "Mouth" }, hold = 1.5, invasive = 0.4 },
			{ kind = "record" },
		},
	},
	CleanWound = {
		steps = {
			{ kind = "open", target = "MedCabinet" },
			{ kind = "take", tool = "Antiseptic" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "pose", pose = "Sit" },
			{ kind = "stroke", region = "Injury", coverage = 0.85, invasive = 0.9 },
			{ kind = "record" },
		},
	},
	Bandage = {
		steps = {
			{ kind = "open", target = "Drawer" },
			{ kind = "take", tool = "Bandage" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "wrap", turns = 3, invasive = 0.4 },
			{ kind = "place", points = { "Injury" }, hold = 0.6, invasive = 0.2, label = "Secure the end" },
			{ kind = "record" },
		},
	},
	RemoveTicks = {
		steps = {
			{ kind = "open", target = "Drawer" },
			{ kind = "take", tool = "TickTool" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "pull", distance = 1, maxSpeed = 2.5, invasive = 0.5 },
			{ kind = "record" },
		},
	},
	Fluids = {
		steps = {
			{ kind = "open", target = "MedCabinet" },
			{ kind = "take", tool = "FluidBag" },
			{ kind = "dose", weightBased = true, mlPerLb = 5, tolerance = 0.2, unit = "ml" },
			{ kind = "approach", maxDist = 4 },
			{ kind = "place", points = { "Scruff" }, hold = 3, invasive = 0.6 },
			{ kind = "wait", seconds = 4, label = "Let the fluids run", keepPlaced = true },
			{ kind = "record" },
		},
	},
}

local GRID = 6 -- stroke/scan coverage grid resolution per side

local function resolvePoint(run, name: string): string
	-- "Ear" / "Injury" resolve per patient
	if name == "Ear" then
		return "Ear" .. (run.patient.affectedEar or "L")
	elseif name == "Injury" then
		local leg = run.patient.injury and run.patient.injury.leg or "FL"
		return "Paw" .. leg
	end
	return name
end

local function landmarkFor(run, name: string)
	return Cases.landmarks[resolvePoint(run, name)]
end

local function regionFor(run, name: string)
	if name == "Ear" then
		return regionAround(resolvePoint(run, "Ear"), 0.08)
	elseif name == "Injury" then
		return regionAround(resolvePoint(run, "Injury"), 0.07)
	end
	return { u0 = 0.05, u1 = 0.95, v0 = 0.05, v1 = 0.95, side = "L" }
end

local function validPoint(p): boolean
	return type(p) == "table"
		and type(p.u) == "number"
		and type(p.v) == "number"
		and p.u == p.u
		and p.v == p.v
		and p.u >= -0.2
		and p.u <= 1.2
		and p.v >= -0.2
		and p.v <= 1.2
		and (p.side == nil or p.side == "L" or p.side == "R" or p.side == "C")
end

local function near(p, l): boolean
	if l.side ~= "C" and p.side and p.side ~= l.side then
		return false
	end
	local du, dv = p.u - l.u, p.v - l.v
	return du * du + dv * dv <= l.radius * l.radius
end

function Procedures.start(id: string, opts)
	local def = Procedures.defs[id]
	assert(def, "unknown procedure " .. tostring(id))
	return {
		id = id,
		def = def,
		patient = opts.patient,
		rng = opts.rng or math.random,
		stepIndex = 1,
		stepStart = opts.now,
		state = {},
		results = {},
		done = false,
		pullAways = 0,
	}
end

function Procedures.currentStep(run)
	return run.def.steps[run.stepIndex]
end

local function advance(run, now: number)
	run.stepIndex += 1
	run.stepStart = now
	run.state = {}
	if run.stepIndex > #run.def.steps then
		run.done = true
	end
end

-- Roll whether the animal tolerates this touch. Applies the stimulus either way.
local function touch(run, mind, invasive: number): (boolean, string?)
	if not mind then
		return true, nil
	end
	local reaction = AnimalMind.stimulus(mind, "Procedure", invasive)
	local params = AnimalMind.derive(mind)
	local threshold = math.clamp(params.cooperation + 0.35 - invasive * 0.2, 0.05, 0.98)
	if reaction == "PullAway" or run.rng() > threshold then
		run.pullAways += 1
		return false, reaction
	end
	return true, reaction
end

-- Readings produced when a place step completes on a landmark.
local function readingFor(run, landmarkName: string, mind)
	local p = run.patient
	if run.id == "Stethoscope" then
		local findings = p.case.findings.Stethoscope or { sounds = {} }
		local sound = findings.sounds[landmarkName] or "Clear"
		local stress = if mind then mind.state.stress else 0
		if landmarkName == "Heart" then
			-- stressed patients read high: calming first gives an accurate number
			local bpm = math.floor(p.vitals.heartRate + stress * 35 + 0.5)
			return { point = landmarkName, sound = sound, heartRate = bpm, stressed = stress > 0.45 }
		end
		local rr = math.floor(p.vitals.respRate + stress * 10 + 0.5)
		return { point = landmarkName, sound = sound, respRate = rr }
	elseif run.id == "Palpate" then
		local f = p.case.findings.Palpate
		local tender = f and f.tender and table.find(f.tender, landmarkName) ~= nil
		if tender and mind then
			AnimalMind.stimulus(mind, "PainfulTouch", 0.6)
		end
		return { point = landmarkName, tender = tender or false, note = tender and f.note or "Soft, not painful" }
	end
	return { point = landmarkName }
end

local HANDLERS = {}

function HANDLERS.open(run, step, action, payload)
	if action ~= "open" then
		return { ok = false, message = "Open the " .. step.target .. " first" }
	end
	if type(payload) ~= "table" or payload.target ~= step.target then
		return { ok = false, message = "That's not where this is kept" }
	end
	return { ok = true, advance = true, event = "Opened" }
end

function HANDLERS.take(run, step, action, payload)
	if action ~= "take" then
		return { ok = false, message = "Pick up the " .. step.tool }
	end
	if type(payload) ~= "table" or payload.tool ~= step.tool then
		return { ok = false, message = "Wrong tool" }
	end
	return { ok = true, advance = true, event = "Took" }
end

function HANDLERS.approach(run, step, action, payload, ctx)
	if (ctx.vetDist or math.huge) <= step.maxDist then
		return { ok = true, advance = true }
	end
	return { ok = false, message = "Move closer to the patient" }
end

function HANDLERS.pose(run, step, action, payload, ctx)
	if action == "requestPose" then
		run.requestedPose = step.pose
	end
	if ctx.pose == step.pose then
		return { ok = true, advance = true }
	end
	return { ok = action == "requestPose", event = "PoseRequested", requestedPose = step.pose }
end

function HANDLERS.place(run, step, action, payload, ctx)
	local st = run.state
	st.done = st.done or {}
	if action == "release" then
		st.holding = nil
		return { ok = true }
	end
	if action ~= "place" or not validPoint(payload) then
		return { ok = false, message = "Place the instrument on the patient" }
	end
	-- which remaining point is this on?
	local hit = nil
	for _, name in step.points do
		local resolved = resolvePoint(run, name)
		if not st.done[resolved] and near(payload, landmarkFor(run, name)) then
			hit = resolved
			break
		end
	end
	if not hit then
		st.holding = nil
		return { ok = false, event = "Miss", message = "Not quite — find the right spot" }
	end
	if not st.holding or st.holding.point ~= hit then
		local tolerated, reaction = touch(run, ctx.mind, step.invasive or 0.3)
		if not tolerated then
			st.holding = nil
			return { ok = false, event = "PulledAway", reaction = reaction, message = "The patient pulled away" }
		end
		st.holding = { point = hit, since = ctx.now }
		return { ok = true, event = "Placed", reaction = reaction }
	end
	-- continuing a hold: occasional fidget checks scaled by time held
	if ctx.mind and ctx.mind.state.stress > 0.75 and run.rng() < 0.25 then
		st.holding = nil
		run.pullAways += 1
		return { ok = false, event = "PulledAway", reaction = "PullAway", message = "The patient wriggled away" }
	end
	if ctx.now - st.holding.since >= step.hold then
		st.done[hit] = true
		local reading = readingFor(run, hit, ctx.mind)
		run.results[hit] = reading
		st.holding = if step.keepPlaced then st.holding else nil
		local remaining = 0
		for _, name in step.points do
			if not st.done[resolvePoint(run, name)] then
				remaining += 1
			end
		end
		return { ok = true, event = "PointDone", reading = reading, advance = remaining == 0 }
	end
	return { ok = true, event = "Holding", progress = (ctx.now - st.holding.since) / step.hold }
end

local function cellOf(region, p): number?
	if p.u < region.u0 or p.u > region.u1 or p.v < region.v0 or p.v > region.v1 then
		return nil
	end
	local cu = math.min(GRID - 1, math.floor((p.u - region.u0) / (region.u1 - region.u0) * GRID))
	local cv = math.min(GRID - 1, math.floor((p.v - region.v0) / (region.v1 - region.v0) * GRID))
	return cv * GRID + cu
end

function HANDLERS.stroke(run, step, action, payload, ctx)
	local st = run.state
	st.cells = st.cells or {}
	st.count = st.count or 0
	if action ~= "stroke" or type(payload) ~= "table" or type(payload.points) ~= "table" then
		return { ok = false, message = step.label or "Rub over the area" }
	end
	if #payload.points > 32 then
		return { ok = false, message = "too many samples" }
	end
	local region = regionFor(run, step.region)
	-- one tolerance roll per stroke batch
	local tolerated, reaction = touch(run, ctx.mind, (step.invasive or 0.5) * 0.5)
	if not tolerated then
		return { ok = false, event = "PulledAway", reaction = reaction, message = "The patient pulled away" }
	end
	local last = st.last
	for _, p in payload.points do
		if validPoint(p) then
			-- anti-teleport: samples must be continuous
			if last and math.abs(p.u - last.u) + math.abs(p.v - last.v) > 0.25 then
				last = p
				continue
			end
			last = p
			local cell = cellOf(region, p)
			if cell and not st.cells[cell] then
				st.cells[cell] = true
				st.count += 1
			end
		end
	end
	st.last = last
	local coverage = st.count / (GRID * GRID)
	if coverage >= step.coverage then
		run.results.strokeCoverage = coverage
		return { ok = true, event = "Covered", progress = 1, advance = true, reaction = reaction }
	end
	return { ok = true, event = "Stroking", progress = coverage / step.coverage, reaction = reaction }
end

local function scanSpots(run, step, side: string)
	local findings = run.patient.case.findings[step.source]
	if step.source == "Otoscope" then
		return (findings and findings[side]) or {}
	end
	local out = {}
	for _, spot in (findings and findings.spots) or {} do
		local s = spot
		if spot.landmark then
			local l = Cases.landmarks[spot.landmark]
			s = { id = spot.id, u = l.u, v = l.v, side = l.side, note = spot.note }
		end
		if (s.side or "L") == side then
			table.insert(out, s)
		end
	end
	return out
end

function HANDLERS.scan(run, step, action, payload, ctx)
	local st = run.state
	st.sides = st.sides or {}
	if action == "finishScan" then
		for _, side in step.sides do
			local s = st.sides[side]
			if not s or (s.count / (GRID * GRID) < step.minCoverage and s.foundAll ~= true) then
				return { ok = false, message = "Look over every side properly first (" .. side .. ")" }
			end
		end
		local found = {}
		for _, side in step.sides do
			for id, spot in st.sides[side].found do
				table.insert(found, { id = id, side = side, note = spot.note })
			end
		end
		table.sort(found, function(a, b)
			return a.side .. a.id < b.side .. b.id
		end)
		run.results.found = found
		return { ok = true, advance = true, event = "ScanDone", found = found }
	end
	if action ~= "scan" or not validPoint(payload) or not table.find(step.sides, payload.side) then
		return { ok = false, message = "Look closely at the patient" }
	end
	local side = payload.side
	local s = st.sides[side]
	if not s then
		s = { cells = {}, count = 0, found = {}, dwell = nil, foundAll = false }
		st.sides[side] = s
		local tolerated, reaction = touch(run, ctx.mind, step.invasive or 0.4)
		if not tolerated then
			st.sides[side] = nil
			return { ok = false, event = "PulledAway", reaction = reaction, message = "The patient pulled away" }
		end
	end
	local cell = cellOf({ u0 = 0, u1 = 1, v0 = 0, v1 = 1 }, payload)
	if cell and not s.cells[cell] then
		s.cells[cell] = true
		s.count += 1
	end
	-- dwell on a spot for 0.5 s to "notice" it
	local spots = scanSpots(run, step, side)
	local over = nil
	for _, spot in spots do
		local du, dv = payload.u - spot.u, payload.v - spot.v
		if du * du + dv * dv <= 0.09 * 0.09 then
			over = spot
			break
		end
	end
	local event = "Scanning"
	local discovered = nil
	if over and not s.found[over.id] then
		if s.dwell and s.dwell.id == over.id then
			if ctx.now - s.dwell.since >= 0.5 then
				s.found[over.id] = over
				discovered = over
				event = "Found"
			end
		else
			s.dwell = { id = over.id, since = ctx.now }
		end
	else
		s.dwell = nil
	end
	local foundCount = 0
	for _ in s.found do
		foundCount += 1
	end
	s.foundAll = #spots > 0 and foundCount == #spots
	return { ok = true, event = event, discovered = discovered, progress = s.count / (GRID * GRID) }
end

function HANDLERS.wrap(run, step, action, payload, ctx)
	local st = run.state
	st.angle = st.angle or 0
	if
		action ~= "wrap"
		or type(payload) ~= "table"
		or type(payload.delta) ~= "number"
		or payload.delta ~= payload.delta
	then
		return { ok = false, message = "Wrap the bandage around the leg" }
	end
	local delta = math.clamp(payload.delta, 0, math.pi / 2) -- per-input cap (no instant wraps)
	if not st.lastTime or ctx.now - st.lastTime >= 0.05 then
		st.angle += delta
		st.lastTime = ctx.now
	end
	if not st.touched then
		st.touched = true
		local tolerated, reaction = touch(run, ctx.mind, step.invasive or 0.4)
		if not tolerated then
			st.angle = 0
			st.touched = false
			return { ok = false, event = "PulledAway", reaction = reaction }
		end
	end
	local turns = st.angle / (2 * math.pi)
	if turns >= step.turns then
		run.results.turns = turns
		return { ok = true, advance = true, event = "Wrapped", progress = 1 }
	end
	return { ok = true, event = "Wrapping", progress = turns / step.turns }
end

function HANDLERS.pull(run, step, action, payload, ctx)
	local st = run.state
	if not st.targets then
		st.targets = {}
		for _, spot in scanSpots(run, { source = "FurCheck" }, "L") do
			table.insert(st.targets, spot.id)
		end
		for _, spot in scanSpots(run, { source = "FurCheck" }, "R") do
			table.insert(st.targets, spot.id)
		end
		st.index = 1
		st.progress = 0
		run.results.removed = {}
		if #st.targets == 0 then
			return { ok = true, advance = true }
		end
	end
	if action ~= "pull" or type(payload) ~= "table" then
		return { ok = false, message = "Grip and pull slowly" }
	end
	local dist, dt = payload.distance, payload.dt
	if not (type(dist) == "number" and type(dt) == "number" and dist == dist and dt == dt and dt > 0 and dt <= 1) then
		return { ok = false }
	end
	dist = math.clamp(dist, 0, 0.5)
	if dist / dt > step.maxSpeed then
		st.progress = 0
		return { ok = false, event = "TooFast", message = "Too fast! Slow and steady." }
	end
	if st.progress == 0 then
		local tolerated, reaction = touch(run, ctx.mind, step.invasive or 0.5)
		if not tolerated then
			return { ok = false, event = "PulledAway", reaction = reaction }
		end
	end
	st.progress += dist
	if st.progress >= step.distance then
		table.insert(run.results.removed, st.targets[st.index])
		st.index += 1
		st.progress = 0
		if st.index > #st.targets then
			return { ok = true, advance = true, event = "AllRemoved" }
		end
		return { ok = true, event = "Removed", progress = (st.index - 1) / #st.targets }
	end
	return { ok = true, event = "Pulling", progress = st.progress / step.distance }
end

function Procedures.doseTarget(run, step): number
	if step.weightBased then
		return math.floor(run.patient.weightLb * step.mlPerLb * 10 + 0.5) / 10
	end
	return step.target
end

function HANDLERS.dose(run, step, action, payload)
	if
		action ~= "dose"
		or type(payload) ~= "table"
		or type(payload.value) ~= "number"
		or payload.value ~= payload.value
	then
		return { ok = false, message = "Set the dose" }
	end
	local target = Procedures.doseTarget(run, step)
	local tol = if step.integer then 0 else math.max(step.tolerance * target, 0.05)
	if math.abs(payload.value - target) <= tol + 1e-9 then
		run.results.dose = payload.value
		return { ok = true, advance = true, event = "DoseSet" }
	end
	return {
		ok = false,
		event = "WrongDose",
		message = if payload.value > target then "That's too much" else "That's not enough",
	}
end

function HANDLERS.wait(run, step, action, payload, ctx)
	if ctx.now - run.stepStart >= step.seconds then
		if run.id == "Thermometer" then
			local noise = (run.rng() - 0.5) * 0.2
			run.results.tempF = math.floor((run.patient.vitals.tempF + noise) * 10 + 0.5) / 10
		end
		return { ok = true, advance = true, event = "Beep" }
	end
	return { ok = true, event = "Waiting", progress = (ctx.now - run.stepStart) / step.seconds }
end

function HANDLERS.record(run, step, action)
	if action ~= "record" then
		return { ok = false, message = "Record your findings in the chart" }
	end
	if run.id == "VisualCheck" then
		run.results.note = run.patient.case.findings.Visual
		run.results.limping = run.patient.injury ~= nil
	end
	return { ok = true, advance = true, event = "Recorded" }
end

--[[
	Feed one player action into the run. Unknown actions/payloads are rejected, never trusted.
	Steps that complete on their own (approach, pose, wait) are checked on every input, so the
	server glue just calls Procedures.input(run, "tick", nil, ctx) periodically.
]]
function Procedures.input(run, action: string, payload, ctx)
	if run.done then
		return { ok = false, done = true, message = "Already finished" }
	end
	local step = Procedures.currentStep(run)
	local handler = HANDLERS[step.kind]
	local r = handler(run, step, action, payload, ctx)
	r.step = run.stepIndex
	r.kind = step.kind
	if r.advance then
		advance(run, ctx.now)
	end
	r.done = run.done
	if run.done then
		r.results = run.results
	end
	return r
end

-- Steps for the UI (labels + kinds) without exposing hidden findings.
function Procedures.describe(id: string)
	local out = {}
	for i, step in Procedures.defs[id].steps do
		out[i] = { kind = step.kind, label = step.label, target = step.target, tool = step.tool, pose = step.pose }
	end
	return out
end

return Procedures
