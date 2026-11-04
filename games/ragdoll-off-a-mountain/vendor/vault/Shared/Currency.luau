--[[
	Currency — server-authoritative wallets, multipliers and passive income.

	local currency = Currency.new({
		currencies = { Cash = { start = 0 }, Gems = { start = 0, max = 1e12 } },
		integer = true, -- floor all balances (default true)
	})
	currency:load(userId, savedBalances)       -- from DataService profile
	currency:earn(userId, "Cash", 10)          -- applies multipliers (gamepass, rebirth, boosts)
	currency:spend(userId, "Cash", 50)         -- returns false if insufficient / invalid
	currency:setMultiplier(userId, "Rebirth", 1.5)
	currency:setIncome(userId, "Plot", "Cash", 25) -- 25 Cash per second
	currency:step(dt)                          -- call from Heartbeat / a 1s loop on the server
	currency:onChanged(function(userId, name, balance, delta, reason) end)

	Never call add/spend with values from the client without validating them first.
]]

local Currency = {}
Currency.__index = Currency

local function isValidAmount(amount: any): boolean
	return type(amount) == "number" and amount == amount and amount >= 0 and amount < math.huge
end

function Currency.new(config)
	assert(type(config) == "table" and type(config.currencies) == "table", "Currency.new: currencies required")
	local self = setmetatable({}, Currency)
	self.defs = config.currencies
	self.integer = config.integer ~= false
	self.wallets = {} -- [userId] = { balances = {}, multipliers = {}, income = {}, carry = {} }
	self.listeners = {}
	return self
end

function Currency:onChanged(callback): () -> ()
	table.insert(self.listeners, callback)
	return function()
		local i = table.find(self.listeners, callback)
		if i then
			table.remove(self.listeners, i)
		end
	end
end

function Currency:_emit(userId, name, balance, delta, reason)
	for _, listener in self.listeners do
		listener(userId, name, balance, delta, reason)
	end
end

function Currency:_def(name: string)
	local def = self.defs[name]
	if not def then
		error("Currency: unknown currency '" .. tostring(name) .. "'", 3)
	end
	return def
end

function Currency:_wallet(userId)
	local wallet = self.wallets[userId]
	if not wallet then
		error("Currency: wallet not loaded for " .. tostring(userId), 3)
	end
	return wallet
end

function Currency:load(userId, saved: { [string]: number }?)
	local balances = {}
	for name, def in self.defs do
		local value = saved and saved[name]
		balances[name] = if isValidAmount(value) then value else (def.start or 0)
	end
	self.wallets[userId] = { balances = balances, multipliers = {}, income = {}, carry = {} }
end

function Currency:isLoaded(userId): boolean
	return self.wallets[userId] ~= nil
end

-- Returns a plain table to persist. Call before unload.
function Currency:serialize(userId): { [string]: number }
	return table.clone(self:_wallet(userId).balances)
end

function Currency:unload(userId)
	self.wallets[userId] = nil
end

function Currency:get(userId, name: string): number
	self:_def(name)
	return self:_wallet(userId).balances[name]
end

function Currency:canAfford(userId, name: string, amount: number): boolean
	return isValidAmount(amount) and self:get(userId, name) >= amount
end

-- Low-level add with no multipliers. Returns the amount actually added (clamped by max).
function Currency:add(userId, name: string, amount: number, reason: string?): number
	if not isValidAmount(amount) then
		return 0
	end
	local def = self:_def(name)
	local wallet = self:_wallet(userId)
	local before = wallet.balances[name]
	local after = before + amount
	if self.integer then
		after = math.floor(after)
	end
	if def.max then
		after = math.min(after, def.max)
	end
	wallet.balances[name] = after
	local delta = after - before
	if delta ~= 0 then
		self:_emit(userId, name, after, delta, reason or "add")
	end
	return delta
end

-- Spends if affordable. Returns true on success. Atomic: nothing changes on failure.
function Currency:spend(userId, name: string, amount: number, reason: string?): boolean
	if not self:canAfford(userId, name, amount) then
		return false
	end
	local wallet = self:_wallet(userId)
	local after = wallet.balances[name] - amount
	wallet.balances[name] = after
	self:_emit(userId, name, after, -amount, reason or "spend")
	return true
end

-- Admin/reset use only (rebirth, migrations).
function Currency:set(userId, name: string, value: number, reason: string?)
	assert(isValidAmount(value), "Currency:set: invalid value")
	self:_def(name)
	local wallet = self:_wallet(userId)
	local before = wallet.balances[name]
	wallet.balances[name] = value
	self:_emit(userId, name, value, value - before, reason or "set")
end

-- Multipliers stack multiplicatively. Set to 1 or nil to remove.
function Currency:setMultiplier(userId, key: string, value: number?, currencyName: string?)
	local wallet = self:_wallet(userId)
	local slot = currencyName or "*"
	wallet.multipliers[slot] = wallet.multipliers[slot] or {}
	wallet.multipliers[slot][key] = if value and value ~= 1 then value else nil
end

function Currency:multiplier(userId, name: string): number
	local wallet = self:_wallet(userId)
	local total = 1
	for _, slot in { "*", name } do
		local list = wallet.multipliers[slot]
		if list then
			for _, value in list do
				total *= value
			end
		end
	end
	return total
end

-- Gameplay earning: applies multipliers. Returns amount added.
function Currency:earn(userId, name: string, base: number, reason: string?): number
	if not isValidAmount(base) then
		return 0
	end
	return self:add(userId, name, base * self:multiplier(userId, name), reason or "earn")
end

-- Passive income per second from a named source (plot, tycoon, pets). nil/0 removes it.
function Currency:setIncome(userId, source: string, name: string, perSecond: number?)
	self:_def(name)
	local wallet = self:_wallet(userId)
	wallet.income[source] = if perSecond and perSecond > 0 then { name = name, rate = perSecond } else nil
end

function Currency:incomePerSecond(userId, name: string): number
	local total = 0
	for _, entry in self:_wallet(userId).income do
		if entry.name == name then
			total += entry.rate
		end
	end
	return total * self:multiplier(userId, name)
end

-- Advances passive income for every loaded wallet by dt seconds. Fractions carry over.
function Currency:step(dt: number)
	if not isValidAmount(dt) then
		return
	end
	for userId, wallet in self.wallets do
		local totals = {}
		for _, entry in wallet.income do
			totals[entry.name] = (totals[entry.name] or 0) + entry.rate * dt
		end
		for name, raw in totals do
			local amount = raw * self:multiplier(userId, name) + (wallet.carry[name] or 0)
			local whole = if self.integer then math.floor(amount) else amount
			wallet.carry[name] = amount - whole
			if whole > 0 then
				self:add(userId, name, whole, "income")
			end
		end
	end
end

return Currency
