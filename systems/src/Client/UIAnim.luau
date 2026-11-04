--[[
	UIAnim — house-style "nothing static" UI motion. Roblox client only.

	UIAnim.popOpen(frame)              -- Back overshoot from center, optional sunburst spin
	UIAnim.close(frame)                -- shrink + fade, then Visible = false
	UIAnim.stagger(container, 0.05)    -- children pop in one after another
	UIAnim.bindButton(button)          -- hover 1.05 + tilt, press squash 0.95
	UIAnim.pulse(guiObject)            -- claimable glow/bob loop; returns stop()
	UIAnim.spinForever(image, 20)      -- sunburst idle rotation; returns stop()
	UIAnim.countdown(label, endsAt)    -- live "MM:SS" text; returns stop()
	UIAnim.numberPop(parent, "+1.2K", color) -- floating rising number

	All motion uses UIScale (added on demand) so layouts keep scale-only sizing.
]]

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Format = require(script.Parent.Parent.Shared.Format)

local UIAnim = {}

local function uiScale(gui: GuiObject): UIScale
	local scale = gui:FindFirstChildOfClass("UIScale")
	if not scale then
		scale = Instance.new("UIScale")
		scale.Parent = gui
	end
	return scale
end

local function tween(instance: Instance, time: number, style: Enum.EasingStyle, dir: Enum.EasingDirection, goal)
	local t = TweenService:Create(instance, TweenInfo.new(time, style, dir), goal)
	t:Play()
	return t
end

function UIAnim.popOpen(frame: GuiObject, duration: number?)
	local scale = uiScale(frame)
	scale.Scale = 0.2
	frame.Visible = true
	tween(scale, duration or 0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out, { Scale = 1 })
	local burst = frame:FindFirstChild("Sunburst")
	if burst and burst:IsA("GuiObject") then
		UIAnim.spinForever(burst, 25)
	end
end

function UIAnim.close(frame: GuiObject, duration: number?)
	local scale = uiScale(frame)
	local t = tween(scale, duration or 0.18, Enum.EasingStyle.Back, Enum.EasingDirection.In, { Scale = 0 })
	t.Completed:Once(function()
		frame.Visible = false
		scale.Scale = 1
	end)
end

function UIAnim.stagger(container: Instance, delayEach: number?)
	local gap = delayEach or 0.05
	local i = 0
	for _, child in container:GetChildren() do
		if child:IsA("GuiObject") and child.Visible then
			local scale = uiScale(child)
			scale.Scale = 0
			task.delay(i * gap, function()
				tween(scale, 0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out, { Scale = 1 })
			end)
			i += 1
		end
	end
end

function UIAnim.bindButton(button: GuiButton)
	local scale = uiScale(button)
	local baseRotation = button.Rotation
	button.MouseEnter:Connect(function()
		tween(scale, 0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Scale = 1.05 })
		tween(button, 0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Rotation = baseRotation - 2 })
	end)
	button.MouseLeave:Connect(function()
		tween(scale, 0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Scale = 1 })
		tween(button, 0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Rotation = baseRotation })
	end)
	button.MouseButton1Down:Connect(function()
		tween(scale, 0.06, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Scale = 0.95 })
	end)
	button.MouseButton1Up:Connect(function()
		tween(scale, 0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out, { Scale = 1 })
	end)
end

function UIAnim.pulse(gui: GuiObject, amount: number?): () -> ()
	local scale = uiScale(gui)
	local info = TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)
	local t = TweenService:Create(scale, info, { Scale = 1 + (amount or 0.08) })
	t:Play()
	return function()
		t:Cancel()
		scale.Scale = 1
	end
end

function UIAnim.spinForever(gui: GuiObject, secondsPerTurn: number?): () -> ()
	local speed = 360 / (secondsPerTurn or 20)
	local conn = RunService.RenderStepped:Connect(function(dt)
		gui.Rotation = (gui.Rotation + speed * dt) % 360
	end)
	return function()
		conn:Disconnect()
	end
end

function UIAnim.countdown(label: TextLabel, endsAt: number, onDone: (() -> ())?): () -> ()
	local running = true
	task.spawn(function()
		while running do
			local remaining = endsAt - os.time()
			label.Text = Format.countdown(remaining)
			if remaining <= 0 then
				running = false
				if onDone then
					onDone()
				end
				break
			end
			task.wait(1)
		end
	end)
	return function()
		running = false
	end
end

function UIAnim.numberPop(parent: GuiObject, text: string, color: Color3?)
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5 + (math.random() - 0.5) * 0.3, 0.5)
	label.Size = UDim2.fromScale(0.3, 0.1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.Text = text
	label.TextColor3 = color or Color3.fromRGB(255, 217, 59)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 3
	stroke.Color = Color3.fromRGB(26, 26, 26)
	stroke.Parent = label
	label.Parent = parent
	local scale = uiScale(label)
	scale.Scale = 0.3
	tween(scale, 0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out, { Scale = 1 })
	local rise = tween(label, 0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, {
		Position = label.Position - UDim2.fromScale(0, 0.15),
		TextTransparency = 1,
	})
	tween(stroke, 0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, { Transparency = 1 })
	rise.Completed:Once(function()
		label:Destroy()
	end)
end

return UIAnim
