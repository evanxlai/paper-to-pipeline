"""Promotion: which of stage 4's candidates are scored again, and how they are judged.

promote_finalists has two halves. The builds and the runs on the promotion
list happen on the cluster and can only be shown there. These tests pin the
other half, the part that decides what those runs mean: which candidates
qualify, where they are read from, and how the variants are compared.

Two real documents anchor the candidates: the sR spec
(spec/sr.paper_only.json) and the CBP2025 host knobs fixture, the same pair
test_constraints.py uses. Every candidate is a header dse.params_header
renders, so a test cannot pass on a header format the search never writes.
"""

import json
from pathlib import Path

import pytest

import adopt_a_paper_loop
import constants as C
import constraints as K
import dse

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def spec():
    return json.loads((REPO / "spec" / "sr.paper_only.json").read_text())


@pytest.fixture
def plan():
    doc = json.loads((FIXTURES / "cbp2025.host_knobs.json").read_text())
    return {"host_knobs": doc["host_knobs"], "host_storage": doc["host_storage"]}


def program(pid, spec, plan, score, feature=None, host=None, iteration=1, scored=True):
    """One evolver program as the search records it. A candidate screening
    built and ran carries the screening metric; a refused one has a score only."""
    metrics = {"combined_score": score}
    if scored:
        metrics[C.DSE_SCREEN_METRIC] = 1000.0 / score - 1
    return {"id": pid, "iteration_found": iteration, "prompts": {"big": "x" * 100},
            "solution": dse.params_header(spec, plan, feature, host), "metrics": metrics}


# ------------------------------------------------------------ selection


def test_finalists_are_the_best_distinct_candidates_other_than_the_defaults(spec, plan):
    population = [
        program("seed", spec, plan, 170.0, iteration=0),
        program("a", spec, plan, 168.0, host={"logg": 11}),
        program("b", spec, plan, 169.0, feature={"num_banks": 10}),
        program("b-again", spec, plan, 165.0, feature={"num_banks": 10}, iteration=4),
        program("refused", spec, plan, 0.5, feature={"num_banks": 12}, scored=False),
        program("illegal", spec, plan, 200.0, feature={"num_banks": 99}),
        program("c", spec, plan, 160.0, feature={"wt_ctr_bits": 5}),
    ]
    finalists, passed_over = dse.select_finalists(
        population, spec, plan, dse.constraint_set("iso-192KiB"), top_k=2)
    assert [f["id"] for f in finalists] == ["b", "a"]
    assert passed_over == {"not_scored": 1, "fails_static_check": 1,
                           "defaults": 1, "duplicate": 1}
    assert finalists[0]["storage_bits"] > 0


def test_a_duplicate_keeps_the_better_score(spec, plan):
    population = [
        program("early", spec, plan, 150.0, feature={"num_banks": 10}, iteration=1),
        program("late", spec, plan, 155.0, feature={"num_banks": 10}, iteration=5),
    ]
    finalists, _ = dse.select_finalists(
        population, spec, plan, dse.constraint_set("iso-192KiB"), top_k=3)
    assert [f["id"] for f in finalists] == ["late"]


def test_a_candidate_over_the_allowance_is_never_promoted(spec, plan):
    """The search refuses such a candidate before the build. Promotion checks
    again from the header itself, so a record that claims a score cannot
    carry an over-budget candidate into the verdict."""
    population = [
        program("grown", spec, plan, 180.0, feature={"num_banks": 16}),
        program("shrunk", spec, plan, 160.0, host={"nbankhigh": 12, "logb": 10}),
    ]
    finalists, passed_over = dse.select_finalists(
        population, spec, plan, dse.constraint_set("iso-64KiB"), top_k=3)
    assert [f["id"] for f in finalists] == ["shrunk"]
    assert passed_over["fails_static_check"] == 1
    assert finalists[0]["storage_bits"] <= C.BUDGET_TRACKS_BITS["iso-64KiB"]


def test_headers_from_another_plan_all_fail_the_static_check(spec, plan):
    """What happens when the plan in force is not the one the search ran
    under: the knob sets differ, so no candidate qualifies, and promotion
    stops with no_finalists instead of building the wrong thing."""
    other = {"host_knobs": plan["host_knobs"][:-1], "host_storage": plan["host_storage"]}
    population = [program("a", spec, plan, 168.0, host={"logg": 11})]
    finalists, passed_over = dse.select_finalists(
        population, spec, other, dse.constraint_set("iso-192KiB"), top_k=3)
    assert finalists == []
    assert passed_over["fails_static_check"] == 1


# ------------------------------------------------------------ loading


def _write_checkpoint(root: Path, n: int, programs: list[dict]):
    d = root / "checkpoints" / f"checkpoint_{n}" / "programs"
    d.mkdir(parents=True)
    for p in programs:
        (d / f"{p['id']}.json").write_text(json.dumps(p))


def test_every_checkpoint_is_read_not_only_the_last(tmp_path, spec, plan):
    seed = program("seed", spec, plan, 170.0, iteration=0)
    dropped = program("dropped", spec, plan, 175.0, feature={"num_banks": 10})
    later = program("later", spec, plan, 160.0, host={"logg": 11}, iteration=2)
    _write_checkpoint(tmp_path, 1, [seed, dropped])
    _write_checkpoint(tmp_path, 2, [seed, later])
    population = dse.load_population(tmp_path)
    assert sorted(p["id"] for p in population) == ["dropped", "later", "seed"]
    assert all("prompts" not in p for p in population)

    one = dse.load_population(tmp_path / "checkpoints" / "checkpoint_2")
    assert sorted(p["id"] for p in one) == ["later", "seed"]


def test_a_summary_json_is_read_for_its_host(tmp_path, spec, plan):
    doc = {"dse": [
        {"host": "cbp2025", "population": [program("a", spec, plan, 168.0)]},
        {"host": "champsim", "population": [program("b", spec, plan, 150.0)]},
    ]}
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(doc))
    assert [p["id"] for p in dse.load_population(path, "cbp2025")] == ["a"]


@pytest.mark.parametrize("make", [lambda p: p / "missing", lambda p: p])
def test_a_path_with_no_search_in_it_stops(tmp_path, make):
    with pytest.raises(SystemExit):
        dse.load_population(make(tmp_path))


# ------------------------------------------------------------ comparison

TRACES = ["int/a.gz", "web/b.gz", "fp/c.gz"]


def runs(mpki, ipc=(2.0, 2.0, 2.0)):
    """Per-trace metrics under the names cbp2025_adapter.parse_metrics uses.
    None marks a failed run."""
    return {t: None if m is None else {"brmispki_50perc_amean": m,
                                       "cycwppki_50perc_amean": m * 80,
                                       "ipc_50perc_amean": i}
            for t, m, i in zip(TRACES, mpki, ipc)}


def test_the_winner_is_the_best_finalist_on_the_promotion_traces():
    per_trace = {
        "baseline": runs([5.0, 6.0, 7.0]),
        "defaults": runs([4.9, 6.0, 7.0]),
        "finalist_1": runs([4.8, 6.1, 7.0]),
        "finalist_2": runs([4.7, 5.9, 6.9]),
    }
    result = dse.compare_variants(per_trace, TRACES, ["finalist_1", "finalist_2"])
    verdict = result["verdict"]
    assert verdict["winner"] == "finalist_2"
    # The screening winner lost on traces the search never saw.
    assert verdict["screening_winner_held"] is False
    assert verdict["tuned_beats_baseline"] and verdict["tuned_beats_defaults"]
    assert verdict["defaults_beat_baseline"]

    vs = result["vs_baseline"]["finalist_2"]["brmispki_50perc_amean"]
    assert vs["traces_lower"] == 3 and vs["traces_higher"] == 0
    assert vs["change"] == pytest.approx(5.8333333 / 6.0 - 1)
    mixed = result["vs_baseline"]["finalist_1"]["brmispki_50perc_amean"]
    assert (mixed["traces_lower"], mixed["traces_higher"], mixed["traces_same"]) == (1, 1, 1)
    assert "finalist_1" in result["vs_defaults"] and "baseline" not in result["vs_defaults"]


def test_a_finalist_that_missed_a_trace_cannot_win():
    per_trace = {
        "baseline": runs([5.0, 6.0, 7.0]),
        "defaults": runs([5.0, 6.0, 7.0]),
        "finalist_1": runs([4.9, 6.0, 7.0]),
        "finalist_2": runs([4.0, 5.0, None]),
    }
    result = dse.compare_variants(per_trace, TRACES, ["finalist_1", "finalist_2"])
    assert result["verdict"]["winner"] == "finalist_1"
    assert result["variants"]["finalist_2"]["failed"] == ["fp/c.gz"]
    assert "finalist_2" not in result["vs_baseline"]


def test_no_verdict_without_a_complete_baseline():
    per_trace = {
        "baseline": runs([5.0, None, 7.0]),
        "defaults": runs([5.0, 6.0, 7.0]),
        "finalist_1": runs([4.9, 6.0, 7.0]),
    }
    result = dse.compare_variants(per_trace, TRACES, ["finalist_1"])
    assert "verdict" not in result
    assert "baseline" in result["error"]


def test_a_measured_constraint_is_checked_on_the_promotion_traces():
    floor = K.Constraint("ipc_50perc_amean", ">=", 1.9, "ipc floor")
    per_trace = {
        "baseline": runs([5.0, 6.0, 7.0]),
        "defaults": runs([5.0, 6.0, 7.0]),
        "finalist_1": runs([4.9, 6.0, 7.0]),
        "finalist_2": runs([4.0, 5.0, 6.0], ipc=(1.5, 1.5, 1.5)),
    }
    result = dse.compare_variants(per_trace, TRACES, ["finalist_1", "finalist_2"],
                                  [floor, *dse.constraint_set("iso-192KiB")])
    assert result["verdict"]["winner"] == "finalist_1"


# ------------------------------------------------------------ driver


@pytest.mark.parametrize("argv", [
    ["--stage", "promote"],
    ["--stage", "promote", "--promote-from", "out/x"],
    ["--stage", "promote", "--host", "cbp2025"],
])
def test_a_promote_stage_without_a_search_says_where_to_find_one(monkeypatch, argv):
    """Checked before ray.init, so a bad command fails in seconds."""
    monkeypatch.setattr("sys.argv", ["adopt_a_paper_loop.py", *argv])
    with pytest.raises(SystemExit, match="--promote-from"):
        adopt_a_paper_loop.main()
