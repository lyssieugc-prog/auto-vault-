# Global Lessons

Read before every build. Newest first. Format in `lessons/README.md`.

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
