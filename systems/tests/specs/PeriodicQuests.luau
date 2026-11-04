local PeriodicQuests = require("../../src/Shared/PeriodicQuests")

local DAY = 86400

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("PeriodicQuests", function()
		local function make()
			-- 1970-01-05 00:00 UTC was a Monday; start Monday of week 3000 at 10:00
			local clock = t.clock(345600 + 3000 * 7 * DAY + 10 * 3600)
			local q = PeriodicQuests.new({
				periods = { daily = { length = DAY }, weekly = { length = 7 * DAY, offset = 345600 } },
				quests = {
					{ id = "d_bones", period = "daily", stat = "bones", goal = 100, reward = { currency = "Cash", amount = 1 } },
					{ id = "d_bones2", period = "daily", stat = "bones", goal = 150, reward = { currency = "Cash", amount = 2 } },
					{ id = "w_bones", period = "weekly", stat = "bones", goal = 500, reward = { currency = "Gems", amount = 5 } },
				},
				now = clock.now,
			})
			return q, clock, PeriodicQuests.newState()
		end
		it("counts a stat once per period even with several quests on it", function()
			local q, _, state = make()
			local done = q:progress(state, "bones", 120)
			expect(#done).toBe(1)
			expect(done[1]).toBe("d_bones")
			expect(q:status(state, "d_bones2").value).toBe(120)
			expect(q:status(state, "w_bones").value).toBe(120)
			expect(q:claim(state, "d_bones").amount).toBe(1)
			local _, again = q:claim(state, "d_bones")
			expect(again).toBe("claimed")
			local _, inc = q:claim(state, "w_bones")
			expect(inc).toBe("incomplete")
			local _, unknown = q:claim(state, { "x" })
			expect(unknown).toBe("unknown")
			expect(#q:progress(state, "bones", 0 / 0)).toBe(0)
		end)
		it("daily resets at UTC midnight, weekly on Monday", function()
			local q, clock, state = make()
			expect(q:secondsUntilReset("daily")).toBe(14 * 3600)
			expect(q:secondsUntilReset("weekly")).toBe(7 * DAY - 10 * 3600)
			q:progress(state, "bones", 120)
			clock.advance(14 * 3600) -- Tuesday 00:00
			expect(q:status(state, "d_bones").value).toBe(0)
			expect(q:status(state, "w_bones").value).toBe(120)
			q:progress(state, "bones", 400)
			expect(q:status(state, "w_bones").complete).toBe(true)
			clock.advance(6 * DAY) -- next Monday 00:00
			expect(q:status(state, "w_bones").value).toBe(0)
			expect(#q:list(state)).toBe(3)
		end)
	end)
end
