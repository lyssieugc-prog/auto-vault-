# Global Lessons

Read before every build. Newest first. Format in `lessons/README.md`.

### L-20261104-10 — UI art: no code-drawn clipart; one benchmark screen before batches
- Scope: global (owner: "STOP… icons look like generic mobile-game clipart… Do not continue generating 30 reward-card variants")
- Root cause: item icons were drawn from vector primitives through the Figma Plugin API, and a
  card set (30 variants) was batch-generated before one screen had been approved. Sparkles and
  gradients were added to make up for the missing illustration quality.
- Rule: item and collectible art comes from Blender renders (or owner-supplied or commissioned
  illustration) placed in a Figma `Art` image slot. Figma owns frames, type and layout. Build ONE
  benchmark screen (the shop) to approval before any other screen or any variant batch. If a
  workflow can't reach the benchmark, say so and propose a better one. Don't present placeholders
  as finished work.
- Applied to: `figma/audits/shop-v1-audit.md` (gap audit + method). The rejected icons
  (`12:3`–`12:101`) and RewardCard v2 (`13:9244`) are kept as rejected examples.

### L-20261104-09 — Learn the art STYLE, never repeat assets; quality ≠ blocky + studs; plausible detail
- Scope: global (owner's "permanent 3D art direction"; "doesn't make sense to have spikes on the frog")
- Rule: bible ★ (verbatim). Test collection = calibration sample only; every game gets ORIGINAL assets
  built with `blender/lib/vault_kit.py` techniques; professional-asset review (§13) before any model is
  done; creature detail must fit the creature; decoration = purposeful vignettes, never random scatter;
  ≥ 2 shades per material.
- Applied to: bible ★/§0/§13, `CLAUDE.md`, `vault_kit.py` (new toolkit), test collection (frog warts/
  eye rims/pouch/lily-pad hat instead of spikes/scales; canopy tool trees; vignettes), make-game skill,
  blender-artist agent, qa/checklist.md, pipeline gates (vignettes ≥7 with ≥3 piece types, frog has
  ≥12 plausible details and no spikes/scales)
- Honest self-review of the current sample: building ≈ pro; trees improved; frog still reads closer to a
  generic block model (stepped head mass, low-contrast warts); open grass needs more vignettes.

### L-20261104-08 — Owner's core art standards ("High-Detail Studded Blocky Roblox Simulator")
- Scope: global (owner supplied 10 standards)
- Rule: `style-guides/3D_STYLE_BIBLE.md` §0 (verbatim + measurable table). Notably: stepped
  rectangular terrain, dense themed decoration with clear paths, creatures with spikes/scales/layers
  and exaggerated faces, trees from ≥8 angular leaf clusters, layered geometric detail.
- Note: §0.3 says studs on "suitable surfaces … and some models"; L-05/L-06 (owner) said EVERYTHING
  incl. pets. Kept "everything" until the owner says otherwise.
- Applied to: bible §0, `test_collection.py` (terrain, paths, lamps, fence, 190 decorations,
  terrace trees, creature spikes/scales/bands, bigger eyes), pipeline gates for std 4/5/6/7

### L-20261104-07 — Buildings need detail on par with collectibles (not more)
- Scope: global (owner: "the brainrot is more detailed than the buildings, that's really not how it
  should be… the buildings should have more detail" → "not MORE than collectibles")
- Root cause: building was clean panels only; detail budget went to the collectible.
- Rule: `style-guides/3D_STYLE_BIBLE.md` §3b detail-parity checklist for every building/prop.
- Applied to: `blender/templates/test_collection.py` (`building_details`), bible §3b,
  `blender/tests/test_pipeline.py` (building piece-count gate)

### L-20261104-06 — Everything studded (pets too); any shape allowed; studs must not look huge
- Scope: global (owner: "it doesn't have to just be cubes… as long as it has the stud texture, and
  yes EVERYTHING even pets should have stud texture"; "the studs are huge, use the roblox stud texture")
- Trigger: v3.1 collection; then a round smooth brainrot (v4) — owner: "ewwww that's worse"
- Root cause: studs mapped too coarse for the model sizes; "too bricky" was over-corrected into
  smooth blobs, which the owner rejected.
- Rule: every surface of every model carries stud texture (exceptions: glass, neon, face pieces);
  cylinders/cones/wedges/rounded shapes are fine for props; studs keep correct size after scaling
  (world-space UVs); brainrot stays the merged-block v3 shape (round v4 rejected).
- RESOLVED: stud size = **0.5-stud spacing** (owner picked option B) → `STUD_PITCH = 0.5`; Roblox
  Texture StudsPerTileU/V = 0.5.
- Applied to: `blender/lib/vault_blocky.py` (world-space `stud_surface`, `restud`, `scale_group`,
  `cyl`/`ball`/`rounded`, `STUD_PITCH`), `blender/templates/test_collection.py` (real Roblox scale,
  studded brainrot), `blender/tools/render_collection.py`
- Validation: pipeline test 0 failures; comparison renders sent to owner

### L-20261104-05 — Stud texture on ALL sides of blocks
- Scope: global (owner: "all sides of blocks should have stud texture in it")
- Trigger: test collection v3 had studs on up-facing faces only
- Root cause: `stud_surface` defaulted to `top`; Claude assumed side studs would be too busy.
- Rule: every solid gets texture studs on all faces (default `studs="all"`); exceptions only glass,
  neon pieces and collectible face pieces. Stud profile is a rounded dome so it shades as raised.
- Applied to: `blender/lib/vault_blocky.py` (defaults + stud profile), `blender/templates/test_collection.py`,
  `style-guides/3D_STYLE_BIBLE.md` §1–§2, `blender/tests/test_pipeline.py` (all-sides gate)
- Validation: pipeline test + v3.1 renders reviewed

### L-20261104-04 — Studs are texture, props are clean solids, collectibles are merged blocks
- Scope: global (owner: "everything physically has studs on it, it should be a part of the texture")
- Trigger: owner on test collection v2: building/tree/conveyor "an absolute no"; brainrot "decent,
  needs a face… toooo bricky, merged blocks"; earlier v1 "looks dorky but details are ok"
- Root cause: Claude read the references as LEGO construction (stacked bricks + stud geometry) and
  built collectibles from tiny noisy voxels; the references actually use clean solid shapes with
  stud *surface texture*, and chunky collectibles with big simple faces.
- Rule: see `style-guides/3D_STYLE_BIBLE.md` §1–§2, §7: SOLID language for props/maps (few big
  crisp solids, texture studs on up-facing faces only); MERGED VOXEL for collectibles (0.5-stud
  blocks, no colour noise) + crisp cartoon face; never stud geometry; no coplanar overlaps.
- Applied to: `blender/lib/vault_blocky.py` (stud textures, `stud_surface`, `solid`, `downsample`),
  `blender/templates/test_collection.py` (v3), `blender/templates/creature.py` (texture studs),
  `blender/tests/test_pipeline.py` (no-stud-geometry, face, merged-block gates),
  `style/house-style.md`, `CLAUDE.md`
- Validation: pipeline test 0 failures; v3 renders reviewed (wide + 5 close-ups); owner verdict PENDING

### L-20261104-03 — Pets must look like appealing Roblox pets, and Claude must judge by eye
- Scope: global (owner restated the design rules as non-negotiable)
- Trigger: owner, on the v1 creature render: "you see how bad that is? no the pet is horrible"
- Root cause: `blender/templates/creature.py` v1 was a few large boxes in one hue with no studs,
  no real face and stiff proportions — the house BAD list. Claude accepted it because a numeric
  check passed (18 parts, a glow material) instead of judging the render against the style.
- Rule (studs amended by L-20261104-04: texture only): pets follow the "Pet minimums" in `style/house-style.md` §4 (chibi proportions, studs on
  the pet, full face, ≥5 colours, ≥50 parts, detail on every side, silhouette feature). Render
  front/side/back and critique before showing. New assets are PENDING until the owner approves.
- Applied to: `blender/templates/creature.py` (v2 rebuild), `blender/lib/vault_blocky.py`
  (`stud_patch`), `blender/tests/test_pipeline.py` (style gates), `blender/tools/render_preview.py`
  (3-angle renders), `style/house-style.md`, `CLAUDE.md` (owner's rules verbatim + "judge by eye"),
  `references/catalog.md` (v1 rejected, v2 pending)
- Validation: `python blender/tests/test_pipeline.py` → 0 failures (97 parts, 8 colours, studs,
  face, proportions, 5.2k tris); 3-angle renders reviewed

### L-20261104-02 — Verify studs and placement visually, not just numerically
- Scope: global
- Trigger: vault setup self-review (map preview render)
- Root cause: `studs()` used a stale `matrix_world` for the parent inverse, so studs landed at 2x
  the plate offset; the triangle-count check also skipped child meshes, so tests still passed.
- Rule: always render a preview (`blender/tools/render_preview.py`) of new geometry and look at
  it before export; budget checks must include child meshes.
- Applied to: `blender/lib/vault_blocky.py`, `blender/tests/test_pipeline.py` (stud-presence check)
- Validation: `python blender/tests/test_pipeline.py` → 0 failures; preview re-rendered

### L-20261104-01 — Map-scale studs must scale with spacing
- Scope: global
- Trigger: vault setup self-review (zone close-up looked like pin-pricks, not studs)
- Rule: stud radius/height scale with stud spacing (`STUD_RADIUS * spacing`).
- Applied to: `blender/lib/vault_blocky.py`
