"""Tests for stage 4's constraint machinery and the accounting behind it.

Two real documents anchor most of these: the sR spec the loop plans from
(spec/sr.paper_only.json), and a hand-written host_knobs/host_storage pair
for the CBP2025 kit whose terms follow predictorsize() term by term
(fixtures/cbp2025.host_knobs.json). The second is checked against the kit
itself where the checkout is present, because a checker that only ever sees
hand-built documents tends to pass hand-built documents.
"""

import asyncio
import json
from pathlib import Path

import pytest

import constraints as K
import dse
import plan_checks
import plan_revision
import spec_checks

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
KIT = REPO / "third_party" / "cbp2025"


@pytest.fixture
def spec():
    return json.loads((REPO / "spec" / "sr.paper_only.json").read_text())


@pytest.fixture
def host():
    doc = json.loads((FIXTURES / "cbp2025.host_knobs.json").read_text())
    return {"host_knobs": doc["host_knobs"], "host_storage": doc["host_storage"]}


def codes(findings):
    return sorted(f.code for f in findings)


# ----------------------------------------------------------------- formulas


def test_formula_arithmetic():
    assert K.evaluate("2**logg * (a + 4)", {"logg": 10, "a": 12}) == 16384
    assert K.evaluate("1 << (b - 2)", {"b": 13}) == 2048
    assert K.evaluate("65 * (1 + max(t, d) + log2(n))", {"t": 14, "d": 12, "n": 256}) == 1495


def test_caret_is_refused_rather_than_read_as_xor():
    """2^10 is 8 in Python. A power written that way must be a finding,
    not a formula quietly off by a factor of 128."""
    with pytest.raises(K.FormulaError):
        K.evaluate("2^logg", {"logg": 10})


@pytest.mark.parametrize("expr", ["__import__('os')", "a.b", "a[0]", "a if a else 1", "a > 1"])
def test_formula_is_plain_arithmetic_only(expr):
    with pytest.raises(K.FormulaError):
        K.evaluate(expr, {"a": 1})


def test_names_in_excludes_functions():
    assert K.names_in("max(a, b) * log2(c)") == {"a", "b", "c"}


# ------------------------------------------------------------- spec formulas


def test_the_real_spec_is_accounted_and_clean(spec):
    findings = spec_checks.run_checks(spec)
    assert [f for f in findings if f.severity != "info"] == []
    feature, host = K.default_values(K.all_knobs(spec, None))
    total, breakdown = K.storage_bits(spec, None, feature, host)
    assert total == spec["resource_accounting"]["total_storage_bits"] == 53863
    assert len(breakdown) == len(spec["state"])


def test_a_formula_that_disagrees_with_its_size_is_an_error(spec):
    spec["state"][2]["size_formula"] = "num_banks * wt0_entries * wt_ctr_bits"
    assert "formula_disagrees" in codes(spec_checks.run_checks(spec))


def test_a_formula_reading_an_undeclared_name_is_an_error(spec):
    spec["state"][1]["size_formula"] = "65 * 3 * ut_entries * counter_bits"
    assert "formula_unknown_name" in codes(spec_checks.run_checks(spec))


def test_a_storage_parameter_no_formula_reads_is_flagged(spec):
    """README's gap: nothing checked that the search could move the storage."""
    for s in spec["state"]:
        s.pop("size_formula", None)
    found = [f for f in spec_checks.run_checks(spec) if f.code == "storage_param_unaccounted"]
    assert {f.pointer for f in found} >= {"/parameters/0", "/parameters/4"}
    assert all(f.severity == "warn" for f in found)


# ------------------------------------------------------------- host storage


def test_the_host_terms_reproduce_predictorsize(host):
    values = {k["name"]: k["default"] for k in host["host_knobs"]}
    assert sum(K.host_storage(host, values).values()) == 524615


def test_host_checks_pass_on_a_correct_pair(host):
    findings = plan_checks._check_host_knobs(host) + plan_checks._check_host_storage(host, 524615)
    assert [f for f in findings if f.severity == "error"] == []


@pytest.mark.skipif(not (KIT / "cbp2016_tage_sc_l.h").exists(), reason="no CBP2025 checkout")
def test_every_observed_line_is_in_the_real_kit(host):
    assert plan_checks._check_host_knobs(host, KIT) == []


def test_a_default_the_observed_line_does_not_hold_is_an_error(host):
    host["host_knobs"][0]["default"] = 9
    assert "host_default_not_observed" in codes(plan_checks._check_host_knobs(host))


@pytest.mark.skipif(not (KIT / "cbp2016_tage_sc_l.h").exists(), reason="no CBP2025 checkout")
def test_an_invented_observed_line_is_an_error(host):
    # A line cut short of its comment is still a quote; this one is not.
    host["host_knobs"][0]["observed"] = "#define LOGG 10  // log2 entries per tagged bank"
    assert "host_observed_missing" in codes(plan_checks._check_host_knobs(host, KIT))


def test_a_misnamed_host_macro_is_an_error(host):
    host["host_knobs"][0]["macro"] = "SR_LOGG"
    assert "host_macro_mismatch" in codes(plan_checks._check_host_knobs(host))


def test_terms_that_miss_the_measurement_are_an_error(host):
    host["host_storage"]["terms"] = host["host_storage"]["terms"][:-1]
    assert "host_storage_disagrees" in codes(plan_checks._check_host_storage(host))


def test_a_baseline_the_host_did_not_measure_is_an_error(host):
    assert "host_storage_unmeasured" in codes(plan_checks._check_host_storage(host, 523367))


def test_host_knobs_without_host_storage_is_an_error(host):
    del host["host_storage"]
    assert "host_storage_missing" in codes(plan_checks._check_host_storage(host))


def test_a_host_knob_no_term_reads_is_flagged(host):
    host["host_knobs"].append({**host["host_knobs"][0], "name": "logl", "macro": "HOST_LOGL",
                               "host_symbol": "LOGL", "observed": "#define LOGL 5",
                               "default": 5, "range": "[3, 7]"})
    found = [f for f in plan_checks._check_host_storage(host) if f.code == "host_knob_unaccounted"]
    assert [f.severity for f in found] == ["warn"]


def test_no_host_knobs_is_a_warning_not_an_error():
    found = plan_checks._check_host_knobs({"host_knobs": []})
    assert [(f.code, f.severity) for f in found] == [("no_host_knobs", "warn")]


# ----------------------------------------------------------------- revision


def test_a_revision_may_correct_a_host_knobs_range_but_not_its_default(host):
    new = json.loads(json.dumps(host))
    new["host_knobs"][0]["range"] = "[8, 12]"
    assert plan_revision._check_collection(
        "/plan", host, new, "host_knobs", *plan_revision._PORT_COLLECTIONS["host_knobs"]) == []
    new["host_knobs"][0]["default"] = 9
    assert "revision_froze_field" in codes(plan_revision._check_collection(
        "/plan", host, new, "host_knobs", *plan_revision._PORT_COLLECTIONS["host_knobs"]))


def test_a_revision_may_not_restate_the_measured_host_storage(host):
    new = json.loads(json.dumps(host))
    new["host_storage"]["baseline_bits"] = 500000
    assert "revision_froze_field" in codes(plan_revision._check_host_storage(host, new))


# ------------------------------------------------------------------- header


def test_the_header_carries_both_kinds_of_knob_and_the_cost_model(spec, host):
    cs = [K.storage_constraint("iso-64KiB", 524288)]
    header = dse.params_header(spec, host, constraint_set=cs)
    defines = [l for l in header.splitlines() if l.startswith("#define")]
    assert len(defines) == len(spec["parameters"]) + len(host["host_knobs"])
    assert "#define HOST_LOGG 10  // range: [7, 12]; sets LOGG" in header
    assert "// constraint: storage_bits <= 524288 (iso-64KiB)" in header
    # The cost model is written in the header's own names.
    assert "SR_NUM_BANKS * (SR_WT0_ENTRIES + SR_WT1_ENTRIES + SR_WT2_ENTRIES) * SR_WT_CTR_BITS" in header
    assert "HOST_NBANKHIGH * 2 ** HOST_LOGG" in header


def test_the_default_header_is_a_legal_candidate(spec, host):
    """Stage 3 is told to create exactly this file, so it must parse back."""
    report = K.check_static(dse.params_header(spec, host), spec, host, [])
    assert report.errors == []
    assert report.feature["num_banks"] == 8 and report.host["logg"] == 10


def test_defaults_do_not_fit_64kib_and_the_breakdown_says_why(spec, host):
    cs = [K.storage_constraint("iso-64KiB", 524288)]
    report = K.check_static(dse.params_header(spec, host, constraint_set=cs), spec, host, cs)
    assert not report.ok
    assert report.metrics["storage_bits"] == 53863 + 524615
    assert "host:tagged tables, high banks" in report.breakdown
    assert "breaks storage_bits <= 524288" in report.message()


def test_shrinking_the_host_makes_room(spec, host):
    cs = [K.storage_constraint("iso-64KiB", 524288)]
    header = dse.params_header(spec, host, host_overrides={"nbankhigh": 16}, constraint_set=cs)
    report = K.check_static(header, spec, host, cs)
    assert report.ok, report.message()
    assert report.metrics["storage_bits"] == 53863 + 524615 - 4 * 1024 * 16


@pytest.mark.parametrize("edit,problem", [
    (("#define SR_NUM_BANKS 8", "#define SR_NUM_BANKS 40"), "outside"),
    (("#define SR_WT0_ENTRIES 512", "#define SR_WT0_ENTRIES 500"), "power of two"),
    (("#define HOST_LOGG 10", "#define HOST_LOGG (1+9)"), "plain literal"),
    (("#define HOST_LOGG 10", "#define HOST_LOGGG 10"), "missing"),
])
def test_an_illegal_candidate_is_refused_with_a_reason(spec, host, edit, problem):
    header = dse.params_header(spec, host).replace(*edit)
    report = K.check_static(header, spec, host, [])
    assert not report.ok and any(problem in e for e in report.errors)


def test_the_worked_toy_pair_renders_a_legal_header():
    """The toy spec spells its bool enable knob as 0; C accepts that, so must we."""
    spec = json.loads((FIXTURES / "tinysc.spec.json").read_text())
    plan = json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())
    report = K.check_static(dse.params_header(spec, plan), spec, plan, [])
    assert report.errors == []
    assert report.host == {"bimodal_entries": 1024}


def test_a_measured_constraint_needs_no_new_code():
    cs = [K.Constraint("ipc_50perc_amean", ">=", 2.9, "ipc floor")]
    assert cs[0].phase == "measured"
    assert K.check_measured({"ipc_50perc_amean": 3.1}, cs) == []
    assert K.check_measured({"ipc_50perc_amean": 2.5}, cs) != []


# ---------------------------------------------------------------- preflight


def _fake_build(inert: set):
    """A build that ignores the macros in `inert`, the way a port that never
    wired them would: their value does not reach the binary."""
    def build(header):
        values, _ = K.parse_header(header)
        return json.dumps({m: v for m, v in values.items() if m not in inert},
                          sort_keys=True).encode()
    return build


def test_preflight_passes_when_every_knob_reaches_the_build(spec, host):
    report = dse.preflight(_fake_build(set()), spec, host, dse.params_header(spec, host))
    assert report["reproducible"] and report["blocking"] == []
    assert {k["result"] for k in report["knobs"]} == {"live"}


def test_an_inert_storage_knob_stops_the_search(spec, host):
    report = dse.preflight(_fake_build({"HOST_NBANKHIGH"}), spec, host,
                           dse.params_header(spec, host))
    assert len(report["blocking"]) == 1 and "HOST_NBANKHIGH" in report["blocking"][0]


def test_an_inert_knob_that_costs_nothing_is_only_a_warning(spec, host):
    report = dse.preflight(_fake_build({"SR_USEFULNESS_THRESHOLD"}), spec, host,
                           dse.params_header(spec, host))
    assert report["blocking"] == []
    assert any("SR_USEFULNESS_THRESHOLD" in w for w in report["warnings"])


def test_unreproducible_builds_stop_the_preflight(spec, host):
    counter = iter(range(1000))
    report = dse.preflight(lambda h: str(next(counter)).encode(), spec, host,
                           dse.params_header(spec, host))
    assert not report["reproducible"] and report["blocking"]


@pytest.mark.parametrize("knob,expected", [
    (K.Knob("M", "n", "int", 512, "[128, 2048] pow2", "feature"), 256),
    (K.Knob("M", "n", "int", 128, "[128, 2048] pow2", "feature"), 256),
    (K.Knob("M", "n", "int", 6, "[3, 8]", "feature"), 5),
    (K.Knob("M", "n", "int", 3, "[3, 8]", "feature"), 4),
    (K.Knob("M", "n", "bool", True, "true|false", "feature"), False),
])
def test_alternate_value_prefers_the_smaller_legal_value(knob, expected):
    assert K.alternate_value(knob) == expected


# ---------------------------------------------------------------- evaluator


def test_evaluator_refuses_an_over_budget_candidate_without_building(spec, host, tmp_path):
    pytest.importorskip("skydiscover", reason="skydiscover/evolve-flows not installed")
    import sr_evaluator
    from skydiscover.evaluation.chia_evaluator import ChiaEvaluator

    cs = [K.storage_constraint("iso-64KiB", 524288)]
    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent", ["int/x.gz"], str(tmp_path), 60, 60,
        spec=spec, port_plan=host, constraints=[c.as_dict() for c in cs])

    async def never(*a, **k):
        raise AssertionError("an over-budget candidate reached the build")

    try:
        ChiaEvaluator._dispatch_build, saved = never, ChiaEvaluator._dispatch_build
        over = asyncio.run(ev._dispatch_build(dse.params_header(spec, host), ""))
        closer = asyncio.run(ev._dispatch_build(
            dse.params_header(spec, host, host_overrides={"nbankhigh": 18}), ""))
    finally:
        ChiaEvaluator._dispatch_build = saved
        ev.close()
    assert over.artifacts["failure_stage"] == "constraints"
    assert over.metrics["storage_bits"] == 578478
    # Below every feasible score, and higher the closer it gets.
    assert 0 < over.metrics["combined_score"] < closer.metrics["combined_score"] < 1
