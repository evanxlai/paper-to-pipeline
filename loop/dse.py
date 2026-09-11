"""Stage 3: distributed iso-budget DSE via ucb-bar/evolve-flows.

The evolver is NOT in the chia tree. It lives in github.com/ucb-bar/evolve-flows
(pip install -e it next to chia); the search engine underneath is the
SkyDiscover submodule. Backend selection is YAML:
  search.type: "adaevolve"    local SkyDiscover; Gemini through the
                              OpenAI-compat endpoint, api_key ${GEMINI_API_KEY}
  search.type: "alphaevolve"  Google Cloud AlphaEvolve API (needs a GCP
                              project + Gemini Enterprise license)
See experiments/config_adaevolve.yaml.

Candidate representation: NOT free-form code. The evolver mutates one
params header (sr_params.h) that instantiates the feature spec's
`parameters` block plus the host budget split. The three-function
evaluator then does: build once per candidate, fan runs across the
screening traces via CHIA scheduling, map results to a score.

CAVEAT (from research, unverified internals): `ChiaEvaluator` comes from
`skydiscover.evaluation.chia_evaluator` and its exact constructor and
EvaluationResult schema were not fetched. The wiring below follows the
published example (evolve-flows examples/alphaevolve-champsim-simple,
champsim_evaluator.py + run_flow.py) and must be reconciled against that
file before first run. TODO(week 3).
"""

from __future__ import annotations

import json
from pathlib import Path

from chia.base.ChiaFunction import get

import constants as C

# Deferred imports so the rest of the loop runs without evolve-flows installed.
def _evolver_imports():
    from evolve_flows.evolver.node import run_evolver, EvolverNode  # noqa
    from evolve_flows.evolver.types import EvolverInput  # noqa
    return run_evolver, EvolverNode, EvolverInput


def params_header_from_spec(spec: dict, overrides: dict | None = None) -> str:
    """Render the spec's tunables as one C header the hosts compile in.
    The evolver mutates this file's values; the gate re-derives storage
    from the same values, so a candidate cannot lie about its budget."""
    lines = ["// generated from feature spec; DSE mutates values only", "#pragma once"]
    for p in spec["parameters"]:
        val = (overrides or {}).get(p["name"], p["default"])
        cval = str(val).lower() if p["type"] == "bool" else str(val)
        lines.append(f"#define SR_{p['name'].upper()} {cval}  // range: {p['range']}")
    return "\n".join(lines) + "\n"


def make_evaluator_fns(host: str, spec: dict, budget_bits: int, screening_traces: list):
    """The evolver's three-function interface: build_fn, run_fn,
    result_mapper_fn. Build failures score 0.0 (evolver convention)."""

    def build_fn(candidate_program: str):
        # candidate_program is the mutated sr_params.h content.
        from hosts import build_with_params  # hosts/__init__.py dispatch, TODO
        return build_with_params(host, candidate_program)

    def run_fn(build_artifact, trace: str):
        from hosts import run_one  # noqa
        return run_one(host, build_artifact, trace)

    def result_mapper_fn(run_results: list) -> dict:
        from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
        agg = get(CBP2025Node.aggregate.chia_remote(list(run_results)))
        mpki = agg.get(C.DSE_SCREEN_METRIC)
        if mpki is None or agg["n"] < len(screening_traces) * 0.9:
            return {"score": 0.0, "agg": agg}
        # Lower MPKI is better; evolvers maximize.
        return {"score": 1000.0 / (1.0 + mpki), "agg": agg, "mpki": mpki}

    return build_fn, run_fn, result_mapper_fn


def run_dse(host: str, spec: dict, budget_name: str, config_path: str) -> dict:
    run_evolver, EvolverNode, EvolverInput = _evolver_imports()
    budget_bits = C.BUDGET_TRACKS_BITS[budget_name]
    screening = [
        t.strip() for t in Path(C.SCREENING_LIST).read_text().splitlines() if t.strip()
    ]
    build_fn, run_fn, mapper = make_evaluator_fns(host, spec, budget_bits, screening)
    initial = params_header_from_spec(spec)
    result = get(
        run_evolver.chia_remote(
            EvolverInput(config_path=config_path, initial_program=initial),
            build_fn,
            run_fn,
            mapper,
        )
    )
    return {
        "host": host,
        "budget": budget_name,
        "best_program": result.best_program,
        "best_metrics": result.best_metrics,
        "iterations": result.iteration_count,
        "status": result.terminal_status,
    }


def promote_finalists(dse_result: dict, top_k: int = C.DSE_PROMOTE_TOP_K) -> list:
    """Full 105-trace validation of the screening winners.
    TODO(week 3): pull the top-k population entries from
    dse_result / metrics_log_path and fan out over FULL_LIST."""
    raise NotImplementedError


if __name__ == "__main__":
    print(json.dumps(list(C.BUDGET_TRACKS_BITS), indent=2))
