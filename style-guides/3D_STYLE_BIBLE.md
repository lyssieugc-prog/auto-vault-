# 3D Style Bible — DRAFT (not final until the owner approves the test collection)

Status: **DRAFT v5** (core standards from owner; stud size approved: 0.5) · Source: 11 reference images + 20 video frames in `3d-model-references/`
(style references only — never copy their objects, characters, layouts or assets).
Test collection: `blender/templates/test_collection.py` → renders in `references/images/pending/`.

Every number below is a default; a game's style profile may override it explicitly.

## 0. Core standards — "High-Detail Studded Blocky Roblox Simulator Art Style" (owner, verbatim)
1. Every major asset should have a recognizable blocky silhouette.
2. Use actual layered geometric details instead of relying on flat image textures.
3. Apply small, consistent studs to suitable surfaces such as terrain, buildings, platforms, and some models.
4. Create trees using multiple clusters of angular leaves, not single spheres.
5. Create terrain using stepped, rectangular geometry with clearly visible elevation changes.
6. Make creatures visually complex through scales, spikes, layered body parts, and exaggerated facial features.
7. Populate environments densely with themed decorations, but preserve clear paths and gameplay areas.
8. Use vibrant, coordinated color palettes rather than realistic, muted colors.
9. Make buildings visually interesting through trims, awnings, signs, windows, props, and layered architectural pieces.
10. Use bright lighting, readable silhouettes, and soft shadows to keep the world playful.

### How each standard is measured in Blender
| # | Measurable rule |
|---|---|
| 1 | Silhouette test: model reads from 50 studs as a flat black shape; ≥ 1 silhouette feature (§3). |
| 2 | Detail is geometry (frames, trims, plates, props). Only studs are a texture. ≥ 3 depth layers on any face larger than 6×6 studs (wall → trim → prop). |
| 3 | Stud texture 0.5-stud spacing (§2), identical size everywhere (world-space UVs). |
| 4 | Trees: ≥ 8 angular leaf clusters (rounded cubes, tilted ±8°, yaw ±20°), 2–3 greens; never one sphere. |
| 5 | Terrain: rectangular terraces with visible steps of 1.5–6 studs; layered (stone/dirt body + grass cap); flat play areas kept between them. |
| 6 | Creatures: ≥ 5 spikes or horns, ≥ 8 scale/plate pieces, ≥ 3 stacked body layers, eyes ≥ 30% of head width. |
| 7 | Decoration density ≥ 1 themed prop per 40 sq studs of non-path ground; keep a ≥ 3-stud clear path and a ≥ 2.5-stud margin around paths and gameplay objects. |
| 8 | 1 main hue + 1 secondary + 1 accent per model; saturation high; no greys except stone/steel. |
| 9 | Building detail-parity checklist (§3b). |
| 10 | Lighting preset (§10): sun 5.0 warm, soft angle 0.12, fill 1.2, sky blue. |

---

## 1. Two construction languages
| Language | Use for | How it's built |
|---|---|---|
| **SOLID** | maps, buildings, props, machines, trees, rocks | Clean chunky boxes (few, large), crisp edges, **texture studs on all sides**. No stacked-brick seams. |
| **MERGED VOXEL** | brainrot collectibles, pets, creatures | Shape blocked out in voxels, then **merged into 0.5-stud blocks** (no per-voxel colour noise), plus a crisp cartoon face built from flat pieces. |

Owner corrections that define these (lessons L-20261104-03/04): stacked-brick buildings, trees and
conveyors were an "absolute no"; tiny jittered voxels were "too bricky — merged blocks".

## 2. Studs — TEXTURE ONLY
- Studs are **never geometry**. They come from a tiling stud texture:
  `blender/textures/stud_height.png` (Blender bump preview) + `stud_normal.png` (Roblox normal map).
- **Stud spacing = 0.5 studs** (owner picked option B, half the 1-stud default). One texture tile
  = one stud bump; stud diameter ≈ 0.54 of the tile, rounded raised top, soft shoulder.
- Set by `vault_blocky.STUD_PITCH = 0.5`; UVs are world-space so the size never changes with scale.
- UVs: world-space box projection, **1 UV unit = 0.5 studs** (`vault_blocky.stud_surface`).
- Placement: **ALL sides of every block** (owner, L-20261104-05) — floors, walls, pillars, beams,
  roofs, trunks, leaf cubes, rocks, machines, crates, pedestals, baseplates.
  Exceptions only: **glass**, **neon/glow pieces**, and **face pieces** on collectibles.
- Profile: rounded raised top (height 0.55→1.0 dome) so studs shade light→dark, not as flat rings.
- Roblox: apply the stud texture to MeshParts/Parts with `Texture` instances on each face,
  **StudsPerTileU = StudsPerTileV = 0.5** (matches the Blender preview), or a MaterialVariant using
  `stud_normal.png` with the same tiling. Verify on the first import and record it in lessons.

## 3. Shape & silhouette
- **Few, big, readable masses.** Typical prop: 8–25 solids; building: 40–70; tree: 15–25.
- Proportions are chunky: minimum thickness **0.3 studs** for any visible piece (thinner reads as noise
  on mobile), walls 0.8, pillars 1.4–2.0, beams 1.0.
- Organic things (trees, rocks, bushes) = **clusters of slightly rotated cubes** (±8° tilt,
  ±20° yaw) in 2–3 shades, never a perfect stepped pyramid.
- Every model has **one silhouette feature** readable at 50 studs (rooftop prop, straw, crest, machine box).
- Overlapping coplanar faces are forbidden (they render black/z-fight): panels must butt, not overlap.

### 3b. Detail parity (owner, L-20261104-07)
Buildings and props carry detail **on par with collectibles — not more** (collectibles stay the
focal point). A building needs at minimum: framed windows (mullions + sills), door frame + lamps +
step/mat, trim bands (baseboard/cornice), an awning or canopy with an edge detail, signage with
icons, roof clutter (parapet, AC/vents, rooftop theme prop), something visible inside the glass,
and 2–3 exterior props (seating, signs, crates, planters). Reference: Smoothie Shack v4 (~190 pieces).

## 4. Edges & bevels
| Element | Bevel (studs) | Segments |
|---|---|---|
| Solids (walls, props, machines) | 0.04 | 1 |
| Organic clumps (leaves, bushes) | 0.06 | 1 |
| Glass / decals / face pieces | 0.01–0.03 | 1 |
| Small round accents (fruit, knobs, lights) | 0.15–0.25 | 2 |
| Merged voxel bodies | 0 (crisp steps) | — |

## 5. Materials
- Smooth plastic: roughness **0.5–0.6**, no metallic, no texture other than studs.
- Glow = emissive pieces only (Roblox **Neon**): windows of machines, lamps, sparkles, interior light
  panels, collect pads. Strength 1–5. Max ~10% of a model's visible area.
- Glass: light cyan `#9BE1FF`, opaque in preview (Roblox: Glass material, Transparency 0.3).

## 6. Colour
- Saturated, cheerful, daytime. Each model: **1 main hue + 1 secondary + 1 accent + neutrals**.
- Environment greens `#4CC24A / #2E9A3E / #86E05A`, ground `#4FC33A`, stone `#8E96A3 / #6E7683`,
  bark `#8A5530`, cream walls `#FFF6EA`, hazard `#FFC21A` + `#1A1A1A`.
- Contrast pairs that read well: teal frame `#22C3A6` + coral `#FF6B6B`; orange machine `#FF8A1F` +
  steel `#5B6B82`.
- Shade variation comes from **separate pieces in 2–3 tones**, not per-voxel noise.

## 7. Faces (collectibles)
- Built from crisp flat pieces on the head front: eyes ≥ **25% of head width each**, white with black
  pupils (offset inward/down for attitude), 1 white sparkle, optional eyelids for expression
  (smug = half-lid), mouth ≥ **50% of head width**, tongue/teeth inside the mouth only, blush.
- The face must read from the wide shot (≈ 40 studs away).

## 8. Scale (1 Blender unit = 1 stud; R6 character = 5 studs)
| Thing | Size (studs) |
|---|---|
| Player (R6) | 5 tall |
| Door | 2.5 × 4.6 |
| Building floor height | 6–7 |
| Two-floor shop | 14 × 10 footprint, ~16 tall + roof prop |
| Tree | 12–14 tall, canopy 9–10 wide |
| Rock | 6 × 4 × 4 |
| Conveyor | 14 long, 3.4 wide, belt at 2.6 (≈ waist height) |
| Collectible on pedestal | 8–10 tall (≈ 2× player), pedestal 6 × 6 |

## 9. Performance (mobile)
- ≤ 15k tris per exported mesh (Roblox hard cap 20k). Collection v3: tree 1.0k, rock 0.4k,
  building 2.3k, conveyor 1.4k, brainrot 2.4k.
- Merged voxel bodies: < 1,500 cells.
- Join each model into ≤ 3 meshes for export (body / glass / neon).

## 10. Lighting & review renders
- Review renders: Cycles CPU, sun 5.0 warm (1.0, 0.96, 0.9), angle 0.12 rad (soft shadow), fill 1.2,
  sky `(0.33, 0.64, 1.0)`, Standard view transform (keeps saturation), 1280×720.
- Always render: the wide collection + a close-up of each model, from the model's FRONT (+y).

## 11. Enforced by tests (`blender/tests/test_pipeline.py`)
No stud geometry · texture studs in use · brainrot full face · merged blocks < 1,500 cells ·
tris ≤ 15k · creature minimums. Looks are judged by the owner, not by tests.

## 12. Open items before FINAL
- Owner verdict on the v3 test collection.
- Export path for multi-colour meshes (one MeshPart per colour group vs palette atlas texture) —
  decide on first real Studio import.
- Confirm Blender→Roblox import scale with `blender/templates/scale_reference.py`.
