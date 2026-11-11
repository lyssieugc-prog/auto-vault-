--[[
	DataStoreAdapter — wraps a Roblox DataStore into the `store:update(key, fn)` interface used by
	Shared/DataService. Roblox-only (not covered by Lune tests; verify in Studio with API access
	enabled: Game Settings → Security → Enable Studio Access to API Services).
]]

local DataStoreService = game:GetService("DataStoreService")

local DataStoreAdapter = {}
DataStoreAdapter.__index = DataStoreAdapter

function DataStoreAdapter.new(name: string, scope: string?)
	local self = setmetatable({}, DataStoreAdapter)
	self.store = DataStoreService:GetDataStore(name, scope)
	return self
end

function DataStoreAdapter:update(key: string, transform)
	local ok, result = pcall(function()
		return self.store:UpdateAsync(key, function(old)
			return transform(old)
		end)
	end)
	if not ok then
		return nil, tostring(result)
	end
	return result, nil
end

-- In-memory store for Studio sessions without API access and for tests.
function DataStoreAdapter.memory()
	local data = {}
	return {
		update = function(_, key, transform)
			local new = transform(data[key])
			if new ~= nil then
				data[key] = new
			end
			return new, nil
		end,
	}
end

return DataStoreAdapter
