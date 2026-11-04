-- Ragdoll Off a Mountain tests: config consistency, bone-scoring rules and the full player loop
-- through GameLogic (Lune). Run from the repo root: `lune run games/ragdoll-off-a-mountain/tests/run`

local process = require("@lune/process")

local Config = require("../src/shared/Config")
local GameLogic = require("../src/shared/GameLogic")
local RagdollScore = require("../src/shared/RagdollScore")
local TestKit = require("../vendor/vault/tests/TestKit")

local M = { RagdollScore = RagdollScore }
for _, name in GameLogic.MODULES do
	M[name] = require("../vendor/vault/Shared/" .. name)
end
M.DataService = require("../vendor/vault/Shared/DataService")

local describe, it, expect = TestKit.describe, TestKit.it, TestKit.expect

local function rewardItemsExist(reward)
	if type(reward) ~= "table" then
		return
	end
	if reward.item and Config.pets[reward.item] == nil then
		error("reward item missing: " .. reward.item)
	end
	if reward.boost and Config.boosts.defs[reward.boost] == nil then
		error("reward boost missing: " .. reward.boost)
	end
	rewardItemsExist(reward.bonus)
end

describe("Config", function()
	it("has exactly 206 bones across the 15 R15 parts", function()
		local total, parts = 0, 0
		for _, part in Config.scoring.parts do
			total += part.bones
			parts += 1
		end
		expect(total).toBe(206)
		expect(parts).toBe(15)
		expect(RagdollScore.new(Config.scoring).totalBones).toBe(206)
	end)
	it("every egg pool pet exists with the matching rarity, every tier present", function()
		for eggName, egg in Config.eggs do
			for tier, pets in egg.pool do
				expect(#pets > 0).toBe(true)
				for _, petId in pets do
					local def = Config.pets[petId]
					if not def or def.rarity ~= tier or def.exclusive then
						error(string.format("egg %s: pet %s missing, exclusive or not %s", eggName, petId, tier))
					end
				end
			end
			for _, tier in Config.rarities do
				if egg.pool[tier.name] == nil then
					error(string.format("egg %s has no pool for tier %s", eggName, tier.name))
				end
			end
			expect(egg.peak >= 1 and egg.peak <= #Config.peaks).toBe(true)
		end
	end)
	it("ladders cover every peak and cannon; peaks and cannons get stronger", function()
		expect(#Config.upgrades.Peak.values).toBe(#Config.peaks)
		expect(#Config.upgrades.Peak.costs).toBe(#Config.peaks - 1)
		expect(#Config.upgrades.Cannon.values).toBe(#Config.cannons)
		for i = 2, #Config.peaks do
			expect(Config.peaks[i].multiplier > Config.peaks[i - 1].multiplier).toBe(true)
			expect(Config.peaks[i].height > Config.peaks[i - 1].height).toBe(true)
			expect(Config.upgrades.Peak.costs[i - 1] > (Config.upgrades.Peak.costs[i - 2] or 0)).toBe(true)
		end
		for i = 2, #Config.cannons do
			expect(Config.cannons[i].speed > Config.cannons[i - 1].speed).toBe(true)
		end
	end)
	it("6 players, 6 bases, 5 stages with rising bonus", function()
		expect(Config.maxPlayers).toBe(6)
		expect(Config.bases.count).toBe(6)
		expect(#Config.bases.stages).toBe(5)
		for i = 2, #Config.bases.stages do
			expect(Config.bases.stages[i].bonus > Config.bases.stages[i - 1].bonus).toBe(true)
		end
	end)
	it("every reward item / boost referenced anywhere exists", function()
		for _, reward in Config.rewards.daily do
			rewardItemsExist(reward)
		end
		for _, entry in Config.rewards.playtime do
			rewardItemsExist(entry.reward)
		end
		for tier = 1, Config.season.tiers do
			rewardItemsExist(Config.season.free[tier])
			rewardItemsExist(Config.season.premium[tier])
			expect(Config.season.free[tier] ~= nil).toBe(true)
		end
		expect(Config.season.tiers).toBe(50)
	end)
	it("x2 ladder is x2 -> x128 max, ids stay CONFIG_REQUIRED placeholders", function()
		local ladder = Config.monetization.ladderMultipliers
		expect(#ladder).toBe(7)
		for i, value in ladder do
			expect(value).toBe(2 ^ i)
		end
		for id in Config.monetization.passes do
			expect(id).toBe(0)
		end
	end)
	it("builds every system without errors", function()
		GameLogic.new(Config, M, { rng = TestKit.seededRng(1) })
	end)
end)

describe("RagdollScore", function()
	local score = RagdollScore.new(Config.scoring)
	it("breaks more bones and pays more for harder hits", function()
		local run = score:newRun({ startedAt = 0 })
		expect(score:impact(run, "Head", 30, 1)).toBeNil() -- under breakSpeed
		local e = score:impact(run, "Head", 120, 2)
		expect(e.broken).toBe(4) -- 1 + floor((120 - 45) / 25)
		expect(e.severity).toBeNear(120 / 45)
		expect(e.cash).toBeNear(4 * 6 * 120 / 45)
		expect(e.combo).toBe(1)
		expect(e.bonesLeft).toBe(25)
	end)
	it("ignores contact jitter, invalid parts and bad numbers", function()
		local run = score:newRun({ startedAt = 0 })
		expect(score:impact(run, "LeftFoot", 100, 1) ~= nil).toBe(true)
		expect(score:impact(run, "LeftFoot", 100, 1.05)).toBeNil() -- part cooldown
		expect(score:impact(run, "Tail", 500, 2)).toBeNil()
		expect(score:impact(run, "Head", 0 / 0, 2)).toBeNil()
		expect(score:impact(run, "Head", -100, 2)).toBeNil()
		expect(score:impact(run, { "Head" }, 100, 2)).toBeNil()
		expect(score:impact(run, "Head", 100, "now")).toBeNil()
		local huge = score:impact(run, "Head", math.huge, 3)
		expect(huge.severity).toBe(Config.scoring.maxSeverity) -- clamped, not infinite
	end)
	it("caps breaks by bones left in the part", function()
		local run = score:newRun({ startedAt = 0 })
		local e = score:impact(run, "LeftUpperLeg", 1000, 1)
		expect(e.broken).toBe(2)
		expect(score:impact(run, "LeftUpperLeg", 1000, 2)).toBeNil()
	end)
	it("chains combos inside the window, resets outside it, caps at comboMax", function()
		local run = score:newRun({ startedAt = 0, comboWindow = 1 })
		local parts = { "Head", "UpperTorso", "LowerTorso", "LeftHand", "RightHand" }
		local last
		for i, part in parts do
			last = score:impact(run, part, 50, i * 0.5)
		end
		expect(last.combo).toBeNear(1.4)
		local reset = score:impact(run, "LeftFoot", 50, 10)
		expect(reset.combo).toBe(1)
		local maxed = score:newRun({ startedAt = 0, comboWindow = 1 })
		for i = 1, 30 do
			last = score:impact(maxed, "UpperTorso", 50, i * 0.2)
		end
		expect(last.combo).toBe(Config.scoring.comboMax)
	end)
	it("crits double severity", function()
		local run = score:newRun({
			startedAt = 0,
			critChance = 1,
			rng = function()
				return 0
			end,
		})
		local e = score:impact(run, "Head", 45, 1)
		expect(e.severity).toBe(2)
		expect(e.critical).toBe(true)
	end)
	it("Full Skeleton: all 206 bones doubles the run", function()
		local run = score:newRun({ startedAt = 0, impactMultiplier = 3 })
		local t = 0
		for _, part in score.partNames do
			t += 5 -- outside the combo window, so combo stays x1
			score:impact(run, part, 2000, t)
		end
		local raw = run.cash
		local summary = score:finish(run)
		expect(summary.bones).toBe(206)
		expect(summary.fullSkeleton).toBe(true)
		expect(summary.cash).toBe(math.floor(raw * 2))
		expect(score:impact(run, "Head", 100, t + 1)).toBeNil() -- finished runs take no more hits
		expect(score:finish(run)).toBe(summary)
	end)
end)

describe("Player loop", function()
	local clock = TestKit.clock(86400 * 20000 + 3600)
	local store = {
		data = {},
		update = function(self, key, transform)
			local new = transform(self.data[key] and M.DataService.deepCopy(self.data[key]))
			if new ~= nil then
				self.data[key] = M.DataService.deepCopy(new)
			end
			return new, nil
		end,
	}
	local function boot()
		local logic = GameLogic.new(Config, M, { rng = TestKit.seededRng(99), now = clock.now })
		local data = M.DataService.new({ store = store, template = GameLogic.profileTemplate(M), now = clock.now })
		return logic, data
	end
	local logic, data = boot()
	local uid = 42
	local profile = data:load(uid)
	logic:loadPlayer(uid, profile)

	local function fullSkeletonRun()
		clock.advance(Config.run.cooldown)
		assert(logic:startRun(uid, 20, 0, 1))
		local t = clock.now()
		for _, part in logic.score.partNames do
			t += 5
			logic:reportImpact(uid, part, 2000, t)
		end
		return logic:finishRun(uid)
	end

	it("claims one of the 6 bases on join", function()
		expect(logic.plots:plotOf(uid)).toBe(1)
		expect(profile.bestStage).toBe(1)
		expect(logic:snapshot(uid).base.plot).toBe(1)
	end)
	it("rejects bad launch input from the client", function()
		for _, args in
			{
				{ 0 / 0, 0, 1 },
				{ 999, 0, 1 },
				{ 20, 90, 1 },
				{ 20, 0, 1.5 },
				{ 20, 0, -1 },
				{ "20", 0, 1 },
				{ 20, {}, 1 },
				{ 20, 0, math.huge },
			}
		do
			local params, err = logic:startRun(uid, args[1], args[2], args[3])
			expect(params).toBeNil()
			expect(err).toBe("invalid")
		end
		expect(logic:isRunning(uid)).toBe(false)
	end)
	it("a launch breaks bones, pays Cash on the server and advances the tutorial", function()
		logic:tutorialEvent(uid, "lift")
		local params = logic:startRun(uid, 20, 0, 1)
		expect(params.speed).toBe(Config.cannons[1].speed)
		expect(params.peak).toBe(1)
		local _, running = logic:startRun(uid, 20, 0, 1)
		expect(running).toBe("running")
		local t = clock.now()
		local e = logic:reportImpact(uid, "Head", 120, t + 1)
		expect(e.broken).toBe(4)
		logic:reportImpact(uid, "UpperTorso", 50, t + 1.5)
		expect(logic:reportImpact(uid, "Head", "lots", t + 2)).toBeNil()
		local summary = logic:finishRun(uid)
		expect(summary.bones).toBe(5)
		expect(summary.earned).toBe(67) -- 64 + 3.67 (combo x1.1), floored
		expect(logic.currency:get(uid, "Cash")).toBe(67)
		expect(profile.stats.bones).toBe(5)
		expect(profile.skeletonIndex.Head).toBe(true)
		expect(#summary.newIndex).toBe(2)
		expect(logic.tutorial:current(profile.tutorial).id).toBe("upgrade")
		expect(logic:reportImpact(uid, "Head", 120, t + 3)).toBeNil() -- no run open
		local _, cooldown = logic:startRun(uid, 20, 0, 1)
		expect(cooldown).toBe("cooldown")
	end)
	it("cannon purchase raises launch speed and finishes onboarding with a timed boost", function()
		local _, funds = logic:buyCannon(uid)
		expect(funds).toBe("funds")
		logic.currency:add(uid, "Cash", 500)
		expect(logic:buyCannon(uid)).toBe(true)
		expect(logic:cannon(uid).name).toBe("Party Popper")
		expect(logic.tutorial:current(profile.tutorial).id).toBe("rewards")
		logic:claimDaily(uid) -- day 1 = 200 Cash, does not count as the rewards step (quests do)
		expect(logic.currency:get(uid, "Cash")).toBe(267)
	end)
	it("Full Skeleton pays double + Gems, completes quests and season tiers", function()
		local before = logic.currency:get(uid, "Cash")
		local summary = fullSkeletonRun()
		expect(summary.fullSkeleton).toBe(true)
		expect(summary.gems).toBe(Config.run.fullSkeletonGems)
		expect(logic.currency:get(uid, "Cash") - before).toBe(summary.earned)
		expect(profile.stats.fullSkeletons).toBe(1)
		expect(#summary.seasonTiers).toBe(2) -- 5 + 206 + 25 XP = 236 -> tiers 1 (100) and 2 (220)
		-- daily quest: break 100 bones -> claim marks the tutorial's last step and grants the boost
		expect(logic:claimQuest(uid, "d_bones").amount).toBe(1000)
		expect(logic.tutorial:isDone(profile.tutorial)).toBe(true)
		expect(logic.boosts:remaining(profile.boosts, "CashX2")).toBe(Config.onboardingBoost.seconds)
		expect(logic.currency:multiplier(uid, "Cash")).toBe(2)
		local _, again = logic:claimQuest(uid, "d_bones")
		expect(again).toBe("claimed")
		local _, weekly = logic:claimQuest(uid, "w_bones")
		expect(weekly).toBe("incomplete")
		expect(logic:claimQuest(uid, "w_skeleton").amount).toBe(100)
		local _, bad = logic:claimQuest(uid, string.rep("x", 100))
		expect(bad).toBe("invalid")
	end)
	it("season pass: free claims once, premium gated, locked tiers refused", function()
		expect(logic:claimSeason(uid, "free", 1).amount).toBe(500)
		local _, again = logic:claimSeason(uid, "free", 1)
		expect(again).toBe("claimed")
		local _, premium = logic:claimSeason(uid, "premium", 1)
		expect(premium).toBe("premium")
		local _, locked = logic:claimSeason(uid, "free", 30)
		expect(locked).toBe("locked")
		local _, invalid = logic:claimSeason(uid, "free", 0 / 0)
		expect(invalid).toBe("invalid")
	end)
	it("eggs: peak-gated, odds as 1-in-N, pets raise Hit Power and run cash", function()
		local _, locked = logic:hatch(uid, "Pine")
		expect(locked).toBe("locked")
		local _, bad = logic:hatch(uid, { "exploit" })
		expect(bad).toBe("invalid_egg")
		local odds = logic:eggOdds(uid, "Trailhead")
		expect(odds[7].name).toBe("Secret")
		expect(odds[7].oneIn).toBeNear(10000, 1e-6)
		logic.currency:add(uid, "Cash", 150)
		local result = logic:hatch(uid, "Trailhead")
		expect(result ~= nil).toBe(true)
		expect(profile.petIndex[result.id]).toBe(true)
		expect(logic.inventory:count(uid)).toBe(1)
		local hitBefore = logic:hitPower(uid)
		expect(logic:equip(uid, result.uid)).toBe(true)
		expect(logic:hitPower(uid) > hitBefore).toBe(true)
		expect(logic:impactMultiplier(uid) <= Config.run.maxPetImpact).toBe(true)
		local _, invalid = logic:equip(uid, string.rep("a", 50))
		expect(invalid).toBe("invalid")
	end)
	it("upgrades validate keys; Peak/Cannon only via their own shops", function()
		local _, invalid = logic:buyUpgrade(uid, "Peak")
		expect(invalid).toBe("invalid")
		local _, junk = logic:buyUpgrade(uid, nil)
		expect(junk).toBe("invalid")
		logic.currency:add(uid, "Cash", 100)
		expect(logic:buyUpgrade(uid, "BoneValue")).toBe(true)
		expect(logic.upgrades:value(uid, "BoneValue")).toBe(1.25)
	end)
	it("unlocking a peak selects it and upgrades the base camp", function()
		local _, locked = logic:selectPeak(uid, 2)
		expect(locked).toBe("locked")
		logic.currency:add(uid, "Cash", 2500)
		expect(logic:unlockPeak(uid)).toBe(true)
		expect(profile.selectedPeak).toBe(2)
		expect(profile.bestStage).toBe(2)
		expect(logic:selectPeak(uid, 1)).toBe(true)
		local _, invalid = logic:selectPeak(uid, 1.5)
		expect(invalid).toBe("invalid")
		logic:selectPeak(uid, 2)
		clock.advance(Config.run.cooldown)
		local params = logic:startRun(uid, 20, 0, 0)
		expect(params.peak).toBe(2)
		expect(params.speed).toBeNear(Config.cannons[2].speed * 0.6)
		logic:finishRun(uid)
	end)
	it("codes redeem once; playtime waits for real session time", function()
		expect(logic:redeemCode(uid, " snap ").amount).toBe(1000)
		local _, again = logic:redeemCode(uid, "SNAP")
		expect(again).toBe("redeemed")
		local _, invalid = logic:redeemCode(uid, "FREEROBUX")
		expect(invalid).toBe("invalid")
		local _, notReady = logic:claimPlaytime(uid, 2)
		expect(notReady).toBe("not_ready")
		clock.advance(900)
		expect(logic:claimPlaytime(uid, 2).amount).toBe(10)
	end)
	it("boost expires on the server clock and multipliers refresh", function()
		clock.advance(Config.onboardingBoost.seconds)
		expect(logic:tick(uid)).toBe(true)
		expect(logic.currency:multiplier(uid, "Cash")).toBe(Config.bases.stages[2].bonus)
	end)
	it("friends bonus is capped", function()
		logic:setFriendsInServer(uid, 10)
		expect(logic.currency:multiplier(uid, "Cash")).toBeNear(Config.bases.stages[2].bonus * 1.3)
		logic:setFriendsInServer(uid, 0)
	end)
	it("rebirth resets peaks/cannons/upgrades, keeps pets, Gems and base stage", function()
		local gems = logic.currency:get(uid, "Gems")
		logic.currency:add(uid, "Cash", Config.rebirth.baseCost)
		expect(logic:doRebirth(uid)).toBe(true)
		expect(logic.currency:get(uid, "Cash")).toBe(0)
		expect(logic.currency:get(uid, "Gems")).toBe(gems)
		expect(logic:unlockedPeak(uid)).toBe(1)
		expect(logic:cannon(uid).name).toBe("Bare Feet")
		expect(logic.upgrades:value(uid, "BoneValue")).toBe(1)
		expect(profile.selectedPeak).toBe(1)
		expect(logic.inventory:count(uid)).toBe(1)
		expect(profile.bestStage).toBe(5) -- Summit Hall unlocks on the first rebirth
		expect(logic.currency:multiplier(uid, "Cash")).toBeNear(1.5 * Config.bases.stages[5].bonus)
	end)
	it("leaving mid-run pays the run out; save -> reload restores everything", function()
		clock.advance(Config.run.cooldown)
		assert(logic:startRun(uid, 20, 0, 1))
		logic:reportImpact(uid, "Head", 120, clock.now() + 1)
		expect(logic:endSession(uid).bones).toBe(4) -- pays the run that was still in the air
		logic:writeProfile(uid, profile)
		expect(data:release(uid)).toBe(true)
		logic:unloadPlayer(uid)
		local logic2, data2 = boot()
		local p2 = data2:load(uid)
		logic2:loadPlayer(uid, p2)
		expect(logic2.currency:get(uid, "Cash") > 0).toBe(true)
		expect(logic2.inventory:count(uid)).toBe(1)
		expect(#logic2.inventory:equipped(uid)).toBe(1)
		expect(logic2.rebirth:count(uid)).toBe(1)
		expect(p2.bestStage).toBe(5)
		expect(p2.stats.fullSkeletons).toBe(1)
		expect(p2.skeletonIndex.Head).toBe(true)
		expect(p2.codes.redeemed.SNAP).toBe(true)
		expect(p2.season.claimed.free["1"]).toBe(true)
		expect(logic2.tutorial:isDone(p2.tutorial)).toBe(true)
		expect(p2.onboardingBoostGiven).toBe(true)
		local snap = logic2:snapshot(uid)
		expect(snap.rebirths).toBe(1)
		expect(snap.base.stage).toBe(5)
		expect(snap.season.tier >= 2).toBe(true)
	end)
	it("has no trading / transfer endpoints (owner standard)", function()
		for name in GameLogic do
			local lower = string.lower(name)
			if string.find(lower, "trade") or string.find(lower, "transfer") or string.find(lower, "gift") then
				error("forbidden endpoint: " .. name)
			end
		end
	end)
end)

local results = TestKit.results()
for _, failure in results.failures do
	print("FAIL " .. failure)
end
print(string.format("\nRagdoll Off a Mountain: %d passed, %d failed", results.passed, results.failed))
if results.failed > 0 then
	process.exit(1)
end
