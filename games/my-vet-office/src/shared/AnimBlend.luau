--[[
	AnimBlend — the math behind the animal animation framework. Pure, so every rule is tested
	under Lune; the client AnimalAnimator applies the results to AnimationTracks + Motor6Ds.

	Layers (bottom → top):
	  1. Locomotion blend space  idle / walk / trot / run / sprint weighted by speed, playback
	                             rate = speed / stride so paws stay planted (no foot sliding)
	  2. Pose layer              PoseGraph from→to cross-fade (eased alpha)
	  3. Gesture layer           one-shots (Scratch, Shake, Yawn …) faded in/out, masked
	  4. Additive procedural     breathing, panting, trembling, tail wag, ear pose, blink,
	                             head look (spring), limp offset
	  5. Foot IK                 two-bone IK on each leg to plant paws on uneven surfaces
	                             (exam table, scale, steps) — near LOD only

	Every weight moves toward its target with exponential smoothing (no instant snapping), and
	the head uses a critically damped spring so look-at never jerks.
]]

local AnimBlend = {}

local function clamp(x: number, lo: number, hi: number): number
	return if x < lo then lo elseif x > hi then hi else x
end

-- Exponential smoothing factor for a time constant (seconds) over dt. Frame-rate independent.
function AnimBlend.smoothing(dt: number, timeConstant: number): number
	if timeConstant <= 0 then
		return 1
	end
	return 1 - math.exp(-dt / timeConstant)
end

--------------------------------------------------------------------------------------------
-- 1. Locomotion blend space
--------------------------------------------------------------------------------------------
AnimBlend.GAITS = { "idle", "walk", "trot", "run", "sprint" }

-- Target weights for a ground speed given the breed's full-weight speed per gait.
-- Piecewise-linear between neighbouring gaits; weights always sum to 1.
function AnimBlend.locomotionWeights(speed: number, gaitSpeed): { [string]: number }
	local points = { { "idle", 0 } }
	for _, g in { "walk", "trot", "run", "sprint" } do
		table.insert(points, { g, gaitSpeed[g] })
	end
	local w = { idle = 0, walk = 0, trot = 0, run = 0, sprint = 0 }
	if speed <= 0 then
		w.idle = 1
		return w
	end
	for i = 1, #points - 1 do
		local a, b = points[i], points[i + 1]
		if speed <= b[2] then
			local t = (speed - a[2]) / math.max(b[2] - a[2], 1e-6)
			w[a[1]] = 1 - t
			w[b[1]] = t
			return w
		end
	end
	w.sprint = 1
	return w
end

-- Playback rate per gait so the cycle length matches distance travelled. A gait clip authored
-- with `cycleSeconds` covers stride[g] * rigScale studs per cycle at rate 1.
function AnimBlend.playbackRate(speed: number, stride: number, rigScale: number, cycleSeconds: number): number
	local strideStuds = stride * rigScale
	if strideStuds <= 0 then
		return 1
	end
	local cyclesPerSecond = speed / strideStuds
	return clamp(cyclesPerSecond * cycleSeconds, 0.25, 2.5)
end

-- Foot slide in studs/second: how far the planted paw moves relative to the ground. Zero when
-- playback matches speed. Used by tests and the debug overlay.
function AnimBlend.footSlide(
	speed: number,
	rate: number,
	stride: number,
	rigScale: number,
	cycleSeconds: number
): number
	local animSpeed = rate / cycleSeconds * stride * rigScale
	return math.abs(speed - animSpeed)
end

--------------------------------------------------------------------------------------------
-- Weight set with smoothing (used for locomotion, pose, gesture layers)
--------------------------------------------------------------------------------------------
function AnimBlend.newWeights(initial: { [string]: number }?)
	return { current = table.clone(initial or {}), target = table.clone(initial or {}) }
end

function AnimBlend.setTargets(ws, targets: { [string]: number })
	for k in ws.target do
		ws.target[k] = 0
	end
	for k, v in targets do
		ws.target[k] = v
		if ws.current[k] == nil then
			ws.current[k] = 0
		end
	end
end

function AnimBlend.stepWeights(ws, dt: number, fadeTime: number)
	local a = AnimBlend.smoothing(dt, fadeTime)
	local sum = 0
	for k, cur in ws.current do
		local nxt = cur + ((ws.target[k] or 0) - cur) * a
		if nxt < 1e-4 and (ws.target[k] or 0) == 0 then
			nxt = 0
		end
		ws.current[k] = nxt
		sum += nxt
	end
	-- keep the layer normalised so the rig never sinks / inflates mid-blend
	if sum > 0 then
		for k, v in ws.current do
			ws.current[k] = v / sum
		end
	end
	return ws.current
end

--------------------------------------------------------------------------------------------
-- 4. Additive procedural layer
--------------------------------------------------------------------------------------------
-- Critically damped spring (for head look, ear swivel, tail).
function AnimBlend.newSpring(value: number, halfLife: number)
	return { value = value, velocity = 0, halfLife = halfLife }
end

function AnimBlend.stepSpring(sp, target: number, dt: number): number
	local omega = 2 * 0.6931 / math.max(sp.halfLife, 1e-4) -- ln2 / halfLife * 2
	local x = sp.value - target
	local exp = math.exp(-omega * dt)
	local temp = (sp.velocity + omega * x) * dt
	sp.velocity = (sp.velocity - omega * temp) * exp
	sp.value = target + (x + temp) * exp
	return sp.value
end

-- Head look: world-space direction to target in the animal's chest frame → clamped yaw/pitch.
-- dir = { x (right), y (up), z (forward) }. Returns yaw, pitch (radians) and whether the
-- body should turn (target outside the comfortable neck range).
AnimBlend.LOOK_LIMITS = { yaw = math.rad(70), pitch = math.rad(35), turnBodyBeyond = math.rad(95) }

function AnimBlend.lookAngles(dir): (number, number, boolean)
	local yaw = math.atan2(dir.x, dir.z)
	local flat = math.sqrt(dir.x * dir.x + dir.z * dir.z)
	local pitch = math.atan2(dir.y, math.max(flat, 1e-6))
	local L = AnimBlend.LOOK_LIMITS
	local turnBody = math.abs(yaw) > L.turnBodyBeyond
	return clamp(yaw, -L.yaw, L.yaw), clamp(pitch, -L.pitch, L.pitch), turnBody
end

-- Breathing: returns chest scale offset and phase. bpm comes from species resting rate ×
-- mind breathRate. Panting adds a fast shallow component.
function AnimBlend.breath(t: number, bpm: number, pant: number): number
	local slow = math.sin(t * bpm / 60 * 2 * math.pi) * 0.025
	local fast = math.sin(t * 3.2 * 2 * math.pi) * 0.012 * pant
	return slow * (1 - pant * 0.6) + fast
end

-- Tail angle (radians) for a segment index; wag speed + amplitude from mind tailWag, height
-- from tailHeight. Each segment lags the previous one for a whip-like follow-through.
function AnimBlend.tailSegment(t: number, segment: number, wag: number, height: number)
	local freq = 0.6 + wag * 3.4 -- Hz: slow sweep → happy blur
	local amp = math.rad(5 + wag * 30)
	local lag = (segment - 1) * 0.35
	local yaw = math.sin((t * freq - lag * 0.25) * 2 * math.pi) * amp * (0.6 + segment * 0.15)
	local pitch = math.rad(-35 + height * 45) / 4 -- spread over 4 segments
	return yaw, pitch
end

-- Blink: returns lid closure 0..1 at time t for a blink schedule {next, duration}.
function AnimBlend.blink(state, t: number, interval: number, rng: () -> number): number
	if state.next == nil then
		state.next = t + interval * (0.5 + rng())
	end
	if t >= state.next then
		local phase = (t - state.next) / 0.16
		if phase >= 1 then
			state.next = t + interval * (0.6 + rng() * 0.8)
			return 0
		end
		return math.sin(phase * math.pi)
	end
	return 0
end

-- Tremble: small high-frequency body offset (studs). Deterministic in t.
function AnimBlend.tremble(t: number, amount: number): number
	return (math.sin(t * 61) * 0.5 + math.sin(t * 43 + 1.3) * 0.5) * 0.015 * amount
end

-- Limp: a favouring leg spends less of the cycle loaded and the body dips on the good leg.
-- Returns {stanceScale for the injured leg, bodyDip studs} at cycle phase 0..1.
function AnimBlend.limp(phase: number, amount: number)
	local stanceScale = 1 - amount * 0.55
	local dip = math.max(0, math.sin(phase * 2 * math.pi)) * 0.12 * amount
	return stanceScale, dip
end

--------------------------------------------------------------------------------------------
-- 5. Two-bone IK (upper + lower leg). Lengths a (upper) and b (lower); target distance d.
-- Returns the hip angle offset and knee bend (radians) in the leg plane, plus whether the
-- target was reachable (clamped otherwise).
--------------------------------------------------------------------------------------------
function AnimBlend.twoBoneIK(a: number, b: number, d: number): (number, number, boolean)
	local reachable = d <= a + b and d >= math.abs(a - b)
	d = clamp(d, math.abs(a - b) + 1e-4, a + b - 1e-4)
	local cosKnee = (a * a + b * b - d * d) / (2 * a * b)
	local knee = math.pi - math.acos(clamp(cosKnee, -1, 1)) -- 0 = straight
	local cosHip = (a * a + d * d - b * b) / (2 * a * d)
	local hip = math.acos(clamp(cosHip, -1, 1))
	return hip, knee, reachable
end

-- Paw height correction for ground under the paw (studs, positive = ground is higher).
-- Pelvis drops by the average of the lowest pair so no paw floats.
function AnimBlend.pelvisOffset(groundDeltas: { number }): number
	local sorted = table.clone(groundDeltas)
	table.sort(sorted)
	if #sorted == 0 then
		return 0
	end
	local low = sorted[1]
	local second = sorted[2] or low
	return math.min(0, (low + second) / 2)
end

--------------------------------------------------------------------------------------------
-- Distance LOD — keeps a busy clinic cheap. Returns the tier for a camera distance (studs)
-- and on-screen flag. Tiers: full (IK + every additive @60 Hz), mid (no IK, additive @30 Hz),
-- low (locomotion + pose only @10 Hz), off (frozen pose, no updates).
--------------------------------------------------------------------------------------------
AnimBlend.LOD = {
	{ name = "full", maxDist = 40, hz = 60, ik = true, additive = true, gestures = true },
	{ name = "mid", maxDist = 90, hz = 30, ik = false, additive = true, gestures = true },
	{ name = "low", maxDist = 180, hz = 10, ik = false, additive = false, gestures = false },
	{ name = "off", maxDist = math.huge, hz = 0, ik = false, additive = false, gestures = false },
}

function AnimBlend.lodFor(distance: number, onScreen: boolean, focused: boolean?)
	if focused then
		return AnimBlend.LOD[1] -- the patient being examined always gets full quality
	end
	for i, tier in AnimBlend.LOD do
		if distance <= tier.maxDist then
			if not onScreen and i < 3 then
				return AnimBlend.LOD[3]
			end
			return tier
		end
	end
	return AnimBlend.LOD[#AnimBlend.LOD]
end

-- Max animals at each tier given a budget (count of full-quality animals). Nearest first.
function AnimBlend.assignLods(distances: { number }, maxFull: number, maxMid: number)
	local order = {}
	for i = 1, #distances do
		order[i] = i
	end
	table.sort(order, function(x, y)
		return distances[x] < distances[y]
	end)
	local tiers = {}
	local full, mid = 0, 0
	for _, i in order do
		local tier = AnimBlend.lodFor(distances[i], true)
		if tier.name == "full" then
			if full < maxFull then
				full += 1
			else
				tier = AnimBlend.LOD[2]
			end
		end
		if tier.name == "mid" then
			if mid < maxMid then
				mid += 1
			else
				tier = AnimBlend.LOD[3]
			end
		end
		tiers[i] = tier.name
	end
	return tiers
end

return AnimBlend
