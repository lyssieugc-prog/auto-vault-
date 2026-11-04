# House Style (applies to every game unless a profile overrides it)

Source: owner's `game-style-vault` skill plus the vault setup brief. Profiles in `style/profiles/`
override **only what they say**; everything else here stays on.

## 0. Core aesthetic
- Colorful, **deliberately blocky** Roblox simulator / brainrot look. Chunky rounded blocks,
  flat saturated colors, **visible studs** on floors, platforms, plot bases and walls where
  real Roblox bricks would have them.
- Recognizable Roblox character proportions (R15 blocky). Collectibles may be stylized but must
  read as "Roblox".
- Readable silhouettes, strong value contrast, max saturation, daytime lighting.
- Detail comes from *many small chunky parts and color breakup*, not from polygon density.
- **Never** substitute smooth, generic, realistic "AI-looking" models.
- Mobile-first performance: see `qa/performance-budget.md`.

## 1. UI — must haves
**Look**
- Thick saturated title bar (red/yellow/blue or theme color) with an oversized, slightly tilted
  icon breaking the top-left corner.
- Big white title text, heavy dark stroke + drop shadow. Panel body dark navy/purple `#1E1B33`.
- Chunky square red close X with a white stroked X.
- Every card: saturated color block + UIGradient + sunburst rays + tiled stud texture, lighter
  inner border + dark outer stroke, big glossy 3D item render.
- Lime-green pill buy buttons with Robux icon + white outlined price; darker 4–6px bottom lip,
  white gloss stripe on top.
- Angled corner tags (-3° to -10°): New!, EXCLUSIVE, SECRET, MYTHIC!, LIMITED!, BEST DEAL!, SAVE %.
- Rarity color-coding; Mythic = animated rainbow gradient stroke; locked = dark "???" silhouette.
- Locked / Claimed states, progress bars, "Found 5/52" counters.

**Fonts & colors** (tokens live in `figma/tokens.json`)
- Fredoka One for titles, buttons, numbers. Heavy sans (Builder Sans Heavy / Gotham Black) for
  ALL-CAPS banners.
- Text: white fill + UIStroke `#1A1A1A` 2–4px + dark offset shadow. Accents gold `#FFD93B`,
  lime `#A8F03C`.
- Palette: red `#E13A2A→#B6261D`, green `#7ADE43` (lip `#57AC35`), blue `#2590D1`/`#326BE3`,
  yellow `#E2C608`, purple `#B678EA`, pink `#DD70E1`, lime `#78BE0E`.
- UICorner ~0.3 on buttons. Scale-only sizing, TextScaled, UIStroke ScaledSize.

**Theme reskin (every game)**: frame decor on corners/edges themed to the game, patterned title
bar, themed close X, themed open animation. Seasonal events reskin frames + falling particles.

**Required screens**: HUD (left Shop/Index/Store, right collectibles, top nav pills, bottom
hotbar, currency counters with "+", center progress bar, event timer) · Shop (featured/limited
with countdown + strikethrough price, starter pack, gamepass grid, timed boosts, 5-tier currency
packs, gift button) · Egg/lucky roll with odds strip + pity counter · Daily Rewards 7-day grid +
Playtime Rewards · Index with claim rewards · Upgrades (x2 → x1,250) · Season 1 Pass.

## 2. UI animation — nothing static
Back/elastic pop-open over a rotating sunburst · cards stagger 0.05s · hover 1.05 + tilt, press
0.95 · claimables glow + bob · CLAIM = flash, burst text, confetti, shockwave, stamp, bar fill,
fly-away · screen transition wipes · headers scramble/type in · errors slam in · live countdowns
on all timed things · icons/sunbursts idle forever. (Implemented by `systems/src/Client/UIAnim`.)

## 3. Maps / world
- Bright saturated daytime cartoon world, stud textures. Central spawn plaza → radiating paths →
  zones. Open center, dense edges. **Large maps, every area has a purpose.**
- Landmarks: water ring + bridges, terraced cliffs, waterfall, themed props per zone.
- Each zone: entry name pop-up, own sub-palette, harder content + better rewards, gated by
  power/rebirth.
- Plots with display grids (if the game has bases). Glowing egg/portal shop with silhouettes.
- Colored chevron roads guide players to shops and the next zone. Ambient particles per theme.
- Floating labels over key objects ("next goal" banner).
- All map geometry is authored in Blender (`blender/templates/map_layout.py`).

## 4. 3D models / pets / creatures
**GOOD**: many small chunky parts (scales, spikes, teeth, voxels); one strong elemental theme;
1–2 hue body + bright glow accent; glowing eyes; emissive cracks/edges; particles, orbiting
props; oversized distinct silhouette; idle loop.
**BAD (never)**: few big plain boxes, single flat color, no glow/VFX, no theme, generic realistic
animal, Minecraft-mob look, smooth generic AI model.

**Pet minimums** (owner rejected creature v1 — see `references/images/rejected/`):
- Chibi Roblox-pet proportions: head is the biggest part (≥ 1.4× body height), stubby legs.
- **Studs on the pet itself** (top of head + back), not only on the map.
- A real face: big white eyes + pupils + sparkle highlights, blush, mouth (teeth/tongue).
- ≥ 5 colours: body, light belly/muzzle, dark trim/pattern, glow accent, face colours.
- ≥ 50 parts before join; **no blank faces from any angle** (front, side, back all detailed).
- A theme feature that changes the silhouette (crest, horns, flame tail, fins…).
- Enforced by `blender/tests/test_pipeline.py`; looks are judged by the owner from 3-angle renders.

**Approval loop**: new model → 3-angle render → owner says GOOD/BAD → GOOD goes to
`references/images/approved/` (becomes the bar to beat), BAD to `references/images/rejected/`
with the reason in `references/catalog.md`.
- Rarer = more glow, particles, orbiting props, bigger aura.
- Write a model handoff (`blender/handoff-template.md`), preview (GLB/OBJ), then build in Blender.

## 5. VFX, cutscenes & camera
Anticipation ≥1s before impacts · impact = 1–3 frame flash + shake + burst, hold 0.5–1s · shot
order: wide → face close-up → 3/4 action → low-angle hero → title slam (~2.5s) · push-ins,
blackout before reveals, silhouette first · rarity reveal ladders up ~1s per step, rarer = bigger
· bosses get reveal + attack VFX · weapons: 4 attacks + dash/block/dodge/stun · skip button after
first view.

## 6. Loop & systems (always on)
Something to buy every few minutes · rebirth with visible next goal · timed server events with
banner + countdown · index with rewards · daily + playtime rewards · pity · zones unlock with
progress.

## 7. Monetization (always on — configure, never publish/buy without approval)
"2x (something)" pass that upgrades every repurchase up to 100x · strong passes (x2 Cash,
x2 Luck, VIP, +Pet Equip, Auto-collect, faster attacks) · Season 1 pass themed to the game ·
15-min boosts, potion bundles, starter pack, limited exclusives with countdowns, server luck,
gifting.

## 8. Thumbnail & promo
Diagonal before→after split, same avatar sad vs smug with aura, tiny "+1" vs huge gold "+7M", no
title text, heavy outlines, max saturation. Promo: BEFORE/NOW pills, word-by-word gold captions,
logo + release time.

## 9. Final check (every build) — see `qa/checklist.md`
Kid-showing-best-friend test · anything static? · any BAD-list model? · 2x→100x, Season pass,
daily/playtime, index, rebirth present? · UI themed to THIS game?
