# Global Lessons

Read before every build. Newest first. Format in `lessons/README.md`.

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
