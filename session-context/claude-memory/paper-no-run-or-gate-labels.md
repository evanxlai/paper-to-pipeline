---
name: paper-no-run-or-gate-labels
description: "In the paper-to-pipeline paper's prose, describe runs and gate conditions in words instead of R1–R3 or G1–G6 labels"
metadata:
  node_type: memory
  pinned: false
  originSessionId: 599ae2e4-0543-482d-9a6a-551790ec3fb2
  modified: 2026-09-25T06:57:22.680Z
---

While I was rewriting the Experimental Setup section of the project's paper
(`paper/main.tex`), the user told me to "refrain from using R* or G*". That
means no run labels such as R1, R2 and R3 for the stage-4 searches, and no
gate labels such as G1 to G6 for the verify gate's conditions. Say what each
one is in words:

- **Runs:** "the first, short search" and "the two longer searches", not R1
  and R2/R3.
- **Gate conditions:** "the feature-off baseline check", "the smoke check"
  and "the performance check", not G2, G4 and G5.

Their draft had used these labels throughout (the verdict table, Results,
Discussion). The request came as a general "refrain from", not as a fix for a
single sentence, so it applies to any paper text I draft or revise for this
project.

The labels still work as internal shorthand in replies, code and project
docs, where `gate.py` and the run records use them. But when I hand the user
LaTeX that will go into the paper, it should not contain them. If a passage
I'm revising sits next to text that still uses the labels, I should point out
the mismatch rather than silently mixing the two styles.
