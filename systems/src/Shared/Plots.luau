--[[
	Plots — base ownership and plot assignment.

	local plots = Plots.new({ count = 8 })
	local index = plots:claim(userId)      -- lowest free plot, idempotent per player
	plots:ownerOf(index); plots:plotOf(userId)
	plots:release(userId)                  -- on PlayerRemoving
	plots:onChanged(function(index, ownerId) end) -- ownerId nil when released

	Physical plot Models live in Workspace.Plots.Plot1..N (Blender-authored); the game script maps
	index -> model. This module only owns the assignment logic.
]]

local Plots = {}
Plots.__index = Plots

function Plots.new(config)
	assert(
		type(config) == "table" and type(config.count) == "number" and config.count >= 1,
		"Plots.new: count required"
	)
	local self = setmetatable({}, Plots)
	self.count = config.count
	self.owners = {} -- [index] = userId
	self.byUser = {} -- [userId] = index
	self.listeners = {}
	return self
end

function Plots:onChanged(callback): () -> ()
	table.insert(self.listeners, callback)
	return function()
		local i = table.find(self.listeners, callback)
		if i then
			table.remove(self.listeners, i)
		end
	end
end

function Plots:_emit(index: number, ownerId)
	for _, listener in self.listeners do
		listener(index, ownerId)
	end
end

-- Claims a plot. preferred = index to try first (e.g. friend's neighbour). Returns index or nil.
function Plots:claim(userId, preferred: number?): number?
	local existing = self.byUser[userId]
	if existing then
		return existing
	end
	local choice = nil
	if preferred and preferred >= 1 and preferred <= self.count and self.owners[preferred] == nil then
		choice = preferred
	else
		for i = 1, self.count do
			if self.owners[i] == nil then
				choice = i
				break
			end
		end
	end
	if not choice then
		return nil
	end
	self.owners[choice] = userId
	self.byUser[userId] = choice
	self:_emit(choice, userId)
	return choice
end

function Plots:release(userId): number?
	local index = self.byUser[userId]
	if not index then
		return nil
	end
	self.byUser[userId] = nil
	self.owners[index] = nil
	self:_emit(index, nil)
	return index
end

function Plots:ownerOf(index: number)
	return self.owners[index]
end

function Plots:plotOf(userId): number?
	return self.byUser[userId]
end

function Plots:freeCount(): number
	local used = 0
	for _ in self.byUser do
		used += 1
	end
	return self.count - used
end

-- True if the user owns the plot (server-side check before any plot interaction).
function Plots:isOwner(userId, index: number): boolean
	return self.owners[index] == userId
end

return Plots
