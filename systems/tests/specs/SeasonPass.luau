local SeasonPass = require("../../src/Shared/SeasonPass")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("SeasonPass", function()
		local function make()
			local free, premium = {}, {}
			for n = 1, 50 do
				free[n] = { currency = "Cash", amount = n * 10 }
			end
			premium[25] = { item = "Pet" }
			premium[50] = { item = "BigPet" }
			return SeasonPass.new({ seasonId = "S1", tiers = 50, baseXp = 100, xpGrowth = 20, free = free, premium = premium })
		end
		it("builds a cumulative curve and reports tiers reached", function()
			local pass = make()
			local state = pass:ensure(nil)
			expect(pass:xpForTier(1)).toBe(100)
			expect(pass:xpForTier(3)).toBe(140)
			expect(#pass:addXp(state, 99)).toBe(0)
			local reached = pass:addXp(state, 221) -- 320 = tiers 1 (100) + 2 (120) + part of 3
			expect(#reached).toBe(2)
			expect(reached[2]).toBe(2)
			local status = pass:status(state)
			expect(status.tier).toBe(2)
			expect(status.xpIntoTier).toBe(100)
			expect(status.xpForNext).toBe(140)
			expect(status.claimable).toBe(2)
		end)
		it("claims free tiers once, locks future tiers, gates premium", function()
			local pass = make()
			local state = pass:ensure(nil)
			pass:addXp(state, 1e9) -- capped at max
			expect(pass:tier(state)).toBe(50)
			expect(pass:claim(state, "free", 1).amount).toBe(10)
			local _, again = pass:claim(state, "free", 1)
			expect(again).toBe("claimed")
			local _, prem = pass:claim(state, "premium", 25)
			expect(prem).toBe("premium")
			pass:setPremium(state, true)
			expect(pass:claim(state, "premium", 25).item).toBe("Pet")
			local _, none = pass:claim(state, "premium", 3)
			expect(none).toBe("none")
			local _, bad = pass:claim(state, "gold", 3)
			expect(bad).toBe("invalid")
			local _, badTier = pass:claim(state, "free", 1.5)
			expect(badTier).toBe("invalid")
			expect(pass:status(state).xpForNext).toBe(0)
		end)
		it("locks unreached tiers and resets on a new season", function()
			local pass = make()
			local state = pass:ensure(nil)
			local _, locked = pass:claim(state, "free", 2)
			expect(locked).toBe("locked")
			expect(#pass:addXp(state, -50)).toBe(0)
			pass:addXp(state, 500)
			local old = SeasonPass.new({ seasonId = "S0" })
			expect(old:ensure(state).xp).toBe(0)
			expect(pass:ensure(state).xp).toBe(500)
		end)
	end)
end
