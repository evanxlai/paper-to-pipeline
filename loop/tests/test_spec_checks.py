"""Tests for the deterministic spec checks.

Every fixture here describes an invented feature ("vtag", a made-up victim-tag
predictor). Nothing references the paper the loop currently adopts: if these
tests only passed for one paper, the checks would not be checks.
"""

import copy

import pytest

import spec_checks
from spec_checks import run_checks, field_widths, parse_range, numerals, tokens


def codes(findings):
    return sorted(f.code for f in findings)


@pytest.fixture
def spec():
    """A small, internally consistent spec for a fictional feature."""
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "A Victim Tag Predictor", "inputs_used": "paper_only"},
        "summary": "Tracks evicted tags to correct the base predictor.",
        "state": [
            {
                "name": "victim tag table",
                # 4 * 2 * 48 entries of (1 + 12 + 3) = 16 bits = 6144 bits.
                "organization": "4 banks, each of two arrays holding 48 entries",
                "entry_format": "valid (1), tag (12), ctr (3)",
                "size_bits": 6144,
                "indexing": "PC xor evicted tag",
            },
            {
                "name": "decay shadow counters",
                "organization": "one counter per bank, 4 banks",
                "entry_format": "decay_ctr (8 bits)",
                "size_bits": 32,
                "size_formula": "4 * ceil(log2(decay_window))",
                "indexing": "bank id",
            },
        ],
        "algorithms": [
            {
                "name": "predict",
                "trigger": "prediction lookup",
                "pseudocode": (
                    "for bank in 0..3:\n"
                    "  v = victim_tag_table[hash(PC)]\n"
                    "  if v.valid and decay_shadow[bank] > 0:\n"
                    "    sum += v.ctr * vtag_weight\n"
                    "return sum"
                ),
                "notes": "saturating at 3 bits",
            },
            {
                "name": "update",
                "trigger": "branch resolution",
                "pseudocode": (
                    "v = victim_tag_table[hash(PC)]\n"
                    "if taken: v.ctr = increment_sat(v.ctr)\n"
                    "else: v.ctr = decrement_sat(v.ctr)\n"
                    "decay_shadow[bank] = decay_window"
                ),
            },
        ],
        "host_interfaces": [
            {"need": "evicted tag", "description": "tag of the evicted entry"}
        ],
        "resource_accounting": {
            "total_storage_bits": 6176,
            "storage_breakdown": "victim tag table: 6144 bits (4 * 2 * 48 * 16), "
                                 "decay shadow counters: 32 bits (4 * 8)",
        },
        "parameters": [
            {
                "name": "decay_window",
                "type": "int",
                "default": 200,
                "range": "[1, 255]",
                "storage_impact": "widens decay_ctr",
            },
            {
                "name": "vtag_weight",
                "type": "float",
                "default": 1.5,
                "range": "[0.0, 4.0]",
                "storage_impact": "None",
            },
        ],
        # One test per structure and per algorithm, plus a test that walks
        # the decay counter over time. `_check_unit_test_coverage` asks for
        # exactly that, and a fixture that stands for "clean" has to meet
        # every check it is the baseline for.
        "unit_tests": [
            {
                "name": "counter saturates",
                "given": "8 taken branches on one entry",
                "expect": "ctr == 7 and does not wrap to 0",
            },
            {
                "name": "predict reads the victim tag table",
                "given": "victim tag table entry valid with ctr = 3",
                "expect": "predict returns 3 * vtag_weight",
            },
            {
                "name": "update refills the decay shadow counters",
                "given": "one resolved branch, then 200 decayed cycles",
                "expect": "update sets decay_ctr = 200, and it reaches 0 "
                          "after 200 cycles",
            },
        ],
    }


# ------------------------------------------------------------- primitives


def test_field_widths_parses_both_notations():
    w = field_widths("valid (1), payload (14 bits), decay_ctr (8-bit)")
    assert w == {"valid": 1, "payload": 14, "decay_ctr": 8}


@pytest.mark.parametrize("text,expected", [
    ("age (12), row_hit (1)", {"age": 12, "row_hit": 1}),     # parenthesised
    ("rrpv: 2 bits", {"rrpv": 2}),                            # colon
    ("16-bit tag, 12-bit stride", {"tag": 16, "stride": 12}),  # width-first
    ("payload [13:0]", {"payload": 14}),                      # bit range
])
def test_field_widths_across_notations(text, expected):
    """Every notation must parse, or the representability check silently
    finds nothing on a spec that writes widths a different way."""
    assert field_widths(text) == expected


def test_representability_fires_regardless_of_notation():
    base = {
        "state": [{"name": "t", "organization": "o", "size_bits": 8,
                   "entry_format": None}],
        "parameters": [{"name": "decay_window", "type": "int", "default": 256,
                        "range": "[1, 1024]", "storage_impact": ""}],
        "algorithms": [{"name": "a", "trigger": "t",
                        "pseudocode": "x = decay_window"}],
    }
    base["parameters"][0]["default"] = 300   # beyond the 256 steps 8 bits span
    for fmt in ("decay_ctr (8)", "decay_ctr: 8 bits", "8-bit decay_ctr",
                "decay_ctr [7:0]"):
        s = copy.deepcopy(base)
        s["state"][0]["entry_format"] = fmt
        assert "unrepresentable_default" in codes(run_checks(s)), fmt


def test_number_words_are_correct():
    assert spec_checks.NUM_WORDS["sixty"] == 60
    assert numerals("sixty entries") == {60}


def test_field_widths_skips_fractional_shared_bits():
    # `hysteresis (1/4)` is a shared-bit notation, not a 1-bit field.
    assert field_widths("prediction (1), hysteresis (1/4)") == {"prediction": 1}


def test_numerals_reads_words_and_powers():
    got = numerals("three tables of 2^10 entries and 65 registers")
    assert {3, 1024, 65} <= got


def test_tokens_stems_so_naming_variants_collide():
    assert tokens("Register tracking table") & tokens("tracker[rd].valid = 0")


@pytest.mark.parametrize("text,kind", [
    ("[1, 1024]", "interval"),
    ("[256, 65536] pow2", "interval"),
    ("choices: xor_fold|concat|truncate", "choices"),
    ("anything goes", None),
])
def test_parse_range_forms(text, kind):
    got = parse_range(text)
    assert (got[0] if got else None) == kind


# ----------------------------------------------------------- clean baseline


def test_consistent_spec_is_clean(spec):
    assert run_checks(spec, budget_bits=1 << 20) == []


# ------------------------------------------------------------ each defect


def test_storage_sum_mismatch(spec):
    spec["resource_accounting"]["total_storage_bits"] = 9999
    assert "storage_sum" in codes(run_checks(spec))


def test_budget_overflow(spec):
    assert "budget_fit" in codes(run_checks(spec, budget_bits=1000))


def test_default_outside_range(spec):
    spec["parameters"][0]["default"] = 999
    assert "param_range" in codes(run_checks(spec))


def test_pow2_modifier_enforced(spec):
    spec["parameters"][0]["range"] = "[1, 1024] pow2"
    spec["parameters"][0]["default"] = 200
    assert "param_range" in codes(run_checks(spec))


def test_a_json_boolean_default_matches_its_lowercase_choices(spec):
    """The defect: `"default": true` against `"choices: true | false"`.

    str(True) is "True", so a correctly typed bool knob failed at `error`.
    A review round spent all three of its landed patches on this and
    "fixed" it by retyping the boolean as the string "true".
    """
    spec["parameters"][0]["range"] = "choices: true | false"
    spec["parameters"][0]["default"] = True
    assert "param_range" not in codes(run_checks(spec))
    spec["parameters"][0]["default"] = "true"
    assert "param_range" not in codes(run_checks(spec))


def test_a_choice_default_is_matched_by_value_not_spelling(spec):
    spec["parameters"][0]["range"] = "choices: 1 | 2 | 4"
    spec["parameters"][0]["default"] = 1.0
    assert "param_range" not in codes(run_checks(spec))
    spec["parameters"][0]["range"] = "choices: XOR_FOLD | CONCAT"
    spec["parameters"][0]["default"] = "xor_fold"
    assert "param_range" not in codes(run_checks(spec))


def test_a_default_outside_its_choices_is_still_an_error(spec):
    """What the check is for, and what the tolerances must not silence."""
    spec["parameters"][0]["range"] = "choices: true | false"
    spec["parameters"][0]["default"] = "maybe"
    assert "param_range" in codes(run_checks(spec))
    spec["parameters"][0]["range"] = "choices: 1 | 2 | 4"
    spec["parameters"][0]["default"] = 3
    assert "param_range" in codes(run_checks(spec))


def test_default_that_does_not_fit_its_field(spec):
    """The defect that survived two distillation runs unflagged."""
    spec["parameters"][0]["default"] = 300      # more steps than 8 bits spans
    spec["parameters"][0]["range"] = "[1, 1024]"
    found = [f for f in run_checks(spec) if f.code == "unrepresentable_default"]
    assert found and "8-bit" in found[0].message


def test_a_span_of_exactly_two_to_the_width_is_representable(spec):
    """An 8-bit counter spans 256 steps, counting 255 down to 0. Calling that
    an error drives reviewers to 'fix' 256 to 255, which then breaks the knob's
    pow2 range -- the round oscillates between two errors and never settles.
    A literal stored INTO the field is still capped at 255; that is
    _check_literal_widths' job."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024] pow2"
    assert not [f for f in run_checks(spec) if f.code == "unrepresentable_default"]
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = 256"
    assert [f for f in run_checks(spec) if f.code == "unrepresentable_literal"]


def test_representability_respects_the_declared_width(spec):
    spec["state"][1]["entry_format"] = "decay_ctr (16 bits)"
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024]"
    assert "unrepresentable_default" not in codes(run_checks(spec))


def test_a_span_of_exactly_the_field_width_is_still_asked_about(spec):
    """The sliver `unrepresentable_default` leaves open, at `warn`.

    `decay_timeout` shipped at 256 against an 8-bit `decay_ctr` in twelve of
    the archived runs. The field counts 256 steps and holds at most 255, and
    none of the twelve said which it meant -- run 7's seeds the counter at
    255 while Section 4.2 says the window is 256.
    """
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024] pow2"
    f = [x for x in run_checks(spec) if x.code == "ambiguous_counter_span"]
    assert len(f) == 1 and f[0].severity == "warn"
    assert "decay_ctr" in f[0].message and "2^8" in f[0].message
    # And it does not double-report as the error that owns everything above.
    assert "unrepresentable_default" not in codes(run_checks(spec))


def test_a_span_inside_the_field_is_silent(spec):
    """200 fits an 8-bit counter as both a span and a value; nothing to ask."""
    assert "ambiguous_counter_span" not in codes(run_checks(spec))


def test_a_default_past_the_field_is_the_error_not_the_warning(spec):
    """Above 2^B the existing error owns it. Two findings for one defect
    would have the round repair it twice, in opposite directions."""
    spec["parameters"][0]["default"] = 300
    spec["parameters"][0]["range"] = "[1, 1024]"
    got = codes(run_checks(spec))
    assert "unrepresentable_default" in got
    assert "ambiguous_counter_span" not in got


def test_a_knob_that_names_no_field_is_not_guessed_at(spec):
    """The link is `storage_impact` naming the field, not name similarity --
    which would re-find every pairing the representability check owns."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["storage_impact"] = "No storage impact"
    assert "ambiguous_counter_span" not in codes(run_checks(spec))


def test_a_width_knob_names_the_field_it_widens(spec):
    """`storage_impact` routinely names the *width knob* rather than the
    field -- "increases decay_ctr_bits" -- and those share their tokens."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["storage_impact"] = (
        "Increases decay_ctr_bits if greater than 255")
    assert "ambiguous_counter_span" in codes(run_checks(spec))


def test_breakdown_factor_not_declared_anywhere(spec):
    """Right product, wrong factors: 4*256*6 == 4*384*4 == 6144."""
    spec["resource_accounting"]["storage_breakdown"] = (
        "victim tag table: 6144 bits (4 * 384 * 4), "
        "decay shadow counters: 32 bits (4 * 8)"
    )
    found = [f for f in run_checks(spec) if f.code == "breakdown_factors"]
    assert found and "384" in found[0].message


def test_breakdown_product_disagrees_with_claim(spec):
    spec["resource_accounting"]["storage_breakdown"] = (
        "victim tag table: 6144 bits (4 * 2 * 48 * 15)"
    )
    assert "breakdown_product" in codes(run_checks(spec))


def test_spelled_out_numbers_do_not_false_positive(spec):
    # "two arrays" in organization must satisfy the factor 2 in the breakdown,
    # and 16 must be satisfied by the sum of the declared field widths.
    spec["resource_accounting"]["storage_breakdown"] = (
        "victim tag table: 6144 bits (2 * 4 * 48 * 16)"
    )
    assert "breakdown_factors" not in codes(run_checks(spec))


def test_undefined_policy_call(spec):
    """Stubbed learning rules are the highest-cost silent omission."""
    spec["algorithms"][1]["pseudocode"] = "update_weights(entry)\nupdate_useful(entry)"
    found = [f for f in run_checks(spec) if f.code == "undefined_policy_call"]
    assert {f.severity for f in found} == {"warn"}
    assert {"update_weights", "update_useful"} <= {
        m for f in found for m in ("update_weights", "update_useful") if m in f.message
    }


@pytest.mark.parametrize("call", [
    "allocate_entry", "evict_victim", "train_weights", "age_counters",
    "reset_state", "insert_line", "promote_way", "throttle_rate",
])
def test_policy_verbs_are_domain_general(spec, call):
    """The policy-verb list must fire outside branch prediction."""
    spec["algorithms"][1]["pseudocode"] = f"{call}(x)"
    assert "undefined_policy_call" in codes(run_checks(spec))


def test_unknown_non_policy_call_is_only_informational(spec):
    """An allowlist can only hold names someone already saw.

    argmax and prefetch are primitives in their own subfields. They are
    reported, but at info severity, so an unfamiliar vocabulary cannot roll
    back a review round.
    """
    spec["algorithms"][0]["pseudocode"] = "return argmax(victim_tag_table)"
    found = [f for f in run_checks(spec) if f.code == "undefined_helper"]
    assert found and {f.severity for f in found} == {"info"}
    assert not spec_checks.is_worse([], found)


def test_primitives_are_not_flagged_as_undefined(spec):
    spec["algorithms"][0]["pseudocode"] = (
        "x = max(0, min(3, popcount(v))) + hash2(PC) if is_valid(v) else 0"
    )
    assert "undefined_helper" not in codes(run_checks(spec))


def test_calling_another_algorithm_is_fine(spec):
    spec["algorithms"][0]["pseudocode"] = "update(entry)"
    assert "undefined_helper" not in codes(run_checks(spec))


def test_orphan_state(spec):
    spec["state"].append({
        "name": "zzz unused buffer",
        "organization": "16 entries",
        "entry_format": "payload (4)",
        "size_bits": 64,
        "indexing": "none",
    })
    spec["resource_accounting"]["total_storage_bits"] += 64
    assert "orphan_state" in codes(run_checks(spec))


def test_unreferenced_parameter(spec):
    spec["parameters"].append({
        "name": "zzz_unused_knob", "type": "int", "default": 2, "range": "[1, 8]",
        "storage_impact": "None",
    })
    assert "unreferenced_param" in codes(run_checks(spec))


def test_a_generic_named_knob_the_pseudocode_reads_is_not_unreferenced(spec):
    """`num_regs` stems to {num, reg}, both generic, so the name falls back to
    its unfiltered tokens while the body keeps dropping them -- and a knob the
    pseudocode reads four times reported as read by nothing. A false positive
    here teaches a reviewer to delete a live knob."""
    spec["parameters"].append({
        "name": "num_regs", "type": "int", "default": 65, "range": "[1, 128]",
        "storage_impact": "None",
    })
    spec["algorithms"][0]["pseudocode"] += "\nfor r in 0 to num_regs - 1:\n  pass"
    assert "unreferenced_param" not in codes(run_checks(spec))


def test_a_generic_named_knob_nothing_reads_is_still_unreferenced(spec):
    """The repair must not go the other way. `WEIGHT_BITS` is all-generic too,
    and "weight" appears in any weight table's prose, so comparing unfiltered
    token sets would wave through a knob no pseudocode mentions."""
    spec["parameters"].append({
        "name": "WEIGHT_BITS", "type": "int", "default": 6, "range": "[1, 8]",
        "storage_impact": "None",
    })
    assert "unreferenced_param" in codes(run_checks(spec))


def test_vacuous_test_hedge_word(spec):
    spec["unit_tests"][0]["expect"] = "the table holds the correct 12-bit digest"
    assert "vacuous_test" in codes(run_checks(spec))


def test_vacuous_test_no_assertion(spec):
    spec["unit_tests"][0]["expect"] = "the predictor behaves as the paper describes"
    assert "vacuous_test" in codes(run_checks(spec))


def test_unparseable_range_is_only_a_warning(spec):
    spec["parameters"][0]["range"] = "some large-ish value"
    found = [f for f in run_checks(spec) if f.code == "range_unparsed"]
    assert found and found[0].severity == "warn"


# --------------------------------------------------------------- severity


def test_is_worse_on_new_error(spec):
    before = run_checks(spec)
    broken = copy.deepcopy(spec)
    broken["resource_accounting"]["total_storage_bits"] = 1
    assert spec_checks.is_worse(before, run_checks(broken))


def test_is_worse_allows_trading_warnings_for_a_fix(spec):
    broken = copy.deepcopy(spec)
    broken["resource_accounting"]["total_storage_bits"] = 1   # 1 error
    fixed = copy.deepcopy(spec)
    fixed["parameters"][0]["range"] = "unparseable"           # 1 warn
    assert not spec_checks.is_worse(run_checks(broken), run_checks(fixed))


def test_is_worse_on_an_error_swapped_for_a_different_error(spec):
    """One error traded for another is not a round that held its ground.

    Counting alone, 1 -> 1 reads as no change, and a round that cleared
    `param_range` while breaking `storage_sum` went straight through this
    gate. It was then rejected downstream by the rule that guards quote-free
    patching -- which blamed the three patches that had done the fixing,
    discarded the round, and left the spec with the error it arrived with.
    """
    before = copy.deepcopy(spec)
    before["parameters"][0]["default"] = 256          # param_range
    after = copy.deepcopy(spec)
    after["resource_accounting"]["total_storage_bits"] = 1   # storage_sum

    b, a = run_checks(before), run_checks(after)
    assert spec_checks.severity_counts(b)["error"] == 1
    assert spec_checks.severity_counts(a)["error"] == 1
    assert spec_checks.is_worse(b, a)
    assert [f.code for f in spec_checks.new_errors(b, a)] == ["storage_sum"]


def test_a_reworded_message_is_not_a_new_error(spec):
    """A round rewrites the numbers a message quotes, so identity is
    (code, pointer) -- otherwise every patch looks like it fixed something and
    broke something in the same place."""
    before = copy.deepcopy(spec)
    before["resource_accounting"]["total_storage_bits"] = 1
    after = copy.deepcopy(spec)
    after["resource_accounting"]["total_storage_bits"] = 2

    b, a = run_checks(before), run_checks(after)
    assert b[0].message != a[0].message
    assert spec_checks.new_errors(b, a) == []
    assert not spec_checks.is_worse(b, a)


# ------------------------------------------- pseudocode surface reading


def test_literal_too_wide_for_its_declared_field(spec):
    """A constant stored into a field must fit it, even when every declared
    parameter default already does. The parameter check never looks here."""
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = 256"
    f = [x for x in run_checks(spec) if x.code == "unrepresentable_literal"]
    assert len(f) == 1
    assert f[0].severity == "error"
    assert "8 bits" in f[0].message and "255" in f[0].message


def test_literal_that_fits_is_not_flagged(spec):
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = 255"
    assert not [x for x in run_checks(spec) if x.code == "unrepresentable_literal"]


@pytest.mark.parametrize("line", [
    "if decay_ctr == 256: pass",      # comparison, not a store
    "if decay_ctr >= 256: pass",
    "decay_ctr += 256",               # accumulate, not a store
])
def test_comparisons_are_not_read_as_assignments(spec, line):
    spec["algorithms"][1]["pseudocode"] += "\n" + line
    assert not [x for x in run_checks(spec) if x.code == "unrepresentable_literal"]


def test_inner_dimension_indexed_differently_across_algorithms(spec):
    """A producer walking absolute ids and a consumer walking slots disagree
    about the structure's shape; one of them is out of bounds.

    The signal is the domain CHANGE -- one side divides an absolute id down to
    a slot within its group -- not the differing names. Names alone proved too
    weak: two algorithms legitimately spell one register id `r` and
    `chosen_reg`, and flagging that punishes correct specs."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] += (
        "\n  for tag_id in bank_tags:\n    x = W0[bank][tag_id]"
    )
    spec["algorithms"][1]["pseudocode"] += "\nslot = chosen / 8\nW0[bank][slot] = 1"
    f = [x for x in run_checks(spec) if x.code == "inconsistent_index"]
    # One per algorithm involved, anchored at that algorithm -- a finding on
    # the container reaches no review unit and so reaches no reviewer.
    assert {x.pointer for x in f} == {"/algorithms/0/pseudocode",
                                      "/algorithms/1/pseudocode"}
    assert all(x.severity == "warn" for x in f)


def test_two_plain_indices_with_no_domain_change_are_clean(spec):
    """`r` in one algorithm and `chosen_reg` in another are both absolute ids.
    This shape was flagged in two consecutive real runs and was correct both
    times."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] += (
        "\n  for r in valid_regs:\n    x = W0[bank][r]"
    )
    spec["algorithms"][1]["pseudocode"] += (
        "\nchosen_reg = pick(bank_avail)\nW0[bank][chosen_reg] = 1"
    )
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


def test_an_annotated_binding_still_matches_its_bare_twin(spec):
    """A trailing `// 9-bit index` is annotation, not derivation."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] += (
        "\n  h = hash_w0(pc, d) // 9-bit index into 512 entries\n  x = W0[bank][h]"
    )
    spec["algorithms"][1]["pseudocode"] += "\nh = hash_w0(pc, d)\nW0[bank][h] = 1"
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


def test_top_level_index_may_be_spelled_differently(spec):
    """Call sites routinely name the same table index differently; only an
    inner dimension is worth flagging."""
    spec["algorithms"][0]["pseudocode"] += "\n  y = victim_tag_table[idx_a]"
    spec["algorithms"][1]["pseudocode"] += "\nvictim_tag_table[idx_b] = 0"
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


def test_conditionally_written_context_read_unconditionally(spec):
    spec["algorithms"][0]["pseudocode"] = (
        "ctx.bank_sum = [0] * 4\n"
        "for bank in 0..3:\n"
        "  if useful[bank] > 0:\n"
        "    ctx.bank_sum[bank] = weight_of(bank)\n"
        "return sum(ctx.bank_sum)"
    )
    spec["algorithms"][1]["pseudocode"] = (
        "for bank in 0..3:\n"
        "  taken = ctx.bank_sum[bank] >= 0\n"
        "  victim_tag_table[hash(PC)].ctr = taken"
    )
    f = [x for x in run_checks(spec) if x.code == "conditional_context_write"]
    # Producer and consumer both hear about it: either end can fix it.
    assert {x.pointer for x in f} == {"/algorithms/0/pseudocode",
                                      "/algorithms/1/pseudocode"}
    assert all(x.severity == "warn" for x in f)
    assert "ctx.bank_sum" in f[0].message


def test_unconditionally_written_context_is_not_flagged(spec):
    """The same shape, minus the conditional: the consumer can trust it."""
    spec["algorithms"][0]["pseudocode"] = (
        "ctx.avail = [[] for _ in range(4)]\n"
        "for bank in 0..3:\n"
        "  ctx.avail[bank] = live_regs(bank)\n"
        "return ctx.avail"
    )
    spec["algorithms"][1]["pseudocode"] = (
        "for bank in 0..3:\n"
        "  n = ctx.avail[bank]"
    )
    assert not [x for x in run_checks(spec) if x.code == "conditional_context_write"]


def test_a_declaration_is_not_a_call_site(spec):
    """`function foo(...)` declares foo. Reading it as a call reports every
    algorithm whose function name differs from its spec name as a hole."""
    spec["algorithms"][1]["pseudocode"] = (
        "function update_vtag(pc):\n"
        "  victim_tag_table[hash(pc)].ctr = 1"
    )
    assert not [x for x in run_checks(spec)
                if x.code in ("undefined_helper", "undefined_policy_call")
                and "update_vtag" in x.message]


def test_indices_named_differently_but_derived_alike_agree(spec):
    """Two algorithms can spell one derived quantity differently in their own
    local vocabulary. Reporting that as a disagreement punishes a correct fix."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] = (
        "slot_a = bank_slot(b, reg)\nx = W0[bank][slot_a]"
    )
    spec["algorithms"][1]["pseudocode"] = (
        "slot_b = bank_slot(b, sampled)\nW0[bank][slot_b] = 1"
    )
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


def test_new_checks_are_silent_on_a_clean_spec(spec):
    """The fixture is self-consistent; a heuristic that fires on it is noise."""
    noisy = {"unrepresentable_literal", "inconsistent_index",
             "conditional_context_write"}
    assert not [x for x in run_checks(spec) if x.code in noisy]


def test_helpers_declared_inline_are_not_holes(spec):
    """A block that declares its own small helpers above the entry point has
    defined them; reporting those trains a reader to ignore the check."""
    spec["algorithms"][1]["pseudocode"] = (
        "function sat_update(ctr, step):\n"
        "  return ctr + step\n"
        "function update_vtag(pc):\n"
        "  victim_tag_table[hash(pc)].ctr = sat_update(1, 1)"
    )
    assert not [x for x in run_checks(spec)
                if x.code in ("undefined_helper", "undefined_policy_call")
                and "sat_update" in x.message]


def test_context_read_but_never_produced(spec):
    """The consumer is unimplementable: nothing in the spec fills the field,
    so an implementer must invent both its contents and its producer."""
    spec["algorithms"][1]["pseudocode"] = (
        "function update(pc, saved_state):\n"
        "  for bank in 0..3:\n"
        "    n = saved_state.regs_per_bank[bank]"
    )
    f = [x for x in run_checks(spec) if x.code == "unproduced_context"]
    assert len(f) == 1 and f[0].severity == "warn"
    assert "saved_state.regs_per_bank" in f[0].message
    assert f[0].pointer == "/algorithms/1/pseudocode"


def test_a_local_alias_is_not_carried_context(spec):
    """`v = table[i]` then `v.ctr` is the consumer's own business; only an
    object that arrives from outside and is never assigned is a handshake."""
    spec["algorithms"][1]["pseudocode"] = (
        "function update(pc):\n"
        "  v = victim_tag_table[hash(pc)]\n"
        "  v.ctr = 1"
    )
    assert not [x for x in run_checks(spec) if x.code == "unproduced_context"]


def test_same_index_name_bound_from_different_domains(spec):
    """Renaming both sides to `r` does not make them agree. The disagreement
    is in where the value comes from, not what it is called."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] = (
        "for r in regs_in_bank:\n"
        "  x = W0[bank][r]"
    )
    spec["algorithms"][1]["pseudocode"] = (
        "r = chosen / 8\n"
        "W0[bank][r] = 1"
    )
    f = [x for x in run_checks(spec) if x.code == "inconsistent_index"]
    assert {x.pointer for x in f} == {"/algorithms/0/pseudocode",
                                      "/algorithms/1/pseudocode"}
    assert "iterated over `regs_in_bank`" in f[0].message
    assert "assigned `chosen / 8`" in f[0].message


def test_same_index_bound_the_same_way_is_clean(spec):
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    for i in (0, 1):
        spec["algorithms"][i]["pseudocode"] = (
            "for r in slots_in_bank:\n"
            "  x = W0[bank][r]"
        )
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


# ------------------------------------- declared bound vs index range


def test_index_exceeding_its_declared_dimension(spec):
    """Two algorithms can agree perfectly with each other and both disagree
    with the state entry they subscript. Comparing them to each other cannot
    see it; comparing each to the declaration can."""
    spec["state"][0]["organization"] = (
        "4 banks; each bank tracks 12 logical registers, sub-table W0"
    )
    spec["state"][0]["entry_format"] = "vector of 12 x 6-bit weights per bank"
    spec["algorithms"][0]["pseudocode"] = (
        "bank_regs = [r for r in 0 .. 47 if (r % 4) == bank]\n"
        "for r in bank_regs:\n"
        "  x = W0[idx][r]"
    )
    f = [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]
    assert len(f) == 1 and f[0].severity == "error"
    assert "reaches 47" in f[0].message and "12 element" in f[0].message
    assert f[0].pointer == "/algorithms/0/pseudocode"


def test_index_within_its_declared_dimension_is_clean(spec):
    """The same shape where the declaration matches the indexing."""
    spec["state"][0]["organization"] = (
        "one table whose entries hold weights for all 48 registers, sub-table W0"
    )
    spec["state"][0]["entry_format"] = "vector of 48 x 6-bit weights"
    spec["algorithms"][0]["pseudocode"] = (
        "bank_regs = [r for r in 0 .. 47 if (r % 4) == bank]\n"
        "for r in bank_regs:\n"
        "  x = W0[idx][r]"
    )
    assert not [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]


def test_bank_relative_index_is_clean(spec):
    """Dividing the absolute id down to a slot is the correct fix, and must
    not still read as an error afterwards."""
    spec["state"][0]["organization"] = (
        "4 banks; each bank tracks 12 logical registers, sub-table W0"
    )
    spec["state"][0]["entry_format"] = "vector of 12 x 6-bit weights per bank"
    spec["algorithms"][0]["pseudocode"] = (
        "bank_regs = [r for r in 0 .. 47 if (r % 4) == bank]\n"
        "for r in bank_regs:\n"
        "  slot = r / 4\n"
        "  x = W0[idx][slot]"
    )
    assert not [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]


def test_an_unbounded_index_produces_no_finding(spec):
    """A bound that cannot be established must not be guessed: a manufactured
    error blocks the stage and deadlocks the review loop."""
    spec["state"][0]["organization"] = (
        "4 banks; each bank tracks 12 logical registers, sub-table W0"
    )
    spec["state"][0]["entry_format"] = "vector of 12 x 6-bit weights per bank"
    spec["algorithms"][0]["pseudocode"] = "x = W0[idx][whatever_reg]"
    assert not [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]


def test_an_aggregate_count_is_not_a_dimension(spec):
    """'total 48 registers' is a sum across banks, not the width of one entry.
    Reading it as a dimension lifts the bound above every possible index, which
    disables the check without ever failing -- the worst way for it to break."""
    spec["state"][0]["organization"] = (
        "4 banks, sub-table W0; bank 0 has 12 registers; total 48 registers"
    )
    spec["state"][0]["entry_format"] = "12 x 6 bits = 72 bits/entry"
    spec["algorithms"][0]["pseudocode"] = (
        "bank_regs = [r for r in 0 .. 47 if (r % 4) == bank]\n"
        "for r in bank_regs:\n"
        "  x = W0[idx][r]"
    )
    f = [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]
    assert len(f) == 1 and "12 element" in f[0].message


def test_entry_format_width_beats_the_organization_prose(spec):
    """entry_format describes exactly one entry, so its per-entry width is
    authoritative over whatever mix of numbers organization carries."""
    spec["state"][0]["organization"] = (
        "4 banks holding 48 registers between them, sub-table W0, 8 entries"
    )
    spec["state"][0]["entry_format"] = "12 x 6 bits per entry"
    spec["algorithms"][0]["pseudocode"] = (
        "for r in 0 .. 47:\n  x = W0[idx][r]"
    )
    f = [x for x in run_checks(spec) if x.code == "index_exceeds_dimension"]
    assert len(f) == 1 and "12 element" in f[0].message


def test_a_binding_phrased_over_each_algorithms_own_local_agrees(spec):
    """'index of r in bank' and 'index of chosen_r in bank' both compute a
    position within the bank; which register they start from is each
    algorithm's business, not a disagreement about the table's shape."""
    spec["state"][0]["organization"] = (
        "4 banks, each of two arrays holding 48 entries, sub-tables W0 and W1"
    )
    spec["algorithms"][0]["pseudocode"] = (
        "for r in valid_regs:\n"
        "  pos = index of r in bank\n"
        "  x = W0[idx][pos]"
    )
    spec["algorithms"][1]["pseudocode"] = (
        "chosen_r = pick(avail)\n"
        "pos = index of chosen_r in bank\n"
        "W0[idx][pos] = 1"
    )
    assert not [x for x in run_checks(spec) if x.code == "inconsistent_index"]


# ------------------------------------------------ bare names across algorithms


def _carried(spec):
    return [f for f in spec_checks.run_checks(spec)
            if f.code in ("unproduced_context", "cross_algorithm_local")]


def _two_algo_spec(predict_body, update_body):
    return {
        "feature_name": "vtag",
        "state": [{"name": "victim tag table", "organization": "256 entries",
                   "entry_format": "tag (12)", "size_bits": 3072,
                   "indexing": "PC"}],
        "algorithms": [
            {"name": "predict", "trigger": "lookup", "pseudocode": predict_body},
            {"name": "update", "trigger": "retire", "pseudocode": update_body},
        ],
        "parameters": [],
    }


def test_a_subscripted_name_nothing_writes_is_unproduced():
    spec = _two_algo_spec(
        "function predict(pc):\n  return victim_tag_table[pc]",
        "function update(pc):\n  t = saved_tag[pc]\n  return t",
    )
    found = _carried(spec)
    assert len(found) == 1
    assert found[0].code == "unproduced_context"
    assert "saved_tag" in found[0].message


def test_reading_another_algorithms_plain_local_is_flagged():
    spec = _two_algo_spec(
        "function predict(pc):\n  w = victim_tag_table[pc]\n  return w",
        "function update(pc, taken):\n  if w + 1 > 0:\n    return taken",
    )
    found = _carried(spec)
    assert [f.code for f in found] == ["cross_algorithm_local"]
    assert "plain local of predict" in found[0].message


def test_a_keyed_store_is_a_real_handshake_not_a_defect():
    spec = _two_algo_spec(
        "function predict(pc):\n  chosen[pc] = victim_tag_table[pc]",
        "function update(pc):\n  return chosen[pc]",
    )
    assert _carried(spec) == []


def test_declared_furniture_is_not_a_missing_producer():
    """Keywords, types, declared state under another spelling, and names
    the algorithm declares as inputs are all furniture, not dataflow."""
    spec = _two_algo_spec(
        "function predict(pc: uint64) -> int:\n"
        "  return VictimTagTable[pc] + pc",
        "function update(pc, outcome):\n  return outcome + pc",
    )
    assert _carried(spec) == []


def test_declared_inputs_count_as_produced():
    spec = _two_algo_spec(
        "v = victim_tag_table[pc]",
        "if squash_signal > 0:\n  return v",
    )
    spec["algorithms"][1]["inputs"] = ["squash_signal from the host"]
    spec["algorithms"][1]["pseudocode"] = "if squash_signal > 0:\n  return 1"
    assert _carried(spec) == []


def test_a_shared_generic_token_does_not_excuse_a_different_name():
    """`recorded_digest` and `selected_reg_digest` both end in "digest" and
    denote different things; one shared token must not suppress the finding."""
    spec = _two_algo_spec(
        "function predict(pc):\n  return victim_tag_table[pc]",
        "function update(pc):\n  return recorded_digest[pc]",
    )
    spec["state"][0]["indexing"] = "hashed from (PC, selected_reg_digest)"
    found = _carried(spec)
    assert [f.code for f in found] == ["unproduced_context"]
    assert "recorded_digest" in found[0].message


# ------------------------------------------ unit-test arithmetic closure


def _arith(spec):
    return [f for f in run_checks(spec) if f.code == "arith_mismatch"]


def one_test(given="given", expect="expect"):
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "t", "inputs_used": "paper_only"},
        "summary": "s",
        "state": [], "algorithms": [], "host_interfaces": [],
        "resource_accounting": {"total_storage_bits": 0},
        "parameters": [],
        "unit_tests": [{"name": "t", "given": given, "expect": expect}],
    }


def test_wrong_decimal_restatement_is_an_error():
    """The defect this check exists for: 0xBBB is 3003, not 2999."""
    f = _arith(one_test(expect="Digest = (0xB << 8) | (0xB << 4) | 0xB "
                               "= 0xBBB (decimal 2999)."))
    assert len(f) == 1
    assert f[0].severity == "error"
    assert f[0].pointer == "/unit_tests/0/expect"
    assert "3003" in f[0].message and "2999" in f[0].message


def test_wrong_equality_chain_is_an_error():
    f = _arith(one_test(expect="Digest = 0x000 ^ 0x1F8 ^ 0x03F = 0x1C8."))
    assert [x.severity for x in f] == ["error"]


def test_correct_arithmetic_is_silent():
    assert _arith(one_test(
        given="4-bit condition code 0b1011 (0xB).",
        expect="Digest = 0x000 ^ 0x1F8 ^ 0x03F = 0x1C7 (decimal 455), and "
               "lead_count (57) << 3 = 0x1C8.",
    )) == []


def test_signed_restatement_of_a_fixed_width_literal_is_silent():
    """`0xFFFFFFFFFFFFFFFE (-2)` is a correct two's-complement restatement.

    Reading only the unsigned value turns every negative test vector into an
    error, and at this severity that fails the whole stage closed.
    """
    assert _arith(one_test(given="64-bit value 0xFFFFFFFFFFFFFFFE (-2).")) == []


def test_caret_as_an_exponent_is_not_decided():
    """`2^11 = 2048` is an exponent to a paper and XOR to Python.

    With no radix literal beside the caret the claim is undecidable, and
    guessing XOR would report a correct storage figure as a contradiction.
    """
    assert _arith(one_test(expect="The table holds 2^11 = 2048 entries.")) == []


def test_bit_position_parenthetical_is_not_a_restatement():
    assert _arith(one_test(expect="0x40 (bit 6) is the highest set bit.")) == []


def test_unit_suffix_does_not_block_a_sum():
    f = _arith(one_test(expect="total = 43008 + 9360 + 1495 = 53864 bits."))
    assert len(f) == 1 and f[0].severity == "error"
    assert _arith(one_test(
        expect="total = 43008 + 9360 + 1495 = 53863 bits (6.575 KiB).")) == []


def test_rounding_expressions_are_left_alone():
    """A multiplier with a rounding rule this evaluator does not model."""
    assert _arith(one_test(expect="Bank 0 outputs floor(4 * 2.5) = +10.")) == []
    assert _arith(one_test(expect="Bank 0 outputs floor(4 * 2.5) = +11.")) == []


def test_a_conjunction_does_not_chain_two_assignments():
    """The defect: "decay_ctr = 255 and valid = 1" is two assignments.

    Reading "and valid" as the unit of 255 left that 255 facing the 1 of the
    other assignment. A whole review round spent its one landed patch
    rewording a test to dodge this, and three more units proposed the same
    reword and were rejected as duplicates.
    """
    assert _arith(one_test(
        given="Register R0 is written at cycle 0 with decay_ctr = 255 "
              "and valid = 1.")) == []
    assert _arith(one_test(
        given="R0 is written with valid = 1 and decay_ctr = 255.")) == []
    assert _arith(one_test(
        expect="entry = 0 or valid = 1.")) == []


def test_a_unit_is_still_stripped_beside_a_conjunction():
    """Only the tail that carries the conjunction goes undecided."""
    assert _arith(one_test(
        expect="total = 43008 + 9360 + 1495 = 53863 bits and the entry "
               "is valid.")) == []
    f = _arith(one_test(expect="sum = 1 + 1 = 3 bits, and valid = 1."))
    assert len(f) == 1 and f[0].severity == "error"


def test_a_prose_tail_naming_a_spec_identifier_is_stripped():
    """`= 569 in the tomasulo_table` is run 7's shape, and it escaped.

    The tail class had no underscore, so `tomasulo_table` survived, the
    literal-character filter then rejected the whole part, and a claim with
    one undecidable side is dropped by design. The spec shipped an expected
    digest of 569 for an expression worth 441, and round 0 returned
    SUPPORTED on it -- no reviewer is asked to be a calculator.
    """
    f = _arith(one_test(
        expect="The complete algorithm computes lead=63, trail=1, val5_0=1, "
               "and stores digest=(1<<6) ^ (63<<3) ^ 1 = 569 in the "
               "tomasulo_table."))
    assert len(f) == 1 and f[0].severity == "error"
    assert "441" in f[0].message and "569" in f[0].message


def test_the_same_claim_with_the_right_value_is_silent():
    assert _arith(one_test(
        expect="The complete algorithm computes lead=63, trail=1, val5_0=1, "
               "and stores digest=(1<<6) ^ (63<<3) ^ 1 = 441 in the "
               "tomasulo_table.")) == []


def test_a_conjunction_in_an_underscored_tail_still_blocks_stripping():
    """Widening the class must not cost the guard the narrow one was
    carrying. `and decay_ctr = 255` is the next assertion, not a unit."""
    assert _arith(one_test(
        expect="sr_wt holds 43008 bits and decay_ctr = 255.")) == []


def test_every_probe_shares_the_widened_tail():
    """The tail gap was general, not specific to the equality chain.

    Each probe below reduces its operands through `_literal_arith`, so all
    of them were blind to an underscored tail and all of them see it now.
    This is the check the handover asked for: one fix, not four regexes.
    """
    # restatement probe, whose parenthetical carries the tail
    assert len(_arith(one_test(
        expect="the digest is 441 (442 in the tomasulo_table)"))) == 1
    # `computed as` probe
    assert len(_arith(one_test(
        expect="digest is 570 (computed as (1<<6) ^ (63<<3) ^ 1) "
               "in the tomasulo_table"))) == 1
    # equality chain
    assert len(_arith(one_test(
        expect="total = 1 + 1 = 3 in the sr_wt table"))) == 1


def test_an_inclusive_range_and_its_count_is_not_a_restatement():
    """`slots 0-8 (9 registers)` is a range and its size, not 8 restated as 9.

    The regex reaches over the hyphen and matches the tail of the range, so
    the parenthetical looked like a restatement of `8`. It never fired on a
    model-written spec and fired immediately on a hand-refined one, at
    `error`, which fails the distill stage closed on correct English.
    """
    assert _arith(one_test(
        expect="Bank 0 holds R0, R8, ..., R64 at slots 0-8 (9 registers). "
               "Bank 1 holds R1, R9, ..., R57 at slots 0-7 (8 registers).")) == []


def test_a_range_whose_count_is_wrong_is_still_a_mismatch():
    f = _arith(one_test(expect="Bank 0 holds slots 0-8 (10 registers)."))
    assert len(f) == 1 and f[0].severity == "error"


def test_a_subtraction_restated_beside_itself_is_silent():
    """The other reading of `L-N (M)`, and the paper's prose uses both."""
    assert _arith(one_test(expect="The high field spans 8-3 (5) bits.")) == []


def test_a_hex_restatement_still_closes_over_a_hyphen():
    """The motivating case must survive the range exemption."""
    f = _arith(one_test(expect="Digest 0xBBB (decimal 2999) is written."))
    assert len(f) == 1 and f[0].severity == "error"


def test_comparisons_are_not_equality_claims():
    assert _arith(one_test(
        expect="After 1st decode, decay_ctr == 1, then decay_ctr == 0.")) == []


def test_a_stated_value_beside_its_expression_is_checked():
    """`376 (computed as ...)` is the shape the distiller writes its digest
    tests in, and the parenthetical is made of parenthesised shifts -- which
    the restatement probe cannot read, because its parenthetical is `[^()]`.
    The evaluator never ran on the one field it was built for."""
    f = _arith(one_test(
        expect="Digest is 376 (computed as (1<<6) ^ (63<<3) ^ 0)"))
    assert len(f) == 1
    assert f[0].severity == "error"
    assert "440" in f[0].message and "376" in f[0].message


def test_a_stated_value_that_matches_its_expression_is_silent():
    assert _arith(one_test(
        expect="Digest is 440 (computed as (1<<6) ^ (63<<3) ^ 0)")) == []


def test_a_bare_binary_restatement_of_a_hex_value_is_not_a_mismatch():
    """`0xA (1010)` is correct read as binary, and nothing in the
    parenthetical says which radix it is. Read as decimal it contradicts a
    test that is right -- at `error`, the severity that gets a correct spec
    rewritten to suit the check instead of the other way round."""
    assert _arith(one_test(
        given="Flag instruction completes with flags 0xA (1010)")) == []


def test_a_bare_binary_restatement_that_does_not_close_is_still_reported():
    """The radix is ambiguous; the arithmetic is not. 1011 is 11, not 0xA."""
    assert len(_arith(one_test(given="flags 0xA (1011)"))) == 1


def test_arith_mismatch_is_a_self_consistency_code():
    """Without this the only fitting verdict has no licence to patch.

    The paper says nothing about a decimal restatement, so CONTRADICTED has no
    quote and UNSUPPORTED may not patch; INCONSISTENT is the verb, and it is
    accepted only at a pointer a self-consistency check named.
    """
    import spec_review
    assert "arith_mismatch" in spec_review._SELF_CONSISTENCY_CODES


# ------------------------------------------------- pseudocode comments


def _ctx(body):
    spec = one_test()
    spec["algorithms"] = [{"name": "a", "trigger": "t", "pseudocode": body}]
    return sorted(f.code for f in run_checks(spec)
                  if f.code in ("unproduced_context", "cross_algorithm_local",
                                "undefined_helper"))


def test_prose_in_comments_is_not_dataflow():
    """Commented figure transcription used to read as eight free variables."""
    assert _ctx(
        "def digest(val):\n"
        "    # Value[5:0] at [11:6], lead_count at [8:3]\n"
        "    # LSUM = sB + sG + sP + sC + sI + sL + sS + sT\n"
        "    # Format determined by MSBs/instruction type\n"
        "    # Right-aligned in 12-bit digest, restore pre-speculative tag\n"
        "    return val & 0xFFF\n"
    ) == []


def test_a_real_free_variable_still_reports():
    assert "unproduced_context" in _ctx(
        "def digest(val):\n"
        "    if fp_format == 'FP16':  # a comment does not hide this\n"
        "        return val >> 13\n"
    )


def test_signature_default_binds_the_parameter():
    """`def tick(n=1)` binds n; the default used to break the name match."""
    assert _ctx(
        "def tick(num_decoded=1):\n"
        "    return num_decoded - 1\n"
    ) == []


def test_keywords_are_not_undefined_helpers():
    assert _ctx(
        "def f(v):\n"
        "    if (v >> 63) & 1:\n"
        "        return (v)\n"
    ) == []


# --------------------------------------------- carried state vs the budget


def _budget(spec):
    return [f for f in run_checks(spec) if f.code == "unbudgeted_carried_state"]


def carried_spec(accounting_text, body):
    spec = one_test()
    spec["algorithms"] = [{"name": "update", "trigger": "resolve",
                           "pseudocode": body}]
    spec["resource_accounting"] = {
        "total_storage_bits": 100,
        "storage_breakdown": accounting_text,
    }
    return spec


def test_unbudgeted_per_branch_structure_reports_at_the_accounting():
    """The two halves of this defect live in different review units.

    `partition` gives the algorithm to one reviewer and resource_accounting to
    another, so the finding has to land at the pointer the accounting reviewer
    owns or nobody can act on it.
    """
    f = _budget(carried_spec(
        "Tables: 43008 bits. Register status table: 1495 bits.",
        "def update(pc):\n    d = checkpointed_digests[r]\n    return d\n"))
    assert len(f) == 1
    assert f[0].pointer == "/resource_accounting/storage_breakdown"
    assert "checkpointed_digests" in f[0].message


def test_a_budgeted_structure_is_silent():
    assert _budget(carried_spec(
        "Checkpointed digests: 780 bits per branch. Tables: 43008 bits.",
        "def update(pc):\n    d = checkpointed_digests[r]\n    return d\n")) == []


def test_a_shared_word_does_not_count_as_budgeted():
    """"Digest generation requires counter trees" budgets no digest table."""
    assert len(_budget(carried_spec(
        "Digest generation requires counter trees. Tables: 43008 bits.",
        "def update(pc):\n    d = checkpointed_digests[r]\n    return d\n"))) == 1


def test_a_scalar_is_not_storage():
    """A decision handed to an algorithm is not a table somebody must build."""
    assert _budget(carried_spec(
        "Tables: 43008 bits.",
        "def digest(v):\n    if fp_format == 1:\n        return v\n")) == []


# ------------------------------------- a threshold that cannot be reached


def _unreachable(entry_format, body):
    spec = one_test()
    spec["state"] = [{"name": "tbl", "organization": "65 entries",
                      "entry_format": entry_format, "size_bits": 8}]
    spec["algorithms"] = [{"name": "tick", "trigger": "decode", "pseudocode": body}]
    return [f for f in run_checks(spec) if f.code == "unreachable_literal_compare"]


def test_a_threshold_above_the_declared_field_width_is_an_error():
    """The live bug this exists for.

    An 8-bit counter incremented from 0 wraps or saturates at 255, so
    `>= 256` is never true and the paper's 256-instruction decay never fires.
    Nothing is assigned out of range, so the assignment scan sees nothing.
    """
    f = _unreachable("valid: 1 bit, decay_counter: 8 bits",
                     "t[r].decay_counter += 1\nif t[r].decay_counter >= 256:\n"
                     "    t[r].valid = 0")
    assert len(f) == 1
    assert f[0].severity == "error"
    assert "never be true" in f[0].message


@pytest.mark.parametrize("body,fires", [
    ("if t[r].decay_counter > 255:\n    pass", True),     # needs 256
    ("if t[r].decay_counter == 300:\n    pass", True),
    ("if t[r].decay_counter >= 255:\n    pass", False),   # the top value
    ("if t[r].decay_counter > 100:\n    pass", False),
    ("if t[r].decay_counter < 256:\n    pass", False),    # always true, milder
    ("if t[r].other_field >= 4096:\n    pass", False),    # not a declared field
    ("if (v >> 63) & 1 == 1:\n    pass", False),          # a bit test
    ("for i in range(65):\n    pass", False),             # a loop bound
])
def test_only_unreachable_comparisons_report(body, fires):
    got = bool(_unreachable("decay_counter: 8 bits", body))
    assert got is fires


def test_a_countdown_counter_is_silent():
    """Initialising to the ceiling and expiring at 0 is the correct encoding,
    and it is what the fix message recommends."""
    assert _unreachable(
        "decay_counter: 8 bits",
        "t[r].decay_counter = 255\nif t[r].decay_counter == 0:\n    pass") == []


def test_a_wide_enough_field_is_silent():
    assert _unreachable("decay_counter: 9 bits",
                        "if t[r].decay_counter >= 256:\n    pass") == []


def _unreachable_param(entry_format, body, params):
    spec = one_test()
    spec["state"] = [{"name": "tbl", "organization": "65 entries",
                      "entry_format": entry_format, "size_bits": 8}]
    spec["algorithms"] = [{"name": "tick", "trigger": "decode",
                           "pseudocode": body}]
    spec["parameters"] = params
    return [f for f in run_checks(spec) if f.code == "unreachable_literal_compare"]


def _knob(default):
    return [{"name": "decay_window", "type": "int", "default": default,
             "range": "[1, 1024]", "storage_impact": "none"}]


def test_a_threshold_named_by_a_parameter_is_still_unreachable():
    """The same dead guard, spelled with a knob instead of a number.

    The literal scan finds no number on the line and the store scan finds no
    store, so this form went through two runs of the real loop and four
    rounds of review untouched. What an implementer compiles in is the
    default, so the arithmetic is the one the literal form already does.
    """
    f = _unreachable_param(
        "valid: 1 bit, decay_counter: 8 bits",
        "t[r].decay_counter += 1\nif t[r].decay_counter >= decay_window:\n"
        "    t[r].valid = 0",
        _knob(256))
    assert len(f) == 1
    assert f[0].severity == "error"
    assert "decay_window" in f[0].message and "256" in f[0].message


@pytest.mark.parametrize("default,fires", [
    (256, True),
    (300, True),
    (255, False),     # the top value an 8-bit field holds
    (100, False),
])
def test_a_parameter_threshold_reports_only_when_it_cannot_be_reached(
        default, fires):
    got = bool(_unreachable_param(
        "decay_counter: 8 bits",
        "if t[r].decay_counter >= decay_window:\n    pass", _knob(default)))
    assert got is fires


def test_a_comparison_against_an_undeclared_name_is_silent():
    """A name with no declared default has no value to compare against, and
    guessing one manufactures an error that blocks the stage."""
    assert _unreachable_param(
        "decay_counter: 8 bits",
        "if t[r].decay_counter >= runtime_limit:\n    pass", []) == []


def test_unreachable_compare_is_a_self_consistency_code():
    import spec_review
    assert "unreachable_literal_compare" in spec_review._SELF_CONSISTENCY_CODES


# --------------------------------- a per-branch carry nobody budgeted for


def _carry_spec(reader_trigger, body, breakdown="Tables: 43008 bits.",
                hosts=None):
    spec = one_test()
    spec["algorithms"] = [
        {"name": "predict", "trigger": "prediction lookup",
         "pseudocode": "s = 0\nreturn s"},
        {"name": "update", "trigger": reader_trigger, "pseudocode": body},
    ]
    spec["host_interfaces"] = hosts or [{"need": "n", "description": "d"}]
    spec["resource_accounting"] = {"total_storage_bits": 100,
                                   "storage_breakdown": breakdown}
    return spec


def _budgetf(spec):
    return [f for f in run_checks(spec) if f.code == "unbudgeted_carried_state"]


def test_a_dotted_carry_read_after_prediction_is_reported():
    """`pred_info.*` read at branch resolution had to be held since predict.

    The earlier version of this check only looked at bare subscripted names,
    so a saved record reached as `pred_info.bank_wt_sum` was invisible.
    """
    f = _budgetf(_carry_spec(
        "Branch resolution or retirement / SC training",
        "d = pred_info.reg_digest_at_pred\nw = pred_info.bank_wt_sum\nreturn d + w"))
    assert len(f) == 1
    assert f[0].pointer == "/resource_accounting/storage_breakdown"
    # One record, one decision -- both fields in a single finding.
    assert "pred_info.bank_wt_sum" in f[0].message
    assert "pred_info.reg_digest_at_pred" in f[0].message


def test_a_decode_stage_signal_is_not_carried_storage():
    """`inst.writes_register` is available where it is read, so nothing holds
    it. Word overlap cannot tell it from a saved record -- both share
    "register" with any host interface that mentions registers -- so the
    reader's own trigger is what decides."""
    assert _budgetf(_carry_spec(
        "Instruction decode / rename stage for each decoded instruction",
        "if inst.writes_register:\n    return 1\nreturn 0")) == []


def _saver(spec, body="d = 1\nsave_pred_context(branch_id, b, d)\nreturn d"):
    spec["algorithms"][0]["pseudocode"] = body
    return spec


def test_a_carry_laundered_through_a_getter_is_reported():
    """`saved = get_pred_context(id, b)` produces the name on the line above
    every read, so the bare-name scan sees an ordinary local and the carry
    disappears. The same value written as a bare subscript was caught. The
    `save_*` twin in the prediction path is what makes the pair a checkpoint
    rather than a lookup of something the host already holds."""
    f = _budgetf(_saver(_carry_spec(
        "Branch resolution",
        "saved = get_pred_context(branch_id, b)\n"
        "w = saved.chosen_digest\nreturn w")))
    assert len(f) == 1
    assert f[0].pointer == "/resource_accounting/storage_breakdown"
    assert "saved.chosen_digest" in f[0].message
    assert "get_pred_context" in f[0].message


def test_a_getter_with_no_saving_twin_is_not_a_checkpoint():
    """A lone `get_*` at resolution may be reading state the host keeps for
    its own reasons. Only the pairing says something was held since predict."""
    assert _budgetf(_carry_spec(
        "Branch resolution",
        "saved = get_pred_context(branch_id, b)\n"
        "return saved.chosen_digest")) == []


def test_a_getter_the_spec_defines_is_not_a_checkpoint():
    """An algorithm the spec writes out is a derivation, not a latch."""
    spec = _saver(_carry_spec(
        "Branch resolution",
        "saved = get_pred_context(branch_id, b)\nreturn saved.chosen_digest"))
    spec["algorithms"].append({"name": "get_pred_context",
                               "trigger": "helper",
                               "pseudocode": "return recompute(b)"})
    assert _budgetf(spec) == []


def test_saying_a_carry_is_not_budgeted_does_not_budget_it():
    """The sentence admitting the gap is made of the same words as the thing
    omitted, so a plain token overlap read the admission as coverage: the one
    spec that said out loud what it had left out was the one this check
    stayed quiet on. The prompt asks for a reason the value is free, and
    "it is not budgeted" is the opposite of one."""
    f = _budgetf(_carry_spec(
        "Branch resolution",
        "d = pred_info.reg_digest\nreturn d",
        breakdown="Tables: 43008 bits. No per-branch checkpoint of this "
                  "pred info reg digest is budgeted."))
    assert len(f) == 1


def test_a_breakdown_that_sizes_the_carry_is_still_a_waiver():
    """The waiver survives: a breakdown that names and sizes the record has
    accounted for it, and the admission guard must not swallow that."""
    assert _budgetf(_carry_spec(
        "Branch resolution",
        "d = pred_info.reg_digest\nreturn d",
        breakdown="Tables: 43008 bits; pred info reg digest checkpoint: "
                  "780 bits per in-flight branch.")) == []


def test_declaring_a_host_interface_does_not_remove_it_from_the_budget():
    """At iso-storage the baseline does not need the latch, so moving it
    across the interface understates the feature."""
    f = _budgetf(_carry_spec(
        "Branch resolution",
        "d = pred_info.saved_digest\nreturn d",
        hosts=[{"need": "checkpointed register mask",
                "description": "At prediction time the available registers "
                               "must be saved in branch prediction state."}]))
    assert len(f) == 1
    assert "host interface does not settle it" in f[0].message


def test_a_budgeted_carry_is_silent():
    assert _budgetf(_carry_spec(
        "Branch resolution",
        "d = pred_info.saved_digest\nreturn d",
        breakdown="pred_info checkpoint: 780 bits per branch. Tables: 43008 bits.",
    )) == []


def test_a_container_method_is_not_a_saved_field():
    """`avail.get(b, [])` is the dialect, not a record somebody must size."""
    assert _budgetf(_carry_spec(
        "Branch resolution",
        "regs = avail.get(b, [])\nreturn regs")) == []


def test_a_bare_scalar_is_still_not_storage():
    assert _budgetf(_carry_spec(
        "Branch resolution", "if fp_format == 1:\n    return 1\nreturn 0")) == []


# ------------------------------------- `^` is XOR or a power; try both


def test_xor_over_decimal_operands_is_decided():
    """The blind spot this closes.

    A guard meant to stop `2^11 = 2048` being read as XOR refused any caret
    with no `0x` beside it -- and a real spec wrote its digest chains over
    decimal operands, so two wrong expected values went through as clean.
    """
    f = _arith(one_test(
        expect="Digest computed as (15 << 6) ^ (60 << 3) ^ 4 "
               "= 960 ^ 480 ^ 4 = 1444 (0x5A4), masked to 12 bits."))
    assert len(f) == 1 and f[0].severity == "error"
    assert "548" in f[0].message and "1444" in f[0].message


def test_an_exponent_reading_that_holds_keeps_it_quiet():
    """No context guessing: `2^11` is 9 as XOR and 2048 as a power, and one
    reading holding is enough to withdraw the claim."""
    assert _arith(one_test(expect="2^11 = 2048")) == []
    assert _arith(one_test(expect="The table holds 2^11 = 2048 entries.")) == []
    assert _arith(one_test(
        expect="Storage is 6 x (2^7 + 2^8 + 2^9) x 8 = 43008 bits.")) == []


def test_a_claim_false_under_every_reading_reports():
    assert _arith(one_test(expect="2^11 = 2047")) != []


def test_a_radix_restatement_does_not_block_the_chain():
    """"= 1444 (0x5A4)" parses as two expressions; the parenthetical has to
    come off before the final term can be read at all."""
    import spec_checks as sc
    assert sc._literal_arith("1444 (0x5A4)") is None
    assert sc._arith_readings(" 960 ^ 480 ^ 4 ") == [548]
    assert _arith(one_test(expect="digest = 960 ^ 480 ^ 4 = 548 (0x224)")) == []


def test_a_real_subexpression_is_not_stripped_as_a_restatement():
    """`(15 << 6)` and `min(count, 63)` must survive the restatement strip,
    or the evaluator decides a claim nobody made."""
    import spec_checks as sc
    readings = sc._arith_readings("(15 << 6) ^ 4")
    assert readings[0] == 964                 # the direct reading comes first
    assert 960 ** 4 in readings               # the power reading is also real
    assert sc._literal_arith("min(count, 63) & 0x3F") is None


def test_extra_readings_make_the_check_quieter_not_louder():
    """A coincidental power match withdraws the claim, and that is the
    intended direction: this severity fails the stage closed, so a missed
    slip costs a round while a false one costs a correct spec."""
    # 2 XOR 3 is 1, but 2**3 is 8, so the claim holds under one reading.
    assert _arith(one_test(expect="mask = 2 ^ 3 = 8")) == []


def test_a_huge_exponent_is_refused_rather_than_computed():
    """`960 ** 480 ** 4` must not be evaluated. The power reading drops out
    and the XOR reading decides the claim on its own."""
    import spec_checks as sc
    assert sc._arith_readings("960 ^ 480 ^ 4") == [548]


# ---------------------------- a span parameter stored without its countdown


def _span(spec):
    return [f for f in run_checks(spec) if f.code == "span_stored_directly"]


def test_span_parameter_stored_directly_is_an_error(spec):
    """The sR decay defect, third appearance and first time caught.

    `unrepresentable_default` waives a default of 2^B against a B-bit field
    because a counter really can span 2^B steps -- as a countdown. Nothing
    checked that the body encodes it that way, and a spec that stores the
    span directly truncates it to 0: the digest is invalidated one decode
    after it becomes valid, and the whole feature is inert.
    """
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024]"
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = decay_window"
    f = _span(spec)
    assert len(f) == 1
    assert f[0].severity == "error"
    assert f[0].pointer == "/algorithms/1/pseudocode"
    assert "256" in f[0].message and "255" in f[0].message
    assert "truncates to 0" in f[0].message


def test_the_countdown_encoding_is_silent(spec):
    """`- 1` is the whole difference between inert and correct."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024]"
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = decay_window - 1"
    assert _span(spec) == []


def test_a_parameter_that_fits_is_stored_freely(spec):
    """Only the waived span is in question. 200 into 8 bits is just a store."""
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = decay_window"
    assert _span(spec) == []


def test_an_oversized_default_stays_with_the_parameter_check(spec):
    """Above 2^B the default is wrong whatever the body does, and
    `unrepresentable_default` owns it. Reporting both would put two errors on
    one defect and send a reviewer to the pointer that does not fix it."""
    spec["parameters"][0]["default"] = 512
    spec["parameters"][0]["range"] = "[1, 1024]"
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = decay_window"
    assert _span(spec) == []
    assert [f for f in run_checks(spec) if f.code == "unrepresentable_default"]


def test_a_non_parameter_right_hand_side_is_not_a_span(spec):
    """`decay_ctr = other_field` says nothing about a default."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024]"
    spec["algorithms"][1]["pseudocode"] += "\ndecay_ctr = refill_value"
    assert _span(spec) == []


def test_a_field_qualified_target_is_still_the_field(spec):
    """Specs write the store through the table: `tbl[r].decay_ctr = knob`."""
    spec["parameters"][0]["default"] = 256
    spec["parameters"][0]["range"] = "[1, 1024]"
    spec["algorithms"][1]["pseudocode"] += (
        "\nregister_status_table[dst].decay_ctr = decay_window")
    assert len(_span(spec)) == 1


def test_span_stored_directly_is_a_self_consistency_code():
    """The paper names the span and never the encoding, so CONTRADICTED has
    no quote and UNSUPPORTED may not patch. Without this the reviewer
    diagnoses it correctly and the patch is refused."""
    import spec_review
    assert "span_stored_directly" in spec_review._SELF_CONSISTENCY_CODES


# ------------------------- an index bounded by the field it is read out of


def _bounds(spec):
    return [f for f in run_checks(spec) if f.code == "index_exceeds_dimension"]


def test_index_bounded_by_the_field_it_is_read_from(spec):
    """The update side of the recurring per-bank-vector defect.

    `predict` builds its register list at runtime, so no bound is derivable
    from the body and the check stayed silent through four runs. `update`
    reads the same index out of a latch field whose declared range the spec
    prints -- and that is enough to decide it.
    """
    spec["state"][0]["organization"] = (
        "4 banks; each bank tracks 12 logical registers, sub-table W0")
    spec["state"][0]["entry_format"] = "vector of 12 x 6-bit weights per bank"
    spec["state"].append({
        "name": "inflight latches",
        "organization": "32 entries",
        "entry_format": "{ sampled_valid: 1 bit, sampled_reg_id: 7 bits (0..47) }",
        "size_bits": 256,
        "indexing": "branch tag",
    })
    spec["algorithms"][0]["pseudocode"] = (
        "r_upd = latch.bank[b].sampled_reg_id\n"
        "x = W0[idx][r_upd]"
    )
    f = _bounds(spec)
    assert len(f) == 1 and f[0].severity == "error"
    assert "reaches 47" in f[0].message and "12 element" in f[0].message


def test_a_field_range_that_fits_the_dimension_is_clean(spec):
    spec["state"][0]["organization"] = (
        "4 banks; each bank tracks 12 logical registers, sub-table W0")
    spec["state"][0]["entry_format"] = "vector of 12 x 6-bit weights per bank"
    spec["state"].append({
        "name": "inflight latches",
        "organization": "32 entries",
        "entry_format": "{ sampled_slot: 4 bits (0..11) }",
        "size_bits": 128,
        "indexing": "branch tag",
    })
    spec["algorithms"][0]["pseudocode"] = (
        "r_upd = latch.bank[b].sampled_slot\n"
        "x = W0[idx][r_upd]"
    )
    assert _bounds(spec) == []


def test_field_ranges_come_only_from_entry_format():
    """A range in `organization` describes the structure, not one field.
    Attributing it to whichever name precedes it invents a bound."""
    import spec_checks as sc
    assert sc._declared_field_ranges({"state": [{
        "organization": "banks 0..7 of registers",
        "entry_format": "{ slot: 4 bits (0..11) }",
    }]}) == {"slot": 11}


def test_a_width_is_not_a_range():
    """`tag (12)` is twelve bits wide, not a value reaching 12."""
    import spec_checks as sc
    assert sc._declared_field_ranges(
        {"state": [{"entry_format": "valid (1), tag (12), ctr (3)"}]}) == {}


# ------------------------------- a branch ordered behind a guard implying it


def _dead(spec):
    return [f for f in run_checks(spec) if f.code == "unreachable_branch_guard"]


def _fp(spec, body):
    spec["algorithms"][0]["pseudocode"] = body
    return _dead(spec)


def test_shorter_prefix_first_makes_the_longer_arm_dead(spec):
    """The sR FP classifier: every FP32 NaN-boxed value has its top 16 bits
    set too, so the FP16 arm swallows all of them."""
    f = _fp(spec, (
        "if (v >> 48) == 0xFFFF:\n"
        "  digest = 1\n"
        "else if (v >> 32) == 0xFFFFFFFF:\n"
        "  digest = 2\n"
        "else:\n"
        "  digest = 3"
    ))
    assert len(f) == 1 and f[0].severity == "error"
    assert "0xffffffff" in f[0].message and "0xffff" in f[0].message


def test_longer_prefix_first_is_the_correct_order(spec):
    """The fix, which must not still read as an error afterwards."""
    assert _fp(spec, (
        "if (v >> 32) == 0xFFFFFFFF:\n"
        "  digest = 2\n"
        "else if (v >> 48) == 0xFFFF:\n"
        "  digest = 1"
    )) == []


def test_disjoint_prefixes_are_reachable(spec):
    """0xE0 >> 4 is 0xE, not 0xF, so neither guard implies the other."""
    assert _fp(spec, (
        "if (v >> 60) == 0xF:\n"
        "  digest = 1\n"
        "else if (v >> 56) == 0xE0:\n"
        "  digest = 2"
    )) == []


def test_guards_on_different_variables_do_not_interact(spec):
    assert _fp(spec, (
        "if (v >> 48) == 0xFFFF:\n"
        "  digest = 1\n"
        "else if (w >> 32) == 0xFFFFFFFF:\n"
        "  digest = 2"
    )) == []


def test_a_nested_chain_inside_an_else_if_arm_is_still_read(spec):
    """Chains nest, and the sR classifier sits inside the `else if` arm of an
    outer one. Walking only the outermost chain skips every guard that
    matters."""
    f = _fp(spec, (
        "if reg_id <= 31:\n"
        "  digest = 0\n"
        "else if reg_id <= 63:\n"
        "  if (v >> 48) == 0xFFFF:\n"
        "    digest = 1\n"
        "  else if (v >> 32) == 0xFFFFFFFF:\n"
        "    digest = 2\n"
        "else:\n"
        "  digest = 3"
    ))
    assert len(f) == 1


def test_an_identical_guard_repeated_is_dead(spec):
    assert len(_fp(spec, (
        "if (v >> 48) == 0xFFFF:\n"
        "  digest = 1\n"
        "else if (v >> 48) == 0xFFFF:\n"
        "  digest = 2"
    ))) == 1


def test_separate_chains_do_not_subsume_each_other(spec):
    """Two sibling `if`s with no `else` are both reachable."""
    assert _fp(spec, (
        "if (v >> 48) == 0xFFFF:\n"
        "  digest = 1\n"
        "if (v >> 32) == 0xFFFFFFFF:\n"
        "  digest = 2"
    )) == []


def test_new_codes_are_self_consistency_codes():
    import spec_review
    assert "unreachable_branch_guard" in spec_review._SELF_CONSISTENCY_CODES


# ------------------------------------- speculative state nobody unwinds


def _recovery(spec):
    return [f for f in run_checks(spec) if f.code == "missing_recovery_algorithm"]


def _spec_with_rob(spec, trigger="branch resolution", name="update"):
    spec["state"].append({
        "name": "victim producer table",
        "organization": "one entry per architectural register",
        "entry_format": "valid (1), rob_index (12)",
        "size_bits": 416,
        "indexing": "architectural register id",
    })
    spec["resource_accounting"]["total_storage_bits"] += 416
    spec["algorithms"].append({
        "name": name, "trigger": trigger,
        "pseudocode": "producer[r].rob_index = inst.rob_index",
    })
    return spec


def test_speculative_state_with_nothing_to_unwind_it_is_an_error(spec):
    """The live bug. Ten runs of the real loop wrote a squash algorithm and
    two did not; the paper cannot settle it either way, so no reviewer running
    spec-against-paper could report the omission, and none did."""
    f = _recovery(_spec_with_rob(spec))
    assert len(f) == 1
    assert f[0].severity == "error"
    assert f[0].pointer == "/algorithms/-"
    assert "rob_index" in f[0].message


def test_a_resolution_trigger_is_not_a_recovery(spec):
    """Every update algorithm already runs at resolution or commit. Matching
    those would make the check vacuous on exactly the specs it is for."""
    assert len(_recovery(_spec_with_rob(spec, trigger="at commit"))) == 1


@pytest.mark.parametrize("trigger,name", [
    ("pipeline flush", "unwind"),
    ("branch mispredict recovery", "unwind"),
    ("on squash", "unwind"),
    ("resolution", "recover_squash"),      # named, if not triggered, for it
])
def test_an_algorithm_that_unwinds_it_silences_the_check(spec, trigger, name):
    s = _spec_with_rob(spec)
    s["algorithms"].append({"name": name, "trigger": trigger,
                            "pseudocode": "producer[r].valid = 0"})
    assert _recovery(s) == []


def test_a_recovery_trigger_over_a_body_that_unwinds_nothing_is_not_a_recovery(spec):
    """The evasion, observed live. A run wrote `update` with the trigger
    "Branch commit or squash" over the ordinary weight-table update, touching
    no speculative entry. One word appended to a trigger string cleared the
    one check whose entire purpose is to insist the work exists, and the spec
    was written with the gap still in it."""
    s = _spec_with_rob(spec)
    s["algorithms"].append({
        "name": "update", "trigger": "Branch commit or squash",
        "pseudocode": (
            "for bank in range(num_banks):\n"
            "  regs = [r for r in bank_regs(bank) if status[r].valid]\n"
            "  if len(regs) > 0:\n"
            "    update_wt(random_choice(regs))"
        ),
    })
    assert len(_recovery(s)) == 1


def test_a_compound_trigger_counts_only_when_the_body_names_the_event(spec):
    """`commit or squash` over a body that clears something is ambiguous: the
    clear may belong to the commit path, and an unconditional one would run
    on every commit, which is a different bug. So the body has to say which
    event it is unwinding."""
    s = _spec_with_rob(spec)
    s["algorithms"].append({
        "name": "update", "trigger": "branch commit or squash",
        "pseudocode": "producer[r].decay_ctr = 0",
    })
    assert len(_recovery(s)) == 1
    s["algorithms"][-1]["pseudocode"] = (
        "if squashed:\n  producer[r].valid = 0"
    )
    assert _recovery(s) == []


def test_a_dedicated_recovery_algorithm_needs_no_event_word_in_its_body(spec):
    """The common shape, and the one every clean run of this loop produced: a
    trigger that names only the flush, and a loop that clears the table. The
    compound-trigger rule must not reach it."""
    s = _spec_with_rob(spec)
    s["algorithms"].append({
        "name": "pipeline_squash_recovery",
        "trigger": "Pipeline flush / branch misprediction squash",
        "pseudocode": (
            "for r = 0 to 64:\n"
            "  if status[r].valid == 0:\n"
            "    status[r].payload = 0\n"
            "    status[r].decay_ctr = 0"
        ),
    })
    assert _recovery(s) == []


@pytest.mark.parametrize("body", [
    "producer[r].valid = 0",
    "producer[r].payload = false",
    "producer[r].tag = -1",
    "invalidate(producer[r])",
    "restore_from_checkpoint(r)",
])
def test_the_shapes_of_undoing_the_loop_actually_writes(spec, body):
    s = _spec_with_rob(spec)
    s["algorithms"].append({"name": "squash", "trigger": "pipeline flush",
                            "pseudocode": body})
    assert _recovery(s) == []


def test_an_equality_test_is_not_a_clearing_store(spec):
    """`if x == 0` reads the field; it does not put anything back."""
    s = _spec_with_rob(spec)
    s["algorithms"].append({
        "name": "squash", "trigger": "pipeline flush",
        "pseudocode": "if producer[r].valid == 0:\n  log(r)",
    })
    assert len(_recovery(s)) == 1


def test_a_restore_from_architectural_state_is_a_recovery(spec):
    """The live false positive, verbatim from the run of 2026-09-24. It puts
    each squashed entry back from the architectural value rather than zeroing
    it, so it stores no clearing value and calls nothing named clear(). The
    check refused it, and no review patch could satisfy a check that rejects
    the correct unwind."""
    s = _spec_with_rob(spec)
    s["algorithms"].append({
        "name": "mispredict_recovery",
        "trigger": "Pipeline squash (branch mispredict)",
        "pseudocode": (
            "def mispredict_recovery(squashed_rob_indices):\n"
            "    for reg in range(num_logical_regs):\n"
            "        if tomasulo_table[reg].valid == 0 and tomasulo_table[reg].payload in squashed_rob_indices:\n"
            "            tomasulo_table[reg].valid = 1\n"
            "            tomasulo_table[reg].payload = digest_register(arch_reg_value(reg), arch_reg_type(reg))\n"
            "            tomasulo_table[reg].decay_ctr = decay_timeout - 1"
        ),
    })
    assert _recovery(s) == []


@pytest.mark.parametrize("body", [
    # A restore with no guard: it rewrites every entry, squashed or not.
    "producer[r].valid = 1",
    # A guard naming the squash that only reads under it.
    "if producer[r].rob_index in squashed:\n  log(r)",
    # A store under a guard that says nothing about what was squashed.
    "if producer[r].valid == 1:\n  producer[r].ctr = ctr + 1",
    # A store after the guarded block has ended, not inside it.
    "if producer[r].rob_index in squashed:\n  log(r)\nproducer[r].valid = 1",
])
def test_a_restore_counts_only_under_a_guard_naming_the_squashed_entries(spec, body):
    s = _spec_with_rob(spec)
    s["algorithms"].append({"name": "squash", "trigger": "pipeline flush",
                            "pseudocode": body})
    assert len(_recovery(s)) == 1


def test_a_spec_holding_no_speculative_state_needs_no_recovery(spec):
    """A table of counters is not tagged with an instruction that may never
    commit, so there is nothing for a flush to put back."""
    assert _recovery(spec) == []


def test_missing_recovery_is_a_self_consistency_code():
    """The paper defers recovery to future work, so CONTRADICTED has no quote
    to offer and UNSUPPORTED forbids the patch. Without the registration the
    one check that enforces the brief rather than the paper is unfixable."""
    import spec_review
    assert "missing_recovery_algorithm" in spec_review._SELF_CONSISTENCY_CODES


def test_a_vector_of_n_bit_counters_declares_a_width_not_a_length():
    """"Vector of 6-bit counters" says how wide each counter is, not how many
    there are. Read as a length it hands the bounds check a dimension the
    structure does not have -- small enough, in practice, to manufacture an
    `error` against indices that are perfectly legal."""
    assert spec_checks._declared_dimensions(
        {"entry_format": "Vector of 6-bit saturating counters"}) is None
    assert spec_checks._declared_dimensions(
        {"entry_format": "vector of 9 counters"}) == 9


# ------------------------------------- a tuning weight compiled in


def _tuning(spec, body, params=None):
    spec["algorithms"] = [{"name": "predict", "trigger": "lookup",
                           "pseudocode": body}]
    if params is not None:
        spec["parameters"] = params
    return [f for f in run_checks(spec)
            if f.code == "hardcoded_tuning_constant"]


def test_a_fractional_literal_no_knob_declares_is_reported(spec):
    """The live bug. Three runs shipped `* 2.5` with nothing in `parameters`
    naming it, so the sweep that was meant to measure the weight could never
    vary it -- while thirteen runs wrote the same multiplier as a knob, which
    is what makes this sampling rather than a reading of the paper.

    `error`, not `warn`, since run 6: a warning does not stop the gate, and
    this shipped twice more after the check started reporting it."""
    f = _tuning(spec, "s = 0\nfor b in 0 to 7:\n  s += w * 2.5\nreturn s",
                params=[])
    assert len(f) == 1
    assert f[0].severity == "error"
    assert f[0].pointer == "/algorithms/0/pseudocode"
    assert "2.5" in f[0].message


def test_a_fractional_literal_a_knob_declares_is_silent(spec):
    assert _tuning(
        spec, "s += w * sr_scale   # sr_scale = 2.5",
        params=[{"name": "sr_scale", "type": "float", "default": 2.5,
                 "range": "[0.0, 8.0]", "storage_impact": "None"}]) == []


def test_a_section_citation_is_not_a_tuning_weight(spec):
    """"Section 4.2" sits in the prose of half these specs. Scanning before
    comments are stripped reported it as a compiled-in weight in two runs."""
    assert _tuning(
        spec, "// randomly pick one available register (Section 4.2)\ns = 1",
        params=[]) == []


@pytest.mark.parametrize("body", [
    "d = val & 0x3F",                  # a mask
    "d = (val & 0x3F) << 6",           # a shift
    "for r in 0 to 64:\n  pass",       # a loop bound
    "if ctr >= 31:\n  pass",           # a saturation bound
])
def test_integer_constants_are_structure_not_tuning(spec, body):
    """Masks, shifts, widths and bounds are all integers and all structure.
    Flagging them would bury the one constant that matters."""
    assert _tuning(spec, body, params=[]) == []


# ---------------------------------- state only one end of the pipe touches


def _liveness(spec, state, algorithms, host=()):
    # Host interfaces are replaced, not inherited: the base fixture declares
    # an "evicted tag" need, and every table here whose name contains "tag"
    # would be silently exempted by it.
    spec["state"] = state
    spec["algorithms"] = algorithms
    spec["host_interfaces"] = list(host)
    return [f for f in spec_checks._check_state_liveness(spec)]


TABLE = {"name": "shadow tags", "organization": "64 entries",
         "entry_format": "tag (12), ctr (3)", "size_bits": 960,
         "indexing": "PC"}


def test_state_written_and_never_read_is_an_error(spec):
    """The live bug, first half: 34816 bits filled on every prediction and
    consulted by nothing. Neither reviewer could see it -- the producer and
    the consumer sit in different spec units, and the finding is that the
    consumer does not exist."""
    f = _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "shadow_tags[PC] = evicted"},
    ])
    assert [x.code for x in f] == ["write_only_state"]
    assert f[0].severity == "error"
    assert "960 bits" in f[0].message


def test_state_read_and_never_written_is_an_error(spec):
    """The other half, and the worse one: an implementer cannot even write
    the dead code. Every read returns whatever the array was initialized to,
    so the behaviour described is not the behaviour that gets built."""
    f = _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "return shadow_tags[PC].ctr"},
    ])
    assert [x.code for x in f] == ["unfilled_state"]
    assert f[0].severity == "error"


def test_a_table_both_read_and_written_is_silent(spec):
    assert _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "return shadow_tags[PC].ctr"},
        {"name": "update", "trigger": "resolution",
         "pseudocode": "shadow_tags[PC].ctr = 0"},
    ]) == []


def test_state_no_algorithm_mentions_at_all_is_silent(spec):
    """Zero traffic in both directions is a different complaint, and one this
    check would state badly."""
    assert _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup", "pseudocode": "return 0"},
    ]) == []


@pytest.mark.parametrize("call", [
    "increment_sat(shadow_tags[PC].ctr)",   # verb first
    "sat_update(shadow_tags[PC].ctr, 1)",   # verb second
    "reset(shadow_tags[PC])",
])
def test_a_table_mutated_through_a_call_counts_as_written(spec, call):
    """Counter tables are rarely assigned to; they are handed to something
    that writes them in place. An earlier version of this check anchored the
    verb at the start of the callee, scored `sat_update` as a read, and
    reported two live weight tables as tables nothing fills."""
    assert _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "return shadow_tags[PC].ctr"},
        {"name": "update", "trigger": "resolution", "pseudocode": call},
    ]) == []


def test_a_read_modify_write_is_both(spec):
    """`-=` is the only thing a decay counter ever does to itself. Reading it
    as neither reported the counter as unfilled."""
    assert _liveness(spec, [TABLE], [
        {"name": "decay", "trigger": "every cycle",
         "pseudocode": "shadow_tags[PC].ctr -= 1"},
    ]) == []


@pytest.mark.parametrize("op", ["==", "!=", ">=", "<="])
def test_a_comparison_is_not_an_assignment(spec, op):
    """`>=` and `<=` reaching the augmented-assignment branch would score
    every guarded read as a write and silence the check."""
    f = _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": f"if shadow_tags {op} 3:\n  return 1"},
    ])
    assert [x.code for x in f] == ["unfilled_state"]


def test_a_write_through_a_row_alias_reaches_the_table(spec):
    """`row = table[i]` then `row.field = x` is the shape the live bug was
    written in. Following only the base name credits the write to a local
    and the table reads as filled by nobody."""
    assert _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "return shadow_tags[PC].ctr"},
        {"name": "update", "trigger": "resolution",
         "pseudocode": "row = shadow_tags[PC]\nrow.ctr = 0"},
    ]) == []


def test_a_row_alias_alone_is_not_a_read(spec):
    """Taking the handle is not consuming a value. If it counted as a read,
    the write-only table -- which must fetch the row before writing into it
    -- would look alive."""
    f = _liveness(spec, [TABLE], [
        {"name": "predict", "trigger": "lookup",
         "pseudocode": "row = shadow_tags[PC]\nrow.ctr = 0"},
    ])
    assert [x.code for x in f] == ["write_only_state"]


def test_a_field_name_is_not_the_table_that_holds_it(spec):
    """Generic-token stripping collapses "decay table" and `decay_ctr` to the
    same single token, so a write of the counter was credited to the table."""
    assert _liveness(
        spec,
        [{"name": "decay table", "organization": "4 counters",
          "entry_format": "decay_ctr (8 bits)", "size_bits": 32,
          "indexing": "bank"}],
        [{"name": "refresh", "trigger": "completion",
          "pseudocode": "decay_ctr = 255"}]) == []


def test_a_local_sharing_one_token_is_not_the_table(spec):
    """`h_wt`, the local holding a hash, shares the token `wt` with a table
    called `sr_wt`. Prefix scoring credited it as a write, and a table with
    one spurious write looks alive."""
    f = _liveness(
        spec,
        [{"name": "sr_wt", "organization": "8 banks", "entry_format": "ctr (6)",
          "size_bits": 48, "indexing": "PC"}],
        [{"name": "predict", "trigger": "lookup",
          "pseudocode": "h_wt = hash(PC)\nreturn sr_wt[h_wt]"}])
    assert [x.code for x in f] == ["unfilled_state"]


def test_two_entries_sharing_a_name_prefix_are_told_apart(spec):
    """Every token of `sr_status` is a token of `sr_status_checkpoints`, so
    subset matching cannot separate them and overlap scoring ties."""
    f = _liveness(
        spec,
        [{"name": "sr_status", "organization": "65 entries",
          "entry_format": "valid (1)", "size_bits": 65, "indexing": "reg"},
         {"name": "sr_status_checkpoints", "organization": "per branch",
          "entry_format": "valid (1)", "size_bits": 1024, "indexing": "rob"}],
        [{"name": "decode", "trigger": "decode",
          "pseudocode": "sr_status[r].valid = 0"},
         {"name": "update", "trigger": "commit",
          "pseudocode": "return sr_status_checkpoints[rob].valid"}])
    assert [(x.pointer, x.code) for x in f] == [
        ("/state/0", "write_only_state"),
        ("/state/1", "unfilled_state"),
    ]


def test_state_the_host_declares_it_fills_needs_no_writer(spec):
    """`host_interfaces` is where a spec says what it does not compute. A
    structure handed over populated has no writer here by design."""
    assert _liveness(
        spec, [TABLE],
        [{"name": "predict", "trigger": "lookup",
          "pseudocode": "return shadow_tags[PC].ctr"}],
        host=[{"need": "shadow tags", "description": "from the host"}]) == []


def test_a_description_mentioning_the_table_does_not_exempt_it(spec):
    """Descriptions name other structures in passing -- sR's ROB-index
    interface explains the index is used "to index checkpoints" -- and
    reading them exempted the largest unfilled table in the spec."""
    f = _liveness(
        spec, [TABLE],
        [{"name": "predict", "trigger": "lookup",
          "pseudocode": "return shadow_tags[PC].ctr"}],
        host=[{"need": "ROB index", "description": "used to index shadow tags"}])
    assert [x.code for x in f] == ["unfilled_state"]


# ------------------------------------------ an algorithm that does nothing


def _hollow(spec, algo):
    spec["algorithms"] = [algo]
    return spec_checks._check_hollow_algorithms(spec)


def test_an_empty_body_under_notes_that_claim_work_is_an_error(spec):
    """The live bug: `pass` under notes reading "Restores the Tomasulo-like
    table". Everything downstream reads the notes, so the spec asserts a
    recovery it does not contain."""
    f = _hollow(spec, {
        "name": "squash", "trigger": "squash",
        "pseudocode": "// recovery is left to future work\npass",
        "notes": "Restores the table to its state at the squashed branch.",
    })
    assert [x.code for x in f] == ["hollow_algorithm"]
    assert f[0].severity == "error"
    assert "Restores" in f[0].message


def test_a_long_comment_is_still_an_empty_body(spec):
    """A stub explaining at length why it is a stub is still a stub, and the
    prose is what makes it read like an implementation."""
    f = _hollow(spec, {
        "name": "squash", "trigger": "squash",
        "pseudocode": "# The paper defers this to future work.\n"
                      "# We do not restore from checkpoints.\n"
                      "# See Section 5.\npass",
        "notes": "Invalidates every speculative entry.",
    })
    assert [x.code for x in f] == ["hollow_algorithm"]


def test_an_empty_body_with_no_claim_over_it_is_a_warning(spec):
    f = _hollow(spec, {"name": "squash", "trigger": "squash",
                       "pseudocode": "pass"})
    assert [(x.code, x.severity) for x in f] == [("empty_algorithm", "warn")]


def test_notes_about_the_paper_are_not_a_claim_about_the_body(spec):
    """"recovery is left to future work" describes the paper. Only a claim in
    the present tense describes this algorithm."""
    f = _hollow(spec, {
        "name": "squash", "trigger": "squash", "pseudocode": "pass",
        "notes": "The paper leaves recovery to future work.",
    })
    assert [x.code for x in f] == ["empty_algorithm"]


def test_a_body_that_does_something_is_silent(spec):
    assert _hollow(spec, {
        "name": "squash", "trigger": "squash",
        "pseudocode": "for e in table:\n  e.valid = 0",
        "notes": "Restores the table.",
    }) == []


# ------------------------------- two algorithms claiming the same recovery


RECOVERS = {"name": "recover", "trigger": "on mispredict",
            "pseudocode": "for e in status:\n  e.valid = 0"}


def test_a_recovery_beside_a_no_op_on_the_same_event_is_an_error(spec):
    """What `_check_recovery` cannot see. It asks whether *any* algorithm
    recovers, so a spec satisfies it by adding one -- which is what the run
    did, bolting on `recover_status_table` and leaving `squash` as `pass`.
    The gap was still in the document, one algorithm to the left."""
    spec["algorithms"] = [
        {"name": "squash", "trigger": "squash (mispredict recovery)",
         "pseudocode": "pass"},
        RECOVERS,
    ]
    f = spec_checks._check_recovery_conflict(spec)
    assert [(x.pointer, x.code) for x in f] == [
        ("/algorithms/0", "contradictory_recovery")]
    assert f[0].severity == "error"
    assert "recover" in f[0].message


def test_one_recovery_algorithm_is_not_a_conflict(spec):
    spec["algorithms"] = [
        {"name": "predict", "trigger": "lookup", "pseudocode": "return 1"},
        RECOVERS,
    ]
    assert spec_checks._check_recovery_conflict(spec) == []


def test_two_working_recoveries_are_only_a_warning(spec):
    """Both do the work, so neither is a lie -- but an implementer still has
    to be told the order."""
    spec["algorithms"] = [
        RECOVERS,
        {"name": "flush_digests", "trigger": "on flush",
         "pseudocode": "for e in digests:\n  e.valid = 0"},
    ]
    f = spec_checks._check_recovery_conflict(spec)
    assert {x.severity for x in f} == {"warn"}
    assert {x.code for x in f} == {"duplicate_recovery"}


def test_ordinary_events_may_share_a_trigger(spec):
    """Two algorithms on `commit` are ordinary: an update and a retirement do
    different work on one event. Only recovery is all-or-nothing."""
    spec["algorithms"] = [
        {"name": "update", "trigger": "commit", "pseudocode": "ctr += 1"},
        {"name": "retire", "trigger": "commit", "pseudocode": "head += 1"},
    ]
    assert spec_checks._check_recovery_conflict(spec) == []


# ------------------------------------- a structure under its sub-table name


def _ut_spec(spec, predict_body, update_body, entry_format, organization=None):
    """A spec whose pseudocode only ever names the sub-tables, never the
    state entry -- the shape every sR run has written and the one that used
    to make the weight tables invisible to every traffic-based check."""
    spec["state"] = [{
        "name": "usefulness_weight_tables",
        "organization": organization or "3 tables (UT0, UT1, UT2) of 8 entries",
        "entry_format": entry_format,
        "size_bits": 1296,
        "indexing": "skewed hash of PC",
    }]
    spec["algorithms"] = [
        {"name": "predict", "trigger": "lookup", "pseudocode": predict_body},
        {"name": "update", "trigger": "resolution", "pseudocode": update_body},
    ]
    return spec


def test_a_subtable_name_resolves_to_the_entry_that_declares_it(spec):
    """Run 6's blind spot. `_state_traffic` matched a state entry by name or
    by token set, and the pseudocode writes only `UT0`/`WT0`, which share no
    token with `usefulness_weight_tables`. Both weight tables reported zero
    reads and zero writes, so the liveness check stayed silent about
    structures it could not see rather than finding them clean."""
    _ut_spec(spec,
             "for ut in (UT0, UT1, UT2):\n  s += ut[i][r]",
             "for ut in (UT0, UT1, UT2):\n  ut[i][r] = 0",
             "Vector of 6-bit counters, one per slot (9 total)")
    reads, writes = spec_checks._state_traffic(spec)
    assert reads[0] == {"predict"} and writes[0] == {"update"}


def test_ordinary_prose_words_are_not_sub_table_names(spec):
    """The harvest reads a state entry's prose, which says "hash of PC" as
    readily as "(UT0, UT1, UT2)". Admitting `PC` would map a local every
    algorithm uses onto the weight tables and call a dead table live."""
    owners = spec_checks._subtable_owners([{
        "name": "wt", "organization": "8 banks of WT0",
        "indexing": "hash of PC and register digest",
    }])
    assert "WT0" in owners
    assert "hash" not in owners and "register" not in owners


def test_a_table_the_prose_only_mentions_is_still_an_orphan(spec):
    """The loose token match stays: resolving sub-tables must not turn
    `orphan_state` off for a structure nothing touches."""
    spec["state"].append({
        "name": "loop termination buffer", "organization": "16 entries",
        "entry_format": "trip (12)", "size_bits": 192, "indexing": "seq",
    })
    spec["resource_accounting"]["total_storage_bits"] = 6368
    assert "orphan_state" in codes(run_checks(spec))


# ----------------------------------- the declaration as the common referent


def test_an_index_from_a_narrow_field_cannot_cover_the_dimension(spec):
    """The live bug in run 6, and the third run in a row to carry some
    version of it. `selected_pred_reg` is 4 bits, so it names 16 positions;
    the vector it subscripts is declared "one per logical register (65
    total)". `_check_index_consistency` cannot see this -- it compares
    algorithms to each other, and here both sides agree with themselves."""
    _ut_spec(spec,
             "for ut in (UT0, UT1, UT2):\n  s += ut[i][r]",
             "idx = latch.bank[b].selected_pred_reg\n"
             "for ut in (UT0, UT1, UT2):\n  ut[i][idx] = 0",
             "Vector of 6-bit counters, one per logical register (65 total)")
    spec["state"].append({
        "name": "inflight", "organization": "128 entries",
        "entry_format": "selected_pred_reg (4 bits)",
        "size_bits": 512, "indexing": "branch id",
    })
    f = [x for x in run_checks(spec) if x.code == "index_too_narrow"]
    assert len(f) == 1 and f[0].severity == "error"
    assert "4 bits" in f[0].message and "65" in f[0].message


def test_an_index_wide_enough_for_the_dimension_is_silent(spec):
    """The same spec with the declaration the paper's figure supports: a
    per-bank vector of 9, which 4 bits reaches comfortably."""
    _ut_spec(spec,
             "for ut in (UT0, UT1, UT2):\n  s += ut[i][r]",
             "idx = latch.bank[b].selected_pred_reg\n"
             "for ut in (UT0, UT1, UT2):\n  ut[i][idx] = 0",
             "Vector of 6-bit counters, one per slot in the bank (9 total)")
    spec["state"].append({
        "name": "inflight", "organization": "128 entries",
        "entry_format": "selected_pred_reg (4 bits)",
        "size_bits": 512, "indexing": "branch id",
    })
    assert "index_too_narrow" not in codes(run_checks(spec))


def test_a_vector_entry_handed_to_a_scalar_mutator_is_an_error(spec):
    """Run 5's `increment_sat(sr_ut[b].UT0[h])`. `UT0[h]` reaches an entry,
    and the entry is declared a vector, so the mutator is handed every
    weight in it. Nothing in the file said so: the subscript depth is right
    for the table and wrong for the value."""
    _ut_spec(spec,
             "s += 1",
             "increment_sat(UT0[h])",
             "Vector of 8 or 9 6-bit signed counters")
    f = [x for x in run_checks(spec) if x.code == "unsubscripted_leaf"]
    assert len(f) == 1 and f[0].severity == "error"
    assert "UT0[h]" in f[0].message


def test_binding_a_row_spends_a_subscript(spec):
    """`vec = ut[idx]` then `vec[r]` reaches an element, not a vector. The
    first draft counted only the subscripts on the line and reported this
    correct pair as a defect."""
    _ut_spec(spec,
             "for ut in (UT0, UT1, UT2):\n  vec = ut[idx]\n  s += vec[r]",
             "s = 0",
             "Vector of 6-bit counters, one per slot (9 total)")
    assert "unsubscripted_leaf" not in codes(run_checks(spec))


def test_handing_a_whole_table_to_a_bulk_helper_is_not_a_leaf_use(spec):
    """`update_sc_weights(sr_ut[r], PC, ...)` means what it says. An earlier
    draft fired on any call and reported a spec that was being explicit."""
    _ut_spec(spec,
             "s = 0",
             "update_sc_weights(UT0[r], PC, correct)",
             "Vector of 6-bit counters, one per slot (9 total)")
    assert "unsubscripted_leaf" not in codes(run_checks(spec))


def test_a_path_through_a_subscript_is_not_the_value_at_its_end(spec):
    """In `sr_ut[r].UT0[h]` only the second half is the leaf. Reporting the
    first says the wrong thing about a line that is fine up to that point."""
    _ut_spec(spec,
             "s = 0",
             "increment_sat(sr_ut[r].UT0[h])",
             "Vector of 8 or 9 6-bit signed counters")
    f = [x for x in run_checks(spec) if x.code == "unsubscripted_leaf"]
    assert len(f) == 1 and "UT0[h]" in f[0].message


# ------------------------------------------- one feature, not the whole chip


def test_a_feature_over_the_papers_own_figure_is_reported(spec):
    """Run 6 came in at 87655 bits against a 1572864-bit track and stayed
    quiet, while sitting 1.63x over the 53863 bits the paper allots the
    feature -- a number that spec stated in the field beside the total."""
    spec["resource_accounting"]["logic_cost_notes"] = (
        "Not budgeted in the paper's Table 3, so this exceeds the paper's "
        "4000 bits.")
    f = [x for x in run_checks(spec, budget_bits=1 << 20)
         if x.code == "feature_budget_fit"]
    assert len(f) == 1 and f[0].severity == "warn"
    assert "4000" in f[0].message and "6176" in f[0].message


def test_a_caller_supplied_feature_budget_fails_the_gate(spec):
    """A figure a caller passes in is a commitment; one read out of prose is
    the spec disclosing its position, and failing closed on an honest
    disclosure teaches the next round to stop disclosing."""
    f = [x for x in run_checks(spec, 1 << 20, feature_budget_bits=1000)
         if x.code == "feature_budget_fit"]
    assert len(f) == 1 and f[0].severity == "error"


def test_a_bit_count_the_paper_is_not_credited_with_is_not_a_budget(spec):
    """`resource_accounting` prose is full of bit counts. One run wrote
    "65 * 23 bits = 1495 bits per branch" two clauses from the word budget,
    and reading that as the allowance would compare the whole structure
    against one branch's worth of it."""
    spec["resource_accounting"]["logic_cost_notes"] = (
        "A snapshot per in-flight branch costs 1495 bits, excluded from the "
        "budget.")
    assert spec_checks._declared_feature_budget(spec) is None


def test_a_feature_inside_the_papers_figure_is_silent(spec):
    spec["resource_accounting"]["logic_cost_notes"] = (
        "The paper's Table 3 budgets 53863 bits.")
    assert "feature_budget_fit" not in codes(run_checks(spec, 1 << 20))


# --------------------------------------- a unit test against its algorithms


def test_a_test_naming_a_layout_the_spec_lacks_is_an_error(spec):
    """Run 6's `digest_generation_fp_variants` expects FP16 to extract
    Val[15:13] and FP32 Value[31:26], over a `write` that implements FP64
    only because U5 was resolved as "treat every value as FP64". An
    integration agent turns that line into an assertion, so it fails against
    a port that implements the spec correctly."""
    spec["unit_tests"].append({
        "name": "fp variants",
        "given": "FP16 and FP32 registers",
        "expect": "FP16 extracts Val[15:13], FP32 extracts Value[31:26].",
    })
    f = [x for x in run_checks(spec) if x.code == "untested_behaviour"]
    assert len(f) == 1 and f[0].severity == "error"
    assert "[15:13]" in f[0].message


def test_a_range_the_pseudocode_spells_as_a_mask_is_declared(spec):
    """Pseudocode writes `(value >> 55) & 0x1FF` where a test writes
    [63:55]. Comparing notations rather than cuts reported three correct
    digest tests as asserting behaviour their own spec did not have."""
    spec["algorithms"][0]["pseudocode"] = "d = (value >> 55) & 0x1FF"
    spec["unit_tests"].append({
        "name": "fp64 digest", "given": "an FP register completes",
        "expect": "the digest takes Value[63:55], giving 0x181.",
    })
    assert "untested_behaviour" not in codes(run_checks(spec))


def test_a_bare_range_describes_where_a_result_lands(spec):
    """"Leading count 61 shifted to [8:3]" is a statement about the digest
    being assembled, not a claim about a source layout. Requiring the
    identifier is what separates the two."""
    spec["unit_tests"].append({
        "name": "int digest", "given": "an INT register completes",
        "expect": "leading count shifted to [8:3] gives 0x1E8.",
    })
    assert "untested_behaviour" not in codes(run_checks(spec))


def test_a_conditional_premise_under_a_flat_expectation_is_reported(spec):
    """Run 6's test hedged its `given` -- "(if classification is supported)"
    -- and stated its `expect` flatly. The gate cannot tell a real failure
    from a configuration the spec declined to choose."""
    spec["unit_tests"].append({
        "name": "fp variants",
        "given": "FP16 and FP32 registers (if classification is supported)",
        "expect": "the digest equals 0x140.",
    })
    f = [x for x in run_checks(spec) if x.code == "conditional_test_premise"]
    assert len(f) == 1 and f[0].severity == "warn"


# ------------------------------------------------- what no unit test covers


def test_a_state_entry_no_test_names_is_reported(spec):
    spec["unit_tests"] = [spec["unit_tests"][0]]
    got = [x for x in run_checks(spec) if x.code == "untested_state"]
    assert {x.pointer for x in got} == {"/state/0/name", "/state/1/name"}
    assert {x.severity for x in got} == {"warn"}


def test_a_test_naming_a_sub_table_covers_its_parent(spec):
    """No test writes out `usefulness_weight_tables`; they name `UT0`."""
    _ut_spec(spec, "s += UT0[i][r]", "UT0[i][r] = 0",
             "Vector of 6-bit counters, one per slot (9 total)")
    spec["unit_tests"] = [
        {"name": "ut0 saturates", "given": "8 updates on UT0",
         "expect": "UT0[i][r] == 31"},
        {"name": "predict sums", "given": "one lookup",
         "expect": "predict returns 3"},
        {"name": "update trains", "given": "one resolution",
         "expect": "update writes 1"},
    ]
    assert "untested_state" not in codes(run_checks(spec))


def test_a_counter_no_test_walks_over_time_is_reported(spec):
    """The only lever this stage has on a temporal bug. Run 6's decay
    counter could wedge a digest valid forever, and no check that reads one
    document at one instant could see it."""
    spec["unit_tests"][2]["given"] = "one resolved branch"
    spec["unit_tests"][2]["expect"] = "update sets decay_ctr = 200"
    got = [x for x in run_checks(spec)
           if x.code == "untested_counter_lifecycle"]
    assert got and {x.severity for x in got} == {"warn"}


# -------------------------------------- context the host is said to supply


def test_a_read_the_host_interfaces_declare_is_not_missing(spec):
    """Sixteen of the twenty findings on run 5 were these, and the four real
    defects produced none. A name a `host_interfaces` entry covers has a
    stated producer; it is just not an algorithm."""
    spec["algorithms"][0]["pseudocode"] = "x = evicted_tag\nreturn x"
    assert "unproduced_context" not in codes(run_checks(spec))


def test_an_object_the_trigger_names_arrives_with_the_call(spec):
    """"branch resolution" hands `update` a branch."""
    spec["algorithms"][1]["pseudocode"] += "\nif branch.taken: v.ctr = 1"
    got = [x for x in spec_checks._check_context_writes(spec)
           if x.code == "unproduced_context"]
    assert got == []


def test_a_read_nothing_declares_is_still_reported(spec):
    """The suppression is for names the spec says arrive from outside. A
    name nothing declares is still the missing half of a handshake."""
    spec["algorithms"][0]["pseudocode"] += "\nsum += mystery_oracle * 2"
    got = [x for x in spec_checks._check_carried_state(spec)
           if x.code == "unproduced_context"]
    assert len(got) == 1 and "mystery_oracle" in got[0].message


# ------------------------------------------------ the generic-word filter


def test_generic_words_are_dropped_in_their_stemmed_form():
    """GENERIC_TOKENS is written as words and what gets filtered is stems,
    so half the list never matched: `stem("entries")` is "entri". The words
    that happened to be their own stem were dropped and the rest leaked
    through as if they carried meaning -- which suppressed real
    `unreferenced_param` findings in two runs."""
    for word in ("entries", "registers", "tables", "values"):
        assert tokens(f"{word} of decay") == {"decay"}, word


def test_a_dimension_is_not_paired_with_a_field_that_shares_a_word(spec):
    """The live one, 2026-09-24: max_in_flight_branches (256) is a FIFO depth
    in the size_formula, and the representability check paired it with a
    1-bit flag, max_useful_positive, on the word "max". No review could fix
    that without distorting the spec. A name outside log2() in a size_formula
    sizes a structure; its value is stored in no field."""
    spec["state"].append({
        "name": "snapshot buffer", "organization": "FIFO per in-flight branch",
        "entry_format": "active (1), max_useful_positive (1)", "size_bits": 512,
        "size_formula": "max_in_flight_branches * 2", "indexing": "branch id"})
    spec["parameters"].append({"name": "max_in_flight_branches", "type": "int",
                               "default": 256, "range": "[1, 1024]"})
    assert not [f for f in run_checks(spec) if f.code == "unrepresentable_default"
                and f.pointer == f"/parameters/{len(spec['parameters']) - 1}/default"]
