# gem5 integration notes for the sR port

Facts below were read from gem5 `stable` (v25.1 era) on 2026-09-11. The integration agent gets this file inside its prompt.

## Where TAGE-SC-L lives

All under `src/cpu/pred/`: `tage_sc_l.hh/.cc` (`TAGE_SC_L`, abstract), `tage_sc_l_64KB.hh/.cc` (`TAGE_SC_L_64KB` plus its `TAGE_SC_L_64KB_StatisticalCorrector`), `tage_base.*`, `statistical_corrector.hh/.cc`, `loop_predictor.*`. Python params live in `BranchPredictor.py`. Build registration is in `SConscript`.

## Interface, version-sensitive

On gem5 v25.1 and later, direction predictors subclass `ConditionalPredictor` (`conditional.hh`):

```cpp
virtual bool lookup(ThreadID tid, Addr pc, void * &bp_history) = 0;
virtual void updateHistories(ThreadID tid, Addr pc, bool uncond, bool taken,
                             Addr target, const StaticInstPtr &inst, void * &bp_history) = 0;
virtual void squash(ThreadID tid, void * &bp_history) = 0;
virtual void update(ThreadID tid, Addr pc, bool taken, void * &bp_history,
                    bool squashed, const StaticInstPtr &inst, Addr target) = 0;
```

On v24.x and earlier the same four virtuals live directly on `BPredUnit`. Pin the checkout to one release before the agent starts. `void *&bp_history` is the per-branch speculative-state token: allocate in `lookup`, restore in `squash`, train and free in `update` at commit.

## Cleanest hook: subclass StatisticalCorrector (option 1)

`TAGE_SC_L::predict` already calls `statisticalCorrector->scPredict(...)` after the TAGE and loop components. So the sR port mirrors `TAGE_SC_L_64KB_StatisticalCorrector`:

1. Subclass `StatisticalCorrector`. Implement the pure virtuals `gPredictions`, `getIndBiasBank`, `gIndexLogsSubstr`, `gUpdates`.
2. Override `scPredict` to add the sR term into the LSUM (the `init_lsum` argument is the clean injection point), and `condBranchUpdate` to train the sR tables.
3. Select it from Python with no TAGE plumbing changes:

```python
cpu.branchPred = BranchPredictor(
    conditionalBranchPred=TAGE_SC_L_64KB(statistical_corrector=SRStatisticalCorrector()))
```

Register the new class in `src/cpu/pred/SConscript` (`Source('sr_corrector.cc')` plus the SimObject list) and in `BranchPredictor.py`, then rebuild with scons.

Fallback options: subclass `TAGE_SC_L` and post-process `pred_taken` after `scPredict` (more code, full visibility), or a new `ConditionalPredictor` wrapper that owns a `TAGE_SC_L_64KB` child (most invasive).

## Register values

`update` receives `const StaticInstPtr &inst`, which gives opcode and register indices, not runtime values. Runtime register values need a probe or an execute-stage hook. This is the spec's `host_interfaces` fallback case: start with a decode-visible proxy digest and record the deviation in PORT_NOTES.md. TODO(week 2): decide between an O3 probe listener and a commit-stage tap.

## Enable knob and tunables

Every sR parameter becomes a `Param` on the new SimObject in `BranchPredictor.py` (pattern: the GEHL knobs on `StatisticalCorrector`). Python-level params retune without a C++ rebuild, which is what the DSE stage needs. Add `sr_enable = Param.Bool(False, ...)` as the feature knob.

## Metrics

From `m5out/stats.txt`: conditional-direction MPKI = 1000 * `system.cpu.branchPred.condIncorrect` / committed instructions. Whole-unit misses: `system.cpu.commit.branchMispredicts`. IPC: `system.cpu.ipc`. The `StatisticalCorrector` stats group has `correct` and `wrong` scalars, useful to see how often sR flips a prediction. Stat prefixes depend on the config script naming. The leaf names are the stable part.
