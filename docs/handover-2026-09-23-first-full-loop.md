# Handover: the first full run from plan to DSE, 2026-09-22/23

The session that wrote this, on 2026-09-23, refined the sR spec by hand and
added host knobs and DSE constraints. It then ran plan, integrate and dse on
the real cluster at `iso-192KiB`. If you are picking the work up, start here.

## Where things stand

The loop ran end to end on the real cluster, and every stage did its job.
The sR port passed the gate for the first time in this repository, with
a small real gain at the paper's defaults. Stage 4 searched for real, with
host knobs and storage accounting working. Its best result is not about sR,
though: it came from doubling TAGE-SC-L's tables. When you submit stage 4
the way the runbook says, it cannot reach its LLM. That needs a code fix
before the next DSE run.

## What changed in this session

Three commits on `main`. The first two are pushed. The third is **local only**.

| commit | what |
| --- | --- |
| `d189393` | The sR spec (`spec/sr.paper_only.json`), refined by hand from the paper. Twelve knobs instead of two: bank count, WT and UT sizes, WT and UT counter widths, digest width, ROB tag width, decay interval, the x2.5 multiplier, the usefulness threshold. One `size_formula` per structure. Several fixes against the paper's figures. Open questions U1 to U9 record the readings the paper does not settle. |
| `cfd7ee9` | Stage 4 runs under constraints (`loop/constraints.py`), and the plan exposes the host's own sizing defines as `host_knobs` with `host_storage` formulas. Details below. |
| `db4fa2d` | **Not pushed.** The planner prompt and schema now ask for host knob ranges on both sides of the default. Then a generous allowance can grow the host too. |

### How the new pieces fit

- **Constraints.** A constraint is `{metric, comparison, allowance}`. Storage is the only one in use, but the mechanism is general. Static metrics are computed from the header before the build, and storage is one of them. Measured metrics are read from the screening results, so an IPC floor needs no new code. `dse.constraint_set` builds the set. `constraints.STATIC_METRICS` is where a new pre-build metric goes.
- **Storage accounting.** Each candidate's storage is recomputed from its own header values: the spec's `state[].size_formula` for sR, plus the plan's `host_storage.terms` for the host. A candidate over the allowance is not built. Its score is below every feasible candidate, and higher the closer it comes to fitting.
- **Host knobs.** The planner lists the host's sizing defines as `HOST_*` macros in the same `sr_params.h`, always at the clean tree's values. Stage 2 checks each one against the real file. It also measures the host's own storage (`adapter.measure_host_storage`, 524,615 bits) and requires the plan's formulas to reproduce it.
- **Preflight.** Before searching, stage 4 builds every knob at a second value. A knob that costs storage but leaves the binary unchanged stops the stage. `P2P_DSE_PREFLIGHT=0` skips it.
- The rule behind all this is in `docs/stages.md`. Only stage 4 applies constraints. Earlier stages can record costs, which is accounting. They never choose values.

## The run

All at `--budget iso-192KiB`, from the plan stage on. The baseline was already
recorded.

| stage | job | `out/` prefix | result | time |
| --- | --- | --- | --- | --- |
| plan | `raysubmit_4Weuqzkjvhg3FVKb` | `20260922_220840` | Accepted on turn 0. 19 host knobs. The storage terms sum to 524,615 exactly. | 15 min |
| integrate | `raysubmit_dRytp7niusan19X6` | `20260922_222452` | **Gate passed** on attempt 3, with one plan revision. | 56 min |
| dse, try 1 | `raysubmit_AFDiGJfqqe8kmGJ7` | `20260922_232234` | Preflight clean. Every LLM call failed, so only the defaults were scored. | 23 min |
| dse, try 2 | `raysubmit_DFQPteLmHh7vCXH8` | none | Died at `ray.init`: runtime-env conflict. | seconds |
| dse, try 3 | `raysubmit_QjWjCUuknxuk8Grb` | `20260922_234721` | Worked. 3 iterations, 4 screening traces. | 48 min |

The evolver's candidate programs and logs from try 3 are saved in
`out/dse/cbp2025/20260922_234721_adaevolve/`. The originals were in Ray's
temporary session directory.

### Stage 3, attempt by attempt

1. **G1 failed.** The first turn wrote most of the port, then stopped on compile errors: `cond_predictor_impl` was not visible from `cbp2016_tage_sc_l.h`, and two fields were missing from `cbp_hist_t`. The debug turn proposed a plan revision that only corrects hook points. The code guard accepted it. Nothing frozen changed.
2. **G1, G2 and G4 passed. G3 and G5 failed.** G2 passing means all 19 host-knob macros at their defaults leave the host bit-identical to the baseline. G3 failed because the unit-test file did not exist yet. G5 failed badly: CycWPPKI went from 388.07 to 656.65, 69% worse. The cause was the host re-running sR's prediction at update time with live register values, which overwrote the saved prediction-time state.
3. **All five passed.** The agent found that bug itself and reused the checkpointed sR vote at update. With sR at the paper's defaults, CycWPPKI on `perf-4` went from 388.07 to 386.73, a 0.35% gain. That is below the plan's assumed 0.5%, which is recorded as a warning. It does not block.

### Stage 4, candidate by candidate

The preflight passed: two builds of the same header were byte-identical, and
all 31 knobs (12 sR, 19 host) changed the binary.

| candidate | what changed | MPKI | CycWPPKI | storage (bits) |
| --- | --- | --- | --- | --- |
| defaults | nothing | 4.977 | 386.73 | 578,478 |
| iteration 1 | sR grown (10 banks, WT and UT doubled, decay 512) **and** host shrunk (`NBANKHIGH` 20→18, `LOGSNB` 9→8, `LOGTNB` 10→8) | 4.985 | 388.11 | 611,967 |
| iteration 2 | not kept in the checkpoints | 4.985 | 387.45 | 633,774 |
| **iteration 3, best** | host only: `LOGG`, `LOGB` and six SC table sizes each +1 (every table doubled). sR untouched. | **4.944** | **385.89** | 1,079,982 |

## What the results mean, and what they do not

- **They show the machinery works.** Host knobs are exposed, wired and live. The storage figures are exact: the evaluator's 578,478 at the defaults is what the formulas predict. The search mutates both kinds of knob. Iteration 1 is exactly the trade the design exists for, paying for a bigger sR by shrinking the host.
- **They show sR helps at the paper's defaults on these four traces.** The gain is small: 0.35% CycWPPKI against the same port with the feature off.
- **They do not show that tuning sR helps.** The best candidate's gain comes entirely from 501,504 more bits of TAGE-SC-L. At `iso-192KiB` the recorded baseline is the kit's default host, which is 64 KiB-class (524,615 bits). So the search bought host capacity the baseline never had. The name says "iso", but this comparison is not iso-storage.
- **They do not exercise constraint rejection on the cluster.** No candidate came near the 1,572,864-bit allowance. Only unit tests exercise the rejection path.
- **They are a smoke result.** 3 iterations, each screened on 4 traces. `promote_finalists`, the 105-trace validation of winners, is still not implemented.

## Known problems, most urgent first

### 1. Stage 4 cannot reach its LLM when submitted as the runbook says

A Ray job does not inherit the submitting shell's environment. The job's
driver therefore has no `HEAD_IP`, no `P2P_GATEWAY_TOKEN` and no
`P2P_GATEWAY_URL`. This was checked with a one-line job. `loop/constants.py`
then falls back to `http://127.0.0.1:8900/v1` with an empty token. The gateway
listens only on `10.128.0.3:8900`, so every evolver LLM call fails with
"Connection error". The search then "completes" having scored only the
defaults. The 2026-09-22 `195908` DSE run, "one iteration, identical scores",
was very likely the same failure.

**Workaround used in try 3.** A private runtime-env file carrying the
variables, plus `RAY_OVERRIDE_JOB_RUNTIME_ENV=1`. The driver's own
`ray.init(runtime_env=C.RUNTIME_ENV)` sets the same keys. Ray refuses to merge
two runtime environments that name the same variable, so the override is
needed.

```bash
source export.sh
umask 077
python3 - /path/to/private/dse_env.json <<'EOF'
import os, sys, json
env = {k: os.environ[k] for k in ("HEAD_IP", "P2P_GATEWAY_TOKEN", "P2P_GATEWAY_URL",
                                  "GCP_PROJECT", "GOOGLE_CLOUD_PROJECT") if os.environ.get(k)}
env["P2P_DSE_CONFIG"] = os.path.abspath("experiments/config_adaevolve_smoke_vertex.yaml")
env["RAY_OVERRIDE_JOB_RUNTIME_ENV"] = "1"
open(sys.argv[1], "w").write(json.dumps({"env_vars": env}))
EOF
chia job submit --runtime-env /path/to/private/dse_env.json -- \
  python "$(pwd)/loop/adopt_a_paper_loop.py" --stage dse --host cbp2025 \
  --budget iso-192KiB --screening-list "$(pwd)/experiments/perf-4.list"
```

**Proper fix, not done yet.** In `loop/constants.py`:
- When `P2P_GATEWAY_TOKEN` is unset, read it from `~/.config/p2p/gateway.env`.
- When `HEAD_IP` is unset, use the driver's own node IP, since the driver runs on the head.
- If the gateway is unreachable, make stage 4 fail loudly. Today it "completes" with only the seed program scored.

Then the runbook command works as written.

**Token exposure.** Try 2's failure message printed both runtime
environments, token included, into that Ray job's record on the cluster. It is
not in any file under `out/`, which was checked. To rotate the gateway token, run
`./scripts/install_llm_gateway.sh --rotate`. A run without `--rotate` keeps the
old token. Then `source export.sh` again, so the new token reaches your shell.

### 2. The 192 KiB track does not compare like with like

Either give 192 KiB a 192 KiB host baseline, or run at `iso-64KiB`:

- **A 192 KiB host baseline.** The kit ships `cbp2016_tage_sc_l_192kb.h`. The comparison is then "sR plus a reshaped host" against "a TAGE-SC-L built for 192 KiB", which is how the paper measured sR.
- **Run at `iso-64KiB` instead.** The limit binds there: the unmodified host alone is 327 bits over 64 KiB. The search must shrink the host to pay for sR. This first needs `--stage baseline --budget iso-64KiB`, because baselines are stored per budget name.

A third option is a new track pinned at the host's own 524,615 bits, which is
a true iso comparison against this host. It is one line in
`C.BUDGET_TRACKS_BITS`.

### 3. Smaller items

- **Unpushed commit and uncommitted run output.** `db4fa2d` is local. The run left modified `plan/sr.cbp2025.{plan,tests}.json`, the new `*.rev1.json` files, and a new `plan/superseded/` directory, where the plan stage retired the old revision. These are the run's plan artifacts and belong in a commit. So do copies of the key `out/` files into `runs/`, which is the repository's convention for runs that back a claim.
- **The port's unit tests use `#define private public`.** It works. When you read `test_sr.cc`, know that it is a test hack.
- **The port reuses the checkpointed sR vote at update.** The spec says to recompute it from the checkpointed snapshot. The host re-reads its own tables at update in the same way. Tables can change between prediction and update, so the difference is small but real.
- **Unused imports.** `hosts/cbp2025/adapter.py` has two, `json` and `helpers`, and they predate this session.

## How to pick up

1. Decide on problem 2 (which budget, which baseline). It decides what the next stage 4 result means.
2. Fix problem 1 in code.
3. Commit the run's plan artifacts, copy the key `out/` files into `runs/`, and push `db4fa2d`.
4. Run stage 4 for longer. The ported tree `~/cbp2025_port` on the checkout node holds the promoted port. Unless the spec changes, you do not need to re-run plan or integrate. Stage 4 copies that tree to `~/cbp2025_dse` each time. Use more iterations and more screening traces, and report both numbers with any result.

When this was written, the cluster was still up and idle. Idle workers cost
credit. `chia down cluster/cluster.yaml` stops them.

## Where to look

| what | where |
| --- | --- |
| the stage contracts, including the constraints rule | `docs/stages.md` |
| constraint set, formulas, header parsing, preflight helpers | `loop/constraints.py` |
| header rendering, `constraint_set`, `preflight`, `run_dse` | `loop/dse.py` |
| pre-build rejection and the infeasible score | `loop/sr_evaluator.py` |
| host-knob and host-storage checks | `loop/plan_checks.py` (`_check_host_knobs`, `_check_host_storage`) |
| host storage measurement | `hosts/cbp2025/adapter.py` (`measure_host_storage`) |
| the host facts both agents read, including the full `predictorsize()` breakdown | `hosts/cbp2025/NOTES.md` |
| the plan in force | `plan/sr.cbp2025.plan.rev1.json`, `plan/sr.cbp2025.tests.rev1.json` |
| the port as the gate saw it | `out/20260922_222452_integrate_cbp2025_diff.patch` |
| stage 4's own summary | `out/20260922_234721_summary.json` |
| tests for all of the above | `loop/tests/test_constraints.py` (45 of the suite's 481 tests) |
