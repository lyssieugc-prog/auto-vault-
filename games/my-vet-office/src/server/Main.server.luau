--[[
	My Vet Office — server entry. Wires Roblox services, remotes and the physical World to the
	pure GameLogic. BUILT, UNTESTED outside Studio: verify with games/my-vet-office/qa/playtest-plan.md.

	Server-authoritative: remotes carry only ids/choices/pointer samples; distances, reach,
	money, stock, xp, ratings and diagnoses are all decided here.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local TextService = game:GetService("TextService")

local SharedVault = ReplicatedStorage:WaitForChild("Vault"):WaitForChild("Shared")
local VaultServer = ServerScriptService:WaitForChild("VaultServer")
local GameShared = ReplicatedStorage:WaitForChild("GameShared")

local Config = require(GameShared:WaitForChild("Config"))
local GameLogic = require(GameShared:WaitForChild("GameLogic"))
local DataService = require(SharedVault.DataService)
local Guard = require(SharedVault.Guard)
local Tutorial = require(SharedVault.Tutorial)
local DataStoreAdapter = require(VaultServer.DataStoreAdapter)
local Net = require(VaultServer.Net)
local World = require(script.Parent:WaitForChild("World"))

local Modules = { Tutorial = Tutorial }
local random = Random.new()
local logic = GameLogic.new(Config, Modules, {
	now = os.clock,
	rng = function()
		return random:NextNumber()
	end,
})
local world = World.new(logic)

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

-- Which clinic each player is currently working in (their own by default).
local workingIn = {} -- userId -> ownerId

Net.event("State")
Net.event("Toast")
Net.event("ProcedureResult")
Net.event("Invoice")

local function clinicOf(player: Player): number
	return workingIn[player.UserId] or player.UserId
end

local function membersOf(ownerId: number)
	local list = {}
	for _, p in Players:GetPlayers() do
		if clinicOf(p) == ownerId then
			table.insert(list, p)
		end
	end
	return list
end

local dirty = {}
local function markDirty(ownerId: number)
	dirty[ownerId] = true
end

local function pushState(ownerId: number)
	for _, p in membersOf(ownerId) do
		local snap = logic:snapshot(ownerId, p.UserId)
		if snap then
			Net.fire(p, "State", snap)
		end
	end
end

local function toast(ownerId: number, kind: string, text: string)
	for _, p in membersOf(ownerId) do
		Net.fire(p, "Toast", kind, text)
	end
end

---------------------------------------------------------------------------------------------
-- Players
---------------------------------------------------------------------------------------------
local function onPlayerAdded(player: Player)
	local profile, err = data:load(player.UserId)
	if not profile then
		player:Kick("Your clinic could not be loaded (" .. tostring(err) .. "). Please rejoin.")
		return
	end
	if not player.Parent then
		data:release(player.UserId)
		return
	end
	logic:loadPlayer(player.UserId, profile)
	if not world:claimPlot(player.UserId) then
		warn("[World] no free plot for " .. player.Name)
	end
	world:buildFurniture(player.UserId)
	markDirty(player.UserId)
end

local function saveAndRelease(player: Player)
	local uid = player.UserId
	-- leave any clinic they were helping in
	local helping = workingIn[uid]
	if helping then
		logic:leave(helping, uid)
		markDirty(helping)
	end
	workingIn[uid] = nil
	-- friends working in this player's clinic go back to their own
	for other, ownerId in workingIn do
		if ownerId == uid then
			workingIn[other] = nil
		end
	end
	local profile = data:get(uid)
	if profile then
		logic:writeProfile(uid, profile)
		data:release(uid)
	end
	world:releasePlot(uid)
	logic:unloadPlayer(uid)
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

---------------------------------------------------------------------------------------------
-- Remotes. Each handler: validate args (Guard) → server checks (reach/distance) → logic.
---------------------------------------------------------------------------------------------
local function reply(player: Player, ownerId: number, r)
	if r and r.message and not r.ok then
		Net.fire(player, "Toast", "Info", r.message)
	end
	markDirty(ownerId)
	return r
end

local function apptArg(id): boolean
	return Guard.integer(id, 1, 1e9)
end

-- Reach check for "open"/"take": the player must stand at the right furniture in the room.
local function nearTarget(player: Player, ownerId: number, target: string, room: string?): Model?
	local pos = world:playerPosition(player.UserId)
	return pos and world:nearInteractable(ownerId, target, pos, room)
end

Net.on("CheckIn", function(player, apptId)
	if not apptArg(apptId) then
		return
	end
	local ownerId = clinicOf(player)
	if not nearTarget(player, ownerId, "VetComputer") and not nearTarget(player, ownerId, "ReceptionDesk") then
		Net.fire(player, "Toast", "Info", "Use the reception computer")
		return
	end
	reply(player, ownerId, logic:checkIn(ownerId, player.UserId, apptId))
end, { rate = 2, burst = 4 })

Net.on("CallPatient", function(player, apptId, room)
	if not apptArg(apptId) or not Guard.string(room, 20) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:callPatient(ownerId, player.UserId, apptId, room))
end, { rate = 2, burst = 4 })

Net.on("OpenCarrier", function(player, apptId)
	if not apptArg(apptId) then
		return
	end
	local ownerId = clinicOf(player)
	if world:vetDistance(ownerId, player.UserId, apptId) > World.REACH then
		return
	end
	reply(player, ownerId, logic:openCarrier(ownerId, player.UserId, apptId))
end, { rate = 2, burst = 3 })

Net.on("HelpOntoTable", function(player, apptId, step)
	if not apptArg(apptId) or not Guard.oneOf(step, { "pickUp", "placeOnTable", "liftFront", "liftBack" }) then
		return
	end
	local ownerId = clinicOf(player)
	if world:vetDistance(ownerId, player.UserId, apptId) > World.REACH then
		Net.fire(player, "Toast", "Info", "Get closer to the patient")
		return
	end
	reply(player, ownerId, logic:helpOntoTable(ownerId, player.UserId, apptId, step))
end, { rate = 3, burst = 4 })

Net.on("Comfort", function(player, apptId, kind)
	if not apptArg(apptId) or not Guard.oneOf(kind, { "Pet", "Comfort", "Treat", "Brush" }) then
		return
	end
	local ownerId = clinicOf(player)
	if world:vetDistance(ownerId, player.UserId, apptId) > World.REACH then
		return
	end
	local r = logic:comfort(ownerId, player.UserId, apptId, kind)
	if r.ok then
		Net.fire(player, "ProcedureResult", apptId, { event = "Reaction", reaction = r.reaction })
	end
end, { rate = 4, burst = 6 })

Net.on("RequestPose", function(player, apptId, pose)
	if not apptArg(apptId) or not Guard.oneOf(pose, GameLogic.EXAM_POSES) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:requestPose(ownerId, player.UserId, apptId, pose))
end, { rate = 2, burst = 3 })

Net.on("BeginExam", function(player, apptId, examId)
	if not apptArg(apptId) or not Guard.string(examId, 20) then
		return
	end
	local ownerId = clinicOf(player)
	local r = reply(player, ownerId, logic:beginExam(ownerId, player.UserId, apptId, examId))
	Net.fire(player, "ProcedureResult", apptId, r)
end, { rate = 2, burst = 3 })

Net.on("BeginTreatment", function(player, apptId, treatmentId)
	if not apptArg(apptId) or not Guard.string(treatmentId, 20) then
		return
	end
	local ownerId = clinicOf(player)
	local r = reply(player, ownerId, logic:beginTreatment(ownerId, player.UserId, apptId, treatmentId))
	Net.fire(player, "ProcedureResult", apptId, r)
end, { rate = 2, burst = 3 })

local PROCEDURE_ACTIONS = {
	"tick",
	"open",
	"take",
	"requestPose",
	"place",
	"release",
	"scan",
	"finishScan",
	"stroke",
	"wrap",
	"pull",
	"dose",
	"record",
}

local function cleanPoint(p)
	if type(p) ~= "table" then
		return nil
	end
	if not Guard.number(p.u, -0.2, 1.2) or not Guard.number(p.v, -0.2, 1.2) then
		return nil
	end
	if p.side ~= nil and not Guard.oneOf(p.side, { "L", "R", "C" }) then
		return nil
	end
	return { u = p.u, v = p.v, side = p.side }
end

-- Copy only the fields each action may carry (never pass client tables through raw).
local function cleanPayload(action: string, payload)
	if action == "open" then
		return type(payload) == "table" and Guard.string(payload.target, 24) and { target = payload.target } or nil
	elseif action == "take" then
		return type(payload) == "table" and Guard.string(payload.tool, 24) and { tool = payload.tool } or nil
	elseif action == "place" or action == "scan" then
		return cleanPoint(payload)
	elseif action == "stroke" then
		if type(payload) ~= "table" or type(payload.points) ~= "table" or #payload.points > 32 then
			return nil
		end
		local pts = {}
		for i = 1, #payload.points do
			local p = cleanPoint(payload.points[i])
			if p then
				table.insert(pts, p)
			end
		end
		return { points = pts }
	elseif action == "wrap" then
		return type(payload) == "table" and Guard.number(payload.delta, -10, 10) and { delta = payload.delta } or nil
	elseif action == "pull" then
		return type(payload) == "table"
				and Guard.number(payload.distance, 0, 5)
				and Guard.number(payload.dt, 0.01, 1)
				and { distance = payload.distance, dt = payload.dt }
			or nil
	elseif action == "dose" then
		return type(payload) == "table" and Guard.number(payload.value, 0, 1000) and { value = payload.value } or nil
	end
	return nil
end

Net.on("Procedure", function(player, apptId, action, payload)
	if not apptArg(apptId) or not Guard.oneOf(action, PROCEDURE_ACTIONS) then
		return
	end
	local ownerId = clinicOf(player)
	local clinic = logic.clinics[ownerId]
	local appt = clinic and clinic.appts[apptId]
	if not appt or not appt.running then
		return
	end
	local clean = cleanPayload(action, payload)
	-- physical reach: opening a cabinet means standing at THAT cabinet in this exam room
	if action == "open" then
		local model = clean and nearTarget(player, ownerId, clean.target, appt.room)
		if not model then
			Net.fire(
				player,
				"ProcedureResult",
				apptId,
				{ ok = false, message = "Walk over to the " .. tostring(clean and clean.target) }
			)
			return
		end
		world:setOpen(model, true)
		task.delay(6, function()
			world:setOpen(model, false)
		end)
	elseif action == "take" and clean then
		player:SetAttribute("HeldTool", clean.tool)
	end
	local dist = world:vetDistance(ownerId, player.UserId, apptId)
	local r = logic:procedureInput(ownerId, player.UserId, apptId, action, clean, dist)
	if r.done then
		player:SetAttribute("HeldTool", nil)
	end
	-- don't send hidden case data back: results carry only what the player measured/found
	Net.fire(player, "ProcedureResult", apptId, {
		ok = r.ok,
		event = r.event,
		message = r.message,
		step = r.step,
		nextStep = r.nextStep,
		kind = r.kind,
		progress = r.progress,
		reading = r.reading,
		discovered = r.discovered and { id = r.discovered.id, note = r.discovered.note } or nil,
		reaction = r.reaction,
		requestedPose = r.requestedPose,
		summary = r.summary,
		relief = r.relief,
		done = r.done,
	})
	if r.done or r.event == "PulledAway" then
		markDirty(ownerId)
	end
end, { rate = 12, burst = 20 })

Net.on("CancelProcedure", function(player, apptId)
	if not apptArg(apptId) then
		return
	end
	local ownerId = clinicOf(player)
	player:SetAttribute("HeldTool", nil)
	reply(player, ownerId, logic:cancelProcedure(ownerId, player.UserId, apptId))
end, { rate = 2, burst = 3 })

Net.on("Diagnose", function(player, apptId, diagnosisId)
	if not apptArg(apptId) or not Guard.string(diagnosisId, 24) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:diagnose(ownerId, player.UserId, apptId, diagnosisId))
end, { rate = 1, burst = 2 })

Net.on("FinishVisit", function(player, apptId)
	if not apptArg(apptId) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:finishVisit(ownerId, player.UserId, apptId))
end, { rate = 1, burst = 2 })

Net.on("PrintInvoice", function(player, apptId)
	if not apptArg(apptId) then
		return
	end
	local ownerId = clinicOf(player)
	if not nearTarget(player, ownerId, "InvoicePrinter") and not nearTarget(player, ownerId, "ReceptionDesk") then
		Net.fire(player, "Toast", "Info", "Print the invoice at reception")
		return
	end
	local r = reply(player, ownerId, logic:pay(ownerId, player.UserId, apptId))
	if r.ok then
		for _, p in membersOf(ownerId) do
			Net.fire(p, "Invoice", apptId, r.bill)
		end
		for _, lvl in r.levelsGained do
			toast(ownerId, "LevelUp", "Clinic level " .. lvl .. "!")
		end
	end
end, { rate = 1, burst = 2 })

Net.on("Order", function(player, item, qty)
	if not Guard.string(item, 24) or not Guard.integer(qty, 1, 50) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:order(ownerId, player.UserId, item, qty))
end, { rate = 2, burst = 4 })

Net.on("Shelve", function(player, boxId)
	if not Guard.integer(boxId, 1, 1e9) then
		return
	end
	local ownerId = clinicOf(player)
	-- must be carrying that box (client picked it up at the delivery door) and stand at a cabinet
	if player:GetAttribute("CarryingBox") ~= boxId then
		Net.fire(player, "Toast", "Info", "Pick up the delivery box first")
		return
	end
	if not nearTarget(player, ownerId, "MedCabinet") and not nearTarget(player, ownerId, "Drawer") then
		Net.fire(player, "Toast", "Info", "Carry it to a cabinet")
		return
	end
	player:SetAttribute("CarryingBox", nil)
	reply(player, ownerId, logic:shelve(ownerId, player.UserId, boxId))
end, { rate = 2, burst = 4 })

Net.on("PickUpBox", function(player, boxId)
	if not Guard.integer(boxId, 1, 1e9) then
		return
	end
	local ownerId = clinicOf(player)
	local clinic = logic.clinics[ownerId]
	if not clinic or not GameLogic.Modules.Clinic.can(logic:roleOf(ownerId, player.UserId), "restock") then
		return
	end
	for _, box in clinic.state.deliveries do
		if box.id == boxId then
			player:SetAttribute("CarryingBox", boxId)
			return
		end
	end
end, { rate = 2, burst = 4 })

local function rebuildAfter(player: Player, r)
	local ownerId = clinicOf(player)
	if r.ok then
		world:buildFurniture(ownerId)
	end
	reply(player, ownerId, r)
end

Net.on("Place", function(player, itemId, room, x, z, rot)
	if not Guard.string(itemId, 24) or not Guard.string(room, 20) then
		return
	end
	if not Guard.integer(x, 0, 200) or not Guard.integer(z, 0, 200) or not Guard.integer(rot, 0, 270) then
		return
	end
	rebuildAfter(player, logic:place(clinicOf(player), player.UserId, itemId, room, x, z, rot))
end, { rate = 3, burst = 6 })

Net.on("Move", function(player, id, x, z, rot)
	if
		not Guard.string(id, 12)
		or not Guard.integer(x, 0, 200)
		or not Guard.integer(z, 0, 200)
		or not Guard.integer(rot, 0, 270)
	then
		return
	end
	rebuildAfter(player, logic:move(clinicOf(player), player.UserId, id, x, z, rot))
end, { rate = 4, burst = 8 })

Net.on("Remove", function(player, id)
	if not Guard.string(id, 12) then
		return
	end
	rebuildAfter(player, logic:remove(clinicOf(player), player.UserId, id))
end, { rate = 2, burst = 4 })

Net.on("BuyRoom", function(player, room)
	if not Guard.string(room, 20) then
		return
	end
	rebuildAfter(player, logic:buyRoom(clinicOf(player), player.UserId, room))
end, { rate = 1, burst = 2 })

Net.on("SetFinish", function(player, room, slot, finishId)
	if not Guard.string(room, 20) or not Guard.oneOf(slot, { "wall", "floor" }) or not Guard.string(finishId, 24) then
		return
	end
	rebuildAfter(player, logic:setFinish(clinicOf(player), player.UserId, room, slot, finishId))
end, { rate = 2, burst = 4 })

Net.on("Rename", function(player, name)
	if not Guard.string(name, 28) then
		return
	end
	local ok, filtered = pcall(function()
		local result = TextService:FilterStringAsync(name, player.UserId)
		return result:GetNonChatStringForBroadcastAsync()
	end)
	if not ok then
		Net.fire(player, "Toast", "Info", "Couldn't check that name — try again")
		return
	end
	local ownerId = clinicOf(player)
	local r = reply(player, ownerId, logic:rename(ownerId, player.UserId, filtered))
	if r.ok and world.plots[ownerId] then
		world.plots[ownerId]:SetAttribute("ClinicName", filtered)
	end
end, { rate = 0.2, burst = 2 })

Net.on("Hire", function(player, role)
	if not Guard.string(role, 20) then
		return
	end
	local ownerId = clinicOf(player)
	reply(player, ownerId, logic:hire(ownerId, player.UserId, role))
end, { rate = 1, burst = 2 })

-- Multiplayer: owners invite friends; invitees accept to work in that clinic.
local invites = {} -- [inviteeId] = ownerId
Net.on("Invite", function(player, targetId)
	if not Guard.integer(targetId, 1, 1e12) then
		return
	end
	local target = Players:GetPlayerByUserId(targetId)
	if not target or clinicOf(player) ~= player.UserId then
		return
	end
	invites[targetId] = player.UserId
	Net.fire(target, "Toast", "Invite", player.DisplayName .. " invited you to work at their clinic")
end, { rate = 1, burst = 3 })

Net.on("AcceptInvite", function(player, ownerId)
	if not Guard.integer(ownerId, 1, 1e12) or invites[player.UserId] ~= ownerId then
		return
	end
	invites[player.UserId] = nil
	local r = logic:join(ownerId, player.UserId)
	if r.ok then
		workingIn[player.UserId] = ownerId
		markDirty(ownerId)
		markDirty(player.UserId)
	end
end, { rate = 1, burst = 2 })

Net.on("LeaveClinic", function(player)
	local ownerId = workingIn[player.UserId]
	if ownerId then
		logic:leave(ownerId, player.UserId)
		workingIn[player.UserId] = nil
		markDirty(ownerId)
		markDirty(player.UserId)
	end
end, { rate = 1, burst = 2 })

Net.on("SetRole", function(player, targetId, role)
	if not Guard.integer(targetId, 1, 1e12) or not Guard.string(role, 20) then
		return
	end
	reply(player, player.UserId, logic:setRole(player.UserId, player.UserId, targetId, role))
end, { rate = 1, burst = 3 })

---------------------------------------------------------------------------------------------
-- Loops
---------------------------------------------------------------------------------------------
local clinicAcc, animalAcc, pushAcc = 0, 0, 0
RunService.Heartbeat:Connect(function(dt)
	clinicAcc += dt
	animalAcc += dt
	pushAcc += dt
	if animalAcc >= 0.2 then -- 5 Hz animal brains, one loop for every animal
		local step = animalAcc
		animalAcc = 0
		for ownerId in logic.clinics do
			logic:tickAnimals(ownerId, step, function(appt)
				return world:sense(ownerId, appt)
			end)
			world:applyAnimals(ownerId)
		end
	end
	if clinicAcc >= 1 then
		local step = clinicAcc
		clinicAcc = 0
		for ownerId, clinic in logic.clinics do
			for _, e in logic:tick(ownerId, step) do
				if e.kind == "Arrived" then
					world:spawnVisit(ownerId, clinic.appts[e.id])
					toast(
						ownerId,
						if e.emergency then "Emergency" else "Arrival",
						if e.emergency then "Emergency patient arriving!" else "A new patient has arrived"
					)
				elseif e.kind == "Impatient" then
					toast(ownerId, "Impatient", "A customer is getting impatient")
				elseif e.kind == "WalkedOut" then
					toast(ownerId, "WalkedOut", "A customer gave up waiting and left")
				elseif e.kind == "DayEnded" then
					toast(ownerId, "Day", string.format("Day over — bills paid: %d", e.result.total))
				end
				markDirty(ownerId)
			end
			for _, appt in clinic.appts do
				world:onPhase(ownerId, appt)
			end
		end
	end
	if pushAcc >= 0.5 then
		pushAcc = 0
		for ownerId in dirty do
			dirty[ownerId] = nil
			pushState(ownerId)
		end
	end
end)
