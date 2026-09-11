"""The deterministic verify gate. This is the only level-specific element
of the loop, and it is plain code: no LLM opinion enters the promotion
decision (circt_issue_solver convention: verification is deterministic,
the agent never self-reports success).

Gate for a performance-model host:
  G1  the host builds with the feature code present;
  G2  with the feature knob OFF, metrics equal the recorded baseline
      (exact equality expected for deterministic trace-driven sims;
      tolerance knob provided for gem5, which can drift across configs);
  G3  spec-derived unit tests pass;
  G4  with the feature knob ON, smoke traces complete without error;
  G5  accounted storage fits the budget track.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GateResult:
    passed: bool
    reasons: list = field(default_factory=list)

    @property
    def feedback(self) -> str:
        return "\n".join(f"- {r}" for r in self.reasons) or "all gate conditions hold"


def check_gate(
    build_ok: bool,
    build_log_tail: str,
    baseline_metrics: dict,
    feature_off_metrics: dict,
    unit_test_failures: list,
    feature_on_ok: bool,
    storage_bits: int,
    budget_bits: int,
    metric_keys: tuple = ("brmispki_50perc_amean", "ipc_50perc_amean"),
    rel_tol: float = 0.0,
) -> GateResult:
    reasons = []
    if not build_ok:
        reasons.append(f"G1 build failed:\n{build_log_tail[-4000:]}")
        return GateResult(False, reasons)
    for key in metric_keys:
        base, off = baseline_metrics.get(key), feature_off_metrics.get(key)
        if base is None or off is None:
            reasons.append(f"G2 metric {key} missing (baseline={base}, feature-off={off})")
        elif base == 0:
            if off != 0:
                reasons.append(f"G2 {key}: baseline 0, feature-off {off}")
        elif abs(off - base) / abs(base) > rel_tol:
            reasons.append(
                f"G2 feature-off {key}={off} differs from baseline {base} "
                f"(tolerance {rel_tol}). The knob-off path is not baseline-identical."
            )
    for fail in unit_test_failures:
        reasons.append(f"G3 unit test failed: {fail}")
    if not feature_on_ok:
        reasons.append("G4 feature-on smoke run did not complete cleanly")
    if storage_bits > budget_bits:
        reasons.append(
            f"G5 storage {storage_bits} bits exceeds budget {budget_bits} bits"
        )
    return GateResult(passed=not reasons, reasons=reasons)
