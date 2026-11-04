local Currency = require("../../src/Shared/Currency")
local Tycoon = require("../../src/Shared/Tycoon")

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("Tycoon", function()
		local function make()
			local cash = Currency.new({ currencies = { Cash = { start = 1000 } } })
			cash:load(1)
			local ty = Tycoon.new({
				items = {
					{ id = "Floor1", cost = 0, currency = "Cash" },
					{ id = "Dropper1", cost = 100, currency = "Cash", requires = { "Floor1" }, income = 5 },
					{ id = "Dropper2", cost = 800, currency = "Cash", requires = { "Dropper1" }, income = 20 },
					{ id = "VIPRoom", cost = 0, currency = "Cash", requires = { "Floor1" }, gamepass = "VIP" },
				},
			})
			ty:load(1)
			return ty, cash
		end
		it("respects requirements and costs", function()
			local ty, cash = make()
			expect(table.concat(ty:available(1), ",")).toBe("Floor1")
			local ok, err = ty:buy(1, "Dropper1", cash)
			expect(ok).toBe(false)
			expect(err).toBe("locked")
			expect(ty:buy(1, "Floor1", cash)).toBe(true)
			expect(ty:buy(1, "Dropper1", cash)).toBe(true)
			expect(cash:get(1, "Cash")).toBe(900)
			local ok2, err2 = ty:buy(1, "Dropper2", cash)
			expect(ok2).toBe(false)
			expect(err2).toBe("funds")
			expect(ty:income(1)).toBe(5)
		end)
		it("gamepass gates", function()
			local ty, cash = make()
			ty:buy(1, "Floor1", cash)
			local _, err = ty:buy(1, "VIPRoom", cash)
			expect(err).toBe("gamepass")
			expect(ty:buy(1, "VIPRoom", cash, { VIP = true })).toBe(true)
		end)
		it("serializes, reloads, resets", function()
			local ty, cash = make()
			ty:buy(1, "Floor1", cash)
			ty:buy(1, "Dropper1", cash)
			local saved = ty:serialize(1)
			expect(table.concat(saved, ",")).toBe("Floor1,Dropper1")
			ty:load(2, { "Floor1", "Bogus" })
			expect(ty:owns(2, "Floor1")).toBe(true)
			expect(ty:owns(2, "Bogus")).toBe(false)
			ty:reset(1, { "Floor1" })
			local owned, total = ty:progress(1)
			expect(owned).toBe(1)
			expect(total).toBe(4)
		end)
		it("rejects bad config", function()
			expect(function()
				Tycoon.new({ items = { { id = "A", cost = 0, currency = "Cash", requires = { "Missing" } } } })
			end).toThrow()
		end)
	end)
end
