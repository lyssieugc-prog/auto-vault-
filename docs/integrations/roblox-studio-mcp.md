# Roblox Studio MCP + Rojo

Studio is for **integration, gameplay scripting, configuration and testing** — never for modelling
custom assets out of Parts.

## Responsibilities
| Job | Tool |
|---|---|
| Source of truth for scripts | Git + Rojo (`games/<slug>/src`) |
| Syncing scripts into Studio | `rojo serve` + Rojo plugin |
| Importing Blender FBX, placing chunks from `layout.json` | Studio MCP `run_code` (Luau) / 3D Importer |
| Building ScreenGuis from Figma | Studio MCP `run_code` following `figma/roblox-mapping.md` |
| Playtests | Studio MCP start/stop play + read output; see `qa/playtest.md` |

## Safety
- Work in a **private test place**. Never publish, change place privacy, create developer products
  or spend Robux without the owner's explicit approval in chat.
- `run_code` snippets that change the DataModel must be saved to `games/<slug>/studio/` so they
  are reproducible (and reviewable in git).
- Anything created in Studio that should persist (UI, placed assets) is exported back as `.rbxm`
  into `games/<slug>/studio/` (LFS) or rebuilt from scripts.
