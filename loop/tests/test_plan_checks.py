"""Tests for the deterministic plan checks.

Every case starts from the worked fixture trio -- the tinysc spec, and the
port plan and test plan that carry it into the toy host -- and breaks exactly
one thing. Starting from a real pair rather than an invented one is the point:
a check that only fires on a hand-built minimal document usually fires on real
plans too, and the fixture is the only plan pair in the repository that a
human has read end to end.

Tests assert on codes, not on message text, the way test_spec_checks.py does.
Two of them assert that a check does NOT fire; those pin the false positives
that a future contributor would otherwise "fix" into existence.
"""

import json

import pytest

from plan_checks import run_checks

FIXTURES = __import__("pathlib").Path(__file__).resolve().parent / "fixtures"
HOST_ROOT = FIXTURES / "toyhost"


def codes(findings):
    return sorted(f.code for f in findings)


def severity_of(findings, code):
    return next(f.severity for f in findings if f.code == code)


@pytest.fixture
def spec():
    return json.loads((FIXTURES / "tinysc.spec.json").read_text())


@pytest.fixture
def plan():
    return json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())


@pytest.fixture
def tests():
    return json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


# --------------------------------------------------------------- the baseline
def test_the_worked_pair_is_clean(spec, plan, tests):
    """If this ever fails, either a check is wrong or the fixture is. Both are
    worth stopping for, which is why the assertion is exact equality."""
    assert run_checks(spec, plan, tests) == []


def test_the_worked_pair_is_clean_against_the_real_checkout(spec, plan, tests):
    assert run_checks(spec, plan, tests, host_root=HOST_ROOT) == []


# ------------------------------------------------------------------ coverage
def test_an_unmapped_state_element_is_an_error(spec, plan, tests):
    plan["spec_map"] = [e for e in plan["spec_map"] if e["spec_pointer"] != "/state/1"]
    found = run_checks(spec, plan, tests)
    assert "uncovered_state" in codes(found)
    assert severity_of(found, "uncovered_state") == "error"
    assert [f.pointer for f in found if f.code == "uncovered_state"] == ["/spec/state/1"]


def test_an_unmapped_algorithm_is_an_error(spec, plan, tests):
    plan["spec_map"] = [e for e in plan["spec_map"] if e["spec_pointer"] != "/algorithms/0"]
    assert "uncovered_algorithm" in codes(run_checks(spec, plan, tests))


def test_an_unresolved_interface_need_is_an_error(spec, plan, tests):
    plan["interface_resolutions"].pop()
    assert "uncovered_interface" in codes(run_checks(spec, plan, tests))


def test_a_parameter_with_no_knob_is_an_error(spec, plan, tests):
    plan["knobs"] = [k for k in plan["knobs"] if k["spec_parameter"] != "TINYSC_THRESHOLD"]
    assert "uncovered_parameter" in codes(run_checks(spec, plan, tests))


def test_a_spec_unit_test_nobody_implements_is_an_error(spec, plan, tests):
    tests["correctness"] = [
        e for e in tests["correctness"] if e.get("spec_pointer") != "/unit_tests/2"
    ]
    assert "uncovered_unit_test" in codes(run_checks(spec, plan, tests))


# -------------------------------------------------------- referential integrity
def test_a_repeated_hook_id_is_an_error(spec, plan, tests):
    plan["hook_points"][1]["id"] = plan["hook_points"][0]["id"]
    assert "duplicate_hook_id" in codes(run_checks(spec, plan, tests))


def test_a_hook_id_naming_nothing_is_an_error(spec, plan, tests):
    plan["spec_map"][0]["hook_ids"] = ["no_such_hook"]
    assert "unknown_hook_id" in codes(run_checks(spec, plan, tests))


def test_a_repeated_test_id_is_an_error(spec, plan, tests):
    tests["performance"][0]["id"] = tests["correctness"][0]["id"]
    assert "duplicate_test_id" in codes(run_checks(spec, plan, tests))


def test_a_risk_detected_by_nothing_real_is_an_error(spec, plan, tests):
    plan["risks"][0]["detected_by"] = "no_such_test"
    assert "unknown_test_id" in codes(run_checks(spec, plan, tests))


def test_a_pointer_that_does_not_resolve_is_an_error(spec, plan, tests):
    plan["spec_map"][0]["spec_pointer"] = "/state/99"
    assert "unresolved_pointer" in codes(run_checks(spec, plan, tests))


# ------------------------------------------------------------ plan versus spec
def test_a_pointer_aimed_at_the_wrong_element_is_caught_by_its_echo(spec, plan, tests):
    """The off-by-one this exists for: /state/1 is covered either way, so
    every coverage count is satisfied while the integrator is pointed at the
    wrong structure."""
    plan["spec_map"][0]["spec_pointer"] = "/state/1"
    found = codes(run_checks(spec, plan, tests))
    assert "spec_item_mismatch" in found
    assert "uncovered_state" in found


def test_a_misquoted_need_is_an_error(spec, plan, tests):
    plan["interface_resolutions"][0]["need"] = "Something the paper never said"
    assert "interface_need_mismatch" in codes(run_checks(spec, plan, tests))


def test_a_knob_naming_the_wrong_parameter_is_an_error(spec, plan, tests):
    plan["knobs"][1]["spec_parameter"] = "TINYSC_HIST_BITS"
    assert "knob_parameter_mismatch" in codes(run_checks(spec, plan, tests))


def test_a_knob_shipping_a_different_default_is_an_error(spec, plan, tests):
    plan["knobs"][1]["default"] = 512
    assert "knob_default_drift" in codes(run_checks(spec, plan, tests))


# ---------------------------------------------------------------- the macros
def test_a_macro_outside_the_generated_header_convention_is_an_error(spec, plan, tests):
    """Schema-legal (it matches ^SR_[A-Z0-9_]+$) and invisible to stage 4."""
    plan["knobs"][1]["macro"] = "SR_TINYSCENTRIES"
    assert "macro_mismatch" in codes(run_checks(spec, plan, tests))


def test_two_knobs_collapsing_to_one_define_is_an_error(spec, plan, tests):
    plan["knobs"][2]["macro"] = plan["knobs"][1]["macro"]
    assert "duplicate_macro" in codes(run_checks(spec, plan, tests))


def test_a_parameter_name_that_cannot_be_a_c_identifier_is_an_error(spec, plan, tests):
    spec["parameters"][1]["name"] = "decay window"
    plan["knobs"][1]["spec_parameter"] = "decay window"
    plan["knobs"][1]["macro"] = "SR_DECAY WINDOW"
    found = codes(run_checks(spec, plan, tests))
    assert "macro_unrepresentable" in found


# ------------------------------------------------------------ the enable knob
def test_an_enable_knob_with_a_different_macro_than_its_own_parameter_is_an_error(
    spec, plan, tests
):
    plan["feature_enable"]["macro"] = "SR_SOMETHING_ELSE"
    assert "enable_macro_mismatch" in codes(run_checks(spec, plan, tests))


def test_an_enable_knob_bound_two_ways_is_an_error(spec, plan, tests):
    plan["feature_enable"]["binding"] = "python_param"
    assert "enable_binding_conflict" in codes(run_checks(spec, plan, tests))


def test_setting_the_enable_knob_in_a_test_env_is_an_error(spec, plan, tests):
    """The rule the test-plan schema states twice in prose and cannot express:
    the forbidden key's name lives in the other document."""
    tests["correctness"][0]["env"] = {"TINYSC_ENABLE": "1"}
    assert "enable_knob_in_env" in codes(run_checks(spec, plan, tests))


def test_a_hedged_off_path_is_a_warning(spec, plan, tests):
    plan["feature_enable"]["off_path"] = "The baseline path behaves correctly."
    found = run_checks(spec, plan, tests)
    assert "hedged_off_path" in codes(found)
    assert severity_of(found, "hedged_off_path") == "warn"


# ------------------------------------------------------------- the pair agrees
def test_two_documents_about_different_features_is_an_error(spec, plan, tests):
    tests["feature_name"] = "something_else"
    assert "feature_name_mismatch" in codes(run_checks(spec, plan, tests))


def test_two_documents_about_different_hosts_is_an_error(spec, plan, tests):
    tests["host"] = "gem5"
    assert "host_mismatch" in codes(run_checks(spec, plan, tests))


def test_a_test_plan_measured_against_another_revision_is_an_error(spec, plan, tests):
    tests["host_revision"] = "deadbeef"
    assert "revision_mismatch" in codes(run_checks(spec, plan, tests))


def test_a_plan_claiming_the_wrong_ablation_arm_is_an_error(spec, plan, tests):
    plan["spec_inputs_used"] = "paper_plus_reference"
    assert "inputs_used_mismatch" in codes(run_checks(spec, plan, tests))


# ------------------------------------------------------ the test plan alone
def test_a_metric_the_host_does_not_report_is_an_error(spec, plan, tests):
    tests["performance"][0]["metric"] = "brmispki_50perc_amean"
    assert "unknown_metric" in codes(run_checks(spec, plan, tests))


def test_an_unknown_companion_metric_is_an_error(spec, plan, tests):
    tests["performance"][0]["block_threshold"]["no_regression"][0]["metric"] = "cycles"
    assert "unknown_metric" in codes(run_checks(spec, plan, tests))


def test_a_pattern_python_cannot_compile_is_an_error(spec, plan, tests):
    tests["correctness"][3]["pass_condition"]["pattern"] = "FAIL: (unclosed"
    assert "uncompilable_pattern" in codes(run_checks(spec, plan, tests))


def test_a_pattern_that_matches_everything_is_a_warning(spec, plan, tests):
    tests["correctness"][3]["pass_condition"]["pattern"] = ".*"
    found = run_checks(spec, plan, tests)
    assert "vacuous_pass_condition" in codes(found)
    assert severity_of(found, "vacuous_pass_condition") == "warn"


def test_a_per_trace_command_without_the_placeholder_is_an_error(spec, plan, tests):
    tests["performance"][0]["run"]["command_template"] = "./build/toysim workloads/bias.trace"
    assert "missing_trace_placeholder" in codes(run_checks(spec, plan, tests))


def test_a_test_plan_with_no_feature_off_baseline_is_an_error(spec, plan, tests):
    tests["correctness"] = [
        e for e in tests["correctness"] if e["kind"] != "feature_off_baseline"
    ]
    assert "missing_feature_off_baseline" in codes(run_checks(spec, plan, tests))


def test_a_baseline_measured_with_the_feature_on_is_an_error(spec, plan, tests):
    tests["correctness"][1]["feature_state"] = "on"
    assert "feature_off_baseline_on" in codes(run_checks(spec, plan, tests))


def test_demanding_a_known_failing_test_pass_is_an_error(spec, plan, tests):
    """The plan records that the suite already fails and then requires exit 0,
    so no port can ever clear the gate."""
    tests["correctness"][0]["clean_tree_result"]["passed"] = False
    tests["correctness"][0]["clean_tree_result"]["exit_code"] = 1
    tests["correctness"][0]["pass_condition"] = {"kind": "exit_zero"}
    assert "unpassable_regression" in codes(run_checks(spec, plan, tests))


def test_requiring_the_feature_on_run_to_equal_the_baseline_is_an_error(spec, plan, tests):
    """Schema-legal and self-contradictory: it asserts the feature does
    nothing."""
    tests["correctness"][1]["feature_state"] = "both"
    assert "contradictory_both" in codes(run_checks(spec, plan, tests))


def test_a_tolerance_with_no_explanation_is_a_warning(spec, plan, tests):
    tests["baseline_rel_tol"] = 0.01
    del tests["notes"]
    found = run_checks(spec, plan, tests)
    assert "notes_missing_for_tolerance" in codes(found)
    assert severity_of(found, "notes_missing_for_tolerance") == "warn"


# ----------------------------------------------------------- the leftovers
def test_a_hook_nothing_references_is_a_warning(spec, plan, tests):
    plan["hook_points"].append({
        "id": "stray", "file": "src/nowhere.cpp", "symbol": "Nothing",
        "action": "create", "change": "unreferenced",
    })
    found = run_checks(spec, plan, tests)
    assert "orphan_hook" in codes(found)
    assert severity_of(found, "orphan_hook") == "warn"


def test_a_mapped_hook_no_step_lands_is_a_warning(spec, plan, tests):
    for step in plan["steps"]:
        step["hook_ids"] = [h for h in step.get("hook_ids", []) if h != "tinysc_header"]
    assert "unstepped_hook" in codes(run_checks(spec, plan, tests))


def test_a_budget_instruction_in_prose_is_a_warning(spec, plan, tests):
    """additionalProperties stops a budget field. Only this stops a budget
    sentence, which is what the integrator actually reads."""
    plan["hook_points"][0]["change"] = "Shrink the bimodal table to make room for the table."
    found = run_checks(spec, plan, tests)
    assert "budget_language" in codes(found)
    assert severity_of(found, "budget_language") == "warn"


def test_a_risk_nothing_detects_is_info(spec, plan, tests):
    del plan["risks"][0]["detected_by"]
    found = run_checks(spec, plan, tests)
    assert "undetected_risk" in codes(found)
    assert severity_of(found, "undetected_risk") == "info"


# ------------------------------------------------------- against the checkout
def test_a_modified_file_that_does_not_exist_is_an_error(spec, plan, tests):
    plan["hook_points"][1]["file"] = "src/imaginary.h"
    assert "hook_file_missing" in codes(run_checks(spec, plan, tests, host_root=HOST_ROOT))


def test_a_created_file_that_already_exists_is_an_error(spec, plan, tests):
    plan["hook_points"][2]["file"] = "src/predictor.h"
    assert "hook_file_exists" in codes(run_checks(spec, plan, tests, host_root=HOST_ROOT))


def test_a_symbol_absent_from_its_file_is_a_warning(spec, plan, tests):
    plan["hook_points"][1]["symbol"] = "ZzyzxQuux"
    found = run_checks(spec, plan, tests, host_root=HOST_ROOT)
    assert "symbol_not_found" in codes(found)
    assert severity_of(found, "symbol_not_found") == "warn"


def test_the_checkout_checks_are_skipped_without_a_host_root(spec, plan, tests):
    plan["hook_points"][1]["file"] = "src/imaginary.h"
    assert run_checks(spec, plan, tests) == []


# ----------------------------------------------- the false positives, pinned
def test_a_shell_command_in_steps_verify_is_not_a_dangling_test_id(spec, plan, tests):
    """steps[].verify is deliberately polymorphic -- a command or a test id --
    and the fixture's first step verifies with 'make', which matches the id
    pattern and names no test. Only risks[].detected_by is unambiguous enough
    to check, and a future contributor extending the check to verify will
    break the repository's own worked example."""
    assert plan["steps"][0]["verify"] == "make"
    assert run_checks(spec, plan, tests) == []


def test_a_spec_unit_test_running_with_the_knob_off_is_not_a_finding(spec, plan, tests):
    """feature_state is how the harness invokes the command, not whether the
    feature is exercised: these cases set their own environment, because
    params.h reads it on every call. A rule of the form 'a spec unit test
    about the feature must run feature-on' fires on all three."""
    unit_tests = [e for e in tests["correctness"] if e["kind"] == "spec_unit_test"]
    assert unit_tests and all(e["feature_state"] == "off" for e in unit_tests)
    assert run_checks(spec, plan, tests) == []


def test_the_word_storage_alone_is_not_budget_language(spec, plan, tests):
    """The fixture says 'the host has no storage model to satisfy'. A keyword
    list containing 'storage' fires on the repository's own worked example."""
    assert "storage" in json.dumps(plan)
    assert "budget_language" not in codes(run_checks(spec, plan, tests))


def test_an_attempt_budget_is_not_a_resource_budget(spec, plan, tests):
    plan["risks"][0]["mitigation"] = "Spend one attempt budget entry on it."
    assert "budget_language" not in codes(run_checks(spec, plan, tests))


def test_findings_carry_the_document_they_are_about_in_their_pointer(spec, plan, tests):
    """The prefix convention: a coverage finding is about the spec, an echo
    mismatch about the plan, a metric about the test plan. Without it a
    plan-review stage routing by prefix could not tell them apart."""
    plan["spec_map"] = []
    tests["performance"][0]["metric"] = "nope"
    found = run_checks(spec, plan, tests)
    prefixes = {f.pointer.split("/")[1] for f in found}
    assert prefixes <= {"spec", "plan", "tests"}
    assert {"spec", "tests"} <= prefixes


def test_plan_findings_work_with_the_stage_one_severity_helpers(spec, plan, tests):
    """plan_checks returns spec_checks.Finding, so severity_counts, is_worse
    and the loop's `[f for f in ... if f.severity == 'error']` fail-closed
    filter all work on plan findings unchanged."""
    import spec_checks

    plan["spec_map"] = []
    found = run_checks(spec, plan, tests)
    assert spec_checks.severity_counts(found)["error"] > 0
    assert spec_checks.is_worse([], found)
