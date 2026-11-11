--[[
	GameLogic — My Vet Office rules, built from Config + game modules + vault systems. Pure:
	clocks/rng are injected, so tests/run.luau drives complete appointments under Lune and the
	server Main script only wires Roblox events + world sensing to these methods.

	One clinic per owner (the player whose server/plot it is). Friends join as members with a
	role; every action checks the role's permission (Clinic.PERMISSIONS) and every value comes
	from the server's own state — client args are only ids/choices, validated here.

	local logic = GameLogic.new(Config, { Tutorial = … }, { now = os.clock, rng = fn })
	logic:loadPlayer(ownerId, profile)                     -- creates/loads the clinic
	local appt = logic:spawnPatient(ownerId)               -- or automatic via logic:tick
	logic:checkIn(ownerId, userId, apptId) … logic:pay(ownerId, userId, apptId)
	logic:tickAnimals(ownerId, dt, sense)                   -- 5 Hz: minds + behaviours
]]

local function import(name: string)
	if script then
		return require(script.Parent:WaitForChild(name))
	end
	return require("./" .. name)
end

local AnimalBehavior = import("AnimalBehavior")
local AnimalMind = import("AnimalMind")
local Appointment = import("Appointment")
local Cases = import("Cases")
local Clinic = import("Clinic")
local Procedures = import("Procedures")
local Species = import("Species")

local GameLogic = {}
GameLogic.__index = GameLogic

GameLogic.Modules = {
	AnimalBehavior = AnimalBehavior,
	AnimalMind = AnimalMind,
	Appointment = Appointment,
	Cases = Cases,
	Clinic = Clinic,
	Procedures = Procedures,
	Species = Species,
}

GameLogic.TABLE_PHASES = { OnTable = true, Exam = true, Diagnosed = true, Treatment = true, Treated = true }
GameLogic.EXAM_POSES = { "Stand", "Sit", "LieSternal", "LieLateral" }

function GameLogic.profileTemplate(M)
	return {
		clinic = {},
		tutorial = M.Tutorial.newState(),
		stats = { patients = 0, correct = 0 },
	}
end

function GameLogic.new(Config, M, deps)
	deps = deps or {}
	local self = setmetatable({}, GameLogic)
	self.Config = Config
	self.M = M
	self.now = deps.now or os.clock
	self.rng = deps.rng or math.random
	local cc = table.clone(Config.clinic)
	cc.supplies = Cases.supplies
	cc.unlocks = Config.unlocks
	cc.rooms = Config.rooms
	cc.catalog = Config.catalog
	cc.finishes = Config.finishes
	cc.staffRoles = Config.staffRoles
	self.clinicConfig = cc
	self.tutorial = M.Tutorial.new(Config.tutorial)
	self.clinics = {}
	self.profiles = {}
	return self
end

---------------------------------------------------------------------------------------------
-- Profiles / clinics
---------------------------------------------------------------------------------------------
local function fail(message: string)
	return { ok = false, message = message }
end

function GameLogic:newClinicState()
	local state = Clinic.newState(self.clinicConfig)
	for _, p in self.Config.startLayout do
		local id = "p" .. state.nextPlacementId
		state.nextPlacementId += 1
		state.placements[id] = { item = p.item, room = p.room, x = p.x, z = p.z, rot = p.rot }
	end
	return state
end

function GameLogic:loadPlayer(ownerId: number, profile)
	if profile.clinic == nil or profile.clinic.name == nil then
		profile.clinic = self:newClinicState()
	else
		-- reconcile new supply ids added in updates
		for id, def in Cases.supplies do
			if profile.clinic.stock[id] == nil then
				profile.clinic.stock[id] = def.start or 0
			end
		end
	end
	self.profiles[ownerId] = profile
	self.clinics[ownerId] = {
		ownerId = ownerId,
		state = profile.clinic,
		members = {},
		appts = {},
		nextApptId = 1,
		arrivalTimer = self.clinicConfig.arrival.firstPatientDelay,
		dayTimer = 0,
		comfortAt = {},
		served = 0,
	}
	return self.clinics[ownerId]
end

function GameLogic:unloadPlayer(ownerId: number)
	self.clinics[ownerId] = nil
	self.profiles[ownerId] = nil
end

function GameLogic:writeProfile(ownerId: number, profile)
	local clinic = self.clinics[ownerId]
	if clinic then
		profile.clinic = clinic.state
	end
end

-- A friend joins someone's clinic as a visitor until the owner gives them a role.
function GameLogic:join(ownerId: number, userId: number)
	local clinic = self.clinics[ownerId]
	if not clinic or userId == ownerId then
		return fail("No clinic")
	end
	clinic.members[userId] = clinic.members[userId] or "Visitor"
	return { ok = true, role = clinic.members[userId] }
end

function GameLogic:leave(ownerId: number, userId: number)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return
	end
	clinic.members[userId] = nil
	for _, appt in clinic.appts do
		Appointment.release(appt, userId)
	end
end

function GameLogic:roleOf(ownerId: number, userId: number): string
	if userId == ownerId then
		return "Owner"
	end
	local clinic = self.clinics[ownerId]
	return (clinic and clinic.members[userId]) or "Visitor"
end

function GameLogic:setRole(ownerId: number, actorId: number, targetId: number, role: string)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return fail("No clinic")
	end
	if not Clinic.can(self:roleOf(ownerId, actorId), "manage") then
		return fail("Only the owner can assign roles")
	end
	if role == "Owner" or not Clinic.PERMISSIONS[role] or clinic.members[targetId] == nil then
		return fail("Bad role")
	end
	clinic.members[targetId] = role
	return { ok = true }
end

-- Resolve clinic + permission for an action.
function GameLogic:_auth(ownerId: number, userId: number, permission: string?)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return nil, fail("No clinic")
	end
	local role = self:roleOf(ownerId, userId)
	if role == "Visitor" and userId ~= ownerId and clinic.members[userId] == nil then
		return nil, fail("Not in this clinic")
	end
	if permission and not Clinic.can(role, permission) then
		return nil, fail("Your role can't do that")
	end
	return clinic, nil
end

function GameLogic:_appt(clinic, apptId: any)
	if type(apptId) ~= "number" then
		return nil
	end
	return clinic.appts[apptId]
end

function GameLogic:_tutorial(ownerId: number, stepId: string)
	local profile = self.profiles[ownerId]
	if profile and profile.tutorial then
		self.tutorial:complete(profile.tutorial, stepId)
	end
end

---------------------------------------------------------------------------------------------
-- Patients
---------------------------------------------------------------------------------------------
local function pickWeighted(rng, entries)
	local total = 0
	for _, e in entries do
		total += e.weight
	end
	local roll = rng() * total
	for _, e in entries do
		roll -= e.weight
		if roll <= 0 then
			return e.value
		end
	end
	return entries[#entries].value
end

local function pick(rng, list)
	return list[math.clamp(math.floor(rng() * #list) + 1, 1, #list)]
end

function GameLogic:activeCount(clinic): number
	local n = 0
	for _, appt in clinic.appts do
		if appt.phase ~= "Done" and appt.phase ~= "WalkedOut" then
			n += 1
		end
	end
	return n
end

function GameLogic:maxActive(clinic): number
	local cc = self.clinicConfig
	return math.floor(cc.maxActiveAppointments + clinic.state.level * cc.arrivalCapPerLevel)
end

--[[
	opts: breed, caseId, emergency, followUp (entry from state.followUps), customerName
	The very first patient of a new clinic is the owner's showcase appointment: a friendly
	golden retriever with kennel cough (stethoscope + thermometer tell the story).
]]
function GameLogic:spawnPatient(ownerId: number, opts)
	opts = opts or {}
	local clinic = self.clinics[ownerId]
	if not clinic then
		return nil
	end
	local state = clinic.state
	local rng = self.rng
	local cfg = self.Config
	local first = state.patientsTreated == 0 and clinic.served == 0 and next(clinic.appts) == nil

	local follow = opts.followUp
	if not follow and not first and #state.followUps > 0 and rng() < self.clinicConfig.followUpChance then
		follow = table.remove(state.followUps, 1)
	end

	local breedName = opts.breed or (follow and follow.breed)
	if not breedName then
		if first then
			breedName = "GoldenRetriever"
		else
			local entries = {}
			for name, lvl in cfg.unlocks.breeds do
				if state.level >= lvl then
					table.insert(entries, { value = name, weight = if name == "GoldenRetriever" then 1.3 else 1 })
				end
			end
			table.sort(entries, function(a, b)
				return a.value < b.value
			end)
			breedName = pickWeighted(rng, entries)
		end
	end
	local breed = Species.breeds[breedName]
	local speciesName = breed.species
	local speciesDef = Species.species[speciesName]

	local caseId = opts.caseId or (follow and follow.caseId)
	if not caseId then
		if first then
			caseId = "KennelCough"
		else
			caseId = pick(rng, Cases.eligible(speciesName, state.level))
		end
	end
	local case = Cases.cases[caseId]

	local petName = (follow and follow.petName) or pick(rng, cfg.customers.petNames[speciesName])
	local personalities = {}
	for name, p in cfg.customers.personalities do
		table.insert(personalities, { value = name, weight = p.weight })
	end
	table.sort(personalities, function(a, b)
		return a.value < b.value
	end)
	local personality = (follow and follow.personality) or pickWeighted(rng, personalities)
	local patience = cfg.customers.personalities[personality].patience
	if opts.emergency then
		patience *= 0.5
	end
	local complaint = string.format(pick(rng, case.complaints), petName)
	if follow then
		complaint = string.format("We're back — %s still isn't right since last time.", petName)
	end

	local w = breed.weightLb
	local patient = {
		name = petName,
		breed = breedName,
		species = speciesName,
		size = breed.size,
		weightLb = (follow and follow.weightLb) or math.floor(w[1] + (w[2] - w[1]) * rng() + 0.5),
		ageYears = (follow and follow.ageYears) or math.floor(1 + rng() * 11),
		coat = pick(rng, breed.coats),
		vitals = Cases.trueVitals(speciesDef, case, rng),
		mind = AnimalMind.new(breed.temperament, case.mind),
		injury = case.injury,
		affectedEar = "L",
		case = case,
		speciesDef = speciesDef,
	}
	local id = clinic.nextApptId
	clinic.nextApptId += 1
	local appt = Appointment.new({
		id = id,
		caseId = caseId,
		case = case,
		patient = patient,
		customer = {
			name = opts.customerName or (follow and follow.customerName) or pick(rng, cfg.customers.firstNames),
			personality = personality,
			patience = patience,
			complaint = complaint,
		},
		now = self.now(),
		rng = rng,
		emergency = opts.emergency,
		followUp = follow ~= nil,
	})
	appt.behavior = AnimalBehavior.new({
		breed = breed,
		species = speciesDef,
		rng = rng,
		inCarrier = speciesName == "Cat",
	})
	appt.carrierOpen = false
	clinic.appts[id] = appt
	return appt
end

-- Waiting list sorted by priority: emergencies first, then follow-ups, then longest wait.
function GameLogic:waitingList(ownerId: number)
	local clinic = self.clinics[ownerId]
	local list = {}
	if not clinic then
		return list
	end
	for _, appt in clinic.appts do
		if appt.phase == "Waiting" or appt.phase == "AtReception" or appt.phase == "Arriving" then
			table.insert(list, appt)
		end
	end
	table.sort(list, function(a, b)
		if a.emergency ~= b.emergency then
			return a.emergency
		end
		if a.followUp ~= b.followUp then
			return a.followUp
		end
		return a.arrivedAt < b.arrivedAt
	end)
	return list
end

---------------------------------------------------------------------------------------------
-- Clinic loop (arrivals, waiting, days). Server calls this ~1 Hz.
---------------------------------------------------------------------------------------------
function GameLogic:tick(ownerId: number, dt: number)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return {}
	end
	local events = {}
	local now = self.now()
	clinic.arrivalTimer -= dt
	if clinic.arrivalTimer <= 0 then
		if self:activeCount(clinic) < self:maxActive(clinic) then
			local emergency = clinic.state.level >= 4 and self.rng() < 0.08
			local appt = self:spawnPatient(ownerId, { emergency = emergency })
			if appt then
				table.insert(events, { kind = "Arrived", id = appt.id, emergency = emergency })
			end
		end
		clinic.arrivalTimer = Clinic.arrivalInterval(self.clinicConfig, clinic.state) * (0.75 + self.rng() * 0.5)
	end
	for id, appt in clinic.appts do
		local mood = Appointment.tickWaiting(appt, now)
		if mood == "leaving" then
			Clinic.addRating(self.clinicConfig, clinic.state, 1)
			table.insert(events, { kind = "WalkedOut", id = id })
		elseif mood == "impatient" and not appt.saidImpatient then
			appt.saidImpatient = true
			table.insert(events, { kind = "Impatient", id = id })
		end
		if appt.phase == "Done" or appt.phase == "WalkedOut" then
			appt.removeIn = (appt.removeIn or 10) - dt
			if appt.removeIn <= 0 then
				clinic.appts[id] = nil
			end
		end
	end
	clinic.dayTimer += dt
	if clinic.dayTimer >= self.clinicConfig.dayLengthSeconds then
		clinic.dayTimer -= self.clinicConfig.dayLengthSeconds
		local result = Clinic.endDay(self.clinicConfig, clinic.state)
		table.insert(events, { kind = "DayEnded", result = result })
	end
	return events
end

--[[
	Animal simulation step for every patient in the clinic (one loop, no per-animal scripts).
	sense(appt) → ctx from the world (distances, POIs, sounds) — provided by the server glue.
	Phase-driven context (leader, onTable, carrier, requested pose) is added here.
]]
function GameLogic:tickAnimals(ownerId: number, dt: number, sense)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return
	end
	for _, appt in clinic.appts do
		local b = appt.behavior
		if b then
			local ctx = (sense and sense(appt)) or {}
			local phase = appt.phase
			ctx.leader = if phase == "Called" or phase == "ToRoom" then "Vet" else "Owner"
			ctx.onTable = GameLogic.TABLE_PHASES[phase] == true
			ctx.inCarrier = appt.patient.species == "Cat" and not appt.carrierOpen and not ctx.onTable
			ctx.carrierOpen = appt.carrierOpen
			ctx.carried = appt.carried == true
			ctx.handled = appt.running ~= nil
			ctx.reunited = (phase == "Paid" or phase == "Leaving") and not appt.reunited
			if ctx.reunited then
				appt.reunited = true
			end
			local running = appt.running
			ctx.requestedPose = (running and running.run.requestedPose) or appt.requestedPose
			AnimalMind.tick(appt.patient.mind, dt)
			appt.anim = AnimalBehavior.tick(b, appt.patient.mind, ctx, dt)
		end
	end
end

---------------------------------------------------------------------------------------------
-- Appointment actions (each validates role + ids)
---------------------------------------------------------------------------------------------
function GameLogic:reachReception(ownerId: number, apptId: number)
	local clinic = self.clinics[ownerId]
	local appt = clinic and self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	return Appointment.reachReception(appt, self.now())
end

function GameLogic:checkIn(ownerId: number, userId: number, apptId: any)
	local clinic, err = self:_auth(ownerId, userId, "checkIn")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	local r = Appointment.checkIn(appt, userId, self.now())
	if r.ok then
		self:_tutorial(ownerId, "CheckIn")
	end
	return r
end

function GameLogic:callPatient(ownerId: number, userId: number, apptId: any, room: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	if type(room) ~= "string" or not clinic.state.rooms[room] or self.Config.rooms[room].kind ~= "Exam" then
		return fail("Pick one of your exam rooms")
	end
	for _, other in clinic.appts do
		if
			other ~= appt
			and other.room == room
			and other.claimedBy
			and other.phase ~= "Done"
			and other.phase ~= "Paid"
			and other.phase ~= "Leaving"
			and other.phase ~= "Checkout"
		then
			return fail("That room is busy")
		end
	end
	local r = Appointment.call(appt, userId, room, self.now())
	if r.ok then
		Appointment.startWalk(appt, self.now())
		self:_tutorial(ownerId, "Call")
	end
	return r
end

function GameLogic:arriveInRoom(ownerId: number, apptId: number)
	local clinic = self.clinics[ownerId]
	local appt = clinic and self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	return Appointment.enterRoom(appt, self.now())
end

function GameLogic:openCarrier(ownerId: number, userId: number, apptId: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or appt.patient.species ~= "Cat" then
		return fail("No carrier")
	end
	appt.carrierOpen = true
	return { ok = true }
end

function GameLogic:helpOntoTable(ownerId: number, userId: number, apptId: any, step: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or type(step) ~= "string" then
		return fail("No such patient")
	end
	local r = Appointment.helpOntoTable(appt, userId, step, self.now(), ownerId)
	appt.carried = r.ok and step == "pickUp"
	if r.event == "OnTable" then
		appt.carried = false
		self:_tutorial(ownerId, "OnTable")
	end
	return r
end

-- Pet / Comfort / Treat / Brush: physical reassurance with a short cooldown.
function GameLogic:comfort(ownerId: number, userId: number, apptId: any, kind: any)
	local clinic, err = self:_auth(ownerId, userId, nil)
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	if kind ~= "Pet" and kind ~= "Comfort" and kind ~= "Treat" and kind ~= "Brush" then
		return fail("Bad action")
	end
	if self:roleOf(ownerId, userId) == "Visitor" then
		return fail("Ask the owner for a role first")
	end
	local key = appt.id .. ":" .. userId
	local now = self.now()
	if clinic.comfortAt[key] and now - clinic.comfortAt[key] < self.clinicConfig.comfortCooldown then
		return fail("Gently…")
	end
	clinic.comfortAt[key] = now
	if kind == "Treat" then
		if not Clinic.consume(clinic.state, { Treats = 1 }) then
			return fail("Out of treats")
		end
	end
	local reaction = AnimalMind.stimulus(appt.patient.mind, kind, 1)
	return { ok = true, reaction = reaction, mind = AnimalMind.snapshot(appt.patient.mind) }
end

function GameLogic:requestPose(ownerId: number, userId: number, apptId: any, pose: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or not table.find(GameLogic.EXAM_POSES, pose) then
		return fail("Bad pose")
	end
	if appt.claimedBy ~= userId and userId ~= ownerId then
		return fail("This isn't your patient")
	end
	appt.requestedPose = pose
	if appt.running then
		appt.running.run.requestedPose = nil
	end
	return { ok = true }
end

function GameLogic:beginExam(ownerId: number, userId: number, apptId: any, examId: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or type(examId) ~= "string" then
		return fail("No such patient")
	end
	if not Clinic.unlocked(self.clinicConfig, clinic.state, "exams", examId) then
		return fail("Not unlocked yet")
	end
	return Appointment.beginExam(appt, userId, examId, self.now(), ownerId)
end

function GameLogic:beginTreatment(ownerId: number, userId: number, apptId: any, treatmentId: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or type(treatmentId) ~= "string" then
		return fail("No such patient")
	end
	if not Clinic.unlocked(self.clinicConfig, clinic.state, "treatments", treatmentId) then
		return fail("Not unlocked yet")
	end
	local t = Cases.treatments[treatmentId]
	local ok, missing = Clinic.hasSupplies(clinic.state, t.supplies)
	if not ok then
		return fail("Out of " .. Cases.supplies[missing].name .. " — order more")
	end
	return Appointment.beginTreatment(appt, userId, treatmentId, self.now(), ownerId)
end

-- vetDist is measured by the server (character ↔ animal), never sent by the client.
function GameLogic:procedureInput(
	ownerId: number,
	userId: number,
	apptId: any,
	action: any,
	payload: any,
	vetDist: number?
)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or type(action) ~= "string" or #action > 20 then
		return fail("No such patient")
	end
	local running = appt.running
	local pose = appt.behavior and appt.behavior.pose.current
	local r = Appointment.procedureInput(
		appt,
		userId,
		action,
		payload,
		{ now = self.now(), vetDist = vetDist, pose = pose },
		ownerId
	)
	if r.done and running then
		if running.kind == "treatment" then
			Clinic.consume(clinic.state, Cases.treatments[running.id].supplies)
			self:_tutorial(ownerId, "Treat")
		else
			self:_tutorial(ownerId, "Exam")
		end
	end
	return r
end

function GameLogic:cancelProcedure(ownerId: number, userId: number, apptId: any)
	local clinic = self.clinics[ownerId]
	local appt = clinic and self:_appt(clinic, apptId)
	if appt then
		Appointment.cancelProcedure(appt, userId, ownerId)
	end
	return { ok = appt ~= nil }
end

function GameLogic:diagnose(ownerId: number, userId: number, apptId: any, diagnosisId: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt or type(diagnosisId) ~= "string" then
		return fail("No such patient")
	end
	local d = Cases.diagnoses[diagnosisId]
	if not d or d.minLevel > clinic.state.level then
		return fail("Unknown diagnosis")
	end
	local r = Appointment.diagnose(appt, userId, diagnosisId, self.now(), ownerId)
	if r.ok then
		self:_tutorial(ownerId, "Diagnose")
	end
	return r
end

function GameLogic:finishVisit(ownerId: number, userId: number, apptId: any)
	local clinic, err = self:_auth(ownerId, userId, "treat")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	return Appointment.finishVisit(appt, userId, self.now(), ownerId)
end

-- Invoice printed at reception, owner pays. All money/xp/rating computed server-side.
function GameLogic:pay(ownerId: number, userId: number, apptId: any)
	local clinic, err = self:_auth(ownerId, userId, "checkIn")
	if not clinic then
		return err
	end
	local appt = self:_appt(clinic, apptId)
	if not appt then
		return fail("No such patient")
	end
	local r = Appointment.pay(appt, self.now())
	if not r.ok then
		return r
	end
	local bill = r.bill
	local state = clinic.state
	Clinic.earn(state, bill.total, "Visit: " .. appt.patient.name)
	local levels = Clinic.addXp(self.clinicConfig, state, bill.xp)
	Clinic.addRating(self.clinicConfig, state, bill.stars)
	state.patientsTreated += 1
	clinic.served += 1
	local profile = self.profiles[ownerId]
	if profile and profile.stats then
		profile.stats.patients += 1
		if bill.correct then
			profile.stats.correct += 1
		end
	end
	if bill.followUp and #state.followUps < 5 then
		table.insert(state.followUps, {
			caseId = appt.caseId,
			breed = appt.patient.breed,
			petName = appt.patient.name,
			weightLb = appt.patient.weightLb,
			ageYears = appt.patient.ageYears,
			customerName = appt.customer.name,
			personality = appt.customer.personality,
		})
	end
	self:_tutorial(ownerId, "Checkout")
	Appointment.leave(appt, self.now())
	r.levelsGained = levels
	r.cash = state.cash
	return r
end

function GameLogic:customerLeft(ownerId: number, apptId: number)
	local clinic = self.clinics[ownerId]
	local appt = clinic and self:_appt(clinic, apptId)
	if appt then
		Appointment.done(appt, self.now())
	end
end

---------------------------------------------------------------------------------------------
-- Management actions
---------------------------------------------------------------------------------------------
function GameLogic:order(ownerId: number, userId: number, item: any, qty: any)
	-- staff may shelve deliveries, but only finance roles spend the clinic's money
	local clinic, err = self:_auth(ownerId, userId, "finance")
	if not clinic then
		return err
	end
	if type(item) ~= "string" then
		return fail("Invalid order")
	end
	return Clinic.order(self.clinicConfig, clinic.state, item, qty)
end

function GameLogic:shelve(ownerId: number, userId: number, boxId: any)
	local clinic, err = self:_auth(ownerId, userId, "restock")
	if not clinic then
		return err
	end
	if type(boxId) ~= "number" then
		return fail("No such box")
	end
	local r = Clinic.shelve(clinic.state, boxId)
	if r.ok then
		self:_tutorial(ownerId, "Restock")
	end
	return r
end

function GameLogic:place(ownerId: number, userId: number, itemId: any, room: any, x: any, z: any, rot: any)
	local clinic, err = self:_auth(ownerId, userId, "build")
	if not clinic then
		return err
	end
	if type(itemId) ~= "string" or type(room) ~= "string" then
		return fail("Bad item")
	end
	local r = Clinic.place(self.clinicConfig, clinic.state, itemId, room, x, z, rot)
	if r.ok then
		self:_tutorial(ownerId, "Decorate")
	end
	return r
end

function GameLogic:move(ownerId: number, userId: number, id: any, x: any, z: any, rot: any)
	local clinic, err = self:_auth(ownerId, userId, "build")
	if not clinic then
		return err
	end
	if type(id) ~= "string" then
		return fail("Bad item")
	end
	return Clinic.move(self.clinicConfig, clinic.state, id, x, z, rot)
end

function GameLogic:remove(ownerId: number, userId: number, id: any)
	local clinic, err = self:_auth(ownerId, userId, "build")
	if not clinic then
		return err
	end
	if type(id) ~= "string" then
		return fail("Bad item")
	end
	return Clinic.remove(self.clinicConfig, clinic.state, id)
end

function GameLogic:buyRoom(ownerId: number, userId: number, room: any)
	local clinic, err = self:_auth(ownerId, userId, "build")
	if not clinic then
		return err
	end
	if type(room) ~= "string" then
		return fail("Bad room")
	end
	return Clinic.buyRoom(self.clinicConfig, clinic.state, room)
end

function GameLogic:setFinish(ownerId: number, userId: number, room: any, slot: any, finishId: any)
	local clinic, err = self:_auth(ownerId, userId, "build")
	if not clinic then
		return err
	end
	if type(room) ~= "string" or type(slot) ~= "string" or type(finishId) ~= "string" then
		return fail("Bad finish")
	end
	return Clinic.setFinish(self.clinicConfig, clinic.state, room, slot, finishId)
end

-- filteredName must already be TextService-filtered by the server glue.
function GameLogic:rename(ownerId: number, userId: number, filteredName: any)
	local clinic, err = self:_auth(ownerId, userId, "manage")
	if not clinic then
		return err
	end
	if not Clinic.validName(filteredName) then
		return fail("3–28 letters, numbers or simple punctuation")
	end
	clinic.state.name = filteredName
	self:_tutorial(ownerId, "NameClinic")
	return { ok = true }
end

function GameLogic:hire(ownerId: number, userId: number, role: any)
	local clinic, err = self:_auth(ownerId, userId, "manage")
	if not clinic then
		return err
	end
	if type(role) ~= "string" then
		return fail("Unknown role")
	end
	local names = self.Config.customers.firstNames
	return Clinic.hire(self.clinicConfig, clinic.state, role, names[(clinic.state.nextStaffId % #names) + 1])
end

---------------------------------------------------------------------------------------------
-- Snapshots for clients (never contain hidden diagnoses)
---------------------------------------------------------------------------------------------
function GameLogic:snapshot(ownerId: number, userId: number)
	local clinic = self.clinics[ownerId]
	if not clinic then
		return nil
	end
	local s = clinic.state
	local appts = {}
	for _, appt in self:waitingList(ownerId) do
		table.insert(appts, Appointment.snapshot(appt))
	end
	for _, appt in clinic.appts do
		if not (appt.phase == "Waiting" or appt.phase == "AtReception" or appt.phase == "Arriving") then
			table.insert(appts, Appointment.snapshot(appt))
		end
	end
	local busyRooms = {}
	for _, appt in clinic.appts do
		if
			appt.room and appt.claimedBy and GameLogic.TABLE_PHASES[appt.phase]
			or (appt.room and (appt.phase == "InRoom" or appt.phase == "ToRoom" or appt.phase == "Called"))
		then
			busyRooms[appt.room] = appt.id
		end
	end
	local profile = self.profiles[ownerId]
	local step = profile and self.tutorial:current(profile.tutorial)
	return {
		role = self:roleOf(ownerId, userId),
		clinic = {
			name = s.name,
			cash = s.cash,
			debt = s.debt or 0,
			level = s.level,
			xp = s.xp,
			xpThis = Clinic.xpForLevel(s.level),
			xpNext = Clinic.xpForLevel(s.level + 1),
			reputation = s.reputation,
			day = s.day,
			stock = s.stock,
			deliveries = s.deliveries,
			staff = s.staff,
			placements = s.placements,
			rooms = s.rooms,
			finishes = s.finishes,
			finance = Clinic.summary(s),
			ledger = table.move(s.ledger, math.max(1, #s.ledger - 29), #s.ledger, 1, {}),
			busyRooms = busyRooms,
			expenses = Clinic.dailyExpenses(self.clinicConfig, s),
		},
		appointments = appts,
		tutorial = step and { id = step.id, text = step.text, target = step.target } or nil,
	}
end

return GameLogic
