#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")"
if [[ -f .local/planner-local.env ]]; then
  set -a
  source .local/planner-local.env
  set +a
fi
exec /opt/homebrew/bin/node planner-local-server.js
