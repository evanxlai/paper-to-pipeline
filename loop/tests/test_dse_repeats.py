"""Stage 4 does not screen the same candidate twice, and keeps every one it screened.

On 2026-09-23, 7 of 24 iterations re-proposed a header the search had already
scored, and each one spent about 18 minutes of trace slots. The same run lost
the header of a candidate its population dropped, so promotion could not score
it. These tests pin both fixes, and that promotion ranks by MPKI.
"""

import asyncio
import json

import pytest

import constants as C
import dse

HEADER = """// generated
#pragma once
#define SR_NUM_BANKS 8  // range: [1, 16]
#define HOST_LOGG 10  // range: [8, 12]; sets LOGG
"""


@pytest.fixture
def evaluator(tmp_path, monkeypatch):
    """An SRParamsEvaluator whose parent screens nothing: each call to the real
    evaluate_program returns the next canned result and is counted."""
    pytest.importorskip("skydiscover", reason="skydiscover/evolve-flows not installed")
    import sr_evaluator
    from skydiscover.evaluation.chia_evaluator import ChiaEvaluator
    from skydiscover.evaluation.evaluation_result import EvaluationResult

    screened = []

    async def fake_parent(self, program_solution, program_id=""):
        screened.append(program_id)
        mpki = 6.0 + len(screened) / 100
        return EvaluationResult(
            metrics={"combined_score": 1000 / (1 + mpki), C.DSE_SCREEN_METRIC: mpki,
                     "storage_bits": 524000.0},
            artifacts={})

    monkeypatch.setattr(ChiaEvaluator, "evaluate_program", fake_parent)
    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["int/a.gz", "int/b.gz"], str(tmp_path), 60, 60)
    ev.screened = screened
    yield ev
    ev.close()


def run(ev, header, pid):
    return asyncio.run(ev.evaluate_program(header, pid))


def test_the_key_ignores_comments_and_spacing():
    import sr_evaluator

    other = HEADER.replace("// range: [1, 16]", "// a different comment").replace(
        "#define HOST_LOGG 10", "#define  HOST_LOGG   10")
    assert sr_evaluator.candidate_key(other) == sr_evaluator.candidate_key(HEADER)


def test_the_key_sees_every_line_of_code_not_only_the_knobs():
    """constraints.parse_header skips any line that is not a SR_/HOST_ define,
    so a key built on knob values would call this a repeat. It builds
    something else."""
    import sr_evaluator

    assert sr_evaluator.candidate_key(HEADER + "static int extra = 1;\n") != \
        sr_evaluator.candidate_key(HEADER)
    assert sr_evaluator.candidate_key(HEADER.replace("SR_NUM_BANKS 8", "SR_NUM_BANKS 9")) != \
        sr_evaluator.candidate_key(HEADER)


def test_a_repeat_is_not_screened_and_says_what_it_repeats(evaluator):
    first = run(evaluator, HEADER, "p1")
    again = run(evaluator, HEADER.replace("// generated", "// proposed again"), "p2")
    assert evaluator.screened == ["p1"]
    # A failed attempt to skydiscover: out of the population, and its error
    # text goes into the retry's prompt.
    assert again.metrics == {"combined_score": 0.0}
    assert again.artifacts["failure_stage"] == "repeat"
    assert again.artifacts["repeat_of"] == "p1"
    assert "p1" in again.artifacts["error"]
    assert str(first.metrics[C.DSE_SCREEN_METRIC]) in again.artifacts["error"]


def test_a_new_candidate_is_screened(evaluator):
    run(evaluator, HEADER, "p1")
    run(evaluator, HEADER.replace("SR_NUM_BANKS 8", "SR_NUM_BANKS 9"), "p2")
    assert evaluator.screened == ["p1", "p2"]


def test_a_candidate_that_was_not_screened_in_full_is_tried_again(evaluator, monkeypatch):
    """A run failure can be a worker that died. Caching it would turn one bad
    minute into a candidate the search can never score."""
    from skydiscover.evaluation.chia_evaluator import ChiaEvaluator
    from skydiscover.evaluation.evaluation_result import EvaluationResult

    calls = []

    async def failing(self, program_solution, program_id=""):
        calls.append(program_id)
        return EvaluationResult(metrics={"error": 0.0, "combined_score": 0.0},
                                artifacts={"failure_stage": "run"})

    monkeypatch.setattr(ChiaEvaluator, "evaluate_program", failing)
    run(evaluator, HEADER, "p1")
    run(evaluator, HEADER, "p2")
    assert calls == ["p1", "p2"]


def test_the_log_keeps_every_screened_header_and_promotion_reads_it(evaluator):
    run(evaluator, HEADER, "p1")
    run(evaluator, HEADER, "p2")  # a repeat
    other = HEADER.replace("SR_NUM_BANKS 8", "SR_NUM_BANKS 9")
    run(evaluator, other, "p3")

    rows = [json.loads(l) for l in open(evaluator.candidates_log)]
    assert [r["program_id"] for r in rows] == ["p1", "p2", "p3"]
    assert [r["repeat_of"] for r in rows] == [None, "p1", None]

    population = dse.load_population(evaluator.candidates_log)
    assert [p["id"] for p in population] == ["p1", "p3"]
    assert population[1]["solution"] == other
    assert dse.candidates_summary(evaluator.candidates_log) == {
        "log": evaluator.candidates_log, "evaluations": 3, "screened": 2,
        "repeats_skipped": 1}


def test_a_missing_log_reads_as_no_candidates(tmp_path):
    assert dse.read_candidates_log(tmp_path / "absent.jsonl") == []
    assert dse.candidates_summary(tmp_path / "absent.jsonl")["missing"] is True


def test_finalists_rank_by_mpki():
    worse = {"id": "a", "iteration_found": 1, "metrics": {C.DSE_SCREEN_METRIC: 6.9}}
    better = {"id": "b", "iteration_found": 5, "metrics": {C.DSE_SCREEN_METRIC: 6.8}}
    tie = {"id": "c", "iteration_found": 2, "metrics": {C.DSE_SCREEN_METRIC: 6.8}}
    assert [p["id"] for p in sorted([worse, better, tie], key=dse._screen_rank)] == ["c", "b", "a"]
