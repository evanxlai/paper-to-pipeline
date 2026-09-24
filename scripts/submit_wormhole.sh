#!/usr/bin/env bash
# Submit one Wormhole pipeline stage without sharing sR's feature namespace.
#
# Usage, after `chia up cluster/cluster.yaml`:
#   ./scripts/submit_wormhole.sh --stage distill --host cbp2025
#   ./scripts/submit_wormhole.sh --stage plan integrate --host cbp2025
#
# The runtime environment reaches the Ray job driver. Its constants then give
# Wormhole its own spec/plan names and CBP2025 port/DSE trees while preserving
# sR's existing paths.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORMHOLE_RUNTIME_ENV="$(python3 - "$ROOT" <<'PY'
import json
import sys

root = sys.argv[1]
print(json.dumps({"env_vars": {
    "P2P_FEATURE_NAME": "wormhole",
    "P2P_PAPER_TEXT": f"{root}/third_party/wormhole/wormhole.txt",
}}))
PY
)"

exec chia job submit --runtime-env-json "$WORMHOLE_RUNTIME_ENV" -- \
  python "$ROOT/loop/adopt_a_paper_loop.py" "$@"
