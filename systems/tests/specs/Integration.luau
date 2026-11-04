-- End-to-end loop with several systems wired together the way templates/game wires them:
-- profile load -> earn -> hatch -> equip -> tycoon buy -> rebirth -> save -> reload.

local Currency = require("../../src/Shared/Currency")
local DataService = require("../../src/Shared/DataService")
local Inventory = require("../../src/Shared/Inventory")
local Rarity = require("../../src/Shared/Rarity")
local Rebirth = require("../../src/Shared/Rebirth")
local Rewards = require("../../src/Shared/Rewards")
local Tycoon = require("../../src/Shared/Tycoon")

local function memoryStore()
	local data = {}
	return {
		update = function(_, key, transform)
			local new = transform(if data[key] then DataService.deepCopy(data[key]) else nil)
			if new ~= nil then
				data[key] = DataService.deepCopy(new)
			end
			return new, nil
		end,
	}
end

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Integration", function()
		it("core loop survives a save/reload", function()
			local store = memoryStore()
			local template = {
				currency = {},
				inventory = {},
				tycoon = {},
				rebirths = 0,
				pity = { count = 0 },
				rewards = Rewards.newState(),
			}
			local function boot()
				local systems = {
					data = DataService.new({ store = store, template = template, sessionId = "S" }),
					currency = Currency.new({ currencies = { Cash = { start = 0 } } }),
					inventory = Inventory.new({ capacity = 50, equipSlots = 3 }),
					rarity = Rarity.new({
						tiers = { { name = "Common", weight = 9 }, { name = "Rare", weight = 1 } },
						pity = { threshold = 5, minTier = "Rare" },
						rng = t.seededRng(7),
					}),
					tycoon = Tycoon.new({
						items = {
							{ id = "Base", cost = 0, currency = "Cash" },
							{ id = "Dropper", cost = 50, currency = "Cash", requires = { "Base" }, income = 10 },
						},
					}),
				}
				systems.rebirth = Rebirth.new({
					currency = "Cash",
					baseCost = 100,
					onReset = function(userId)
						systems.tycoon:reset(userId, { "Base" })
					end,
				})
				return systems
			end
			local s = boot()
			local uid = 1
			local profile = s.data:load(uid)
			s.currency:load(uid, profile.currency)
			s.inventory:load(uid, profile.inventory)
			s.tycoon:load(uid, profile.tycoon)
			s.rebirth:load(uid, profile.rebirths)

			s.currency:earn(uid, "Cash", 60)
			s.tycoon:buy(uid, "Base", s.currency)
			expect(s.tycoon:buy(uid, "Dropper", s.currency)).toBe(true)
			s.currency:setIncome(uid, "Tycoon", "Cash", s.tycoon:income(uid))
			s.currency:step(10)
			expect(s.currency:get(uid, "Cash")).toBe(110)

			local sawRare = false
			for _ = 1, 5 do
				local tier = s.rarity:roll(1, profile.pity)
				sawRare = sawRare or tier == "Rare"
				local petUid = s.inventory:add(uid, { id = "Pet", rarity = tier })
				s.inventory:equip(uid, petUid)
			end
			expect(sawRare).toBe(true) -- pity guarantees one Rare within 5 rolls
			expect(#s.inventory:equipped(uid)).toBe(3)

			expect(s.rebirth:rebirth(uid, s.currency)).toBe(true)
			s.currency:setMultiplier(uid, "Rebirth", s.rebirth:multiplier(uid))
			expect(s.tycoon:owns(uid, "Dropper")).toBe(false)

			profile.currency = s.currency:serialize(uid)
			profile.inventory = s.inventory:serialize(uid)
			profile.tycoon = s.tycoon:serialize(uid)
			profile.rebirths = s.rebirth:serialize(uid)
			expect(s.data:release(uid)).toBe(true)

			local s2 = boot()
			local p2 = s2.data:load(uid)
			s2.inventory:load(uid, p2.inventory)
			s2.rebirth:load(uid, p2.rebirths)
			expect(s2.inventory:count(uid)).toBe(5)
			expect(#s2.inventory:equipped(uid)).toBe(3)
			expect(s2.rebirth:count(uid)).toBe(1)
			expect(p2.currency.Cash).toBe(0)
		end)
	end)
end
