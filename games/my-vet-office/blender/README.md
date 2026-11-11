# My Vet Office — Blender sources

Copy templates from `blender/templates/` here, edit SPEC/LAYOUT, then run e.g.:
`python games/my-vet-office/blender/map.py games/my-vet-office/assets/export/map`
Write `handoff.md` (from `blender/handoff-template.md`) for every creature/hero asset first.

## Assets in this folder (all PENDING owner approval)
| Script | Output | Run (bpy Python, repo root) |
|---|---|---|
| `golden_retriever.py` | rigged dog `assets/export/golden_retriever.fbx/.glb` | `python games/my-vet-office/blender/golden_retriever.py [--render]` |
| `exam_room_props.py` | exam table, cabinet + door, stethoscope, otoscope, thermometer, bandage roll | `python games/my-vet-office/blender/exam_room_props.py [--render]` |
| `vet_common.py` | shared primitives, rig builder, checks, preview renderer | (imported) |
| `test_assets.py` | gate: bone names/hierarchy, tri budgets, ground contact, exports | `python games/my-vet-office/blender/test_assets.py` |

Rig, pivots and Roblox import notes: `handoff.md`. Self-review: `../assets/review.md`.
