local Monetization = require("../../src/Shared/Monetization")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Monetization", function()
		local function make()
			local grants = 0
			local checks = 0
			local m = Monetization.new({
				products = {
					[1] = {
						name = "Cash1",
						grant = function(_, profile)
							grants += 1
							profile.cash = (profile.cash or 0) + 1000
							return true
						end,
					},
					[2] = {
						name = "Broken",
						grant = function()
							error("boom")
						end,
					},
				},
				passes = { [500] = "VIP" },
				ladders = {
					Cash = {
						{ productId = 11, multiplier = 2 },
						{ productId = 12, multiplier = 5 },
						{ productId = 13, multiplier = 100 },
					},
				},
				ownsPass = function(_, passId)
					checks += 1
					return passId == 500
				end,
				historySize = 3,
			})
			return m, function()
				return grants, checks
			end
		end
		it("grants once per PurchaseId (idempotent retries)", function()
			local m, counts = make()
			local profile = {}
			local receipt = { PurchaseId = "abc", PlayerId = 1, ProductId = 1 }
			expect(m:processReceipt(receipt, profile)).toBe("granted")
			expect(m:processReceipt(receipt, profile)).toBe("granted")
			local grants = counts()
			expect(grants).toBe(1)
			expect(profile.cash).toBe(1000)
		end)
		it("retries when profile missing, product unknown or grant fails", function()
			local m = make()
			expect(m:processReceipt({ PurchaseId = "a", PlayerId = 1, ProductId = 1 }, nil)).toBe("retry")
			expect(m:processReceipt({ PurchaseId = "b", PlayerId = 1, ProductId = 999 }, {})).toBe("retry")
			local profile = {}
			expect(m:processReceipt({ PurchaseId = "c", PlayerId = 1, ProductId = 2 }, profile)).toBe("retry")
			expect(profile.purchases.history.c).toBeNil()
		end)
		it("2x -> 100x ladder upgrades and never downgrades", function()
			local m = make()
			local profile = {}
			expect(m:ladderMultiplier(profile, "Cash")).toBe(1)
			expect(m:nextLadderTier(profile, "Cash").productId).toBe(11)
			m:processReceipt({ PurchaseId = "p1", PlayerId = 1, ProductId = 11 }, profile)
			expect(m:ladderMultiplier(profile, "Cash")).toBe(2)
			m:processReceipt({ PurchaseId = "p2", PlayerId = 1, ProductId = 13 }, profile)
			expect(m:ladderMultiplier(profile, "Cash")).toBe(100)
			m:processReceipt({ PurchaseId = "p3", PlayerId = 1, ProductId = 12 }, profile)
			expect(m:ladderMultiplier(profile, "Cash")).toBe(100)
			expect(m:nextLadderTier(profile, "Cash")).toBeNil()
		end)
		it("caps receipt history", function()
			local m = make()
			local profile = {}
			for i = 1, 5 do
				m:processReceipt({ PurchaseId = "r" .. i, PlayerId = 1, ProductId = 1 }, profile)
			end
			expect(#profile.purchases.order).toBe(3)
			expect(profile.purchases.history.r1).toBeNil()
			expect(profile.purchases.history.r5).toBe(true)
		end)
		it("caches gamepass checks", function()
			local m, counts = make()
			expect(m:hasPass(1, "VIP")).toBe(true)
			expect(m:hasPass(1, "VIP")).toBe(true)
			local _, checks = counts()
			expect(checks).toBe(1)
			expect(m:hasPass(1, "Nope")).toBe(false)
			expect(m:passFlags(1).VIP).toBe(true)
		end)
	end)
end
