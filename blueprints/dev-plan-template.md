# <Game Name> — Development Plan

Each milestone ends with `scripts/validate.sh` + a commit on `game/<slug>`.

| # | Milestone | Output | Tool | Done when |
|---|---|---|---|---|
| 0 | Audit | updated `docs/integrations/STATUS.md` | all | every tool has a live result |
| 1 | Spec | `games/<slug>/game.md` | — | brief + tables complete |
| 2 | Assets | `games/<slug>/blender/*.py` → `assets/export/` + previews | Blender | pipeline checks + preview reviewed vs BAD list |
| 3 | UI | Figma file + `figma/figma.json` | Figma | all required screens exist |
| 4 | Systems | `games/<slug>/src/**` config + glue | Luau | Lune tests pass |
| 5 | Integration | assets + UI in Studio place | Studio MCP / Rojo | place opens, no output errors |
| 6 | Playtest | `games/<slug>/qa/playtest-<date>.md` | Studio MCP | qa/checklist.md run |
| 7 | Fix | commits | all | blocking issues closed |
| 8 | Report | `games/<slug>/STATUS.md` | — | tested / untested / not done listed |
