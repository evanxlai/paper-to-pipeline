"""adopt-a-paper loop driver (head process).

Stages (docs/stages.md is the authoritative contract):
  1.   distill    LLM reads the paper (+ optional artifact) -> feature spec
                  JSON, schema-checked by code, not by the model.
  1.5  review     evidence-checked spec (spec_review.py).
  2.   plan       per host: an agent reads the host checkout and runs the
                  suite it already ships -> a port plan and a test plan,
                  schema-checked and coverage-checked by code (plan_node.py).
  3.   integrate  per host: coding agent executes the plan through a BashTool;
                  a deterministic gate (gate.py, fed by plan_runner.py)
                  decides promotion.
  4.   dse        evolve-flows evolver tunes the spec's parameters under a
                  constraint set -- the only stage that knows about budgets;
                  screening fan-out, then full-suite validation (dse.py).

Run (after `chia up cluster/cluster.yaml`):
  chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage all
Env knobs are P2P_* (constants.py), forwarded via
  chia job submit --runtime-env-json '{"env_vars": {"P2P_DISTILL_MODE": "paper_plus_reference"}}' -- ...

Status: stages 1 through 3 run end to end against the cbp2025 host on a real
cluster (hosts/cbp2025/). The champsim and gem5 adapters are still TODO and
their gate fails closed; the stage-4 evaluator wiring carries its own TODOs
(see docs/plan.md).
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import ray
from chia.base.ChiaFunction import ChiaFunction, get
from chia.base.tools.BashTool import BashTool
from chia.trace.profiler import start_collector

import constants as C
import dse
import gate
import helpers
import plan_node
import plan_revision
import paper_markers
import spec_checks
import spec_review
from llm import load_prompt, make_llm, run_llm

from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
from hosts.cbp2025 import adapter as cbp2025_adapter


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
                # "head", not a host token. REFERENCE_ARTIFACT_DIR is under
                # third_party/ in this repository, which scripts/
                # fetch_artifacts.sh populates on the head and no worker
                # ever has. A host token would place this shell on a trace
                # worker, where every command it runs reports an empty
                # directory and the distiller concludes the artifact says
                # nothing.
                task_options={"resources": {"head": 0.1}},
            )
        ]
    # The schema must be inlined: in paper_only mode the agent has no tools,
    # so it cannot read spec/feature_spec.schema.json off disk and will
    # otherwise invent its own field names.
    schema = Path(C.SPEC_SCHEMA_PATH).read_text()
    llm = make_llm(C.LLM_BACKEND, tools, resume=False)
    # Ambiguities the source declares about its own figure transcriptions.
    # Hoisted out of the body so they cannot be skimmed past: the distiller
    # reading them inline is what did not happen, and the resulting guess
    # then rode three review rounds as an established fact.
    ann = paper_markers.annotate(paper)
    notes = ann.render_notes()
    caveats = (
        "\n\n## Declared ambiguities in the source\n\n"
        "Each of these is a point the input marks `UNCERTAIN`: the figure is "
        "genuinely ambiguous there. Choose a default so the spec stays "
        "implementable, but record the alternative in `open_questions`, and "
        "do not describe either reading as something the paper states.\n\n"
        + notes
    ) if notes else ""
    prompt = (
        load_prompt("distiller.md", feature_name=C.FEATURE_NAME)
        + f"\n\n## The schema\n\n```json\n{schema}\n```"
        + caveats
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

    # Always leave the artifact behind, even when the gate below refuses to
    # promote it. Failing closed must cost the run its promotion, never its
    # evidence: a refused run that writes nothing is one nobody can diagnose
    # without re-running the whole stage.
    dump.json("spec_final.json", spec)

    # Fail closed, exactly as the schema check above does. An `error` finding
    # is the spec contradicting itself -- a literal that will not fit its own
    # field, a total that does not match its parts. The integration agents
    # implement from this file and never read the paper, so a contradiction
    # here does not stop them: it produces a predictor that builds, runs, and
    # is quietly wrong, which the gate cannot distinguish from a real result.
    errs = [f for f in spec_checks.run_checks(spec, C.BUDGET_TRACKS_BITS[budget])
            if f.severity == "error"]
    if errs and not C.SPEC_ALLOW_ERRORS:
        raise SystemExit(
            f"spec has {len(errs)} unresolved self-consistency error(s); "
            f"refusing to write {C.SPEC_OUT_PATH}:\n"
            + "\n".join(f"  {f.pointer}: {f.message}" for f in errs)
            + "\nRe-run with P2P_SPEC_ALLOW_ERRORS=1 to write it anyway."
        )

    Path(C.SPEC_OUT_PATH).write_text(json.dumps(spec, indent=2))
    return spec


# ------------------------------------------------------------ baselines
def record_cbp_baseline(
    dump: helpers.Dumper, trace_list: Path, budget: str = "iso-192KiB"
) -> dict:
    """Build the unmodified kit (TAGE-SC-L 64KB wired to the 192KB budget
    rules) and fan the trace list out one run per trace.

    The build is pinned to the node that owns the checkout, and it is the
    *pristine* checkout: stage 3 edits a copy (`C.CBP2025_PORT_ROOT`), so a
    baseline recorded after an integration run still describes the host and
    not the port. G2 compares the port's knob-off metrics against this
    document, and a baseline measured on the ported tree could not tell the
    two apart.

    What lands on disk is the suite aggregate plus a `per_trace` map keyed by
    the trace path as the list writes it. The aggregate alone is not enough:
    a `feature_off_baseline` entry runs one shell command, so it needs a
    comparison point for one trace, and pointing it at a mean over six is a
    comparison between two different things that the gate would report as a
    regression.
    """
    # The recorded baseline is what G2 holds every port to, so it has to be
    # the host and not the host plus whatever a previous agent left in the
    # tree. Stage 2's planner has a shell on this same checkout.
    dump.json("cbp2025_baseline_restore.json",
              cbp2025_adapter.restore_host_checkout(C.CBP2025_ROOT))
    build = get(
        CBP2025Node.build.options(resources={C.CBP2025_HOST_RESOURCE: 1.0})
        .chia_remote(C.CBP2025_ROOT, None, C.BUILD_TIMEOUT_S, None)
    )
    if not build.success:
        raise SystemExit("baseline cbp2025 build failed:\n" + build.log[-4000:])
    traces = helpers.load_trace_list(trace_list)
    refs = [
        CBP2025Node.run.options(resources={C.CBP2025_RESOURCE: 1.0})
        .chia_remote(build.binary, f"{C.TRACE_DIR}/{t}", (), C.RUN_TIMEOUT_S, None)
        for t in traces
    ]
    results = [get(r) for r in refs]
    agg = get(CBP2025Node.aggregate.chia_remote(results))
    path = Path(trace_list)
    agg["trace_list"] = str(
        path.relative_to(C.REPO_ROOT) if path.is_absolute()
        and path.is_relative_to(C.REPO_ROOT) else path
    )
    agg["host_revision"] = cbp2025_adapter.checkout_revision()
    agg["per_trace"] = {
        rel: cbp2025_adapter.parse_metrics(result.log)
        for rel, result in zip(traces, results)
        if result is not None and result.success
    }
    # Carry forward per-trace numbers from an earlier recording of the same
    # tree. A run over experiments/perf-4.list would otherwise drop the
    # sample-trace entry that G2's single-command comparison points at, and
    # the two lists cannot be measured in one go: G2 needs a trace a shell
    # command finishes inside the agent's cap, and G5 needs traces that
    # carry signal. Same revision only -- numbers from another tree are
    # hearsay, and the top-level aggregate always describes `trace_list`
    # alone.
    previous = helpers.load_baseline("cbp2025", budget) or {}
    if previous.get("host_revision") == agg["host_revision"]:
        agg["per_trace"] = {**previous.get("per_trace", {}), **agg["per_trace"]}
    # The run's evidence lands either way, under out/. What does not land
    # either way is hosts/cbp2025/baselines/<budget>.json, because that file
    # is what G2 measures a port against and every later stage reads it
    # without knowing which run wrote it. A partial baseline promoted there
    # is a wrong yardstick with no way to tell, so the incomplete case keeps
    # whatever was already recorded and says why.
    dump.json("cbp2025_baseline.json", agg)
    if agg.get("n") != len(traces):
        raise SystemExit(
            f"baseline ran {agg.get('n')} of {len(traces)} traces; failed: "
            f"{agg.get('failed')}. A baseline over a different trace set than "
            f"the plan will name is not a baseline, so "
            f"{helpers.baseline_path('cbp2025', budget)} was left alone. The "
            f"measurement is in {dump.dir}."
        )
    helpers.record_baseline("cbp2025", budget, agg)
    return agg


# ------------------------------------------------------------ stage 2
def host_paths(host: str) -> tuple[str, str]:
    """The checkout stage 2 reads, and the recorded hook points, for one
    production host. This is the pristine tree in every case: stage 2 records
    `host_revision` and every clean-tree result against it, so it must be the
    tree nobody has ported into."""
    work_dir = {
        "cbp2025": C.CBP2025_ROOT,
        "champsim": C.CHAMPSIM_ROOT,
        "gem5": C.GEM5_ROOT,
    }[host]
    return work_dir, (C.REPO_ROOT / "hosts" / host / "NOTES.md").read_text()


# Ray resource token per host, for the shell the agents reach the checkout
# through. cbp2025 has its own because its checkout lives on exactly one node
# (see hosts/cbp2025/adapter.py); champsim and gem5 name their own token.
HOST_SHELL_RESOURCE = {"cbp2025": C.CBP2025_HOST_RESOURCE}


def shell_resources(host: str) -> dict:
    return {HOST_SHELL_RESOURCE.get(host, host): 0.1}


def checks_root(host: str) -> str | None:
    """Where the deterministic plan checks open the files a hook point names.

    `None` means "the work_dir", which is right for any host whose checkout
    is on this machine. cbp2025's is not: it is on a worker, and this process
    is the head, so plan_checks would report every hook point's file missing.
    The head keeps a mirror of the same upstream repository under
    third_party/ (scripts/fetch_artifacts.sh), and `plan` below refuses to
    use it unless it is at the same commit as the worker's."""
    if host == "cbp2025":
        return str(C.REPO_ROOT / "third_party" / "cbp2025")
    return None


def plan(dump: helpers.Dumper, spec: dict, host: str,
         baseline_key: str = "iso-192KiB") -> tuple[dict, dict]:
    """Planning node: an agent reads the host checkout, runs the suite that
    checkout already ships, and emits a port plan and a test plan. Code
    decides whether they cover the spec; see plan_node."""
    work_dir, notes = host_paths(host)
    mirror = checks_root(host)
    revision = None
    host_storage_bits = None
    if host == "cbp2025":
        # Read the commit off the worker that actually holds the checkout,
        # and refuse to run the file checks against a mirror at some other
        # commit. Without this, `hook_file_missing` would be a statement
        # about the head's copy and the planner would be sent to fix a file
        # that is present on the machine it is looking at.
        # The planner gets a shell on this tree and the next stage copies
        # it, so whatever the last run left behind would travel into the
        # port. On the first real stage-2 run that was a `test_sr.cc`
        # printing "Test passed", which then satisfied all seven
        # spec_unit_test entries against an unported tree. Clean before, so
        # the clean-tree results the planner records are about a clean tree.
        print(f"[plan] restoring {work_dir}: "
              f"{json.dumps(cbp2025_adapter.restore_host_checkout(work_dir))}")
        revision = cbp2025_adapter.checkout_revision()
        mirror_rev = _mirror_revision(mirror)
        if mirror_rev != revision:
            raise SystemExit(
                f"the head's mirror of the cbp2025 checkout ({mirror}) is at "
                f"{mirror_rev}, and the worker's ({work_dir}) is at {revision}. "
                f"The deterministic plan checks read the mirror, so they would "
                f"be about a different tree than the planner. Re-run "
                f"scripts/fetch_artifacts.sh, or `git -C {mirror} fetch && git "
                f"-C {mirror} checkout {revision}`."
            )
        # The host's own storage accounting on the clean tree. The plan's
        # host_storage has to reproduce it, because stage 4 costs every
        # candidate that shrinks the host with those terms.
        host_storage_bits = cbp2025_adapter.host_storage_bits(work_dir)
        print(f"[plan] host storage by its own accounting: {host_storage_bits} bits")
    bash = BashTool(
        name=f"{host}_bash",
        work_dir=work_dir,
        timeout_seconds=C.BASH_TOOL_TIMEOUT_S,
        task_options={"resources": shell_resources(host)},
    )
    try:
        return plan_node.make_plan(
            dump, spec, host, work_dir, notes, tools=[bash],
            revision=revision, checks_root=mirror,
            # So a metrics_equal_baseline pointer that resolves to nothing
            # is a repair turn here rather than a frozen G2 that stage 3 can
            # only escalate.
            baseline=helpers.load_baseline(host, baseline_key),
            host_storage_bits=host_storage_bits,
        )
    finally:
        bash.stop()
        if host == "cbp2025":
            # And clean after, so --stage baseline and the next run start
            # from the tree this plan describes rather than from this
            # planner's leftovers.
            dump.json(
                f"plan_{host}_checkout_restored.json",
                cbp2025_adapter.restore_host_checkout(work_dir),
            )


def _mirror_revision(mirror: str | None) -> str:
    """The commit of the head-local mirror, or a reason it has none."""
    import subprocess

    if not mirror or not Path(mirror).exists():
        return f"(absent: {mirror})"
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=mirror, capture_output=True, text=True
    )
    return proc.stdout.strip() or "(not a git checkout)"


def load_plans(host: str, spec: dict) -> tuple[dict, dict]:
    """This host's plan pair off disk, or a plain refusal.

    What comes back is the pair *in force*: stage 2's output, plus any
    revision stage 3 has already earned over it (`plan_revision.latest`). A
    run that stopped after a revision therefore resumes from it instead of
    silently re-litigating a correction the tree has already been edited to
    match.

    Not `None` on a miss: the spec path already has that failure mode, where
    a missing artifact renders into the prompt as the literal string "null"
    and the agent is simply told the document is empty."""
    plan_path, tests_path = helpers.plan_paths(host, spec.get("feature_name"))
    missing = [str(p) for p in (plan_path, tests_path) if not p.exists()]
    if missing:
        raise SystemExit(
            f"no plan for {host}: {', '.join(missing)} does not exist. "
            f"Run --stage plan first."
        )
    port_plan, test_plan, _ = plan_revision.latest(host, spec.get("feature_name"))
    return port_plan, test_plan


# ------------------------------------------------------------ stage 3
@dataclass
class HostAdapter:
    """Everything stage 3 needs to know about one host.

    `integrate` holds no per-host branches, so the only thing standing between
    the real stage and a host is this object: a fixture host (see
    loop/tests/toy_host.py) drives the production code path rather than a copy
    of it, and the champsim/gem5 adapters land here without touching the stage.
    """

    name: str
    work_dir: str
    notes: str
    resources: dict
    baseline: Callable[[], Optional[dict]]
    # (baseline, port_plan, test_plan) -> verdict. The plan pair is an
    # argument rather than something the adapter closed over at construction
    # because stage 3 can now revise it mid-run (plan_revision.py), and a gate
    # still judging the superseded test plan would be judging a standard
    # nobody holds.
    run_gate: Callable[[dict, dict, dict], gate.GateResult]
    # Where plan_checks opens the files a hook point names, when that is not
    # `work_dir`. It is not `work_dir` for any host whose checkout lives on
    # another machine: this process runs on the head, and a plan revision
    # reviewed there would report every hook point's file missing. `None`
    # means the two are the same directory, which is the one-machine case.
    checks_root: Optional[str] = None


def default_adapter(host: str, baseline_key: str) -> HostAdapter:
    """The production hosts.

    cbp2025 is implemented (hosts/cbp2025/adapter.py). champsim and gem5 are
    not, and their gate fails closed, which is the safe direction: an
    unimplemented check must never read as a pass.

    TODO(week 2): the other two. Per hosts/<host>/NOTES.md:
      champsim: one module dir composing a base TAGE-SC-L + the sR term
                (multi-module lists keep only the LAST return value).
      gem5:     subclass StatisticalCorrector on TAGE_SC_L_64KB
                (cleanest verified hook; see NOTES.md option 1).
    """
    if host == "cbp2025":
        # Lay down a pristine copy for the agent to edit before anything
        # else happens, so the bash tool the caller is about to start has a
        # tree to open and every attempt begins from the same place.
        cbp2025_adapter.clean_port_tree(fresh=C.CBP2025_PORT_FRESH)
        return HostAdapter(
            name=host,
            work_dir=C.CBP2025_PORT_ROOT,
            notes=cbp2025_adapter.notes(),
            resources={C.CBP2025_HOST_RESOURCE: 0.1},
            baseline=lambda: helpers.load_baseline(host, baseline_key),
            checks_root=checks_root(host),
            run_gate=cbp2025_adapter.run_gate,
        )
    work_dir, notes = host_paths(host)
    return HostAdapter(
        name=host,
        work_dir=work_dir,
        notes=notes,
        resources=shell_resources(host),
        baseline=lambda: helpers.load_baseline(host, baseline_key),
        checks_root=checks_root(host),
        run_gate=lambda baseline, port_plan, test_plan: gate.GateResult(
            False, ["gate adapters not implemented yet (hosts/ TODO)"]
        ),
    )


def _consider_revision(
    dump: helpers.Dumper,
    spec: dict,
    adapter: HostAdapter,
    llm,
    tools: list,
    reply: str,
    port_plan: dict,
    test_plan: dict,
    revision: int,
) -> tuple[dict, dict, int, Optional[dict]]:
    """Take a plan revision off a debug turn, if it proposed one.

    Returns the pair in force after the turn, its revision number, and an
    escalation if the repair turn emitted one. A
    rejected proposal returns the pair unchanged: the plan on disk is written
    by `plan_revision.commit` and by nothing else, so a revision that does not
    survive review leaves no trace on the artifacts and the agent faces the
    gate it already had.

    A rejection buys exactly one repair turn, the same allowance stage 2 gives
    a rejected plan (`C.PLAN_REPAIR_TURNS`). One is the right number for the
    same reason it is there: the rejection names every blocking item at once,
    so a second turn with the same list buys nothing a first turn could not.
    The repair turn costs an LLM call and no gate run, which is why it happens
    here rather than being folded into the next attempt."""
    if not plan_revision.proposed(reply):
        return port_plan, test_plan, revision, None

    feature = spec.get("feature_name")
    if revision >= C.PLAN_REVISIONS:
        # Say so, and only once: the agent has to stop proposing and either
        # port against the plan it has or escalate. Silently dropping the
        # proposal would leave it revising into a void every attempt.
        dump.json(f"plan_revision_{adapter.name}_refused.json", {
            "revision_budget": C.PLAN_REVISIONS,
            "reason": "revision budget spent",
        })
        run_llm(llm, plan_revision.budget_spent_prompt(C.PLAN_REVISIONS), tools)
        return port_plan, test_plan, revision, None

    index = revision + 1
    for turn in range(C.PLAN_REPAIR_TURNS + 1):
        new_port, new_tests, errors, findings = plan_revision.review(
            spec, adapter.work_dir, port_plan, test_plan, reply,
            checks_root=adapter.checks_root)
        # Evidence before verdict, like plan_node: a refused revision that
        # writes nothing is one nobody can diagnose without re-running stage 3.
        dump.json(f"plan_revision_{adapter.name}_{index}_review_{turn}.json", {
            "schema_errors": errors,
            "findings": [f.as_dict() for f in findings],
        })
        if not errors and not plan_revision.blocking(findings):
            return plan_revision.commit(
                dump, adapter.name, feature, index, new_port, new_tests, findings
            ) + (index, None)
        if turn == C.PLAN_REPAIR_TURNS:
            break
        resp = run_llm(llm, plan_revision.repair_prompt(errors, findings), tools)
        dump.llm(f"plan_revision_{adapter.name}_{index}_repair_{turn}", resp)
        reply = resp.result
        # The repair prompt itself offers escalation as the other move, so a
        # reply that takes it has to be heard here as well. Dropping it left
        # the agent's "the planning stage has to decide this" unrecorded and
        # sent it back into the same gate it had just declined to meet.
        escalated = plan_revision.escalation(reply)
        if escalated is not None:
            return port_plan, test_plan, revision, escalated
        if not plan_revision.proposed(reply):
            break  # it took the hint and stopped proposing

    return port_plan, test_plan, revision, None


def integrate(
    dump: helpers.Dumper,
    spec: dict,
    host: str,
    baseline_key: str,
    port_plan: Optional[dict] = None,
    test_plan: Optional[dict] = None,
    adapter: Optional[HostAdapter] = None,
) -> dict:
    """Coding agent executes the port plan in `host` behind an enable knob,
    iterating against build/run feedback until the deterministic gate passes
    or attempts run out.

    `baseline_key` selects which recorded baseline to compare against. It is
    a filename, not a constraint: stage 3 has no budget, and naming it after
    one was how the old signature implied otherwise.

    The plan arguments are keyword-with-default so that a caller holding a
    host adapter -- the stage-3 smoke test -- keeps working while it catches
    up."""
    adapter = adapter or default_adapter(host, baseline_key)
    if port_plan is None or test_plan is None:
        port_plan, test_plan = load_plans(host, spec)
    # Where a revision this run earns will be numbered from. Read off disk
    # rather than started at zero even when the caller handed us the pair, so
    # a second run over a host that already revised once cannot overwrite the
    # first revision and lose the record of what was asked of the first port.
    revision = plan_revision.count(host, spec.get("feature_name"))
    baseline = adapter.baseline()
    if baseline is None:
        raise SystemExit(
            f"no recorded baseline for {host}/{baseline_key}; run --stage baseline"
        )

    bash = BashTool(
        name=f"{adapter.name}_bash",
        work_dir=adapter.work_dir,
        timeout_seconds=C.BASH_TOOL_TIMEOUT_S,
        task_options={"resources": adapter.resources},
    )
    llm = make_llm(C.LLM_BACKEND, [bash], resume=True)  # one threaded session
    prompt = load_prompt(
        "integrator.md",
        host_path=adapter.work_dir,
        host_name=adapter.name,
    ) + (
        f"\n\n## Port plan\n\n```json\n{json.dumps(port_plan, indent=2)}\n```"
        f"\n\n## Test plan\n\n```json\n{json.dumps(test_plan, indent=2)}\n```"
        f"\n\n## Feature spec\n\n```json\n{json.dumps(spec, indent=2)}\n```"
        f"\n\n## The params header\n\n"
        f"Create `sr_params.h` with exactly this content. Stage 4 regenerates "
        f"it from the same spec and plan, with the values changed and nothing "
        f"else, so every macro below must be one the port reads.\n\n"
        f"```c\n{dse.params_header(spec, port_plan)}```"
        f"\n\n## Host notes\n\n{adapter.notes}"
    )

    status = "failed"
    attempts_used = 0
    started_at = revision
    escalated: Optional[dict] = None
    backend_error: Optional[str] = None
    try:
        resp = run_llm(llm, prompt, [bash])
        dump.llm(f"integrate_{host}_0", resp)
        for attempt in range(C.NUM_INTEGRATION_ATTEMPTS):
            attempts_used = attempt + 1
            g = adapter.run_gate(baseline, port_plan, test_plan)
            dump.json(f"gate_{host}_{attempt}.json", {
                "passed": g.passed, "reasons": g.reasons, "warnings": g.warnings,
                "plan_revision": revision,
            })
            if g.passed:
                status = "passed"
                break
            feedback = load_prompt("debug.md", gate_feedback=g.feedback, attempt=str(attempt + 1))
            resp = run_llm(llm, feedback, [bash])
            dump.llm(f"integrate_{host}_{attempt + 1}", resp)

            # Escalation before revision, and unconditionally: a turn that
            # says it cannot decide this has ended the attempt, and accepting
            # a plan edit out of the same turn would write a document its own
            # author just disclaimed.
            escalated = plan_revision.escalation(resp.result)
            if escalated is not None:
                status = "needs_replan"
                record = {
                    **escalated, "attempt": attempts_used,
                    "plan_revision": revision, "gate_reasons": g.reasons,
                    "raised_in": "debug turn",
                }
                dump.json(f"plan_escalation_{host}.json", record)
                # And beside the plan, where the next stage-2 run reads it.
                # out/ is timestamped and untracked, so an escalation that
                # only lands there is evidence nobody acts on.
                plan_revision.record_escalation(
                    host, spec.get("feature_name"), record)
                break

            port_plan, test_plan, revision, escalated = _consider_revision(
                dump, spec, adapter, llm, [bash], resp.result,
                port_plan, test_plan, revision,
            )
            if escalated is not None:
                # Same rule as an escalation in the debug turn itself: a turn
                # that says it cannot decide this has ended the attempt.
                status = "needs_replan"
                record = {
                    **escalated, "attempt": attempts_used,
                    "plan_revision": revision, "gate_reasons": g.reasons,
                    "raised_in": "plan revision repair turn",
                }
                dump.json(f"plan_escalation_{host}.json", record)
                plan_revision.record_escalation(
                    host, spec.get("feature_name"), record)
                break
    except Exception as e:  # noqa: BLE001
        # The backend, not the port. A Vertex 429 took down a run an hour
        # into it, and the traceback said nothing about the 400 lines of
        # C++ sitting on the worker or about how to pick them up. What the
        # agent wrote is still there, so record why the run stopped and say
        # what to do about it, rather than losing the run to an exception
        # that is not about the work.
        status = "backend_error"
        backend_error = f"{type(e).__name__}: {e}"
        dump.json(f"integrate_{host}_backend_error.json", {
            "error": backend_error,
            "attempts": attempts_used,
            "work_dir": adapter.work_dir,
            "resume": "re-run --stage integrate with P2P_CBP2025_PORT_FRESH=0 "
                      "to continue from the tree this run left, instead of "
                      "starting the port over",
        })
        print(f"[integrate] {host}: the backend failed mid-run: {backend_error}")
    finally:
        bash.stop()
    return {
        "host": host, "baseline": baseline_key, "status": status,
        "attempts": attempts_used,
        # How many revisions this run earned, not the absolute index, so the
        # number reads the same whether or not an earlier run left some behind.
        "plan_revisions": revision - started_at,
        **({"escalation": escalated} if escalated else {}),
        **({"backend_error": backend_error} if backend_error else {}),
    }


# ------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["distill", "baseline", "plan", "integrate", "dse", "all"])
    ap.add_argument("--host", default=None, help="limit plan/integrate/dse to one host")
    ap.add_argument("--budget", default="iso-192KiB", choices=list(C.BUDGET_TRACKS_BITS))
    # Which traces --stage baseline measures. The default is the two traces
    # the CBP2025 kit ships, because the only gate condition that reads the
    # recorded baseline is G2, and G2's command is one ./cbp run inside the
    # agent's 300-second shell. A real training trace does not fit there, so
    # recording one would produce a per_trace entry no correctness entry can
    # compare against. Point this at experiments/perf-8.list to record the
    # bigger set for the write-up.
    ap.add_argument("--baseline-list", default=str(C.REPO_ROOT / "experiments" / "smoke-2.list"))
    # Which traces stage 4 screens each candidate on. The default is the
    # 60-trace stratified set, which is the honest screening population and
    # also most of the search's wall clock: one candidate is 60 simulator
    # runs. Point it at a shorter list to demonstrate the stage, and say so
    # when reporting the result -- a winner screened on four traces is a
    # winner on four traces.
    ap.add_argument("--screening-list", default=str(C.SCREENING_LIST))
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
        summary["cbp2025_baseline"] = record_cbp_baseline(
            dump, Path(args.baseline_list), args.budget
        )

    hosts = [args.host] if args.host else list(C.HOSTS)
    plans: dict = {}
    if args.stage in ("plan", "integrate", "all"):
        if spec is None:
            raise SystemExit(
                f"no feature spec at {C.SPEC_OUT_PATH}; run --stage distill first."
            )
    if args.stage in ("plan", "all"):
        summary["plan"] = []
        for h in hosts:
            plans[h] = plan(dump, spec, h, args.budget)
            summary["plan"].append({
                "host": h,
                "hook_points": len(plans[h][0]["hook_points"]),
                "steps": len(plans[h][0]["steps"]),
                "correctness": len(plans[h][1]["correctness"]),
                "performance": len(plans[h][1]["performance"]),
            })

    if args.stage in ("integrate", "all"):
        summary["integrate"] = []
        for h in hosts:
            port_plan, test_plan = plans.get(h) or load_plans(h, spec)
            summary["integrate"].append(
                integrate(dump, spec, h, args.budget,
                          port_plan=port_plan, test_plan=test_plan)
            )
            if h == "cbp2025":
                # The patch is the run's primary evidence and it lives on a
                # worker, so it has to be pulled back before the job ends.
                # Written whether the gate passed or failed: a refused port
                # is the one a reader most needs to see.
                dump.text(f"integrate_{h}_diff.patch", cbp2025_adapter.port_diff())

    if args.stage in ("dse", "all"):
        # In an --stage all run, only tune what the gate promoted. The
        # default search is 250 iterations over the screening set, which is
        # a day and a half of cluster time; spending it on a port the gate
        # refused measures how a broken feature responds to its parameters.
        # An explicit --stage dse still runs, because re-running the search
        # over an already-integrated tree is exactly what that invocation is
        # for and the gate verdict is not in hand there.
        promoted = {
            entry["host"] for entry in summary.get("integrate") or []
            if entry.get("status") == "passed"
        }
        targets = hosts if args.stage == "dse" else [h for h in hosts if h in promoted]
        skipped = [h for h in hosts if h not in targets]
        if skipped:
            summary["dse_skipped"] = {
                "hosts": skipped,
                "reason": "the verify gate did not promote this port, so tuning it "
                          "would search the parameters of a feature that does not work",
            }
        summary["dse"] = [
            dse.run_dse(h, spec, args.budget, C.DSE_CONFIG,
                        screening_list_path=Path(args.screening_list))
            for h in targets
        ]

    dump.json("summary.json", summary)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
