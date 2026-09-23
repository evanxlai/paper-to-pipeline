"""Tests for the escalation re-plan loop (loop/replan.py), with no cluster.

Three layers. `design_changes` is the rule that decides whether a re-plan
keeps the port tree, so it is tested field by field. `integrate_with_replans`
is driven with fake stages, so every budget and failure branch is
deterministic. The last test wires the real pieces together, the real stage 3,
the real escalation file and the real stage-2 planner, with only the model
scripted. It shows that an escalation raised in one round reaches the planner
in the same job and is answered there.
"""

import json
import sys
import types
from pathlib import Path

import pytest

import adopt_a_paper_loop as loop
import constants as C
import gate
import helpers
import plan_node
import plan_revision
import replan

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SPEC = json.loads((FIXTURES / "tinysc.spec.json").read_text())
PORT = json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())
TESTS = json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


def copy(doc):
    return json.loads(json.dumps(doc))


# ------------------------------------------------------------ design_changes


def test_the_same_plan_changes_nothing():
    assert replan.design_changes(PORT, copy(PORT)) == []


def test_reworded_prose_is_not_a_design_change():
    """A re-plan rewrites its sentences freely. A reworded hook point or
    rationale is still the same port, and must not throw the port away."""
    new = copy(PORT)
    new["hook_points"][0]["change"] = "Reworded: " + new["hook_points"][0]["change"]
    new["interface_resolutions"][0]["rationale"] = "A different explanation."
    new["risks"] = new.get("risks", []) + ["a new risk"]
    assert replan.design_changes(PORT, new) == []


def test_a_new_structure_is_a_design_change():
    new = copy(PORT)
    new["structure"]["choice"] = "one term in the host's own corrector sum"
    assert replan.design_changes(PORT, new) == ["structure.choice"]


def test_a_moved_hook_is_a_design_change():
    new = copy(PORT)
    new["hook_points"][0]["symbol"] = "somewhere_else"
    assert replan.design_changes(PORT, new) == ["hook_points"]


def test_a_changed_interface_resolution_is_a_design_change():
    """The first real escalation's shape: /host_interfaces/4 went from
    `fallback` to `exact`, and the port built for the fallback was the wrong
    mechanism, not a slightly wrong one."""
    new = copy(PORT)
    old_status = new["interface_resolutions"][0]["status"]
    new["interface_resolutions"][0]["status"] = (
        "fallback" if old_status == "exact" else "exact")
    assert replan.design_changes(PORT, new) == ["interface_resolutions.status"]


def test_a_renamed_knob_macro_is_a_design_change():
    new = copy(PORT)
    new["knobs"][0]["macro"] = new["knobs"][0]["macro"] + "_RENAMED"
    assert replan.design_changes(PORT, new) == ["knobs"]


# ------------------------------------------------------- integrate_with_replans


class Stages:
    """Fake stage 2 and stage 3 for one host.

    `statuses` is what each integrate round returns, in order. `plans` is
    what each re-plan returns, in order. A plan entry that is an exception is
    raised instead, the way stage 2 refuses a plan."""

    def __init__(self, statuses, plans=()):
        self.statuses = list(statuses)
        self.plans = list(plans)
        self.integrate_calls: list[dict] = []
        self.plan_calls: list[str] = []
        self.saved: list[str] = []

    def integrate(self, dump, port_plan, test_plan, fresh):
        self.integrate_calls.append({
            "prefix": dump.prefix, "port": port_plan, "tests": test_plan, "fresh": fresh,
        })
        status = self.statuses.pop(0)
        result = {"host": "toy", "status": status, "attempts": 1}
        if status == "needs_replan":
            result["escalation"] = {"pointer": "/tests/performance/0/metric",
                                    "reason": "unreachable"}
        return result

    def plan(self, dump):
        self.plan_calls.append(dump.prefix)
        nxt = self.plans.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt

    def save_port(self, dump):
        self.saved.append(dump.prefix)

    def run(self, dump, replans=None):
        return replan.integrate_with_replans(
            dump, PORT, TESTS, integrate=self.integrate, plan=self.plan,
            save_port=self.save_port, replans=replans)


@pytest.fixture
def dump(tmp_path):
    return helpers.Dumper(out_dir=tmp_path, prefix="20260923_000000_")


def test_no_escalation_runs_one_round_exactly_as_before(dump):
    stages = Stages(["passed"])
    result = stages.run(dump, replans=2)

    assert result["status"] == "passed"
    assert result["replans"] == 0
    assert stages.plan_calls == []
    assert stages.integrate_calls[0]["prefix"] == dump.prefix
    assert stages.integrate_calls[0]["fresh"] is None  # the host's own default


def test_an_escalation_re_plans_and_integrates_again(dump):
    new_port = copy(PORT)
    new_port["structure"]["choice"] = "a different design"
    stages = Stages(["needs_replan", "passed"], plans=[(new_port, TESTS)])
    result = stages.run(dump, replans=2)

    assert result["status"] == "passed"
    assert result["replans"] == 1
    assert stages.plan_calls == ["20260923_000000_replan1_"]
    second = stages.integrate_calls[1]
    assert second["port"] is new_port
    assert second["prefix"] == "20260923_000000_replan1_"
    assert result["rounds"][0]["escalation"]["pointer"] == "/tests/performance/0/metric"
    assert result["rounds"][0]["replan"]["design_changes"] == ["structure.choice"]


def test_a_design_change_starts_the_next_round_fresh(dump):
    new_port = copy(PORT)
    new_port["hook_points"][0]["symbol"] = "moved"
    stages = Stages(["needs_replan", "passed"], plans=[(new_port, TESTS)])
    result = stages.run(dump, replans=1)

    assert stages.integrate_calls[1]["fresh"] is True
    assert result["rounds"][0]["replan"]["port_tree"] == "fresh"


def test_a_measurement_only_re_plan_keeps_the_port(dump):
    new_tests = copy(TESTS)
    new_tests["correctness"][0]["description"] = "measured differently now"
    stages = Stages(["needs_replan", "passed"], plans=[(copy(PORT), new_tests)])
    result = stages.run(dump, replans=1)

    assert stages.integrate_calls[1]["fresh"] is False
    assert stages.integrate_calls[1]["tests"] is new_tests
    assert result["rounds"][0]["replan"]["port_tree"] == "kept"


def test_the_budget_stops_a_plan_that_keeps_escalating(dump):
    stages = Stages(["needs_replan"] * 3, plans=[(copy(PORT), TESTS)] * 2)
    result = stages.run(dump, replans=2)

    assert result["status"] == "needs_replan"
    assert result["replans"] == 2
    assert len(stages.integrate_calls) == 3
    assert stages.plan_calls == ["20260923_000000_replan1_", "20260923_000000_replan2_"]
    assert "replan" not in result["rounds"][-1]


def test_a_zero_budget_is_the_old_behavior(dump):
    stages = Stages(["needs_replan"])
    result = stages.run(dump, replans=0)

    assert result["status"] == "needs_replan"
    assert result["replans"] == 0
    assert stages.plan_calls == []


def test_the_budget_defaults_to_the_constant(dump, monkeypatch):
    monkeypatch.setattr(C, "ESCALATION_REPLANS", 1)
    stages = Stages(["needs_replan"] * 2, plans=[(copy(PORT), TESTS)])
    result = stages.run(dump)

    assert result["replans"] == 1
    assert len(stages.integrate_calls) == 2


@pytest.mark.parametrize("refusal", [
    SystemExit("plan for toy has 1 unresolved plan error(s)"),
    RuntimeError("backend went away"),
])
def test_a_refused_re_plan_ends_the_rounds_and_says_why(dump, refusal):
    stages = Stages(["needs_replan"], plans=[refusal])
    result = stages.run(dump, replans=2)

    assert result["status"] == "replan_failed"
    assert str(refusal) in result["replan_error"]
    assert result["replans"] == 1
    assert len(stages.integrate_calls) == 1


@pytest.mark.parametrize("status", ["failed", "backend_error"])
def test_only_an_escalation_re_plans(dump, status):
    """A port that ran out of attempts, or a backend that failed, is not a
    plan defect. Re-planning it would hide the real result."""
    stages = Stages([status])
    result = stages.run(dump, replans=2)

    assert result["status"] == status
    assert stages.plan_calls == []


def test_the_port_is_saved_after_every_round(dump):
    """Before the next round can replace the tree it was built in."""
    new_port = copy(PORT)
    new_port["structure"]["choice"] = "a different design"
    stages = Stages(["needs_replan", "passed"], plans=[(new_port, TESTS)])
    stages.run(dump, replans=1)

    assert stages.saved == ["20260923_000000_", "20260923_000000_replan1_"]


# ------------------------------------------------------------ Dumper.child


def test_a_child_dumper_cannot_overwrite_its_parent(tmp_path):
    parent = helpers.Dumper(out_dir=tmp_path, prefix="20260923_000000_")
    first = parent.json("gate_toy_0.json", {"round": 0})
    second = parent.child("replan1").json("gate_toy_0.json", {"round": 1})

    assert first != second
    assert first.parent == second.parent
    assert json.loads(first.read_text()) == {"round": 0}
    assert second.name == "20260923_000000_replan1_gate_toy_0.json"


# ------------------------------------------------- the real pieces, together


class _NullTool:
    def stop(self):
        pass


def _stub_planner(monkeypatch, reply_text):
    """Stage 2's model, scripted. plan_node imports `llm` lazily for exactly
    this reason (see test_plan_node.py)."""
    seen = []
    mod = types.ModuleType("llm")
    mod.load_prompt = lambda name, **kw: f"[prompt {name}]"
    mod.make_llm = lambda backend, tools, resume=False: object()

    def run_llm(llm, prompt, tools):
        seen.append(prompt)
        return types.SimpleNamespace(result=reply_text, stream_result="", success=True)

    mod.run_llm = run_llm
    monkeypatch.setitem(sys.modules, "llm", mod)
    return seen


def test_an_escalation_reaches_the_planner_in_the_same_job(tmp_path, monkeypatch):
    """Round 0 escalates through the real stage 3. The real stage-2 node then
    reads that escalation, writes a new pair and marks it answered. Round 1
    ports against the new pair and passes. Nobody submits anything by hand."""
    monkeypatch.setattr(C, "PLAN_DIR", tmp_path / "plan")
    monkeypatch.setattr(C, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 3)
    monkeypatch.setattr(loop, "BashTool", lambda **kw: _NullTool())
    monkeypatch.setattr(loop, "make_llm", lambda *a, **kw: None)

    # Stage 3's model: implement, escalate after the gate fails, then
    # implement again in round 1.
    integrator_replies = [
        "implementing",
        "PLAN ESCALATION: /tests/performance/0/metric -- the host does not "
        "report this metric, so no port can move it.",
        "implementing against the new plan",
    ]
    monkeypatch.setattr(loop, "run_llm",
                        lambda _llm, prompt, _tools: types.SimpleNamespace(
                            result=integrator_replies.pop(0), stream_result="",
                            success=True, usage=None))
    verdicts = [gate.GateResult(False, ["G5 [bias_mpki] no improvement"]),
                gate.GateResult(True, [])]
    judged: list[dict] = []

    def run_gate(baseline, port_plan, test_plan):
        judged.append(port_plan)
        return verdicts.pop(0)

    adapter = loop.HostAdapter(
        name="toy", work_dir=str(FIXTURES / "toyhost"), notes="(notes)",
        resources={}, baseline=lambda: {"mpki": 1.0, "ipc": 1.0}, run_gate=run_gate,
    )

    new_port = copy(PORT)
    new_port["structure"]["choice"] = "re-planned after the escalation"
    planner_prompts = _stub_planner(
        monkeypatch,
        "## Port plan\n\n```json\n" + json.dumps(new_port)
        + "\n```\n\n## Test plan\n\n```json\n" + json.dumps(TESTS) + "\n```\n")

    def plan(d):
        return plan_node.make_plan(
            d, SPEC, "toy", str(FIXTURES / "toyhost"), "(notes)",
            revision=PORT["host_revision"])

    dump = helpers.Dumper(out_dir=tmp_path / "out", prefix="20260923_000000_")
    result = replan.integrate_with_replans(
        dump, PORT, TESTS,
        integrate=lambda d, pp, tp, fresh: loop.integrate(
            d, SPEC, "toy", "smoke", port_plan=pp, test_plan=tp, adapter=adapter),
        plan=plan, replans=2,
    )

    assert result["status"] == "passed", result
    assert result["replans"] == 1
    # The planner was told what stage 3 refused.
    assert "/tests/performance/0/metric" in planner_prompts[0]
    # The escalation is on file beside the plan, answered by round 1's plan.
    entries = json.loads(plan_revision.escalation_path("toy", "tinysc").read_text())
    assert [e["resolved"] for e in entries] == ["20260923_000000_replan1_"]
    # Round 1 was judged against the new plan, and both rounds kept their evidence.
    assert judged[-1]["structure"]["choice"] == "re-planned after the escalation"
    out = tmp_path / "out"
    assert (out / "20260923_000000_gate_toy_0.json").exists()
    assert (out / "20260923_000000_replan1_gate_toy_0.json").exists()
