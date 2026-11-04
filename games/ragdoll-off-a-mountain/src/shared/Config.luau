--[[
	Ragdoll Off a Mountain — game configuration. Pure data (no requires) so Lune tests can load it.
	Source of truth: games/ragdoll-off-a-mountain/game.md. All numbers are tunable.
	CONFIG_REQUIRED: product/pass ids are 0 placeholders and season dates / promo codes are mock
	values until the owner approves real ones. Never publish or create products without approval.
]]

local Config = {}

Config.name = "Ragdoll Off a Mountain"
Config.dataStoreName = "ragdoll-off-a-mountain_PlayerData_v1"
Config.studioDataStore = "memory" -- "memory" | "real" (real needs Studio API access, private place)
Config.autosaveSeconds = 90
Config.maxPlayers = 6 -- also set in Game Settings (verify there; scripts cannot enforce it)

Config.currencies = {
	Cash = { start = 0 },
	Gems = { start = 0 },
}

-- Core rule (game.md §3.1). 206 bones across the R15 body parts.
Config.scoring = {
	breakSpeed = 45, -- studs/s of sudden velocity change needed to snap a bone
	stepSpeed = 25, -- every extra 25 studs/s snaps one more bone in that part
	maxSeverity = 8,
	critSeverity = 4, -- severity shown as "CRITICAL!"
	comboStep = 0.1,
	comboMax = 3,
	comboWindow = 1.2,
	maxSpeed = 2000,
	partCooldown = 0.12,
	fullSkeletonMultiplier = 2,
	parts = {
		Head = { bones = 29, value = 6 },
		UpperTorso = { bones = 41, value = 3 },
		LowerTorso = { bones = 14, value = 3 },
		LeftUpperArm = { bones = 3, value = 2 },
		RightUpperArm = { bones = 3, value = 2 },
		LeftLowerArm = { bones = 2, value = 2 },
		RightLowerArm = { bones = 2, value = 2 },
		LeftHand = { bones = 27, value = 1 },
		RightHand = { bones = 27, value = 1 },
		LeftUpperLeg = { bones = 2, value = 4 },
		RightUpperLeg = { bones = 2, value = 4 },
		LeftLowerLeg = { bones = 2, value = 3 },
		RightLowerLeg = { bones = 2, value = 3 },
		LeftFoot = { bones = 25, value = 1 },
		RightFoot = { bones = 25, value = 1 },
	},
}

-- Run lifecycle (server physics glue reads these).
Config.run = {
	cooldown = 2, -- seconds between launches
	maxSeconds = 25, -- run ends after this
	restSpeed = 3, -- body slower than this ...
	restSeconds = 1.5, -- ... for this long ends the run
	maxPetImpact = 3, -- pets raise impact force at most x3 (the rest of Hit Power pays as cash)
	fullSkeletonGems = 25,
	aim = { minPitch = -10, maxPitch = 60, maxYaw = 35 }, -- degrees, validated on the server
	padRadius = 30, -- must stand within this many studs of the peak pad to launch
}

-- Peaks = zones (tier ladder). values[level + 1] = peak data at that unlock level.
Config.peaks = {
	{ name = "Pebble Hill", multiplier = 1, height = 120, palette = { "#4CC24A", "#FFD93B" } },
	{ name = "Pine Ridge", multiplier = 4, height = 260, palette = { "#2E9A3E", "#F4FBFF" } },
	{ name = "Frostbite Cliffs", multiplier = 15, height = 420, palette = { "#9BE1FF", "#FFFFFF" } },
	{ name = "Magma Spire", multiplier = 60, height = 620, palette = { "#E13A2A", "#FFC21A" } },
	{ name = "Stormcrown Summit", multiplier = 250, height = 880, palette = { "#B678EA", "#3EF0FF" } },
}

Config.cannons = {
	{ name = "Bare Feet", speed = 40 },
	{ name = "Party Popper", speed = 70 },
	{ name = "Barrel Blaster", speed = 100 },
	{ name = "Rocket Rig", speed = 140 },
	{ name = "Mega Mortar", speed = 190 },
	{ name = "Meteor Launcher", speed = 250 },
}

local peakIndex, cannonIndex = {}, {}
for i = 1, #Config.peaks do
	peakIndex[i] = i
end
for i = 1, #Config.cannons do
	cannonIndex[i] = i
end

Config.upgrades = {
	-- Tier ladders: value = index into Config.peaks / Config.cannons.
	Peak = { currency = "Cash", costs = { 2500, 120000, 6000000, 350000000 }, values = peakIndex },
	Cannon = { currency = "Cash", costs = { 500, 12000, 400000, 15000000, 600000000 }, values = cannonIndex },
	-- Leveled Cash upgrades.
	BoneValue = {
		currency = "Cash",
		baseCost = 100,
		growth = 1.55,
		maxLevel = 30,
		effect = function(level)
			return 1 + 0.25 * level
		end,
	},
	Brittle = {
		currency = "Cash",
		baseCost = 250,
		growth = 1.6,
		maxLevel = 20,
		effect = function(level)
			return 1 + 0.05 * level
		end,
	},
	Bounce = {
		currency = "Cash",
		baseCost = 400,
		growth = 1.7,
		maxLevel = 10,
		effect = function(level)
			return 0.3 + 0.03 * level -- ragdoll Elasticity
		end,
	},
	ComboTime = {
		currency = "Cash",
		baseCost = 300,
		growth = 1.65,
		maxLevel = 10,
		effect = function(level)
			return 1.2 + 0.15 * level
		end,
	},
	-- Gems ladder (Gems are earned only): crit chance.
	LuckyBones = {
		currency = "Gems",
		costs = { 10, 40, 150, 600, 2500 },
		values = { 0, 0.05, 0.1, 0.15, 0.2, 0.25 },
	},
}
Config.rebirthResets = { "Peak", "Cannon", "BoneValue", "Brittle", "Bounce", "ComboTime" }

Config.rarities = {
	{ name = "Common", weight = 600 },
	{ name = "Uncommon", weight = 250 },
	{ name = "Rare", weight = 100 },
	{ name = "Epic", weight = 40 },
	{ name = "Legendary", weight = 9 },
	{ name = "Mythic", weight = 0.9 },
	{ name = "Secret", weight = 0.1 },
}
Config.announceRarities = { Mythic = true, Secret = true }

Config.mutations = {
	{ name = "Gold", chance = 0.05, multiplier = 2 },
	{ name = "Rainbow", chance = 0.01, multiplier = 5 },
}

-- "Crash Buddies": power adds to Hit Power (1 + sum of equipped power).
Config.pets = {
	PebblePup = { name = "Pebble Pup", rarity = "Common", power = 0.1 },
	Goatling = { name = "Goatling", rarity = "Common", power = 0.12 },
	BackpackBeaver = { name = "Backpack Beaver", rarity = "Uncommon", power = 0.25 },
	HelmetHedgehog = { name = "Helmet Hedgehog", rarity = "Rare", power = 0.5 },
	BoulderBull = { name = "Boulder Bull", rarity = "Epic", power = 1 },
	AvalanchePug = { name = "Avalanche Pug", rarity = "Legendary", power = 2 },
	ThunderYak = { name = "Thunder Yak", rarity = "Mythic", power = 5 },

	PineconePig = { name = "Pinecone Pig", rarity = "Common", power = 0.4 },
	LumberLynx = { name = "Lumber Lynx", rarity = "Common", power = 0.45 },
	MooseMallet = { name = "Moose Mallet", rarity = "Uncommon", power = 0.9 },
	OwlRanger = { name = "Owl Ranger", rarity = "Rare", power = 1.8 },
	Bearricade = { name = "Bear-ricade", rarity = "Epic", power = 3.5 },
	TimberWolf = { name = "Timber Wolf", rarity = "Legendary", power = 7 },
	Sasquash = { name = "Sasquash", rarity = "Mythic", power = 18 },

	SnowballSeal = { name = "Snowball Seal", rarity = "Common", power = 1.5 },
	IcicleImp = { name = "Icicle Imp", rarity = "Common", power = 1.7 },
	SledHusky = { name = "Sled Husky", rarity = "Uncommon", power = 3.4 },
	PenguinPilot = { name = "Penguin Pilot", rarity = "Rare", power = 7 },
	GlacierWalrus = { name = "Glacier Walrus", rarity = "Epic", power = 14 },
	YetiYeeter = { name = "Yeti Yeeter", rarity = "Legendary", power = 28 },
	BlizzardBison = { name = "Blizzard Bison", rarity = "Mythic", power = 70 },

	EmberNewt = { name = "Ember Newt", rarity = "Common", power = 6 },
	CinderCrab = { name = "Cinder Crab", rarity = "Common", power = 7 },
	LavaLlama = { name = "Lava Llama", rarity = "Uncommon", power = 14 },
	ObsidianOx = { name = "Obsidian Ox", rarity = "Rare", power = 28 },
	MagmaMammoth = { name = "Magma Mammoth", rarity = "Epic", power = 55 },
	VolcanoDragon = { name = "Volcano Dragon", rarity = "Legendary", power = 110 },
	PhoenixPancake = { name = "Phoenix Pancake", rarity = "Mythic", power = 280 },

	StaticSheep = { name = "Static Sheep", rarity = "Common", power = 24 },
	CloudCalf = { name = "Cloud Calf", rarity = "Common", power = 28 },
	ZapFerret = { name = "Zap Ferret", rarity = "Uncommon", power = 56 },
	Thunderbird = { name = "Thunderbird", rarity = "Rare", power = 110 },
	StormRhino = { name = "Storm Rhino", rarity = "Epic", power = 220 },
	SkyKraken = { name = "Sky Kraken", rarity = "Legendary", power = 450 },
	LightningLion = { name = "Lightning Lion", rarity = "Mythic", power = 1100 },

	SkellyCat = { name = "Skelly-Cat", rarity = "Secret", power = 2500 },

	-- Season 1 premium exclusives (not in eggs).
	FrostyRagdog = { name = "Frosty Ragdog", rarity = "Legendary", power = 40, exclusive = true },
	AvalancheSkelly = { name = "Avalanche Skelly", rarity = "Mythic", power = 900, exclusive = true },
}

local function egg(cost, peak, pets)
	return {
		cost = cost,
		currency = "Cash",
		peak = peak, -- buyable once this peak is unlocked
		luckStartsAt = "Rare",
		pity = { threshold = 75, minTier = "Legendary" },
		pool = {
			Common = { pets[1], pets[2] },
			Uncommon = { pets[3] },
			Rare = { pets[4] },
			Epic = { pets[5] },
			Legendary = { pets[6] },
			Mythic = { pets[7] },
			Secret = { "SkellyCat" },
		},
	}
end

Config.eggs = {
	Trailhead = egg(150, 1, {
		"PebblePup",
		"Goatling",
		"BackpackBeaver",
		"HelmetHedgehog",
		"BoulderBull",
		"AvalanchePug",
		"ThunderYak",
	}),
	Pine = egg(6000, 2, {
		"PineconePig",
		"LumberLynx",
		"MooseMallet",
		"OwlRanger",
		"Bearricade",
		"TimberWolf",
		"Sasquash",
	}),
	Frost = egg(300000, 3, {
		"SnowballSeal",
		"IcicleImp",
		"SledHusky",
		"PenguinPilot",
		"GlacierWalrus",
		"YetiYeeter",
		"BlizzardBison",
	}),
	Magma = egg(15000000, 4, {
		"EmberNewt",
		"CinderCrab",
		"LavaLlama",
		"ObsidianOx",
		"MagmaMammoth",
		"VolcanoDragon",
		"PhoenixPancake",
	}),
	Storm = egg(750000000, 5, {
		"StaticSheep",
		"CloudCalf",
		"ZapFerret",
		"Thunderbird",
		"StormRhino",
		"SkyKraken",
		"LightningLion",
	}),
}

Config.inventory = { capacity = 200, equipSlots = 3 }
Config.extraEquipPassSlots = 1

-- 6 progressive base camps (game.md §3.6). Stage = highest reached ever (never downgrades).
Config.bases = {
	count = 6,
	stages = {
		{ name = "Trail Tent", model = "BaseCamp_Stage1", peak = 1, bonus = 1 },
		{ name = "Log Cabin", model = "BaseCamp_Stage2", peak = 2, bonus = 1.05 },
		{ name = "Ski Lodge", model = "BaseCamp_Stage3", peak = 3, bonus = 1.1 },
		{ name = "Alpine Chalet", model = "BaseCamp_Stage4", peak = 4, bonus = 1.15 },
		{ name = "Summit Hall", model = "BaseCamp_Stage5", peak = 5, rebirths = 1, bonus = 1.25 },
	},
}

Config.rebirth = { currency = "Cash", baseCost = 1000000000, growth = 3, multiplierPerRebirth = 0.5 }

Config.boosts = {
	defs = {
		CashX2 = { multiplier = 2, label = "x2 Cash" },
		LuckX2 = { multiplier = 2, label = "x2 Luck" },
	},
	maxSeconds = 4 * 3600,
}
Config.onboardingBoost = { boost = "CashX2", seconds = 600 } -- after the tutorial, once

Config.friends = { perFriend = 0.1, max = 0.3 }

-- Config-driven events (no live schedule invented). Server toggles `active`.
Config.events = {
	AvalancheHour = { label = "AVALANCHE HOUR: x2 Bone Value", boneValue = 2 },
}

Config.rewards = {
	quests = {
		{ id = "first_launch", stat = "launches", goal = 1, reward = { currency = "Cash", amount = 100 } },
		{ id = "bones_1k", stat = "bones", goal = 1000, reward = { currency = "Gems", amount = 10 } },
		{ id = "hatch10", stat = "eggsHatched", goal = 10, reward = { currency = "Gems", amount = 10 } },
	},
	daily = {
		{ currency = "Cash", amount = 200 },
		{ currency = "Cash", amount = 1000 },
		{ currency = "Gems", amount = 5 },
		{ currency = "Cash", amount = 10000 },
		{ currency = "Gems", amount = 15 },
		{ boost = "CashX2", seconds = 900 },
		{ item = "BackpackBeaver", bonus = { currency = "Gems", amount = 50 } }, -- big Day 7 prize
	},
	playtime = {
		{ seconds = 300, reward = { currency = "Cash", amount = 500 } },
		{ seconds = 900, reward = { currency = "Gems", amount = 10 } },
		{ seconds = 1800, reward = { boost = "LuckX2", seconds = 900 } },
		{ seconds = 3600, reward = { currency = "Gems", amount = 40 } },
	},
}

Config.periodicQuests = {
	periods = {
		daily = { length = 86400 },
		weekly = { length = 604800, offset = 345600 }, -- Monday 00:00 UTC
	},
	quests = {
		{
			id = "d_bones",
			period = "daily",
			stat = "bones",
			goal = 100,
			text = "Break 100 bones",
			reward = {
				currency = "Cash",
				amount = 1000,
			},
		},
		{
			id = "d_launch",
			period = "daily",
			stat = "launches",
			goal = 10,
			text = "Launch 10 times",
			reward = {
				currency = "Gems",
				amount = 5,
			},
		},
		{
			id = "d_combo",
			period = "daily",
			stat = "combo2",
			goal = 1,
			text = "Land a x2 combo",
			reward = {
				currency = "Cash",
				amount = 2000,
			},
		},
		{
			id = "w_bones",
			period = "weekly",
			stat = "bones",
			goal = 5000,
			text = "Break 5,000 bones",
			reward = {
				currency = "Gems",
				amount = 50,
			},
		},
		{
			id = "w_skeleton",
			period = "weekly",
			stat = "fullSkeleton",
			goal = 1,
			text = "Full Skeleton once",
			reward = {
				currency = "Gems",
				amount = 100,
			},
		},
		{
			id = "w_hatch",
			period = "weekly",
			stat = "eggsHatched",
			goal = 25,
			text = "Hatch 25 eggs",
			reward = {
				currency = "Gems",
				amount = 40,
			},
		},
	},
	xpPerQuest = 50,
}

-- Season 1: AVALANCHE — 50 tiers. End date + premium price are CONFIG_REQUIRED.
local seasonFree, seasonPremium = {}, {}
for tier = 1, 50 do
	if tier % 10 == 0 then
		seasonFree[tier] = { decoration = "S1_Deco_" .. tier, bonus = { currency = "Gems", amount = tier } }
	elseif tier % 5 == 0 then
		seasonFree[tier] = { boost = "CashX2", seconds = 600 }
	elseif tier % 2 == 0 then
		seasonFree[tier] = { currency = "Gems", amount = 5 + tier // 5 }
	else
		seasonFree[tier] = { currency = "Cash", amount = 500 * tier }
	end
	if tier == 25 then
		seasonPremium[tier] = { item = "FrostyRagdog" }
	elseif tier == 50 then
		seasonPremium[tier] = { item = "AvalancheSkelly" }
	elseif tier % 5 == 0 then
		seasonPremium[tier] = { cosmetic = "S1_Cosmetic_" .. tier }
	else
		seasonPremium[tier] = { currency = "Gems", amount = 10 + tier }
	end
end
Config.season = {
	seasonId = "S1_Avalanche",
	tiers = 50,
	baseXp = 100,
	xpGrowth = 20,
	free = seasonFree,
	premium = seasonPremium,
	xpPerBone = 1,
	xpPerFullSkeleton = 25,
	endsAt = nil, -- CONFIG_REQUIRED (UTC seconds)
	premiumPassId = 0, -- CONFIG_REQUIRED
}

-- Promo codes: mock values, owner approves real ones (CONFIG_REQUIRED).
Config.codes = {
	SNAP = { reward = { currency = "Cash", amount = 1000 } },
	BONEZONE = { reward = { currency = "Gems", amount = 10 } },
}

Config.tutorial = {
	steps = {
		{ id = "lift", text = "Step on the Lift pad to ride up Pebble Hill!", target = "LiftPad" },
		{ id = "launch", text = "Hold LAUNCH to charge, release to yeet yourself!", ui = "LaunchButton" },
		{ id = "bones", text = "Every bone you break = Cash! Check your run summary.", ui = "RunSummary" },
		{ id = "upgrade", text = "Buy the Party Popper cannon to launch harder!", target = "CannonShop" },
		{ id = "rewards", text = "Free stuff lives here: Daily, Quests and Season!", ui = "RewardsButton" },
	},
}

Config.leaderboards = {
	bonesStore = "ragdoll-off-a-mountain_TotalBones_v1", -- OrderedDataStore (all-time)
	refreshSeconds = 60,
	size = 50,
}

Config.announcements = { minSeconds = 10 }

-- Monetization: every id is a CONFIG_REQUIRED placeholder (0 = not created yet).
Config.monetization = {
	passes = {
		-- [passId] = name ; fill real ids once the owner creates them
	},
	passNames = { "VIP", "x2Luck", "ExtraEquip", "GlassBones", "AutoLaunch", "SeasonPremium" },
	ladders = {
		-- context-named "x2 Cash" ladder: x2 -> x4 -> x8 -> x16 -> x32 -> x64 -> x128 (max).
		-- { productId = <CONFIG_REQUIRED>, multiplier = 2 }, ... rising prices set on Roblox.
		Cash = {},
	},
	ladderMultipliers = { 2, 4, 8, 16, 32, 64, 128 },
	vipCashMultiplier = 1.5,
	glassBonesImpact = 1.5,
}

return Config
