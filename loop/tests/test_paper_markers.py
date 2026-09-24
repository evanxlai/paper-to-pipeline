"""Tests for provenance grading of the source text.

The defect these exist for: a reviewer quoted a figure transcription's own
inference, wrote "the paper states", and the claim landed SUPPORTED three
rounds running. As elsewhere in the test suite, the fixture is an invented
feature, so nothing here is tied to the RUNLTS text.
"""

import os

import pytest

import paper_markers as pm

SOURCE = """Some ordinary prose about the predictor.

[Figure 2: Layout of the tag field.

--- (a) short tags -------------------------------------------------------

LITERAL. Two boxes drawn side by side:

  bit 7 | tag | bit 4
  bit 3 | ctr | bit 0

  field   digest bits   width
  tag     [7:4]         4 bits
  ctr     [3:0]         4 bits

INFERRED - the two boxes abut rather than overlap, so the field is a
concatenation and not an XOR fold.

--- (b) long tags --------------------------------------------------------

LITERAL. One box labelled "Value[15:8]", drawn right-aligned with (a).

  format  source bits    digest bits
  long    Value[15:8]    [11:4]

INFERRED - placement. The box lines up with the tag box above it, so it
starts at bit 4.

CROSS-CHECK against Table 9 (consistent):
  the field is 8 bits wide, matching the 8-bit column in Table 9.

UNCERTAIN. The alignment at bit 4 is read off the drawing, not stated. An
alternative is that the field is right-aligned at bit 0.
]

More prose after the figure.
"""


def test_unmarked_text_is_all_prose():
    ann = pm.annotate("Just a paper with no figure transcriptions in it.")
    assert ann.notes == []
    assert ann.render_notes() == ""
    assert ann.locate("no figure transcriptions") is None


def test_notes_are_collected_with_their_section():
    ann = pm.annotate(SOURCE)
    # Document order, numbered per tier: (a)'s inference, (b)'s inference,
    # then (b)'s retraction.
    assert [(n.note_id, n.tier) for n in ann.notes] == [
        ("I1", pm.INFERRED), ("I2", pm.INFERRED), ("U1", pm.UNCERTAIN),
    ]
    by_id = {n.note_id: n for n in ann.notes}
    assert by_id["U1"].where == "Figure 2 (b) long tags"
    assert "right-aligned at bit 0" in by_id["U1"].text
    assert by_id["I1"].where == "Figure 2 (a) short tags"
    assert "not an XOR fold" in by_id["I1"].text


def test_an_inferred_paragraph_raises_a_note_of_its_own():
    """The tier the source states most quietly and code must state loudly.

    An INFERRED paragraph reads as settled -- it gives its conclusion first
    and only then says the conclusion was read off a drawing -- so unlike an
    UNCERTAIN one it reaches a spec looking like a fact. Before these notes
    existed the tier was parsed, used to reject a direct quote, and then
    dropped, so nothing downstream ever learned the conclusion was a reading.
    """
    ann = pm.annotate(SOURCE)
    inferred = [n for n in ann.notes if n.tier == pm.INFERRED]
    assert [n.note_id for n in inferred] == ["I1", "I2"]
    rendered = ann.render_notes()
    assert "**I1** (INFERRED, Figure 2 (a) short tags)" in rendered
    assert "**U1** (UNCERTAIN, Figure 2 (b) long tags)" in rendered


def test_a_note_id_is_recognized_by_the_shared_pattern():
    """Downstream ranking matches note ids by regex; it must know both kinds."""
    ann = pm.annotate(SOURCE)
    ids = {n.note_id for n in ann.notes}
    assert set(pm.NOTE_ID_RE.findall(" ".join(sorted(ids)))) == ids


def test_tier_follows_the_paragraph_marker():
    ann = pm.annotate(SOURCE)
    assert ann.locate("Some ordinary prose") is None
    assert ann.locate("Two boxes drawn side by side").tier == pm.LITERAL
    assert ann.locate("concatenation and not an XOR fold").tier == pm.INFERRED
    assert ann.locate("read off the drawing, not stated").tier == pm.UNCERTAIN
    assert ann.locate("More prose after the figure") is None


def test_a_note_bears_on_its_whole_section_not_just_its_paragraph():
    """The retraction sits below a LITERAL table it contradicts.

    This is the shape that got through review: the derived `digest bits`
    column is printed inside a literal block, and the note that withdraws it
    is two paragraphs down.
    """
    ann = pm.annotate(SOURCE)
    literal = ann.locate("long    Value[15:8]    [11:4]")
    assert literal.tier == pm.LITERAL
    assert [n.note_id for n in ann.notes_for(literal)] == ["I2", "U1"]

    # A different section of the same figure inherits its own notes, not (b)'s.
    other = ann.locate("tag     [7:4]         4 bits")
    assert other.section == "(a) short tags"
    assert [n.note_id for n in ann.notes_for(other)] == ["I1"]


def test_quotes_are_located_through_whitespace_normalization():
    ann = pm.annotate(SOURCE)
    span = ann.locate("field   digest   bits\n  tag     [7:4]")
    assert span is None  # not a real substring even after squeezing
    span = ann.locate("tag     [7:4]\n         4 bits")
    assert span is not None and span.tier == pm.LITERAL


def test_marker_words_in_running_prose_do_not_open_a_block():
    text = ("The transcription marks each claim LITERAL, INFERRED or "
            "UNCERTAIN.\n  LITERAL  - an indented legend entry.\n")
    ann = pm.annotate(text)
    assert ann.notes == []
    assert ann.tier_at(0) == pm.PROSE


def test_crosscheck_arithmetic_is_not_hedged():
    """A recomputed cross-check is evidence, even next to an UNCERTAIN note.

    These blocks sit inside marked paragraphs, and grading one `uncertain`
    because of its neighbour demoted six correct storage claims in a real
    run. The note still attaches to the section, so the caveat is not lost.
    """
    ann = pm.annotate(SOURCE)
    span = ann.locate("matching the 8-bit column in Table 9")
    assert span.tier == pm.CROSSCHECK
    assert span.tier not in pm.HEDGED_TIERS
    assert [n.note_id for n in ann.notes_for(span)] == ["I2", "U1"]
    # The note itself stops at the cross-check rather than swallowing it.
    u1 = next(n for n in ann.notes if n.note_id == "U1")
    assert "Table 9" not in u1.text


# ------------------------------------------------- ungraded source guard


UNGRADED = """Some prose about a predictor.

[Figure 6: Method for generating a digest.]

  (a) INT registers
        Field "Value[5:0]" occupying bits [11:6]
      (the bits are placed right-aligned in the digest)
"""

GRADED = """Some prose about a predictor.

[Figure 6: Method for generating a digest.

--- (a) INT registers ---

LITERAL
    Field "Value[5:0]" occupying bits [11:6]

UNCERTAIN
    The alignment is read off the drawing, not stated. Right-aligned and
    left-aligned are both consistent with the figure.
]
"""

PROSE_ONLY = "A paper with no figures at all, only running text.\n"


def test_ungraded_transcription_is_refused():
    text = UNGRADED
    with pytest.raises(pm.UngradedSource) as exc:
        pm.require_markers(text, pm.annotate(text), "p.txt")
    assert "p.txt" in str(exc.value)
    assert "1 figure/table transcription" in str(exc.value)


def test_a_graded_source_passes():
    text = GRADED
    pm.require_markers(text, pm.annotate(text), "p.txt")


def test_a_source_with_no_transcriptions_passes():
    """An unmarked input stays legitimate when there is nothing to grade."""
    text = PROSE_ONLY
    pm.require_markers(text, pm.annotate(text), "p.txt")


def test_the_adopted_paper_text_is_graded():
    """Regression guard on the input itself, not on the parser.

    This is the failure the module was written for: the marked extraction was
    replaced by an unmarked one, every stage still reported success, and a
    reading of Figure 6(b) reached the integration agents as a fact.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "third_party", "runlts", "runlts.txt",
    )
    if not os.path.exists(path):          # fetched input; absent on a bare clone
        pytest.skip("paper text not fetched")
    with open(path) as fh:
        text = fh.read()
    ann = pm.annotate(text)
    pm.require_markers(text, ann, path)
    assert ann.notes, "the source declares no ambiguities at all"
    # The one the loop actually got wrong: FP digest bit placement.
    fp = [n for n in ann.notes if "FP registers" in n.where]
    assert fp, "Figure 6(b) carries no UNCERTAIN note"
    assert any("align" in n.text.lower() for n in fp)
    # The one it got wrong without ever failing a test: Figure 6(a) grades
    # "the three fields are XORed together" a reading of the drawing, and
    # every integer digest value in the design follows from it.
    xor = [n for n in ann.notes
           if n.tier == pm.INFERRED and "INT registers" in n.where]
    assert xor, "Figure 6(a) carries no INFERRED note"
    assert any("xor" in n.text.lower() for n in xor)


# ------------------------------- corroborating a claim the citation missed


def test_numbers_ignores_digits_that_belong_to_an_identifier():
    """`UT0` and `FP16` are names. Yielding their digits would let a claim
    match almost any paragraph."""
    assert pm._numbers("UT0 holds 8 entries") == {"8"}
    assert pm._numbers("FP16 and R64 and h23") == set()


def test_numbers_survives_a_sentence_final_period():
    """Claims arrive as English sentences. Treating the closing period as
    part of the number left every one of them with no numbers at all."""
    assert pm._numbers("The default is 65.") == {"65"}


def test_numbers_reads_a_decimal_glued_to_a_letter():
    """This source prints multipliers as "x0 or x2.5". An integer-strength
    rule finds no 2.5 anywhere in the paper."""
    assert pm._numbers("the multiplier is x2.5") == {"2.5"}
    assert pm._numbers("x1.19 then x1.29") == {"1.19", "1.29"}


def test_a_literal_paragraph_corroborates_a_value_it_prints():
    """The defect this exists for. A reviewer paraphrases instead of copying,
    the quote is correctly rejected, and the claim is then written into
    open_questions as unsettled -- asking what the tag width is, next to the
    figure that prints it."""
    ann = pm.annotate(SOURCE)
    span = ann.corroborates("The tag field is 4 bits wide.")
    assert span is not None and span.tier == pm.LITERAL


def test_crosscheck_arithmetic_corroborates():
    """Recomputed arithmetic settles a claim as well as a printed value --
    it is where this source states most of its storage totals, so excluding
    it would leave the majority of value claims uncorroborated."""
    ann = pm.annotate(SOURCE)
    span = ann.corroborates("The width matches the column in Table 9.")
    assert span is not None and span.tier == pm.CROSSCHECK


def test_a_number_sharing_no_word_with_the_claim_is_coincidence():
    """8 occurs in this source many times over. Without a shared word it
    establishes nothing -- the live case was "the maximum number of in-flight
    branches is 256", where 256 is elsewhere a component's table depth."""
    ann = pm.annotate(SOURCE)
    assert ann.corroborates("The replacement queue holds 8 victims.") is None


def test_a_claim_with_no_numbers_is_not_eligible():
    """Prose can be argued either way, and a paraphrase match would let weak
    citations through alongside mis-copied ones."""
    ann = pm.annotate(SOURCE)
    assert ann.corroborates("The field is a concatenation, not an XOR.") is None


def test_a_hedged_paragraph_cannot_corroborate():
    """The whole point of the tiers. A value only an UNCERTAIN paragraph
    names is not a value the source states."""
    ann = pm.annotate(
        "[Figure 1: a thing.\n\n"
        "LITERAL\n    The table has 16 entries.\n\n"
        "UNCERTAIN\n    The victim queue may hold 37 entries; unstated.\n]\n"
    )
    assert ann.corroborates("The table has 16 entries.") is not None
    assert ann.corroborates("The victim queue holds 37 entries.") is None


def test_an_unannotated_source_corroborates_nothing():
    """A paper with no transcription blocks has no authoritative spans, so
    the gate stays shut and every demotion behaves as it did before."""
    ann = pm.annotate("The table holds 16 entries, plainly stated in prose.")
    assert ann.corroborates("The table holds 16 entries.") is None
