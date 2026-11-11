--[[
	Interaction — physical exam/treatment input on PC (mouse) and mobile (touch), plus
	contextual cameras. Turns pointer gestures on the animal into Procedure remote calls:

	  open/take   click the highlighted cabinet / tool in the world
	  place       press and HOLD the instrument on the body (stethoscope, thermometer, syringe)
	  scan        magnified lens view (otoscope / coat check): drag to pan, dwell to notice
	  stroke      drag across the area to clean / massage
	  wrap        circle around the paw to wind the bandage
	  pull        slow upward drag (tick removal)
	  dose        slider in the ExamOverlay
	  record      Record button
	approach / pose / wait steps are auto-polled with "tick".

	The client only sends pointer samples in normalised body coordinates; every rule (right
	spot, hold time, coverage, speed, pull-aways) is decided by the server.
	BUILT, UNTESTED in Studio.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local GameShared = ReplicatedStorage:WaitForChild("GameShared")
local AnimBlend = require(GameShared:WaitForChild("AnimBlend"))
local Procedures = require(GameShared:WaitForChild("Procedures"))
local Cases = require(GameShared:WaitForChild("Cases"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local player = Players.LocalPlayer

local Interaction = {}
Interaction.active = nil -- { apptId, kind = "exam"|"treatment", id, procedure, step, steps }
Interaction.onChanged = nil -- callback(state) for the UI layer

---------------------------------------------------------------------------------------------
-- Camera director: smooth, never spins (angular speed clamped), always restores.
---------------------------------------------------------------------------------------------
local Camera = { mode = nil, target = nil }

local MAX_TURN = math.rad(240) -- deg/s cap so transitions can't whip around

function Camera.set(mode: string?, focus: () -> CFrame?)
	local cam = Workspace.CurrentCamera
	if mode == nil then
		Camera.mode = nil
		Camera.focus = nil
		cam.CameraType = Enum.CameraType.Custom
		return
	end
	Camera.mode = mode
	Camera.focus = focus
	cam.CameraType = Enum.CameraType.Scriptable
end

RunService:BindToRenderStep("VetCamera", Enum.RenderPriority.Camera.Value + 1, function(dt)
	if not Camera.mode or not Camera.focus then
		return
	end
	local goal = Camera.focus()
	if not goal then
		return
	end
	local cam = Workspace.CurrentCamera
	local cur = cam.CFrame
	local a = AnimBlend.smoothing(dt, 0.22)
	local nextPos = cur.Position:Lerp(goal.Position, a)
	local curLook, goalLook = cur.LookVector, goal.LookVector
	local angle = math.acos(math.clamp(curLook:Dot(goalLook), -1, 1))
	local maxStep = MAX_TURN * dt
	local t = if angle > 1e-4 then math.min(1, a, maxStep / angle) else 1
	local look = curLook:Lerp(goalLook, t).Unit
	cam.CFrame = CFrame.lookAt(nextPos, nextPos + look)
end)

local function animalModel(apptId: number): Model?
	for _, m in game:GetService("CollectionService"):GetTagged("Animal") do
		if m:GetAttribute("ApptId") == apptId then
			return m
		end
	end
	return nil
end

-- Contextual camera presets around the patient.
local function presetFor(apptId: number, kind: string)
	return function()
		local animal = animalModel(apptId)
		local char = player.Character
		local head = char and char:FindFirstChild("Head")
		if not animal or not animal.PrimaryPart then
			return nil
		end
		local body = animal.PrimaryPart.CFrame
		if kind == "Ear" then
			local ear = animal:FindFirstChild("EarL", true)
			local p = if ear and ear:IsA("BasePart") then ear.Position else body.Position + Vector3.new(0, 1.5, 0)
			return CFrame.lookAt(p + body.RightVector * -2.2 + Vector3.new(0, 0.4, 0), p)
		elseif kind == "Paw" then
			local paw = animal:FindFirstChild("PawFL", true)
			local p = if paw and paw:IsA("BasePart") then paw.Position else body.Position
			return CFrame.lookAt(p + body.LookVector * 2.5 + Vector3.new(0, 1.6, 0), p)
		end
		-- over-the-shoulder treatment camera
		local from = if head then head.Position + Vector3.new(0, 0.8, 0) else body.Position + Vector3.new(0, 5, 6)
		local back = (from - body.Position).Unit
		return CFrame.lookAt(body.Position + back * 6 + Vector3.new(0, 2.5, 0), body.Position + Vector3.new(0, 0.6, 0))
	end
end

Interaction.Camera = Camera

---------------------------------------------------------------------------------------------
-- Pointer → normalised body coordinates (u: tail 0 → nose 1, v: paws 0 → back 1, side L/R).
---------------------------------------------------------------------------------------------
local function pointerRay(): Ray
	local pos = UserInputService:GetMouseLocation()
	return Workspace.CurrentCamera:ViewportPointToRay(pos.X, pos.Y)
end

function Interaction.bodyPoint(apptId: number)
	local animal = animalModel(apptId)
	if not animal or not animal.PrimaryPart then
		return nil
	end
	local ray = pointerRay()
	local params = RaycastParams.new()
	params.FilterDescendantsInstances = { animal }
	params.FilterType = Enum.RaycastFilterType.Include
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 60, params)
	if not hit then
		return nil
	end
	local size = animal:GetAttribute("RestSize")
	if not size then
		local _, s = animal:GetBoundingBox()
		size = s
		animal:SetAttribute("RestSize", s)
	end
	local loc = animal.PrimaryPart.CFrame:PointToObjectSpace(hit.Position)
	local u = (-loc.Z + size.Z / 2) / size.Z -- model faces -Z (LookVector)
	local v = (loc.Y + size.Y / 2) / size.Y
	local side = nil
	if math.abs(loc.X) > size.X * 0.15 then
		side = if loc.X < 0 then "L" else "R"
	end
	return { u = u, v = v, side = side }, hit.Position
end

---------------------------------------------------------------------------------------------
-- Procedure driving
---------------------------------------------------------------------------------------------
local function send(action: string, payload)
	local a = Interaction.active
	if a then
		Remotes.Procedure:FireServer(a.apptId, action, payload)
	end
end

function Interaction.begin(apptId: number, kind: string, id: string)
	local procId = if kind == "exam" then Cases.exams[id].procedure else Cases.treatments[id].procedure
	Interaction.active = {
		apptId = apptId,
		kind = kind,
		id = id,
		procedure = procId,
		steps = Procedures.describe(procId),
		step = 1,
		progress = 0,
		side = "L",
		strokeBuf = {},
		lastSend = 0,
		message = nil,
		readings = {},
	}
	if kind == "exam" then
		Remotes.BeginExam:FireServer(apptId, id)
	else
		Remotes.BeginTreatment:FireServer(apptId, id)
	end
	Camera.set("Exam", presetFor(apptId, "Body"))
	if Interaction.onChanged then
		Interaction.onChanged(Interaction.active)
	end
end

function Interaction.cancel()
	local a = Interaction.active
	if a then
		Remotes.CancelProcedure:FireServer(a.apptId)
	end
	Interaction.active = nil
	Camera.set(nil)
	if Interaction.onChanged then
		Interaction.onChanged(nil)
	end
end

function Interaction.currentKind(): string?
	local a = Interaction.active
	return a and a.steps[a.step] and a.steps[a.step].kind
end

-- Results from the server move the UI along.
Remotes:WaitForChild("ProcedureResult").OnClientEvent:Connect(function(apptId, r)
	local a = Interaction.active
	if not a or a.apptId ~= apptId or type(r) ~= "table" then
		return
	end
	if r.ok == false and r.step == nil and r.message and not r.event then
		-- begin refused
		Interaction.active = nil
		Camera.set(nil)
	end
	if r.nextStep then
		a.step = r.nextStep -- server is the source of truth for which step we're on
	end
	a.progress = r.progress or a.progress
	a.message = r.message
	a.lastEvent = r.event
	if r.reading then
		table.insert(a.readings, r.reading)
	end
	if r.discovered then
		a.found = a.found or {}
		table.insert(a.found, r.discovered)
	end
	-- camera follows the step
	local kind = Interaction.currentKind()
	if kind == "scan" and a.procedure == "Otoscope" then
		Camera.set("Ear", presetFor(a.apptId, "Ear"))
	elseif kind == "wrap" or (kind == "stroke" and a.procedure == "CleanWound") then
		Camera.set("Paw", presetFor(a.apptId, "Paw"))
	elseif kind then
		Camera.set("Exam", presetFor(a.apptId, "Body"))
	end
	if r.done then
		a.summary = r.summary
		task.delay(1.5, function()
			if Interaction.active == a then
				Interaction.active = nil
				Camera.set(nil)
				if Interaction.onChanged then
					Interaction.onChanged(nil)
				end
			end
		end)
	end
	if Interaction.onChanged then
		Interaction.onChanged(a)
	end
end)

-- World clicks for open/take (cabinets, tools)
local function clickedTarget(): string?
	local ray = pointerRay()
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 40)
	local inst = hit and hit.Instance
	while inst and inst ~= Workspace do
		local target = inst:GetAttribute("Target") or inst:GetAttribute("Tool")
		if target then
			return target
		end
		inst = inst.Parent
	end
	return nil
end

local pressing = false
local wrapCenter, wrapAngle, pullLastY = nil, nil, nil

UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	if input.UserInputType ~= Enum.UserInputType.MouseButton1 and input.UserInputType ~= Enum.UserInputType.Touch then
		return
	end
	local a = Interaction.active
	if not a then
		return
	end
	local step = a.steps[a.step]
	if not step then
		return
	end
	pressing = true
	if step.kind == "open" then
		local t = clickedTarget()
		if t then
			send("open", { target = t })
		end
	elseif step.kind == "take" then
		-- tools sit inside the opened cabinet / on the tray; clicking the tool or its home works
		send("take", { tool = clickedTarget() or step.tool })
	elseif step.kind == "wrap" then
		local animal = animalModel(a.apptId)
		local paw = animal and animal:FindFirstChild("PawFL", true)
		if paw and paw:IsA("BasePart") then
			local sp = Workspace.CurrentCamera:WorldToViewportPoint(paw.Position)
			wrapCenter = Vector2.new(sp.X, sp.Y)
			local m = UserInputService:GetMouseLocation()
			wrapAngle = math.atan2(m.Y - wrapCenter.Y, m.X - wrapCenter.X)
		end
	elseif step.kind == "pull" then
		pullLastY = UserInputService:GetMouseLocation().Y
	end
end)

UserInputService.InputEnded:Connect(function(input)
	if input.UserInputType ~= Enum.UserInputType.MouseButton1 and input.UserInputType ~= Enum.UserInputType.Touch then
		return
	end
	pressing = false
	local a = Interaction.active
	if a and a.steps[a.step] and a.steps[a.step].kind == "place" then
		send("release", nil)
	end
	wrapCenter, pullLastY = nil, nil
end)

-- Continuous gestures at fixed send rates
local acc = 0
RunService.RenderStepped:Connect(function(dt)
	local a = Interaction.active
	if not a then
		return
	end
	local step = a.steps[a.step]
	if not step then
		return
	end
	acc += dt
	local kind = step.kind
	if kind == "stroke" and pressing then
		local p = Interaction.bodyPoint(a.apptId)
		if p then
			table.insert(a.strokeBuf, { u = p.u, v = p.v, side = p.side })
		end
	end
	if acc < 0.15 then
		return
	end
	local window = acc
	acc = 0
	if kind == "approach" or kind == "wait" or kind == "pose" then
		send(if kind == "pose" then "requestPose" else "tick", nil)
	elseif kind == "place" and pressing then
		local p = Interaction.bodyPoint(a.apptId)
		if p then
			send("place", p)
		end
	elseif kind == "scan" then
		-- the Magnifier lens maps pointer position inside the lens to 0..1
		local lens = a.lensPoint
		if lens then
			send("scan", { u = lens.X, v = lens.Y, side = a.side })
		end
	elseif kind == "stroke" and #a.strokeBuf > 0 then
		local batch = {}
		for i = 1, math.min(#a.strokeBuf, 32) do
			batch[i] = a.strokeBuf[i]
		end
		a.strokeBuf = {}
		send("stroke", { points = batch })
	elseif kind == "wrap" and pressing and wrapCenter then
		local m = UserInputService:GetMouseLocation()
		local ang = math.atan2(m.Y - wrapCenter.Y, m.X - wrapCenter.X)
		local delta = ang - wrapAngle
		if delta < -math.pi then
			delta += 2 * math.pi
		elseif delta > math.pi then
			delta -= 2 * math.pi
		end
		wrapAngle = ang
		if delta > 0 then
			send("wrap", { delta = delta })
		end
	elseif kind == "pull" and pressing and pullLastY then
		local y = UserInputService:GetMouseLocation().Y
		local dist = math.max(0, (pullLastY - y) / 120)
		pullLastY = y
		send("pull", { distance = dist, dt = window })
	end
end)

-- UI hooks (ExamOverlay buttons call these)
function Interaction.setDose(value: number)
	send("dose", { value = value })
end

function Interaction.record()
	send("record", nil)
end

function Interaction.finishScan()
	send("finishScan", nil)
end

function Interaction.setLensPoint(v2: Vector2?)
	if Interaction.active then
		Interaction.active.lensPoint = v2
	end
end

function Interaction.setSide(side: string)
	if Interaction.active then
		Interaction.active.side = side
	end
end

function Interaction.doseTarget()
	-- shown on the bottle label (weight-based for medicine) — the player still sets it
	local a = Interaction.active
	if not a then
		return nil
	end
	local step = Procedures.defs[a.procedure].steps[a.step]
	if not step or step.kind ~= "dose" then
		return nil
	end
	return step
end

return Interaction
