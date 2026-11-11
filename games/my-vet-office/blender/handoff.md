# Model Handoff — My Vet Office: Golden Retriever (+ exam-room props)

Game: `my-vet-office` · Profile: `simulator` (house style §4, bible ★/§0/§13) · Rarity: hero patient (not a gacha pet)
Template: patterns from `blender/templates/creature.py` + `prop_kit.py`, rebuilt as ORIGINAL assets.
Status: **PENDING owner approval** — nothing here is approved. Not yet imported into Studio.

Sources: `golden_retriever.py`, `exam_room_props.py`, shared helpers `vet_common.py`, gate `test_assets.py`.

## Game-specific art direction (owner, via lead)
"I would rather have three exceptionally animated dog breeds than 30 poorly animated animals."
→ Patients are the stars: **believable dog proportions, chunky-stylized** (not chibi blobs, not cube-on-sticks),
expressive face (separate eyelids, eye highlights, jaw, floppy ears, plumed tail) and a real rig so Roblox
can animate them procedurally with Motor6Ds.
Deliberate deviation from house §4 "head ≥ 1.4× body height": a vet patient must read as a *breed*, so the head
is enlarged (~1.3× realistic, eyes ≈ 32 % of head width each) but the body keeps dog anatomy. **Flagged for the owner.**

## Style rules applied
- Many chunky parts with colour breakup; coat in 4 shades (`vault_kit.shades`); cream chest/feathering in 2 shades.
- Studs = TEXTURE on every surface at `STUD_PITCH = 0.5` (pets too), never stud geometry. Exceptions: eyes,
  nose, mouth/tongue/teeth (face pieces), the tag cross, glass and neon.
- Plausible dog detail only: chest ruff, belly fringe, foreleg feathering, "pants", hock tufts, plumed tail, brows,
  flews, whisker dots, toes + claws, darker back saddle, collar + rivets + buckle + vet ID tag. No spikes/scales/horns.
- Glow accent: neon vet ID tag + eye sparkles only (well under 10 % area).

## Palette (Golden Retriever)
| Role | Hex |
|---|---|
| Coat light / base / dark / deep | `shades("#E9A23B")` → `#FFC548` / `#E9A23B` / `#B67E2E` / `#8B6123` |
| Cream ruff / feathering | `#FFD996`, `#FFEAC0` |
| Nose / claws | `#2B1D19`, `#4A3426` |
| Eyes | sclera `#FFFFFF`, iris `#6B3A1A` + `#A0612C`, pupil `#141010`, sparkles neon white, lash line `#5A3410` |
| Tongue / mouth | `#FF6F91`, `#E04F78`, `#5A1E2A` |
| Collar (accent) | `#E8403A` / `#B8261F`, steel `#D7DEE8` |
| Glow (neon) | ID tag `#3EE6FF` with white cross |

## Scale & orientation
1 Blender unit = 1 stud (1 stud = 0.28 m). Dog faces **+Y**, up +Z, dog's LEFT = −X (in front views the dog's left
is on screen-right). Root bone at the ground origin; paws rest flat on z = 0 (checked by the script).
Measured: 1.59 W × 5.12 L (nose → tail tip; nose → rump ≈ 4.0) × 3.31 H studs; head top 3.32 studs.

## Rig — 34 bones (pivot = bone head, in studs x / y / z)
All bones point +Y with roll 0, so every bone's local axes equal the model axes at rest → Motor6D C0/C1 are pure
translations at rest. Positive X rotation swings a limb forward / pitches the nose up.

| Bone | Parent | Pivot |
|---|---|---|
| `Root` | — | (0.00, 0.00, 0.00) |
| `Pelvis` | Root | (0.00, -0.95, 1.74) |
| `SpineLow` | Pelvis | (0.00, -0.50, 1.80) |
| `SpineMid` | SpineLow | (0.00, 0.00, 1.84) |
| `Chest` | SpineMid | (0.00, 0.50, 1.86) |
| `Neck` | Chest | (0.00, 0.95, 2.02) |
| `Head` | Neck | (0.00, 1.30, 2.56) |
| `Jaw` | Head | (0.00, 1.75, 2.42) |
| `EarL` / `EarR` | Head | (∓0.50, 1.48, 3.06) |
| `LidL` / `LidR` | Head | (∓0.28, 1.98, 2.87) — same pivot as the eye; rest = relaxed open, rotate −X ≈ 60–90° to blink |
| `EyeL` / `EyeR` | Head | (∓0.28, 1.98, 2.87) — rotate X/Z for look-at |
| `Tail1` | Pelvis | (0.00, -1.36, 1.98) |
| `Tail2` | Tail1 | (0.00, -1.62, 2.14) |
| `Tail3` | Tail2 | (0.00, -1.86, 2.27) |
| `Tail4` | Tail3 | (0.00, -2.09, 2.33) |
| `ShoulderL` / `ShoulderR` | Chest | (∓0.38, 0.74, 1.62) |
| `ElbowL` / `ElbowR` | Shoulder* | (∓0.38, 0.56, 1.00) |
| `WristL` / `WristR` | Elbow* | (∓0.38, 0.66, 0.32) |
| `PawFL` / `PawFR` | Wrist* | (∓0.38, 0.72, 0.13) |
| `HipL` / `HipR` | Pelvis | (∓0.40, -0.98, 1.62) |
| `KneeL` / `KneeR` | Hip* | (∓0.40, -0.74, 0.98) — stifle sits forward, bends like a dog |
| `HockL` / `HockR` | Knee* | (∓0.40, -1.17, 0.46) — hock sits back |
| `PawBL` / `PawBR` | Hock* | (∓0.40, -1.10, 0.13) |

Joint gaps: every child segment starts with an overlapping rounded cap (elbow / wrist / knee / hock / tail joints)
and segments overlap their parent by 0.04–0.06, so ±40° bends do not open holes. The Sit and Lie test poses
(`POSES` in the script, rendered in `assets/previews/golden_retriever_sit*.png` / `_lie*.png`) bend much further
than that.

## Part naming (export)
- One rigid mesh per bone: `<Bone>_Geo` (e.g. `Head_Geo`, `KneeL_Geo`). Each has exactly ONE vertex group named
  after its bone, weight 1.0 on every vertex, plus an Armature modifier → a 100 %-rigid skin. Object origin = that
  bone's pivot.
- `Root_Geo`: invisible 1.1 × 3.0 × 0.1 root plate (custom prop `roblox_transparency = 1`, material
  `M_RootInvisible`) so the importer has a root part. Use it as PrimaryPart / HumanoidRootPart stand-in.
- Materials carry `roblox_color` / `roblox_neon` custom props (vault convention). Every mesh also has a `Col`
  colour attribute baked from its materials (fallback for importers that ignore materials).
- Files: `assets/export/golden_retriever.fbx` (Roblox) + `.glb` (preview). The armature object is `GoldenRetriever`.

## How Roblox should import it (UNTESTED — first import must verify and record in lessons)
1. Studio → Avatar/3D Importer → `golden_retriever.fbx`. Rig type: custom/"Rig General"; File Dimensions: **Studs**
   (1 Blender unit = 1 stud; verify with `blender/templates/scale_reference.py`, vault open item).
2. Expected result: a Model with one MeshPart per `<Bone>_Geo` and the joints converted to **Motor6Ds** named after the
   bones (Part0 = parent bone's part, Part1 = this bone's part, C0/C1 at the pivots above). If the importer instead
   produces a single skinned MeshPart with Bones, re-import with the rigid/"separate parts" option, or rebuild the
   Motor6Ds from the pivot table above (a short script can do this: pivots are in the table and in the FBX).
3. Multi-colour parts: each `<Bone>_Geo` holds several materials. Bible §12 open item — decide on the first import
   whether the importer keeps per-material colours (SurfaceAppearance / vertex colours) or whether parts must be
   split per colour. The stud texture is a separate tiling normal map (bible §2: StudsPerTile 0.5).
4. Procedural animation targets: idle breathing (Chest/SpineMid ±3° X), tail wag (Tail1–4 Z, phase-offset),
   blink (Lid* −X), ear flop (Ear* Y), look-at (Neck/Head/Eye*), pant (Jaw −X 8–15°), sit/lie (see `POSES`).

## Silhouette check
At 50 studs: a golden dog with a domed head, hanging ears, deep chest with a cream bib, angled hind legs and a
plumed tail curving up behind — reads as "golden retriever", not as a box on four sticks.

## Studio-side extras (not modelled)
Procedural animation (above), happy/sick particles on a Head attachment, optional PointLight on the tag.

## Budget (measured)
Whole dog 11,816 tris (my hero-pet cap 12k; largest part `Head_Geo` 1,228 ≪ 15k per MeshPart) · 197 pieces before
join · 34 rigid parts.

---

## Exam-room props (`exam_room_props.py`)
Original vet-clinic props in the SOLID language (clean chunky solids, texture studs on all sides, physical trims).
Palette: clinic teal `#22C3A6` (3 shades) + coral `#FF6B6B` accent, stainless `#C9D3DE`/`#E6ECF2`/`#8E9BAA`/`#5F6B7A`,
rubber `#2F4858`/`#43627A`, glass `#9BE1FF`, neon readouts `#7CFFB2`.

| Asset (mesh name) | File | Pivot / notes | Tris | Pieces |
|---|---|---|---|---|
| `ExamTable` | `exam_table.fbx/.glb` | bottom-centre; mat top at z 3.34; 6.0 × 3.2 top | 5,304 | 77 |
| `EquipmentCabinet` | `equipment_cabinet.fbx/.glb` | bottom-centre, back face on y = 0 (put against the wall) | 2,668 | 60 |
| `CabinetDoor` | (same files) | **origin = hinge axis** (−1.58, 1.36, 0); rotate about +Z, 0° closed → ~105° open | 772 | 17 |
| `Stethoscope` | `stethoscope.fbx/.glb` | origin = grip (tubing Y-junction) → Tool `Handle` | 908 | 14 |
| `Otoscope` | `otoscope.fbx/.glb` | origin = grip (handle middle) | 976 | 14 |
| `Thermometer` | `thermometer.fbx/.glb` | origin = grip (body middle) | 636 | 11 |
| `BandageRoll` | `bandage_roll.fbx/.glb` | origin = roll centre | 852 | 11 |

Studio: door → separate MeshPart + HingeConstraint (or Motor6D) at its origin; the scale readout and otoscope light ring
are Neon material; glass panels Glass, Transparency 0.3.
