# Ragdoll Off a Mountain — UI Spec (Figma → Roblox)

Tokens: `figma/tokens.json`. Mapping rules: `figma/roblox-mapping.md`. Components: `figma/components.md`.
Owner lessons applied: **L-10** (branch `test/foundation-ui-art`) — item/collectible art comes from
**Blender renders** (`assets/ui/*.png`) in an `Art` image slot, never code-drawn clipart; build ONE
benchmark screen (the Shop) to approval before batching the rest. Layer names below are the
Roblox instance names the client binds to (`src/client/Main.client.luau`).

## Theme reskin — "Avalanche Alpine"
| Element | Treatment |
|---|---|
| Title bar | ice-blue → deep-blue gradient `#5EC8FF → #2590D1`, tiled **snowflake + bone** pattern at 10 % opacity, **snow cap** dripping over the top edge |
| Corner decor | rope coil + orange carabiner hanging off the top-left, little pine sprig bottom-right |
| Close X | chunky red square, white stroked X, with a pink **bandage** strip across one corner |
| Progress bars | bone-shaped end caps (cream `#FFF1CF`), gold fill `#FFD93B`, "SNAP" orange glow `#FF8A1F` at the tip |
| Open animation | window drops in from above with a snow puff (Back.Out 0.35 s) over a rotating sunburst |
| Particles | falling snow on every full-screen window; Season 1 = heavier blizzard |
| Panel body | `#1E1B33` with a subtle frost vignette |

## Screens (Figma frame → ScreenGui)
| # | Frame | ScreenGui | Key layers (Roblox names) | States |
|---|---|---|---|---|
| 1 | HUD | `HUD` | `Cash`, `Gems` (counters + "+"), `LaunchButton` (giant orange pill, hold-to-charge), `ChargeBar.Fill`, `LiftButton`, left rail `ShopButton` `PetsButton` `IndexButton`, right rail **`X2CashButton`** (owned tier + next tier + price CONFIG_REQUIRED), `RewardsButton` (Daily/Quests/Season), top `PeakPill` (current peak name + multiplier), `Boosts` (live countdowns), centre-top `NextGoalBar` (next peak / rebirth), `EventBanner` | normal, charging, running (launch disabled), boost active |
| 2 | Loading | `LoadingScreen` | `Logo`, `Bar.Fill` (real `ContentProvider:PreloadAsync` progress), `Tip`, `SkipButton` (after 8 s) | loading, slow (skip shown), done |
| 3 | Tutorial pointer | `Tutorial` | `Arrow` (world beam / screen arrow), `Caption`, `SkipButton`, `ReplayButton` (settings) | 5 steps from `Config.tutorial` |
| 4 | Bone pops | world `BillboardGui` | "+$1.2K CRITICAL x1.4 / SNAP x3! SKULL" | normal, critical (orange + shake), combo |
| 5 | Run summary | `RunSummary` | `Bones` ("87 / 206"), `Cash`, `Combo`, `NewBest`, skeleton silhouette `Skeleton` (parts light up), `FullSkeletonStamp` | normal, new best, FULL SKELETON |
| 6 | **Shop (BENCHMARK)** | `Shop` | `Featured` (Blender hero render, countdown, strikethrough price), `Offers` (3 stacked cards small/medium/best), `RarityStrip` (1-in-N odds), `PremiumPromo` (Season 1 / VIP), `GiftButton` | normal, owned, locked, loading |
| 7 | Cannon shop | `CannonShop` | 6 `CannonCard`s with Blender renders `cannon_<n>.png`, speed stat bar, price, `BuyButton` | owned / next / locked "???" |
| 8 | Upgrades | `Upgrades` | `BoneValue`, `Brittle`, `Bounce`, `ComboTime` rows (level, next cost, effect), `LuckyBones` Gem ladder | can afford, cannot, maxed |
| 9 | Peaks | `Peaks` | 5 `PeakCard`s (biome render, multiplier, height, unlock cost), `SelectButton` | selected, unlocked, locked |
| 10 | Egg hatch | `EggHatch` | egg render, `OddsStrip` (rarity → "1 in N"), `PityCounter` ("Legendary in 23"), `HatchButton`, reveal ladder | idle, rolling, reveal per rarity, mythic+ cinematic (skip + reduced motion) |
| 11 | Pets | `Pets` | grid (filters/search), `DetailPanel` (power, mutation), `EquipButton`, slots "3/3 (+1 pass)" | equipped, locked, full |
| 12 | Skeleton Index | `SkeletonIndex` | skeleton diagram, 15 part groups found/not found, pet index "Found 5/38", claim rewards | seen / owned / claimed |
| 13 | Daily rewards | `DailyRewards` | 7-day grid, day 7 big prize card, streak, countdown | claimable glow, claimed stamp, locked |
| 14 | Playtime | `Playtime` | 4 timed chests with countdowns | counting, ready, claimed |
| 15 | Quests | `Quests` | Daily / Weekly tabs, rows with progress bars + reset countdown | in progress, complete (glow), claimed |
| 16 | Season 1 Pass | `Season1Pass` | 50-tier virtualized scroll, free + premium rows, XP bar, `PremiumButton` (CONFIG_REQUIRED) | locked, claimable, claimed, premium-locked |
| 17 | Rebirth | `Rebirth` | cost, progress, what resets / what stays (explicit lists), `ConfirmButton` | can't afford, confirm |
| 18 | Codes | `Codes` | `CodeBox`, `RedeemButton`, result text | success, invalid, expired, redeemed |
| 19 | Settings | `Settings` | Music, UI SFX, Reduce Motion, Replay tutorial | toggles |
| 20 | Leaderboards | world `SurfaceGui` on `LeaderboardBones` / `LeaderboardRun` | top 50 rows, your rank | loading, populated |
| 21 | Announcement | `Announcement` | `Text` banner slide-in | Full Skeleton, Mythic/Secret hatch |
| 22 | Base sign | world `SurfaceGui` on `OwnerSign` / `TrophyBoard` | owner name, best run, total bones, stage name | free base, owned |

## Item art (from Blender, `games/ragdoll-off-a-mountain/assets/ui/`)
`cannon_1..5.png`, `pet_pebble_pup.png`, `pet_avalanche_pug.png`, `pet_skelly_cat.png`, `egg_trailhead.png`,
`icon_cash.png`, `icon_gem.png` — transparent 1024² hero renders (key + rim + fill). Upload as Decals
needs owner approval (account action).

## Motion (UIAnim / standards UI_ANIMATION_STANDARDS)
Hover 1.06 + lift 150 ms · press 0.95 → spring · open 0.85 → 1.03 → 1.0 · claim = flash + burst text +
confetti + stamp · bars animate to server-confirmed values · countdowns live · Reduce Motion disables
shake/shine/particles.

## Status
- Spec: ✅ written (this file).
- Figma file: see `figma.json` (benchmark Shop frame only — pending owner approval per L-10).
- Roblox ScreenGuis: ❌ not built (needs Studio MCP). Client falls back to a labelled DEV HUD.
