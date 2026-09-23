"""What a failing gate tells the debug agent, and proof that it tells it
nothing new about pass or fail.

A host returns its log with every trace fan-out (TraceOutcome.log_tail):
a gem5 panic and its simerr tail, a guest's stderr, or the compiler errors
of a feature-on build that failed. Before these tests, plan_runner dropped
that text, so a G4 or G5 failure named workloads and said nothing about
why. A G2 command whose metrics were missing said "measured=None" and
nothing about the crash that caused it.

Every test here keeps one rule in view: the log only adds text to a reason
that already exists. The verdict, the set of reasons and each reason's
first line are the same with or without it. cbp2025 is producing the
project's main result, so its pass/fail must not move.
"""

import pytest

import gate
import plan_runner
from plan_runner import ShellOutcome, TraceOutcome

PANIC = "panic: TAGE_SC_L::sr_update: index out of range\nsimerr: Aborted (core dumped)"


class TraceExecutor:
    """A host_adapter host whose fan-outs are scripted per state.

    `outcomes[feature_on]` is the TraceOutcome that state returns, or a
    callable of the trace list that builds one. Every shell command exits
    `shell_exit` and prints `shell_output`, which by default matches the
    baseline, so the G2 entry holds unless a test says otherwise."""

    name = "stub"

    def __init__(self, on, off=None, shell_output="mpki 10.0\nipc 1.0\n", shell_exit=0):
        self.outcomes = {True: on, False: off if off is not None else on}
        self.shell_output = shell_output
        self.shell_exit = shell_exit

    def build(self, *, feature_on, timeout_s):
        return plan_runner.BuildOutcome(ok=True, log="")

    def shell(self, command, *, feature_on, env=None, timeout_s=0):
        return ShellOutcome(exit_code=self.shell_exit, output=self.shell_output)

    def parse_metrics(self, output):
        out = {}
        for line in output.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] in ("mpki", "ipc"):
                out[parts[0]] = float(parts[1])
        return out

    def run_traces(self, traces, *, feature_on, timeout_s):
        outcome = self.outcomes[feature_on]
        return outcome(list(traces)) if callable(outcome) else outcome


def clean(mpki=10.0, ipc=1.0):
    return TraceOutcome(ok=True, metrics={"mpki": mpki, "ipc": ipc})


def failed(names, log=PANIC, metrics=None):
    return TraceOutcome(ok=False, metrics=dict(metrics or {}), failed=list(names),
                        log_tail=log)


def plan(**over):
    doc = {
        "metric_keys": ["mpki", "ipc"],
        "correctness": [{
            "id": "off_equals_baseline", "kind": "feature_off_baseline",
            "description": "d", "command": "run a", "feature_state": "off",
            "pass_condition": {"kind": "metrics_equal_baseline",
                               "baseline_pointer": "/per_trace/a", "rel_tol": 0.0},
        }],
        "smoke": {"traces": ["a", "b"]},
        "performance": [{
            "id": "mpki_drops", "description": "d", "metric": "mpki",
            "direction": "decrease", "traces": ["a", "b"],
            "block_threshold": {"min_relative_improvement": 0.0,
                                "no_regression": [{"metric": "ipc", "direction": "increase",
                                                   "max_relative_regression": 0.0}]},
            "warn_threshold": {"target_relative_improvement": 0.05, "claim_source": "s"},
        }],
    }
    doc.update(over)
    return doc


BASELINE = {"per_trace": {"a": {"mpki": 10.0, "ipc": 1.0}}}


def judge(executor, test_plan=None):
    results = plan_runner.run_test_plan(executor, test_plan or plan(), {}, BASELINE)
    return results, gate.check_gate(results)


def first_lines(verdict):
    return [r.splitlines()[0] for r in verdict.reasons]


# ------------------------------------------------------------------- G4


def test_a_failed_smoke_carries_the_hosts_log_into_the_g4_reason():
    executor = TraceExecutor(on=failed(["b"]), off=clean())
    results, verdict = judge(executor, plan(performance=[]))
    assert results.smoke_log_tail == PANIC
    [g4] = [r for r in verdict.reasons if r.startswith("G4")]
    assert g4.splitlines()[0] == "G4 feature-on smoke did not complete cleanly: b"
    assert "panic: TAGE_SC_L::sr_update" in g4
    assert "simerr: Aborted" in g4


def test_a_feature_on_build_failure_reaches_the_g4_reason():
    """The compile_time_define case: the code under the enable macro does not
    compile, and run_traces hands back the compiler output instead of
    running anything. The agent must see the compiler, not two workload
    names that suggest a runtime bug."""
    compiler = ("the host did not build with the feature on, so no workload was run:\n"
                "src/cpu/pred/tage_sc_l.cc:212: error: 'srTable' was not declared")
    executor = TraceExecutor(on=failed(["a", "b"], log=compiler), off=clean())
    _, verdict = judge(executor, plan(performance=[]))
    [g4] = [r for r in verdict.reasons if r.startswith("G4")]
    assert "'srTable' was not declared" in g4


def test_the_g4_log_is_cut_to_its_last_characters():
    log = "EARLY-LINE\n" + "x" * 5000 + "\nLAST-LINE"
    _, verdict = judge(TraceExecutor(on=failed(["a"], log=log), off=clean()),
                       plan(performance=[]))
    [g4] = [r for r in verdict.reasons if r.startswith("G4")]
    assert g4.endswith("LAST-LINE")
    assert "EARLY-LINE" not in g4
    assert len(g4) < len(log)
    assert g4.split("log ends with:\n", 1)[1] == log[-gate.LOG_TAIL_CHARS:]


def test_a_passing_smoke_adds_nothing_even_when_the_host_sent_a_log():
    """The command_per_trace route keeps the last output on success too.
    A passing G4 is not a reason, so there is nothing to append to."""
    executor = TraceExecutor(on=TraceOutcome(ok=True, metrics={"mpki": 5.0, "ipc": 1.0},
                                             log_tail="all fine"),
                             off=clean())
    _, verdict = judge(executor)
    assert not [r for r in verdict.reasons if r.startswith("G4")]
    assert verdict.passed


# ------------------------------------------------------------------- G5


def test_g5_failed_traces_carry_the_failing_sides_log():
    executor = TraceExecutor(on=failed(["b"], metrics={"mpki": 5.0, "ipc": 1.0}),
                             off=clean())
    results, verdict = judge(executor)
    [perf] = results.performance
    assert perf.log_tail == f"feature-on log:\n{PANIC}"
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert g5.splitlines()[0].startswith("G5 [mpki_drops] 1 of 2 trace(s) did not complete: b.")
    assert "feature-on log:" in g5 and "panic: TAGE_SC_L::sr_update" in g5


def test_g5_with_the_metric_missing_carries_the_log():
    """Every workload died, so there is no mean at all."""
    executor = TraceExecutor(on=failed(["a", "b"]), off=clean())
    _, verdict = judge(executor)
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert "panic: TAGE_SC_L::sr_update" in g5


def test_g5_names_the_baseline_side_when_only_it_failed():
    executor = TraceExecutor(on=clean(mpki=5.0),
                             off=failed(["a"], log="off-side crash",
                                        metrics={"mpki": 10.0, "ipc": 1.0}))
    results, verdict = judge(executor)
    [perf] = results.performance
    assert perf.log_tail == "feature-off log:\noff-side crash"
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert "feature-off log:\noff-side crash" in g5


def test_when_both_sides_fail_the_feature_on_log_comes_last():
    """The gate keeps the end of the text, and the feature-on run is the one
    the port changed, so that is the one a cut must not lose."""
    # Each side still has a mean over the traces that survived, so both
    # sides run. With no feature-on mean the entry stops before feature-off.
    executor = TraceExecutor(on=failed(["a"], log="ON" * 2000,
                                       metrics={"mpki": 5.0, "ipc": 1.0}),
                             off=failed(["a"], log="OFF",
                                        metrics={"mpki": 10.0, "ipc": 1.0}))
    results, verdict = judge(executor)
    [perf] = results.performance
    assert perf.log_tail.index("feature-off log:") < perf.log_tail.index("feature-on log:")
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert g5.endswith("ON")


def test_g5_below_its_floor_on_clean_runs_carries_no_log():
    """A port that ran cleanly and did not move the metric has no log that
    explains anything. The reason is the arithmetic, as before."""
    executor = TraceExecutor(on=TraceOutcome(ok=True, metrics={"mpki": 10.0, "ipc": 1.0},
                                             log_tail="noise"),
                             off=TraceOutcome(ok=True, metrics={"mpki": 10.0, "ipc": 1.0},
                                              log_tail="noise"))
    results, verdict = judge(executor)
    [perf] = results.performance
    assert perf.log_tail == ""
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert "log ends with" not in g5
    assert "does not beat the 0.0 floor" in g5


def test_a_missing_companion_metric_counts_as_something_to_report():
    executor = TraceExecutor(on=TraceOutcome(ok=True, metrics={"mpki": 5.0},
                                             log_tail="ipc stat absent"),
                             off=clean())
    results, verdict = judge(executor)
    [perf] = results.performance
    assert "ipc stat absent" in perf.log_tail
    [g5] = [r for r in verdict.reasons if r.startswith("G5")]
    assert "companion metric 'ipc' was not measured" in g5.splitlines()[0]
    assert "ipc stat absent" in g5


# --------------------------------------------- the verdict does not move


@pytest.mark.parametrize("on, off", [
    (failed(["b"], metrics={"mpki": 5.0, "ipc": 1.0}), clean()),
    (failed(["a", "b"]), clean()),
    (clean(mpki=5.0), failed(["a"], metrics={"mpki": 10.0, "ipc": 1.0})),
    (failed(["a"]), failed(["a"])),
    (clean(), clean()),
    (clean(mpki=5.0), clean()),
])
def test_the_log_never_changes_pass_fail_or_a_reasons_first_line(on, off):
    """The same runs with and without the host's log. Only the text after
    each reason's first line may differ."""
    def silent(outcome):
        return TraceOutcome(ok=outcome.ok, metrics=dict(outcome.metrics),
                            failed=list(outcome.failed), log_tail="")

    _, loud = judge(TraceExecutor(on=on, off=off))
    _, quiet = judge(TraceExecutor(on=silent(on), off=silent(off)))
    assert loud.passed == quiet.passed
    assert first_lines(loud) == first_lines(quiet)
    assert all("log ends with" not in r for r in quiet.reasons)
    assert loud.warnings == quiet.warnings


def test_a_gate_result_without_the_new_fields_is_still_judged():
    """check_gate takes its input structurally. A caller that builds results
    without log fields gets the reasons it got before."""
    from types import SimpleNamespace

    results = SimpleNamespace(
        build_ok=True, build_log_tail="",
        correctness=[plan_runner.CorrectnessResult(
            id="off", kind="feature_off_baseline", passed=True)],
        smoke_ok=False, smoke_failures=["a"],
        performance=[SimpleNamespace(id="p", failed_traces=["a"], n_traces=1,
                                     block_passed=False, reason="", warning="")],
    )
    verdict = gate.check_gate(results)
    assert verdict.reasons == [
        "G4 feature-on smoke did not complete cleanly: a",
        "G5 [p] 1 of 1 trace(s) did not complete: a. The entry was scored on the "
        "rest, which is a number about a different trace set than the one the plan "
        "declared.",
    ]


# ------------------------------------------------------------------- G2


def g2_entry():
    return plan()["correctness"][0]


def g2(outcome, metrics):
    return plan_runner.evaluate_condition(
        g2_entry(), outcome, metrics, plan(), BASELINE)


def test_g2_with_its_metrics_missing_names_the_exit_code_and_the_output():
    output = "P2P_WORKLOAD a\n" + "y" * 3000 + "\nP2P_STATUS failed gem5 exited 139"
    why = g2(ShellOutcome(exit_code=1, output=output), {})
    assert why.splitlines()[0].startswith("metric mpki missing (baseline=10.0, measured=None)")
    assert "the command exited 1" in why
    assert why.endswith("P2P_STATUS failed gem5 exited 139")
    assert output[-2000:] in why
    assert "P2P_WORKLOAD a" not in why


def test_g2_with_one_metric_missing_also_names_the_output():
    why = g2(ShellOutcome(exit_code=0, output="mpki 10.0\n"), {"mpki": 10.0})
    assert "metric ipc missing" in why
    assert "the command exited 0" in why


def test_g2_that_differs_but_printed_everything_adds_no_output():
    """The command ran and measured something else. The numbers are the
    diagnosis, and the output would only bury them."""
    why = g2(ShellOutcome(exit_code=0, output="lots of output"), {"mpki": 11.0, "ipc": 1.0})
    assert "mpki=11.0 differs from baseline 10.0" in why
    assert "the command exited" not in why
    assert "lots of output" not in why


def test_g2_that_matches_still_passes():
    assert g2(ShellOutcome(exit_code=0, output="x"), {"mpki": 10.0, "ipc": 1.0}) == ""


def test_g2_missing_metrics_through_the_whole_gate():
    executor = TraceExecutor(on=clean(mpki=5.0), off=clean(),
                             shell_output="panic: fake gem5 crash\n", shell_exit=134)
    results, verdict = judge(executor)
    [entry] = results.correctness
    assert not entry.passed
    [g2_reason] = [r for r in verdict.reasons if r.startswith("G2")]
    assert g2_reason.splitlines()[0] == (
        "G2 [off_equals_baseline] metric mpki missing (baseline=10.0, measured=None); "
        "metric ipc missing (baseline=1.0, measured=None)"
    )
    assert "the command exited 134" in g2_reason
    assert "panic: fake gem5 crash" in g2_reason
