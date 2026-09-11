"""LLM backend factory, copied from the memcpy example's conventions.
Default backend is antigravity (Gemini via the agy CLI) per the proposal
budget; claude and opencode(+Vertex Gemini) are the alternates.

Dispatch rule (from the examples): llm.prompt is itself a ChiaFunction,
so it must be dispatched onto the container holding that backend's
credentials, via the matching resource token.
"""

from chia.base.ChiaFunction import get
from chia.base.tools.ChiaTool import ChiaTool
from chia.base.llm_call import QueryResult
from chia.models.claude import ClaudeCodeLLM
from chia.models.antigravity import AntigravityLLM
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


def run_llm(llm, prompt: str, tools: list[ChiaTool]) -> QueryResult:
    if isinstance(llm, OpenCodeLLM):
        resources = C.OPENCODE_RESOURCE
    elif isinstance(llm, AntigravityLLM):
        resources = C.ANTIGRAVITY_RESOURCE
    else:
        resources = C.LLM_RESOURCE
    return get(llm.prompt.options(resources=resources).chia_remote(llm, prompt, tools))
