# Ragdoll Off a Mountain — open in Studio + publish to your group

What's in this download
| Item | What it is |
|---|---|
| `Ragdoll Off a Mountain.rbxl` | The place: all game scripts, every UI screen in StarterGui (visible in Edit mode), map markers, daytime lighting |
| `models/` | Blender FBX exports: `map/` (mountain chunks), `basecamp/` (5 base stages), `props/` (cannons, shops, statue…), `pets/` |
| `studio_scripts/` | Command-bar scripts (`build_edit_preview.luau`, `preview_screen.luau`, …) |
| `ui_art/` | Blender-rendered item art for the UI cards (upload as Decals) |

## Steps (about 10 minutes)
1. Double-click **`Ragdoll Off a Mountain.rbxl`** → Studio opens it. You'll see the HUD + Shop
   screens over the viewport right away (Edit mode, no Play).
2. **Import the 3D models** (Roblox only turns FBX into meshes when *you* import them):
   **Home → Import 3D** (or File → Import 3D) → pick each FBX:
   - `models/map/*.fbx` → drop into **Workspace → Map** (keep them Anchored)
   - `models/basecamp/BaseCamp_Stage1..5.fbx` → move into **ReplicatedStorage → Assets → BaseCamps**
   - `models/props/*.fbx` → **ReplicatedStorage → Assets → Props**
   - `models/pets/*.fbx` → **ReplicatedStorage → Assets → Pets**
   (Create the `Assets`, `BaseCamps`, `Props`, `Pets` folders if they don't exist.)
   Importer settings: scale 1 (1 Blender unit = 1 stud), "Anchored" on, keep hierarchy.
3. **Place bases + props in Edit mode**: View → Command Bar → paste `studio_scripts/build_edit_preview.luau` → Enter.
   All 6 base camps and the hub props appear on their spots (still Edit mode).
4. Flip UI screens with `studio_scripts/preview_screen.luau` (change `NAME`).
5. **Game Settings** (Home → Game Settings): Places → Max Players **6**; Avatar → **R15**.
6. **Publish**: File → Publish to Roblox As… → choose **your group** as the creator → name
   "Ragdoll Off a Mountain 🏔️". (Your account, your choice — Claude never publishes.)
7. Tell Claude what you see (screenshots help) — anything off gets fixed in the repo and rebuilt.

## Not in this file yet (honest list)
- Gamepass / product IDs, prices, season end date, real promo codes: CONFIG_REQUIRED (you create them; then I wire the IDs in `Config.luau`).
- UI art images: upload `ui_art/*.png` as Decals and send me the IDs; until then cards show the item name.
- Nothing has been playtested in Studio yet.
