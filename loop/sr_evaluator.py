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
import hashlib
import json
import os
import time

import constants as C
import constraints as K
from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
from skydiscover.evaluation.chia_evaluator import ChiaEvaluator
from skydiscover.evaluation.evaluation_result import EvaluationResult

def _unwrap(result):
    """Strip the profiler's wrapper off a resolved ChiaFunction result.

    `start_collector()` is on for the whole job (adopt_a_paper_loop.main),
    so every ChiaFunction returns a `_ProfiledResult` carrying the real
    value plus worker metadata. `chia.base.ChiaFunction.get` unwraps that
    transparently, and every other caller in this repository goes through
    it. skydiscover's ChiaEvaluator does not: it awaits the ObjectRef
    itself.

    Without this the first stage-4 run died with "'_ProfiledResult' object
    has no attribute 'success'" before a single candidate was evaluated. It
    is duck-typed rather than imported so that the evaluator keeps working
    if the profiler is off, and so this module does not take a dependency
    on a private chia class."""
    value = getattr(result, "value", None)
    if value is not None and type(result).__name__ == "_ProfiledResult":
        return value
    return result


# Per-evaluation binary handoff between build and run. ChiaEvaluator calls
# build_fn and run_fn separately with no shared argument -- run_fn is invoked
# as run_fn(workload=trace) and never receives the build artifact -- so build
# stashes the binary here and run picks it up. Safe because
# ChiaEvaluator.evaluate_batch is deliberately sequential ("to prevent actor
# state races"), and because each asyncio task gets its own context copy.
_eval_binary: contextvars.ContextVar[bytes | None] = contextvars.ContextVar(
    "_eval_binary", default=None
)
# The same handoff for the candidate's static metrics (its accounted storage
# and the breakdown behind it), so the scored result can report them.
_eval_static: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "_eval_static", default=None
)


def infeasible_score(report: "K.CandidateReport", constraints: list) -> float:
    """The score of a candidate that breaks a constraint: in [0, 1), so it is
    below every candidate that fits (1000 / (1 + MPKI) is above 1 for any
    MPKI under 999), and higher the closer it comes to fitting.

    Zero for everything would leave a search that starts over the allowance
    with no direction at all, and at a tight allowance that is where the
    defaults start: the paper's feature on the unmodified host."""
    if report.errors:
        return 0.0
    score = 1.0
    for c in constraints:
        value = report.metrics.get(c.metric)
        if c.phase != "static" or value is None or c.holds(value) or not value:
            continue
        ratio = c.allowance / value if c.comparison in ("<=", "<") else value / c.allowance
        score *= max(0.0, min(ratio, 1.0))
    return min(score, 0.99)


def candidate_key(program_solution: str) -> str:
    """What the compiler sees in a header, as a short hash: every line with its
    `//` comment removed and its whitespace collapsed, blank lines dropped.

    Two headers with the same key compile the same source, and this simulator
    is deterministic, so they score the same. The key is the code and not the
    parsed knob values, because constraints.parse_header skips every line that
    is not a SR_/HOST_ #define, and a proposal that adds any other line builds
    something else under the same values. Two keys that differ only in a way
    the compiler ignores just cost a second screening, which is the safe way
    to be wrong."""
    lines = []
    for line in (program_solution or "").splitlines():
        code = " ".join(line.split("//", 1)[0].split())
        if code:
            lines.append(code)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]


class SRParamsEvaluator(ChiaEvaluator):
    def __init__(
        self,
        cbp_root: str,
        screening_traces: list,
        output_dir: str,
        build_timeout_s: int,
        run_timeout_s: int,
        feature_env: dict | None = None,
        spec: dict | None = None,
        port_plan: dict | None = None,
        constraints: list | None = None,
    ):
        self._cbp_root = cbp_root
        self._screening_traces = list(screening_traces)
        self._build_timeout_s = build_timeout_s
        self._run_timeout_s = run_timeout_s
        # The environment that turns the ported feature ON. Without it the
        # search tunes a feature that is not running: the port defaults its
        # enable knob off (the gate's G2 requires that), so every candidate
        # would execute the identical baseline predictor and score the same.
        # The search would then look healthy for 250 iterations and learn
        # nothing. dse.run_dse derives this from the port plan's
        # feature_enable block, which is the only place the knob is named.
        self._feature_env = dict(feature_env or {})
        # What a candidate must satisfy before it is built, and what it is
        # costed from. Plain dicts, because this instance is pickled to the
        # EvolverNode actor. With no spec there is nothing to check, which is
        # how the older tests construct it.
        self._spec = spec
        self._port_plan = port_plan or {}
        self._constraints = [K.Constraint(c["metric"], c["comparison"], c["allowance"],
                                          c.get("name", "")) for c in constraints or []]
        # Candidates this search has already screened, by candidate_key. On
        # 2026-09-23, 7 of 24 iterations re-proposed a header the search had
        # scored, and each one spent about 18 minutes of trace slots to learn
        # nothing. Per instance, so per search: a new search can run on a
        # different port or trace list, where the same header scores
        # differently. The instance lives in the EvolverNode actor, so this
        # fills as the search goes.
        self._screened: dict = {}
        # One JSON line per evaluation, repeats included, with the full
        # header. The search's own database keeps only its population, so a
        # candidate it dropped is otherwise gone with its header.
        self.candidates_log = os.path.join(
            output_dir, f"candidates_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
        super().__init__(
            build_fn=self._build,
            run_fn=self._run,
            result_mapper_fn=self._map_results,
            workloads=self._screening_traces,
            output_dir=output_dir,
            timeout=run_timeout_s,
        )

    async def evaluate_program(self, program_solution: str, program_id: str = ""):
        """Screen a candidate, unless this search already screened the same code.

        A repeat is not built or run. It comes back as a failed attempt, which
        is how skydiscover treats a build failure: combined_score 0 and an
        `error` artifact. That keeps it out of the population, where a copy
        would take one of the few slots, and skydiscover retries the iteration
        with the error text in the next prompt. So the proposer hears at once
        that it repeated itself, and which earlier program it matched."""
        key = candidate_key(program_solution)
        first = self._screened.get(key)
        if first is not None:
            metrics = first["metrics"]
            message = (
                f"Repeat: this header is the same code as program {first['id']}, which "
                f"this search already built and screened ({C.DSE_SCREEN_METRIC} "
                f"{metrics.get(C.DSE_SCREEN_METRIC)}, storage_bits "
                f"{metrics.get('storage_bits')}). It was not built or run again. Change "
                f"at least one value to a setting this search has not tried.")
            print(f"[sr_evaluator] {program_id or 'candidate'}: repeat of {first['id']}, "
                  f"skipped the build and {len(self._screening_traces)} trace runs")
            result = EvaluationResult(
                metrics={"combined_score": 0.0},
                artifacts={"failure_stage": "repeat", "error": message,
                           "repeat_of": first["id"]})
            self._record(program_id, key, program_solution, result, repeat_of=first["id"])
            return result
        result = await super().evaluate_program(program_solution, program_id)
        # Only a candidate that was screened in full. A refusal or a build
        # failure costs little to redo, and a run failure can be a worker
        # that died, which the next attempt would not repeat.
        if C.DSE_SCREEN_METRIC in (result.metrics or {}):
            self._screened[key] = {"id": program_id, "metrics": dict(result.metrics)}
        self._record(program_id, key, program_solution, result)
        return result

    def _record(self, program_id, key, program_solution, result, repeat_of=None):
        entry = {
            "ts": time.time(), "program_id": program_id, "key": key,
            "repeat_of": repeat_of,
            "failure_stage": (result.artifacts or {}).get("failure_stage"),
            "metrics": {k: v for k, v in (result.metrics or {}).items()
                        if isinstance(v, (int, float))},
            "header": program_solution,
        }
        try:
            with open(self.candidates_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:  # evidence only; never worth ending a search over
            print(f"[sr_evaluator] could not write {self.candidates_log}: {e}")

    def _build(self, program_solution: str):
        # program_solution is the evolver's mutated sr_params.h content;
        # overlaying just this file assumes the checkout's predictor already
        # #includes "sr_params.h" (stage-2 integration's job -- until then the
        # header is inert and every candidate scores identically).
        # Pinned to the node that holds the checkout. The default token on
        # CBP2025Node.build is "cbp2025", which every trace node also
        # advertises, and cbp_root here is the PORTED tree -- it exists on
        # one machine only.
        return CBP2025Node.build.options(
            resources={C.CBP2025_HOST_RESOURCE: 1.0}
        ).chia_remote(
            self._cbp_root,
            {"sr_params.h": program_solution.encode()},
            self._build_timeout_s,
            self._feature_env,
        )

    def check(self, program_solution: str):
        """The candidate's static report, or None when there is no spec to
        check it against."""
        if self._spec is None:
            return None
        return K.check_static(program_solution, self._spec, self._port_plan,
                              self._constraints)

    async def _dispatch_build(self, program_solution, label):
        _eval_binary.set(None)
        _eval_static.set(None)
        report = self.check(program_solution)
        if report is not None and not report.ok:
            # Refused before the build. It costs no build and no trace, and
            # the message is the proposer's feedback: which value is illegal
            # or which constraint broke, and where the bits are.
            return EvaluationResult(
                metrics={"error": 0.0,
                         "combined_score": infeasible_score(report, self._constraints),
                         **{k: float(v) for k, v in report.metrics.items()}},
                artifacts={"failure_stage": "constraints", "report": report.message()},
            )
        if report is not None:
            _eval_static.set({"metrics": report.metrics, "breakdown": report.breakdown})
        result = _unwrap(await super()._dispatch_build(program_solution, label))
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
        return CBP2025Node.run.options(
            resources={C.CBP2025_RESOURCE: 1.0}
        ).chia_remote(
            binary, trace, (), self._run_timeout_s, self._feature_env
        )

    def _map_results(self, run_results: list) -> EvaluationResult:
        # Same unwrap as the build side: these came back through
        # skydiscover rather than through chia's get().
        agg = CBP2025Node.aggregate([_unwrap(r) for r in run_results])
        mpki = agg.get(C.DSE_SCREEN_METRIC)
        if mpki is None or agg["n"] < len(self._screening_traces) * 0.9:
            return EvaluationResult(
                metrics={"error": 0.0, "combined_score": 0.0},
                artifacts={"failure_stage": "run", "agg": json.dumps(agg, default=str)},
            )
        measured = K.check_measured(agg, self._constraints)
        static = _eval_static.get() or {}
        if measured:
            return EvaluationResult(
                metrics={"error": 0.0, "combined_score": 0.0},
                artifacts={"failure_stage": "constraints",
                           "report": "\n".join(measured),
                           "agg": json.dumps(agg, default=str)},
            )
        # Lower MPKI is better; skydiscover maximizes combined_score.
        metrics = {"combined_score": 1000.0 / (1.0 + mpki)}
        metrics.update({k: v for k, v in agg.items() if isinstance(v, (int, float))})
        metrics.update({k: float(v) for k, v in (static.get("metrics") or {}).items()})
        artifacts = {"agg": json.dumps(agg, default=str)}
        if static.get("breakdown"):
            artifacts["storage_breakdown"] = json.dumps(static["breakdown"])
        return EvaluationResult(metrics=metrics, artifacts=artifacts)
