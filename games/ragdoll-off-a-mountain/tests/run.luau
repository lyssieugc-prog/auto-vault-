-- Ragdoll Off a Mountain tests: config consistency + full player loop through GameLogic (Lune).
-- Run from the game folder's parent repo root: `lune run games/ragdoll-off-a-mountain/tests/run`

local process = require("@lune/process")

local Config = require("../src/shared/Config")
local GameLogic = require("../src/shared/GameLogic")
local TestKit = require("../vendor/vault/tests/TestKit")

local M = {}
for _, name in
	{ "Currency", "Inventory", "Upgrades", "Rebirth", "Rewards", "Tutorial", "Monetization", "Rarity", "DataService" }
do
	M[name] = require("../vendor/vault/Shared/" .. name)
end

local describe, it, expect = TestKit.describe, TestKit.it, TestKit.expect

describe("Ragdoll Off a Mountain config", function()
	it("every egg pool pet exists with the matching rarity", function()
		for eggName, egg in Config.eggs do
			for tier, pets in egg.pool do
				expect(#pets > 0).toBe(true)
				for _, petId in pets do
					local def = Config.pets[petId]
					if not def or def.rarity ~= tier then
						error(string.format("egg %s: pet %s missing or not %s", eggName, petId, tier))
					end
				end
			end
			for _, tier in Config.rarities do
				if egg.pool[tier.name] == nil then
					error(string.format("egg %s has no pool for tier %s", eggName, tier.name))
				end
			end
		end
	end)
	it("reward items exist", function()
		for _, reward in Config.rewards.daily do
			if reward.item then
				expect(Config.pets[reward.item] ~= nil).toBe(true)
			end
		end
	end)
	it("builds every system without errors", function()
		GameLogic.new(Config, M, { rng = TestKit.seededRng(1) })
	end)
end)

describe("Ragdoll Off a Mountain player loop", function()
	local clock = TestKit.clock(86400 * 20000)
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

	it("collect earns and advances tutorial", function()
		for _ = 1, 60 do
			logic:collect(uid)
		end
		expect(logic.currency:get(uid, "Cash")).toBe(60)
		expect(logic.tutorial:current(profile.tutorial).id).toBe("hatch")
	end)
	it("hatch spends, rolls, adds pet; rejects bad input", function()
		local result = logic:hatch(uid, "Starter")
		expect(result ~= nil).toBe(true)
		expect(logic.currency:get(uid, "Cash")).toBe(10)
		expect(logic.inventory:count(uid)).toBe(1)
		local none, err = logic:hatch(uid, "Starter")
		expect(none).toBeNil()
		expect(err).toBe("funds")
		local _, bad = logic:hatch(uid, { "exploit" })
		expect(bad).toBe("invalid_egg")
	end)
	it("equip raises the pet multiplier", function()
		local before = logic.currency:multiplier(uid, "Cash")
		local uidPet = next(logic.inventory:list(uid))
		expect(logic:equip(uid, uidPet)).toBe(true)
		expect(logic.currency:multiplier(uid, "Cash") > before).toBe(true)
		expect(logic.tutorial:isDone(profile.tutorial)).toBe(true)
	end)
	it("upgrades validate keys and funds", function()
		local _, invalid = logic:buyUpgrade(uid, "NotAnUpgrade")
		expect(invalid).toBe("invalid")
		logic.currency:add(uid, "Cash", 1000)
		expect(logic:buyUpgrade(uid, "ClickPower")).toBe(true)
	end)
	it("daily + playtime + quests", function()
		local reward, day = logic:claimDaily(uid)
		expect(day).toBe(1)
		expect(reward ~= nil).toBe(true)
		local _, notReady = logic:claimPlaytime(uid, 1)
		expect(notReady).toBe("not_ready")
		clock.advance(301)
		expect(logic:claimPlaytime(uid, 1) ~= nil).toBe(true)
		local _, inc = logic:claimQuest(uid, "hatch5")
		expect(inc).toBe("incomplete")
	end)
	it("rebirth resets cash and boosts multiplier", function()
		logic.currency:add(uid, "Cash", Config.rebirth.baseCost)
		expect(logic:doRebirth(uid)).toBe(true)
		expect(logic.currency:get(uid, "Cash")).toBe(0)
		expect(logic.rebirth:count(uid)).toBe(1)
	end)
	it("save -> reload restores everything", function()
		logic:writeProfile(uid, profile)
		expect(data:release(uid)).toBe(true)
		logic:unloadPlayer(uid)
		local logic2, data2 = boot()
		local p2 = data2:load(uid)
		logic2:loadPlayer(uid, p2)
		expect(logic2.inventory:count(uid)).toBe(1)
		expect(#logic2.inventory:equipped(uid)).toBe(1)
		expect(logic2.rebirth:count(uid)).toBe(1)
		expect(logic2.tutorial:isDone(p2.tutorial)).toBe(true)
		expect(p2.rewards.daily.streak).toBe(1)
		expect(logic2:snapshot(uid).rebirths).toBe(1)
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
