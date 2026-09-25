---
name: cbp2025-not-a-kit
description: "Call the CBP2025 simulator \"CBP2025\", never \"the kit\" or \"the CBP2025 kit\", in paper text and in replies"
metadata:
  node_type: memory
  pinned: false
  originSessionId: 599ae2e4-0543-482d-9a6a-551790ec3fb2
  modified: 2026-09-25T05:16:20.595Z
---

The user asked me to stop calling CBP2025 a "kit". It should be called just
"CBP2025", as in "CBP2025's TAGE-SC-L", "CBP2025 is at commit 6074966", or
"the metrics CBP2025 reports", and never "the CBP2025 kit", "the kit" or "the
kit's reference results". This came up while I was drafting sections of the
project's paper (`paper/main.tex`), and it covers any prose I write for this
project: paper paragraphs, suggested LaTeX and replies to the user.

The user's own earlier draft used "the CBP2025 kit" in several places. When I
revise or quote a passage that contains the phrase, I should rename it there
too and point out the leftover occurrences, not copy them forward. Identifiers
that already exist in the source are the exception, for example the BibTeX key
`cbp2025kit`. Renaming one would break references, so they stay as they are
unless the user asks for a change.
