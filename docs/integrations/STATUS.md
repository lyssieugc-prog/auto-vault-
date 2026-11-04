# Integration Status

Only mark a tool ✅ after a **live successful call in that environment**. Re-verify at the start of
every `/make-game` run (step 0) and update this file when anything changes.

Last audit: 2026-11-04 (re-run for `/make-game ragdoll-off-a-mountain`) · Environment: Claude Code cloud session (Linux container)

| Tool | Status | Evidence / what is missing |
|---|---|---|
| GitHub (MCP) | ✅ Connected | `get_me` → `lyssieugc-prog`; branch listing on `lyssieugc-prog/auto-vault-` OK; git push over proxy OK. |
| GitHub Actions CI | ✅ Runs | Run #18 (`dabd239`): Lune 81/81 vault + 28/28 Ragdoll game tests, rojo builds, StyLua + luau-analyze clean; 1 selene warning (fixed in `fca1248`). |
| Blender (bpy 5.2.3 Python module) | ✅ Works in cloud + CI (re-installed via pip 2026-11-04, pipeline test 0 failures) | `blender/tests/test_pipeline.py` passed (all templates exported FBX/GLB, budgets OK). Cycles CPU previews render. |
| Blender MCP (live Blender app) | ❌ Not connected | Local-only server. Needs owner's PC: Blender + `blender-mcp` addon + `uvx blender-mcp`. See `local-setup.md` + `blender/README.md`. |
| Figma MCP | ✅ Connected | `whoami` → handle `lyssie`, team "lyssie ugc's team" (pro, Full seat, admin). Re-verified 2026-11-04. |
| Roblox Studio MCP | ❌ Not connected | Local-only (Studio plugin + MCP server on owner's PC). No computer linked to this session (`list_computer_folders` → none, re-checked 2026-11-04). See `local-setup.md` + `roblox-studio-mcp.md`. |
| Rojo 7.4.4 | ✅ in CI · ❌ live sync | `rojo build` of vault + scaffolded game succeeds in CI. Live sync to Studio needs the Rojo plugin on the owner's PC. |
| StyLua 2.0.2 / Selene 0.28.0 / luau-analyze 0.650 / Lune 0.8.9 | ✅ in CI · ❌ in cloud session | CI: format clean, 0 lint issues, analyze clean, 71/71 system tests + 10/10 template tests. Running prebuilt binaries inside the cloud session was blocked by its safety policy (re-confirmed 2026-11-04), so cloud sessions rely on CI (push → read Actions logs). Locally: `rokit install`. |
| Git LFS | ✅ Installed | `git-lfs` present; `.gitattributes` tracks binaries. |

## Manual setup the owner must do (one time)
1. ~~Install the Figma connector~~ — done (verified 2026-11-04).
2. **On your Windows/Mac PC** (for Blender + Studio work), open this repo in Claude Code / Claude
   Desktop and run `scripts/setup-local.sh` (or follow `docs/integrations/local-setup.md`):
   Rokit toolchain, Rojo plugin, Blender MCP addon, Roblox Studio MCP plugin.
3. In Roblox Studio: Game Settings → Security → *Enable Studio Access to API Services* (DataStore
   tests) — only for a private test place.
4. Confirm the scale-reference import (see `blender/README.md`).

## CI results log
| Date | Commit | Result |
|---|---|---|
| 2026-11-04 | `5424737` | ❌ StyLua diffs (5), luau-analyze union iteration (3), 1 test bug, Lune abs-path; Blender ✅ |
| 2026-11-04 | `7fe5b72` | ✅ Luau job: all checks pass, 71/71 + 10/10 tests, rojo builds OK · Blender job ✅ |
| 2026-11-04 | `dabd239` | ❌ only selene `manual_table_clone` warning; 81/81 + 28/28 tests pass, rojo OK · Blender ✅ |
