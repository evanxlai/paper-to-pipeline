"""The deterministic verify gate. This is the only level-specific element
of the loop, and it is plain code: no LLM opinion enters the promotion
decision (circt_issue_solver convention: verification is deterministic,
the agent never self-reports success).

Gate for a performance-model host:
  G1  the host builds with the feature code present;
  G2  with the feature knob OFF, metrics equal the recorded baseline --
      the test plan's `feature_off_baseline` entries, which is where the
      plan says which workloads and which tolerance;
  G3  the test plan's other `correctness[]` entries pass;
  G4  with the feature knob ON, the plan's smoke traces complete cleanly;
  G5  the test plan's `performance[]` entries pass their `block_threshold`,
      and every trace they declare completes -- an entry scored on the
      traces that survived is a number about a different trace set than the
      plan asked for, and on a measure_feature_off entry the two sides can
      drop different traces, which is not a comparison at all.

There is no storage condition. Only the DSE stage knows about resource
constraints (docs/stages.md), so a gate that weighed a budget could not tell
"the feature is implemented wrong" from "the feature does not fit" -- which
is the distinction the whole stage split exists to preserve.

Everything the gate judges was measured by plan_runner and declared by the
plan. The gate itself runs nothing, reads no host and has no defaults: a
metric name, a tolerance, a threshold and a workload all come from the test
plan, because a condition the gate invented is a condition nobody wrote down
and nobody can audit.

`warn_threshold` shortfalls are warnings, never reasons. A shortfall is the
expected condition for an untuned port, and the agent must not be handed one
as something to fix -- .feedback is only ever rendered on a failing gate, so
anything in `reasons` is work the debug turn will try to do.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GateResult:
    passed: bool
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def feedback(self) -> str:
        return "\n".join(f"- {r}" for r in self.reasons) or "all gate conditions hold"


def metric_differences(
    baseline: dict, measured: dict, keys, rel_tol: float = 0.0
) -> list:
    """Where `measured` differs from `baseline` beyond `rel_tol`, one string
    per metric. The single comparator behind G2, so the feature-off equality
    check has one implementation and not one per caller.

    Iterate the declared keys, never the baseline's own: a recorded baseline
    document also holds raw counters and, on some hosts, a nested sub-document
    per workload, none of which the plan asked about."""
    out = []
    for key in keys:
        base, seen = baseline.get(key), measured.get(key)
        if base is None or seen is None:
            out.append(f"metric {key} missing (baseline={base}, measured={seen})")
        elif base == 0:
            if seen != 0:
                out.append(f"{key}: baseline 0, measured {seen}")
        elif abs(seen - base) / abs(base) > rel_tol:
            out.append(
                f"{key}={seen} differs from baseline {base} (tolerance {rel_tol}). "
                f"The knob-off path is not baseline-identical."
            )
    return out


def check_gate(results) -> GateResult:
    """Judge one integration attempt from what plan_runner measured.

    `results` is a plan_runner.TestPlanResults. Taken structurally rather than
    imported so the gate keeps its one job and no dependency on the module
    that shells out."""
    reasons: list = []
    warnings: list = []

    if not results.build_ok:
        # Nothing downstream is meaningful without a binary, and a wall of
        # consequential failures buries the one that caused them.
        return GateResult(False, [f"G1 build failed:\n{results.build_log_tail[-4000:]}"])

    baseline_entries = [r for r in results.correctness if r.kind == "feature_off_baseline"]
    if not baseline_entries:
        reasons.append(
            "G2 the test plan declares no feature_off_baseline entry, so the strongest "
            "regression available was never run."
        )
    for result in baseline_entries:
        if not result.passed:
            reasons.append(f"G2 [{result.id}] {result.reason}")

    for result in results.correctness:
        if result.kind != "feature_off_baseline" and not result.passed:
            reasons.append(f"G3 [{result.id}] {result.reason}")

    if not results.smoke_ok:
        failed = ", ".join(results.smoke_failures) or "no trace completed"
        reasons.append(f"G4 feature-on smoke did not complete cleanly: {failed}")

    for result in results.performance:
        if result.failed_traces:
            # Scoring the entry on the traces that survived is the quiet
            # version of passing: the mean is taken over whatever ran, and on
            # a measure_feature_off entry the two sides can drop different
            # traces, so the comparison is between two different trace sets.
            # G4 already refuses this for the smoke list; a performance trace
            # that does not complete is at least as serious.
            reasons.append(
                f"G5 [{result.id}] {len(result.failed_traces)} of {result.n_traces} "
                f"trace(s) did not complete: {', '.join(result.failed_traces)}. The "
                f"entry was scored on the rest, which is a number about a different "
                f"trace set than the one the plan declared."
            )
        elif not result.block_passed:
            reasons.append(f"G5 [{result.id}] {result.reason}")
        if result.warning:
            warnings.append(result.warning)

    return GateResult(passed=not reasons, reasons=reasons, warnings=warnings)
