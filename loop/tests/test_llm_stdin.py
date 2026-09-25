"""A prompt too long for argv reaches agy on stdin; every other prompt is
sent exactly as before.

On 2026-09-24 the gem5 planner prompt was 148,826 bytes. Linux refuses any
single argv string over 131,072 bytes, so `agy --print <prompt>` failed with
E2BIG three times and stage 2 died before the model saw it. The CBP2025
prompts fit, and they must keep getting chia's own command unchanged.
"""

import json

import pytest

import llm
from chia.models.antigravity import AntigravityLLM


def _pair(**kw):
    kw.setdefault("model", "gemini-3.1-pro-high")
    kw.setdefault("system_message", "sys")
    return AntigravityLLM(**kw), llm.StdinAntigravityLLM(**kw)


@pytest.mark.parametrize("size", [0, 99_110, llm._ARGV_STRING_MAX - 1000])
def test_a_prompt_that_fits_argv_gets_chias_command(size):
    base, ours = _pair()
    msg = "x" * size
    assert ours._build_cmd(msg) == base._build_cmd(msg)


def test_a_resumed_prompt_that_fits_argv_gets_chias_command():
    base, ours = _pair(resume_session=True)
    for m in (base, ours):
        m._conversation_id = "c0ffee"
    assert ours._build_cmd("short") == base._build_cmd("short")


def test_a_long_prompt_goes_to_stdin_from_the_run_home(tmp_path):
    base, ours = _pair(resume_session=True)
    for m in (base, ours):
        m._conversation_id = "c0ffee"
    ours._run_home = str(tmp_path)
    msg = "y" * 150_000
    chia = base._build_cmd(msg)
    cmd = ours._build_cmd(msg)

    # exec, so agy keeps the PID chia's Popen hook tracks and a stop kills it
    assert cmd[:3] == ["sh", "-c", 'exec "$@" < "$0"']
    path = cmd[3]
    assert path.startswith(str(tmp_path))
    # chia's own flags, resume included, minus the prompt, plus stdin input
    assert cmd[4:] == chia[:-2] + ["--input-format", "stream-json"]
    assert "--print" not in cmd and "--output-format" in cmd
    assert all(len(a.encode()) < llm._ARGV_STRING_MAX for a in cmd)

    lines = open(path).read().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "event": "user", "message": {"content": chia[-1]}}


def test_make_llm_uses_the_stdin_capable_class():
    m = llm.make_llm("antigravity", [], resume=True)
    assert isinstance(m, llm.StdinAntigravityLLM)
    assert llm.llm_resources(m) == llm.C.ANTIGRAVITY_RESOURCE
