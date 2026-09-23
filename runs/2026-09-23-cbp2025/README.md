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
