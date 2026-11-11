# My Vet Office! — Dev Plan

Owner priority: **animal rigging, animation, behaviour and interaction first**; everything else is
built around them. One extremely polished appointment (golden retriever) before expanding.

## Systems
| System | Source | Notes |
|---|---|---|
| DataService, Guard, Net, Tutorial, Format | vault (`vendor/vault`) | reused unchanged |
| Currency / Tycoon / Rarity / Rebirth / Trading / Monetization | vault | **not used** — no click-income, eggs or purchase pads in this game |
| Species, AnimalMind, AnimalBehavior, PoseGraph, PoseLibrary, AnimBlend | new, game-local | candidates to promote to `systems/` (generic creature AI + animation) once a 2nd game needs them |
| Cases, Procedures, Appointment, Clinic, GameLogic | new, game-local | vet-specific |
| World, Main (server) · AnimalAnimator, Interaction, Main (client) | new, game-local | Roblox glue, Studio-only testable |

## Integration (Studio — needs the owner's PC: Studio MCP + Rojo plugin)
1. `rojo serve games/my-vet-office/default.project.json`.
2. Import FBX from `assets/export/` (Studio 3D Importer, *rig* = keep Motor6Ds): animals →
   `ReplicatedStorage.Assets.Animals.<Breed>`; furniture → `Assets.Furniture.<CatalogId>`
   (cabinet door part named `Door`, drawer part `Drawer`); tools → `Assets.Tools.<Tool>`;
   `Assets.Carrier`, optional `Assets.BandageWrap`; sounds → `Assets.Sounds.<Species>.<Vocal>`.
3. Clinic shell (Blender) → `Workspace.Clinics.Plot1..6` with the markers listed at the top of
   `src/server/World.luau` (Entrance, ReceptionQueue, WaitingSeats/*, Rooms/<Room>/Origin, Door,
   TableSpot, OwnerSpot, Checkout, Exit, DeliveryDoor). Tag sniffable spots `Scent`.
4. Lighting: Future, warm interior, day/night following `Config.clinic.dayLengthSeconds`.
5. Build the Figma ScreenGuis with the layer names in `figma/ui-spec.md`; delete nothing — the
   Studio dev panel auto-hides once `VetComputer` exists.
6. Run `qa/playtest-plan.md`.

## Risks
- Procedural poses/gait are a first pass: authored clips (Blender actions → Roblox animations)
  will likely be needed for Sit/Lie transitions and gestures to look truly natural. The animator
  already prefers authored tracks when present (layered on the same additive system).
- Body-coordinate mapping assumes the model faces −Z with Root at ground; verify on import.
