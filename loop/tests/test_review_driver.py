"""End-to-end tests for the review round driver with a stubbed backend.

review_spec() is the one part of the stage that talks to chia, so it is also
the part the other test modules cannot reach. Here the `llm` module is replaced
with a stub, which exercises the real driver logic -- round sequencing, fan-out
and collection, evidence checking, patch merging, the regression gate and the
accept/reject decision -- without a cluster.
"""

import json
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
    assert any("shorten" in q for q in out["open_questions"])


def test_driver_rolls_back_collateral_loss_inside_a_rewritten_object(
    monkeypatch, dump, spec
):
    """Rewriting a whole element must not launder a dropped field.

    The patch replaces /algorithms/0 wholesale and silently omits `notes`.
    The patch justifies its own pointer but not the key lost beneath it, so
    the round is rejected and the spec rolls back.
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
    out, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert out == spec                                   # rolled back
    assert summary["rounds"][0]["accepted"] is False
    assert "regression" in summary["rounds"][0]["reject_reason"]


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
    """A reviewer that keeps appending open questions never converges."""
    counter = {"n": 0}

    def reply_factory(ref, llm=None):
        counter["n"] += 1
        body = json.dumps({"records": [{
            "pointer": "/algorithms/0/pseudocode", "verdict": "UNSUPPORTED",
            "claim": "c", "open_question": f"q{counter['n']}",
        }]}) if "algo:predict" in ref else '{"records": []}'
        return types.SimpleNamespace(result=body, stream_result="", success=True, usage={})

    install_stub_llm(monkeypatch, {})
    sys.modules["llm"].collect_llm = reply_factory
    monkeypatch.setattr(C, "REVIEW_ROUNDS", 3)
    _, summary = spec_review.review_spec(dump, spec, PAPER, 1 << 20)
    assert len(summary["rounds"]) == 3


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
