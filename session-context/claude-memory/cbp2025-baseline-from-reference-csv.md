---
name: cbp2025-baseline-from-reference-csv
description: "CBP2025 baseline (64KB TAGE-SC-L) numbers for any trace list come from the kit's reference CSV; never claim they are missing or re-run them"
metadata:
  node_type: memory
  pinned: false
  originSessionId: 43872e67-833c-460a-8d51-1c076dbca26f
  modified: 2026-09-24T19:42:43.041Z
---

When a question needs the CBP2025 baseline — the unmodified 64KB TAGE-SC-L
that ships with the kit — on any subset of the 105 training traces, compute
it from `third_party/cbp2025/reference_results_training_set.csv`. That file
holds per-trace results for all 105 training traces, every one `Pass`.

The user had to point this out. Asked how a running DSE compared with
baseline, I searched only the loop's own outputs (`hosts/cbp2025/baselines/`,
`runs/`), concluded that no baseline existed for the DSE's 60 screening
traces, and offered to spend cluster time measuring one. The user replied
that reference results for the 64KB TAGE-SC-L should already be in the repo,
and they were.

The file is trustworthy for this. Checked 2026-09-24: on the 8 training
traces the loop had measured itself on the pristine kit (revision `6074966`,
the same commit the vendored copy is at), `50PercMPKI`, `50PercCycWPPKI` and
`50PercIPC` matched the loop's numbers to four decimal places. To reproduce
the loop's suite metrics, take the arithmetic mean of those three columns
over the trace list, which is what `CBP2025Node.aggregate` does
(`brmispki_50perc_amean` and so on). Row keys are `<Workload>/<Run>.gz`,
which is the format the `experiments/*.list` files use. The CSV does not
cover the kit's two `sample_traces`.

More generally: before saying a reference number does not exist, check the
vendored upstream kits under `third_party/` as well as the loop's own output
directories.
