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
`parameters` block plus the host budget split. Build+run+score is done by
CBP2025Node (chia_nodes/cbp2025/cbp2025_node.py), the only simulator kit
with a working host adapter today -- see the "host" caveat below.

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


def params_header_from_spec(spec: dict, overrides: dict | None = None) -> str:
    """Render the spec's tunables as one C header the hosts compile in.
    The evolver mutates this file's values; the gate re-derives storage
    from the same values, so a candidate cannot lie about its budget.

    `enum` parameters (spec_review.promote_unsupported's DSE knobs for
    paper ambiguities the reviewer couldn't resolve) are NOT emitted as
    their literal prose value -- most choices are free-text sentences, not
    C literals, and would fail to compile. Instead each one is rendered as
    an integer index into its '|'-delimited choices, with the mapping kept
    in the range comment so both the LLM proposer and a future host
    #if/#elif ladder can read it back."""
    lines = ["// generated from feature spec; DSE mutates values only", "#pragma once"]
    for p in spec["parameters"]:
        val = (overrides or {}).get(p["name"], p["default"])
        if p["type"] == "bool":
            cval = str(val).lower()
            range_comment = p["range"]
        elif p["type"] == "enum":
            choices = _enum_choices(p["range"])
            try:
                idx = choices.index(str(val))
            except ValueError:
                idx = int(val) if str(val).lstrip("-").isdigit() else 0
            cval = str(idx)
            range_comment = "index 0-%d (%s)" % (
                len(choices) - 1,
                " | ".join(f"{i}={c}" for i, c in enumerate(choices)),
            )
        else:
            cval = str(val)
            range_comment = p["range"]
        lines.append(f"#define SR_{p['name'].upper()} {cval}  // range: {range_comment}")
    return "\n".join(lines) + "\n"


def _feature_env(host: str, spec: dict) -> dict:
    """The environment that turns the ported feature on during the search.

    Read off the port plan rather than assumed, because the enable knob's
    name is the plan's to choose and the gate already reads it from there.
    An absent plan returns an empty dict and the search then tunes a feature
    that never runs, so say so loudly instead."""
    import plan_revision
    from hosts.cbp2025 import adapter as cbp2025_adapter

    try:
        port_plan, _tests, _rev = plan_revision.latest(host, spec.get("feature_name"))
    except FileNotFoundError:
        port_plan = {}
    enable = (port_plan or {}).get("feature_enable") or {}
    if not enable.get("name"):
        raise SystemExit(
            f"no port plan for {host}/{spec.get('feature_name')}, so the name of "
            f"the enable knob is unknown and every candidate would be screened "
            f"with the feature off. Run --stage plan and --stage integrate first."
        )
    return cbp2025_adapter.enable_env(enable, True)


def run_dse(
    host: str, spec: dict, budget_name: str, config_path: str,
    screening_list_path: Path | str = C.SCREENING_LIST,
) -> dict:
    ray, EvolverNode, EvolverInput, SRParamsEvaluator = _evolver_imports()
    budget_bits = C.BUDGET_TRACKS_BITS[budget_name]  # TODO(week 3): per-host split; unused today
    screening = helpers.load_trace_list(screening_list_path)
    if not screening:
        raise SystemExit(
            f"{screening_list_path} has no trace entries yet (still the "
            "TODO(week 1) placeholder) -- populate it before running DSE"
        )
    output_dir = str(C.OUT_DIR / "dse" / host)
    os.makedirs(output_dir, exist_ok=True)

    # A copy of the ported tree. Not the pristine checkout, because
    # sr_params.h means nothing until stage 3 has written a predictor that
    # includes it, and screening the pristine kit would build the baseline
    # once per candidate and report that no parameter matters. Not the
    # ported tree itself either, because the evolver overwrites that header
    # on every iteration and the port the gate promoted has to stay on disk
    # as the gate saw it.
    from hosts.cbp2025 import adapter as cbp2025_adapter

    search_root = cbp2025_adapter.dse_tree()
    evaluator = SRParamsEvaluator(
        search_root, screening, output_dir,
        C.BUILD_TIMEOUT_S, C.RUN_TIMEOUT_S,
        feature_env=_feature_env(host, spec),
    )
    initial = params_header_from_spec(spec)
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

    return {
        "host": host,
        "budget": budget_name,
        "budget_bits": budget_bits,
        "search_root": search_root,
        "screening_traces": len(screening),
        "best_program": result.best_program,
        "best_metrics": result.best_metrics,
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
