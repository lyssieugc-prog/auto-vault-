---
name: vault-learn
description: Record an owner correction into the vault (global rule or game-specific exception), update affected templates/systems, validate and commit. Use whenever the owner corrects, criticises or overrides something Claude made ("no, make it…", "don't…", "I hate…", "always…", "from now on…"), or says /vault-learn.
argument-hint: "<what was wrong / the correction>" [game slug]
---

# /vault-learn — persistent corrections

1. **Restate** the correction in one line and identify the **underlying mistake** (which rule,
   template, system or missing instruction caused it). Look at the actual file/asset.
2. **Scope it**:
   - Default: **game-specific** → `games/<slug>/lessons.md`.
   - **Global** → `lessons/global.md` only if the owner said it applies everywhere ("always",
     "every game", "from now on", "never again"), OR the same correction already exists in
     another game's lessons — in that case ask once: "Make this a rule for all games?"
   - Never promote a one-time exception to a global rule on your own.
3. **Write the lesson** (format in `lessons/README.md`), newest first.
4. **Fix the source** when appropriate:
   - Global visual rule → `style/house-style.md` or the matching `style/profiles/*.md`.
   - Genre mechanic → `genres/*.md`. Code behaviour → `systems/src` (+ a test that would have
     caught it). Asset look → `blender/lib` / `blender/templates`. UI → `figma/*`.
   - Game-only → that game's files only.
   - Also fix the current game's instance of the mistake.
5. **Validate**: `scripts/validate.sh` (plus re-render previews for visual fixes).
6. **Commit** as its own commit: `lesson(<global|slug>): <title>` so it can be reverted with
   `git revert`. Push the current branch.
7. Tell the owner: what was recorded, where, scope, files changed, validation result.
