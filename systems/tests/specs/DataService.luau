local DataService = require("../../src/Shared/DataService")

-- Mock with Roblox UpdateAsync semantics: transform returning nil cancels the write.
local function memoryStore()
	local store = { data = {}, failNext = 0, writes = 0 }
	function store:update(key, transform)
		if self.failNext > 0 then
			self.failNext -= 1
			error("DataStore throttled")
		end
		local current = self.data[key]
		local new = transform(if current then DataService.deepCopy(current) else nil)
		if new ~= nil then
			self.data[key] = DataService.deepCopy(new)
			self.writes += 1
		end
		return new, nil
	end
	return store
end

local TEMPLATE = { coins = 0, inventory = { items = {} }, settings = { music = true } }

return function(t)
	local describe, it, expect = t.describe, t.it, t.expect
	describe("DataService", function()
		it("creates from template, saves, reloads", function()
			local store = memoryStore()
			local ds = DataService.new({ store = store, template = TEMPLATE, sessionId = "A" })
			local p = ds:load(1)
			expect(p.coins).toBe(0)
			p.coins = 42
			expect(ds:release(1)).toBe(true)
			local p2 = ds:load(1)
			expect(p2.coins).toBe(42)
			expect(p2 == p).toBe(false)
		end)
		it("template edits do not leak between profiles", function()
			local ds = DataService.new({ store = memoryStore(), template = TEMPLATE })
			local a = ds:load(1)
			a.inventory.items.x = true
			local b = ds:load(2)
			expect(b.inventory.items.x).toBeNil()
			expect(TEMPLATE.inventory.items.x).toBeNil()
		end)
		it("session lock blocks a second server until released or expired", function()
			local clock = t.clock(1000)
			local store = memoryStore()
			local a = DataService.new({
				store = store,
				template = TEMPLATE,
				sessionId = "A",
				now = clock.now,
				lockTimeout = 100,
			})
			local b = DataService.new({
				store = store,
				template = TEMPLATE,
				sessionId = "B",
				now = clock.now,
				lockTimeout = 100,
			})
			a:load(1)
			local none, err = b:load(1)
			expect(none).toBeNil()
			expect(err).toBe("locked")
			a:release(1)
			expect(b:load(1)).toBeTruthy()
			-- crashed server: B never releases; A can take over after timeout
			clock.advance(101)
			expect(a:load(1)).toBeTruthy()
			-- B now lost the lock and must not overwrite A's data
			local ok, saveErr = b:save(1)
			expect(ok).toBe(false)
			expect(saveErr).toBe("lost_lock")
		end)
		it("reconciles new template keys and runs migrations", function()
			local store = memoryStore()
			store.data["u_1"] = { data = { coins = 5, version = 1, settings = {} } }
			local ds = DataService.new({
				store = store,
				template = TEMPLATE,
				version = 3,
				migrations = {
					[2] = function(p)
						p.coins *= 10
					end,
					[3] = function(p)
						p.migrated = true
					end,
				},
			})
			local p = ds:load(1)
			expect(p.coins).toBe(50)
			expect(p.migrated).toBe(true)
			expect(p.version).toBe(3)
			expect(p.settings.music).toBe(true)
			expect(type(p.inventory.items)).toBe("table")
		end)
		it("retries transient failures", function()
			local store = memoryStore()
			store.failNext = 2
			local waits = 0
			local ds = DataService.new({
				store = store,
				template = TEMPLATE,
				retries = 3,
				wait = function()
					waits += 1
				end,
			})
			expect(ds:load(1)).toBeTruthy()
			expect(waits).toBe(2)
			store.failNext = 5
			local ok = ds:save(1)
			expect(ok).toBe(false)
		end)
	end)
end
