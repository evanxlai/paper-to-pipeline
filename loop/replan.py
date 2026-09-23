"""Stage 3's escalation, answered inside the job: re-plan, then integrate again.

An escalation is stage 3 saying that a frozen value in the plan is wrong and
that only stage 2 may change it (docs/stages.md). It used to end the job with
status `needs_replan`, and a person then submitted stage 2 and stage 3 again by
hand. Nothing in that hand-off needed the person. Stage 2 already reads every
open escalation into the planner prompt and marks it answered by the plan it
writes. So the loop now does the re-plan itself, up to
`C.ESCALATION_REPLANS` times per host, and carries on.

Three things differ between one round and the next, and each has a rule here.

Artifact names. The driver's Dumper has one prefix per job, and every stage-3
artifact name repeats from round to round (`gate_<host>_0.json`,
`integrate_<host>_0.md`). Round N therefore writes through
`dump.child("replan<N>")`, and its plan run does too. That also keeps apart the
stamps stage 2 writes when it retires old revisions and answers escalations.
Round 0 writes through the job's own Dumper, so a job with no escalation
writes exactly the names it always did.

The port tree. `docs/cbp2025-runbook.md` gave the person the rule: keep the
port for a re-plan that changed the measurement, and start over for one that
changed the design. `design_changes` is that rule in code. It compares the
fields of the port plan that say where and how the feature is built. Any
difference there starts the next round from a clean copy of the host. The
comparison leans towards starting over, because a port built for the old design
can pass a gate built for the new one only by accident, and a clean copy costs
time and nothing else.

A refused re-plan. Stage 2 raises SystemExit when its checks refuse the plan,
and a backend failure can raise anything. Either one ends the rounds for this
host with status `replan_failed` and the reason recorded. The open
escalations stay open, because stage 2 marks them answered only after it
writes a plan. The next run, by hand or not, sees them again.
"""

from __future__ import annotations

from typing import Callable, Optional

import constants as C


def _hook_sites(port_plan: dict) -> set:
    return {
        (h.get("file"), h.get("symbol"), h.get("action"))
        for h in port_plan.get("hook_points") or []
    }


def _resolution_status(port_plan: dict) -> dict:
    return {
        r.get("spec_pointer"): r.get("status")
        for r in port_plan.get("interface_resolutions") or []
    }


def _enable(port_plan: dict) -> tuple:
    fe = port_plan.get("feature_enable") or {}
    return fe.get("name"), fe.get("macro"), fe.get("binding")


def _knob_macros(port_plan: dict) -> set:
    return {(k.get("macro"), k.get("binding")) for k in port_plan.get("knobs") or []}


def _host_knob_sites(port_plan: dict) -> set:
    return {
        (k.get("macro"), k.get("file"), k.get("host_symbol"))
        for k in port_plan.get("host_knobs") or []
    }


# The port plan's design, field by field. Prose (a hook point's `change`, a
# resolution's `rationale`) is left out on purpose: a re-plan rewords it
# freely, and a reworded sentence is not a different port. What is compared
# is what the code the agent wrote depends on: the structure, which files and
# symbols it hooks, how each host interface is met, the enable switch, and the
# macros stage 4 rewrites.
DESIGN = {
    "structure.choice": lambda p: (p.get("structure") or {}).get("choice"),
    "hook_points": _hook_sites,
    "interface_resolutions.status": _resolution_status,
    "feature_enable": _enable,
    "knobs": _knob_macros,
    "host_knobs": _host_knob_sites,
}


def design_changes(old_port: dict, new_port: dict) -> list[str]:
    """The parts of the port's design the re-plan changed, by name.

    An empty list means that only the measurement changed: the tests, their
    commands, thresholds or traces. Then the port the agent already wrote is
    still a port of this plan, and the next round keeps it."""
    return [name for name, read in DESIGN.items() if read(old_port) != read(new_port)]


def integrate_with_replans(
    dump,
    port_plan: dict,
    test_plan: dict,
    *,
    integrate: Callable[..., dict],
    plan: Callable[..., tuple[dict, dict]],
    save_port: Optional[Callable[..., None]] = None,
    replans: Optional[int] = None,
) -> dict:
    """Integrate one host, and re-plan after each escalation, within budget.

    The callables are the driver's own stages, bound to one host, so this
    module holds no host logic and a test can drive it with fakes:

    - `integrate(dump, port_plan, test_plan, fresh)` runs stage 3 and returns
      its result. `fresh=None` means the host's own default
      (`P2P_<HOST>_PORT_FRESH`). True and False override it.
    - `plan(dump)` runs stage 2 and returns the new pair.
    - `save_port(dump)`, if given, writes the port tree's diff. It runs after
      every round, before the next one can replace the tree, because the port
      an escalation refused is the one a reader most needs to see.

    Returns the last round's result with two more keys. `replans` is how many
    re-plans ran, a refused one included. `rounds` has one entry per round:
    its status, and for a round that escalated, what the re-plan did about
    it."""
    budget = C.ESCALATION_REPLANS if replans is None else replans
    rounds: list[dict] = []
    round_dump = dump
    fresh: Optional[bool] = None
    result: dict = {}
    for n in range(budget + 1):
        result = integrate(round_dump, port_plan, test_plan, fresh)
        if save_port is not None:
            save_port(round_dump)
        entry = {
            "round": n,
            "artifacts": round_dump.prefix,
            "status": result.get("status"),
            "attempts": result.get("attempts"),
            **({"escalation": result["escalation"]} if result.get("escalation") else {}),
        }
        rounds.append(entry)
        if result.get("status") != "needs_replan" or n == budget:
            break

        round_dump = dump.child(f"replan{n + 1}")
        print(f"[replan] stage 3 escalated "
              f"{(result.get('escalation') or {}).get('pointer')}; re-running stage 2 "
              f"(re-plan {n + 1} of {budget}), artifacts under {round_dump.prefix}")
        try:
            new_port, new_tests = plan(round_dump)
        except (SystemExit, Exception) as e:  # noqa: BLE001
            # SystemExit is how stage 2 refuses a plan, and it is not an
            # Exception. Caught either way so the job goes on to the next
            # host and writes its summary, rather than losing both to one
            # host's planner.
            entry["replan"] = {"error": f"{type(e).__name__}: {e}"}
            result = {**result, "status": "replan_failed",
                      "replan_error": entry["replan"]["error"]}
            print(f"[replan] stage 2 did not produce a plan: {entry['replan']['error']}")
            break
        changes = design_changes(port_plan, new_port)
        fresh = bool(changes)
        entry["replan"] = {
            "artifacts": round_dump.prefix,
            "design_changes": changes,
            "port_tree": "fresh" if fresh else "kept",
        }
        port_plan, test_plan = new_port, new_tests

    # A refused re-plan still counts: it ran, and it is what ended the rounds.
    return {**result, "replans": sum("replan" in r for r in rounds), "rounds": rounds}
