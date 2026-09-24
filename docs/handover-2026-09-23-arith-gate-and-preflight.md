# Handover: the arithmetic gate, and a knob the DSE cannot sweep, 2026-09-23

Supersedes `docs/handover-2026-09-23-spec-review-hardening.md`. Read that one
first for the checks it added and the reasoning behind them; three of its seven
problems are now closed and the rest are carried forward here with their
numbering changed.

The session that wrote this audited the third distill run against the paper,
found one wrong number and one red test, and root-caused both. It changed
nothing. Everything below is a plan.

## Where things stand

Branch `spec-review-hardening`, five commits ahead of `main`, plus a **large
uncommitted working tree**. Nothing in this session was committed.

Three distill runs now:

| run | `out/` prefix | result |
| --- | --- | --- |
| first | `20260923_170937` | 4 `error` findings. |
| second | `20260923_183748` | 0 errors, 4 warns. Was the promoted spec. |
| third | `20260923_211658` | 0 errors, 10 warns, 2 infos. **Is** the promoted spec. |

`spec/sr.paper_only.json` is byte-identical to
`out/20260923_211658_spec_final.json`. Two things are wrong with that:

- **The suite is red.** `1 failed, 671 passed, 20 skipped`. See problem 2.
- **The zero is wrong.** The spec states an expected digest of 569 for an
  expression worth 441, and `_check_unit_test_arithmetic` does not see it. See
  problem 1.

## What the third run got right

The audit compared the spec against `third_party/runlts/runlts.txt` claim by
claim. Everything ties out except the one unit test in problem 1:

- **Storage.** `sr_wt` 43008, `sr_ut` 9360, `tomasulo_table` 1495, summing to
  the 53863 Table 3 prints for sR. Field widths `{valid (1), payload (14),
  decay_ctr (8)} x 65` match the table literally.
- **Digest extraction.** INT fields at `[11:6]`/`[8:3]`/`[5:0]`, FP16
  `>>13 & 0x7`, FP32 `>>26 & 0x3F`, FP64 `>>55 & 0x1FF`, flags replicated three
  times. All match Figure 6.
- **Bank mapping.** `range(b, 65, 8)` gives bank 0 nine registers and banks 1-7
  eight, which is the figure's stride-8 reading and closes against the 65 the
  table multiplies by.
- **Open questions** U1-U5 and I1 restate the paper's own UNCERTAIN and
  INFERRED blocks rather than inventing hedges, and recovery is correctly
  carried as the paper's stated future work.
- **The 27776-bit overage** for `sr_inflight` is disclosed in
  `logic_cost_notes`, which is exactly what the paper's own cross-check note
  says nobody budgeted.

Closed since the last handover, and worth not re-opening:

- Its problem 4 (hardcoded `2.5`). `_check_tuning_literals` was promoted to
  `error` and this run declared the multiplier as a knob.
- Its problem 6 (a unit test asserting behaviour the algorithm lacks). This
  run's FP test matches what `complete` implements.
- Its problem 7 (schema leakage). `additionalProperties: false` is on the
  top-level schema and `loop/tests/test_spec_schema.py` pins it. The raw model
  response in `out/20260923_211658_distill.md` still carries the schema
  furniture; the parsed artifact does not, which is the guard working.

## Known problems, most urgent first

### 1. The arithmetic gate is blind to a prose tail

`spec/sr.paper_only.json`, `/unit_tests/0/expect`:

> "The complete algorithm computes lead=63, trail=1, val5_0=1, and stores
> digest=`(1<<6) ^ (63<<3) ^ 1` = **569** in the tomasulo_table."

`(1<<6) ^ (63<<3) ^ 1` is **441**. 569 is the three fields *added*, and Figure
6(a) is explicit that they overlap and are XORed. The draft shipped `trail=0
... = 568`; rounds 1 and 2 corrected the operand to `trail=1` (right — val=1
has its LSB set, so the trailing run is ones) and moved the stated value to
569, which is 568+1. The addition survived the correction.

**Root cause.** The equality-chain arm of `_arith_claims` splits the clause
into three parts: `digest`, `(1<<6) ^ (63<<3) ^ 1`, and
`569 in the tomasulo_table`. The third never reduces to an integer, because
`_UNIT_TAIL_RE` (`spec_checks.py:761`) is

```
\s+[A-Za-z][A-Za-z/%\s]*$
```

with no underscore in the class. `in the tomasulo_table` is therefore not
recognised as a tail, is not stripped, and `_ARITH_CHARS_RE.fullmatch` then
rejects the whole part. The left side evaluates to 441 without trouble; the
right comes back `None`, and a claim with one undecidable side is dropped —
correctly, by the design rule that an `error` must never rest on a guess.

**Fix.** Add `_` to the tail character class. Nothing else. The evaluator
already handles `^` and `<<`, `_arith_readings` already tries both readings of
the caret, and `_CONJUNCTION_RE` already guards the "this tail is the next
assertion" case the narrow class was protecting.

**Evidence it is safe.** Replaying `_check_unit_test_arithmetic` over all 36
specs under `out/` plus the checked-in one, with and without the change:

| | findings |
| --- | --- |
| before | 9 |
| after | 12 |

The three new findings are the draft, the final and `sr.paper_only.json` —
all the same real defect. Nothing was lost and nothing new was invented. That
clears the corpus rule.

**Also add** a test in `loop/tests/test_spec_checks.py` pinning the prose-tail
shape, beside the existing `_COMPUTED_AS_RE` cases. Read the docstring above
`_ALLOWED_ARITH_NODES` before you do: this same expression has now escaped in
three different dresses across runs 5, 6 and this one, and each escape was
answered with a new regex for the shape that got through. The tail-stripping
gap is the general one, and it is worth checking whether the other probes have
the same blind spot.

**Do not** ask reviewers to verify the arithmetic. Round 0 returned
`SUPPORTED` on "computes a digest of 568", which is exactly the failure the
check's docstring already records and explains — no reviewer is asked to be a
calculator. This class belongs to the check.

### 2. Two knobs have no second legal value, and the suite is red

```
tests/test_constraints.py::test_preflight_passes_when_every_knob_reaches_the_build
AssertionError: assert {'live', 'no second legal value'} == {'live'}
```

`num_logical_registers` has range `[65, 65]` and `num_banks` has `[8, 8]`.
`dse.preflight` expects every declared knob to be sweepable, and a degenerate
range admits one value.

This is new in run 3. Runs 1 and 2 declared no degenerate ranges, so promoting
this spec turned the suite red.

**The decision to make.** Both values are structural — the paper's register
file is 65 entries and the figure draws eight banks — so the range is honest.
Two ways to resolve it, and they point in opposite directions:

- **Treat a pinned knob as legitimate.** A parameter with a degenerate range
  tells the integrator both the value and that it is not free, which is more
  useful than burying it in prose. Then `preflight` should classify it as
  `pinned` rather than failing, and a check should verify the default sits
  inside the pinned range.
- **Keep parameters sweepable by definition.** Then the distiller brief has to
  say so, and structural constants move into `state`/`organization` — where
  `num_logical_registers` already appears, in three `size_formula` strings
  that would then reference a name `parameters` no longer declares.

Recommendation: the first. The second breaks `_check_size_formulas`, and the
information is worth keeping. But this is a call about what `parameters` means
to stage 4, so it is yours to make, not the loop's.

### 3. Open questions regressed, and knob minting is duplicating parameters

The last handover's problem 5 asked for dedup and staleness passes. They were
not built, and the count went **34 -> 36**. Every cluster it named is still
present:

- usefulness threshold: `/parameters/15/default`, `/parameters/22/default`,
  `/algorithms/0`, `/algorithms/0/pseudocode` — four entries, one question
- theta: `/parameters/16`, `/parameters/16/default`
- FP classification: `/algorithms/2/pseudocode`, twice

Review-process text is leaking into the artifact again. Integration agents read
this list, and it currently contains `"Reviewer wanted to shorten
/resource_accounting/budget_donors: ..."`, `"Unrepaired contradiction: ..."`,
and a question about Figure 7 — the MPKI chart, which sR does not touch.

There is a second-order symptom worth treating as the real bug. The draft had
17 parameters and the final has 23, and `/parameters/22`
(`algorithms_0_pseudocode_variant`, `ge_zero|gt_zero`) encodes the same
decision `/parameters/15` (`usefulness_threshold`, default 0) already carries.
**Stage 4 will sweep both and they will disagree.**

Fix, with machinery that exists: cluster on `tokens()`/`stem()` overlap
(`spec_checks.py:71,86`) and collapse at merge time; drop any question quoting
a spec value no longer in the spec; refuse to mint a knob whose question
clusters with one already minted; filter entries naming a review artifact
rather than a spec pointer.

### 4. `feature_budget_fit` is built, but nothing hands it a measured budget

The last handover's problem 3 is half-done — and note the check is already
smarter than that problem statement was, so read `spec_checks.py:350-367`
before touching it. `_check_storage` now takes a `feature_budget_bits` and
grades deliberately at two severities: `error` for a figure a caller measured
and committed to, `warn` for one scraped out of the spec's own prose, on the
reasoning that failing the gate closed on an honest disclosure teaches the next
round to stop disclosing. That reasoning is right; leave it alone.

What is missing is a caller. Nothing passes `feature_budget_bits`, so the check
falls back to `_declared_feature_budget` and warns. Today's position:

```
paper total 1,570,890 - sR's 53,863 + this spec's 81,639 = 1,598,666 bits
                                                         = 195.1 KiB
cap                                                        192 KiB
over by                                                 25,802 bits
```

Wire `adapter.measure_host_storage` — stage 4 already uses it — through to the
check so the overage lands as an `error` against a measured number.

### 5. Index consistency is still unbuilt, and this run passes it by luck

The last handover's problem 1, which it called the one live correctness bug.
The bug is gone from this run: `predict` and `update` both index
`sr_ut[t][hash(PC, b)][r]` with an absolute register id, and because the hash
domain is 8 and bank `b` only reaches `r = b (mod 8)`, the live cell count is
8 x 65 = 520 per table — exactly the `6 x 65 x (2^3 + 2^3 + 2^3)` Table 3
budgets. It closes.

It closes by luck. The check was never written, and the same class shipped
wrong in two consecutive runs before this one. Build `_check_index_consistency`
against `_declared_dimensions` as the previous handover specifies, together
with sub-table name resolution (its problem 2, still open: `_check_state_liveness`
still reports zero traffic for both weight tables because the pseudocode names
them `WT0`/`wt[bank][idx]`, never by their declared names). They want the same
plumbing.

### 6. The decay counter is off by one against the paper

`decay_timeout` defaults to 256 and `decay_ctr_bits` to 8. `complete` seeds
`decay_ctr = decay_timeout - 1` = 255 and `decode` decrements once per
instruction, so a digest dies after **255** decodes. Section 4.2 says 256. An
8-bit field cannot hold 256, so something had to give — the spec simply does
not say it chose.

Narrow check: when a parameter's `storage_impact` ties it to a state field of
declared width *w*, flag a default that *w* cannot represent. Low value alone,
cheap alongside problem 5's dimension parsing. Grade it `warn`; the
false-positive surface is wider than problem 1's.

### 7. A reviewer may edit an operand without recomputing the result

Rounds 1 and 2 changed `trail=0` to `trail=1` and `568` to `569` without
re-evaluating the expression. With problem 1 fixed, `_drop_regressing_patches`
catches this shape on its own, so this is a round-efficiency item rather than a
correctness one. One rule in `loop/prompts/reviewer.md` covers it: a patch that
edits an operand inside an arithmetic claim must restate the result, and may
not adjust the result without restating the expression.

## Reproducibility protocol

No spec JSON gets hand-edited, `spec/sr.paper_only.json` included, even though
it currently ships `569`. Fix the check and re-run; a red canary is the gate
working.

Per phase:

1. Land the check change and its tests.
2. `pytest` green (see below).
3. Replay every check over all 36 archived specs under `out/`; diff findings
   before and after and account for each delta. Problem 1 is already done:
   +3, -0, all true.
4. Re-run `run_checks` on `spec/sr.paper_only.json` and **confirm it goes red.**
   That red is the canary for the whole change.
5. Re-run distill. Round 0 should open with a non-zero `error` count on
   `/unit_tests/0/expect`, forcing a repair instead of the `SUPPORTED` it
   returned this time.
6. Promote only if the new run's `checks_after` is clean and step 3's diff was
   accounted for.

Suggested order: problem 1 first — it is tight, fully evidenced, and fixes the
only wrong number in the spec. Problem 2 next, because the suite is red and
nothing should be committed over it. Then 3 and 4, which are what integration
agents and stage 4 actually consume. Then 5, 6, 7.

## How to pick up

```
cd loop
python3 -m pytest tests/ -q \
  --ignore=tests/test_promote.py --ignore=tests/test_cbp2025_adapter.py \
  --ignore=tests/test_integrate_revision.py --ignore=tests/test_llm_gateway.py \
  --ignore=tests/test_llm_retry.py
```

Expect **1 failed, 671 passed, 20 skipped** until problem 2 is resolved. The
one failure is `test_preflight_passes_when_every_knob_reaches_the_build`. The
five ignored modules fail to import for want of `ray`; that is pre-existing and
unrelated.

`tests/test_constraints.py::test_the_real_spec_is_accounted_and_clean` is the
canary on the checked-in spec and is currently green. Note that it is green
over a spec with a wrong number in it — that is problem 1, not a reason to
distrust the canary.

To see what the checks say about any spec:

```
cd loop && python3 -c "
import json, spec_checks
for f in spec_checks.run_checks(json.load(open('../spec/sr.paper_only.json')), 192*1024*8):
    print(f.severity.upper(), f.pointer, f.code)
"
```

Current output is 10 warns, 2 infos, 0 errors: `feature_budget_fit` (problem
4), `storage_param_unaccounted` on `/parameters/11`, six `unreferenced_param`
warns on the WT and UT entry-count knobs, `untested_counter_lifecycle` on the
Tomasulo entry format, `unproduced_context` on `complete`, and two
`undefined_helper` infos on `update`.

To replay one check across the corpus — the shape step 3 needs:

```
cd loop && python3 -c "
import json, glob, spec_checks
for f in sorted(glob.glob('../out/*_spec_*.json')):
    s = json.load(open(f))
    if 'unit_tests' not in s: continue
    for x in spec_checks._check_unit_test_arithmetic(s):
        print(f.split('/')[-1], x.pointer, x.message[:60])
"
```

## Where to look

- `loop/spec_checks.py` — all deterministic checks. Read the docstrings; each
  records the run that motivated it and the false positives that shaped it.
  `_ALLOWED_ARITH_NODES` onward is the arithmetic gate and is the most
  historically-annotated block in the file.
- `loop/spec_review.py` — `_drop_regressing_patches` and the round gate, for
  problem 7.
- `out/20260923_183748_*` and `out/20260923_211658_*` — the last two runs.
  Diffing the two `spec_final.json` files shows what the promoted spec gained
  and lost.
- `third_party/runlts/runlts.txt` — the paper. Table 3 is at line 868, the
  digest figure at 485, the register components at 446.
