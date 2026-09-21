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
        "unit_tests": [
            {
                "name": "counter saturates",
                "given": "8 taken branches on one entry",
                "expect": "ctr == 7 and does not wrap to 0",
            }
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
