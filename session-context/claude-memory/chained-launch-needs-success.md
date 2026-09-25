---
name: chained-launch-needs-success
description: "When told to launch a cluster job after another one finishes, a failed predecessor or an open question means stop and ask, not launch"
metadata:
  node_type: memory
  pinned: false
  originSessionId: eeefcace-57e8-4d49-beb0-11dd8f7f765c
  modified: 2026-09-24T09:12:06.309Z
---

When the user asks for a job to be launched "after" another job is done, the
trigger is that job finishing the way they expect, not merely reaching a
terminal state. If the predecessor fails, report the failure and ask before
launching anything; the user may be about to re-run it, and a second job
competes for the same cluster and LLM quota.

This came from a session where the user asked me to launch a Wormhole
pipeline run after their sR run completed. The sR job failed in its distill
stage eleven minutes in; I read that as "done" and launched Wormhole's
distill stage on my own initiative — splitting the requested `--stage all`
into a distill-only job so it could start while a question I had asked them
about the host notes was still unanswered. They stopped it: "I am still
running the other one, I did not ask you to run this one."

Two rules follow. Do not launch while a question to the user is still open,
even a partial or "harmless" subset of the requested job. And do not
reinterpret the requested job (for example, splitting stages) to make an
early start possible; that is a new decision the user has not made.
