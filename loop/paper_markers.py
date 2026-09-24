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
  carries the ambiguity. A note can retract a number printed two paragraphs
  above it inside a LITERAL block -- in Figure 6(b) an UNCERTAIN note retracts
  a whole derived column -- so relevance of a note is scoped to its section,
  not to its own paragraph.

Both hedged tiers raise a note, because both describe something the paper
does not state, and the difference between them is how loudly the source says
so rather than whether the spec would be guessing. An UNCERTAIN paragraph
declares the ambiguity and names the alternatives; an INFERRED paragraph
quietly resolves it and says only in passing that the resolution was read off
a drawing. The second is the more dangerous of the two downstream: Figure 6(a)
grades "the three fields are XORed together" INFERRED, and an implementation
that takes it as settled produces every integer digest value in the design and
passes every test it is given. Notes are tagged `U1`, `U2`, ... and `I1`,
`I2`, ... so a reader -- model or human -- can tell which kind it is holding.
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

# Only these two cannot settle a claim about what the paper says. Both also
# raise a note: see the module docstring on why INFERRED needs one.
HEDGED_TIERS = (INFERRED, UNCERTAIN)
# The mirror set: paragraphs the source does assert. A value printed in one of
# these is the paper's own, whatever a reviewer managed to quote for it.
AUTHORITATIVE_TIERS = (LITERAL, CROSSCHECK)

_NOTE_PREFIX = {UNCERTAIN: "U", INFERRED: "I"}
# How a note is referred to once it has left this module -- in a reviewer's
# prose, in an open question, in a spec. Defined here so the promotion ranking
# and the note ids cannot drift apart.
NOTE_ID_RE = re.compile(r"\b[UI]\d+\b")

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
# A note's text begins at its own marker line, so the word is otherwise
# repeated in every rendering: "**I1** (INFERRED, Figure 2): INFERRED The SC
# output ...". The tier is carried on the Note now, so drop it from the body.
_LEADING_MARKER_RE = re.compile(
    r"^(?:LITERAL|CROSS-CHECK|INFERRED|UNCERTAIN)\b\s*[-.:]?\s*"
)

# Numbers as a claim spells them, for `corroborates`. The left lookbehind
# excludes digits and letters, so "UT0" yields nothing. On the right, a
# following "." is only disqualifying when a digit follows it -- otherwise
# "...is 65." at the end of a sentence yields no numbers at all, and every
# claim written as an English sentence became ineligible.
#
# Decimals and integers need different left-hand rules. An integer running on
# from a letter is part of an identifier -- UT0, WT1, FP16, R64, h23 -- and
# yielding its digits matches noise. A decimal never is, and this paper writes
# every multiplier glued to an "x": the figure prints "x0 or x2.5", so an
# integer-strength lookbehind finds no 2.5 anywhere and the one claim that
# quotes it stays uncorroborated.
_NUMERIC_RE = re.compile(
    r"(?<![\d.])(\d+\.\d+)(?!\.?\d)(?!\w)"
    r"|(?<![\w.])(\d+)(?!\.?\d)(?!\w)"
)


def _numbers(text: str) -> set[str]:
    return {m.group(1) or m.group(2) for m in _NUMERIC_RE.finditer(text or "")}

# Function words carry no evidence. Everything else a claim says -- including
# the domain nouns `tokens()` treats as generic, like "register" and "table"
# -- is what ties a number to the structure it belongs to.
_STOPWORDS = frozenset((
    "a", "an", "and", "are", "as", "at", "be", "by", "each", "for", "from",
    "in", "is", "it", "its", "of", "on", "or", "per", "that", "the", "this",
    "to", "with",
))


def _evidence_tokens(text: str) -> set[str]:
    # spec_checks' stemmer, not a second one: a claim and a paragraph have to
    # be reduced the same way for their overlap to mean anything, and two
    # tokenizers that agree today drift. The dependency runs this way only --
    # spec_checks imports nothing from here.
    from spec_checks import tokens as _tokens
    return {t for t in _tokens(text, drop_generic=False)
            if t not in _STOPWORDS and not t.isdigit()}


@dataclass(frozen=True)
class Note:
    """One hedged paragraph: something the source declines to state as fact.

    `tier` is UNCERTAIN when the source refuses to resolve the point at all,
    and INFERRED when it resolved the point by reading a figure's layout.
    """

    note_id: str
    tier: str
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

    def text_of(self, span: Span) -> str:
        return self._text[span.start:span.end]

    def corroborates(self, claim: str) -> Span | None:
        """A LITERAL or CROSS-CHECK paragraph printing every number in *claim*.

        This exists to catch a reviewer failure, not a spec failure. A quote
        that cannot be found in the source is rejected -- correctly, a bad
        citation must never carry a patch -- and the claim it was offered for
        is then written into `open_questions` as unsettled. That step is the
        bug when the claim is one the source states outright: the sR spec
        shipped six of them, asking what the multiplier is next to a figure
        that prints "x0 or x2.5", and what UT0's depth is next to one that
        prints "8 ent. UT0". Each reads as a gap in the paper. None is.

        A single span has to print all of them, and has to share a word with
        the claim besides. Numbers alone are not enough: "the maximum number
        of in-flight branches is 256" is a value this paper never states, and
        256 nonetheless appears in a LITERAL span as the sI component's UT
        depth. The shared word is what ties a number to the structure it
        belongs to, so that one is left standing as the open question it is.

        Function words are excluded from that overlap and domain nouns are
        not, which is the opposite of what `tokens()` does by default:
        "register" and "table" are exactly the words that identify which
        row of Table 3 a claim is about.

        Known limitation: a claim whose only number is incidental to it can
        still match -- "the digest is left-aligned in the 12-bit field"
        shares both 12 and "digest" with the CROSS-CHECK that derives the
        digest width, while the alignment itself is marked UNCERTAIN two
        paragraphs above. That costs nothing here, because an UNCERTAIN point
        the spec leans on is carried into open_questions by
        `carry_source_notes` regardless of what any reviewer said about it.
        """
        wanted = _numbers(claim)
        if not wanted:
            return None
        said = _evidence_tokens(claim)
        if not said:
            return None
        for span in self.spans:
            if span.tier not in AUTHORITATIVE_TIERS:
                continue
            body = self.text_of(span)
            if not wanted <= _numbers(body):
                continue
            if said & _evidence_tokens(body):
                return span
        return None

    # -- rendering -------------------------------------------------------

    def render_notes(self) -> str:
        if not self.notes:
            return ""
        out = []
        for n in self.notes:
            body = " ".join(n.text.split())
            where = f", {n.where}" if n.where else ""
            out.append(f"- **{n.note_id}** ({n.tier.upper()}{where}): {body}")
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
    counts = {UNCERTAIN: 0, INFERRED: 0}
    note_start = 0

    def close(at: int) -> None:
        nonlocal start
        if at > start:
            spans.append(Span(start, at, tier, block, section))
        start = at

    def close_note(at: int) -> None:
        if tier not in HEDGED_TIERS:
            return
        counts[tier] += 1
        body = _LEADING_MARKER_RE.sub("", text[note_start:at], count=1)
        notes.append(Note(f"{_NOTE_PREFIX[tier]}{counts[tier]}", tier,
                          block, section, body))

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

# A transcription block the source opened but graded nowhere. Anything read
# out of such a block is treated as the paper's own prose, which is only safe
# when the block really is verbatim.
_TRANSCRIPTION_RE = re.compile(r"^\[(?:Figure|Table)\s", re.I | re.M)


class UngradedSource(RuntimeError):
    """A figure-bearing source text that carries no provenance markers."""


def require_markers(text: str, ann: "Annotation", where: str = "<source>") -> None:
    """Refuse a source that transcribes figures and grades none of them.

    The markers are not decoration. `verify_evidence` needs them to refuse a
    quote lifted out of an INFERRED or UNCERTAIN paragraph, and the review
    stage's promotion ranking needs them to spend a capped knob budget on the
    ambiguities the source itself declares. An ungraded input yields no notes,
    so both degrade to no-ops -- silently, because a paper with no figures to
    transcribe is a legitimate input and must stay one.

    So the trigger is the contradiction rather than the absence: a text that
    opens figure or table transcription blocks and grades none of them has
    almost certainly lost its annotations. That is what happened between this
    module being written and the run that shipped the sR floating-point digest
    alignment as a fact -- the marked source said in as many words that the
    alignment was read off the drawing, and the text the run actually read had
    been replaced by an unmarked extraction.
    """
    if ann.notes or any(s.tier != PROSE for s in ann.spans):
        return
    blocks = _TRANSCRIPTION_RE.findall(text or "")
    if not blocks:
        return
    raise UngradedSource(
        f"{where}: {len(blocks)} figure/table transcription block(s), none of "
        f"them graded. The provenance layer is inert for this input: "
        f"hedged-evidence rejection cannot fire and the knob budget cannot be "
        f"ranked by declared ambiguity, so a reading of a drawing will reach "
        f"the integration agents as something the paper states. Add LITERAL / "
        f"CROSS-CHECK / INFERRED / UNCERTAIN markers to the transcriptions, or "
        f"set P2P_REQUIRE_SOURCE_MARKERS=0 to accept an ungraded source."
    )
