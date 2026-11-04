# Integration Audit Procedure

Run at vault setup, at the start of every `/make-game`, and whenever a tool fails.
Record results in `STATUS.md`. A tool counts as connected ONLY if its live test passes.

| Tool | Live test | Pass condition |
|---|---|---|
| GitHub | `mcp__github__get_me` + `git fetch origin` | login returned, fetch OK |
| CI | latest Actions run on the branch (`actions_list list_workflow_runs`) | conclusion `success` |
| Blender (bpy) | `python blender/tests/test_pipeline.py` | `0 failure(s)` |
| Blender MCP | `get_scene_info` (or equivalent) then create + delete a cube | cube appears/disappears |
| Figma MCP | `get_metadata` / `whoami` on the game's file | metadata returned |
| Roblox Studio MCP | `run_code` with `print(game.PlaceId)` / list Workspace children | output returned |
| Rojo | `rojo build systems/default.project.json -o /tmp/v.rbxm` | file written |
| Luau tooling | `scripts/validate.sh` | exits 0 |

If a tool is missing: say so in the game report, keep working on everything that does not need
it, and list the exact manual step (from `local-setup.md`) that unblocks it. Never fake output.
