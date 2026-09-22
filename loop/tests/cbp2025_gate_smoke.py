#!/usr/bin/env python3
"""Drive the whole cbp2025 verify gate with no agent and no LLM.

Stage 3 costs an hour and a lot of tokens. Almost everything that can go
wrong in it is not the agent: a resource token that pins a task to a node
without the files, a metric name that does not match the recorded baseline,
a trace list that resolves to nothing, a shell whose output the pass
condition cannot see. All of that is reachable in ten minutes by running the
real `plan_runner.run_test_plan` and the real `gate.check_gate` against an
UNPORTED copy of the checkout.

The expected verdict is a specific failure, and that is the point:

  G1 build            passes  -- the pristine kit compiles
  G2 feature-off      passes  -- an unported tree IS the baseline
  G3 correctness      the existing_regression entries pass; every
                      spec_unit_test entry fails, because no test file exists
  G4 smoke            passes
  G5 performance      fails   -- there is no feature, so nothing improves

Anything else is a defect in the harness rather than in a port. In
particular a G1 or G2 or G4 failure here is always the harness.

A spec_unit_test that PASSES here is the harness too, and it is the worst
case of it. The first run of this script reported all seven passing,
because stage 2's planner had left a `test_sr.cc` printing "Test passed" in
the checkout while working out the compile command, and the port tree was a
copy of that checkout. The gate was then holding a port to a standard
already met by a file nobody wrote on purpose.

    chia job submit -- python "$(pwd)/loop/tests/cbp2025_gate_smoke.py"

It is deliberately not named test_*.py: pytest must not collect it, because
it needs a live cluster and several minutes of simulator.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "loop")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ray

import constants as C
import gate
import helpers
import plan_runner
from hosts.cbp2025 import adapter as cbp2025_adapter


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="cbp2025")
    ap.add_argument("--budget", default="iso-192KiB")
    ap.add_argument("--skip-performance", action="store_true",
                    help="drop the performance entries, which are most of the wall clock")
    args = ap.parse_args()

    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)

    spec_path = Path(C.SPEC_OUT_PATH)
    spec = json.loads(spec_path.read_text())
    port_plan, test_plan = (
        json.loads(p.read_text())
        for p in helpers.plan_paths(args.host, spec.get("feature_name"))
    )
    baseline = helpers.load_baseline(args.host, args.budget)
    if baseline is None:
        raise SystemExit(f"no recorded baseline for {args.host}/{args.budget}")

    if args.skip_performance:
        test_plan = {**test_plan, "performance": []}

    print(f"[gate-smoke] restoring {C.CBP2025_ROOT}: "
          f"{json.dumps(cbp2025_adapter.restore_host_checkout())}")
    print(f"[gate-smoke] materializing {C.CBP2025_PORT_ROOT} from {C.CBP2025_ROOT}")
    print(f"[gate-smoke] {json.dumps(cbp2025_adapter.clean_port_tree())}")

    executor = cbp2025_adapter.CBP2025Executor(
        work_dir=C.CBP2025_PORT_ROOT,
        feature_enable=port_plan.get("feature_enable") or {},
        metric_keys=test_plan.get("metric_keys") or cbp2025_adapter.METRIC_KEYS,
    )
    print(f"[gate-smoke] rebuild_per_state={executor.rebuild_per_state} "
          f"enable_env(on)={cbp2025_adapter.enable_env(executor.feature_enable, True)}")

    t0 = time.time()
    results = plan_runner.run_test_plan(executor, test_plan, port_plan, baseline)
    verdict = gate.check_gate(results)
    wall = time.time() - t0

    print(f"\n[gate-smoke] build_ok={results.build_ok}")
    if not results.build_ok:
        print(results.build_log_tail[-3000:])
    print(f"[gate-smoke] feature_off_metrics={json.dumps(results.feature_off_metrics)}")
    print("[gate-smoke] correctness")
    for r in results.correctness:
        print(f"  {'PASS' if r.passed else 'FAIL'}  {r.id:14s} ({r.kind})"
              f"  {r.reason.splitlines()[0][:150] if r.reason else ''}")
    print(f"[gate-smoke] smoke_ok={results.smoke_ok} failures={results.smoke_failures}")
    print("[gate-smoke] performance")
    for r in results.performance:
        print(f"  {'PASS' if r.block_passed else 'FAIL'}  {r.id:14s} {r.metric} "
              f"base={r.baseline} measured={r.measured} rel={r.relative_improvement} "
              f"n={r.n_traces} failed={r.failed_traces}")
        if r.reason:
            print(f"      {r.reason[:300]}")

    print(f"\n[gate-smoke] verdict passed={verdict.passed} in {wall:.0f}s")
    for reason in verdict.reasons:
        print(f"  - {reason.splitlines()[0][:200]}")
    for warning in verdict.warnings:
        print(f"  ~ {warning.splitlines()[0][:200]}")

    # What the harness itself must get right, independent of any port.
    off_baseline = [r for r in results.correctness if r.kind == "feature_off_baseline"]
    regressions = [r for r in results.correctness if r.kind == "existing_regression"]
    unit_tests = [r for r in results.correctness if r.kind == "spec_unit_test"]
    checks = [
        ("G1 the pristine copy builds", results.build_ok),
        ("G2 an unported tree equals the recorded baseline",
         bool(off_baseline) and all(r.passed for r in off_baseline)),
        ("G3 the host's own regressions pass",
         bool(regressions) and all(r.passed for r in regressions)),
        # The direction is deliberate. These tests do not exist until the
        # integration agent writes them, so one passing here means something
        # already satisfies it, and the only things that can are leftovers.
        ("G3 no spec unit test passes on an unported tree",
         not any(r.passed for r in unit_tests)),
        ("G4 the smoke traces complete", results.smoke_ok),
        ("the performance entries produced a number, or said why",
         args.skip_performance or all(
             r.measured is not None or r.reason for r in results.performance)),
    ]
    print("\n[gate-smoke] harness checks")
    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
