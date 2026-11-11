--[[
	Species — species + breed definitions for My Vet Office. Pure data (no requires).

	A breed sets the body (size, rig scale, stride lengths that keep feet planted), the default
	temperament (personality baselines for AnimalMind), and the sounds / idle repertoire that
	AnimalBehavior draws from. Species sets the rig skeleton and normal vital ranges.

	Vital ranges are simplified, veterinarian-informed teaching values for a game — not clinical
	reference material.
]]

local Species = {}

-- Bone names the Blender rig exports (blender/rig spec in games/my-vet-office/blender/handoff.md).
-- The client animator drives these Motor6Ds procedurally + via AnimationTracks.
Species.rigs = {
	Quadruped = {
		root = "Root",
		spine = { "Pelvis", "SpineLow", "SpineMid", "Chest" },
		neck = { "Neck", "Head" },
		jaw = "Jaw",
		ears = { "EarL", "EarR" },
		eyelids = { "LidL", "LidR" },
		eyes = { "EyeL", "EyeR" },
		tail = { "Tail1", "Tail2", "Tail3", "Tail4" },
		legs = {
			FL = { "ShoulderL", "ElbowL", "WristL", "PawFL" },
			FR = { "ShoulderR", "ElbowR", "WristR", "PawFR" },
			BL = { "HipL", "KneeL", "HockL", "PawBL" },
			BR = { "HipR", "KneeR", "HockR", "PawBR" },
		},
		-- Gait phase offsets (fraction of a cycle) per leg. Walk = 4-beat lateral sequence,
		-- trot = diagonal pairs, gallop = rotary.
		gaitPhases = {
			walk = { BL = 0, FL = 0.25, BR = 0.5, FR = 0.75 },
			trot = { FL = 0, BR = 0, FR = 0.5, BL = 0.5 },
			run = { BL = 0, BR = 0.1, FL = 0.5, FR = 0.6 },
			sprint = { BL = 0, BR = 0.08, FL = 0.45, FR = 0.53 },
		},
	},
}

Species.species = {
	Dog = {
		rig = "Quadruped",
		vitals = {
			heartRate = { 60, 140 }, -- bpm, resting
			respRate = { 10, 35 }, -- breaths/min
			tempF = { 100.5, 102.5 },
		},
		sounds = { "Pant", "Whine", "Bark", "SoftBark", "Sniff", "Yawn", "Pawsteps", "CollarJingle", "Growl" },
		idles = { "Sniff", "LookAround", "Scratch", "Shake", "Yawn", "LickNose", "HeadTilt", "Stretch" },
		poses = { "Stand", "Sit", "LieSternal", "LieLateral", "RollOver" },
	},
	Cat = {
		rig = "Quadruped",
		vitals = {
			heartRate = { 140, 220 },
			respRate = { 20, 30 },
			tempF = { 100.5, 102.5 },
		},
		sounds = { "Meow", "Purr", "Hiss", "Chirp", "Pawsteps", "CarrierRattle" },
		idles = { "Groom", "TailFlick", "EarSwivel", "Stretch", "LookAround", "Knead", "Rub" },
		poses = { "Stand", "Sit", "Crouch", "LieSternal", "Loaf", "Curl" },
	},
}

--[[
	Breed fields
	  size          "small" | "medium" | "large" (handling: small = pick up, large = help onto table)
	  rigScale      uniform rig scale vs the species base rig
	  stride        studs travelled per full gait cycle at scale 1, per gait — used to sync
	                playback speed to velocity so paws never slide
	  gaitSpeed     studs/s where each gait is fully weighted
	  temperament   AnimalMind baselines 0..1
	  quirks        extra idle weights (e.g. Beagle sniffs far more)
]]
Species.breeds = {
	GoldenRetriever = {
		species = "Dog",
		displayName = "Golden Retriever",
		size = "large",
		rigScale = 1.0,
		weightLb = { 55, 75 },
		stride = { walk = 2.6, trot = 4.2, run = 6.4, sprint = 8.0 },
		gaitSpeed = { walk = 3.5, trot = 7, run = 12, sprint = 17 },
		temperament = {
			fear = 0.1,
			trust = 0.7,
			stress = 0.15,
			pain = 0,
			energy = 0.7,
			curiosity = 0.7,
			comfort = 0.65,
			sociability = 0.9,
		},
		quirks = { Sniff = 1.2, LookAround = 1, HeadTilt = 1.1, LickNose = 0.8 },
		voice = { pitch = 0.95 },
		coats = { "Gold", "Cream", "Red" },
	},
	Chihuahua = {
		species = "Dog",
		displayName = "Chihuahua",
		size = "small",
		rigScale = 0.42,
		weightLb = { 3, 6 },
		stride = { walk = 2.3, trot = 3.8, run = 5.6, sprint = 7.0 },
		gaitSpeed = { walk = 2.2, trot = 4.5, run = 8, sprint = 11 },
		temperament = {
			fear = 0.55,
			trust = 0.3,
			stress = 0.4,
			pain = 0,
			energy = 0.8,
			curiosity = 0.5,
			comfort = 0.35,
			sociability = 0.35,
		},
		quirks = { Shake = 1.5, LookAround = 1.4, SoftBark = 1.6 },
		voice = { pitch = 1.6 },
		coats = { "Fawn", "Black&Tan", "Cream" },
	},
	Beagle = {
		species = "Dog",
		displayName = "Beagle",
		size = "medium",
		rigScale = 0.7,
		weightLb = { 20, 30 },
		stride = { walk = 2.5, trot = 4.0, run = 6.0, sprint = 7.5 },
		gaitSpeed = { walk = 3, trot = 6, run = 10, sprint = 14 },
		temperament = {
			fear = 0.2,
			trust = 0.55,
			stress = 0.2,
			pain = 0,
			energy = 0.85,
			curiosity = 0.95,
			comfort = 0.55,
			sociability = 0.75,
		},
		quirks = { Sniff = 2.5, Scratch = 1.1 },
		voice = { pitch = 1.1 },
		coats = { "Tricolor", "Lemon" },
	},
	DomesticShorthair = {
		species = "Cat",
		displayName = "Domestic Shorthair",
		size = "small",
		rigScale = 0.45,
		weightLb = { 8, 12 },
		stride = { walk = 2.2, trot = 3.6, run = 5.4, sprint = 6.8 },
		gaitSpeed = { walk = 2.5, trot = 5, run = 9, sprint = 13 },
		temperament = {
			fear = 0.45,
			trust = 0.35,
			stress = 0.35,
			pain = 0,
			energy = 0.5,
			curiosity = 0.6,
			comfort = 0.4,
			sociability = 0.4,
		},
		quirks = { Groom = 1.6, TailFlick = 1.3, EarSwivel = 1.4 },
		voice = { pitch = 1.0 },
		coats = { "Tabby", "Tuxedo", "Ginger", "Grey" },
	},
}

Species.breedNames = {}
for name in Species.breeds do
	table.insert(Species.breedNames, name)
end
table.sort(Species.breedNames)

function Species.breed(name: string)
	return Species.breeds[name]
end

function Species.speciesOf(breedName: string)
	local breed = Species.breeds[breedName]
	return breed and Species.species[breed.species]
end

return Species
