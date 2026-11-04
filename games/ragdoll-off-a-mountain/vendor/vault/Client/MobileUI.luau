--[[
	MobileUI — touch-first helpers. Roblox client only.

	MobileUI.isTouch()                       -- touch device without keyboard
	MobileUI.enforceTouchTarget(button)      -- min 44px tap target via UISizeConstraint
	MobileUI.applySafeArea(screenGui)        -- respect notches / top bar
	MobileUI.scaleForDevice(screenGui)       -- adds UIScale tuned for phone/tablet/desktop
	MobileUI.onTap(button, fn)               -- Activated (works for mouse, touch, gamepad)
]]

local GuiService = game:GetService("GuiService")
local UserInputService = game:GetService("UserInputService")

local MobileUI = {}

MobileUI.MIN_TOUCH_PX = 44

function MobileUI.isTouch(): boolean
	return UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
end

function MobileUI.enforceTouchTarget(button: GuiObject)
	local constraint = button:FindFirstChildOfClass("UISizeConstraint") or Instance.new("UISizeConstraint")
	constraint.MinSize = Vector2.new(MobileUI.MIN_TOUCH_PX, MobileUI.MIN_TOUCH_PX)
	constraint.Parent = button
end

function MobileUI.applySafeArea(screenGui: ScreenGui)
	screenGui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets
	screenGui.IgnoreGuiInset = false
end

function MobileUI.scaleForDevice(screenGui: ScreenGui)
	local scale = screenGui:FindFirstChildOfClass("UIScale") or Instance.new("UIScale")
	scale.Parent = screenGui
	local function update()
		local viewport = workspace.CurrentCamera.ViewportSize
		local shortest = math.min(viewport.X, viewport.Y)
		-- Phones (~360-430px short side) get slightly larger UI for thumbs.
		if MobileUI.isTouch() and shortest < 500 then
			scale.Scale = 1.1
		elseif shortest > 1000 then
			scale.Scale = 0.9
		else
			scale.Scale = 1
		end
	end
	update()
	workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(update)
end

function MobileUI.onTap(button: GuiButton, callback: () -> ())
	return button.Activated:Connect(function()
		if GuiService.MenuIsOpen then
			return
		end
		callback()
	end)
end

return MobileUI
