--[[
	My Vet Office — server entry. Wires Roblox services/remotes to GameLogic.
	Untestable outside Studio: verify with qa/playtest.md.
]]

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local SharedVault = ReplicatedStorage:WaitForChild("Vault"):WaitForChild("Shared")
local VaultServer = ServerScriptService:WaitForChild("VaultServer")
local GameShared = ReplicatedStorage:WaitForChild("GameShared")

local Config = require(GameShared:WaitForChild("Config"))
local GameLogic = require(GameShared:WaitForChild("GameLogic"))
local DataService = require(SharedVault.DataService)
local DataStoreAdapter = require(VaultServer.DataStoreAdapter)
local MarketplaceAdapter = require(VaultServer.MarketplaceAdapter)
local Net = require(VaultServer.Net)

local Modules = {}
for _, name in { "Currency", "Inventory", "Upgrades", "Rebirth", "Rewards", "Tutorial", "Monetization", "Rarity" } do
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

-- Create server->client events up front so clients can WaitForChild them immediately.
Net.event("State")
Net.event("Currency")

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
	sync(player)
end

local function saveAndRelease(player: Player)
	local profile = data:get(player.UserId)
	if not profile then
		return
	end
	logic:writeProfile(player.UserId, profile)
	data:release(player.UserId)
	logic:unloadPlayer(player.UserId)
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
			logic:writeProfile(player.UserId, profile)
		end
	end
	data:saveAll(true)
end)

-- Autosave
task.spawn(function()
	while true do
		task.wait(Config.autosaveSeconds)
		for _, player in Players:GetPlayers() do
			local profile = data:get(player.UserId)
			if profile then
				logic:writeProfile(player.UserId, profile)
				data:save(player.UserId)
			end
		end
	end
end)

-- Passive income tick (1s)
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc >= 1 then
		logic.currency:step(acc)
		acc = 0
	end
end)

-- Purchases
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

-- Remotes: every handler re-validates inside GameLogic. Rate limits per remote.
local function loaded(player: Player): boolean
	return logic.profiles[player.UserId] ~= nil
end

Net.on("Collect", function(player)
	if loaded(player) then
		logic:collect(player.UserId)
	end
end, { rate = Config.collect.rate, burst = Config.collect.burst })

Net.invoke("Hatch", function(player, eggName)
	if not loaded(player) then
		return nil
	end
	local result, err = logic:hatch(player.UserId, eggName)
	sync(player)
	return { result = result, error = err }
end, { rate = 2, burst = 4 })

for remote, method in { Equip = "equip", Unequip = "unequip", BuyUpgrade = "buyUpgrade" } do
	Net.invoke(remote, function(player, arg)
		if not loaded(player) then
			return nil
		end
		local ok, err = logic[method](logic, player.UserId, arg)
		sync(player)
		return { ok = ok, error = err }
	end, { rate = 4, burst = 8 })
end

for remote, method in { Rebirth = "doRebirth", ClaimDaily = "claimDaily" } do
	Net.invoke(remote, function(player)
		if not loaded(player) then
			return nil
		end
		local a, b = logic[method](logic, player.UserId)
		sync(player)
		return { result = a, info = b }
	end, { rate = 1, burst = 2 })
end

for remote, method in { ClaimPlaytime = "claimPlaytime", ClaimQuest = "claimQuest" } do
	Net.invoke(remote, function(player, arg)
		if not loaded(player) then
			return nil
		end
		local reward, err = logic[method](logic, player.UserId, arg)
		sync(player)
		return { reward = reward, error = err }
	end, { rate = 2, burst = 4 })
end
