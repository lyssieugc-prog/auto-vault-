# Local Setup (owner's computer)

The cloud session can write code, run tests, build Blender assets headless and push to GitHub.
**Live Blender, Figma desktop and Roblox Studio require a session running on your own computer**
(Claude Code CLI / Desktop opened in this repo).

## 1. Toolchain (Rojo, StyLua, Selene, Lune, Luau)
```bash
# install rokit once: https://github.com/rojo-rbx/rokit
rokit install          # reads rokit.toml (pinned versions)
scripts/validate.sh    # lint + format check + tests + rojo build
```

## 2. MCP servers
Copy `docs/integrations/mcp.local.example.json` to `.mcp.json` in the repo root (it is gitignored)
and adjust paths. Claude Code asks you to approve project servers on first launch.

| Server | Install |
|---|---|
| Roblox Studio MCP | Roblox's official `studio-rust-mcp-server` release: run its installer, which adds the Studio plugin and registers the server with Claude. Open Studio → Plugins → MCP → enable. |
| Blender MCP | Install the `blender-mcp` addon in Blender (Edit → Preferences → Add-ons → Install `addon.py`), enable it, click *Connect to Claude* in the N-panel; server runs via `uvx blender-mcp` (needs `uv`). |
| Figma | Preferred: the Figma connector on claude.ai (remote). Alternative: Figma desktop → Dev Mode → enable the local MCP server. |

## 3. Rojo live sync
`rojo serve games/<slug>/default.project.json` → Studio Rojo plugin → Connect.

## 4. Verify
Start Claude Code in the repo and ask: "run the integration audit" — Claude follows
`docs/integrations/audit.md` and updates `STATUS.md` with real results.
