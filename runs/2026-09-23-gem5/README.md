# gem5 host, 2026-09-23: first bring-up on the real cluster

These files back the first claims about the gem5 host. Every run went
through `chia job submit` on the project's CHIA cluster. The gem5 node was
one c2d-standard-32 (32 vCPU, 128 GB) that advertises `{"gem5_host": 30}`.
gem5 is v25.1.0.0 at commit `7a2b0e413d06c5ce7097104abef3b1d9eaabca91`,
built for ARM as `gem5.opt`.

Nothing here is a port. Every run is the pristine TAGE-SC-L 64 KB predictor
on an unported tree. These runs show that the host plumbing works: the
build, the run scripts, the workloads, the baseline and the gate.

## The runs

| File | Job | What it shows |
| --- | --- | --- |
| `20260923_0557_gem5_pristine_build.json` | `p2p_gem5_build_pristine_0923` | The pristine build through CHIA's own `Gem5Node.build_gem5`. It took 670 s on 32 vCPUs. |
| `20260923_1012_gem5_cluster_smoke_o3.txt` | `p2p_gem5_cluster_smoke_o3_0923a` | All 28 workloads ran on the O3 CPU and passed their self-checks. The fan-out took 398 s. |
| `20260923_104036_gem5_baseline.json` | `p2p_gem5_baseline_all_0923b` | The first baseline over all 28 workloads. |
| `20260923_104036_gem5_baseline_*.json`, `..._baseline_summary.json` | the same job | The restore, install and build records of that baseline run, and the driver's summary. |
| `20260923_1048_gem5_gate_smoke.txt` | `p2p_gem5_gate_smoke_0923b` | The real gate on an unported copy. G1, G2 and G4 pass. G5 fails, as it must with no feature. |
| `20260923_114937_gem5_baseline*.json`, `..._baseline_summary.json` | `p2p_gem5_baseline_all_0923c` | The same baseline, recorded again after the review fixes changed the run scripts' fingerprints. This one is `hosts/gem5/baselines/iso-64KiB.json` now. |
| `20260923_1159_gem5_gate_smoke.txt`, `20260923_115811_gem5_gate_smoke_test_plan.json` | `p2p_gem5_gate_smoke_0923c` | The gate on the final code, in its own tree `~/gem5_smoke`. The stale-baseline check passed, the run dir install was a no-op, and the verdict is the expected one again. |

## What the gate smoke proves

- G2 compares a feature-off run through `run_workload.py` in a shell with
  the baseline, which the fan-out recorded. The two agree to the last bit:
  `cond_mpki` is 13.841743082714196 on both paths for `gapbs_bfs_s`.
- With the knob on and with the knob off, an unported tree gives
  bit-identical numbers. So the knob does not reach the guest.
- The baseline job's `branch_mpki` mean over 28 workloads,
  9.690411027686881, equals the cluster smoke's mean from a separate job
  run 28 minutes earlier. gem5 on this host repeats exactly.

## One caveat about the smoke table

The cluster smoke ran before the metric fix. In that file, the `cond_mpki`
column equals the `branch_mpki` column on every row. The reason is that
gem5 v25.1's `condIncorrect` counts every committed mispredicted branch,
of every type. After the fix, `cond_mpki` counts only the conditional rows
of `branchPred.mispredicted_0`. The baseline and the gate smoke use the
fixed metric. `hosts/gem5/run/p2p_metrics.py` explains the change.

## Measured speed

- The O3 CPU ran 97,000 to 323,000 instructions per second on this node.
- A smoke workload (2 to 6 M instructions) took 14 to 31 s.
- A perf workload (34 to 65 M instructions) took 136 to 396 s alone on the
  node, and up to 521 s while a gem5 build shared it.
- A fresh copy of the tree reuses most of the copied `build/`. Each gate
  smoke, which includes that copy's first build and about 90 s of gem5
  runs, took 336 to 376 s in all.
