# Lessons & Corrections (automatic learning)

Handled by the `/vault-learn` skill whenever the owner corrects something.

| File | Scope |
|---|---|
| `global.md` | applies to every future game |
| `games/<slug>/lessons.md` | applies to that game only (exceptions live here) |

## Promotion rules
- A correction is **game-specific by default**.
- Promote to `global.md` only if (a) the owner says it applies to all games ("always", "every
  game", "from now on"), or (b) the same correction has appeared in **2+ different games** — then
  ask the owner once before promoting.
- Never turn a one-time exception into a global rule.

## Entry format
```
### L-YYYYMMDD-NN — <short title>
- Scope: global | game:<slug>
- Trigger: what the owner said (quote)
- Root cause: why it happened (which file/rule/template was wrong or missing)
- Rule: the corrected behaviour, stated as an instruction
- Applied to: files changed (templates/systems/style) + commit sha
- Validation: what was run
```
One lesson = one commit (`lesson(<scope>): <title>`) so it can be reverted cleanly.
