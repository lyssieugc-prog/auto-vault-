# Ragdoll Off a Mountain 🏔️ — Game Design Spec

> Filled by `/make-game` step 3. Inferred decisions are marked *(inferred)* so the owner can
> override them. Also follows the owner's permanent standards on branch
> `test/foundation-ui-art` (`standards/GAME_SYSTEMS.md`): **no trading**, x2→x128 ladder,
> 6 players / 6 progressive bases, 50-tier Season 1 pass, odds shown as "1 in N". Prices,
> product IDs and season dates are **CONFIG_REQUIRED** (0 / nil placeholders).

## 1. Brief
| Field | Value |
|---|---|
| Name | Ragdoll Off a Mountain 🏔️ |
| Pitch (owner's words) | "Mix: the ragdoll trend + an incremental. Loop: throw yourself off a cliff, and every bone you break earns cash. Buy higher cliffs, launch cannons and pets that hit harder. Why it works: ragdoll games are flooding the chart, but nearly all of them are sandboxes with no progression. This adds a loop that keeps people coming back." |
| Genre (primary / borrowed) | `genres/simulator.md` (incremental) / borrowed: Plots (bases) from `brainrot-steal`, meme tags + money pops from brainrot |
| Style profile | `style/profiles/simulator.md` (+ brainrot UI tags/pops) |
| Theme / setting | One giant stepped cartoon mountain with 5 launch peaks stacked by altitude above a bouncy landing valley ("the Bone Zone") and 6 base camps |
| Theme palette | Mountain stone `#8E96A3`/`#6E7683`, alpine green `#4CC24A`, snow `#F4FBFF`; accent **bone cream `#FFF1CF`** + glow **"SNAP!" orange `#FF8A1F`** and cash gold `#FFD93B` |
| One-sentence fantasy | "I fling my blocky self off ever-higher mountains with ever-bigger cannons and get rich off every bone I break." |
| 15-second activity | Aim + charge at the cliff edge → launch → tumble down the cliff face hitting ledges, bumpers and trees → "+$ SNAP! Left Femur" pops stack into a combo → land in the Bone Zone → run summary card |
| 2–5-minute goal | Buy the next cannon or Brittle Bones level; hatch an egg for a harder-hitting pet |
| 15–30-minute goal | Unlock the next peak (bigger multiplier, new biome); upgrade your base camp a stage |
| Repeat/return hook | Daily streak + daily/weekly quests, "break all 206 bones" Skeleton Index, Season 1 pass, rebirth for a permanent multiplier |
| Core loop | launch off a peak → bone breaks earn Cash → buy cannons/upgrades/eggs → unlock higher peak → rebirth |
| Main currency / icon | **Cash** (gold coin stamped with a bone) · secondary **Gems** (earned only: quests, daily, Full Skeleton) |
| Collectible type | **Pets ("Crash Buddies")** — explicitly in the pitch: they ride along and make you *hit harder* (impact multiplier) — plus the **Skeleton Index** (break every bone group at least once) |
| Rarity ladder | Common → Uncommon → Rare → Epic → Legendary → Mythic → Secret |
| Hero creature | **Avalanche Pug** (Legendary) — a chunky snow-pug in a crash helmet *(inferred)* |
| Season 1 pass theme | "Season 1: AVALANCHE" — icy blue/white frames, falling snow particles *(inferred)* |
| UI frame decor | Snow caps dripping over title bars, rope + carabiner corner hangers, bandage-cross close X, bone-shaped progress bar caps *(inferred)* |
| Players / bases | 6 players max per server, 6 base camps (one per player) |

## 2. World (all geometry from Blender — `games/ragdoll-off-a-mountain/blender/`)
Scale: 1 Blender unit = 1 stud, R6 player = 5 studs. Map ~ 900 × 700 studs → **StreamingEnabled**.

| Region | Size / position | Purpose | Blender source |
|---|---|---|---|
| **The Bone Zone** (hub/landing valley) | 220 × 180 stud basin at y=0, south of the mountain | Landing area: stepped turf terraces, giant hay-bale and trampoline bouncers, score rings, the Bone Clinic, shops ring, Rebirth statue (giant cheerful skeleton holding a trophy) | `map.py` → `Map_BoneZone` |
| **Base camps ×6** | Semicircle on the valley's south rim, 48 × 40 studs each, all facing the mountain (north) | Spawn + respawn after a run, pet display, trophy board, Lift pad (teleport up to your current peak). 5 visual stages | `base_camp.py` → `BaseCamp_Stage1..5` + `layout.json` markers `Base1..6` |
| **Peak 1 — Pebble Hill** | launch pad y=120 | grass + gold flowers, chunky rocks, wooden fences | `map.py` → `Map_Peak1` |
| **Peak 2 — Pine Ridge** | y=260 | pine clusters, snow-dusted ledges, log ramps | `Map_Peak2` |
| **Peak 3 — Frostbite Cliffs** | y=420 | ice shelves, icicle curtains, frozen waterfall, ice bumpers | `Map_Peak3` |
| **Peak 4 — Magma Spire** | y=620 | basalt steps, glowing lava cracks (neon), steam vents | `Map_Peak4` |
| **Peak 5 — Stormcrown Summit** | y=880 | purple crystal crown, floating cloud steps, lightning rods (neon cyan) | `Map_Peak5` |
| **Cliff faces** | Below each peak's launch lip | stepped rectangular terraces (1.5–6 stud steps), bumper rocks, sign posts, pine/ice/lava props — every impact surface is a scoring opportunity | part of each `Map_PeakN` chunk |

Each peak's launch pad: studded wooden/stone deck with hazard-stripe lip, flag, distance markers,
cannon mount marker (`CannonMountN`), zone gate (studded arch + lock sign + price) at the lift.
Landmarks: waterfall from Peak 3 into the valley lake ring, chevron path from bases → shops → lift.

Shops ring in the Bone Zone (markers in `layout.json`): `EggStand1..5` (one egg per peak, a peak's
egg is buyable once that peak is unlocked), `CannonShop`, `UpgradeStand`, `RebirthStatue`,
`SeasonBoard`, `LeaderboardBones`, `LeaderboardRun`, `DailyChest`.

## 3. Content tables (all numbers live in `src/shared/Config.luau`)

### 3.1 Scoring (the core rule — `src/shared/RagdollScore.luau`)
- The server simulates the ragdoll (network owner = server) and reports **impacts**: `{ part, speed }`
  where speed = sudden velocity change of that body part (studs/s).
- `effective = speed × impactMultiplier` where impactMultiplier = `1 + Σ equipped pet power`
  × Brittle Bones upgrade × "Glass Bones" pass.
- If `effective ≥ breakSpeed` (45): breaks `1 + floor((effective − breakSpeed) / 25)` bones in that
  body part (capped by bones left in that part this run).
- Cash per bone = `boneValue[part] × severity × combo × peakMultiplier`, severity =
  `clamp(effective / breakSpeed, 1, 8)` ("CRITICAL!" ≥ 4).
- **Combo**: each break within `comboWindow` (1.2 s + upgrades) of the last adds +0.1×, max ×3.
- **Full Skeleton**: all **206** bones in one run → run cash ×2 + 25 Gems + server announcement.
- Run ends when the body rests (< 3 studs/s for 1.5 s), enters the landing net, or 25 s pass.
- Run cash is paid through `Currency:earn` (rebirth, x2 ladder, VIP, boosts, base stage, friends).

| Body part (R15) | Bones | Value / bone |
|---|---|---|
| Head (skull + jaw) | 29 | 6 |
| UpperTorso (ribs, sternum, spine) | 41 | 3 |
| LowerTorso (pelvis, lumbar) | 14 | 3 |
| Left/RightUpperArm (humerus, shoulder) | 3 each | 2 |
| Left/RightLowerArm (radius, ulna) | 2 each | 2 |
| Left/RightHand | 27 each | 1 |
| Left/RightUpperLeg (femur, patella) | 2 each | 4 |
| Left/RightLowerLeg (tibia, fibula) | 2 each | 3 |
| Left/RightFoot | 25 each | 1 |
| **Total** | **206** | |

### 3.2 Peaks (zones — tier ladder `Peak`)
| # | Peak | Unlock cost (Cash) | Cash multiplier | Launch height |
|---|---|---|---|---|
| 1 | Pebble Hill | free | ×1 | 120 |
| 2 | Pine Ridge | 2,500 | ×4 | 260 |
| 3 | Frostbite Cliffs | 120,000 | ×15 | 420 |
| 4 | Magma Spire | 6,000,000 | ×60 | 620 |
| 5 | Stormcrown Summit | 350,000,000 | ×250 | 880 |

### 3.3 Cannons (tier ladder `Cannon` — launch speed, studs/s)
| # | Cannon | Cost (Cash) | Launch speed |
|---|---|---|---|
| 0 | Bare Feet (jump) | — | 40 |
| 1 | Party Popper | 500 | 70 |
| 2 | Barrel Blaster | 12,000 | 100 |
| 3 | Rocket Rig | 400,000 | 140 |
| 4 | Mega Mortar | 15,000,000 | 190 |
| 5 | Meteor Launcher | 600,000,000 | 250 |

### 3.4 Upgrades (leveled, Cash)
| Key | Effect | Base cost | Growth | Max |
|---|---|---|---|---|
| BoneValue | Cash per bone ×(1 + 0.25·lvl) | 100 | 1.55 | 30 |
| Brittle | impact ×(1 + 0.05·lvl) | 250 | 1.6 | 20 |
| Bounce | ragdoll elasticity +0.03·lvl (more impacts) | 400 | 1.7 | 10 |
| ComboTime | combo window +0.15 s·lvl | 300 | 1.65 | 10 |
| LuckyBones (Gems ladder) | crit chance 0/5/10/15/20/25 % (severity ×2) | 10, 40, 150, 600, 2500 Gems | — | 5 |

### 3.5 Pets — "Crash Buddies" (`power` adds to the impact multiplier)
5 eggs (one per peak), each with all 7 tiers. Secret **Skelly-Cat** is shared by all eggs.

| Egg (cost) | Common | Common | Uncommon | Rare | Epic | Legendary | Mythic |
|---|---|---|---|---|---|---|---|
| Trailhead Egg (150) | Pebble Pup 0.10 | Goatling 0.12 | Backpack Beaver 0.25 | Helmet Hedgehog 0.5 | Boulder Bull 1.0 | **Avalanche Pug** 2.0 | Thunder Yak 5 |
| Pine Egg (6K) | Pinecone Pig 0.4 | Lumber Lynx 0.45 | Moose Mallet 0.9 | Owl Ranger 1.8 | Bear-ricade 3.5 | Timber Wolf 7 | Sasquash 18 |
| Frost Egg (300K) | Snowball Seal 1.5 | Icicle Imp 1.7 | Sled Husky 3.4 | Penguin Pilot 7 | Glacier Walrus 14 | Yeti Yeeter 28 | Blizzard Bison 70 |
| Magma Egg (15M) | Ember Newt 6 | Cinder Crab 7 | Lava Llama 14 | Obsidian Ox 28 | Magma Mammoth 55 | Volcano Dragon 110 | Phoenix Pancake 280 |
| Storm Egg (750M) | Static Sheep 24 | Cloud Calf 28 | Zap Ferret 56 | Thunderbird 110 | Storm Rhino 220 | Sky Kraken 450 | Lightning Lion 1,100 |
| all eggs | — | — | — | — | — | — | Secret: **Skelly-Cat** 2,500 |

Odds (base weights 600/250/100/40/9/0.9/0.1 → shown as **1 in N**: Common 1 in 1.7, Uncommon 1 in 4,
Rare 1 in 10, Epic 1 in 25, Legendary 1 in 111, Mythic 1 in 1,111, Secret 1 in 10,000). Pity: Legendary+
guaranteed within 75 hatches per egg. Mutations: Gold (1 in 20, ×2), Rainbow (1 in 100, ×5).
Equip 3 (+1 with pass). Inventory 200.

### 3.6 Base camp stages (6 bases, `Plots` count 6)
| Stage | Model | Requirement | Bonus |
|---|---|---|---|
| 1 | Trail Tent (tent, campfire, sleeping bag, sign) | start | — |
| 2 | Log Cabin | Peak 2 unlocked (ever) | +5 % Cash |
| 3 | Ski Lodge (balcony, ski rack, trophy shelf) | Peak 3 | +10 % |
| 4 | Alpine Chalet + trophy tower | Peak 4 | +15 % |
| 5 | Summit Hall (bone-trophy spire, banners) | Peak 5 **or** 1 rebirth | +25 % |
Stage = highest ever reached (rebirth never downgrades a base).

### 3.7 Rebirth
Cost 1B Cash × 3^n. Resets Cash, peaks, cannons, Cash upgrades. Keeps pets, Gems, base stage,
Skeleton Index, Season pass. Permanent multiplier +0.5× per rebirth. Confirmation dialog previews resets.

### 3.8 Rewards & retention
- **Daily (7-day)**: 200 Cash · 1K Cash · 5 Gems · 10K Cash · 15 Gems · 15-min x2 Cash boost · **Backpack Beaver (Uncommon pet)** + 50 Gems. Missed day resets streak to day 1 (UTC days).
- **Playtime (per session)**: 5 min 500 Cash · 15 min 10 Gems · 30 min 15-min Lucky boost · 60 min 40 Gems.
- **Daily quests** (reset UTC midnight): break 100 bones (1K Cash) · do 10 launches (5 Gems) · land a ×2 combo (2K Cash).
- **Weekly quests** (reset Monday 00:00 UTC): break 5,000 bones (50 Gems) · Full Skeleton once (100 Gems) · hatch 25 eggs (40 Gems).
- **Onboarding boost**: finishing the tutorial grants **x2 Cash for 10 minutes** (labelled, countdown).
- **Promo codes** (server-validated, one per user, case-insensitive): `SNAP` 1K Cash, `BONEZONE` 10 Gems *(placeholders — owner approves real codes)*.
- **Leaderboards**: total bones broken (all-time, OrderedDataStore), best single run Cash (server board).
- **Events** (config-driven, no live schedule invented): "Avalanche Hour" ×2 bones value.
- **Announcements**: Full Skeleton, Mythic/Secret hatch (rate-limited 1 per 10 s).
- **Friends bonus**: +10 % Cash per friend in server, max +30 %.
- Offline earnings: **not used** (core loop is active, not passive).

### 3.9 Season 1: AVALANCHE (50 tiers)
XP = 1 per bone broken, +25 per Full Skeleton, quests give XP. Tier n needs `100 + 20·(n−1)` XP.
Free track every tier (Cash/Gems/boosts, trails, base decorations at 10/20/30/40/50); premium track
(CONFIG_REQUIRED price) adds exclusive pets at 25 (Frosty Ragdog) & 50 (Avalanche Skelly), cannon skins,
"Bandaged" ragdoll cosmetics. Season end date: CONFIG_REQUIRED.

### 3.10 Monetization (placeholders only — owner approves real products)
- **x2 Cash ladder** (right HUD rail): x2 → x4 → x8 → x16 → x32 → x64 → x128 max; rising prices CONFIG_REQUIRED.
- Passes: VIP (×1.5 Cash, chat tag), x2 Luck, +1 Pet Equip, Glass Bones (impact ×1.5), Auto-Launch, Season 1 Premium.
- Products: 15-min boosts (x2 Cash, x2 Luck), starter pack, Cash packs (5 tiers scaled to peak).
- No trading, no gifting-as-trading. Purchases only via Roblox prompts; success shown after server confirms.

## 4. Systems used
| System | Config summary | Custom code needed? |
|---|---|---|
| Currency | Cash, Gems; multipliers Rebirth/Ladder/VIP/Base/Boost/Friends/Event | — |
| Upgrades | Peak + Cannon tier ladders, 4 leveled Cash upgrades, LuckyBones Gem ladder | — |
| Rarity | 5 eggs, weights above, pity 75, Gold/Rainbow mutations | — |
| Inventory | 200 cap, 3 equip (+1 pass) | — |
| Rebirth | 1B × 3^n, +0.5×, onReset → Peak/Cannon/Cash upgrades | — |
| Plots | 6 base camps | stage logic in GameLogic |
| Rewards | 7-day daily, playtime, all-time quests | — |
| Tutorial | 6 steps (claim base → lift → launch → see bones → buy upgrade → rewards) | — |
| Monetization | Cash ladder x2..x128, passes | — |
| DataService / Guard / Net | standard | — |
| **RagdollScore** (new, game) | bones per part, break math, combo, Full Skeleton | `src/shared/RagdollScore.luau` |
| **Boosts** (new, vault) | timed multipliers with expiry (onboarding, products, rewards) | `systems/src/Shared/Boosts.luau` |
| **SeasonPass** (new, vault) | 50-tier XP curve, free/premium claims | `systems/src/Shared/SeasonPass.luau` |
| **PeriodicQuests** (new, vault) | daily + weekly quests with UTC reset | `systems/src/Shared/PeriodicQuests.luau` |
| **Codes** (new, vault) | promo codes, one redemption per user | `systems/src/Shared/Codes.luau` |
| Trading | **Prohibited — not used** | — |

## 5. UI screens (Figma → ScreenGui)
HUD · LoadingScreen · Tutorial pointer · RunSummary ("BONES BROKEN 87/206") · BonePops (world
billboards) · Shop (benchmark screen) · CannonShop · Upgrades · EggHatch (odds strip 1-in-N + pity) ·
Pets inventory · SkeletonIndex · DailyRewards · Playtime · Quests · Season1Pass · Rebirth confirm ·
Codes · Settings (sounds, reduce motion) · Leaderboards (world SurfaceGuis) · Announcement toast.
Full layer spec: `figma/ui-spec.md`.

## 6. Monetization — see §3.10 (CONFIG_REQUIRED everywhere)

## 7. Economy pacing targets
| Milestone | Target |
|---|---|
| First launch | < 30 s (tutorial walks base → lift → pad) |
| First cash | first launch (~60–150 Cash off Pebble Hill) |
| First purchase (Party Popper cannon / Brittle 1) | < 2 min |
| First egg | < 3 min |
| Peak 2 | ~8 min |
| Peak 3 | ~20 min |
| First rebirth | ~45–60 min |

## 8. Out of scope for v1
Moving obstacles, ragdoll skins beyond Season rewards, PvP shoving, custom cliffs editor,
trading (prohibited), real product IDs/prices, live event schedule.
