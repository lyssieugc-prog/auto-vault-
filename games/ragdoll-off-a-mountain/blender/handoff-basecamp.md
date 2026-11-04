# Model Handoff — Base Camp (shared kit + 5 progressive stages)

Game: `ragdoll-off-a-mountain` · Profile: `simulator` (+ alpine sub-palette) · Rarity: n/a (progression set) ·
Template: `prop_kit` techniques + `vault_kit` (framed_window, striped_awning, canopy, vignettes, shades)
Script: `games/ragdoll-off-a-mountain/blender/base_camp.py` → `assets/export/basecamp/`, previews in `assets/previews/basecamp/`.
Spec: `game.md` §2 (6 base camps on the south rim, facing north/+Y) and §3.6 (stages).

## Style rules that apply (house-style §3/§4, bible ★, §0, §3b, §13)
- SOLID language: few big chunky solids per element, crisp 0.04 bevels, texture studs (0.5 pitch) on ALL sides;
  exceptions only glass + neon. No stud geometry, no coplanar overlaps (panels butt or are offset ≥ 0.02).
- Every stage is an ORIGINAL alpine building designed for this game (tent → log cabin → ski lodge → chalet →
  summit hall). Nothing copied from the calibration Smoothie Shack; techniques only.
- Detail parity §3b on every building (stage 2-5; the tent gets the tent equivalent): framed windows with
  mullions + sills, door frame + lamps + step/mat, trim bands, awning/canopy with edge detail, signage with
  icons (bone icon, ski icon, bandage icon), roof clutter (chimney, snow cap, vents, weather vane / flags),
  something visible through the glass (fireplace, trophy shelf, bunk), 2-3 exterior props per stage.
- Detail makes sense for the subject: logs with end-grain caps, snow on roofs, skis/sleds, firewood, rope,
  bandages for the clinic (NO Red Cross emblem — bandage icon + pink), bones as the game's trophy motif.
- Proportions exaggerated: fat logs (0.9 stud), extra-thick snow caps, oversized lamps, chunky signs.
- NEVER: few big plain boxes, single flat colour, smooth realistic chalet, generic AI look, random scatter.

## Palette (mountain/alpine sub-palette; each material in ≥ 2 shades via `vault_kit.shades`)
| Role | Hex |
|---|---|
| Warm wood (main) | `#A8683A` (light `#CD7F47`, dark `#83512D`, deep `#643E22`) |
| Log end grain / bone cream | `#FFF1CF` / `#F2D9A6` |
| Roof red (stages 1,3,5) | `#E13A2A` / `#B6261D` |
| Forest green (stage 2,4 roof trim, banners) | `#2E9A3E` / `#4CC24A` |
| Snow caps | `#F4FBFF` / `#D9ECF7` |
| Stone (foundations, chimney) | `#8E96A3` / `#6E7683` |
| Accent cash gold | `#FFD93B` |
| Glow (neon) | lamp `#FFE7A8`, "SNAP!" orange `#FF8A1F`, lift cyan `#5CF2FF`, summit gold `#FFD93B` |
| Clinic bandage pink | `#FF8FB8` / `#FFC7DA` |
| Glass | `#9BE1FF` (preview: part-transmissive so interiors read; Roblox Glass, Transparency 0.3) |

## Part list (summary — positions relative to pad top centre, +Y = front/mountain)
| Part | Size (studs) | Position | Colour | Notes |
|---|---|---|---|---|
| Kit: Lift pad | Ø 7 disc, 0.8 tall | (16.5, 13.5) | stone + gold chevrons | neon cyan ring, chairlift pole + arrow sign pointing +Y |
| Kit: Bone Clinic bed | 3 × 6 stretcher | (-16.5, 13) | white/pink | wheels, pillow, blanket, IV-style bandage stand, canopy + bandage sign |
| Kit: Pet pedestals ×4 | 2.6 × 2.6 × 1.6 | x ±6, ±10 at y 9.5 | wood + gold trim | studded tops, glow front strips, tiny plaques |
| Kit: TrophyBoard | 6 × 3.4 plank face | (-8, 17.5) facing +Y | wood planks + gold frame | blank face for SurfaceGui, bone crest on top |
| Kit: OwnerSign | mailbox + 3 × 1.6 face | (6.5, 18) facing +Y | red mailbox + plank | blank face for SurfaceGui |
| Kit: path, edging, pines, rocks | — | front path y 4→20; back corners | — | vignettes, ≥ 3-stud clear path |
| S1 Trail Tent | ~10 × 9 × 7 | (0, -7) | orange/red canvas | A-frame, guy ropes, campfire ring, sleeping bag, first-aid crate, trail sign |
| S2 Log Cabin | ~18 × 13 × 13 | (0, -9) | logs + green roof | notched corners, framed windows, porch, chimney, woodpile |
| S3 Ski Lodge | ~24 × 15 × 19 | (0, -10) | wood + red roof | 2 floors, balcony railings, ski/sled rack, trophy shelf behind glass, striped awning, sign |
| S4 Alpine Chalet | ~28 × 17 × 25 + tower 30 | (0, -10) | cream/wood + red roof | big gable, snow cap, timber trim, flower boxes, trophy tower with bone trophy |
| S5 Summit Hall | ~36 × 20 × 28 + spire 44 | (0, -10) | stone/wood + red/gold | grand hall, banners, bone-trophy spire (gold bone + friendly skull), neon accents |

## Silhouette check
Stage 1 reads as a pointed tent + campfire; stage 2 a chunky gabled log box with chimney; stage 3 a tall two-storey
box with a jutting balcony; stage 4 a giant snow-capped A-roof beside a thin tower topped by a bone; stage 5 a wide
hall with twin banner towers and a central spire crowned by a bone + skull — five clearly different heights/shapes.

## Studio-side extras (added in Studio, not modelled)
Campfire/fireplace ParticleEmitter (embers) + PointLight; Lift pad Beam/ProximityPrompt at marker `LiftPad`;
ClinicBed respawn CFrame; SurfaceGui on `TrophyBoard` / `OwnerSign` faces; PointLights on lamp glow pieces;
banner cloth sway (optional). Markers in `assets/export/basecamp/markers.json`.

## Budget
Target tris: ≤ 15k per exported mesh (body/glass/neon per stage + kit) · Parts before join: kit ~250, stages 80-400.
