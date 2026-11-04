#!/usr/bin/env bash
# Validate the vault (and every game under games/). Used locally and in CI.
#   scripts/validate.sh            run everything available, report what was skipped
#   STRICT=1 scripts/validate.sh   fail if any tool is missing (CI)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FAIL=0
SKIPPED=()

have() { command -v "$1" >/dev/null 2>&1; }
step() { printf '\n== %s\n' "$1"; }
run() { "$@" || { echo "FAILED: $*"; FAIL=1; }; }
need() {
  if have "$1"; then return 0; fi
  SKIPPED+=("$1")
  [[ "${STRICT:-0}" == "1" ]] && { echo "MISSING TOOL: $1"; FAIL=1; }
  return 1
}

LUAU_DIRS=(systems/src templates/game/src)
for g in games/*/src; do [[ -d "$g" ]] && LUAU_DIRS+=("$g"); done

step "Secrets"
run scripts/check-secrets.sh

step "Standards: no player-to-player trading"
if grep -rlE "Shared/Trading|Shared\.Trading|\bTrading\.new" games/*/src templates/game/src 2>/dev/null | grep -q .; then
  echo "FAILED: a game references the prohibited Trading module"; FAIL=1
else echo "ok no trading references"; fi

step "Structure"
for f in CLAUDE.md .claude/skills/make-game/SKILL.md .claude/skills/vault-learn/SKILL.md \
  style/house-style.md systems/default.project.json templates/game/default.project.json; do
  [[ -f "$f" ]] && echo "ok $f" || { echo "MISSING $f"; FAIL=1; }
done
for p in brainrot simulator tycoon obby realistic-building girly; do
  [[ -f "style/profiles/$p.md" ]] || { echo "MISSING style profile $p"; FAIL=1; }
done
run python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" \
  figma/tokens.json systems/default.project.json templates/game/default.project.json \
  docs/integrations/mcp.local.example.json && echo "ok json"

step "StyLua (format)"
need stylua && run stylua --check "${LUAU_DIRS[@]}" systems/tests templates/game/tests

step "Selene (lint)"
need selene && run selene "${LUAU_DIRS[@]}"

step "luau-analyze (pure modules)"
need luau-analyze && run luau-analyze systems/src/Shared/*.luau

step "Lune (systems tests)"
need lune && run lune run systems/tests/run.luau

step "Template end-to-end (scaffold + tests + rojo build)"
TMP="$(mktemp -d)"
run scripts/new-game.sh "Vault Smoke Test" --dest "$TMP"
if need lune; then run lune run "$TMP/vault-smoke-test/tests/run.luau"; fi
if need rojo; then
  run rojo build systems/default.project.json -o "$TMP/vault.rbxm"
  run rojo build "$TMP/vault-smoke-test/default.project.json" -o "$TMP/smoke.rbxl"
fi
rm -rf "$TMP"

step "Games"
for g in games/*/; do
  [[ -f "$g/default.project.json" ]] || continue
  if need lune && [[ -f "$g/tests/run.luau" ]]; then run lune run "${g%/}/tests/run.luau"; fi
  if need rojo; then run rojo build "$g/default.project.json" -o "$(mktemp -d)/game.rbxl"; fi
done

step "Blender pipeline"
if [[ "${SKIP_BLENDER:-0}" == "1" ]]; then
  echo "skipped (SKIP_BLENDER=1; CI runs it in its own job)"
elif python3 -c "import bpy" >/dev/null 2>&1; then
  run python3 blender/tests/test_pipeline.py
elif [[ -n "${BPY_PYTHON:-}" ]]; then
  run "$BPY_PYTHON" blender/tests/test_pipeline.py
elif have blender; then
  run blender -b -P blender/tests/test_pipeline.py
else
  SKIPPED+=("bpy/blender")
  [[ "${STRICT:-0}" == "1" ]] && FAIL=1
fi

echo
if [[ ${#SKIPPED[@]} -gt 0 ]]; then echo "SKIPPED (tool missing): ${SKIPPED[*]}"; fi
if [[ $FAIL -ne 0 ]]; then echo "VALIDATION FAILED"; exit 1; fi
echo "VALIDATION PASSED"
