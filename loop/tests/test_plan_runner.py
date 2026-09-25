"""Tests for the test-plan runner and the gate it feeds.

The fast half evaluates pass conditions and threshold arithmetic against
hand-built outcomes, with no host at all. The slow half compiles the fixture
host three times -- unported, correctly ported, and ported with one specific
defect -- and runs the real `plan_runner.run_test_plan` and `gate.check_gate`
over it. No LLM is involved in any of it.

The slow half is the point. A gate is only worth anything if both halves are
shown: that it passes a port which does what the plan says, and that it fails
one which does not. Before this file existed, the recorded artifact of a
passing stage-3 run was a checkout containing none of the plan's spec unit
tests and no params header -- the gate promoted it because the only thing it
asked was whether the host's pre-existing suite still exited 0.
"""

import json
import shutil
from pathlib import Path

import pytest

import gate
import plan_runner
from plan_runner import ShellOutcome
from toy_host import ToyHost

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REFERENCE = FIXTURES / "tinysc_reference"


@pytest.fixture
def tests_doc():
    return json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())


@pytest.fixture
def baseline():
    return {"mpki": 10.0, "ipc": 1.0, "bias": {"mpki": 20.0, "ipc": 0.5}}


def entry(**over):
    base = {
        "id": "e", "kind": "generated_smoke", "description": "d",
        "command": "true", "feature_state": "off",
        "pass_condition": {"kind": "exit_zero"},
    }
    base.update(over)
    return base


def evaluate(e, outcome, metrics=None, tests=None, baseline_doc=None):
    return plan_runner.evaluate_condition(
        e, outcome, metrics or {}, tests or {"metric_keys": ["mpki", "ipc"]},
        baseline_doc or {},
    )


# ------------------------------------------------------- the pass conditions
def test_exit_zero_passes_on_zero_and_fails_otherwise():
    assert evaluate(entry(), ShellOutcome(0, "fine")) == ""
    assert "exited 3" in evaluate(entry(), ShellOutcome(3, "bad"))


def test_a_timeout_is_a_failure_with_a_reason_not_an_exception():
    why = evaluate(entry(), ShellOutcome(-1, "", timed_out=True))
    assert "timed out" in why


def test_stdout_matches_needs_the_pattern():
    e = entry(pass_condition={"kind": "stdout_matches", "pattern": "ok: thing"})
    assert evaluate(e, ShellOutcome(0, "ok: thing\n")) == ""
    assert "does not match" in evaluate(e, ShellOutcome(0, "nothing here"))


def test_a_pattern_condition_also_requires_a_clean_exit():
    """The vacuity this closes: 'the output contains no FAIL line' is
    satisfied by a command that crashed before printing anything, which is
    the most likely way a broken port passes a test."""
    e = entry(pass_condition={"kind": "stdout_excludes", "pattern": "FAIL"})
    assert evaluate(e, ShellOutcome(0, "all good")) == ""
    why = evaluate(e, ShellOutcome(1, ""))
    assert "not evidence" in why


def test_a_pattern_condition_can_opt_out_of_the_exit_clause():
    e = entry(pass_condition={
        "kind": "stdout_excludes", "pattern": "FAIL", "allow_nonzero_exit": True,
    })
    assert evaluate(e, ShellOutcome(1, "expected to exit non-zero")) == ""


def test_matches_clean_tree_compares_the_recorded_exit_code():
    e = entry(
        kind="existing_regression",
        clean_tree_result={"exit_code": 1, "passed": False, "summary": "2 failures"},
        pass_condition={"kind": "matches_clean_tree"},
    )
    # A test that already failed must keep failing the same way; passing it
    # is not the bar, and exiting 0 here would mean the tree changed.
    assert evaluate(e, ShellOutcome(1, "still broken")) == ""
    assert "where the clean tree" in evaluate(e, ShellOutcome(0, "fixed?"))


def test_matches_clean_tree_compares_a_captured_group_against_the_summary():
    e = entry(
        kind="existing_regression",
        clean_tree_result={"exit_code": 0, "passed": True, "summary": "4 checks"},
        pass_condition={"kind": "matches_clean_tree", "pattern": r"(\d+ checks)"},
    )
    assert evaluate(e, ShellOutcome(0, "4 checks, 0 failures")) == ""
    assert "summary is" in evaluate(e, ShellOutcome(0, "9 checks, 0 failures"))


def test_metrics_equal_baseline_reads_the_pointer_and_the_declared_keys(baseline):
    e = entry(pass_condition={
        "kind": "metrics_equal_baseline", "baseline_pointer": "/bias",
    })
    assert evaluate(e, ShellOutcome(0, ""), {"mpki": 20.0, "ipc": 0.5},
                    baseline_doc=baseline) == ""
    why = evaluate(e, ShellOutcome(0, ""), {"mpki": 20.1, "ipc": 0.5},
                   baseline_doc=baseline)
    assert "not baseline-identical" in why


def test_metrics_equal_baseline_ignores_keys_the_plan_did_not_declare(baseline):
    """A recorded baseline also holds raw counters and a nested sub-document.
    Iterating its own keys instead of the declared ones would compare those."""
    e = entry(pass_condition={"kind": "metrics_equal_baseline"})
    assert evaluate(e, ShellOutcome(0, ""), {"mpki": 10.0, "ipc": 1.0, "cycles": 7},
                    baseline_doc=baseline) == ""


def test_a_per_entry_tolerance_overrides_the_plan_wide_one(baseline):
    tests = {"metric_keys": ["mpki"], "baseline_rel_tol": 0.0}
    loose = entry(pass_condition={"kind": "metrics_equal_baseline", "rel_tol": 0.05})
    strict = entry(pass_condition={"kind": "metrics_equal_baseline"})
    assert evaluate(loose, ShellOutcome(0, ""), {"mpki": 10.2}, tests, baseline) == ""
    assert evaluate(strict, ShellOutcome(0, ""), {"mpki": 10.2}, tests, baseline) != ""


def test_metric_threshold_compares_one_parsed_metric():
    e = entry(pass_condition={
        "kind": "metric_threshold", "metric": "mpki", "comparison": "<=", "value": 5,
    })
    assert evaluate(e, ShellOutcome(0, ""), {"mpki": 4.0}) == ""
    assert "fails mpki <= 5" in evaluate(e, ShellOutcome(0, ""), {"mpki": 6.0})
    assert "no metric" in evaluate(e, ShellOutcome(0, ""), {})


# ------------------------------------------------------------- the arithmetic
def test_relative_improvement_follows_the_declared_direction():
    assert plan_runner._relative_improvement(10.0, 8.0, "decrease") == pytest.approx(0.2)
    assert plan_runner._relative_improvement(10.0, 12.0, "increase") == pytest.approx(0.2)
    assert plan_runner._relative_improvement(10.0, 12.0, "decrease") == pytest.approx(-0.2)


# --------------------------------------------------- traces that never ran
class StubExecutor:
    """A host whose runs are scripted. `fails` maps (trace, feature_on) to a
    failure, so a trace can die on one side of the comparison and not the
    other."""

    def __init__(self, fails=(), mpki_on=50.0, mpki_off=100.0):
        self.name = "stub"
        self.fails = set(fails)
        self.mpki = {True: mpki_on, False: mpki_off}
        self.state = None

    def build(self, *, feature_on, timeout_s):
        return plan_runner.BuildOutcome(ok=True, log="")

    def shell(self, command, *, feature_on, env=None, timeout_s=0):
        self.state = feature_on
        trace = command.rsplit(" ", 1)[-1]
        if (trace, feature_on) in self.fails:
            return plan_runner.ShellOutcome(exit_code=1, output="crashed")
        return plan_runner.ShellOutcome(
            exit_code=0, output='{"mpki": %f, "ipc": 1.0}' % self.mpki[feature_on]
        )

    def parse_metrics(self, output):
        return json.loads(output) if output.startswith("{") else {}

    def run_traces(self, traces, *, feature_on, timeout_s):
        raise AssertionError("this plan declares command_per_trace")


def perf_entry(**over):
    base = {
        "id": "p", "description": "d", "metric": "mpki", "direction": "decrease",
        "traces": ["a.trace", "b.trace"],
        "run": {"mode": "command_per_trace", "command_template": "sim {trace}"},
        "block_threshold": {"min_relative_improvement": 0.0},
        "warn_threshold": {"target_relative_improvement": 0.1, "claim_source": "s"},
    }
    base.update(over)
    return base


def test_the_gate_refuses_an_entry_scored_on_the_traces_that_survived():
    """Scoring on whatever ran is the quiet version of passing: the mean is
    over a different trace set than the plan declared."""
    result = plan_runner.PerformanceResult(
        id="bias_mpki", metric="mpki", direction="decrease",
        baseline=100.0, measured=50.0, relative_improvement=0.5,
        block_passed=True, warn_passed=True,
        n_traces=3, failed_traces=["hard_a.trace", "hard_b.trace"],
    )
    verdict = gate.check_gate(plan_runner.TestPlanResults(
        build_ok=True,
        correctness=[plan_runner.CorrectnessResult(
            id="off", kind="feature_off_baseline", passed=True)],
        performance=[result], smoke_ok=True,
    ))
    assert not verdict.passed
    assert "2 of 3 trace(s) did not complete" in verdict.reasons[0]
    assert "hard_a.trace" in verdict.reasons[0]


def test_a_trace_that_dies_only_on_the_baseline_side_is_still_recorded():
    """Feature-on and feature-off dropping different traces leaves the two
    means over different trace sets. Recording only the feature-on side hides
    half of that."""
    executor = StubExecutor(fails=[("b.trace", False)])
    result = plan_runner._run_performance(executor, perf_entry(), 60, {})
    assert result.failed_traces == ["b.trace"]


def test_a_clean_run_on_both_sides_records_no_failures():
    result = plan_runner._run_performance(StubExecutor(), perf_entry(), 60, {})
    assert result.failed_traces == []
    assert result.block_passed
    assert result.relative_improvement == pytest.approx(0.5)


def test_a_recorded_baseline_entry_only_reports_its_own_side(baseline):
    """With `recorded` there is no second run to fail, so the only failures
    are the feature-on ones."""
    entry = perf_entry(baseline={"source": "recorded", "pointer": "/bias"},
                       metric="mpki", traces=["a.trace", "b.trace"])
    executor = StubExecutor(fails=[("b.trace", True)])
    result = plan_runner._run_performance(executor, entry, 60, baseline)
    assert result.failed_traces == ["b.trace"]


# ------------------------------------------------------------ the whole gate
def materialize(tmp_path, ported=False, defect=None):
    """A host, and the baseline recorded off it BEFORE the port lands.

    The ordering is the point, and it is the ordering the real loop uses: a
    baseline measured on the ported tree is a baseline the port had a chance
    to move, so a knob that fails to gate would quietly define its own
    reference and G2 would compare a leak against itself."""
    host = ToyHost(tmp_path / "host", force_first_fail=False)
    host.materialize()
    baseline = host.record_baseline()
    shutil.rmtree(host.work_dir / "build", ignore_errors=True)

    if ported:
        for src in (REFERENCE / "src").iterdir():
            shutil.copyfile(src, host.work_dir / "src" / src.name)
        shutil.copyfile(
            REFERENCE / "tests" / "test_predictor.cpp",
            host.work_dir / "tests" / "test_predictor.cpp",
        )
    if defect == "off_path_leaks":
        # The single most important thing G2 exists to catch: the feature
        # runs even with its knob off, so the port is no longer a superset of
        # the baseline and every later measurement is against the wrong thing.
        # Both guards have to go: dropping only the one in apply() changes
        # nothing observable, because a table that train() never writes stays
        # at zero and a zero counter is never confident enough to override.
        path = host.work_dir / "src" / "tinysc.cpp"
        body = path.read_text()
        body = body.replace(
            "bool TinySC::apply(uint64_t pc, bool base) const {\n  if (!enabled_) return base;",
            "bool TinySC::apply(uint64_t pc, bool base) const {",
        )
        body = body.replace(
            "void TinySC::train(uint64_t pc, bool taken) {\n  if (!enabled_) return;",
            "void TinySC::train(uint64_t pc, bool taken) {",
        )
        assert "if (!enabled_)" not in body, "the defect injection stopped matching"
        path.write_text(body)
    return host, baseline


@pytest.fixture(scope="module")
def _cc_available():
    if shutil.which("g++") is None:
        pytest.skip("g++ is not installed; the fixture host cannot be built")


def run_gate_over(pair):
    host, baseline = pair
    return host.run_gate(baseline)


def test_the_unported_host_fails_the_gate(tmp_path, _cc_available):
    """The host builds, its own suite passes and the feature-off metrics
    match -- and the gate must still refuse it, because none of the plan's
    spec unit tests exist and nothing moved the metric."""
    verdict = run_gate_over(materialize(tmp_path))
    assert not verdict.passed
    codes = " ".join(verdict.reasons)
    assert "G3 [spec_disabled_matches_base_predictor]" in codes
    assert "G3 [spec_history_correlated_branch_is_learned]" in codes
    assert "G3 [spec_untrained_entry_defers_to_base]" in codes
    assert "G5 [bias_mpki]" in codes
    # It gets the easy ones right, which is what makes the refusal specific.
    assert "G1" not in codes and "G2" not in codes and "G4" not in codes


def test_the_reference_port_passes_the_gate(tmp_path, _cc_available):
    verdict = run_gate_over(materialize(tmp_path, ported=True))
    assert verdict.passed, verdict.feedback
    assert verdict.reasons == []


def test_a_port_whose_knob_does_not_gate_fails_g2(tmp_path, _cc_available):
    verdict = run_gate_over(materialize(tmp_path, ported=True, defect="off_path_leaks"))
    assert not verdict.passed
    assert any(r.startswith("G2 ") for r in verdict.reasons), verdict.feedback
    assert any("not baseline-identical" in r for r in verdict.reasons)


def test_a_met_magnitude_target_produces_no_warning(tmp_path, _cc_available):
    """The reference port improves bias MPKI by about 0.58 against a claimed
    0.5, so there is no shortfall to record."""
    verdict = run_gate_over(materialize(tmp_path, ported=True))
    assert verdict.warnings == []


def test_a_magnitude_shortfall_is_recorded_and_does_not_block(tmp_path, _cc_available):
    """The asymmetry the whole two-threshold design exists for: an untuned
    port that moves the metric the right way is promoted, and its distance
    from the paper's claim is reported rather than held against it."""
    host, baseline = materialize(tmp_path, ported=True)
    host.test_plan["performance"][0]["warn_threshold"]["target_relative_improvement"] = 0.95
    verdict = run_gate_over((host, baseline))
    assert verdict.passed
    assert len(verdict.warnings) == 1
    assert "Recorded, not blocking" in verdict.warnings[0]


def test_a_wrong_direction_blocks_even_though_the_metric_moved(tmp_path, _cc_available):
    host, baseline = materialize(tmp_path, ported=True)
    host.test_plan["performance"][0]["direction"] = "increase"
    verdict = run_gate_over((host, baseline))
    assert not verdict.passed
    assert any("does not beat the 0.0 floor" in r for r in verdict.reasons)
    # The mechanism fired and did harm; telling the debug agent it is "not
    # reaching the metric" sends it hunting for wiring that is fine.
    assert any("moved the wrong way" in r for r in verdict.reasons)
    assert not any("not reaching the metric" in r for r in verdict.reasons)


def test_an_unmoved_metric_is_diagnosed_as_not_reaching_it(tmp_path, _cc_available):
    verdict = run_gate_over(materialize(tmp_path, ported=False))
    assert not verdict.passed
    assert any("not reaching the metric" in r for r in verdict.reasons)
    assert not any("wrong way" in r for r in verdict.reasons)
    # On and off are bit-identical and the fixture binds its knob at run
    # time, so the reason names the one-build trap with the plan's macro.
    assert any("identical in every metric" in r and "#if SR_TINYSC_ENABLE" in r
               for r in verdict.reasons)


def test_identical_runs_under_a_rebuilt_binding_point_at_the_macro_not_at_if():
    from plan_runner import _identical_on_and_off
    text = _identical_on_and_off({"macro": "SR_X", "binding": "compile_time_define"})
    assert "builds once per state" in text and "SR_X" in text
    assert "#if" not in text
    text = _identical_on_and_off({"macro": "SR_X", "binding": "runtime_env"})
    assert "ONE build" in text and "#if SR_X" in text


def test_a_companion_regression_reads_as_a_trade_only_when_the_target_improved(
        tmp_path, _cc_available):
    host, baseline = materialize(tmp_path, ported=True)
    companion = host.test_plan["performance"][0]["block_threshold"]["no_regression"][0]
    companion["direction"] = "decrease"
    verdict = run_gate_over((host, baseline))
    assert any("is buying" in r for r in verdict.reasons)

    host, baseline = materialize(tmp_path / "both", ported=True)
    perf = host.test_plan["performance"][0]
    perf["direction"] = "increase"  # the target now got worse too
    perf["block_threshold"]["no_regression"][0]["direction"] = "decrease"
    verdict = run_gate_over((host, baseline))
    assert not any("is buying" in r for r in verdict.reasons)
    assert any("a cost, not a trade" in r for r in verdict.reasons)


def test_a_companion_metric_regression_blocks(tmp_path, _cc_available):
    """A feature that buys its target metric with another one is not a port
    that works, and the target-metric check alone cannot see it."""
    host, baseline = materialize(tmp_path, ported=True)
    companion = host.test_plan["performance"][0]["block_threshold"]["no_regression"][0]
    companion["direction"] = "decrease"  # now pretend lower IPC is better
    verdict = run_gate_over((host, baseline))
    assert not verdict.passed
    assert any("regressed" in r and "ipc" in r for r in verdict.reasons)


def test_a_performance_trace_that_does_not_run_blocks_on_the_real_host(
    tmp_path, _cc_available
):
    """End to end: a correct port, improving the metric on the trace that
    works, is still refused when another declared trace never completes."""
    host, baseline = materialize(tmp_path, ported=True)
    host.test_plan["performance"][0]["traces"] = [
        "workloads/bias.trace", "workloads/nope.trace",
    ]
    verdict = run_gate_over((host, baseline))
    assert not verdict.passed
    assert any("nope.trace" in r and "did not complete" in r for r in verdict.reasons)


def test_a_build_failure_short_circuits_to_one_reason(tmp_path, _cc_available):
    host, _ = materialize(tmp_path)
    (host.work_dir / "src" / "predictor.cpp").write_text("this is not c++\n")
    verdict = host.run_gate({"mpki": 0.0, "ipc": 0.0})
    assert not verdict.passed
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].startswith("G1 build failed")


def test_the_shell_runs_each_distinct_command_once(tmp_path, _cc_available):
    """Four correctness entries share `make test`. Without dedup a single
    attempt runs the suite four times, and on a real host the equivalent is
    four multi-minute rebuilds."""
    host, baseline = materialize(tmp_path, ported=True)
    calls = []
    real = host.executor.shell

    def counting(command, **kw):
        calls.append((command, kw.get("feature_on")))
        return real(command, **kw)

    host.executor.shell = counting
    run_gate_over((host, baseline))
    assert calls.count(("make test", False)) == 1


def test_the_injected_first_failure_survives_a_build_failure(tmp_path, _cc_available):
    """The smoke test injects a first-attempt failure to prove the debug turn
    works. It used to be computed after the build, so an attempt 1 that did
    not compile never asked for the marker while attempt 2 still demanded
    it -- the run then failed with a message its own transcript contradicted."""
    host = ToyHost(tmp_path / "host", force_first_fail=True)
    host.materialize()
    (host.work_dir / "src" / "predictor.cpp").write_text("this is not c++\n")
    verdict = host.run_gate({"mpki": 0.0, "ipc": 0.0})
    assert not verdict.passed
    assert any("append the exact line" in r for r in verdict.reasons)
