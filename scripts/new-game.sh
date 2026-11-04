#!/usr/bin/env bash
# Scaffold a new game from templates/game.
#   scripts/new-game.sh "Lava Pets" [--branch] [--dest <dir>]
# Creates games/<slug>/ (or <dir>/<slug>), vendors the current systems library (pinned in
# vault.lock), copies the GDD template, fills placeholders. --branch creates game/<slug> first.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?usage: new-game.sh \"Game Name\" [--branch] [--dest dir]}"
shift
BRANCH=0
DEST="$ROOT/games"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH=1 ;;
    --dest) DEST="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
  shift
done

SLUG="$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
[[ -n "$SLUG" ]] || { echo "could not derive slug from name" >&2; exit 2; }
TARGET="$DEST/$SLUG"
[[ ! -e "$TARGET" ]] || { echo "$TARGET already exists" >&2; exit 1; }

if [[ $BRANCH -eq 1 ]]; then
  git -C "$ROOT" checkout -b "game/$SLUG"
fi

mkdir -p "$TARGET"
cp -R "$ROOT/templates/game/." "$TARGET/"
mkdir -p "$TARGET/vendor/vault/tests"
cp -R "$ROOT/systems/src/Shared" "$ROOT/systems/src/Server" "$ROOT/systems/src/Client" "$TARGET/vendor/vault/"
cp "$ROOT/systems/tests/TestKit.luau" "$TARGET/vendor/vault/tests/"
cp "$ROOT/blueprints/gdd-template.md" "$TARGET/game.md"

VAULT_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
cat > "$TARGET/vault.lock" <<EOF
vault_commit=$VAULT_SHA
vendored=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# To update: re-copy systems/src/* into vendor/vault and bump this file in the same commit.
EOF

TODAY="$(date -u +%Y-%m-%d)"
# Escape sed replacement metacharacters in the display name.
ESC_NAME="$(printf '%s' "$NAME" | sed -e 's/[\/&|]/\\&/g')"
grep -rlE '\{\{(GAME_NAME|SLUG|DATE)\}\}' "$TARGET" | while read -r f; do
  sed -i.bak -e "s|{{GAME_NAME}}|$ESC_NAME|g" -e "s|{{SLUG}}|$SLUG|g" -e "s|{{DATE}}|$TODAY|g" "$f"
  rm -f "$f.bak"
done
sed -i.bak -e "s|^# <Game Name>|# $ESC_NAME|" "$TARGET/game.md" && rm -f "$TARGET/game.md.bak"

echo "Created $TARGET (slug: $SLUG, vault $VAULT_SHA)"
