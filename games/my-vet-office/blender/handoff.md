# Model Handoff — My Vet Office: Golden Retriever (+ exam-room props)

Game: `my-vet-office` · Profile: `simulator` (house style §4, bible ★/§0/§13) · Rarity: hero patient (not a gacha pet)
Template: patterns from `blender/templates/creature.py` + `prop_kit.py`, rebuilt as an original rigged pet.
Status: **PENDING owner approval** — nothing here is approved.

## Game-specific art direction (owner, via lead)
"I would rather have three exceptionally animated dog breeds than 30 poorly animated animals."
→ Patients are the stars: **believable dog proportions, chunky-stylized** (not chibi blobs, not cube-on-sticks),
expressive face (separate eyelids, eye highlights, jaw, floppy ears, plumed tail) and a real rig so Roblox
can animate them procedurally with Motor6Ds.
Deliberate deviation from house §4 "head ≥ 1.4× body height": a vet patient must read as a *breed*, so the head
is enlarged (~1.3× realistic, eyes ≥ 30 % of head width) but the body keeps dog anatomy. Flagged for the owner.

## Style rules that apply
- Many chunky parts with colour breakup; coat in ≥ 2 shades (`vault_kit.shades`); cream chest/feathering.
- Studs = TEXTURE on every surface at `STUD_PITCH = 0.5` (pets too) — never stud geometry. Exceptions: eyes,
  nose, mouth/tongue (face pieces) and neon.
- Detail must be plausible for a dog: feathering, chest ruff, toes + claws, brows, flews, collar + ID tag.
  No spikes / scales / horns.
- Glow accent: small neon vet ID tag + eye sparkles only (≤ 10 % area).
- NEVER: few plain boxes, single flat colour, realistic fur, smooth generic AI model, Minecraft-mob look.

## Palette (Golden Retriever)
| Role | Hex |
|---|---|
| Coat (light / base / dark / deep) | `#FFC548` / `#E9A23B` / `#B67E2E` / `#8B6123` (`shades("#E9A23B")`) |
| Cream ruff / feathering | `#FFE3AE`, `#FFF2D6` |
| Nose / claws | `#2B1D19`, `#4A3426` |
| Eyes | sclera `#FFFFFF`, iris `#6B3A1A`, pupil `#141010`, sparkle neon white |
| Tongue / mouth | `#FF6F91`, `#E04F78`, `#5A1E2A` |
| Collar (accent) | `#E8403A` / `#B8261F`, buckle `#D7DEE8` |
| Glow (neon) | ID tag `#3EE6FF` with white cross |

## Scale & orientation
1 Blender unit = 1 stud (1 stud = 0.28 m). Dog faces **+Y**, up +Z, dog's LEFT = −X. Root bone at the
ground origin; paws rest flat on z = 0. Nose-to-rump ≈ 4.1 studs, head top ≈ 3.2 studs.

## Rig (bone name → parent → pivot in studs, x/y/z)
See the `BONES` table at the top of `golden_retriever.py` (single source of truth); final values are
copied below after the build.

## Part naming (export)
One rigid mesh per bone, named `<Bone>_Geo` (e.g. `Head_Geo`, `KneeL_Geo`), skinned 100 % to that bone via a
vertex group of the same name. `Root_Geo` is an invisible root box (custom prop `roblox_transparency = 1`)
so the importer has a root part.

## Silhouette check
At 50 studs: a golden dog with a domed head, hanging ears, deep chest with a cream bib, long plumed tail
held out behind — reads as "golden retriever", not as a box on four sticks.

## Studio-side extras (not modelled)
Procedural animation (idle breathe, tail wag, blink, ear flop, head look-at), happy/sick particle emitters
on the Head attachment, PointLight on the tag (optional).

## Budget
Target: whole dog ≤ 12k tris (hero creature, my interpretation of the ≤ 15k-per-MeshPart rule in
`qa/performance-budget.md`), every `<Bone>_Geo` far below 15k. Parts before join: ≥ 150.

---

## Exam-room props (`exam_room_props.py`)
Original vet-clinic props in the SOLID language (clean chunky solids, texture studs on all sides, physical
trims): exam table (stainless top + rubber mat + hydraulic base), wall equipment cabinet (door is a separate
part with a hinge pivot), stethoscope (separate grip part), otoscope, digital thermometer, bandage roll.
Palette: clinic teal `#22C3A6` + coral `#FF6B6B` accent, stainless `#C9D3DE`/`#8E9BAA`, rubber `#2F4858`,
screen glow `#7CFFB2`.
