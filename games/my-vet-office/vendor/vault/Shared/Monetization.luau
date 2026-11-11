--[[
	Monetization — idempotent developer-product receipts, gamepass caching and the house-style
	"2x → 100x" repurchasable multiplier ladder.

	local shop = Monetization.new({
		products = {
			[123456] = { name = "Cash_Tier1", grant = function(userId, profile) ... return true end },
		},
		passes = { [987654] = "VIP", [987655] = "x2Luck" },
		ladders = {
			Cash = { -- each tier is a developer product; buying the next tier raises the multiplier
				{ productId = 111, multiplier = 2 }, { productId = 112, multiplier = 3 },
				{ productId = 113, multiplier = 5 }, { productId = 114, multiplier = 10 },
				{ productId = 115, multiplier = 25 }, { productId = 116, multiplier = 50 },
				{ productId = 117, multiplier = 100 },
			},
		},
		ownsPass = function(userId, passId) return MarketplaceService:UserOwnsGamePassAsync(userId, passId) end,
		historySize = 200,
	})

	processReceipt returns "granted" or "retry"; Server/MarketplaceAdapter maps these to
	Enum.ProductPurchaseDecision and saves the profile BEFORE returning PurchaseGranted.

	IDs here are placeholders until the owner creates real products. Never create products,
	publish, or spend Robux without explicit owner approval.
]]

local Monetization = {}
Monetization.__index = Monetization

function Monetization.new(config)
	config = config or {}
	local self = setmetatable({}, Monetization)
	self.products = config.products or {}
	self.passes = config.passes or {}
	self.ladders = config.ladders or {}
	self.ownsPass = config.ownsPass
	self.historySize = config.historySize or 200
	self.passCache = {} -- [userId] = { [passName] = bool }
	-- Register ladder tiers as products.
	for ladderName, tiers in self.ladders do
		for index, tier in tiers do
			assert(self.products[tier.productId] == nil, "Monetization: product id reused by ladder")
			self.products[tier.productId] = {
				name = ladderName .. "_x" .. tostring(tier.multiplier),
				ladder = ladderName,
				tierIndex = index,
			}
		end
	end
	return self
end

function Monetization.ensureState(profile)
	profile.purchases = profile.purchases or { history = {}, order = {}, ladders = {} }
	return profile.purchases
end

function Monetization:ladderMultiplier(profile, ladderName: string): number
	local state = Monetization.ensureState(profile)
	local index = state.ladders[ladderName] or 0
	local tiers = self.ladders[ladderName]
	if not tiers or index == 0 then
		return 1
	end
	return tiers[index].multiplier
end

-- Next tier to sell (productId, multiplier) or nil when maxed.
function Monetization:nextLadderTier(profile, ladderName: string)
	local state = Monetization.ensureState(profile)
	local tiers = self.ladders[ladderName]
	if not tiers then
		return nil
	end
	return tiers[(state.ladders[ladderName] or 0) + 1]
end

function Monetization:_record(state, purchaseId: string)
	state.history[purchaseId] = true
	table.insert(state.order, purchaseId)
	while #state.order > self.historySize do
		local oldest = table.remove(state.order, 1)
		state.history[oldest] = nil
	end
end

-- receipt = { PurchaseId, PlayerId, ProductId }. Returns "granted" | "retry".
function Monetization:processReceipt(receipt, profile): string
	if not profile then
		return "retry" -- player not loaded yet; Roblox will retry later
	end
	local state = Monetization.ensureState(profile)
	local purchaseId = tostring(receipt.PurchaseId)
	if state.history[purchaseId] then
		return "granted" -- already granted on an earlier attempt
	end
	local product = self.products[receipt.ProductId]
	if not product then
		return "retry"
	end
	if product.ladder then
		local current = state.ladders[product.ladder] or 0
		-- Buying any tier sets you to at least that tier (never downgrade).
		state.ladders[product.ladder] = math.max(current, product.tierIndex)
	elseif product.grant then
		local ok, result = pcall(product.grant, receipt.PlayerId, profile, receipt)
		if not ok or result == false then
			return "retry"
		end
	end
	self:_record(state, purchaseId)
	return "granted"
end

-- Cached gamepass check by pass NAME. Errors from the checker return false (not cached).
function Monetization:hasPass(userId, passName: string): boolean
	local cache = self.passCache[userId]
	if cache and cache[passName] ~= nil then
		return cache[passName]
	end
	local passId = nil
	for id, name in self.passes do
		if name == passName then
			passId = id
			break
		end
	end
	if not passId or not self.ownsPass then
		return false
	end
	local ok, owns = pcall(self.ownsPass, userId, passId)
	if not ok then
		return false
	end
	self.passCache[userId] = cache or {}
	self.passCache[userId][passName] = owns == true
	return owns == true
end

-- Call from MarketplaceService.PromptGamePassPurchaseFinished when purchased = true.
function Monetization:markPassOwned(userId, passId: number)
	local name = self.passes[passId]
	if name then
		self.passCache[userId] = self.passCache[userId] or {}
		self.passCache[userId][name] = true
	end
end

function Monetization:removePlayer(userId)
	self.passCache[userId] = nil
end

-- Flags table for Tycoon gates etc: { VIP = true, x2Luck = false }.
function Monetization:passFlags(userId): { [string]: boolean }
	local flags = {}
	for _, name in self.passes do
		flags[name] = self:hasPass(userId, name)
	end
	return flags
end

return Monetization
