--[[
	PoseLibrary — procedural key poses for the shared quadruped rig (Species.rigs.Quadruped).
	Pure data + blending. The client animator uses these as the pose layer whenever an authored
	AnimationTrack for the pose isn't available yet, and as the IK "rest" reference; they also
	make every pose transition testable (blend is continuous, every bone is defined).

	Angles are degrees on each Motor6D in the bone's local frame:
	  p = pitch (X: + = rotate forward/up), y = yaw (Y: + = left), r = roll (Z: + = left side up)
	root = { h = height offset as a fraction of standing shoulder height, p, r }
	Bones a pose doesn't list are 0 (= the Blender rest pose, which is the Stand pose).
]]

local PoseLibrary = {}

local P = {}

P.Stand = { root = { h = 0, p = 0, r = 0 }, bones = {} }

P.Sit = {
	root = { h = -0.3, p = 24, r = 0 },
	bones = {
		Pelvis = { p = -6 },
		SpineMid = { p = 4 },
		Neck = { p = -14 },
		Head = { p = -8 },
		ShoulderL = { p = -24 },
		ShoulderR = { p = -24 },
		HipL = { p = -72 },
		HipR = { p = -72 },
		KneeL = { p = 112 },
		KneeR = { p = 112 },
		HockL = { p = -64 },
		HockR = { p = -64 },
		PawBL = { p = 20 },
		PawBR = { p = 20 },
		Tail1 = { p = -28 },
		Tail2 = { p = 10 },
	},
}

P.LieSternal = {
	root = { h = -0.62, p = 0, r = 0 },
	bones = {
		Neck = { p = 12 },
		Head = { p = -12 },
		ShoulderL = { p = 72 },
		ShoulderR = { p = 72 },
		ElbowL = { p = -104 },
		ElbowR = { p = -104 },
		WristL = { p = 36 },
		WristR = { p = 36 },
		HipL = { p = -84, r = 12 },
		HipR = { p = -84, r = -12 },
		KneeL = { p = 124 },
		KneeR = { p = 124 },
		HockL = { p = -52 },
		HockR = { p = -52 },
		Tail1 = { p = -40, y = 20 },
		Tail2 = { y = 15 },
	},
}

P.LieLateral = {
	root = { h = -0.72, p = 0, r = 84 },
	bones = {
		SpineMid = { y = 6 },
		Neck = { p = -10, y = 8 },
		Head = { p = -6, r = -10 },
		ShoulderL = { p = 22 },
		ShoulderR = { p = 30 },
		ElbowL = { p = -24 },
		ElbowR = { p = -34 },
		HipL = { p = -18 },
		HipR = { p = -26 },
		KneeL = { p = 26 },
		KneeR = { p = 34 },
		Tail1 = { p = -20 },
	},
}

P.RollOver = {
	root = { h = -0.65, p = 0, r = 170 },
	bones = {
		Neck = { p = -20 },
		Head = { r = 20 },
		ShoulderL = { p = 64 },
		ShoulderR = { p = 64 },
		ElbowL = { p = -84 },
		ElbowR = { p = -84 },
		WristL = { p = -40 },
		WristR = { p = -40 },
		HipL = { p = -56 },
		HipR = { p = -56 },
		KneeL = { p = 82 },
		KneeR = { p = 82 },
		Tail1 = { p = -10, y = 30 },
	},
}

P.Crouch = {
	root = { h = -0.26, p = -4, r = 0 },
	bones = {
		Neck = { p = -22 },
		Head = { p = -10 },
		ShoulderL = { p = 26 },
		ShoulderR = { p = 26 },
		ElbowL = { p = -42 },
		ElbowR = { p = -42 },
		WristL = { p = 18 },
		WristR = { p = 18 },
		HipL = { p = -42 },
		HipR = { p = -42 },
		KneeL = { p = 62 },
		KneeR = { p = 62 },
		HockL = { p = -30 },
		HockR = { p = -30 },
		Tail1 = { p = -48 },
		Tail2 = { p = -10 },
	},
}

P.Loaf = {
	root = { h = -0.6, p = 0, r = 0 },
	bones = {
		Neck = { p = 6 },
		Head = { p = -6 },
		ShoulderL = { p = 82 },
		ShoulderR = { p = 82 },
		ElbowL = { p = -150 },
		ElbowR = { p = -150 },
		WristL = { p = 60 },
		WristR = { p = 60 },
		HipL = { p = -84 },
		HipR = { p = -84 },
		KneeL = { p = 128 },
		KneeR = { p = 128 },
		HockL = { p = -50 },
		HockR = { p = -50 },
		Tail1 = { p = -30, y = 40 },
		Tail2 = { y = 30 },
		Tail3 = { y = 25 },
	},
}

P.Curl = {
	root = { h = -0.66, p = 0, r = 70 },
	bones = {
		SpineLow = { y = 22 },
		SpineMid = { y = 28 },
		Chest = { y = 24 },
		Neck = { y = 36, p = -10 },
		Head = { y = 20, p = -8 },
		ShoulderL = { p = 40 },
		ShoulderR = { p = 48 },
		ElbowL = { p = -70 },
		ElbowR = { p = -80 },
		HipL = { p = -50 },
		HipR = { p = -58 },
		KneeL = { p = 80 },
		KneeR = { p = 90 },
		Tail1 = { y = 40 },
		Tail2 = { y = 40 },
		Tail3 = { y = 35 },
		Tail4 = { y = 30 },
	},
}

P.Carried = {
	root = { h = 0, p = 4, r = 0 },
	bones = {
		ShoulderL = { p = 12 },
		ShoulderR = { p = 12 },
		ElbowL = { p = -14 },
		ElbowR = { p = -14 },
		HipL = { p = 14 },
		HipR = { p = 14 },
		KneeL = { p = 18 },
		KneeR = { p = 18 },
		Tail1 = { p = -30 },
		Neck = { p = 6 },
	},
}

PoseLibrary.poses = P

local ZERO = { p = 0, y = 0, r = 0 }

local function lerp(a: number, b: number, t: number): number
	return a + (b - a) * t
end

local function rot(pose, bone: string)
	local b = pose.bones[bone]
	if not b then
		return ZERO
	end
	return { p = b.p or 0, y = b.y or 0, r = b.r or 0 }
end

-- Blend two poses for every bone in `boneList`. t is the eased PoseGraph alpha.
function PoseLibrary.blend(fromName: string, toName: string, t: number, boneList: { string })
	local a, b = P[fromName] or P.Stand, P[toName] or P.Stand
	local out = {
		root = {
			h = lerp(a.root.h, b.root.h, t),
			p = lerp(a.root.p, b.root.p, t),
			r = lerp(a.root.r, b.root.r, t),
		},
		bones = {},
	}
	for _, bone in boneList do
		local ra, rb = rot(a, bone), rot(b, bone)
		out.bones[bone] = { p = lerp(ra.p, rb.p, t), y = lerp(ra.y, rb.y, t), r = lerp(ra.r, rb.r, t) }
	end
	return out
end

-- Flat list of all bone names for a rig definition (Species.rigs.Quadruped).
function PoseLibrary.boneList(rig): { string }
	local list = { rig.root }
	for _, b in rig.spine do
		table.insert(list, b)
	end
	for _, b in rig.neck do
		table.insert(list, b)
	end
	table.insert(list, rig.jaw)
	for _, group in { rig.ears, rig.eyelids, rig.eyes, rig.tail } do
		for _, b in group do
			table.insert(list, b)
		end
	end
	for _, legName in { "FL", "FR", "BL", "BR" } do
		for _, b in rig.legs[legName] do
			table.insert(list, b)
		end
	end
	return list
end

--[[
	Leg cycle for procedural locomotion. phase 0..1, duty = fraction of the cycle the paw is on
	the ground. Returns fore-aft offset (-1 back … +1 forward, in half-strides) and lift 0..1.
	During stance the paw moves back at CONSTANT speed (it's planted while the body moves
	forward); during swing it arcs forward. With playback synced to speed (AnimBlend), the
	planted paw has zero ground velocity.
]]
PoseLibrary.DUTY = { walk = 0.65, trot = 0.5, run = 0.4, sprint = 0.35 }

function PoseLibrary.legCycle(phase: number, duty: number): (number, number)
	phase %= 1
	if phase < duty then
		local t = phase / duty
		return 1 - 2 * t, 0
	end
	local t = (phase - duty) / (1 - duty)
	local eased = t * t * (3 - 2 * t)
	return -1 + 2 * eased, math.sin(t * math.pi)
end

return PoseLibrary
