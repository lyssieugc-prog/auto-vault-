--[[
	Ragdoll Off a Mountain — client entry. Renders server state; never decides outcomes.
	Untestable outside Studio: verify with qa/playtest.md (built, untested until a Studio playtest).

	Real UI = ScreenGuis built from the Figma file (figma/ui-spec.md) and bound here by layer NAME:
	  HUD.Cash, HUD.Gems, HUD.LaunchButton, HUD.ChargeBar.Fill, HUD.LiftButton, HUD.Boosts,
	  RunSummary (Bones, Cash, Combo, NewBest), Announcement.Text
	If the HUD is missing (no Figma build imported yet) a clearly labelled DEV HUD is created so the
	loop can be playtested. It is NOT the final UI and must never ship.
]]

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Vault = ReplicatedStorage:WaitForChild("Vault")
local Format = require(Vault.Shared.Format)
local MobileUI = require(Vault.Client.MobileUI)
local UIAnim = require(Vault.Client.UIAnim)
local VFX = require(Vault.Client.VFX)
local Config = require(ReplicatedStorage:WaitForChild("GameShared"):WaitForChild("Config"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local player = Players.LocalPlayer
local gui = player:WaitForChild("PlayerGui")

local state = nil
local CHARGE_SECONDS = 1.2

-- DEV HUD fallback (playtest only) ------------------------------------------------------------------

local function devLabel(parent, name, text, pos, size)
	local label = Instance.new("TextLabel")
	label.Name = name
	label.Text = text
	label.Position = pos
	label.Size = size
	label.BackgroundColor3 = Color3.fromHex("#1E1B33")
	label.TextColor3 = Color3.new(1, 1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.Parent = parent
	return label
end

local function devButton(parent, name, text, pos, size, color)
	local button = Instance.new("TextButton")
	button.Name = name
	button.Text = text
	button.Position = pos
	button.Size = size
	button.BackgroundColor3 = Color3.fromHex(color or "#7ADE43")
	button.TextColor3 = Color3.new(1, 1, 1)
	button.Font = Enum.Font.FredokaOne
	button.TextScaled = true
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.3, 0)
	corner.Parent = button
	button.Parent = parent
	return button
end

local function buildDevHud(): ScreenGui
	warn("[Client] HUD ScreenGui not found — building DEV HUD (playtest only, not the Figma UI)")
	local screen = Instance.new("ScreenGui")
	screen.Name = "HUD"
	screen.ResetOnSpawn = false
	screen:SetAttribute("DevFallback", true)
	devLabel(screen, "DevBanner", "DEV HUD — replace with Figma UI", UDim2.fromScale(0.35, 0), UDim2.fromScale(0.3, 0.04))
	devLabel(screen, "Cash", "0", UDim2.fromScale(0.4, 0.05), UDim2.fromScale(0.2, 0.06))
	devLabel(screen, "Gems", "0", UDim2.fromScale(0.62, 0.05), UDim2.fromScale(0.1, 0.06))
	devButton(screen, "LaunchButton", "HOLD TO LAUNCH", UDim2.fromScale(0.4, 0.82), UDim2.fromScale(0.2, 0.1), "#FF8A1F")
	local bar = devLabel(screen, "ChargeBar", "", UDim2.fromScale(0.4, 0.78), UDim2.fromScale(0.2, 0.03))
	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = Color3.fromHex("#FFD93B")
	fill.Parent = bar
	devButton(screen, "LiftButton", "LIFT ⬆", UDim2.fromScale(0.02, 0.4), UDim2.fromScale(0.1, 0.07))
	devButton(screen, "BuyCannonButton", "CANNON", UDim2.fromScale(0.02, 0.48), UDim2.fromScale(0.1, 0.07))
	devButton(screen, "UnlockPeakButton", "PEAK", UDim2.fromScale(0.02, 0.56), UDim2.fromScale(0.1, 0.07))
	devButton(screen, "HatchButton", "EGG", UDim2.fromScale(0.02, 0.64), UDim2.fromScale(0.1, 0.07))
	devButton(screen, "DailyButton", "DAILY", UDim2.fromScale(0.02, 0.72), UDim2.fromScale(0.1, 0.07))
	devLabel(screen, "Boosts", "", UDim2.fromScale(0.75, 0.05), UDim2.fromScale(0.23, 0.05))
	screen.Parent = gui
	return screen
end

local hud = gui:WaitForChild("HUD", 5) or buildDevHud()
MobileUI.applySafeArea(hud)
MobileUI.scaleForDevice(hud)
for _, d in hud:GetDescendants() do
	if d:IsA("GuiButton") then
		UIAnim.bindButton(d)
		MobileUI.enforceTouchTarget(d)
	end
end

local function find(name: string): Instance?
	return hud:FindFirstChild(name, true)
end

local function setText(name: string, text: string)
	local label = find(name)
	if label and label:IsA("TextLabel") then
		label.Text = text
	end
end

-- State --------------------------------------------------------------------------------------------

local function renderBoosts()
	if not state then
		return
	end
	local parts = {}
	for _, boost in state.boosts do
		table.insert(parts, boost.label .. " " .. Format.countdown(boost.remaining))
	end
	setText("Boosts", table.concat(parts, "  "))
end

Remotes:WaitForChild("Currency").OnClientEvent:Connect(function(name, balance)
	setText(name, Format.abbreviate(balance))
end)

Remotes:WaitForChild("State").OnClientEvent:Connect(function(snapshot)
	state = snapshot
	for name, balance in snapshot.currency do
		setText(name, Format.abbreviate(balance))
	end
	renderBoosts()
	hud:SetAttribute("TutorialStep", snapshot.tutorial and snapshot.tutorial.id or "")
	hud:SetAttribute("TutorialText", snapshot.tutorial and snapshot.tutorial.text or "")
end)

-- Bone pops: "+$1.2K SNAP! Head" above the body part that broke ----------------------------------------

local PART_LABEL = {
	Head = "SKULL",
	UpperTorso = "RIBS",
	LowerTorso = "PELVIS",
	LeftUpperArm = "L ARM",
	RightUpperArm = "R ARM",
	LeftLowerArm = "L FOREARM",
	RightLowerArm = "R FOREARM",
	LeftHand = "L HAND",
	RightHand = "R HAND",
	LeftUpperLeg = "L FEMUR",
	RightUpperLeg = "R FEMUR",
	LeftLowerLeg = "L SHIN",
	RightLowerLeg = "R SHIN",
	LeftFoot = "L FOOT",
	RightFoot = "R FOOT",
}

local function bonePop(event)
	local character = player.Character
	local part = character and character:FindFirstChild(event.part)
	if not part then
		return
	end
	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromScale(6, 2.4)
	billboard.StudsOffset = Vector3.new(math.random() * 2 - 1, 2, 0)
	billboard.AlwaysOnTop = true
	billboard.Adornee = part
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = if event.critical then Color3.fromHex("#FF8A1F") else Color3.fromHex("#FFD93B")
	local combo = if event.combo > 1 then string.format("  x%.1f", event.combo) else ""
	label.Text = string.format(
		"+$%s %s%s\n%s! %s",
		Format.abbreviate(event.displayCash or event.cash),
		if event.critical then "CRITICAL" else "",
		combo,
		if event.broken > 1 then "SNAP x" .. event.broken else "SNAP",
		PART_LABEL[event.part] or event.part
	)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 3
	stroke.Color = Color3.fromHex("#1A1A1A")
	stroke.Parent = label
	label.Parent = billboard
	billboard.Parent = gui
	UIAnim.popOpen(label, 0.2)
	if event.critical then
		VFX.shake(0.25, 0.6)
	end
	task.delay(1.1, function()
		billboard:Destroy()
	end)
end

Remotes:WaitForChild("BonePop").OnClientEvent:Connect(bonePop)

Remotes:WaitForChild("RunSummary").OnClientEvent:Connect(function(summary)
	local panel = gui:FindFirstChild("RunSummary", true)
	if panel and panel:IsA("GuiObject") then
		local function set(name, text)
			local label = panel:FindFirstChild(name, true)
			if label and label:IsA("TextLabel") then
				label.Text = text
			end
		end
		set("Bones", string.format("%d / %d", summary.bones, summary.totalBones))
		set("Cash", "+$" .. Format.abbreviate(summary.earned))
		set("Combo", string.format("x%.1f", summary.bestCombo))
		set("NewBest", if summary.newBest then "NEW BEST!" else "")
		panel.Visible = true
		UIAnim.popOpen(panel)
		task.delay(3, function()
			UIAnim.close(panel)
		end)
	else
		UIAnim.numberPop(hud, string.format("%d/206 BONES  +$%s", summary.bones, Format.abbreviate(summary.earned)))
	end
	if summary.fullSkeleton then
		VFX.flash(hud, 0.2)
		VFX.bloomPulse(1.5, 1)
	end
end)

Remotes:WaitForChild("Announcement").OnClientEvent:Connect(function(text)
	local banner = gui:FindFirstChild("Announcement", true)
	local label = banner and banner:FindFirstChild("Text", true)
	if label and label:IsA("TextLabel") then
		label.Text = text
		banner.Visible = true
		UIAnim.popOpen(banner)
		task.delay(4, function()
			UIAnim.close(banner)
		end)
	else
		UIAnim.numberPop(hud, text, Color3.fromHex("#B678EA"))
	end
end)

Remotes:WaitForChild("Notify").OnClientEvent:Connect(function(text)
	UIAnim.numberPop(hud, text, Color3.fromHex("#A8F03C"))
end)

-- Launch: hold to charge, release to fire. Aim = camera direction (server clamps + validates) -------------

local charging = false
local chargeStart = 0

local function aim(): (number, number)
	local camera = Workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not camera or not root then
		return 20, 0
	end
	local look = camera.CFrame.LookVector
	local pitch = math.deg(math.asin(math.clamp(look.Y, -1, 1))) + 25
	local flatCam = Vector3.new(look.X, 0, look.Z)
	-- yaw is measured against the selected peak pad's facing (the server launches along it)
	local map = Workspace:FindFirstChild("Map")
	local markers = map and map:FindFirstChild("Markers")
	local pad = markers and state and markers:FindFirstChild("Peak" .. state.peak.selected .. "Pad")
	local forward = if pad and pad:IsA("BasePart") then pad.CFrame.LookVector else root.CFrame.LookVector
	local flatRoot = Vector3.new(forward.X, 0, forward.Z)
	local yaw = 0
	if flatCam.Magnitude > 0.01 and flatRoot.Magnitude > 0.01 then
		local a, b = flatRoot.Unit, flatCam.Unit
		yaw = math.deg(math.atan2(a:Cross(b).Y, a:Dot(b)))
	end
	local limits = Config.run.aim
	return math.clamp(pitch, limits.minPitch, limits.maxPitch), math.clamp(yaw, -limits.maxYaw, limits.maxYaw)
end

local function setCharge(value: number)
	local fill = find("Fill")
	if fill and fill:IsA("GuiObject") then
		fill.Size = UDim2.fromScale(value, 1)
	end
end

local function beginCharge()
	if charging or (state and state.running) then
		return
	end
	charging = true
	chargeStart = os.clock()
end

local function release()
	if not charging then
		return
	end
	charging = false
	local charge = math.clamp((os.clock() - chargeStart) / CHARGE_SECONDS, 0, 1)
	setCharge(0)
	local pitch, yaw = aim()
	local response = Remotes.Launch:InvokeServer(pitch, yaw, charge)
	if response and response.error == "not_on_pad" then
		UIAnim.numberPop(hud, "Ride the LIFT to your peak first!", Color3.fromHex("#E13A2A"))
	elseif response and response.ok then
		VFX.shake(0.3, 0.8)
	end
end

RunService.RenderStepped:Connect(function()
	if charging then
		setCharge(math.clamp((os.clock() - chargeStart) / CHARGE_SECONDS, 0, 1))
	end
end)

local launchButton = find("LaunchButton")
if launchButton and launchButton:IsA("GuiButton") then
	launchButton.MouseButton1Down:Connect(beginCharge)
	launchButton.MouseButton1Up:Connect(release)
end
ContextActionService:BindAction("RagdollLaunch", function(_, inputState)
	if inputState == Enum.UserInputState.Begin then
		beginCharge()
	elseif inputState == Enum.UserInputState.End then
		release()
	end
	return Enum.ContextActionResult.Sink
end, false, Enum.KeyCode.F, Enum.KeyCode.ButtonR2)

local function bindTap(name: string, callback: () -> ())
	local button = find(name)
	if button and button:IsA("GuiButton") then
		MobileUI.onTap(button, callback)
	end
end

bindTap("LiftButton", function()
	Remotes.Lift:InvokeServer(nil)
end)
bindTap("BuyCannonButton", function()
	Remotes.BuyCannon:InvokeServer()
end)
bindTap("UnlockPeakButton", function()
	Remotes.UnlockPeak:InvokeServer()
end)
bindTap("HatchButton", function()
	local response = Remotes.Hatch:InvokeServer("Trailhead")
	local result = response and response.result
	if result then
		UIAnim.numberPop(hud, string.format("%s %s!", result.rarity, Config.pets[result.id].name))
		Remotes.Equip:InvokeServer(result.uid)
	end
end)
bindTap("DailyButton", function()
	Remotes.ClaimDaily:InvokeServer()
end)

-- live boost countdowns
task.spawn(function()
	while true do
		task.wait(1)
		if state then
			for _, boost in state.boosts do
				boost.remaining = math.max(0, boost.remaining - 1)
			end
			renderBoosts()
		end
	end
end)
