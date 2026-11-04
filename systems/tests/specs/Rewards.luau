local Rewards = require("../../src/Shared/Rewards")

local DAY = 86400

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Rewards", function()
		local function make()
			local clock = t.clock(DAY * 1000 + 100)
			local daily = {}
			for i = 1, 7 do
				daily[i] = { currency = "Cash", amount = i * 100 }
			end
			local r = Rewards.new({
				quests = { { id = "hatch3", stat = "hatched", goal = 3, reward = { currency = "Cash", amount = 50 } } },
				daily = daily,
				playtime = { { seconds = 60, reward = { currency = "Gems", amount = 1 } } },
				now = clock.now,
			})
			return r, clock, Rewards.newState()
		end
		it("quest progress, completion, single claim", function()
			local r, _, state = make()
			expect(#r:progress(state, "hatched", 2)).toBe(0)
			local _, err = r:claimQuest(state, "hatch3")
			expect(err).toBe("incomplete")
			local done = r:progress(state, "hatched", 5)
			expect(done[1]).toBe("hatch3")
			expect(r:claimQuest(state, "hatch3").amount).toBe(50)
			local _, again = r:claimQuest(state, "hatch3")
			expect(again).toBe("claimed")
			expect(r:questStatus(state, "hatch3").value).toBe(3)
		end)
		it("daily streak advances, blocks same day, resets on a missed day, loops after 7", function()
			local r, clock, state = make()
			local reward, day = r:claimDaily(state)
			expect(day).toBe(1)
			expect(reward.amount).toBe(100)
			local none, err = r:claimDaily(state)
			expect(none).toBeNil()
			expect(err).toBe("claimed_today")
			expect(r:dailyStatus(state).secondsUntilNext).toBe(DAY - 100)
			clock.advance(DAY)
			local _, day2 = r:claimDaily(state)
			expect(day2).toBe(2)
			clock.advance(DAY * 2) -- missed a day
			local _, reset = r:claimDaily(state)
			expect(reset).toBe(1)
			for _ = 2, 7 do
				clock.advance(DAY)
				r:claimDaily(state)
			end
			expect(state.daily.streak).toBe(7)
			clock.advance(DAY)
			local _, looped = r:claimDaily(state)
			expect(looped).toBe(1)
		end)
		it("playtime rewards", function()
			local r, _, state = make()
			local _, notReady = r:claimPlaytime(state, 1, 30)
			expect(notReady).toBe("not_ready")
			expect(r:playtimeStatus(state, 30)[1].remaining).toBe(30)
			expect(r:claimPlaytime(state, 1, 61).amount).toBe(1)
			local _, claimed = r:claimPlaytime(state, 1, 100)
			expect(claimed).toBe("claimed")
			Rewards.resetPlaytime(state)
			expect(r:playtimeStatus(state, 0)[1].claimed).toBe(false)
		end)
	end)
end
