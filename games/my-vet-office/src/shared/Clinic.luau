--[[
	Clinic — the business side. Pure + server-authoritative (plain-table state, persisted in the
	owner's profile).

	  money        Cash balance (all changes go through earn/spend here — never client values)
	  progression  XP → level (unlock table), reputation (rolling average of star ratings)
	  inventory    supply stock; orders arrive as DELIVERY BOXES that someone must carry in and
	               shelve (stock only rises when shelved)
	  finances     ledger of revenue + expenses; daily rent/utilities/wages at end of each day
	  staff        hired NPC employees (role, wage) — they physically do jobs (server glue)
	  roles        friends in the clinic: Vet / Receptionist / Technician / Assistant / Visitor,
	               with a permission matrix (visitors can't modify anything)
	  placement    grid furniture placement per room: bounds, overlap, rotation, cost, refunds
	  branding     clinic name, paint/floor per room, uniform colour
]]

local Clinic = {}

function Clinic.newState(config)
	local stock = {}
	for id, def in config.supplies do
		stock[id] = def.start or 0
	end
	return {
		name = config.defaultName,
		cash = config.startCash,
		xp = 0,
		level = 1,
		ratings = {},
		reputation = config.startReputation,
		stock = stock,
		deliveries = {}, -- { id, item, qty }
		nextDeliveryId = 1,
		ledger = {}, -- { day, kind, label, amount }
		day = 1,
		staff = {}, -- { id, role, name, wage }
		nextStaffId = 1,
		placements = {}, -- "p<n>" -> { item, room, x, z, rot }
		nextPlacementId = 1,
		rooms = { Reception = true, Waiting = true, Exam1 = true },
		finishes = {}, -- room -> { wall, floor }
		uniform = "Teal",
		patientsTreated = 0,
		followUps = {}, -- pending follow-up visits { patient, caseId }
	}
end

---------------------------------------------------------------------------------------------
-- Money + ledger
---------------------------------------------------------------------------------------------
local function ledger(state, kind: string, label: string, amount: number)
	table.insert(state.ledger, { day = state.day, kind = kind, label = label, amount = amount })
	if #state.ledger > 200 then
		table.remove(state.ledger, 1)
	end
end

function Clinic.earn(state, amount: number, label: string)
	assert(type(amount) == "number" and amount >= 0 and amount == amount, "bad amount")
	state.cash += amount
	ledger(state, "revenue", label, amount)
end

function Clinic.spend(state, amount: number, label: string): boolean
	if type(amount) ~= "number" or amount < 0 or amount ~= amount or state.cash < amount then
		return false
	end
	state.cash -= amount
	ledger(state, "expense", label, -amount)
	return true
end

---------------------------------------------------------------------------------------------
-- Progression
---------------------------------------------------------------------------------------------
function Clinic.xpForLevel(level: number): number
	-- total XP needed to REACH `level` (level 1 = 0). Gentle early, ~8 patients for level 2.
	if level <= 1 then
		return 0
	end
	return math.floor(250 * (level - 1) ^ 1.55)
end

function Clinic.addXp(config, state, xp: number): { number }
	state.xp += xp
	local gained = {}
	while state.level < config.maxLevel and state.xp >= Clinic.xpForLevel(state.level + 1) do
		state.level += 1
		table.insert(gained, state.level)
	end
	return gained
end

function Clinic.addRating(config, state, stars: number)
	table.insert(state.ratings, stars)
	if #state.ratings > config.ratingWindow then
		table.remove(state.ratings, 1)
	end
	local sum = config.startReputation * 2 -- prior: two virtual ratings at the start value
	for _, s in state.ratings do
		sum += s
	end
	state.reputation = math.floor(sum / (#state.ratings + 2) * 100 + 0.5) / 100
end

function Clinic.unlocked(config, state, kind: string, id: string): boolean
	local need = config.unlocks[kind] and config.unlocks[kind][id]
	if need == nil then
		return false
	end
	return state.level >= need
end

-- Customer arrival interval (seconds) from reputation: better clinics get busier.
function Clinic.arrivalInterval(config, state): number
	local rep = state.reputation
	return math.max(config.arrival.min, config.arrival.base - (rep - 3) * config.arrival.perStar)
end

---------------------------------------------------------------------------------------------
-- Inventory
---------------------------------------------------------------------------------------------
function Clinic.hasSupplies(state, supplies): (boolean, string?)
	for id, qty in supplies do
		if (state.stock[id] or 0) < qty then
			return false, id
		end
	end
	return true, nil
end

function Clinic.consume(state, supplies): (boolean, string?)
	local ok, missing = Clinic.hasSupplies(state, supplies)
	if not ok then
		return false, missing
	end
	for id, qty in supplies do
		state.stock[id] -= qty
	end
	return true, nil
end

-- Order supplies: pays now, a delivery box appears at the back door.
function Clinic.order(config, state, item: string, qty: number)
	local def = config.supplies[item]
	if not def or type(qty) ~= "number" or qty % 1 ~= 0 or qty < 1 or qty > 50 then
		return { ok = false, message = "Invalid order" }
	end
	if #state.deliveries >= config.maxDeliveries then
		return { ok = false, message = "Shelve the boxes already waiting first" }
	end
	local cost = math.ceil(def.cost * qty)
	if not Clinic.spend(state, cost, "Supplies: " .. def.name) then
		return { ok = false, message = "Not enough cash" }
	end
	local box = { id = state.nextDeliveryId, item = item, qty = qty }
	state.nextDeliveryId += 1
	table.insert(state.deliveries, box)
	return { ok = true, box = box }
end

-- Someone carried a delivery box to the right shelf.
function Clinic.shelve(state, boxId: number)
	for i, box in state.deliveries do
		if box.id == boxId then
			table.remove(state.deliveries, i)
			state.stock[box.item] = (state.stock[box.item] or 0) + box.qty
			return { ok = true, item = box.item, qty = box.qty }
		end
	end
	return { ok = false, message = "No such box" }
end

---------------------------------------------------------------------------------------------
-- Days + expenses
---------------------------------------------------------------------------------------------
function Clinic.dailyExpenses(config, state)
	local wages = 0
	for _, s in state.staff do
		wages += s.wage
	end
	local rooms = 0
	for _ in state.rooms do
		rooms += 1
	end
	return {
		rent = config.expenses.rentBase + rooms * config.expenses.rentPerRoom,
		utilities = config.expenses.utilitiesBase + rooms * config.expenses.utilitiesPerRoom,
		wages = wages,
	}
end

-- End of an in-game day. Cash can't go below 0 from bills: the shortfall becomes debt that
-- blocks hiring/expansion until paid (manageable, never a game over).
function Clinic.endDay(config, state)
	local e = Clinic.dailyExpenses(config, state)
	local total = e.rent + e.utilities + e.wages
	local paid = math.min(total, state.cash)
	state.cash -= paid
	ledger(state, "expense", "Rent + utilities + wages", -paid)
	state.debt = (state.debt or 0) + (total - paid)
	state.day += 1
	return { expenses = e, total = total, debt = state.debt }
end

function Clinic.summary(state, day: number?)
	day = day or state.day
	local revenue, expenses = 0, 0
	for _, entry in state.ledger do
		if entry.day == day then
			if entry.amount >= 0 then
				revenue += entry.amount
			else
				expenses -= entry.amount
			end
		end
	end
	return { day = day, revenue = revenue, expenses = expenses, profit = revenue - expenses }
end

---------------------------------------------------------------------------------------------
-- Staff
---------------------------------------------------------------------------------------------
function Clinic.hire(config, state, role: string, name: string)
	local def = config.staffRoles[role]
	if not def then
		return { ok = false, message = "Unknown role" }
	end
	if state.level < def.minLevel then
		return { ok = false, message = "Unlocks at level " .. def.minLevel }
	end
	if (state.debt or 0) > 0 then
		return { ok = false, message = "Pay off your bills first" }
	end
	if #state.staff >= config.maxStaff then
		return { ok = false, message = "No room for more staff" }
	end
	if not Clinic.spend(state, def.hireCost, "Hired " .. role) then
		return { ok = false, message = "Not enough cash" }
	end
	local s = { id = state.nextStaffId, role = role, name = name, wage = def.wage }
	state.nextStaffId += 1
	table.insert(state.staff, s)
	return { ok = true, staff = s }
end

function Clinic.fire(state, staffId: number)
	for i, s in state.staff do
		if s.id == staffId then
			table.remove(state.staff, i)
			return true
		end
	end
	return false
end

---------------------------------------------------------------------------------------------
-- Roles + permissions (multiplayer)
---------------------------------------------------------------------------------------------
Clinic.PERMISSIONS = {
	Owner = { treat = true, checkIn = true, restock = true, build = true, manage = true, finance = true },
	CoOwner = { treat = true, checkIn = true, restock = true, build = true, manage = false, finance = true },
	Vet = { treat = true, checkIn = true, restock = true },
	Technician = { treat = true, checkIn = true, restock = true, assist = true },
	Receptionist = { checkIn = true, restock = true },
	Assistant = { restock = true, assist = true, clean = true },
	Visitor = {},
}

function Clinic.can(role: string?, action: string): boolean
	local perms = Clinic.PERMISSIONS[role or "Visitor"] or Clinic.PERMISSIONS.Visitor
	return perms[action] == true
end

---------------------------------------------------------------------------------------------
-- Placement (customisation) — grid of 1-stud cells; footprint w×d rotated by 90° steps.
---------------------------------------------------------------------------------------------
local function footprint(item, rot: number)
	if rot % 180 == 90 then
		return item.d, item.w
	end
	return item.w, item.d
end

local function rectOf(item, x: number, z: number, rot: number)
	local w, d = footprint(item, rot)
	return { x0 = x, z0 = z, x1 = x + w, z1 = z + d }
end

local function overlaps(a, b): boolean
	return a.x0 < b.x1 and b.x0 < a.x1 and a.z0 < b.z1 and b.z0 < a.z1
end

function Clinic.canPlace(
	config,
	state,
	itemId: string,
	room: string,
	x: number,
	z: number,
	rot: number,
	ignoreId: string?
)
	local item = config.catalog[itemId]
	if not item then
		return false, "Unknown item"
	end
	local bounds = config.rooms[room]
	if not bounds or not state.rooms[room] then
		return false, "You don't own that room yet"
	end
	if (item.minLevel or 1) > state.level then
		return false, "Unlocks at level " .. item.minLevel
	end
	if item.rooms and not table.find(item.rooms, bounds.kind) then
		return false, "That doesn't belong in this room"
	end
	for _, v in { x, z, rot } do
		if type(v) ~= "number" or v ~= v or v % 1 ~= 0 then
			return false, "Snap to the grid"
		end
	end
	if rot % 90 ~= 0 or rot < 0 or rot >= 360 then
		return false, "Bad rotation"
	end
	local r = rectOf(item, x, z, rot)
	if r.x0 < 0 or r.z0 < 0 or r.x1 > bounds.w or r.z1 > bounds.d then
		return false, "Out of the room"
	end
	for id, p in state.placements do
		if id ~= ignoreId and p.room == room then
			if overlaps(r, rectOf(config.catalog[p.item], p.x, p.z, p.rot)) then
				return false, "Something is already there"
			end
		end
	end
	return true, nil
end

function Clinic.place(config, state, itemId: string, room: string, x: number, z: number, rot: number)
	local ok, err = Clinic.canPlace(config, state, itemId, room, x, z, rot)
	if not ok then
		return { ok = false, message = err }
	end
	local item = config.catalog[itemId]
	if not Clinic.spend(state, item.price, "Bought " .. item.name) then
		return { ok = false, message = "Not enough cash" }
	end
	-- string ids: DataStores can't hold sparse integer-keyed tables
	local id = "p" .. state.nextPlacementId
	state.nextPlacementId += 1
	state.placements[id] = { item = itemId, room = room, x = x, z = z, rot = rot }
	return { ok = true, id = id }
end

function Clinic.move(config, state, id: string, x: number, z: number, rot: number)
	local p = state.placements[id]
	if not p then
		return { ok = false, message = "No such item" }
	end
	local ok, err = Clinic.canPlace(config, state, p.item, p.room, x, z, rot, id)
	if not ok then
		return { ok = false, message = err }
	end
	p.x, p.z, p.rot = x, z, rot
	return { ok = true }
end

function Clinic.remove(config, state, id: string)
	local p = state.placements[id]
	if not p then
		return { ok = false, message = "No such item" }
	end
	local item = config.catalog[p.item]
	if item.essential then
		local count = 0
		for _, other in state.placements do
			if other.item == p.item then
				count += 1
			end
		end
		if count <= 1 then
			return { ok = false, message = "Your clinic needs at least one " .. item.name }
		end
	end
	state.placements[id] = nil
	local refund = math.floor(item.price * config.refundRate)
	Clinic.earn(state, refund, "Sold " .. item.name)
	return { ok = true, refund = refund }
end

function Clinic.buyRoom(config, state, room: string)
	local def = config.rooms[room]
	if not def then
		return { ok = false, message = "Unknown room" }
	end
	if state.rooms[room] then
		return { ok = false, message = "Already yours" }
	end
	if state.level < (def.minLevel or 1) then
		return { ok = false, message = "Unlocks at level " .. def.minLevel }
	end
	if (state.debt or 0) > 0 then
		return { ok = false, message = "Pay off your bills first" }
	end
	if not Clinic.spend(state, def.price or 0, "Expanded: " .. room) then
		return { ok = false, message = "Not enough cash" }
	end
	-- the room is an empty shell: walls/floor go up, the player furnishes it (no instant rooms)
	state.rooms[room] = true
	return { ok = true }
end

function Clinic.setFinish(config, state, room: string, slot: string, finishId: string)
	if not state.rooms[room] then
		return { ok = false, message = "Not your room" }
	end
	if slot ~= "wall" and slot ~= "floor" then
		return { ok = false, message = "Bad slot" }
	end
	local finish = config.finishes[slot][finishId]
	if not finish then
		return { ok = false, message = "Unknown finish" }
	end
	if not Clinic.spend(state, finish.price, "Decor: " .. finishId) then
		return { ok = false, message = "Not enough cash" }
	end
	state.finishes[room] = state.finishes[room] or {}
	state.finishes[room][slot] = finishId
	return { ok = true }
end

-- Name validation (length/characters). Text filtering is done by the server glue (TextService).
function Clinic.validName(name: any): boolean
	return type(name) == "string" and #name >= 3 and #name <= 28 and name:match("^[%w%s'%-!&%.]+$") ~= nil
end

function Clinic.payDebt(state)
	local debt = state.debt or 0
	if debt <= 0 then
		return { ok = true }
	end
	local pay = math.min(debt, state.cash)
	state.cash -= pay
	state.debt = debt - pay
	ledger(state, "expense", "Paid bills", -pay)
	return { ok = true, remaining = state.debt }
end

return Clinic
