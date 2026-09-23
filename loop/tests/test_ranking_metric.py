"""G5 judges the metric stage 4 ranks by.

Stage 4 screens and promotes cbp2025 candidates on MPKI. A G5 on CycWPPKI
promotes a port on one question and tunes it on another, so on a host with a
ranking metric the plan check refuses any other performance metric.
"""

import constants as C
import plan_checks


def plan_with(metric, direction="decrease", host="cbp2025"):
    return {"host": host, "performance": [{"id": "perf", "metric": metric,
                                           "direction": direction}]}


def codes(tests):
    return [f.code for f in plan_checks._check_ranking_metric(tests)]


def test_cbp2025_ranks_by_the_stage_4_screening_metric():
    assert plan_checks.RANKING_METRIC["cbp2025"] == C.DSE_SCREEN_METRIC == "brmispki_50perc_amean"


def test_another_metric_is_refused():
    findings = plan_checks._check_ranking_metric(plan_with("cycwppki_50perc_amean"))
    assert [f.code for f in findings] == ["not_ranking_metric"]
    assert findings[0].severity == "error"
    assert findings[0].pointer == "/tests/performance/0/metric"


def test_the_ranking_metric_passes():
    assert codes(plan_with("brmispki_50perc_amean")) == []


def test_the_direction_has_to_be_decrease():
    assert codes(plan_with("brmispki_50perc_amean", "increase")) == ["ranking_metric_direction"]


def test_a_host_with_no_ranking_metric_chooses_freely():
    assert codes(plan_with("ipc", "increase", host="gem5")) == []


def test_run_checks_includes_it():
    spec = {"feature_name": "x", "parameters": [], "state": [], "algorithms": [],
            "host_interfaces": [], "unit_tests": []}
    found = [f.code for f in plan_checks.run_checks(spec, {}, plan_with("cycwppki_50perc_amean"))]
    assert "not_ranking_metric" in found


def test_the_test_plan_in_force_uses_it():
    import plan_revision

    _port, tests, revision = plan_revision.latest("cbp2025", "sr")
    assert codes(tests) == []
    assert all(e["metric"] == C.DSE_SCREEN_METRIC for e in tests["performance"])
