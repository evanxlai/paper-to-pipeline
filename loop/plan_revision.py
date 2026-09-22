"""Stage 3's narrow door back into the stage-2 artifacts.

Why this exists. During integration the plan sometimes turns out to be wrong
about the tree: a hook point names a symbol that has moved, an `observed` block
describes code that is not there, a correctness command names a build target
this checkout does not produce. Re-running stage 2 to fix that is the wrong
price. The plan node needs the reviewed spec, the host notes, a fresh shell on
the checkout and a full read of the tree, and it re-derives every decision that
was already right in order to fix the one that was not. So stage 3 may revise
the plan in place, and a stage-2 re-run is reserved for defects stage 3 may not
decide.

What this module exists to prevent. The test plan *is* the gate. Every
threshold, tolerance, metric name, pass condition and workload that
`gate.check_gate` weighs is declared there -- the gate holds no defaults, on
purpose, so that no condition is one nobody wrote down. That makes the party
proposing a revision the same party the revision judges. An unguarded in-place
edit therefore lets the integrator clear the gate by lowering the bar instead
of meeting it, which is the one outcome the whole stage split exists to
prevent: verification is deterministic and the agent never self-reports
success.

`plan_checks.run_checks` is not that guard. It decides whether one pair is
internally coherent and still covers the spec, and it has no notion of a
previous version -- so it cannot see a revision that is perfectly coherent and
simply weaker. The missing comparison is this module. Its precedent is
`spec_checks.is_worse`, which is how stage 1.5 refuses a review round that made
the spec worse; the difference is that a plan cannot be judged by counting
findings, because a weaker test plan produces fewer of them.

The line drawn here is not "small change versus large change". It is who the
change serves:

  a factual correction -- where to look, what the code there does, which
      command builds it -- is revisable in place;
  a weaker demand -- a lower threshold, a wider tolerance, a deleted test, a
      rewritten pass condition -- is not, and escalates to a stage-2 re-run.

Classification is by field, never by the agent's account of its own intent.
Two rules cover every field, so that what is allowed can be read off a table
rather than reasoned about per case:

  FROZEN       the revision must repeat the value exactly.
  APPEND-ONLY  a keyed collection may gain entries and may never lose one;
               a surviving entry is frozen except for a named allowlist.

Note what is absent: no rule here compares two numbers for looseness. Freezing
a threshold outright rather than requiring it to move one way is deliberate.
Monotonic comparison is where this kind of guard goes wrong -- every threshold
in the test plan has its own sense of "tighter", `no_regression` bands invert
it, and one sign error silently readmits the whole hazard. Nothing legitimate
is lost: a mid-run tightening is not something the judged party needs, and a
threshold that is genuinely wrong is a measurement-design defect, which is
exactly what escalation is for.

One more boundary, which decides what does *not* belong in this module. Where
another layer can hold a condition itself, this guard should not hold it by
proxy -- two places holding one rule is how they drift apart, and the copy
that drifts is the one nobody is testing.

Two fields show what that means in practice. A revision that introduces
budget language needs no rule here, because `plan_checks._check_budget_language`
already rejects it on the revised pair: only the DSE stage knows about
constraints, and that is where the rule lives. And `performance[].timeout_seconds`
was frozen for a while, because `plan_runner._measure` scores the mean over
the traces that completed and `gate.check_gate` did not look at the rest, so a
shorter timeout scored the entry on the easy subset. G5 now blocks any
performance entry with a failed trace. The hole belonged to the gate, the gate
closed it, and the freeze came out -- a plan that guessed a timeout too short
for this host is wrong about the tree, which is the revisable class.

The test that distinguishes the two cases: can the gate see the defect in what
it already measures? If it can, it should refuse it, and a freeze here only
hides the gap. If it cannot -- as with a `performance[].run` change that works
and reports a better number against a fixed comparison point -- then this is
the only layer that can, and the field is frozen.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import helpers
import plan_checks
import plan_node
from spec_checks import Finding

# The agent announces a revision with this heading, and code keys off the
# heading rather than off "the reply happens to contain two json blocks". A
# debug turn that quotes a pair of JSON snippets while explaining a failure is
# a normal thing to do, and reading that as a proposal would hand the writer
# path a document nobody meant to propose.
REVISION_MARKER = "## Plan revision"

# The other outcome: the agent has concluded the plan is wrong in a way this
# module will not let it fix. That is a real finding and the end of the
# attempt, not a failure to be retried -- so it is machine-readable, and
# `integrate` turns it into a distinct status rather than burning the
# remaining attempts on a defect no edit to the checkout can reach.
ESCALATION_RE = re.compile(
    r"^\s*PLAN ESCALATION:\s*(?P<pointer>\S+)\s*(?:--|—|-)\s*(?P<reason>.+)$",
    re.MULTILINE,
)

# ------------------------------------------------------------ the field table

# Values a revision must repeat exactly, in both documents. `host_revision` is
# frozen rather than re-checked against the tree because the integrator is
# working the same checkout stage 2 read: if the revision disagrees, either the
# tree moved under the port or the agent is restating evidence it cannot have
# re-measured, and both are stage-2 business. `spec_inputs_used` is an ablation
# label -- ablation 2 compares two ports of one feature into one host, and a
# run that relabels itself mid-flight is one nobody can place afterwards.
_FROZEN_TOP = ("feature_name", "host", "host_revision", "spec_inputs_used")

# Port plan: collection name -> (key field, fields a revision may change).
# Everything not listed as revisable is frozen. The keys are what identifies
# "the same entry" across two versions; an entry whose key disappears is a
# deletion regardless of what replaced it.
_PORT_COLLECTIONS = {
    # The macro is the only name stage 4 can mutate and the default is
    # cross-checked against the spec, so both are frozen. Which host-native
    # knob the macro drives, and how the value reaches the host, are facts
    # about the tree that integration is entitled to correct.
    "knobs": ("spec_pointer", {"host_knob", "binding", "notes"}),
    # A host knob's macro is what stage 4 mutates and its default is the clean
    # tree's value, which G2 depends on, so both are frozen, as is its type.
    # Where the symbol lives, how the value reaches it and which values the
    # host really tolerates are facts integration can be first to learn.
    "host_knobs": (
        "name",
        {"host_symbol", "file", "observed", "binding", "range", "description", "notes"},
    ),
    # The legitimate revision, and the common one: the same spec item now
    # lands at different hook points, realized a different way. `spec_item` is
    # the verbatim echo that stops an off-by-one pointer from satisfying
    # coverage while aiming the integrator at the wrong element.
    "spec_map": ("spec_pointer", {"realization", "hook_ids"}),
    # `status` is revisable because "this host facility does not actually
    # work" is precisely what integration discovers; the schema already forces
    # a `fidelity_note` for fallback and unavailable, and a drop in fidelity
    # raises a warn below so it reaches a human through the revision record.
    "interface_resolutions": (
        "spec_pointer",
        {"status", "resolution", "rationale", "fidelity_note", "hook_ids"},
    ),
    # The planner had the tree in front of it and took a reading; stage 3
    # implements that reading. Re-answering it silently is the thing
    # integrator.md forbids, so `assumption` is frozen while the cost of being
    # wrong -- which integration is the first to learn -- is not.
    "open_questions": ("question", {"spec_pointer", "cost_if_wrong"}),
}

# Test plan: same shape. This is the half the gate reads, so the allowlists are
# short and every one of them is a path or a plumbing detail rather than a bar.
_TESTS_COLLECTIONS = {
    # `command` is revisable and is the reason this feature exists: a test
    # whose command names the wrong target fails for a reason no edit to the
    # feature can fix. What the entry *demands* -- its kind, which state it
    # runs in, its pass condition, and the clean-tree result it is measured
    # against -- is frozen. `clean_tree_result` especially: it was measured on
    # an unmodified tree that no longer exists, so a revision cannot honestly
    # restate it.
    "correctness": (
        "id",
        {"description", "command", "env", "timeout_seconds", "test_file"},
    ),
    # `run` is listed here so the generic rule ignores it, and is then judged
    # by `_check_performance_run` below, which is the only field in either
    # document whose revisability depends on the rest of its entry.
    #
    # `timeout_seconds` is revisable because G5 blocks a performance entry
    # with any failed trace, so a shortened timeout is refused at the gate
    # rather than rewarded here. See the boundary note in the module
    # docstring: it was frozen until that clause existed.
    "performance": ("id", {"description", "run", "timeout_seconds"}),
}

# Fidelity, worst last. Used only to decide whether an
# `interface_resolutions[].status` change is worth a warn.
_FIDELITY = {"exact": 0, "fallback": 1, "unavailable": 2}


# --------------------------------------------------------------- the comparer


def _entries(document: dict, name: str, key: str) -> dict:
    """One collection as {key value: entry}, skipping entries with no key.

    A missing or duplicated key is not this module's error to report: the
    schema requires the field and `plan_checks` reports duplicates, and both
    run on the revised pair before this does."""
    out: dict = {}
    for entry in document.get(name) or []:
        if isinstance(entry, dict) and entry.get(key) is not None:
            out.setdefault(json.dumps(entry[key], sort_keys=True), entry)
    return out


def _check_collection(
    label: str, old: dict, new: dict, name: str, key: str, revisable: set
) -> list[Finding]:
    """Append-only, with a per-entry allowlist. `label` is the pointer root
    (`/plan` or `/tests`) so a finding reads the same way `plan_checks`' do."""
    out: list[Finding] = []
    before, after = _entries(old, name, key), _entries(new, name, key)

    for handle, entry in before.items():
        shown = json.loads(handle)
        if handle not in after:
            out.append(Finding(
                f"{label}/{name}", "revision_deleted_entry", "error",
                f"the revision drops the {name} entry {key}={shown!r}. A revision may "
                f"add to a collection and may never remove from one: an entry that "
                f"disappears is a demand the port no longer has to meet, and nothing "
                f"downstream can tell that from an entry that was never there.",
            ))
            continue
        replacement = after[handle]
        index = (new.get(name) or []).index(replacement)
        for field in sorted(set(entry) | set(replacement)):
            if field in revisable or entry.get(field) == replacement.get(field):
                continue
            out.append(Finding(
                f"{label}/{name}/{index}/{field}", "revision_froze_field", "error",
                f"{field!r} is frozen on a {name} entry; this revision changes it from "
                f"{_brief(entry.get(field))} to {_brief(replacement.get(field))}. "
                f"Revisable on this entry: {', '.join(sorted(revisable)) or 'nothing'}. "
                f"If the frozen value is genuinely wrong, escalate instead of "
                f"rewriting it -- see the revision rules in your prompt.",
            ))
    return out


def _brief(value) -> str:
    """A field value short enough to sit inside a finding message."""
    return helpers.truncate(json.dumps(value, sort_keys=True), 160)


def _render(findings) -> str:
    """`plan_node`'s finding layout, repeated rather than imported from its
    private name: the agent reading these has already read stage 2's repair
    prompt, and one reader should learn one layout."""
    if not findings:
        return "(none)"
    return "\n".join(
        f"- [{f.severity}] {f.pointer} ({f.code}): {f.message}" for f in findings
    )


def _check_frozen_top(old_port, old_tests, new_port, new_tests) -> list[Finding]:
    out: list[Finding] = []
    for label, old, new in (
        ("/plan", old_port, new_port), ("/tests", old_tests, new_tests),
    ):
        for field in _FROZEN_TOP:
            if old.get(field) == new.get(field):
                continue
            out.append(Finding(
                f"{label}/{field}", "revision_froze_field", "error",
                f"{field!r} identifies this plan rather than describing the port, and "
                f"this revision changes it from {_brief(old.get(field))} to "
                f"{_brief(new.get(field))}.",
            ))
    return out


def _check_metric_keys(old_tests: dict, new_tests: dict) -> list[Finding]:
    """Append-only. Adding a key widens what G2 has to match and is therefore
    safe; dropping one retires a metric that was disagreeing with baseline,
    which is how a knob-off path that is not baseline-identical gets through."""
    dropped = [
        k for k in (old_tests.get("metric_keys") or [])
        if k not in (new_tests.get("metric_keys") or [])
    ]
    if not dropped:
        return []
    return [Finding(
        "/tests/metric_keys", "revision_deleted_entry", "error",
        f"the revision drops {dropped} from metric_keys. G2 compares exactly these "
        f"between the feature-off run and the recorded baseline, so removing one "
        f"stops the gate asking about a metric rather than making it agree.",
    )]


def _check_tolerance(old_tests: dict, new_tests: dict) -> list[Finding]:
    before, after = old_tests.get("baseline_rel_tol") or 0, new_tests.get("baseline_rel_tol") or 0
    if before == after:
        return []
    return [Finding(
        "/tests/baseline_rel_tol", "revision_froze_field", "error",
        f"baseline_rel_tol is frozen; this revision moves it from {before} to {after}. "
        f"It is G2's tolerance, and on a deterministic trace-driven host the only "
        f"honest value is the one the plan node measured against the clean tree.",
    )]


def _check_smoke(old_tests: dict, new_tests: dict) -> list[Finding]:
    """G4's declared input. `run` and `timeout_seconds` are plumbing; the
    workload set is the condition."""
    out: list[Finding] = []
    before, after = old_tests.get("smoke") or {}, new_tests.get("smoke") or {}
    if before.get("trace_list") != after.get("trace_list"):
        out.append(Finding(
            "/tests/smoke/trace_list", "revision_froze_field", "error",
            f"the smoke trace list is frozen; this revision moves it from "
            f"{_brief(before.get('trace_list'))} to {_brief(after.get('trace_list'))}.",
        ))
    dropped = [t for t in (before.get("traces") or []) if t not in (after.get("traces") or [])]
    if dropped:
        out.append(Finding(
            "/tests/smoke/traces", "revision_deleted_entry", "error",
            f"the revision drops the smoke workloads {dropped}. G4 asks whether the "
            f"feature-on build runs at all, so a shorter list is a weaker question.",
        ))
    return out


def _check_host_storage(old_port: dict, new_port: dict) -> list[Finding]:
    """`host_storage.baseline_bits` is frozen; its terms are not.

    The number was measured on the clean tree, like a `clean_tree_result`,
    and that tree no longer exists by stage 3, so a revision cannot honestly
    restate it. The terms are the plan's reading of the host's accounting and
    may be corrected; `plan_checks` then requires the corrected terms to
    reproduce the frozen number."""
    old = (old_port.get("host_storage") or {}).get("baseline_bits")
    new = (new_port.get("host_storage") or {}).get("baseline_bits")
    if old is not None and new != old:
        return [Finding(
            "/plan/host_storage/baseline_bits", "revision_froze_field", "error",
            f"baseline_bits is frozen at {old}; this revision says {new}. It was "
            f"measured on the clean tree, which a revision cannot re-measure.",
        )]
    return []


def _check_feature_enable(old_port: dict, new_port: dict) -> list[Finding]:
    """The knob's identity is frozen; the prose about its off path is not, but
    a change to it is recorded.

    `name` and `macro` are frozen for the reason `knobs[].macro` is: stage 4
    mutates one generated header, and integrator.md forbids renaming a knob.
    `default_off` and `off_path` are descriptions of a mechanism, and G2 tests
    the mechanism numerically rather than reading the prose -- so rewriting
    them cannot loosen the gate. It can still quietly retire a promise
    somebody made, which is what the warn is for: it lands in the revision
    record, where a human reads it."""
    out: list[Finding] = []
    before, after = old_port.get("feature_enable") or {}, new_port.get("feature_enable") or {}
    for field in ("name", "macro"):
        if before.get(field) != after.get(field):
            out.append(Finding(
                f"/plan/feature_enable/{field}", "revision_froze_field", "error",
                f"the enable knob's {field!r} is frozen; this revision changes it from "
                f"{_brief(before.get(field))} to {_brief(after.get(field))}. Renaming "
                f"the one knob that turns the feature on strands every artifact that "
                f"already refers to it.",
            ))
    for field in ("default_off", "off_path"):
        if before.get(field) != after.get(field):
            out.append(Finding(
                f"/plan/feature_enable/{field}", "revision_restated_off_path", "warn",
                f"this revision rewrites the enable knob's {field!r}. G2 measures the "
                f"off path rather than reading this text, so the claim has been "
                f"restated after the fact; it is recorded here so the restatement is "
                f"visible next to the port that prompted it.",
            ))
    return out


def _check_performance_run(old_tests: dict, new_tests: dict) -> list[Finding]:
    """`run` is revisable on a performance entry only when both sides of the
    comparison go through it.

    `plan_runner._run_performance` measures the feature-on side by handing the
    traces to `_measure` with this entry's `run`. Where the comparison point
    comes from then decides whether revising `run` is symmetric:

    `measure_feature_off` (the default) calls `_measure` a second time with
    the same `run` and the knob off. A changed command moves both sides, so
    `relative_improvement` stays honest and the legitimate correction -- the
    plan named a binary this tree does not build -- costs nothing.

    `recorded` reads the comparison point out of the baseline document the
    host recorded before the port existed. `run` then feeds only the measured
    side, against a fixed number. Revising it is a way to move
    `relative_improvement` without touching a threshold, a trace list or the
    baseline -- the three things the table above locks -- so for those entries
    it is frozen.

    The asymmetry is worth one bespoke rule rather than a warn, because unlike
    `feature_enable.off_path` this field is not inert: it changes a number G5
    computes. A warn would record the loosening after the gate had already
    accepted it. An entry whose command is genuinely wrong escalates, which
    also leaves the tree the other honest option -- build the target the plan
    named.

    Reading `source` off the pair in force is safe because `baseline` is
    frozen by omission from the allowlist, so a revision cannot move an entry
    between the two cases in order to unlock this field."""
    out: list[Finding] = []
    before = _entries(old_tests, "performance", "id")
    after = _entries(new_tests, "performance", "id")
    for handle, entry in before.items():
        if handle not in after:
            continue  # already reported as a deletion
        replacement = after[handle]
        if entry.get("run") == replacement.get("run"):
            continue
        source = (entry.get("baseline") or {}).get("source", "measure_feature_off")
        if source != "recorded":
            continue
        index = (new_tests.get("performance") or []).index(replacement)
        out.append(Finding(
            f"/tests/performance/{index}/run", "revision_froze_field", "error",
            f"`run` is frozen on this entry because its baseline source is 'recorded'. "
            f"The comparison point was measured before the port existed, so `run` feeds "
            f"only the measured side and changing it moves the improvement without "
            f"moving the bar. Build the target the plan named, or escalate. (`run` is "
            f"revisable on an entry whose baseline source is 'measure_feature_off', "
            f"where both sides go through it.)",
        ))
    return out


def _check_rejected_alternatives(old_port: dict, new_port: dict) -> list[Finding]:
    """Append-only. These were decided against this tree, and integrator.md
    forbids revisiting them -- an alternative that turns out to be necessary is
    a plan revision in the escalating sense, not a quiet deletion."""
    def by_text(document):
        structure = document.get("structure") or {}
        return {
            (e or {}).get("alternative"): e
            for e in (structure.get("rejected_alternatives") or [])
        }

    before, after = by_text(old_port), by_text(new_port)
    out: list[Finding] = []
    for text, entry in before.items():
        if text not in after:
            out.append(Finding(
                "/plan/structure/rejected_alternatives", "revision_deleted_entry", "error",
                f"the revision drops the rejected alternative {_brief(text)}. Dropping "
                f"the record of a road not taken is how the port ends up on it without "
                f"anyone deciding to.",
            ))
        elif after[text] != entry:
            out.append(Finding(
                "/plan/structure/rejected_alternatives", "revision_froze_field", "error",
                f"the revision rewrites why {_brief(text)} was rejected. That reason was "
                f"reached against this tree before the port existed.",
            ))
    return out


def _check_fidelity(old_port: dict, new_port: dict) -> list[Finding]:
    """A resolution that moved toward less fidelity. Allowed -- discovering
    that a host facility does not do what it looked like it did is the whole
    point of letting integration revise -- but never silent: this is the text
    that becomes PORT_NOTES.md, and the results write-up depends on it."""
    before = _entries(old_port, "interface_resolutions", "spec_pointer")
    after = _entries(new_port, "interface_resolutions", "spec_pointer")
    out: list[Finding] = []
    for handle, entry in before.items():
        if handle not in after:
            continue  # already reported as a deletion
        was, now = entry.get("status"), after[handle].get("status")
        if _FIDELITY.get(now, 0) > _FIDELITY.get(was, 0):
            out.append(Finding(
                f"/plan/interface_resolutions/{json.loads(handle)}/status",
                "revision_lost_fidelity", "warn",
                f"this revision downgrades {json.loads(handle)} from {was!r} to {now!r}. "
                f"The port is now further from the paper here than the plan said it "
                f"would be, and the fidelity_note is what the write-up will report.",
            ))
    return out


def guard(old_port: dict, old_tests: dict, new_port: dict, new_tests: dict) -> list[Finding]:
    """Everything `plan_checks` cannot see, because it judges one pair.

    Errors are refusals. Warns are recorded and do not block, matching the
    severity contract the rest of the loop uses -- and matching `gate.py`'s
    reason: anything handed back as a blocking reason is work the next turn
    will try to do, so an observation must not be filed among them."""
    findings: list[Finding] = []
    findings += _check_frozen_top(old_port, old_tests, new_port, new_tests)
    findings += _check_metric_keys(old_tests, new_tests)
    findings += _check_tolerance(old_tests, new_tests)
    findings += _check_smoke(old_tests, new_tests)
    findings += _check_performance_run(old_tests, new_tests)
    findings += _check_feature_enable(old_port, new_port)
    findings += _check_host_storage(old_port, new_port)
    findings += _check_rejected_alternatives(old_port, new_port)
    for name, (key, revisable) in _PORT_COLLECTIONS.items():
        findings += _check_collection("/plan", old_port, new_port, name, key, revisable)
    for name, (key, revisable) in _TESTS_COLLECTIONS.items():
        findings += _check_collection("/tests", old_tests, new_tests, name, key, revisable)
    findings += _check_fidelity(old_port, new_port)
    return findings


# ------------------------------------------------------------------ the entry


def blocking(findings) -> list:
    """`plan_node`'s rule, so one severity means one thing across both stages."""
    return [f for f in findings if f.severity == "error"]


def proposed(reply: str) -> bool:
    """Did this debug turn propose a revision, as opposed to explaining one?"""
    return REVISION_MARKER.lower() in (reply or "").lower()


def escalation(reply: str) -> dict | None:
    """The agent's claim that this defect is stage 2's, not its own."""
    match = ESCALATION_RE.search(reply or "")
    if match is None:
        return None
    return {
        "pointer": match.group("pointer").rstrip(","),
        "reason": match.group("reason").strip(),
    }


def review(
    spec: dict,
    work_dir: str,
    old_port: dict,
    old_tests: dict,
    reply: str,
    checks_root: str | None = None,
) -> tuple[dict | None, dict | None, list[str], list]:
    """Judge a proposed revision. Writes nothing.

    Returns the parsed pair plus the two failure channels the caller has to
    record either way: `errors` from the schema, `findings` from the plan
    checks and from `guard`. Both are returned even when the pair is rejected,
    for `plan_node`'s reason -- failing closed must cost the run its
    promotion, never its evidence.

    `checks_root` is where `plan_checks` looks for the files a hook point
    names, and it defaults to `work_dir` because on a one-machine host they
    are the same directory. They are not the same on a cluster host: the
    checkout lives on a worker and this function runs on the head, where
    that path does not exist and every hook point would be reported
    missing. Such a host passes a head-local mirror of the tree at the same
    revision. The agent still edits `work_dir` and nothing else."""
    new_port, new_tests, errors = plan_node.parse_reply(reply)
    if new_port is None or new_tests is None:
        return new_port, new_tests, errors, []
    findings = plan_checks.run_checks(
        spec, new_port, new_tests, host_root=(checks_root or work_dir))
    findings += guard(old_port, old_tests, new_port, new_tests)
    return new_port, new_tests, errors, findings


def repair_prompt(errors: list[str], findings) -> str:
    """Hand back exactly what was wrong, once. Shaped like
    `plan_node._repair_prompt` so an agent that has seen one recognises the
    other, but without re-inlining the schemas: this session already has both,
    and the plan pair, in its context."""
    body = [
        "Your plan revision was rejected and nothing was written. The plan pair in "
        "force is still the one you were given. Fix every item below and emit the "
        f"revision again, in full, under a `{REVISION_MARKER}` heading as two fenced "
        "json blocks, the port plan then the test plan. Do not emit a diff or a "
        "partial document.",
    ]
    if errors:
        body.append("## Schema errors\n\n" + "\n".join(f"- {e}" for e in errors))
    blockers = blocking(findings)
    if blockers:
        body.append(
            "## Rejected changes\n\n"
            "A `revision_froze_field` or `revision_deleted_entry` item below is not a "
            "mistake in your JSON. It is a change a revision is not allowed to make, "
            "because it would lower the bar the gate holds you to rather than correct "
            "a fact about the tree. Restore the original value. If you believe the "
            "original value is genuinely wrong, do not revise it: emit\n\n"
            "    PLAN ESCALATION: <json pointer> -- <why stage 2 has to decide this>\n\n"
            "and stop. Anything else in the list is an ordinary plan-check failure and "
            "is answered by re-reading the checkout you still have a shell on.\n\n"
            + _render(blockers)
        )
    return "\n\n".join(body)


def budget_spent_prompt(budget: int) -> str:
    """Told once, when the agent proposes a revision it cannot have.

    The alternative -- dropping the proposal silently -- leaves it revising
    into a void on every remaining attempt while the gate output never
    changes, which looks from the inside exactly like a revision that was
    accepted and did not help."""
    return (
        f"Your plan revision was not reviewed and nothing was written: this run has "
        f"already used its {budget} revision(s). The plan pair in force is final for "
        f"the rest of this integration.\n\n"
        f"Two things are left. Port against the plan you have, accepting the "
        f"fidelity cost and recording it in PORT_NOTES.md. Or, if a frozen value is "
        f"genuinely wrong and no edit to the checkout can reach the gate reason, emit\n\n"
        f"    PLAN ESCALATION: <json pointer> -- <why the planning stage has to decide this>\n\n"
        f"and stop. Do not propose another revision."
    )


def revision_paths(host: str, feature: str | None, index: int):
    """Where revision `index` is written.

    Stage 2's own output is never overwritten. The plan a port was originally
    judged against is the only record of what was asked of it, and a defect
    found three attempts later is diagnosed by comparing the two -- so
    revisions sit beside the original, numbered, and the highest one present
    is the pair in force."""
    plan_path, tests_path = helpers.plan_paths(host, feature)
    return (
        plan_path.with_suffix(f".rev{index}.json"),
        tests_path.with_suffix(f".rev{index}.json"),
    )


def count(host: str, feature: str | None) -> int:
    """How many revisions this host's plan has already earned. 0 means the
    pair on disk is stage 2's output, untouched.

    Both files or neither: a revision with only its port plan written is a
    crashed write, and reading it would pair a new plan with an old test plan
    -- which is the one combination `plan_checks` was built to reject and the
    one a resume must never construct silently."""
    index = 0
    while True:
        plan_path, tests_path = revision_paths(host, feature, index + 1)
        if not (plan_path.exists() and tests_path.exists()):
            return index
        index += 1


def escalation_path(host: str, feature: str | None) -> Path:
    """Where stage 3's escalations accumulate for stage 2 to read.

    Beside the plan and not under out/, for one reason: out/ is timestamped
    and untracked, so an escalation written there is evidence a human can
    read and nothing a later stage can find. An escalation is the one
    stage-3 output that is addressed to stage 2."""
    plan_path, _ = helpers.plan_paths(host, feature)
    return plan_path.with_suffix(".escalations.json")


def record_escalation(host: str, feature: str | None, entry: dict) -> Path:
    """Append one escalation. Appended rather than replaced: two runs can
    hit two different frozen values, and the second one does not make the
    first one wrong."""
    path = escalation_path(host, feature)
    existing = json.loads(path.read_text()) if path.exists() else []
    existing.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))
    return path


def open_escalations(host: str, feature: str | None) -> list:
    """Every escalation recorded against this host that no later plan has
    answered. `resolved` is set by `clear_escalations` once stage 2 has
    written a plan that had them in front of it."""
    path = escalation_path(host, feature)
    if not path.exists():
        return []
    return [e for e in json.loads(path.read_text()) if not e.get("resolved")]


def clear_escalations(host: str, feature: str | None, plan_stamp: str) -> int:
    """Mark the open escalations as answered by the plan just written.

    Marked, not deleted. Which frozen value stage 3 refused to meet, and
    which re-plan answered it, is the record of why the second plan differs
    from the first."""
    path = escalation_path(host, feature)
    if not path.exists():
        return 0
    entries = json.loads(path.read_text())
    n = 0
    for entry in entries:
        if not entry.get("resolved"):
            entry["resolved"] = plan_stamp
            n += 1
    if n:
        path.write_text(json.dumps(entries, indent=2))
    return n


def retire(host: str, feature: str | None, stamp: str) -> list:
    """Move every existing revision out of the way, and say which ones.

    Stage 2 writing a fresh pair does not delete `<plan>.rev1.json` from an
    earlier run, and `latest` returns the highest-numbered revision it can
    see. A re-planned host would therefore keep being judged against a
    correction somebody made to the *previous* plan, silently, and the new
    stage-2 output would never be read at all.

    Moved rather than deleted. A revision is the record of what was asked of
    an earlier port, and that is exactly what a reader needs when comparing
    two runs of the same host."""
    moved = []
    index = 0
    while True:
        index += 1
        pair = revision_paths(host, feature, index)
        if not any(p.exists() for p in pair):
            break
        for path in pair:
            if not path.exists():
                continue
            target = path.parent / "superseded" / f"{stamp}{path.name}"
            target.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target)
            moved.append(str(target))
    return moved


def latest(host: str, feature: str | None) -> tuple[dict, dict, int]:
    """The plan pair in force, and which revision it is.

    Revision 0 is stage 2's output. A run that stops mid-way and is restarted
    resumes from the revisions it already earned rather than silently
    re-litigating them."""
    index = count(host, feature)
    if index == 0:
        plan_path, tests_path = helpers.plan_paths(host, feature)
    else:
        plan_path, tests_path = revision_paths(host, feature, index)
    return json.loads(plan_path.read_text()), json.loads(tests_path.read_text()), index


def commit(
    dump,
    host: str,
    feature: str | None,
    index: int,
    port_plan: dict,
    test_plan: dict,
    findings,
) -> tuple[dict, dict]:
    """Write an accepted revision. Code writes the plan, never the agent: the
    only tool stage 3 holds is a shell rooted at the host checkout, and that is
    the property that makes this module the single door."""
    plan_path, tests_path = revision_paths(host, feature, index)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(port_plan, indent=2))
    tests_path.write_text(json.dumps(test_plan, indent=2))
    dump.json(f"plan_revision_{host}_{index}.json", {
        "revision": index,
        "port_plan": str(plan_path),
        "test_plan": str(tests_path),
        "recorded": [f.as_dict() for f in findings],
    })
    return port_plan, test_plan
