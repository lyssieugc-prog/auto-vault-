local Currency = require("../../src/Shared/Currency")
local Upgrades = require("../../src/Shared/Upgrades")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Upgrades", function()
		local function make()
			local cur = Currency.new({ currencies = { Cash = { start = 1000 }, Gems = { start = 100 } } })
			cur:load(1)
			local up = Upgrades.new({
				upgrades = {
					WalkSpeed = {
						currency = "Cash",
						baseCost = 100,
						growth = 2,
						maxLevel = 3,
						effect = function(level)
							return 16 + level * 2
						end,
					},
					CashMulti = { currency = "Gems", costs = { 10, 50 }, values = { 1, 2, 1250 } },
				},
			})
			up:load(1)
			return up, cur
		end
		it("curve costs and effects", function()
			local up, cur = make()
			expect(up:cost(1, "WalkSpeed")).toBe(100)
			expect(up:buy(1, "WalkSpeed", cur)).toBe(true)
			expect(up:cost(1, "WalkSpeed")).toBe(200)
			expect(up:value(1, "WalkSpeed")).toBe(18)
			up:buy(1, "WalkSpeed", cur)
			up:buy(1, "WalkSpeed", cur)
			expect(cur:get(1, "Cash")).toBe(300)
			local ok, err = up:buy(1, "WalkSpeed", cur)
			expect(ok).toBe(false)
			expect(err).toBe("maxed")
			expect(up:cost(1, "WalkSpeed")).toBeNil()
		end)
		it("tier ladders", function()
			local up, cur = make()
			expect(up:value(1, "CashMulti")).toBe(1)
			up:buy(1, "CashMulti", cur)
			up:buy(1, "CashMulti", cur)
			expect(up:value(1, "CashMulti")).toBe(1250)
			expect(cur:get(1, "Gems")).toBe(40)
			expect(up:isMaxed(1, "CashMulti")).toBe(true)
		end)
		it("insufficient funds leaves level unchanged", function()
			local up, cur = make()
			cur:set(1, "Cash", 50)
			local ok, err = up:buy(1, "WalkSpeed", cur)
			expect(ok).toBe(false)
			expect(err).toBe("funds")
			expect(up:level(1, "WalkSpeed")).toBe(0)
		end)
		it("clamps saved levels and resets", function()
			local up = make()
			up:load(2, { WalkSpeed = 99, CashMulti = -3 })
			expect(up:level(2, "WalkSpeed")).toBe(3)
			expect(up:level(2, "CashMulti")).toBe(0)
			up:reset(2, { "WalkSpeed" })
			expect(up:level(2, "WalkSpeed")).toBe(0)
		end)
	end)
end
