"""A fixture host for stage 3, and the executor the gate drives it through.

The production hosts are a ChampSim checkout and a gem5 checkout: minutes to
build, a trace download to run, and a cluster to run on. None of that is what
stage 3 is made of. Stage 3 is a loop -- prompt the agent, let it edit a
checkout through the bash tool, build, test, judge with plain code, hand the
failure back -- and that loop can be exercised in seconds against a host small
enough to read in one sitting.

`loop/tests/fixtures/toyhost` is that host: a trace-driven branch-predictor
simulator of a few hundred lines with a bimodal predictor, a Makefile, and its
own test suite. `ToyHostExecutor` is the four methods plan_runner needs from
any host; `ToyHost` copies the fixture somewhere writable, records a baseline
off the pristine copy, and answers the gate's five questions through the same
`plan_runner.run_test_plan` and `gate.check_gate` the production hosts will.

What this file deliberately no longer decides: which workloads to run, which
metrics to compare, at what tolerance, and what counts as the feature working.
All of that is in `fixtures/tinysc.toy.tests.json`, because a gate condition
hardcoded here is one the plan cannot state and a reader cannot audit. What
stays is what no plan can express -- how to build this host, how to flip its
knob, and how to get numbers out of its stdout.

Storage is not one of the gate's questions. Only the DSE stage knows about
resource constraints (docs/stages.md), so nothing here carries a budget.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

import gate
import plan_runner

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "toyhost"
SPEC_PATH = Path(__file__).resolve().parent / "fixtures" / "tinysc.spec.json"
PORT_PLAN_PATH = Path(__file__).resolve().parent / "fixtures" / "tinysc.toy.plan.json"
TEST_PLAN_PATH = Path(__file__).resolve().parent / "fixtures" / "tinysc.toy.tests.json"

# Baseline recording only. These are not gate policy: a baseline is measured
# before any port exists, so there is no plan yet to name the workloads, and
# the test plan's `baseline_pointer` values are written against this layout.
SMOKE_WORKLOAD = "workloads/smoke.trace"
BIAS_WORKLOAD = "workloads/bias.trace"

# The line a debug turn must add to PORT_NOTES.md to clear an injected
# failure. See `ToyHost.force_first_fail`.
DEBUG_TURN_MARKER = "debug-turn-ok"

BUILD_TIMEOUT_S = 180
RUN_TIMEOUT_S = 120


@dataclass
class Shell:
    """One command's outcome, with the tail the gate is allowed to quote."""

    ok: bool
    output: str

    @property
    def tail(self) -> str:
        return self.output[-2000:]


class ToyHostExecutor:
    """plan_runner.HostExecutor over a materialized copy of the fixture."""

    def __init__(self, work_dir: Path, enable_knob: str, metric_keys: Sequence[str]):
        self.name = "toy"
        self.work_dir = Path(work_dir)
        self.enable_knob = enable_knob
        self.metric_keys = tuple(metric_keys)

    def build(self, *, feature_on: bool, timeout_s: int = BUILD_TIMEOUT_S):
        shell = self._sh("make", timeout=timeout_s)
        return plan_runner.BuildOutcome(ok=shell.ok, log=shell.output)

    def shell(
        self, command: str, *, feature_on: bool,
        env: Optional[Mapping[str, str]] = None, timeout_s: int = RUN_TIMEOUT_S,
    ):
        # The knob is applied here rather than by the runner, because only the
        # host knows how a value reaches it. On this host that is an
        # environment variable, which params.h reads on every call; on a host
        # whose knob is a compile-time define it would be a rebuild.
        merged = {self.enable_knob: "1" if feature_on else "0", **(env or {})}
        shell = self._sh(command, timeout=timeout_s, env=merged)
        if shell.output.endswith("[timed out]"):
            return plan_runner.ShellOutcome(exit_code=-1, output=shell.output, timed_out=True)
        code = 0 if shell.ok else 1
        marker = "[exit "
        if marker in shell.output:
            tail = shell.output.rsplit(marker, 1)[1]
            code = int(tail.split("]")[0])
        return plan_runner.ShellOutcome(exit_code=code, output=shell.output)

    def parse_metrics(self, output: str) -> dict:
        """The simulator prints exactly one line of JSON. Returning {} rather
        than raising on anything else is deliberate: a crashed run is a gate
        failure with a reason, not a crashed loop."""
        for line in reversed((output or "").splitlines()):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if all(key in parsed for key in self.metric_keys):
                return parsed
        return {}

    def run_traces(
        self, traces: Sequence[str], *, feature_on: bool, timeout_s: int = RUN_TIMEOUT_S
    ):
        """This host's native fan-out: one simulator invocation per workload,
        arithmetic mean per metric, which is how the real host adapters
        aggregate a suite."""
        rows, failed = [], []
        for trace in traces:
            outcome = self.shell(
                f"./build/toysim {trace}", feature_on=feature_on, timeout_s=timeout_s
            )
            row = self.parse_metrics(outcome.output) if outcome.exit_code == 0 else {}
            (rows.append(row) if row else failed.append(trace))
        if not rows:
            return plan_runner.TraceOutcome(ok=False, metrics={}, failed=failed)
        keys = set(rows[0]).intersection(*(set(r) for r in rows))
        means = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
        return plan_runner.TraceOutcome(ok=not failed, metrics=means, failed=failed)

    def _sh(self, command: str, timeout: int, env: Optional[dict] = None) -> Shell:
        try:
            proc = subprocess.run(
                command, shell=True, cwd=self.work_dir, capture_output=True,
                text=True, timeout=timeout, env={**os.environ, **(env or {})},
            )
        except subprocess.TimeoutExpired:
            # A hung command is a gate failure with a diagnosis. Letting the
            # exception escape would kill the loop instead.
            return Shell(ok=False, output=f"$ {command}\n[timed out after {timeout}s]\n[timed out]")
        return Shell(
            ok=proc.returncode == 0,
            output=f"$ {command}\n{proc.stdout}{proc.stderr}[exit {proc.returncode}]",
        )


class ToyHost:
    """A writable copy of the fixture, plus the gate over it."""

    def __init__(self, work_dir: Path, force_first_fail: bool = True,
                 port_plan: Optional[dict] = None, test_plan: Optional[dict] = None):
        self.work_dir = Path(work_dir)
        self.force_first_fail = force_first_fail
        self.attempts = 0
        self.history: list[dict] = []
        self.port_plan = port_plan or json.loads(PORT_PLAN_PATH.read_text())
        self.test_plan = test_plan or json.loads(TEST_PLAN_PATH.read_text())
        self.executor = ToyHostExecutor(
            self.work_dir,
            enable_knob=self.port_plan["feature_enable"]["name"],
            metric_keys=self.test_plan["metric_keys"],
        )

    # -------------------------------------------------------------- setup
    def materialize(self) -> Path:
        """Lay down a pristine copy of the fixture. The agent edits this one;
        the fixture in the repository is never touched, so a failed run leaves
        the next run's starting point intact."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        shutil.copytree(FIXTURE_DIR, self.work_dir)
        shutil.rmtree(self.work_dir / "build", ignore_errors=True)
        return self.work_dir

    def record_baseline(self) -> dict:
        """Build the unmodified host and run it. Called before the agent sees
        the checkout, so what it records is the host's own behavior and not
        the feature-off path of a port -- those being equal is exactly what G2
        is for, and a baseline read off the ported tree could not tell."""
        build = self.executor.build(feature_on=False)
        if not build.ok:
            raise SystemExit("toy host baseline build failed:\n" + build.log[-2000:])
        smoke = self._measure(SMOKE_WORKLOAD)
        bias = self._measure(BIAS_WORKLOAD)
        if smoke is None or bias is None:
            raise SystemExit("toy host baseline run produced no stats")
        return {**smoke, "bias": bias}

    def notes(self) -> str:
        return (self.work_dir / "NOTES.md").read_text()

    # --------------------------------------------------------------- gate
    def run_gate(self, baseline: dict, port_plan: Optional[dict] = None,
                 test_plan: Optional[dict] = None) -> gate.GateResult:
        """Run the test plan, then let gate.check_gate judge it. Every
        condition and every threshold comes from the plan; nothing about what
        counts as a working port is decided in this file.

        The pair is an argument so that a plan stage 3 revised mid-run
        (plan_revision.py) is the one judged. It defaults to the pair this
        host was constructed with, which is what the tests that call this
        directly want."""
        port_plan = self.port_plan if port_plan is None else port_plan
        test_plan = self.test_plan if test_plan is None else test_plan
        self.attempts += 1
        # Computed before the build, not after: a first attempt that fails to
        # compile still has to be told to append the marker, or attempt 2
        # demands one that attempt 1 never asked for.
        reasons = self._injection_reasons()

        results = plan_runner.run_test_plan(
            self.executor, test_plan, port_plan, baseline
        )
        verdict = gate.check_gate(results)
        reasons += verdict.reasons
        return self._record(
            gate.GateResult(passed=not reasons, reasons=reasons, warnings=verdict.warnings),
            build_ok=results.build_ok,
        )

    def _injection_reasons(self) -> list:
        """Fault injection, off by default in production and on by default in
        the smoke test.

        A run where the agent gets it right first try never executes the debug
        turn, so a broken debug turn would pass the smoke test silently. This
        rejects the first attempt unconditionally and then verifies that the
        debug turn actually wrote something to the checkout -- so what the
        injection proves is that the feedback reached the agent and the agent's
        reply reached the tree, not merely that a second gate call happened.

        It is harness policy, not a gate condition: no plan declares it and no
        real host has it."""
        if not self.force_first_fail:
            return []
        if self.attempts == 1:
            return [
                "G0 harness fault injection (--force-first-fail). This run "
                "rejects the first integration on purpose, to prove the debug "
                "turn works. Nothing in your implementation caused it and "
                "nothing about it needs diagnosing. To clear it, append the "
                f"exact line `{DEBUG_TURN_MARKER}` to PORT_NOTES.md in the host "
                "checkout, leaving the rest of your work alone. Every gate "
                "condition below this one is reported normally and is real."
            ]
        notes = self.work_dir / "PORT_NOTES.md"
        if not notes.exists() or DEBUG_TURN_MARKER not in notes.read_text():
            return [
                f"G0 PORT_NOTES.md does not contain the line "
                f"`{DEBUG_TURN_MARKER}` that attempt 1 asked for."
            ]
        return []

    def _record(self, result: gate.GateResult, build_ok: bool = True) -> gate.GateResult:
        self.history.append(
            {
                "attempt": self.attempts,
                "passed": result.passed,
                "build_ok": build_ok,
                "reasons": result.reasons,
                "warnings": result.warnings,
            }
        )
        return result

    def _measure(self, workload: str) -> Optional[dict]:
        outcome = self.executor.shell(
            f"./build/toysim {workload}", feature_on=False, timeout_s=RUN_TIMEOUT_S
        )
        if outcome.exit_code != 0:
            return None
        return self.executor.parse_metrics(outcome.output) or None
