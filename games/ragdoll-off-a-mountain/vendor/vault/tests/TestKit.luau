-- Minimal test framework for Lune. Specs are functions(t) using t.describe / t.it / t.expect.

local TestKit = {}

local results = { passed = 0, failed = 0, failures = {} }
local suite = ""

local function fmt(v): string
	if type(v) == "string" then
		return string.format("%q", v)
	end
	return tostring(v)
end

local function deepEqual(a, b): boolean
	if a == b then
		return true
	end
	if type(a) ~= "table" or type(b) ~= "table" then
		return false
	end
	for k, v in a do
		if not deepEqual(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end

function TestKit.describe(name: string, fn: () -> ())
	local previous = suite
	suite = if previous == "" then name else previous .. " > " .. name
	fn()
	suite = previous
end

function TestKit.it(name: string, fn: () -> ())
	local ok, err = pcall(fn)
	if ok then
		results.passed += 1
	else
		results.failed += 1
		table.insert(results.failures, suite .. " > " .. name .. "\n    " .. tostring(err))
	end
end

function TestKit.expect(actual)
	local e = {}
	function e.toBe(expected)
		if actual ~= expected then
			error(string.format("expected %s, got %s", fmt(expected), fmt(actual)), 2)
		end
	end
	function e.toEqual(expected)
		if not deepEqual(actual, expected) then
			error("tables not deeply equal", 2)
		end
	end
	function e.toBeNear(expected: number, epsilon: number?)
		if type(actual) ~= "number" or math.abs(actual - expected) > (epsilon or 1e-6) then
			error(string.format("expected ~%s, got %s", fmt(expected), fmt(actual)), 2)
		end
	end
	function e.toBeTruthy()
		if not actual then
			error("expected truthy, got " .. fmt(actual), 2)
		end
	end
	function e.toBeFalsy()
		if actual then
			error("expected falsy, got " .. fmt(actual), 2)
		end
	end
	function e.toBeNil()
		if actual ~= nil then
			error("expected nil, got " .. fmt(actual), 2)
		end
	end
	function e.toBeGreaterThan(n: number)
		if not (actual > n) then
			error(string.format("expected > %s, got %s", fmt(n), fmt(actual)), 2)
		end
	end
	function e.toBeLessThan(n: number)
		if not (actual < n) then
			error(string.format("expected < %s, got %s", fmt(n), fmt(actual)), 2)
		end
	end
	function e.toThrow()
		local ok = pcall(actual)
		if ok then
			error("expected function to throw", 2)
		end
	end
	return e
end

-- Deterministic RNG for tests (Park–Miller; products stay below 2^53). Returns () -> [0, 1).
function TestKit.seededRng(seed: number)
	local state = math.max(1, seed % 2147483647)
	return function()
		state = (state * 48271) % 2147483647
		return (state - 1) / 2147483646
	end
end

-- Manual clock for time-based systems.
function TestKit.clock(start: number?)
	local c = { t = start or 0 }
	function c.now()
		return c.t
	end
	function c.advance(dt: number)
		c.t += dt
	end
	return c
end

function TestKit.results()
	return results
end

return TestKit
