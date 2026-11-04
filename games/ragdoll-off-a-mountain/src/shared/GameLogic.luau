--[[
	GameLogic — Ragdoll Off a Mountain rules, built from Config + vault systems. Pure: modules and
	clocks are injected, so tests/run.luau drives the full loop under Lune and the server scripts only
	wire Roblox events (remotes, physics, DataStores) to these methods.

	local logic = GameLogic.new(Config, Modules, { rng = fn, now = os.time, ownsPass = fn })
	logic:loadPlayer(userId, profile)
	local params = logic:startRun(userId, pitch, yaw, charge)   -- server applies the launch physics
	logic:reportImpact(userId, "Head", 140, t)                  -- server physics glue only; t = s since launch
	local summary = logic:finishRun(userId)                     -- pays Cash, stats, quests, season XP

	Every method validates its own inputs (server-authoritative); callers pass raw remote args.
	NO trading: there is intentionally no method that moves items or currency between players.
]]

local GameLogic = {}
GameLogic.__index = GameLogic

local MODULES = {
	"Currency",
	"Inventory",
	"Upgrades",
	"Rebirth",
	"Rewards",
	"Tutorial",
	"Monetization",
	"Rarity",
	"Plots",
	"Boosts",
	"SeasonPass",
	"PeriodicQuests",
	"Codes",
}
GameLogic.MODULES = MODULES

local SHOP_UPGRADES = { BoneValue = true, Brittle = true, Bounce = true, ComboTime = true, LuckyBones = true }

function GameLogic.profileTemplate(M)
	return {
		currency = {},
		inventory = {},
		upgrades = {},
		rebirths = 0,
		pity = {},
		rewards = M.Rewards.newState(),
		tutorial = M.Tutorial.newState(),
		boosts = M.Boosts.newState(),
		season = false, -- SeasonPass:ensure() creates it on load
		periodicQuests = M.PeriodicQuests.newState(),
		codes = M.Codes.newState(),
		skeletonIndex = {}, -- [partName] = true once that part had a bone broken
		petIndex = {}, -- [petId] = true once owned
		stats = { bones = 0, launches = 0, bestRun = 0, fullSkeletons = 0, eggsHatched = 0 },
		bestStage = 1,
		selectedPeak = 1,
		onboardingBoostGiven = false,
	}
end

function GameLogic.new(Config, M, deps)
	deps = deps or {}
	local self = setmetatable({}, GameLogic)
	self.Config = Config
	self.M = M
	self.now = deps.now or os.time
	self.rng = deps.rng or math.random
	self.Score = deps.RagdollScore or M.RagdollScore
	assert(self.Score, "GameLogic.new: RagdollScore module required")
	self.score = self.Score.new(Config.scoring)
	self.currency = M.Currency.new({ currencies = Config.currencies })
	self.inventory = M.Inventory.new(Config.inventory)
	self.upgrades = M.Upgrades.new({ upgrades = Config.upgrades })
	self.rebirth = M.Rebirth.new({
		currency = Config.rebirth.currency,
		baseCost = Config.rebirth.baseCost,
		growth = Config.rebirth.growth,
		multiplierPerRebirth = Config.rebirth.multiplierPerRebirth,
		onReset = function(userId)
			self.upgrades:reset(userId, Config.rebirthResets)
			local profile = self.profiles[userId]
			profile.selectedPeak = 1
			self:updateBaseStage(userId)
		end,
	})
	self.rewards = M.Rewards.new({
		quests = Config.rewards.quests,
		daily = Config.rewards.daily,
		playtime = Config.rewards.playtime,
		now = self.now,
	})
	self.tutorial = M.Tutorial.new(Config.tutorial)
	self.plots = M.Plots.new({ count = Config.bases.count })
	self.boosts = M.Boosts.new({ defs = Config.boosts.defs, maxSeconds = Config.boosts.maxSeconds, now = self.now })
	self.season = M.SeasonPass.new(Config.season)
	self.quests = M.PeriodicQuests.new({
		periods = Config.periodicQuests.periods,
		quests = Config.periodicQuests.quests,
		now = self.now,
	})
	self.codes = M.Codes.new({ codes = Config.codes, now = self.now })
	local passes = {}
	for id, name in Config.monetization.passes do
		if type(id) == "number" and id > 0 then -- 0 = placeholder, never query
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
	self.runs = {} -- [userId] = active RagdollScore run
	self.lastLaunch = {}
	self.friendCount = {}
	self.activeEvents = {}
	return self
end

-- Player lifecycle ---------------------------------------------------------------------------------

function GameLogic:loadPlayer(userId, profile)
	local template = GameLogic.profileTemplate(self.M)
	for key, value in template do
		if profile[key] == nil then
			profile[key] = value
		end
	end
	for key, value in template.stats do
		if profile.stats[key] == nil then
			profile.stats[key] = value
		end
	end
	profile.season = self.season:ensure(profile.season)
	self.profiles[userId] = profile
	self.currency:load(userId, profile.currency)
	self.inventory:load(userId, profile.inventory)
	self.upgrades:load(userId, profile.upgrades)
	self.rebirth:load(userId, profile.rebirths)
	self.M.Rewards.resetPlaytime(profile.rewards)
	self.boosts:prune(profile.boosts)
	self.sessionStart[userId] = self.now()
	local slots = self.Config.inventory.equipSlots
	if self.monetization:hasPass(userId, "ExtraEquip") then
		slots += self.Config.extraEquipPassSlots
	end
	self.inventory:setEquipSlots(userId, slots)
	if self.monetization:hasPass(userId, "SeasonPremium") then
		self.season:setPremium(profile.season, true)
	end
	profile.selectedPeak = math.clamp(math.floor(tonumber(profile.selectedPeak) or 1), 1, self:unlockedPeak(userId))
	self.plots:claim(userId)
	self:updateBaseStage(userId)
	self:refreshMultipliers(userId)
end

function GameLogic:writeProfile(userId, profile)
	profile.currency = self.currency:serialize(userId)
	profile.inventory = self.inventory:serialize(userId)
	profile.upgrades = self.upgrades:serialize(userId)
	profile.rebirths = self.rebirth:serialize(userId)
end

-- Call before the final writeProfile on leave/shutdown: pays out a run that is still in the air.
function GameLogic:endSession(userId)
	if self.runs[userId] then
		return self:finishRun(userId)
	end
	return nil
end

function GameLogic:unloadPlayer(userId)
	self.runs[userId] = nil
	self.currency:unload(userId)
	self.inventory:unload(userId)
	self.upgrades:unload(userId)
	self.rebirth:unload(userId)
	self.monetization:removePlayer(userId)
	self.plots:release(userId)
	self.profiles[userId] = nil
	self.sessionStart[userId] = nil
	self.lastLaunch[userId] = nil
	self.friendCount[userId] = nil
end

-- Derived values -----------------------------------------------------------------------------------

function GameLogic:unlockedPeak(userId): number
	return self.upgrades:value(userId, "Peak")
end

function GameLogic:cannon(userId)
	return self.Config.cannons[self.upgrades:value(userId, "Cannon")]
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

-- Hit Power = 1 + equipped pet power. Part of it raises physical impact force (capped), all of it pays.
function GameLogic:hitPower(userId): number
	return 1 + self:petPower(userId)
end

function GameLogic:impactMultiplier(userId): number
	local mult = math.min(self:hitPower(userId), self.Config.run.maxPetImpact) * self.upgrades:value(userId, "Brittle")
	if self.monetization:hasPass(userId, "GlassBones") then
		mult *= self.Config.monetization.glassBonesImpact
	end
	return mult
end

function GameLogic:eventBoneValue(): number
	local mult = 1
	for name, def in self.Config.events do
		if self.activeEvents[name] and def.boneValue then
			mult *= def.boneValue
		end
	end
	return mult
end

function GameLogic:luck(userId): number
	local luck = self.boosts:multiplier(self.profiles[userId].boosts, "LuckX2")
	if self.monetization:hasPass(userId, "x2Luck") then
		luck *= 2
	end
	return luck
end

function GameLogic:baseStageFor(userId): number
	local profile = self.profiles[userId]
	local peak = self:unlockedPeak(userId)
	local rebirths = self.rebirth:count(userId)
	local best = 1
	for i, stage in self.Config.bases.stages do
		if peak >= (stage.peak or 1) or (stage.rebirths ~= nil and rebirths >= stage.rebirths) then
			best = i
		end
	end
	return math.max(best, profile.bestStage or 1)
end

-- Returns the new stage and whether it went up.
function GameLogic:updateBaseStage(userId): (number, boolean)
	local profile = self.profiles[userId]
	local before = profile.bestStage or 1
	profile.bestStage = self:baseStageFor(userId)
	return profile.bestStage, profile.bestStage > before
end

function GameLogic:setFriendsInServer(userId, count: number)
	self.friendCount[userId] = math.max(0, math.floor(tonumber(count) or 0))
	if self.profiles[userId] then
		self:refreshMultipliers(userId)
	end
end

function GameLogic:setEventActive(name: string, active: boolean)
	if self.Config.events[name] then
		self.activeEvents[name] = active == true or nil
	end
end

function GameLogic:refreshMultipliers(userId)
	local c = self.currency
	local profile = self.profiles[userId]
	c:setMultiplier(userId, "Rebirth", self.rebirth:multiplier(userId), "Cash")
	c:setMultiplier(userId, "Ladder", self.monetization:ladderMultiplier(profile, "Cash"), "Cash")
	local vip = self.monetization:hasPass(userId, "VIP")
	c:setMultiplier(userId, "VIP", if vip then self.Config.monetization.vipCashMultiplier else nil, "Cash")
	c:setMultiplier(userId, "Base", self.Config.bases.stages[profile.bestStage].bonus, "Cash")
	c:setMultiplier(userId, "Boost", self.boosts:multiplier(profile.boosts, "CashX2"), "Cash")
	local friends = self.friendCount[userId] or 0
	local bonus = math.min(friends * self.Config.friends.perFriend, self.Config.friends.max)
	c:setMultiplier(userId, "Friends", if bonus > 0 then 1 + bonus else nil, "Cash")
end

-- Grants a reward table: { currency, amount } | { item } | { boost, seconds } | { decoration } |
-- { cosmetic }, optionally with a `bonus` reward attached.
function GameLogic:grant(userId, reward)
	if type(reward) ~= "table" then
		return false
	end
	local profile = self.profiles[userId]
	local ok = false
	if reward.currency then
		self.currency:add(userId, reward.currency, reward.amount, "reward")
		ok = true
	elseif reward.item then
		local def = self.Config.pets[reward.item]
		if def then
			ok = self.inventory:add(userId, { id = reward.item, rarity = def.rarity }) ~= nil
			if ok then
				profile.petIndex[reward.item] = true
			end
		end
	elseif reward.boost then
		ok = self.boosts:grant(profile.boosts, reward.boost, reward.seconds) ~= nil
		self:refreshMultipliers(userId)
	elseif reward.decoration or reward.cosmetic then
		profile.unlocks = profile.unlocks or {}
		profile.unlocks[reward.decoration or reward.cosmetic] = true
		ok = true
	end
	if ok and reward.bonus then
		self:grant(userId, reward.bonus)
	end
	return ok
end

function GameLogic:_progress(userId, stat: string, amount: number)
	local profile = self.profiles[userId]
	self.rewards:progress(profile.rewards, stat, amount)
	self.quests:progress(profile.periodicQuests, stat, amount)
end

function GameLogic:tutorialEvent(userId, stepId: string)
	local profile = self.profiles[userId]
	local nextStep, changed = self.tutorial:complete(profile.tutorial, stepId)
	if changed and self.tutorial:isDone(profile.tutorial) and not profile.onboardingBoostGiven then
		profile.onboardingBoostGiven = true
		local boost = self.Config.onboardingBoost
		self.boosts:grant(profile.boosts, boost.boost, boost.seconds)
		self:refreshMultipliers(userId)
	end
	return nextStep, changed
end

function GameLogic:skipTutorial(userId)
	local profile = self.profiles[userId]
	self.tutorial:skip(profile.tutorial)
end

-- Runs (the core loop) -----------------------------------------------------------------------------

function GameLogic:selectPeak(userId, index: any): (boolean, string?)
	if type(index) ~= "number" or index % 1 ~= 0 or index < 1 or index > #self.Config.peaks then
		return false, "invalid"
	end
	if index > self:unlockedPeak(userId) then
		return false, "locked"
	end
	self.profiles[userId].selectedPeak = index
	return true, nil
end

-- Validates the launch request and opens a run. Returns launch params for the physics glue.
function GameLogic:startRun(userId, pitch: any, yaw: any, charge: any)
	local aim = self.Config.run.aim
	if type(pitch) ~= "number" or pitch ~= pitch or pitch < aim.minPitch or pitch > aim.maxPitch then
		return nil, "invalid"
	end
	if type(yaw) ~= "number" or yaw ~= yaw or math.abs(yaw) > aim.maxYaw then
		return nil, "invalid"
	end
	if type(charge) ~= "number" or charge ~= charge or charge < 0 or charge > 1 then
		return nil, "invalid"
	end
	if self.runs[userId] then
		return nil, "running"
	end
	local now = self.now()
	local last = self.lastLaunch[userId]
	if last and now - last < self.Config.run.cooldown then
		return nil, "cooldown"
	end
	self.lastLaunch[userId] = now
	local profile = self.profiles[userId]
	local peak = self.Config.peaks[profile.selectedPeak]
	local cannon = self:cannon(userId)
	self.runs[userId] = self.score:newRun({
		impactMultiplier = self:impactMultiplier(userId),
		cashMultiplier = self:hitPower(userId) * self.upgrades:value(userId, "BoneValue") * self:eventBoneValue(),
		peakMultiplier = peak.multiplier,
		comboWindow = self.upgrades:value(userId, "ComboTime"),
		critChance = self.upgrades:value(userId, "LuckyBones"),
		rng = self.rng,
		startedAt = 0, -- impact times are seconds since launch (server physics clock)
	})
	profile.stats.launches += 1
	self:_progress(userId, "launches", 1)
	self:tutorialEvent(userId, "launch")
	return {
		peak = profile.selectedPeak,
		cannon = cannon.name,
		speed = cannon.speed * (0.6 + 0.4 * charge),
		pitch = pitch,
		yaw = yaw,
		elasticity = self.upgrades:value(userId, "Bounce"),
		maxSeconds = self.Config.run.maxSeconds,
	},
		nil
end

function GameLogic:isRunning(userId): boolean
	return self.runs[userId] ~= nil
end

-- Called by the SERVER physics glue only. Returns the scoring event (for the bone pop) or nil.
function GameLogic:reportImpact(userId, partName: any, speed: any, t: any)
	local run = self.runs[userId]
	if not run then
		return nil
	end
	local event = self.score:impact(run, partName, speed, t)
	if event then
		event.displayCash = math.floor(event.cash * self.currency:multiplier(userId, "Cash"))
	end
	return event
end

function GameLogic:finishRun(userId)
	local run = self.runs[userId]
	if not run then
		return nil, "not_running"
	end
	self.runs[userId] = nil
	local summary = self.score:finish(run)
	local profile = self.profiles[userId]
	summary.earned = if summary.cash > 0 then self.currency:earn(userId, "Cash", summary.cash, "run") else 0
	summary.gems = 0
	if summary.fullSkeleton then
		summary.gems = self.Config.run.fullSkeletonGems
		self.currency:add(userId, "Gems", summary.gems, "fullSkeleton")
		profile.stats.fullSkeletons += 1
		self:_progress(userId, "fullSkeleton", 1)
	end
	local stats = profile.stats
	stats.bones += summary.bones
	summary.newBest = summary.earned > stats.bestRun
	stats.bestRun = math.max(stats.bestRun, summary.earned)
	summary.newIndex = {}
	for part in summary.partsHit do
		if not profile.skeletonIndex[part] then
			profile.skeletonIndex[part] = true
			table.insert(summary.newIndex, part)
		end
	end
	table.sort(summary.newIndex)
	if summary.bones > 0 then
		self:_progress(userId, "bones", summary.bones)
		self:tutorialEvent(userId, "bones")
	end
	if summary.bestCombo >= 2 then
		self:_progress(userId, "combo2", 1)
	end
	local xp = summary.bones * self.Config.season.xpPerBone
	if summary.fullSkeleton then
		xp += self.Config.season.xpPerFullSkeleton
	end
	summary.seasonTiers = self.season:addXp(profile.season, xp)
	return summary, nil
end

-- Shops ----------------------------------------------------------------------------------------------

function GameLogic:buyUpgrade(userId, key: any): (boolean, string?)
	if type(key) ~= "string" or not SHOP_UPGRADES[key] then
		return false, "invalid"
	end
	local ok, err = self.upgrades:buy(userId, key, self.currency)
	return ok, err
end

function GameLogic:buyCannon(userId): (boolean, string?)
	local ok, err = self.upgrades:buy(userId, "Cannon", self.currency)
	if ok then
		self:tutorialEvent(userId, "upgrade")
	end
	return ok, err
end

function GameLogic:unlockPeak(userId): (boolean, string?)
	local ok, err = self.upgrades:buy(userId, "Peak", self.currency)
	if ok then
		self.profiles[userId].selectedPeak = self:unlockedPeak(userId)
		self:updateBaseStage(userId)
		self:refreshMultipliers(userId)
	end
	return ok, err
end

function GameLogic:hatch(userId, eggName: any)
	local egg = type(eggName) == "string" and self.Config.eggs[eggName]
	if not egg then
		return nil, "invalid_egg"
	end
	if egg.peak > self:unlockedPeak(userId) then
		return nil, "locked"
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
	local tier = roller:roll(self:luck(userId), profile.pity[eggName])
	local pool = egg.pool[tier]
	local petId = pool[math.clamp(math.floor(self.rng() * #pool) + 1, 1, #pool)]
	local mutation, mult = roller:rollMutation()
	local uid =
		self.inventory:add(userId, { id = petId, rarity = tier, mutation = mutation, mutationMultiplier = mult })
	profile.petIndex[petId] = true
	profile.stats.eggsHatched += 1
	self:_progress(userId, "eggsHatched", 1)
	return {
		uid = uid,
		id = petId,
		rarity = tier,
		mutation = mutation,
		announce = self.Config.announceRarities[tier] == true,
		pityRemaining = roller:pityRemaining(profile.pity[eggName]),
	},
		nil
end

-- Odds strip data as "1 in N" + percent (true server weights with the player's current luck).
function GameLogic:eggOdds(userId, eggName: any)
	local roller = type(eggName) == "string" and self.eggs[eggName]
	if not roller then
		return nil
	end
	local rows = {}
	for _, row in roller:odds(self:luck(userId)) do
		table.insert(rows, {
			name = row.name,
			percent = row.percent,
			oneIn = if row.percent > 0 then 100 / row.percent else nil, -- UI shows "1 in N"
		})
	end
	return rows
end

function GameLogic:equip(userId, uid: any)
	if type(uid) ~= "string" or #uid > 20 then
		return false, "invalid"
	end
	return self.inventory:equip(userId, uid)
end

function GameLogic:unequip(userId, uid: any)
	if type(uid) ~= "string" or #uid > 20 then
		return false
	end
	return self.inventory:unequip(userId, uid)
end

function GameLogic:doRebirth(userId)
	if self.runs[userId] then
		return false, "running"
	end
	local ok, err = self.rebirth:rebirth(userId, self.currency)
	if ok then
		self:refreshMultipliers(userId)
	end
	return ok, err
end

-- Rewards ----------------------------------------------------------------------------------------------

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

-- Claims an all-time quest (Rewards) or a daily/weekly quest (PeriodicQuests) by id.
function GameLogic:claimQuest(userId, questId: any)
	if type(questId) ~= "string" or #questId > 40 then
		return nil, "invalid"
	end
	local profile = self.profiles[userId]
	local reward, err
	if self.rewards.questById[questId] then
		reward, err = self.rewards:claimQuest(profile.rewards, questId)
	else
		reward, err = self.quests:claim(profile.periodicQuests, questId)
		if reward then
			self.season:addXp(profile.season, self.Config.periodicQuests.xpPerQuest)
		end
	end
	if reward then
		self:grant(userId, reward)
		self:tutorialEvent(userId, "rewards")
	end
	return reward, err
end

function GameLogic:claimSeason(userId, track: any, tier: any)
	local profile = self.profiles[userId]
	local reward, err = self.season:claim(profile.season, track, tier)
	if reward then
		self:grant(userId, reward)
	end
	return reward, err
end

function GameLogic:redeemCode(userId, code: any)
	local reward, err = self.codes:redeem(self.profiles[userId].codes, code)
	if reward then
		self:grant(userId, reward)
	end
	return reward, err
end

-- Called once per second by the server: expires boosts and refreshes multipliers when one ends.
function GameLogic:tick(userId)
	local profile = self.profiles[userId]
	if profile and #self.boosts:prune(profile.boosts) > 0 then
		self:refreshMultipliers(userId)
		return true
	end
	return false
end

-- Snapshot sent to the client for HUD/UI rendering (read-only view).
function GameLogic:snapshot(userId)
	local profile = self.profiles[userId]
	local upgrades = {}
	for key in SHOP_UPGRADES do
		upgrades[key] = {
			level = self.upgrades:level(userId, key),
			cost = self.upgrades:cost(userId, key),
			value = self.upgrades:value(userId, key),
		}
	end
	return {
		currency = self.currency:serialize(userId),
		cashMultiplier = self.currency:multiplier(userId, "Cash"),
		inventory = self.inventory:serialize(userId),
		upgrades = upgrades,
		peak = { selected = profile.selectedPeak, unlocked = self:unlockedPeak(userId), nextCost = self.upgrades:cost(
			userId,
			"Peak"
		) },
		cannon = { level = self.upgrades:value(userId, "Cannon"), nextCost = self.upgrades:cost(userId, "Cannon") },
		hitPower = self:hitPower(userId),
		base = { plot = self.plots:plotOf(userId), stage = profile.bestStage },
		rebirths = self.rebirth:count(userId),
		rebirthGoal = self.rebirth:nextGoal(userId, self.currency),
		tutorial = self.tutorial:current(profile.tutorial),
		daily = self.rewards:dailyStatus(profile.rewards),
		quests = self.quests:list(profile.periodicQuests),
		season = self.season:status(profile.season),
		boosts = self.boosts:list(profile.boosts),
		stats = table.clone(profile.stats),
		skeletonIndex = table.clone(profile.skeletonIndex),
		petIndex = table.clone(profile.petIndex),
		running = self.runs[userId] ~= nil,
	}
end

return GameLogic
