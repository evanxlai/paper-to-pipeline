# CBP2025 host, 2026-09-22 night to 2026-09-23

The artifacts behind the first run from plan to DSE with host knobs and
constraints, and behind the first `iso-64KiB` run. Copied out of `out/`,
which is timestamped and untracked. Every file keeps its `out/` timestamp
prefix, which is also the run id. Stage 4 summaries are renamed
`*_dse_summary.json` so they cannot be mistaken for another stage's.

The cluster was one GCP head, two `n2-standard-2` trace workers (4 trace
slots), and the CBP2025 kit at commit
`607496629452740887dc1b90a46834cc90dda1e0`. Every stage went through
`chia job submit`.

## The first run from plan to DSE, at `iso-192KiB`

`docs/handover-2026-09-23-first-full-loop.md` tells this run in full.

| run | stage | outcome |
| --- | --- | --- |
| `220840` | plan | Accepted on turn 0. 19 host knobs. The host storage terms sum to 524,615 bits, the host's own `predictorsize()`. Retired the previous plan's revision. |
| `222452` | integrate | Gate passed on attempt 3, with one plan revision (hook points only). CycWPPKI on `perf-4` 388.07 to 386.73 with sR at the paper's defaults, a 0.35% gain. |
| `232234` | dse | Every LLM call failed: the job's driver had no gateway address or token. Only the seed was scored, and the job still reported success. |
| `234721` | dse | The same search with the variables passed by hand. 3 iterations, 4 screening traces. The best candidate doubled TAGE-SC-L's tables and left sR alone. |

What `234721` does not show: that tuning sR helps. The `iso-192KiB`
baseline is the kit's default host, which is 64 KiB-class, so the search
bought host capacity the baseline never had. That is why the next run is at
`iso-64KiB`.

## The `iso-64KiB` baseline

`20260923_031241_cbp2025_baseline.json` is the kit's default host on the two
sample traces. It is identical to the `iso-192KiB` baseline, which is the
expected result: same host, same commit. At 64 KiB it is the fair baseline. It is 327
bits over the 524,288-bit allowance, so any candidate that fits uses
slightly less storage than the baseline does.

## Stages 2 to 4 in one submission, at `iso-64KiB`

Job `p2p_stages234_iso64_0923_0328`, `out/` prefix `20260923_032823`:
`--stage plan integrate dse --budget iso-64KiB`, with
`experiments/config_adaevolve_medium_vertex.yaml` (24 iterations) and
`--screening-list experiments/perf-8.list` (8 traces). Nothing was passed at
submission except the config choice: the job found the LLM gateway itself.
It ran 10 hours.

An earlier submission, `p2p_stages234_iso64_0923_0314`, stopped 11 minutes
into planning on one `RESOURCE_EXHAUSTED (429)` from Vertex. That is why
`llm.run_llm` now waits out a 429 before it gives up.

| stage | time | result |
| --- | --- | --- |
| plan | 7 min | Accepted on turn 0. 19 host knobs with ranges on both sides of the default. Three warnings, none blocking. |
| integrate | 1 h 41 min | Gate passed on attempt 4, with no plan revision. See below. |
| dse | 8 h 12 min | 10 min of preflight, then 24 iterations. Status `completed`. |

### Stage 3, attempt by attempt

`*_gate_cbp2025_<n>.json`. G1, G2 and G4 passed every time.

1. G5 failed: CycWPPKI on `perf-4` went from 388.07 to 389.65, 0.41% worse.
   The port left sR's vote out of the sum the host recomputes at update.
2. G5 failed: 388.07 to 391.51, 0.89% worse. At the host's first request
   for a vote, sR had no snapshot yet. So it voted 0 at prediction and still
   trained at update.
3. G3 failed, because the unit tests no longer compiled after a signature
   change. G5 failed: 388.07 to 388.78, 0.18% worse.
4. All passed. The gate does not record the size of a passing G5 gain, only
   that it beat the plan's floor of 0.

### Stage 4

The host alone, measured on the same 8 traces by
`20260923_062725_cbp2025_baseline.json`, is the reference:

| | bits | MPKI | CycWPPKI |
| --- | --- | --- | --- |
| host alone (baseline) | 524,615 | 6.922 | 470.32 |
| seed: sR at the paper's defaults, host unchanged | 578,478 | not built: over the allowance | |
| **best, iteration 4** | 524,206 | **6.844** (1.1% lower) | 470.36 (level) |
| iteration 19 | 524,220 | 6.853 (1.0% lower) | **470.05** (0.06% lower) |

The best candidate keeps sR at the paper's defaults. It pays for sR by
cutting the host's tagged banks, `NBANKLOW` 10 to 8 and `NBANKHIGH` 20 to 18.
It spends some of the bits saved on a bigger IMLI table (`LOGIMNB` 9 to 10).
Every candidate the search kept paid for sR the same way.

`20260923_032823_dse_candidates.json` lists all 24 iterations. Before you
read it, know these points:

- **7 of the 24 were repeats.** The LLM proposed a header it had already
  seen, and the search screened it again. Iteration 4's header came back as
  iterations 6 and 16. One other header came back five times.
- **The search did try the split between sR and the host.** sR's storage
  ranged from 53,863 bits (the paper's defaults) to 88,059, and the host's
  own storage from 470,343 down to 433,479 to pay for it. The storage
  breakdown in `20260923_032823_chia_eval_log.jsonl` shows this for every
  candidate. The lowest MPKI came with sR at its defaults (iteration 4). The
  lowest CycWPPKI came with sR at 87,669 bits (iteration 19): its prediction
  weight tables are 67,584 bits instead of 43,008, its usefulness tables are
  doubled, and the high tagged banks dropped further to pay. The other
  large-sR candidates (iterations 18, 21, 22) did worse than the host on
  CycWPPKI.
- **Iteration 19's header is lost.** The search ranks by MPKI, so its
  population of 8 dropped the candidate, and no checkpoint kept it. The
  storage breakdown fixes its sizes, but not its knobs that cost no
  storage. So promotion cannot score it.
- **`SR_MULTIPLIER_USEFUL` is inert in this port.** The preflight reported
  it. `my_cond_branch_predictor.h` has the literal `std::floor(p * 2.5)` at
  both uses, from the debug turn that fixed rounding for negative weights.
  The knob costs no storage, so the stage went on. No candidate changed it.
- The port also leaves 17 of the agent's helper scripts (`fix_*.py`,
  `patch_*.py`) in the tree. They are in the diff. They do not affect the
  build.

## Promotion: the verdict, on 16 traces the search never saw

Job `p2p_promote_iso64_0923_1423`, `out/` prefix `20260923_142307`, 2 h 57
min. `--stage promote --budget iso-64KiB` over the search's checkpoints, on
`experiments/promote-16.list`, which holds every workload family. It ran
from a clean `git worktree` at `126141f`, so only committed code ran. Files:
`20260923_142307_promote_cbp2025.json` holds every trace for every variant.

| variant | bits | fits 64 KiB | MPKI | CycWPPKI | traces with lower MPKI than the host |
| --- | --- | --- | --- | --- | --- |
| host alone (baseline) | 524,615 | 327 bits over | 2.6945 | 114.48 | |
| untuned port: sR at defaults, full host | 578,478 | no | 2.6776 (0.63% lower) | 114.44 (0.03% lower) | 8 of 16 |
| finalist 1 (iteration 4) | 524,206 | yes | 2.7151 (0.76% higher) | 115.41 (0.81% higher) | 5 of 16 |
| finalist 2 (iteration 8) | 523,326 | yes | 2.7195 (0.93% higher) | 115.56 (0.94% higher) | 4 of 16 |
| finalist 3 (iteration 17) | 524,271 | yes | 2.7261 (1.17% higher) | 115.89 (1.23% higher) | 4 of 16 |

**At 64 KiB, the tuned candidates lose to the plain host.** Every finalist
is worse on both metrics. The screening winner stayed the best finalist, so
the ranking among finalists held. What did not hold is the gain over the
host: 1.1% lower MPKI on `perf-8`, 0.76% higher here.

**sR helps, but not enough to pay for two banks of TAGE.** Take sR at its
defaults on the full host. Its MPKI is 0.63% lower than the host alone. That
costs 53,863 bits the 64 KiB allowance does not have. Every candidate that
fits paid for sR by cutting the tagged banks, and on these traces that cut
costs more than sR gives back.

**The gain is in a few families.** Against the host, per trace, with sR at
its defaults: compress improves by about 8% (`compress_5` 8.0%,
`compress_6` 7.8%), fp by 0.6 to 1.4%, and `infra_15` by 1.5%. Most int
and web traces, and `media_2`, are 0.4 to 2.5% worse. `perf-8`, the
screening list, has no compress or media trace, so the search never saw
the family where sR helps most. Cutting the tagged banks hurts int and web
most: finalist 1 is 6.6% worse than the host on `int_36`.

What this result does not settle:

- **Iteration 19 was not tested.** It grew sR the most of any candidate
  and had the best CycWPPKI in screening, but its header was lost (see
  above).
- **A screening list with compress in it is untested.** Such a search sees
  sR's biggest gain, and it can rank candidates differently. It also costs
  more screening time: compress traces are two to three times the size of
  the `perf-8` traces.
- **The port hard-codes the ×2.5 multiplier**, so that dimension was never
  searched.

## After the verdict: repeats skipped, and G5 on MPKI

Two changes came out of this run. Three short cluster jobs check them.

**Stage 4 skips repeats.** A proposal that compiles to the same code as a
candidate this search already screened is not built or run. The evolver
gets it back as a failed attempt that names the earlier candidate and its
MPKI, and it proposes again in the same iteration. Every evaluation now goes
to a candidates log with its full header. Promotion ranks every screened
candidate from that log by MPKI, not only the ones the population kept.

- `20260923_192847_dse_repeat_check_cbp2025.json`: the real evaluator,
  outside the evolver. One header was built and screened on the two sample
  traces in 28.5 s. The same header with another comment came back in
  0.001 s as a repeat, with no build.
- `20260923_192912_dse_smoke_summary.json` and
  `20260923_192912_dse_smoke_candidates.jsonl`: a 3-iteration search through
  the real evolver, on the two sample traces. In iteration 2 the LLM's first
  proposal repeated iteration 1. It was skipped, and the retry was new. The
  summary counts 5 evaluations: the seed (over the allowance), 3 screened, 1
  repeat. Its population holds all 3 screened candidates, though the
  evolver's own database kept 2.

**G5 judges MPKI.** On cbp2025, every performance entry in a test plan must
use `brmispki_50perc_amean`, the metric stage 4 ranks by
(`plan_checks.RANKING_METRIC`). The plan in force is now revision 1:
`plan/sr.cbp2025.tests.rev1.json` is the stage 2 test plan with G5 moved to
MPKI, and the port plan is unchanged.

- `20260923_192652_gate_mpki_check_cbp2025.json`: the gate, run once on the
  promoted port under revision 1. Every check passes. G5 on `perf-4`: MPKI
  5.0935 with sR off, 5.0594 with sR on, 0.67% lower. This is the first
  measured size of this port's G5 gain. The gate itself records no numbers
  for a pass.
