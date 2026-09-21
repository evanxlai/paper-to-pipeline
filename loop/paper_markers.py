"""Provenance grading of the source text a spec is distilled from.

A paper's figures carry numbers the prose never repeats, so the input text
this loop reads carries structured figure transcriptions rather than prose
paraphrases. Those transcriptions grade their own confidence per paragraph:

    LITERAL     text and numbers that appear in the figure, transcribed verbatim
    CROSS-CHECK arithmetic recomputed against another part of the paper
    INFERRED    a reading of the figure's layout that is not stated in words
    UNCERTAIN   the figure is genuinely ambiguous at this point

Until this module existed, the loop treated every byte of the input as equally
authoritative. `verify_evidence` asked only whether a quote *occurred* in the
source, so a reviewer could quote an explicitly-hedged inference, write "the
paper states", and have the claim land as SUPPORTED. That is exactly what
happened to the sR floating-point digest placement: the source said in as many
words that the alignment was "read off the drawing, not stated" and named the
alternative reading, and three review rounds stamped the guess SUPPORTED seven
times because the sentence it quoted was really in the file.

Nothing here is keyed to a particular paper. A source text that uses no
markers yields no notes and grades every offset as `prose`, which is the
behaviour the loop had before, so an unannotated input is unaffected.

Two granularities matter, and they are not the same:

* A *paragraph* carries the tier. A quote lifted out of an INFERRED or
  UNCERTAIN paragraph cannot establish what the paper says, and code can
  enforce that without judgement.
* A *section* (one `--- (b) FP registers ---` division of a figure block)
  carries the ambiguity. An UNCERTAIN note can retract a number printed two
  paragraphs above it inside a LITERAL block -- in Figure 6(b) it retracts a
  whole derived column -- so relevance of a note is scoped to its section,
  not to its own paragraph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Tiers, weakest evidence last. `prose` is the paper's own running text and
# the default for anything outside a transcription block.
PROSE = "prose"
LITERAL = "literal"
# Arithmetic the transcription recomputed against a table elsewhere in the
# paper. Authoritative -- more so than a bare reading of a drawing -- and it
# needs its own tier because these blocks sit inside marked paragraphs whose
# tier would otherwise swallow them. One appears mid-UNCERTAIN in Figure 5(c),
# and grading it `uncertain` demoted seven correct storage claims at once.
CROSSCHECK = "crosscheck"
INFERRED = "inferred"
UNCERTAIN = "uncertain"

# Only these two cannot settle a claim about what the paper says.
HEDGED_TIERS = (INFERRED, UNCERTAIN)

_TIER_BY_MARKER = {
    "LITERAL": LITERAL, "CROSS-CHECK": CROSSCHECK,
    "INFERRED": INFERRED, "UNCERTAIN": UNCERTAIN,
}

_BLOCK_OPEN_RE = re.compile(r"^\[((?:Figure|Table)\s+[^:\]]*)", re.I)
_BLOCK_CLOSE_RE = re.compile(r"^\]\s*$")
_SECTION_RE = re.compile(r"^---+\s*(.*?)\s*-*$")
# Anchored at column 0 on purpose: the conventions preamble explains the
# markers in an indented list, and running prose elsewhere names them in a
# sentence. Neither is a marked paragraph.
_MARKER_RE = re.compile(
    r"^(LITERAL|CROSS-CHECK|INFERRED|UNCERTAIN)\b\s*[-.:]?\s*(.*)$"
)


@dataclass(frozen=True)
class Note:
    """One UNCERTAIN paragraph: an ambiguity the source refuses to resolve."""

    note_id: str
    block: str
    section: str
    text: str

    @property
    def where(self) -> str:
        return f"{self.block} {self.section}".strip()


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    tier: str
    block: str
    section: str


class Annotation:
    """Tier and location lookup over one source text, by character offset."""

    def __init__(self, spans: list[Span], notes: list[Note], text: str):
        self.spans = spans
        self.notes = notes
        self._text = text
        self._norm, self._map = _normalize_with_map(text)

    # -- lookup ----------------------------------------------------------

    def span_at(self, offset: int) -> Span | None:
        for s in self.spans:
            if s.start <= offset < s.end:
                return s
        return None

    def tier_at(self, offset: int) -> str:
        s = self.span_at(offset)
        return s.tier if s else PROSE

    def locate(self, quote: str) -> Span | None:
        """Where a quote sits, matched the way verify_evidence matches it.

        Returns None when the quote does not occur, or occurs only outside
        any transcription block -- both mean "no provenance objection".
        """
        q = _squeeze(quote)
        if not q:
            return None
        i = self._norm.find(q)
        if i < 0:
            i = self._norm.lower().find(q.lower())
        if i < 0:
            return None
        return self.span_at(self._map[i])

    def notes_for(self, span: Span | None) -> list[Note]:
        """Declared ambiguities that bear on the section a quote came from."""
        if span is None:
            return []
        return [n for n in self.notes
                if n.block == span.block and n.section == span.section]

    # -- rendering -------------------------------------------------------

    def render_notes(self) -> str:
        if not self.notes:
            return ""
        out = []
        for n in self.notes:
            body = " ".join(n.text.split())
            out.append(f"- **{n.note_id}** ({n.where}): {body}")
        return "\n".join(out)


def _squeeze(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Whitespace-squeezed text plus, per output character, its source offset.

    verify_evidence matches quotes against the squeezed form, so a match
    position has to be translatable back to the original in order to be graded.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_ws = True  # leading whitespace is stripped
    for i, ch in enumerate(text):
        if ch.isspace():
            if prev_ws:
                continue
            out.append(" ")
            idx.append(i)
            prev_ws = True
        else:
            out.append(ch)
            idx.append(i)
            prev_ws = False
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def annotate(text: str) -> Annotation:
    """Grade every character of *text* by the confidence its source declares."""
    spans: list[Span] = []
    notes: list[Note] = []
    block = section = ""
    tier = PROSE
    start = 0
    offset = 0
    n_uncertain = 0
    note_start = 0

    def close(at: int) -> None:
        nonlocal start
        if at > start:
            spans.append(Span(start, at, tier, block, section))
        start = at

    def close_note(at: int) -> None:
        nonlocal n_uncertain
        if tier != UNCERTAIN:
            return
        n_uncertain += 1
        notes.append(Note(f"U{n_uncertain}", block, section,
                          text[note_start:at]))

    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\n")
        line_end = offset + len(line)

        if m := _BLOCK_OPEN_RE.match(bare):
            close_note(offset)
            close(offset)
            block, section, tier = _squeeze(m.group(1)), "", PROSE
        elif block and _BLOCK_CLOSE_RE.match(bare):
            close_note(offset)
            close(line_end)
            block, section, tier = "", "", PROSE
            start = line_end
        elif block and (m := _SECTION_RE.match(bare)) and m.group(1):
            close_note(offset)
            close(offset)
            section, tier = _squeeze(m.group(1)), PROSE
        elif m := _MARKER_RE.match(bare):
            close_note(offset)
            close(offset)
            tier = _TIER_BY_MARKER[m.group(1)]
            note_start = offset

        offset = line_end

    close_note(offset)
    close(offset)
    return Annotation([s for s in spans if s.tier != PROSE or s.block],
                      notes, text)
