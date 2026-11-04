local Currency = require("../../src/Shared/Currency")
local Rebirth = require("../../src/Shared/Rebirth")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Rebirth", function()
		it("costs, resets currency, raises multiplier, calls onReset", function()
			local cur = Currency.new({ currencies = { Cash = { start = 0 }, Gems = { start = 0 } } })
			cur:load(1)
			local resets = 0
			local r = Rebirth.new({
				currency = "Cash",
				baseCost = 1000,
				growth = 2,
				multiplierPerRebirth = 0.5,
				onReset = function()
					resets += 1
				end,
			})
			r:load(1)
			local ok, err = r:rebirth(1, cur)
			expect(ok).toBe(false)
			expect(err).toBe("funds")
			cur:add(1, "Cash", 1500)
			cur:add(1, "Gems", 7)
			expect(r:nextGoal(1, cur).progress).toBe(1)
			expect(r:rebirth(1, cur)).toBe(true)
			expect(cur:get(1, "Cash")).toBe(0)
			expect(cur:get(1, "Gems")).toBe(7)
			expect(r:count(1)).toBe(1)
			expect(r:multiplier(1)).toBe(1.5)
			expect(r:cost(1)).toBe(2000)
			expect(resets).toBe(1)
		end)
		it("spends the paid currency if it is not in the reset list", function()
			local cur = Currency.new({ currencies = { Cash = { start = 0 }, Gems = { start = 0 } } })
			cur:load(1)
			local r = Rebirth.new({ currency = "Gems", baseCost = 10, resetCurrencies = { "Cash" } })
			r:load(1, 0)
			cur:add(1, "Gems", 15)
			cur:add(1, "Cash", 99)
			expect(r:rebirth(1, cur)).toBe(true)
			expect(cur:get(1, "Gems")).toBe(5)
			expect(cur:get(1, "Cash")).toBe(0)
		end)
	end)
end
