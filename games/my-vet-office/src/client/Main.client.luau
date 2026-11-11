--[[
	My Vet Office — client entry.
	  • Binds server State to the Figma-built ScreenGuis BY NAME (games/my-vet-office/figma/ui-spec.md):
	    HUD, VetComputer, ExamOverlay, Magnifier, Invoice, BuildMode, Dialogue.
	  • Starts the single AnimalAnimator loop and the Interaction (exam input + cameras) layer.
	  • Animates interactables (cabinet doors / drawers / fridge) from the server "Open" attribute,
	    shows held tools, plays animal sounds from replicated "Vocal" attributes.
	  • DEV ONLY: when running in Studio and the Figma ScreenGuis haven't been imported yet, builds
	    a plain debug panel so the full loop can be playtested. It is not the game UI.
	BUILT, UNTESTED in Studio.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Vault = ReplicatedStorage:WaitForChild("Vault")
local Format = require(Vault.Shared.Format)
local GameShared = ReplicatedStorage:WaitForChild("GameShared")
local Cases = require(GameShared:WaitForChild("Cases"))
local Config = require(GameShared:WaitForChild("Config"))

local AnimalAnimator = require(script.Parent:WaitForChild("AnimalAnimator"))
local Interaction = require(script.Parent:WaitForChild("Interaction"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local player = Players.LocalPlayer
local gui = player:WaitForChild("PlayerGui")

local state = nil
local selectedAppt = nil

AnimalAnimator.start()

---------------------------------------------------------------------------------------------
-- Figma UI binding (by layer name). Missing pieces are skipped silently.
---------------------------------------------------------------------------------------------
local function find(screenName: string, childName: string): Instance?
	local screen = gui:FindFirstChild(screenName)
	return screen and screen:FindFirstChild(childName, true)
end

local function setText(screenName: string, childName: string, text: string)
	local label = find(screenName, childName)
	if label and (label:IsA("TextLabel") or label:IsA("TextButton")) then
		label.Text = text
	end
end

local function renderHud()
	if not state then
		return
	end
	local c = state.clinic
	setText("HUD", "ClinicName", c.name)
	setText("HUD", "Cash", "$" .. Format.abbreviate(c.cash))
	setText("HUD", "Level", "Lv " .. c.level)
	setText("HUD", "Reputation", string.format("%.1f ★", c.reputation))
	setText("HUD", "Day", "Day " .. c.day)
	local fill = find("HUD", "XpBar")
	fill = fill and fill:FindFirstChild("Fill")
	if fill and fill:IsA("GuiObject") then
		local span = math.max(1, c.xpNext - c.xpThis)
		fill.Size = UDim2.fromScale(math.clamp((c.xp - c.xpThis) / span, 0, 1), 1)
	end
	local banner = find("HUD", "TutorialBanner")
	if banner and banner:IsA("GuiObject") then
		banner.Visible = state.tutorial ~= nil
		if state.tutorial then
			setText("HUD", "Text", state.tutorial.text)
		end
	end
end

local function renderExamOverlay(a)
	local screen = gui:FindFirstChild("ExamOverlay")
	if screen and screen:IsA("ScreenGui") then
		screen.Enabled = a ~= nil
	end
	if not a then
		return
	end
	local step = a.steps[a.step]
	local labels = {
		open = "Open the %s",
		take = "Pick up the %s",
		approach = "Move next to the patient",
		pose = "Ask the patient to %s",
		place = "Place it and hold still",
		scan = "Look closely — drag to explore",
		stroke = "Gently rub over the area",
		wrap = "Circle around the paw to wrap",
		pull = "Grip and pull slowly",
		dose = "Set the dose",
		wait = "Wait…",
		record = "Record your findings",
	}
	if step then
		local fmt = labels[step.kind] or step.kind
		setText(
			"ExamOverlay",
			"StepLabel",
			step.label or string.format(fmt, step.target or step.tool or step.pose or "")
		)
	elseif a.summary then
		setText("ExamOverlay", "StepLabel", a.summary)
	end
	local reading = a.readings[#a.readings]
	if reading then
		local text = reading.heartRate and string.format("♥ %d bpm · %s", reading.heartRate, reading.sound)
			or reading.respRate and string.format("Lungs: %s · %d /min", reading.sound, reading.respRate)
			or reading.note
			or ""
		setText("ExamOverlay", "Reading", text)
	end
	if a.message then
		setText("ExamOverlay", "StepLabel", a.message)
	end
end

Interaction.onChanged = function(a)
	renderExamOverlay(a)
end

Remotes:WaitForChild("State").OnClientEvent:Connect(function(snap)
	state = snap
	renderHud()
end)

Remotes:WaitForChild("Toast").OnClientEvent:Connect(function(kind, text)
	local list = find("HUD", "AlertsList")
	if list and list:IsA("GuiObject") then
		local template = list:FindFirstChild("Template")
		if template then
			local item = template:Clone()
			item.Name = "Toast"
			item.Visible = true
			local label = item:FindFirstChildWhichIsA("TextLabel", true)
			if label then
				label.Text = text
			end
			item.Parent = list
			task.delay(4, function()
				item:Destroy()
			end)
		end
	end
	if RunService:IsStudio() then
		print(string.format("[Toast:%s] %s", kind, text))
	end
end)

Remotes:WaitForChild("Invoice").OnClientEvent:Connect(function(_, bill)
	local screen = gui:FindFirstChild("Invoice")
	if screen and screen:IsA("ScreenGui") then
		screen.Enabled = true
		setText("Invoice", "Total", "$" .. bill.total)
		setText(
			"Invoice",
			"Stars",
			string.rep("★", math.floor(bill.stars)) .. (if bill.stars % 1 > 0 then "½" else "")
		)
		task.delay(5, function()
			screen.Enabled = false
		end)
	end
end)

---------------------------------------------------------------------------------------------
-- Interactables: animate doors / drawers from the server "Open" attribute
---------------------------------------------------------------------------------------------
local function bindInteractable(model: Instance)
	if not model:IsA("Model") then
		return
	end
	local hinge = model:FindFirstChild("Door") or model:FindFirstChild("Drawer")
	if not hinge or not hinge:IsA("BasePart") then
		return
	end
	local closed = hinge.CFrame
	local isDrawer = hinge.Name == "Drawer"
	local function update()
		local base = model:GetPivot():ToWorldSpace(model:GetPivot():ToObjectSpace(closed))
		local open = if isDrawer
			then base * CFrame.new(0, 0, -hinge.Size.Z * 0.8)
			else base * CFrame.new(-hinge.Size.X / 2, 0, 0) * CFrame.Angles(0, math.rad(-100), 0) * CFrame.new(
				hinge.Size.X / 2,
				0,
				0
			)
		local goal = if model:GetAttribute("Open") then open else base
		TweenService
			:Create(hinge, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { CFrame = goal })
			:Play()
	end
	model:GetAttributeChangedSignal("Open"):Connect(update)
end

for _, m in CollectionService:GetTagged("Interactable") do
	bindInteractable(m)
end
CollectionService:GetInstanceAddedSignal("Interactable"):Connect(bindInteractable)

---------------------------------------------------------------------------------------------
-- Held tool props (visible to everyone, driven by the server HeldTool attribute)
---------------------------------------------------------------------------------------------
local function bindHeldTool(p: Player)
	local current = nil
	local function refresh()
		if current then
			current:Destroy()
			current = nil
		end
		local toolName = p:GetAttribute("HeldTool")
		local char = p.Character
		local hand = char and char:FindFirstChild("RightHand")
		local tools = ReplicatedStorage.Assets:FindFirstChild("Tools")
		local template = tools and toolName and tools:FindFirstChild(toolName)
		if hand and template then
			current = template:Clone()
			current:PivotTo(hand.CFrame)
			for _, part in current:GetDescendants() do
				if part:IsA("BasePart") then
					part.CanCollide = false
					part.Massless = true
					local weld = Instance.new("WeldConstraint")
					weld.Part0 = hand
					weld.Part1 = part
					weld.Parent = part
				end
			end
			current.Parent = char
		end
	end
	p:GetAttributeChangedSignal("HeldTool"):Connect(refresh)
	p.CharacterAdded:Connect(refresh)
end
for _, p in Players:GetPlayers() do
	bindHeldTool(p)
end
Players.PlayerAdded:Connect(bindHeldTool)

---------------------------------------------------------------------------------------------
-- Spatial animal sounds (Assets.Sounds.<Species>.<Name>), rate-limited per animal
---------------------------------------------------------------------------------------------
local lastVocal = {}
local function bindAnimalSounds(model: Instance)
	model:GetAttributeChangedSignal("Vocal"):Connect(function()
		local vocal = model:GetAttribute("Vocal")
		if not vocal then
			return
		end
		local now = os.clock()
		local key = model
		local cooldown = if vocal == "Pant" or vocal == "Purr" then 2.5 else 4
		if lastVocal[key] and now - lastVocal[key] < cooldown then
			return
		end
		lastVocal[key] = now
		local sounds = ReplicatedStorage.Assets:FindFirstChild("Sounds")
		local folder = sounds and sounds:FindFirstChild(model:GetAttribute("Species") or "")
		local template = folder and folder:FindFirstChild(vocal)
		local head = model:FindFirstChild("Head", true)
		if template and head then
			local s = template:Clone()
			s.RollOffMaxDistance = 60
			s.PlaybackSpeed = (s.PlaybackSpeed or 1) * (model:GetAttribute("Size") == "small" and 1.35 or 1)
			s.Parent = head
			s:Play()
			s.Ended:Once(function()
				s:Destroy()
			end)
		end
	end)
end
for _, m in CollectionService:GetTagged("Animal") do
	bindAnimalSounds(m)
end
CollectionService:GetInstanceAddedSignal("Animal"):Connect(bindAnimalSounds)

---------------------------------------------------------------------------------------------
-- DEV-ONLY debug panel (Studio, before the Figma UI is imported). Not the shipped UI.
---------------------------------------------------------------------------------------------
if RunService:IsStudio() then
	task.delay(3, function()
		if gui:FindFirstChild("VetComputer") then
			return -- real UI present
		end
		local screen = Instance.new("ScreenGui")
		screen.Name = "DevVetPanel"
		screen.ResetOnSpawn = false
		screen.Parent = gui
		local frame = Instance.new("ScrollingFrame")
		frame.Size = UDim2.new(0, 360, 1, -40)
		frame.Position = UDim2.fromOffset(10, 20)
		frame.BackgroundTransparency = 0.25
		frame.AutomaticCanvasSize = Enum.AutomaticSize.Y
		frame.CanvasSize = UDim2.new()
		frame.Parent = screen
		local layout = Instance.new("UIListLayout")
		layout.Padding = UDim.new(0, 4)
		layout.Parent = frame

		local function button(text: string, fn)
			local b = Instance.new("TextButton")
			b.Size = UDim2.new(1, -8, 0, 30)
			b.Text = text
			b.TextScaled = true
			b.Parent = frame
			b.Activated:Connect(fn)
			return b
		end
		local function label(text: string)
			local l = Instance.new("TextLabel")
			l.Size = UDim2.new(1, -8, 0, 0)
			l.AutomaticSize = Enum.AutomaticSize.Y
			l.TextWrapped = true
			l.TextXAlignment = Enum.TextXAlignment.Left
			l.Text = text
			l.BackgroundTransparency = 1
			l.TextColor3 = Color3.new(1, 1, 1)
			l.Parent = frame
		end
		local function rebuild()
			for _, child in frame:GetChildren() do
				if not child:IsA("UIListLayout") then
					child:Destroy()
				end
			end
			if not state then
				label("waiting for state…")
				return
			end
			local c = state.clinic
			label(
				string.format(
					"[DEV PANEL] %s · $%d · Lv %d · %.1f★ · Day %d",
					c.name,
					c.cash,
					c.level,
					c.reputation,
					c.day
				)
			)
			if state.tutorial then
				label("Tutorial: " .. state.tutorial.text)
			end
			for _, appt in state.appointments do
				label(
					string.format(
						"#%d %s (%s) — %s\n“%s”",
						appt.id,
						appt.patient.name,
						appt.patient.breed,
						appt.phase,
						appt.customer.complaint
					)
				)
				if appt.phase == "AtReception" then
					button("Check in #" .. appt.id, function()
						Remotes.CheckIn:FireServer(appt.id)
					end)
				elseif appt.phase == "Waiting" then
					button("Call #" .. appt.id .. " to Exam1", function()
						selectedAppt = appt.id
						Remotes.CallPatient:FireServer(appt.id, "Exam1")
					end)
				elseif appt.phase == "InRoom" then
					local large = appt.patient.breed == "GoldenRetriever"
					button(if large then "Help up: front paws" else "Pick up", function()
						Remotes.HelpOntoTable:FireServer(appt.id, if large then "liftFront" else "pickUp")
					end)
					button(if large then "Help up: back end" else "Place on table", function()
						Remotes.HelpOntoTable:FireServer(appt.id, if large then "liftBack" else "placeOnTable")
					end)
					button("Open carrier", function()
						Remotes.OpenCarrier:FireServer(appt.id)
					end)
				elseif appt.phase == "OnTable" or appt.phase == "Exam" then
					for examId in Config.unlocks.exams do
						if Config.unlocks.exams[examId] <= c.level then
							button("Exam: " .. Cases.exams[examId].name, function()
								Interaction.begin(appt.id, "exam", examId)
							end)
						end
					end
					for diagId, d in Cases.diagnoses do
						if d.minLevel <= c.level then
							button("Diagnose: " .. d.name, function()
								Remotes.Diagnose:FireServer(appt.id, diagId)
							end)
						end
					end
				elseif appt.phase == "Diagnosed" or appt.phase == "Treatment" or appt.phase == "Treated" then
					for tId, t in Cases.treatments do
						if (Config.unlocks.treatments[tId] or 99) <= c.level and not appt.treatmentsDone[tId] then
							button("Treat: " .. t.name, function()
								Interaction.begin(appt.id, "treatment", tId)
							end)
						end
					end
					button("Finish visit", function()
						Remotes.FinishVisit:FireServer(appt.id)
					end)
				elseif appt.phase == "Checkout" then
					button("Print invoice #" .. appt.id, function()
						Remotes.PrintInvoice:FireServer(appt.id)
					end)
				end
				for _, entry in appt.chart do
					label("  • " .. entry.kind .. ": " .. entry.text)
				end
				if appt.phase ~= "Waiting" and appt.phase ~= "AtReception" then
					for _, kind in { "Pet", "Comfort", "Treat" } do
						button(kind .. " #" .. appt.id, function()
							Remotes.Comfort:FireServer(appt.id, kind)
						end)
					end
				end
			end
			local a = Interaction.active
			if a then
				local step = a.steps[a.step]
				label(
					"Procedure "
						.. a.id
						.. " step "
						.. a.step
						.. ": "
						.. (step and step.kind or "done")
						.. " "
						.. (a.message or "")
				)
				if step and step.kind == "record" then
					button("Record", Interaction.record)
				elseif step and step.kind == "scan" then
					button("Side L", function()
						Interaction.setSide("L")
					end)
					button("Side R", function()
						Interaction.setSide("R")
					end)
					button("Done looking", Interaction.finishScan)
				end
				button("Cancel procedure", Interaction.cancel)
			end
		end
		task.spawn(function()
			while screen.Parent do
				rebuild()
				task.wait(0.75)
			end
		end)
	end)
end

_ = selectedAppt
