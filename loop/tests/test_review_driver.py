"""End-to-end tests for the review round driver with a stubbed backend.

review_spec() is the one part of the stage that talks to chia, so it is also
the part the other test modules cannot reach. Here the `llm` module is replaced
with a stub, which exercises the real driver logic -- round sequencing, fan-out
and collection, evidence checking, patch merging, the regression gate and the
accept/reject decision -- without a cluster.
"""

import copy
import json
import re
import sys
import types

import pytest

import constants as C
import helpers
import spec_review


PAPER = (
    "The victim tag table holds 256 entries of 12 bits each.\n\n"
    "Each decay counter is decremented once per cycle and the entry is "
    "invalidated when it reaches zero.\n"
)


@pytest.fixture
def spec():
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "A Victim Tag Predictor", "inputs_used": "paper_only"},
        "summary": "Tracks evicted tags.",
        "state": [
            {"name": "victim tag table", "organization": "256 entries",
             "entry_format": "tag (12)", "size_bits": 3072, "indexing": "PC"},
        ],
        "algorithms": [
            {"name": "predict", "trigger": "lookup",
             "pseudocode": "v = victim_tag_table[PC]\nreturn v.tag"},
        ],
        "host_interfaces": [{"need": "evicted tag", "description": "the tag"}],
        "resource_accounting": {"total_storage_bits": 3072},
        "parameters": [],
        "unit_tests": [{"name": "t", "given": "one fill", "expect": "tag == 0x1A"}],
    }


def install_stub_llm(monkeypatch, replies, fail_on=None, fail_with=RuntimeError):
    """Replace the lazily imported `llm` module.

    submit_llm returns the prompt itself as the "ref", so collect_llm can pick
    a canned reply by looking at which unit the prompt was built for. That also
    proves the driver keeps prompts and results correctly paired across a
    fan-out.
    """
    mod = types.ModuleType("llm")
    mod.load_prompt = lambda name, **kw: f"[prompt {name} {kw.get('unit_id', '')}]"
    mod.make_llm = lambda backend, tools, resume=False: object()
    mod.submit_llm = lambda llm, prompt, tools: prompt

    def collect_llm(ref, llm=None):
        if fail_on and fail_on in ref:
            raise fail_with("backend exploded")
        body = '{"records": []}'
        for key, reply in (replies or {}).items():
            if key in ref:
                body = reply
                break
        return types.SimpleNamespace(
            result=body, stream_result="", success=True, usage={}
        )

    mod.collect_llm = collect_llm
    monkeypatch.setitem(sys.modules, "llm", mod)


def record(**kw):
    base = {"pointer": "/summary", "claim": "c", "verdict": "SUPPORTED",
            "evidence": {"quote": "holds 256 entries of 12 bits each", "why": "w"}}
    base.update(kw)
    return json.dumps({"records": [base]})


@pytest.fixture
def dump(tmp_path):
    return helpers.Dumper(out_dir=tmp_path)


# --------------------------------------------------------------- the driver


def test_driver_terminates_when_no_reviewer_patches(monkeypatch, dump, spec):
    install_stub_llm(monkeypatch, {})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec
    assert len(summary["rounds"]) == 1          # stopped as soon as nothing changed
    assert summary["rounds"][0]["accepted"]


def test_the_feature_budget_reaches_the_rounds(monkeypatch, dump, spec):
    """A feature budget the reviewers never see is one the gate can only
    refuse the spec over, with no round left in which to repair it. Before
    this, only the final gate in `adopt_a_paper_loop` was passed the
    figure, so every round scored the spec against the whole track."""
    install_stub_llm(monkeypatch, {})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)

    _, loose = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert loose["rounds"][0]["checks_before"]["error"] == 0

    _, tight = spec_review.review_spec(
        dump, spec, PAPER, 1 << 20, feature_budget_bits=1000)
    assert tight["rounds"][0]["checks_before"]["error"] == 1


def test_driver_applies_an_evidenced_patch(monkeypatch, dump, spec):
    reply = record(
        pointer="/state/0/size_bits", verdict="CONTRADICTED",
        patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 3072},
    )
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out["state"][0]["size_bits"] == 3072
    assert summary["rounds"][0]["verdicts"]["CONTRADICTED"] == 1


def test_driver_promotes_an_ambiguity_to_a_dse_knob(monkeypatch, dump, spec):
    reply = record(
        pointer="/algorithms/0/pseudocode", verdict="UNSUPPORTED", evidence=None,
        open_question="Is the tag checked before use?",
        enum_candidates=["checked", "unchecked"],
    )
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    out, _ = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert any("Is the tag checked before use?" in q for q in out["open_questions"])
    assert [p for p in out["parameters"] if p.get("origin") == "review:unsupported"]


def test_driver_refuses_an_evidenced_patch_that_guts_a_field(monkeypatch, dump, spec):
    """An evidenced patch is still not licence to replace a rule with a stub.

    The patch below is in scope and cites a real quote, so nothing earlier in
    the pipeline stops it. It is refused at apply time for the size of the
    loss, and the reviewer's claim is escalated rather than dropped.
    """
    reply = json.dumps({"records": [
        {"pointer": "/algorithms/0/pseudocode", "claim": "rule is wrong",
         "verdict": "CONTRADICTED",
         "evidence": {"quote": "holds 256 entries of 12 bits each", "why": "w"},
         "patch": {"op": "replace", "pointer": "/algorithms/0/pseudocode",
                   "value": "x"}},
    ]})
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out["algorithms"][0]["pseudocode"] == spec["algorithms"][0]["pseudocode"]
    assert summary["rounds"][0]["accepted"]
    # Escalated as a question about the field, tagged with it. "Reviewer
    # wanted to shorten /x" was the loop's own bookkeeping, and untagged it
    # was invisible to the pointer-scoped dedup as well.
    escalated = [q for q in out["open_questions"] if "rule is wrong" in q]
    assert escalated and escalated[0].startswith("[/algorithms/0/pseudocode]")


def test_driver_rolls_back_collateral_loss_inside_a_rewritten_object(
    monkeypatch, dump, spec, tmp_path
):
    """Rewriting a whole element must not launder a dropped field.

    The patch replaces /algorithms/0 wholesale and silently omits `notes`.
    The patch justifies its own pointer but not the key lost beneath it, so
    it is dropped -- and only it. The round is no longer rejected over one
    attributable loss: blaming the round discarded every correct patch beside
    the offender and ended the stage, which is how a run once shipped with an
    unresolved `missing_recovery_algorithm` the reviewer had already fixed.
    """
    spec["algorithms"][0]["notes"] = "saturating counter; ties break toward LRU"
    reply = json.dumps({"records": [
        {"pointer": "/algorithms/0", "claim": "trigger is wrong",
         "verdict": "CONTRADICTED",
         "evidence": {"quote": "decremented once per cycle", "why": "w"},
         "patch": {"op": "replace", "pointer": "/algorithms/0", "value": {
             "name": "predict", "trigger": "every cycle",
             "pseudocode": "v = victim_tag_table[PC]\nreturn v.tag"}}},
    ]})
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    before = copy.deepcopy(spec)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    # The loss never lands: the only patch in the round was the offender.
    assert out["algorithms"][0] == before["algorithms"][0]
    assert summary["rounds"][0]["accepted"] is True
    assert summary["rounds"][0]["patches_landed"] == 0
    log = json.loads(next(tmp_path.glob("*review_round0.json")).read_text())
    assert log["regressions"] == []
    assert any("no patch this round claimed" in r["reason"]
               for r in log["rejections"])


def test_driver_survives_one_dead_reviewer(monkeypatch, dump, spec):
    install_stub_llm(monkeypatch, {}, fail_on="global")
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec
    assert summary["rounds"][0]["accepted"]


def test_systemexit_from_the_backend_does_not_kill_the_job(monkeypatch, dump, spec):
    """collect_llm signals failure with SystemExit, which is a BaseException.

    `except Exception` does not catch it, so an exhausted reviewer used to take
    the whole job down and skip the partial-review bookkeeping entirely.
    """
    install_stub_llm(monkeypatch, {}, fail_on="global", fail_with=SystemExit)
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec
    assert summary["final"]["complete"] is False
    assert summary["final"]["unreviewed_units"] == ["global"]


def test_all_reviewers_dying_still_returns_a_spec(monkeypatch, dump, spec):
    install_stub_llm(monkeypatch, {}, fail_on="", fail_with=SystemExit)
    sys.modules["llm"].collect_llm = lambda ref, llm=None: (_ for _ in ()).throw(
        SystemExit("AntigravityLLM call failed (success=False). result='' stream=''")
    )
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec
    assert summary["final"]["complete"] is False
    assert len(summary["final"]["unreviewed_units"]) == len(spec_review.partition(spec)) + 1


def test_a_dead_reviewer_marks_the_review_incomplete(monkeypatch, dump, spec, capsys):
    """A unit nobody reviewed must not look the same as a unit that came back clean."""
    install_stub_llm(monkeypatch, {}, fail_on="global")
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert summary["final"]["complete"] is False
    assert summary["final"]["unreviewed_units"] == ["global"]
    assert "INCOMPLETE" in capsys.readouterr().out


def test_a_fully_reviewed_spec_is_marked_complete(monkeypatch, dump, spec):
    install_stub_llm(monkeypatch, {})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert summary["final"]["complete"] is True
    assert summary["final"]["unreviewed_units"] == []


def test_quota_exhaustion_stops_the_loop_immediately(monkeypatch, dump, spec):
    """Firing another wave at an exhausted account buys nothing."""
    calls = {"n": 0}

    def rate_limited(ref, llm=None):
        calls["n"] += 1
        raise RuntimeError(
            "RateLimitError: RESOURCE_EXHAUSTED (code 429): Individual quota "
            "reached. Resets in 140h47m37s."
        )

    install_stub_llm(monkeypatch, {})
    sys.modules["llm"].collect_llm = rate_limited
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec
    assert len(summary["rounds"]) == 1                    # did not start round 2
    assert summary["rounds"][0]["quota_exhausted"] is True
    assert summary["final"]["complete"] is False
    units = spec_review.partition(spec)
    assert calls["n"] == len(units) + 1   # this round's jobs were already in flight


@pytest.mark.parametrize("msg", [
    "RESOURCE_EXHAUSTED (code 429): Individual quota reached",
    "rate_limit on fe12278b: error: Individual quota reached",
    "429 Too Many Requests",
    "Quota exceeded for this project",
])
def test_quota_error_detection(msg):
    assert spec_review._is_quota_error(RuntimeError(msg))


def test_ordinary_failure_is_not_read_as_quota():
    assert not spec_review._is_quota_error(RuntimeError("connection reset by peer"))


def test_driver_honours_the_round_cap(monkeypatch, dump, spec):
    """A reviewer that makes progress every round is stopped by the cap.

    Progress has to be real for the cap to be what ends the loop: this
    reviewer surfaces a *different* ambiguity each round, so each round mints
    a knob. Driving it with a reviewer that only appends open questions tests
    nothing about the cap -- see
    test_open_questions_alone_do_not_buy_another_round for why that case must
    converge at round 1 instead.
    """
    counter = {"n": 0}

    def reply_factory(ref, llm=None):
        counter["n"] += 1
        n = counter["n"]
        body = json.dumps({"records": [{
            "pointer": "/algorithms/0/pseudocode", "verdict": "UNSUPPORTED",
            "claim": f"c{n}", "open_question": f"q{n}",
            "enum_candidates": [f"a{n}", f"b{n}"],
        }]}) if "algo:predict" in ref else '{"records": []}'
        return types.SimpleNamespace(result=body, stream_result="", success=True, usage={})

    install_stub_llm(monkeypatch, {})
    sys.modules["llm"].collect_llm = reply_factory
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 10)   # not the binding limit
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert len(summary["rounds"]) == 3
    assert all(r["knobs_minted"] for r in summary["rounds"])
    assert summary["rounds"][-1]["stop_reason"] is None  # the cap ended it


def test_driver_writes_an_auditable_artifact_per_round(monkeypatch, dump, spec, tmp_path):
    install_stub_llm(monkeypatch, {"algo:predict": record()})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    rounds = list(tmp_path.glob("*review_round0.json"))
    transcripts = list(tmp_path.glob("*review_r0_*.md"))
    assert rounds and transcripts
    log = json.loads(rounds[0].read_text())
    assert {"records", "rejections", "checks_before", "checks_after",
            "regressions", "accepted"} <= set(log)


def test_driver_fans_out_one_job_per_unit_plus_coverage(monkeypatch, dump, spec):
    seen = []
    install_stub_llm(monkeypatch, {})
    original = sys.modules["llm"].collect_llm

    def spy(ref, llm=None):
        seen.append(ref)
        return original(ref, llm)

    sys.modules["llm"].collect_llm = spy
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    units = spec_review.partition(spec)
    assert len(seen) == len(units) + 1          # + one coverage chunk


# ---------------------------------- INCONSISTENT at the driver level


@pytest.fixture
def contradicted_spec():
    """Both halves copied faithfully from the paper; together unimplementable."""
    return {
        "feature_name": "vtag",
        "source": {"paper_title": "A Victim Tag Predictor", "inputs_used": "paper_only"},
        "summary": "Tracks evicted tags.",
        "state": [
            {"name": "decay table", "organization": "4 counters",
             "entry_format": "decay_ctr (8 bits)", "size_bits": 32,
             "indexing": "bank"},
        ],
        "algorithms": [
            {"name": "refresh", "trigger": "completion",
             "pseudocode": "decay_ctr = 256"},
        ],
        "host_interfaces": [{"need": "tick", "description": "per-instruction tick"}],
        "resource_accounting": {"total_storage_bits": 32},
        "parameters": [],
        "unit_tests": [{"name": "t", "given": "g", "expect": "ctr == 0"}],
    }


def test_driver_clears_a_self_contradiction(monkeypatch, dump, contradicted_spec):
    reply = record(
        pointer="/algorithms/0/pseudocode", verdict="INCONSISTENT",
        evidence=None,
        patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
               "value": "decay_ctr = 255  // 256 steps encoded as 255..0"},
    )
    install_stub_llm(monkeypatch, {"algo:refresh": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    out, summary = spec_review.review_spec(dump, contradicted_spec, PAPER, 1 << 20)
    assert "255" in out["algorithms"][0]["pseudocode"]
    assert summary["rounds"][0]["accepted"]
    assert summary["final"]["errors"] == 0


def test_driver_rolls_back_an_inconsistent_patch_that_fixes_nothing(
    monkeypatch, dump, contradicted_spec
):
    """No quote vouches for an INCONSISTENT patch, so the only thing that can
    is the contradiction disappearing. If it does not, the patch rewrote the
    spec on no authority at all."""
    reply = record(
        pointer="/algorithms/0/pseudocode", verdict="INCONSISTENT",
        evidence=None,
        patch={"op": "replace", "pointer": "/algorithms/0/pseudocode",
               "value": "decay_ctr = 256  // reworded, still does not fit"},
    )
    install_stub_llm(monkeypatch, {"algo:refresh": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    out, summary = spec_review.review_spec(dump, contradicted_spec, PAPER, 1 << 20)
    assert out == contradicted_spec                       # rolled back
    assert not summary["rounds"][0]["accepted"]
    assert "error count did not fall" in summary["rounds"][0]["reject_reason"]
    assert summary["final"]["errors"] == 1


def test_summary_reports_outstanding_errors(monkeypatch, dump, contradicted_spec):
    """distill() reads this to decide whether to write the spec at all."""
    install_stub_llm(monkeypatch, {})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 1)
    _, summary = spec_review.review_spec(dump, contradicted_spec, PAPER, 1 << 20)
    assert summary["final"]["errors"] == 1


# ------------------------------------------- convergence, not document churn


def test_open_questions_alone_do_not_buy_another_round(monkeypatch, dump, spec):
    """The bug this exists for: every round grows open_questions, so the old
    `candidate != spec` test never went False and the cap, not convergence,
    ended every run.

    An observed round cost an hour of wall clock, landed no patch, left all
    three deterministic check counts byte-identical, and added ten lines of
    prose -- and the loop then started another.
    """
    # UNSUPPORTED at a pointer no knob can resolve: the question is recorded,
    # so the document changes, but nothing an implementer can act on does.
    reply = record(
        pointer="/summary", verdict="UNSUPPORTED", evidence=None,
        open_question="Does the paper give a fill policy?",
    )
    install_stub_llm(monkeypatch, {"global": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert len(summary["rounds"]) == 1
    assert summary["rounds"][0]["stop_reason"].startswith("converged")
    assert summary["rounds"][0]["patches_landed"] == 0
    assert summary["rounds"][0]["knobs_minted"] == 0
    # The question is still recorded -- stopping early loses nothing.
    assert any("fill policy" in q for q in out["open_questions"])


def test_a_minted_knob_does_buy_another_round(monkeypatch, dump, spec):
    """Progress must still keep the loop alive, or the fix is just a cap of 1."""
    reply = record(
        pointer="/algorithms/0/pseudocode", verdict="UNSUPPORTED", evidence=None,
        open_question="Is the tag checked before use?",
        enum_candidates=["checked", "unchecked"],
    )
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 6)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert summary["rounds"][0]["knobs_minted"] == 1
    assert summary["rounds"][0]["stop_reason"] is None
    assert len(summary["rounds"]) > 1


def test_an_exhausted_knob_budget_ends_the_loop(monkeypatch, dump, spec):
    """The shape this run actually hit.

    The cap is spec-wide, so once it is spent no later round can mint
    anything; a round that also lands no patch cannot advance the spec and the
    loop has to stop instead of burning the remaining rounds.
    """
    reply = record(
        pointer="/algorithms/0/pseudocode", verdict="UNSUPPORTED", evidence=None,
        open_question="Is the tag checked before use?",
        enum_candidates=["checked", "unchecked"],
    )
    install_stub_llm(monkeypatch, {"algo:predict": reply})
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 5)
    monkeypatch.setattr(C, "REVIEW_MAX_PROMOTED", 1)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert [r["knobs_minted"] for r in summary["rounds"]] == [1, 0]
    assert summary["rounds"][-1]["stop_reason"].startswith("converged")


def test_a_failed_unit_is_not_convergence(monkeypatch, dump, spec):
    """A unit whose reviewer died was never reviewed, so the next round is
    its retry -- not a round that found nothing."""
    install_stub_llm(monkeypatch, {}, fail_on="algo:predict")
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert summary["rounds"][0]["failed_units"]
    assert summary["rounds"][0]["stop_reason"] is None
    assert len(summary["rounds"]) == 2


def test_review_knobs_counts_only_this_stage_s_parameters():
    """It reads the provenance marker promote_unsupported writes, which is
    also what the spec-wide cap counts."""
    assert spec_review.review_knobs({}) == 0
    assert spec_review.review_knobs({"parameters": [
        {"name": "hand_written", "type": "int"},
        {"name": "from_review", "type": "enum", "origin": "review:unsupported"},
    ]}) == 1

# --------------------------------------------- a retry reviews only the loss


def spy_llm(monkeypatch, fail_unit=None, fail_rounds=(), replies=None):
    """Stub the `llm` module and record which units each round submitted.

    The unit id is parsed back out of the prompt header the stub itself
    builds, which is how this harness pairs a reply to a unit; coverage has no
    unit_id, so it reads back as "coverage".
    """
    rounds: list[list[str]] = []

    def unit_of(ref):
        m = re.match(r"\[prompt (\S+) ([^\]]*)\]", ref)
        if not m:
            return "?"
        name, unit_id = m.group(1), m.group(2).strip()
        return unit_id or ("coverage" if "coverage" in name else "?")

    def collect_llm(ref, llm=None):
        unit = unit_of(ref)
        rounds[-1].append(unit)
        if unit == fail_unit and (len(rounds) - 1) in fail_rounds:
            raise RuntimeError("backend exploded")
        body = '{"records": []}'
        for key, reply in (replies or {}).items():
            if key == unit:
                body = reply
                break
        return types.SimpleNamespace(
            result=body, stream_result="", success=True, usage={})

    install_stub_llm(monkeypatch, {})
    sys.modules["llm"].collect_llm = collect_llm

    real_partition = spec_review.partition

    def partition(sp, max_units=None):
        rounds.append([])
        return real_partition(sp, max_units)

    monkeypatch.setattr(spec_review, "partition", partition)
    return rounds


def test_a_retry_round_reviews_only_the_failed_unit(monkeypatch, dump, spec):
    """The shape this run hit: one empty response cost a whole round.

    Round 0 loses `global` to a dead backend call. Nothing else is left to do
    -- no patch landed, no knob minted -- so round 1 is that unit's retry, and
    re-asking the units that already answered would only re-derive verdicts
    the round log already holds.
    """
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    rounds = spy_llm(monkeypatch, fail_unit="global", fail_rounds=(0,))
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert len(rounds) == 2
    assert sorted(rounds[0]) == ["algo:predict", "coverage", "global"]
    # Only the loss -- and not the whole-spec coverage pass, which succeeded
    # and is the most expensive call in a round.
    assert rounds[1] == ["global"]
    assert summary["rounds"][1]["retry_of"] == ["global"]
    assert summary["rounds"][1]["units"] == ["global"]


def test_a_retry_that_answers_ends_the_loop(monkeypatch, dump, spec):
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 5)
    rounds = spy_llm(monkeypatch, fail_unit="global", fail_rounds=(0,))
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert len(rounds) == 2                       # not the full cap of 5
    assert summary["rounds"][1]["failed_units"] == []
    assert summary["rounds"][1]["stop_reason"].startswith("converged")


def test_a_unit_that_keeps_failing_keeps_being_retried_alone(monkeypatch, dump, spec):
    """A repeated failure is worth re-asking now that it costs one call.

    What must not happen is the whole partition going again each time.
    """
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    rounds = spy_llm(monkeypatch, fail_unit="global", fail_rounds=(0, 1, 2))
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert rounds[1] == ["global"] and rounds[2] == ["global"]
    assert summary["final"]["unreviewed_units"] == ["global"]


def test_a_round_that_made_progress_is_not_narrowed(monkeypatch, dump, spec):
    """A patch changed the spec under every unit, so the next round is full.

    Narrowing here would re-review the failed unit against a spec none of the
    others have been re-checked against.
    """
    reply = record(
        pointer="/state/0/size_bits", verdict="CONTRADICTED",
        patch={"op": "replace", "pointer": "/state/0/size_bits", "value": 3072},
    )
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    rounds = spy_llm(monkeypatch, fail_unit="global", fail_rounds=(0,),
                     replies={"algo:predict": reply})
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert summary["rounds"][0]["patches_landed"] == 1
    assert summary["rounds"][0]["failed_units"] == ["global"]
    assert summary["rounds"][1]["retry_of"] is None
    assert sorted(rounds[1]) == ["algo:predict", "coverage", "global"]


def test_a_vanished_retry_target_falls_back_to_the_full_partition(
        monkeypatch, dump, spec):
    """Unit ids are derived, so a retry target can stop existing.

    Reviewing nothing would let the run report a spec as fully reviewed when
    the failed unit never was, so the fallback errs towards reviewing too much.
    """
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 2)
    rounds: list[list[str]] = []

    def collect_llm(ref, llm=None):
        m = re.match(r"\[prompt (\S+) ([^\]]*)\]", ref)
        unit = (m.group(2).strip() or "coverage") if m else "?"
        rounds[-1].append(unit)
        if unit == "global" and len(rounds) == 1:
            raise RuntimeError("backend exploded")
        return types.SimpleNamespace(
            result='{"records": []}', stream_result="", success=True, usage={})

    install_stub_llm(monkeypatch, {})
    sys.modules["llm"].collect_llm = collect_llm
    real_partition = spec_review.partition

    def partition(sp, max_units=None):
        rounds.append([])
        units = real_partition(sp, max_units)
        # Round 1: the failed unit is gone from the partition entirely.
        return [u for u in units if u.unit_id != "global"] if rounds[1:] else units

    monkeypatch.setattr(spec_review, "partition", partition)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)

    assert summary["rounds"][1]["retry_of"] == ["global"]
    assert rounds[1] and rounds[1] != []          # reviewed something, not nothing
    assert "algo:predict" in rounds[1]            # the full remaining partition
