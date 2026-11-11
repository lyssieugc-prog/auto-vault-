-- My Vet Office tests: animal mind/behaviour/animation math, procedures, clinic economy and a
-- complete golden-retriever appointment driven step-by-step like a player would (Lune).
-- Run from the repo root: `lune run games/my-vet-office/tests/run`

local process = require("@lune/process")

local AnimBlend = require("../src/shared/AnimBlend")
local AnimalBehavior = require("../src/shared/AnimalBehavior")
local AnimalMind = require("../src/shared/AnimalMind")
local Appointment = require("../src/shared/Appointment")
local Cases = require("../src/shared/Cases")
local Clinic = require("../src/shared/Clinic")
local Config = require("../src/shared/Config")
local GameLogic = require("../src/shared/GameLogic")
local PoseGraph = require("../src/shared/PoseGraph")
local PoseLibrary = require("../src/shared/PoseLibrary")
local Procedures = require("../src/shared/Procedures")
local Species = require("../src/shared/Species")
local TestKit = require("../vendor/vault/tests/TestKit")

local M = {
	Tutorial = require("../vendor/vault/Shared/Tutorial"),
	DataService = require("../vendor/vault/Shared/DataService"),
}

local describe, it, expect = TestKit.describe, TestKit.it, TestKit.expect

local function constRng(v)
	return function()
		return v
	end
end

---------------------------------------------------------------------------------------------
describe("Content consistency", function()
	it("every case references real diagnoses, treatments, exams and species", function()
		for name, c in Cases.cases do
			assert(Cases.diagnoses[c.diagnosis], name .. " diagnosis")
			for _, t in c.treatments do
				assert(Cases.treatments[t], name .. " treatment " .. t)
			end
			for _, e in c.keyExams do
				assert(Cases.exams[e], name .. " key exam " .. e)
			end
			for _, s in c.species do
				assert(Species.species[s], name .. " species " .. s)
			end
			assert(#c.complaints >= 2, name .. " needs ≥2 complaint phrasings")
		end
	end)
	it("complaints never give away the diagnosis name", function()
		for name, c in Cases.cases do
			local diag = string.lower(Cases.diagnoses[c.diagnosis].name)
			for _, line in c.complaints do
				local l = string.lower(line)
				assert(not string.find(l, diag, 1, true), name .. " complaint reveals diagnosis")
			end
		end
	end)
	it("every unlocked exam/treatment has a procedure and supplies exist", function()
		for id, lvl in Config.unlocks.exams do
			if lvl <= 2 then
				assert(Procedures.defs[Cases.exams[id].procedure], "exam procedure " .. id)
			end
		end
		for id, lvl in Config.unlocks.treatments do
			local t = Cases.treatments[id]
			assert(t, "treatment " .. id)
			if lvl <= 2 then
				assert(Procedures.defs[t.procedure], "treatment procedure " .. id)
			end
			for supply in t.supplies do
				assert(Cases.supplies[supply], "supply " .. supply)
			end
		end
	end)
	it("every procedure references real landmarks", function()
		for id, def in Procedures.defs do
			for _, step in def.steps do
				for _, p in step.points or {} do
					assert(p == "Ear" or p == "Injury" or Cases.landmarks[p], id .. " landmark " .. p)
				end
			end
		end
	end)
	it("start layout is valid placement and catalog items fit their rooms", function()
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(1) })
		local state = logic:newClinicState()
		for id, p in state.placements do
			local ok, err = Clinic.canPlace(logic.clinicConfig, state, p.item, p.room, p.x, p.z, p.rot, id)
			assert(ok, p.item .. " in " .. p.room .. ": " .. tostring(err))
		end
	end)
	it("every breed has temperament for all mind attributes and all gait speeds", function()
		for name, b in Species.breeds do
			for _, key in AnimalMind.ATTRIBUTES do
				assert(type(b.temperament[key]) == "number", name .. " " .. key)
			end
			for _, g in { "walk", "trot", "run", "sprint" } do
				assert(b.gaitSpeed[g] and b.stride[g], name .. " gait " .. g)
			end
			assert(b.gaitSpeed.walk < b.gaitSpeed.trot and b.gaitSpeed.trot < b.gaitSpeed.run, name .. " gait order")
		end
	end)
end)

---------------------------------------------------------------------------------------------
describe("AnimalMind", function()
	local G = Species.breeds.GoldenRetriever.temperament
	local C = Species.breeds.Chihuahua.temperament
	it("personalities differ: a golden is more cooperative than a nervous chihuahua", function()
		local g, c = AnimalMind.new(G), AnimalMind.new(C)
		expect(AnimalMind.derive(g).cooperation).toBeGreaterThan(AnimalMind.derive(c).cooperation + 0.2)
		expect(AnimalMind.derive(g).tailWag).toBeGreaterThan(AnimalMind.derive(c).tailWag)
	end)
	it("a terrified animal pulls away from petting instead of relaxing", function()
		local m = AnimalMind.new({ fear = 0.9, trust = 0.05, stress = 0.8, sociability = 0.2 })
		local before = m.state.stress
		expect(AnimalMind.stimulus(m, "Pet")).toBe("PullAway")
		expect(m.state.stress).toBeGreaterThan(before)
	end)
	it("treats + comfort calm a nervous chihuahua until it cooperates", function()
		local m = AnimalMind.new(C)
		local start = AnimalMind.derive(m).cooperation
		for _ = 1, 3 do
			AnimalMind.stimulus(m, "Comfort")
			AnimalMind.stimulus(m, "Treat")
			AnimalMind.stimulus(m, "Pet")
		end
		expect(AnimalMind.derive(m).cooperation).toBeGreaterThan(start + 0.15)
		expect(AnimalMind.derive(m).tremble).toBe(0)
	end)
	it("pain shows in the body: limp, low head, careful gait", function()
		local hurt = AnimalMind.new(G, Cases.cases.PawLaceration.mind)
		local fine = AnimalMind.new(G)
		local ph, pf = AnimalMind.derive(hurt), AnimalMind.derive(fine)
		expect(ph.limp).toBeGreaterThan(0.3)
		expect(pf.limp).toBe(0)
		expect(ph.headHeight).toBeLessThan(pf.headHeight)
		expect(ph.gaitScale).toBeLessThan(pf.gaitScale)
	end)
	it("relief lowers pain permanently (baseline moves) and the animal relaxes", function()
		local m = AnimalMind.new(G, { pain = 0.5 })
		AnimalMind.stimulus(m, "Relief", 1)
		for _ = 1, 600 do
			AnimalMind.tick(m, 0.2)
		end
		expect(m.state.pain).toBeLessThan(0.2)
	end)
	it("tick relaxes toward baseline and stays in 0..1", function()
		local m = AnimalMind.new(G)
		for _ = 1, 5 do
			AnimalMind.stimulus(m, "LoudNoise")
		end
		local scared = m.state.fear
		for _ = 1, 300 do
			AnimalMind.tick(m, 0.2)
		end
		expect(m.state.fear).toBeLessThan(scared)
		for _, k in AnimalMind.ATTRIBUTES do
			assert(m.state[k] >= 0 and m.state[k] <= 1, k)
		end
	end)
	it("unknown stimulus throws", function()
		expect(function()
			AnimalMind.stimulus(AnimalMind.new(G), "Teleport")
		end).toThrow()
	end)
end)

---------------------------------------------------------------------------------------------
describe("PoseGraph (no teleporting)", function()
	it("routes Stand → LieLateral through intermediate poses", function()
		local allowed = { Stand = true, Sit = true, LieSternal = true, LieLateral = true }
		local route = PoseGraph.route(PoseGraph.QUADRUPED, "Stand", "LieLateral", allowed)
		expect(#route >= 2).toBe(true)
		expect(route[#route]).toBe("LieLateral")
	end)
	it("transitions take time and alpha is continuous", function()
		local pg = PoseGraph.new(PoseGraph.QUADRUPED, "Stand")
		PoseGraph.request(pg, "Sit")
		expect(pg.current).toBeNil()
		local last = 0
		for _ = 1, 30 do
			PoseGraph.tick(pg, 0.05)
			if pg.current == nil then
				expect(pg.alpha - last <= 0.1).toBe(true)
				last = pg.alpha
			end
		end
		expect(pg.current).toBe("Sit")
	end)
	it("a mid-transition request finishes the current edge first", function()
		local pg =
			PoseGraph.new(PoseGraph.QUADRUPED, "Stand", { allowed = { Stand = true, Sit = true, LieSternal = true } })
		PoseGraph.request(pg, "Sit")
		PoseGraph.tick(pg, 0.3)
		PoseGraph.request(pg, "LieSternal")
		expect(pg.to).toBe("Sit")
		for _ = 1, 60 do
			PoseGraph.tick(pg, 0.05)
		end
		expect(pg.current).toBe("LieSternal")
		expect(table.concat(pg.history, ">")).toBe("Stand>Sit>LieSternal")
	end)
	it("eased alpha has zero slope at both ends", function()
		local pg = { alpha = 0.001 }
		expect(PoseGraph.easedAlpha(pg)).toBeLessThan(0.0001)
		pg.alpha = 0.999
		expect(PoseGraph.easedAlpha(pg)).toBeGreaterThan(0.9999)
	end)
	it("refuses poses the species can't do", function()
		local pg = PoseGraph.new(PoseGraph.QUADRUPED, "Stand", { allowed = { Stand = true, Sit = true } })
		expect(PoseGraph.request(pg, "Curl")).toBe(false)
	end)
end)

---------------------------------------------------------------------------------------------
describe("AnimBlend (animation framework math)", function()
	local golden = Species.breeds.GoldenRetriever
	it("locomotion weights sum to 1 and pick neighbouring gaits", function()
		for _, speed in { 0, 1, 3.5, 5, 7, 10, 12, 15, 30 } do
			local w = AnimBlend.locomotionWeights(speed, golden.gaitSpeed)
			local sum = 0
			local nonzero = 0
			for _, v in w do
				sum += v
				if v > 0 then
					nonzero += 1
				end
			end
			expect(sum).toBeNear(1, 1e-6)
			expect(nonzero <= 2).toBe(true)
		end
		expect(AnimBlend.locomotionWeights(5.25, golden.gaitSpeed).walk).toBeNear(0.5, 1e-6)
	end)
	it("playback rate syncs stride to speed so paws don't slide", function()
		for _, speed in { 1.5, 3.5, 6 } do
			local rate = AnimBlend.playbackRate(speed, golden.stride.walk, golden.rigScale, 1)
			expect(AnimBlend.footSlide(speed, rate, golden.stride.walk, golden.rigScale, 1)).toBeNear(0, 1e-6)
		end
		-- smaller dogs take more steps for the same speed
		local chi = Species.breeds.Chihuahua
		expect(AnimBlend.playbackRate(2, chi.stride.walk, chi.rigScale, 1)).toBeGreaterThan(
			AnimBlend.playbackRate(2, golden.stride.walk, golden.rigScale, 1)
		)
	end)
	it("weights cross-fade smoothly (no snapping) and stay normalised", function()
		local ws = AnimBlend.newWeights({ Stand = 1 })
		AnimBlend.setTargets(ws, { Sit = 1 })
		local w = AnimBlend.stepWeights(ws, 1 / 60, 0.25)
		expect(w.Sit).toBeLessThan(0.1)
		expect(w.Sit + w.Stand).toBeNear(1, 1e-6)
		for _ = 1, 120 do
			w = AnimBlend.stepWeights(ws, 1 / 60, 0.25)
		end
		expect(w.Sit).toBeGreaterThan(0.99)
	end)
	it("smoothing is frame-rate independent", function()
		local a = AnimBlend.smoothing(1 / 30, 0.2)
		local b = 1 - (1 - AnimBlend.smoothing(1 / 60, 0.2)) ^ 2
		expect(a).toBeNear(b, 1e-9)
	end)
	it("head look spring converges without overshoot", function()
		local sp = AnimBlend.newSpring(0, 0.12)
		local maxV = 0
		for _ = 1, 120 do
			local v = AnimBlend.stepSpring(sp, 1, 1 / 60)
			maxV = math.max(maxV, v)
		end
		expect(sp.value).toBeNear(1, 1e-3)
		expect(maxV <= 1 + 1e-6).toBe(true)
	end)
	it("look angles clamp to the neck range and ask the body to turn when behind", function()
		local yaw, pitch, turn = AnimBlend.lookAngles({ x = 0, y = 0, z = -1 })
		expect(turn).toBe(true)
		expect(math.abs(yaw) <= AnimBlend.LOOK_LIMITS.yaw + 1e-9).toBe(true)
		local _, p2, t2 = AnimBlend.lookAngles({ x = 0.2, y = 5, z = 1 })
		expect(t2).toBe(false)
		expect(p2).toBeNear(AnimBlend.LOOK_LIMITS.pitch, 1e-9)
		_ = pitch
	end)
	it("two-bone IK: straight leg at full reach, bends when the ground is closer", function()
		local _, kneeStraight = AnimBlend.twoBoneIK(1, 1, 2)
		expect(kneeStraight).toBeLessThan(0.05)
		local _, kneeBent, ok = AnimBlend.twoBoneIK(1, 1, 1.4)
		expect(ok).toBe(true)
		expect(kneeBent).toBeGreaterThan(0.5)
		local _, _, reach = AnimBlend.twoBoneIK(1, 1, 3)
		expect(reach).toBe(false)
	end)
	it("pelvis drops so no paw floats on uneven ground", function()
		expect(AnimBlend.pelvisOffset({ 0, 0, -0.4, -0.2 })).toBeNear(-0.3, 1e-9)
		expect(AnimBlend.pelvisOffset({ 0.1, 0.2, 0.3, 0.1 })).toBe(0)
	end)
	it("tail wags faster and wider when happy; blink closes then reopens", function()
		local function sweep(wag)
			local maxYaw = 0
			for i = 0, 200 do
				local yaw = AnimBlend.tailSegment(i / 100, 3, wag, 0.5)
				maxYaw = math.max(maxYaw, math.abs(yaw))
			end
			return maxYaw
		end
		expect(sweep(1)).toBeGreaterThan(sweep(0.1) * 2)
		local bs = {}
		local closed = 0
		for i = 0, 600 do
			local v = AnimBlend.blink(bs, i / 60, 3, constRng(0.5))
			if v > 0.9 then
				closed += 1
			end
		end
		expect(closed > 0 and closed < 20).toBe(true)
	end)
	it("LOD keeps a busy clinic cheap and the focused patient full quality", function()
		expect(AnimBlend.lodFor(10, true).name).toBe("full")
		expect(AnimBlend.lodFor(10, false).name).toBe("low")
		expect(AnimBlend.lodFor(300, true).name).toBe("off")
		expect(AnimBlend.lodFor(300, false, true).name).toBe("full")
		local tiers = AnimBlend.assignLods({ 5, 6, 7, 8, 9, 30, 50, 60 }, 3, 3)
		local full = 0
		for _, t in tiers do
			if t == "full" then
				full += 1
			end
		end
		expect(full).toBe(3)
		expect(tiers[1]).toBe("full")
		expect(tiers[8]).toBe("low")
	end)
end)

---------------------------------------------------------------------------------------------
describe("PoseLibrary (procedural poses + gait)", function()
	local bones = PoseLibrary.boneList(Species.rigs.Quadruped)
	local boneSet = {}
	for _, b in bones do
		boneSet[b] = true
	end
	it("every pose only uses real rig bones, with sane angles", function()
		for name, pose in PoseLibrary.poses do
			for bone, rot in pose.bones do
				assert(boneSet[bone], name .. " uses unknown bone " .. bone)
				for _, axis in { "p", "y", "r" } do
					local v = rot[axis] or 0
					assert(math.abs(v) <= 160, name .. "." .. bone .. " angle " .. v)
				end
			end
			assert(pose.root.h <= 0 and pose.root.h >= -0.8, name .. " root height")
		end
	end)
	it("every pose the species can do exists in the library", function()
		for sname, sp in Species.species do
			for _, pose in sp.poses do
				assert(PoseLibrary.poses[pose], sname .. " pose " .. pose)
			end
		end
	end)
	it("pose blending is continuous (no joint jumps between frames)", function()
		local prev = PoseLibrary.blend("Stand", "LieSternal", 0, bones)
		for i = 1, 60 do
			local t = i / 60
			t = t * t * (3 - 2 * t)
			local cur = PoseLibrary.blend("Stand", "LieSternal", t, bones)
			for _, b in bones do
				assert(math.abs(cur.bones[b].p - prev.bones[b].p) < 6, "jump on " .. b)
			end
			prev = cur
		end
		expect(prev.root.h).toBeNear(PoseLibrary.poses.LieSternal.root.h, 1e-9)
	end)
	it("leg cycle: planted paw moves back at constant speed with zero lift", function()
		local duty = PoseLibrary.DUTY.walk
		local last = nil
		local speeds = {}
		for i = 0, 20 do
			local phase = i / 20 * duty * 0.99
			local x, lift = PoseLibrary.legCycle(phase, duty)
			expect(lift).toBe(0)
			if last then
				table.insert(speeds, last - x)
			end
			last = x
		end
		for _, v in speeds do
			expect(v).toBeNear(speeds[1], 1e-9)
		end
		local _, swingLift = PoseLibrary.legCycle(duty + (1 - duty) / 2, duty)
		expect(swingLift).toBeNear(1, 1e-9)
		-- continuous at the stance→swing and swing→stance seams
		local a = PoseLibrary.legCycle(duty - 1e-6, duty)
		local b = PoseLibrary.legCycle(duty + 1e-6, duty)
		expect(a).toBeNear(b, 1e-3)
		local c = PoseLibrary.legCycle(1 - 1e-6, duty)
		local d = PoseLibrary.legCycle(0, duty)
		expect(c).toBeNear(d, 1e-3)
	end)
	it("gait phases give 4-beat walk and diagonal-pair trot", function()
		local g = Species.rigs.Quadruped.gaitPhases
		expect(g.trot.FL).toBe(g.trot.BR)
		expect(g.trot.FR).toBe(g.trot.BL)
		local seen = {}
		for _, v in g.walk do
			assert(not seen[v], "walk beats overlap")
			seen[v] = true
		end
	end)
end)

---------------------------------------------------------------------------------------------
describe("AnimalBehavior (emergent AI)", function()
	local dog = Species.species.Dog
	local cat = Species.species.Cat
	local function run(b, mind, ctxFn, seconds)
		local out
		for i = 1, math.floor(seconds * 5) do
			out = AnimalBehavior.tick(b, mind, ctxFn(i), 0.2)
		end
		return out
	end
	it("follows the walking owner and stops to sniff interesting scents", function()
		local b = AnimalBehavior.new({ breed = Species.breeds.Beagle, species = dog, rng = TestKit.seededRng(3) })
		local mind = AnimalMind.new(Species.breeds.Beagle.temperament)
		local sniffs = 0
		for i = 1, 200 do
			local out = AnimalBehavior.tick(b, mind, {
				leaderDist = 3,
				leaderMoving = true,
				poi = { id = "scent" .. math.floor(i / 10), kind = "Scent", dist = 1 },
			}, 0.2)
			if out.state == "Sniff" and b.stateTime <= 0.2 + 1e-9 then
				sniffs += 1
			end
			if out.state == "Follow" then
				expect(out.move).toBe("follow")
				expect(out.speed).toBeGreaterThan(0)
			end
		end
		expect(sniffs >= 3).toBe(true)
	end)
	it("sits beside the seated owner, then idles with gestures", function()
		local breed = Species.breeds.GoldenRetriever
		local b = AnimalBehavior.new({ breed = breed, species = dog, rng = TestKit.seededRng(7) })
		local mind = AnimalMind.new(breed.temperament)
		local gestures = 0
		for _ = 1, 150 do
			local out = AnimalBehavior.tick(b, mind, { leaderDist = 2, leaderSeated = true }, 0.2)
			if out.gesture then
				gestures += 1
			end
		end
		expect(b.state).toBe("Settle")
		expect(b.pose.current == "Sit" or b.pose.current == "LieSternal").toBe(true)
		expect(gestures >= 2).toBe(true)
	end)
	it("a nervous chihuahua hesitates far longer at the exam-room door than a golden", function()
		local function hesitation(breedName)
			local breed = Species.breeds[breedName]
			local b = AnimalBehavior.new({ breed = breed, species = dog, rng = TestKit.seededRng(5) })
			local mind = AnimalMind.new(breed.temperament)
			local t = 0
			for _ = 1, 200 do
				local out =
					AnimalBehavior.tick(b, mind, { leaderDist = 3, leaderMoving = true, atThreshold = true }, 0.1)
				if out.state == "Hesitate" then
					t += 0.1
				elseif t > 0 then
					break
				end
			end
			return t
		end
		local g, c = hesitation("GoldenRetriever"), hesitation("Chihuahua")
		expect(g < 1.5).toBe(true)
		expect(c).toBeGreaterThan(g * 1.5)
	end)
	it("a scared cat stays hidden in its carrier until comforted and the door opens", function()
		local breed = Species.breeds.DomesticShorthair
		local b = AnimalBehavior.new({ breed = breed, species = cat, rng = TestKit.seededRng(9), inCarrier = true })
		local mind = AnimalMind.new(breed.temperament, { fear = 0.3 })
		local out = run(b, mind, function()
			return { inCarrier = true, carrierOpen = true, leaderDist = 2 }
		end, 3)
		expect(out.state).toBe("Hide")
		expect(out.pose == "Crouch" or out.to == "Crouch").toBe(true)
		for _ = 1, 6 do
			AnimalMind.stimulus(mind, "Comfort")
			AnimalMind.stimulus(mind, "Treat")
		end
		out = run(b, mind, function()
			return { inCarrier = true, carrierOpen = true, leaderDist = 2, leaderMoving = true }
		end, 3)
		expect(out.state).toBe("Follow")
	end)
	it("on the table it holds the requested exam pose, reached smoothly", function()
		local breed = Species.breeds.GoldenRetriever
		local b = AnimalBehavior.new({ breed = breed, species = dog, rng = TestKit.seededRng(2) })
		local mind = AnimalMind.new(breed.temperament)
		run(b, mind, function()
			return { onTable = true }
		end, 3)
		expect(b.pose.current).toBe("Sit")
		local out = AnimalBehavior.tick(b, mind, { onTable = true, requestedPose = "LieLateral" }, 0.2)
		expect(out.pose).toBeNil() -- transitioning, not teleported
		run(b, mind, function()
			return { onTable = true, requestedPose = "LieLateral" }
		end, 5)
		expect(b.pose.current).toBe("LieLateral")
		local h = table.concat(b.pose.history, ">")
		expect(string.find(h, "LieSternal>LieLateral", 1, true) ~= nil).toBe(true)
	end)
	it("barking nearby startles a nervous dog and it looks toward the sound", function()
		local breed = Species.breeds.Chihuahua
		local b = AnimalBehavior.new({ breed = breed, species = dog, rng = TestKit.seededRng(4) })
		local mind = AnimalMind.new(breed.temperament)
		local before = mind.state.fear
		local out = AnimalBehavior.tick(b, mind, { leaderDist = 2, sound = { kind = "Bark", dist = 5 } }, 0.2)
		expect(mind.state.fear).toBeGreaterThan(before)
		expect(out.lookAt).toBe("Bark")
	end)
	it("an injured dog only walks (no trotting) when following", function()
		local breed = Species.breeds.GoldenRetriever
		local b = AnimalBehavior.new({ breed = breed, species = dog, rng = TestKit.seededRng(2) })
		local mind = AnimalMind.new(breed.temperament, Cases.cases.PawLaceration.mind)
		local out = run(b, mind, function()
			return { leaderDist = 12, leaderMoving = true }
		end, 1)
		expect(out.gait).toBe("walk")
		expect(out.params.limp).toBeGreaterThan(0.3)
	end)
end)

---------------------------------------------------------------------------------------------
-- A scripted "player" that physically performs any procedure step by step.
---------------------------------------------------------------------------------------------
local Robot = {}

function Robot.new(logic, clock, ownerId, userId)
	return { logic = logic, clock = clock, owner = ownerId, user = userId, events = {} }
end

local function landmarkPoint(appt, name)
	if name == "Ear" then
		name = "Ear" .. (appt.patient.affectedEar or "L")
	elseif name == "Injury" then
		name = "Paw" .. ((appt.patient.injury and appt.patient.injury.leg) or "FL")
	end
	local l = Cases.landmarks[name]
	return { u = l.u, v = l.v, side = if l.side == "C" then nil else l.side }
end

function Robot.advance(robot, dt)
	robot.clock.advance(dt)
	robot.logic:tickAnimals(robot.owner, dt, function()
		return { leaderDist = 2 }
	end)
end

function Robot.send(robot, appt, action, payload)
	local r = robot.logic:procedureInput(robot.owner, robot.user, appt.id, action, payload, 2)
	if r.event then
		table.insert(robot.events, r.event)
	end
	if r.event == "PulledAway" or r.event == "Struggled" then
		robot.logic:comfort(robot.owner, robot.user, appt.id, "Comfort")
		Robot.advance(robot, 1)
		robot.logic:comfort(robot.owner, robot.user, appt.id, "Pet")
		Robot.advance(robot, 1)
	end
	return r
end

-- Perform the running procedure to completion. Returns the final result.
function Robot.perform(robot, appt)
	local guard = 0
	while appt.running and guard < 2000 do
		guard += 1
		local run = appt.running.run
		local step = Procedures.currentStep(run)
		local k = step.kind
		local r
		if k == "open" then
			r = Robot.send(robot, appt, "open", { target = step.target })
		elseif k == "take" then
			r = Robot.send(robot, appt, "take", { tool = step.tool })
		elseif k == "approach" or k == "wait" then
			Robot.advance(robot, 0.5)
			r = Robot.send(robot, appt, "tick", nil)
		elseif k == "pose" then
			r = Robot.send(robot, appt, "requestPose", nil)
			Robot.advance(robot, 0.4)
		elseif k == "place" then
			for _, name in step.points do
				local p = landmarkPoint(appt, name)
				local tries = 0
				repeat
					tries += 1
					r = Robot.send(robot, appt, "place", p)
					Robot.advance(robot, 0.5)
				until r.event == "PointDone"
					or tries > 40
					or not appt.running
					or Procedures.currentStep(appt.running.run) ~= step
				if not appt.running or Procedures.currentStep(appt.running.run) ~= step then
					break
				end
			end
		elseif k == "scan" then
			for _, side in step.sides do
				for gu = 0, 5 do
					for gv = 0, 5 do
						r = Robot.send(robot, appt, "scan", { u = (gu + 0.5) / 6, v = (gv + 0.5) / 6, side = side })
					end
				end
				-- dwell on every spot (a real player pans to them in the magnified view)
				local spots = {}
				local f = appt.patient.case.findings[step.source]
				if step.source == "Otoscope" then
					spots = f[side]
				else
					for _, s in f.spots do
						local pt = s
						if s.landmark then
							local l = Cases.landmarks[s.landmark]
							pt = { u = l.u, v = l.v, side = l.side }
						end
						if (pt.side or "L") == side then
							table.insert(spots, pt)
						end
					end
				end
				for _, spot in spots do
					Robot.send(robot, appt, "scan", { u = spot.u, v = spot.v, side = side })
					robot.clock.advance(0.6)
					Robot.send(robot, appt, "scan", { u = spot.u, v = spot.v, side = side })
				end
			end
			r = Robot.send(robot, appt, "finishScan", nil)
		elseif k == "stroke" then
			local region = appt.running.run.def
			_ = region
			local center = landmarkPoint(appt, step.region)
			local size = if step.region == "Ear" then 0.08 elseif step.region == "Injury" then 0.07 else 0.45
			local pts = {}
			for gv = 0, 5 do
				for gu = 0, 5 do
					local u = center.u - size + (gu + 0.5) / 6 * size * 2
					local v = center.v - size + (gv + 0.5) / 6 * size * 2
					table.insert(
						pts,
						{ u = if gv % 2 == 0 then u else center.u + size - (gu + 0.5) / 6 * size * 2, v = v }
					)
				end
			end
			for i = 1, #pts, 12 do
				r = Robot.send(robot, appt, "stroke", { points = table.move(pts, i, math.min(i + 11, #pts), 1, {}) })
				robot.clock.advance(0.3)
				if not appt.running or Procedures.currentStep(appt.running.run) ~= step then
					break
				end
			end
		elseif k == "wrap" then
			r = Robot.send(robot, appt, "wrap", { delta = math.pi / 3 })
			robot.clock.advance(0.1)
		elseif k == "pull" then
			r = Robot.send(robot, appt, "pull", { distance = 0.2, dt = 0.2 })
			robot.clock.advance(0.2)
		elseif k == "dose" then
			r = Robot.send(robot, appt, "dose", { value = Procedures.doseTarget(run, step) })
		elseif k == "record" then
			r = Robot.send(robot, appt, "record", nil)
		end
		if r and r.done then
			return r
		end
	end
	error("procedure did not finish: " .. tostring(appt.running and appt.running.id))
end

local function memoryStore()
	return {
		data = {},
		update = function(self, key, transform)
			local new = transform(self.data[key] and M.DataService.deepCopy(self.data[key]))
			if new ~= nil then
				self.data[key] = M.DataService.deepCopy(new)
			end
			return new, nil
		end,
	}
end

---------------------------------------------------------------------------------------------
describe("Procedures (physical steps, server-validated)", function()
	local function patientFor(caseId, breedName)
		local breed = Species.breeds[breedName or "GoldenRetriever"]
		local sp = Species.species[breed.species]
		local case = Cases.cases[caseId]
		return {
			case = case,
			vitals = Cases.trueVitals(sp, case, constRng(0.5)),
			weightLb = 60,
			injury = case.injury,
			affectedEar = "L",
			speciesDef = sp,
		}
	end
	it("steps must happen in order — no skipping to the reading", function()
		local run =
			Procedures.start("Stethoscope", { patient = patientFor("KennelCough"), now = 0, rng = constRng(0.1) })
		local r = Procedures.input(run, "place", Cases.landmarks.Heart, { now = 0, vetDist = 1 })
		expect(r.ok).toBe(false)
		r = Procedures.input(run, "open", { target = "Fridge" }, { now = 0 })
		expect(r.ok).toBe(false)
		r = Procedures.input(run, "open", { target = "EquipmentCabinet" }, { now = 0 })
		expect(r.ok).toBe(true)
	end)
	it("holding the stethoscope needs real time on the right spot; misses don't count", function()
		local run =
			Procedures.start("Stethoscope", { patient = patientFor("KennelCough"), now = 0, rng = constRng(0.1) })
		Procedures.input(run, "open", { target = "EquipmentCabinet" }, { now = 0 })
		Procedures.input(run, "take", { tool = "Stethoscope" }, { now = 0 })
		Procedures.input(run, "tick", nil, { now = 0, vetDist = 9 })
		expect(run.stepIndex).toBe(3) -- too far away
		Procedures.input(run, "tick", nil, { now = 0, vetDist = 2 })
		expect(run.stepIndex).toBe(4)
		local miss = Procedures.input(run, "place", { u = 0.1, v = 0.1, side = "L" }, { now = 1 })
		expect(miss.event).toBe("Miss")
		local heart = { u = 0.66, v = 0.42, side = "L" }
		expect(Procedures.input(run, "place", heart, { now = 1 }).event).toBe("Placed")
		expect(Procedures.input(run, "place", heart, { now = 2 }).event).toBe("Holding")
		local done = Procedures.input(run, "place", heart, { now = 3.6 })
		expect(done.event).toBe("PointDone")
		expect(type(done.reading.heartRate)).toBe("number")
	end)
	it("a stressed patient reads a higher heart rate than a calm one", function()
		local function hr(stress)
			local run =
				Procedures.start("Stethoscope", { patient = patientFor("Wellness"), now = 0, rng = constRng(0.1) })
			run.stepIndex = 4
			local mind = AnimalMind.new(Species.breeds.GoldenRetriever.temperament)
			mind.state.stress = stress
			local ctx = { now = 0, mind = mind }
			Procedures.input(run, "place", { u = 0.66, v = 0.42, side = "L" }, ctx)
			ctx.now = 3
			mind.state.stress = stress
			return Procedures.input(run, "place", { u = 0.66, v = 0.42, side = "L" }, ctx).reading.heartRate
		end
		expect(hr(0.7)).toBeGreaterThan(hr(0.05) + 15)
	end)
	it("an uncooperative patient pulls away and progress resets", function()
		local run = Procedures.start("Thermometer", { patient = patientFor("Wellness"), now = 0, rng = constRng(0.99) })
		run.stepIndex = 5
		local mind = AnimalMind.new(Species.breeds.Chihuahua.temperament, { fear = 0.4 })
		local r = Procedures.input(run, "place", { u = 0.3, v = 0.45, side = "L" }, { now = 0, mind = mind })
		expect(r.event).toBe("PulledAway")
		expect(run.state.holding).toBeNil()
	end)
	it("otoscope only reveals findings you actually look at", function()
		local run = Procedures.start("Otoscope", { patient = patientFor("Otitis"), now = 0, rng = constRng(0.1) })
		run.stepIndex = 4
		local ctx = { now = 0 }
		-- not enough coverage yet
		Procedures.input(run, "scan", { u = 0.5, v = 0.5, side = "L" }, ctx)
		expect(Procedures.input(run, "finishScan", nil, ctx).ok).toBe(false)
		for gu = 0, 5 do
			for gv = 0, 5 do
				Procedures.input(run, "scan", { u = (gu + 0.5) / 6, v = (gv + 0.5) / 6, side = "L" }, ctx)
				Procedures.input(run, "scan", { u = (gu + 0.5) / 6, v = (gv + 0.5) / 6, side = "R" }, ctx)
			end
		end
		-- swept but never dwelt on a spot → nothing found
		local r = Procedures.input(run, "finishScan", nil, ctx)
		expect(r.ok).toBe(true)
		expect(#r.found).toBe(0)
	end)
	it("tick removal fails if you yank too fast", function()
		local run = Procedures.start("RemoveTicks", { patient = patientFor("Ticks"), now = 0, rng = constRng(0.1) })
		run.stepIndex = 4
		local r = Procedures.input(run, "pull", { distance = 0.5, dt = 0.05 }, { now = 0 })
		expect(r.event).toBe("TooFast")
	end)
	it("weight-based dose: wrong amounts are refused", function()
		local run =
			Procedures.start("Administer", { patient = patientFor("KennelCough"), now = 0, rng = constRng(0.1) })
		run.stepIndex = 3
		expect(Procedures.input(run, "dose", { value = 20 }, { now = 0 }).ok).toBe(false)
		expect(Procedures.input(run, "dose", { value = 6 }, { now = 0 }).ok).toBe(true)
	end)
	it("rejects garbage payloads (NaN, huge stroke batches, teleporting samples)", function()
		local run =
			Procedures.start("CleanWound", { patient = patientFor("PawLaceration"), now = 0, rng = constRng(0.1) })
		run.stepIndex = 5
		local nan = 0 / 0
		expect(Procedures.input(run, "stroke", { points = { { u = nan, v = 0.1 } } }, { now = 0 }).event).toBe(
			"Stroking"
		)
		local many = {}
		for i = 1, 40 do
			many[i] = { u = 0.7, v = 0.05 }
		end
		expect(Procedures.input(run, "stroke", { points = many }, { now = 0 }).ok).toBe(false)
		local jumpy = {}
		for i = 1, 20 do
			jumpy[i] = { u = if i % 2 == 0 then 0.65 else 0.95, v = if i % 2 == 0 then 0 else 0.5 }
		end
		local r = Procedures.input(run, "stroke", { points = jumpy }, { now = 0 })
		expect((r.progress or 0) < 0.2).toBe(true)
	end)
end)

---------------------------------------------------------------------------------------------
describe("Clinic management", function()
	local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(11) })
	local cc = logic.clinicConfig
	it("xp curve is increasing and first level-up takes a handful of patients", function()
		for lvl = 2, 50 do
			assert(Clinic.xpForLevel(lvl) > Clinic.xpForLevel(lvl - 1))
		end
		local patients = math.ceil(Clinic.xpForLevel(2) / 45)
		expect(patients >= 4 and patients <= 8).toBe(true)
	end)
	it("orders arrive as boxes; stock only rises when shelved", function()
		local s = logic:newClinicState()
		local before = s.stock.Bandage
		local r = Clinic.order(cc, s, "Bandage", 5)
		expect(r.ok).toBe(true)
		expect(s.stock.Bandage).toBe(before)
		expect(s.cash).toBe(250 - 15)
		Clinic.shelve(s, r.box.id)
		expect(s.stock.Bandage).toBe(before + 5)
		expect(Clinic.order(cc, s, "Bandage", 0).ok).toBe(false)
		expect(Clinic.order(cc, s, "Bandage", 1.5).ok).toBe(false)
		expect(Clinic.order(cc, s, "Gold", 1).ok).toBe(false)
	end)
	it("placement: grid snap, bounds, overlap, rotation, room type, refunds", function()
		local s = logic:newClinicState()
		s.cash = 1000
		expect(Clinic.place(cc, s, "PlantTall", "Waiting", 15, 8, 0).ok).toBe(true)
		expect(Clinic.place(cc, s, "PlantTall", "Waiting", 15, 8, 0).ok).toBe(false) -- overlap
		expect(Clinic.place(cc, s, "WaitingBench", "Waiting", 18, 5, 0).ok).toBe(false) -- out of bounds
		expect(Clinic.place(cc, s, "WaitingBench", "Waiting", 18, 5, 90).ok).toBe(true) -- rotated fits
		expect(Clinic.place(cc, s, "PlantTall", "Waiting", 1.5, 1, 0).ok).toBe(false) -- off grid
		expect(Clinic.place(cc, s, "ExamTable", "Waiting", 2, 8, 0).ok).toBe(false) -- wrong room
		expect(Clinic.place(cc, s, "XRayMachine", "Exam1", 0, 4, 0).ok).toBe(false) -- locked/room
		local cash = s.cash
		local id
		for pid, p in s.placements do
			if p.item == "PlantTall" and p.x == 15 then
				id = pid
			end
		end
		expect(Clinic.remove(cc, s, id).refund).toBe(22)
		expect(s.cash).toBe(cash + 22)
	end)
	it("can't remove the last exam table", function()
		local s = logic:newClinicState()
		for id, p in s.placements do
			if p.item == "ExamTable" then
				expect(Clinic.remove(cc, s, id).ok).toBe(false)
			end
		end
	end)
	it("expansion rooms are level-gated empty shells you furnish yourself", function()
		local s = logic:newClinicState()
		s.cash = 99999
		expect(Clinic.buyRoom(cc, s, "Exam2").ok).toBe(false)
		s.level = 3
		expect(Clinic.buyRoom(cc, s, "Exam2").ok).toBe(true)
		local count = 0
		for _, p in s.placements do
			if p.room == "Exam2" then
				count += 1
			end
		end
		expect(count).toBe(0)
	end)
	it("daily bills never crash the game: shortfall becomes debt that blocks expansion", function()
		local s = logic:newClinicState()
		s.cash = 10
		local r = Clinic.endDay(cc, s)
		expect(s.cash).toBe(0)
		expect(r.debt).toBeGreaterThan(0)
		s.level = 3
		s.cash = 5000
		expect(Clinic.hire(cc, s, "Receptionist", "Ana").ok).toBe(false)
		Clinic.payDebt(s)
		expect(Clinic.hire(cc, s, "Receptionist", "Ana").ok).toBe(true)
		expect(Clinic.dailyExpenses(cc, s).wages).toBe(45)
	end)
	it("reputation is a smoothed rolling average", function()
		local s = logic:newClinicState()
		Clinic.addRating(cc, s, 5)
		expect(s.reputation).toBeNear(3.67, 0.01)
		for _ = 1, 30 do
			Clinic.addRating(cc, s, 5)
		end
		expect(s.reputation).toBeGreaterThan(4.7)
		expect(Clinic.arrivalInterval(cc, s)).toBeLessThan(cc.arrival.base)
	end)
	it("permissions: visitors can't do anything, receptionists can't treat or build", function()
		expect(Clinic.can("Visitor", "build")).toBe(false)
		expect(Clinic.can("Visitor", "treat")).toBe(false)
		expect(Clinic.can("Receptionist", "checkIn")).toBe(true)
		expect(Clinic.can("Receptionist", "treat")).toBe(false)
		expect(Clinic.can("Vet", "build")).toBe(false)
		expect(Clinic.can("Owner", "build")).toBe(true)
	end)
	it("clinic name validation", function()
		expect(Clinic.validName("Happy Paws Vet")).toBe(true)
		expect(Clinic.validName("ab")).toBe(false)
		expect(Clinic.validName(string.rep("a", 40))).toBe(false)
		expect(Clinic.validName("<script>")).toBe(false)
		expect(Clinic.validName(42)).toBe(false)
	end)
end)

---------------------------------------------------------------------------------------------
describe("Showcase appointment: golden retriever, start to finish", function()
	local clock = TestKit.clock(1000)
	local store = memoryStore()
	local OWNER, FRIEND = 101, 202
	local function boot()
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(42), now = clock.now })
		local data = M.DataService.new({
			store = store,
			template = GameLogic.profileTemplate(M),
			sessionId = "test",
			now = clock.now,
			wait = function() end,
		})
		return logic, data
	end
	local logic, data = boot()
	local profile = data:load(OWNER)
	logic:loadPlayer(OWNER, profile)
	local robot = Robot.new(logic, clock, OWNER, OWNER)
	local appt
	it("the first customer arrives on their own with a golden retriever", function()
		local events = {}
		for _ = 1, 10 do
			clock.advance(1)
			for _, e in logic:tick(OWNER, 1) do
				table.insert(events, e)
			end
		end
		expect(#events >= 1 and events[1].kind == "Arrived").toBe(true)
		appt = logic.clinics[OWNER].appts[events[1].id]
		expect(appt.patient.breed).toBe("GoldenRetriever")
		expect(appt.caseId).toBe("KennelCough")
		expect(string.find(appt.customer.complaint, appt.patient.name, 1, true) ~= nil).toBe(true)
	end)
	it("the dog walks beside its owner (follow state, real gait speed)", function()
		logic:tickAnimals(OWNER, 0.2, function()
			return { leaderDist = 4, leaderMoving = true }
		end)
		expect(appt.anim.state == "Follow" or appt.anim.state == "Sniff").toBe(true)
		expect(appt.anim.params.tailWag).toBeGreaterThan(0.3)
	end)
	it("check-in at reception; visitors can't, the owner can", function()
		logic:reachReception(OWNER, appt.id)
		logic:join(OWNER, FRIEND)
		expect(logic:checkIn(OWNER, FRIEND, appt.id).ok).toBe(false)
		expect(logic:checkIn(OWNER, OWNER, appt.id).ok).toBe(true)
		expect(appt.phase).toBe("Waiting")
		local snap = logic:snapshot(OWNER, OWNER)
		expect(snap.tutorial.id).toBe("Call")
	end)
	it("the hidden diagnosis is never in the client snapshot", function()
		local snap = logic:snapshot(OWNER, FRIEND)
		local function scan(t, depth)
			if depth > 6 then
				return
			end
			for k, v in t do
				assert(k ~= "case" and k ~= "diagnosisId", "leaked key " .. tostring(k))
				if type(v) == "string" then
					assert(v ~= "KennelCough", "leaked case id")
				elseif type(v) == "table" then
					scan(v, depth + 1)
				end
			end
		end
		scan(snap, 0)
	end)
	it("calling the patient claims it; a second vet can't steal it", function()
		logic:setRole(OWNER, OWNER, FRIEND, "Vet")
		expect(logic:callPatient(OWNER, OWNER, appt.id, "Exam1").ok).toBe(true)
		expect(logic:callPatient(OWNER, FRIEND, appt.id, "Exam1").ok).toBe(false)
		expect(appt.phase).toBe("ToRoom")
		logic:tickAnimals(OWNER, 0.2, function()
			return { leaderDist = 3, leaderMoving = true, atThreshold = true }
		end)
		logic:arriveInRoom(OWNER, appt.id)
		expect(appt.phase).toBe("InRoom")
	end)
	it("a big dog has to be helped up front paws first, then the back", function()
		expect(logic:helpOntoTable(OWNER, OWNER, appt.id, "pickUp").ok).toBe(false)
		local tries = 0
		while appt.phase ~= "OnTable" and tries < 10 do
			tries += 1
			local step = if (appt.tableSteps or 0) == 0 then "liftFront" else "liftBack"
			local r = logic:helpOntoTable(OWNER, OWNER, appt.id, step)
			if not r.ok then
				logic:comfort(OWNER, OWNER, appt.id, "Pet")
				clock.advance(1)
			end
		end
		expect(appt.phase).toBe("OnTable")
		for _ = 1, 20 do
			Robot.advance(robot, 0.2)
		end
		expect(appt.anim.state).toBe("Table")
		expect(appt.anim.pose).toBe("Sit")
	end)
	it("petting a friendly golden makes it lean in", function()
		clock.advance(1)
		local r = logic:comfort(OWNER, OWNER, appt.id, "Pet")
		expect(r.ok).toBe(true)
		expect(r.reaction == "Lean" or r.reaction == "Accept").toBe(true)
		expect(logic:comfort(OWNER, OWNER, appt.id, "Pet").ok).toBe(false) -- cooldown
	end)
	it("stethoscope: cabinet → pick up → listen to heart + both lungs → chart", function()
		expect(logic:beginExam(OWNER, FRIEND, appt.id, "Stethoscope").ok).toBe(false) -- not FRIEND's patient
		expect(logic:beginExam(OWNER, OWNER, appt.id, "Stethoscope").ok).toBe(true)
		expect(logic:beginExam(OWNER, OWNER, appt.id, "Thermometer").ok).toBe(false) -- one at a time
		local r = Robot.perform(robot, appt)
		expect(r.done).toBe(true)
		expect(string.find(r.summary, "Harsh", 1, true) ~= nil).toBe(true)
		expect(#appt.chart >= 2).toBe(true)
	end)
	it("thermometer: drawer → stand pose → hold → wait for the beep → fever", function()
		expect(logic:beginExam(OWNER, OWNER, appt.id, "Thermometer").ok).toBe(true)
		local r = Robot.perform(robot, appt)
		expect(r.done).toBe(true)
		expect(string.find(r.summary, "FEVER", 1, true) ~= nil).toBe(true)
		expect(appt.behavior.pose.current).toBe("Stand")
	end)
	it("locked exams can't be used at level 1", function()
		expect(logic:beginExam(OWNER, OWNER, appt.id, "XRay").ok).toBe(false)
	end)
	it("diagnosis from the evidence, then treatment consumes supplies", function()
		expect(logic:diagnose(OWNER, OWNER, appt.id, "KennelCough").ok).toBe(true)
		expect(logic:beginExam(OWNER, OWNER, appt.id, "Otoscope").ok).toBe(false)
		local syrup = logic.clinics[OWNER].state.stock.CoughSyrup
		expect(logic:beginTreatment(OWNER, OWNER, appt.id, "CoughMeds").ok).toBe(true)
		local stressBefore = appt.patient.mind.state.stress
		local r = Robot.perform(robot, appt)
		expect(r.done).toBe(true)
		expect(r.relief).toBe(true)
		expect(logic.clinics[OWNER].state.stock.CoughSyrup).toBe(syrup - 1)
		expect(appt.phase).toBe("Treated")
		expect(appt.patient.mind.state.stress <= stressBefore + 0.05).toBe(true)
	end)
	it("the dog visibly becomes more comfortable after treatment", function()
		for _ = 1, 50 do
			Robot.advance(robot, 0.2)
		end
		expect(appt.anim.params.tailWag).toBeGreaterThan(0.3)
		expect(appt.anim.params.tremble).toBe(0)
	end)
	it("checkout: invoice, payment, xp, rating — then the reunion and leaving", function()
		expect(logic:finishVisit(OWNER, OWNER, appt.id).ok).toBe(true)
		local cashBefore = logic.clinics[OWNER].state.cash
		local r = logic:pay(OWNER, OWNER, appt.id)
		expect(r.ok).toBe(true)
		expect(r.bill.correct).toBe(true)
		expect(r.bill.total).toBe(50 + 10 + 35)
		expect(r.bill.stars >= 4).toBe(true)
		expect(logic.clinics[OWNER].state.cash).toBe(cashBefore + r.bill.total)
		expect(logic.clinics[OWNER].state.xp).toBe(40)
		expect(r.bill.followUp).toBe(false)
		expect(appt.phase).toBe("Leaving")
		Robot.advance(robot, 0.2)
		expect(appt.anim.state).toBe("Excited")
		logic:customerLeft(OWNER, appt.id)
		expect(appt.phase).toBe("Done")
		expect(logic:snapshot(OWNER, OWNER).tutorial.id).toBe("NameClinic")
	end)
	it("save → reload keeps cash, xp, stock, layout and tutorial progress", function()
		local cash = logic.clinics[OWNER].state.cash
		logic:writeProfile(OWNER, profile)
		expect(data:release(OWNER)).toBe(true)
		logic:unloadPlayer(OWNER)
		local logic2, data2 = boot()
		local p2 = data2:load(OWNER)
		logic2:loadPlayer(OWNER, p2)
		local s = logic2.clinics[OWNER].state
		expect(s.cash).toBe(cash)
		expect(s.xp).toBe(40)
		expect(s.patientsTreated).toBe(1)
		local n = 0
		for _ in s.placements do
			n += 1
		end
		expect(n).toBe(#Config.startLayout)
		expect(logic2:snapshot(OWNER, OWNER).tutorial.id).toBe("NameClinic")
	end)
end)

---------------------------------------------------------------------------------------------
describe("Wrong diagnosis has manageable consequences", function()
	local clock = TestKit.clock(5000)
	local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(8), now = clock.now })
	local OWNER = 7
	logic:loadPlayer(OWNER, GameLogic.profileTemplate(M))
	local state = logic.clinics[OWNER].state
	state.patientsTreated = 3 -- skip the showcase patient
	local robot = Robot.new(logic, clock, OWNER, OWNER)
	it("pays less, rates lower, and the pet comes back for a follow-up", function()
		local appt = logic:spawnPatient(OWNER, { breed = "Beagle", caseId = "Otitis" })
		logic:reachReception(OWNER, appt.id)
		logic:checkIn(OWNER, OWNER, appt.id)
		logic:callPatient(OWNER, OWNER, appt.id, "Exam1")
		logic:arriveInRoom(OWNER, appt.id)
		for _ = 1, 10 do
			if appt.phase == "OnTable" then
				break
			end
			local step = if (appt.tableSteps or 0) == 0 then "pickUp" else "placeOnTable"
			if not logic:helpOntoTable(OWNER, OWNER, appt.id, step).ok then
				clock.advance(1)
				logic:comfort(OWNER, OWNER, appt.id, "Comfort")
			end
		end
		expect(appt.phase).toBe("OnTable")
		logic:beginExam(OWNER, OWNER, appt.id, "Thermometer")
		Robot.perform(robot, appt)
		logic:diagnose(OWNER, OWNER, appt.id, "KennelCough") -- wrong
		logic:finishVisit(OWNER, OWNER, appt.id)
		local r = logic:pay(OWNER, OWNER, appt.id)
		expect(r.bill.correct).toBe(false)
		expect(r.bill.total < Cases.cases.Otitis.basePay).toBe(true)
		expect(r.bill.stars <= 2.5).toBe(true)
		expect(#state.followUps).toBe(1)
		local back = logic:spawnPatient(OWNER, { followUp = table.remove(state.followUps, 1) })
		expect(back.followUp).toBe(true)
		expect(back.caseId).toBe("Otitis")
		expect(back.patient.name).toBe(appt.patient.name)
	end)
end)

---------------------------------------------------------------------------------------------
describe("Every level-1/2 case can be fully solved by physically doing the work", function()
	for _, caseId in Cases.caseNames do
		local case = Cases.cases[caseId]
		for _, speciesName in case.species do
			it(caseId .. " (" .. speciesName .. ")", function()
				local clock = TestKit.clock(9000)
				local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(#caseId * 13), now = clock.now })
				local OWNER = 55
				logic:loadPlayer(OWNER, GameLogic.profileTemplate(M))
				local state = logic.clinics[OWNER].state
				state.level = 2
				state.patientsTreated = 5
				for id in state.stock do
					state.stock[id] = 20
				end
				local robot = Robot.new(logic, clock, OWNER, OWNER)
				local breed = if speciesName == "Cat" then "DomesticShorthair" else "Beagle"
				local appt = logic:spawnPatient(OWNER, { breed = breed, caseId = caseId })
				logic:reachReception(OWNER, appt.id)
				logic:checkIn(OWNER, OWNER, appt.id)
				assert(logic:callPatient(OWNER, OWNER, appt.id, "Exam1").ok)
				logic:arriveInRoom(OWNER, appt.id)
				if speciesName == "Cat" then
					logic:openCarrier(OWNER, OWNER, appt.id)
				end
				for _ = 1, 20 do
					if appt.phase == "OnTable" then
						break
					end
					local step = if (appt.tableSteps or 0) == 0 then "pickUp" else "placeOnTable"
					if not logic:helpOntoTable(OWNER, OWNER, appt.id, step).ok then
						clock.advance(1)
						logic:comfort(OWNER, OWNER, appt.id, "Treat")
						clock.advance(1)
						logic:comfort(OWNER, OWNER, appt.id, "Comfort")
					end
				end
				assert(appt.phase == "OnTable", "never got onto the table")
				for _, examId in case.keyExams do
					local r = logic:beginExam(OWNER, OWNER, appt.id, examId)
					assert(r.ok, examId .. ": " .. tostring(r.message))
					Robot.perform(robot, appt)
				end
				assert(logic:diagnose(OWNER, OWNER, appt.id, case.diagnosis).ok)
				for _, t in case.treatments do
					local r = logic:beginTreatment(OWNER, OWNER, appt.id, t)
					assert(r.ok, t .. ": " .. tostring(r.message))
					Robot.perform(robot, appt)
				end
				assert(appt.phase == "Treated", "phase " .. appt.phase)
				assert(logic:finishVisit(OWNER, OWNER, appt.id).ok)
				local paid = logic:pay(OWNER, OWNER, appt.id)
				assert(paid.ok and paid.bill.correct, "not correct")
				assert(paid.bill.stars >= 3.5, "stars " .. paid.bill.stars)
				if case.treatments[1] == "Bandage" or table.find(case.treatments, "Bandage") then
					assert(#appt.bandages == 1, "bandage not visible on the animal")
				end
			end)
		end
	end
end)

---------------------------------------------------------------------------------------------
describe("Busy clinic", function()
	it("arrivals respect the active-appointment cap and impatient customers walk out", function()
		local clock = TestKit.clock(0)
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(99), now = clock.now })
		logic:loadPlayer(1, GameLogic.profileTemplate(M))
		local walked = 0
		for _ = 1, 1200 do
			clock.advance(1)
			for _, e in logic:tick(1, 1) do
				if e.kind == "WalkedOut" then
					walked += 1
				end
			end
			for _, appt in logic.clinics[1].appts do
				if appt.phase == "Arriving" then
					logic:reachReception(1, appt.id)
					logic:checkIn(1, 1, appt.id)
				end
			end
			assert(logic:activeCount(logic.clinics[1]) <= logic:maxActive(logic.clinics[1]))
		end
		expect(walked >= 1).toBe(true)
		expect(logic.clinics[1].state.reputation).toBeLessThan(3)
	end)
	it("the waiting list puts emergencies first", function()
		local clock = TestKit.clock(0)
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(5), now = clock.now })
		logic:loadPlayer(1, GameLogic.profileTemplate(M))
		logic.clinics[1].state.patientsTreated = 2
		logic:spawnPatient(1)
		clock.advance(5)
		local e = logic:spawnPatient(1, { emergency = true })
		expect(logic:waitingList(1)[1].id).toBe(e.id)
	end)
	it("a day ends with rent + utilities and a finance summary", function()
		local clock = TestKit.clock(0)
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(5), now = clock.now })
		logic:loadPlayer(1, GameLogic.profileTemplate(M))
		local cash = logic.clinics[1].state.cash
		local events = logic:tick(1, Config.clinic.dayLengthSeconds)
		local ended = false
		for _, ev in events do
			if ev.kind == "DayEnded" then
				ended = true
			end
		end
		expect(ended).toBe(true)
		expect(logic.clinics[1].state.cash).toBe(cash - (40 + 3 * 15 + 15 + 3 * 5))
		expect(logic.clinics[1].state.day).toBe(2)
	end)
	it("100 animals simulate in one loop quickly (no per-animal scripts)", function()
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(5) })
		logic:loadPlayer(1, GameLogic.profileTemplate(M))
		logic.clinics[1].state.patientsTreated = 1
		for _ = 1, 100 do
			logic:spawnPatient(1)
		end
		local t0 = os.clock()
		for _ = 1, 50 do
			logic:tickAnimals(1, 0.2, function()
				return { leaderDist = 3 }
			end)
		end
		local perTick = (os.clock() - t0) / 50
		expect(perTick).toBeLessThan(0.02) -- < 20 ms for 100 animals at 5 Hz
	end)
end)

local results = TestKit.results()
for _, failure in results.failures do
	print("FAIL " .. failure)
end
print(string.format("\nMy Vet Office: %d passed, %d failed", results.passed, results.failed))
if results.failed > 0 then
	process.exit(1)
end
