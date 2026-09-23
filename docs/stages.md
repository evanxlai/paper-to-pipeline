# Loop stages and their contracts

This is the authoritative description of what each node in the loop consumes, what it
emits, and who decides whether it passed. The four-week task schedule is in
[plan.md](plan.md); the accepted proposal text is in [proposal.md](proposal.md) and is
kept as a historical record, not updated to match this document.

"Host" throughout means the existing performance model being ported into: ChampSim,
gem5, or the CBP2025 kit.

## The one rule that shapes the split

**Only the DSE stage applies resource constraints.** Every stage before it exists to
implement the paper's feature *correctly*, and nothing more.

A storage budget is a constraint over a candidate's accounted resources. "Iso-budget" is
not a special mode: it is one value of that constraint, with the allowance pinned to the
host's baseline storage. A 192 KiB track and a 64 KiB track are two allowances, not two
kinds of run. Storage is also not the only constraint there can be. It is the first one,
and the only one the demonstration uses, but a latency bound, a logic-cost bound or an
IPC floor has the same shape, and stage 4 applies whatever set it is given (see stage 4
below).

Consequences, all of them load-bearing:

- No pre-DSE stage takes a `budget` argument.
- The verify gate has no storage condition.
- A spec's `resource_accounting` block is still distilled, because it is a fact about the
  paper, and is still checked for *self-consistency* (the breakdown must sum to the
  declared total). It is never compared against an allowance before DSE. A
  self-consistency check is not a budget check.
- `resource_accounting.budget_donors` is a DSE input, not an integration instruction. The
  integrator never shrinks a host structure to make room.
- Accounting is not a budget decision, so it may happen before DSE. The spec says what
  each of its structures costs at any parameter setting (`state[].size_formula`). The
  plan exposes the host's own sizing knobs (`host_knobs`) and says what the host's
  structures cost (`host_storage`), because stage 4 cannot shrink what it cannot move.
  Both ship every value at its default. Choosing any other value is stage 4's alone.

The reason is diagnostic clarity. A stage that has to satisfy correctness *and* a budget
cannot distinguish "the feature is implemented wrong" from "the feature does not fit",
and the tuning stage is the only one that is actually allowed to trade the feature's
parameters against the host's storage.

## Pipeline

```
paper (+ optional artifact)
   |
   v
[1]   distill        -> feature spec (schema-checked by code)
   |
   v
[1.5] spec review    -> evidence-checked spec
   |
   v
[2]   plan           -> port plan + test plan          <- the heavy lifting
   |
   v
[3]   implement  --> run test plan --> fail --> [3b] debug (root-cause report)
   ^                      |                              |
   +----------------------+------ report back -----------+
   |                      |
   |                    pass
   v                      v
       verify gate (plain code) -> promote
                              |
                              v
[4]   DSE            -> tuned candidate under a constraint set
```

## Stage 1: distill

- **In:** paper text (`P2P_PAPER_TEXT`); optionally a read-only bash on the reference
  artifact checkout (`paper_plus_reference` arm); the feature-spec schema, inlined
  because the paper-only arm has no tools with which to read it off disk.
- **Out:** `spec/<feature>.<mode>.json`, where mode is the ablation arm.
- **Decided by code:** JSON Schema validation, one repair turn on failure, then
  `spec_checks.run_checks`. Fails closed on any `error` finding.

## Stage 1.5: spec review

- **In:** the draft spec, the paper text.
- **Out:** the reviewed spec plus a review summary.
- **Decided by code:** reviewers propose patches grounded in verbatim quotes;
  `spec_review.apply_patches` decides which survive. Unsupported claims become open
  questions and candidate values, never silent rewrites.
- Off-switchable (`P2P_SPEC_REVIEW=0`) so ablation 2 can measure what the stage is worth.

## Stage 2: plan

The planning node does the heavy lifting of the port. It answers two questions: how does
this feature go into *this* model, and how will we know it worked?

- **In:**
  - the reviewed feature spec;
  - the host checkout, which it may **read** and against which it may **run the existing
    test suite and a baseline smoke** — so "the regressions this model already provides"
    is a verified fact rather than a guess;
  - `hosts/<host>/NOTES.md` (the recorded hook points);
  - the host checkout's git revision, which it records into both outputs.
- **Out:** two schema-checked JSON artifacts per host, against
  `plan/port_plan.schema.json` and `plan/test_plan.schema.json`. Those schemas are the
  enforceable form of the two tables below; where this document is prose, they are the
  contract, and `loop/tests/fixtures/tinysc.toy.{plan,tests}.json` is a worked pair.
- **Decided by code:** schema validation plus coverage checks (`loop/plan_checks.py`) —
  every spec `state` element, `algorithms` entry, `parameters` entry, `host_interfaces`
  need and `unit_tests` entry must map to something in the plan pair. An unmapped spec
  item is a planning failure, not an integration surprise. The checks also settle what
  the schemas cannot: ids that are unique, references that resolve, each verbatim echo
  agreeing with the pointer it claims, and every rule whose two halves live in different
  documents.

### Port plan (`plan/<feature>.<host>.plan.json`)

| Field | Contents |
|---|---|
| `host`, `host_revision` | which model, and the exact commit the plan was written against |
| `structure` | the module or class shape chosen, and why the alternatives in NOTES.md were rejected |
| `hook_points[]` | file, symbol, and what goes there; a site being *modified* also records what it does today, so a plan can only claim a hook point somebody read |
| `spec_map[]` | spec JSON pointer -> code site; this is the coverage check's input |
| `interface_resolutions[]` | every `host_interfaces[].need` -> `exact`, `fallback` or `unavailable`, with a rationale, and for the last two what the port loses. The met needs are recorded too: that is what lets coverage demand a decision per need rather than only for the ones the planner found hard |
| `knobs[]` | each spec parameter -> its host-native knob, named to the `SR_<NAME>` convention `dse.params_header` emits, so stage 4 can mutate it |
| `host_knobs[]` | each host sizing define the port leaves in place -> a `HOST_<NAME>` macro in the same header, at the clean tree's value, with the verbatim line it replaces and its legal range. Code checks that the line is in the checkout and holds the default |
| `host_storage` | the host's storage as one formula per structure over the host knobs, plus `baseline_bits`, the host's own accounting on the clean tree. Code requires the formulas to reproduce that number at the defaults, and stage 2 measures the number itself where the host can |
| `feature_enable` | the enable knob's name, its default-off mechanism, and what executes on the off path — G2 is a claim about this, so the plan states it before the integrator is held to it |
| `steps[]` | ordered, individually buildable increments |
| `risks[]`, `open_questions[]` | what could go wrong, and what the spec left unresolved |

Note what is absent: no storage split, no allowance, no budget. The plan exposes the
host's sizing knobs and says what they cost, which is accounting; it never picks a value
other than the clean tree's. Which structures shrink, and by how much, is stage 4's
subject.

### Test plan (`plan/<feature>.<host>.tests.json`)

Two buckets, because they answer different questions.

**`correctness[]`** — does the implementation do what the spec says? Each entry carries a
`kind`, a command, and a pass condition:

- `existing_regression` — a test the model already ships. The plan records the result it
  produced on the clean tree at plan time, so a pre-existing failure can never be
  mistaken for one the port introduced.
- `generated_smoke` — written by the planner for models that ship no usable suite.
- `spec_unit_test` — the spec's own `unit_tests[]` entries, placed into the host's suite.
- `feature_off_baseline` — with the enable knob off, metrics must equal the recorded
  baseline. This is the strongest regression available and it is exact for
  trace-driven simulators.

**`smoke`** — the workloads G4 runs with the feature on, answering "does it run" rather
than "is it better". It is its own section because a gate condition with no declared
input is one the gate has to invent, and an invented condition is one nobody can audit.

**`performance[]`** — does the feature's claimed benefit actually show up? Each entry
carries a metric, a direction, a trace list, and two thresholds:

- `block_threshold` — directional and non-regression. Feature-on must move the target
  metric the paper's way and must not regress beyond noise. **This blocks promotion.**
- `warn_threshold` — magnitude, compared against the paper's claimed gain. A shortfall is
  recorded and reported. **This does not block.**

The asymmetry is deliberate. At this point the port carries the spec's default
parameters and has not been tuned, so a magnitude shortfall is the expected condition,
not a defect — gating on it would strand a correct port before the stage whose entire job
is to fix it. A wrong *direction*, on the other hand, means the mechanism is misbuilt and
no amount of tuning will rescue it.

Performance entries need enough traces to carry signal. The five-trace smoke list is for
"does it run", not for "is it better"; a performance list sits between smoke and the
60-trace screening set. When an entry names several traces it is scored on the
improvement of the means, not the mean of the improvements — the two differ on a
heterogeneous trace list, and the first is how the host adapters already aggregate a
suite.

## Stage 3: integrate

- **In:** the port plan, the test plan, the reviewed feature spec, and the host checkout
  (read/write, through a `BashTool` plus the host build/run/stats adapters). Plus the
  attempt budget, `P2P_INTEGRATION_ATTEMPTS`, and the plan-revision budget,
  `P2P_PLAN_REVISIONS`.
- **Precedence:** the plan is authoritative on *where and how* to hook; the spec is
  authoritative on *what the mechanism is*. The plan does not restate pseudocode.
- **Out:** the edited checkout, `PORT_NOTES.md` recording any deviation, the per-attempt
  test results, a promotion verdict, and any accepted plan revision as
  `plan/<feature>.<host>.plan.rev<N>.json` plus its test-plan twin.
- **Decided by code**, in `gate.py`. Agents never self-report success.

| | Gate condition |
|---|---|
| G1 | the host builds with the feature code present |
| G2 | with the feature knob off, metrics equal the recorded baseline — reported as the results of the test plan's `feature_off_baseline` entries, so the plan owns which workloads and which tolerance |
| G3 | the test plan's other `correctness[]` entries pass |
| G4 | with the feature knob on, the smoke traces complete without error |
| G5 | the test plan's `performance[]` entries pass their `block_threshold`, and every trace they declare completes — an entry scored on the traces that survived is a number about a different trace set than the plan asked for. On a host with a ranking metric (`plan_checks.RANKING_METRIC`; MPKI on cbp2025), every entry judges that metric, the one stage 4 ranks by |

There is no storage condition. See the rule at the top.

A `warn_threshold` shortfall is recorded as a warning and never as a reason. The
distinction is load-bearing rather than cosmetic: the gate's reasons are what the debug
node is handed and told to fix, so a non-blocking observation placed among them becomes
work the next turn tries to do.

Inner loop: implement, run the test plan, and on any failure hand off to the debug node,
which reports a root cause back to the implement node. Repeat until the gate passes or
the attempt budget runs out.

### Plan revision (`plan_revision.py`)

The plan was written against this checkout and can still be wrong about it. A hook point
may name a symbol that has moved, or a correctness command may name a target this tree
does not build. Stage 3 repairs that itself rather than returning the work to stage 2,
because stage 2 needs the reviewed spec, the host notes and a full read of the tree, and
re-running it re-derives every decision that was already right.

The hazard is that the test plan *is* the gate. Every threshold, tolerance, metric name,
pass condition and workload `gate.py` weighs is declared there, so the party proposing a
revision is the party the revision judges. `plan_checks.run_checks` cannot catch that: it
decides whether one pair is coherent and covers the spec, and has no notion of a previous
version, so it cannot see a revision that is coherent and simply weaker.

So the split is not by size of change. It is by who the change serves. A factual
correction about the tree is revisable in place. A weaker demand is not, and escalates.

The mechanism, in order. The agent emits a `## Plan revision` heading and two complete
fenced JSON blocks. Code then validates both against their schemas, re-runs the plan
checks, and diffs the pair against the one in force. Code writes the files, and only if
nothing was weakened. The agent's one tool is a shell rooted at the host checkout, so it
cannot reach the plan artifacts itself, and this is the single door. A rejection writes
nothing and buys one repair turn (`P2P_PLAN_REPAIR_TURNS`) that names each refused field.

Two rules cover every field, so what is allowed is read off a table rather than reasoned
about per case. **Frozen** means the revision must repeat the value exactly.
**Append-only** means a keyed collection may gain entries and may never lose one, and a
surviving entry is frozen apart from a named allowlist.

| | Fields |
|---|---|
| Revisable | `hook_points` entire, `structure.choice`, `spec_map[].realization` and `hook_ids`, `steps`, `risks`, `interface_resolutions[].status` / `resolution` / `rationale` / `fidelity_note`, `knobs[].host_knob` and `binding`, `open_questions[].cost_if_wrong`, `correctness[].command` / `env` / `test_file`, any `timeout_seconds`, any `description`, `notes`, `smoke.run`, and anything added |
| Frozen | `feature_name`, `host`, `host_revision`, `spec_inputs_used`, every `pass_condition`, every `clean_tree_result`, `baseline_rel_tol`, both `performance[]` thresholds, `performance[].metric` / `direction` / `baseline`, the smoke and performance trace sets, `knobs[].macro` and `default`, `host_knobs[].macro`, `type` and `default`, `host_storage.baseline_bits`, `feature_enable.name` and `macro`, a `rejected_alternatives` entry, an `open_questions[].assumption` |
| Append-only | `metric_keys`, `correctness[]`, `performance[]`, `spec_map[]` pointers, `knobs[]`, `host_knobs[]`, `interface_resolutions[]`, `open_questions[]`, `structure.rejected_alternatives`, `smoke.traces` |

No rule compares two numbers for looseness. A threshold is frozen in both directions on
purpose: each one has its own sense of "tighter", a `no_regression` band inverts it, and
one sign error readmits the whole hazard. Nothing legitimate is lost, because a
mid-run tightening is not something the judged party needs.

Two fields are recorded rather than refused, both as `warn` findings in the revision
record. `feature_enable.off_path` and `default_off` are prose that G2 does not read, so
rewriting them cannot loosen the gate numerically. It can retire a promise quietly, which
is what the warn prevents. An `interface_resolutions[].status` that drops in fidelity is
the legitimate discovery that a host facility does not do what it looked like it did, and
the `fidelity_note` beside it is what the write-up reports.

One field's revisability depends on its entry. A `performance[].run` block is revisable
when that entry's `baseline.source` is `measure_feature_off`, because `plan_runner`
measures feature-on and feature-off through the same `run` and a corrected command moves
both sides. It is frozen when the source is `recorded`, where the comparison point was
measured before the port existed, so `run` feeds only the measured side and revising it
moves the improvement without moving the bar.

**Escalation.** A defect stage 3 may not decide ends the attempt. The agent emits
`PLAN ESCALATION: <pointer> -- <reason>`, and the stage returns status `needs_replan` with
the pointer and reason recorded. It does not spend the remaining attempts. This is the
"serious issue" route back to stage 2, and it is what a frozen-but-wrong value gets
instead of a rewrite. It ends the attempt, not the job: the driver runs stage 2 again and
then stage 3 against the new pair (see "Re-planning inside the job" below).

An escalation is the only message that travels backwards through this loop. Where it is
written is therefore part of the contract, not a logging choice. Stage 3 appends it to
`plan/<feature>.<host>.plan.escalations.json`, beside the plan it is about. The next stage-2
run inlines every unresolved entry into the planner prompt and marks them answered by the
plan it writes. Marked, not deleted: which frozen value stage 3 refused to meet, and which
re-plan answered it, is the record of why the second plan differs from the first.

Recording it only under `out/` is not enough. That directory is timestamped and untracked,
so an escalation written there is evidence a reader can find and nothing a later stage can.
The first real stage-3 run on the cbp2025 host escalated `/host_interfaces/4`, after the
gate measured its port 43 percent worse on CycWPPKI. The re-plan that answered it moved the
hook from a standalone override into the host's own statistical-corrector sum.

**Re-planning inside the job** (`loop/replan.py`). An escalation does not stop the job. The
driver runs stage 2 for that host again, which reads the escalation and answers it, and
then runs stage 3 against the new pair. Nobody has to submit anything. The rules:

- **Budget.** At most `P2P_ESCALATION_REPLANS` re-plans per host per job, 2 by default.
  After that the host's status stays `needs_replan` and the job goes on without it.
  `P2P_ESCALATION_REPLANS=0` restores the old behavior, where the first escalation stops
  the host.
- **Only an escalation re-plans.** A port that ran out of attempts, or a backend that
  failed, is not a plan defect. Re-planning it hides the real result.
- **The port tree.** A re-plan that changed the port's design starts the next round from a
  clean copy of the host. The design has six parts: the structure choice, the hook
  points (file, symbol, action), each interface resolution's status, the enable switch,
  the knob macros and the host-knob macros. If only the measurement changed, the next
  round keeps the port the agent already wrote. Prose is not compared, because a reworded
  sentence is not a different port.
- **Evidence.** Round N writes its artifacts, and its plan run's, under a `replan<N>_`
  prefix, so no round overwrites another's gate results or transcripts. The port diff is
  saved after every round, before the next round can replace the tree.
- **A refused re-plan.** Stage 2 can refuse the new plan, or its backend can fail. Either
  way the host's status is `replan_failed`, with the reason. The escalation stays open,
  because stage 2 marks it answered only after it writes a plan.

Stage 4 runs only for a host whose last round passed the gate, as before.

Stage 2's own artifacts are never overwritten. A revision is written beside them, numbered,
and the highest revision present is the pair in force, so the plan a port was originally
judged against survives for diagnosis and a restarted run resumes from the revisions it
already earned.

## Stage 3b: debug

- **In:** the failing test output, the build and run logs, the integration diff, and both
  plan artifacts. It may run build, run, and the tests in order to reproduce and narrow
  a failure.
- **Out:** a structured root-cause report addressed to the implement node. Or a proposed
  plan revision. Or an escalation to stage 2.
- **Authority: diagnosis and proposal only.** The debug node never edits the checkout,
  and it never edits the plan either. It proposes, and code disposes: the implement node
  applies every fix to the tree, and `plan_revision.py` writes every accepted revision to
  the artifacts.

The split is the same one stage 1.5 uses — the proposer is not the disposer — and it
keeps exactly one writer on the tree, so a regression always has one author. The
revision path does not weaken that. It is the same rule applied to a second artifact: the
node that finds the defect states it, and code decides whether it may be acted on.

## Stage 4: DSE

- **In:** the gate-passed integration; the spec's `parameters` and `state[].size_formula`;
  the plan's `host_knobs` and `host_storage`; a **constraint set**; the screening and promotion
  trace lists; the evolve-flows search config.
- **Out:** the tuned candidate and the tuned-vs-baseline verdict. Only the tuned
  configuration counts as the verdict.
- Candidates are not free-form code: the evolver mutates one params header that
  instantiates the spec's `parameters` (`SR_*`) and the plan's host knobs (`HOST_*`), and
  every constraint is re-derived from the same values, so a candidate cannot misreport its
  own cost.

A constraint is `{metric, comparison, allowance}` (`loop/constraints.py`). Storage is the
one the demonstration uses, with the two allowances in `experiments/budgets.yaml`.
Rejecting an over-budget candidate happens here, in the search, and nowhere earlier.

Constraints are more general than storage, and the mechanism is built for that. A
*static* metric is computed from the header values before anything is built; storage is
one, the sum of the spec's formulas and the host's, and a candidate that breaks it costs
no build and no trace. A *measured* metric is read off the screening aggregate after the
traces run, so an IPC floor or a CycWPPKI ceiling needs no new code at all. A new static
metric is one function in `constraints.STATIC_METRICS`; a new constraint of either kind is
one more entry in `dse.constraint_set`. A candidate that breaks a constraint scores below
every candidate that fits, and higher the closer it comes, so a search that starts
infeasible still has a direction.

Before searching, stage 4 builds every knob once at a second legal value (`dse.preflight`).
Two builds of the same header must give the same binary, and a knob whose change leaves
the binary unchanged is wired to nothing. For a knob that costs storage that stops the
stage, because the search would credit bits the predictor never gave up.

### Promotion

The search ranks candidates on a screening list, and a screening list is small on purpose.
So the verdict does not come from the search. `dse.promote_finalists` takes the top
candidates (`P2P_DSE_TOP_K`, 3 by default) and scores them again on traces the search
never saw (`experiments/promote-16.list`). Two references run on the same traces in the
same job: the kit's default host, built from the pristine checkout, and the port with
every knob at its default. The finalist with the lowest screening metric on the promotion
traces is the tuned candidate. Its comparison with the two references is the verdict.

Promotion applies the constraint set again. It re-derives each finalist's static metrics
from its header, and it checks the measured constraints on the promotion traces, so a
candidate cannot break a constraint and still win. A variant that did not run every
promotion trace is reported and cannot win, for the same reason G5 refuses a partial trace
set: its mean is a number about other traces.
