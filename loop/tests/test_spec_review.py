"""Tests for the reviewer stage's pure functions.

No cluster and no LLM: partitioning, evidence verification, patch merging and
the regression differ are all deterministic, which is the point of keeping the
backend import lazy inside review_spec().

As in test_spec_checks, every fixture is an invented feature.
"""

import copy
import json

import pytest

import spec_checks
import spec_review
from spec_review import (
    Record, apply_patches, chunk_text, parse_records, partition,
    promote_unsupported, ptr_apply, ptr_get, regressions,
    uncovered_regressions, verify_evidence,
)


@pytest.fixture
def spec():
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "A Victim Tag Predictor", "inputs_used": "paper_only"},
        "summary": "Tracks evicted tags.",
        "state": [
            {"name": "victim tag table", "organization": "256 entries",
             "entry_format": "tag (12)", "size_bits": 3072, "indexing": "PC"},
            {"name": "decay shadow counters", "organization": "4 counters",
             "entry_format": "decay_ctr (8)", "size_bits": 32, "indexing": "bank"},
        ],
        "algorithms": [
            {"name": "predict", "trigger": "lookup",
             "pseudocode": "v = victim_tag_table[PC]; return v.tag"},
            {"name": "decay", "trigger": "every cycle",
             "pseudocode": "decay_shadow[bank] -= 1"},
        ],
        "host_interfaces": [{"need": "evicted tag", "description": "..."}],
        "resource_accounting": {"total_storage_bits": 3104},
        "parameters": [
            {"name": "decay_window", "type": "int", "default": 200,
             "range": "[1, 255]", "storage_impact": "widens decay_ctr"},
        ],
        "unit_tests": [
            {"name": "tag survives", "given": "one fill", "expect": "tag == 0x1A"},
        ],
    }


PAPER = (
    "The victim tag table holds 256 entries of 12 bits each.\n\n"
    "Each decay counter is decremented once per cycle and the entry is "
    "invalidated when it reaches zero.\n"
)


# ------------------------------------------------------------- pointers


def test_pointer_get_and_apply(spec):
    assert ptr_get(spec, "/state/0/size_bits") == 3072
    ptr_apply(spec, "/state/0/size_bits", 99, "replace")
    assert spec["state"][0]["size_bits"] == 99


def test_pointer_append(spec):
    ptr_apply(spec, "/unit_tests/-", {"name": "n", "given": "g", "expect": "e"}, "add")
    assert len(spec["unit_tests"]) == 2


def test_pointer_missing_returns_default(spec):
    assert ptr_get(spec, "/state/9/size_bits", "absent") == "absent"


# ------------------------------------------------------------ partition


def test_partition_groups_state_with_the_algorithm_that_uses_it(spec):
    units = {u.unit_id: u for u in partition(spec)}
    predict = units["algo:predict"]
    assert "/state/0" in predict.prefixes          # victim_tag_table
    assert "/state/1" not in predict.prefixes      # decay counters belong to decay


def test_partition_attaches_parameters_by_reference(spec):
    spec["algorithms"][1]["pseudocode"] = "decay_shadow[bank] -= 1  # of decay_window"
    units = {u.unit_id: u for u in partition(spec)}
    assert "/parameters/0" in units["algo:decay"].prefixes


def test_partition_emits_a_global_unit(spec):
    units = {u.unit_id: u for u in partition(spec)}
    assert "/summary" in units["global"].prefixes
    assert "/resource_accounting" in units["global"].prefixes


def test_partition_collects_orphans(spec):
    spec["state"].append({"name": "zzz floating buffer", "organization": "8",
                          "entry_format": "p (4)", "size_bits": 32, "indexing": "n"})
    units = {u.unit_id: u for u in partition(spec)}
    assert "/state/2" in units["orphan"].prefixes


def test_partition_respects_the_unit_cap(spec):
    spec["algorithms"] += [
        {"name": f"op{i}", "trigger": "t", "pseudocode": "x = 1"} for i in range(20)
    ]
    assert len(partition(spec, max_units=5)) == 5


def test_unit_ownership_is_prefix_scoped(spec):
    unit = {u.unit_id: u for u in partition(spec)}["algo:predict"]
    assert unit.owns("/algorithms/0/pseudocode")
    assert not unit.owns("/algorithms/1/pseudocode")


# ------------------------------------------------------ evidence checking


def rec(**kw):
    base = dict(unit_id="algo:predict", pointer="/state/0/size_bits",
                claim="c", verdict="SUPPORTED")
    base.update(kw)
    return Record(**base)


def test_verbatim_quote_verifies():
    r = rec(quote="holds 256 entries of 12 bits each")
    verify_evidence([r], PAPER)
    assert r.evidence_ok and r.verdict == "SUPPORTED"


def test_quote_matching_ignores_whitespace_reflow():
    r = rec(quote="holds 256 entries\n   of 12 bits each")
    verify_evidence([r], PAPER)
    assert r.evidence_ok


def test_fabricated_quote_is_demoted_and_disarmed():
    r = rec(verdict="CONTRADICTED", quote="the table holds 512 entries",
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 1})
    verify_evidence([r], PAPER)
    assert r.verdict == "UNSUPPORTED"
    assert r.patch is None and r.open_question


def test_trivially_short_quote_rejected():
    r = rec(quote="the")
    verify_evidence([r], PAPER)
    assert not r.evidence_ok and r.verdict == "UNSUPPORTED"


# --------------------------------------------------------- patch merging


def units_for(spec):
    return partition(spec)


def test_contradicted_patch_with_evidence_applies(spec):
    r = rec(verdict="CONTRADICTED", quote="holds 256 entries of 12 bits each",
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 3072})
    verify_evidence([r], PAPER)
    new, rejections = apply_patches(spec, [r], units_for(spec))
    assert new["state"][0]["size_bits"] == 3072 and not rejections


def test_unsupported_may_not_patch(spec):
    r = rec(verdict="UNSUPPORTED",
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 1})
    new, rejections = apply_patches(spec, [r], units_for(spec))
    assert new == spec
    assert "may not carry a patch" in rejections[0]["reason"]


def test_out_of_scope_patch_rejected(spec):
    r = rec(unit_id="algo:predict", verdict="CONTRADICTED",
            quote="holds 256 entries of 12 bits each",
            patch={"op": "replace", "pointer": "/algorithms/1/pseudocode", "value": "x"})
    verify_evidence([r], PAPER)
    new, rejections = apply_patches(spec, [r], units_for(spec))
    assert new == spec and "outside the unit's scope" in rejections[0]["reason"]


def test_underspecified_patch_must_add_detail(spec):
    shrink = rec(verdict="UNDERSPECIFIED", quote=None,
                 patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                        "value": "x"})
    shrink.unit_id = "algo:predict"
    new, rejections = apply_patches(spec, [shrink], units_for(spec))
    assert new == spec and "must add detail" in rejections[0]["reason"]


def test_underspecified_patch_that_expands_is_accepted(spec):
    longer = spec["algorithms"][0]["pseudocode"] + "\n# saturating at 12 bits"
    r = rec(verdict="UNDERSPECIFIED",
            patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                   "value": longer})
    new, rejections = apply_patches(spec, [r], units_for(spec))
    assert new["algorithms"][0]["pseudocode"] == longer and not rejections


def test_conflicting_patches_are_both_dropped_and_escalated(spec):
    common = dict(verdict="CONTRADICTED", quote="holds 256 entries of 12 bits each")
    a = rec(**common, patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 10})
    b = rec(**common, patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 20})
    verify_evidence([a, b], PAPER)
    new, rejections = apply_patches(spec, [a, b], units_for(spec))
    assert new["state"][0]["size_bits"] == 3072
    assert len(rejections) == 2
    assert any("disagreed" in q for q in new["open_questions"])


def test_reviewers_agreeing_on_a_value_is_not_a_conflict(spec):
    """Independent convergence on one number is the stage's best signal.

    Comparing prose byte-for-byte turned three reviewers who all derived the
    same digest into a three-way dispute and dropped the answer entirely.
    """
    common = dict(verdict="UNDERSPECIFIED", unit_id="algo:predict")
    a = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "The 12-bit digest is 0x0A8."})
    b = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "The 12-bit digest is 0x0A8, the XOR of "
                                      "trailing 0, leading 61 and value 5."})
    new, rejections = apply_patches(spec, [a, b], units_for(spec))
    assert new["unit_tests"][0]["expect"].startswith("The 12-bit digest is 0x0A8, the XOR")
    assert len(rejections) == 1 and "same assertion" in rejections[0]["reason"]


def test_hex_and_decimal_forms_of_the_same_number_agree(spec):
    common = dict(verdict="UNDERSPECIFIED", unit_id="algo:predict")
    a = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "digest == 0x0A8 exactly"})
    b = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "digest == 168"})
    new, _ = apply_patches(spec, [a, b], units_for(spec))
    assert "0x0A8" in new["unit_tests"][0]["expect"]


def test_different_values_are_still_a_conflict(spec):
    common = dict(verdict="UNDERSPECIFIED", unit_id="algo:predict")
    a = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "digest == 0x0A8"})
    b = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "digest == 0x1FF"})
    new, rejections = apply_patches(spec, [a, b], units_for(spec))
    assert new["unit_tests"][0]["expect"] == spec["unit_tests"][0]["expect"]
    assert len(rejections) == 2
    assert any("disagreed" in q for q in new["open_questions"])


def test_negation_blocks_the_agreement_merge(spec):
    """Same numbers, opposite claim -- must not silently merge."""
    common = dict(verdict="UNDERSPECIFIED", unit_id="algo:predict")
    a = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "the counter saturates at 63"})
    b = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "the counter does not saturate at 63"})
    new, rejections = apply_patches(spec, [a, b], units_for(spec))
    assert len(rejections) == 2
    assert new["unit_tests"][0]["expect"] == spec["unit_tests"][0]["expect"]


def test_agreement_requires_an_actual_number(spec):
    """Two different prose rewrites with no figures are not evidence of agreement."""
    common = dict(verdict="UNDERSPECIFIED", unit_id="algo:predict")
    a = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "the tag is preserved"})
    b = rec(**common, patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                             "value": "the entry survives eviction"})
    _, rejections = apply_patches(spec, [a, b], units_for(spec))
    assert len(rejections) == 2


def test_appends_to_one_array_are_not_conflicts(spec):
    """Three reviewers appending to /xs/- are three additions, not a dispute.

    Grouping them by pointer read them as a three-way disagreement and dropped
    all three, which is how a live round lost its best finding.
    """
    spec.setdefault("open_questions", [])
    rs = [
        rec(unit_id="coverage", verdict="UNDERSPECIFIED", claim=f"gap {i}",
            patch={"op": "add", "pointer": "/open_questions/-", "value": f"q{i}"})
        for i in range(3)
    ]
    new, rejections = apply_patches(spec, rs, units_for(spec))
    assert new["open_questions"] == ["q0", "q1", "q2"]
    assert not rejections


def test_identical_appends_are_deduplicated(spec):
    spec.setdefault("open_questions", [])
    rs = [
        rec(unit_id="coverage", verdict="UNDERSPECIFIED", claim=f"r{i}",
            patch={"op": "add", "pointer": "/open_questions/-", "value": "same"})
        for i in range(2)
    ]
    new, rejections = apply_patches(spec, rs, units_for(spec))
    assert new["open_questions"] == ["same"]
    assert len(rejections) == 1 and "duplicate" in rejections[0]["reason"]


def test_appends_still_apply_alongside_a_replace(spec):
    spec.setdefault("open_questions", [])
    add = rec(unit_id="coverage", verdict="UNDERSPECIFIED",
              patch={"op": "add", "pointer": "/state/-",
                     "value": {"name": "n", "organization": "o",
                               "entry_format": "f (1)", "size_bits": 1,
                               "indexing": "i"}})
    repl = rec(verdict="CONTRADICTED", quote="holds 256 entries of 12 bits each",
               patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 3072})
    verify_evidence([repl], PAPER)
    new, rejections = apply_patches(spec, [add, repl], units_for(spec))
    assert len(new["state"]) == 3 and new["state"][0]["size_bits"] == 3072
    assert not rejections


# ------------------------------------------------- test-expectation carve-out


def test_concretizing_a_test_may_shorten_it(spec):
    """'digest == 0x0A8' is shorter than the prose it replaces, and better.

    The length rules exist to stop rules being hollowed into stubs; applying
    them to test expectations refuses the exact fix the vacuous_test check is
    meant to provoke.
    """
    spec["unit_tests"][0]["expect"] = (
        "The digest is computed correctly by folding the leading count, the "
        "trailing count and the low value bits together as the figure shows."
    )
    r = rec(verdict="UNDERSPECIFIED", unit_id="algo:predict",
            patch={"op": "replace", "pointer": "/unit_tests/0/expect",
                   "value": "digest == 0x0A8"})
    new, rejections = apply_patches(spec, [r], units_for(spec))
    assert new["unit_tests"][0]["expect"] == "digest == 0x0A8"
    assert not rejections


def test_shortening_a_test_is_not_a_regression(spec):
    old = copy.deepcopy(spec)
    old["unit_tests"][0]["expect"] = "a long prose expectation " * 5
    new = copy.deepcopy(old)
    new["unit_tests"][0]["expect"] = "digest == 0x0A8"
    assert regressions(old, new) == []


def test_hollowing_a_rule_is_still_a_regression(spec):
    """The carve-out must not leak outside unit tests."""
    new = copy.deepcopy(spec)
    new["algorithms"][0]["pseudocode"] = "u()"
    assert [f.code for f in regressions(spec, new)] == ["shortened_field"]


def test_coverage_records_may_append_anywhere_but_only_add(spec):
    add = rec(unit_id="coverage", verdict="UNDERSPECIFIED",
              patch={"op": "add", "pointer": "/open_questions/-", "value": "q"})
    replace = rec(unit_id="coverage", verdict="UNDERSPECIFIED",
                  patch={"op": "replace", "pointer": "/summary", "value": "short"})
    spec.setdefault("open_questions", [])
    new, rejections = apply_patches(spec, [add, replace], units_for(spec))
    assert "q" in new["open_questions"]
    assert new["summary"] == spec["summary"]
    assert len(rejections) == 1


# ------------------------------------------------------------- promotion


def test_unsupported_becomes_an_open_question_and_a_dse_knob(spec):
    r = rec(verdict="UNSUPPORTED",
            pointer="/algorithms/0/pseudocode",
            open_question="Does the counter saturate or wrap?",
            enum_candidates=["saturate", "wrap", "clamp_to_zero"])
    out = promote_unsupported(spec, [r])
    assert out["open_questions"] == [
        "[/algorithms/0/pseudocode] Does the counter saturate or wrap?"]
    knob = [p for p in out["parameters"] if p["type"] == "enum"][0]
    assert knob["range"] == "choices: saturate|wrap|clamp_to_zero"
    assert knob["default"] == "saturate"


def test_single_candidate_does_not_become_a_knob(spec):
    r = rec(verdict="UNSUPPORTED", open_question="q", enum_candidates=["only"])
    out = promote_unsupported(spec, [r])
    assert all(p["type"] != "enum" for p in out["parameters"])


def test_prose_candidates_do_not_become_knobs(spec):
    """dse.py emits `#define SR_<NAME> <value>`; a sentence is uncompilable."""
    r = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
            open_question=None,
            enum_candidates=["A simple XOR fold of the PC bits",
                             "No skew (use the raw PC)"])
    out = promote_unsupported(spec, [r])
    assert all(p["type"] != "enum" for p in out["parameters"])
    # The information is kept, just not as a search dimension.
    assert any("XOR fold" in q for q in out["open_questions"])


@pytest.mark.parametrize("cands,promoted", [
    (["xor_fold", "concat"], True),
    (["at_completion", "at_decode"], True),
    (["64", "128", "256"], True),
    (["2.5", "1.0"], True),
    (["saturate at 63", "wrap modulo 64"], False),
    (["[0.0, 4.0]", "[1.0, 3.0]"], False),
])
def test_only_literal_candidates_are_promoted(spec, cands, promoted):
    r = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
            open_question="q", enum_candidates=cands)
    out = promote_unsupported(spec, [r])
    assert bool([p for p in out["parameters"] if p["type"] == "enum"]) is promoted


def test_ambiguity_about_an_existing_parameter_is_not_a_new_knob(spec):
    """A disputed range belongs in that range, not in a knob of range strings."""
    r = rec(verdict="UNSUPPORTED", pointer="/parameters/0/range",
            open_question="What is the legal range?",
            enum_candidates=["wide", "narrow"])
    out = promote_unsupported(spec, [r])
    assert all(p["type"] != "enum" for p in out["parameters"])
    # Questions are stored tagged with the spec location that raised them.
    assert out["open_questions"] == ["[/parameters/0/range] What is the legal range?"]


def test_promotion_is_capped(spec, monkeypatch):
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 2)
    # Distinct candidate sets: five *different* ambiguities, so the cap is
    # what limits promotion here rather than the same-question dedup.
    rs = [
        rec(verdict="UNSUPPORTED", pointer=f"/algorithms/0/pseudocode",
            claim=f"c{i}", open_question=f"q{i}",
            enum_candidates=[f"a{i}", f"b{i}"])
        for i in range(5)
    ]
    out = promote_unsupported(spec, rs)
    assert len([p for p in out["parameters"] if p["type"] == "enum"]) == 2
    assert len(out["open_questions"]) == 5      # nothing is lost, only deferred


def test_promoted_knob_names_do_not_collide(spec):
    rs = [
        rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
            open_question=f"q{i}", enum_candidates=["a", "b"])
        for i in range(3)
    ]
    out = promote_unsupported(spec, rs)
    names = [p["name"] for p in out["parameters"]]
    assert len(names) == len(set(names))


# ---------------------------------------------------------- regressions


def test_removed_array_element_is_a_regression(spec):
    new = copy.deepcopy(spec)
    new["unit_tests"] = []
    assert "removed_element" in [f.code for f in regressions(spec, new)]


def test_removed_key_is_a_regression(spec):
    new = copy.deepcopy(spec)
    del new["algorithms"][0]["trigger"]
    assert "removed_key" in [f.code for f in regressions(spec, new)]


def test_hollowed_out_field_is_a_regression(spec):
    """A rule replaced by a stub still validates and still builds."""
    new = copy.deepcopy(spec)
    new["algorithms"][0]["pseudocode"] = "update()"
    codes = [f.code for f in regressions(spec, new)]
    assert "shortened_field" in codes


def test_growth_is_never_a_regression(spec):
    new = copy.deepcopy(spec)
    new["algorithms"][0]["pseudocode"] += "\n# plus a documented corner case"
    assert regressions(spec, new) == []


def test_regression_justified_by_a_patch_is_not_reported(spec):
    new = copy.deepcopy(spec)
    new["algorithms"][0]["pseudocode"] = "u()"
    r = rec(verdict="CONTRADICTED", quote="holds 256 entries of 12 bits each",
            patch={"op": "replace", "pointer": "/algorithms/0/pseudocode", "value": "u()"})
    r.evidence_ok = True
    assert uncovered_regressions(spec, new, [r]) == []


def test_unjustified_regression_is_reported(spec):
    new = copy.deepcopy(spec)
    new["algorithms"][0]["pseudocode"] = "u()"
    assert uncovered_regressions(spec, new, []) != []


# --------------------------------------------------------------- chunking


def test_chunking_is_a_noop_for_short_papers():
    assert chunk_text("a\n\nb", 1000) == ["a\n\nb"]


def test_chunking_splits_on_paragraph_boundaries():
    text = "\n\n".join(["para " + "x" * 50 for _ in range(10)])
    chunks = chunk_text(text, 200)
    assert len(chunks) > 1
    assert "".join(c.replace("\n\n", "") for c in chunks).count("para") == 10


# ------------------------------------------------------------- parsing


def test_parse_records_tolerates_fenced_output():
    raw = 'prose\n```json\n{"records": [{"pointer": "/summary", "claim": "c", ' \
          '"verdict": "supported", "evidence": {"quote": "q", "why": "w"}}]}\n```'
    recs, errs = spec_review.parse_records("global", raw)
    assert not errs and recs[0].verdict == "SUPPORTED" and recs[0].quote == "q"


def test_parse_records_rejects_unknown_verdict():
    raw = '{"records": [{"pointer": "/summary", "verdict": "PROBABLY_FINE"}]}'
    recs, errs = spec_review.parse_records("global", raw)
    assert not recs and "unknown verdict" in errs[0]


def test_parse_records_reports_bad_json():
    recs, errs = spec_review.parse_records("global", "not json at all")
    assert not recs and "not valid JSON" in errs[0]


# -------------------------------------- promotion scope and question dedup


def test_promotion_cap_is_spec_wide_not_per_round(spec, monkeypatch):
    """Rounds accumulate into one spec, so a per-call counter would multiply
    the cap by REVIEW_ROUNDS -- the knobs are still there next round."""
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 2)
    rs = [rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
              claim=f"c{i}", open_question=f"is it {i} or {i + 90}?",
              enum_candidates=["a", "b"]) for i in range(4)]

    after_round_1 = promote_unsupported(spec, rs)
    after_round_2 = promote_unsupported(after_round_1, rs)

    minted = [p for p in after_round_2["parameters"]
              if str(p.get("origin", "")).startswith("review:")]
    assert len(minted) == 2


@pytest.mark.parametrize("pointer", [
    "/resource_accounting/budget_donors",
    "/unit_tests/3",
    "/unit_tests/4/expect",
    "/summary",
])
def test_only_compiled_parts_of_the_spec_become_knobs(spec, pointer):
    """A #define can switch behaviour, not an accounting sentence or a test's
    expectation. Promoting those spends a search dimension on nothing."""
    r = rec(verdict="UNSUPPORTED", pointer=pointer, claim="c",
            enum_candidates=["alpha", "beta"])
    out = promote_unsupported(spec, [r])
    assert not [p for p in out["parameters"]
                if str(p.get("origin", "")).startswith("review:")]
    assert out["open_questions"]          # the information is kept


@pytest.mark.parametrize("pointer", ["/algorithms/0/pseudocode",
                                     "/state/1/entry_format"])
def test_algorithm_and_state_ambiguities_still_promote(spec, pointer):
    r = rec(verdict="UNSUPPORTED", pointer=pointer, claim="c",
            enum_candidates=["alpha", "beta"])
    out = promote_unsupported(spec, [r])
    assert [p for p in out["parameters"]
            if str(p.get("origin", "")).startswith("review:")]


def test_reworded_question_at_one_pointer_is_recorded_once(spec):
    """Fresh reviewers each round phrase the same hole differently; exact
    dedup never fires on that, which is what inflates the list."""
    ptr = "/state/1/entry_format"
    first = rec(verdict="UNSUPPORTED", pointer=ptr, claim="c",
                open_question="How is the 8-bit decay_ctr initialised to span "
                              "a 256-step window?")
    second = rec(verdict="UNSUPPORTED", pointer=ptr, claim="c",
                 open_question="What reset value does decay_ctr take, given "
                               "that 256 exceeds 8 bits for that window?")
    out = promote_unsupported(promote_unsupported(spec, [first]), [second])
    assert len(out["open_questions"]) == 1


def test_a_different_question_at_the_same_pointer_is_kept(spec):
    ptr = "/state/1/entry_format"
    rs = [
        rec(verdict="UNSUPPORTED", pointer=ptr, claim="c",
            open_question="How is the 8-bit decay_ctr initialised for 256 steps?"),
        rec(verdict="UNSUPPORTED", pointer=ptr, claim="c",
            open_question="Is the victim tag compared before the shadow read?"),
    ]
    out = promote_unsupported(spec, rs)
    assert len(out["open_questions"]) == 2


def test_the_same_question_at_two_pointers_is_kept_twice(spec):
    """Dedup is scoped to a location: the same hole in two places is two
    fixes, and the tag tells the implementer where each one is."""
    q = "How is the 8-bit decay_ctr initialised for 256 steps?"
    rs = [rec(verdict="UNSUPPORTED", pointer=p, claim="c", open_question=q)
          for p in ("/state/1/entry_format", "/algorithms/1/pseudocode")]
    out = promote_unsupported(spec, rs)
    assert len(out["open_questions"]) == 2
    assert all(o.startswith("[/") for o in out["open_questions"])


# ------------------------------------- INCONSISTENT: self-contradiction


def _contradiction_spec():
    """A spec that copied both halves of the paper faithfully and cannot
    implement them together: 256 steps in a field it declares as 8 bits."""
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "A Victim Tag Predictor", "inputs_used": "paper_only"},
        "summary": "Tracks evicted tags.",
        "state": [
            {"name": "decay table", "organization": "4 counters",
             "entry_format": "decay_ctr (8 bits)", "size_bits": 32,
             "indexing": "bank"},
        ],
        "algorithms": [
            {"name": "refresh", "trigger": "completion",
             "pseudocode": "decay_ctr = 256"},
        ],
        "host_interfaces": [{"need": "tick", "description": "per-instruction tick"}],
        "resource_accounting": {"total_storage_bits": 32},
        "parameters": [],
        "unit_tests": [{"name": "t", "given": "g", "expect": "ctr == 0"}],
    }


def test_inconsistent_patches_without_a_quote(spec):
    """The verdict exists precisely so a self-contradiction can be fixed with
    no paper citation -- the paper states both halves."""
    s = _contradiction_spec()
    findings = spec_checks.run_checks(s)
    assert any(f.code == "unrepresentable_literal" for f in findings)

    r = rec(unit_id="algo:refresh", pointer="/algorithms/0/pseudocode",
            verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                   "value": "decay_ctr = 255  // counts 256 steps, 255..0"})
    units = partition(s)
    new, rejections = apply_patches(s, [r], units, findings)
    assert not rejections
    assert "255" in new["algorithms"][0]["pseudocode"]
    assert not [f for f in spec_checks.run_checks(new)
                if f.code == "unrepresentable_literal"]


def test_inconsistent_is_refused_where_no_check_flagged(spec):
    """Otherwise the verdict degrades into 'rewrite anything, cite nothing'."""
    s = _contradiction_spec()
    findings = spec_checks.run_checks(s)
    r = rec(unit_id="global", pointer="/summary", verdict="INCONSISTENT",
            quote=None,
            patch={"op": "replace", "pointer": "/summary", "value": "anything"})
    new, rejections = apply_patches(s, [r], partition(s), findings)
    assert new["summary"] == s["summary"]
    assert rejections and "no self-consistency check" in rejections[0]["reason"]


def test_inconsistent_without_findings_cannot_patch(spec):
    """No findings passed in means no scope, so nothing is patchable."""
    s = _contradiction_spec()
    r = rec(unit_id="algo:refresh", pointer="/algorithms/0/pseudocode",
            verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                   "value": "decay_ctr = 255"})
    new, rejections = apply_patches(s, [r], partition(s), None)
    assert rejections and new == s


def test_inconsistent_verdict_survives_evidence_checking():
    """verify_evidence must not demote a verdict that never claimed a quote."""
    r = rec(verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 1})
    verify_evidence([r], "some paper text that says nothing relevant")
    assert r.verdict == "INCONSISTENT" and r.patch is not None


def test_parse_records_accepts_the_new_verdict():
    recs, errs = parse_records("algo:refresh", json.dumps({"records": [{
        "pointer": "/algorithms/0/pseudocode", "claim": "c",
        "verdict": "INCONSISTENT",
        "patch": {"op": "replace", "pointer": "/algorithms/0/pseudocode",
                  "value": "decay_ctr = 255"},
    }]}))
    assert not errs and recs[0].verdict == "INCONSISTENT"


# ------------------------------------------------- dedup pointer scope


def test_dedup_spans_an_element_and_its_subfields(spec):
    """Reviewers anchor the same question at /algorithms/0 one round and
    /algorithms/0/pseudocode the next; keying on the exact pointer lets every
    reword back in through a suffix."""
    q = "How is the 8-bit decay_ctr initialised for 256 steps?"
    rs = [rec(verdict="UNSUPPORTED", pointer=p, claim="c", open_question=q)
          for p in ("/algorithms/0", "/algorithms/0/pseudocode",
                    "/algorithms/0/notes")]
    out = promote_unsupported(spec, rs)
    assert len(out["open_questions"]) == 1


def test_dedup_still_separates_different_elements(spec):
    q = "How is the 8-bit decay_ctr initialised for 256 steps?"
    rs = [rec(verdict="UNSUPPORTED", pointer=p, claim="c", open_question=q)
          for p in ("/algorithms/0/pseudocode", "/algorithms/1/pseudocode")]
    out = promote_unsupported(spec, rs)
    assert len(out["open_questions"]) == 2


# ---------------------------------------------- findings must be routable


def test_every_finding_reaches_a_review_unit(spec):
    """A finding anchored where no unit owns it is dropped from every reviewer
    prompt and can never be acted on -- silently, and only visible by
    inspection. Any new check must anchor somewhere a unit claims."""
    s = _contradiction_spec()
    s["algorithms"].append({
        "name": "consume", "trigger": "update",
        "pseudocode": "ctx.sum = [0] * 4\nfor b in 0..3:\n  if ok(b):\n"
                      "    ctx.sum[b] = w(b)\nx = ctx.sum[0]\ndecay_ctr = 999",
    })
    for target in (spec, s):
        units = partition(target)
        for f in spec_checks.run_checks(target):
            assert any(u.owns(f.pointer) for u in units), \
                f"{f.code} at {f.pointer} reaches no reviewer"


# ------------------------------------------------- provenance of the evidence

HEDGED_PAPER = """The predictor keeps a tag per set.

[Figure 3: Tag layout.

--- (a) field placement ---------------------------------------------------

LITERAL. One box labelled "Value[15:8]".

  format  source bits    digest bits
  long    Value[15:8]    [11:4]

INFERRED - the box lines up with the row above, so it starts at bit 4.

UNCERTAIN. The alignment at bit 4 is read off the drawing, not stated. An
alternative is that the field is right-aligned at bit 0.
]

Unrelated closing prose.
"""


def test_a_quote_from_an_inferred_paragraph_cannot_support():
    rec = Record(
        unit_id="u", pointer="/algorithms/0/pseudocode",
        claim="The tag field starts at bit 4.", verdict="SUPPORTED",
        quote="the box lines up with the row above, so it starts at bit 4",
    )
    verify_evidence([rec], HEDGED_PAPER)
    assert rec.verdict == "UNSUPPORTED"
    assert rec.tier == "inferred"
    assert rec.evidence_ok is False
    assert "INFERRED" in rec.open_question


def test_a_quote_from_an_uncertain_paragraph_cannot_contradict():
    rec = Record(
        unit_id="u", pointer="/algorithms/0/pseudocode",
        claim="The tag field is right-aligned at bit 0.", verdict="CONTRADICTED",
        quote="the field is right-aligned at bit 0",
        patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
               "value": "x"},
    )
    verify_evidence([rec], HEDGED_PAPER)
    assert rec.verdict == "UNSUPPORTED"
    assert rec.patch is None


def test_a_literal_quote_still_supports_but_carries_its_section_caveat():
    """The exact shape that slipped through: a derived column in a LITERAL
    block, retracted by a note further down the same figure section."""
    rec = Record(
        unit_id="u", pointer="/algorithms/0/pseudocode",
        claim="Value[15:8] lands in digest bits [11:4].", verdict="SUPPORTED",
        quote="long    Value[15:8]    [11:4]",
    )
    verify_evidence([rec], HEDGED_PAPER)
    assert rec.verdict == "SUPPORTED"
    assert rec.tier == "literal"
    assert rec.caveats == ["U1"]


def test_ordinary_prose_is_unaffected():
    rec = Record(
        unit_id="u", pointer="/summary", claim="There is a tag per set.",
        verdict="SUPPORTED", quote="The predictor keeps a tag per set.",
    )
    verify_evidence([rec], HEDGED_PAPER)
    assert rec.verdict == "SUPPORTED"
    assert rec.tier == "prose"
    assert rec.caveats is None


def test_cited_ambiguities_are_carried_into_open_questions(spec):
    import paper_markers

    ann = paper_markers.annotate(HEDGED_PAPER)
    rec = Record(
        unit_id="u", pointer="/algorithms/0/pseudocode",
        claim="Value[15:8] lands in digest bits [11:4].", verdict="SUPPORTED",
        quote="long    Value[15:8]    [11:4]",
    )
    verify_evidence([rec], HEDGED_PAPER, ann)
    out = copy.deepcopy(spec)
    assert spec_review.carry_uncertainties(out, [rec], ann) == 1
    carried = [q for q in out["open_questions"] if "source U1" in q]
    assert carried and "right-aligned at bit 0" in carried[0]
    # Idempotent: a second round must not re-append the same note.
    assert spec_review.carry_uncertainties(out, [rec], ann) == 0


def test_an_uncited_ambiguity_is_not_carried(spec):
    import paper_markers

    ann = paper_markers.annotate(HEDGED_PAPER)
    rec = Record(
        unit_id="u", pointer="/summary", claim="There is a tag per set.",
        verdict="SUPPORTED", quote="The predictor keeps a tag per set.",
    )
    verify_evidence([rec], HEDGED_PAPER, ann)
    out = copy.deepcopy(spec)
    assert spec_review.carry_uncertainties(out, [rec], ann) == 0


# ------------------------------------------------- ranking the knob budget


def _unsup(pointer, cands, question=None):
    return Record(unit_id="u", pointer=pointer, claim=f"ambiguity at {pointer}",
                  verdict="UNSUPPORTED", enum_candidates=cands,
                  open_question=question)


def test_a_source_declared_ambiguity_outranks_one_a_reviewer_noticed(spec, monkeypatch):
    monkeypatch.setattr(spec_review.C, "REVIEW_MAX_PROMOTED", 2)
    records = [
        _unsup("/state/0/indexing", ["xor_hash", "folded_hash"]),
        _unsup("/state/1/indexing", ["rotate", "shift"]),
        _unsup("/algorithms/0/pseudocode", ["align_bit_3", "align_bit_0"],
               "Per ambiguity U4, which alignment does the FP slice use?"),
    ]
    out = promote_unsupported(spec, records, {"U4"})
    minted = [p["range"] for p in out["parameters"]
              if str(p.get("origin", "")).startswith("review:")]
    assert "choices: align_bit_3|align_bit_0" in minted
    assert len(minted) == 2


def test_consensus_outranks_arrival_order(spec, monkeypatch):
    monkeypatch.setattr(spec_review.C, "REVIEW_MAX_PROMOTED", 1)
    records = [
        _unsup("/state/0/indexing", ["rotate", "shift"]),
        # Raised three times, once at a pointer no knob can resolve. The
        # unit-test record still counts as a third reviewer agreeing.
        _unsup("/unit_tests/0", ["align_bit_3", "align_bit_0"]),
        _unsup("/algorithms/0/pseudocode", ["align_bit3", "align_bit0"]),
        _unsup("/algorithms/1/pseudocode", ["align_bit_3", "align_bit_0"]),
    ]
    out = promote_unsupported(spec, records)
    minted = [p["range"] for p in out["parameters"]
              if str(p.get("origin", "")).startswith("review:")]
    assert minted == ["choices: align_bit3|align_bit0"]


def test_one_question_at_sibling_pointers_costs_one_slot(spec, monkeypatch):
    monkeypatch.setattr(spec_review.C, "REVIEW_MAX_PROMOTED", 6)
    records = [
        _unsup("/state/0/indexing", ["xor_hash", "folded_hash"]),
        _unsup("/state/1/indexing", ["xor_hash", "folded_hash"]),
        _unsup("/state/2/indexing", ["xor_hash", "folded_hash"]),
        _unsup("/algorithms/0/pseudocode", ["saturate", "wrap"]),
    ]
    out = promote_unsupported(spec, records)
    minted = [p["range"] for p in out["parameters"]
              if str(p.get("origin", "")).startswith("review:")]
    assert sorted(minted) == ["choices: saturate|wrap",
                              "choices: xor_hash|folded_hash"]


def test_every_unsupported_record_still_becomes_an_open_question(spec, monkeypatch):
    """Capping the knobs must not lose the questions they stood for."""
    monkeypatch.setattr(spec_review.C, "REVIEW_MAX_PROMOTED", 0)
    records = [
        _unsup("/algorithms/0/pseudocode", ["a1", "b1"], "first question?"),
        _unsup("/algorithms/1/pseudocode", ["a2", "b2"], "second question?"),
    ]
    out = promote_unsupported(spec, records)
    assert not [p for p in out["parameters"]
                if str(p.get("origin", "")).startswith("review:")]
    joined = " ".join(out["open_questions"])
    assert "first question?" in joined and "second question?" in joined


def test_an_index_overrun_patch_is_inside_the_inconsistent_scope(spec):
    """A deterministic error must not be un-fixable by the verdict for it.

    `index_exceeds_dimension` was missing from the allow-list that bounds
    INCONSISTENT patching, so a reviewer that diagnosed the overrun correctly
    had its patch refused as "a pointer no self-consistency check flagged" --
    by the very check that flagged it. Three rounds of one run were lost that
    way before the stage failed closed with the defect intact.
    """
    assert "index_exceeds_dimension" in spec_review._SELF_CONSISTENCY_CODES

    finding = spec_checks.Finding(
        "/algorithms/0/pseudocode", "index_exceeds_dimension", "error",
        "subscripts the table with an id that overruns its declared dimension",
    )
    rec = Record(
        unit_id="algo:predict", pointer="/algorithms/0/pseudocode",
        claim="predict indexes by absolute id, not intra-group position.",
        verdict="INCONSISTENT",
        why="the declared dimension is 9 but the index reaches 64",
        patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
               "value": "slot = r / 8\nv = victim_tag_table[PC]\nreturn v.tag"},
    )
    units = partition(spec)
    _, rejections = apply_patches(spec, [rec], units, [finding])
    assert rejections == []
    assert rec.rejected is None
