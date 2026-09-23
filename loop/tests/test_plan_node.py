"""Tests for the stage-2 plan node, with no LLM and no cluster.

The node is driven by replacing the lazily imported `llm` module, the same
trick test_review_driver.py uses. That is the whole reason the import sits
inside the function: a module-level one would be bound before the stub is
installed, and none of this would be testable without spending tokens.

The canned replies are the real fixture pair, so a test that asserts "this is
accepted" is asserting it about a document the rest of the suite also holds
to the schemas and the coverage checks.
"""

import json
import sys
import types
from pathlib import Path

import pytest

import constants as C
import helpers
import plan_node

FIXTURES = Path(__file__).resolve().parent / "fixtures"
HOST_ROOT = FIXTURES / "toyhost"

SPEC = json.loads((FIXTURES / "tinysc.spec.json").read_text())
PORT_PLAN = json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())
TEST_PLAN = json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())
REVISION = PORT_PLAN["host_revision"]


def reply(port_plan=None, test_plan=None, blocks=None):
    """A planner reply: two fenced blocks under the two headings."""
    if blocks is not None:
        return blocks
    return (
        "## Port plan\n\n```json\n"
        + json.dumps(port_plan if port_plan is not None else PORT_PLAN)
        + "\n```\n\n## Test plan\n\n```json\n"
        + json.dumps(test_plan if test_plan is not None else TEST_PLAN)
        + "\n```\n"
    )


def install_stub_llm(monkeypatch, replies):
    """`replies` is a list, one per turn; the last one repeats."""
    seen = []
    mod = types.ModuleType("llm")
    mod.load_prompt = lambda name, **kw: f"[prompt {name}]"
    mod.make_llm = lambda backend, tools, resume=False: object()

    def run_llm(llm, prompt, tools):
        seen.append(prompt)
        body = replies[min(len(seen) - 1, len(replies) - 1)]
        return types.SimpleNamespace(result=body, stream_result="", success=True)

    mod.run_llm = run_llm
    monkeypatch.setitem(sys.modules, "llm", mod)
    return seen


@pytest.fixture
def dump(tmp_path):
    return helpers.Dumper(out_dir=tmp_path)


@pytest.fixture
def plan_dir(tmp_path, monkeypatch):
    """Never write into the repository's real plan/ directory."""
    out = tmp_path / "plan"
    out.mkdir()
    monkeypatch.setattr(C, "PLAN_DIR", out)
    return out


def make_plan(dump, **kw):
    kw.setdefault("host", "toy")
    kw.setdefault("work_dir", str(HOST_ROOT))
    kw.setdefault("notes", "(notes)")
    kw.setdefault("revision", REVISION)
    return plan_node.make_plan(dump, SPEC, **kw)


# ------------------------------------------------------------------ parsing
def test_two_blocks_are_read_in_order():
    port, tests, errors = plan_node.parse_reply(reply())
    assert errors == []
    assert port["feature_name"] == "tinysc" and "correctness" in tests


def test_one_block_is_an_error_rather_than_a_silent_port_plan_loss():
    """The failure this guards: the repo's other extractor keeps the LAST
    fenced block, so a two-document reply parsed with it would lose the port
    plan and report schema errors about a test plan missing every port-plan
    field."""
    text = "```json\n" + json.dumps(TEST_PLAN) + "\n```"
    port, tests, errors = plan_node.parse_reply(text)
    assert port is None and tests is None
    assert "expected exactly two" in errors[0]


def test_a_truncated_reply_says_so():
    text = "## Port plan\n\n```json\n" + json.dumps(PORT_PLAN)[:400]
    _, _, errors = plan_node.parse_reply(text)
    assert "cut off" in errors[0]


def test_schema_errors_name_which_document_they_came_from():
    broken = {k: v for k, v in PORT_PLAN.items() if k != "knobs"}
    _, _, errors = plan_node.parse_reply(reply(port_plan=broken))
    assert errors and all(e.startswith("port plan:") for e in errors)


def test_a_budget_field_is_rejected_by_the_node_not_just_by_a_test():
    smuggled = {**PORT_PLAN, "storage_budget_bits": 196608}
    _, _, errors = plan_node.parse_reply(reply(port_plan=smuggled))
    assert any("storage_budget_bits" in e for e in errors)


# ------------------------------------------------------------------- driver
def test_a_good_pair_is_written_to_disk(monkeypatch, dump, plan_dir):
    install_stub_llm(monkeypatch, [reply()])
    port, tests = make_plan(dump)
    plan_path, tests_path = helpers.plan_paths("toy", feature="tinysc")
    assert json.loads(plan_path.read_text()) == port
    assert json.loads(tests_path.read_text()) == tests


def test_a_good_pair_costs_exactly_one_turn(monkeypatch, dump, plan_dir):
    seen = install_stub_llm(monkeypatch, [reply()])
    make_plan(dump)
    assert len(seen) == 1


def test_a_coverage_gap_is_repaired_on_the_same_session(monkeypatch, dump, plan_dir):
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["spec_map"] = [e for e in gapped["spec_map"] if e["spec_pointer"] != "/state/1"]
    seen = install_stub_llm(monkeypatch, [reply(port_plan=gapped), reply()])
    port, _ = make_plan(dump)
    assert len(seen) == 2
    assert any(e["spec_pointer"] == "/state/1" for e in port["spec_map"])


def test_the_repair_turn_shows_the_agent_the_findings(monkeypatch, dump, plan_dir):
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["spec_map"] = [e for e in gapped["spec_map"] if e["spec_pointer"] != "/state/1"]
    seen = install_stub_llm(monkeypatch, [reply(port_plan=gapped), reply()])
    make_plan(dump)
    assert "uncovered_state" in seen[1]
    assert "/spec/state/1" in seen[1]


def test_the_repair_turn_carries_the_schemas_only_when_the_schema_failed(
    monkeypatch, dump, plan_dir
):
    """A coverage finding does not need 33 KB of schema re-sent to explain
    it; a validator message does."""
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["spec_map"] = [e for e in gapped["spec_map"] if e["spec_pointer"] != "/state/1"]
    seen = install_stub_llm(monkeypatch, [reply(port_plan=gapped), reply()])
    make_plan(dump)
    assert "The port plan schema" not in seen[1]

    broken = {k: v for k, v in PORT_PLAN.items() if k != "knobs"}
    seen = install_stub_llm(monkeypatch, [reply(port_plan=broken), reply()])
    make_plan(dump)
    assert "The port plan schema" in seen[1]


def test_an_unrepaired_gap_fails_the_stage_closed(monkeypatch, dump, plan_dir):
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["knobs"] = []
    install_stub_llm(monkeypatch, [reply(port_plan=gapped)])
    with pytest.raises(SystemExit, match="uncovered_parameter|unresolved plan error"):
        make_plan(dump)
    plan_path, _ = helpers.plan_paths("toy", feature="tinysc")
    assert not plan_path.exists()


def test_failing_closed_still_leaves_the_evidence(monkeypatch, dump, plan_dir):
    """A refused run that writes nothing is one nobody can diagnose without
    re-running the whole stage."""
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["knobs"] = []
    install_stub_llm(monkeypatch, [reply(port_plan=gapped)])
    with pytest.raises(SystemExit):
        make_plan(dump)
    written = [p.name for p in Path(dump.dir).iterdir()]
    assert any("plan_toy_final.json" in n for n in written)
    assert any("plan_toy_rounds.json" in n for n in written)
    assert any("plan_toy_0.md" in n for n in written)


def test_the_override_writes_a_gapped_plan_anyway(monkeypatch, dump, plan_dir):
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["knobs"] = []
    install_stub_llm(monkeypatch, [reply(port_plan=gapped)])
    monkeypatch.setattr(C, "PLAN_ALLOW_GAPS", True)
    port, _ = make_plan(dump)
    assert port["knobs"] == []


def test_a_warning_does_not_block(monkeypatch, dump, plan_dir):
    warned = json.loads(json.dumps(PORT_PLAN))
    warned["feature_enable"]["off_path"] = "It behaves correctly."
    install_stub_llm(monkeypatch, [reply(port_plan=warned)])
    port, _ = make_plan(dump)
    assert port["feature_enable"]["off_path"] == "It behaves correctly."


def test_a_plan_written_against_another_revision_is_an_error(monkeypatch, dump, plan_dir):
    install_stub_llm(monkeypatch, [reply()])
    with pytest.raises(SystemExit, match="revision"):
        make_plan(dump, revision="0000000000000000000000000000000000000000")


def test_the_checkout_is_checked_against_the_real_tree(monkeypatch, dump, plan_dir):
    bad = json.loads(json.dumps(PORT_PLAN))
    bad["hook_points"][1]["file"] = "src/imaginary.h"
    install_stub_llm(monkeypatch, [reply(port_plan=bad)])
    with pytest.raises(SystemExit, match="hook_file_missing|does not exist"):
        make_plan(dump)


def test_repair_turns_can_be_switched_off(monkeypatch, dump, plan_dir):
    gapped = json.loads(json.dumps(PORT_PLAN))
    gapped["knobs"] = []
    seen = install_stub_llm(monkeypatch, [reply(port_plan=gapped), reply()])
    with pytest.raises(SystemExit):
        make_plan(dump, repair_turns=0)
    assert len(seen) == 1


# ------------------------------------------------------------ shell limit

def _install_prompt_filling_llm(monkeypatch):
    """The stub LLM, with a load_prompt that fills the real prompt file the
    way llm.load_prompt does, so the test sees what the planner would read."""
    seen = install_stub_llm(monkeypatch, [reply()])

    def load_prompt(name, **subs):
        text = (C.PROMPTS_DIR / name).read_text()
        for key, val in subs.items():
            text = text.replace("{{" + key + "}}", val).replace("${" + key + "}", val)
        return text

    sys.modules["llm"].load_prompt = load_prompt
    return seen


def test_the_planner_prompt_states_the_shell_limit_it_was_given(
    monkeypatch, dump, plan_dir
):
    """gem5's shell allows 1200 s. A prompt that still said 300 would have
    the planner narrow or drop commands its shell can run."""
    seen = _install_prompt_filling_llm(monkeypatch)
    make_plan(dump, bash_timeout=1200)
    assert "capped at 1200 seconds per command" in seen[0]
    assert "{{bash_timeout}}" not in seen[0]


def test_the_planner_prompt_defaults_to_the_generic_shell_limit(
    monkeypatch, dump, plan_dir
):
    seen = _install_prompt_filling_llm(monkeypatch)
    make_plan(dump)
    assert f"capped at {C.BASH_TOOL_TIMEOUT_S} seconds per command" in seen[0]
