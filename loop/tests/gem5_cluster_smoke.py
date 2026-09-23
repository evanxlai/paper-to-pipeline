#!/usr/bin/env python3
"""Does the gem5 host work on this cluster, and how long does each workload take?

No LLM, no agent, no gate. Install the run dir on the gem5 node, build the
pristine checkout there, run every manifest workload once with the feature
off, and print what came back. The table has the numbers nobody can guess
from the head: instructions, cycles, the three metrics, the wall time, and
the simulation speed in instructions per second on this node. That speed
decides how big a smoke workload and a perf workload may be.

Run it the way the loop runs:

    chia job submit -- python loop/tests/gem5_cluster_smoke.py

Useful variations:

    ... gem5_cluster_smoke.py --only bfs lua        # a few workloads
    ... gem5_cluster_smoke.py --list experiments/gem5-perf.list
    ... gem5_cluster_smoke.py --cpu atomic          # count instructions fast
    ... gem5_cluster_smoke.py --skip-build          # reuse the built binary

`--cpu atomic` runs the same guests on gem5's atomic CPU. It has no O3
pipeline, so it reports instructions and wall time but not the metrics. It
is the quick way to size a workload before paying for O3.

The build uses the adapter's own path (hosts/gem5/adapter.py build_tree),
the one the baseline and every gate build use, so a later build of the same
tree finds nothing to do. See constants.GEM5_SCONS_ARGS for why the scons
arguments are flags only.

cond_mpki and branch_mpki must differ. cond_mpki counts committed
conditional mispredictions only, and branch_mpki counts every branch type.
The first cluster run (2026-09-23) printed them equal on all 28 workloads,
because it read condIncorrect, which counts every type. The script prints
both, and flags a workload where they are still equal.

It is deliberately not named test_*.py: pytest must not collect it, because
it needs a live cluster and minutes of simulation.
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
import helpers
from hosts.gem5 import adapter as gem5_adapter


def _fmt(value, spec: str) -> str:
    return "-" if value is None else format(value, spec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", help="a workload list; default: every manifest workload")
    ap.add_argument("--only", nargs="+", help="run just these workloads")
    ap.add_argument("--cpu", choices=("o3", "atomic"), default="o3")
    ap.add_argument("--skip-build", action="store_true",
                    help="use the gem5 binary already in the pristine tree")
    ap.add_argument("--restore", action="store_true",
                    help="reset and clean the pristine tree first (keeps build/)")
    ap.add_argument("--timeout", type=int, default=C.GEM5_RUN_TIMEOUT_S,
                    help="per-run limit in seconds")
    args = ap.parse_args()

    if not Path(C.GEM5_WORKLOADS_MANIFEST).is_file():
        print(f"[gem5-smoke] {C.GEM5_WORKLOADS_MANIFEST} does not exist; it names the "
              f"workloads")
        return 2
    manifest = gem5_adapter.workloads()
    if args.only:
        names = list(args.only)
    elif args.list:
        names = helpers.load_trace_list(Path(args.list))
    else:
        names = sorted(manifest)
    unknown = [n for n in names if n not in manifest]
    if unknown or not names:
        print(f"[gem5-smoke] unknown workloads {unknown}; the manifest has "
              f"{sorted(manifest)}")
        return 2

    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)
    print(f"[gem5-smoke] cluster resources: "
          f"{json.dumps(ray.cluster_resources(), default=str)}")
    print(f"[gem5-smoke] scons args {C.GEM5_SCONS_ARGS!r}")
    print(f"[gem5-smoke]   command line {gem5_adapter.split_scons_args()[0]!r}")
    print(f"[gem5-smoke]   environment  {gem5_adapter.build_env()}")

    if args.restore:
        print(f"[gem5-smoke] restore {C.GEM5_ROOT}: "
              f"{json.dumps(gem5_adapter.restore_host_checkout())}")
    installed = gem5_adapter.install_run_dir_on_cluster()
    print(f"[gem5-smoke] run dir {installed['dest']}: installed={installed['installed']} "
          f"sha256={installed['sha256'][:12]} bytes={installed['bytes']} "
          f"files={len(installed.get('files', []))}"
          + (f" because {installed.get('why')}" if installed.get("installed") else ""))
    print(f"[gem5-smoke] revision {gem5_adapter.checkout_revision()} "
          f"(mirror {gem5_adapter.mirror_revision()})")

    if args.skip_build:
        binary = gem5_adapter.binary_path(C.GEM5_ROOT)
        print(f"[gem5-smoke] skipping the build; using {binary}")
    else:
        t0 = time.time()
        build = gem5_adapter.build_tree(C.GEM5_ROOT)
        print(f"[gem5-smoke] build ok={build.get('ok')} in {time.time() - t0:.0f}s "
              f"(scons {build.get('duration_s')}s): {build.get('binary')}")
        if not build.get("ok"):
            print((build.get("log") or "")[-4000:])
            return 1
        binary = build["binary"]

    extra = ["--cpu", "atomic"] if args.cpu == "atomic" else []
    print(f"[gem5-smoke] running {len(names)} workload(s) on the {args.cpu} CPU: {names}")
    t0 = time.time()
    records = gem5_adapter.run_workloads(
        binary, names, env={}, timeout_s=args.timeout, label=f"smoke-{args.cpu}",
        extra_config_args=extra, require_metrics=(args.cpu == "o3"),
    )
    wall = time.time() - t0

    width = max([len("workload")] + [len(r["name"]) for r in records])
    header = (f"{'workload':<{width}} {'ok':<4} {'insts':>12} {'cycles':>12} "
              f"{'cond_mpki':>10} {'branch_mpki':>11} {'ipc':>7} {'wall_s':>8} "
              f"{'insts/s':>9}")
    print("\n" + header + "\n" + "-" * len(header))
    for r in records:
        m = r["metrics"]
        rate = (r["sim_insts"] / r["wall_s"]) if r["sim_insts"] and r["wall_s"] else None
        print(f"{r['name']:<{width}} {'yes' if r['ok'] else 'NO':<4} "
              f"{_fmt(r['sim_insts'], ',d'):>12} {_fmt(r['num_cycles'], ',d'):>12} "
              f"{_fmt(m.get('cond_mpki'), '.4f'):>10} {_fmt(m.get('branch_mpki'), '.4f'):>11} "
              f"{_fmt(m.get('ipc'), '.4f'):>7} {_fmt(r['wall_s'], '.1f'):>8} "
              f"{_fmt(rate, ',.0f'):>9}")
    for r in records:
        if not r["ok"]:
            print(f"\n[gem5-smoke] {r['name']} FAILED: {r['reason']}")
            print(f"  outdir {r['outdir']}")
            if r.get("stderr_tail"):
                print("  stderr tail:\n" + r["stderr_tail"][-1500:])
            if r.get("stdout_tail"):
                print("  stdout tail:\n" + r["stdout_tail"][-800:])

    good = [r for r in records if r["ok"]]
    if good and args.cpu == "o3":
        agg = gem5_adapter.p2p_metrics.aggregate([r["metrics"] for r in good])
        print(f"\n[gem5-smoke] aggregate over {len(good)}: {json.dumps(agg)}")
        # Equal values mean cond_mpki came from a count of every branch type
        # again. A workload with no mispredicted indirect, return or
        # unconditional branch could be equal honestly, which is rare.
        same = [r["name"] for r in good
                if r["metrics"].get("cond_mpki") == r["metrics"].get("branch_mpki")]
        print(f"[gem5-smoke] cond_mpki below branch_mpki on {len(good) - len(same)} of "
              f"{len(good)}" + (f"; EQUAL on {same}" if same else ""))
    print(f"[gem5-smoke] {len(good)} of {len(records)} ok, {wall:.0f}s wall for the "
          f"whole fan-out")
    print(f"[gem5-smoke] verdict: {'PASS' if len(good) == len(records) else 'FAIL'}")
    return 0 if len(good) == len(records) else 1


if __name__ == "__main__":
    sys.exit(main())
