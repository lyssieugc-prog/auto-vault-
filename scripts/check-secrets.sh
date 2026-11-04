#!/usr/bin/env bash
# Fails if tracked or staged files look like they contain credentials.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PATTERNS='(_\|WARNING:-DO-NOT-SHARE-THIS|ROBLOSECURITY=|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|figd_[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})'

FILES="$( (git ls-files; git diff --cached --name-only) 2>/dev/null | sort -u | grep -vE '^scripts/check-secrets\.sh$' || true)"
[[ -z "$FILES" ]] && { echo "no tracked files"; exit 0; }

HITS="$(echo "$FILES" | while read -r f; do
  [[ -f "$f" ]] || continue
  # skip LFS/binary files
  if file -b --mime "$f" 2>/dev/null | grep -q 'charset=binary'; then continue; fi
  grep -HnE "$PATTERNS" "$f" 2>/dev/null || true
done)"

BAD_NAMES="$(echo "$FILES" | grep -E '(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa|\.mcp\.json|cookie.*\.txt)$' | grep -v '\.example' || true)"

if [[ -n "$HITS" || -n "$BAD_NAMES" ]]; then
  echo "Possible secrets found — do not commit:"
  [[ -n "$HITS" ]] && echo "$HITS" | sed -E 's/(:[0-9]+:).*/\1 <redacted>/'
  [[ -n "$BAD_NAMES" ]] && echo "$BAD_NAMES"
  exit 1
fi
echo "secrets check clean"
