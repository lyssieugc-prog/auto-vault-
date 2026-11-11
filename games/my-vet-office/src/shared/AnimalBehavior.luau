--[[
	AnimalBehavior — per-animal AI: picks what the animal is doing from its mind (AnimalMind) and
	what it senses, and drives its PoseGraph. Pure; the server runs one shared loop at ~5 Hz for
	all animals (no script per animal) and replicates the output as attributes.

	Behaviours EMERGE from states + triggers instead of one long scripted animation:
	  Follow    walk beside the leader (owner, or the vet once called) at heel distance
	  Sniff     stop at an interesting scent for a moment (curiosity × breed quirk)
	  LookAt    track a person / animal / sound with the head while doing anything else
	  Settle    sit (or lie, when tired) next to the seated owner
	  Hesitate  stop at a threshold (exam-room door) — fear sets how long; comfort/treats help
	  Hide      press behind the owner, or stay at the back of the carrier (cats)
	  Table     on the exam table: hold requested pose, fidget, look toward the owner
	  Carried   being carried / lifted
	  Excited   reunited with the owner, happy greeting
	  Sleep     low energy and settled for a while
	One-shot gestures (Scratch, Shake, Yawn, LickNose, HeadTilt, Groom, TailFlick, …) play on top
	of Settle/Table/Follow-stops, chosen by weight from the species + breed quirk table.

	local b = AnimalBehavior.new({ breed = Species.breeds.GoldenRetriever, species = …, rng = rng })
	local out = AnimalBehavior.tick(b, mind, ctx, dt)
	-- out = { state, pose, from, to, alpha, move, gait, lookAt, gesture, vocal, reaction }

	ctx (all optional):
	  leaderDist, leaderMoving, leaderSeated, leader ("Owner"|"Vet")
	  poi = { id, kind = "Scent"|"Animal"|"Person"|"Sound", dist }
	  sound = { kind = "Bark"|"Loud"|"Name", dist }   (events this tick)
	  atThreshold (bool)   approaching the exam-room door while following
	  inCarrier, carrierOpen, onTable, carried (bools)
	  requestedPose (string)   exam pose asked by the vet
	  handled (bool)           a procedure is touching the animal right now
	  reunited (bool)
]]

-- Works in Roblox (sibling ModuleScripts) and Lune (relative files).
local function import(name: string)
	if script then
		return require(script.Parent:WaitForChild(name))
	end
	-- Lune: path require (aliased so the Roblox std lint does not apply)
	local requirePath: any = require
	return requirePath("./" .. name)
end

local AnimalMind = import("AnimalMind")
local PoseGraph = import("PoseGraph")

local AnimalBehavior = {}

local HEEL = 3 -- studs from the leader where a following animal is happy
local MIN_STATE_TIME = {
	Follow = 0.4,
	Sniff = 1.2,
	Settle = 2,
	Hesitate = 0.8,
	Hide = 1.5,
	Table = 0,
	Carried = 0,
	Excited = 2.5,
	Sleep = 4,
}

function AnimalBehavior.new(opts)
	local breed = opts.breed
	local species = opts.species
	local allowed = {}
	for _, pose in species.poses do
		allowed[pose] = true
	end
	allowed.Carried = true
	local speed = if breed.size == "small" then 1.25 elseif breed.size == "large" then 0.9 else 1
	local gestureWeights = {}
	for _, name in species.idles do
		gestureWeights[name] = (breed.quirks and breed.quirks[name]) or 1
	end
	return {
		breed = breed,
		species = species,
		rng = opts.rng or math.random,
		state = if opts.inCarrier then "Hide" else "Follow",
		stateTime = 0,
		pose = PoseGraph.new(PoseGraph.QUADRUPED, if opts.inCarrier and allowed.Crouch then "Crouch" else "Stand", {
			speed = speed,
			allowed = allowed,
		}),
		gestureWeights = gestureWeights,
		gestureCooldown = 2,
		hesitation = 0, -- seconds of hesitation still owed at the current threshold
		thresholdHandled = false,
		sniffTarget = nil,
		sniffed = {}, -- poi ids already sniffed (don't re-sniff the same spot)
		settledTime = 0,
		lookAt = nil,
		lookTimer = 0,
		log = {}, -- state history (for tests/debug)
	}
end

local function enter(b, state: string)
	if b.state ~= state then
		b.state = state
		b.stateTime = 0
		table.insert(b.log, state)
		if #b.log > 64 then
			table.remove(b.log, 1)
		end
	end
end

local function canLeave(b): boolean
	return b.stateTime >= (MIN_STATE_TIME[b.state] or 0)
end

local function pickGesture(b, mind)
	local total = 0
	for _, w in b.gestureWeights do
		total += w
	end
	local roll = b.rng() * total
	-- deterministic iteration order for reproducible tests
	local names = {}
	for name in b.gestureWeights do
		table.insert(names, name)
	end
	table.sort(names)
	for _, name in names do
		roll -= b.gestureWeights[name]
		if roll <= 0 then
			-- sick/tired animals don't shake off or stretch energetically
			if (name == "Shake" or name == "Stretch") and mind.state.energy < 0.3 then
				return "Yawn"
			end
			return name
		end
	end
	return nil
end

-- Hesitation owed at a threshold, from fear/stress/trust. A confident golden ≈ 0.5 s,
-- a nervous chihuahua several seconds unless comforted.
function AnimalBehavior.hesitationFor(mind): number
	local s = mind.state
	return math.max(0, 0.3 + s.fear * 5 + s.stress * 2 - s.trust * 2.5)
end

local function chooseState(b, mind, ctx, params)
	if ctx.carried then
		return "Carried"
	end
	if ctx.onTable then
		return "Table"
	end
	if ctx.reunited then
		return "Excited"
	end
	if b.state == "Excited" and not canLeave(b) then
		return "Excited"
	end
	if ctx.inCarrier then
		if ctx.carrierOpen and not params.wantsHide and params.willApproach then
			return "Follow" -- comes out
		end
		return "Hide"
	end
	if params.wantsHide then
		return "Hide"
	end
	-- Threshold hesitation (once per threshold).
	if ctx.atThreshold and not b.thresholdHandled then
		b.thresholdHandled = true
		b.hesitation = AnimalBehavior.hesitationFor(mind)
	elseif not ctx.atThreshold then
		b.thresholdHandled = false
	end
	if b.hesitation > 0 then
		return "Hesitate"
	end
	local leaderDist = ctx.leaderDist or 0
	if ctx.leaderMoving or leaderDist > HEEL * 2 then
		-- maybe stop to sniff while the leader is still close
		if b.state == "Sniff" and not canLeave(b) and leaderDist < HEEL * 4 then
			return "Sniff"
		end
		local poi = ctx.poi
		if poi and poi.kind == "Scent" and poi.dist < 2.5 and not b.sniffed[poi.id] and leaderDist < HEEL * 2.5 then
			local sniffWeight = (b.breed.quirks and b.breed.quirks.Sniff) or 1
			local chance = mind.state.curiosity * 0.6 * sniffWeight * (1 - mind.state.fear)
			b.sniffed[poi.id] = true
			if b.rng() < chance then
				b.sniffTarget = poi.id
				return "Sniff"
			end
		end
		return "Follow"
	end
	if b.state == "Sniff" and not canLeave(b) then
		return "Sniff"
	end
	if b.state == "Sleep" or (params.sleepy > 0.5 and b.settledTime > 20) then
		return "Sleep"
	end
	if ctx.leaderSeated or not ctx.leaderMoving then
		return "Settle"
	end
	return "Follow"
end

local function poseFor(b, state: string, mind, ctx, params)
	if state == "Carried" then
		return "Carried"
	elseif state == "Table" then
		return ctx.requestedPose or (if params.sleepy > 0.6 or mind.state.pain > 0.6 then "LieSternal" else "Sit")
	elseif state == "Hide" then
		return if table.find(b.species.poses, "Crouch") then "Crouch" else "Sit"
	elseif state == "Settle" then
		if mind.state.energy < 0.35 or b.settledTime > 25 then
			return if table.find(b.species.poses, "Loaf") and mind.state.comfort > 0.5 then "Loaf" else "LieSternal"
		end
		return "Sit"
	elseif state == "Sleep" then
		return if table.find(b.species.poses, "Curl") then "Curl" else "LieLateral"
	end
	return "Stand"
end

local function gaitFor(b, state: string, ctx, params)
	if state ~= "Follow" and state ~= "Excited" then
		return "idle", 0
	end
	local leaderDist = ctx.leaderDist or 0
	local gait = "walk"
	if state ~= "Excited" and leaderDist > HEEL * 5 then
		gait = "run"
	elseif state == "Excited" or leaderDist > HEEL * 3 then
		gait = "trot"
	end
	if params.limp > 0.4 and gait ~= "walk" then
		gait = "walk" -- injured animals move carefully
	end
	local speed = (b.breed.gaitSpeed[gait] or 0) * params.gaitScale
	return gait, speed
end

function AnimalBehavior.tick(b, mind, ctx, dt: number)
	ctx = ctx or {}
	local params = AnimalMind.derive(mind)
	b.stateTime += dt
	b.gestureCooldown -= dt

	local reaction = nil
	if ctx.sound then
		if ctx.sound.kind == "Bark" then
			reaction = AnimalMind.stimulus(mind, "Bark", math.clamp(1 - ctx.sound.dist / 40, 0.1, 1))
		elseif ctx.sound.kind == "Loud" then
			reaction = AnimalMind.stimulus(mind, "LoudNoise", 1)
		end
		b.lookAt = ctx.sound.kind
		b.lookTimer = 1.5
	end
	if ctx.leaderDist then
		AnimalMind.stimulus(mind, if ctx.leaderDist < 8 then "OwnerNear" else "OwnerAway", dt * 0.5)
	end
	if b.state == "Hesitate" then
		-- comfort and time both work the hesitation down; trust speeds it up
		b.hesitation -= dt * (1 + mind.state.trust)
	end

	local wanted = chooseState(b, mind, ctx, params)
	if wanted ~= b.state and (canLeave(b) or wanted == "Carried" or wanted == "Table" or wanted == "Hesitate") then
		if wanted == "Excited" and b.state ~= "Excited" then
			reaction = AnimalMind.stimulus(mind, "Reunite", 1)
		end
		enter(b, wanted)
	end
	if b.state == "Settle" or b.state == "Table" or b.state == "Sleep" then
		b.settledTime += dt
	else
		b.settledTime = 0
	end

	-- Pose
	local targetPose = poseFor(b, b.state, mind, ctx, params)
	local finalPose = if #b.pose.queue > 0 then b.pose.queue[#b.pose.queue] else b.pose.to
	if finalPose ~= targetPose then
		PoseGraph.request(b.pose, targetPose)
	end
	PoseGraph.tick(b.pose, dt)

	-- Head look target: sound > poi (animal/person) > leader
	b.lookTimer -= dt
	if b.lookTimer <= 0 then
		local poi = ctx.poi
		if b.state == "Table" and mind.state.stress > 0.4 then
			b.lookAt = "Owner" -- nervous patients keep looking to their person
		elseif poi and (poi.kind == "Animal" or poi.kind == "Person") and poi.dist < 15 then
			b.lookAt = poi.id
		elseif b.state == "Sniff" then
			b.lookAt = b.sniffTarget
		else
			b.lookAt = ctx.leader or "Owner"
		end
		b.lookTimer = 1 + b.rng() * 2.5
	end

	-- One-shot gesture while stationary
	local gesture = nil
	local stationary = b.state == "Settle" or b.state == "Table" or (b.state == "Follow" and not ctx.leaderMoving)
	if stationary and b.gestureCooldown <= 0 and PoseGraph.settled(b.pose) and not ctx.handled then
		gesture = pickGesture(b, mind)
		b.gestureCooldown = 4 + b.rng() * 6 + mind.state.stress * 4
	end

	-- Vocalisation (sparse; sound manager rate-limits further)
	local vocal = nil
	if b.state == "Hide" and mind.state.fear > 0.7 and b.rng() < 0.05 * dt * 5 then
		vocal = if b.breed.species == "Cat" then "Hiss" else "Whine"
	elseif params.purr > 0.3 and b.breed.species == "Cat" then
		vocal = "Purr"
	elseif params.pant > 0.35 and b.breed.species == "Dog" then
		vocal = "Pant"
	end

	local gait, speed = gaitFor(b, b.state, ctx, params)
	local move = "stay"
	if b.state == "Follow" or b.state == "Excited" then
		move = "follow"
	elseif b.state == "Hide" then
		move = if ctx.inCarrier then "stay" else "behindOwner"
	end

	return {
		state = b.state,
		pose = b.pose.current,
		from = b.pose.from,
		to = b.pose.to,
		alpha = PoseGraph.easedAlpha(b.pose),
		move = move,
		gait = gait,
		speed = speed,
		heel = HEEL,
		lookAt = b.lookAt,
		gesture = gesture,
		vocal = vocal,
		reaction = reaction,
		params = params,
	}
end

return AnimalBehavior
