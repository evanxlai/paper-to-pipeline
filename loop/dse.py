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

CAVEAT (host coverage): CBP2025Node's build/run are the only host adapter
this stage knows (used already by record_cbp_baseline). `run_dse`'s and
`promote_finalists`' `host` argument only labels/namespaces output: every
build and run below goes through CBP2025Node, and loop/sr_evaluator.py does
the same. So a gem5 or champsim search would screen the CBP2025 kit and
report the result under the other host's name. Both entry points refuse
every host but cbp2025 (`require_searchable`), and so does the driver before
it starts a job. Per-host budget-bit splitting and a champsim/gem5-native
evaluator are TODO(week 3).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import constants as C
import constraints as K
import helpers


# The hosts stage 4 can search. Only cbp2025, because run_dse and
# promote_finalists build and run through CBP2025Node alone (see the host
# coverage caveat above).
SEARCHABLE_HOSTS = ("cbp2025",)


def require_searchable(host: str) -> None:
    """Refuse a host this stage would silently search on the CBP2025 kit.

    Here, in the entry points, and not only in the driver, so no caller can
    go around it: a script or a test that calls run_dse("gem5", ...) gets
    the refusal too. Without it the search runs, finishes, and writes a
    confident gem5 result that is the CBP2025 kit's under another name.
    Nothing in that result would say so."""
    if host not in SEARCHABLE_HOSTS:
        raise SystemExit(
            f"stage 4 cannot search {host}: run_dse and promote_finalists build "
            f"and run only through CBP2025Node, so a {host} search would silently "
            f"search the CBP2025 kit and report it as {host}'s. Stages dse and "
            f"promote take --host {' or '.join(SEARCHABLE_HOSTS)} until {host} has "
            f"its own evaluator."
        )


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
    A knob whose range admits exactly one value is reported `pinned` and
    skipped -- there is no second value to build, and the spec said so.

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
            # A range that admits exactly one value is a declaration, not a
            # defect: the knob is pinned by the paper's structure, and saying
            # so in `parameters` tells the integrator the value and that it
            # is not free. Nothing to build, nothing to warn about.
            if K.is_pinned(knob):
                entry["result"] = "pinned"
            else:
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


def _expand(text: str, env: dict) -> str:
    """${VAR} substitution the way skydiscover's Config.from_yaml does it: a
    name that is not set stays as the literal placeholder."""
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
                  lambda m: env.get(m.group(1), m.group(0)), text)


def check_llm(config_path: str, timeout_s: int = 120) -> dict:
    """Send one small request to every model the search config names, through
    the same URL and key the evolver will use. Returns the per-model result
    and a list of errors; an empty list means every model answered.

    Why this exists: when the evolver cannot reach its LLM, skydiscover logs
    each failed call and carries on. The search then "completes" having
    scored only the seed program, and nothing in the result says that no
    proposal was ever made. That happened on 2026-09-22, twice. The probe
    costs a few seconds and a few tokens, so a dead route stops the stage
    before any build instead of after the whole search.

    The ${VAR} placeholders are expanded from the environment the evolver
    actor will see: this process's plus what RUNTIME_ENV forwards."""
    import urllib.error
    import urllib.request

    import yaml

    llm = (yaml.safe_load(Path(config_path).read_text()) or {}).get("llm") or {}
    env = {**os.environ, **C.RUNTIME_ENV["env_vars"]}
    report = {"config": str(config_path), "models": {}, "errors": []}
    for m in llm.get("models") or []:
        name = m.get("name", "?")
        base = _expand(str(m.get("api_base") or llm.get("api_base") or ""), env)
        key = _expand(str(m.get("api_key") or llm.get("api_key") or ""), env)
        report["api_base"] = base
        unset = re.findall(r"\$\{(\w+)\}", base + key)
        if unset or not base:
            result = (f"{', '.join(unset)} not set in the evolver's environment"
                      if unset else "no api_base in the config")
        else:
            request = urllib.request.Request(
                base.rstrip("/") + "/chat/completions",
                data=json.dumps({
                    "model": name, "max_tokens": 256,
                    "messages": [{"role": "user", "content": "Reply with the word OK."}],
                }).encode(),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"},
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout_s) as resp:
                    result = "ok" if resp.status == 200 else f"HTTP {resp.status}"
            except urllib.error.HTTPError as e:
                result = f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}"
            except (urllib.error.URLError, OSError) as e:
                result = f"{base} unreachable: {getattr(e, 'reason', e)}"
        report["models"][name] = result
        if result != "ok":
            report["errors"].append(f"{name}: {result}")
    if not report["models"]:
        report["errors"].append(f"{config_path} names no llm.models")
    return report


# The run_dse statuses that mean the search produced a result. Anything else
# is a stage-4 failure, and the job exits non-zero on it (adopt_a_paper_loop).
DSE_OK = ("completed", "stopped")


def search_outcome(result) -> tuple[str, str | None]:
    """(status, error) for a finished EvolverResult.

    iteration_count is the number of programs the search scored, and the
    seed is one of them. A "completed" search with nothing else in it never
    got a proposal back, whatever the reason, and reporting its seed as the
    best candidate reads as a result when it is not one."""
    if result.terminal_status in DSE_OK and result.iteration_count <= 1:
        return "no_candidates", ("the search scored only its seed program: no "
                                 "proposal came back from the LLM, or every one "
                                 "repeated the seed. The EvolverNode's log and the "
                                 "candidates log say which.")
    return result.terminal_status, result.error_message


def read_candidates_log(path: Path | str) -> list[dict]:
    """Every candidate a search screened in full, from the evaluator's own log
    (sr_evaluator.SRParamsEvaluator.candidates_log), as program entries.

    This is the only complete record. The search's database keeps a small
    population and drops the rest, header and all: on 2026-09-23 the one
    candidate that grew sR and led on CycWPPKI was dropped, and it could not
    be promoted. Repeats are left out, because each one is a copy of an
    earlier entry. A missing log reads as no candidates."""
    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return []
    out = []
    for n, line in enumerate(lines):
        row = json.loads(line)
        if row.get("repeat_of") or C.DSE_SCREEN_METRIC not in (row.get("metrics") or {}):
            continue
        out.append({"id": row.get("program_id") or row.get("key"), "iteration_found": None,
                    "evaluation": n, "solution": row.get("header") or "",
                    "metrics": dict(row.get("metrics") or {})})
    return out


def candidates_summary(path: Path | str) -> dict:
    """How many proposals the search evaluated, and how many it skipped as
    repeats of a candidate it had already screened."""
    try:
        rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    except OSError:
        return {"log": str(path), "missing": True}
    return {
        "log": str(path),
        "evaluations": len(rows),
        "screened": sum(1 for r in rows if not r.get("repeat_of")
                        and C.DSE_SCREEN_METRIC in (r.get("metrics") or {})),
        "repeats_skipped": sum(1 for r in rows if r.get("repeat_of")),
    }


def evolver_actor_name(host: str) -> str:
    """The detached actor a running search lives in. run_dse kills any
    actor of this name before it starts, and promotion refuses to run
    while one exists."""
    return f"p2p-dse-evolver-{host}"


def run_dse(
    host: str, spec: dict, budget_name: str, config_path: str,
    screening_list_path: Path | str = C.SCREENING_LIST,
) -> dict:
    # First, before the evolver imports: a host this stage cannot search is
    # refused the same way whether or not evolve-flows is installed.
    require_searchable(host)
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

    # Before the preflight's thirty-odd builds, not after them.
    summary["llm_check"] = check_llm(config_path)
    if summary["llm_check"]["errors"]:
        return {**summary, "status": "llm_unreachable",
                "error": "; ".join(summary["llm_check"]["errors"])}

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

    actor_name = evolver_actor_name(host)
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
    status, error = search_outcome(result)
    return {
        **summary,
        "best_program": result.best_program,
        "best_metrics": result.best_metrics,
        # Re-derived here, not read off the search's own record, so the
        # summary's storage figure is one nobody could have misreported.
        "best_storage": {"feasible": best.ok, "metrics": best.metrics,
                         "breakdown": best.breakdown},
        "iterations": result.iteration_count,
        "candidates": candidates_summary(evaluator.candidates_log),
        # What promote_finalists picks from, in this job or a later one:
        # every candidate the search screened, not only the population it
        # kept. The database's own record wins where both have a program,
        # because it carries iteration_found.
        "population": list({
            **{p["id"]: p for p in read_candidates_log(evaluator.candidates_log)},
            **{p.get("id"): _program_entry(p) for p in result.population or []},
        }.values()),
        "status": status,
        "error": error,
    }


# ------------------------------------------------------------ promotion
#
# The search picks its winners on a screening list of a few traces, and a
# winner on a few traces can lose on others. Promotion scores the top few
# again on traces the search never saw (C.PROMOTE_LIST), next to two
# references run on the same traces in the same job: the kit's default host,
# which is the baseline, and the port with every knob at its default, which
# is the untuned port. That comparison is stage 4's verdict.

BASELINE, DEFAULTS = "baseline", "defaults"
PROMOTE_OK = ("promoted",)
# Lower is better for both branch metrics. IPC is reported, not judged.
_LOWER_IS_BETTER = ("brmispki_50perc_amean", "cycwppki_50perc_amean")
_PROMOTE_METRICS = (*_LOWER_IS_BETTER, "ipc_50perc_amean")


def _program_entry(p: dict) -> dict:
    """The part of one evolver program that promotion needs. The full record
    also carries the prompts and the parent's source, which no summary needs."""
    return {"id": p.get("id"), "iteration_found": p.get("iteration_found"),
            "solution": p.get("solution") or "", "metrics": dict(p.get("metrics") or {})}


def load_population(path: Path | str, host: str | None = None) -> list[dict]:
    """The programs a finished search scored, read back from disk.

    `path` is one of four things:
    - a job's summary.json, whose dse[] entries carry `population`;
    - the evaluator's candidates_<time>.jsonl, which holds every candidate
      the search screened (read_candidates_log), the most complete of the four;
    - an adaevolve output directory, which holds checkpoints/checkpoint_<N>/;
    - one checkpoint_<N> directory, which holds programs/.

    Every checkpoint is read, not only the last. A checkpoint holds the
    programs that were in the database at that moment, and the database
    drops programs as the search goes on. So a later checkpoint can lack a
    program an earlier one kept, and that program can have the best score."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"{path} does not exist, so there is no search to promote from")
    if path.is_file() and path.suffix == ".jsonl":
        return read_candidates_log(path)
    if path.is_file():
        doc = json.loads(path.read_text())
        runs = [d for d in doc.get("dse") or [] if host is None or d.get("host") == host]
        return [_program_entry(p) for d in runs for p in d.get("population") or []]
    dirs = ([path / "programs"] if (path / "programs").is_dir()
            else sorted((path / "checkpoints").glob("checkpoint_*/programs")))
    if not dirs:
        raise SystemExit(f"{path} holds no programs/ and no checkpoints/checkpoint_*/programs/")
    programs = {}
    for d in dirs:
        for f in sorted(d.glob("*.json")):
            p = json.loads(f.read_text())
            programs[p.get("id") or f.stem] = _program_entry(p)
    return list(programs.values())


def _knob_key(report: "K.CandidateReport") -> tuple:
    return tuple(sorted(report.feature.items())), tuple(sorted(report.host.items()))


def _screen_rank(p: dict) -> tuple:
    """Best first: the lower screening MPKI, then the earlier find.

    MPKI itself, not the search's combined_score. The two give the same
    order, since combined_score is 1000 / (1 + MPKI), but every stage ranks
    by C.DSE_SCREEN_METRIC and this says so. Only candidates that carry it
    get here (select_finalists)."""
    return (float(p["metrics"][C.DSE_SCREEN_METRIC]), p.get("iteration_found") or 0,
            p.get("evaluation") or 0)


def select_finalists(
    population: list[dict], spec: dict, port_plan: dict, constraints: list, top_k: int,
) -> tuple[list[dict], dict]:
    """The top_k distinct candidates by screening score, and a count of the
    candidates passed over, by reason.

    A candidate qualifies when screening built and scored it, which means its
    metrics carry the screening metric (a refused or failed candidate has
    only a score), and when its header still passes every static constraint
    here. Candidates with the same knob values are one candidate. The
    defaults are left out, because promotion runs them anyway, as the
    untuned port."""
    defaults = _knob_key(K.check_static(params_header(spec, port_plan), spec, port_plan, []))
    best: dict = {}
    passed_over = {"not_scored": 0, "fails_static_check": 0, "defaults": 0, "duplicate": 0}
    for p in population:
        if (p.get("metrics") or {}).get(C.DSE_SCREEN_METRIC) is None:
            passed_over["not_scored"] += 1
            continue
        report = K.check_static(p.get("solution") or "", spec, port_plan, constraints)
        if not report.ok:
            passed_over["fails_static_check"] += 1
            continue
        key = _knob_key(report)
        if key == defaults:
            passed_over["defaults"] += 1
            continue
        entry = {**p, "storage_bits": report.metrics.get("storage_bits")}
        if key in best:
            passed_over["duplicate"] += 1
            if _screen_rank(best[key]) <= _screen_rank(entry):
                continue
        best[key] = entry
    return sorted(best.values(), key=_screen_rank)[:top_k], passed_over


def _mean(values: list) -> float | None:
    return sum(values) / len(values) if values else None


def _versus(a: dict, b: dict, traces: list, metric: str) -> dict:
    """Variant a against variant b on one metric, over traces both ran.
    `change` is a's mean over b's, minus one: negative means a is lower."""
    both = [t for t in traces if a.get(t) and b.get(t)]
    mean_a = _mean([a[t][metric] for t in both])
    mean_b = _mean([b[t][metric] for t in both])
    return {
        "change": (mean_a / mean_b - 1) if mean_a is not None and mean_b else None,
        "traces_lower": sum(a[t][metric] < b[t][metric] for t in both),
        "traces_higher": sum(a[t][metric] > b[t][metric] for t in both),
        "traces_same": sum(a[t][metric] == b[t][metric] for t in both),
    }


def compare_variants(per_trace: dict, traces: list, finalists: list[str],
                     constraints: list | None = None) -> dict:
    """Score every variant on the promotion traces and name the winner.

    `per_trace` is {label: {trace: metrics or None}}, with None for a run
    that failed. Means are only compared over the same traces: a variant
    that did not run every trace is reported, and it can be neither a
    reference nor the winner. The winner is the complete finalist with the
    lowest screening metric that also meets every measured constraint on
    these traces."""
    scores = {}
    for label, runs in per_trace.items():
        ok = [runs[t] for t in traces if runs.get(t)]
        scores[label] = {"n": len(ok), "failed": [t for t in traces if not runs.get(t)],
                         **{m: _mean([r[m] for r in ok if m in r]) for m in _PROMOTE_METRICS}}
    complete = {label for label, s in scores.items() if not s["failed"]}
    result = {"variants": scores, "vs_baseline": {}, "vs_defaults": {}}
    # Everything against the baseline, and the finalists against the untuned
    # port too: that second comparison is what the tuning itself bought.
    pairs = [(label, BASELINE, "vs_baseline") for label in per_trace if label != BASELINE]
    pairs += [(label, DEFAULTS, "vs_defaults") for label in finalists]
    for label, ref, into in pairs:
        if ref in per_trace and {label, ref} <= complete:
            result[into][label] = {m: _versus(per_trace[label], per_trace[ref], traces, m)
                                   for m in _LOWER_IS_BETTER}
    missing = [ref for ref in (BASELINE, DEFAULTS) if ref not in complete]
    if missing:
        result["error"] = (f"{' and '.join(missing)} did not run every promotion trace, "
                           f"so nothing can be compared against it")
        return result
    eligible = [f for f in finalists
                if f in complete and not K.check_measured(scores[f], constraints or [])]
    if not eligible:
        result["error"] = "no finalist ran every promotion trace within the constraints"
        return result
    metric = C.DSE_SCREEN_METRIC
    winner = min(eligible, key=lambda f: (scores[f][metric], finalists.index(f)))
    result["verdict"] = {
        "metric": metric,
        "winner": winner,
        # finalists[0] is the screening winner. When promotion picks another
        # one, the screening list was too small to rank these candidates.
        "screening_winner_held": winner == finalists[0],
        "tuned_beats_baseline": scores[winner][metric] < scores[BASELINE][metric],
        "tuned_beats_defaults": scores[winner][metric] < scores[DEFAULTS][metric],
        "defaults_beat_baseline": scores[DEFAULTS][metric] < scores[BASELINE][metric],
    }
    return result


def search_running(host: str) -> bool:
    """Whether a stage-4 search holds the search tree right now."""
    import ray

    try:
        ray.get_actor(evolver_actor_name(host))
        return True
    except ValueError:
        return False


def promote_finalists(
    host: str, spec: dict, budget_name: str, population: list[dict],
    top_k: int = C.DSE_PROMOTE_TOP_K,
    promote_list_path: Path | str = C.PROMOTE_LIST,
) -> dict:
    """Score the search's top_k candidates on the promotion list, next to
    the baseline host and the untuned port, and name the winner.

    The candidates are built in a fresh copy of the ported tree, the same
    way the search built them. So the port has to be the one the search
    ran on, and the plan in force the one it searched under: a header that
    does not match the plan's knobs fails its static check and is not
    promoted. The baseline is built from the pristine checkout, as
    record_cbp_baseline builds it.

    Each variant runs every trace. All the runs are submitted at once, so
    the cluster's trace slots stay busy; the builds go one at a time,
    because every candidate is written to the same sr_params.h."""
    # Before anything else, including the reset of the pristine CBP2025
    # checkout below, which a gem5 promotion has no business touching.
    require_searchable(host)
    from chia.base.ChiaFunction import get
    from chia_nodes.cbp2025.cbp2025_node import CBP2025Node
    from hosts.cbp2025 import adapter as cbp2025_adapter

    traces = helpers.load_trace_list(promote_list_path)
    port_plan = _port_plan(host, spec)
    constraints = constraint_set(budget_name)
    finalists, passed_over = select_finalists(population, spec, port_plan, constraints, top_k)
    labels = [f"finalist_{i + 1}" for i in range(len(finalists))]
    defaults_header = params_header(spec, port_plan, constraint_set=constraints)
    summary = {
        "host": host,
        "budget": budget_name,
        "promote_list": str(promote_list_path),
        "traces": traces,
        "constraints": [c.as_dict() for c in constraints],
        "population": len(population),
        "passed_over": passed_over,
        "finalists": [
            {"label": label, "id": f["id"], "iteration_found": f.get("iteration_found"),
             "screening": {k: f["metrics"].get(k) for k in ("combined_score", *_PROMOTE_METRICS)},
             "storage_bits": f["storage_bits"], "header": f["solution"]}
            for label, f in zip(labels, finalists)
        ],
        "storage_bits": {
            BASELINE: (port_plan.get("host_storage") or {}).get("baseline_bits"),
            DEFAULTS: K.check_static(defaults_header, spec, port_plan, constraints)
                       .metrics.get("storage_bits"),
            **{label: f["storage_bits"] for label, f in zip(labels, finalists)},
        },
    }
    if not traces:
        return {**summary, "status": "no_traces", "error": f"{promote_list_path} lists no traces"}
    if not finalists:
        return {**summary, "status": "no_finalists",
                "error": f"none of the {len(population)} programs qualifies: {passed_over}. "
                         f"If they all fail the static check, the plan in force is probably "
                         f"not the one the search ran under."}
    if search_running(host):
        return {**summary, "status": "search_running",
                "error": f"a stage-4 search for {host} is running in the search tree; "
                         f"promote after it ends"}

    feature_env = _feature_env(port_plan, spec, host)
    summary["restore"] = cbp2025_adapter.restore_host_checkout(C.CBP2025_ROOT)
    summary["host_revision"] = cbp2025_adapter.checkout_revision()
    search_root = cbp2025_adapter.dse_tree()

    def build(root: str, header: str | None, env: dict | None):
        sources = None if header is None else {"sr_params.h": header.encode()}
        return get(CBP2025Node.build.options(resources={C.CBP2025_HOST_RESOURCE: 1.0})
                   .chia_remote(root, sources, C.BUILD_TIMEOUT_S, env))

    variants = [(BASELINE, C.CBP2025_ROOT, None, None),
                (DEFAULTS, search_root, defaults_header, feature_env),
                *[(label, search_root, f["solution"], feature_env)
                  for label, f in zip(labels, finalists)]]
    binaries, summary["build_failed"] = {}, {}
    for label, root, header, env in variants:
        result = build(root, header, env)
        if result.success:
            binaries[label] = (result.binary, env)
        else:
            summary["build_failed"][label] = result.log[-2000:]
    if BASELINE not in binaries or DEFAULTS not in binaries:
        return {**summary, "status": "build_failed",
                "error": "a reference did not build: "
                         + ", ".join(summary["build_failed"])}

    refs = {
        (label, t): CBP2025Node.run.options(resources={C.CBP2025_RESOURCE: 1.0})
        .chia_remote(binary, f"{C.TRACE_DIR}/{t}", (), C.RUN_TIMEOUT_S, env)
        for label, (binary, env) in binaries.items() for t in traces
    }
    per_trace = {label: {} for label in binaries}
    summary["run_errors"] = {}
    for (label, t), ref in refs.items():
        # A worker lost mid-run (a spot preemption, say) raises here. It is
        # one failed trace, not a reason to lose every other run's result.
        try:
            run = get(ref)
        except Exception as e:  # noqa: BLE001
            summary["run_errors"][f"{label} {t}"] = str(e)[-500:]
            run = None
        ok = run is not None and run.success
        per_trace[label][t] = (cbp2025_adapter.parse_metrics(run.log) or None) if ok else None
    comparison = compare_variants(per_trace, traces, [l for l in labels if l in binaries],
                                  constraints)
    summary.update(per_trace=per_trace, **comparison)
    if "error" in comparison:
        return {**summary, "status": "incomplete"}
    return {**summary, "status": "promoted", "error": None}


if __name__ == "__main__":
    print(json.dumps(list(C.BUDGET_TRACKS_BITS), indent=2))
