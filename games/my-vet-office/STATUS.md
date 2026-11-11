# My Vet Office! — Status

Branch: `claude/my-vet-office-roblox-glys4p` · Vault: see `vault.lock` · Last update: 2026-11-11

## Next step
Connect the owner's PC (Roblox Studio MCP + Rojo, see `docs/integrations/local-setup.md`), import
the Blender assets, build the clinic shell, and run `qa/playtest-plan.md` §A.

## Features
| Feature | State | Evidence |
|---|---|---|
| Game design document (`game.md`, 10 sections) + `plan.md` | ✅ written | — |
| Animal mind / behaviour AI / pose graph / animation math / procedural poses + gait | ✅ tested (logic) | Lune `tests/run.luau` |
| Procedures (16 physical step machines), appointments, diagnosis, billing, follow-ups | ✅ tested (logic) | every level-1/2 case solved end-to-end by a scripted player |
| Clinic: economy, deliveries, placement, rooms, staff hiring, roles/permissions, save/reload | ✅ tested (logic) | Lune |
| Server glue (World: NPC pathfinding, furniture, sensing; remotes + validation) | 🟡 built, untested | needs Studio |
| Client AnimalAnimator (layers, IK, LOD), Interaction (gestures, cameras), dev panel | 🟡 built, untested | needs Studio |
| Blender assets (golden retriever rig, exam props) | 🟡 see `assets/review.md` | renders pending owner approval |
| Figma UI | ❌ blocked — spec + tokens written, file not created | `figma/ui-spec.md` |
| Studio integration + playtest | ❌ blocked — no Studio MCP / computer connected | — |
| Staff AI, emergencies UI, X-ray/blood/ultrasound, surgery, more species | ❌ later milestones | `game.md` §10 |

Legend: ✅ tested · 🟡 built, untested · ❌ not done (see qa/README.md)

## Blocked on
- Roblox Studio MCP + Rojo live sync (owner's PC) — integration and every in-engine test.
- Figma file creation (spec ready).
