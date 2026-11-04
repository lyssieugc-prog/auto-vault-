--[[
	Format — number + time formatting for HUDs ("1.2K", "3.4M", "05:09", "1h 02m").
	Pure module. No Roblox APIs.
]]

local Format = {}

local SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }

local function trimZeros(s: string): string
	if string.find(s, ".", 1, true) then
		s = (string.gsub(s, "0+$", ""))
		s = (string.gsub(s, "%.$", ""))
	end
	return s
end

-- Abbreviates a number: 999 -> "999", 1234 -> "1.2K", 1500000 -> "1.5M".
function Format.abbreviate(n: number, decimals: number?): string
	local places = decimals or 1
	if n ~= n or n == math.huge or n == -math.huge then
		return if n == math.huge then "inf" elseif n == -math.huge then "-inf" else "0"
	end
	local sign = if n < 0 then "-" else ""
	n = math.abs(n)
	if n < 1000 then
		return sign .. tostring(math.floor(n))
	end
	local tier = math.floor(math.log10(n) / 3)
	if n / (1000 ^ tier) < 1 then
		tier -= 1
	elseif n / (1000 ^ tier) >= 1000 then
		tier += 1
	end
	tier = math.min(tier, #SUFFIXES - 1)
	local factor = 10 ^ places
	local scaled = math.floor((n / (1000 ^ tier)) * factor) / factor
	local text = trimZeros(string.format("%." .. tostring(places) .. "f", scaled))
	return sign .. text .. SUFFIXES[tier + 1]
end

-- 1234567 -> "1,234,567"
function Format.commas(n: number): string
	local sign = if n < 0 then "-" else ""
	local digits = tostring(math.floor(math.abs(n)))
	local out = ""
	local count = 0
	for i = #digits, 1, -1 do
		out = string.sub(digits, i, i) .. out
		count += 1
		if count % 3 == 0 and i > 1 then
			out = "," .. out
		end
	end
	return sign .. out
end

-- Countdown text: <1h -> "MM:SS", <1d -> "1h 02m", else "2d 03h".
function Format.countdown(seconds: number): string
	local s = math.max(0, math.floor(seconds))
	local days = s // 86400
	local hours = (s % 86400) // 3600
	local minutes = (s % 3600) // 60
	local secs = s % 60
	if days > 0 then
		return string.format("%dd %02dh", days, hours)
	elseif hours > 0 then
		return string.format("%dh %02dm", hours, minutes)
	end
	return string.format("%02d:%02d", minutes, secs)
end

return Format
