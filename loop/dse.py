"""Stage 3: distributed iso-budget DSE via ucb-bar/evolve-flows.

The evolver is NOT in the chia tree. It lives in github.com/ucb-bar/evolve-flows
(cloned as a sibling of this repo and pip-installed -e, along with its
skydiscover submodule -- see docs/dse-setup.md); the search engine underneath
is the SkyDiscover submodule. Backend selection is YAML:
  search.type: "adaevolve"    local SkyDiscover; Gemini through an
                              OpenAI-compat endpoint -- either the public one
                              with ${GEMINI_API_KEY}, or Vertex AI with an ADC
                              bearer token (this project's route; see
                              experiments/config_adaevolve_smoke_vertex.yaml
                              and docs/dse-setup.md for the two naming traps)
  search.type: "alphaevolve"  Google Cloud AlphaEvolve API (needs a GCP
                              project + Gemini Enterprise license)
Which config the dse stage uses is C.DSE_CONFIG / $P2P_DSE_CONFIG; it
defaults to experiments/config_adaevolve.yaml.

Candidate representation: NOT free-form code. The evolver mutates one
params header (sr_params.h) that instantiates the feature spec's
`parameters` block (SR_* macros) and the port plan's `host_knobs` (HOST_*
macros), so the search can shrink a host structure to pay for the feature.
Build+run+score is done by CBP2025Node (chia_nodes/cbp2025/cbp2025_node.py),
the only simulator kit with a working host adapter today -- see the "host"
caveat below.

Constraints (loop/constraints.py). The search runs under a constraint set,
not a budget number. Storage is the only constraint today: every candidate's
storage is re-derived from its own header values, through the spec's
`state[].size_formula` and the plan's `host_storage.terms`, and a candidate
over the allowance is not built at all. Constraints are more general than
storage, and the evaluator applies whatever set it is handed; see that
module for how to add one.

Preflight. Before the search, every knob is built once at a second legal
value. A binary identical to the default build means the knob is wired to
nothing, and for a knob that costs storage that is not harmless: the search
would "save" bits the real predictor still spends, and the iso-budget result
would be fiction. So an inert storage knob stops the stage.

Verified against the real evolve-flows/skydiscover source (this module's
first draft assumed a build_fn(program) / run_fn(build_artifact, trace) /
result_mapper_fn(results) -> dict interface; the actual contract, confirmed
by reading evolve_flows/evolver/{node,bridge}.py and
skydiscover/evaluation/chia_evaluator.py, is different in three ways):

  1. Real fan-out across multiple workloads only happens through a
     ChiaEvaluator (sub)class constructed with `workloads=[...]` and passed
     as `EvolverNode.run_search(..., evaluator=...)`. The one-shot
     `run_evolver` ChiaFunction never takes an `evaluator` kwarg, so it
     always falls back to a single dummy `workloads=["default"]` -- fine
     for a smoke test, useless for real screening. This module uses the
     stateful `EvolverNode` actor, mirroring
     evolve-flows/examples/alphaevolve-champsim-simple/run_flow.py.
  2. `run_fn` is called as `run_fn(workload=trace)` -- it is NOT handed the
     build artifact. The evaluator dispatches build once, then fans out
     runs; state (the built binary) must be stashed by build and picked up
     by run within the same evaluation, hence the ContextVar in
     loop/sr_evaluator.py (same pattern as the reference
     `ChampSimEvaluator`).
  3. `result_mapper_fn` must return a `skydiscover.evaluation
     .evaluation_result.EvaluationResult`, not a plain dict, and
     skydiscover's fitness function (`get_score`) reads the
     `combined_score` metric specifically.

The evaluator itself lives in loop/sr_evaluator.py rather than here. It has
to be a module-scope class: the instance is pickled to the EvolverNode
actor, and a class nested inside a factory function gets pickled by value,
which pulls in its module's ContextVar and fails with "cannot pickle
'_contextvars.ContextVar' object". See that module's docstring. Because the
actor re-imports it by name, `loop/` must be on the actor's PYTHONPATH --
hence RUNTIME_ENV's PYTHONPATH is ".:loop", not just ".".

CAVEAT (host coverage): CBP2025Node's build/run are the only fully working
host adapter (used already by record_cbp_baseline). `hosts/champsim` and
`hosts/gem5` (hosts/__init__.py) are still NotImplementedError stubs, so
`run_dse`'s `host` argument currently only labels/namespaces output -- every
host is screened through the same cbp2025 kit and gets an identical search.
Per-host budget-bit splitting and a champsim/gem5-native evaluator are
TODO(week 3) once the stage-2 host adapters exist.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import constants as C
import constraints as K
import helpers


# Deferred imports so the rest of the loop runs without evolve-flows installed.
def _evolver_imports():
    import ray
    from evolve_flows.evolver.node import EvolverNode  # noqa
    from evolve_flows.evolver.types import EvolverInput  # noqa
    from sr_evaluator import SRParamsEvaluator  # noqa
    return ray, EvolverNode, EvolverInput, SRParamsEvaluator


def _enum_choices(range_str: str) -> list[str]:
    """Parse spec_review.promote_unsupported's 'choices: A|B|C' range format."""
    prefix = "choices:"
    body = range_str[len(prefix):] if range_str.lower().startswith(prefix) else range_str
    return [c.strip() for c in body.split("|")]


def _knob_line(macro: str, cval: str, comment: str) -> str:
    return f"#define {macro} {cval}  // {comment}"


def _render_value(p: dict, val) -> tuple[str, str]:
    """(C literal, range comment) for one knob value."""
    if p.get("type") == "bool":
        return str(val).lower(), p["range"]
    if p.get("type") == "enum":
        choices = _enum_choices(p["range"])
        try:
            idx = choices.index(str(val))
        except ValueError:
            idx = int(val) if str(val).lstrip("-").isdigit() else 0
        return str(idx), "index 0-%d (%s)" % (
            len(choices) - 1, " | ".join(f"{i}={c}" for i, c in enumerate(choices)))
    return str(val), p["range"]


def _renamed(formula: str, names: dict) -> str:
    """A formula with its variable names replaced by their macros, so the
    cost model in the header reads in the header's own terms."""
    import ast

    tree = ast.parse(formula, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in names:
            node.id = names[node.id]
    return ast.unparse(tree)


def params_header(
    spec: dict,
    port_plan: dict | None = None,
    overrides: dict | None = None,
    host_overrides: dict | None = None,
    constraint_set: list | None = None,
) -> str:
    """The one C header stage 4 mutates: the spec's parameters as SR_*
    macros, then the plan's host knobs as HOST_* macros, then the cost model.

    Stage 3 creates this file with exactly this content at the defaults, and
    every candidate is this file with values changed. The comments are for
    the proposer: the range of each value, the constraint set, and the
    formulas the evaluator costs a candidate with, written in macro names.
    The evaluator ignores comments; it re-derives every metric from the
    #define values alone."""
    lines = ["// generated from the feature spec and the port plan; DSE mutates values only"]
    for c in constraint_set or []:
        lines.append(f"// constraint: {c.describe()}. A candidate that breaks it is not built.")
    lines.append("#pragma once")
    for p in spec["parameters"]:
        cval, comment = _render_value(p, (overrides or {}).get(p["name"], p["default"]))
        lines.append(_knob_line(f"SR_{p['name'].upper()}", cval, f"range: {comment}"))
    host = (port_plan or {}).get("host_knobs") or []
    if host:
        lines.append("// host knobs: the host's own structures, at the clean tree's values by default")
        for k in host:
            val = (host_overrides or {}).get(k["name"], k["default"])
            lines.append(_knob_line(
                k.get("macro") or f"HOST_{k['name'].upper()}", str(val),
                f"range: {k['range']}; sets {k.get('host_symbol', k['name'])}"))
    names = {p["name"]: f"SR_{p['name'].upper()}" for p in spec["parameters"]}
    names.update({k["name"]: k.get("macro") or f"HOST_{k['name'].upper()}" for k in host})
    model = []
    for st in spec.get("state") or []:
        formula = st.get("size_formula")
        model.append(f"//   {st.get('name')}: "
                     + (_renamed(formula, names) if formula else str(st.get("size_bits"))))
    for t in ((port_plan or {}).get("host_storage") or {}).get("terms") or []:
        model.append(f"//   host {t.get('structure')}: {_renamed(t.get('formula', '0'), names)}")
    if model:
        lines.append("// storage_bits is the sum of these, in bits:")
        lines += model
    return "\n".join(lines) + "\n"


def params_header_from_spec(
    spec: dict, overrides: dict | None = None, port_plan: dict | None = None,
) -> str:
    """Render the spec's tunables as one C header the hosts compile in.
    The evolver mutates this file's values; the evaluator re-derives storage
    from the same values, so a candidate cannot misreport its own cost.

    `enum` parameters (spec_review.promote_unsupported's DSE knobs for
    paper ambiguities the reviewer couldn't resolve) are NOT emitted as
    their literal prose value -- most choices are free-text sentences, not
    C literals, and would fail to compile. Instead each one is rendered as
    an integer index into its '|'-delimited choices, with the mapping kept
    in the range comment so both the LLM proposer and a future host
    #if/#elif ladder can read it back.

    Kept for its callers; `params_header` is the full form."""
    return params_header(spec, port_plan, overrides)


def _port_plan(host: str, spec: dict) -> dict:
    """The port plan in force, which names the enable knob and the host knobs."""
    import plan_revision

    try:
        port_plan, _tests, _rev = plan_revision.latest(host, spec.get("feature_name"))
    except FileNotFoundError:
        port_plan = {}
    return port_plan or {}


def _feature_env(port_plan: dict, spec: dict, host: str = "cbp2025") -> dict:
    """The environment that turns the ported feature on during the search.

    Read off the port plan rather than assumed, because the enable knob's
    name is the plan's to choose and the gate already reads it from there.
    An absent plan returns an empty dict and the search then tunes a feature
    that never runs, so say so loudly instead."""
    from hosts.cbp2025 import adapter as cbp2025_adapter

    enable = (port_plan or {}).get("feature_enable") or {}
    if not enable.get("name"):
        raise SystemExit(
            f"no port plan for {host}/{spec.get('feature_name')}, so the name of "
            f"the enable knob is unknown and every candidate would be screened "
            f"with the feature off. Run --stage plan and --stage integrate first."
        )
    return cbp2025_adapter.enable_env(enable, True)


def constraint_set(budget_name: str) -> list:
    """The constraints stage 4 searches under, for one budget track.

    Storage is the only one today, and only for time: a constraint is
    {metric, comparison, allowance}, and a latency bound, a logic-cost bound
    or an IPC floor is one more entry here plus, for a pre-build metric, one
    function in constraints.STATIC_METRICS. A measured metric (any key the
    screening aggregate reports) needs no new code at all."""
    return [K.storage_constraint(budget_name, C.BUDGET_TRACKS_BITS[budget_name])]


def preflight(build, spec: dict, port_plan: dict, header: str) -> dict:
    """Prove that every knob reaches the build before the search trusts it.

    `build(header_text) -> bytes | None` compiles the search tree with that
    params header and returns the binary. The default header is built twice,
    because the whole test rests on identical sources giving identical
    bytes; this kit's builds do (checked by hand, 2026-09-22). Then each knob
    is built once at a second legal value, with every other knob at its
    default. Same bytes as the default build means nothing reads the macro.

    `blocking` lists the inert knobs that cost storage. The stage stops on
    any of them: the evaluator would credit a candidate for bits it did not
    remove, and every storage comparison after that is fiction. An inert
    knob with no storage cost only wastes proposals, so it is reported and
    the search goes on."""
    import hashlib

    def digest(binary):
        return hashlib.sha256(binary).hexdigest()[:16] if binary else None

    first, second = digest(build(header)), digest(build(header))
    report = {"default_build": first, "reproducible": bool(first) and first == second,
              "knobs": [], "blocking": [], "warnings": []}
    if not first:
        report["blocking"].append("the ported tree does not build with the generated header")
        return report
    if not report["reproducible"]:
        report["blocking"].append(
            "two builds of the same header gave different binaries, so a knob "
            "cannot be shown to reach the build; set P2P_DSE_PREFLIGHT=0 to search anyway")
        return report

    costed = set()
    for st in spec.get("state") or []:
        if st.get("size_formula"):
            costed |= {f"SR_{n.upper()}" for n in K.names_in(st["size_formula"])}
    host_names = {k["name"]: k.get("macro") or f"HOST_{k['name'].upper()}"
                  for k in port_plan.get("host_knobs") or []}
    for t in (port_plan.get("host_storage") or {}).get("terms") or []:
        costed |= {host_names[n] for n in K.names_in(t.get("formula", "0")) if n in host_names}

    for knob in K.all_knobs(spec, port_plan):
        value = K.alternate_value(knob)
        entry = {"macro": knob.macro, "origin": knob.origin, "default": knob.default,
                 "tested": value, "costs_storage": knob.macro in costed}
        if value is None:
            entry["result"] = "no second legal value"
            report["warnings"].append(f"{knob.macro}: no second legal value to test")
            report["knobs"].append(entry)
            continue
        feature = {k.name: k.default for k in K.feature_knobs(spec)}
        host = {k.name: k.default for k in K.host_knobs(port_plan)}
        (feature if knob.origin == "feature" else host)[knob.name] = value
        variant = digest(build(params_header(spec, port_plan, feature, host)))
        if variant is None:
            entry["result"] = "does not build"
            report["warnings"].append(
                f"{knob.macro} = {value} does not build, though its range allows it")
        elif variant == first:
            entry["result"] = "inert"
            (report["blocking"] if entry["costs_storage"] else report["warnings"]).append(
                f"{knob.macro} = {value} builds the same binary as {knob.default}: "
                f"nothing reads it"
                + (", yet the evaluator would credit its storage" if entry["costs_storage"]
                   else ""))
        else:
            entry["result"] = "live"
        report["knobs"].append(entry)
    return report


def run_dse(
    host: str, spec: dict, budget_name: str, config_path: str,
    screening_list_path: Path | str = C.SCREENING_LIST,
) -> dict:
    ray, EvolverNode, EvolverInput, SRParamsEvaluator = _evolver_imports()
    screening = helpers.load_trace_list(screening_list_path)
    if not screening:
        raise SystemExit(
            f"{screening_list_path} has no trace entries yet (still the "
            "TODO(week 1) placeholder) -- populate it before running DSE"
        )
    output_dir = str(C.OUT_DIR / "dse" / host)
    os.makedirs(output_dir, exist_ok=True)

    port_plan = _port_plan(host, spec)
    feature_env = _feature_env(port_plan, spec, host)
    constraints = constraint_set(budget_name)
    initial = params_header(spec, port_plan, constraint_set=constraints)
    start = K.check_static(initial, spec, port_plan, constraints)
    summary = {
        "host": host,
        "budget": budget_name,
        "constraints": [c.as_dict() for c in constraints],
        "host_knobs": len(port_plan.get("host_knobs") or []),
        # The defaults are the paper's feature on the unmodified host. At a
        # tight allowance they do not fit, and the search starts infeasible:
        # it has to shrink something before any candidate scores.
        "initial": {"feasible": start.ok, "metrics": start.metrics,
                    "breakdown": start.breakdown, "errors": start.errors,
                    "violations": start.violations},
    }
    if start.errors:
        return {**summary, "status": "header_invalid", "error": start.message()}

    # A copy of the ported tree. Not the pristine checkout, because
    # sr_params.h means nothing until stage 3 has written a predictor that
    # includes it, and screening the pristine kit would build the baseline
    # once per candidate and report that no parameter matters. Not the
    # ported tree itself either, because the evolver overwrites that header
    # on every iteration and the port the gate promoted has to stay on disk
    # as the gate saw it.
    from chia.base.ChiaFunction import get
    from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
    from hosts.cbp2025 import adapter as cbp2025_adapter

    search_root = cbp2025_adapter.dse_tree()
    summary["search_root"] = search_root
    summary["screening_traces"] = len(screening)

    if C.DSE_PREFLIGHT:
        def build(header_text: str):
            result = get(CBP2025Node.build.options(
                resources={C.CBP2025_HOST_RESOURCE: 1.0}
            ).chia_remote(search_root, {"sr_params.h": header_text.encode()},
                          C.BUILD_TIMEOUT_S, feature_env))
            return result.binary if result.success else None

        summary["preflight"] = preflight(build, spec, port_plan, initial)
        if summary["preflight"]["blocking"]:
            return {**summary, "status": "preflight_failed",
                    "error": "; ".join(summary["preflight"]["blocking"])}

    evaluator = SRParamsEvaluator(
        search_root, screening, output_dir,
        C.BUILD_TIMEOUT_S, C.RUN_TIMEOUT_S,
        feature_env=feature_env,
        spec=spec, port_plan=port_plan,
        constraints=[c.as_dict() for c in constraints],
    )
    config_content = Path(config_path).read_text()
    evolver_input = EvolverInput(
        config_path=config_path,
        initial_program=initial,
        config_content=config_content,
    )

    actor_name = f"p2p-dse-evolver-{host}"
    try:
        ray.kill(ray.get_actor(actor_name))
    except ValueError:
        pass  # no stale actor from a previous run
    evolver = EvolverNode.options(
        name=actor_name, lifetime="detached", resources={"evolver": 1.0},
    ).remote()
    try:
        result = ray.get(
            evolver.run_search.remote(
                evolver_input,
                build_fn=evaluator._build,
                run_fn=evaluator._run,
                result_mapper_fn=evaluator._map_results,
                evaluator=evaluator,
            )
        )
    finally:
        evaluator.close()
        ray.kill(evolver)

    best = K.check_static(result.best_program or "", spec, port_plan, constraints)
    return {
        **summary,
        "best_program": result.best_program,
        "best_metrics": result.best_metrics,
        # Re-derived here, not read off the search's own record, so the
        # summary's storage figure is one nobody could have misreported.
        "best_storage": {"feasible": best.ok, "metrics": best.metrics,
                         "breakdown": best.breakdown},
        "iterations": result.iteration_count,
        "status": result.terminal_status,
        "error": result.error_message,
    }


def promote_finalists(dse_result: dict, top_k: int = C.DSE_PROMOTE_TOP_K) -> list:
    """Full 105-trace validation of the screening winners.
    TODO(week 3): pull the top-k population entries from
    dse_result / metrics_log_path and fan out over FULL_LIST."""
    raise NotImplementedError


if __name__ == "__main__":
    print(json.dumps(list(C.BUDGET_TRACKS_BITS), indent=2))
