--[[
	My Vet Office — game configuration. Pure data (no requires) so Lune tests can load it.
	Medical content lives in Cases.luau, animals in Species.luau. All numbers are tunable; see
	games/my-vet-office/game.md §7 for the pacing they were tuned to.
	No Robux products in v1 (owner approval needed before any are created).
]]

local Config = {}

Config.name = "My Vet Office!"
Config.dataStoreName = "my-vet-office_PlayerData_v1"
Config.studioDataStore = "memory" -- "memory" | "real" (real needs Studio API access, private place)
Config.autosaveSeconds = 90

Config.clinic = {
	defaultName = "Paws & Whiskers Vet",
	startCash = 250,
	startReputation = 3,
	maxLevel = 50,
	ratingWindow = 20,
	refundRate = 0.5,
	maxStaff = 12,
	maxDeliveries = 6,
	maxActiveAppointments = 4, -- waiting + in progress, grows with level (see arrivalCapPerLevel)
	arrivalCapPerLevel = 0.15,
	dayLengthSeconds = 720, -- 12 real minutes per clinic day (day/night lighting follows this)
	arrival = { base = 70, min = 25, perStar = 12, firstPatientDelay = 6 },
	followUpChance = 0.35,
	comfortCooldown = 0.8, -- seconds between pet/comfort/treat actions on one patient
	expenses = { rentBase = 40, rentPerRoom = 15, utilitiesBase = 15, utilitiesPerRoom = 5 },
}

-- Level a feature unlocks at. Milestones mirror the owner's progression outline.
Config.unlocks = {
	exams = {
		Visual = 1,
		Stethoscope = 1,
		Thermometer = 1,
		Otoscope = 1,
		FurCheck = 1,
		Palpate = 2,
		BloodTest = 5,
		XRay = 5,
		Ultrasound = 10,
	},
	treatments = {
		Vaccinate = 1,
		CleanEar = 1,
		EarDrops = 1,
		MiteTreatment = 1,
		CoughMeds = 1,
		CleanWound = 1,
		Bandage = 1,
		RemoveTicks = 1,
		TickPrevention = 1,
		AntiNausea = 2,
		Fluids = 2,
		Cast = 5,
		RemoveObject = 20,
	},
	breeds = { GoldenRetriever = 1, Beagle = 1, DomesticShorthair = 1, Chihuahua = 2 },
}

Config.milestones = {
	{ level = 1, title = "Small Vet Office", note = "Checkups, vaccinations, minor illnesses" },
	{ level = 5, title = "Established Clinic", note = "Blood tests, X-rays, complex diagnoses" },
	{ level = 10, title = "Advanced Veterinary Practice", note = "Ultrasound, dental, new species" },
	{ level = 20, title = "Animal Hospital", note = "Surgery, recovery rooms, emergencies" },
	{ level = 35, title = "Premium Veterinary Hospital", note = "Specialists, larger staff" },
	{ level = 50, title = "Veterinary Empire", note = "Multiple locations, departments" },
}

Config.staffRoles = {
	Receptionist = { minLevel = 3, hireCost = 300, wage = 45, jobs = { "CheckIn", "Checkout", "Phone" } },
	Janitor = { minLevel = 3, hireCost = 200, wage = 30, jobs = { "CleanTable", "Mop", "EmptyBins" } },
	Assistant = { minLevel = 4, hireCost = 400, wage = 55, jobs = { "Restock", "PrepRoom", "Escort" } },
	Technician = { minLevel = 6, hireCost = 700, wage = 80, jobs = { "Escort", "Restrain", "LabRun" } },
	Veterinarian = { minLevel = 12, hireCost = 2000, wage = 160, jobs = { "Treat" } },
}

-- Rooms: grid size in studs (1 cell = 1 stud). `kind` gates which catalog items fit.
Config.rooms = {
	Reception = { kind = "Reception", w = 22, d = 14 },
	Waiting = { kind = "Waiting", w = 20, d = 14 },
	Exam1 = { kind = "Exam", w = 14, d = 12 },
	Exam2 = { kind = "Exam", w = 14, d = 12, minLevel = 3, price = 1500 },
	Lab = { kind = "Lab", w = 12, d = 10, minLevel = 5, price = 3500 },
	Imaging = { kind = "Imaging", w = 14, d = 12, minLevel = 5, price = 5000 },
	Kennels = { kind = "Recovery", w = 16, d = 10, minLevel = 8, price = 4000 },
	Surgery = { kind = "Surgery", w = 16, d = 14, minLevel = 20, price = 15000 },
}

-- Placeable items (Blender models; see games/my-vet-office/assets/manifest.json).
-- w/d = footprint in studs. essential = can't remove the last one.
Config.catalog = {
	ExamTable = { name = "Exam table", w = 5, d = 3, price = 400, rooms = { "Exam" }, essential = true },
	EquipmentCabinet = { name = "Equipment cabinet", w = 3, d = 1, price = 250, rooms = { "Exam" } },
	MedCabinet = { name = "Medicine cabinet", w = 3, d = 1, price = 300, rooms = { "Exam", "Lab" } },
	DrawerUnit = { name = "Drawer unit", w = 3, d = 2, price = 180, rooms = { "Exam", "Lab", "Reception" } },
	VaccineFridge = { name = "Vaccine fridge", w = 2, d = 2, price = 350, rooms = { "Exam", "Lab" } },
	Sink = { name = "Hand-wash sink", w = 3, d = 2, price = 200, rooms = { "Exam", "Lab", "Surgery" } },
	VetComputer = { name = "Vet computer desk", w = 4, d = 2, price = 300, rooms = { "Exam", "Reception" } },
	ReceptionCounter = {
		name = "Reception counter",
		w = 8,
		d = 3,
		price = 500,
		rooms = { "Reception" },
		essential = true,
	},
	InvoicePrinter = { name = "Invoice printer", w = 1, d = 1, price = 120, rooms = { "Reception" } },
	WaitingChair = { name = "Waiting chair", w = 2, d = 2, price = 60, rooms = { "Waiting", "Reception" } },
	WaitingBench = { name = "Waiting bench", w = 5, d = 2, price = 140, rooms = { "Waiting" } },
	PlantTall = { name = "Tall plant", w = 1, d = 1, price = 45 },
	PlantShelf = { name = "Shelf plant", w = 2, d = 1, price = 35 },
	PawPrintRug = { name = "Paw-print rug", w = 6, d = 4, price = 90, flat = true },
	DogArtPrint = { name = "Dog art print", w = 2, d = 1, price = 50, wall = true },
	CatArtPrint = { name = "Cat art print", w = 2, d = 1, price = 50, wall = true },
	WaitingTV = { name = "Waiting room TV", w = 3, d = 1, price = 260, rooms = { "Waiting" }, minLevel = 2 },
	TreatJar = { name = "Treat jar stand", w = 1, d = 1, price = 40 },
	PetScale = { name = "Pet weighing scale", w = 3, d = 2, price = 220, rooms = { "Exam", "Reception" } },
	Kennel = { name = "Recovery kennel", w = 3, d = 3, price = 320, rooms = { "Recovery" }, minLevel = 8 },
	XRayMachine = { name = "X-ray machine", w = 6, d = 4, price = 4000, rooms = { "Imaging" }, minLevel = 5 },
	LabAnalyzer = { name = "Blood analyser", w = 2, d = 2, price = 2500, rooms = { "Lab" }, minLevel = 5 },
	UltrasoundCart = { name = "Ultrasound cart", w = 2, d = 2, price = 6000, rooms = { "Exam" }, minLevel = 10 },
	SurgicalTable = { name = "Surgical table", w = 5, d = 3, price = 9000, rooms = { "Surgery" }, minLevel = 20 },
}

-- Starter clinic (pre-placed, owned): tiny but complete.
Config.startLayout = {
	{ item = "ReceptionCounter", room = "Reception", x = 7, z = 2, rot = 0 },
	{ item = "InvoicePrinter", room = "Reception", x = 15, z = 2, rot = 0 },
	{ item = "VetComputer", room = "Reception", x = 2, z = 2, rot = 0 },
	{ item = "WaitingChair", room = "Waiting", x = 2, z = 2, rot = 0 },
	{ item = "WaitingChair", room = "Waiting", x = 5, z = 2, rot = 0 },
	{ item = "WaitingChair", room = "Waiting", x = 8, z = 2, rot = 0 },
	{ item = "PlantTall", room = "Waiting", x = 18, z = 1, rot = 0 },
	{ item = "ExamTable", room = "Exam1", x = 5, z = 5, rot = 0 },
	{ item = "EquipmentCabinet", room = "Exam1", x = 1, z = 0, rot = 0 },
	{ item = "MedCabinet", room = "Exam1", x = 5, z = 0, rot = 0 },
	{ item = "DrawerUnit", room = "Exam1", x = 9, z = 0, rot = 0 },
	{ item = "VaccineFridge", room = "Exam1", x = 12, z = 0, rot = 0 },
	{ item = "Sink", room = "Exam1", x = 0, z = 9, rot = 0 },
	{ item = "VetComputer", room = "Exam1", x = 10, z = 10, rot = 0 },
}

Config.finishes = {
	wall = {
		WarmCream = { price = 0 },
		SageGreen = { price = 80 },
		SkyBlue = { price = 80 },
		BlushPink = { price = 80 },
		OakPanel = { price = 220 },
		PawWallpaper = { price = 260 },
	},
	floor = {
		CleanVinyl = { price = 0 },
		CheckerTile = { price = 150 },
		WarmOak = { price = 240 },
		TerrazzoSpeckle = { price = 300 },
	},
}

Config.customers = {
	firstNames = {
		"Maya",
		"Jordan",
		"Priya",
		"Sam",
		"Elena",
		"Marcus",
		"Hana",
		"Theo",
		"Grace",
		"Diego",
		"Aisha",
		"Noah",
		"Lena",
		"Kofi",
		"Ruby",
		"Oscar",
	},
	petNames = {
		Dog = { "Biscuit", "Maple", "Rocket", "Honey", "Scout", "Pepper", "Waffles", "Luna", "Buddy", "Teddy" },
		Cat = { "Mochi", "Pumpkin", "Salem", "Nala", "Pickles", "Olive", "Ziggy", "Clementine" },
	},
	-- personality: patience seconds + line style for dialogue
	personalities = {
		Calm = { patience = 240, weight = 3 },
		Chatty = { patience = 200, weight = 3 },
		Worried = { patience = 150, weight = 2 },
		Busy = { patience = 100, weight = 2 },
	},
}

-- First-15-minutes onboarding (vault Tutorial step machine; client shows arrows/text).
Config.tutorial = {
	steps = {
		{
			id = "CheckIn",
			text = "A customer is at the desk — use the computer to check them in.",
			target = "VetComputer",
		},
		{ id = "Call", text = "Walk to the waiting room and call your patient in.", target = "Waiting" },
		{ id = "OnTable", text = "Help the patient onto the exam table.", target = "ExamTable" },
		{
			id = "Exam",
			text = "Grab the stethoscope from the cabinet and listen to the heart.",
			target = "EquipmentCabinet",
		},
		{ id = "Diagnose", text = "Review the chart on the computer and choose a diagnosis.", target = "VetComputer" },
		{ id = "Treat", text = "Treat your patient.", target = "ExamTable" },
		{ id = "Checkout", text = "Print the invoice at reception so the owner can pay.", target = "InvoicePrinter" },
		{ id = "NameClinic", text = "Your first patient is happy! Now name your clinic on the sign out front." },
		{ id = "Restock", text = "You're low on supplies — order more on the computer, then shelve the box." },
		{ id = "Decorate", text = "Make it yours: place a plant or art print in the waiting room." },
	},
}

return Config
