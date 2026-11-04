--[[
	MarketplaceAdapter — binds Shared/Monetization + Shared/DataService to MarketplaceService.
	Saves the profile BEFORE telling Roblox a purchase was granted.

	MarketplaceAdapter.bind(monetization, dataService, function(userId) ... end) -- onGranted
]]

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local MarketplaceAdapter = {}

function MarketplaceAdapter.bind(monetization, dataService, onGranted: ((number, number) -> ())?)
	MarketplaceService.ProcessReceipt = function(receipt)
		local profile = dataService:get(receipt.PlayerId)
		local decision = monetization:processReceipt(receipt, profile)
		if decision ~= "granted" then
			return Enum.ProductPurchaseDecision.NotProcessedYet
		end
		local saved = dataService:save(receipt.PlayerId)
		if not saved then
			return Enum.ProductPurchaseDecision.NotProcessedYet
		end
		if onGranted then
			task.spawn(onGranted, receipt.PlayerId, receipt.ProductId)
		end
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end

	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, passId, purchased)
		if purchased then
			monetization:markPassOwned(player.UserId, passId)
		end
	end)

	Players.PlayerRemoving:Connect(function(player)
		monetization:removePlayer(player.UserId)
	end)
end

return MarketplaceAdapter
