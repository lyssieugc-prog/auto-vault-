# Testing & Quality Control

## Definition of "tested"
| Label | Meaning |
|---|---|
| ✅ Tested | An automated test or a recorded playtest step exercised it and it passed |
| 🟡 Built, untested | Code/asset exists but nothing has exercised it (e.g. no Studio available) |
| ❌ Not done | Missing |

Never upgrade a label without evidence (test output, playtest log, screenshot).

## Layers
1. **Static**: StyLua format, Selene lint, luau-analyze (CI, `scripts/validate.sh`).
2. **Unit/integration (Lune)**: `systems/tests` + `games/<slug>/tests`.
3. **Asset pipeline**: `blender/tests/test_pipeline.py` + per-game asset script run + preview review.
4. **Build**: `rojo build` for vault + each game project.
5. **Studio playtest** (needs Studio MCP): `playtest.md`.
6. **Performance**: `performance-budget.md`.
7. **Style**: `checklist.md` (final house-style check).
