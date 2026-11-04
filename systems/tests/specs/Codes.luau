local Codes = require("../../src/Shared/Codes")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Codes", function()
		local clock = t.clock(1000)
		local codes = Codes.new({
			codes = {
				SNAP = { reward = { currency = "Cash", amount = 1000 } },
				Old = { reward = { currency = "Gems", amount = 1 }, expiresAt = 2000 },
			},
			now = clock.now,
		})
		it("normalizes input and redeems once per user", function()
			local state = Codes.newState()
			expect(codes:redeem(state, "  snap ").amount).toBe(1000)
			local _, again = codes:redeem(state, "SNAP")
			expect(again).toBe("redeemed")
			expect(codes:redeem(Codes.newState(), "Snap").amount).toBe(1000)
		end)
		it("rejects invalid, junk and expired codes", function()
			local state = Codes.newState()
			for _, junk in { "nope", "", "SN AP", "SNAP!", 42, { "SNAP" }, string.rep("A", 100) } do
				local _, err = codes:redeem(state, junk)
				expect(err).toBe("invalid")
			end
			expect(codes:redeem(state, "old").amount).toBe(1)
			clock.advance(1000)
			local _, expired = codes:redeem(Codes.newState(), "OLD")
			expect(expired).toBe("expired")
		end)
	end)
end
