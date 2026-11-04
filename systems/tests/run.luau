-- Test runner: `lune run systems/tests/run` (from repo root). Exits 1 on any failure.

local process = require("@lune/process")
local TestKit = require("./TestKit")

local SPECS = {
	require("./specs/Format"),
	require("./specs/Rarity"),
	require("./specs/Currency"),
	require("./specs/Inventory"),
	require("./specs/Plots"),
	require("./specs/Stealing"),
	require("./specs/Tycoon"),
	require("./specs/Upgrades"),
	require("./specs/Rebirth"),
	require("./specs/Trading"),
	require("./specs/Rewards"),
	require("./specs/Tutorial"),
	require("./specs/Guard"),
	require("./specs/DataService"),
	require("./specs/Monetization"),
	require("./specs/Boosts"),
	require("./specs/SeasonPass"),
	require("./specs/PeriodicQuests"),
	require("./specs/Codes"),
	require("./specs/Integration"),
}

for _, spec in SPECS do
	spec(TestKit)
end

local results = TestKit.results()
for _, failure in results.failures do
	print("FAIL " .. failure)
end
print(string.format("\n%d passed, %d failed", results.passed, results.failed))
if results.failed > 0 then
	process.exit(1)
end
