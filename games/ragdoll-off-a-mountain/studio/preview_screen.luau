-- Edit-mode UI preview: show the HUD plus ONE screen. Change NAME and run in the command bar.
-- Names: LoadingScreen Tutorial RunSummary Shop CannonShop Pets EggHatch Season1Pass DailyRewards
--        Quests Rebirth Codes Announcement   (nil = HUD only)
local NAME = "Shop"
local UIScreens = require(game:GetService("ReplicatedStorage").GameShared.UIScreens)
UIScreens.preview(game:GetService("StarterGui"), NAME)
print("[Preview] showing HUD + " .. tostring(NAME))
