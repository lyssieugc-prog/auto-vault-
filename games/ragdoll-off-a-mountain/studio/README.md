# Studio integration (needs Roblox Studio MCP on the owner's PC — not available in cloud sessions)

Order (run each through Studio MCP `run_code`, or paste into the Studio command bar):

1. **Scale check** — import `blender/templates/scale_reference.py` output, confirm the cube is 4×4×4 studs.
2. **Import FBX chunks** (3D Importer or Studio MCP bulk import) from `assets/export/`:
   - `map/*.fbx` → `Workspace.Map` (Anchored, CanCollide on; keep chunk names `Map_*`)
   - `basecamp/*.fbx` → `ReplicatedStorage.Assets.BaseCamps.BaseCamp_Stage1..5` (Models, PrimaryPart = pad centre)
   - `props/*.fbx` → `ReplicatedStorage.Assets.Props.*` then place hub props on their markers
   - `pets/*.fbx` → `ReplicatedStorage.Assets.Pets.<PetId>`
   - Apply the stud texture: `Texture` on every face, StudsPerTileU/V = 0.5 (bible §2). Record the
     importer settings that worked in `games/ragdoll-off-a-mountain/lessons.md`.
3. **Markers** — run `place_markers.luau` (generated from `assets/export/map/layout.json` by
   `python3 games/ragdoll-off-a-mountain/studio/gen_markers.py`). It creates `Workspace.Map.Markers.*`
   anchored, invisible, CanCollide=false parts the server scripts look up by name.
4. **Rojo** — `rojo serve games/ragdoll-off-a-mountain/default.project.json` and connect the plugin.
4b. **Edit-mode preview (owner rule L-11)** — run `build_edit_preview.luau`: puts every ScreenGui in
   StarterGui (mock data) and places base camps + hub props on their markers, all saved in the place,
   so map + UI are visible WITHOUT pressing Play. Flip screens with `preview_screen.luau`.
5. **Game Settings (owner)** — Max Players **6**, Avatar **R15**, Studio API access only in a private test place.
6. Play (Server + 1 client) and follow `qa/playtest.md`. Never publish.
