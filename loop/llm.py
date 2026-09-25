"""LLM backend factory, copied from the memcpy example's conventions.
Default backend is antigravity (Gemini via the agy CLI) per the proposal
budget; claude and opencode(+Vertex Gemini) are the alternates.

Dispatch rule (from the examples): llm.prompt is itself a ChiaFunction,
so it must be dispatched onto the container holding that backend's
credentials, via the matching resource token.
"""

import json
import os
import time

from chia.base.ChiaFunction import get
from chia.base.tools.ChiaTool import ChiaTool
from chia.base.llm_call import QueryResult
from chia.models.claude import ClaudeCodeLLM
from chia.models.antigravity import AntigravityLLM, RateLimitError
from chia.models.opencode import OpenCodeLLM, AdditionalModelProvider

import constants as C

_SYSTEM = (C.PROMPTS_DIR / "system.md").read_text()


def load_prompt(name: str, **subs: str) -> str:
    """${VAR} substitution by replace, not str.format, so C++/JSON braces
    in prompts and pasted logs survive (memcpy example convention)."""
    text = (C.PROMPTS_DIR / name).read_text()
    for key, val in subs.items():
        text = text.replace("{{" + key + "}}", val).replace("${" + key + "}", val)
    return text


# Linux caps ONE argv string at 32 pages (MAX_ARG_STRLEN, 131072 bytes with
# its NUL), whatever ARG_MAX says. AntigravityLLM passes the whole prompt as
# the value of `--print`, so a longer prompt is not sent late or truncated: it
# is never sent at all. execve fails with E2BIG ("[Errno 7] Argument list too
# long: 'agy'"), all three of chia's retries fail the same way, and the stage
# dies before the model sees a byte. The gem5 planner prompt was the first to
# cross it, on 2026-09-24: 148,826 bytes, because hosts/gem5/NOTES.md is
# three times the CBP2025 notes. The CBP2025 planner prompt is 99,110.
_ARGV_STRING_MAX = 131072


class StdinAntigravityLLM(AntigravityLLM):
    """AntigravityLLM that hands agy a prompt too long for argv on stdin.

    agy 1.2.10 reads print-mode input from stdin with `--input-format
    stream-json`, one NDJSON message per turn, and it requires the
    `--output-format stream-json` chia already passes. The message shape is
    {"event": "user", "message": {"content": <prompt>}}: agy names the
    missing field for every other shape tried. A prompt that fits argv gets
    exactly the command AntigravityLLM builds, byte for byte.

    `exec` matters. chia's Popen hook tracks the direct child's PID and a
    stop kills that PID alone, not its process group, so an `sh` that forked
    agy would leave agy running after its job was stopped. The prompt file
    lives in chia's per-call run home, which chia deletes after every call.
    """

    def _prepare_run_home(self, tools):
        self._run_home = super()._prepare_run_home(tools)
        return self._run_home

    def _build_cmd(self, user_message: str) -> list[str]:
        cmd = super()._build_cmd(user_message)
        assert cmd[-2] == "--print", cmd[-2:]  # chia passes the prompt last
        prompt = cmd[-1]
        if len(prompt.encode()) < _ARGV_STRING_MAX:
            return cmd
        path = os.path.join(self._run_home, "prompt.ndjson")
        with open(path, "w") as f:
            f.write(json.dumps({"event": "user", "message": {"content": prompt}}) + "\n")
        return ["sh", "-c", 'exec "$@" < "$0"', path,
                *cmd[:-2], "--input-format", "stream-json"]


def make_llm(backend: str, tools: list[ChiaTool], resume: bool = True):
    if backend == "antigravity":
        return StdinAntigravityLLM(
            model=C.ANTIGRAVITY_MODEL,
            system_message=_SYSTEM,
            timeout_seconds=C.LLM_TIMEOUT_SECONDS,
            resume_session=resume,
        )
    if backend == "opencode":
        vertex = AdditionalModelProvider(
            id="google-vertex",
            npm="@ai-sdk/google-vertex",
            name="Google Vertex AI",
            models=[C.OPENCODE_MODEL.split("/", 1)[1]],
            options={
                "project": C.OPENCODE_VERTEX_PROJECT,
                "location": C.OPENCODE_VERTEX_LOCATION,
            },
        )
        # Deny opencode's built-in file/bash tools: they act on the LLM
        # container's filesystem, not the host-simulator container's.
        perms = {"*": "deny", **{f"{t.name}_*": "allow" for t in tools}}
        return OpenCodeLLM(
            model=C.OPENCODE_MODEL,
            system_message=_SYSTEM,
            timeout_seconds=C.LLM_TIMEOUT_SECONDS,
            additional_providers=[vertex],
            config=perms,
        )
    return ClaudeCodeLLM(
        model=C.CLAUDE_MODEL,
        system_message=_SYSTEM,
        timeout_seconds=C.LLM_TIMEOUT_SECONDS,
        resume_session=resume,
        projects_cwd=None,
        extra_cli_args=["--effort", "max"],
    )


def llm_resources(llm) -> dict:
    if isinstance(llm, OpenCodeLLM):
        return C.OPENCODE_RESOURCE
    if isinstance(llm, AntigravityLLM):
        return C.ANTIGRAVITY_RESOURCE
    return C.LLM_RESOURCE


def submit_llm(llm, prompt: str, tools: list[ChiaTool]):
    """Non-blocking half of run_llm: returns the ref without get()ing it.

    The reviewer stage fans one call out per spec unit, so it needs every
    prompt in flight before any of them is collected. run_llm blocks, which
    would serialize the whole round.
    """
    return llm.prompt.options(resources=llm_resources(llm)).chia_remote(llm, prompt, tools)


def collect_llm(ref, llm=None) -> QueryResult:
    """Blocking half of run_llm, with the same fail-loud behavior."""
    resp = get(ref)
    if not resp.success:
        raise SystemExit(
            f"{type(llm).__name__ if llm else 'LLM'} call failed (success=False). "
            f"result={resp.result!r}\nstream={resp.stream_result!r}"
        )
    return resp


def _rate_limited(exc: Exception) -> bool:
    """A Vertex 429. Ray re-raises a task's exception as a subclass of both
    RayTaskError and the original class, so isinstance sees through it; the
    string check covers a backend that reports the same quota in plain text."""
    return isinstance(exc, RateLimitError) or "RESOURCE_EXHAUSTED" in str(exc)


def run_llm(llm, prompt: str, tools: list[ChiaTool]) -> QueryResult:
    resources = llm_resources(llm)
    # chia raises a rate limit at once rather than retrying it, which is the
    # right default for a library and the wrong one for a job that runs for
    # hours. On 2026-09-23 a single 429 from gemini-3.1-pro, eleven minutes
    # into stage 2, ended a stage 2-to-4 submission and lost the planner's
    # turn. The quota is per minute, so waiting is the fix. A resumed session
    # is safe to re-send: its transcript is only synced back on success, so
    # the retry continues from the last turn that completed.
    for attempt in range(C.LLM_RATE_LIMIT_RETRIES + 1):
        try:
            resp = get(llm.prompt.options(resources=resources).chia_remote(llm, prompt, tools))
            break
        except Exception as exc:  # noqa: BLE001
            if not _rate_limited(exc) or attempt == C.LLM_RATE_LIMIT_RETRIES:
                raise
            wait = min(C.LLM_RATE_LIMIT_BACKOFF_S * 2 ** attempt, 900)
            print(f"[llm] {type(llm).__name__} rate-limited (429), attempt "
                  f"{attempt + 1} of {C.LLM_RATE_LIMIT_RETRIES + 1}; retrying in {wait}s")
            time.sleep(wait)
    if not resp.success:
        # Backend-level failure (bad creds, CLI crash, timeout). Surface it
        # here: callers only see an empty result, which otherwise shows up
        # downstream as a bogus "not valid JSON" schema error.
        raise SystemExit(
            f"{type(llm).__name__} call failed (success=False). "
            f"result={resp.result!r}\nstream={resp.stream_result!r}"
        )
    return resp
