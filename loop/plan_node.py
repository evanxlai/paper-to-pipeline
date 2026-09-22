"""Stage 2: the planning node.

One agent, one live shell on the host checkout, two documents out. It is
distill()'s shape -- call, validate, one repair turn, fail closed -- with
three differences that come from what stage 2 actually is.

First, the reply carries two interdependent documents rather than one, so
they are parsed as two fenced blocks and repaired together. Repairing them
separately would let a fix to one invalidate the other: the test plan's
`host_revision` has to equal the port plan's, `risks[].detected_by` names a
test id, and the spec's `unit_tests` coverage is satisfied by the test plan
while its `parameters` coverage is satisfied by the port plan.

Second, the repair runs on the same resumed session with the shell still
attached. distill's repair is fresh and tool-free because its failures are
pure JSON-shape errors; a coverage failure is not. "No hook point covers
/state/2" and "this existing_regression has no clean-tree result" are both
answered by going back and reading, or re-running, the host checkout.

Third, validation is not only the schema. plan_checks decides whether every
spec item reached the plan, and an unmapped item fails the stage -- the
integration agent implements from these two documents and never reads the
paper, so a hole here becomes a guess there.

Artifacts are dumped before the fail-closed check, always. Failing closed
must cost the run its promotion, never its evidence.
"""

from __future__ import annotations

import json

import constants as C
import helpers
import plan_checks
import spec_checks


def _render(findings) -> str:
    """spec_review's finding format, so one reader learns one layout."""
    if not findings:
        return "(none)"
    return "\n".join(
        f"- [{f.severity}] {f.pointer} ({f.code}): {f.message}" for f in findings
    )


def parse_reply(text: str) -> tuple[dict | None, dict | None, list[str]]:
    """Two fenced JSON blocks, port plan first.

    Not `helpers.extract_json_block`: that one keeps the LAST block, so a
    perfectly good two-document reply would lose the port plan in silence and
    the stage would report schema errors about a test plan missing every
    port-plan field."""
    blocks = helpers.extract_json_blocks(text)
    if len(blocks) != 2:
        return None, None, [
            f"expected exactly two fenced json blocks, the port plan then the "
            f"test plan; found {len(blocks)}."
            + (" A block may have been cut off mid-document."
               if text.count("```") % 2 else "")
        ]
    errors: list[str] = []
    documents = []
    for label, block, schema in (
        ("port plan", blocks[0], C.PORT_PLAN_SCHEMA_PATH),
        ("test plan", blocks[1], C.TEST_PLAN_SCHEMA_PATH),
    ):
        # require_jsonschema: the plan schemas put nearly all of their force
        # in nested required, if/then and additionalProperties, none of which
        # the degraded path sees. For a plan that is not a weaker check.
        document, errs = helpers.validate_json(block, schema, require_jsonschema=True)
        documents.append(document)
        errors += [f"{label}: {helpers.truncate(e)}" for e in errs]
    return documents[0], documents[1], errors


def _repair_prompt(errors: list[str], findings, schemas_needed: bool) -> str:
    body = [
        "Your plan pair did not pass. Fix every item below and emit the two "
        "documents again, in full, as two fenced json blocks under the same "
        "two headings. Do not emit a diff or a partial document.",
    ]
    if errors:
        body.append("## Schema errors\n\n" + "\n".join(f"- {e}" for e in errors))
    if findings:
        body.append(
            "## Plan checks\n\nThese are about the plan, not its JSON shape. A "
            "pointer named here is a spec item nothing in your plan claims, or "
            "a claim that disagrees with what the pointer resolves to. Several "
            "of them are answered by re-reading or re-running the host "
            "checkout, which you still have a shell on.\n\n" + _render(findings)
        )
    if schemas_needed:
        # Carried again for distill's reason: the bare validator messages do
        # not say what the missing fields mean.
        body.append(
            "## The port plan schema\n\n```json\n"
            + C.PORT_PLAN_SCHEMA_PATH.read_text()
            + "\n```\n\n## The test plan schema\n\n```json\n"
            + C.TEST_PLAN_SCHEMA_PATH.read_text() + "\n```"
        )
    return "\n\n".join(body)


def make_plan(
    dump,
    spec: dict,
    host: str,
    work_dir: str,
    notes: str,
    tools=None,
    revision: str | None = None,
    repair_turns: int | None = None,
    checks_root: str | None = None,
    baseline: dict | None = None,
) -> tuple[dict, dict]:
    """Plan the port of `spec` into `host`, or refuse to.

    `tools` is injectable so the node can be driven in a test without a
    cluster; in production it is one BashTool rooted at the host checkout.

    `checks_root` is the tree `plan_checks` opens to settle whether a hook
    point's file exists, and it defaults to `work_dir`. The two differ on a
    cluster host: `work_dir` is a path on the worker the agent's shell runs
    on, and this node runs on the head, where that path holds nothing. Such
    a host passes a head-local mirror at the same revision, and `revision`
    then carries the worker checkout's real commit so a mirror that has
    drifted is a planning error rather than a silent one."""
    # Lazy, like spec_review: this module stays importable, and testable,
    # without chia installed.
    from llm import load_prompt, make_llm, run_llm

    tools = [] if tools is None else tools
    turns = C.PLAN_REPAIR_TURNS if repair_turns is None else repair_turns

    # Anything stage 3 refused to decide on a previous run. These are the
    # only messages that travel backwards through the loop, and they are the
    # whole point of the escalation move: the integrator is forbidden to
    # lower a frozen value, so a genuinely wrong one can only be fixed here.
    import plan_revision as _plan_revision

    escalations = _plan_revision.open_escalations(host, spec.get("feature_name"))
    escalation_section = ""
    if escalations:
        escalation_section = (
            "\n\n## Escalations from integration\n\n"
            "A previous run of this plan reached the integration stage and "
            "stopped. Each item below names a value the integration agent is "
            "not allowed to change and says why it could not port against it. "
            "These are not optional. A plan that leaves one of them as it was "
            "sends the next run into the same wall, and it will escalate "
            "again. Resolve each one, and say in the entry's own text what "
            "changed and why.\n\n"
            + "\n".join(
                f"- `{e.get('pointer')}`: {e.get('reason')}"
                + (f"\n  The gate had just reported: "
                   + "; ".join(r.splitlines()[0] for r in e.get("gate_reasons") or [])
                   if e.get("gate_reasons") else "")
                for e in escalations
            )
        )

    prompt = load_prompt(
        "planner.md",
        spec_path=str(C.SPEC_OUT_PATH),
        host_path=work_dir,
        host_name=host,
        bash_timeout=str(C.BASH_TOOL_TIMEOUT_S),
    ) + escalation_section + (
        f"\n\n## The port plan schema\n\n```json\n{C.PORT_PLAN_SCHEMA_PATH.read_text()}\n```"
        f"\n\n## The test plan schema\n\n```json\n{C.TEST_PLAN_SCHEMA_PATH.read_text()}\n```"
        f"\n\n## Feature spec\n\n```json\n{json.dumps(spec, indent=2)}\n```"
        f"\n\n## Host notes\n\n{notes}"
    )

    llm = make_llm(C.LLM_BACKEND, tools, resume=True)  # one threaded session
    resp = run_llm(llm, prompt, tools)
    dump.llm(f"plan_{host}_0", resp)

    port_plan, test_plan, errors = parse_reply(resp.result)
    findings = _checks(spec, port_plan, test_plan, checks_root or work_dir, revision, baseline)
    rounds = [{"turn": 0, "schema_errors": errors, "findings": [f.as_dict() for f in findings]}]

    for turn in range(turns):
        if not errors and not _blocking(findings):
            break
        resp = run_llm(llm, _repair_prompt(errors, findings, bool(errors)), tools)
        dump.llm(f"plan_{host}_repair_{turn}", resp)
        port_plan, test_plan, errors = parse_reply(resp.result)
        findings = _checks(spec, port_plan, test_plan, checks_root or work_dir, revision, baseline)
        rounds.append({
            "turn": turn + 1, "schema_errors": errors,
            "findings": [f.as_dict() for f in findings],
        })

    # Evidence first, verdict second: a refused run that writes nothing is
    # one nobody can diagnose without re-running the whole stage.
    dump.json(f"plan_{host}_rounds.json", rounds)
    if port_plan is not None:
        dump.json(f"plan_{host}_final.json", port_plan)
    if test_plan is not None:
        dump.json(f"tests_{host}_final.json", test_plan)

    # The spec names the feature, not the environment: a run planning tinysc
    # must not write its artifacts under whatever P2P_FEATURE_NAME happens to
    # say. plan_checks already requires the two to agree.
    feature = spec.get("feature_name")
    blocking = _blocking(findings)
    if (errors or blocking) and not C.PLAN_ALLOW_GAPS:
        plan_path, tests_path = helpers.plan_paths(host, feature)
        raise SystemExit(
            f"plan for {host} has {len(errors)} schema error(s) and "
            f"{len(blocking)} unresolved plan error(s); refusing to write "
            f"{plan_path} and {tests_path}:\n"
            + "\n".join(f"  {e}" for e in errors)
            + ("\n" if errors and blocking else "")
            + "\n".join(f"  {f.pointer}: {f.message}" for f in blocking)
            + "\nRe-run with P2P_PLAN_ALLOW_GAPS=1 to write it anyway."
        )

    plan_path, tests_path = helpers.plan_paths(host, feature)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(port_plan, indent=2))
    tests_path.write_text(json.dumps(test_plan, indent=2))
    # Retire any revision an earlier run left beside the old pair. They are
    # corrections to a plan that no longer exists, and `plan_revision.latest`
    # prefers the highest-numbered revision on disk -- so leaving them there
    # means stage 3 never reads the plan this stage just wrote.
    import plan_revision

    retired = plan_revision.retire(host, feature, dump.prefix)
    if retired:
        dump.json(f"plan_{host}_retired_revisions.json", retired)
    # This plan was written with the open escalations in front of it, so
    # they are answered whether or not the answer is a good one. Leaving
    # them open would put them in front of every future planner forever.
    answered = plan_revision.clear_escalations(host, feature, dump.prefix)
    if answered:
        dump.json(f"plan_{host}_escalations_answered.json", {
            "count": answered,
            "path": str(plan_revision.escalation_path(host, feature)),
        })
    return port_plan, test_plan


def _blocking(findings) -> list:
    return [f for f in findings if f.severity == "error"]


def _checks(spec, port_plan, test_plan, work_dir, revision, baseline=None) -> list:
    """Plan checks, plus the two facts only the caller can know.

    `baseline` is the recorded baseline G2 will compare against. Resolving
    every `metrics_equal_baseline` pointer here is the only place it can be
    done cheaply: a pass_condition is frozen for stage 3, so a pointer that
    resolves to nothing costs a whole gate attempt there and can only be
    escalated."""
    if port_plan is None or test_plan is None:
        return []
    findings = plan_checks.run_checks(
        spec, port_plan, test_plan, host_root=work_dir, baseline=baseline,
        repo_root=C.REPO_ROOT)
    if revision is not None and port_plan.get("host_revision") != revision:
        findings.append(spec_checks.Finding(
            "/plan/host_revision", "revision_not_measured", "error",
            f"the plan records {port_plan.get('host_revision')!r} but the checkout is at "
            f"{revision!r}. Every clean-tree result in the test plan is evidence about "
            f"the tree it was measured on and about no other.",
        ))
    return findings
