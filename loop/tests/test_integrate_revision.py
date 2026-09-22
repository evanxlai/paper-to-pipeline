"""Tests for stage 3's plan-revision wiring, with a scripted LLM.

`test_plan_revision.py` covers the guard: which edits are allowed. These cover
the loop around it, which is where a guard that works can still be useless --
an accepted revision that the next gate run does not actually use, a rejection
that quietly writes the file anyway, a revision numbered over the top of an
earlier one.

The LLM is a list of canned replies rather than a model, and the gate is a
callable the test controls, so every case is deterministic and spends no
tokens. What is real is the code under test: `adopt_a_paper_loop.integrate`,
`plan_revision`, and the artifacts they write to a tmp dir.
"""

import json
from pathlib import Path

import pytest

import adopt_a_paper_loop as loop
import constants as C
import gate
import helpers
import plan_revision

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class FakeResponse:
    """What `run_llm` hands back, reduced to what the loop and Dumper read."""

    def __init__(self, text: str):
        self.result = text
        self.success = True
        self.stream_result = ""
        self.usage = None


class FakeLLM:
    """A scripted session.

    Replies are consumed in order. Past the end of the script the session
    answers with an inert line that proposes nothing and escalates nothing, so
    a test does not have to predict the exact turn count of a loop whose turn
    count is not what it is testing. `prompts` is the record every assertion
    about what the agent was told reads from."""

    INERT = "Continuing to work on the implementation."

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> FakeResponse:
        self.prompts.append(prompt)
        return FakeResponse(self.replies.pop(0) if self.replies else self.INERT)


@pytest.fixture
def port():
    return json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())


@pytest.fixture
def tests():
    return json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


@pytest.fixture
def spec():
    return json.loads((FIXTURES / "tinysc.spec.json").read_text())


@pytest.fixture
def harness(tmp_path, monkeypatch):
    """`integrate` with its two outside edges replaced: no chia bash tool and
    no model. Everything between them is the production code path."""
    monkeypatch.setattr(C, "PLAN_DIR", tmp_path / "plan")
    monkeypatch.setattr(C, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(loop, "BashTool", lambda **kw: _NullTool())
    monkeypatch.setattr(loop, "make_llm", lambda *a, **kw: None)

    def build(replies, gate_verdicts, port_plan, test_plan, spec):
        llm = FakeLLM(replies)
        monkeypatch.setattr(loop, "run_llm", lambda _llm, prompt, _tools: llm(prompt))
        seen: list[tuple] = []
        verdicts = list(gate_verdicts)

        def run_gate(baseline, pp, tp):
            seen.append((pp, tp))
            return verdicts.pop(0) if verdicts else gate.GateResult(False, ["still failing"])

        adapter = loop.HostAdapter(
            name="toy", work_dir=str(FIXTURES / "toyhost"), notes="(notes)",
            resources={}, baseline=lambda: {"mpki": 1.0, "ipc": 1.0},
            run_gate=run_gate,
        )
        dump = helpers.Dumper(out_dir=tmp_path / "out")
        result = loop.integrate(
            dump, spec, "toy", "smoke",
            port_plan=port_plan, test_plan=test_plan, adapter=adapter,
        )
        return result, seen, llm

    return build


class _NullTool:
    def stop(self):
        pass


def _revision_reply(port_plan, test_plan) -> str:
    return (
        "The plan named a symbol that has moved. Revising the hook point.\n\n"
        f"{plan_revision.REVISION_MARKER}\n\n"
        f"```json\n{json.dumps(port_plan)}\n```\n\n"
        f"```json\n{json.dumps(test_plan)}\n```\n"
    )


# ------------------------------------------------------------ the happy path


def test_accepted_revision_reaches_the_next_gate_run(harness, monkeypatch, spec, port, tests):
    """The whole point. A revision the guard accepts must be the pair the gate
    judges on the following attempt, not a file written and then ignored."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 2)
    revised = json.loads(json.dumps(port))
    revised["hook_points"][0]["symbol"] = "ToyPredictor::predict_v2"

    result, seen, _ = harness(
        replies=["implementing", _revision_reply(revised, tests)],
        gate_verdicts=[gate.GateResult(False, ["G3 [host_suite] failed"]),
                       gate.GateResult(True)],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["status"] == "passed"
    assert result["plan_revisions"] == 1
    assert len(seen) == 2
    assert seen[0][0]["hook_points"][0]["symbol"] != "ToyPredictor::predict_v2"
    assert seen[1][0]["hook_points"][0]["symbol"] == "ToyPredictor::predict_v2"


def test_accepted_revision_is_written_beside_stage_twos_output(
    harness, monkeypatch, spec, port, tests
):
    """Stage 2's artifact is the only record of what was originally asked of
    the port, so a revision is written next to it and never over it."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 2)
    base_plan, base_tests = helpers.plan_paths("toy", "tinysc")
    base_plan.parent.mkdir(parents=True, exist_ok=True)
    base_plan.write_text(json.dumps(port))
    base_tests.write_text(json.dumps(tests))

    revised = json.loads(json.dumps(port))
    revised["structure"]["choice"] = "revised shape"
    harness(
        replies=["implementing", _revision_reply(revised, tests)],
        gate_verdicts=[gate.GateResult(False, ["G3 failed"]), gate.GateResult(True)],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert json.loads(base_plan.read_text())["structure"]["choice"] == port["structure"]["choice"]
    rev_plan, rev_tests = plan_revision.revision_paths("toy", "tinysc", 1)
    assert json.loads(rev_plan.read_text())["structure"]["choice"] == "revised shape"
    assert rev_tests.exists()


def test_a_second_run_numbers_its_revision_after_the_first(
    harness, monkeypatch, spec, port, tests
):
    """`revision` is read off disk, so two runs over one host cannot both
    write rev1 and lose the earlier record."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 2)
    first_plan, first_tests = plan_revision.revision_paths("toy", "tinysc", 1)
    first_plan.parent.mkdir(parents=True, exist_ok=True)
    first_plan.write_text(json.dumps(port))
    first_tests.write_text(json.dumps(tests))

    revised = json.loads(json.dumps(port))
    revised["structure"]["choice"] = "from the second run"
    result, _, _ = harness(
        replies=["implementing", _revision_reply(revised, tests)],
        gate_verdicts=[gate.GateResult(False, ["G3 failed"]), gate.GateResult(True)],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["plan_revisions"] == 1
    second_plan, _ = plan_revision.revision_paths("toy", "tinysc", 2)
    assert json.loads(second_plan.read_text())["structure"]["choice"] == "from the second run"
    assert json.loads(first_plan.read_text())["structure"]["choice"] == port["structure"]["choice"]


# ------------------------------------------------------------- the refusals


def test_rejected_revision_writes_nothing_and_keeps_the_old_pair(
    harness, monkeypatch, spec, port, tests
):
    """A weakened test plan must leave no trace on the artifacts and must not
    reach the gate. The agent gets one repair turn and then the loop moves on."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 2)
    weakened = json.loads(json.dumps(tests))
    weakened["performance"][0]["block_threshold"]["min_relative_improvement"] = -1.0

    result, seen, llm = harness(
        replies=[
            "implementing",
            _revision_reply(port, weakened),
            "understood, I will port it properly",  # the repair turn's answer
        ],
        gate_verdicts=[gate.GateResult(False, ["G5 [bias_mpki] no improvement"]),
                       gate.GateResult(False, ["G5 [bias_mpki] no improvement"])],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["status"] == "failed"
    assert result["plan_revisions"] == 0
    assert not plan_revision.revision_paths("toy", "tinysc", 1)[0].exists()
    # Both gate runs saw the original threshold.
    for _, tp in seen:
        assert tp["performance"][0]["block_threshold"]["min_relative_improvement"] == 0.0
    # And the rejection told the agent what it may not change. Checked over
    # every prompt rather than the last one: the loop carries on to the next
    # attempt after a rejection, so the repair turn is not the final word.
    assert any("revision_froze_field" in p for p in llm.prompts)


def test_rejection_names_the_escalation_route(harness, monkeypatch, spec, port, tests):
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 1)
    weakened = json.loads(json.dumps(tests))
    weakened["correctness"] = weakened["correctness"][1:]

    _, _, llm = harness(
        replies=["implementing", _revision_reply(port, weakened), "ok"],
        gate_verdicts=[gate.GateResult(False, ["G3 failed"])],
        port_plan=port, test_plan=tests, spec=spec,
    )
    assert any("PLAN ESCALATION:" in p for p in llm.prompts)


def test_a_reply_without_the_marker_is_an_ordinary_debug_turn(
    harness, monkeypatch, spec, port, tests
):
    """Two fenced json blocks in a reply that explains a failure must not be
    read as a proposal -- quoting JSON while debugging is normal."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 2)
    chatty = (
        "The stats came out as\n```json\n{\"mpki\": 3}\n```\nand baseline was\n"
        "```json\n{\"mpki\": 2}\n```\nso the off path leaks. Fixed.\n"
    )
    result, seen, _ = harness(
        replies=["implementing", chatty],
        gate_verdicts=[gate.GateResult(False, ["G2 leak"]), gate.GateResult(True)],
        port_plan=port, test_plan=tests, spec=spec,
    )
    assert result["status"] == "passed"
    assert result["plan_revisions"] == 0


# ------------------------------------------------------------- escalation


def test_escalation_ends_the_attempt_with_its_own_status(
    harness, monkeypatch, spec, port, tests
):
    """The "serious issue" route. It is not a failure by the port, so it does
    not read as one, and it does not burn the remaining attempts."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 6)
    result, seen, _ = harness(
        replies=[
            "implementing",
            "This metric cannot be reached from the only hook this host offers.\n"
            "PLAN ESCALATION: /tests/performance/0/metric -- the host does not "
            "report mpki per branch, so no port can move it.\n",
        ],
        gate_verdicts=[gate.GateResult(False, ["G5 [bias_mpki] no improvement"])],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["status"] == "needs_replan"
    assert result["attempts"] == 1
    assert result["escalation"]["pointer"] == "/tests/performance/0/metric"
    assert "does not report mpki" in result["escalation"]["reason"]
    assert len(seen) == 1


def test_escalation_beats_a_revision_in_the_same_turn(
    harness, monkeypatch, spec, port, tests
):
    """A turn that disclaims its own judgement must not also get a plan edit
    accepted out of it."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 3)
    revised = json.loads(json.dumps(port))
    revised["structure"]["choice"] = "should not be written"

    result, _, _ = harness(
        replies=[
            "implementing",
            _revision_reply(revised, tests)
            + "\nPLAN ESCALATION: /plan/structure -- this host has no usable hook.\n",
        ],
        gate_verdicts=[gate.GateResult(False, ["G1 build failed"])],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["status"] == "needs_replan"
    assert result["plan_revisions"] == 0
    assert not plan_revision.revision_paths("toy", "tinysc", 1)[0].exists()


# ---------------------------------------------------------- the budget


def test_revision_budget_is_enforced_and_announced(harness, monkeypatch, spec, port, tests):
    """Past the budget the proposal is not reviewed at all, and the agent is
    told so -- a silently dropped proposal looks like an accepted one that did
    not help."""
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 3)
    monkeypatch.setattr(C, "PLAN_REVISIONS", 1)

    first = json.loads(json.dumps(port))
    first["structure"]["choice"] = "first revision"
    second = json.loads(json.dumps(port))
    second["structure"]["choice"] = "second revision"

    result, seen, llm = harness(
        replies=["implementing", _revision_reply(first, tests),
                 _revision_reply(second, tests)],
        gate_verdicts=[gate.GateResult(False, ["G3 failed"]),
                       gate.GateResult(False, ["G3 failed"]),
                       gate.GateResult(False, ["G3 failed"])],
        port_plan=port, test_plan=tests, spec=spec,
    )

    assert result["plan_revisions"] == 1
    assert not plan_revision.revision_paths("toy", "tinysc", 2)[0].exists()
    assert seen[-1][0]["structure"]["choice"] == "first revision"
    assert any("already used its 1 revision" in p for p in llm.prompts)
