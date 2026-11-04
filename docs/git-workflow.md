# Git Workflow, Status & Recovery

## Branches
| Branch | Purpose |
|---|---|
| default branch | the vault: instructions, systems, templates (always green CI) |
| `game/<slug>` | one branch per game; game lives in `games/<slug>/` |
| `vault/<topic>` | improvements to shared systems/templates (merged via PR after CI) |
| `claude/*` | session branches created by Claude Code |

## Commit at milestones (Claude does this automatically)
`spec` → `assets` → `ui` → `systems` → `integration` → `tests` → `report`. Message format:
`<area>(<slug>): <what>` e.g. `assets(lava-pets): blender map chunks + layout.json`.
Run `scripts/validate.sh` before every commit; never commit with failing checks without
saying so in the message (`WIP: tests failing — <why>`).

## Never commit
Secrets of any kind (`.ROBLOSECURITY`, API keys, Open Cloud keys, Figma tokens). `.gitignore`
blocks common files; `scripts/check-secrets.sh` runs in CI.

## Large files
Git LFS tracks `.blend .fbx .glb .obj .png .jpg .psd .rbxl .rbxm .wav .ogg .mp3` (see
`.gitattributes`). Keep source scripts (`.py`) as plain text so assets are reproducible.

## Status
Each game keeps `games/<slug>/STATUS.md` (what is tested / built-untested / not done, next step).

## Recovery
| Problem | Fix |
|---|---|
| Bad vault change | `git log -- <file>` → `git revert <sha>` (never force-push the default branch) |
| Bad lesson/rule | revert the lesson commit; lessons are one commit each for this reason |
| Broken game branch | `git checkout game/<slug>` → `git reset --hard <last good sha>` locally, push to a new branch `game/<slug>-recovered` |
| Lost session | new session reads `CLAUDE.md` → `games/<slug>/STATUS.md` → continues from "Next step" |
| LFS files missing | `git lfs install && git lfs pull` |
