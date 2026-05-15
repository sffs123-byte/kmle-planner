#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <CLOUDFLARED_TUNNEL_TOKEN>" >&2
  exit 2
fi
TOKEN="$1"
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found" >&2
  exit 1
fi
sudo cloudflared service install "$TOKEN"
cloudflared service status || true
