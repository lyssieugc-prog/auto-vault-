--[[
	PoseGraph — smooth, never-teleporting pose transitions. Pure.

	Poses are nodes; edges are animated transitions with a duration. Requesting a pose that is
	not adjacent routes through the graph (Stand → LieLateral goes Stand → Sit → LieSternal →
	LieLateral), so an animal on the exam table always moves through believable intermediate
	poses. While a transition plays, `alpha` runs 0→1 and the client cross-fades the two pose
	tracks with it; a new request mid-transition finishes the current edge first (no snapping
	back halfway), then continues on the new route.

	local pg = PoseGraph.new(PoseGraph.QUADRUPED, "Stand")
	PoseGraph.request(pg, "LieLateral")
	PoseGraph.tick(pg, dt) --> pg.from, pg.to, pg.alpha, pg.current (settled pose or nil)
]]

local PoseGraph = {}

-- Undirected edges with seconds per transition (both directions). Values tuned for a
-- medium dog; scaled per breed by `speed`.
PoseGraph.QUADRUPED = {
	edges = {
		{ "Stand", "Sit", 0.7 },
		{ "Sit", "LieSternal", 0.9 },
		{ "LieSternal", "LieLateral", 1.1 },
		{ "LieSternal", "Stand", 1.2 },
		{ "LieLateral", "RollOver", 0.9 },
		{ "Stand", "Crouch", 0.4 },
		{ "Crouch", "LieSternal", 0.6 },
		{ "LieSternal", "Loaf", 0.6 },
		{ "Loaf", "Curl", 0.8 },
		{ "Stand", "Carried", 0.5 },
		{ "Sit", "Carried", 0.6 },
	},
}

local function buildAdjacency(def)
	if def.adjacency then
		return def.adjacency
	end
	local adj = {}
	for _, e in def.edges do
		local a, b, t = e[1], e[2], e[3]
		adj[a] = adj[a] or {}
		adj[b] = adj[b] or {}
		adj[a][b] = t
		adj[b][a] = t
	end
	def.adjacency = adj
	return adj
end

-- Fastest route (Dijkstra on transition time). Returns list of poses after `from`, or nil.
function PoseGraph.route(def, from: string, to: string, allowed: { [string]: boolean }?)
	local adj = buildAdjacency(def)
	if from == to then
		return {}
	end
	if not adj[from] or not adj[to] then
		return nil
	end
	local dist, prev, done = { [from] = 0 }, {}, {}
	while true do
		local best, bestD = nil, math.huge
		for node, d in dist do
			if not done[node] and d < bestD then
				best, bestD = node, d
			end
		end
		if not best then
			return nil
		end
		if best == to then
			break
		end
		done[best] = true
		for nxt, t in adj[best] do
			if not allowed or allowed[nxt] or nxt == to then
				local nd = bestD + t
				if dist[nxt] == nil or nd < dist[nxt] then
					dist[nxt] = nd
					prev[nxt] = best
				end
			end
		end
	end
	local path = {}
	local node = to
	while node ~= from do
		table.insert(path, 1, node)
		node = prev[node]
	end
	return path
end

function PoseGraph.new(def, startPose: string, opts)
	buildAdjacency(def)
	opts = opts or {}
	return {
		def = def,
		current = startPose, -- settled pose (nil while transitioning)
		from = startPose,
		to = startPose,
		alpha = 1,
		duration = 0,
		queue = {},
		speed = opts.speed or 1, -- >1 faster (small agile breeds), <1 slower (sick / large)
		allowed = opts.allowed, -- species pose whitelist (set of names)
		history = { startPose },
	}
end

local function beginEdge(pg, nextPose: string)
	local t = pg.def.adjacency[pg.from][nextPose]
	pg.to = nextPose
	pg.alpha = 0
	pg.duration = t / pg.speed
	pg.current = nil
end

-- Request a target pose. Returns false if it can't be reached.
function PoseGraph.request(pg, target: string): boolean
	local origin = if pg.current then pg.current else pg.to
	if pg.allowed and not pg.allowed[target] then
		return false
	end
	local path = PoseGraph.route(pg.def, origin, target, pg.allowed)
	if not path then
		return false
	end
	pg.queue = path
	if pg.current and #path > 0 then
		pg.from = pg.current
		beginEdge(pg, table.remove(pg.queue, 1))
	end
	return true
end

function PoseGraph.tick(pg, dt: number)
	if pg.current then
		return
	end
	pg.alpha = math.min(1, pg.alpha + dt / math.max(pg.duration, 1e-3))
	if pg.alpha >= 1 then
		pg.from = pg.to
		table.insert(pg.history, pg.to)
		if #pg.queue > 0 then
			beginEdge(pg, table.remove(pg.queue, 1))
		else
			pg.current = pg.to
		end
	end
end

-- Smoothstep-eased alpha for cross-fading (zero velocity at both ends → no visible snap).
function PoseGraph.easedAlpha(pg): number
	local a = pg.alpha
	return a * a * (3 - 2 * a)
end

function PoseGraph.settled(pg): boolean
	return pg.current ~= nil
end

return PoseGraph
