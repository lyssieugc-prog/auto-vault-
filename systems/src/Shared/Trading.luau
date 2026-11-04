--[[
	Trading — server-authoritative two-player trades with anti-scam rules.

	local trading = Trading.new({
		inventory = inventory,    -- Inventory instance
		currency = currency,      -- optional Currency instance (for currency in trades)
		tradableCurrencies = { "Gems" },
		maxItems = 8,
		confirmDelay = 3,         -- seconds both players must wait after both are ready
		requestTimeout = 30,
		now = os.clock,
	})

	Flow: request(a, b) -> accept(b, a) -> setOffer(player, uids, currencies) ...
	      -> ready(a) + ready(b) -> (wait confirmDelay) -> confirm(a) + confirm(b) -> executes.
	Any offer change clears both ready flags. Offered items are locked in Inventory so they cannot
	be sold/removed mid-trade. Execution re-validates everything and rolls back on any failure.
]]

local Trading = {}
Trading.__index = Trading

function Trading.new(config)
	assert(type(config) == "table" and config.inventory, "Trading.new: inventory required")
	local self = setmetatable({}, Trading)
	self.inventory = config.inventory
	self.currency = config.currency
	self.tradableCurrencies = config.tradableCurrencies or {}
	self.maxItems = config.maxItems or 8
	self.confirmDelay = config.confirmDelay or 3
	self.requestTimeout = config.requestTimeout or 30
	self.now = config.now or os.clock
	self.requests = {} -- [toId] = { [fromId] = time }
	self.sessions = {} -- [userId] = session (shared by both players)
	self.listeners = {}
	return self
end

function Trading:onCompleted(callback): () -> ()
	table.insert(self.listeners, callback)
	return function()
		local i = table.find(self.listeners, callback)
		if i then
			table.remove(self.listeners, i)
		end
	end
end

function Trading:sessionOf(userId)
	return self.sessions[userId]
end

function Trading:request(fromId, toId): (boolean, string?)
	if fromId == toId then
		return false, "self"
	end
	if self.sessions[fromId] or self.sessions[toId] then
		return false, "busy"
	end
	self.requests[toId] = self.requests[toId] or {}
	self.requests[toId][fromId] = self.now()
	return true, nil
end

function Trading:accept(toId, fromId): (boolean, string?)
	local pending = self.requests[toId]
	local sentAt = pending and pending[fromId]
	if not sentAt then
		return false, "no_request"
	end
	pending[fromId] = nil
	if self.now() - sentAt > self.requestTimeout then
		return false, "expired"
	end
	if self.sessions[fromId] or self.sessions[toId] then
		return false, "busy"
	end
	local session = {
		players = { fromId, toId },
		offers = {
			[fromId] = { items = {}, currencies = {} },
			[toId] = { items = {}, currencies = {} },
		},
		ready = {},
		confirmed = {},
		readyAt = nil,
	}
	self.sessions[fromId] = session
	self.sessions[toId] = session
	return true, nil
end

local function otherPlayer(session, userId)
	return if session.players[1] == userId then session.players[2] else session.players[1]
end

function Trading:_unlockOffer(userId, offer)
	for _, uid in offer.items do
		if self.inventory:has(userId, uid) then
			self.inventory:setLocked(userId, uid, false)
		end
	end
end

function Trading:_resetReady(session)
	session.ready = {}
	session.confirmed = {}
	session.readyAt = nil
end

-- Replaces a player's whole offer. uids = { "i1", ... }, currencies = { Gems = 100 }.
function Trading:setOffer(userId, uids: { string }, currencies: { [string]: number }?): (boolean, string?)
	local session = self.sessions[userId]
	if not session then
		return false, "no_session"
	end
	if type(uids) ~= "table" or #uids > self.maxItems then
		return false, "too_many"
	end
	local seen = {}
	for _, uid in uids do
		if type(uid) ~= "string" or seen[uid] or not self.inventory:has(userId, uid) then
			return false, "invalid_item"
		end
		seen[uid] = true
	end
	local cleanCurrencies = {}
	for name, amount in pairs(currencies or {}) do
		if not table.find(self.tradableCurrencies, name) or not self.currency then
			return false, "invalid_currency"
		end
		if type(amount) ~= "number" or amount ~= amount or amount < 0 or amount % 1 ~= 0 then
			return false, "invalid_amount"
		end
		if not self.currency:canAfford(userId, name, amount) then
			return false, "funds"
		end
		if amount > 0 then
			cleanCurrencies[name] = amount
		end
	end
	local offer = session.offers[userId]
	self:_unlockOffer(userId, offer)
	offer.items = table.clone(uids)
	offer.currencies = cleanCurrencies
	for _, uid in offer.items do
		self.inventory:setLocked(userId, uid, true)
	end
	self:_resetReady(session)
	return true, nil
end

function Trading:ready(userId): (boolean, string?)
	local session = self.sessions[userId]
	if not session then
		return false, "no_session"
	end
	session.ready[userId] = true
	if session.ready[session.players[1]] and session.ready[session.players[2]] then
		session.readyAt = self.now()
	end
	return true, nil
end

function Trading:cancel(userId, reason: string?): boolean
	local session = self.sessions[userId]
	if not session then
		return false
	end
	for _, player in session.players do
		self:_unlockOffer(player, session.offers[player])
		self.sessions[player] = nil
	end
	session.cancelled = reason or "cancelled"
	return true
end

-- Both must confirm after confirmDelay. Returns ok, reason; executes when second confirms.
function Trading:confirm(userId): (boolean, string?)
	local session = self.sessions[userId]
	if not session then
		return false, "no_session"
	end
	if not session.readyAt then
		return false, "not_ready"
	end
	if self.now() - session.readyAt < self.confirmDelay then
		return false, "too_early"
	end
	session.confirmed[userId] = true
	local other = otherPlayer(session, userId)
	if not session.confirmed[other] then
		return true, "waiting"
	end
	return self:_execute(session)
end

function Trading:_execute(session): (boolean, string?)
	local a, b = session.players[1], session.players[2]
	local inv, cur = self.inventory, self.currency
	-- Re-validate.
	for _, pair in { { a, b }, { b, a } } do
		local giver, receiver = pair[1], pair[2]
		local offer = session.offers[giver]
		for _, uid in offer.items do
			if not inv:has(giver, uid) then
				self:cancel(a, "item_missing")
				return false, "item_missing"
			end
		end
		for name, amount in offer.currencies do
			if not cur:canAfford(giver, name, amount) then
				self:cancel(a, "funds")
				return false, "funds"
			end
		end
		local incoming = #offer.items
		local outgoing = #session.offers[receiver].items
		if inv:count(receiver) - outgoing + incoming > inv.capacity then
			self:cancel(a, "full")
			return false, "full"
		end
	end
	-- Remove all offered items first (so capacity frees up), then add to the other side.
	local removed = { [a] = {}, [b] = {} }
	for _, giver in { a, b } do
		for _, uid in session.offers[giver].items do
			local item = inv:remove(giver, uid, true)
			table.insert(removed[giver], item)
		end
	end
	local added = { [a] = {}, [b] = {} }
	local failed = false
	for _, giver in { a, b } do
		local receiver = if giver == a then b else a
		for _, item in removed[giver] do
			local uid = inv:add(receiver, item)
			if not uid then
				failed = true
				break
			end
			table.insert(added[receiver], uid)
		end
		if failed then
			break
		end
	end
	if failed then
		-- Roll back: take back what was added, return originals.
		for player, uids in added do
			for _, uid in uids do
				inv:remove(player, uid, true)
			end
		end
		for giver, items in removed do
			for _, item in items do
				inv:add(giver, item)
			end
		end
		self:cancel(a, "rollback")
		return false, "rollback"
	end
	for _, giver in { a, b } do
		local receiver = if giver == a then b else a
		for name, amount in session.offers[giver].currencies do
			cur:spend(giver, name, amount, "trade")
			cur:add(receiver, name, amount, "trade")
		end
	end
	self.sessions[a] = nil
	self.sessions[b] = nil
	session.completed = true
	for _, listener in self.listeners do
		listener(a, b, added)
	end
	return true, nil
end

function Trading:removePlayer(userId)
	self:cancel(userId, "left")
	self.requests[userId] = nil
	for _, pending in self.requests do
		pending[userId] = nil
	end
end

return Trading
