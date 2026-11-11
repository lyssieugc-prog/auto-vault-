--[[
	Appointment — one patient visit as a continuous state machine. Pure + server-side.

	Arriving → AtReception → Waiting → Called → ToRoom → InRoom → OnTable → Exam ⇄ (procedures)
	→ Diagnosed → Treatment → Treated → Checkout → Paid → Leaving → Done

	• Multiplayer-safe: a staff member CLAIMS the appointment when calling the patient; only the
	  claimer (or the clinic owner) can run exams/treatments, and only one procedure at a time.
	• The diagnosis is never told to the player: the owner's complaint + exam findings are the
	  evidence; the player picks a diagnosis from the list.
	• Wrong diagnosis → manageable consequences: exams still billed, treatment fee waived, lower
	  rating, and the pet comes back for a follow-up with the same case.

	local appt = Appointment.new({ id, case, caseId, patient, customer, now, rng })
	Appointment.checkIn(appt, staffId, now)   ... Appointment.pay(appt, now) → bill
]]

local function import(name: string)
	if script then
		return require(script.Parent:WaitForChild(name))
	end
	-- Lune: path require (aliased so the Roblox std lint does not apply)
	local requirePath: any = require
	return requirePath("./" .. name)
end

local AnimalMind = import("AnimalMind")
local Cases = import("Cases")
local Procedures = import("Procedures")

local Appointment = {}

Appointment.PHASES = {
	"Arriving",
	"AtReception",
	"Waiting",
	"Called",
	"ToRoom",
	"InRoom",
	"OnTable",
	"Exam",
	"Diagnosed",
	"Treatment",
	"Treated",
	"Checkout",
	"Paid",
	"Leaving",
	"Done",
	"WalkedOut",
}

local ORDER = {}
for i, name in Appointment.PHASES do
	ORDER[name] = i
end

function Appointment.new(opts)
	local case = opts.case
	return {
		id = opts.id,
		caseId = opts.caseId,
		case = case,
		patient = opts.patient, -- { name, breed, species, weightLb, vitals, mind, injury, affectedEar, case }
		customer = opts.customer, -- { name, patience, personality, complaint }
		phase = "Arriving",
		phaseSince = opts.now,
		arrivedAt = opts.now,
		waitStart = nil,
		waited = 0,
		claimedBy = nil,
		room = nil,
		exams = {}, -- ordered list of { id, results }
		examsDone = {},
		chart = {}, -- player-visible notes
		running = nil, -- { kind = "exam"|"treatment", id, run }
		diagnosis = nil,
		diagnosisCorrect = nil,
		treatmentsDone = {},
		bandages = {}, -- visible on the animal: { leg }
		emergency = opts.emergency or false,
		followUp = opts.followUp or false,
		log = {},
		rng = opts.rng or math.random,
	}
end

local function setPhase(appt, phase: string, now: number)
	appt.phase = phase
	appt.phaseSince = now
	table.insert(appt.log, phase)
end

local function fail(msg: string)
	return { ok = false, message = msg }
end

local function at(appt, phase: string): boolean
	return appt.phase == phase
end

local function isHandler(appt, userId: number, ownerId: number?): boolean
	return appt.claimedBy == userId or (ownerId ~= nil and userId == ownerId)
end

function Appointment.reachReception(appt, now: number)
	if not at(appt, "Arriving") then
		return fail("not arriving")
	end
	setPhase(appt, "AtReception", now)
	return { ok = true }
end

-- Receptionist (player or NPC staff) checks the customer in at the computer.
function Appointment.checkIn(appt, staffId: number, now: number)
	if not at(appt, "AtReception") then
		return fail("Customer isn't at the desk")
	end
	appt.checkedInBy = staffId
	appt.waitStart = now
	table.insert(appt.chart, { kind = "Complaint", text = appt.customer.complaint })
	setPhase(appt, "Waiting", now)
	return { ok = true }
end

-- Waiting-room tick: patience and walk-outs. Returns mood: "fine" | "impatient" | "leaving".
function Appointment.tickWaiting(appt, now: number): string
	if not at(appt, "Waiting") then
		return "fine"
	end
	local waited = now - appt.waitStart
	appt.waited = waited
	local patience = appt.customer.patience
	if waited > patience * 2.2 then
		setPhase(appt, "WalkedOut", now)
		return "leaving"
	elseif waited > patience then
		return "impatient"
	end
	return "fine"
end

-- A vet calls the patient's name: claims the appointment (one handler at a time).
function Appointment.call(appt, vetId: number, room: string, now: number)
	if not at(appt, "Waiting") then
		return fail("Patient isn't waiting")
	end
	if appt.claimedBy and appt.claimedBy ~= vetId then
		return fail("Another vet already called this patient")
	end
	appt.claimedBy = vetId
	appt.room = room
	appt.waited = now - appt.waitStart
	setPhase(appt, "Called", now)
	return { ok = true }
end

function Appointment.release(appt, vetId: number)
	-- handler left the server: patient goes back to waiting, keeps their history
	if appt.claimedBy ~= vetId then
		return
	end
	appt.claimedBy = nil
	appt.running = nil
	if ORDER[appt.phase] >= ORDER.Called and ORDER[appt.phase] <= ORDER.Treated then
		appt.phase = "Waiting"
	end
end

function Appointment.startWalk(appt, now: number)
	if not at(appt, "Called") then
		return fail("not called")
	end
	setPhase(appt, "ToRoom", now)
	return { ok = true }
end

function Appointment.enterRoom(appt, now: number)
	if not at(appt, "ToRoom") then
		return fail("not walking to room")
	end
	setPhase(appt, "InRoom", now)
	return { ok = true }
end

--[[
	Getting onto the table. Small animals: "pickUp" then "placeOnTable". Large dogs can't just
	be lifted: "liftFront" (front paws on the table edge) then "liftBack" (support the hind end).
	Each step is a handling stimulus — a scared animal may need calming first.
]]
function Appointment.helpOntoTable(appt, userId: number, step: string, now: number, ownerId: number?)
	if not at(appt, "InRoom") then
		return fail("Bring the patient into the exam room first")
	end
	if not isHandler(appt, userId, ownerId) then
		return fail("This isn't your patient")
	end
	local breedSize = appt.patient.size
	local mind = appt.patient.mind
	local expected = if breedSize == "large" then { "liftFront", "liftBack" } else { "pickUp", "placeOnTable" }
	appt.tableSteps = appt.tableSteps or 0
	local want = expected[appt.tableSteps + 1]
	if step ~= want then
		return fail(
			if breedSize == "large" then "Big dogs need help: front paws first" else "Pick the patient up first"
		)
	end
	local reaction = AnimalMind.stimulus(mind, "PickedUp", if breedSize == "large" then 0.6 else 1)
	if reaction == "Struggle" and appt.rng() > AnimalMind.derive(mind).cooperation + 0.3 then
		appt.tableSteps = 0
		return { ok = false, event = "Struggled", message = "The patient wriggled free — calm them down first" }
	end
	appt.tableSteps += 1
	if appt.tableSteps == #expected then
		setPhase(appt, "OnTable", now)
		return { ok = true, event = "OnTable" }
	end
	return { ok = true, event = step }
end

local function canWork(appt, userId: number, ownerId: number?)
	if not isHandler(appt, userId, ownerId) then
		return fail("This isn't your patient")
	end
	if not (at(appt, "OnTable") or at(appt, "Exam") or at(appt, "Diagnosed") or at(appt, "Treatment")) then
		return fail("The patient needs to be on the exam table")
	end
	return nil
end

-- Begin an exam (procedure). unlocked(level check) is decided by the caller (Clinic).
function Appointment.beginExam(appt, userId: number, examId: string, now: number, ownerId: number?)
	local err = canWork(appt, userId, ownerId)
	if err then
		return err
	end
	if ORDER[appt.phase] >= ORDER.Diagnosed then
		return fail("You've already made a diagnosis")
	end
	local exam = Cases.exams[examId]
	if not exam or not Procedures.defs[exam.procedure] then
		return fail("Unknown exam")
	end
	if appt.running then
		return fail("Finish the current procedure first")
	end
	appt.running = {
		kind = "exam",
		id = examId,
		run = Procedures.start(exam.procedure, { patient = appt.patient, now = now, rng = appt.rng }),
	}
	if at(appt, "OnTable") then
		setPhase(appt, "Exam", now)
	end
	return { ok = true, steps = Procedures.describe(exam.procedure) }
end

-- Player-readable summary of exam results (goes into the chart and the vet computer).
function Appointment.summarize(appt, examId: string, results): string
	local p = appt.patient
	local speciesVitals = p.speciesDef
	if examId == "Stethoscope" then
		local h = results.Heart
		local parts = {}
		if h then
			local normal = Cases.inRange(speciesVitals, "heartRate", h.heartRate)
			table.insert(
				parts,
				string.format(
					"Heart %d bpm (%s)%s, %s rhythm",
					h.heartRate,
					if normal then "normal" else "outside normal",
					if h.stressed then " — patient stressed, may read high" else "",
					string.lower(h.sound)
				)
			)
		end
		for _, side in { "LungL", "LungR" } do
			local l = results[side]
			if l then
				table.insert(
					parts,
					string.format(
						"%s lung: %s, %d breaths/min",
						side == "LungL" and "Left" or "Right",
						l.sound,
						l.respRate
					)
				)
			end
		end
		return table.concat(parts, "; ")
	elseif examId == "Thermometer" then
		local t = results.tempF
		local r = speciesVitals.vitals.tempF
		local verdict = if t > r[2] then "FEVER" elseif t < r[1] then "low" else "normal"
		return string.format("Temperature %.1f°F (%s; normal %.1f–%.1f)", t, verdict, r[1], r[2])
	elseif examId == "Otoscope" or examId == "FurCheck" then
		if not results.found or #results.found == 0 then
			return if examId == "Otoscope"
				then "Both ear canals look clean and healthy"
				else "Coat and skin look normal"
		end
		local notes = {}
		for _, f in results.found do
			table.insert(notes, string.format("%s side: %s", f.side, f.note))
		end
		return table.concat(notes, "; ")
	elseif examId == "Palpate" then
		local a = results.Abdomen
		return a and a.note or "Abdomen normal"
	elseif examId == "Visual" then
		return results.note or "No visible problems"
	end
	return "Done"
end

function Appointment.procedureInput(appt, userId: number, action: string, payload, ctx, ownerId: number?)
	if not isHandler(appt, userId, ownerId) then
		return fail("This isn't your patient")
	end
	local running = appt.running
	if not running then
		return fail("No procedure in progress")
	end
	ctx.mind = appt.patient.mind
	local r = Procedures.input(running.run, action, payload, ctx)
	if r.event == "PulledAway" then
		appt.pullAways = (appt.pullAways or 0) + 1
	end
	if r.done then
		appt.running = nil
		if running.kind == "exam" then
			local summary = Appointment.summarize(appt, running.id, running.run.results)
			table.insert(appt.exams, { id = running.id, results = running.run.results, summary = summary })
			appt.examsDone[running.id] = true
			table.insert(appt.chart, { kind = "Exam", exam = running.id, text = summary })
			r.summary = summary
		else
			appt.treatmentsDone[running.id] = true
			table.insert(
				appt.chart,
				{ kind = "Treatment", treatment = running.id, text = Cases.treatments[running.id].name }
			)
			if running.id == "Bandage" then
				table.insert(appt.bandages, { leg = (appt.patient.injury and appt.patient.injury.leg) or "FL" })
			end
			-- does it help? only treatments the real problem needs relieve the animal
			if table.find(appt.case.treatments, running.id) then
				AnimalMind.stimulus(appt.patient.mind, "Relief", 1 / #appt.case.treatments)
				r.relief = true
			end
			local all = true
			for _, t in appt.case.treatments do
				if not appt.treatmentsDone[t] then
					all = false
				end
			end
			if all then
				appt.phase = "Treated"
				table.insert(appt.log, "Treated")
			end
		end
	end
	return r
end

function Appointment.cancelProcedure(appt, userId: number, ownerId: number?)
	if isHandler(appt, userId, ownerId) then
		appt.running = nil
	end
end

function Appointment.diagnose(appt, userId: number, diagnosisId: string, now: number, ownerId: number?)
	if not isHandler(appt, userId, ownerId) then
		return fail("This isn't your patient")
	end
	if not (at(appt, "Exam") or at(appt, "OnTable")) or appt.running then
		return fail("Examine the patient first")
	end
	if not Cases.diagnoses[diagnosisId] then
		return fail("Unknown diagnosis")
	end
	appt.diagnosis = diagnosisId
	appt.diagnosisCorrect = diagnosisId == appt.case.diagnosis
	local evidence = false
	for _, e in appt.case.keyExams do
		if appt.examsDone[e] then
			evidence = true
		end
	end
	appt.evidence = evidence
	table.insert(appt.chart, { kind = "Diagnosis", diagnosis = diagnosisId, text = Cases.diagnoses[diagnosisId].name })
	setPhase(appt, "Diagnosed", now)
	return { ok = true, correct = nil } -- correctness is revealed at checkout / follow-up, not now
end

-- Recommend + perform a treatment. inventory check/consume is done by Clinic via the caller.
function Appointment.beginTreatment(appt, userId: number, treatmentId: string, now: number, ownerId: number?)
	local err = canWork(appt, userId, ownerId)
	if err then
		return err
	end
	if not (at(appt, "Diagnosed") or at(appt, "Treatment")) then
		return fail("Make a diagnosis first")
	end
	local t = Cases.treatments[treatmentId]
	if not t or not Procedures.defs[t.procedure] then
		return fail("Unknown treatment")
	end
	if appt.running then
		return fail("Finish the current procedure first")
	end
	if appt.treatmentsDone[treatmentId] then
		return fail("Already done")
	end
	appt.running = {
		kind = "treatment",
		id = treatmentId,
		run = Procedures.start(t.procedure, { patient = appt.patient, now = now, rng = appt.rng }),
	}
	setPhase(appt, "Treatment", now)
	return { ok = true, steps = Procedures.describe(t.procedure) }
end

-- Done treating (or decided nothing more is needed): patient goes down, owner to checkout.
function Appointment.finishVisit(appt, userId: number, now: number, ownerId: number?)
	if not isHandler(appt, userId, ownerId) then
		return fail("This isn't your patient")
	end
	if appt.running then
		return fail("Finish the current procedure first")
	end
	if not (at(appt, "Treated") or at(appt, "Treatment") or at(appt, "Diagnosed")) then
		return fail("Diagnose the patient first")
	end
	setPhase(appt, "Checkout", now)
	return { ok = true }
end

--[[
	Bill + rating. Exams are always billed (the work was done); treatment fees only when the
	diagnosis was right; base visit pay scales with correctness. Rating 1..5:
	  +2.2 correct diagnosis, +0.4 backed by a key exam, +0.6 all treatments done,
	  +0.8 × patient comfort at the end, −0.6 per unnecessary paid test beyond 1,
	  −0.15 per pull-away (rough handling) beyond 2, −wait penalty, floor 1.
]]
function Appointment.bill(appt)
	local lines = {}
	local total = 0
	local correct = appt.diagnosisCorrect == true
	local visit = math.floor(appt.case.basePay * (if correct then 1 else 0.4))
	table.insert(lines, { label = "Consultation", amount = visit })
	total += visit
	local unnecessary = 0
	local pullAways = appt.pullAways or 0
	for _, e in appt.exams do
		local price = Cases.exams[e.id].price
		if price > 0 then
			table.insert(lines, { label = Cases.exams[e.id].name, amount = price })
			total += price
			if not table.find(appt.case.keyExams, e.id) then
				unnecessary += 1
			end
		end
	end
	-- only treatments that actually fit the problem are billed (no charging for wrong care)
	for _, t in appt.case.treatments do
		if appt.treatmentsDone[t] then
			local price = Cases.treatments[t].price
			table.insert(lines, { label = Cases.treatments[t].name, amount = price })
			total += price
		end
	end
	local allTreated = true
	for _, t in appt.case.treatments do
		if not appt.treatmentsDone[t] then
			allTreated = false
		end
	end
	local mind = appt.patient.mind
	local comfort = mind.state.comfort
	local stars = 1
	if correct then
		stars += 2.2
		if appt.evidence then
			stars += 0.4
		end
		if allTreated then
			stars += 0.6
		end
	end
	stars += comfort * 0.8
	stars -= math.max(0, unnecessary - 1) * 0.6
	stars -= math.max(0, pullAways - 2) * 0.15
	local patience = appt.customer.patience
	if appt.waited > patience then
		stars -= math.min(1.2, (appt.waited - patience) / patience)
	end
	stars = math.clamp(math.floor(stars * 2 + 0.5) / 2, 1, 5)
	local xp = math.floor(appt.case.xp * (if correct then 1 else 0.35) * (if appt.evidence then 1 else 0.7))
	return {
		lines = lines,
		total = total,
		stars = stars,
		xp = xp,
		correct = correct,
		followUp = not (correct and allTreated),
	}
end

-- Owner pays at the desk (invoice printed). Returns the bill once.
function Appointment.pay(appt, now: number)
	if not at(appt, "Checkout") then
		return fail("Not at checkout")
	end
	appt.finalBill = Appointment.bill(appt)
	setPhase(appt, "Paid", now)
	return { ok = true, bill = appt.finalBill }
end

function Appointment.leave(appt, now: number)
	if at(appt, "Paid") then
		setPhase(appt, "Leaving", now)
		return { ok = true }
	end
	return fail("Hasn't paid")
end

function Appointment.done(appt, now: number)
	if at(appt, "Leaving") then
		setPhase(appt, "Done", now)
		return { ok = true }
	end
	return fail("not leaving")
end

-- Snapshot for the vet computer / UI. Never includes the hidden case diagnosis.
function Appointment.snapshot(appt)
	return {
		id = appt.id,
		phase = appt.phase,
		patient = {
			name = appt.patient.name,
			breed = appt.patient.breed,
			species = appt.patient.species,
			weightLb = appt.patient.weightLb,
			ageYears = appt.patient.ageYears,
		},
		customer = {
			name = appt.customer.name,
			complaint = appt.customer.complaint,
			personality = appt.customer.personality,
			patience = appt.customer.patience,
		},
		claimedBy = appt.claimedBy,
		chart = appt.chart,
		running = appt.running and {
			kind = appt.running.kind,
			id = appt.running.id,
			step = appt.running.run.stepIndex,
		},
		diagnosis = appt.diagnosis,
		treatmentsDone = appt.treatmentsDone,
		bandages = appt.bandages,
		emergency = appt.emergency,
		followUp = appt.followUp,
		waited = appt.waited,
	}
end

return Appointment
