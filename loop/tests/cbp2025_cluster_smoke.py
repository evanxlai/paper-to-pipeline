#!/usr/bin/env python3
"""Does the CBP2025 host node actually work on this cluster?

No LLM, no agent, no gate: build the unmodified kit on the node that owns
the checkout, fan a trace list out over the nodes that own the traces, and
print what came back with a wall-clock time per trace. That last number is
the one that decides how long a performance list may be, and it is the one
nobody can guess -- a CBP2025 training trace is 30-100x the sample trace
the kit ships.

Run it the way the loop runs:

    chia job submit -- python loop/tests/cbp2025_cluster_smoke.py --traces 2

It is deliberately not named test_*.py: pytest must not collect it, because
it needs a live cluster.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "loop")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ray
from chia.base.ChiaFunction import get

import constants as C
import helpers
from chia_nodes.cbp2025.cbp2025_node import CBP2025Node


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", type=int, default=2,
                    help="how many lines of the list to actually run")
    ap.add_argument("--list", default=str(C.SMOKE_LIST))
    args = ap.parse_args()

    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)
    print(f"[smoke] cluster resources: "
          f"{json.dumps(ray.cluster_resources(), default=str)}")

    t0 = time.time()
    build = get(
        CBP2025Node.build.options(resources={"cbp2025_host": 1.0})
        .chia_remote(C.CBP2025_ROOT, None, C.BUILD_TIMEOUT_S)
    )
    print(f"[smoke] build ok={build.success} in {time.time() - t0:.1f}s, "
          f"binary {len(build.binary)} bytes")
    if not build.success:
        print(build.log[-4000:])
        return 1

    traces = helpers.load_trace_list(Path(args.list))[: args.traces]
    print(f"[smoke] running {len(traces)} trace(s) from {args.list}: {traces}")

    t0 = time.time()
    refs = [
        CBP2025Node.run.chia_remote(
            build.binary, f"{C.TRACE_DIR}/{t}", (), C.RUN_TIMEOUT_S
        )
        for t in traces
    ]
    results = [get(r) for r in refs]
    wall = time.time() - t0

    for r in results:
        row = (r.metrics or {}).get("50perc", {})
        print(f"[smoke]   {r.trace}: ok={r.success} rc={r.returncode} "
              f"instr={row.get('instr')} mpki={row.get('mpki')} "
              f"cycwppki={row.get('cycwppki')} ipc={row.get('ipc')}")
        if not r.success:
            print(r.log[-2000:])

    agg = get(CBP2025Node.aggregate.chia_remote(results))
    print(f"[smoke] aggregate: {json.dumps(agg, indent=2)}")
    print(f"[smoke] {len(traces)} trace(s) in {wall:.1f}s wall "
          f"({wall / max(1, len(traces)):.1f}s per trace at this fan-out)")
    return 0 if agg.get("n") == len(traces) else 1


if __name__ == "__main__":
    sys.exit(main())
