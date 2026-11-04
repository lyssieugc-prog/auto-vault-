---
name: make-game
description: Generate a complete Roblox game from a name + short description using the vault's style profiles, genre profiles, reusable Luau systems, Blender asset pipeline, Figma UI specs and QA procedures. Use when the owner says /make-game, pitches a new game, or asks to build a game.
argument-hint: "<Game Name>" "<short description>" [custom requirements]
---

# /make-game

Input: **game name**, **short description**, optional **custom requirements** (`$ARGUMENTS`).
Goal: plan → build → integrate → test → save → report, with as few questions as possible.

Ask the owner ONLY if a missing decision would materially change the game (e.g. the core loop
is genuinely ambiguous between two genres). Otherwise decide, mark it *(inferred)* in the spec,
and keep going. Never stop between steps unless blocked.

## 0. Load context + audit (always)
1. Read `CLAUDE.md`, `style/house-style.md`, `lessons/global.md`, `qa/README.md`.
2. Run the live checks in `docs/integrations/audit.md`; update `docs/integrations/STATUS.md`.
   Note which tools are unavailable — steps that need them become "built, untested" or
   "blocked", never faked.

## 1. Classify
Pick primary genre (`genres/*.md`) and style profile (`style/profiles/*.md`). Hybrids: primary +
borrowed systems. Read both files fully.

## 2. Scaffold
`scripts/new-game.sh "<Name>" --branch` → `games/<slug>/` on branch `game/<slug>`.
(If the session must push to a fixed branch, skip `--branch` and use the session branch.)

## 3. Spec
Fill `games/<slug>/game.md` (from `blueprints/gdd-template.md`) including the house quickstart
brief, zones, content tables, systems, screens, monetization placeholders, pacing targets.
Commit: `spec(<slug>): game design spec`.

## 4. Plan
Write `games/<slug>/plan.md` from `blueprints/dev-plan-template.md`. Choose systems from
`systems/README.md`; list any genuinely new system needed (build it in `systems/` as a reusable
module with tests if it is generic, else in `games/<slug>/src`).

## 5. Assets (Blender — ALL custom models/maps)
- **Originality:** design ORIGINAL assets for THIS game with the shared modeling language
  (`style-guides/3D_STYLE_BIBLE.md` ★). Never reuse calibration-sample objects
  (`blender/templates/test_collection.py`) or copy reference objects/compositions. Build with the
  technique toolkit `blender/lib/vault_kit.py` (+ `vault_blocky.py`).
- **Quality gate:** for every major asset run the professional-asset review (bible §13) and write
  in `games/<slug>/assets/review.md`: "Pro simulator asset or generic procedural block model?" +
  the fixes made. Detail must make sense for the subject (no frog spikes).
- Write `games/<slug>/blender/handoff.md` for hero/collectible assets.
- Copy + adapt `blender/templates/*.py` into `games/<slug>/blender/`; run them (Blender MCP if
  connected, else `bpy`/CLI) → `games/<slug>/assets/export/`.
- Render previews (`blender/tools/render_preview.py` pattern), LOOK at them, fix BAD-list issues.
- Check triangle budgets. Update `assets/manifest.json`. Commit `assets(<slug>): …`.
- Never build custom models from Studio Parts.

## 6. UI (Figma)
If Figma MCP is connected: create/duplicate the UI file from `figma/components.md` + tokens,
theme it for this game, record `figma/figma.json`. If not: write `games/<slug>/figma/ui-spec.md`
(every required screen, layer names per `figma/roblox-mapping.md`) and mark UI "blocked on Figma".
Commit `ui(<slug>): …`.

## 7. Systems (Luau)
Rewrite `games/<slug>/src/shared/Config.luau` from the spec; extend `GameLogic.luau` for
genre systems (Plots/Stealing/Tycoon/Trading from `vendor/vault/Shared`). Every remote goes
through `Net` with `Guard` validation, all economy server-side. Add tests to
`games/<slug>/tests/run.luau` for every new rule. Commit `systems(<slug>): …`.

## 8. Integrate (Studio MCP + Rojo)
Rojo-sync scripts; import FBX chunks and place them from `layout.json` via saved `run_code`
scripts in `games/<slug>/studio/`; build ScreenGuis from Figma. Never publish.
If Studio MCP is unavailable, mark integration "blocked" and continue with everything else.

## 9. Test
`scripts/validate.sh` (must pass) + `qa/playtest.md` (if Studio available) + `qa/checklist.md`.
Write `games/<slug>/qa/playtest-<date>.md`.

## 10. Fix
Fix every blocking finding; re-run the failing checks. Record generalizable mistakes with
`/vault-learn` rules (game-specific by default).

## 11. Save
Commit per milestone; push the branch (`git push -u origin <branch>`). Never commit secrets.
Do not publish to Roblox, create products or spend Robux without explicit approval in chat.

## 12. Report
Update `games/<slug>/STATUS.md` and reply with:
- ✅ **Tested** (with the evidence: which test / playtest step)
- 🟡 **Built, untested** (and why: e.g. Studio MCP not connected)
- ❌ **Not done / blocked** (exact manual step that unblocks it)
- House-style final check results (`qa/checklist.md` style section)
- Next recommended step.
Never call the game playable unless a playtest in Studio actually ran it.
