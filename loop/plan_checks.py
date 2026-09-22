"""Deterministic port-plan checks (stage-2 analogue of spec_checks.py).

Same philosophy as the verify gate and as the spec checks: no LLM opinion
decides whether a plan is complete. Everything here is plain code comparing
two documents the planner already wrote against the spec it planned from, so
nothing below is keyed to a feature, a predictor, or a particular host.

The central obligation is coverage. Every `state` element, `algorithms` entry,
`parameters` entry, `host_interfaces` need and `unit_tests` entry in the spec
must map to something in the plan pair, or the plan fails before integration
starts. An unmapped spec item is not a gap the integrator will notice and ask
about -- it is a gap the integrator fills by guessing, and a guess that builds
and runs is indistinguishable from a port.

The second obligation is everything the two JSON Schemas deliberately cannot
express: uniqueness of an id, a reference that resolves, a verbatim echo that
matches its pointer, and every rule whose two halves live in different
documents. `additionalProperties: false` stops a budget *field*; only code can
stop a knob wired to a macro stage 4 will never mutate.

Severities:
  error  an exact comparison between two values both documents already
         declare: a set difference, a string equality, a pointer that does or
         does not resolve. Always worth a repair turn.
  warn   a parser, a token match or a keyword list fired. Reported, never
         blocking -- these are deliberately loose so that they generalize,
         and a loose parser that blocks deadlocks the stage.
  info   a note that must never count against the plan. `is_worse` ignores
         info entirely, so nothing here should be something you want acted on.

Pointer convention: every finding is anchored in the document it is *about*,
prefixed so the three cannot collide -- `/plan/knobs/2/macro`,
`/tests/correctness/3/pass_condition`, and `/spec/state/1` for a coverage
finding, which is about a spec item nothing in the plan claims. The prefix
matters because spec_review routes findings to reviewers by pointer prefix; an
unprefixed `/knobs/2` would be indistinguishable from a spec pointer if a
plan-review stage is ever added.
"""

from __future__ import annotations

import re
from pathlib import Path

# _HEDGE_RE is imported rather than copied so the two stages agree on what a
# hedge word is. A plan's off_path and a spec's unit test fail the same way
# when they lean on "correctly" instead of naming the mechanism.
from spec_checks import Finding, _HEDGE_RE, tokens

# ------------------------------------------------------------------ pointers


def ptr_get(doc, pointer: str, default=None):
    """Tolerant RFC 6901 resolution: a pointer that does not resolve returns
    `default` rather than raising. A dangling spec_pointer has to become a
    Finding the agent can repair, not a KeyError that kills the stage before
    any other check runs."""
    node = doc
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            if not token.isdigit() or int(token) >= len(node):
                return default
            node = node[int(token)]
        elif isinstance(node, dict):
            if token not in node:
                return default
            node = node[token]
        else:
            return default
    return node


_MISSING = object()


def _resolves(doc, pointer: str) -> bool:
    return ptr_get(doc, pointer, _MISSING) is not _MISSING


# ------------------------------------------------------------------- macros

# dse.params_header_from_spec emits `#define SR_{name.upper()} ...` for every
# feature -- the prefix is fixed in code, not derived from feature_name. The
# expected macro is re-derived here with a one-line f-string rather than by
# calling that function, which does bare spec['parameters'] / p['type'] /
# p['range'] lookups and raises KeyError on a partial spec. A check that
# crashes on a malformed plan reports nothing about the rest of it.
def expected_macro(parameter_name: str) -> str:
    return "SR_" + str(parameter_name).upper()


_MACRO_BODY_RE = re.compile(r"^[A-Z0-9_]+$")


# ------------------------------------------------------------------ coverage


def _check_coverage(spec: dict, plan: dict, tests: dict) -> list[Finding]:
    """Every spec item maps to something. One mechanism per spec section, so
    a reader never has to ask which of two places an item was covered in."""
    out: list[Finding] = []
    mapped = {e.get("spec_pointer") for e in plan.get("spec_map") or []}
    for section, code in (("state", "uncovered_state"), ("algorithms", "uncovered_algorithm")):
        for i, item in enumerate(spec.get(section) or []):
            pointer = f"/{section}/{i}"
            if pointer not in mapped:
                name = (item or {}).get("name", "unnamed")
                out.append(Finding(
                    f"/spec{pointer}", code, "error",
                    f"{section[:-1] if section.endswith('s') else section} '{name}' appears "
                    f"in no spec_map entry. Add one naming the hook_ids that realize it; "
                    f"an unmapped spec item is one the integrator implements by guessing.",
                ))

    resolved = {e.get("spec_pointer") for e in plan.get("interface_resolutions") or []}
    for i, item in enumerate(spec.get("host_interfaces") or []):
        pointer = f"/host_interfaces/{i}"
        if pointer not in resolved:
            need = (item or {}).get("need", "unnamed")
            out.append(Finding(
                f"/spec{pointer}", "uncovered_interface", "error",
                f"need '{need}' has no interface_resolutions entry. Every need gets one, "
                f"including the ones this host meets exactly -- that is what makes the "
                f"decision per need rather than per need the planner found hard.",
            ))

    knobbed = {k.get("spec_pointer") for k in plan.get("knobs") or []}
    for i, item in enumerate(spec.get("parameters") or []):
        pointer = f"/parameters/{i}"
        if pointer not in knobbed:
            name = (item or {}).get("name", "unnamed")
            out.append(Finding(
                f"/spec{pointer}", "uncovered_parameter", "error",
                f"parameter '{name}' has no knobs entry. A parameter missing here is a "
                f"parameter stage 4 cannot search, and nothing downstream notices: the "
                f"port builds, runs, and never moves when the evolver changes it.",
            ))

    tested = {
        e.get("spec_pointer")
        for e in tests.get("correctness") or []
        if e.get("kind") == "spec_unit_test"
    }
    for i, item in enumerate(spec.get("unit_tests") or []):
        pointer = f"/unit_tests/{i}"
        if pointer not in tested:
            name = (item or {}).get("name", "unnamed")
            out.append(Finding(
                f"/spec{pointer}", "uncovered_unit_test", "error",
                f"unit test '{name}' is implemented by no correctness entry of kind "
                f"spec_unit_test. Add one naming its spec_pointer and the test_file it "
                f"lands in.",
            ))
    return out


# ------------------------------------------------------ referential integrity


def _check_references(plan: dict, tests: dict) -> list[Finding]:
    out: list[Finding] = []
    hooks = plan.get("hook_points") or []
    seen: dict[str, int] = {}
    for i, hook in enumerate(hooks):
        hid = (hook or {}).get("id")
        if hid in seen:
            out.append(Finding(
                f"/plan/hook_points/{i}/id", "duplicate_hook_id", "error",
                f"hook id '{hid}' is already used by /plan/hook_points/{seen[hid]}. "
                f"Ids are how spec_map and steps name a site, so a repeat makes one of "
                f"the two references silently point at the wrong file.",
            ))
        else:
            seen[hid] = i
    known_hooks = set(seen)
    for section in ("spec_map", "interface_resolutions", "steps"):
        for i, entry in enumerate(plan.get(section) or []):
            for j, hid in enumerate((entry or {}).get("hook_ids") or []):
                if hid not in known_hooks:
                    out.append(Finding(
                        f"/plan/{section}/{i}/hook_ids/{j}", "unknown_hook_id", "error",
                        f"'{hid}' names no hook point. Known ids: "
                        f"{', '.join(sorted(known_hooks)) or '(none)'}.",
                    ))

    ids: dict[str, str] = {}
    for section in ("correctness", "performance"):
        for i, entry in enumerate(tests.get(section) or []):
            tid = (entry or {}).get("id")
            if tid in ids:
                out.append(Finding(
                    f"/tests/{section}/{i}/id", "duplicate_test_id", "error",
                    f"test id '{tid}' is already used by {ids[tid]}. Ids are unique across "
                    f"correctness and performance together, because steps and risks "
                    f"reference them without saying which bucket they are in.",
                ))
            else:
                ids[tid] = f"/tests/{section}/{i}"
    for i, risk in enumerate(plan.get("risks") or []):
        detected = (risk or {}).get("detected_by")
        if detected is not None and detected not in ids:
            out.append(Finding(
                f"/plan/risks/{i}/detected_by", "unknown_test_id", "error",
                f"'{detected}' names no test-plan entry. Either name one, or drop the "
                f"field -- a risk nothing detects is worth recording as such.",
            ))
    return out


def _check_pointers(spec: dict, plan: dict, tests: dict) -> list[Finding]:
    """Every spec_pointer resolves, and every verbatim echo matches what it
    resolves to. The echo is the redundancy that catches an off-by-one: a
    pointer at the wrong element satisfies every coverage count above while
    aiming the integrator at the wrong thing."""
    out: list[Finding] = []
    checks = [
        ("spec_map", "spec_item", "name", "spec_item_mismatch"),
        ("interface_resolutions", "need", "need", "interface_need_mismatch"),
        ("knobs", "spec_parameter", "name", "knob_parameter_mismatch"),
    ]
    for section, echo_field, spec_field, code in checks:
        for i, entry in enumerate(plan.get(section) or []):
            pointer = (entry or {}).get("spec_pointer")
            if pointer is None:
                continue
            target = ptr_get(spec, pointer, _MISSING)
            if target is _MISSING:
                out.append(Finding(
                    f"/plan/{section}/{i}/spec_pointer", "unresolved_pointer", "error",
                    f"'{pointer}' does not resolve against the feature spec.",
                ))
                continue
            claimed = entry.get(echo_field)
            actual = target.get(spec_field) if isinstance(target, dict) else None
            if claimed != actual:
                out.append(Finding(
                    f"/plan/{section}/{i}/{echo_field}", code, "error",
                    f"the plan calls {pointer} '{claimed}', but the spec calls it "
                    f"'{actual}'. One of the two is pointing at the wrong element.",
                ))

    for i, entry in enumerate(plan.get("open_questions") or []):
        pointer = (entry or {}).get("spec_pointer")
        if pointer is not None and not _resolves(spec, pointer):
            out.append(Finding(
                f"/plan/open_questions/{i}/spec_pointer", "unresolved_pointer", "error",
                f"'{pointer}' does not resolve against the feature spec.",
            ))
    for i, entry in enumerate(tests.get("correctness") or []):
        pointer = (entry or {}).get("spec_pointer")
        if pointer is not None and not _resolves(spec, pointer):
            out.append(Finding(
                f"/tests/correctness/{i}/spec_pointer", "unresolved_pointer", "error",
                f"'{pointer}' does not resolve against the feature spec.",
            ))
    return out


# --------------------------------------------------------------- the knobs


def _check_knobs(spec: dict, plan: dict) -> list[Finding]:
    out: list[Finding] = []
    by_macro: dict[str, int] = {}
    for i, knob in enumerate(plan.get("knobs") or []):
        knob = knob or {}
        name = knob.get("spec_parameter")
        macro = knob.get("macro")
        if name is not None:
            want = expected_macro(name)
            if macro != want:
                out.append(Finding(
                    f"/plan/knobs/{i}/macro", "macro_mismatch", "error",
                    f"'{macro}' is not the define dse.params_header_from_spec emits for "
                    f"parameter '{name}'; that is '{want}'. Stage 4 mutates only that "
                    f"header, so a knob under any other name is invisible to the search.",
                ))
            if not _MACRO_BODY_RE.match(str(name).upper()):
                out.append(Finding(
                    f"/plan/knobs/{i}/spec_parameter", "macro_unrepresentable", "error",
                    f"parameter name '{name}' upper-cases to something that is not a legal "
                    f"C identifier, and params_header_from_spec does no sanitising -- it "
                    f"would emit an uncompilable `#define {want}`.",
                ))
        if macro in by_macro:
            out.append(Finding(
                f"/plan/knobs/{i}/macro", "duplicate_macro", "error",
                f"'{macro}' is already the macro of /plan/knobs/{by_macro[macro]}. Two "
                f"parameters collapsing to one #define means the header defines it twice "
                f"and stage 4 can only move one of them.",
            ))
        else:
            by_macro[macro] = i

        pointer = knob.get("spec_pointer")
        target = ptr_get(spec, pointer, None) if pointer else None
        if isinstance(target, dict) and "default" in target:
            if knob.get("default") != target["default"]:
                out.append(Finding(
                    f"/plan/knobs/{i}/default", "knob_default_drift", "error",
                    f"the plan ships {knob.get('default')!r} where the spec's default is "
                    f"{target['default']!r}. A port that quietly ships a different default "
                    f"measures something the spec does not describe.",
                ))
    return out


def _check_enable_knob(spec: dict, plan: dict, tests: dict) -> list[Finding]:
    """The enable knob's name lives in the port plan and is referenced, by
    absence, from the test plan. Both halves of every rule here sit in
    different documents, which is exactly what JSON Schema cannot reach."""
    out: list[Finding] = []
    enable = plan.get("feature_enable") or {}
    name = enable.get("name")
    knobs = {k.get("spec_parameter"): (i, k) for i, k in enumerate(plan.get("knobs") or [])}
    spec_params = {(p or {}).get("name") for p in spec.get("parameters") or []}

    if name in spec_params:
        if name not in knobs:
            out.append(Finding(
                "/plan/feature_enable/name", "enable_macro_mismatch", "error",
                f"'{name}' is a spec parameter but has no knobs entry, so the one knob "
                f"that turns the feature on is not a knob stage 4 can see.",
            ))
        else:
            i, knob = knobs[name]
            if enable.get("macro") != knob.get("macro"):
                out.append(Finding(
                    "/plan/feature_enable/macro", "enable_macro_mismatch", "error",
                    f"feature_enable names macro {enable.get('macro')!r} while "
                    f"/plan/knobs/{i} names {knob.get('macro')!r} for the same parameter.",
                ))
            if enable.get("binding") != knob.get("binding"):
                out.append(Finding(
                    "/plan/feature_enable/binding", "enable_binding_conflict", "error",
                    f"feature_enable binds '{name}' as {enable.get('binding')!r} while "
                    f"/plan/knobs/{i} binds it as {knob.get('binding')!r}. One knob "
                    f"cannot reach the host two ways.",
                ))

    for i, entry in enumerate(tests.get("correctness") or []):
        for key in (entry or {}).get("env") or {}:
            if key == name:
                out.append(Finding(
                    f"/tests/correctness/{i}/env/{key}", "enable_knob_in_env", "error",
                    "the enable knob is set here as well as by feature_state. The "
                    "knob's name comes from the port plan so there is one place to get "
                    "it wrong; an env entry overrides feature_state and makes the "
                    "entry's declared state a lie.",
                ))

    off_path = enable.get("off_path") or ""
    hedge = _HEDGE_RE.search(off_path)
    if hedge:
        out.append(Finding(
            "/plan/feature_enable/off_path", "hedged_off_path", "warn",
            f"the off path leans on a hedge word ('{hedge.group()}') where it has to say "
            f"why the knob-off run is bit-identical to the baseline rather than merely "
            f"close. G2 checks that claim numerically; a hedge hides what it rests on.",
        ))
    return out


# ------------------------------------------------------- the pair agreeing


def _check_pair(spec: dict, plan: dict, tests: dict) -> list[Finding]:
    out: list[Finding] = []
    for field, code in (("feature_name", "feature_name_mismatch"), ("host", "host_mismatch")):
        if plan.get(field) != tests.get(field):
            out.append(Finding(
                f"/tests/{field}", code, "error",
                f"the test plan says {tests.get(field)!r} and the port plan says "
                f"{plan.get(field)!r}. They are one port.",
            ))
    if plan.get("feature_name") != spec.get("feature_name"):
        out.append(Finding(
            "/plan/feature_name", "feature_name_mismatch", "error",
            f"the plan is for {plan.get('feature_name')!r} but the spec describes "
            f"{spec.get('feature_name')!r}.",
        ))
    if plan.get("host_revision") != tests.get("host_revision"):
        out.append(Finding(
            "/tests/host_revision", "revision_mismatch", "error",
            f"the test plan was written against {tests.get('host_revision')!r} and the "
            f"port plan against {plan.get('host_revision')!r}. The clean-tree results are "
            f"only evidence about the tree they were measured on; against another tree "
            f"they are hearsay.",
        ))
    declared = plan.get("spec_inputs_used")
    actual = (spec.get("source") or {}).get("inputs_used")
    if declared is not None and actual is not None and declared != actual:
        out.append(Finding(
            "/plan/spec_inputs_used", "inputs_used_mismatch", "error",
            f"the plan records the {declared!r} arm but the spec was produced by the "
            f"{actual!r} arm. Ablation 2 compares two ports of the same feature into the "
            f"same host and cannot tell them apart if this is wrong.",
        ))
    return out


# ------------------------------------------------------ the test plan alone

_VACUOUS_PATTERNS = {"", ".", ".*", ".+", "^", "$", "(.*)", "[\\s\\S]*"}


def _check_test_plan(tests: dict) -> list[Finding]:
    out: list[Finding] = []
    metric_keys = set(tests.get("metric_keys") or [])

    def known(metric, pointer, code="unknown_metric"):
        if metric is not None and metric not in metric_keys:
            out.append(Finding(
                pointer, code, "error",
                f"'{metric}' is not in metric_keys {sorted(metric_keys)}. The gate reads "
                f"metrics by those names, so an unknown one reports as a missing metric "
                f"and reads like a broken host rather than a broken plan.",
            ))

    kinds = [(e or {}).get("kind") for e in tests.get("correctness") or []]
    if "feature_off_baseline" not in kinds:
        out.append(Finding(
            "/tests/correctness", "missing_feature_off_baseline", "error",
            "no correctness entry of kind feature_off_baseline, so G2 has nothing to "
            "decide and the strongest regression the pipeline has goes unrun.",
        ))

    for i, entry in enumerate(tests.get("correctness") or []):
        entry = entry or {}
        at = f"/tests/correctness/{i}"
        pc = entry.get("pass_condition") or {}
        kind, state, pkind = entry.get("kind"), entry.get("feature_state"), pc.get("kind")

        if kind == "feature_off_baseline" and state != "off":
            out.append(Finding(
                f"{at}/feature_state", "feature_off_baseline_on", "error",
                f"a feature_off_baseline entry running with the knob {state!r} measures "
                f"the feature and calls the result a baseline.",
            ))
        if state == "both" and pkind == "metrics_equal_baseline":
            out.append(Finding(
                f"{at}/feature_state", "contradictory_both", "error",
                "'both' applies the same pass condition to the feature-on run as to the "
                "feature-off one, so this entry asserts that turning the feature on "
                "changes no metric -- that the feature does nothing.",
            ))
        clean = entry.get("clean_tree_result") or {}
        if kind == "existing_regression" and clean.get("passed") is False and pkind == "exit_zero":
            out.append(Finding(
                f"{at}/pass_condition", "unpassable_regression", "error",
                "the plan records that this test already fails on the clean tree and then "
                "demands it exit 0, so the port can never clear the gate. Use "
                "matches_clean_tree, which requires it to fail the same way.",
            ))
        pattern = pc.get("pattern")
        if pattern is not None:
            if pattern.strip() in _VACUOUS_PATTERNS:
                out.append(Finding(
                    f"{at}/pass_condition/pattern", "vacuous_pass_condition", "warn",
                    f"the pattern {pattern!r} matches everything, so the gate cannot "
                    f"decide whether this entry passed.",
                ))
            try:
                re.compile(pattern)
            except re.error as e:
                out.append(Finding(
                    f"{at}/pass_condition/pattern", "uncompilable_pattern", "error",
                    f"Python's re rejects this pattern ({e}). The schema calls the dialect "
                    f"ECMA-262 but the gate evaluates it with re, so this crashes the gate "
                    f"rather than failing the test.",
                ))
        for j, metric in enumerate(pc.get("metrics") or []):
            known(metric, f"{at}/pass_condition/metrics/{j}")
        known(pc.get("metric"), f"{at}/pass_condition/metric")

    for i, entry in enumerate(tests.get("performance") or []):
        entry = entry or {}
        at = f"/tests/performance/{i}"
        known(entry.get("metric"), f"{at}/metric")
        for j, companion in enumerate((entry.get("block_threshold") or {}).get("no_regression") or []):
            known((companion or {}).get("metric"), f"{at}/block_threshold/no_regression/{j}/metric")

    for at, run in _runs(tests):
        template = (run or {}).get("command_template")
        if (run or {}).get("mode") == "command_per_trace" and template is not None:
            placeholders = set(re.findall(r"\{([a-z_]*)\}", template))
            if placeholders != {"trace"}:
                out.append(Finding(
                    f"{at}/command_template", "missing_trace_placeholder", "error",
                    f"a per-trace command must contain '{{trace}}' and no other "
                    f"placeholder; this one has {sorted(placeholders) or 'none'}.",
                ))

    if (tests.get("baseline_rel_tol") or 0) > 0 and not tests.get("notes"):
        out.append(Finding(
            "/tests/baseline_rel_tol", "notes_missing_for_tolerance", "warn",
            "a non-zero G2 tolerance is a claim that this host is not reproducible run to "
            "run, and no notes say why.",
        ))
    return out


def _runs(tests: dict):
    """Every `run` block in the test plan, with the pointer it sits at."""
    smoke = tests.get("smoke") or {}
    if "run" in smoke:
        yield "/tests/smoke/run", smoke["run"]
    for i, entry in enumerate(tests.get("performance") or []):
        if "run" in (entry or {}):
            yield f"/tests/performance/{i}/run", entry["run"]


# ------------------------------------------------------------- the leftovers


def _check_hooks_used(plan: dict) -> list[Finding]:
    out: list[Finding] = []
    referenced: set[str] = set()
    stepped: set[str] = set()
    for section in ("spec_map", "interface_resolutions", "steps"):
        for entry in plan.get(section) or []:
            for hid in (entry or {}).get("hook_ids") or []:
                referenced.add(hid)
                if section == "steps":
                    stepped.add(hid)
    for i, hook in enumerate(plan.get("hook_points") or []):
        hid = (hook or {}).get("id")
        if hid not in referenced:
            out.append(Finding(
                f"/plan/hook_points/{i}/id", "orphan_hook", "warn",
                f"nothing references hook '{hid}'. Either some spec item belongs here and "
                f"the mapping is missing, or the hook point is not part of this port.",
            ))
        elif hid not in stepped:
            out.append(Finding(
                f"/plan/hook_points/{i}/id", "unstepped_hook", "warn",
                f"hook '{hid}' is mapped but no step lands it, so no increment in the plan "
                f"produces the code it describes.",
            ))
    return out


# "storage" is deliberately absent: a plan legitimately says things like "the
# host has no storage model to satisfy", and a keyword that fires on the
# repository's own worked example is a keyword nobody will keep.
_BUDGET_RE = re.compile(r"\b(budget|iso-budget|allowance|donor|make room)\b", re.I)
_BUDGET_EXEMPT = re.compile(r"\battempt budget\b", re.I)


def _check_budget_language(plan: dict, tests: dict) -> list[Finding]:
    """`additionalProperties: false` stops a budget field. It cannot stop a
    budget *instruction* inside a change or a rationale, and the integrator
    reads those as prose it is meant to act on."""
    out: list[Finding] = []
    for label, doc in (("plan", plan), ("tests", tests)):
        for pointer, text in _strings(doc, f"/{label}"):
            if _BUDGET_EXEMPT.search(text):
                continue
            hit = _BUDGET_RE.search(text)
            if hit:
                out.append(Finding(
                    pointer, "budget_language", "warn",
                    f"this field talks about a resource budget ('{hit.group()}'). Only "
                    f"stage 4 knows about constraints; the integrator never shrinks a host "
                    f"structure to make room, so a budget written here is an instruction "
                    f"no stage is allowed to follow.",
                ))
    return out


def _strings(node, pointer: str):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _strings(value, f"{pointer}/{i}")
    elif isinstance(node, str):
        yield pointer, node


def _check_risks(plan: dict) -> list[Finding]:
    return [
        Finding(
            f"/plan/risks/{i}", "undetected_risk", "info",
            f"no test detects this risk: {(risk or {}).get('risk', '')[:120]}",
        )
        for i, risk in enumerate(plan.get("risks") or [])
        if not (risk or {}).get("detected_by")
    ]


# ------------------------------------------------------- against the checkout


def _check_checkout(plan: dict, host_root) -> list[Finding]:
    """The two facts that can only be settled by looking at the tree the plan
    claims to have been written against. `observed` prose is deliberately not
    checked: it is free text, there is no parse that would not manufacture
    errors."""
    out: list[Finding] = []
    root = Path(host_root)
    for i, hook in enumerate(plan.get("hook_points") or []):
        hook = hook or {}
        rel = hook.get("file")
        if not rel:
            continue
        exists = (root / rel).exists()
        if hook.get("action") == "modify" and not exists:
            out.append(Finding(
                f"/plan/hook_points/{i}/file", "hook_file_missing", "error",
                f"'{rel}' does not exist under {root}, so the `observed` note describing "
                f"what it does today cannot have come from reading it.",
            ))
        elif hook.get("action") == "create" and exists:
            out.append(Finding(
                f"/plan/hook_points/{i}/file", "hook_file_exists", "error",
                f"'{rel}' already exists under {root}; a plan to create it is a plan to "
                f"clobber code nobody read.",
            ))
        elif exists and hook.get("symbol"):
            try:
                body = (root / rel).read_text(errors="replace")
            except OSError:
                continue
            symbol = str(hook["symbol"])
            if symbol not in body and not (tokens(symbol) & tokens(body)):
                out.append(Finding(
                    f"/plan/hook_points/{i}/symbol", "symbol_not_found", "warn",
                    f"'{symbol}' does not occur in {rel}. This is a substring scan and a "
                    f"symbol can legitimately be spelled differently in the file than in "
                    f"the plan, so check before believing it.",
                ))
    return out


# ------------------------------------------------------------------- driver


def run_checks(
    spec: dict, port_plan: dict, test_plan: dict, host_root=None
) -> list[Finding]:
    """All deterministic plan checks, in a stable order.

    `host_root` is optional for the same reason `budget_bits` is optional in
    spec_checks.run_checks: the pure checks stay unit-testable with no
    filesystem, and the two checkout-dependent ones only run when the caller
    passes the tree the plan was actually written against."""
    findings: list[Finding] = []
    findings += _check_coverage(spec, port_plan, test_plan)
    findings += _check_references(port_plan, test_plan)
    findings += _check_pointers(spec, port_plan, test_plan)
    findings += _check_knobs(spec, port_plan)
    findings += _check_enable_knob(spec, port_plan, test_plan)
    findings += _check_pair(spec, port_plan, test_plan)
    findings += _check_test_plan(test_plan)
    findings += _check_hooks_used(port_plan)
    findings += _check_budget_language(port_plan, test_plan)
    findings += _check_risks(port_plan)
    if host_root is not None:
        findings += _check_checkout(port_plan, host_root)
    return findings
