# Blender Asset Pipeline

**Rule: every custom 3D model and all custom map geometry come from Blender.** Roblox Studio only
imports, configures and scripts them.

```
blender/
  lib/vault_blocky.py        blocky/studded primitives, palette materials, joins, poly report, FBX/GLB export
  templates/
    scale_reference.py       4x4x4 cube: import first in every game to verify scale
    creature.py              pet/creature (many parts, glow eyes, rarity-scaled spikes)
    prop_kit.py              tree / rock / lamp / chevron road tile / egg stand
    map_layout.py            hub plaza + paths + zone islands + water ring + plot ring, chunked, layout.json
  tools/render_preview.py    Cycles CPU PNG previews (headless-safe)
  tests/test_pipeline.py     runs all templates, checks exports + triangle budgets + stud guard
  handoff-template.md        model handoff doc (write BEFORE modelling)
```

## How to run
| Where | Command |
|---|---|
| Blender MCP (local, `execute_blender_code`) | `exec(open("<repo>/blender/templates/creature.py").read())` then call `main("<out>")` |
| Blender CLI | `blender -b -P blender/templates/map_layout.py -- games/<slug>/assets/export/map` |
| Python `bpy` module (cloud/CI) | `pip install bpy==5.2.3` (Python 3.13) → `python blender/tests/test_pipeline.py` |

## Per-game workflow
1. Write `games/<slug>/blender/handoff.md` from `handoff-template.md` (style rules + part list).
2. Copy the closest template into `games/<slug>/blender/` and edit its `SPEC`/`LAYOUT`.
3. Run it → exports to `games/<slug>/assets/export/` (FBX per asset/chunk, GLB previews,
   `layout.json` markers, `manifest.json`).
4. Render previews (`tools/render_preview.py`) and look at them. Fix anything on the BAD list.
5. Import into Studio (3D Importer or Studio MCP bulk import) → MeshParts under
   `Workspace.Map` / `ReplicatedStorage.Assets`. Record resulting asset IDs in
   `games/<slug>/assets/manifest.json`.
6. Commit `.blend`/`.fbx`/`.glb` (Git LFS) + scripts + manifest.

## Conventions
- 1 Blender unit = 1 stud. Pivot = bottom-center. Names: `PascalCase`, map chunks `Map_<Region>`.
- Materials carry `roblox_color` / `roblox_neon` custom props → importer sets Color/Material.
- Studs: real geometry up to 400 per surface; larger surfaces set `vault_stud_texture` and get
  the stud texture in Studio instead (mobile budget).
- Triangle budget per exported mesh ≤ 15k (Roblox hard cap 20k). See `qa/performance-budget.md`.
- Scale is verified per game with `scale_reference.py`; record the importer setting that gives
  exactly 4 studs in `lessons/global.md` once confirmed.
