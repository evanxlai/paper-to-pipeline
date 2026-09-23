#!/usr/bin/env python3
"""Drive the whole gem5 verify gate with no agent and no LLM.

The gem5 twin of loop/tests/cbp2025_gate_smoke.py, and it has the same
purpose. Almost everything that can go wrong in stage 3 is not the agent: a
resource token that lands a task on a node without the tree, a metric name
that does not match the recorded baseline, a workload list that resolves to
nothing, a knob that leaks into the guest. All of that is reachable without
an agent, by running the real `plan_runner.run_test_plan` and the real
`gate.check_gate` against an UNPORTED copy of the checkout.

The copy is the smoke's own tree, ~/gem5_smoke, next to the pristine
checkout. It is deleted and copied again from ~/gem5 at every run, and
nothing else uses it. The smoke never touches ~/gem5_port. A lead re-runs
the smoke after a host change while stage 3 may be running, or has just
finished, and ~/gem5_port holds that run's port: the live tree of a running
agent, or the resume point of P2P_GEM5_PORT_FRESH=0.

The gate itself runs through `hosts/gem5/adapter.gate_attempt`, the code
behind stage 3's run_gate with the tree as a parameter. So the smoke also
covers what run_gate does before it measures: it installs the run dir
again, and it refuses a recorded baseline that no longer matches the
pristine revision or the workload files.

There is no gem5 test plan yet (stage 2 has not run on this host), so this
script writes a small one itself and checks it against
plan/test_plan.schema.json before it touches the cluster:

  correctness   one feature_off_baseline entry: run_workload.py on one smoke
                workload, compared at rel_tol 0 against the recorded
                baseline's /per_trace/<workload>
  smoke         the smoke list, feature on
  performance   one entry on the smoke list: cond_mpki must decrease

The expected verdict is a specific failure, and that is the point:

  G1 build        passes   the pristine copy compiles
  G2 feature-off  passes   an unported tree IS the baseline
  G4 smoke        passes   the smoke workloads complete with the knob set
  G5 performance  fails    there is no feature, so nothing improves

Anything else is a defect in the harness rather than in a port. A G1, G2 or
G4 failure here is always the harness.

The G5 failure has to be exact, too. The performance entry measures the
smoke list with the knob on and with it off. On an unported tree the two
must be bit-identical, so the relative improvement must be exactly 0.0. A
non-zero value means the knob reached the guest (its environment moves the
guest's stack) or gem5 is not deterministic run to run. Either one breaks
every G2 a real port will face.

    chia job submit -- python "$(pwd)/loop/tests/gem5_gate_smoke.py"

Before it: a recorded baseline that holds the smoke workload.

    chia job submit -- python loop/adopt_a_paper_loop.py --stage baseline --host gem5

It is deliberately not named test_*.py: pytest must not collect it, because
it needs a live cluster and several minutes of simulation.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import shlex
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "loop")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import constants as C
import helpers
from hosts.gem5 import adapter as gem5_adapter


def smoke_root() -> str:
    """The smoke's own tree: gem5_smoke, next to the pristine checkout
    (~/gem5_smoke by default). Derived here, not a constant, because
    nothing but this script may use it."""
    parent = posixpath.dirname(posixpath.normpath(C.GEM5_ROOT)) or "/"
    return posixpath.join(parent, "gem5_smoke")


def smoke_root_refusal(root: str) -> str:
    """Why `root` must not be the smoke's tree, or "". The smoke deletes
    its tree at every run, and each P2P_GEM5_* path can be overridden."""
    mine = posixpath.normpath(root)
    for other, what in ((C.GEM5_ROOT, "the pristine checkout"),
                        (C.GEM5_PORT_ROOT, "stage 3's port tree"),
                        (C.GEM5_DSE_ROOT, "stage 4's search tree"),
                        (C.GEM5_RUN_DIR, "the run dir")):
        theirs = posixpath.normpath(other)
        if mine == theirs or mine.startswith(theirs + "/") or theirs.startswith(mine + "/"):
            return f"{root} is, or overlaps, {what} ({other})"
    return ""


def _pointer_token(name: str) -> str:
    """RFC 6901 escaping for one path segment."""
    return name.replace("~", "~0").replace("/", "~1")


def _rel(path: Path) -> str:
    path = Path(path).resolve()
    return str(path.relative_to(C.REPO_ROOT)) if path.is_relative_to(C.REPO_ROOT) else str(path)


def synthesize_test_plan(*, feature_name: str, host_revision: str, workload: str,
                         smoke_list: Path, perf_list: Path, timeout_s: int) -> dict:
    """The smallest test plan that exercises G1, G2, G4 and G5 on gem5."""
    performance = [{
        "id": "perf_cond_mpki",
        "description": "Conditional-branch MPKI with the knob on against the same "
                       "workloads with it off. On an unported tree nothing moves.",
        "metric": "cond_mpki",
        "direction": "decrease",
        "trace_list": _rel(perf_list),
        "run": {"mode": "host_adapter"},
        "baseline": {"source": "measure_feature_off"},
        "timeout_seconds": timeout_s,
        "block_threshold": {"min_relative_improvement": 0.0, "no_regression": []},
        "warn_threshold": {"target_relative_improvement": 0.0,
                           "claim_source": "gate smoke on an unported tree; no claim"},
    }]
    return {
        "feature_name": feature_name,
        "host": "gem5",
        "host_revision": host_revision,
        "metric_keys": list(gem5_adapter.METRIC_KEYS),
        "baseline_rel_tol": 0,
        "smoke": {"trace_list": _rel(smoke_list), "run": {"mode": "host_adapter"},
                  "timeout_seconds": timeout_s},
        "correctness": [{
            "id": "feature_off_baseline",
            "kind": "feature_off_baseline",
            "description": f"With the enable knob off, {workload} equals the recorded "
                           f"baseline exactly.",
            "command": f"python3 {C.GEM5_RUN_DIR}/run_workload.py {shlex.quote(workload)}",
            "feature_state": "off",
            "timeout_seconds": timeout_s,
            "pass_condition": {
                "kind": "metrics_equal_baseline",
                "baseline_pointer": f"/per_trace/{_pointer_token(workload)}",
                "rel_tol": 0,
            },
        }],
        "performance": performance,
        # A schema field for exactly this kind of note, and not one the gate reads.
        "notes": "Written by loop/tests/gem5_gate_smoke.py for an unported tree.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", default="iso-64KiB",
                    help="which recorded baseline file to compare against")
    ap.add_argument("--smoke-list", default=str(C.GEM5_SMOKE_LIST))
    ap.add_argument("--perf-list", default=None,
                    help="the performance entry's list; default: the smoke list")
    ap.add_argument("--workload", default=None,
                    help="the G2 workload; default: the smoke list's first line")
    ap.add_argument("--feature-name", default=C.FEATURE_NAME)
    ap.add_argument("--knob", default="sr_enable",
                    help="feature_enable.name; nothing on an unported tree reads it")
    ap.add_argument("--binding", default="runtime_env",
                    choices=("runtime_env", "compile_time_define"),
                    help="compile_time_define costs a full recompile per state")
    ap.add_argument("--timeout", type=int, default=C.GEM5_BASH_TOOL_TIMEOUT_S,
                    help="per-entry limit in seconds (default: the agents' shell cap). "
                         "The executor raises a run_traces limit below "
                         "GEM5_RUN_TIMEOUT_S to that floor")
    ap.add_argument("--skip-performance", action="store_true",
                    help="drop the performance entry, which is half the wall clock")
    ap.add_argument("--dry-run", action="store_true",
                    help="write and schema-check the test plan, then stop before Ray")
    args = ap.parse_args()

    smoke_list = Path(args.smoke_list)
    perf_list = Path(args.perf_list or args.smoke_list)
    for path in (smoke_list, perf_list):
        if not path.is_file():
            raise SystemExit(f"{path} does not exist")
    smoke = helpers.load_trace_list(smoke_list)
    workload = args.workload or (smoke[0] if smoke else None)
    if not workload:
        raise SystemExit(f"{smoke_list} names no workloads")

    baseline = helpers.load_baseline("gem5", args.budget)
    if baseline is None:
        raise SystemExit(
            f"no recorded baseline at {helpers.baseline_path('gem5', args.budget)}. "
            f"Run --stage baseline --host gem5 first."
        )
    if workload not in (baseline.get("per_trace") or {}):
        raise SystemExit(
            f"the recorded baseline has no per_trace entry for {workload!r} (it has "
            f"{sorted(baseline.get('per_trace') or {})}). Record it with --stage baseline "
            f"--host gem5 --baseline-list <a list naming {workload}>."
        )

    # Schema first, on the head: a plan the schema rejects is a bug in this
    # script, and finding it must not cost a cluster run. The schema wants at
    # least one performance entry, so --skip-performance drops it after the
    # check, as the cbp2025 smoke does.
    test_plan = synthesize_test_plan(
        feature_name=args.feature_name, host_revision=baseline.get("host_revision", ""),
        workload=workload, smoke_list=smoke_list, perf_list=perf_list,
        timeout_s=args.timeout,
    )
    _, errors = helpers.validate_json(json.dumps(test_plan), C.TEST_PLAN_SCHEMA_PATH,
                                      require_jsonschema=True)
    if errors:
        print("[gem5-gate-smoke] the synthesized test plan fails the schema:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"[gem5-gate-smoke] test plan is schema-valid against "
          f"{_rel(C.TEST_PLAN_SCHEMA_PATH)}")
    if args.skip_performance:
        test_plan = {**test_plan, "performance": []}
    port_plan = {"feature_enable": {"name": args.knob, "binding": args.binding}}
    root = smoke_root()
    refusal = smoke_root_refusal(root)
    if refusal:
        raise SystemExit(f"[gem5-gate-smoke] refusing to use {root} as the smoke tree: "
                         f"{refusal}")
    if args.dry_run:
        print(json.dumps(test_plan, indent=2))
        print(f"[gem5-gate-smoke] the smoke tree would be {root}")
        print("[gem5-gate-smoke] --dry-run: stopping before the cluster")
        return 0

    import ray

    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)
    dump = helpers.Dumper()
    dump.json("gem5_gate_smoke_test_plan.json", test_plan)

    revision = gem5_adapter.checkout_revision()
    print(f"[gem5-gate-smoke] {C.GEM5_ROOT} is at {revision}; the baseline was recorded "
          f"at {baseline.get('host_revision')}")
    # Before the copy and the build: a stale baseline would fail G2 for a
    # reason that has nothing to do with the harness. gate_attempt checks
    # it again, the way stage 3 does.
    gem5_adapter.check_baseline_current(baseline, test_plan, revision=revision)
    print(f"[gem5-gate-smoke] the baseline matches {C.GEM5_ROOT} and the workload files "
          f"of {sorted(gem5_adapter.baseline_workloads(test_plan, baseline))}")
    print(f"[gem5-gate-smoke] restore {C.GEM5_ROOT}: "
          f"{json.dumps(gem5_adapter.restore_host_checkout())}")
    print(f"[gem5-gate-smoke] materializing an UNPORTED {root} from {C.GEM5_ROOT} "
          f"(the smoke's own tree; {C.GEM5_PORT_ROOT} is not touched)")
    copied = gem5_adapter.copy_tree(C.GEM5_ROOT, root, fresh=True)
    print(f"[gem5-gate-smoke] {json.dumps(copied)}")
    if not copied.get("ok"):
        return 1

    # Only for the printout. gate_attempt builds its own executor.
    shown = gem5_adapter.Gem5Executor(root, port_plan["feature_enable"])
    print(f"[gem5-gate-smoke] rebuild_per_state={shown.rebuild_per_state} "
          f"enable_env(on)={gem5_adapter.enable_env(shown.feature_enable, True)}"
          + (f" define_env(on)={gem5_adapter.define_env(shown.feature_enable, True)}"
             if shown.rebuild_per_state else ""))

    t0 = time.time()
    attempt = gem5_adapter.gate_attempt(baseline, port_plan, test_plan, work_dir=root)
    results, verdict = attempt.results, attempt.verdict
    wall = time.time() - t0
    print(f"[gem5-gate-smoke] install run dir: "
          f"{json.dumps({k: v for k, v in attempt.install.items() if k != 'files'})}")

    print(f"\n[gem5-gate-smoke] build_ok={results.build_ok}")
    if not results.build_ok:
        print(results.build_log_tail[-3000:])
    print(f"[gem5-gate-smoke] feature_off_metrics={json.dumps(results.feature_off_metrics)}")
    print(f"[gem5-gate-smoke] baseline /per_trace/{workload}="
          f"{json.dumps(baseline['per_trace'][workload])}")
    print("[gem5-gate-smoke] correctness")
    for r in results.correctness:
        print(f"  {'PASS' if r.passed else 'FAIL'}  {r.id:22s} ({r.kind})"
              f"  {r.reason.splitlines()[0][:150] if r.reason else ''}")
    print(f"[gem5-gate-smoke] smoke_ok={results.smoke_ok} failures={results.smoke_failures}")
    print("[gem5-gate-smoke] performance")
    for r in results.performance:
        print(f"  {'PASS' if r.block_passed else 'FAIL'}  {r.id:22s} {r.metric} "
              f"base={r.baseline!r} measured={r.measured!r} rel={r.relative_improvement!r} "
              f"n={r.n_traces} failed={r.failed_traces}")
        if r.reason:
            print(f"      {r.reason[:300]}")

    print(f"\n[gem5-gate-smoke] verdict passed={verdict.passed} in {wall:.0f}s")
    for reason in verdict.reasons:
        print(f"  - {reason.splitlines()[0][:200]}")
    for warning in verdict.warnings:
        print(f"  ~ {warning.splitlines()[0][:200]}")

    off_baseline = [r for r in results.correctness if r.kind == "feature_off_baseline"]
    reasons_by_gate = {g: [x for x in verdict.reasons if x.startswith(g)]
                       for g in ("G1", "G2", "G3", "G4", "G5")}
    checks = [
        ("the baseline was recorded at the checkout's revision",
         baseline.get("host_revision") == revision),
        ("G1 the pristine copy builds", results.build_ok),
        ("G2 an unported tree equals the recorded baseline",
         bool(off_baseline) and all(r.passed for r in off_baseline)),
        ("G4 the smoke workloads complete with the knob on", results.smoke_ok),
        ("no G1, G2, G3 or G4 reason in the verdict",
         not any(reasons_by_gate[g] for g in ("G1", "G2", "G3", "G4"))),
    ]
    if not args.skip_performance:
        perf = results.performance
        checks += [
            ("G5 fails, because there is no feature",
             bool(perf) and not verdict.passed and bool(reasons_by_gate["G5"])),
            # The exact zero is the determinism and knob-isolation check.
            ("knob on and knob off are bit-identical on an unported tree",
             bool(perf) and all(r.relative_improvement == 0.0 and not r.failed_traces
                                for r in perf)),
        ]
    print("\n[gem5-gate-smoke] harness checks")
    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    ok = all(ok for _, ok in checks)
    print(f"[gem5-gate-smoke] verdict: {'PASS' if ok else 'FAIL'} (the expected result is "
          f"G1, G2 and G4 passing and G5 failing)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
