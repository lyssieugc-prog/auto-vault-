--[[
	Ragdoll Off a Mountain — client entry. Receives server state, drives HUD + UI motion.
	Real UI is built from the Figma file (figma/README.md); this binds by instance NAME so the
	Figma-built ScreenGui only needs matching names: HUD.Cash, HUD.Gems, HUD.CollectButton.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Vault = ReplicatedStorage:WaitForChild("Vault")
local Format = require(Vault.Shared.Format)
local MobileUI = require(Vault.Client.MobileUI)
local UIAnim = require(Vault.Client.UIAnim)

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local player = Players.LocalPlayer
local gui = player:WaitForChild("PlayerGui")

local function hud()
	local screen = gui:FindFirstChild("HUD")
	return screen
end

local function setCurrency(name: string, balance: number)
	local screen = hud()
	local label = screen and screen:FindFirstChild(name, true)
	if label and label:IsA("TextLabel") then
		label.Text = Format.abbreviate(balance)
	end
end

Remotes:WaitForChild("Currency").OnClientEvent:Connect(function(name, balance)
	setCurrency(name, balance)
end)

Remotes:WaitForChild("State").OnClientEvent:Connect(function(state)
	for name, balance in state.currency do
		setCurrency(name, balance)
	end
end)

task.spawn(function()
	local screen = gui:WaitForChild("HUD", 30)
	if not screen then
		warn("[Client] HUD ScreenGui not found — build it from the Figma file")
		return
	end
	MobileUI.applySafeArea(screen)
	MobileUI.scaleForDevice(screen)
	for _, d in screen:GetDescendants() do
		if d:IsA("GuiButton") then
			UIAnim.bindButton(d)
			MobileUI.enforceTouchTarget(d)
		end
	end
	local collect = screen:FindFirstChild("CollectButton", true)
	if collect and collect:IsA("GuiButton") then
		MobileUI.onTap(collect, function()
			Remotes.Collect:FireServer()
			UIAnim.numberPop(screen, "+1")
		end)
	end
end)
