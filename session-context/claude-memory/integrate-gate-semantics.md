---
name: integrate-gate-semantics
description: "The integrate-stage gate's pass condition is feature-dependent, not a fixed \"beat baseline\" comparison"
metadata: 
  node_type: memory
  pinned: false
  originSessionId: c86f8226-a48a-4642-9eff-920d71491a1b
  modified: 2026-09-20T05:45:07.475Z
---

In the adopt-a-paper loop (`loop/adopt_a_paper_loop.py`), stage 2 (`integrate`) currently frames gate success around comparing the integrated feature's metrics against a recorded baseline (see `_run_gate` and `helpers.load_baseline`/`record_baseline`). The user clarified that this isn't the right mental model: the gate does not need to make the change "beat" the baseline. The actual pass/fail criteria should be dynamically determined per feature being integrated — different features will have different notions of success (e.g. correctness/build/test-only for some, a metric-improvement threshold for others) — rather than a single fixed "must outperform baseline" rule hardcoded into the gate. As of this note the exact per-feature criteria design is still undecided (the user said not to worry about the specifics yet), but any future work on `gate.py` or `_run_gate` should keep the gate's pass condition parameterized/feature-specific rather than assuming a universal "compare to baseline and require improvement" check.
