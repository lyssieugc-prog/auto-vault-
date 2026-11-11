--[[
	VFX — camera shake, screen flash, particle bursts, rarity reveal ladder, animation playback.
	Roblox client only.

	VFX.shake(0.4, 1.2)                         -- duration, intensity (studs)
	VFX.flash(screenGui, 0.08)                  -- 1–3 frame white flash
	VFX.burst(part, 30)                         -- :Emit on every ParticleEmitter under part
	VFX.revealLadder(label, tiers, finalIndex, onStep) -- climbs rarity colors ~1s per step
	VFX.playAnimation(humanoidOrController, animationId, { [markerName] = fn })
]]

local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local VFX = {}

function VFX.shake(duration: number, intensity: number?)
	local camera = workspace.CurrentCamera
	local strength = intensity or 1
	local elapsed = 0
	local conn
	conn = RunService.RenderStepped:Connect(function(dt)
		elapsed += dt
		if elapsed >= duration then
			conn:Disconnect()
			return
		end
		local falloff = 1 - elapsed / duration
		local offset = Vector3.new(math.random() - 0.5, math.random() - 0.5, 0) * strength * falloff
		camera.CFrame *= CFrame.new(offset)
	end)
end

function VFX.flash(screenGui: ScreenGui, holdTime: number?)
	local frame = Instance.new("Frame")
	frame.Size = UDim2.fromScale(1, 1)
	frame.BackgroundColor3 = Color3.new(1, 1, 1)
	frame.BorderSizePixel = 0
	frame.ZIndex = 1000
	frame.Parent = screenGui
	task.delay(holdTime or 0.05, function()
		local t = TweenService:Create(frame, TweenInfo.new(0.25), { BackgroundTransparency = 1 })
		t:Play()
		t.Completed:Once(function()
			frame:Destroy()
		end)
	end)
end

function VFX.burst(root: Instance, count: number?)
	for _, d in root:GetDescendants() do
		if d:IsA("ParticleEmitter") then
			d:Emit(count or 20)
		end
	end
end

-- Bloom pulse for big reveals.
function VFX.bloomPulse(peak: number?, duration: number?)
	local bloom = Lighting:FindFirstChildOfClass("BloomEffect")
	if not bloom then
		return
	end
	local base = bloom.Intensity
	local up = TweenService:Create(bloom, TweenInfo.new((duration or 0.6) / 2), { Intensity = peak or 2 })
	up:Play()
	up.Completed:Once(function()
		TweenService:Create(bloom, TweenInfo.new((duration or 0.6) / 2), { Intensity = base }):Play()
	end)
end

-- tiers = { { name = "Common", color = Color3 }, ... }; climbs to finalIndex, ~stepTime each.
function VFX.revealLadder(label: TextLabel, tiers, finalIndex: number, onStep, stepTime: number?)
	for i = 1, finalIndex do
		local tier = tiers[i]
		label.Text = string.upper(tier.name)
		label.TextColor3 = tier.color
		if onStep then
			onStep(i, tier)
		end
		if i < finalIndex then
			task.wait(stepTime or 0.9)
		end
	end
end

-- Plays an animation and binds KeyframeMarker callbacks (sync VFX to animation beats).
function VFX.playAnimation(target: Instance, animationId: string, markers: { [string]: () -> () }?)
	local animator = target:FindFirstChildOfClass("Animator")
	if not animator then
		animator = Instance.new("Animator")
		animator.Parent = target
	end
	local animation = Instance.new("Animation")
	animation.AnimationId = animationId
	local track = (animator :: Animator):LoadAnimation(animation)
	for marker, callback in markers or {} do
		track:GetMarkerReachedSignal(marker):Connect(callback)
	end
	track:Play()
	return track
end

return VFX
