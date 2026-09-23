"""LLM backend factory, copied from the memcpy example's conventions.
Default backend is antigravity (Gemini via the agy CLI) per the proposal
budget; claude and opencode(+Vertex Gemini) are the alternates.

Dispatch rule (from the examples): llm.prompt is itself a ChiaFunction,
so it must be dispatched onto the container holding that backend's
credentials, via the matching resource token.
"""

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


def make_llm(backend: str, tools: list[ChiaTool], resume: bool = True):
    if backend == "antigravity":
        return AntigravityLLM(
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
