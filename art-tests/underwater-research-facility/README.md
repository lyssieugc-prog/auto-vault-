# Art Test — Underwater Research Facility ("Coralreach Station")

Original design made with **no references**, to test whether the vault's art style transfers to a
brand-new concept. Nothing here reuses the café calibration sample or any reference object/layout.
The café project (`blender/templates/test_collection.py`) was not modified.

## Deliverables
| File | What |
|---|---|
| `underwater_facility.blend` | Complete scene (Git LFS) |
| `scripts/build_facility.py` | Builds the whole environment with Blender Python |
| `scripts/uw_kit.py` | Underwater modeling techniques (tunnels, portholes, rings, reef life, kelp, stud normal-map shader) |
| `scripts/render_facility.py` | Lighting rig + all renders + material/stud preview scene |
| `renders/01_full_environment.png` | Full environment |
| `renders/02–09, 12–13` | Close-ups: hub, lab windows, dome, creature, sub dock, ruins, reef, tunnels/pod, submarine, trench bridge |
| `renders/10_material_board.png`, `11_stud_macro.png` | Material + stud texture preview |
| `textures/stud_tile_height.png`, `stud_tile_normal.png` | Seamless 256 px stud tile (height + OpenGL tangent normal map) |

Rebuild: `python art-tests/underwater-research-facility/scripts/render_facility.py 18`
(uses the `bpy` module, Python 3.13; or run the scripts with `blender -b -P`).

## What's in the scene
- **Research hub** — octagonal 3-tier station: studded plinth, wall bands with bolt rows, corner struts with
  plates, leaning buttresses, framed portholes (frame ring + lit glass + bolts), panel strips, airlock door
  (frame, hazard lintel, wheel, lamps, two-step stair), fish sign, observation deck with brackets, marker
  lights, glass ring + consoles inside, stepped roof with fins, railed cap deck with gear, radar dish, beacon
  mast, roof vents with bubble columns, external pipes with clamps, tethered sensor buoy (silhouette).
- **Laboratory wing** — big window wall (mullions, transom, hood + light bar), corner frame pillars, bolted
  side panels, back-wall pipe runs with clamps, roof fans, parapet, skylight, dish array, ladder, sign with
  flask icon. **Visible inside:** ceiling lights, benches with monitors, microscopes and jars, glowing
  specimen tanks, server racks with LEDs, whiteboard.
- **Habitat pod** — 12-sided pod with ribs, portholes, bolt ring, accent plates, angled landing legs,
  rooftop glass greenhouse with hydroponic plants and grow light, ladder, antenna.
- **Glass observation tunnels** — smooth glass tubes with studded rib rings, walkway, light strip,
  support legs, cradles and footings (hub↔lab, hub↔pod, hub↔dome, lab↔dock).
- **Aquarium dome** — ribbed glass hemisphere (latitude rings + segmented meridian ribs), studded base with
  uplights, sand floor with coral/anemone/sponge/starfish, bubbles, crown light, info plaque.
- **Bubblemunch** (original creature) — chunky magenta lure-fish: belly plate, brow, giant eyes, toothy grin,
  scale plates and gill slits on the flanks, layered dorsal/pectoral/tail fins, back spots, arched lure stalk
  with a glowing bulb. (Scales/fins fit a fish — no implausible details.)
- **Submarine dock + "Snorkel-9"** — pier with plank lines, hazard edge, pilings with bands, cross-bracing,
  bollards, railing, crane with cab/counterweight/hook, crates with straps, fuel tanks, docking clamps, hose,
  control hut with framed window. Sub: rounded hull + keel + stepped nose, bubble cockpit with frame,
  hull bands, bolted armor plates, stripe, portholes, ballast pods, headlights, conning tower with hatch,
  periscope and whip antenna, searchlight arm, thrusters with grilles, stabilizers with nav lights,
  rudders, shrouded propeller, claw arm, keel fins, intake grilles, handrail, tow ring, rivets.
- **Ruins dig site** — stepped platform with a broken corner, ring of intact/broken/fallen columns,
  archway with glowing keystone rune, carved guardian totem with glowing eyes, crystal clusters, rune
  tablets, floating orbs, survey stakes with tape and flags, tool crate + shovel, work lamp, open treasure
  chest with coins.
- **Landscape** — blocky stepped seabed grid (rock body + darker ledge band + sand/moss cap per column),
  rolling stepped mounds, high back/side shelves, a two-step trench with a wooden bridge, reef groups
  (branch, brain, table coral, sea fans, tube sponges, anemones, starfish, urchins), kelp forests,
  sea-grass meadows, glow plants, rock arch, balancing rock pillars, sunken boat bow, anchor, barrels.
- **Machinery & life** — pump station (tanks, valves, gauges, pipes into the lab), generator with fans and
  exhaust, seabed power cables with junction boxes, tiled path network with lamps and signposts, sensor
  buoys on chains, crate stacks, fish trap, fish schools, jellyfish, bubble vents, three divers (5-stud
  R6 scale) for scale.

## Modeling techniques used
1. **Composition from simple primitives** — boxes, rounded boxes, cylinders/cones, rings, balls; every
   asset is many layered pieces (base → trim/panel → bolts/props), never one textured cube.
2. **Texture studs only** — seamless 256 px stud tile → tangent normal map → Normal Map node; world-space
   box UVs at 0.5-stud spacing so studs stay small and consistent on every solid surface (including the
   creature). Glass, water, glow and face pieces stay smooth. No stud geometry anywhere.
3. **Physical detail for architecture** — frames, mullions, bands, bolts, struts, buttresses, brackets,
   hazard stripes, pipes and clamps are real geometry.
4. **Multi-shade palettes** — every material uses `vault_kit.shades` (light/base/dark/deep):
   sunny yellow + lagoon teal + deep navy + coral accent on the facility; slate rock + sand + moss on terrain.
5. **Exaggerated proportions** — giant eyes and lure on the creature, chunky sub with oversized cockpit
   bubble, tall beacon masts and buoys for readable silhouettes.
6. **Stepped terrain** — grid columns run-length merged per row; height function combines flat building
   pads, structured stepped mounds, shelves and a two-step trench.
7. **Purposeful dressing** — reefs, meadows, base plantings, props and machinery are placed as groups
   along paths, building bases, shelf tops and the trench (environmental storytelling: researchers dig at
   the ruins, power runs from the generator, tanks feed the lab).
8. **Lighting** — bright warm sun with soft shadows, low blue ambient for contrast, light bounded
   underwater haze (not a world fog), emissive accents for glowing windows, screens, crystals and plants.

## Honest self-review (pro simulator asset or generic procedural block model?)
- **Strongest:** hub, dome, submarine, dock — layered, readable silhouettes, intentional colour.
- **Good:** lab (interior reads through glass), ruins (storytelling), trench + bridge.
- **Weaker:** terrain shelf tops are still large planes in places; tunnel interiors are simple; the creature's
  side scales read small at distance.

## Not done in this test (by request)
Nothing was built or imported in Roblox Studio. Assets are not yet split into per-asset export batches;
that is the next step if this style is approved.
