"""Execute a test plan against a host, and evaluate what it declared.

This is the half of the verify gate that has to touch a machine. gate.py
decides promotion and is the only thing that returns `passed`; this module
runs the commands the plan names, fans out its traces, and turns each
declared condition into a verdict the gate can assemble. Splitting them that
way keeps the promotion decision readable in one screen of plain code, and
keeps the part that shells out testable against a fixture host.

Hosts differ more than the test plan admits. The CBP2025 kit builds a binary
and fans traces out over Ray with no shell and no environment; the fixture
host is a Makefile and a subprocess. Everything they disagree about lives
behind `HostExecutor` below, and the single decision that makes one runner
drive both is that `feature_on` is a parameter of build/shell/run_traces
rather than an environment variable the runner sets itself. A runner that
wrote the knob name into an env dict could never drive a host whose knob is a
compile-time define, because no environment reaches a #define.

Decisions the schema leaves open, settled here and nowhere else:

  * A pattern is compiled with Python's `re`, though the schema calls the
    dialect ECMA-262. plan_checks rejects what `re` cannot parse, so the
    disagreement surfaces as a plan finding rather than a crashed gate.
  * `matches_clean_tree` with a pattern compares the first capturing group,
    or the whole match when the pattern has no group, against the recorded
    `summary` -- the only text the clean-tree record holds.
  * A performance entry naming several traces is scored on improvement of
    the means, not the mean of the improvements. The two differ on a
    heterogeneous trace list, and this one matches how the host adapters
    already aggregate a suite.
  * A timeout is a failed entry with a reason, never an exception. A hung
    test is a gate failure with a diagnosis; a crashed loop is neither.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, Sequence

import gate

DEFAULT_TIMEOUT_S = 900


# ---------------------------------------------------------------- outcomes


@dataclass
class BuildOutcome:
    ok: bool
    log: str
    handle: object = None  # cbp2025: the built binary; fixture host: None


@dataclass
class ShellOutcome:
    exit_code: int
    output: str  # stdout and stderr combined: every pattern matches the pair
    timed_out: bool = False


@dataclass
class TraceOutcome:
    ok: bool
    metrics: dict  # aggregated, keyed by the plan's metric_keys and nothing else
    failed: list = field(default_factory=list)
    log_tail: str = ""


class HostExecutor(Protocol):
    """Everything the runner is allowed to know about a host."""

    name: str

    def build(self, *, feature_on: bool, timeout_s: int) -> BuildOutcome: ...

    def shell(
        self, command: str, *, feature_on: bool,
        env: Optional[Mapping[str, str]] = None, timeout_s: int,
    ) -> ShellOutcome: ...

    def parse_metrics(self, output: str) -> dict: ...

    def run_traces(
        self, traces: Sequence[str], *, feature_on: bool, timeout_s: int
    ) -> TraceOutcome: ...


# ----------------------------------------------------------------- results


@dataclass
class CorrectnessResult:
    id: str
    kind: str
    passed: bool
    reason: str = ""
    metrics: dict = field(default_factory=dict)


@dataclass
class PerformanceResult:
    id: str
    metric: str
    direction: str
    baseline: Optional[float] = None
    measured: Optional[float] = None
    relative_improvement: Optional[float] = None
    block_passed: bool = False
    warn_passed: bool = False
    reason: str = ""
    warning: str = ""
    n_traces: int = 0
    failed_traces: list = field(default_factory=list)


@dataclass
class TestPlanResults:
    """Everything the gate needs, and nothing it has to go and fetch."""

    build_ok: bool
    build_log_tail: str = ""
    feature_off_metrics: dict = field(default_factory=dict)
    correctness: list = field(default_factory=list)
    performance: list = field(default_factory=list)
    smoke_ok: bool = False
    smoke_failures: list = field(default_factory=list)


# -------------------------------------------------------------- conditions


def _states(feature_state: str) -> tuple:
    return {"off": (False,), "on": (True,), "both": (False, True)}[feature_state]


def _resolve(document, pointer: str):
    """RFC 6901, tolerant: an unresolvable pointer yields None so the caller
    reports a missing baseline rather than raising inside the gate."""
    node = document
    for raw in (pointer or "").lstrip("/").split("/"):
        if raw == "":
            continue
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        elif isinstance(node, dict) and token in node:
            node = node[token]
        else:
            return None
    return node


_COMPARISONS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
}


def evaluate_condition(
    entry: dict, outcome: ShellOutcome, metrics: dict, test_plan: dict, baseline: dict
) -> str:
    """Empty string when the condition holds, else why it did not."""
    pc = entry.get("pass_condition") or {}
    kind = pc.get("kind")

    if outcome.timed_out:
        return f"the command timed out: {entry.get('command')!r}"

    if kind == "exit_zero":
        return "" if outcome.exit_code == 0 else (
            f"exited {outcome.exit_code}\n{outcome.output[-2000:]}"
        )

    if kind in ("stdout_matches", "stdout_excludes"):
        if not pc.get("allow_nonzero_exit", False) and outcome.exit_code != 0:
            return (
                f"exited {outcome.exit_code}, so its output is not evidence about "
                f"the pattern\n{outcome.output[-2000:]}"
            )
        hit = re.search(pc["pattern"], outcome.output)
        if kind == "stdout_matches" and hit is None:
            return f"output does not match {pc['pattern']!r}\n{outcome.output[-2000:]}"
        if kind == "stdout_excludes" and hit is not None:
            return f"output contains {hit.group()!r}, which this entry forbids"
        return ""

    if kind == "matches_clean_tree":
        clean = entry.get("clean_tree_result") or {}
        if outcome.exit_code != clean.get("exit_code"):
            return (
                f"exited {outcome.exit_code} where the clean tree at plan time exited "
                f"{clean.get('exit_code')}\n{outcome.output[-2000:]}"
            )
        pattern = pc.get("pattern")
        if pattern:
            hit = re.search(pattern, outcome.output)
            if hit is None:
                return f"output does not match {pattern!r}, so there is nothing to compare"
            seen = hit.group(1) if hit.groups() else hit.group(0)
            if seen != clean.get("summary"):
                return (
                    f"summary is {seen!r} where the clean tree produced "
                    f"{clean.get('summary')!r}"
                )
        return ""

    if kind == "metrics_equal_baseline":
        base = _resolve(baseline, pc.get("baseline_pointer", ""))
        if not isinstance(base, dict):
            return f"no recorded baseline at {pc.get('baseline_pointer', '')!r}"
        keys = pc.get("metrics") or test_plan.get("metric_keys") or []
        tol = pc["rel_tol"] if "rel_tol" in pc else test_plan.get("baseline_rel_tol", 0.0)
        return "; ".join(gate.metric_differences(base, metrics, keys, tol))

    if kind == "metric_threshold":
        name = pc.get("metric")
        if name not in metrics:
            return f"the run produced no metric {name!r}"
        if not _COMPARISONS[pc["comparison"]](metrics[name], pc["value"]):
            return f"{name}={metrics[name]} fails {name} {pc['comparison']} {pc['value']}"
        return ""

    return f"unknown pass condition {kind!r}"


# ------------------------------------------------------------- measurement


def _measure(
    executor: HostExecutor, traces: Sequence[str], run: dict, *,
    feature_on: bool, timeout_s: int,
) -> TraceOutcome:
    """One aggregated metrics dict over a trace list, by whichever route the
    plan declared. Absent `run` means host_adapter, which is the mode a real
    cluster host uses; the fixture host declares command_per_trace."""
    mode = (run or {}).get("mode", "host_adapter")
    if mode == "host_adapter":
        return executor.run_traces(list(traces), feature_on=feature_on, timeout_s=timeout_s)

    template = (run or {}).get("command_template") or ""
    rows, failed, tail = [], [], ""
    for trace in traces:
        outcome = executor.shell(
            template.replace("{trace}", trace), feature_on=feature_on, timeout_s=timeout_s
        )
        tail = outcome.output[-2000:]
        if outcome.timed_out or outcome.exit_code != 0:
            failed.append(trace)
            continue
        row = executor.parse_metrics(outcome.output)
        if row:
            rows.append(row)
        else:
            failed.append(trace)
    if not rows:
        return TraceOutcome(ok=False, metrics={}, failed=list(failed), log_tail=tail)
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    means = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
    return TraceOutcome(ok=not failed, metrics=means, failed=failed, log_tail=tail)


def _relative_improvement(baseline: float, measured: float, direction: str) -> float:
    delta = (baseline - measured) if direction == "decrease" else (measured - baseline)
    return delta / abs(baseline)


def _traces_of(entry: dict) -> list:
    if entry.get("traces"):
        return list(entry["traces"])
    import constants as C
    import helpers

    return helpers.load_trace_list(C.REPO_ROOT / entry["trace_list"])


# ------------------------------------------------------------------ driver


def run_test_plan(
    executor: HostExecutor, test_plan: dict, port_plan: dict, baseline: dict
) -> TestPlanResults:
    """Build, then run everything the plan declared, once each."""
    default_timeout = DEFAULT_TIMEOUT_S
    build = executor.build(feature_on=False, timeout_s=default_timeout)
    if not build.ok:
        return TestPlanResults(build_ok=False, build_log_tail=build.log[-4000:])

    results = TestPlanResults(build_ok=True, build_log_tail=build.log[-4000:])

    # One shell run per distinct (command, state, env): the fixture plan alone
    # has four entries sharing `make test`, and on a real host an equivalent
    # duplicate is a multi-minute rebuild each time.
    cache: dict = {}

    def run_once(command, feature_on, env, timeout_s):
        key = (command, feature_on, tuple(sorted((env or {}).items())))
        if key not in cache:
            outcome = executor.shell(
                command, feature_on=feature_on, env=env, timeout_s=timeout_s
            )
            cache[key] = (outcome, executor.parse_metrics(outcome.output))
        return cache[key]

    for entry in test_plan.get("correctness") or []:
        timeout_s = entry.get("timeout_seconds", default_timeout)
        reasons, metrics = [], {}
        for feature_on in _states(entry["feature_state"]):
            outcome, metrics = run_once(
                entry["command"], feature_on, entry.get("env"), timeout_s
            )
            why = evaluate_condition(entry, outcome, metrics, test_plan, baseline)
            if why:
                label = "feature-on" if feature_on else "feature-off"
                reasons.append(f"{label}: {why}" if entry["feature_state"] == "both" else why)
            if entry.get("kind") == "feature_off_baseline" and not feature_on:
                results.feature_off_metrics.update(metrics)
        results.correctness.append(CorrectnessResult(
            id=entry["id"], kind=entry["kind"], passed=not reasons,
            reason="; ".join(reasons), metrics=metrics,
        ))

    smoke = test_plan.get("smoke") or {}
    if smoke:
        outcome = _measure(
            executor, _traces_of(smoke), smoke.get("run"),
            feature_on=True, timeout_s=smoke.get("timeout_seconds", default_timeout),
        )
        results.smoke_ok = outcome.ok
        results.smoke_failures = list(outcome.failed)

    for entry in test_plan.get("performance") or []:
        results.performance.append(
            _run_performance(executor, entry, default_timeout, baseline)
        )
    return results


def _run_performance(
    executor: HostExecutor, entry: dict, default_timeout: int, baseline_doc: dict
) -> PerformanceResult:
    traces = _traces_of(entry)
    metric, direction = entry["metric"], entry["direction"]
    timeout_s = entry.get("timeout_seconds", default_timeout)
    out = PerformanceResult(id=entry["id"], metric=metric, direction=direction,
                            n_traces=len(traces))

    on = _measure(executor, traces, entry.get("run"), feature_on=True, timeout_s=timeout_s)
    out.failed_traces = list(on.failed)
    if metric not in on.metrics:
        out.reason = (
            f"the feature-on run produced no {metric!r} over {len(traces)} trace(s)"
            + (f"; failed: {', '.join(on.failed)}" if on.failed else "")
        )
        return out
    out.measured = on.metrics[metric]

    source = (entry.get("baseline") or {}).get("source", "measure_feature_off")
    if source == "recorded":
        base_doc = _resolve(baseline_doc, (entry.get("baseline") or {}).get("pointer", ""))
        base_metrics = base_doc if isinstance(base_doc, dict) else {}
    else:
        off = _measure(executor, traces, entry.get("run"),
                       feature_on=False, timeout_s=timeout_s)
        base_metrics = off.metrics
    if metric not in base_metrics:
        out.reason = f"no baseline value for {metric!r} (source {source!r})"
        return out
    out.baseline = base_metrics[metric]

    if out.baseline == 0:
        out.reason = f"the baseline {metric} is 0, so a relative improvement is undefined"
        return out
    out.relative_improvement = _relative_improvement(out.baseline, out.measured, direction)

    block = entry["block_threshold"]
    floor = block["min_relative_improvement"]
    reasons = []
    # Strictly greater, per the schema: with a floor of 0.0 an exactly
    # unchanged metric is not evidence that the mechanism fired.
    if not out.relative_improvement > floor:
        reasons.append(
            f"{metric} moved {out.relative_improvement:+.4f} relative "
            f"({out.baseline} -> {out.measured}, {direction} is better), which does not "
            f"beat the {floor} floor. The mechanism is not reaching the metric."
        )
    for companion in block.get("no_regression") or []:
        cname = companion["metric"]
        if cname not in on.metrics or cname not in base_metrics:
            reasons.append(f"companion metric {cname!r} was not measured")
            continue
        ri = _relative_improvement(
            base_metrics[cname], on.metrics[cname], companion["direction"]
        )
        # Non-strict: max_relative_regression 0.0 means "must not get worse",
        # not "must get strictly better" -- it is a noise band, not a target.
        if -ri > companion["max_relative_regression"]:
            reasons.append(
                f"{cname} regressed {-ri:+.4f} relative "
                f"({base_metrics[cname]} -> {on.metrics[cname]}), beyond the "
                f"{companion['max_relative_regression']} band. The feature is buying "
                f"{metric} with {cname}."
            )
    out.block_passed = not reasons
    out.reason = "; ".join(reasons)

    warn = entry["warn_threshold"]
    target = warn["target_relative_improvement"]
    out.warn_passed = out.relative_improvement >= target
    if not out.warn_passed:
        out.warning = (
            f"{entry['id']}: {metric} improved {out.relative_improvement:.4f} against a "
            f"claimed {target} ({warn['claim_source'][:160]}). Recorded, not blocking: "
            f"the port is untuned and closing that gap is stage 4's job."
        )
    return out
