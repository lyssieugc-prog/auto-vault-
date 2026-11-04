--[[
	GameLogic — the game's rules, built from Config + vault systems. Pure: modules and clocks are
	injected, so tests/run.luau can drive the full loop under Lune and the server Main script only
	wires Roblox events to these methods.

	local logic = GameLogic.new(Config, Modules, { rng = fn, now = os.time, ownsPass = fn })
	logic:loadPlayer(userId, profile) ... logic:hatch(userId, "Starter") ... logic:writeProfile(userId, profile)

	Every method validates its own inputs (server-authoritative); callers pass raw remote args.
]]

local GameLogic = {}
GameLogic.__index = GameLogic

function GameLogic.profileTemplate(M)
	return {
		currency = {},
		inventory = {},
		upgrades = {},
		rebirths = 0,
		pity = {},
		rewards = M.Rewards.newState(),
		tutorial = M.Tutorial.newState(),
	}
end

function GameLogic.new(Config, M, deps)
	deps = deps or {}
	local self = setmetatable({}, GameLogic)
	self.Config = Config
	self.M = M
	self.now = deps.now or os.time
	self.rng = deps.rng or math.random
	self.currency = M.Currency.new({ currencies = Config.currencies })
	self.inventory = M.Inventory.new(Config.inventory)
	self.upgrades = M.Upgrades.new({ upgrades = Config.upgrades })
	self.rebirth = M.Rebirth.new({
		currency = Config.rebirth.currency,
		baseCost = Config.rebirth.baseCost,
		growth = Config.rebirth.growth,
		multiplierPerRebirth = Config.rebirth.multiplierPerRebirth,
		onReset = function(userId)
			self.upgrades:reset(userId, { "ClickPower" })
		end,
	})
	self.rewards = M.Rewards.new({
		quests = Config.rewards.quests,
		daily = Config.rewards.daily,
		playtime = Config.rewards.playtime,
		now = self.now,
	})
	self.tutorial = M.Tutorial.new(Config.tutorial)
	local passes = {}
	for id, name in Config.monetization.passes do
		if id > 0 then -- 0 = placeholder, never query
			passes[id] = name
		end
	end
	local ladders = {}
	for name, tiers in Config.monetization.ladders do
		if #tiers > 0 then
			ladders[name] = tiers
		end
	end
	self.monetization = M.Monetization.new({ passes = passes, ladders = ladders, ownsPass = deps.ownsPass })
	self.eggs = {}
	for eggName, egg in Config.eggs do
		self.eggs[eggName] = M.Rarity.new({
			tiers = Config.rarities,
			luckStartsAt = egg.luckStartsAt,
			pity = egg.pity,
			mutations = Config.mutations,
			rng = self.rng,
		})
	end
	self.profiles = {}
	self.sessionStart = {}
	return self
end

-- Player lifecycle ---------------------------------------------------------------------------------

function GameLogic:loadPlayer(userId, profile)
	self.profiles[userId] = profile
	self.currency:load(userId, profile.currency)
	self.inventory:load(userId, profile.inventory)
	self.upgrades:load(userId, profile.upgrades)
	self.rebirth:load(userId, profile.rebirths)
	self.M.Rewards.resetPlaytime(profile.rewards)
	self.sessionStart[userId] = self.now()
	self:refreshMultipliers(userId)
end

function GameLogic:writeProfile(userId, profile)
	profile.currency = self.currency:serialize(userId)
	profile.inventory = self.inventory:serialize(userId)
	profile.upgrades = self.upgrades:serialize(userId)
	profile.rebirths = self.rebirth:serialize(userId)
end

function GameLogic:unloadPlayer(userId)
	self.currency:unload(userId)
	self.inventory:unload(userId)
	self.upgrades:unload(userId)
	self.rebirth:unload(userId)
	self.monetization:removePlayer(userId)
	self.profiles[userId] = nil
	self.sessionStart[userId] = nil
end

function GameLogic:petPower(userId): number
	local total = 0
	for _, uid in self.inventory:equipped(userId) do
		local item = self.inventory:get(userId, uid)
		local def = item and self.Config.pets[item.id]
		if def then
			total += def.power * (item.mutationMultiplier or 1)
		end
	end
	return total
end

function GameLogic:refreshMultipliers(userId)
	local c = self.currency
	c:setMultiplier(userId, "Rebirth", self.rebirth:multiplier(userId))
	c:setMultiplier(userId, "Pets", 1 + self:petPower(userId))
	c:setMultiplier(userId, "CashMulti", self.upgrades:value(userId, "CashMulti"), "Cash")
	local profile = self.profiles[userId]
	c:setMultiplier(userId, "Ladder", self.monetization:ladderMultiplier(profile, "Cash"), "Cash")
	local vip = self.monetization:hasPass(userId, "VIP")
	c:setMultiplier(userId, "VIP", if vip then self.Config.monetization.vipCashMultiplier else nil, "Cash")
end

function GameLogic:grant(userId, reward)
	if reward == nil then
		return false
	end
	if reward.currency then
		self.currency:add(userId, reward.currency, reward.amount, "reward")
		return true
	elseif reward.item then
		local def = self.Config.pets[reward.item]
		return self.inventory:add(userId, { id = reward.item, rarity = def and def.rarity }) ~= nil
	end
	return false
end

-- Actions (called from remotes) --------------------------------------------------------------------

function GameLogic:collect(userId)
	local cfg = self.Config.collect
	local amount = cfg.amount * self.upgrades:value(userId, "ClickPower")
	local earned = self.currency:earn(userId, cfg.currency, amount, "collect")
	self.rewards:progress(self.profiles[userId].rewards, "clicks", 1)
	self:tutorialEvent(userId, "collect")
	return earned
end

function GameLogic:hatch(userId, eggName: any)
	local egg = type(eggName) == "string" and self.Config.eggs[eggName]
	if not egg then
		return nil, "invalid_egg"
	end
	if self.inventory:isFull(userId) then
		return nil, "full"
	end
	if not self.currency:spend(userId, egg.currency, egg.cost, "hatch:" .. eggName) then
		return nil, "funds"
	end
	local roller = self.eggs[eggName]
	local profile = self.profiles[userId]
	profile.pity[eggName] = profile.pity[eggName] or { count = 0 }
	local luck = if self.monetization:hasPass(userId, "x2Luck") then 2 else 1
	local tier = roller:roll(luck, profile.pity[eggName])
	local pool = egg.pool[tier]
	local petId = pool[math.clamp(math.floor(self.rng() * #pool) + 1, 1, #pool)]
	local mutation, mult = roller:rollMutation()
	local uid =
		self.inventory:add(userId, { id = petId, rarity = tier, mutation = mutation, mutationMultiplier = mult })
	self.rewards:progress(profile.rewards, "eggsHatched", 1)
	self:tutorialEvent(userId, "hatch")
	return { uid = uid, id = petId, rarity = tier, mutation = mutation }, nil
end

function GameLogic:equip(userId, uid: any)
	if type(uid) ~= "string" or #uid > 20 then
		return false, "invalid"
	end
	local ok, err = self.inventory:equip(userId, uid)
	if ok then
		self:refreshMultipliers(userId)
		self:tutorialEvent(userId, "equip")
	end
	return ok, err
end

function GameLogic:unequip(userId, uid: any)
	if type(uid) ~= "string" then
		return false
	end
	local ok = self.inventory:unequip(userId, uid)
	self:refreshMultipliers(userId)
	return ok
end

function GameLogic:buyUpgrade(userId, key: any)
	if type(key) ~= "string" or self.Config.upgrades[key] == nil then
		return false, "invalid"
	end
	local ok, err = self.upgrades:buy(userId, key, self.currency)
	if ok then
		self:refreshMultipliers(userId)
	end
	return ok, err
end

function GameLogic:doRebirth(userId)
	local ok, err = self.rebirth:rebirth(userId, self.currency)
	if ok then
		self:refreshMultipliers(userId)
	end
	return ok, err
end

function GameLogic:claimDaily(userId)
	local reward, dayOrErr = self.rewards:claimDaily(self.profiles[userId].rewards)
	if reward then
		self:grant(userId, reward)
	end
	return reward, dayOrErr
end

function GameLogic:claimPlaytime(userId, index: any)
	if type(index) ~= "number" or index % 1 ~= 0 then
		return nil, "invalid"
	end
	local seconds = self.now() - self.sessionStart[userId]
	local reward, err = self.rewards:claimPlaytime(self.profiles[userId].rewards, index, seconds)
	if reward then
		self:grant(userId, reward)
	end
	return reward, err
end

function GameLogic:claimQuest(userId, questId: any)
	if type(questId) ~= "string" then
		return nil, "invalid"
	end
	local reward, err = self.rewards:claimQuest(self.profiles[userId].rewards, questId)
	if reward then
		self:grant(userId, reward)
	end
	return reward, err
end

function GameLogic:tutorialEvent(userId, stepId: string)
	local profile = self.profiles[userId]
	return self.tutorial:complete(profile.tutorial, stepId)
end

-- Snapshot sent to the client for HUD/UI rendering.
function GameLogic:snapshot(userId)
	local profile = self.profiles[userId]
	return {
		currency = self.currency:serialize(userId),
		inventory = self.inventory:serialize(userId),
		upgrades = self.upgrades:serialize(userId),
		rebirths = self.rebirth:count(userId),
		rebirthCost = self.rebirth:cost(userId),
		tutorial = self.tutorial:current(profile.tutorial),
		daily = self.rewards:dailyStatus(profile.rewards),
	}
end

return GameLogic
