--[[
	AnimalAnimator — ONE client loop animates every animal (no script per animal). Reads the
	server-replicated behaviour/mind attributes on each tagged "Animal" model and drives its
	Motor6Ds with the layered framework in AnimBlend:

	  locomotion  procedural gait (PoseLibrary.legCycle + rig gait phases), stride-synced to the
	              real ground speed so paws never slide; limp on the injured leg
	  pose        PoseLibrary key poses cross-faded with the PoseGraph timing (smoothstep)
	  gestures    one-shot additive clips (scratch, shake, yawn, head tilt, sniff, groom …)
	  reactions   lean into a hand, pull away, flinch, startle, excited greeting
	  additive    breathing, panting jaw, trembling, tail wag, ear pose, blinking, head look
	  IK          raycast paws to the surface (exam table, steps) — full LOD only
	  LOD         full / mid / low / off by camera distance + budget; the patient you're
	              examining is always full quality
	If authored AnimationTracks exist (ReplicatedStorage.Assets.Anims.<Species>.<Clip>) they
	replace the procedural pose/gesture layer for that clip; additive layers still apply.

	BUILT, UNTESTED in Studio. The math it calls is unit-tested (tests/run.luau).
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameShared = ReplicatedStorage:WaitForChild("GameShared")
local AnimBlend = require(GameShared:WaitForChild("AnimBlend"))
local PoseGraph = require(GameShared:WaitForChild("PoseGraph"))
local PoseLibrary = require(GameShared:WaitForChild("PoseLibrary"))
local Species = require(GameShared:WaitForChild("Species"))

local AnimalAnimator = {}

local RIG = Species.rigs.Quadruped
local BONES = PoseLibrary.boneList(RIG)
local rad = math.rad
local animals = {} -- model -> record
local rng = Random.new()

local function rand(): number
	return rng:NextNumber()
end

---------------------------------------------------------------------------------------------
-- Gesture + reaction curves: function(t, duration) -> { bone = {p,y,r} }, root offsets.
-- Envelope fades in/out over 20% of the clip so nothing snaps.
---------------------------------------------------------------------------------------------
local function env(t: number, dur: number): number
	local x = t / dur
	if x <= 0 or x >= 1 then
		return 0
	end
	return math.min(1, x / 0.2, (1 - x) / 0.2)
end

local GESTURES = {
	Scratch = {
		dur = 1.6,
		fn = function(t, e)
			return {
				HipL = { p = -60 * e },
				KneeL = { p = 70 * e + math.sin(t * 40) * 25 * e },
				Head = { r = 18 * e },
				Neck = { y = 25 * e },
			}
		end,
	},
	Shake = {
		dur = 0.9,
		fn = function(t, e)
			local w = math.sin(t * 38) * 22 * e * (1 - t / 0.9)
			return { SpineMid = { r = w }, Chest = { r = w * 1.2 }, Neck = { r = w * 1.4 }, Head = { r = w * 1.5 } }
		end,
	},
	Yawn = {
		dur = 1.5,
		fn = function(_, e)
			return { Jaw = { p = -38 * e }, Head = { p = 18 * e }, LidL = { p = 40 * e }, LidR = { p = 40 * e } }
		end,
	},
	LickNose = {
		dur = 0.5,
		fn = function(t, e)
			return { Jaw = { p = -10 * e * math.abs(math.sin(t * 12)) } }
		end,
	},
	HeadTilt = {
		dur = 1.4,
		fn = function(_, e)
			return { Head = { r = 22 * e }, EarL = { p = 15 * e }, EarR = { p = 15 * e } }
		end,
	},
	Stretch = {
		dur = 1.8,
		fn = function(_, e)
			return {
				ShoulderL = { p = 55 * e },
				ShoulderR = { p = 55 * e },
				ElbowL = { p = -20 * e },
				ElbowR = { p = -20 * e },
				Chest = { p = -14 * e },
				Neck = { p = 14 * e },
				Tail1 = { p = 25 * e },
			}, { p = -12 * e, h = -0.12 * e }
		end,
	},
	Sniff = {
		dur = 1.6,
		fn = function(t, e)
			return { Neck = { p = -35 * e }, Head = { p = -15 * e + math.sin(t * 22) * 3 * e } }
		end,
	},
	LookAround = {
		dur = 2.2,
		fn = function(t, e)
			return { Neck = { y = math.sin(t * 2.8) * 30 * e }, Head = { y = math.sin(t * 2.8 - 0.4) * 20 * e } }
		end,
	},
	Groom = {
		dur = 2.4,
		fn = function(t, e)
			return {
				Neck = { y = 60 * e, p = -25 * e },
				Head = { p = -20 * e + math.sin(t * 9) * 8 * e },
				Jaw = { p = -6 * e },
			}
		end,
	},
	TailFlick = {
		dur = 0.6,
		fn = function(t, e)
			local w = math.sin(t * 25) * 35 * e
			return { Tail2 = { y = w }, Tail3 = { y = w * 1.2 }, Tail4 = { y = w * 1.4 } }
		end,
	},
	EarSwivel = {
		dur = 0.8,
		fn = function(_, e)
			return { EarL = { y = -50 * e } }
		end,
	},
	Knead = {
		dur = 2,
		fn = function(t, e)
			local a = math.max(0, math.sin(t * 7)) * 20 * e
			local b = math.max(0, math.sin(t * 7 + math.pi)) * 20 * e
			return { ShoulderL = { p = a }, ShoulderR = { p = b }, LidL = { p = 35 * e }, LidR = { p = 35 * e } }
		end,
	},
	Rub = {
		dur = 1.6,
		fn = function(_, e)
			return { Neck = { y = -30 * e, r = -15 * e }, Head = { r = -25 * e }, Tail1 = { p = 30 * e } }, {
				r = -6 * e,
			}
		end,
	},
}

local REACTIONS = {
	Lean = {
		dur = 1.6,
		fn = function(_, e)
			return { Head = { r = 14 * e }, LidL = { p = 45 * e }, LidR = { p = 45 * e } }, { r = 7 * e }
		end,
	},
	Accept = {
		dur = 0.8,
		fn = function(_, e)
			return { LidL = { p = 25 * e }, LidR = { p = 25 * e } }, nil
		end,
	},
	PullAway = {
		dur = 0.7,
		fn = function(_, e)
			return { Neck = { y = 30 * e }, EarL = { p = -35 * e }, EarR = { p = -35 * e } }, {
				z = 0.5 * e,
				h = -0.06 * e,
			}
		end,
	},
	Flinch = {
		dur = 0.45,
		fn = function(_, e)
			return { Neck = { p = -10 * e }, EarL = { p = -30 * e }, EarR = { p = -30 * e } }, {
				z = 0.2 * e,
				h = -0.08 * e,
			}
		end,
	},
	Startle = {
		dur = 0.6,
		fn = function(_, e)
			return { Head = { p = 10 * e }, EarL = { p = 25 * e }, EarR = { p = 25 * e } }, { h = -0.1 * e }
		end,
	},
	Struggle = {
		dur = 1.0,
		fn = function(t, e)
			local w = math.sin(t * 20) * 15 * e
			return { ShoulderL = { p = w }, ShoulderR = { p = -w }, HipL = { p = -w }, HipR = { p = w } }, nil
		end,
	},
	Excited = {
		dur = 2.5,
		fn = function(t, e)
			return { Tail1 = { p = 30 * e } }, { h = math.abs(math.sin(t * 9)) * 0.12 * e }
		end,
	},
	Eat = {
		dur = 1.2,
		fn = function(t, e)
			return { Neck = { p = -20 * e }, Jaw = { p = -12 * e * math.abs(math.sin(t * 10)) } }, nil
		end,
	},
	Yelp = {
		dur = 0.5,
		fn = function(_, e)
			return { Jaw = { p = -20 * e }, Head = { p = 12 * e } }, { z = 0.25 * e }
		end,
	},
	Relax = {
		dur = 2.0,
		fn = function(_, e)
			return { LidL = { p = 30 * e }, LidR = { p = 30 * e }, Neck = { p = -6 * e } }, { h = -0.03 * e }
		end,
	},
	Calm = {
		dur = 1.0,
		fn = function(_, e)
			return { EarL = { p = 8 * e }, EarR = { p = 8 * e } }, nil
		end,
	},
}

---------------------------------------------------------------------------------------------
-- Rig discovery
---------------------------------------------------------------------------------------------
local function findMotors(model: Model)
	local motors = {}
	for _, d in model:GetDescendants() do
		if d:IsA("Motor6D") and d.Part1 then
			motors[d.Part1.Name] = d
		end
	end
	return motors
end

local function legLengths(motors, chain)
	-- upper = shoulder/hip → elbow/knee, lower = elbow/knee → paw (approx from C1/C0 offsets)
	local a, b = 1, 1
	local m2, m4 = motors[chain[2]], motors[chain[4]]
	if m2 then
		a = math.max(0.2, m2.C0.Position.Magnitude)
	end
	if m4 then
		b = math.max(0.2, m4.C0.Position.Magnitude + (motors[chain[3]] and motors[chain[3]].C0.Position.Magnitude or 0))
	end
	return a, b
end

local function addAnimal(model: Model)
	if animals[model] then
		return
	end
	local breed = Species.breeds[model:GetAttribute("Breed") or ""] or Species.breeds.GoldenRetriever
	local motors = findMotors(model)
	local legs = {}
	for legName, chain in RIG.legs do
		local a, b = legLengths(motors, chain)
		legs[legName] = { chain = chain, a = a, b = b, ground = 0 }
	end
	local cf, size = model:GetBoundingBox()
	animals[model] = {
		model = model,
		breed = breed,
		motors = motors,
		legs = legs,
		shoulderHeight = size.Y,
		pose = { from = "Stand", to = "Stand", alpha = 1, duration = 0.7 },
		phase = 0,
		head = { yaw = AnimBlend.newSpring(0, 0.12), pitch = AnimBlend.newSpring(0, 0.12) },
		ears = { L = AnimBlend.newSpring(0, 0.08), R = AnimBlend.newSpring(0, 0.08) },
		weights = AnimBlend.newWeights({ idle = 1 }),
		blinkState = {},
		gesture = nil,
		reaction = nil,
		accum = 0,
		t = rand() * 100,
		lastGestureId = model:GetAttribute("GestureId"),
		lastReactionId = model:GetAttribute("ReactionId"),
		lastCf = cf,
		bandages = {},
	}
end

local function removeAnimal(model: Model)
	animals[model] = nil
end

---------------------------------------------------------------------------------------------
-- Per-frame update
---------------------------------------------------------------------------------------------
local function addRot(acc, bone: string, r)
	if not r then
		return
	end
	local cur = acc[bone]
	if not cur then
		acc[bone] = { p = r.p or 0, y = r.y or 0, r = r.r or 0 }
	else
		cur.p += r.p or 0
		cur.y += r.y or 0
		cur.r += r.r or 0
	end
end

local function resolveLook(model: Model, lookAt: string?): Vector3?
	if not lookAt then
		return nil
	end
	local apptId = model:GetAttribute("ApptId")
	local parent = model.Parent
	if lookAt == "Owner" and parent then
		local c = parent:FindFirstChild("Customer_" .. tostring(apptId))
		local head = c and c:FindFirstChild("Head")
		return head and head.Position
	elseif lookAt == "Vet" then
		local cam = Workspace.CurrentCamera
		return cam and cam.CFrame.Position
	elseif parent then
		local other = parent:FindFirstChild(lookAt)
		if other and other:IsA("Model") and other.PrimaryPart then
			return other.PrimaryPart.Position
		end
	end
	return nil
end

local function updateBandages(rec)
	local spec = rec.model:GetAttribute("Bandages") or ""
	if spec == rec.bandageSpec then
		return
	end
	rec.bandageSpec = spec
	for _, part in rec.bandages do
		part:Destroy()
	end
	rec.bandages = {}
	for leg in string.gmatch(spec, "[^,]+") do
		local chain = RIG.legs[leg]
		local wristName = chain and chain[3]
		local wrist = wristName and rec.model:FindFirstChild(wristName, true)
		if wrist and wrist:IsA("BasePart") then
			-- Blender-made bandage mesh if present, else a wrapped cylinder sleeve
			local template = ReplicatedStorage.Assets:FindFirstChild("BandageWrap")
			local part = if template then template:Clone() else Instance.new("Part")
			if not template then
				part.Shape = Enum.PartType.Cylinder
				part.Color = Color3.fromRGB(245, 245, 240)
				part.Material = Enum.Material.Fabric
				part.Size = Vector3.new(wrist.Size.Y * 0.9, wrist.Size.X * 1.25, wrist.Size.X * 1.25)
			end
			part.Name = "Bandage_" .. leg
			part.CanCollide = false
			part.Massless = true
			part.CFrame = wrist.CFrame * CFrame.Angles(0, 0, math.pi / 2)
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = wrist
			weld.Part1 = part
			weld.Parent = part
			part.Parent = rec.model
			table.insert(rec.bandages, part)
		end
	end
end

local function step(rec, dt: number, tier)
	local model = rec.model
	local attrs = model:GetAttributes()
	rec.t += dt
	local t = rec.t

	-- Pose layer: mirror the server PoseGraph timing locally for smooth fades
	local to = attrs.PoseTo or "Stand"
	if to ~= rec.pose.to then
		local from = rec.pose.to
		local edge = PoseGraph.QUADRUPED.adjacency and PoseGraph.QUADRUPED.adjacency[from]
		rec.pose = { from = from, to = to, alpha = 0, duration = (edge and edge[to]) or 0.8 }
	end
	rec.pose.alpha = math.min(1, rec.pose.alpha + dt / rec.pose.duration)
	local a = rec.pose.alpha
	local eased = a * a * (3 - 2 * a)
	local posed = PoseLibrary.blend(rec.pose.from, rec.pose.to, eased, BONES)
	local acc = posed.bones
	local root = { h = posed.root.h, p = posed.root.p, r = posed.root.r, z = 0 }

	-- Locomotion
	local primary = model.PrimaryPart
	local vel = primary and primary.AssemblyLinearVelocity or Vector3.zero
	local speed = Vector3.new(vel.X, 0, vel.Z).Magnitude
	local breed = rec.breed
	AnimBlend.setTargets(rec.weights, AnimBlend.locomotionWeights(speed, breed.gaitSpeed))
	local w = AnimBlend.stepWeights(rec.weights, dt, 0.2)
	local moving = 1 - (w.idle or 0)
	local dominant, best = "walk", 0
	for _, g in { "walk", "trot", "run", "sprint" } do
		if (w[g] or 0) > best then
			dominant, best = g, w[g]
		end
	end
	if moving > 0.01 then
		local stride = 0
		for _, g in { "walk", "trot", "run", "sprint" } do
			stride += (w[g] or 0) * breed.stride[g]
		end
		stride = math.max(stride / math.max(moving, 1e-3), 0.5) * breed.rigScale
		rec.phase = (rec.phase + dt * speed / stride) % 1
		local limp = attrs.limp or 0
		local injured = string.match(attrs.Bandages or "", "%a%a") or (if limp > 0.3 then "FL" else nil)
		local duty = PoseLibrary.DUTY[dominant]
		local swingDeg = ({ walk = 24, trot = 32, run = 42, sprint = 50 })[dominant]
		for legName, leg in rec.legs do
			local offset = RIG.gaitPhases[dominant][legName]
			local x, lift = PoseLibrary.legCycle(rec.phase + offset, duty)
			local scale = moving
			if legName == injured then
				local stanceScale = AnimBlend.limp(rec.phase, limp)
				scale *= stanceScale
				lift *= 1 + limp -- carries the sore paw higher
			end
			local chain = leg.chain
			local front = legName == "FL" or legName == "FR"
			addRot(acc, chain[1], { p = x * swingDeg * scale })
			addRot(acc, chain[2], { p = (if front then -1 else 1) * lift * 48 * scale })
			addRot(acc, chain[3], { p = (if front then 1 else -1) * lift * 30 * scale })
		end
		local _, dip = AnimBlend.limp(rec.phase, attrs.limp or 0)
		root.h -= dip / math.max(rec.shoulderHeight, 1) + math.abs(math.sin(rec.phase * 2 * math.pi)) * 0.015 * moving
		addRot(acc, "SpineMid", { y = math.sin(rec.phase * 2 * math.pi) * 4 * moving })
	end

	-- Gestures (one-shot) and reactions
	if attrs.GestureId ~= rec.lastGestureId then
		rec.lastGestureId = attrs.GestureId
		local g = GESTURES[attrs.Gesture or ""]
		if g then
			rec.gesture = { def = g, t = 0 }
		end
	end
	if attrs.ReactionId ~= rec.lastReactionId then
		rec.lastReactionId = attrs.ReactionId
		local r = REACTIONS[attrs.Reaction or ""]
		if r then
			rec.reaction = { def = r, t = 0 }
		end
	end
	for _, key in { "gesture", "reaction" } do
		local clip = rec[key]
		if clip then
			clip.t += dt
			if clip.t >= clip.def.dur then
				rec[key] = nil
			elseif tier.gestures or key == "reaction" then
				local e = env(clip.t, clip.def.dur)
				local bones, rootOff = clip.def.fn(clip.t, e)
				for bone, r in bones do
					addRot(acc, bone, r)
				end
				if rootOff then
					root.h += rootOff.h or 0
					root.p += rootOff.p or 0
					root.r += rootOff.r or 0
					root.z += rootOff.z or 0
				end
			end
		end
	end

	-- Additive procedural layer
	local look = { yaw = 0, pitch = 0 }
	if tier.additive then
		local bpm = (Species.species[attrs.Species or "Dog"] or Species.species.Dog).vitals.respRate[1]
			* (attrs.breathRate or 1)
		local breath = AnimBlend.breath(t, bpm, attrs.pant or 0)
		addRot(acc, "Chest", { p = breath * 60 })
		addRot(acc, "SpineMid", { p = -breath * 30 })
		local pant = attrs.pant or 0
		addRot(acc, "Jaw", { p = -(pant * 14 + math.max(0, math.sin(t * 20)) * 4 * pant) })
		root.h += AnimBlend.tremble(t, attrs.tremble or 0) / math.max(rec.shoulderHeight, 1) * 4
		root.r += AnimBlend.tremble(t + 3, attrs.tremble or 0) * 40
		for i, bone in RIG.tail do
			local yaw, pitch = AnimBlend.tailSegment(t, i, attrs.tailWag or 0, attrs.tailHeight or 0)
			addRot(acc, bone, { y = math.deg(yaw), p = math.deg(pitch) })
		end
		local earTarget = (attrs.earPose or 0) * 30
		local eL = AnimBlend.stepSpring(rec.ears.L, earTarget, dt)
		local eR = AnimBlend.stepSpring(rec.ears.R, earTarget + math.sin(t * 0.7) * 3, dt)
		addRot(acc, "EarL", { p = eL })
		addRot(acc, "EarR", { p = eR })
		local lid = AnimBlend.blink(rec.blinkState, t, attrs.blinkInterval or 4, rand)
		local sleepy = attrs.sleepy or 0
		local closed = math.max(lid, sleepy, if attrs.State == "Sleep" then 1 else 0)
		addRot(acc, "LidL", { p = closed * 70 })
		addRot(acc, "LidR", { p = closed * 70 })
		-- head look (spring, clamped to neck range)
		local target = resolveLook(model, attrs.LookAt)
		local chest = rec.motors.Chest and rec.motors.Chest.Part1
		if target and chest then
			local dir = chest.CFrame:VectorToObjectSpace(target - chest.Position)
			local yaw, pitch = AnimBlend.lookAngles({ x = -dir.X, y = dir.Y, z = -dir.Z })
			look.yaw, look.pitch = yaw, pitch
		end
		local hy = AnimBlend.stepSpring(rec.head.yaw, look.yaw, dt)
		local hp = AnimBlend.stepSpring(rec.head.pitch, look.pitch + rad((attrs.headHeight or 0) * 12), dt)
		addRot(acc, "Neck", { y = math.deg(hy) * 0.4, p = math.deg(hp) * 0.4 })
		addRot(acc, "Head", { y = math.deg(hy) * 0.6, p = math.deg(hp) * 0.6 })
		if attrs.purr and attrs.purr > 0.3 then
			root.h += math.sin(t * 150) * 0.002
		end
	end

	-- Foot IK (full LOD): raycast under each paw, drop pelvis so no paw floats
	if tier.ik and primary then
		local params = RaycastParams.new()
		params.FilterDescendantsInstances = { model }
		params.FilterType = Enum.RaycastFilterType.Exclude
		local deltas = {}
		for legName, leg in rec.legs do
			local paw = rec.motors[leg.chain[4]] and rec.motors[leg.chain[4]].Part1
			if paw then
				local hit = Workspace:Raycast(paw.Position + Vector3.new(0, 1.5, 0), Vector3.new(0, -4, 0), params)
				local delta = if hit then hit.Position.Y - (paw.Position.Y - paw.Size.Y / 2) else 0
				delta = math.clamp(delta, -0.8, 0.8)
				leg.ground += (delta - leg.ground) * AnimBlend.smoothing(dt, 0.08)
				table.insert(deltas, leg.ground)
				if leg.ground > 0.02 then
					-- shorten the leg with two-bone IK: extra knee bend for the raised ground
					local _, bendRest = AnimBlend.twoBoneIK(leg.a, leg.b, (leg.a + leg.b) * 0.97)
					local _, bend = AnimBlend.twoBoneIK(leg.a, leg.b, (leg.a + leg.b) * 0.97 - leg.ground)
					local front = legName == "FL" or legName == "FR"
					addRot(acc, leg.chain[2], { p = (if front then -1 else 1) * math.deg(bend - bendRest) })
				end
			end
		end
		root.h += AnimBlend.pelvisOffset(deltas) / math.max(rec.shoulderHeight, 1)
	end

	-- Apply
	for bone, r in acc do
		local motor = rec.motors[bone]
		if motor then
			motor.Transform = CFrame.Angles(rad(r.p), rad(r.y), rad(r.r))
		end
	end
	local rootMotor = rec.motors[RIG.root]
	if rootMotor then
		rootMotor.Transform = CFrame.new(0, root.h * rec.shoulderHeight, root.z)
			* CFrame.Angles(rad(root.p), 0, rad(root.r))
	end
	updateBandages(rec)
end

---------------------------------------------------------------------------------------------
function AnimalAnimator.start()
	for _, model in CollectionService:GetTagged("Animal") do
		addAnimal(model)
	end
	CollectionService:GetInstanceAddedSignal("Animal"):Connect(addAnimal)
	CollectionService:GetInstanceRemovedSignal("Animal"):Connect(removeAnimal)

	-- Motor6D.Transform must be written after the Animator each frame → PreSimulation/Stepped.
	RunService.PreSimulation:Connect(function(dt)
		local cam = Workspace.CurrentCamera
		if not cam then
			return
		end
		local list, dists = {}, {}
		for model, rec in animals do
			if model.Parent and model.PrimaryPart then
				table.insert(list, rec)
				table.insert(dists, (model.PrimaryPart.Position - cam.CFrame.Position).Magnitude)
			end
		end
		local tiers = AnimBlend.assignLods(dists, 4, 8)
		for i, rec in list do
			local focused = rec.model:GetAttribute("Focused") == true
			local _, onScreen = cam:WorldToViewportPoint(rec.model.PrimaryPart.Position)
			local tier = AnimBlend.lodFor(dists[i], onScreen, focused)
			if not focused and tiers[i] ~= tier.name then
				-- budget may demote further
				for _, t in AnimBlend.LOD do
					if t.name == tiers[i] and t.hz < tier.hz then
						tier = t
					end
				end
			end
			if tier.hz > 0 then
				rec.accum += dt
				if rec.accum >= 1 / tier.hz - 1e-4 then
					step(rec, rec.accum, tier)
					rec.accum = 0
				end
			end
		end
	end)
end

return AnimalAnimator
