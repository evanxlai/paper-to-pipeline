"""Tests for the stage-3 plan-revision guard.

Every case starts from the worked fixture pair and changes exactly one thing,
the way test_plan_checks.py does. The reason is sharper here than there: the
guard's whole job is to tell one kind of edit from another, so a case that
changes two fields at once cannot show which rule fired.

The tests are organised around the distinction the module exists to draw.
`test_allows_*` pins the factual corrections that must get through -- those are
the feature. `test_rejects_*` pins the weakenings that must not -- those are
the hazard. A future contributor who loosens a rule to make a real run pass
will break one of the second group, which is the point of writing them as
narrowly as possible.

Assertions are on codes and pointers, never on message text.
"""

import json
from pathlib import Path

import pytest

import plan_revision
from plan_revision import guard

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def codes(findings):
    return sorted(f.code for f in findings)


def blockers(findings):
    return plan_revision.blocking(findings)


@pytest.fixture
def port():
    return json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())


@pytest.fixture
def tests():
    return json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


# ---------------------------------------------------------------- the no-op


def test_identical_pair_is_clean(port, tests):
    """The baseline every other case is measured against. A guard that fires
    on an unchanged pair would make every revision look like an attack."""
    assert guard(port, tests, json.loads(json.dumps(port)),
                 json.loads(json.dumps(tests))) == []


# ------------------------------------------- what a revision is FOR (allowed)


def test_allows_hook_point_correction(port, tests):
    """The plan was wrong about the tree. This is the case the feature exists
    for, so it must pass with nothing recorded at all."""
    new = json.loads(json.dumps(port))
    new["hook_points"][0]["symbol"] = "ToyPredictor::predict_v2"
    new["hook_points"][0]["observed"] = "renamed since the plan was written"
    assert guard(port, tests, new, tests) == []


def test_allows_new_hook_point(port, tests):
    new = json.loads(json.dumps(port))
    new["hook_points"].append({
        "id": "extra_site", "file": "src/sim.cpp", "symbol": "main",
        "action": "modify", "observed": "drives the trace loop",
        "change": "thread the knob through",
    })
    assert guard(port, tests, new, tests) == []


def test_allows_realization_and_hook_ids_rewrite(port, tests):
    """Same spec item, different code site. `spec_map` is append-only on its
    pointers, not frozen on its contents."""
    new = json.loads(json.dumps(port))
    new["spec_map"][0]["realization"] = "a std::vector on the module instead"
    new["spec_map"][0]["hook_ids"] = ["extra_site"]
    assert guard(port, tests, new, tests) == []


def test_allows_fixing_a_test_command(port, tests):
    """A correctness command naming the wrong target fails for a reason no
    edit to the feature can fix, which is the test-plan half of the feature."""
    new = json.loads(json.dumps(tests))
    new["correctness"][0]["command"] = "make check"
    assert guard(port, new, port, new) == []
    assert guard(port, tests, port, new) == []


def test_allows_adding_a_correctness_entry(port, tests):
    new = json.loads(json.dumps(tests))
    new["correctness"].append({
        "id": "extra_case", "kind": "generated_smoke",
        "description": "a case the planner missed",
        "command": "make test", "feature_state": "on",
        "pass_condition": {"kind": "exit_zero"},
    })
    assert guard(port, tests, port, new) == []


def test_allows_adding_a_metric_key(port, tests):
    """Widening what G2 has to match is a tightening, so it is not the guard's
    business."""
    new = json.loads(json.dumps(tests))
    new["metric_keys"].append("cycles")
    assert guard(port, tests, port, new) == []


def test_allows_host_knob_and_binding_correction(port, tests):
    """The macro is frozen; which host-native knob it drives is a fact about
    the tree."""
    new = json.loads(json.dumps(port))
    new["knobs"][1]["host_knob"] = "kToySCEntries"
    new["knobs"][1]["binding"] = "compile_time_define"
    assert guard(port, tests, new, tests) == []


def test_allows_steps_and_risks_rewrite(port, tests):
    new = json.loads(json.dumps(port))
    new["steps"] = [{"title": "one step now", "detail": "all of it",
                     "verify": "make test"}]
    new["risks"] = []
    assert guard(port, tests, new, tests) == []


# --------------------------------------- what a revision may NOT do (blocked)


def test_rejects_lowering_a_block_threshold(port, tests):
    """The headline hazard: G5's bar, edited by the party G5 judges."""
    new = json.loads(json.dumps(tests))
    new["performance"][0]["block_threshold"]["min_relative_improvement"] = -1.0
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field"]
    assert found[0].pointer == "/tests/performance/0/block_threshold"


def test_rejects_widening_a_no_regression_band(port, tests):
    """Nested inside block_threshold, so it is covered by freezing the whole
    object rather than by a rule of its own."""
    new = json.loads(json.dumps(tests))
    new["performance"][0]["block_threshold"]["no_regression"][0]["max_relative_regression"] = 0.5
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_flipping_a_performance_direction(port, tests):
    new = json.loads(json.dumps(tests))
    new["performance"][0]["direction"] = "increase"
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_retargeting_a_performance_metric(port, tests):
    new = json.loads(json.dumps(tests))
    new["performance"][0]["metric"] = "ipc"
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_rewriting_the_papers_claim(port, tests):
    """`warn_threshold` does not block, but it is a claim about the paper, and
    nothing read in the checkout can change what the paper claimed."""
    new = json.loads(json.dumps(tests))
    new["performance"][0]["warn_threshold"]["target_relative_improvement"] = 0.0
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_deleting_a_performance_entry(port, tests):
    new = json.loads(json.dumps(tests))
    new["performance"] = []
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_deleted_entry"]


def test_rejects_deleting_a_correctness_entry(port, tests):
    """Schema-legal and coherent -- `plan_checks` sees nothing wrong with a
    shorter list, which is exactly why this rule lives here."""
    new = json.loads(json.dumps(tests))
    new["correctness"] = [c for c in new["correctness"] if c["id"] != "host_suite"]
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_deleted_entry"]


def test_rejects_rewriting_a_pass_condition(port, tests):
    new = json.loads(json.dumps(tests))
    new["correctness"][0]["pass_condition"] = {"kind": "exit_zero"}
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field"]
    assert found[0].pointer.endswith("/pass_condition")


def test_rejects_restating_a_clean_tree_result(port, tests):
    """Measured on a tree the agent has since modified, so a revision cannot
    honestly restate it."""
    new = json.loads(json.dumps(tests))
    entry = next(c for c in new["correctness"] if "clean_tree_result" in c)
    entry["clean_tree_result"]["exit_code"] = 1
    entry["clean_tree_result"]["passed"] = False
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_moving_a_correctness_entry_off_the_baseline(port, tests):
    new = json.loads(json.dumps(tests))
    entry = next(c for c in new["correctness"] if c["kind"] == "feature_off_baseline")
    entry["kind"] = "generated_smoke"
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_changing_a_feature_state(port, tests):
    new = json.loads(json.dumps(tests))
    entry = next(c for c in new["correctness"] if c["feature_state"] == "off")
    entry["feature_state"] = "on"
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_dropping_a_metric_key(port, tests):
    new = json.loads(json.dumps(tests))
    new["metric_keys"] = ["mpki"]
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_deleted_entry"]
    assert found[0].pointer == "/tests/metric_keys"


def test_rejects_widening_the_g2_tolerance(port, tests):
    new = json.loads(json.dumps(tests))
    new["baseline_rel_tol"] = 0.05
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field"]
    assert found[0].pointer == "/tests/baseline_rel_tol"


def test_rejects_tightening_the_g2_tolerance_too(port, tests):
    """Frozen means frozen in both directions. The module says so on purpose:
    a rule with a direction needs a sign, and a sign is a thing to get wrong."""
    new = json.loads(json.dumps(tests))
    new["baseline_rel_tol"] = 0.0
    tests["baseline_rel_tol"] = 0.01
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_shrinking_the_smoke_list(port, tests):
    new = json.loads(json.dumps(tests))
    new["smoke"]["traces"] = []
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_deleted_entry"]
    assert found[0].pointer == "/tests/smoke/traces"


def test_allows_fixing_the_smoke_run_command(port, tests):
    new = json.loads(json.dumps(tests))
    new["smoke"]["run"]["command_template"] = "./build/toysim --trace {trace}"
    assert guard(port, tests, port, new) == []


def test_allows_fixing_a_performance_run_when_both_sides_move(port, tests):
    """The fixture entry's baseline source is `measure_feature_off`, so
    `plan_runner` measures feature-on and feature-off through the same `run`.
    A corrected command moves both sides and the improvement stays honest."""
    new = json.loads(json.dumps(tests))
    assert new["performance"][0]["baseline"]["source"] == "measure_feature_off"
    new["performance"][0]["run"]["command_template"] = "./build/toysim --trace {trace}"
    assert guard(port, tests, port, new) == []


def test_rejects_fixing_a_performance_run_against_a_recorded_baseline(port, tests):
    """The asymmetric case. `run` feeds only the measured side, so revising it
    moves `relative_improvement` without touching a threshold, a trace list or
    the baseline."""
    tests["performance"][0]["baseline"] = {"source": "recorded", "pointer": "/bias"}
    new = json.loads(json.dumps(tests))
    new["performance"][0]["run"]["command_template"] = "./build/toysim --easy {trace}"
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field"]
    assert found[0].pointer == "/tests/performance/0/run"


def test_rejects_switching_a_recorded_entrys_run_mode(port, tests):
    """Not only the template: changing the mode changes what is measured."""
    tests["performance"][0]["baseline"] = {"source": "recorded", "pointer": "/bias"}
    new = json.loads(json.dumps(tests))
    new["performance"][0]["run"] = {"mode": "host_adapter"}
    assert codes(blockers(guard(port, tests, port, new))) == ["revision_froze_field"]


def test_rejects_moving_an_entry_to_unlock_its_run(port, tests):
    """The way around the rule would be to relabel the baseline source and
    revise `run` in one go. `baseline` is frozen, so the relabel is caught and
    `source` is read off the pair in force rather than off the proposal."""
    tests["performance"][0]["baseline"] = {"source": "recorded", "pointer": "/bias"}
    new = json.loads(json.dumps(tests))
    new["performance"][0]["baseline"] = {"source": "measure_feature_off"}
    new["performance"][0]["run"]["command_template"] = "./build/toysim --easy {trace}"
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field", "revision_froze_field"]
    assert sorted(f.pointer for f in found) == [
        "/tests/performance/0/baseline", "/tests/performance/0/run",
    ]


def test_rejects_shortening_a_performance_timeout(port, tests):
    """`plan_runner._measure` scores the traces that completed and the gate
    does not block on the ones that did not, so a shorter timeout scores the
    entry on the easy subset."""
    tests["performance"][0]["timeout_seconds"] = 600
    new = json.loads(json.dumps(tests))
    new["performance"][0]["timeout_seconds"] = 5
    found = blockers(guard(port, tests, port, new))
    assert codes(found) == ["revision_froze_field"]
    assert found[0].pointer == "/tests/performance/0/timeout_seconds"


def test_allows_lengthening_a_correctness_timeout(port, tests):
    """The correctness half has no subset hazard: a command that times out
    fails its entry outright, so the timeout stays revisable there."""
    new = json.loads(json.dumps(tests))
    new["correctness"][0]["timeout_seconds"] = 1800
    assert guard(port, tests, port, new) == []


def test_rejects_renaming_a_knob_macro(port, tests):
    """Stage 4 mutates one generated header; a knob under another name is one
    the search can never move."""
    new = json.loads(json.dumps(port))
    new["knobs"][1]["macro"] = "SR_SOMETHING_ELSE"
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_rejects_changing_a_knob_default(port, tests):
    """Cross-checked against the spec, so a port shipping another default
    measures something the spec does not describe."""
    new = json.loads(json.dumps(port))
    new["knobs"][1]["default"] = 4096
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_rejects_renaming_the_enable_knob(port, tests):
    new = json.loads(json.dumps(port))
    new["feature_enable"]["name"] = "TINYSC_ON"
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_rejects_dropping_a_spec_map_pointer(port, tests):
    """`plan_checks` catches a dropped `/state/N` through spec coverage; this
    rule is what catches the pointers coverage does not reach."""
    new = json.loads(json.dumps(port))
    new["spec_map"] = new["spec_map"][1:]
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_deleted_entry"]


def test_rejects_reanswering_an_open_question(port, tests):
    new = json.loads(json.dumps(port))
    new["open_questions"][0]["assumption"] = "the opposite reading"
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_allows_recording_the_cost_of_a_wrong_assumption(port, tests):
    """Integration is the first thing to learn what the assumption costs."""
    new = json.loads(json.dumps(port))
    new["open_questions"][0]["cost_if_wrong"] = "one member and a rebuild"
    assert guard(port, tests, new, tests) == []


def test_rejects_deleting_a_rejected_alternative(port, tests):
    new = json.loads(json.dumps(port))
    new["structure"]["rejected_alternatives"] = []
    assert codes(blockers(guard(port, tests, new, tests))) == [
        "revision_deleted_entry", "revision_deleted_entry",
    ]


def test_rejects_rewriting_why_an_alternative_lost(port, tests):
    new = json.loads(json.dumps(port))
    new["structure"]["rejected_alternatives"][0]["why_rejected"] = "no reason"
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_allows_changing_the_structure_choice(port, tests):
    """The shape the port took is revisable; the roads not taken are not."""
    new = json.loads(json.dumps(port))
    new["structure"]["choice"] = "a free function after all"
    assert guard(port, tests, new, tests) == []


@pytest.mark.parametrize(
    "field,value",
    [("feature_name", "other"), ("host", "champsim"),
     ("host_revision", "deadbeef"), ("spec_inputs_used", "paper_plus_reference")],
)
def test_rejects_changing_an_identity_field(port, tests, field, value):
    new = json.loads(json.dumps(port))
    new[field] = value
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_froze_field"]


def test_rejects_deleting_an_interface_resolution(port, tests):
    new = json.loads(json.dumps(port))
    new["interface_resolutions"] = new["interface_resolutions"][:1]
    assert codes(blockers(guard(port, tests, new, tests))) == ["revision_deleted_entry"]


# ------------------------------------------------- recorded but not refused


def test_fidelity_downgrade_is_recorded_not_blocked(port, tests):
    """Discovering that a host facility does not do what it looked like it did
    is the legitimate case. It must get through, and it must not get through
    quietly."""
    new = json.loads(json.dumps(port))
    new["interface_resolutions"][0]["status"] = "fallback"
    new["interface_resolutions"][0]["fidelity_note"] = "no per-branch history here"
    found = guard(port, tests, new, tests)
    assert codes(found) == ["revision_lost_fidelity"]
    assert blockers(found) == []


def test_fidelity_upgrade_is_not_recorded(port, tests):
    """The other direction is good news and needs no note."""
    downgraded = json.loads(json.dumps(port))
    downgraded["interface_resolutions"][0]["status"] = "unavailable"
    downgraded["interface_resolutions"][0]["fidelity_note"] = "pending"
    assert guard(downgraded, tests, port, tests) == []


def test_off_path_rewrite_is_recorded_not_blocked(port, tests):
    """G2 measures the off path rather than reading the prose, so rewriting it
    cannot loosen the gate -- but it does restate a promise after the fact."""
    new = json.loads(json.dumps(port))
    new["feature_enable"]["off_path"] = "a shorter claim"
    found = guard(port, tests, new, tests)
    assert codes(found) == ["revision_restated_off_path"]
    assert blockers(found) == []


# ------------------------------------------------------ the reply protocol


def test_proposed_needs_the_marker():
    assert plan_revision.proposed("## Plan revision\n```json\n{}\n```")
    assert plan_revision.proposed("## plan REVISION\n")
    assert not plan_revision.proposed("Here are two blocks:\n```json\n{}\n```\n```json\n{}\n```")
    assert not plan_revision.proposed("")
    assert not plan_revision.proposed(None)


@pytest.mark.parametrize("dash", ["--", "-", "—"])
def test_escalation_is_machine_readable(dash):
    got = plan_revision.escalation(
        f"I cannot fix this.\nPLAN ESCALATION: /tests/performance/0 {dash} the metric is "
        f"not reachable from this hook at all.\n"
    )
    assert got["pointer"] == "/tests/performance/0"
    assert got["reason"].startswith("the metric is not reachable")


def test_no_escalation_in_an_ordinary_reply():
    assert plan_revision.escalation("I rebuilt and the test passes now.") is None


# ----------------------------------------------------------- artifact paths


def test_revision_paths_sit_beside_stage_twos_output():
    plan_path, tests_path = plan_revision.revision_paths("toy", "tinysc", 2)
    assert plan_path.name == "tinysc.toy.plan.rev2.json"
    assert tests_path.name == "tinysc.toy.tests.rev2.json"


def test_latest_walks_the_revisions(tmp_path, monkeypatch, port, tests):
    """Revision 0 is stage 2's output, and a restarted run resumes from the
    revisions it already earned rather than re-litigating them."""
    import constants as C

    monkeypatch.setattr(C, "PLAN_DIR", tmp_path)
    base_plan, base_tests = plan_revision.helpers.plan_paths("toy", "tinysc")
    base_plan.parent.mkdir(parents=True, exist_ok=True)
    base_plan.write_text(json.dumps(port))
    base_tests.write_text(json.dumps(tests))

    assert plan_revision.latest("toy", "tinysc")[2] == 0

    first_plan, first_tests = plan_revision.revision_paths("toy", "tinysc", 1)
    revised = json.loads(json.dumps(port))
    revised["structure"]["choice"] = "revision one"
    first_plan.write_text(json.dumps(revised))
    first_tests.write_text(json.dumps(tests))

    got_port, _, index = plan_revision.latest("toy", "tinysc")
    assert index == 1
    assert got_port["structure"]["choice"] == "revision one"


def test_latest_ignores_a_half_written_revision(tmp_path, monkeypatch, port, tests):
    """Both files or neither: a revision with only its port plan on disk is a
    crashed write, and reading it would pair a new plan with an old test plan."""
    import constants as C

    monkeypatch.setattr(C, "PLAN_DIR", tmp_path)
    base_plan, base_tests = plan_revision.helpers.plan_paths("toy", "tinysc")
    base_plan.parent.mkdir(parents=True, exist_ok=True)
    base_plan.write_text(json.dumps(port))
    base_tests.write_text(json.dumps(tests))
    plan_revision.revision_paths("toy", "tinysc", 1)[0].write_text(json.dumps(port))

    assert plan_revision.latest("toy", "tinysc")[2] == 0
