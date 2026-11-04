--[[
	Offline place builder (Lune, runs in CI): Rojo-built place -> "Ragdoll Off a Mountain.rbxl" with
	everything that can exist without Studio, so the owner opens ONE file and sees it in Edit mode
	(owner rule L-11):
	  • all scripts (from the Rojo build)
	  • every UI screen saved in StarterGui with mock preview data (HUD + Shop enabled)
	  • Workspace.Map.Markers from the Blender layout.json (when the map export exists)
	  • bright daytime Lighting
	Blender meshes CANNOT be added here: Roblox only creates MeshParts when the owner imports the
	FBX files in Studio (File > Import 3D), which uploads them to their account. See IMPORT_GUIDE.md.

	lune run games/ragdoll-off-a-mountain/studio/build_place.luau <in.rbxl> <out.rbxl> [layout.json]
]]

local fs = require("@lune/fs")
local process = require("@lune/process")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")

local Config = require("../src/shared/Config")
local UIScreens = require("../src/shared/UIScreens")

local input, output, layoutPath = process.args[1], process.args[2], process.args[3]
assert(input and output, "usage: build_place.luau <in.rbxl> <out.rbxl> [layout.json]")

local game = roblox.deserializePlace(fs.readFile(input))
local Instance = roblox.Instance

-- UI in StarterGui (Edit-mode visible) ---------------------------------------------------------------
UIScreens.setRuntime(roblox)
local starterGui = game:GetService("StarterGui")
UIScreens.buildAll(starterGui, Config, "Shop")
print("[build_place] ScreenGuis in StarterGui: " .. #starterGui:GetChildren())

-- Lighting: bright daytime (bible §10) -----------------------------------------------------------------
local lighting = game:GetService("Lighting")
lighting.ClockTime = 13
lighting.Brightness = 3
lighting.GlobalShadows = true
lighting.OutdoorAmbient = roblox.Color3.fromRGB(150, 160, 180)

-- Markers from the Blender layout (Blender Z-up -> Roblox Y-up: (x, y, z) -> (x, z, -y)) -------------
local workspace = game:GetService("Workspace")
local map = workspace:FindFirstChild("Map") or Instance.new("Model")
map.Name = "Map"
map.Parent = workspace
local markers = map:FindFirstChild("Markers") or Instance.new("Folder")
markers.Name = "Markers"
markers.Parent = map

local placed = 0
if layoutPath and fs.isFile(layoutPath) then
	local layout = serde.decode("json", fs.readFile(layoutPath))
	local list = layout.markers or layout
	for key, m in list do
		local name = m.name or key
		local p = m.position
		local size = m.size or { 4, 4, 1 }
		local part = Instance.new("Part")
		part.Name = name
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.Transparency = 1
		part.Size = roblox.Vector3.new(size[1] or 4, math.max(size[3] or 1, 1), size[2] or 4)
		part.CFrame = roblox.CFrame.new(p[1], p[3], -p[2])
			* roblox.CFrame.Angles(0, math.rad(tonumber(m.rotationY) or 0), 0)
		part.Parent = markers
		placed += 1
	end
end
print("[build_place] markers placed: " .. placed .. (if placed == 0 then " (map layout not exported yet)" else ""))

-- Readme inside the place so the owner sees the next step in Explorer
local note = Instance.new("StringValue")
note.Name = "READ_ME_ImportBlenderModels"
note.Value = "Import the FBX files from the download (File > Import 3D) — see IMPORT_GUIDE.md. "
	.. "Then run studio/build_edit_preview.luau in the command bar to place base camps + props."
note.Parent = workspace

fs.writeFile(output, roblox.serializePlace(game))
print("[build_place] wrote " .. output)
