--[[
	Edit-mode preview builder (owner rule L-11: see the map + UI WITHOUT pressing Play).
	Run once in Studio (command bar or Studio MCP run_code) after:
	  1. the Blender FBX chunks are imported (studio/README.md step 2),
	  2. studio/place_markers.luau has run,
	  3. Rojo is connected (so ReplicatedStorage.GameShared exists in Edit mode).
	It saves into the place: every ScreenGui under StarterGui (mock data), stage-1 base camps on all
	6 base pads, and hub props on their markers. Re-run any time; it replaces what it built.
	Runtime scripts later swap bases to each owner's stage — this is a PREVIEW, not a playtest.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local GameShared = ReplicatedStorage:WaitForChild("GameShared")
local Config = require(GameShared.Config)
local UIScreens = require(GameShared.UIScreens)

-- 1. UI: all screens in StarterGui; HUD + Shop visible (flip with studio/preview_screen.luau)
UIScreens.buildAll(StarterGui, Config, "Shop")
print("[Preview] built " .. #UIScreens.order .. " ScreenGuis in StarterGui")

-- 2. World: base camps + hub props onto the Blender markers
local markers = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Markers")
local assets = ReplicatedStorage:FindFirstChild("Assets")
if not markers or not assets then
	warn("[Preview] Workspace.Map.Markers or ReplicatedStorage.Assets missing — import the map + run place_markers first")
	return
end

local function place(templateParent, templateName, markerName, folder, cloneName)
	local template = templateParent and templateParent:FindFirstChild(templateName)
	local marker = markers:FindFirstChild(markerName)
	if not template or not marker then
		warn(string.format("[Preview] skipped %s on %s (missing template or marker)", templateName, markerName))
		return
	end
	local old = folder:FindFirstChild(cloneName)
	if old then
		old:Destroy()
	end
	local model = template:Clone()
	model.Name = cloneName
	model:PivotTo(marker.CFrame)
	model:SetAttribute("EditPreview", true)
	model.Parent = folder
end

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name) or Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

local bases = folderIn(workspace, "Bases")
for i = 1, Config.bases.count do
	place(assets:FindFirstChild("BaseCamps"), Config.bases.stages[1].model, "Base" .. i, bases, "Base" .. i)
end

-- marker -> prop model name (ReplicatedStorage.Assets.Props). Edit if the Blender export names change.
local PROPS = {
	RebirthStatue = "RebirthStatue",
	CannonShop = "CannonShop",
	UpgradeStand = "UpgradeStand",
	SeasonBoard = "SeasonBoard",
	LeaderboardBones = "Leaderboard",
	LeaderboardRun = "Leaderboard",
	DailyChest = "DailyChest",
	EggStand1 = "EggStand",
	EggStand2 = "EggStand",
	EggStand3 = "EggStand",
	EggStand4 = "EggStand",
	EggStand5 = "EggStand",
	CannonMount1 = "Cannon1_PartyPopper",
	CannonMount2 = "Cannon2_BarrelBlaster",
	CannonMount3 = "Cannon3_RocketRig",
	CannonMount4 = "Cannon4_MegaMortar",
	CannonMount5 = "Cannon5_MeteorLauncher",
}
local props = folderIn(workspace, "HubProps")
for markerName, modelName in PROPS do
	place(assets:FindFirstChild("Props"), modelName, markerName, props, markerName)
end
print("[Preview] placed bases + hub props — map, bases and UI are now visible in Edit mode")
