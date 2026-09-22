#!/usr/bin/env python3
"""End-to-end smoke test of stage 3 (integrate), on a fixture host.

What it proves, and the order it proves it in:

1. the LLM backend can be called through chia at all, with an MCP bash tool
   attached and a resumable session behind it;
2. the agent's edits land in the host checkout;
3. the checkout still compiles;
4. the host's own test suite runs and its result reaches the gate;
5. the deterministic gate judges the port instead of the agent judging itself;
6. a gate rejection comes back as a debug turn on the *same* session, and that
   turn's edits reach the tree.

It does all of that against `fixtures/toyhost` -- a few hundred lines of C++
that build in a second -- so a stage-3 regression is caught in a couple of
minutes rather than after a cluster bring-up, a simulator build, and a trace
download. It is not a test of whether an agent can port sR into ChampSim.

The stage code under test is the real one: `adopt_a_paper_loop.integrate`,
reached with a `HostAdapter` pointed at the fixture. Nothing here reimplements
the loop.

Run it:

    python loop/tests/integrate_smoke.py                 # ~5-10 minutes, calls the LLM
    python loop/tests/integrate_smoke.py --no-force-first-fail
    python loop/tests/integrate_smoke.py --attempts 5 --model gemini-3.1-pro-high

The backend is whatever `P2P_LLM_BACKEND` says, which defaults to antigravity
like the rest of the loop -- deliberately, because that is the backend whose
spend lands on the project's GCP budget. `--backend claude` works and needs no
credential setup, but it bills the machine's signed-in Anthropic account
instead, so it is not the default even though it is the easiest to reach.

It is deliberately not named test_*.py: pytest must not collect it, because it
spends real tokens and needs a working LLM backend.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
LOOP_DIR = TESTS_DIR.parent
REPO_ROOT = LOOP_DIR.parent
for _path in (str(TESTS_DIR), str(LOOP_DIR), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# The loop reads its knobs at import time, so the fixture's values have to be
# in the environment before `constants` is imported. setdefault, not
# assignment: an explicit P2P_* from the caller still wins.
#
# P2P_LLM_BACKEND is deliberately absent: the smoke test uses whatever backend
# the loop itself is configured for, so what it exercises is the path that will
# actually run, on the budget that will actually pay for it.
os.environ.setdefault("P2P_FEATURE_NAME", "tinysc")
os.environ.setdefault("P2P_INTEGRATION_ATTEMPTS", "3")

HOST = "toy"
BASELINE_KEY = "smoke"  # which recorded baseline to compare against


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--attempts", type=int, default=None,
                    help="gate attempts before giving up (default: P2P_INTEGRATION_ATTEMPTS)")
    ap.add_argument("--backend", default=None, help="claude | antigravity | opencode")
    ap.add_argument("--model", default=None, help="backend model id override")
    ap.add_argument("--work-dir", default=None,
                    help="where to materialize the host copy (default: out/toyhost_<timestamp>)")
    ap.add_argument("--no-force-first-fail", dest="force_first_fail",
                    action="store_false",
                    help="do not inject a first-attempt gate failure; the debug "
                         "turn is then only exercised if the agent genuinely fails")
    ap.set_defaults(force_first_fail=True)
    return ap.parse_args()


def apply_overrides(args: argparse.Namespace) -> None:
    """Env first, then import constants, so the overrides are visible."""
    if args.attempts is not None:
        os.environ["P2P_INTEGRATION_ATTEMPTS"] = str(args.attempts)
    if args.backend:
        os.environ["P2P_LLM_BACKEND"] = args.backend
    if args.model:
        # Mirrors constants.LLM_BACKEND's own default. It cannot be read from
        # there: constants must not be imported until the env is settled.
        backend = os.environ.get("P2P_LLM_BACKEND", "antigravity")
        os.environ[{
            "claude": "P2P_CLAUDE_MODEL",
            "antigravity": "P2P_ANTIGRAVITY_MODEL",
            "opencode": "P2P_OPENCODE_MODEL",
        }[backend]] = args.model


def tree_diff(work_dir: Path, fixture: Path) -> str:
    """What the agent changed. `diff -ru` rather than git: the host copy is a
    plain directory, which is also what a real simulator checkout looks like
    after the loop has been at it."""
    proc = subprocess.run(
        ["diff", "-ru", "--exclude=build", str(fixture), str(work_dir)],
        capture_output=True, text=True,
    )
    return proc.stdout or "(no changes)"


# Every backend logs tool calls in its own vocabulary, and two shapes have
# shown up so far:
#   claude: one entry per MCP tool, "mcp__<server>__<server>_run_command"
#           (doubly prefixed -- FastMCP registers the command as
#           "<tool>_run_command" and the server itself as "<tool>")
#   agy:    a single generic "call_mcp_tool", with the server in its Args as
#           {"ServerName": "toy_bash", "ToolName": "toy_bash_run_command"}
# Rather than enumerate each backend's *native* tools -- a list that drifts
# every time a CLI adds one -- only the MCP shapes are named, and everything
# else is counted as "not through the MCP server".
MCP_SERVER = f"{HOST}_bash"
_TOOL_CALL = re.compile(
    r"\[Tool Call: ([A-Za-z0-9_]+)\]\n(?:Args: (.*))?"
)


def tool_census(dump) -> tuple[dict, int, int]:
    """Count tool calls by name; return (census, mcp_calls, total_calls).

    Stage 3's premise is that the agent reaches the host only through tools the
    loop handed it: on the cluster the host checkout lives in a different
    container from the LLM, so an edit made with the backend's own file tool
    lands nowhere. The fixture run has both on one machine, so those edits do
    land and the gate passes anyway -- which is exactly why this is counted
    rather than inferred from the verdict."""
    census: dict[str, int] = {}
    mcp = total = 0
    for path in sorted(dump.dir.glob(f"{dump.prefix}integrate_{HOST}_*.md")):
        for name, args in _TOOL_CALL.findall(path.read_text()):
            # agy routes every MCP tool through one generic call; the server it
            # reached is only visible in the arguments.
            through_mcp = name.startswith(f"mcp__{MCP_SERVER}") or (
                name == "call_mcp_tool" and f'"ServerName": "{MCP_SERVER}"' in args
            )
            label = f"{name} -> {MCP_SERVER}" if through_mcp and args else name
            census[label] = census.get(label, 0) + 1
            total += 1
            mcp += through_mcp
    return census, mcp, total


def main() -> int:
    args = parse_args()
    apply_overrides(args)

    import ray

    import constants as C
    import helpers
    from adopt_a_paper_loop import HostAdapter, integrate
    from toy_host import SPEC_PATH, ToyHost

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = Path(args.work_dir) if args.work_dir else C.OUT_DIR / f"toyhost_{stamp}"

    print(f"[smoke] backend={C.LLM_BACKEND} attempts={C.NUM_INTEGRATION_ATTEMPTS} "
          f"force_first_fail={args.force_first_fail}")
    print(f"[smoke] host copy: {work_dir}")

    host = ToyHost(work_dir, force_first_fail=args.force_first_fail)
    host.materialize()
    # The prompt inlines the spec and both plan documents, so nothing has to
    # travel into the checkout for the agent to read.
    spec = json.loads(SPEC_PATH.read_text())

    baseline = host.record_baseline()
    print(f"[smoke] baseline: mpki={baseline['mpki']} ipc={baseline['ipc']} "
          f"(bias workload mpki={baseline['bias']['mpki']})")
    # The agent must not see the pristine build: it has to compile its own.
    shutil.rmtree(work_dir / "build", ignore_errors=True)

    # A local single-node Ray carrying the resource tokens cluster.yaml would
    # otherwise provide. Every backend's credential token is advertised rather
    # than just the selected one's: `llm.llm_resources` picks the token from the
    # LLM object, which does not exist yet here, and a token nothing requests
    # costs nothing. Getting this wrong does not raise -- the prompt task would
    # sit in Ray's pending queue forever waiting for a resource no node offers.
    ray.init(
        resources={"llm": 1, "antigravity_creds": 1, "opencode_creds": 1, HOST: 1},
        ignore_reinit_error=True,
        log_to_driver=False,
    )

    adapter = HostAdapter(
        name=HOST,
        work_dir=str(work_dir),
        notes=host.notes(),
        resources={HOST: 0.1},
        baseline=lambda: baseline,
        run_gate=host.run_gate,
    )

    dump = helpers.Dumper()
    try:
        result = integrate(
            dump, spec, HOST, BASELINE_KEY,
            port_plan=host.port_plan, test_plan=host.test_plan, adapter=adapter,
        )
    finally:
        ray.shutdown()

    diff = tree_diff(work_dir, Path(__file__).resolve().parent / "fixtures" / "toyhost")
    dump.text(f"integrate_{HOST}_diff.patch", diff)
    census, mcp_calls, total_calls = tool_census(dump)
    native_calls = total_calls - mcp_calls

    summary = {
        "status": result["status"],
        "attempts": result["attempts"],
        "debug_turns": max(0, result["attempts"] - 1),
        "tool_census": census,
        "mcp_tool_calls": mcp_calls,
        "native_tool_calls": native_calls,
        "gate_history": host.history,
        "work_dir": str(work_dir),
        "artifacts": str(dump.dir),
    }
    dump.json(f"integrate_{HOST}_smoke.json", summary)

    print("\n[smoke] gate history")
    for entry in host.history:
        verdict = "PASS" if entry["passed"] else "FAIL"
        print(f"  attempt {entry['attempt']}: {verdict}")
        for reason in entry["reasons"]:
            print(f"      - {reason.splitlines()[0][:160]}")
        # Shortfalls never block, so they never appear as reasons. Printing
        # them here is the only way a passing run reports one at all.
        for warning in entry.get("warnings", []):
            print(f"      ~ {warning.splitlines()[0][:160]}")

    checks = [
        ("agent called the MCP bash tool", mcp_calls > 0),
        ("the checkout changed", diff != "(no changes)"),
        ("a debug turn ran", result["attempts"] > 1),
        ("the gate passed", result["status"] == "passed"),
    ]
    if not args.force_first_fail:
        # Without injection a first-try success is the good outcome, so a run
        # with no debug turn must not be scored as a failure.
        checks = [c for c in checks if c[0] != "a debug turn ran"]

    print("\n[smoke] tool calls")
    for tool, count in sorted(census.items(), key=lambda kv: -kv[1]):
        print(f"  {count:3d}  {tool}")

    print("\n[smoke] checks")
    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if native_calls:
        # Not a failure of this run: on one machine those edits are correct,
        # and the gate confirms it. It is a warning about the cluster, where
        # the same call would edit the wrong container's filesystem.
        print(f"\n[smoke] warning: {native_calls} of {total_calls} tool calls did "
              f"not go through the {MCP_SERVER} MCP server.\n"
              f"  Here that is harmless: the host checkout is on this machine. "
              f"On the cluster it is\n"
              f"  in another container, so any of those that wrote files would "
              f"have written nothing.\n"
              f"  llm.make_llm denies the built-in tools for the opencode "
              f"backend but not for the others.")
    print(f"\n[smoke] artifacts: {dump.dir}")
    print(f"[smoke] host copy: {work_dir}")

    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
