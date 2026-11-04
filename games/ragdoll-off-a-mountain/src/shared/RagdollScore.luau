--[[
	RagdollScore — the core rule of Ragdoll Off a Mountain: impacts break bones, bones pay Cash.
	Pure (no Roblox APIs) so tests/run.luau drives it under Lune. The SERVER measures impacts on a
	server-owned ragdoll (Ragdoll.server glue) and feeds them here; the client never reports hits.

	local score = RagdollScore.new(Config.scoring)
	local run = score:newRun({
		impactMultiplier = 1.6,     -- pets (capped) x Brittle Bones x Glass Bones pass
		cashMultiplier = 3.2,       -- pet Hit Power x Bone Value upgrade x event (NOT currency multipliers)
		peakMultiplier = 4,
		comboWindow = 1.35,
		critChance = 0.05,
		rng = math.random,
		startedAt = now,
	})
	local event = score:impact(run, "Head", 120, t)   -- nil when nothing broke
	local summary = score:finish(run)                 -- { bones, cash, fullSkeleton, bestCombo, ... }

	Rules (game.md §3.1):
	  effective = speed * impactMultiplier
	  breaks    = 1 + floor((effective - breakSpeed) / stepSpeed), capped by bones left in the part
	  severity  = clamp(effective / breakSpeed, 1, maxSeverity)  (x2 on a crit)
	  cash      = breaks * boneValue[part] * severity * combo * peakMultiplier * cashMultiplier
	  combo     = 1 + comboStep * chain (max comboMax); chain grows when breaks are <= comboWindow apart
	  all bones broken in one run -> run cash * fullSkeletonMultiplier
]]

local RagdollScore = {}
RagdollScore.__index = RagdollScore

local function finitePositive(n: any): boolean
	return type(n) == "number" and n == n and n > 0 and n < math.huge
end

function RagdollScore.new(config)
	assert(type(config) == "table" and type(config.parts) == "table", "RagdollScore.new: parts required")
	local self = setmetatable({}, RagdollScore)
	self.parts = {}
	self.partNames = {}
	self.totalBones = 0
	for name, part in config.parts do
		assert(type(part.bones) == "number" and part.bones >= 1, "RagdollScore.new: " .. name .. " needs bones")
		assert(type(part.value) == "number" and part.value > 0, "RagdollScore.new: " .. name .. " needs value")
		self.parts[name] = { bones = part.bones, value = part.value }
		table.insert(self.partNames, name)
		self.totalBones += part.bones
	end
	table.sort(self.partNames)
	self.breakSpeed = config.breakSpeed or 45
	self.stepSpeed = config.stepSpeed or 25
	self.maxSeverity = config.maxSeverity or 8
	self.critSeverity = config.critSeverity or 4
	self.comboStep = config.comboStep or 0.1
	self.comboMax = config.comboMax or 3
	self.comboWindow = config.comboWindow or 1.2
	self.maxSpeed = config.maxSpeed or 2000 -- physics glitches above this are clamped
	self.partCooldown = config.partCooldown or 0.12 -- one impact per part per cooldown (contact jitter)
	self.fullSkeletonMultiplier = config.fullSkeletonMultiplier or 2
	return self
end

function RagdollScore:isPart(name: any): boolean
	return type(name) == "string" and self.parts[name] ~= nil
end

function RagdollScore:newRun(opts)
	opts = opts or {}
	local left = {}
	for name, part in self.parts do
		left[name] = part.bones
	end
	return {
		impactMultiplier = if finitePositive(opts.impactMultiplier) then opts.impactMultiplier else 1,
		cashMultiplier = if finitePositive(opts.cashMultiplier) then opts.cashMultiplier else 1,
		peakMultiplier = if finitePositive(opts.peakMultiplier) then opts.peakMultiplier else 1,
		comboWindow = if finitePositive(opts.comboWindow) then opts.comboWindow else self.comboWindow,
		critChance = math.clamp(tonumber(opts.critChance) or 0, 0, 1),
		rng = opts.rng or math.random,
		startedAt = opts.startedAt or 0,
		left = left,
		lastHit = {},
		bones = 0,
		cash = 0,
		chain = 0,
		lastBreakAt = nil,
		bestCombo = 1,
		impacts = 0,
		crits = 0,
		broken = {},
		finished = false,
	}
end

-- Returns an event table when bones broke, else nil. `t` = server time in seconds.
function RagdollScore:impact(run, partName: any, speed: any, t: any)
	if run.finished or not self:isPart(partName) then
		return nil
	end
	if type(speed) ~= "number" or speed ~= speed or speed <= 0 or type(t) ~= "number" or t ~= t then
		return nil
	end
	local last = run.lastHit[partName]
	if last and t - last < self.partCooldown then
		return nil
	end
	run.lastHit[partName] = t
	run.impacts += 1
	local effective = math.min(speed, self.maxSpeed) * run.impactMultiplier
	if effective < self.breakSpeed or run.left[partName] <= 0 then
		return nil
	end
	local wanted = 1 + math.floor((effective - self.breakSpeed) / self.stepSpeed)
	local broken = math.min(wanted, run.left[partName])
	run.left[partName] -= broken
	run.bones += broken
	run.broken[partName] = (run.broken[partName] or 0) + broken

	if run.lastBreakAt and t - run.lastBreakAt <= run.comboWindow then
		run.chain += 1
	else
		run.chain = 0
	end
	run.lastBreakAt = t
	local combo = math.min(1 + self.comboStep * run.chain, self.comboMax)
	run.bestCombo = math.max(run.bestCombo, combo)

	local severity = math.clamp(effective / self.breakSpeed, 1, self.maxSeverity)
	local crit = run.critChance > 0 and run.rng() < run.critChance
	if crit then
		severity *= 2
		run.crits += 1
	end
	local cash = broken
		* self.parts[partName].value
		* severity
		* combo
		* run.peakMultiplier
		* run.cashMultiplier
	run.cash += cash
	return {
		part = partName,
		broken = broken,
		bonesLeft = run.left[partName],
		totalBones = run.bones,
		severity = severity,
		critical = crit or severity >= self.critSeverity,
		combo = combo,
		cash = cash,
		t = t - run.startedAt,
	}
end

function RagdollScore:finish(run)
	if run.finished then
		return run.summary
	end
	run.finished = true
	local full = run.bones >= self.totalBones
	local cash = run.cash
	if full then
		cash *= self.fullSkeletonMultiplier
	end
	local partsHit = {}
	for name, count in run.broken do
		partsHit[name] = count
	end
	run.summary = {
		bones = run.bones,
		totalBones = self.totalBones,
		cash = math.floor(cash),
		fullSkeleton = full,
		bestCombo = run.bestCombo,
		impacts = run.impacts,
		crits = run.crits,
		partsHit = partsHit,
	}
	return run.summary
end

return RagdollScore
