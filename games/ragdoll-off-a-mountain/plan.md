# Ragdoll Off a Mountain — Development Plan

Branch: `claude/ragdoll-mountain-game-5fy1iq` (session-fixed branch, so no `game/<slug>` branch).
Each milestone ends with `scripts/validate.sh` (CI runs the Luau toolchain) + a commit.

| # | Milestone | Output | Tool | Done when |
|---|---|---|---|---|
| 0 | Audit | `docs/integrations/STATUS.md` | all | every tool has a live result |
| 1 | Spec | `game.md` | — | brief + tables complete |
| 2 | Assets | `blender/{map,base_camp,cannons,hub_props,pets}.py` → `assets/export/**` + `assets/previews/**` | Blender (bpy) | pipeline checks + 3-angle renders reviewed vs BAD list + §13 review |
| 3 | UI | `figma/ui-spec.md` + Figma benchmark screen (Shop) with Blender-rendered art | Figma | spec covers all screens; benchmark screen pending owner OK (lesson L-10) |
| 4 | Systems | `src/shared/{Config,RagdollScore,GameLogic}.luau`, `src/server/{Main.server,Ragdoll}.luau`, `src/client/Main.client.luau` | Luau | Lune tests pass in CI |
| 5 | Integration | `studio/import_map.luau` places Blender chunks + markers from `layout.json` | Studio MCP / Rojo | place opens, no output errors |
| 6 | Playtest | `qa/playtest-<date>.md` | Studio MCP | qa/checklist.md run |
| 7 | Fix | commits | all | blocking issues closed |
| 8 | Report | `STATUS.md` | — | tested / untested / not done listed |

## Systems chosen (systems/README.md)
Currency · Upgrades (Peak + Cannon tier ladders, leveled upgrades, Gems ladder) · Rarity · Inventory ·
Rebirth · Plots (6 bases) · Rewards · Tutorial · Monetization · DataService · Guard · Net ·
MarketplaceAdapter · UIAnim · VFX · MobileUI. **Trading: prohibited, not vendored.**

## New code
| Module | Where | Why |
|---|---|---|
| Boosts | `systems/src/Shared/Boosts.luau` (vault, reusable) | timed multipliers (onboarding boost, products, rewards) |
| SeasonPass | `systems/src/Shared/SeasonPass.luau` (vault) | 50-tier free + premium pass |
| PeriodicQuests | `systems/src/Shared/PeriodicQuests.luau` (vault) | daily + weekly quests with UTC resets |
| Codes | `systems/src/Shared/Codes.luau` (vault) | promo codes, one per user |
| RagdollScore | `games/ragdoll-off-a-mountain/src/shared/` (game) | bones → Cash rule |
| Ragdoll | `games/ragdoll-off-a-mountain/src/server/` (game, Studio-only) | server-owned ragdoll + impact measurement |

## Risks
- Ragdoll physics tuning (break speeds, slope angles, landing) can only be tuned in a Studio playtest.
- Economy pacing in game.md §7 is a target, not measured — needs playtest telemetry.
