#!/usr/bin/env python3
"""Can the loop's LLM backend reach the CBP2025 checkout through chia?

The cheapest question stage 2 and stage 3 both depend on, asked on its own:
one prompt, one MCP bash tool pinned to the node that owns the checkout,
and an answer that can only be produced by running a command there. It
spends a few thousand tokens and takes a minute, instead of discovering the
same failure forty minutes into a planning run.

    chia job submit -- python "$(pwd)/loop/tests/llm_cluster_smoke.py"

Backend is whatever P2P_LLM_BACKEND says (default antigravity, which is the
backend whose spend lands on the project's GCP budget).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "loop")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ray
from chia.base.tools.BashTool import BashTool

import constants as C
from llm import make_llm, run_llm

PROMPT = (
    "You have one shell tool, rooted at a CBP2025 branch-predictor simulator "
    "checkout. Run exactly these two commands and report what they printed:\n"
    "  1. git rev-parse HEAD\n"
    "  2. ls\n"
    "Then answer, on the last line and nothing else on it:\n"
    "REVISION=<the 40-character commit hash>"
)


def main() -> int:
    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)
    print(f"[llm-smoke] backend={C.LLM_BACKEND} work_dir={C.CBP2025_ROOT}")

    bash = BashTool(
        name="cbp2025_bash",
        work_dir=C.CBP2025_ROOT,
        timeout_seconds=C.BASH_TOOL_TIMEOUT_S,
        task_options={"resources": {C.CBP2025_HOST_RESOURCE: 0.1}},
    )
    try:
        llm = make_llm(C.LLM_BACKEND, [bash], resume=False)
        resp = run_llm(llm, PROMPT, [bash])
    finally:
        bash.stop()

    print(f"[llm-smoke] usage: {getattr(resp, 'usage', None)}")
    print("[llm-smoke] ---- result ----")
    print(resp.result)
    print("[llm-smoke] ---- stream (tail) ----")
    print((resp.stream_result or "")[-4000:])

    hit = re.search(r"REVISION=([0-9a-f]{40})", resp.result or "")
    tool_calls = len(re.findall(r"\[Tool Call: ", resp.stream_result or ""))
    checks = [
        ("the backend answered", bool(resp.result)),
        ("it called a tool", tool_calls > 0),
        ("it read a real commit hash off the checkout", hit is not None),
    ]
    print("\n[llm-smoke] checks")
    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if hit:
        print(f"[llm-smoke] revision: {hit.group(1)}")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
