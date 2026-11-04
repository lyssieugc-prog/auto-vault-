# Integration Status

Only mark a tool ✅ after a **live successful call in that environment**. Re-verify at the start of
every `/make-game` run (step 0) and update this file when anything changes.

Last audit: 2026-11-04 · Environment: Claude Code cloud session (Linux container)

| Tool | Status | Evidence / what is missing |
|---|---|---|
| GitHub (MCP) | ✅ Connected | `get_me` → `lyssieugc-prog`; branch listing on `lyssieugc-prog/auto-vault-` OK; git push over proxy OK. |
| GitHub Actions CI | ✅ Green | Run #2 (`7fe5b72`): Luau job + Blender job passed. See log below. |
| Blender (bpy 5.2.3 Python module) | ✅ Works in cloud + CI | `blender/tests/test_pipeline.py` passed (all templates exported FBX/GLB, budgets OK). Cycles CPU previews render. |
| Blender MCP (live Blender app) | ❌ Not connected | Local-only server. Needs owner's PC: Blender + `blender-mcp` addon + `uvx blender-mcp`. See `local-setup.md` + `blender/README.md`. |
| Figma MCP | ❌ Not connected | Figma connector exists in the claude.ai directory but is **not installed** for this account. See `figma/README.md`. |
| Roblox Studio MCP | ❌ Not connected | Local-only (Studio plugin + MCP server on owner's PC). No computer linked to this session. See `local-setup.md` + `roblox-studio-mcp.md`. |
| Rojo 7.4.4 | ✅ in CI · ❌ live sync | `rojo build` of vault + scaffolded game succeeds in CI. Live sync to Studio needs the Rojo plugin on the owner's PC. |
| StyLua 2.0.2 / Selene 0.28.0 / luau-analyze 0.650 / Lune 0.8.9 | ✅ in CI · ❌ in cloud session | CI: format clean, 0 lint issues, analyze clean, 71/71 system tests + 10/10 template tests. Running prebuilt binaries inside the cloud session was blocked by its safety policy, so cloud sessions rely on CI (push → read Actions logs). Locally: `rokit install`. |
| Git LFS | ✅ Installed | `git-lfs` present; `.gitattributes` tracks binaries. |

## Manual setup the owner must do (one time)
1. **Install the Figma connector** at claude.ai → Settings → Connectors → Figma (then re-run audit).
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
