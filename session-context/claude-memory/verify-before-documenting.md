---
name: verify-before-documenting
description: "Confirm a suspected problem empirically before documenting it, planning against it, or building a fix for it"
metadata: 
  node_type: memory
  pinned: true
  originSessionId: 19ca4bbb-73b0-4105-b007-a9518b705bc2
  modified: 2026-09-20T20:19:23.009Z
---

# Investigate before noting it down — or planning against it

The user has now asked for this twice, in two different sessions, which is
what makes it a standing order rather than a one-off.

The first time, I flagged a suspected problem (a Vertex access token expiring
mid-run) and offered to record it in the project docs. Their response was to
"note it down somewhere *if it is real*" and to "investigate it deeper
first."

The second time, they handed me an existing handover document and asked me to
plan a solution to the problem it described, with the explicit rider:
"Before all of this, please verify the problem exists to a degree." So the
scope is wider than documentation. **Verify before writing docs, before
planning, and before building** — including when the problem statement comes
from a document this project already wrote and treats as authoritative. A
prior session's confirmed finding is a snapshot that can go stale, not a
premise to build on unchecked.

That check paid for itself. Re-probing a handover doc's claims turned up two
that were no longer true: a model the doc said `404`ed in one region now
served `200` there, and a suggested mitigation (normalising model names at a
proxy) provably could not work, because the behaviour it was meant to defuse
happens in the client's own process before any HTTP request exists. Both
would have been carried forward into the plan as fact.

In practice this means preferring a measurement to an inference, and
reporting the check alongside the claim. For the token case, the useful
version was not "ADC tokens expire, so long runs will break" but the chain of
confirmed facts: the token's real lifetime read off `tokeninfo`, a
deliberately bogus token proving the endpoint returns 401 per request rather
than tolerating staleness, a grep establishing the library has no refresh
path at all, and a per-iteration timing measurement showing exactly how far
into the search the failure lands. The quantified version only existed
because of the verification step.

This fits the project's own conventions, which are worth matching: the
codebase explicitly separates what was confirmed from what was assumed
(`loop/dse.py`'s docstring records that its first draft guessed an interface
wrong and what reading the real source corrected), and `docs/dse-setup.md`
has a standing "what was found wrong in the first draft" section. Write
findings in that register — state what was verified and how, and label
anything still unconfirmed as an estimate.
