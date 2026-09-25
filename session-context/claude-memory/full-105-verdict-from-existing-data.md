---
name: full-105-verdict-from-existing-data
description: "In paper-to-pipeline, a 105-trace baseline-vs-tuned verdict is assembled from data already on disk, not by launching new cluster runs"
metadata:
  node_type: memory
  pinned: false
  originSessionId: 1c428422-dfb0-428c-99b5-6d18dfb5837b
  modified: 2026-09-24T20:20:13.045Z
---

In paper-to-pipeline, the CBP2025 training set is split so that the search's
screening list (`experiments/screening-60.list`) and the promotion list
(`experiments/promote-45.list`) together cover all 105 training traces with
no overlap. The user made promote-45 the promotion default precisely so that
a finished stage-4 run yields a baseline-vs-tuned comparison on the full 105.

The baseline side of that comparison already exists:
`third_party/cbp2025/reference_results_training_set.csv` holds the
organizers' per-trace results for the kit's default TAGE-SC-L on all 105
traces (`docs/plan.md` records a local build reproducing its `int_0` row
exactly). The tuned side is the search's own screening runs on the 60 plus
the promote stage's per-trace results on the 45.

When asked for "the verdict on all 105", assemble it from those three
sources. The user stopped me when I instead submitted a new promote job over
the screening list to re-measure the baseline and finalists: it cost cluster
time, delayed another session's queued Wormhole run, and measured nothing
that was missing. Check for recorded reference results before measuring.

Keep the in-sample caveat when reporting: the tuned candidate was selected on
the 60 screening traces, so its advantage there is not independent evidence;
report the 60 and 45 halves separately alongside the 105 total.
