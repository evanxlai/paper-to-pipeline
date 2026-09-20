"""The ChiaEvaluator that scores one sr_params.h candidate for stage-3 DSE.

Overlays the candidate header onto the cbp2025 checkout, builds it, fans the
screening traces out, and aggregates to the DSE screening metric.

This lives in its own module, imported lazily by `dse.run_dse`, for two
reasons -- the second one non-obvious and load-bearing:

 1. Importing it requires skydiscover/evolve-flows, which are not on PyPI and
    not in this repo (see docs/dse-setup.md). The rest of the loop must keep
    running without them installed, so nothing imports this at module scope.

 2. The evaluator instance is pickled to the `EvolverNode` Ray actor:
    `evolve_flows.evolver.bridge` registers it in `_EVALUATOR_REGISTRY` and
    generates a shim file that calls `evaluator.evaluate_program(source)`.
    cloudpickle pickles a class defined at *module scope* by reference, but a
    class defined inside a factory function by *value* -- and pickling by
    value drags the module-level `_eval_binary` ContextVar below into the
    payload, which dies with:

        TypeError: cannot pickle '_contextvars.ContextVar' object

    So this class must stay at module scope. The reference evaluator,
    evolve-flows/examples/alphaevolve-champsim-simple/champsim_evaluator.py,
    is module-scope with a module-level ContextVar for exactly this reason.
    Note this also means `loop/` must be on the PYTHONPATH of the actor (not
    just the repo root), since the actor re-imports this module by name.
"""

from __future__ import annotations

import contextvars
import json
import os

import constants as C
from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
from skydiscover.evaluation.chia_evaluator import ChiaEvaluator
from skydiscover.evaluation.evaluation_result import EvaluationResult

# Per-evaluation binary handoff between build and run. ChiaEvaluator calls
# build_fn and run_fn separately with no shared argument -- run_fn is invoked
# as run_fn(workload=trace) and never receives the build artifact -- so build
# stashes the binary here and run picks it up. Safe because
# ChiaEvaluator.evaluate_batch is deliberately sequential ("to prevent actor
# state races"), and because each asyncio task gets its own context copy.
_eval_binary: contextvars.ContextVar[bytes | None] = contextvars.ContextVar(
    "_eval_binary", default=None
)


class SRParamsEvaluator(ChiaEvaluator):
    def __init__(
        self,
        cbp_root: str,
        screening_traces: list,
        output_dir: str,
        build_timeout_s: int,
        run_timeout_s: int,
    ):
        self._cbp_root = cbp_root
        self._screening_traces = list(screening_traces)
        self._build_timeout_s = build_timeout_s
        self._run_timeout_s = run_timeout_s
        super().__init__(
            build_fn=self._build,
            run_fn=self._run,
            result_mapper_fn=self._map_results,
            workloads=self._screening_traces,
            output_dir=output_dir,
            timeout=run_timeout_s,
        )

    def _build(self, program_solution: str):
        # program_solution is the evolver's mutated sr_params.h content;
        # overlaying just this file assumes the checkout's predictor already
        # #includes "sr_params.h" (stage-2 integration's job -- until then the
        # header is inert and every candidate scores identically).
        return CBP2025Node.build.chia_remote(
            self._cbp_root,
            {"sr_params.h": program_solution.encode()},
            self._build_timeout_s,
        )

    async def _dispatch_build(self, program_solution, label):
        _eval_binary.set(None)
        result = await super()._dispatch_build(program_solution, label)
        if isinstance(result, EvaluationResult) or result is None:
            return result
        if not result.success:
            return EvaluationResult(
                metrics={"error": 0.0, "combined_score": 0.0},
                artifacts={
                    "failure_stage": "build",
                    "error_type": "BuildFailure",
                    "stderr": result.log[-2000:],
                },
            )
        _eval_binary.set(result.binary)
        return result

    def _run(self, *, workload: str):
        binary = _eval_binary.get()
        if binary is None:
            raise RuntimeError("no binary available -- build must succeed first")
        # Trace-list entries are relative to P2P_TRACE_DIR --
        # helpers.load_trace_list returns them verbatim, and
        # adopt_a_paper_loop.record_cbp_baseline prefixes them the same way.
        # Without this the bare relative path resolves against the Ray
        # worker's cwd (the runtime_env working_dir), so every run fails to
        # open its trace. That failure mode is quiet rather than loud:
        # aggregate() returns n=0, _map_results maps it to combined_score 0.0,
        # and the search appears to run normally while scoring every candidate
        # identically zero.
        trace = workload if os.path.isabs(workload) else f"{C.TRACE_DIR}/{workload}"
        return CBP2025Node.run.chia_remote(binary, trace, (), self._run_timeout_s)

    def _map_results(self, run_results: list) -> EvaluationResult:
        agg = CBP2025Node.aggregate(list(run_results))
        mpki = agg.get(C.DSE_SCREEN_METRIC)
        if mpki is None or agg["n"] < len(self._screening_traces) * 0.9:
            return EvaluationResult(
                metrics={"error": 0.0, "combined_score": 0.0},
                artifacts={"failure_stage": "run", "agg": json.dumps(agg, default=str)},
            )
        # Lower MPKI is better; skydiscover maximizes combined_score.
        metrics = {"combined_score": 1000.0 / (1.0 + mpki)}
        metrics.update({k: v for k, v in agg.items() if isinstance(v, (int, float))})
        return EvaluationResult(
            metrics=metrics,
            artifacts={"agg": json.dumps(agg, default=str)},
        )
