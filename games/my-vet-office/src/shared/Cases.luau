--[[
	Cases — medical content for My Vet Office. Pure data + small helpers.

	All medicine here is SIMPLIFIED and FICTIONALISED for a game: veterinarian-informed in spirit
	(the right kind of test finds the right kind of problem) but never real-world instructions.

	exams        diagnostic actions; each maps to a procedure in Procedures.luau
	diagnoses    what the player can choose on the diagnosis screen
	treatments   what the player can perform; each consumes supplies and maps to a procedure
	cases        illness templates a patient can arrive with
	landmarks    body points (normalised side-view coords: u 0 = tail → 1 = nose, v 0 = paws →
	             1 = back, side "L"/"R"/"C") used by place/scan procedures
]]

local Cases = {}

Cases.landmarks = {
	Heart = { u = 0.66, v = 0.42, side = "L", radius = 0.09 },
	LungL = { u = 0.58, v = 0.6, side = "L", radius = 0.1 },
	LungR = { u = 0.58, v = 0.6, side = "R", radius = 0.1 },
	Flank = { u = 0.3, v = 0.45, side = "L", radius = 0.12 }, -- simplified thermometer spot
	Abdomen = { u = 0.45, v = 0.3, side = "C", radius = 0.12 },
	EarL = { u = 0.9, v = 0.9, side = "L", radius = 0.07 },
	EarR = { u = 0.9, v = 0.9, side = "R", radius = 0.07 },
	Scruff = { u = 0.78, v = 0.85, side = "C", radius = 0.1 }, -- vaccine site
	PawFL = { u = 0.72, v = 0.05, side = "L", radius = 0.08 },
	PawFR = { u = 0.72, v = 0.05, side = "R", radius = 0.08 },
	Mouth = { u = 0.98, v = 0.7, side = "C", radius = 0.06 },
}

Cases.exams = {
	Visual = { name = "Visual check", procedure = "VisualCheck", minLevel = 1, price = 0, invasive = 0.1 },
	Stethoscope = { name = "Stethoscope", procedure = "Stethoscope", minLevel = 1, price = 0, invasive = 0.3 },
	Thermometer = { name = "Temperature", procedure = "Thermometer", minLevel = 1, price = 10, invasive = 0.6 },
	Otoscope = { name = "Ear exam", procedure = "Otoscope", minLevel = 1, price = 15, invasive = 0.7 },
	FurCheck = { name = "Coat & skin check", procedure = "FurCheck", minLevel = 1, price = 0, invasive = 0.2 },
	Palpate = { name = "Belly palpation", procedure = "Palpate", minLevel = 2, price = 0, invasive = 0.5 },
	BloodTest = { name = "Blood test", procedure = "BloodTest", minLevel = 5, price = 45, invasive = 0.7 },
	XRay = { name = "X-ray", procedure = "XRay", minLevel = 5, price = 90, invasive = 0.4 },
	Ultrasound = { name = "Ultrasound", procedure = "Ultrasound", minLevel = 10, price = 110, invasive = 0.4 },
}

Cases.diagnoses = {
	Healthy = { name = "Healthy — routine wellness", minLevel = 1 },
	Otitis = { name = "Ear infection (otitis externa)", minLevel = 1 },
	EarMites = { name = "Ear mites", minLevel = 1 },
	KennelCough = { name = "Kennel cough (infectious tracheobronchitis)", minLevel = 1 },
	PawLaceration = { name = "Paw pad cut", minLevel = 1 },
	Ticks = { name = "Tick infestation", minLevel = 1 },
	Gastroenteritis = { name = "Upset stomach (gastroenteritis)", minLevel = 2 },
	ForeignBody = { name = "Swallowed object (foreign body)", minLevel = 5 },
	Fracture = { name = "Broken leg (fracture)", minLevel = 5 },
	Anemia = { name = "Low red blood cells (anemia)", minLevel = 5 },
	Pregnancy = { name = "Pregnancy check", minLevel = 10 },
}

--[[ treatment: supplies consumed, price billed, procedure, which diagnoses it helps ]]
Cases.treatments = {
	Vaccinate = {
		name = "Vaccination",
		procedure = "Vaccinate",
		supplies = { Vaccine = 1, Syringe = 1 },
		price = 40,
		minLevel = 1,
	},
	CleanEar = {
		name = "Clean ear canal",
		procedure = "CleanEar",
		supplies = { EarCleaner = 1, CottonPad = 2 },
		price = 30,
		minLevel = 1,
	},
	EarDrops = {
		name = "Medicated ear drops",
		procedure = "EarDrops",
		supplies = { EarDrops = 1 },
		price = 25,
		minLevel = 1,
	},
	MiteTreatment = {
		name = "Anti-mite spot-on",
		procedure = "SpotOn",
		supplies = { SpotOn = 1 },
		price = 30,
		minLevel = 1,
	},
	CoughMeds = {
		name = "Cough medicine + rest plan",
		procedure = "Administer",
		supplies = { CoughSyrup = 1 },
		price = 35,
		minLevel = 1,
	},
	CleanWound = {
		name = "Clean wound",
		procedure = "CleanWound",
		supplies = { Antiseptic = 1, Gauze = 2 },
		price = 30,
		minLevel = 1,
	},
	Bandage = {
		name = "Bandage",
		procedure = "Bandage",
		supplies = { Bandage = 1 },
		price = 25,
		minLevel = 1,
	},
	RemoveTicks = {
		name = "Remove ticks",
		procedure = "RemoveTicks",
		supplies = { TickTool = 0 }, -- reusable tool, listed for the UI
		price = 30,
		minLevel = 1,
	},
	TickPrevention = {
		name = "Tick prevention chew",
		procedure = "Administer",
		supplies = { TickChew = 1 },
		price = 20,
		minLevel = 1,
	},
	AntiNausea = {
		name = "Tummy medicine + bland diet",
		procedure = "Administer",
		supplies = { StomachMeds = 1, BlandFood = 1 },
		price = 40,
		minLevel = 2,
	},
	Fluids = {
		name = "Fluids (hydration)",
		procedure = "Fluids",
		supplies = { FluidBag = 1, Syringe = 1 },
		price = 55,
		minLevel = 2,
	},
	Cast = { name = "Apply cast", procedure = "Cast", supplies = { CastRoll = 2 }, price = 120, minLevel = 5 },
	RemoveObject = {
		name = "Retrieve swallowed object",
		procedure = "RemoveObject",
		supplies = { SurgicalKit = 1 },
		price = 250,
		minLevel = 20,
	},
}

Cases.supplies = {
	Vaccine = { name = "Vaccine vial", cost = 12, start = 6 },
	Syringe = { name = "Syringe", cost = 1, start = 20 },
	EarCleaner = { name = "Ear cleaner", cost = 6, start = 5 },
	CottonPad = { name = "Cotton pads", cost = 0.5, start = 30 },
	EarDrops = { name = "Ear drops", cost = 8, start = 4 },
	SpotOn = { name = "Anti-mite spot-on", cost = 9, start = 3 },
	CoughSyrup = { name = "Cough syrup", cost = 10, start = 3 },
	Antiseptic = { name = "Antiseptic", cost = 4, start = 6 },
	Gauze = { name = "Gauze", cost = 0.5, start = 20 },
	Bandage = { name = "Bandage roll", cost = 3, start = 8 },
	TickTool = { name = "Tick remover", cost = 0, start = 1 },
	TickChew = { name = "Tick chew", cost = 6, start = 4 },
	StomachMeds = { name = "Stomach medicine", cost = 9, start = 0 },
	BlandFood = { name = "Bland diet food", cost = 4, start = 0 },
	FluidBag = { name = "Fluid bag", cost = 14, start = 0 },
	CastRoll = { name = "Cast roll", cost = 15, start = 0 },
	SurgicalKit = { name = "Surgical kit", cost = 60, start = 0 },
	LabCartridge = { name = "Lab cartridge", cost = 18, start = 0 },
	XRayPlate = { name = "X-ray plate", cost = 0, start = 0 },
	Treats = { name = "Pet treats", cost = 0.25, start = 40 },
}

--[[
	Case template fields
	  species        allowed species
	  minLevel       clinic level needed before it can spawn
	  diagnosis      correct diagnosis id
	  treatments     required treatments (all of them, order free) for full recovery
	  complaints     owner's descriptions (one is picked) — symptoms, never the answer
	  mind           AnimalMind condition modifiers (pain, energy …)
	  vitals         deltas on the species normal mid-point (heartRate, respRate, tempF)
	  injury         optional { leg = "FL"|… } → limp + where the bandage goes
	  findings       per exam: what the exam reveals (see Procedures for shape)
	  keyExams       exams that actually reveal this problem (diagnosing without any → "guess")
	  basePay, xp
]]
Cases.cases = {
	Wellness = {
		species = { "Dog", "Cat" },
		minLevel = 1,
		diagnosis = "Healthy",
		treatments = { "Vaccinate" },
		complaints = {
			"%s is due for their yearly checkup and shots!",
			"Just a routine visit — %s seems totally fine, we want to keep it that way.",
		},
		mind = {},
		vitals = {},
		findings = {
			Visual = "Bright, alert, healthy coat.",
			Stethoscope = { sounds = { Heart = "Normal", LungL = "Clear", LungR = "Clear" } },
			Otoscope = { L = {}, R = {} },
			FurCheck = { spots = {} },
		},
		keyExams = { "Visual", "Stethoscope" },
		basePay = 30,
		xp = 30,
	},
	Otitis = {
		species = { "Dog", "Cat" },
		minLevel = 1,
		diagnosis = "Otitis",
		treatments = { "CleanEar", "EarDrops" },
		complaints = {
			"%s keeps shaking their head and scratching their left ear.",
			"There's a funny smell coming from %s's ear, and they cry when I touch it.",
		},
		mind = { pain = 0.25, comfort = -0.1 },
		vitals = { tempF = 0.5 },
		gestureBias = { Shake = 3, Scratch = 2.5, HeadTilt = 2 },
		findings = {
			Visual = "Head tilted left; scratching at the left ear.",
			Stethoscope = { sounds = { Heart = "Normal", LungL = "Clear", LungR = "Clear" } },
			Otoscope = {
				L = {
					{ id = "Redness", u = 0.42, v = 0.55, note = "Red, swollen ear canal" },
					{ id = "Discharge", u = 0.6, v = 0.38, note = "Brown waxy discharge" },
				},
				R = {},
			},
			FurCheck = { spots = {} },
		},
		keyExams = { "Otoscope" },
		basePay = 55,
		xp = 45,
	},
	EarMites = {
		species = { "Cat", "Dog" },
		minLevel = 1,
		diagnosis = "EarMites",
		treatments = { "CleanEar", "MiteTreatment" },
		complaints = {
			"%s won't stop scratching both ears — there's dark gunk in there.",
			"We just adopted %s and they keep pawing at their ears.",
		},
		mind = { pain = 0.15, stress = 0.1 },
		vitals = {},
		gestureBias = { Scratch = 3, EarSwivel = 2 },
		findings = {
			Visual = "Scratch marks around both ears.",
			Stethoscope = { sounds = { Heart = "Normal", LungL = "Clear", LungR = "Clear" } },
			Otoscope = {
				L = { { id = "Debris", u = 0.5, v = 0.5, note = "Dark coffee-ground debris" } },
				R = {
					{ id = "Debris", u = 0.45, v = 0.6, note = "Dark coffee-ground debris" },
					{ id = "Mites", u = 0.58, v = 0.42, note = "Tiny moving white specks" },
				},
			},
			FurCheck = { spots = {} },
		},
		keyExams = { "Otoscope" },
		basePay = 55,
		xp = 45,
	},
	KennelCough = {
		species = { "Dog" },
		minLevel = 1,
		diagnosis = "KennelCough",
		treatments = { "CoughMeds" },
		complaints = {
			"%s has this honking cough since we got back from the dog park.",
			"%s sounds like he's got something stuck in his throat — he keeps coughing.",
		},
		mind = { energy = -0.15, comfort = -0.1 },
		vitals = { tempF = 1.7, respRate = 8 },
		gestureBias = { LickNose = 1.5 },
		findings = {
			Visual = "Occasional dry, honking cough; eyes bright.",
			Stethoscope = { sounds = { Heart = "Normal", LungL = "Harsh", LungR = "Harsh" } },
			Otoscope = { L = {}, R = {} },
			FurCheck = { spots = {} },
		},
		keyExams = { "Stethoscope", "Thermometer" },
		basePay = 50,
		xp = 40,
	},
	PawLaceration = {
		species = { "Dog" },
		minLevel = 1,
		diagnosis = "PawLaceration",
		treatments = { "CleanWound", "Bandage" },
		complaints = {
			"%s stepped on something on our walk and is holding up a front paw.",
			"%s is limping and licking her paw a lot.",
		},
		mind = { pain = 0.45, stress = 0.1 },
		vitals = { heartRate = 10 },
		injury = { leg = "FL" },
		findings = {
			Visual = "Limping; not putting weight on the front-left paw.",
			Stethoscope = { sounds = { Heart = "Fast", LungL = "Clear", LungR = "Clear" } },
			Otoscope = { L = {}, R = {} },
			FurCheck = { spots = { { id = "Cut", landmark = "PawFL", note = "Small cut on the paw pad" } } },
		},
		keyExams = { "Visual", "FurCheck" },
		basePay = 60,
		xp = 50,
	},
	Ticks = {
		species = { "Dog", "Cat" },
		minLevel = 1,
		diagnosis = "Ticks",
		treatments = { "RemoveTicks", "TickPrevention" },
		complaints = {
			"We went camping and now %s has little bumps on their skin.",
			"I found something stuck to %s near the ear — I think it's a bug?",
		},
		mind = { comfort = -0.05 },
		vitals = {},
		gestureBias = { Scratch = 2 },
		findings = {
			Visual = "A couple of small bumps in the coat.",
			Stethoscope = { sounds = { Heart = "Normal", LungL = "Clear", LungR = "Clear" } },
			Otoscope = { L = {}, R = {} },
			FurCheck = {
				spots = {
					{ id = "Tick1", u = 0.82, v = 0.82, side = "L", note = "Tick behind the ear" },
					{ id = "Tick2", u = 0.55, v = 0.55, side = "R", note = "Tick on the shoulder" },
					{ id = "Tick3", u = 0.35, v = 0.4, side = "L", note = "Tick on the flank" },
				},
			},
		},
		keyExams = { "FurCheck" },
		basePay = 50,
		xp = 40,
	},
	Gastroenteritis = {
		species = { "Dog", "Cat" },
		minLevel = 2,
		diagnosis = "Gastroenteritis",
		treatments = { "AntiNausea", "Fluids" },
		complaints = {
			"%s hasn't been eating much, and he's been acting really tired.",
			"%s threw up twice yesterday and just wants to lie down.",
		},
		mind = { energy = -0.4, pain = 0.3, comfort = -0.15 },
		vitals = { tempF = 1.8, heartRate = 20 },
		findings = {
			Visual = "Lethargic, slightly dehydrated (gums a little tacky).",
			Stethoscope = { sounds = { Heart = "Fast", LungL = "Clear", LungR = "Clear" } },
			Otoscope = { L = {}, R = {} },
			FurCheck = { spots = {} },
			Palpate = { tender = { "Abdomen" }, note = "Belly tender and gurgly" },
		},
		keyExams = { "Palpate", "Thermometer" },
		basePay = 80,
		xp = 60,
	},
}

Cases.caseNames = {}
for name in Cases.cases do
	table.insert(Cases.caseNames, name)
end
table.sort(Cases.caseNames)

-- Cases that could spawn for a species at a clinic level (sorted).
function Cases.eligible(speciesName: string, level: number): { string }
	local out = {}
	for _, name in Cases.caseNames do
		local c = Cases.cases[name]
		if c.minLevel <= level and table.find(c.species, speciesName) then
			table.insert(out, name)
		end
	end
	return out
end

-- True vitals for a patient (before measurement noise/stress), from species + case deltas.
function Cases.trueVitals(speciesDef, case, rng: () -> number)
	local v = speciesDef.vitals
	local function mid(range, jitter)
		return (range[1] + range[2]) / 2 + (rng() - 0.5) * jitter
	end
	local d = case.vitals or {}
	return {
		heartRate = math.floor(mid(v.heartRate, 20) + (d.heartRate or 0) + 0.5),
		respRate = math.floor(mid(v.respRate, 6) + (d.respRate or 0) + 0.5),
		tempF = math.floor((mid(v.tempF, 0.6) + (d.tempF or 0)) * 10 + 0.5) / 10,
	}
end

-- Is a reading inside the species normal range?
function Cases.inRange(speciesDef, vital: string, value: number): boolean
	local r = speciesDef.vitals[vital]
	return value >= r[1] and value <= r[2]
end

return Cases
