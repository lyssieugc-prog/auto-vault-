--[[
	Ragdoll Off a Mountain — server entry. Wires Roblox services, physics and remotes to GameLogic.
	Untestable outside Studio: verify with qa/playtest.md (built, untested until a Studio playtest).

	World contract (created by studio/import_map.luau from the Blender layout.json):
	  Workspace.Map.Markers.<Name>   anchored invisible parts: Base1..6, Peak1Pad..Peak5Pad, LiftPad,
	                                 LandingZone (box), SpawnFallback, EggStand1..5, CannonShop, ...
	  ReplicatedStorage.Assets.BaseCamps.BaseCamp_Stage1..5   Blender base-camp stage models
	  ReplicatedStorage.Assets.Pets.<PetId>                   Blender pet models (optional in v1)
	Game Settings (owner, cannot be scripted): Max Players = 6, Avatar = R15.
]]

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local SharedVault = ReplicatedStorage:WaitForChild("Vault"):WaitForChild("Shared")
local VaultServer = ServerScriptService:WaitForChild("VaultServer")
local GameShared = ReplicatedStorage:WaitForChild("GameShared")

local Config = require(GameShared:WaitForChild("Config"))
local GameLogic = require(GameShared:WaitForChild("GameLogic"))
local DataService = require(SharedVault.DataService)
local Guard = require(SharedVault.Guard)
local DataStoreAdapter = require(VaultServer.DataStoreAdapter)
local MarketplaceAdapter = require(VaultServer.MarketplaceAdapter)
local Net = require(VaultServer.Net)
local Ragdoll = require(script.Parent:WaitForChild("Ragdoll"))

local Modules = { RagdollScore = require(GameShared:WaitForChild("RagdollScore")) }
for _, name in GameLogic.MODULES do
	Modules[name] = require(SharedVault[name])
end

local random = Random.new()
local logic = GameLogic.new(Config, Modules, {
	now = os.time,
	rng = function()
		return random:NextNumber()
	end,
	ownsPass = function(userId, passId)
		return MarketplaceService:UserOwnsGamePassAsync(userId, passId)
	end,
})

local useMemory = RunService:IsStudio() and Config.studioDataStore ~= "real"
if useMemory then
	warn("[Data] Studio: using in-memory DataStore (set Config.studioDataStore = 'real' to test persistence)")
end
local data = DataService.new({
	store = if useMemory then DataStoreAdapter.memory() else DataStoreAdapter.new(Config.dataStoreName),
	template = GameLogic.profileTemplate(Modules),
	sessionId = game.JobId ~= "" and game.JobId or "studio",
	wait = task.wait,
})

-- World markers -------------------------------------------------------------------------------------

local function marker(name: string): BasePart?
	local map = Workspace:FindFirstChild("Map")
	local markers = map and map:FindFirstChild("Markers")
	local part = markers and markers:FindFirstChild(name)
	if part and part:IsA("BasePart") then
		return part
	end
	return nil
end

local function teleport(player: Player, name: string)
	local target = marker(name) or marker("SpawnFallback")
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if target and root then
		character:PivotTo(target.CFrame + Vector3.new(0, 4, 0))
	end
end

local basesFolder = Workspace:FindFirstChild("Bases") or Instance.new("Folder")
basesFolder.Name = "Bases"
basesFolder.Parent = Workspace

local function renderBase(index: number, ownerId: number?)
	local old = basesFolder:FindFirstChild("Base" .. index)
	if old then
		old:Destroy()
	end
	local pad = marker("Base" .. index)
	local assets = ReplicatedStorage:FindFirstChild("Assets")
	local camps = assets and assets:FindFirstChild("BaseCamps")
	if not pad or not camps then
		return
	end
	local profile = ownerId and logic.profiles[ownerId]
	local stage = Config.bases.stages[if profile then profile.bestStage else 1]
	local template = camps:FindFirstChild(stage.model)
	if not template then
		warn("[Bases] missing model " .. stage.model)
		return
	end
	local model = template:Clone()
	model.Name = "Base" .. index
	model:PivotTo(pad.CFrame)
	model:SetAttribute("OwnerUserId", ownerId or 0)
	local sign = model:FindFirstChild("OwnerSign", true)
	local owner = ownerId and Players:GetPlayerByUserId(ownerId)
	if sign then
		sign:SetAttribute("OwnerName", if owner then owner.DisplayName else "Free Base")
	end
	model.Parent = basesFolder
end

logic.plots:onChanged(function(index, ownerId)
	task.defer(renderBase, index, ownerId)
end)
for i = 1, Config.bases.count do
	task.defer(renderBase, i, nil)
end

local function landingCheck(position: Vector3): boolean
	local zone = marker("LandingZone")
	if not zone then
		return false
	end
	local localPos = zone.CFrame:PointToObjectSpace(position)
	local half = zone.Size / 2
	return math.abs(localPos.X) <= half.X and math.abs(localPos.Y) <= half.Y and math.abs(localPos.Z) <= half.Z
end

-- Remotes (server -> client) ----------------------------------------------------------------------------

for _, name in { "State", "Currency", "BonePop", "RunSummary", "Announcement", "Notify" } do
	Net.event(name)
end

local function sync(player: Player)
	if logic.profiles[player.UserId] then
		Net.fire(player, "State", logic:snapshot(player.UserId))
	end
end

logic.currency:onChanged(function(userId, name, balance)
	local player = Players:GetPlayerByUserId(userId)
	if player then
		Net.fire(player, "Currency", name, balance)
	end
end)

local lastAnnouncement = 0
local function announce(text: string)
	local now = os.clock()
	if now - lastAnnouncement < Config.announcements.minSeconds then
		return
	end
	lastAnnouncement = now
	for _, player in Players:GetPlayers() do
		Net.fire(player, "Announcement", text)
	end
end

-- Friends bonus ----------------------------------------------------------------------------------------

local function refreshFriends()
	local list = Players:GetPlayers()
	for _, player in list do
		local count = 0
		for _, other in list do
			if other ~= player then
				local ok, isFriend = pcall(player.IsFriendsWith, player, other.UserId)
				if ok and isFriend then
					count += 1
				end
			end
		end
		if logic.profiles[player.UserId] then
			logic:setFriendsInServer(player.UserId, count)
		end
	end
end

-- Leaderboards (all-time bones: OrderedDataStore; best run: this server) --------------------------------

local bonesBoard = nil
if not useMemory then
	local ok, store = pcall(function()
		return game:GetService("DataStoreService"):GetOrderedDataStore(Config.leaderboards.bonesStore)
	end)
	bonesBoard = if ok then store else nil
end

local function pushLeaderboard(player: Player)
	local profile = logic.profiles[player.UserId]
	if bonesBoard and profile then
		pcall(function()
			bonesBoard:SetAsync(tostring(player.UserId), math.floor(profile.stats.bones))
		end)
	end
end

local leaderboardTop = { bones = {}, run = {} }
task.spawn(function()
	while true do
		if bonesBoard then
			local ok, pages = pcall(function()
				return bonesBoard:GetSortedAsync(false, Config.leaderboards.size)
			end)
			if ok and pages then
				leaderboardTop.bones = pages:GetCurrentPage()
			end
		end
		local runs = {}
		for userId, profile in logic.profiles do
			table.insert(runs, { key = userId, value = profile.stats.bestRun })
		end
		table.sort(runs, function(a, b)
			return a.value > b.value
		end)
		leaderboardTop.run = runs
		ReplicatedStorage:SetAttribute("LeaderboardVersion", os.time())
		task.wait(Config.leaderboards.refreshSeconds)
	end
end)

-- Player lifecycle ---------------------------------------------------------------------------------------

local function onCharacter(player: Player, character: Model)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if humanoid and logic.profiles[player.UserId] then
		local plot = logic.plots:plotOf(player.UserId)
		task.defer(teleport, player, if plot then "Base" .. plot else "SpawnFallback")
	end
end

local function onPlayerAdded(player: Player)
	local profile, err = data:load(player.UserId)
	if not profile then
		player:Kick("Your data could not be loaded (" .. tostring(err) .. "). Please rejoin.")
		return
	end
	if not player.Parent then
		data:release(player.UserId)
		return
	end
	logic:loadPlayer(player.UserId, profile)
	player.CharacterAdded:Connect(function(character)
		onCharacter(player, character)
	end)
	if player.Character then
		onCharacter(player, player.Character)
	end
	refreshFriends()
	sync(player)
end

local function saveAndRelease(player: Player)
	local profile = data:get(player.UserId)
	if not profile then
		return
	end
	logic:endSession(player.UserId)
	pushLeaderboard(player)
	logic:writeProfile(player.UserId, profile)
	data:release(player.UserId)
	logic:unloadPlayer(player.UserId)
	refreshFriends()
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end
Players.PlayerRemoving:Connect(saveAndRelease)

game:BindToClose(function()
	for _, player in Players:GetPlayers() do
		local profile = data:get(player.UserId)
		if profile then
			logic:endSession(player.UserId)
			logic:writeProfile(player.UserId, profile)
		end
	end
	data:saveAll(true)
end)

task.spawn(function()
	while true do
		task.wait(Config.autosaveSeconds)
		for _, player in Players:GetPlayers() do
			local profile = data:get(player.UserId)
			if profile then
				logic:writeProfile(player.UserId, profile)
				data:save(player.UserId)
				pushLeaderboard(player)
			end
		end
	end
end)

-- 1 s tick: boost expiry
task.spawn(function()
	while true do
		task.wait(1)
		for _, player in Players:GetPlayers() do
			if logic.profiles[player.UserId] and logic:tick(player.UserId) then
				sync(player)
			end
		end
	end
end)

-- Purchases (ids are CONFIG_REQUIRED placeholders; nothing is sold until the owner creates products)
MarketplaceAdapter.bind(logic.monetization, {
	get = function(_, userId)
		return data:get(userId)
	end,
	save = function(_, userId)
		local profile = data:get(userId)
		if profile then
			logic:writeProfile(userId, profile)
		end
		return data:save(userId)
	end,
}, function(userId)
	logic:refreshMultipliers(userId)
	local player = Players:GetPlayerByUserId(userId)
	if player then
		sync(player)
	end
end)

-- Runs: launch -> server ragdoll -> impacts -> summary ----------------------------------------------------

local activeRagdolls = {}

local function nearPad(player: Player, peak: number): boolean
	local pad = marker("Peak" .. peak .. "Pad")
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not pad or not root then
		return false
	end
	return (root.Position - pad.Position).Magnitude <= Config.run.padRadius
end

local function loaded(player: Player): boolean
	return logic.profiles[player.UserId] ~= nil
end

Net.invoke("Launch", function(player, pitch, yaw, charge)
	if not loaded(player) or activeRagdolls[player] then
		return { error = "running" }
	end
	local profile = logic.profiles[player.UserId]
	if not nearPad(player, profile.selectedPeak) then
		return { error = "not_on_pad" }
	end
	local params, err = logic:startRun(player.UserId, pitch, yaw, charge)
	if not params then
		return { error = err }
	end
	local userId = player.UserId
	local pad = marker("Peak" .. profile.selectedPeak .. "Pad")
	params.forward = pad and pad.CFrame.LookVector
	activeRagdolls[player] = Ragdoll.launch(player.Character, params, {
		restSpeed = Config.run.restSpeed,
		restSeconds = Config.run.restSeconds,
		isLanded = landingCheck,
		onImpact = function(partName, speed, t)
			local event = logic:reportImpact(userId, partName, speed, t)
			if event then
				Net.fire(player, "BonePop", event)
			end
		end,
		onFinish = function()
			activeRagdolls[player] = nil
			if not logic.profiles[userId] then
				return
			end
			local summary = logic:finishRun(userId)
			if summary then
				Net.fire(player, "RunSummary", summary)
				if summary.fullSkeleton then
					announce(player.DisplayName .. " broke ALL 206 BONES! 💀")
				end
				local stage, upgraded = logic:updateBaseStage(userId)
				if upgraded then
					renderBase(logic.plots:plotOf(userId), userId)
					Net.fire(player, "Notify", "BASE UPGRADED: " .. Config.bases.stages[stage].name)
				end
			end
			sync(player)
			task.delay(1.5, function()
				if player.Parent then
					player:LoadCharacter() -- respawns at the base camp (Bone Clinic)
				end
			end)
		end,
	})
	if not activeRagdolls[player] then
		logic:finishRun(userId)
		return { error = "no_character" }
	end
	return { ok = true, params = params }
end, { rate = 1, burst = 2 })

-- Lift: base pad / HUD button -> your selected peak's pad
Net.invoke("Lift", function(player, peak)
	if not loaded(player) or activeRagdolls[player] then
		return { error = "busy" }
	end
	if peak ~= nil then
		local ok, err = logic:selectPeak(player.UserId, peak)
		if not ok then
			return { error = err }
		end
	end
	teleport(player, "Peak" .. logic.profiles[player.UserId].selectedPeak .. "Pad")
	logic:tutorialEvent(player.UserId, "lift")
	sync(player)
	return { ok = true }
end, { rate = 1, burst = 2 })

local function bindTouchPad(name: string, onTouch)
	local pad = marker(name)
	if not pad then
		return
	end
	local debounce = {}
	pad.Touched:Connect(function(hit)
		local player = Players:GetPlayerFromCharacter(hit.Parent)
		if player and not debounce[player] and loaded(player) and not activeRagdolls[player] then
			debounce[player] = true
			onTouch(player)
			task.delay(2, function()
				debounce[player] = nil
			end)
		end
	end)
end
task.defer(function()
	bindTouchPad("LiftPad", function(player)
		teleport(player, "Peak" .. logic.profiles[player.UserId].selectedPeak .. "Pad")
		logic:tutorialEvent(player.UserId, "lift")
		sync(player)
	end)
end)

-- Shops + rewards (every handler re-validates inside GameLogic) -------------------------------------------

local simple = {
	UnlockPeak = "unlockPeak",
	BuyCannon = "buyCannon",
	Rebirth = "doRebirth",
	ClaimDaily = "claimDaily",
	SkipTutorial = "skipTutorial",
}
for remote, method in simple do
	Net.invoke(remote, function(player)
		if not loaded(player) then
			return nil
		end
		local a, b = logic[method](logic, player.UserId)
		sync(player)
		return { result = a, info = b }
	end, { rate = 2, burst = 4 })
end

local oneArg = {
	SelectPeak = {
		method = "selectPeak",
		valid = function(v)
			return Guard.integer(v, 1, #Config.peaks)
		end,
	},
	BuyUpgrade = {
		method = "buyUpgrade",
		valid = function(v)
			return Guard.string(v, 20)
		end,
	},
	Hatch = {
		method = "hatch",
		valid = function(v)
			return Guard.string(v, 20)
		end,
	},
	Equip = {
		method = "equip",
		valid = function(v)
			return Guard.string(v, 20)
		end,
	},
	Unequip = {
		method = "unequip",
		valid = function(v)
			return Guard.string(v, 20)
		end,
	},
	ClaimPlaytime = {
		method = "claimPlaytime",
		valid = function(v)
			return Guard.integer(v, 1, #Config.rewards.playtime)
		end,
	},
	ClaimQuest = {
		method = "claimQuest",
		valid = function(v)
			return Guard.string(v, 40)
		end,
	},
	RedeemCode = {
		method = "redeemCode",
		valid = function(v)
			return Guard.string(v, 64)
		end,
	},
}
for remote, def in oneArg do
	Net.invoke(remote, function(player, arg)
		if not loaded(player) or not def.valid(arg) then
			return { error = "invalid" }
		end
		local result, err = logic[def.method](logic, player.UserId, arg)
		if remote == "Hatch" and result and result.announce then
			announce(player.DisplayName .. " hatched a " .. result.rarity .. " " .. Config.pets[result.id].name .. "!")
		end
		sync(player)
		return { result = result, error = err }
	end, { rate = 3, burst = 6 })
end

Net.invoke("ClaimSeason", function(player, track, tier)
	if not loaded(player) or not Guard.oneOf(track, { "free", "premium" }) or not Guard.integer(tier, 1, 50) then
		return { error = "invalid" }
	end
	local reward, err = logic:claimSeason(player.UserId, track, tier)
	sync(player)
	return { result = reward, error = err }
end, { rate = 4, burst = 8 })

Net.invoke("EggOdds", function(player, eggName)
	if not loaded(player) or not Guard.string(eggName, 20) then
		return nil
	end
	return logic:eggOdds(player.UserId, eggName)
end, { rate = 4, burst = 8 })

Net.invoke("Leaderboards", function()
	return leaderboardTop
end, { rate = 1, burst = 2 })

-- Config-driven events: an admin/scheduler sets ReplicatedStorage attribute "Event_<Name>" = true.
for name in Config.events do
	local attr = "Event_" .. name
	ReplicatedStorage:GetAttributeChangedSignal(attr):Connect(function()
		logic:setEventActive(name, ReplicatedStorage:GetAttribute(attr) == true)
	end)
end
