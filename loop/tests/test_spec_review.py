"""Tests for the reviewer stage's pure functions.

No cluster and no LLM: partitioning, evidence verification, patch merging and
the regression differ are all deterministic, which is the point of keeping the
backend import lazy inside review_spec().

As in test_spec_checks, every fixture is an invented feature.
"""

import copy
import json

import pytest

import paper_markers as pm
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


def test_the_global_unit_owns_the_algorithm_append_pointer(spec):
    """A finding about something the spec does not contain yet has no element
    pointer to anchor to -- a unit owns `/algorithms/0`, not the array's next
    slot. Without append scope such a finding reaches no reviewer and can be
    patched by none, so an `error` of that shape deadlocks the stage instead
    of gating it."""
    units = {u.unit_id: u for u in partition(spec)}
    assert units["global"].owns("/algorithms/-")
    assert not units["algo:predict"].owns("/algorithms/-")


def test_a_deterministic_finding_at_the_append_pointer_reaches_a_reviewer(spec):
    import spec_checks
    f = spec_checks.Finding("/algorithms/-", "missing_recovery_algorithm",
                            "error", "speculative state, nothing unwinds it")
    units = {u.unit_id: u for u in partition(spec)}
    assert spec_review._findings_for([f], units["global"]) == [f]


def test_the_global_unit_may_append_the_algorithm_a_finding_asks_for(spec):
    """The repair has to close, not just route: an error the loop can detect
    and cannot clear is worse than no check at all."""
    import spec_checks
    f = spec_checks.Finding("/algorithms/-", "missing_recovery_algorithm",
                            "error", "speculative state, nothing unwinds it")
    r = Record(unit_id="global", pointer="/algorithms/-",
               claim="nothing unwinds the table on a flush",
               verdict="INCONSISTENT", why="w",
               patch={"op": "add", "pointer": "/algorithms/-",
                      "value": {"name": "recover_squash",
                                "trigger": "pipeline flush",
                                "pseudocode": "tbl[r].valid = 0"}})
    new, rejections = apply_patches(spec, [r], partition(spec), [f])
    assert rejections == []
    assert new["algorithms"][-1]["name"] == "recover_squash"


def test_an_append_missing_a_required_field_is_rejected_alone(spec):
    """The observed failure: the global reviewer wrote the recovery algorithm
    the checks were asking for and called its body `logic`. Schema-invalid, so
    the round-level gate threw the round away -- with nine correct patches in
    it -- and the stage stopped at round 0 with the error still standing."""
    import spec_checks
    f = spec_checks.Finding("/algorithms/-", "missing_recovery_algorithm",
                            "error", "speculative state, nothing unwinds it")
    bad = Record(unit_id="global", pointer="/algorithms/-",
                 claim="nothing unwinds the table on a flush",
                 verdict="INCONSISTENT", why="w",
                 patch={"op": "add", "pointer": "/algorithms/-",
                        "value": {"name": "recover_on_flush",
                                  "trigger": "pipeline flush",
                                  "logic": "clear every valid bit"}})
    good = Record(unit_id="algo:predict", pointer="/algorithms/0/pseudocode",
                  claim="the lookup reads the tag field",
                  verdict="UNDERSPECIFIED", why="w",
                  patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                         "value": "v = victim_tag_table[PC]; return v.tag if "
                                  "v.valid else NO_PREDICTION"})
    new, rejections = apply_patches(spec, [bad, good], partition(spec), [f])
    assert len(rejections) == 1
    assert "pseudocode" in rejections[0]["reason"]
    # The correct patch beside it survives, which is the whole point.
    assert "NO_PREDICTION" in new["algorithms"][0]["pseudocode"]
    assert [a["name"] for a in new["algorithms"]] == ["predict", "decay"]


def test_an_append_that_is_not_an_object_is_rejected(spec):
    r = Record(unit_id="global", pointer="/algorithms/-", claim="c",
               verdict="UNDERSPECIFIED", why="w",
               patch={"op": "add", "pointer": "/algorithms/-",
                      "value": "recover the table on a flush"})
    new, rejections = apply_patches(spec, [r], partition(spec))
    assert len(rejections) == 1
    assert len(new["algorithms"]) == 2


def test_open_questions_append_is_untyped_and_still_lands(spec):
    """`/open_questions/-` holds bare strings, so a required-field check that
    assumed every append is an object would refuse the append the coverage
    reviewer makes for every ambiguity the paper leaves open."""
    spec["open_questions"] = []
    r = Record(unit_id="coverage", pointer="/open_questions/-", claim="c",
               verdict="UNDERSPECIFIED", why="w", evidence_ok=True,
               patch={"op": "add", "pointer": "/open_questions/-",
                      "value": "Does the table survive a flush?"})
    new, rejections = apply_patches(spec, [r], partition(spec))
    assert rejections == []
    assert new["open_questions"][-1] == "Does the table survive a flush?"


def test_a_schema_breaking_patch_does_not_cost_the_round_its_other_patches(spec):
    """The general case, below the per-append shape check: any patch that
    leaves the document unparseable as a spec is dropped on its own."""
    bad = Record(unit_id="algo:predict", pointer="/algorithms/0/pseudocode",
                 claim="c", verdict="UNDERSPECIFIED", why="w",
                 patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
                        "value": {"not": "a string"}})
    good = Record(unit_id="global", pointer="/algorithms/-", claim="c",
                  verdict="UNDERSPECIFIED", why="w",
                  patch={"op": "add", "pointer": "/algorithms/-",
                         "value": {"name": "recover_squash",
                                   "trigger": "pipeline flush",
                                   "pseudocode": "tbl[r].valid = 0"}})
    new, rejections = apply_patches(spec, [bad, good], partition(spec))
    assert [r["pointer"] for r in rejections] == ["/algorithms/0/pseudocode"]
    assert new["algorithms"][-1]["name"] == "recover_squash"
    assert spec_review._schema_errors(new) == []


def test_a_laundering_patch_does_not_cost_the_round_its_other_patches(spec):
    """The other half of the observed failure: a correct, paper-backed
    rewrite of /state/1 that cut `indexing` down to a stub in passing. The
    loss is real and must not land -- but it is attributable to one patch,
    and the round-level verdict blamed all ten."""
    launders = Record(
        unit_id="algo:decay", pointer="/state/1", claim="c",
        verdict="CONTRADICTED", why="w", evidence_ok=True,
        patch={"op": "replace", "pointer": "/state/1",
               "value": {"name": "decay shadow counters",
                         "organization": "8 counters",
                         "entry_format": "decay_ctr (8)",
                         "size_bits": 64,
                         "indexing": "bank"}})
    good = Record(unit_id="global", pointer="/algorithms/-", claim="c",
                  verdict="UNDERSPECIFIED", why="w",
                  patch={"op": "add", "pointer": "/algorithms/-",
                         "value": {"name": "recover_squash",
                                   "trigger": "pipeline flush",
                                   "pseudocode": "tbl[r].valid = 0"}})
    spec["state"][1]["indexing"] = (
        "indexed by the bank number and the logical register index, with the "
        "low bit of the PC breaking ties"
    )
    new, rejections = apply_patches(spec, [launders, good], partition(spec))
    assert [r["pointer"] for r in rejections] == ["/state/1"]
    # The loss is reverted...
    assert new["state"][1]["indexing"].startswith("indexed by the bank number")
    # ...and the unrelated patch beside it still lands.
    assert new["algorithms"][-1]["name"] == "recover_squash"
    assert spec_review.uncovered_regressions(spec, new, [launders, good]) == []


def test_append_required_fields_are_read_from_the_schema():
    """Restating them here would let the schema rename a field without this
    check or the reviewer prompt noticing."""
    assert spec_review._append_required("/algorithms/-") == [
        "name", "trigger", "pseudocode"]
    assert spec_review._append_required("/open_questions/-") == []


def test_an_algorithm_unit_may_mint_the_knob_its_pseudocode_should_read(spec):
    """`hardcoded_tuning_constant` asks for two edits in one round: the knob
    added and the pseudocode changed to read it. They sit in different
    top-level arrays, and a round's patches land as a set -- without append
    scope the reviewer can only ever propose half, and half is a regression."""
    unit = {u.unit_id: u for u in partition(spec)}["algo:predict"]
    assert unit.owns("/parameters/-")
    assert unit.owns("/algorithms/0/pseudocode")


def test_merging_units_keeps_append_scope(spec):
    """The cap merges units; a merged unit that dropped its append scope
    would put the finding back out of everyone's reach."""
    a = spec_review.ReviewUnit("a", "global", [], ["/algorithms/-"])
    b = spec_review.ReviewUnit("b", "algorithm", [])
    assert spec_review._merge_units(a, b).owns("/algorithms/-")
    assert spec_review._merge_units(b, a).owns("/algorithms/-")


def test_partition_merges_algorithms_that_write_the_same_state(spec):
    """A repair to a shared field spans every writer of it, and the gate
    applies a round's patches as one set -- so the writers have to be in one
    reviewer's hands or only part of the repair can ever be proposed."""
    spec["algorithms"] += [
        {"name": "fill", "trigger": "miss",
         "pseudocode": "victim_tag_table[PC].tag = t"},
        {"name": "evict", "trigger": "evict",
         "pseudocode": "victim_tag_table[PC].tag = 0"},
    ]
    unit = next(u for u in partition(spec) if u.owns("/algorithms/2"))
    assert unit.owns("/algorithms/3")
    assert unit.unit_id == "algo:fill+algo:evict"


def test_partition_does_not_merge_on_a_shared_word(spec):
    """Token overlap is right for attaching context and wrong for merging:
    'weight tables' and 'usefulness tables' share a word, not a field."""
    spec["state"] = [
        {"name": "sr weight tables", "organization": "8", "entry_format": "w (6)",
         "size_bits": 48, "indexing": "PC"},
        {"name": "sr usefulness tables", "organization": "8", "entry_format": "u (6)",
         "size_bits": 48, "indexing": "PC"},
    ]
    spec["algorithms"] = [
        {"name": "train_w", "trigger": "update", "pseudocode": "sr_weight_tables[b] += 1"},
        {"name": "train_u", "trigger": "update",
         "pseudocode": "sr_usefulness_tables[b] += 1"},
    ]
    ids = {u.unit_id for u in partition(spec)}
    assert {"algo:train_w", "algo:train_u"} <= ids


def test_a_read_is_not_a_write(spec):
    """Every algorithm reads the shared tables; merging on reads would put
    the whole spec in one unit and defeat the partition."""
    spec["algorithms"].append(
        {"name": "peek", "trigger": "debug", "pseudocode": "x = victim_tag_table[PC]"}
    )
    ids = {u.unit_id for u in partition(spec)}
    assert "algo:peek" in ids


def test_merged_unit_carries_each_pointer_once(spec):
    spec["algorithms"] += [
        {"name": "fill", "trigger": "miss",
         "pseudocode": "victim_tag_table[PC].tag = t  # of decay_window"},
        {"name": "evict", "trigger": "evict",
         "pseudocode": "victim_tag_table[PC].tag = 0  # of decay_window"},
    ]
    unit = next(u for u in partition(spec) if u.owns("/algorithms/2"))
    assert len(unit.prefixes) == len(set(unit.prefixes))


# ------------------------------------------------------- coupled ranges


@pytest.fixture
def tunable(spec):
    """A spec whose decay_window knob is referenced, so a unit owns it."""
    spec["algorithms"][1]["pseudocode"] = "decay_shadow[bank] -= 1  # decay_window"
    return spec


def couple(spec, default):
    findings = spec_checks.run_checks(spec)
    r = rec(unit_id=next(u.unit_id for u in partition(spec) if u.owns("/parameters/0")),
            pointer="/parameters/0/default", verdict="CONTRADICTED",
            quote="Each decay counter is decremented once per cycle",
            patch={"op": "replace", "pointer": "/parameters/0/default",
                   "value": default})
    verify_evidence([r], PAPER)
    return apply_patches(spec, [r], partition(spec), findings)


def test_a_landed_default_widens_the_range_it_outgrew(tunable):
    """The range is the DSE's search space, not a claim from the paper. No
    verdict lets a reviewer patch it, so the pipeline moves its own bound."""
    new, rejections = couple(tunable, 256)
    assert not rejections
    assert new["parameters"][0]["default"] == 256
    assert new["parameters"][0]["range"] == "[1, 256]"


def test_a_default_the_hardware_cannot_hold_is_still_refused(tunable):
    """Widening admits a value the state field can store. 512 steps do not
    fit an 8-bit counter however the search space is written."""
    new, rejections = couple(tunable, 512)
    assert new["parameters"][0]["default"] == 200
    assert new["parameters"][0]["range"] == "[1, 255]"
    assert rejections and "did not have before this round" in rejections[0]["reason"]


def test_coupling_does_not_clear_an_inherited_range_error(tunable):
    """A contradiction the round did not cause is not the round's to erase:
    silently widening it would hide a defect the gate is there to fail on."""
    tunable["parameters"][0]["range"] = "[1, 100]"
    findings = spec_checks.run_checks(tunable)
    assert any(f.code == "param_range" for f in findings)
    r = rec(unit_id=next(u.unit_id for u in partition(tunable)
                         if u.owns("/state/0")),
            verdict="CONTRADICTED", quote="holds 256 entries of 12 bits each",
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 3072})
    verify_evidence([r], PAPER)
    new, _ = apply_patches(tunable, [r], partition(tunable), findings)
    assert new["parameters"][0]["range"] == "[1, 100]"


def test_coupling_keeps_the_range_modifier(tunable):
    tunable["parameters"][0].update(default=64, range="[1, 64] pow2")
    new, _ = couple(tunable, 128)
    assert new["parameters"][0]["range"] == "[1, 128] pow2"


# ------------------------------------------------------ rejection feedback


def test_rejection_feedback_carries_the_refusing_check(spec):
    unit = next(u for u in partition(spec) if u.owns("/parameters/0"))
    section = spec_review._render_rejections([{
        "unit": unit.unit_id, "pointer": "/parameters/0/default",
        "verdict": "CONTRADICTED", "value": "256",
        "reason": "patch introduced param_range at /parameters/0/default, which "
                  "the spec did not have before this round",
        "detail": "default 256 lies outside range [1, 255].",
    }], unit)
    assert "/parameters/0/default" in section
    assert "default 256 lies outside range [1, 255]." in section
    assert "EVERY edit the repair needs" in section


def test_rejection_feedback_is_scoped_to_the_unit(spec):
    elsewhere = [{"unit": "algo:decay", "pointer": "/algorithms/1/pseudocode",
                  "verdict": "CONTRADICTED", "value": "x", "reason": "r"}]
    unit = {u.unit_id: u for u in partition(spec)}["algo:predict"]
    assert spec_review._render_rejections(elsewhere, unit) == ""


def test_a_rejection_with_no_patch_value_is_not_fed_back(spec):
    """Parse failures and duplicate appends are noise, not lessons."""
    unit = {u.unit_id: u for u in partition(spec)}["algo:predict"]
    assert spec_review._render_rejections(
        [{"unit": "algo:predict", "pointer": "/algorithms/0/pseudocode",
          "verdict": "CONTRADICTED", "value": None, "reason": "r"}], unit
    ) == ""


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
    assert new["algorithms"][1]["pseudocode"] == spec["algorithms"][1]["pseudocode"]
    assert "outside the unit's scope" in rejections[0]["reason"]


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


def test_refused_contradiction_survives_as_an_open_question(spec):
    """The quote is the strongest evidence this stage has. Losing the patch
    must not lose the finding."""
    r = rec(unit_id="algo:predict", verdict="CONTRADICTED",
            claim="The table holds 256 entries, not 4.",
            quote="holds 256 entries of 12 bits each",
            patch={"op": "replace", "pointer": "/algorithms/1/pseudocode", "value": "x"})
    verify_evidence([r], PAPER)
    new, _ = apply_patches(spec, [r], units_for(spec))
    q = "\n".join(new["open_questions"])
    assert "The table holds 256 entries, not 4." in q
    assert "holds 256 entries of 12 bits each" in q
    assert "[/algorithms/1/pseudocode]" in q
    assert "still says what it said" in q
    # Which internal gate rejected the patch is this loop talking to itself.
    # Integration agents read this list.
    assert "refused by code" not in q


def test_a_fabricated_contradiction_is_not_escalated(spec):
    """Escalation rides on verified evidence, or it becomes a channel for
    writing unsourced claims into the spec the patch gate just refused."""
    r = rec(unit_id="algo:predict", verdict="CONTRADICTED",
            quote="the table is flushed on every context switch",
            patch={"op": "replace", "pointer": "/algorithms/1/pseudocode", "value": "x"})
    verify_evidence([r], PAPER)
    new, _ = apply_patches(spec, [r], units_for(spec))
    assert not any("Unrepaired contradiction" in q
                   for q in new.get("open_questions", []))


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


# ------------------------------------- one decision, one knob


def test_a_question_naming_an_existing_knob_does_not_mint_a_second(spec):
    """Two knobs for one decision is worse than no knob: stage 4 sweeps both
    and the winner states the decision twice, in two ways, with nothing
    making them agree."""
    r = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
            claim="c",
            open_question="What decay window should the counters use?",
            enum_candidates=["short", "long"])
    out = promote_unsupported(spec, [r])
    assert [p for p in out["parameters"]
            if str(p.get("origin", "")).startswith("review:")] == []
    # The information is kept, and it says where the decision already lives.
    assert any("decay_window" in q for q in out["open_questions"])


def test_a_question_sharing_one_generic_word_still_mints(spec):
    """`decay_window` is two tokens and a question naming only one of them
    is a different question. Refusing on a single word loses real
    dimensions -- it cost `stride_by_8|contiguous` its slot in testing."""
    r = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
            claim="c",
            open_question="Does decay run every cycle or every commit?",
            enum_candidates=["per_cycle", "per_commit"])
    out = promote_unsupported(spec, [r])
    assert [p for p in out["parameters"]
            if str(p.get("origin", "")).startswith("review:")]


def test_a_reviewer_filing_the_same_hole_at_a_parameter_blocks_the_mint(spec):
    """Run 7's escape. One reviewer asks at `/parameters/N`, correctly
    refused because an ambiguity about a knob belongs in its range; another
    asks the same thing in different words at an algorithm, and a second
    knob is minted for the decision the first one already carries."""
    at_param = rec(verdict="UNSUPPORTED", pointer="/parameters/0/default",
                   claim="c",
                   open_question="What is the exact decay window value?")
    at_algo = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                  claim="c",
                  open_question="Does the decay counter reach zero before or "
                                "after the window?",
                  enum_candidates=["before", "after"])
    out = promote_unsupported(spec, [at_param, at_algo])
    assert [p for p in out["parameters"]
            if str(p.get("origin", "")).startswith("review:")] == []


def test_a_parameter_filing_about_something_else_does_not_block(spec):
    """The two questions must name the whole knob between them. Sharing one
    word with a one-token knob name is how the guard refused a real
    dimension the first time it was written."""
    at_param = rec(verdict="UNSUPPORTED", pointer="/parameters/0/default",
                   claim="c",
                   open_question="Is the decay window 200 or 255?")
    at_algo = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                  claim="c",
                  open_question="How is the victim tag hashed into the table?",
                  enum_candidates=["xor_fold", "low_bits"])
    out = promote_unsupported(spec, [at_param, at_algo])
    assert [p for p in out["parameters"]
            if str(p.get("origin", "")).startswith("review:")]


def test_a_minted_knob_carries_its_question_for_the_next_round(spec):
    """Candidate values are not an identity: two reviewers rarely spell one
    fork the same way twice, so `_candidate_key` alone lets the same
    ambiguity through as a second dimension a round later."""
    first = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                claim="c",
                open_question="Is the victim tag hashed by an XOR fold of the "
                              "PC bits or taken from the low PC bits?",
                enum_candidates=["xor_fold", "low_bits"])
    after = promote_unsupported(spec, [first])
    knob = [p for p in after["parameters"]
            if str(p.get("origin", "")).startswith("review:")][0]
    assert "XOR fold" in knob["question"]

    second = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                 claim="c",
                 open_question="Is the victim tag hashed by an XOR fold of the "
                               "PC bits, or simply the low PC bits taken raw?",
                 enum_candidates=["fold_xor", "raw_low_bits"])
    out = promote_unsupported(after, [second])
    assert len([p for p in out["parameters"]
                if str(p.get("origin", "")).startswith("review:")]) == 1


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
    # Both hedged notes in the section attach, the inference included: the
    # quote is verbatim, but what the section concludes from it is not.
    assert rec.caveats == ["I1", "U1"]


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
    assert spec_review.carry_source_notes(out, [rec], ann) == 1
    carried = [q for q in out["open_questions"] if "source U1" in q]
    assert carried and "right-aligned at bit 0" in carried[0]
    # Idempotent: a second round must not re-append the same note.
    assert spec_review.carry_source_notes(out, [rec], ann) == 0


# A figure section that infers something and never flags it as unsettled --
# the common case, and the one that used to leave no trace at all.
INFERRED_ONLY_PAPER = """The predictor keeps a tag per set.

[Figure 4: Digest construction.

--- (a) INT registers -----------------------------------------------------

LITERAL. Three bars labelled Value[5:0], lead[8:3], trail[5:0].

INFERRED - the bars overlap and are combined with "+", so the three fields
are XORed together rather than concatenated.
]

Unrelated closing prose.
"""


def test_an_inference_is_carried_as_an_assumption(spec):
    """No UNCERTAIN note to ride on, and the spec still has to admit it.

    This is the gap the tier existed without closing. `verify_evidence`
    already refused a direct quote of the inference, so a reviewer could not
    cite it -- but a reviewer citing the LITERAL bars above it landed a claim
    that silently depends on the inference, and nothing recorded that.
    """
    import paper_markers

    ann = paper_markers.annotate(INFERRED_ONLY_PAPER)
    rec = Record(
        unit_id="u", pointer="/algorithms/0/pseudocode",
        claim="The digest combines three fields.", verdict="SUPPORTED",
        quote="Three bars labelled Value[5:0], lead[8:3], trail[5:0].",
    )
    verify_evidence([rec], INFERRED_ONLY_PAPER, ann)
    assert rec.verdict == "SUPPORTED"      # the bars really are transcribed
    assert rec.caveats == ["I1"]
    out = copy.deepcopy(spec)
    assert spec_review.carry_source_notes(out, [rec], ann) == 1
    carried = [q for q in out["open_questions"] if "source I1" in q]
    assert carried and "XORed together" in carried[0]
    # Stated as an assumption, not as a point the source refuses to resolve.
    assert "INFERRED" in carried[0] and "assumption and not a fact" in carried[0]
    assert spec_review.carry_source_notes(out, [rec], ann) == 0


def test_an_uncited_ambiguity_is_not_carried(spec):
    import paper_markers

    ann = paper_markers.annotate(HEDGED_PAPER)
    rec = Record(
        unit_id="u", pointer="/summary", claim="There is a tag per set.",
        verdict="SUPPORTED", quote="The predictor keeps a tag per set.",
    )
    verify_evidence([rec], HEDGED_PAPER, ann)
    out = copy.deepcopy(spec)
    assert spec_review.carry_source_notes(out, [rec], ann) == 0


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


def test_a_sibling_field_is_inside_the_inconsistent_scope(spec):
    """A check names where it *detected* the contradiction, not the only
    place to *fix* it.

    `param_range` compares a default against a range and reports
    /parameters/0/default, but "default 256 outside [64, 255]" is a
    disagreement between two siblings: widening the range settles it as well
    as lowering the default, and only a reviewer holding the parameter can
    say which side is wrong. Scoping to the flagged leaf refused the range
    patch as "a pointer no self-consistency check flagged", so the one repair
    the paper supports had nowhere to land.
    """
    s = copy.deepcopy(spec)
    s["parameters"][0] = {
        "name": "decay_window", "type": "int", "default": 256,
        "range": "[64, 255] pow2", "storage_impact": "none",
    }
    findings = spec_checks.run_checks(s)
    flagged = [f for f in findings if f.code == "param_range"]
    assert [f.pointer for f in flagged] == ["/parameters/0/default"]

    unit = next(u for u in partition(s) if u.owns("/parameters/0"))
    r = rec(unit_id=unit.unit_id, pointer="/parameters/0/range",
            verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/parameters/0/range",
                   "value": "[64, 256] pow2"})
    new, rejections = apply_patches(s, [r], partition(s), findings)

    assert rejections == [] and r.rejected is None
    assert new["parameters"][0]["range"] == "[64, 256] pow2"
    assert not [f for f in spec_checks.run_checks(new)
                if f.code == "param_range"]


def test_the_inconsistent_scope_does_not_widen_past_an_object(spec):
    """One finding must not put every sibling entry, or the whole spec, in
    reach of a quote-free patch.

    Widening to the enclosing object is what makes the sibling repair above
    possible; widening past it would hand a reviewer that found one bad
    counter the right to rewrite every other one on the same authority.
    """
    # Parent is a list: the other state entries stay out of scope.
    entry = spec_checks.Finding(
        "/state/1", "storage_sum", "error", "sizes do not add up")
    r = rec(unit_id="algo:predict", pointer="/state/0/size_bits",
            verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/state/0/size_bits",
                   "value": 1})
    _, rejections = apply_patches(spec, [r], partition(spec), [entry])
    assert rejections and "no self-consistency check" in rejections[0]["reason"]

    # Parent is the document root: nothing else joins the scope either.
    top = spec_checks.Finding(
        "/summary", "storage_sum", "error", "sizes do not add up")
    r = rec(unit_id="algo:predict", pointer="/state/0/size_bits",
            verdict="INCONSISTENT", quote=None,
            patch={"op": "replace", "pointer": "/state/0/size_bits",
                   "value": 1})
    _, rejections = apply_patches(spec, [r], partition(spec), [top])
    assert rejections and "no self-consistency check" in rejections[0]["reason"]


# -------------------------------- a patch that trades one error for another


def test_a_patch_that_introduces_an_error_is_dropped_not_the_round(spec):
    """The fixes in a round must survive the regression beside them.

    One observed round landed the correct widening of /parameters/0's range
    and, from another reviewer, a cut of total_storage_bits to the figure the
    paper's table prints -- correct about the paper, but the spec also
    declares checkpoint state that figure excludes. Errors went 1 -> 1, so the
    round was rejected wholesale and the run failed closed carrying the very
    contradiction three reviewers had just fixed.
    """
    s = copy.deepcopy(spec)
    s["parameters"][0]["default"] = 256            # param_range, 1 error

    findings = spec_checks.run_checks(s)
    assert [f.code for f in findings if f.severity == "error"] == ["param_range"]

    fix = rec(unit_id=next(u.unit_id for u in partition(s)
                           if u.owns("/parameters/0")),
              pointer="/parameters/0/range", verdict="INCONSISTENT", quote=None,
              patch={"op": "replace", "pointer": "/parameters/0/range",
                     "value": "[1, 256]"})
    regress = rec(unit_id="global", pointer="/resource_accounting/total_storage_bits",
                  verdict="CONTRADICTED", quote="q", evidence_ok=True,
                  patch={"op": "replace",
                         "pointer": "/resource_accounting/total_storage_bits",
                         "value": 1})

    new, rejections = apply_patches(
        s, [fix, regress], partition(s), findings)

    assert fix.rejected is None
    assert new["parameters"][0]["range"] == "[1, 256]"
    assert new["resource_accounting"]["total_storage_bits"] == \
        s["resource_accounting"]["total_storage_bits"]
    assert [r["pointer"] for r in rejections] == \
        ["/resource_accounting/total_storage_bits"]
    assert "introduced storage_sum" in rejections[0]["reason"]
    assert not [f for f in spec_checks.run_checks(new) if f.severity == "error"]


def test_the_whole_object_goes_when_one_of_its_fields_regresses(spec):
    """A total and the breakdown explaining it are one statement in two
    fields. Dropping only the field a check happens to name would leave the
    other still asserting the number just rejected."""
    s = copy.deepcopy(spec)
    findings = spec_checks.run_checks(s)

    total = rec(unit_id="global", pointer="/resource_accounting/total_storage_bits",
                verdict="CONTRADICTED", quote="q", evidence_ok=True,
                patch={"op": "replace",
                       "pointer": "/resource_accounting/total_storage_bits",
                       "value": 1})
    breakdown = rec(unit_id="global", pointer="/resource_accounting/storage_breakdown",
                    verdict="CONTRADICTED", quote="q", evidence_ok=True,
                    patch={"op": "add",
                           "pointer": "/resource_accounting/storage_breakdown",
                           "value": "everything accounts to 1 bit"})

    new, rejections = apply_patches(s, [total, breakdown], partition(s), findings)

    assert {r["pointer"] for r in rejections} == {
        "/resource_accounting/total_storage_bits",
        "/resource_accounting/storage_breakdown",
    }
    assert "storage_breakdown" not in new["resource_accounting"]


def test_an_unattributable_regression_is_left_to_the_round_gate(spec):
    """Dropping has to earn it. A patch the enclosing-object rule cannot tie
    to the new error stands, and `is_worse` rejects the round instead -- a
    half-repaired round is worse than a visibly rejected one."""
    s = copy.deepcopy(spec)
    findings = spec_checks.run_checks(s)

    # Shrinking a state entry breaks the total, which lives elsewhere.
    r = rec(unit_id="algo:predict", pointer="/state/0/size_bits",
            verdict="CONTRADICTED", quote="q", evidence_ok=True,
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 8})

    new, rejections = apply_patches(s, [r], partition(s), findings)

    assert rejections == [] and new["state"][0]["size_bits"] == 8
    assert spec_checks.is_worse(findings, spec_checks.run_checks(new))


# ----------------------------------- ranking a capped knob budget by evidence


def test_a_corroborated_ambiguity_outranks_an_uncorroborated_one(spec, monkeypatch):
    """A check that found the hole unasked is evidence the ambiguity matters.

    The sR run spent all six slots on decay bookkeeping and a tie-break rule
    while `update`'s invented usefulness-training rule got none -- and
    `_check_carried_state` had already flagged that very element for reading
    digests nothing produces. On an unmarked source the `declared` key is
    uniformly false, so without this the rank collapses to a bare consensus
    count and arrival order decides.
    """
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    quiet = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                claim="tie-break", open_question="how are ties broken?",
                enum_candidates=["first", "lowest"])
    flagged = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                  claim="training rule", open_question="what trains the UT?",
                  enum_candidates=["agreement", "always"])
    findings = [spec_checks.Finding("/algorithms/1/pseudocode",
                                    "unproduced_context", "warn", "m")]

    out = promote_unsupported(spec, [quiet, flagged], None, findings)
    knobs = [p for p in out["parameters"] if p["type"] == "enum"]
    assert [k["resolves"] for k in knobs] == ["/algorithms/1/pseudocode"]
    # The loser is deferred, not dropped.
    assert len(out["open_questions"]) == 2

    # Without the findings the order is the arrival order again.
    plain = promote_unsupported(spec, [quiet, flagged])
    assert [p["resolves"] for p in plain["parameters"]
            if p["type"] == "enum"] == ["/algorithms/0/pseudocode"]


def test_info_findings_do_not_rank(spec, monkeypatch):
    """`info` informs a reviewer; letting it rank puts the loosest parser
    in charge of a budget."""
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    first = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                claim="a", open_question="qa", enum_candidates=["x", "y"])
    second = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                 claim="b", open_question="qb", enum_candidates=["p", "q"])
    findings = [spec_checks.Finding("/algorithms/1/pseudocode",
                                    "undefined_helper", "info", "m")]
    out = promote_unsupported(spec, [first, second], None, findings)
    assert [p["resolves"] for p in out["parameters"]
            if p["type"] == "enum"] == ["/algorithms/0/pseudocode"]


def test_declared_ambiguity_still_outranks_corroboration(spec, monkeypatch):
    """A source that refuses to resolve a point is the strongest evidence."""
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    declared = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                   claim="alignment", open_question="U1 leaves alignment open",
                   enum_candidates=["right", "left"])
    corroborated = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                       claim="other", open_question="qb",
                       enum_candidates=["p", "q"])
    findings = [spec_checks.Finding("/algorithms/1/pseudocode",
                                    "unproduced_context", "warn", "m")]
    out = promote_unsupported(spec, [declared, corroborated], {"U1"}, findings)
    assert [p["resolves"] for p in out["parameters"]
            if p["type"] == "enum"] == ["/algorithms/0/pseudocode"]


def test_a_refused_question_outranks_an_unnoticed_one(spec, monkeypatch):
    """Both tiers are declared ambiguities; they are not worth the same slot.

    An UNCERTAIN note names the fork and declines to pick. An INFERRED one
    picked already and only admits where the pick came from, so it is the
    weaker claim on a budget both are competing for.
    """
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    refused = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                  claim="alignment", open_question="U1 leaves alignment open",
                  enum_candidates=["right", "left"])
    inferred = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                   claim="fold", open_question="I1 reads the bars as XORed",
                   enum_candidates=["xor", "concat"])
    out = promote_unsupported(spec, [inferred, refused], {"U1", "I1"}, None)
    assert [p["resolves"] for p in out["parameters"]
            if p["type"] == "enum"] == ["/algorithms/0/pseudocode"]


def test_an_inference_still_outranks_an_ambiguity_nobody_declared(spec,
                                                                  monkeypatch):
    import constants as C
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    inferred = rec(verdict="UNSUPPORTED", pointer="/algorithms/0/pseudocode",
                   claim="fold", open_question="I1 reads the bars as XORed",
                   enum_candidates=["xor", "concat"])
    noticed = rec(verdict="UNSUPPORTED", pointer="/algorithms/1/pseudocode",
                  claim="other", open_question="a reviewer wondered",
                  enum_candidates=["p", "q"])
    out = promote_unsupported(spec, [noticed, inferred], {"U1", "I1"}, None)
    assert [p["resolves"] for p in out["parameters"]
            if p["type"] == "enum"] == ["/algorithms/0/pseudocode"]


# ------------------------------------- what is not a claim about the paper


def test_a_parameter_range_is_marked_as_this_pipeline_s_invention(spec):
    """The distiller is told to invent a range for every knob.

    Rendered as bare JSON, `"range": "[4, 8]"` is indistinguishable from a
    transcribed fact, and reviewers spent a third of the sR round arguing that
    the paper does not state it -- which is true of every range in the
    document.
    """
    units = {u.unit_id: u for u in partition(spec)}
    rendered = [spec_review._render_unit(u) for u in units.values()]
    param_views = [r for r in rendered if '"range"' in r]
    assert param_views, "no unit carried a parameter"
    for view in param_views:
        assert "_not_paper_claims" in view
        assert "not the paper" in view


def test_non_parameter_elements_are_not_annotated(spec):
    element = {"pointer": "/state/0", "value": spec["state"][0]}
    assert spec_review._annotate_invented(element) == element


# ------------------------- a bad citation for a claim the paper does state

GRADED_PAPER = (
    "The predictor corrects the base prediction.\n\n"
    "[Figure 4: the register component.\n\n"
    "LITERAL\n"
    "    Weight tables: 512 ent. WT0, 256 ent. WT1.\n"
    "    Output multiplier: x0 or x2.5.\n\n"
    "UNCERTAIN\n"
    "    What switches the multiplier is not stated; the figure draws no\n"
    "    control line and names no threshold.\n]\n"
)


def test_a_misquoted_claim_the_source_prints_raises_no_open_question():
    """The live bug, and a reviewer failure rather than a spec failure. The
    quote is rejected -- a citation nobody can find must never carry a patch
    -- but the claim was written into open_questions anyway, so the spec
    shipped six questions the paper had already answered, each phrased as
    the paper's silence rather than the reviewer's slip."""
    r = rec(claim="The default multiplier is 2.5.",
            quote="the multiplier is set to two and a half",
            patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 1})
    verify_evidence([r], GRADED_PAPER)
    assert r.verdict == "UNSUPPORTED"
    assert r.patch is None                     # the bad citation still disarms
    assert r.open_question is None             # but there is nothing open
    assert "only the citation is bad" in r.rejected


def test_a_misquoted_claim_the_source_does_not_print_still_opens_one():
    r = rec(claim="The default multiplier is 9.75.",
            quote="the multiplier is set to nine and three quarters")
    verify_evidence([r], GRADED_PAPER)
    assert r.verdict == "UNSUPPORTED"
    assert r.open_question and "9.75" in r.open_question


def test_a_hedged_quote_still_opens_a_question_even_if_numbers_match():
    """A reviewer who quoted accurately from an UNCERTAIN paragraph has found
    a real gap. Corroboration must not reach that branch and close it: the
    numbers in the claim are printed two lines above, in LITERAL."""
    r = rec(claim="The multiplier is gated at 2.5 when usefulness is 0.",
            quote="What switches the multiplier is not stated")
    verify_evidence([r], GRADED_PAPER)
    assert r.verdict == "UNSUPPORTED"
    assert r.tier == pm.UNCERTAIN
    assert r.open_question


def test_a_reviewer_authored_open_question_is_never_discarded():
    r = rec(claim="The default multiplier is 2.5.",
            quote="fabricated",
            open_question="Does the multiplier apply per bank or once?")
    verify_evidence([r], GRADED_PAPER)
    assert r.open_question == "Does the multiplier apply per bank or once?"


# --------------------------------------------- pruning the question list


def _oq(spec, *questions):
    spec["open_questions"] = list(questions)
    return spec


def test_a_question_quoting_a_value_the_spec_no_longer_holds_is_dropped(spec):
    """Run 6 carried "the expected value 0xBEC" against a unit test that had
    already been repaired to 0x0BDC. The repair landed and nobody withdrew
    the question, which is how the list grows while the spec improves."""
    spec["unit_tests"] = [{"name": "t", "given": "an INT register completes",
                           "expect": "the digest is 0x0BDC"}]
    _oq(spec, "[/unit_tests/0/expect] The expected value 0xBEC assumes the "
              "overlapping XOR layout. Is it correct?")
    assert spec_review.prune_open_questions(spec)["stale"] == 1
    assert spec["open_questions"] == []


def test_a_question_quoting_a_value_the_spec_still_holds_is_kept(spec):
    spec["unit_tests"] = [{"name": "t", "given": "an INT register completes",
                           "expect": "the digest is 0x0BDC"}]
    _oq(spec, "[/unit_tests/0/expect] Does 0x0BDC assume the XOR layout?")
    assert spec_review.prune_open_questions(spec)["stale"] == 0


def test_a_short_hex_argument_is_not_a_citation(spec):
    """One source note explains that "a 64-bit register yields a count of 64
    for 0x0". Reading that as a quotation of the spec withdrew a hedge the
    paper never resolved."""
    _oq(spec, "A 64-bit register yields a count of 64 for 0x0, which needs "
              "seven bits. Saturate or mask?")
    assert spec_review.prune_open_questions(spec)["stale"] == 0


def test_a_question_contradicting_a_declared_default_is_dropped(spec):
    """Run 6's OQ6 said the defaults set wt0_entries to 128. They were 512,
    matching the figure -- the discrepancy had been repaired and the
    question was not withdrawn."""
    spec["parameters"] = [{"name": "wt0_entries", "type": "int",
                           "default": 512, "range": "[64, 1024] pow2",
                           "storage_impact": "scales WT0"}]
    _oq(spec, "WT sizes: Figure 5(c) says 512 for WT0, but the parameter "
              "defaults set wt0_entries to 128.")
    out = spec_review.prune_open_questions(spec)
    assert out["stale"] == 1 and spec["open_questions"] == []


def test_the_same_question_at_two_pointers_becomes_one(spec):
    """`_append_open_question` dedups within a pointer only, so one
    ambiguity raised against two algorithms survives as two entries."""
    _oq(spec,
        "[/algorithms/0/pseudocode] How is the PC skewed for UT indexing?",
        "[/algorithms/1/pseudocode] How is the PC skewed for UT indexing?")
    out = spec_review.prune_open_questions(spec)
    assert out["merged"] == 1 and len(spec["open_questions"]) == 1
    # Both places it was raised survive on the entry that remains.
    kept = spec["open_questions"][0]
    assert kept.startswith("[/algorithms/0/pseudocode]")
    assert "/algorithms/1/pseudocode" in kept


def test_two_questions_about_one_subject_collapse_onto_the_fuller_one(spec):
    """Rare-word overlap, not prose overlap. The head is the longest member
    because a carried source note states the ambiguity, quotes the paper and
    records the duty not to resolve it; the re-ask states only the
    ambiguity."""
    _oq(spec,
        "U5: How is FP format classified? Assumed all treated as FP64.",
        "[/algorithms/0/pseudocode] How is the floating-point format "
        "classified dynamically? By treating all as FP64, using NaN boxing, "
        "or relying on an external opcode width?")
    spec_review.prune_open_questions(spec)
    assert len(spec["open_questions"]) == 1
    assert "NaN boxing" in spec["open_questions"][0]


def test_two_questions_on_different_subjects_both_survive(spec):
    """The bar is set for precision. A surviving duplicate costs a reviewer
    a second read; a wrongly merged pair loses a question for good."""
    _oq(spec,
        "[/algorithms/1/pseudocode] How should the usefulness table entries "
        "be updated?",
        "[/host_interfaces/0] The paper defers recovery, stating that "
        "recovering the Tomasulo-like table may present some challenges. "
        "Should a squash use the ROB index for precise invalidation, flush "
        "all uncommitted entries, or take no action?")
    spec_review.prune_open_questions(spec)
    assert len(spec["open_questions"]) == 2


def test_this_loops_own_boilerplate_does_not_make_questions_look_alike(spec):
    """Every carried source note shares thirty words of template. Unstripped,
    that dominates any word overlap and merges unrelated hedges -- in run 6
    it pulled four distinct source notes into one cluster."""
    duty = ("the input marks this UNCERTAIN, so it must not be resolved by "
            "assumption: ")
    _oq(spec,
        f"[source U3: Figure 6 (a)] {duty}The victim tag field is drawn "
        f"twelve bits wide, but the address range printed beside it needs "
        f"thirteen.",
        f"[source U5: Figure 6 (b)] {duty}What the decay counter is seeded "
        f"to at allocation is unstated; the window, the window minus one "
        f"and zero are all consistent with the figure.")
    spec_review.prune_open_questions(spec)
    assert len(spec["open_questions"]) == 2


def test_a_carried_note_the_spec_draws_nothing_from_is_dropped(spec):
    """`carry_source_notes` decides relevance by citation, and a section is
    coarse: one quote out of Section 6 inherits every hedge in it. Run 7
    shipped Figure 7's note -- no per-feature MPKI delta can be read off a
    stacked bar chart -- into a spec that never reads that chart."""
    _oq(spec,
        "[source I5: Figure 7] the input marks this INFERRED -- a reading of "
        "the figure's layout that the paper never states: No per-feature MPKI "
        "delta can be read off this chart to better than the gridline "
        "spacing; the bars are stacked and unlabelled.")
    report = spec_review.prune_open_questions(spec)
    assert report["stale"] == 1 and spec["open_questions"] == []


def test_a_carried_note_the_spec_does_draw_on_survives(spec):
    """The same shape, about something this spec is made of."""
    _oq(spec,
        "[source U3: Figure 6 (a)] the input marks this UNCERTAIN, so it must "
        "not be resolved by assumption: What the decay counter is seeded to "
        "at allocation is unstated; the decay window, the window minus one "
        "and zero are all consistent with the victim tag figure.")
    spec_review.prune_open_questions(spec)
    assert len(spec["open_questions"]) == 1


def test_an_off_topic_question_that_is_not_a_carried_note_survives(spec):
    """A reviewer-written question is *supposed* to name things the spec does
    not contain -- that is what a gap is. Applying the relevance rule to one
    would delete the list."""
    _oq(spec,
        "[/algorithms/0/pseudocode] No per-feature MPKI delta can be read off "
        "the stacked bar chart; what should the gridline spacing imply?")
    spec_review.prune_open_questions(spec)
    assert len(spec["open_questions"]) == 1


# The weighted clustering rule scores a word by how rare it is across the
# whole list, so it says nothing about a list of two -- there, every shared
# word has frequency 2 of 2 and weighs zero. It was calibrated on a list of
# thirty-five and needs one to be exercised at all, so these tests carry
# filler: eighteen invented questions on eighteen distinct subjects, none
# of which is a carried source note and none of which quotes a value.
_FILLER = [
    "[/algorithms/0/pseudocode] Is the victim tag read before or after the "
    "allocation check?",
    "[/algorithms/1/pseudocode] Should decay run on a stall cycle?",
    "[/state/0/indexing] Which address bits index the table, and is the "
    "index folded?",
    "[/state/0/entry_format] Are the stored tags truncated or hashed?",
    "[/state/1/organization] How many shadow counters does each bank own?",
    "[/host_interfaces/0] What signals eviction to the predictor?",
    "[/resource_accounting/total_storage_bits] Does the total include the "
    "allocation queue?",
    "[/unit_tests/0/given] Should the fill be warm or cold?",
    "[/summary] Does this feature interact with prefetch?",
    "[/algorithms/0/trigger] Is lookup driven by fetch or by rename?",
    "[/state/0/size_bits] Is the valid flag counted separately?",
    "[/algorithms/1/notes] What happens on a counter underflow?",
    "[/host_interfaces/0/need] Is the evicted way reported alongside?",
    "[/unit_tests/0/expect] Should a miss return a sentinel or nothing?",
    "[/parameters/0/range] May the window exceed the counter span?",
    "[/algorithms/0/notes] Is a partial match ever accepted?",
    "[/state/1/indexing] Does the bank come from the set or the way?",
    "[/source/inputs_used] Were any figures beyond the first consulted?",
]


def _pruned(spec, *questions):
    """Prune `questions` in a list long enough for the rule to mean
    something, and return the ones under test that survived."""
    _oq(spec, *(_FILLER + list(questions)))
    spec_review.prune_open_questions(spec)
    kept = spec["open_questions"]
    return [q for q in kept if q not in _FILLER]


def test_one_question_asked_four_ways_collapses_to_one(spec):
    """The rare-word rule has a blind spot that grows with the thing it is
    looking for: run 7 asked the usefulness threshold four times, which put
    "usefulness" at eight occurrences against a cutoff of four, and the four
    entries did not cluster at all."""
    kept = _pruned(
        spec,
        "[/algorithms/0/pseudocode] Does the usefulness gate open at >= 0 "
        "or > 0?",
        "[/parameters/15/default] What is the exact usefulness threshold "
        "value?",
        "[/algorithms/0] What is the minimum usefulness threshold required "
        "to activate the x2.5 multiplier?",
        "[/parameters/22/default] The paper does not specify the exact "
        "threshold for the usefulness gate on the multiplier. The gate could "
        "open for usefulness at or above zero, or strictly above it.")
    assert len(kept) == 1


def test_a_short_pair_sharing_two_words_still_collapses(spec):
    """The theta pair missed for the opposite reason to the one above: both
    questions are short, so their two genuinely shared words could never
    reach a floor of three."""
    kept = _pruned(
        spec,
        "[/parameters/16] The paper budgets storage for dynamic update "
        "thresholds but does not state the initial or default value for "
        "theta. What should the default be?",
        "[/parameters/16/default] What is the correct default value for the "
        "theta parameter?")
    assert len(kept) == 1


def test_two_questions_sharing_only_their_framing_stay_apart(spec):
    """"The paper does not specify the exact ..." is how half a question
    list opens, and it is four words about how a question is phrased and
    none about its subject. Unfiltered it linked an ROB-size question to a
    usefulness-gate one at run 7 -- the closest false pair to the bar."""
    kept = _pruned(
        spec,
        "[/parameters/0/default] The paper does not specify the exact "
        "maximum number of in-flight branches the structures must hold.",
        "[/state/1/entry_format] The paper does not specify the exact "
        "saturation point of the decay counter.")
    assert len(kept) == 2


def test_the_stopword_list_is_matched_against_stems(spec):
    """The list is written as words and subtracted from stems -- the same
    mismatch `_GENERIC_STEMS` fixed for `GENERIC_TOKENS`. `stem("does")` is
    "doe" and leaked through as a content word."""
    from spec_checks import stem

    assert stem("does") in spec_review._QUESTION_STOPWORD_STEMS
    assert stem("using") in spec_review._QUESTION_STOPWORD_STEMS
    assert stem("paper") in spec_review._QUESTION_STOPWORD_STEMS


def test_pruning_a_spec_with_no_questions_is_a_no_op(spec):
    spec.pop("open_questions", None)
    assert spec_review.prune_open_questions(spec)["after"] == 0
