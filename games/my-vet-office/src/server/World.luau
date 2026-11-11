--[[
	World — the physical clinic on the server: plots, furniture built from saved placements,
	NPC customers walking with their pets (PathfindingService), animal movement, world sensing
	for AnimalBehavior, and replication of animal state as Attributes (clients animate locally).

	BUILT, UNTESTED: needs a Studio playtest (qa/playtest-plan in games/my-vet-office/qa/).

	Expected place layout (Blender shell + Studio markers, see games/my-vet-office/plan.md §Integration):
	  Workspace.Clinics.Plot<n>                 Model per player clinic
	    Markers/Entrance, ReceptionQueue, ReceptionDesk, Checkout, Exit, DeliveryDoor (Parts)
	    Markers/WaitingSeats/<Seat parts>
	    Rooms/<RoomName>/Origin                 grid origin (corner, +X/+Z into the room)
	    Rooms/<RoomName>/Door                   threshold part (animals hesitate here)
	    Rooms/<RoomName>/TableSpot              where the patient stands on the exam table
	    Rooms/<RoomName>/OwnerSpot              where the customer stands during the visit
	  ReplicatedStorage.Assets.Animals.<Breed>  rigged models (Blender export, Motor6D per bone)
	  ReplicatedStorage.Assets.Furniture.<Item> furniture models (Blender export)
	  ReplicatedStorage.Assets.Carrier          pet carrier model
]]

local CollectionService = game:GetService("CollectionService")
local PathfindingService = game:GetService("PathfindingService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local World = {}
World.__index = World

local ASSETS = ReplicatedStorage:WaitForChild("Assets")

-- Furniture item → interactable target name used by Procedures ("open" steps).
World.INTERACT_TARGET = {
	EquipmentCabinet = "EquipmentCabinet",
	MedCabinet = "MedCabinet",
	DrawerUnit = "Drawer",
	VaccineFridge = "Fridge",
	VetComputer = "VetComputer",
	InvoicePrinter = "InvoicePrinter",
	ReceptionCounter = "ReceptionDesk",
	Sink = "Sink",
	ExamTable = "ExamTable",
	PetScale = "PetScale",
	WaitingTV = "WaitingTV",
}

World.REACH = 7 -- studs: how close a player must be to use something

function World.new(logic)
	local self = setmetatable({}, World)
	self.logic = logic
	self.plots = {} -- ownerId -> plot Model
	self.freePlots = {}
	local folder = Workspace:WaitForChild("Clinics")
	for _, plot in folder:GetChildren() do
		table.insert(self.freePlots, plot)
	end
	table.sort(self.freePlots, function(a, b)
		return a.Name < b.Name
	end)
	self.npcs = {} -- [ownerId][apptId] = { customer, animal, carrier, path state }
	self.sounds = {} -- per-plot recent sound events { kind, position, t }
	return self
end

---------------------------------------------------------------------------------------------
-- Plots + furniture
---------------------------------------------------------------------------------------------
function World:claimPlot(ownerId: number)
	local plot = table.remove(self.freePlots, 1)
	if not plot then
		return nil
	end
	plot:SetAttribute("OwnerId", ownerId)
	self.plots[ownerId] = plot
	self.npcs[ownerId] = {}
	self.sounds[ownerId] = {}
	return plot
end

function World:releasePlot(ownerId: number)
	local plot = self.plots[ownerId]
	if not plot then
		return
	end
	for _, npc in self.npcs[ownerId] or {} do
		self:_destroyNpc(npc)
	end
	local furniture = plot:FindFirstChild("Furniture")
	if furniture then
		furniture:ClearAllChildren()
	end
	plot:SetAttribute("OwnerId", nil)
	self.plots[ownerId] = nil
	self.npcs[ownerId] = nil
	table.insert(self.freePlots, plot)
end

function World:roomCFrame(plot, room: string, x: number, z: number, w: number, d: number, rot: number): CFrame?
	local roomFolder = plot.Rooms:FindFirstChild(room)
	if not roomFolder then
		return nil
	end
	local origin = roomFolder.Origin.CFrame
	return origin * CFrame.new(x + w / 2, 0, z + d / 2) * CFrame.Angles(0, math.rad(rot), 0)
end

-- (Re)build all furniture from the clinic state. Called on load and after build actions.
function World:buildFurniture(ownerId: number)
	local plot = self.plots[ownerId]
	local clinic = self.logic.clinics[ownerId]
	if not plot or not clinic then
		return
	end
	local folder = plot:FindFirstChild("Furniture")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "Furniture"
		folder.Parent = plot
	end
	local existing = {}
	for _, model in folder:GetChildren() do
		existing[model.Name] = model
	end
	for id, p in clinic.state.placements do
		local item = self.logic.Config.catalog[p.item]
		local w, d = item.w, item.d
		if p.rot % 180 == 90 then
			w, d = d, w
		end
		local cf = self:roomCFrame(plot, p.room, p.x, p.z, w, d, p.rot)
		local model = existing[id]
		existing[id] = nil
		if not model then
			local template = ASSETS.Furniture:FindFirstChild(p.item)
			if not template then
				warn("[World] missing furniture asset " .. p.item .. " (Blender export not imported yet)")
				continue
			end
			model = template:Clone()
			model.Name = id
			model:SetAttribute("Item", p.item)
			model:SetAttribute("Room", p.room)
			local target = World.INTERACT_TARGET[p.item]
			if target then
				model:SetAttribute("Target", target)
				model:SetAttribute("Open", false)
				CollectionService:AddTag(model, "Interactable")
			end
			model.Parent = folder
		end
		if cf then
			model:PivotTo(cf)
		end
	end
	for _, stale in existing do
		stale:Destroy()
	end
end

-- Nearest interactable with this target in a room (or any room) within reach of a position.
function World:nearInteractable(ownerId: number, target: string, position: Vector3, room: string?)
	local plot = self.plots[ownerId]
	if not plot or not plot:FindFirstChild("Furniture") then
		return nil
	end
	for _, model in plot.Furniture:GetChildren() do
		if model:GetAttribute("Target") == target and (room == nil or model:GetAttribute("Room") == room) then
			if (model:GetPivot().Position - position).Magnitude <= World.REACH then
				return model
			end
		end
	end
	return nil
end

function World:setOpen(model: Model, open: boolean)
	model:SetAttribute("Open", open)
	model:SetAttribute("OpenedAt", os.clock())
end

---------------------------------------------------------------------------------------------
-- NPCs
---------------------------------------------------------------------------------------------
local function marker(plot, name: string): BasePart?
	return plot:FindFirstChild("Markers") and plot.Markers:FindFirstChild(name)
end

local SKIN_TONES = {
	Color3.fromRGB(255, 224, 189),
	Color3.fromRGB(234, 192, 134),
	Color3.fromRGB(198, 134, 66),
	Color3.fromRGB(141, 85, 36),
	Color3.fromRGB(92, 56, 31),
}
local CLOTHES = {
	Color3.fromRGB(70, 110, 160),
	Color3.fromRGB(180, 70, 80),
	Color3.fromRGB(90, 140, 100),
	Color3.fromRGB(230, 190, 90),
	Color3.fromRGB(120, 90, 160),
	Color3.fromRGB(60, 60, 70),
}

function World:_makeCustomer(appt, spawnCf: CFrame)
	local rng = Random.new(appt.id * 7919)
	local desc = Instance.new("HumanoidDescription")
	local skin = SKIN_TONES[rng:NextInteger(1, #SKIN_TONES)]
	desc.HeadColor, desc.LeftArmColor, desc.RightArmColor = skin, skin, skin
	desc.LeftLegColor, desc.RightLegColor, desc.TorsoColor = skin, skin, skin
	local ok, model = pcall(function()
		return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	end)
	if not ok then
		warn("[World] customer rig failed: " .. tostring(model))
		return nil
	end
	model.Name = "Customer_" .. appt.id
	local shirt = CLOTHES[rng:NextInteger(1, #CLOTHES)]
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") and (part.Name:find("Torso") or part.Name:find("Arm") or part.Name:find("Hand")) then
			part.Color = if part.Name:find("Hand") then skin else shirt
		end
	end
	model:SetAttribute("ApptId", appt.id)
	model:SetAttribute("CustomerName", appt.customer.name)
	model:PivotTo(spawnCf)
	return model
end

function World:_makeAnimal(appt, spawnCf: CFrame)
	local template = ASSETS.Animals:FindFirstChild(appt.patient.breed)
	if not template then
		warn("[World] missing animal asset " .. appt.patient.breed)
		return nil
	end
	local model = template:Clone()
	model.Name = "Animal_" .. appt.id
	local root = model:FindFirstChild("HumanoidRootPart")
	if not root then
		-- movement collider: invisible box at the body, Motor6D to the rig Root
		root = Instance.new("Part")
		root.Name = "HumanoidRootPart"
		root.Transparency = 1
		root.CanCollide = false
		local cf, size = model:GetBoundingBox()
		root.Size = Vector3.new(size.X, size.Y * 0.6, size.Z)
		root.CFrame = cf
		root.Parent = model
		local motor = Instance.new("Motor6D")
		motor.Name = "RootJoint"
		motor.Part0 = root
		motor.Part1 = model:FindFirstChild("Root") or model.PrimaryPart
		motor.C0 = root.CFrame:ToObjectSpace(motor.Part1.CFrame)
		motor.Parent = root
	end
	model.PrimaryPart = root
	local hum = model:FindFirstChildOfClass("Humanoid") or Instance.new("Humanoid")
	hum.Parent = model
	hum.RequiresNeck = false
	hum.BreakJointsOnDeath = false
	hum.HipHeight = root.Size.Y / 2
	hum.WalkSpeed = 0
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	model:SetAttribute("ApptId", appt.id)
	model:SetAttribute("Breed", appt.patient.breed)
	model:SetAttribute("Species", appt.patient.species)
	model:SetAttribute("PetName", appt.patient.name)
	model:SetAttribute("Coat", appt.patient.coat)
	model:SetAttribute("Size", appt.patient.size)
	model:PivotTo(spawnCf)
	CollectionService:AddTag(model, "Animal")
	return model
end

function World:spawnVisit(ownerId: number, appt)
	local plot = self.plots[ownerId]
	if not plot then
		return
	end
	local entrance = marker(plot, "Entrance")
	local spawnCf = (entrance and entrance.CFrame or plot:GetPivot()) * CFrame.new(0, 3, 6)
	local npc = { apptId = appt.id, path = nil, target = nil }
	npc.customer = self:_makeCustomer(appt, spawnCf)
	npc.animal = self:_makeAnimal(appt, spawnCf * CFrame.new(2, -1.5, 0))
	if appt.patient.species == "Cat" then
		local carrierT = ASSETS:FindFirstChild("Carrier")
		if carrierT and npc.customer then
			npc.carrier = carrierT:Clone()
			npc.carrier.Name = "Carrier_" .. appt.id
			local hand = npc.customer:FindFirstChild("RightHand")
			if hand then
				npc.carrier:PivotTo(hand.CFrame * CFrame.new(0, -1, 0))
				local weld = Instance.new("WeldConstraint")
				weld.Part0 = hand
				weld.Part1 = npc.carrier.PrimaryPart
				weld.Parent = npc.carrier
			end
			npc.carrier.Parent = plot
		end
	end
	local npcFolder = plot:FindFirstChild("NPCs") or Instance.new("Folder")
	npcFolder.Name = "NPCs"
	npcFolder.Parent = plot
	if npc.customer then
		npc.customer.Parent = npcFolder
	end
	if npc.animal then
		npc.animal.Parent = npcFolder
		for _, part in npc.animal:GetDescendants() do
			if part:IsA("BasePart") then
				part:SetNetworkOwner(nil) -- server-owned: multiplayer-consistent patient
			end
		end
	end
	self.npcs[ownerId][appt.id] = npc
	return npc
end

function World:_destroyNpc(npc)
	for _, key in { "customer", "animal", "carrier" } do
		if npc[key] then
			npc[key]:Destroy()
		end
	end
end

-- Walk a humanoid to a position with pathfinding; re-paths if blocked. Non-blocking.
function World:walkTo(npc, who: string, goal: Vector3, onArrive: (() -> ())?)
	local model = npc[who]
	local hum = model and model:FindFirstChildOfClass("Humanoid")
	if not hum or not model.PrimaryPart then
		if onArrive then
			onArrive()
		end
		return
	end
	npc.walkToken = (npc.walkToken or 0) + 1
	local token = npc.walkToken
	task.spawn(function()
		local path = PathfindingService:CreatePath({ AgentRadius = 1.6, AgentHeight = 5, AgentCanJump = false })
		local ok = pcall(function()
			path:ComputeAsync(model.PrimaryPart.Position, goal)
		end)
		if not ok or path.Status ~= Enum.PathStatus.Success then
			hum:MoveTo(goal)
			hum.MoveToFinished:Wait()
		else
			path.Blocked:Connect(function()
				if npc.walkToken == token then
					self:walkTo(npc, who, goal, onArrive)
				end
			end)
			hum.WalkSpeed = 9
			for _, wp in path:GetWaypoints() do
				if npc.walkToken ~= token or not model.Parent then
					return
				end
				hum:MoveTo(wp.Position)
				local reached = hum.MoveToFinished:Wait()
				if not reached then
					break
				end
			end
		end
		if npc.walkToken == token and onArrive then
			onArrive()
		end
	end)
end

---------------------------------------------------------------------------------------------
-- Visit choreography: phase → where people go. Called whenever an appointment phase changes.
---------------------------------------------------------------------------------------------
function World:onPhase(ownerId: number, appt)
	local plot = self.plots[ownerId]
	local npc = self.npcs[ownerId] and self.npcs[ownerId][appt.id]
	if not plot or not npc then
		return
	end
	local phase = appt.phase
	if npc.lastPhase == phase then
		return
	end
	npc.lastPhase = phase
	local logic = self.logic
	if phase == "Arriving" then
		local q = marker(plot, "ReceptionQueue")
		if q then
			self:walkTo(npc, "customer", q.Position, function()
				logic:reachReception(ownerId, appt.id)
			end)
		end
	elseif phase == "Waiting" then
		local seats = plot.Markers:FindFirstChild("WaitingSeats")
		local seat = nil
		if seats then
			for _, s in seats:GetChildren() do
				if s:IsA("Seat") and not s.Occupant and not s:GetAttribute("Reserved") then
					seat = s
					break
				end
			end
		end
		if seat then
			seat:SetAttribute("Reserved", appt.id)
			npc.seat = seat
			self:walkTo(npc, "customer", seat.Position, function()
				local hum = npc.customer and npc.customer:FindFirstChildOfClass("Humanoid")
				if hum then
					seat:Sit(hum)
				end
			end)
		end
	elseif phase == "Called" or phase == "ToRoom" then
		if npc.seat then
			npc.seat:SetAttribute("Reserved", nil)
			local hum = npc.customer and npc.customer:FindFirstChildOfClass("Humanoid")
			if hum then
				hum.Sit = false
			end
			npc.seat = nil
		end
		local room = plot.Rooms:FindFirstChild(appt.room)
		if room then
			self:walkTo(npc, "customer", room.OwnerSpot.Position)
		end
	elseif phase == "OnTable" then
		local room = plot.Rooms:FindFirstChild(appt.room)
		if room and npc.animal then
			-- smooth lift onto the table (no teleport): tween the pivot over 0.8 s on clients via
			-- attribute; server moves the collider once the animation has played
			npc.animal:SetAttribute("TableCFrame", room.TableSpot.CFrame)
			task.delay(0.8, function()
				if npc.animal and npc.animal.Parent then
					npc.animal:PivotTo(room.TableSpot.CFrame)
					npc.animal.PrimaryPart.Anchored = true
				end
			end)
		end
	elseif phase == "Checkout" then
		if npc.animal and npc.animal.PrimaryPart then
			npc.animal.PrimaryPart.Anchored = false
			npc.animal:SetAttribute("TableCFrame", nil)
			local room = plot.Rooms:FindFirstChild(appt.room)
			if room then
				npc.animal:PivotTo(room.OwnerSpot.CFrame * CFrame.new(2, 0, 0))
			end
		end
		local c = marker(plot, "Checkout")
		if c then
			self:walkTo(npc, "customer", c.Position)
		end
	elseif phase == "Leaving" or phase == "WalkedOut" then
		if npc.seat then
			npc.seat:SetAttribute("Reserved", nil)
		end
		local hum = npc.customer and npc.customer:FindFirstChildOfClass("Humanoid")
		if hum then
			hum.Sit = false
		end
		local exit = marker(plot, "Exit")
		if exit then
			self:walkTo(npc, "customer", exit.Position, function()
				logic:customerLeft(ownerId, appt.id)
				self:_destroyNpc(npc)
				self.npcs[ownerId][appt.id] = nil
			end)
		end
	end
end

---------------------------------------------------------------------------------------------
-- Sensing + animal movement + replication (5 Hz, one loop for every animal)
---------------------------------------------------------------------------------------------
function World:soundEvent(ownerId: number, kind: string, position: Vector3)
	local list = self.sounds[ownerId]
	if list then
		table.insert(list, { kind = kind, position = position, t = os.clock() })
	end
end

local function charRoot(userId: number?): BasePart?
	local player = userId and Players:GetPlayerByUserId(userId)
	local char = player and player.Character
	return char and char:FindFirstChild("HumanoidRootPart")
end

function World:leaderPart(_ownerId: number, appt, npc): BasePart?
	if (appt.phase == "Called" or appt.phase == "ToRoom") and appt.claimedBy then
		return charRoot(appt.claimedBy)
	end
	return npc.customer and npc.customer:FindFirstChild("HumanoidRootPart")
end

function World:sense(ownerId: number, appt)
	local npc = self.npcs[ownerId] and self.npcs[ownerId][appt.id]
	if not npc or not npc.animal or not npc.animal.PrimaryPart then
		return {}
	end
	local pos = npc.animal.PrimaryPart.Position
	local ctx = {}
	local leader = self:leaderPart(ownerId, appt, npc)
	if leader then
		ctx.leaderDist = (leader.Position - pos).Magnitude
		ctx.leaderMoving = leader.AssemblyLinearVelocity.Magnitude > 1
		local hum = leader.Parent and leader.Parent:FindFirstChildOfClass("Humanoid")
		ctx.leaderSeated = hum ~= nil and hum.Sit
	end
	-- nearest point of interest: scent spots (tagged), other animals, people
	local best, bestD = nil, 20
	for _, scent in CollectionService:GetTagged("Scent") do
		local d = (scent.Position - pos).Magnitude
		if d < bestD then
			best, bestD = { id = scent:GetFullName(), kind = "Scent", dist = d }, d
		end
	end
	for _, other in CollectionService:GetTagged("Animal") do
		if other ~= npc.animal and other.PrimaryPart then
			local d = (other.PrimaryPart.Position - pos).Magnitude
			if d < bestD then
				best, bestD = { id = other.Name, kind = "Animal", dist = d }, d
			end
		end
	end
	ctx.poi = best
	-- recent sounds within earshot
	local now = os.clock()
	for _, s in self.sounds[ownerId] or {} do
		if now - s.t < 0.4 and (s.position - pos).Magnitude < 40 then
			ctx.sound = { kind = s.kind, dist = (s.position - pos).Magnitude }
		end
	end
	-- exam-room threshold
	if appt.room and (appt.phase == "ToRoom") then
		local room = self.plots[ownerId].Rooms:FindFirstChild(appt.room)
		if room and room:FindFirstChild("Door") then
			local d = (room.Door.Position - pos).Magnitude
			ctx.atThreshold = d < 5
			if d < 3 and appt.anim and appt.anim.state ~= "Hesitate" then
				self.logic:arriveInRoom(ownerId, appt.id)
			end
		end
	end
	return ctx
end

local ATTRS = {
	"tailWag",
	"tailHeight",
	"earPose",
	"tremble",
	"pant",
	"breathRate",
	"blinkInterval",
	"limp",
	"headHeight",
	"purr",
	"sleepy",
}

local function round2(x: number): number
	return math.floor(x * 100 + 0.5) / 100
end

function World:applyAnimals(ownerId: number)
	local clinic = self.logic.clinics[ownerId]
	if not clinic then
		return
	end
	local now = os.clock()
	local list = self.sounds[ownerId]
	if list then
		for i = #list, 1, -1 do
			if now - list[i].t > 1 then
				table.remove(list, i)
			end
		end
	end
	for id, appt in clinic.appts do
		local npc = self.npcs[ownerId] and self.npcs[ownerId][id]
		local out = appt.anim
		if npc and npc.animal and out then
			local model = npc.animal
			model:SetAttribute("State", out.state)
			model:SetAttribute("PoseFrom", out.from)
			model:SetAttribute("PoseTo", out.to)
			model:SetAttribute("PoseAlpha", round2(out.alpha))
			model:SetAttribute("Gait", out.gait)
			model:SetAttribute("LookAt", out.lookAt and tostring(out.lookAt) or nil)
			if out.gesture then
				model:SetAttribute("Gesture", out.gesture)
				model:SetAttribute("GestureId", (model:GetAttribute("GestureId") or 0) + 1)
			end
			if out.reaction then
				model:SetAttribute("Reaction", out.reaction)
				model:SetAttribute("ReactionId", (model:GetAttribute("ReactionId") or 0) + 1)
			end
			model:SetAttribute("Vocal", out.vocal)
			if out.vocal == "Bark" and model.PrimaryPart then
				self:soundEvent(ownerId, "Bark", model.PrimaryPart.Position)
			end
			for _, key in ATTRS do
				model:SetAttribute(key, round2(out.params[key]))
			end
			local bandages = {}
			for _, b in appt.bandages do
				table.insert(bandages, b.leg)
			end
			model:SetAttribute("Bandages", table.concat(bandages, ","))
			model:SetAttribute("Focused", appt.running ~= nil)
			-- movement
			local hum = model:FindFirstChildOfClass("Humanoid")
			local leader = self:leaderPart(ownerId, appt, npc)
			if hum and model.PrimaryPart and not model.PrimaryPart.Anchored then
				hum.WalkSpeed = out.speed or 0
				if out.move == "follow" and leader then
					-- heel position: beside and slightly behind the leader
					local heel = leader.CFrame * CFrame.new(2.2, 0, 1.5)
					if (heel.Position - model.PrimaryPart.Position).Magnitude > out.heel * 0.6 then
						hum:MoveTo(heel.Position)
					end
				elseif out.move == "behindOwner" and npc.customer and npc.customer.PrimaryPart then
					hum.WalkSpeed = 4
					hum:MoveTo((npc.customer.PrimaryPart.CFrame * CFrame.new(0, 0, 2)).Position)
				else
					hum:MoveTo(model.PrimaryPart.Position)
				end
			end
		end
	end
end

-- Server-measured distance from a player's character to their patient.
function World:vetDistance(ownerId: number, userId: number, apptId: number): number
	local npc = self.npcs[ownerId] and self.npcs[ownerId][apptId]
	local root = charRoot(userId)
	if not npc or not npc.animal or not npc.animal.PrimaryPart or not root then
		return math.huge
	end
	return (npc.animal.PrimaryPart.Position - root.Position).Magnitude
end

function World:playerPosition(userId: number): Vector3?
	local root = charRoot(userId)
	return root and root.Position
end

-- Which clinic plot a player is standing in (for joining friends' clinics).
function World:plotOwnerAt(position: Vector3): number?
	for ownerId, plot in self.plots do
		local cf, size = plot:GetBoundingBox()
		local p = cf:PointToObjectSpace(position)
		if math.abs(p.X) <= size.X / 2 and math.abs(p.Z) <= size.Z / 2 then
			return ownerId
		end
	end
	return nil
end

return World
