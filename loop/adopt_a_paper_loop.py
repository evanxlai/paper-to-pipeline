"""adopt-a-paper loop driver (head process).

Stages (proposal section: Methodology):
  1. distill    LLM reads the paper (+ optional artifact) -> feature spec JSON,
                schema-checked by code, not by the model.
  2. integrate  per host: coding agent edits the host checkout through a
                BashTool; a deterministic gate (gate.py) decides promotion.
  3. dse        evolve-flows evolver tunes the spec's parameters + the host
                budget split at iso-storage; screening fan-out, then
                full-suite validation of finalists (dse.py).

Run (after `chia up cluster/cluster.yaml`):
  chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage all
Env knobs are P2P_* (constants.py), forwarded via
  chia job submit --runtime-env-json '{"env_vars": {"P2P_DISTILL_MODE": "paper_plus_reference"}}' -- ...

Status: rough draft. Stage 1 and the gate skeleton are complete; stage 2
host adapters and stage 3 evaluator wiring carry TODOs (see docs/plan.md).
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
from pathlib import Path

import ray
from chia.base.ChiaFunction import ChiaFunction, get
from chia.base.tools.BashTool import BashTool
from chia.trace.profiler import start_collector

import constants as C
import dse
import gate
import helpers
import spec_review
from llm import load_prompt, make_llm, run_llm

from chia_nodes.cbp2025.cbp2025_node import CBP2025Node


# ------------------------------------------------------------ stage 1
def distill(dump: helpers.Dumper, budget: str = "iso-192KiB") -> dict:
    """Feature-spec distillation. Paper-only mode gives the agent no tools;
    paper_plus_reference adds a read-only bash on the artifact checkout.

    The distiller's output is a draft. When P2P_SPEC_REVIEW is on it goes
    through spec_review before being written: deterministic checks, then one
    evidence-grounded reviewer per spec unit, then a code-side patch merge.
    Only the reviewed spec reaches the integration agents."""
    paper = Path(C.PAPER_TEXT_PATH).read_text()
    tools = []
    if C.DISTILL_MODE == "paper_plus_reference":
        tools = [
            BashTool(
                name="artifact_bash",
                work_dir=C.REFERENCE_ARTIFACT_DIR,
                timeout_seconds=C.BASH_TOOL_TIMEOUT_S,
                task_options={"resources": {"cbp2025": 0.1}},
            )
        ]
    # The schema must be inlined: in paper_only mode the agent has no tools,
    # so it cannot read spec/feature_spec.schema.json off disk and will
    # otherwise invent its own field names.
    schema = Path(C.SPEC_SCHEMA_PATH).read_text()
    llm = make_llm(C.LLM_BACKEND, tools, resume=False)
    prompt = (
        load_prompt("distiller.md", feature_name=C.FEATURE_NAME)
        + f"\n\n## The schema\n\n```json\n{schema}\n```"
        + f"\n\n## The paper\n\n{paper}"
    )
    try:
        resp = run_llm(llm, prompt, tools)
    finally:
        for t in tools:
            t.stop()
    dump.llm("distill", resp)

    spec, errs = helpers.validate_spec(helpers.extract_json_block(resp.result))
    if errs:
        # One repair turn with the schema errors inlined; still code-gated.
        # Carry the schema again: the repair runs in a fresh session, and the
        # bare validator messages do not say what the missing fields mean.
        resp = run_llm(
            make_llm(C.LLM_BACKEND, [], resume=False),
            "Your previous spec had schema errors. Emit the corrected full "
            "JSON document only, matching the schema exactly.\n\n"
            f"## The schema\n\n```json\n{schema}\n```\n\nErrors:\n"
            + "\n".join(helpers.truncate(e) for e in errs)
            + "\n\nPrevious:\n" + resp.result,
            [],
        )
        dump.llm("distill_repair", resp)
        spec, errs = helpers.validate_spec(helpers.extract_json_block(resp.result))
    if errs or spec is None:
        raise SystemExit(f"distillation failed schema check: {errs}")

    dump.json("spec_draft.json", spec)
    if C.SPEC_REVIEW:
        spec, review = spec_review.review_spec(
            dump, spec, paper, C.BUDGET_TRACKS_BITS[budget]
        )
        dump.json("spec_review_summary.json", review)
        print(json.dumps(review["rounds"], indent=2, default=str))

    Path(C.SPEC_OUT_PATH).write_text(json.dumps(spec, indent=2))
    return spec


# ------------------------------------------------------------ baselines
def record_cbp_baseline(dump: helpers.Dumper, trace_list: Path) -> dict:
    """Build the unmodified kit (TAGE-SC-L 64KB wired to the 192KB budget
    rules) and fan the trace list out one run per trace."""
    build = get(CBP2025Node.build.chia_remote(C.CBP2025_ROOT, None, C.BUILD_TIMEOUT_S))
    if not build.success:
        raise SystemExit("baseline cbp2025 build failed:\n" + build.log[-4000:])
    traces = helpers.load_trace_list(trace_list)
    # TEMP: only run the first trace for faster testing. (Was a hardcoded
    # "media" substring filter, which silently ran zero traces whenever the
    # list didn't happen to name a media-workload trace -- e.g. the sample
    # traces shipped in the cbp2025 kit, which are fp/int only.)
    traces = traces[:1]
    refs = [
        CBP2025Node.run.chia_remote(build.binary, f"{C.TRACE_DIR}/{t}", (), C.RUN_TIMEOUT_S)
        for t in traces
    ]
    agg = get(CBP2025Node.aggregate.chia_remote([get(r) for r in refs]))
    dump.json("cbp2025_baseline.json", agg)
    helpers.record_baseline("cbp2025", "iso-192KiB", agg)
    return agg


# ------------------------------------------------------------ stage 2
def integrate(dump: helpers.Dumper, spec: dict, host: str, budget: str) -> dict:
    """Coding agent implements the spec in `host` behind an enable knob,
    iterating against build/run feedback until the deterministic gate
    passes or attempts run out.

    TODO(week 2): host adapters. Per hosts/<host>/NOTES.md:
      champsim: one module dir composing a base TAGE-SC-L + the sR term
                (multi-module lists keep only the LAST return value).
      gem5:     subclass StatisticalCorrector on TAGE_SC_L_64KB
                (cleanest verified hook; see NOTES.md option 1).
    """
    baseline = helpers.load_baseline(host, budget)
    if baseline is None:
        raise SystemExit(f"no recorded baseline for {host}/{budget}; run --stage baseline")

    work_dir = {"champsim": C.CHAMPSIM_ROOT, "gem5": C.GEM5_ROOT}[host]
    bash = BashTool(
        name=f"{host}_bash",
        work_dir=work_dir,
        timeout_seconds=C.BASH_TOOL_TIMEOUT_S,
        task_options={"resources": {host: 0.1}},
    )
    llm = make_llm(C.LLM_BACKEND, [bash], resume=True)  # one threaded session
    notes = (C.REPO_ROOT / "hosts" / host / "NOTES.md").read_text()
    prompt = load_prompt(
        "integrator.md",
        spec_path=str(C.SPEC_OUT_PATH),
        host_path=work_dir,
        host_name=host,
        feature_name=C.FEATURE_NAME,
    ) + f"\n\n## Feature spec\n\n{json.dumps(spec, indent=2)}\n\n## Host notes\n\n{notes}"

    status = "failed"
    try:
        resp = run_llm(llm, prompt, [bash])
        dump.llm(f"integrate_{host}_0", resp)
        for attempt in range(C.NUM_INTEGRATION_ATTEMPTS):
            g = _run_gate(host, budget, baseline)  # TODO: host build/run adapters
            dump.json(f"gate_{host}_{attempt}.json", {"passed": g.passed, "reasons": g.reasons})
            if g.passed:
                status = "passed"
                break
            feedback = load_prompt("debug.md", gate_feedback=g.feedback, attempt=str(attempt + 1))
            resp = run_llm(llm, feedback, [bash])
            dump.llm(f"integrate_{host}_{attempt + 1}", resp)
    finally:
        bash.stop()
    return {"host": host, "budget": budget, "status": status}


def _run_gate(host: str, budget: str, baseline: dict) -> gate.GateResult:
    """Build + feature-off run + unit tests + feature-on smoke, then
    gate.check_gate. TODO(week 2): implement via hosts/ adapters; until
    then the gate fails closed."""
    return gate.GateResult(False, ["gate adapters not implemented yet (hosts/ TODO)"])


# ------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["distill", "baseline", "integrate", "dse", "all"])
    ap.add_argument("--host", default=None, help="limit integrate/dse to one host")
    ap.add_argument("--budget", default="iso-192KiB", choices=list(C.BUDGET_TRACKS_BITS))
    args = ap.parse_args()

    ray.init(address="auto", runtime_env=C.RUNTIME_ENV)
    start_collector()  # token + compute cost per accepted change (chia viz-profile)
    dump = helpers.Dumper()
    summary: dict = {"stage": args.stage, "budget": args.budget}

    spec = None
    if args.stage in ("distill", "all"):
        spec = distill(dump, args.budget)
    elif Path(C.SPEC_OUT_PATH).exists():
        spec = json.loads(Path(C.SPEC_OUT_PATH).read_text())

    if args.stage in ("baseline", "all"):
        summary["cbp2025_baseline"] = record_cbp_baseline(dump, C.SMOKE_LIST)

    hosts = [args.host] if args.host else list(C.HOSTS)
    if args.stage in ("integrate", "all"):
        summary["integrate"] = [integrate(dump, spec, h, args.budget) for h in hosts]

    if args.stage in ("dse", "all"):
        cfg = str(C.REPO_ROOT / "experiments" / "config_adaevolve.yaml")
        summary["dse"] = [dse.run_dse(h, spec, args.budget, cfg) for h in hosts]

    dump.json("summary.json", summary)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
