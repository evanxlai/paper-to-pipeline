"""Tests for provenance grading of the source text.

The defect these exist for: a reviewer quoted a figure transcription's own
inference, wrote "the paper states", and the claim landed SUPPORTED three
rounds running. As elsewhere in the test suite, the fixture is an invented
feature, so nothing here is tied to the RUNLTS text.
"""

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
    assert [n.note_id for n in ann.notes] == ["U1"]
    assert ann.notes[0].where == "Figure 2 (b) long tags"
    assert "right-aligned at bit 0" in ann.notes[0].text


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
    assert [n.note_id for n in ann.notes_for(literal)] == ["U1"]

    # A different section of the same figure does not inherit it.
    other = ann.locate("tag     [7:4]         4 bits")
    assert other.section == "(a) short tags"
    assert ann.notes_for(other) == []


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
    assert [n.note_id for n in ann.notes_for(span)] == ["U1"]
    # The note itself stops at the cross-check rather than swallowing it.
    assert "Table 9" not in ann.notes[0].text
