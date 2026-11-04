local Rarity = require("../../src/Shared/Rarity")

local TIERS = {
	{ name = "Common", weight = 600 },
	{ name = "Uncommon", weight = 250 },
	{ name = "Rare", weight = 100 },
	{ name = "Epic", weight = 40 },
	{ name = "Legendary", weight = 9 },
	{ name = "Mythic", weight = 1 },
}

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Rarity", function()
		it("odds sum to 100", function()
			local r = Rarity.new({ tiers = TIERS })
			local total = 0
			for _, o in r:odds() do
				total += o.percent
			end
			expect(total).toBeNear(100, 1e-9)
			expect(r:odds()[1].percent).toBeNear(60, 1e-9)
		end)
		it("luck boosts only tiers from luckStartsAt", function()
			local r = Rarity.new({ tiers = TIERS, luckStartsAt = "Rare" })
			local w = r:weights(2)
			expect(w[1]).toBe(600)
			expect(w[3]).toBe(200)
			expect(w[6]).toBe(2)
		end)
		it("roll distribution roughly matches weights", function()
			local r = Rarity.new({ tiers = TIERS, rng = t.seededRng(42) })
			local counts = {}
			for _ = 1, 20000 do
				local name = r:roll()
				counts[name] = (counts[name] or 0) + 1
			end
			expect(counts.Common / 20000).toBeNear(0.6, 0.02)
			expect(counts.Uncommon / 20000).toBeNear(0.25, 0.02)
		end)
		it("pity guarantees minTier at threshold and resets", function()
			local r = Rarity.new({
				tiers = TIERS,
				pity = { threshold = 10, minTier = "Legendary" },
				rng = function()
					return 0 -- always the first eligible tier
				end,
			})
			local pity = { count = 0 }
			for _ = 1, 9 do
				expect(r:roll(1, pity)).toBe("Common")
			end
			expect(r:pityRemaining(pity)).toBe(1)
			expect(r:roll(1, pity)).toBe("Legendary")
			expect(pity.count).toBe(0)
		end)
		it("rolls mutations by chance", function()
			local r = Rarity.new({
				tiers = TIERS,
				mutations = { { name = "Gold", chance = 0.5, multiplier = 2 } },
				rng = function()
					return 0.25
				end,
			})
			local name, mult = r:rollMutation()
			expect(name).toBe("Gold")
			expect(mult).toBe(2)
			local none, one = r:rollMutation(0.1)
			expect(none).toBeNil()
			expect(one).toBe(1)
		end)
		it("rejects bad config", function()
			expect(function()
				Rarity.new({ tiers = {} })
			end).toThrow()
			expect(function()
				Rarity.new({ tiers = TIERS, luckStartsAt = "Nope" })
			end).toThrow()
		end)
		it("pickWeighted", function()
			local v = Rarity.pickWeighted({ { value = "a", weight = 1 }, { value = "b", weight = 3 } }, function()
				return 0.5
			end)
			expect(v).toBe("b")
		end)
	end)
end
