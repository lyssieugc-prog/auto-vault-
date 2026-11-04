--[[
	Net — creates RemoteEvents/Functions under ReplicatedStorage.Remotes and wraps every handler
	with rate limiting + pcall. Argument validation stays in each handler (use Shared/Guard).

	local Net = require(ServerScriptService.Vault.Server.Net)
	Net.on("BuyEgg", function(player, eggName, amount)
		if not Guard.oneOf(eggName, EGG_NAMES) or not Guard.integer(amount, 1, 3) then return end
		...
	end, { rate = 3, burst = 5 })
	Net.fire(player, "CurrencyChanged", "Cash", 120)
	Net.invoke("GetProfile", function(player) return snapshot end)
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Layout (see systems/default.project.json): ReplicatedStorage.Vault.{Shared,Client},
-- ServerScriptService.VaultServer = these Server modules (never replicated to clients).
local Guard = require(ReplicatedStorage:WaitForChild("Vault"):WaitForChild("Shared"):WaitForChild("Guard"))

local Net = {}

local folder = ReplicatedStorage:FindFirstChild("Remotes")
if not folder then
	folder = Instance.new("Folder")
	folder.Name = "Remotes"
	folder.Parent = ReplicatedStorage
end

local limiters = {}

local function getRemote(name: string, className: string)
	local remote = folder:FindFirstChild(name)
	if not remote then
		remote = Instance.new(className)
		remote.Name = name
		remote.Parent = folder
	end
	return remote
end

function Net.event(name: string): RemoteEvent
	return getRemote(name, "RemoteEvent")
end

function Net.on(name: string, handler, limits)
	local limiter = Guard.rateLimiter(limits)
	limiters[name] = limiter
	Net.event(name).OnServerEvent:Connect(function(player, ...)
		if not limiter:allow(player.UserId, name) then
			return
		end
		local ok, err = pcall(handler, player, ...)
		if not ok then
			warn(string.format("[Net] %s handler error for %s: %s", name, player.Name, tostring(err)))
		end
	end)
end

function Net.invoke(name: string, handler, limits)
	local limiter = Guard.rateLimiter(limits)
	limiters[name] = limiter
	local remote = getRemote(name, "RemoteFunction")
	remote.OnServerInvoke = function(player, ...)
		if not limiter:allow(player.UserId, name) then
			return nil
		end
		local ok, result = pcall(handler, player, ...)
		if not ok then
			warn(string.format("[Net] %s invoke error for %s: %s", name, player.Name, tostring(result)))
			return nil
		end
		return result
	end
end

function Net.fire(player: Player, name: string, ...)
	Net.event(name):FireClient(player, ...)
end

function Net.fireAll(name: string, ...)
	Net.event(name):FireAllClients(...)
end

Players.PlayerRemoving:Connect(function(player)
	for _, limiter in limiters do
		limiter:removePlayer(player.UserId)
	end
end)

return Net
