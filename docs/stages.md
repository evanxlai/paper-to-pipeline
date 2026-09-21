# Loop stages and their contracts

This is the authoritative description of what each node in the loop consumes, what it
emits, and who decides whether it passed. The four-week task schedule is in
[plan.md](plan.md); the accepted proposal text is in [proposal.md](proposal.md) and is
kept as a historical record, not updated to match this document.

"Host" throughout means the existing performance model being ported into: ChampSim,
gem5, or the CBP2025 kit.

## The one rule that shapes the split

**Only the DSE stage knows about resource constraints.** Every stage before it exists to
implement the paper's feature *correctly*, and nothing more.

A storage budget is a constraint over a candidate's accounted resources. "Iso-budget" is
not a special mode: it is one value of that constraint, with the allowance pinned to the
host's baseline storage. A 192 KiB track and a 64 KiB track are two allowances, not two
kinds of run.

Consequences, all of them load-bearing:

- No pre-DSE stage takes a `budget` argument.
- The verify gate has no storage condition.
- A spec's `resource_accounting` block is still distilled, because it is a fact about the
  paper, and is still checked for *self-consistency* (the breakdown must sum to the
  declared total). It is never compared against an allowance before DSE. A
  self-consistency check is not a budget check.
- `resource_accounting.budget_donors` is a DSE input, not an integration instruction. The
  integrator never shrinks a host structure to make room.

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
- **Out:** two schema-checked JSON artifacts per host.
- **Decided by code:** schema validation plus coverage checks — every spec `state`
  element, `algorithms` entry, `parameters` entry, and `host_interfaces` need must map to
  something in the plan. An unmapped spec item is a planning failure, not an integration
  surprise.

### Port plan (`plan/<feature>.<host>.plan.json`)

| Field | Contents |
|---|---|
| `host`, `host_revision` | which model, and the exact commit the plan was written against |
| `structure` | the module or class shape chosen, and why the alternatives in NOTES.md were rejected |
| `hook_points[]` | file, symbol, and what goes there |
| `spec_map[]` | spec JSON pointer -> code site; this is the coverage check's input |
| `interface_resolutions[]` | each unmet `host_interfaces[].need` -> the chosen fallback and its rationale |
| `knobs[]` | each spec parameter -> its host-native knob, named to the `SR_<NAME>` convention `dse.params_header_from_spec` emits, so stage 4 can mutate it |
| `feature_enable` | the enable knob's name and its default-off mechanism |
| `steps[]` | ordered, individually buildable increments |
| `risks[]`, `open_questions[]` | what could go wrong, and what the spec left unresolved |

Note what is absent: no storage split, no donor structures, no budget. Those are stage 4's
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
60-trace screening set.

## Stage 3: integrate

- **In:** the port plan, the test plan, the reviewed feature spec, and the host checkout
  (read/write, through a `BashTool` plus the host build/run/stats adapters). Plus the
  attempt budget, `P2P_INTEGRATION_ATTEMPTS`.
- **Precedence:** the plan is authoritative on *where and how* to hook; the spec is
  authoritative on *what the mechanism is*. The plan does not restate pseudocode.
- **Out:** the edited checkout, `PORT_NOTES.md` recording any deviation, the per-attempt
  test results, and a promotion verdict.
- **Decided by code**, in `gate.py`. Agents never self-report success.

| | Gate condition |
|---|---|
| G1 | the host builds with the feature code present |
| G2 | with the feature knob off, metrics equal the recorded baseline |
| G3 | the test plan's `correctness[]` entries pass |
| G4 | with the feature knob on, the smoke traces complete without error |
| G5 | the test plan's `performance[]` entries pass their `block_threshold` |

There is no storage condition. See the rule at the top.

Inner loop: implement, run the test plan, and on any failure hand off to the debug node,
which reports a root cause back to the implement node. Repeat until the gate passes or
the attempt budget runs out.

## Stage 3b: debug

- **In:** the failing test output, the build and run logs, the integration diff, and both
  plan artifacts. It may run build, run, and the tests in order to reproduce and narrow
  a failure.
- **Out:** a structured root-cause report addressed to the implement node.
- **Authority: diagnosis only.** The debug node never edits the checkout. The implement
  node applies every fix.

The split is the same one stage 1.5 uses — the proposer is not the disposer — and it
keeps exactly one writer on the tree, so a regression always has one author.

## Stage 4: DSE

- **In:** the gate-passed integration; the spec's `parameters` and `resource_accounting`;
  a **constraint set**; the screening and full trace lists; the evolve-flows search
  config.
- **Out:** the tuned candidate and the tuned-vs-baseline verdict. Only the tuned
  configuration counts as the verdict.
- Candidates are not free-form code: the evolver mutates one params header that
  instantiates the spec's `parameters`, and the constraint is re-derived from the same
  values, so a candidate cannot misreport its own cost.

A constraint is `{metric, comparison, allowance}`. Storage is the one the demonstration
uses, with the two allowances in `experiments/budgets.yaml`. Rejecting an over-budget
candidate happens here, in the search, and nowhere earlier.
