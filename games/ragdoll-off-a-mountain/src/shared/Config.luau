--[[
	Ragdoll Off a Mountain — game configuration. Pure data (no requires) so Lune tests can load it.
	/make-game rewrites this from games/ragdoll-off-a-mountain/game.md. All numbers are tunable.
	Product/pass IDs are 0 placeholders until the owner creates real ones.
]]

local Config = {}

Config.name = "Ragdoll Off a Mountain"
Config.dataStoreName = "ragdoll-off-a-mountain_PlayerData_v1"
Config.studioDataStore = "memory" -- "memory" | "real" (real needs Studio API access, private place)
Config.autosaveSeconds = 90

Config.currencies = {
	Cash = { start = 0 },
	Gems = { start = 0 },
}

Config.collect = { currency = "Cash", amount = 1, rate = 8, burst = 12 } -- per click, server-side

Config.rarities = {
	{ name = "Common", weight = 600 },
	{ name = "Uncommon", weight = 250 },
	{ name = "Rare", weight = 100 },
	{ name = "Epic", weight = 40 },
	{ name = "Legendary", weight = 9 },
	{ name = "Mythic", weight = 0.9 },
	{ name = "Secret", weight = 0.1 },
}

Config.mutations = {
	{ name = "Gold", chance = 0.05, multiplier = 2 },
	{ name = "Rainbow", chance = 0.01, multiplier = 5 },
}

Config.pets = {
	Dog = { rarity = "Common", power = 0.1 },
	Cat = { rarity = "Common", power = 0.12 },
	Bunny = { rarity = "Uncommon", power = 0.25 },
	Fox = { rarity = "Rare", power = 0.6 },
	Dragon = { rarity = "Epic", power = 1.5 },
	Phoenix = { rarity = "Legendary", power = 4 },
	Kraken = { rarity = "Mythic", power = 12 },
	Glitch = { rarity = "Secret", power = 40 },
}

Config.eggs = {
	Starter = {
		cost = 50,
		currency = "Cash",
		luckStartsAt = "Rare",
		pity = { threshold = 75, minTier = "Legendary" },
		pool = {
			Common = { "Dog", "Cat" },
			Uncommon = { "Bunny" },
			Rare = { "Fox" },
			Epic = { "Dragon" },
			Legendary = { "Phoenix" },
			Mythic = { "Kraken" },
			Secret = { "Glitch" },
		},
	},
}

Config.inventory = { capacity = 200, equipSlots = 3 }

Config.upgrades = {
	ClickPower = {
		currency = "Cash",
		baseCost = 25,
		growth = 1.7,
		maxLevel = 25,
		effect = function(level)
			return 1 + level
		end,
	},
	CashMulti = {
		currency = "Gems",
		costs = { 10, 40, 150, 600, 2500, 10000 },
		values = { 1, 2, 5, 25, 100, 500, 1250 },
	},
}

Config.rebirth = { currency = "Cash", baseCost = 10000, growth = 2.5, multiplierPerRebirth = 0.5 }

Config.rewards = {
	quests = {
		{ id = "hatch5", stat = "eggsHatched", goal = 5, reward = { currency = "Gems", amount = 5 } },
		{ id = "click100", stat = "clicks", goal = 100, reward = { currency = "Cash", amount = 250 } },
	},
	daily = {
		{ currency = "Cash", amount = 100 },
		{ currency = "Cash", amount = 250 },
		{ currency = "Gems", amount = 5 },
		{ currency = "Cash", amount = 1000 },
		{ currency = "Gems", amount = 15 },
		{ currency = "Cash", amount = 5000 },
		{ item = "Phoenix" }, -- big Day 7 prize
	},
	playtime = {
		{ seconds = 300, reward = { currency = "Cash", amount = 200 } },
		{ seconds = 900, reward = { currency = "Gems", amount = 3 } },
		{ seconds = 1800, reward = { currency = "Gems", amount = 10 } },
	},
}

Config.tutorial = {
	steps = {
		{ id = "collect", text = "Tap to collect Cash!", clientCompletable = false },
		{ id = "hatch", text = "Hatch your first egg!", target = "EggStand", clientCompletable = false },
		{ id = "equip", text = "Equip your new pet!", ui = "PetsButton", clientCompletable = false },
	},
}

Config.monetization = {
	passes = { [0] = "VIP" }, -- placeholder id
	ladders = {
		Cash = {}, -- fill with { productId, multiplier } 2,3,5,10,25,50,100 once products exist
	},
	vipCashMultiplier = 1.5,
}

return Config
