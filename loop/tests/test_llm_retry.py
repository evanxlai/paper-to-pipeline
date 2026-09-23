"""run_llm waits out a 429 instead of ending the job.

On 2026-09-23 one RESOURCE_EXHAUSTED from Vertex, eleven minutes into stage 2,
ended a submission meant to run stages 2 to 4 unattended. chia raises a rate
limit at once by design, so the retry has to live in run_llm.
"""

import pytest

import constants as C
import llm
from chia.models.antigravity import RateLimitError


class _FakeLLM:
    """Just enough of a chia LLM for run_llm to dispatch it."""

    def __init__(self):
        self.sent = []
        outer = self

        class _Prompt:
            @staticmethod
            def options(**_):
                return _Prompt

            @staticmethod
            def chia_remote(model, prompt, tools):
                outer.sent.append(prompt)
                return len(outer.sent)

        self.prompt = _Prompt


class _Resp:
    success = True
    result = "done"


@pytest.fixture
def quiet(monkeypatch):
    waits = []
    monkeypatch.setattr(llm.time, "sleep", waits.append)
    monkeypatch.setattr(C, "LLM_RATE_LIMIT_RETRIES", 3)
    monkeypatch.setattr(C, "LLM_RATE_LIMIT_BACKOFF_S", 10)
    return waits


def _get_failing(times, exc):
    calls = {"n": 0}

    def get(ref):
        calls["n"] += 1
        if calls["n"] <= times:
            raise exc
        return _Resp()

    return get


def test_a_429_is_retried_with_backoff(quiet, monkeypatch):
    monkeypatch.setattr(llm, "get", _get_failing(2, RateLimitError(node_id="n")))
    fake = _FakeLLM()
    assert llm.run_llm(fake, "plan it", []).result == "done"
    assert fake.sent == ["plan it"] * 3
    assert quiet == [10, 20]


def test_a_quota_reported_as_text_is_retried_too(quiet, monkeypatch):
    monkeypatch.setattr(llm, "get", _get_failing(1, RuntimeError("RESOURCE_EXHAUSTED (code 429)")))
    assert llm.run_llm(_FakeLLM(), "p", []).result == "done"
    assert quiet == [10]


def test_a_quota_that_stays_spent_still_fails(quiet, monkeypatch):
    monkeypatch.setattr(llm, "get", _get_failing(99, RateLimitError(node_id="n")))
    with pytest.raises(RateLimitError):
        llm.run_llm(_FakeLLM(), "p", [])
    assert len(quiet) == 3


def test_any_other_error_is_not_retried(quiet, monkeypatch):
    monkeypatch.setattr(llm, "get", _get_failing(1, ValueError("bad prompt")))
    with pytest.raises(ValueError):
        llm.run_llm(_FakeLLM(), "p", [])
    assert quiet == []
