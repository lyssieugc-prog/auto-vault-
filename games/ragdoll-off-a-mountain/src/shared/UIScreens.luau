--[[
	UIScreens — builds every Ragdoll Off a Mountain ScreenGui from the UI spec (figma/ui-spec.md) in
	house style, filled with MOCK preview data from Config.

	Used two ways (owner rule L-11: map + UI visible in Edit mode without pressing Play):
	  • Edit mode: studio/build_edit_preview.luau calls UIScreens.buildAll(StarterGui) once, so every
	    screen is saved in the place and visible in the Studio viewport.
	  • Runtime: the client binds to those same instances by NAME; if one is missing it builds it.
	Live values always come from the server; mock values are preview only.
	Item art slots ("Art") are ImageLabels with empty Image until the Blender renders are uploaded
	(owner approval needed for uploads) — they show the item name meanwhile.

	Flip the visible screen in Edit mode: studio/preview_screen.luau (sets attribute PreviewScreen).
]]

local UIScreens = {}

local C = {
	panel = Color3.fromHex("#1E1B33"),
	panelRaised = Color3.fromHex("#2B2748"),
	stroke = Color3.fromHex("#1A1A1A"),
	white = Color3.new(1, 1, 1),
	gold = Color3.fromHex("#FFD93B"),
	lime = Color3.fromHex("#A8F03C"),
	green = Color3.fromHex("#7ADE43"),
	greenLip = Color3.fromHex("#57AC35"),
	red = Color3.fromHex("#E13A2A"),
	redDark = Color3.fromHex("#B6261D"),
	ice = Color3.fromHex("#5EC8FF"),
	blue = Color3.fromHex("#2590D1"),
	orange = Color3.fromHex("#FF8A1F"),
	bone = Color3.fromHex("#FFF1CF"),
	purple = Color3.fromHex("#B678EA"),
	pink = Color3.fromHex("#FF9BC8"),
}
UIScreens.colors = C

local RARITY = {
	Common = Color3.fromHex("#B8C2CC"),
	Uncommon = Color3.fromHex("#7ADE43"),
	Rare = Color3.fromHex("#2590D1"),
	Epic = Color3.fromHex("#B678EA"),
	Legendary = Color3.fromHex("#FFC21A"),
	Mythic = Color3.fromHex("#FF3EC8"),
	Secret = Color3.fromHex("#1A1A1A"),
}

local function abbreviate(n: number): string
	local units = { "", "K", "M", "B", "T", "Qa" }
	local i = 1
	while math.abs(n) >= 1000 and i < #units do
		n /= 1000
		i += 1
	end
	if i == 1 then
		return tostring(math.floor(n))
	end
	local out = string.gsub(string.format("%.1f%s", n, units[i]), "%.0(%a)", "%1")
	return out
end

local function new(className: string, props, parent: Instance?)
	local inst = Instance.new(className)
	for k, v in props do
		(inst :: any)[k] = v
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end

local function corner(parent: Instance, scale: number?)
	return new("UICorner", { CornerRadius = UDim.new(scale or 0.2, 0) }, parent)
end

local function stroke(parent: Instance, thickness: number, color: Color3?, border: boolean?)
	return new("UIStroke", {
		Thickness = thickness,
		Color = color or C.stroke,
		ApplyStrokeMode = if border then Enum.ApplyStrokeMode.Border else Enum.ApplyStrokeMode.Contextual,
	}, parent)
end

local function gradient(parent: Instance, top: Color3, bottom: Color3)
	return new("UIGradient", { Color = ColorSequence.new(top, bottom), Rotation = 90 }, parent)
end

-- Stroked white text with a dark offset shadow copy (house style).
local function text(parent: Instance, name: string, value: string, pos: UDim2, size: UDim2, color: Color3?)
	local shadow = new("TextLabel", {
		Name = name .. "Shadow",
		Text = value,
		Position = pos + UDim2.fromScale(0, 0.012),
		Size = size,
		BackgroundTransparency = 1,
		TextColor3 = C.stroke,
		TextTransparency = 0.35,
		Font = Enum.Font.FredokaOne,
		TextScaled = true,
	}, parent)
	local label = new("TextLabel", {
		Name = name,
		Text = value,
		Position = pos,
		Size = size,
		BackgroundTransparency = 1,
		TextColor3 = color or C.white,
		Font = Enum.Font.FredokaOne,
		TextScaled = true,
		ZIndex = 2,
	}, parent)
	stroke(label, 2.5)
	label:GetPropertyChangedSignal("Text"):Connect(function()
		shadow.Text = label.Text
	end)
	return label
end

-- Glossy pill button with a darker bottom lip and a white gloss stripe.
local function button(
	parent: Instance,
	name: string,
	label: string,
	pos: UDim2,
	size: UDim2,
	color: Color3?,
	lip: Color3?
)
	local holder =
		new("Frame", { Name = name .. "Holder", Position = pos, Size = size, BackgroundTransparency = 1 }, parent)
	local lipFrame = new("Frame", {
		Name = "Lip",
		Position = UDim2.fromScale(0, 0.1),
		Size = UDim2.fromScale(1, 0.95),
		BackgroundColor3 = lip or C.greenLip,
	}, holder)
	corner(lipFrame, 0.3)
	local btn = new("TextButton", {
		Name = name,
		Text = "",
		Size = UDim2.fromScale(1, 0.9),
		BackgroundColor3 = color or C.green,
		AutoButtonColor = false,
		ZIndex = 2,
	}, holder)
	corner(btn, 0.3)
	stroke(btn, 2, C.stroke, true)
	local gloss = new("Frame", {
		Name = "Gloss",
		Position = UDim2.fromScale(0.08, 0.08),
		Size = UDim2.fromScale(0.84, 0.28),
		BackgroundColor3 = C.white,
		BackgroundTransparency = 0.65,
		ZIndex = 3,
	}, btn)
	corner(gloss, 0.5)
	text(btn, "Label", label, UDim2.fromScale(0.06, 0.12), UDim2.fromScale(0.88, 0.76)).ZIndex = 4
	return btn
end

local function tag(parent: Instance, value: string, color: Color3, pos: UDim2)
	local t = new("TextLabel", {
		Name = "Tag",
		Text = value,
		Position = pos,
		Size = UDim2.fromScale(0.42, 0.12),
		BackgroundColor3 = color,
		TextColor3 = C.white,
		Font = Enum.Font.LuckiestGuy,
		TextScaled = true,
		Rotation = -8,
		ZIndex = 6,
	}, parent)
	corner(t, 0.25)
	stroke(t, 2, C.stroke, true)
	return t
end

local function screen(parent: Instance, name: string, preview: boolean?): ScreenGui
	local old = parent:FindFirstChild(name)
	if old then
		old:Destroy()
	end
	return new("ScreenGui", {
		Name = name,
		ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets,
		Enabled = preview ~= false,
	}, parent) :: ScreenGui
end

-- Themed window: snow-capped ice title bar, bandage close X, rope/carabiner corner decor.
local function window(gui: ScreenGui, title: string, color: Color3?, size: UDim2?): Frame
	local win = new("Frame", {
		Name = "Window",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.53),
		Size = size or UDim2.fromScale(0.62, 0.72),
		BackgroundColor3 = C.panel,
	}, gui) :: Frame
	corner(win, 0.06)
	stroke(win, 4, C.stroke, true)
	new("UIAspectRatioConstraint", { AspectRatio = 1.6 }, win)
	local bar = new("Frame", { Name = "TitleBar", Size = UDim2.fromScale(1, 0.14), BackgroundColor3 = C.white }, win)
	corner(bar, 0.35)
	gradient(bar, color or C.ice, (color or C.blue):Lerp(C.stroke, 0.35))
	stroke(bar, 3, C.stroke, true)
	-- snow cap dripping over the bar
	for i = 0, 5 do
		local blob = new("Frame", {
			Name = "Snow" .. i,
			Position = UDim2.fromScale(0.05 + i * 0.16, -0.18),
			Size = UDim2.fromScale(0.14 + (i % 2) * 0.04, 0.42),
			BackgroundColor3 = Color3.fromHex("#F4FBFF"),
			ZIndex = 3,
		}, bar)
		corner(blob, 0.5)
	end
	text(bar, "Title", title, UDim2.fromScale(0.16, 0.1), UDim2.fromScale(0.68, 0.8)).ZIndex = 5
	-- oversized tilted icon breaking the corner (carabiner + rope)
	local icon = new("TextLabel", {
		Name = "TitleIcon",
		Text = "🧗",
		Position = UDim2.fromScale(-0.04, -0.55),
		Size = UDim2.fromScale(0.16, 1.6),
		BackgroundTransparency = 1,
		TextScaled = true,
		Rotation = -8,
		ZIndex = 6,
	}, bar)
	new("UIAspectRatioConstraint", { AspectRatio = 1 }, icon)
	local close = new("TextButton", {
		Name = "CloseButton",
		Text = "X",
		Font = Enum.Font.FredokaOne,
		TextScaled = true,
		TextColor3 = C.white,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.98, 0.04),
		Size = UDim2.fromScale(0.08, 0.13),
		BackgroundColor3 = C.red,
		ZIndex = 7,
	}, win)
	corner(close, 0.2)
	stroke(close, 3, C.stroke, true)
	new("UIAspectRatioConstraint", { AspectRatio = 1 }, close)
	local bandage = new("Frame", {
		Name = "Bandage",
		Position = UDim2.fromScale(-0.1, 0.62),
		Size = UDim2.fromScale(0.6, 0.22),
		BackgroundColor3 = C.pink,
		Rotation = 40,
		ZIndex = 8,
	}, close)
	corner(bandage, 0.4)
	local body = new("Frame", {
		Name = "Body",
		Position = UDim2.fromScale(0.03, 0.18),
		Size = UDim2.fromScale(0.94, 0.78),
		BackgroundTransparency = 1,
	}, win)
	return body
end

-- Item card: saturated block + gradient + Art slot + name + optional price button.
local function card(parent: Instance, name: string, title: string, color: Color3, pos: UDim2, size: UDim2)
	local frame = new("Frame", { Name = name, Position = pos, Size = size, BackgroundColor3 = C.white }, parent)
	corner(frame, 0.12)
	gradient(frame, color:Lerp(C.white, 0.25), color:Lerp(C.stroke, 0.3))
	stroke(frame, 3, C.stroke, true)
	local inner = new("UIStroke", { Thickness = 2, Color = color:Lerp(C.white, 0.6), Transparency = 0.2 }, frame)
	inner.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	local art = new("ImageLabel", {
		Name = "Art",
		BackgroundTransparency = 1,
		Position = UDim2.fromScale(0.1, 0.06),
		Size = UDim2.fromScale(0.8, 0.52),
		ScaleType = Enum.ScaleType.Fit,
		Image = "",
	}, frame)
	text(art, "ArtPending", title, UDim2.fromScale(0, 0.3), UDim2.fromScale(1, 0.4), C.bone).TextTransparency = 0.4
	text(frame, "Name", title, UDim2.fromScale(0.05, 0.6), UDim2.fromScale(0.9, 0.14))
	return frame
end

local function progressBar(parent: Instance, name: string, pos: UDim2, size: UDim2, fill: number, label: string)
	local bar = new("Frame", { Name = name, Position = pos, Size = size, BackgroundColor3 = C.panelRaised }, parent)
	corner(bar, 0.5)
	stroke(bar, 3, C.stroke, true)
	local f = new(
		"Frame",
		{ Name = "Fill", Size = UDim2.fromScale(math.clamp(fill, 0, 1), 1), BackgroundColor3 = C.gold },
		bar
	)
	corner(f, 0.5)
	gradient(f, C.gold, C.orange)
	for i, x in { -0.02, 0.98 } do -- bone-shaped end caps
		local cap = new("Frame", {
			Name = "BoneCap" .. i,
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromScale(x, 0.5),
			Size = UDim2.fromScale(0.04, 1.4),
			BackgroundColor3 = C.bone,
			ZIndex = 3,
		}, bar)
		corner(cap, 0.5)
		stroke(cap, 2, C.stroke, true)
	end
	text(bar, "Text", label, UDim2.fromScale(0.05, 0.05), UDim2.fromScale(0.9, 0.9)).ZIndex = 4
	return bar
end

-- Screens ----------------------------------------------------------------------------------------------

function UIScreens.buildHUD(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "HUD")
	local top = new("Frame", {
		Name = "TopBar",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0.02),
		Size = UDim2.fromScale(0.44, 0.08),
		BackgroundTransparency = 1,
	}, gui)
	for i, info in { { "Cash", "💰", "12.4K", C.gold }, { "Gems", "💎", "135", C.lime } } do
		local pill = new("Frame", {
			Name = info[1] .. "Pill",
			Position = UDim2.fromScale((i - 1) * 0.52, 0),
			Size = UDim2.fromScale(0.48, 1),
			BackgroundColor3 = C.panel,
		}, top)
		corner(pill, 0.5)
		stroke(pill, 3, C.stroke, true)
		text(pill, "Icon", info[2], UDim2.fromScale(0.02, 0.05), UDim2.fromScale(0.22, 0.9))
		text(pill, info[1], info[3], UDim2.fromScale(0.24, 0.1), UDim2.fromScale(0.56, 0.8), info[4])
		button(pill, info[1] .. "Plus", "+", UDim2.fromScale(0.8, 0.12), UDim2.fromScale(0.18, 0.76))
	end
	local peak = Config.peaks[2]
	local peakPill = new("Frame", {
		Name = "PeakPill",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0.11),
		Size = UDim2.fromScale(0.26, 0.05),
		BackgroundColor3 = C.blue,
	}, gui)
	corner(peakPill, 0.5)
	stroke(peakPill, 3, C.stroke, true)
	text(
		peakPill,
		"Text",
		"🏔️ " .. peak.name .. "  x" .. peak.multiplier,
		UDim2.fromScale(0.04, 0.08),
		UDim2.fromScale(0.92, 0.84)
	)
	progressBar(
		gui,
		"NextGoalBar",
		UDim2.fromScale(0.36, 0.17),
		UDim2.fromScale(0.28, 0.035),
		0.42,
		"Next: Frostbite Cliffs 50.4K / 120K"
	)

	-- left rail
	for i, info in
		{
			{ "ShopButton", "SHOP", C.red, C.redDark },
			{ "PetsButton", "PETS", C.purple, C.purple:Lerp(C.stroke, 0.3) },
			{ "IndexButton", "INDEX", C.blue, C.blue:Lerp(C.stroke, 0.3) },
			{ "UpgradesButton", "UPGRADES", C.green, C.greenLip },
		}
	do
		button(
			gui,
			info[1],
			info[2],
			UDim2.fromScale(0.015, 0.28 + (i - 1) * 0.1),
			UDim2.fromScale(0.09, 0.085),
			info[3],
			info[4]
		)
	end
	-- right rail: context-named x2 Cash ladder (x2 -> x128), rewards
	local ladder = button(
		gui,
		"X2CashButton",
		"x2 CASH",
		UDim2.fromScale(0.895, 0.28),
		UDim2.fromScale(0.09, 0.1),
		C.gold,
		C.orange
	)
	text(ladder, "Tier", "Owned: x1 · Next: x2", UDim2.fromScale(-0.2, 1.05), UDim2.fromScale(1.4, 0.3))
	button(
		gui,
		"RewardsButton",
		"REWARDS",
		UDim2.fromScale(0.895, 0.44),
		UDim2.fromScale(0.09, 0.085),
		C.purple,
		C.purple:Lerp(C.stroke, 0.3)
	)
	button(gui, "SeasonButton", "SEASON 1", UDim2.fromScale(0.895, 0.54), UDim2.fromScale(0.09, 0.085), C.ice, C.blue)
	local boosts = text(gui, "Boosts", "x2 Cash 9:42", UDim2.fromScale(0.78, 0.11), UDim2.fromScale(0.2, 0.04), C.lime)
	boosts.TextXAlignment = Enum.TextXAlignment.Right

	-- launch controls (bottom centre)
	button(
		gui,
		"LiftButton",
		"⬆ LIFT",
		UDim2.fromScale(0.27, 0.84),
		UDim2.fromScale(0.1, 0.09),
		C.blue,
		C.blue:Lerp(C.stroke, 0.3)
	)
	button(
		gui,
		"LaunchButton",
		"HOLD TO LAUNCH!",
		UDim2.fromScale(0.39, 0.83),
		UDim2.fromScale(0.22, 0.12),
		C.orange,
		C.redDark
	)
	progressBar(gui, "ChargeBar", UDim2.fromScale(0.39, 0.78), UDim2.fromScale(0.22, 0.035), 0.65, "POWER")
	local event = new("Frame", {
		Name = "EventBanner",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0.22),
		Size = UDim2.fromScale(0.3, 0.045),
		BackgroundColor3 = C.purple,
		Visible = false,
	}, gui)
	corner(event, 0.5)
	text(event, "Text", "AVALANCHE HOUR: x2 Bone Value  12:00", UDim2.fromScale(0.03, 0.05), UDim2.fromScale(0.94, 0.9))
	return gui
end

function UIScreens.buildRunSummary(parent: Instance): ScreenGui
	local gui = screen(parent, "RunSummary")
	local body = window(gui, "RUN SUMMARY", C.orange, UDim2.fromScale(0.42, 0.5))
	text(body, "BonesTitle", "BONES BROKEN", UDim2.fromScale(0.05, 0.02), UDim2.fromScale(0.9, 0.14), C.bone)
	text(body, "Bones", "87 / 206", UDim2.fromScale(0.1, 0.17), UDim2.fromScale(0.8, 0.26), C.gold)
	text(body, "Cash", "+$4.2K", UDim2.fromScale(0.1, 0.45), UDim2.fromScale(0.8, 0.2), C.lime)
	text(body, "Combo", "x2.3", UDim2.fromScale(0.05, 0.7), UDim2.fromScale(0.4, 0.14))
	text(body, "NewBest", "NEW BEST!", UDim2.fromScale(0.5, 0.7), UDim2.fromScale(0.45, 0.14), C.orange)
	button(body, "ContinueButton", "AGAIN!", UDim2.fromScale(0.3, 0.86), UDim2.fromScale(0.4, 0.13))
	return gui
end

function UIScreens.buildCannonShop(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "CannonShop")
	local body = window(gui, "CANNONS", C.orange)
	local costs = Config.upgrades.Cannon.costs
	for i = 2, #Config.cannons do
		local cannon = Config.cannons[i]
		local x = ((i - 2) % 5) * 0.2
		local c = card(
			body,
			"CannonCard" .. (i - 1),
			cannon.name,
			if i == 2 then C.green elseif i == 3 then C.blue else C.purple,
			UDim2.fromScale(x + 0.005, 0.05),
			UDim2.fromScale(0.19, 0.85)
		)
		progressBar(
			c,
			"Speed",
			UDim2.fromScale(0.08, 0.75),
			UDim2.fromScale(0.84, 0.07),
			cannon.speed / 250,
			cannon.speed .. " SPEED"
		)
		button(
			c,
			"BuyButton",
			"$" .. abbreviate(costs[i - 1]),
			UDim2.fromScale(0.08, 0.85),
			UDim2.fromScale(0.84, 0.12)
		)
		if i == 2 then
			tag(c, "OWNED", C.lime, UDim2.fromScale(-0.08, -0.04))
		elseif i == 3 then
			tag(c, "NEXT!", C.orange, UDim2.fromScale(-0.08, -0.04))
		end
	end
	return gui
end

function UIScreens.buildShop(parent: Instance): ScreenGui
	local gui = screen(parent, "Shop")
	local body = window(gui, "SHOP", C.red)
	local featured =
		card(body, "Featured", "Avalanche Pug", RARITY.Legendary, UDim2.fromScale(0, 0.02), UDim2.fromScale(0.44, 0.78))
	tag(featured, "LIMITED!", C.red, UDim2.fromScale(-0.05, -0.03))
	text(featured, "Countdown", "ENDS IN 23:59:12", UDim2.fromScale(0.1, 0.74), UDim2.fromScale(0.8, 0.08), C.gold)
	button(featured, "BuyButton", "R$ CONFIG", UDim2.fromScale(0.15, 0.85), UDim2.fromScale(0.7, 0.12))
	for i, info in { { "Small", "2,500 Cash" }, { "Medium", "15K Cash" }, { "Best", "120K Cash" } } do
		local offer = card(
			body,
			"Offer" .. info[1],
			info[2],
			if i == 3 then C.gold else C.blue,
			UDim2.fromScale(0.47, 0.02 + (i - 1) * 0.27),
			UDim2.fromScale(0.3, 0.25)
		)
		button(offer, "BuyButton", "R$ CONFIG", UDim2.fromScale(0.55, 0.62), UDim2.fromScale(0.42, 0.32))
		if i == 3 then
			tag(offer, "BEST DEAL!", C.gold, UDim2.fromScale(0.6, -0.1))
		end
	end
	local promo =
		card(body, "PremiumPromo", "Season 1 Pass", C.ice, UDim2.fromScale(0.79, 0.02), UDim2.fromScale(0.21, 0.78))
	button(promo, "BuyButton", "R$ CONFIG", UDim2.fromScale(0.08, 0.85), UDim2.fromScale(0.84, 0.12))
	local strip = new(
		"Frame",
		{
			Name = "RarityStrip",
			Position = UDim2.fromScale(0, 0.84),
			Size = UDim2.fromScale(1, 0.14),
			BackgroundTransparency = 1,
		},
		body
	)
	for i, info in
		{
			{ "Common", "1 in 1.7" },
			{ "Rare", "1 in 10" },
			{ "Epic", "1 in 25" },
			{ "Legendary", "1 in 111" },
			{ "Mythic", "1 in 1,111" },
		}
	do
		local chip = new(
			"Frame",
			{
				Name = info[1],
				Position = UDim2.fromScale((i - 1) * 0.2 + 0.005, 0),
				Size = UDim2.fromScale(0.19, 1),
				BackgroundColor3 = RARITY[info[1]],
			},
			strip
		)
		corner(chip, 0.3)
		stroke(chip, 2, C.stroke, true)
		text(chip, "Odds", info[1] .. " " .. info[2], UDim2.fromScale(0.04, 0.1), UDim2.fromScale(0.92, 0.8))
	end
	return gui
end

function UIScreens.buildPets(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "Pets")
	local body = window(gui, "CRASH BUDDIES", C.purple)
	local grid = new(
		"ScrollingFrame",
		{
			Name = "Grid",
			Size = UDim2.fromScale(0.64, 1),
			BackgroundTransparency = 1,
			ScrollBarThickness = 6,
			CanvasSize = UDim2.fromScale(0, 1.4),
		},
		body
	)
	new("UIGridLayout", { CellSize = UDim2.fromScale(0.23, 0.3), CellPadding = UDim2.fromScale(0.02, 0.03) }, grid)
	for i, id in
		{
			"PebblePup",
			"Goatling",
			"BackpackBeaver",
			"HelmetHedgehog",
			"BoulderBull",
			"AvalanchePug",
			"ThunderYak",
			"SkellyCat",
		}
	do
		local def = Config.pets[id]
		local c = card(grid, "Pet" .. i, def.name, RARITY[def.rarity], UDim2.new(), UDim2.new())
		text(c, "Power", "+" .. def.power .. " HIT", UDim2.fromScale(0.05, 0.78), UDim2.fromScale(0.9, 0.16), C.gold)
		if i <= 3 then
			tag(c, "EQUIPPED", C.lime, UDim2.fromScale(-0.1, -0.05))
		end
	end
	local detail = new(
		"Frame",
		{
			Name = "DetailPanel",
			Position = UDim2.fromScale(0.67, 0),
			Size = UDim2.fromScale(0.33, 1),
			BackgroundColor3 = C.panelRaised,
		},
		body
	)
	corner(detail, 0.08)
	stroke(detail, 3, C.stroke, true)
	text(detail, "Name", "Avalanche Pug", UDim2.fromScale(0.05, 0.03), UDim2.fromScale(0.9, 0.1), RARITY.Legendary)
	text(detail, "Stats", "HIT POWER +2\nLegendary", UDim2.fromScale(0.05, 0.55), UDim2.fromScale(0.9, 0.18))
	text(detail, "Slots", "Equipped 3 / 3 (+1 pass)", UDim2.fromScale(0.05, 0.74), UDim2.fromScale(0.9, 0.08))
	button(detail, "EquipButton", "EQUIP", UDim2.fromScale(0.1, 0.85), UDim2.fromScale(0.8, 0.12))
	return gui
end

function UIScreens.buildEggHatch(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "EggHatch")
	local body = window(gui, "TRAILHEAD EGG", C.green, UDim2.fromScale(0.5, 0.62))
	card(body, "Egg", "Trailhead Egg", C.green, UDim2.fromScale(0.3, 0), UDim2.fromScale(0.4, 0.55))
	local strip = new(
		"Frame",
		{
			Name = "OddsStrip",
			Position = UDim2.fromScale(0, 0.58),
			Size = UDim2.fromScale(1, 0.16),
			BackgroundTransparency = 1,
		},
		body
	)
	local total = 0
	for _, r in Config.rarities do
		total += r.weight
	end
	for i, r in Config.rarities do
		local chip = new(
			"Frame",
			{
				Name = r.name,
				Position = UDim2.fromScale((i - 1) / 7 + 0.003, 0),
				Size = UDim2.fromScale(1 / 7 - 0.006, 1),
				BackgroundColor3 = RARITY[r.name],
			},
			strip
		)
		corner(chip, 0.2)
		stroke(chip, 2, C.stroke, true)
		local n = total / r.weight
		text(
			chip,
			"Odds",
			"1 in " .. (if n < 10 then string.format("%.1f", n) else abbreviate(math.floor(n + 0.5))),
			UDim2.fromScale(0.04, 0.1),
			UDim2.fromScale(0.92, 0.8)
		)
	end
	text(
		body,
		"PityCounter",
		"Legendary guaranteed in 75",
		UDim2.fromScale(0.1, 0.76),
		UDim2.fromScale(0.8, 0.08),
		C.gold
	)
	button(body, "HatchButton", "HATCH  $150", UDim2.fromScale(0.3, 0.86), UDim2.fromScale(0.4, 0.13))
	return gui
end

function UIScreens.buildSeason(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "Season1Pass")
	local body = window(gui, "SEASON 1: AVALANCHE", C.ice)
	progressBar(body, "XPBar", UDim2.fromScale(0.02, 0.02), UDim2.fromScale(0.7, 0.07), 0.6, "TIER 7  ·  84 / 220 XP")
	button(
		body,
		"PremiumButton",
		"PREMIUM  R$ CONFIG",
		UDim2.fromScale(0.74, 0),
		UDim2.fromScale(0.26, 0.11),
		C.gold,
		C.orange
	)
	local scroll = new(
		"ScrollingFrame",
		{
			Name = "Tiers",
			Position = UDim2.fromScale(0, 0.15),
			Size = UDim2.fromScale(1, 0.85),
			BackgroundTransparency = 1,
			CanvasSize = UDim2.fromScale(8.5, 0),
			ScrollBarThickness = 6,
		},
		body
	)
	for tier = 1, Config.season.tiers do
		local x = (tier - 1) * 0.17
		local free = card(
			scroll,
			"Free" .. tier,
			"Tier " .. tier,
			if tier <= 6 then C.green else C.blue,
			UDim2.fromScale(x / 8.5 * 1, 0),
			UDim2.fromScale(0.15 / 8.5, 0.46)
		)
		local prem = card(
			scroll,
			"Premium" .. tier,
			"Premium " .. tier,
			C.gold,
			UDim2.fromScale(x / 8.5, 0.52),
			UDim2.fromScale(0.15 / 8.5, 0.46)
		)
		if tier <= 6 then
			tag(free, "CLAIMED", C.lime, UDim2.fromScale(0.3, 0.4))
		end
		tag(prem, "🔒", C.stroke, UDim2.fromScale(0.3, 0.4))
	end
	return gui
end

function UIScreens.buildDaily(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "DailyRewards")
	local body = window(gui, "DAILY REWARDS", C.gold)
	for day, reward in Config.rewards.daily do
		local label = if reward.currency
			then abbreviate(reward.amount) .. " " .. reward.currency
			elseif reward.boost then "x2 Cash 15m"
			else "Backpack Beaver + 50 Gems"
		local big = day == 7
		local c = card(
			body,
			"Day" .. day,
			"DAY " .. day,
			if big then C.purple elseif day <= 2 then C.green else C.blue,
			UDim2.fromScale(if big then 0.76 else ((day - 1) % 3) * 0.25, if big then 0 else (day - 1) // 3 * 0.5),
			UDim2.fromScale(if big then 0.24 else 0.23, if big then 0.98 else 0.46)
		)
		text(c, "Reward", label, UDim2.fromScale(0.05, 0.76), UDim2.fromScale(0.9, 0.16), C.gold)
		if day <= 2 then
			tag(c, "CLAIMED", C.lime, UDim2.fromScale(0.3, 0.3))
		elseif day == 3 then
			tag(c, "TODAY!", C.orange, UDim2.fromScale(0.3, 0.3))
			button(c, "ClaimButton", "CLAIM!", UDim2.fromScale(0.1, 0.55), UDim2.fromScale(0.8, 0.2))
		end
	end
	return gui
end

function UIScreens.buildQuests(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "Quests")
	local body = window(gui, "QUESTS", C.green)
	for i, q in Config.periodicQuests.quests do
		local row = new(
			"Frame",
			{
				Name = q.id,
				Position = UDim2.fromScale(0, (i - 1) * 0.165),
				Size = UDim2.fromScale(1, 0.15),
				BackgroundColor3 = C.panelRaised,
			},
			body
		)
		corner(row, 0.25)
		stroke(row, 2, C.stroke, true)
		text(
			row,
			"Text",
			(if q.period == "daily" then "DAILY · " else "WEEKLY · ") .. q.text,
			UDim2.fromScale(0.02, 0.1),
			UDim2.fromScale(0.44, 0.8)
		)
		progressBar(row, "Progress", UDim2.fromScale(0.48, 0.25), UDim2.fromScale(0.3, 0.5), 0.5, "50%")
		button(
			row,
			"ClaimButton",
			"+" .. q.reward.amount .. " " .. q.reward.currency,
			UDim2.fromScale(0.8, 0.12),
			UDim2.fromScale(0.19, 0.76)
		)
	end
	return gui
end

function UIScreens.buildRebirth(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "Rebirth")
	local body = window(gui, "REBIRTH", C.purple, UDim2.fromScale(0.46, 0.6))
	text(
		body,
		"Cost",
		"COST: $" .. abbreviate(Config.rebirth.baseCost),
		UDim2.fromScale(0.1, 0.02),
		UDim2.fromScale(0.8, 0.14),
		C.gold
	)
	text(
		body,
		"Resets",
		"RESETS: Cash, Peaks, Cannons, Cash upgrades",
		UDim2.fromScale(0.05, 0.22),
		UDim2.fromScale(0.9, 0.12),
		C.red
	)
	text(
		body,
		"Keeps",
		"KEEPS: Pets, Gems, Base camp, Index, Season",
		UDim2.fromScale(0.05, 0.38),
		UDim2.fromScale(0.9, 0.12),
		C.lime
	)
	text(body, "Gain", "PERMANENT x1.5 CASH", UDim2.fromScale(0.1, 0.55), UDim2.fromScale(0.8, 0.14), C.gold)
	button(
		body,
		"ConfirmButton",
		"REBIRTH!",
		UDim2.fromScale(0.3, 0.8),
		UDim2.fromScale(0.4, 0.17),
		C.purple,
		C.purple:Lerp(C.stroke, 0.35)
	)
	return gui
end

function UIScreens.buildCodes(parent: Instance): ScreenGui
	local gui = screen(parent, "Codes")
	local body = window(gui, "CODES", C.blue, UDim2.fromScale(0.4, 0.4))
	local box = new(
		"TextBox",
		{
			Name = "CodeBox",
			PlaceholderText = "Enter code…",
			Text = "",
			Font = Enum.Font.FredokaOne,
			TextScaled = true,
			Position = UDim2.fromScale(0.05, 0.1),
			Size = UDim2.fromScale(0.9, 0.3),
			BackgroundColor3 = C.white,
			TextColor3 = C.stroke,
		},
		body
	)
	corner(box, 0.3)
	stroke(box, 3, C.stroke, true)
	button(body, "RedeemButton", "REDEEM", UDim2.fromScale(0.3, 0.5), UDim2.fromScale(0.4, 0.3))
	text(body, "Result", "", UDim2.fromScale(0.05, 0.84), UDim2.fromScale(0.9, 0.14), C.lime)
	return gui
end

function UIScreens.buildTutorial(parent: Instance, Config): ScreenGui
	local gui = screen(parent, "Tutorial")
	local bubble = new(
		"Frame",
		{
			Name = "Bubble",
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromScale(0.5, 0.62),
			Size = UDim2.fromScale(0.4, 0.1),
			BackgroundColor3 = C.panel,
		},
		gui
	)
	corner(bubble, 0.3)
	stroke(bubble, 3, C.stroke, true)
	text(bubble, "Caption", Config.tutorial.steps[2].text, UDim2.fromScale(0.04, 0.1), UDim2.fromScale(0.74, 0.8))
	button(bubble, "SkipButton", "SKIP", UDim2.fromScale(0.8, 0.2), UDim2.fromScale(0.17, 0.6), C.red, C.redDark)
	text(gui, "Arrow", "⬇", UDim2.fromScale(0.47, 0.72), UDim2.fromScale(0.06, 0.08), C.gold)
	return gui
end

function UIScreens.buildLoading(parent: Instance): ScreenGui
	local gui = screen(parent, "LoadingScreen")
	local bg = new("Frame", { Name = "Background", Size = UDim2.fromScale(1, 1), BackgroundColor3 = C.white }, gui)
	gradient(bg, C.ice, C.blue)
	text(bg, "Logo", "RAGDOLL OFF A MOUNTAIN 🏔️", UDim2.fromScale(0.15, 0.28), UDim2.fromScale(0.7, 0.18), C.white)
	progressBar(bg, "Bar", UDim2.fromScale(0.3, 0.62), UDim2.fromScale(0.4, 0.05), 0.35, "Loading mountain… 35%")
	text(
		bg,
		"Tip",
		"TIP: Hit the bumpers for CRITICAL breaks!",
		UDim2.fromScale(0.2, 0.72),
		UDim2.fromScale(0.6, 0.05),
		C.bone
	)
	button(bg, "SkipButton", "SKIP", UDim2.fromScale(0.85, 0.88), UDim2.fromScale(0.1, 0.07), C.red, C.redDark).Parent.Visible =
		false
	return gui
end

function UIScreens.buildAnnouncement(parent: Instance): ScreenGui
	local gui = screen(parent, "Announcement")
	local banner = new(
		"Frame",
		{
			Name = "Banner",
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromScale(0.5, 0.25),
			Size = UDim2.fromScale(0.42, 0.06),
			BackgroundColor3 = C.purple,
		},
		gui
	)
	corner(banner, 0.5)
	stroke(banner, 3, C.stroke, true)
	text(banner, "Text", "lyssie broke ALL 206 BONES! 💀", UDim2.fromScale(0.04, 0.08), UDim2.fromScale(0.92, 0.84))
	return gui
end

-- Builders in preview order (studio/preview_screen.luau cycles through these names).
UIScreens.order = {
	{ "HUD", "buildHUD" },
	{ "LoadingScreen", "buildLoading" },
	{ "Tutorial", "buildTutorial" },
	{ "RunSummary", "buildRunSummary" },
	{ "Shop", "buildShop" },
	{ "CannonShop", "buildCannonShop" },
	{ "Pets", "buildPets" },
	{ "EggHatch", "buildEggHatch" },
	{ "Season1Pass", "buildSeason" },
	{ "DailyRewards", "buildDaily" },
	{ "Quests", "buildQuests" },
	{ "Rebirth", "buildRebirth" },
	{ "Codes", "buildCodes" },
	{ "Announcement", "buildAnnouncement" },
}

-- Builds every screen under `parent`. Only HUD + `showScreen` stay enabled (Edit-mode preview).
function UIScreens.buildAll(parent: Instance, Config, showScreen: string?)
	for _, entry in UIScreens.order do
		local gui = (UIScreens :: any)[entry[2]](parent, Config)
		gui:SetAttribute("PreviewMock", true)
		gui.Enabled = entry[1] == "HUD" or entry[1] == showScreen
	end
end

-- Shows exactly one non-HUD screen (Edit-mode preview helper).
function UIScreens.preview(parent: Instance, name: string?)
	for _, entry in UIScreens.order do
		local gui = parent:FindFirstChild(entry[1])
		if gui and gui:IsA("ScreenGui") then
			gui.Enabled = entry[1] == "HUD" or entry[1] == name
		end
	end
end

return UIScreens
