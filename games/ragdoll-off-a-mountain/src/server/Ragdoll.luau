--[[
	Ragdoll — server-side ragdoll physics + impact measurement for Ragdoll Off a Mountain.
	Untestable outside Studio: verify with qa/playtest.md (built, untested until a Studio playtest).

	local Ragdoll = require(script.Parent.Ragdoll)
	local handle = Ragdoll.launch(character, params, {
		onImpact = function(partName, speed, t) end,   -- t = seconds since launch; feeds GameLogic:reportImpact
		onFinish = function(reason) end,               -- "rest" | "timeout" | "landed" | "removed"
		isLanded = function(position) return bool end, -- LandingZone check
		restSpeed = 3, restSeconds = 1.5,
	})
	handle:stop()

	Anti-exploit: the ragdoll's network owner is the SERVER for the whole run, so velocities and
	impacts are measured on the server and a client cannot report fake hits or teleport mid-run.
	Impact = sudden change of a body part's velocity beyond what gravity explains (studs/s).
]]

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Ragdoll = {}

local MIN_REPORT = 20 -- studs/s; smaller velocity changes are rolling/sliding noise

local function ragdollify(character: Model, elasticity: number)
	for _, motor in character:GetDescendants() do
		if motor:IsA("Motor6D") and motor.Part0 and motor.Part1 then
			local a0 = Instance.new("Attachment")
			a0.Name = "RagdollA0"
			a0.CFrame = motor.C0
			a0.Parent = motor.Part0
			local a1 = Instance.new("Attachment")
			a1.Name = "RagdollA1"
			a1.CFrame = motor.C1
			a1.Parent = motor.Part1
			local socket = Instance.new("BallSocketConstraint")
			socket.Name = "RagdollSocket"
			socket.Attachment0 = a0
			socket.Attachment1 = a1
			socket.LimitsEnabled = true
			socket.TwistLimitsEnabled = true
			socket.UpperAngle = 60
			socket.TwistLowerAngle = -45
			socket.TwistUpperAngle = 45
			socket.Parent = motor.Part0
			motor.Enabled = false
		end
	end
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") then
			part.CanCollide = part.Name ~= "HumanoidRootPart"
			part.CustomPhysicalProperties = PhysicalProperties.new(0.7, 0.4, elasticity, 1, 1)
		end
	end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.PlatformStand = true
		humanoid.AutoRotate = false
		humanoid:ChangeState(Enum.HumanoidStateType.Physics)
	end
end

local function setServerOwner(character: Model)
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") and not part.Anchored then
			pcall(function()
				part:SetNetworkOwner(nil)
			end)
		end
	end
end

function Ragdoll.launch(character: Model, params, opts)
	local root = character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then
		return nil
	end
	ragdollify(character, params.elasticity or 0.3)
	setServerOwner(character)

	-- Launch direction: the pad's facing (off the cliff) rotated by yaw, pitched up by pitch.
	local look = params.forward or root.CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 0.01 then flat.Unit else Vector3.new(0, 0, -1)
	local dir = CFrame.Angles(0, math.rad(params.yaw), 0):VectorToWorldSpace(flat)
	local pitch = math.rad(params.pitch)
	local velocity = (dir * math.cos(pitch) + Vector3.new(0, math.sin(pitch), 0)) * params.speed
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") then
			part.AssemblyLinearVelocity = velocity
		end
	end
	root.AssemblyAngularVelocity = Vector3.new(math.random() * 6 - 3, math.random() * 6 - 3, math.random() * 6 - 3)

	local parts = {}
	for _, part in character:GetChildren() do
		if part:IsA("BasePart") and part.Name ~= "HumanoidRootPart" then
			parts[part] = part.AssemblyLinearVelocity
		end
	end

	local started = os.clock()
	local restTime = 0
	local finished = false
	local handle = {}
	local connection

	local function finish(reason: string)
		if finished then
			return
		end
		finished = true
		if connection then
			connection:Disconnect()
		end
		opts.onFinish(reason)
	end

	connection = RunService.Heartbeat:Connect(function(dt)
		if not character.Parent or not root.Parent then
			finish("removed")
			return
		end
		local gravity = Vector3.new(0, -Workspace.Gravity * dt, 0)
		local now = os.clock()
		for part, previous in parts do
			if part.Parent then
				local current = part.AssemblyLinearVelocity
				local change = (current - (previous + gravity)).Magnitude
				if change >= MIN_REPORT then
					opts.onImpact(part.Name, change, now - started) -- seconds since launch
				end
				parts[part] = current
			end
		end
		local speed = root.AssemblyLinearVelocity.Magnitude
		restTime = if speed < (opts.restSpeed or 3) then restTime + dt else 0
		if restTime >= (opts.restSeconds or 1.5) then
			finish("rest")
		elseif opts.isLanded and opts.isLanded(root.Position) and speed < 20 then
			finish("landed")
		elseif now - started >= (params.maxSeconds or 25) then
			finish("timeout")
		end
	end)

	function handle:stop()
		finish("stopped")
	end

	return handle
end

return Ragdoll
