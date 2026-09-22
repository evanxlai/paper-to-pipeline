"""Tests for the stage-2 plan schemas and the worked example under them.

Two things are being checked, and they are different things.

The first is that `plan/port_plan.schema.json` and `plan/test_plan.schema.json`
are well-formed and reject what they claim to reject -- including a budget
field, which every pre-DSE stage is forbidden to carry (docs/stages.md).

The second is that the schemas can actually express a real port. A schema
nobody has written a document against is a guess about what the planner will
need, so `fixtures/tinysc.{toy.plan,toy.tests}.json` plan the fixture spec into
the fixture host, and the tests below hold that pair to the invariants the
schema descriptions promise but JSON Schema cannot state: unique ids, pointers
that resolve against the spec they claim to map, knob names that match the
header `dse.params_header_from_spec` actually emits, and full coverage of the
spec.

Coverage here is asserted about the fixture, not implemented for the loop. The
plan coverage checks are their own week-2 task and will live beside
spec_checks.py; what this file establishes is that a plan *can* satisfy them,
which is the part a schema is responsible for.
"""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import constants as C
import dse

FIXTURES = Path(__file__).resolve().parent / "fixtures"

PORT_PLAN_SCHEMA = json.loads(C.PORT_PLAN_SCHEMA_PATH.read_text())
TEST_PLAN_SCHEMA = json.loads(C.TEST_PLAN_SCHEMA_PATH.read_text())

SPEC = json.loads((FIXTURES / "tinysc.spec.json").read_text())
PLAN = json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())
TEST_PLAN = json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


def errors(schema, document):
    return [
        f"{'/'.join(map(str, e.path))}: {e.message}"
        for e in Draft202012Validator(schema).iter_errors(document)
    ]


def resolve(document, pointer):
    """RFC 6901, enough of it for the pointers a plan may carry."""
    node = document
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


# ------------------------------------------------------------ the schemas
def test_schemas_are_valid():
    Draft202012Validator.check_schema(PORT_PLAN_SCHEMA)
    Draft202012Validator.check_schema(TEST_PLAN_SCHEMA)


def test_fixture_plan_pair_validates():
    assert errors(PORT_PLAN_SCHEMA, PLAN) == []
    assert errors(TEST_PLAN_SCHEMA, TEST_PLAN) == []


def test_a_budget_cannot_enter_either_plan():
    """The one rule that shapes the stage split: no pre-DSE artifact carries a
    resource constraint. `additionalProperties: false` is what enforces it, so
    it is worth a test -- relaxing it later would silently reopen the door."""
    for schema, document in ((PORT_PLAN_SCHEMA, PLAN), (TEST_PLAN_SCHEMA, TEST_PLAN)):
        for field in ("budget", "budget_bits", "storage_budget_bits", "iso_budget"):
            smuggled = {**document, field: 192 * 1024 * 8}
            assert errors(schema, smuggled), f"{field} was accepted"


def test_a_knob_outside_the_generated_header_convention_is_rejected():
    plan = copy.deepcopy(PLAN)
    plan["knobs"][1]["macro"] = "TINYSC_ENTRIES"  # missing the SR_ prefix
    assert errors(PORT_PLAN_SCHEMA, plan)


def test_a_modified_hook_point_must_say_what_is_there_now():
    plan = copy.deepcopy(PLAN)
    hook = next(h for h in plan["hook_points"] if h["action"] == "modify")
    del hook["observed"]
    assert errors(PORT_PLAN_SCHEMA, plan)


def test_a_fallback_interface_must_record_what_it_costs():
    plan = copy.deepcopy(PLAN)
    plan["interface_resolutions"][0]["status"] = "fallback"
    assert errors(PORT_PLAN_SCHEMA, plan)


def test_an_existing_regression_must_carry_its_clean_tree_result():
    """The whole point of the kind: a pre-existing failure must be on record
    before the port starts, or it gets charged to the port."""
    plan = copy.deepcopy(TEST_PLAN)
    entry = next(e for e in plan["correctness"] if e["kind"] == "existing_regression")
    del entry["clean_tree_result"]
    assert errors(TEST_PLAN_SCHEMA, plan)


def test_matches_clean_tree_needs_a_clean_tree_to_match():
    """The condition is only decidable against a recorded result, on any kind
    that uses it -- not only on the kind that is required to carry one."""
    plan = copy.deepcopy(TEST_PLAN)
    entry = next(e for e in plan["correctness"] if e["kind"] == "feature_off_baseline")
    entry["pass_condition"] = {"kind": "matches_clean_tree"}
    assert errors(TEST_PLAN_SCHEMA, plan)


def test_a_spec_unit_test_must_name_the_spec_test_it_implements():
    plan = copy.deepcopy(TEST_PLAN)
    entry = next(e for e in plan["correctness"] if e["kind"] == "spec_unit_test")
    del entry["spec_pointer"]
    assert errors(TEST_PLAN_SCHEMA, plan)


def test_a_performance_entry_needs_traces_and_both_thresholds():
    for field in ("traces", "block_threshold", "warn_threshold"):
        plan = copy.deepcopy(TEST_PLAN)
        del plan["performance"][0][field]
        assert errors(TEST_PLAN_SCHEMA, plan), f"missing {field} was accepted"


def test_a_per_trace_command_must_say_what_the_command_is():
    plan = copy.deepcopy(TEST_PLAN)
    del plan["performance"][0]["run"]["command_template"]
    assert errors(TEST_PLAN_SCHEMA, plan)


# ------------------------------------------- the fixture pair's invariants
def test_hook_ids_are_unique_and_every_reference_resolves():
    ids = [h["id"] for h in PLAN["hook_points"]]
    assert len(ids) == len(set(ids))
    referenced = [
        (where, hook_id)
        for key in ("spec_map", "interface_resolutions", "steps")
        for where in PLAN[key]
        for hook_id in where.get("hook_ids", [])
    ]
    unknown = [(w, h) for w, h in referenced if h not in set(ids)]
    assert unknown == []


def test_every_pointer_resolves_to_what_the_plan_says_it_does():
    """The echoed name is the redundancy that catches an off-by-one pointer:
    without it a plan can point the integrator at the wrong state element and
    still satisfy every coverage count."""
    for entry in PLAN["spec_map"]:
        assert resolve(SPEC, entry["spec_pointer"])["name"] == entry["spec_item"]
    for entry in PLAN["interface_resolutions"]:
        assert resolve(SPEC, entry["spec_pointer"])["need"] == entry["need"]
    for knob in PLAN["knobs"]:
        assert resolve(SPEC, knob["spec_pointer"])["name"] == knob["spec_parameter"]
    for entry in PLAN["open_questions"]:
        if "spec_pointer" in entry:
            resolve(SPEC, entry["spec_pointer"])
    for entry in TEST_PLAN["correctness"]:
        if "spec_pointer" in entry:
            resolve(SPEC, entry["spec_pointer"])


def test_the_fixture_plan_covers_every_spec_item():
    mapped = {e["spec_pointer"] for e in PLAN["spec_map"]}
    for section in ("state", "algorithms"):
        for i in range(len(SPEC[section])):
            assert f"/{section}/{i}" in mapped

    resolved = {e["spec_pointer"] for e in PLAN["interface_resolutions"]}
    for i in range(len(SPEC["host_interfaces"])):
        assert f"/host_interfaces/{i}" in resolved

    knobbed = {k["spec_pointer"] for k in PLAN["knobs"]}
    for i in range(len(SPEC["parameters"])):
        assert f"/parameters/{i}" in knobbed

    tested = {
        e["spec_pointer"]
        for e in TEST_PLAN["correctness"]
        if e["kind"] == "spec_unit_test"
    }
    for i in range(len(SPEC["unit_tests"])):
        assert f"/unit_tests/{i}" in tested


def test_the_knobs_match_the_header_the_dse_stage_will_mutate():
    """A knob wired to any other name is invisible to stage 4, and nothing
    downstream would notice: the port builds, runs, and simply never moves
    when the evolver changes that parameter."""
    header = dse.params_header_from_spec(SPEC)
    emitted = {line.split()[1] for line in header.splitlines() if line.startswith("#define")}
    planned = {k["macro"] for k in PLAN["knobs"]}
    assert planned == emitted
    assert PLAN["feature_enable"]["macro"] in emitted


def test_every_knob_ships_the_spec_default():
    for knob in PLAN["knobs"]:
        assert knob["default"] == resolve(SPEC, knob["spec_pointer"])["default"]


def test_the_two_artifacts_describe_the_same_port():
    assert PLAN["feature_name"] == TEST_PLAN["feature_name"] == SPEC["feature_name"]
    assert PLAN["host"] == TEST_PLAN["host"]
    assert PLAN["host_revision"] == TEST_PLAN["host_revision"]


def test_test_ids_are_unique_and_referenced_ones_exist():
    ids = [e["id"] for e in TEST_PLAN["correctness"]] + [
        e["id"] for e in TEST_PLAN["performance"]
    ]
    assert len(ids) == len(set(ids))
    for risk in PLAN["risks"]:
        if "detected_by" in risk:
            assert risk["detected_by"] in set(ids)


def test_every_metric_named_anywhere_is_one_the_host_reports():
    known = set(TEST_PLAN["metric_keys"])
    for entry in TEST_PLAN["correctness"]:
        assert set(entry["pass_condition"].get("metrics", [])) <= known
    for entry in TEST_PLAN["performance"]:
        assert entry["metric"] in known
        for companion in entry["block_threshold"].get("no_regression", []):
            assert companion["metric"] in known
