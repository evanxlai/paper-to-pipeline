---
name: read-papers-visually-not-pdftotext
description: "Read research PDFs with the Read tool's visual page rendering rather than shelling out to pdftotext"
metadata: 
  node_type: memory
  pinned: false
  originSessionId: ea6641ff-cb64-4ea4-8d5a-7d5ee13fe8bc
  modified: 2026-09-20T18:12:53.068Z
---

When checking a distilled feature spec (or any loop output) against a source
paper in this project, read the PDF directly with the Read tool's `pages`
parameter so the pages render visually. Do not pipe the PDF through
`pdftotext`; the user explicitly asked for the visual read instead.

The reason this matters here is that the payload of these architecture papers
lives in the figures and tables — RUNLTS's sR digest construction is Figure 6,
its table organization is Figure 5(c), and its storage accounting is Tables 2
and 3. `pdftotext` flattens or drops that content, so a comparison built on the
extracted text can silently miss exactly the details the spec needs to match.
