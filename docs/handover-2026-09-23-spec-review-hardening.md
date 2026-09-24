# Handover: hardening the spec review, 2026-09-23

The session that wrote this audited a distill output against the paper, found
four defects nothing in the loop reported, added checks for them, and re-ran
distill. The second run fixed all four. This is what is left.

## Where things stand

Branch `spec-review-hardening`, two commits ahead of `main`, plus a **large
uncommitted working tree**. Nothing here is committed. Run the tests before
you commit anything; see "How to pick up".

Two distill runs this session:

| run | `out/` prefix | result |
| --- | --- | --- |
| first | `20260923_170937` | 4 `error` findings. Would now fail the gate. |
| second | `20260923_183748` | 0 errors, 4 warns. Passed the gate, and is what sits in `spec/sr.paper_only.json`. |

The second run fixed every error the first one shipped: the write-only
in-flight table, the read-but-never-written checkpoint table, three mutually
contradictory squash algorithms, and a decay counter that could wedge a digest
valid forever. Storage went from 338,279 bits to 87,655. Open questions went
from 62 to 34, with zero false "unverifiable evidence" entries and no
review-process text leaking into the artifact.

It is a good spec. It is not a correct one — see problem 1.

## What changed in this session

Four new deterministic checks in `loop/spec_checks.py`, all wired into
`run_checks`, and one reviewer-accuracy gate spanning `loop/paper_markers.py`
and `loop/spec_review.py`.

| what | where | severity |
| --- | --- | --- |
| `_check_state_liveness` — storage only one end of the pipeline touches. Emits `write_only_state` and `unfilled_state`. | `spec_checks.py:1644` | error |
| `_check_hollow_algorithms` — a body that does nothing under notes that claim work. Emits `hollow_algorithm` (error) and `empty_algorithm` (warn). | `spec_checks.py:1730` | error / warn |
| `_check_recovery_conflict` — two algorithms on the same flush, one of which unwinds nothing. Emits `contradictory_recovery` and `duplicate_recovery`. | `spec_checks.py:1896` | error / warn |
| `Annotation.corroborates` — a LITERAL or CROSS-CHECK paragraph printing every number in a claim *and* sharing a content word with it. | `paper_markers.py:216` | — |
| `verify_evidence` no longer writes an open question when the source corroborates the claim. The quote is still rejected and the patch still dropped. | `spec_review.py:638` | — |

### The design rule behind `_check_recovery_conflict`

`_check_recovery` (`spec_checks.py:1836`) asks whether *any* algorithm
recovers. The first run satisfied it by **adding** `recover_status_table`
next to a `squash` whose body was `pass`. The gap the check exists to close
was still in the document, one algorithm to the left, and the check was quiet
because it had found its `any`.

Generalize this. An existence check is satisfiable by addition, and a model
asked to repair a spec adds before it edits. Every `any`-shaped check in this
file needs a companion asking whether what it found contradicts anything still
present.

### Things `_check_state_liveness` had to learn the hard way

Each of these was a false positive or negative caught while testing, and each
is pinned by a test in `loop/tests/test_spec_checks.py`:

- `_best_state_match` scores a shared *prefix*. Right for prose labels, wrong
  for identifiers: `h_wt` matched `sr_wt`, `pred_match` matched
  `sr_inflight_predictions`. Replaced with exact-key-then-token-set-equality
  in `_state_owner` (`spec_checks.py:1558`).
- Generic-token stripping collapses a field onto its table: "decay table" and
  `decay_ctr` both reduce to `{decay}`. Field names are excluded.
- `sat_update(...)` did not match a start-anchored verb pattern, so two live
  weight tables read as unfilled. Mutators are matched per underscore segment.
- `-=` is the only thing a decay counter does to itself; it counts as both a
  read and a write.
- The `unfilled_state` host exemption reads `need` only, **not**
  `description`. sR's ROB-index interface says the index is used "to index
  checkpoints", and reading descriptions exempted the largest unfilled table
  in the spec.

## Known problems, most urgent first

### 1. The UT index disagreement moved rather than died, and no check sees it

This is the one real correctness bug in the current spec.

`usefulness_weight_tables` declares `entry_format` as "Vector of 6-bit signed
counters, one per logical register (65 total)". Then:

- `predict` does `vec[r]`, where `r` is an **absolute register id**, 0–64.
- `update` does `ut[idx][pred_reg_idx]`, where `pred_reg_idx` is
  `bank_regs.index(...)` — a **slot within the bank**, 0–8.

One of them trains the wrong counter. The stored field `selected_pred_reg` is
4 bits, which only fits the slot reading, and Figure 5(c) prints
"9x6bit 8 ent. UT0" — an 8-or-9 element per-bank vector. So `update` is right
and `predict` is wrong.

Related, and probably the cause: `state[1].organization` now describes "3
tables (UT0, UT1, UT2)" and has dropped the per-bank dimension entirely, while
`prediction_weight_tables` kept its and is indexed `wt[bank][idx]`.

The first run had the same defect in a different place (`sr_ut[r_up]`, indexing
an 8-bank array with a register id up to 64). It has now survived two runs.
**Fix the check, not just the spec** — this is a recurring class.

What to build: `_check_index_consistency` (`spec_checks.py:2502`) compares
subscripts across algorithms, which cannot catch both sides being wrong
together, and it skips depth 1 entirely. Anchor the comparison to the state
entry's **declared** dimensions instead. `_declared_dimensions`
(`spec_checks.py:2729`) already parses `organization`/`entry_format` for
exactly this. Two rules:

- Every subscript of a declared structure must range over a domain consistent
  with the declared dimension at that position.
- Every leaf use must be subscripted to the declared rank before being read as
  a scalar. The first run's `increment_sat(sr_ut[b].UT0[h])` passed a whole
  vector to a scalar mutator, and nothing said so.

### 2. `_check_state_liveness` is blind to sub-table names

On the current spec it reports **zero traffic** for both weight tables — it
sees neither reads nor writes, so it stays silent rather than finding them
clean:

```
0 prediction_weight_tables     reads=[] writes=[]
1 usefulness_weight_tables     reads=[] writes=[]
2 register_status_table        reads=[decay, predict, recovery] writes=[allocate, decay, recovery, write]
3 inflight_branch_state        reads=[update] writes=[predict]
```

The pseudocode names them `WT0`/`wt[bank][idx]` and `UT0`/`ut[idx]`, never by
their declared names, and `_state_owner` resolves only an exact name or a row
alias. So this run's "0 errors" is partly the check not looking. The
pre-existing `orphan_state` check caught the UT side as a warn; nothing caught
the WT side.

Fix: resolve a sub-table name to its parent state entry.
`_check_index_consistency` already builds a `declared_words` set for this
(`spec_checks.py:2517`) — harvest identifiers out of each entry's
`organization`/`entry_format`/`indexing` prose and map them back to the owning
entry. Do this together with problem 1; they want the same plumbing.

### 3. The budget check compares a feature against the whole chip

`_check_storage` (`spec_checks.py:273`) is passed
`C.BUDGET_TRACKS_BITS["iso-192KiB"]` = 1,572,864 bits, but the spec covers only
sR. 87,655 < 1,572,864, so it stays quiet about a feature 1.63x the paper's own
53,863-bit line item.

The real position: substituting sR into the paper's total gives
1,570,890 − 53,863 + 87,655 = **1,604,682 bits = 195.88 KiB**, over the 192 KiB
cap by 31,818 bits. `logic_cost_notes` and `budget_donors` state the debt
honestly, so it is disclosed rather than hidden, but it is unresolved and the
gate cannot see it.

Give the check a feature-level budget: either the paper's own figure for this
feature, or the track budget minus the host's measured storage
(`adapter.measure_host_storage`, used by stage 4 already).

### 4. A hardcoded `2.5` shipped again, because a warn does not block

`predict` multiplies by the literal `2.5`. The previous run declared it as a
`multiplier` parameter; this one compiled it in, so stage 4 cannot sweep a knob
the paper prints in Figure 5(c). `_check_tuning_literals`
(`spec_checks.py:1453`) fired — correctly, at `warn`, which does not stop the
gate.

Decide whether this class is an error. The argument for: the distiller brief
explicitly asks for "the knobs the paper fixes silently", so a fractional
literal is a brief violation, not a heuristic guess. The argument against: the
parser is loose by design. If you promote it, run the previous specs through
first to see what else it catches.

### 5. Stale and duplicate open questions

34 entries, down from 62, but the remaining set still has both failure modes:

- **Stale.** OQ6 says "the parameter defaults set wt0_entries to 128 and
  wt2_entries to 512". They are 512 and 128, matching the figure — the
  discrepancy was repaired and the question was not withdrawn. OQ23 cites an
  expected digest of `0xBEC`; the unit test says `0xBDC` (which is correct for
  `0x1234567890ABCDEF`).
- **Duplicated.** Roughly five clusters: FP classification at 4/10/15, FP
  alignment at 3/14, the INT field combination at 8/16/23/27, the UT skew at
  1/21/24/29, the count-of-64 handling at 2/13.

Two passes at merge time, both cheap and both using machinery that exists:

- Drop any question quoting a spec value that no longer appears in the spec.
- Cluster on `tokens()`/`stem()` overlap (`spec_checks.py:71,86`) and collapse.

### 6. Unit test 3 tests behaviour the spec does not have

`digest_generation_fp_variants` expects FP16 to extract `Val[15:13]` and FP32
`Value[31:26]`, but `write` implements FP64 only — U5 was resolved as "treat
every value as FP64". The `given` hedges with "if classification is
supported"; the `expect` does not.

Milder than the first run, which asserted the predictor "does not save it to
the inflight state" over pseudocode that saved it, but the same shape: a unit
test contradicting the algorithm it covers. A check comparing each unit test's
named behaviour against the algorithm it exercises would catch both.

### 7. Smaller items

- **`unproduced_context` noise.** Names covered by a `host_interfaces` entry
  are declared, not missing. Before the new checks existed, these were 16 of
  the 20 findings on the first run — `branch.pc`, `inst.dest_reg` and
  friends — and the four real defects produced none. Suppressing them would
  free reviewer attention at no cost.
- **Schema leakage.** The first run copied the schema's own `$schema`, `$id`,
  `title`, `description` and `type` into the instance, because the distiller
  inlines the schema in its prompt. The second run did not, so this is
  intermittent rather than fixed. `additionalProperties: false` on the
  top-level schema is a one-line guard and deserves a test.
- **Unit-test coverage.** 3 tests for 4 state entries and 6 algorithms.
  Requiring one test naming each state entry and each algorithm, plus a
  lifecycle test for any counter field, is the only lever that reaches
  temporal bugs like the decay wedge — which deterministic checks cannot see,
  and which the reviewers did fix on their own this time.

## How to pick up

```
cd loop
python3 -m pytest tests/ -q \
  --ignore=tests/test_promote.py --ignore=tests/test_cbp2025_adapter.py \
  --ignore=tests/test_integrate_revision.py --ignore=tests/test_llm_gateway.py \
  --ignore=tests/test_llm_retry.py
```

Expect **631 passed, 20 skipped**. The five ignored modules fail to import for
want of `ray`; that is pre-existing and unrelated.

`tests/test_constraints.py::test_the_real_spec_is_accounted_and_clean` is the
canary on the checked-in spec. It failed for the whole middle of this session
and is green again. If it goes red, read the message before assuming the check
is wrong — it was right both times.

To see what the checks say about any spec:

```
cd loop && python3 -c "
import json, spec_checks
for f in spec_checks.run_checks(json.load(open('../spec/sr.paper_only.json')), 192*1024*8):
    print(f.severity.upper(), f.pointer, f.code)
"
```

Current output is 4 warns, 5 infos, 0 errors. The warns are `ctr_bits`
unreferenced, `usefulness_weight_tables` orphaned (problem 2), `random.choice`
unproduced, and the hardcoded `2.5` (problem 4).

Suggested order: problems 1 and 2 together, since they share the
declared-dimension plumbing and problem 1 is the only live correctness bug.
Then 3, then 5.

## Where to look

- `loop/spec_checks.py` — all deterministic checks. Read the docstrings; each
  one records the run that motivated it and, more usefully, the false
  positives that shaped it.
- `loop/paper_markers.py` — tier grading of the source text. `corroborates`
  documents one known limitation: a claim whose only number is incidental can
  still match. It costs nothing today because `carry_source_notes` carries
  hedged points independently, but it is real.
- `loop/spec_review.py:554` — `verify_evidence`, where a citation is checked
  and a claim is demoted.
- `out/20260923_170937_*` and `out/20260923_183748_*` — the two runs. Diffing
  the two `spec_final.json` files is the fastest way to see what the checks
  bought.
