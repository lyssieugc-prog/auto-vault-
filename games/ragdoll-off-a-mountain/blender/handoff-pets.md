# Model Handoff — Crash Buddies pets, Trailhead Egg, currency icons

Game: `ragdoll-off-a-mountain` · Profile: `simulator` (+ brainrot UI pops) · Script: `blender/pets.py`
Template technique reference: `blender/templates/creature.py` (part-count / face / rarity ladder ideas only —
the dog-like v2 LavaPup is NOT reused or reskinned) and the merged-block Frappo construction
(`VoxelCanvas` → 0.5-stud cells, no colour noise). Every model below is an original design for this game.

## Style rules that apply (house-style §4 + bible §1/§2/§7/§13)
- MERGED VOXEL language: main masses (head, torso, legs) are one 0.5-stud merged-block mesh per pet,
  painted in regions (belly, mask, patches) — never per-voxel colour noise, never smooth blobs.
- Crisp cartoon face from flat pieces seated on a FLAT face plane: eyes ≥ 25 % head width each, white +
  pupil + sparkle, blush, mouth ≥ 50 % head width with tongue/teeth inside.
- Chibi: head height ≥ 1.4 × torso height, stubby legs. ≥ 5 colours, ≥ 2 shades per material.
- ≥ 50 parts before join; front, side and back all carry detail; one silhouette feature per pet.
- Studs = texture only (`vault_blocky.stud_surface`, 0.5-stud world-space) on every non-face, non-neon,
  non-glass piece. Rarer = more glow, orbiters, bigger aura. Detail fits the creature (no pug spikes).
- Export: ≤ 3 meshes per model (`Body`, `Glass`, `Neon`) + a separate `_FX` mesh (orbiters + aura) so
  Studio can spin/bob it. ≤ 15k tris per mesh. Front faces +Y, pivot bottom-centre, 1 unit = 1 stud.

## Shared palette (game theme: stone, alpine green, snow, bone cream `#FFF1CF`, SNAP orange `#FF8A1F`, gold `#FFD93B`)
| Role | Hex |
|---|---|
| Eye white / pupil / sparkle | `#FFFFFF` / `#1A1A2E` / `#FFFFFF` (emissive 1.5) |
| Blush / tongue / mouth | `#FF8FB1` / `#FF6F9B` / `#2A1420` |

---
## 1. Pebble Pup (Common, power 0.10) — ~4.4 studs tall
| Role | Hex |
|---|---|
| Pebble body (3 shades) | `#A9A39A` / `#8E8880` / `#C9C3B8` |
| Muzzle / belly / paw pads | `#EFE3CC` |
| Moss (3 shades) | `#6FCB4A` / `#4FA83A` / `#9BE36A` |
| Backpack (main / dark / trim) | `#E8432E` / `#B02A1F` / `#FFD93B` |
| Bedroll | `#2E9BD6` |
| Glow (minimal) | `#FFE27A` clip-on mini lantern only |

| Part | Size (studs) | Position | Colour | Notes |
|---|---|---|---|---|
| Merged body mesh | ~3.8 × 3.6 × 4.4 | centred | pebble + muzzle + moss caps painted in regions | head ellipsoid flattened at front = face plane; torso; 4 stubby legs; muzzle block |
| Pebble chunks ×9 | 0.5–1.0 | back, hips, cheeks, head | 3 pebble shades | rounded, tilted ±15°, the "made of pebbles" read |
| Moss tufts ×6 + sprout (stem + 2 leaves) | 0.3–0.8 | head top, back | moss shades | sprout = silhouette feature with the backpack |
| Floppy ears ×2 (base + tip + moss cap) | 0.9 × 0.5 × 1.2 | head sides, drooping | pebble dark | |
| Face: eyes, pupils, sparkles ×2 each, lids none, blush ×2, nose, mouth, tongue, 2 teeth | — | face plane | face colours | big friendly smile |
| Paw pads ×4 + toes ×12 | 0.25 | leg fronts | muzzle cream | |
| Tail: 3 stacked pebbles + moss tip | 0.4–0.6 | back, rising | pebble / moss | |
| Backpack: body, top flap, buckle, front pocket, 2 side pockets, 2 shoulder straps, chest strap, bedroll + 2 ties, carabiner, lantern (neon) | 0.2–1.8 | on the back | pack colours | back view hero detail |
| Bandana (triangle stack 3 pieces) | 1.6 wide | neck front | `#2E9BD6` | |
Silhouette: a big round-headed pup with a sprout on top and a boxy backpack + bedroll hump on its back.

## 2. Avalanche Pug (Legendary, power 2.0, HERO) — ~5.6 studs tall + FX
| Role | Hex |
|---|---|
| Snow body (3 shades) | `#F4FBFF` / `#D6E8F5` / `#FFFFFF` |
| Pug mask / ears / wrinkles (ice-blue, 3 shades) | `#7FC4F0` / `#4E96D6` / `#3A6FB0` |
| Crash helmet (SNAP orange, 3 shades) | `#FF8A1F` / `#E06A0C` / `#FFB066` |
| Helmet stripe / stickers | `#FFFFFF` / `#FFD93B` / `#1A1A2E` |
| Goggles frame / strap | `#2E3A55` / `#1E2740` |
| Visor (glass) | `#9BE1FF` |
| Ice glow (neon) | `#7CF7FF` / `#BFFBFF` |

| Part | Size | Position | Colour | Notes |
|---|---|---|---|---|
| Merged body mesh | ~4.4 × 4 × 4.6 | centred | snow + ice-blue mask region + belly | wide flat pug face plane, chunky torso, 4 stubby legs, stepped curly tail stub |
| Crash helmet merged dome (separate merged mesh) | 4.0 × 3.6 × 1.6 | head top | orange + white centre stripe | DENT carved on the left (darker dent floor + 3 crack bits) |
| Helmet brim, chin straps ×2 + buckle, ear guards ×2, stickers (bone, star, "2" plate) | — | helmet | orange dark / gold / navy | |
| Visor flipped up (glass) + 2 hinges | 3.2 × 0.25 × 0.9 | helmet front | glass | |
| Goggles: strap band, 2 frames, 2 glowing lenses, bridge | — | helmet front above visor | navy + neon ice | |
| Snowball cheeks ×2 (big) + 4 small snow puffs | 1.1–1.4 | face sides | snow light | round = snowball (fits) |
| Pug wrinkles ×3 (stepped bands) + forehead mask | — | face plane above eyes | ice-blue dark | |
| Folded ears ×2 (base + flap) | 0.9 | head sides | ice-blue dark | |
| Face: eyes/pupils/sparkles ×2, blush ×2, nose, jowls ×2, open mouth, tongue, 2 teeth | — | face | face colours | |
| Frosty mane tufts ×12 (two rows) | 0.6–0.9 | neck ring | snow / ice light / ice | tilted rounded clumps, NOT spikes |
| Snowflake collar tag (neon) + collar band | — | chest | ice | |
| Paws ×4 + glowing ice toe pads ×12 | — | legs | snow / neon | icy glow accent |
| Curly tail: 4 stepped segments + glowing snowball tip | — | back | snow / ice | back-view detail |
| Back: frost saddle patch + 3 snowflake decals (raised) + helmet back stripe + number plate | — | back | ice | |
| FX: 8 snowflake orbiters (3 crossed bars + core each), 2-ring aura (24 + 16 segments), 6 frost sparkles | — | around | neon ice | Studio spins `_FX` |
Silhouette: a wide, flat-faced snow pug whose orange helmet dome + goggles + fluffy mane collar read at 50 studs.

## 3. Skelly-Cat (Secret, power 2,500) — ~5.0 studs tall + FX
| Role | Hex |
|---|---|
| Bone cream (3 shades) | `#FFF1CF` / `#E8D3A2` / `#FFFAEB` |
| Soft body core (between bones) | `#4B3A78` / `#33275A` (deep plum = friendly, not black) |
| Eye glow (neon) | `#7DFFE9` (mint) with `#1A1A2E` pupils + white sparkle |
| Collar + bell | `#FF3EC8` (neon pink) / `#FFD93B` |
| Rainbow aura | `#FF4D6D #FF9F1C #FFE14D #5CFF7A #4DC3FF #B26BFF` |

| Part | Size | Position | Colour | Notes |
|---|---|---|---|---|
| Merged body mesh | ~3.8 × 3.6 × 4.4 | centred | plum core torso + cream skull head + cream rib bands painted around torso | skull-ish head with flat face plane, stepped cat ears in the voxel mass |
| Rib bands ×4 per side (separate raised bone bars) + sternum + spine vertebrae ×5 + pelvis plate | 0.3–0.5 | torso | bone shades | the "made of bones" read from side + back |
| Leg bones ×4: shaft + 2 knob joints + paw (toes ×3) | — | legs | bone | |
| Skull face: eye sockets ×2 (plum rims), glowing mint eyes + pupils + sparkles, nose hole (heart), stitched grin + 4 square teeth, blush ×2, cheekbones ×2 | — | face plane | | cute, wide-eyed, smiling |
| Inner ears ×2 (pink) + ear tips | — | ears | | |
| Bone tail: 6 vertebra segments rising in a curl + cartoon bone tip (shaft + 4 knobs) | — | back | bone | silhouette feature |
| Neon collar band + gold bell + bell slot | — | neck | pink neon / gold | |
| Skull-top stitch line + 2 crack doodles (cute) | — | head top/back | bone dark | back of head detail |
| FX: rainbow aura ring (24 segments, 6 hues) + inner glow ring, 6 orbiting cartoon bones (neon tips), 8 sparkles | — | around | rainbow neon | Secret = most glow |
Silhouette: a big-headed cat with pointed ears and a tall curling bone-tail ending in a cartoon bone, ringed by a rainbow halo.

## 4. Trailhead Egg — ~6 studs tall
Merged-block egg (one mesh) painted as stacked RINGS: alpine-green base ring → stone band → snowy
zig-zag peak band → cream top. Separate pieces: braided rope band (24 twisted segments), orange
carabiner (recolorable material `EggAccent`) + gate + glowing gem, 3 trail-marker blazes, small
mountain-flag topper (stepped rock + snow cap + pole + flag in `EggAccent`), base stand ring (6 rocks + grass tufts).
Silhouette: tall stepped egg with a rope belt and a tiny flag on top.

## 5. Currency icons (models for UI renders)
- **Cash coin**: thick 16-side gold coin (`#FFD93B` / `#E0A800` / `#FFF08A`), raised rim ring, recessed
  inner disc, raised bone stamp (shaft + 4 knobs) in light gold, 8 rim notches, 2 sparkle glints (neon).
- **Gem "SNAP" crystal**: faceted blocky crystal (table, crown, girdle, pavilion) with per-facet orange-gold
  shades (`#FFB02E` / `#FF8A1F` / `#FFD36B` / `#D9610A`), neon zig-zag SNAP crack across the front, inner glow
  core, 4 sparkle glints. Crystal = glass-like exception (no studs on facets).

## Studio-side extras (added in Studio, not modelled)
`_FX` mesh: rotate around Z (orbiters 40°/s, aura -20°/s), bob 0.25 studs. ParticleEmitters: Pug snow
flurries (rate 6), Skelly-Cat rainbow sparkles (rate 8); PointLight on Neon (Pug ice 8 range, Cat mint).
Idle: bounce + head tilt. Attachment `PetRoot` at pivot (bottom-centre).

## Budget
Target tris: pets ≤ 6k each, egg ≤ 4k, icons ≤ 2k (all well under 15k/mesh) · Parts before join: ≥ 60 per pet.
