"""A fixture host for stage 3, and the gate that judges a port into it.

The production hosts are a ChampSim checkout and a gem5 checkout: minutes to
build, a trace download to run, and a cluster to run on. None of that is what
stage 3 itself is made of. Stage 3 is a loop -- prompt the agent, let it edit a
checkout through the bash tool, build, test, judge with plain code, hand the
failure back -- and that loop can be exercised in seconds against a host small
enough to read in one sitting.

`loop/tests/fixtures/toyhost` is that host: a trace-driven branch-predictor
simulator of a few hundred lines with a bimodal predictor, a Makefile, and its
own test suite. `ToyHost` copies it somewhere writable, records a baseline off
the pristine copy, and answers the same five gate questions the real hosts
will, against the same `gate.check_gate`.

Storage is not one of those questions. Only the DSE stage knows about resource
constraints (docs/stages.md), so the storage arguments are passed as 0 against
an allowance of 0 -- satisfied, and carrying no budget.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import gate

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "toyhost"
SPEC_PATH = Path(__file__).resolve().parent / "fixtures" / "tinysc.spec.json"

ENABLE_KNOB = "TINYSC_ENABLE"
SMOKE_WORKLOAD = "workloads/smoke.trace"
BIAS_WORKLOAD = "workloads/bias.trace"

# The metrics the gate compares. `gate.check_gate` defaults to the CBP2025
# metric names; the toy simulator prints these two.
METRIC_KEYS = ("mpki", "ipc")

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


class ToyHost:
    """A writable copy of the fixture, plus the gate over it."""

    def __init__(self, work_dir: Path, force_first_fail: bool = True):
        self.work_dir = Path(work_dir)
        self.force_first_fail = force_first_fail
        self.attempts = 0
        self.history: list[dict] = []

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
        build = self._sh("make")
        if not build.ok:
            raise SystemExit("toy host baseline build failed:\n" + build.tail)
        smoke = self._measure(SMOKE_WORKLOAD, enable=False)
        bias = self._measure(BIAS_WORKLOAD, enable=False)
        if smoke is None or bias is None:
            raise SystemExit("toy host baseline run produced no stats")
        return {**smoke, "bias": bias}

    def notes(self) -> str:
        return (self.work_dir / "NOTES.md").read_text()

    # --------------------------------------------------------------- gate
    def run_gate(self, baseline: dict) -> gate.GateResult:
        """G1 build, G2 feature-off equals baseline, G3 the test suite, G4 the
        feature-on smoke, G5 the direction of the metric the feature claims to
        move.

        G5 is the one condition that asks whether the port *works* rather than
        whether it is harmless, and it is directional only: the feature must
        move MPKI down on a history-correlated workload. How far down is a
        tuning question, and tuning is stage 4's job.

        Note this is a *fixture* condition, hardcoded because there is no plan
        stage yet to hand the gate anything better. The production G5 is not a
        fixed must-beat-baseline comparison: it is whatever the test plan's
        `performance[]` entries declare for that feature, with `block_threshold`
        blocking and `warn_threshold` only reported (docs/stages.md)."""
        self.attempts += 1

        build = self._sh("make")
        if not build.ok:
            result = gate.GateResult(False, [f"G1 build failed:\n{build.tail}"])
            return self._record(result, build_ok=False)

        feature_off = self._measure(SMOKE_WORKLOAD, enable=False) or {}
        tests = self._sh("make test")
        feature_on = self._measure(SMOKE_WORKLOAD, enable=True)

        result = gate.check_gate(
            build_ok=True,
            build_log_tail=build.tail,
            baseline_metrics=baseline,
            feature_off_metrics=feature_off,
            unit_test_failures=[] if tests.ok else [f"`make test`:\n{tests.tail}"],
            feature_on_ok=feature_on is not None,
            # Stage 3 has no storage condition; see the module docstring.
            storage_bits=0,
            budget_bits=0,
            metric_keys=METRIC_KEYS,
            rel_tol=0.0,
        )

        # Injection first, so a run that is only failing because of it says
        # so on the first line rather than after a real-looking G5.
        reasons = self._injection_reasons()
        reasons += result.reasons
        reasons += self._direction_reasons(baseline)
        return self._record(gate.GateResult(passed=not reasons, reasons=reasons))

    def _direction_reasons(self, baseline: dict) -> list:
        """G5. The spec claims TinySC recovers branches whose outcome depends
        on global history, and `workloads/bias.trace` is built out of them, so
        a correct port must show up here. A port that does not is misbuilt:
        no parameter value rescues a mechanism that is wired wrong."""
        on = self._measure(BIAS_WORKLOAD, enable=True)
        if on is None:
            return ["G5 feature-on run over the bias workload did not produce stats"]
        before = baseline["bias"]["mpki"]
        after = on["mpki"]
        if after >= before:
            return [
                f"G5 with {ENABLE_KNOB}=1 the MPKI on {BIAS_WORKLOAD} is {after}, "
                f"which is not below the baseline {before}. The feature is "
                f"either not reaching the prediction path or is not consulting "
                f"global history."
            ]
        return []

    def _injection_reasons(self) -> list:
        """Fault injection, off by default in production and on by default in
        the smoke test.

        A run where the agent gets it right first try never executes the debug
        turn, so a broken debug turn would pass the smoke test silently. This
        rejects the first attempt unconditionally and then verifies that the
        debug turn actually wrote something to the checkout -- so what the
        injection proves is that the feedback reached the agent and the agent's
        reply reached the tree, not merely that a second gate call happened."""
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
            }
        )
        return result

    # ---------------------------------------------------------- internals
    def _sh(self, command: str, timeout: int = BUILD_TIMEOUT_S, env: Optional[dict] = None) -> Shell:
        import os

        proc = subprocess.run(
            command,
            shell=True,
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **(env or {})},
        )
        return Shell(
            ok=proc.returncode == 0,
            output=f"$ {command}\n{proc.stdout}{proc.stderr}[exit {proc.returncode}]",
        )

    def _measure(self, workload: str, enable: bool) -> Optional[dict]:
        """Run the simulator and parse its stats line, or None if the run did
        not produce one. Returning None rather than raising is deliberate: a
        crashed run is a gate failure with a reason, not a crashed loop."""
        shell = self._sh(
            f"./build/toysim {workload}",
            timeout=RUN_TIMEOUT_S,
            env={ENABLE_KNOB: "1" if enable else "0"},
        )
        if not shell.ok:
            return None
        for line in reversed(shell.output.splitlines()):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if all(key in parsed for key in METRIC_KEYS):
                return parsed
        return None
