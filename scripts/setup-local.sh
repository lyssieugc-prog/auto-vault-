#!/usr/bin/env bash
# One-time setup on the OWNER'S computer (not the cloud). Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git lfs install
git config core.hooksPath .githooks
echo "git hooks: .githooks (pre-commit secret scan)"

if command -v rokit >/dev/null 2>&1; then
  rokit install
else
  echo "Install rokit (https://github.com/rojo-rbx/rokit), then re-run to get rojo/stylua/selene/lune."
fi

if [[ ! -f .mcp.json ]]; then
  cp docs/integrations/mcp.local.example.json .mcp.json
  echo "Created .mcp.json from the example (gitignored). Edit paths if needed."
fi

echo
echo "Remaining manual steps: docs/integrations/local-setup.md §2 (Blender addon, Studio MCP, Figma)."
echo "Then start Claude Code here and say: run the integration audit"
