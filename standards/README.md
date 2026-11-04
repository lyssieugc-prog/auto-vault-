# Permanent Project Standards (owner-provided, verbatim — do not silently override)

| File | Scope |
|---|---|
| `GAME_SYSTEMS.md` | Pipeline, 6 players / 6 progressive bases, x2→x128 multiplier, Season 1 50-tier pass, onboarding, collections/odds, NO trading, universal systems, data, deliverables, quality gates |
| `UI_ANIMATION_STANDARDS.md` | Bright bubbly UI, Figma components + states, motion contract, UIEffects rules, UI playground checklist |
| `VALIDATION_PLAN.md` | **MISSING — not yet received from the owner.** Until provided, validation follows the quality gates in the two files above + `qa/`. |
| `FOUNDATION_START_PROMPT.md` | The foundation-test brief (steps 1–5) |

Precedence: these files > `style/` + `style-guides/` > older vault defaults. Explicit per-game owner
instructions override, except the non-negotiables.

## Conflicts with older vault defaults (resolved in favour of these standards)
| Older vault default | Now |
|---|---|
| `systems/src/Shared/Trading.luau` offered player-to-player trading | **Prohibited.** Module kept only as code history; must never be required by a game. `scripts/validate.sh` fails if a game references it. |
| Multiplier ladder 2→3→5→10→25→50→100 | **x2 → x4 → x8 → x16 → x32 → x64 → x128 max**, prices rise per tier, prices/IDs are CONFIG_REQUIRED |
| 8 plots per server | **6 players max, 6 themed progressive bases**, one per player |
| Pets/eggs in every game (house-style) | Only when the description calls for them; otherwise a theme-appropriate collection/acquisition system |
| Odds shown as % | **1 in N** and/or %, server-defined, true |
