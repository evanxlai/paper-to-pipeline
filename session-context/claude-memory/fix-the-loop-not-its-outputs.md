---
name: fix-the-loop-not-its-outputs
description: "In paper-to-pipeline, repair the loop's mechanism rather than hand-editing the artifacts it produces"
metadata: 
  node_type: memory
  pinned: true
  originSessionId: ea6641ff-cb64-4ea4-8d5a-7d5ee13fe8bc
  modified: 2026-09-24T09:10:45.881Z
---

The deliverable of this project is the adopt-a-paper loop itself, not any
particular artifact the loop emits. When a defect turns up in a generated
artifact such as `spec/sr.*.json`, the correct response is to fix whatever part
of the loop failed to catch it — a prompt, a deterministic check in
`loop/spec_checks.py`, the review partition, or the verdict taxonomy — and then
re-run. Do not recommend hand-editing the generated spec.

The user pushed back on exactly this advice. Hand-patching an output
contaminates the evidence: if the spec is edited by hand and a later stage then
succeeds, that success says nothing about whether the loop works, which is the
only question the project is trying to answer.

The same holds for the loop's hand-written inputs. The user called it
"cheating" on discovering that `hosts/cbp2025/NOTES.md` — inlined verbatim
into the stage-2 planner and stage-3 integrator prompts — carried the answer
to sR's own design question ("sR is not an override, it is one more `LSUM +=`
line"), written in by an earlier session after a failed run, rather than
letting the escalation mechanism send the question back to the planner. Host
notes should hold host facts that any paper's port would need (interfaces,
hook points, build and gate rules), never a verdict about how a particular
paper's mechanism should be integrated. When a run fails on such a question,
the fix goes into the loop's mechanism, not into the notes as the answer.

A useful distinction when triaging a miss is whether the loop lacks a
*mechanism* for the defect or merely has a *heuristic* that is not sharp
enough. Mechanism gaps are worth fixing immediately and tend to pay off at
once: adding an `INCONSISTENT` verdict for spec-internal contradictions cleared
two long-standing errors in a single review round after six rounds across two
earlier runs had failed to touch them. Heuristic sharpening is more open-ended,
so it is worth setting an explicit stopping rule before starting, and treating
a defect that survives repeated attempts as a documented limitation of the loop
rather than something to keep grinding on.
