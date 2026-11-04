# Model Handoff — Map (Bone Zone valley + 5-peak massif + base rim)

Game: `ragdoll-off-a-mountain` · Profile: `simulator` · Rarity: n/a (hero environment) · Template: `map_layout`
(techniques only) + `vault_kit` (terrace_field, path_network, canopy, shades, vignettes)
Script: `games/ragdoll-off-a-mountain/blender/map.py` (build + export) and `map_render.py` (review renders)
→ `assets/export/map/` (FBX per chunk, GLB per chunk, `layout.json`) · previews in `assets/previews/map/`.
Status: PENDING owner approval.

## Style rules that apply (house-style §0/§3/§4, bible ★ §0 §3 §5 §6 §13, simulator profile)
- SOLID language at map scale: big chunky stepped masses, crisp bevels, 0.5-stud TEXTURE studs on all sides
  (world-space UVs) except water / ice glass / neon. Never stud geometry, never coplanar overlaps.
- Terrain = rectangular terraces with visible 1.5–6 stud steps (cliff faces) and 18–36 stud tiers (massif),
  layered: stone body → darker ledge band → grass / snow / ash cap → props.
- Every peak face = a readable FALL LINE: a stepped channel framed by marker poles + rock fins, packed with
  impact features (ledges, bumpers, outcrops, signs, theme props) — every hit is a scoring opportunity.
- Decoration is purposeful vignettes (first-aid station, picnic spot, signposts at forks, flower beds along
  paths, rock gardens, lookout benches) — never uniform random scatter; ≥ 3-stud clear paths everywhere.
- Each zone has its own 2-hue sub-palette + glow accent; ≥ 2 shades per material.
- Kid-friendly: bandages, crutches, stretchers, cartoon bones — no gore, no skulls-as-horror, no Red Cross emblem.
- NEVER: smooth cone mountain, plain boxes, flat empty zones, generic realistic terrain, AI-smooth look.

## Palette
| Role | Hex |
|---|---|
| Mountain stone | `#8E96A3` / `#6E7683` / `#B3BAC4` |
| Alpine grass | `#4CC24A` / `#2E9A3E` / `#86E05A` |
| Snow | `#F4FBFF` / `#D9ECF7` |
| Bone cream (accent) | `#FFF1CF` |
| SNAP orange (glow accent) | `#FF8A1F` |
| Cash gold | `#FFD93B` |
| Hazard | `#FFC21A` + `#1A1A1A` |
| Wood deck | `#B5733A` / `#8A5530` |
| P1 Pebble Hill | grass + gold flowers `#FFD93B`, fence wood |
| P2 Pine Ridge | pine `#1F7A3A`/`#2E9A3E`, logs `#8A5530`, snow dust |
| P3 Frostbite Cliffs | ice `#8FE3FF`/`#5CC8F0`, snow, glacier blue |
| P4 Magma Spire | basalt `#3B3540`/`#2A2530`, lava neon `#FF6A1F` + `#FFC21A` |
| P5 Stormcrown | storm slate `#5A5478`, crystal `#B678EA`/`#8E4FE0`, cloud white, neon cyan `#3EF0FF` |
| Water | `#3EC6FF` / `#2A9BE0` (no studs) |

## Part list (world coords: X east, Y north, Z up; 1 unit = 1 stud)
| Part | Size (studs) | Position | Colour | Notes |
|---|---|---|---|---|
| Valley ground (Map_BoneZone) | ~580 × 380, 10-stud cells | centre (0,-80) | grass 3 tones / dirt body | run-length merged stepped cells, designed terraces 1.5–6 high, flank terraces E/W |
| Landing catch strip | 400 × 90 | y 10 → 100 | turf + mats | hay bales (P1), striped trampolines (P2), target crash mats (P3/P5), bounce cushions (P4) |
| Hub plaza + moat (Map_Lake / Map_BoneZone) | plaza Ø96, moat r48–60, promenade r60–78 | (0,-92) | cream stone / water / slate | 4 bridges N/S/E/W, studded marker pads for shops ring |
| Stream + waterfall | 10 wide | x = 44, foot pool y≈100 → moat | water + ice | cascade down the P3/P4 seam, frozen top section (icicles) |
| Lift plaza | 44 × 26 | (0,-2) | stone + neon cyan ring | LiftPad marker, lift tower + sign, chevrons from hub |
| Base rim (Map_BaseRim) | rim terrace z=4, 6 pads 48 × 40 | arc y≈-216…-185 | stone pad + per-base accent trim | low fences, number plaques, stairs + chevron paths north |
| Massif tiers (Map_PeakN) | 18–36 stud tiers | x -280…300, y 100…850 | biome stone + caps | 3 segments per tier per peak (flank / channel / flank), outcrops, strata bands |
| Cliff face channel | 36 wide, 1.5–6 stud steps, 45–62° per step | below each pad | biome | ledge bands every 4–7 steps with bumpers / signs / props, marker poles at edges |
| Launch pad deck | 30 × 24 | top of face | wood planks + stone frame | hazard lip, flag, height sign (block digits), cannon ring Ø9, side rails |
| Zone gate arch + arrival pad | 18 wide × 16 tall | back of deck | stone + peak colour | lock sign (P2–P5), arrival teleport pad with neon ring |
| Summit spire | 20–60 above pad | behind pad | biome | P5: purple crystal crown + lightning rods |

## Silhouette check
From the south: a five-summit stepped massif climbing west → east like a giant staircase skyline, each summit
crowned differently (rock knob, pine crown, ice fang, glowing volcano spire, purple crystal crown), five
visible vertical fall-line stripes down its face, and a round moat hub with a green valley in front.

## Studio-side extras (added in Studio, not modelled)
Water: Transparency 0.25, Reflectance 0.1. Ice: Glass/Ice material Transparency 0.2. Neon groups → Neon
material. Steam vents / waterfall mist / snow / storm sparks ParticleEmitters; lightning Beam between rods;
PointLights on lamps. Trampolines/hay/mats: Elasticity tuned in Studio (CustomPhysicalProperties).
Zone-gate lock signs become SurfaceGui price boards; LandingZone box = trigger region. StreamingEnabled on.

## Budget
Target tris: ≤ 15k per exported mesh; whole map ≈ 350k; exported as one mesh per colour group per chunk
(→ one MeshPart per colour in Roblox) ≈ 120–200 MeshParts total (≤ 300). Parts before join: ~8–12k.
