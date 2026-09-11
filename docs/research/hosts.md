# Branch-predictor integration points: ChampSim & gem5 (verified against live repos, 2026-09-11)

## A) ChampSim (github.com/ChampSim/ChampSim, default branch `master`, last push 2026-09-04)

### A.1 Directory layout / what ships
`branch/` on master contains exactly four predictors (each a dir with `<name>.h`/`<name>.cc`):
- `branch/bimodal/`, `branch/gshare/`, `branch/perceptron/`, `branch/hashed_perceptron/` (+ `folded_shift_register.h`)

**No TAGE or TAGE-SC-L ships in ChampSim master.** The most TAGE-SC-L-ish thing is `hashed_perceptron` (16 GEHL-style tables, geometric history lengths 0..232, adaptive threshold — see `branch/hashed_perceptron/hashed_perceptron.h`). **`hashed_perceptron` is the default** when a config doesn't specify one — `config/parse.py` line 425:
```python
'_branch_predictor_data':
    [*map(branch_parse, util.wrap_list(c.get('branch_predictor', 'hashed_perceptron')))],
```
(Note: the repo's example `champsim_config.json` sets `"branch_predictor": "bimodal"`, but that file must be explicitly passed; bare `./config.sh` uses hashed_perceptron.)

### A.2 Current module API (class-based; the legacy free-function API is deprecated)
Modules are C++ classes inheriting `champsim::modules::branch_predictor` (defined in `inc/modules.h`). Hook methods are detected by SFINAE (`has_initialize`, `has_predict_branch`, `has_last_branch_result`), so you implement only what you need, choosing among documented overloads (`docs/src/Modules.rst`):

```cpp
// inc/modules.h (verbatim, core of the branch predictor module base)
struct branch_predictor : public bound_to<O3_CPU> {
  explicit branch_predictor(O3_CPU* cpu) : bound_to<O3_CPU>(cpu) {}
  // SFINAE detection for: initialize_branch_predictor, last_branch_result, predict_branch
  template <typename T, typename... Args>
  constexpr static bool has_initialize = ...;
  template <typename T, typename... Args>
  constexpr static bool has_last_branch_result = ...;
  template <typename T, typename... Args>
  constexpr static bool has_predict_branch = ...;
};
```

Accepted member-function signatures (from `docs/src/Modules.rst`, resolution order for `predict_branch` per `inc/ooo_cpu.h` lines 284–312):
```cpp
void initialize_branch_predictor();                    // optional
bool predict_branch(champsim::address ip, champsim::address predicted_target, bool always_taken, uint8_t branch_type);
bool predict_branch(uint64_t ip, uint64_t predicted_target, bool always_taken, uint8_t branch_type);
bool predict_branch(champsim::address ip);
bool predict_branch(uint64_t ip);
void last_branch_result(champsim::address ip, champsim::address branch_target, bool taken, uint8_t branch_type);
void last_branch_result(uint64_t ip, uint64_t branch_target, bool taken, uint8_t branch_type);
```
`branch_type` values: `BRANCH_DIRECT_JUMP, BRANCH_INDIRECT, BRANCH_CONDITIONAL, BRANCH_DIRECT_CALL, BRANCH_INDIRECT_CALL, BRANCH_RETURN, BRANCH_OTHER`.

Minimal complete example — `branch/bimodal/bimodal.h` (verbatim, trimmed):
```cpp
class bimodal : champsim::modules::branch_predictor
{
  static constexpr std::size_t TABLE_SIZE = 16384;
  std::array<champsim::msl::fwcounter<2>, TABLE_SIZE> bimodal_table;
public:
  using branch_predictor::branch_predictor;   // inherit O3_CPU* ctor
  bool predict_branch(champsim::address ip);
  void last_branch_result(champsim::address ip, champsim::address branch_target, bool taken, uint8_t branch_type);
};
```

**Legacy API** (old ChampSim, still supported): free functions `void O3_CPU::initialize_branch_predictor()`, `uint8_t O3_CPU::predict_branch(uint64_t ip, uint64_t predicted_target, uint8_t always_taken, uint8_t branch_type)`, `void O3_CPU::last_branch_result(uint64_t ip, uint64_t branch_target, uint8_t taken, uint8_t branch_type)`. Enabled by dropping an empty file named `__legacy__` in the module dir, or `{"path": ..., "legacy": true}` in the config (`docs/src/Legacy-modules.rst`, detection in `config/modules.py`).

### A.3 Adding + selecting a new predictor
1. `mkdir branch/rbias && $EDITOR branch/rbias/rbias.{h,cc}` — **the class name must equal the directory basename** (`config/modules.py`: `'class': ... os.path.basename(path)` for non-legacy modules).
2. Config JSON (top level or per-core under `ooo_cpu[]`): `{"branch_predictor": "rbias"}`. Legal values are directory names under `branch/` **or arbitrary paths** (`docs/src/Creating-a-configuration-file.rst`). Out-of-tree module dirs: `./config.sh --branch-dir DIR` or `--module-dir DIR` (dir containing a `branch/` subdir) — this is how a hackathon repo can keep its module outside the ChampSim checkout.
3. `./config.sh my_config.json && make`, run `bin/champsim`.

**Composition caveat (matters for RBias):** `"branch_predictor"` accepts a JSON list (`util.wrap_list`). All listed modules get `initialize`/`last_branch_result` calls, but `impl_predict_branch` combines returns with a comma-fold — `return std::apply([&](auto&... b) { return (..., process_one(b)); }, intern_);` (`inc/ooo_cpu.h` line 309) — i.e. **only the LAST module's return value is used, and modules cannot see each other's predictions**. So for a side-predictor that biases a base prediction, the clean ChampSim pattern is **one module that internally instantiates the base predictor** (modules are plain classes constructible from `O3_CPU*`, so e.g. `#include "../hashed_perceptron/hashed_perceptron.h"` and hold it as a member, or copy a TAGE implementation in), then apply the RBias override inside your own `predict_branch(ip, predicted_target, always_taken, branch_type)` (use the 4-arg overload — it gets branch_type and the BTB's target/always-taken hint). Feed both components from `last_branch_result`.

### A.4 Where predictions are consumed (host hook)
`src/ooo_cpu.cc` `O3_CPU::do_predict_branch` (lines 131–170):
```cpp
sim_stats.total_branch_types.increment(arch_instr.branch);
auto [predicted_branch_target, always_taken] = impl_btb_prediction(arch_instr.ip, arch_instr.branch);
arch_instr.branch_prediction = impl_predict_branch(arch_instr.ip, predicted_branch_target, always_taken, arch_instr.branch) || always_taken;
...
if (predicted_branch_target != arch_instr.branch_target
    || (((arch_instr.branch == BRANCH_CONDITIONAL) || (arch_instr.branch == BRANCH_OTHER))
        && arch_instr.branch_taken != arch_instr.branch_prediction)) {
  sim_stats.branch_type_misses.increment(arch_instr.branch);
  ...
}
impl_update_btb(...); impl_last_branch_result(arch_instr.ip, arch_instr.branch_target, arch_instr.branch_taken, arch_instr.branch);
```
Note prediction is invoked for **every** instruction (branch or not), and the update (`last_branch_result`) happens immediately at fetch/predict time in program order — no squash/rollback API exists in ChampSim (trace-driven).

### A.5 Getting MPKI / IPC
Plain text output (`src/plain_printer.cc`, per simulation phase, per cpu):
```
{cpu} cumulative IPC: {ipc} instructions: {n} cycles: {c}
{cpu} Branch Prediction Accuracy: {pct}% MPKI: {mpki} Average ROB Occupancy at Mispredict: {occ}
Branch type MPKI
BRANCH_DIRECT_JUMP: ...   (one line per type)
```
MPKI is computed as `1000 * total_mispredictions / instrs` where mispredictions sum `branch_type_misses` over the 6 real branch types. Machine-readable: run with `--json [filename]` (stdout if no filename) — JSON contains `"instructions"`, `"cycles"`, and a `"mispredict"` map of per-type miss counts (`src/json_printer.cc`); compute MPKI/IPC from those. Stats cover only the Simulation phase, not Warmup.

### A.6 Traces
Positional CLI args (one per configured core), required, `CLI::ExistingFile`-checked (`src/main.cc`):
```
bin/champsim --warmup-instructions 200000000 --simulation-instructions 500000000 path/to/600.perlbench_s-210B.champsimtrace.xz
```
- Short forms `-w`, `-i`; if only `-i` given, warmup defaults to `simulation/5`. `--json`, `--listeners` also available. Underscore spellings (`--warmup_instructions`) are deprecated aliases.
- Format: xz/gz-compressed `.champsimtrace.xz` (fixed-layout `input_instr` records, see `inc/trace_instruction.h`); DPC-3 SPEC traces at https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/ ; self-tracing tools (Pin-based) in `tracer/`.
- Build deps via vcpkg submodule: `git submodule update --init && vcpkg/bootstrap-vcpkg.sh && vcpkg/vcpkg install`.

---

## B) gem5 (github.com/gem5/gem5, default branch `stable`, current = v25.1 era)

### B.1 Where TAGE-SC-L lives (exact files under `src/cpu/pred/`)
- `tage_sc_l.hh/.cc` — `TAGE_SC_L` (abstract, extends `LTAGE`), `TAGE_SC_L_TAGE` (extends `TAGEBase`), `TAGE_SC_L_LoopPredictor`
- `tage_sc_l_64KB.hh/.cc`, `tage_sc_l_8KB.hh/.cc` — concrete `TAGE_SC_L_64KB` / `TAGE_SC_L_8KB` + their `*_StatisticalCorrector`s
- `tage_base.hh/.cc` (`TAGEBase`), `tage.hh/.cc` (`TAGE`), `ltage.hh/.cc` (`LTAGE`), `loop_predictor.hh/.cc`, `statistical_corrector.hh/.cc`
- Wrapper/plumbing: `bpred_unit.hh/.cc` (`BPredUnit`), `conditional.hh/.cc` (`ConditionalPredictor`), `btb.*`, `simple_btb.*`, `ras.*`, `simple_indirect.*`, `branch_type.hh`
- Python params: `BranchPredictor.py`; build registration: `SConscript`

### B.2 The interface a direction predictor implements — **VERSION-SENSITIVE**
**Current `stable` (v25.1+; `conditional.hh` first appears at tag v25.1.0.0 — 404s at v25.0.0.0 and earlier):** direction predictors subclass `ConditionalPredictor` (SimObject), and `BPredUnit` is a wrapper holding `btb`, `ras`, `cPred` (conditional), `iPred` (indirect). Verbatim from `src/cpu/pred/conditional.hh`:
```cpp
class ConditionalPredictor : public SimObject
{
  public:
    virtual bool lookup(ThreadID tid, Addr pc, void * &bp_history) = 0;
    virtual void updateHistories(ThreadID tid, Addr pc, bool uncond,
                                 bool taken, Addr target,
                                 const StaticInstPtr &inst,
                                 void * &bp_history) = 0;
    virtual void squash(ThreadID tid, void * &bp_history) = 0;
    virtual void update(ThreadID tid, Addr pc, bool taken,
                        void * &bp_history, bool squashed,
                        const StaticInstPtr &inst, Addr target) = 0;
    virtual void branchPlaceholder(ThreadID tid, Addr pc,
                                   bool uncond, void * &bp_history); // optional (decoupled front-end)
};
```
**v24.x and earlier (e.g. v24.1.0.1):** these same four pure virtuals (`lookup`, `updateHistories`, `squash`, `update`) live directly on `BPredUnit` (`bpred_unit.hh` lines 146–186 at that tag) and predictors subclass `BPredUnit`. Same semantics, different base class + wiring.

`void *&bp_history` is the per-branch speculative-state token: allocate your history object in `lookup`, restore-and-free in `squash`, train-and-free in `update` (called at commit; `squashed=true` calls mean "revert speculative history using resolved direction/target" and do NOT free). Call sites in `BPredUnit::predict` (`bpred_unit.cc`): `hist->condPred = cPred->lookup(tid, pc.instAddr(), hist->bpHistory);` (line 153), `cPred->updateHistories(...)` (line 320), `cPred->update(...)` at commit (line 380) and at squash (line 526), `cPred->squash(...)` (line 453).

### B.3 SimObject params (Python) and wiring
`src/cpu/pred/BranchPredictor.py` (verbatim, trimmed):
```python
class BranchPredictor(SimObject):
    type = "BranchPredictor"
    cxx_class = "gem5::branch_prediction::BPredUnit"
    cxx_header = "cpu/pred/bpred_unit.hh"
    instShiftAmt = Param.Unsigned(0, "...")           # 2 for Arm/RISC-V, 0 for x86
    speculativeHistUpdate = Param.Bool(True, "...")
    requiresBTBHit = Param.Bool(False, "...")
    updateBTBAtSquash = Param.Bool(True, "...")
    takenOnlyHistory = Param.Bool(False, "...")
    btb = Param.BranchTargetBuffer(SimpleBTB(), "Branch target buffer (BTB)")
    ras = Param.ReturnAddrStack(ReturnAddrStack(), "...")
    conditionalBranchPred = Param.ConditionalPredictor("Conditional branch predictor")
    indirectBranchPred = Param.IndirectPredictor(SimpleIndirectPredictor(), "...")

class TAGE_SC_L(LTAGE):          # abstract
    statistical_corrector = Param.StatisticalCorrector("Statistical Corrector. Set to NULL to disable it")

class TAGE_SC_L_64KB(TAGE_SC_L):
    type = "TAGE_SC_L_64KB"
    cxx_class = "gem5::branch_prediction::TAGE_SC_L_64KB"
    cxx_header = "cpu/pred/tage_sc_l_64KB.hh"
    tage = TAGE_SC_L_TAGE_64KB()
    loop_predictor = TAGE_SC_L_64KB_LoopPredictor()
    statistical_corrector = TAGE_SC_L_64KB_StatisticalCorrector()
```
O3 default (`src/cpu/o3/BaseO3CPU.py` lines 202–207, stable):
```python
branchPred = Param.BranchPredictor(
    BranchPredictor(conditionalBranchPred=TournamentBP(numThreads=Parent.numThreads)),
    "Branch Predictor")
```
So on current stable you select TAGE-SC-L with:
```python
cpu.branchPred = BranchPredictor(conditionalBranchPred=TAGE_SC_L_64KB())
```
(on v24.x and earlier it was `cpu.branchPred = TAGE_SC_L_64KB()` directly). Tunables are ordinary Params on `TAGEBase` (nHistoryTables, minHist, maxHist, tagTableTagWidths, logTagTableSizes, logUResetPeriod, ...) and on `StatisticalCorrector` (GEHL knobs — `bwnb/bwm/logBwnb/bwWeightInitValue`, `lnb/lm/logLnb`, `inb/im/logInb`, `logBias`, `logSizeUp`, `chooserConfWidth`, `updateThresholdWidth`, `pUpdateThresholdWidth`, `extraWeightsWidth`, `scCountersWidth`, `speculativeHistUpdate`), overridable per-instance from the Python config with no C++ rebuild.

Registering a new C++ predictor: add `Source('rbias.cc')` and the SimObject class name to the `sim_objects=[...]` list in `src/cpu/pred/SConscript` (plus a params class in `BranchPredictor.py` or your own SimObject .py), then rebuild with scons.

### B.4 Cleanest hook points for an RBias (statistical-corrector-style) side predictor
The exact precedent is in `TAGE_SC_L::predict` (`src/cpu/pred/tage_sc_l.cc` lines 404–458, verbatim core):
```cpp
bool
TAGE_SC_L::predict(ThreadID tid, Addr pc, bool cond_branch, void* &b)
{
    TageSCLBranchInfo *bi = new TageSCLBranchInfo(*tage, *statisticalCorrector, *loopPredictor, pc, cond_branch);
    b = (void*)(bi);
    bool pred_taken = tage->tagePredict(tid, pc, cond_branch, bi->tageBranchInfo);
    pred_taken = loopPredictor->loopPredict(tid, pc, cond_branch, bi->lpBranchInfo, pred_taken, instShiftAmt);
    ...
    if (statisticalCorrector) {
        bool use_tage_ctr = bi->tageBranchInfo->hitBank > 0;
        int8_t tage_ctr = use_tage_ctr ? tage->getCtr(...) : 0;
        bool bias = (bi->tageBranchInfo->longestMatchPred != bi->tageBranchInfo->altTaken);
        pred_taken = statisticalCorrector->scPredict(tid, pc, cond_branch, bi->scBranchInfo,
                                                     pred_taken, bias, use_tage_ctr, tage_ctr,
                                                     tage->getTageCtrBits(),
                                                     bi->tageBranchInfo->hitBank, bi->tageBranchInfo->altBank);
        if (bi->scBranchInfo->usedScPred) bi->tageBranchInfo->provider = SC;
    }
    bi->lpBranchInfo->predTaken = pred_taken;
    return pred_taken;
}
```
The SC override signature (`statistical_corrector.hh`):
```cpp
virtual bool scPredict(ThreadID tid, Addr branch_pc, bool cond_branch, BranchInfo *bi,
                       bool prev_pred_taken, bool bias_bit, bool use_conf_ctr,
                       int8_t conf_ctr, unsigned conf_bits, int hitBank, int altBank,
                       int init_lsum = 0);
```
and its `BranchInfo` carries `scPred, lsum, thres, predBeforeSC, usedScPred` plus TAGE confidences `lowConf/highConf/altConf/medConf`. Training hook: `TAGE_SC_L::update` → `statisticalCorrector->condBranchUpdate(tid, pc, taken, bi, corrTarget, bias_bit, hitBank, altBank)`; history maintenance via `scHistoryUpdate`/`updateHistories` + checkpoint/restore `scRecordHistState`/`scRestoreHistState`.

Three porting options, cleanest first:
1. **Subclass `StatisticalCorrector`** (mirror `TAGE_SC_L_64KB_StatisticalCorrector` in `tage_sc_l_64KB.{hh,cc}`) and set it as `statistical_corrector=` on a `TAGE_SC_L_64KB` instance from Python. You must implement the pure virtuals `gPredictions`, `getIndBiasBank`, `gIndexLogsSubstr`, `gUpdates`; override `scPredict`/`condBranchUpdate` to inject the RBias term (e.g. via `init_lsum` or by adding a GEHL-like component). Zero changes to the TAGE plumbing; RBias sees the base prediction (`prev_pred_taken`) and TAGE confidence exactly like a real SC.
2. **Subclass `TAGE_SC_L` and override `predict()`** to post-process `pred_taken` after `scPredict` (add a provider enum value after `SC`). Slightly more code, full visibility.
3. **New `ConditionalPredictor` wrapper** that owns a `TAGE_SC_L_64KB` child param plus the RBias table, overriding all 4 virtuals and delegating — most invasive, but keeps RBias host-agnostic.

### B.5 Stats for MPKI / IPC (names as they appear in stats.txt, m5out)
- Branch predictor group (child SimObject `branchPred` of the CPU → `system.cpu.branchPred.*`), from `BPredUnit::BPredUnitStats` (`bpred_unit.hh` lines 444–481 / `bpred_unit.cc` ADD_STATs):
  - `condPredicted`, `condPredictedTaken`, `condIncorrect` ("Number of conditional branches incorrect") — **conditional-direction MPKI = 1000 * condIncorrect / committed insts**
  - `lookups`, `squashes`, `corrected`, `committed`, `mispredicted` (all Vector2d, indexed [tid][BranchType]), `mispredictDueToPredictor`, `mispredictDueToBTBMiss`, `targetProvider`, `targetWrong`, `BTBLookups/BTBUpdates/BTBHits/BTBHitRatio/BTBMispredicted`, `indirect*`
- Commit-side: `system.cpu.commit.branchMispredicts` (`src/cpu/o3/commit.cc` line 177 ADD_STAT; incremented at line 841) — total committed mispredicted branches, the usual numerator for whole-BPU MPKI.
- IPC: `system.cpu.ipc` and `system.cpu.cpi` — core-level formulas in `BaseCPU::BaseCPUStats` (`src/cpu/base.cc`): `ipc = numInsts / numCycles`. Per-thread variants under `system.cpu.commitStats0.ipc` etc. Instruction count: `system.cpu.commitStats0.numInsts` / `baseStats numInsts`.
- SC-specific: `StatisticalCorrectorStats` has `correct` / `wrong` scalars (`statistical_corrector.hh` lines 215–220) — handy for measuring how often the corrector (or your RBias) flips usefully.
- Debug flags for tracing: `DebugFlag('Branch')`, `'Tage'`, `'LTage'`, `'TageSCL'` (`src/cpu/pred/SConscript`).

## Side-by-side summary for the RBias port
| | ChampSim | gem5 (stable v25.1) |
|---|---|---|
| Direction-pred base | `champsim::modules::branch_predictor` (inc/modules.h) | `branch_prediction::ConditionalPredictor` (conditional.hh); `BPredUnit` virtuals on ≤ v24.x |
| Predict hook | `bool predict_branch(ip[, predicted_target, always_taken, branch_type])` | `bool lookup(tid, pc, void*& bp_history)` |
| Train hook | `void last_branch_result(ip, target, taken, branch_type)` (immediate, in-order, no squash) | `update(..., squashed, ...)` at commit + `squash()` + `updateHistories()` (speculative state via bp_history token) |
| Base TAGE-SC-L available? | No (default = hashed_perceptron); bring your own TAGE | Yes: `TAGE_SC_L_64KB` / `TAGE_SC_L_8KB` |
| Cleanest SC-style insertion | One module class composing base predictor + RBias internally (multi-module list only keeps the LAST return value) | Subclass `StatisticalCorrector` (or override `TAGE_SC_L::predict` after `scPredict`) |
| Selection | JSON `"branch_predictor": "name-or-path"` → `./config.sh [--branch-dir DIR]` → `make` | Python: `cpu.branchPred = BranchPredictor(conditionalBranchPred=TAGE_SC_L_64KB(...))`; new C++ needs SConscript + BranchPredictor.py + scons rebuild |
| MPKI/IPC | stdout lines `cumulative IPC:` / `Branch Prediction Accuracy: ...% MPKI: ...` + per-type `Branch type MPKI`; `--json` for machine-readable | `system.cpu.branchPred.condIncorrect`, `system.cpu.commit.branchMispredicts`, `system.cpu.ipc` in m5out/stats.txt |
| Workload | positional `.champsimtrace.xz` traces + `-w/-i` instruction counts | full-system/SE-mode binaries via gem5 config scripts |

## SOURCES
https://api.github.com/repos/ChampSim/ChampSim/git/trees/master?recursive=1
https://raw.githubusercontent.com/ChampSim/ChampSim/master/inc/modules.h
https://raw.githubusercontent.com/ChampSim/ChampSim/master/branch/bimodal/bimodal.h
https://raw.githubusercontent.com/ChampSim/ChampSim/master/branch/bimodal/bimodal.cc
https://raw.githubusercontent.com/ChampSim/ChampSim/master/branch/hashed_perceptron/hashed_perceptron.h
https://raw.githubusercontent.com/ChampSim/ChampSim/master/champsim_config.json
https://raw.githubusercontent.com/ChampSim/ChampSim/master/docs/src/Modules.rst
https://raw.githubusercontent.com/ChampSim/ChampSim/master/docs/src/Legacy-modules.rst
https://raw.githubusercontent.com/ChampSim/ChampSim/master/docs/src/Creating-a-configuration-file.rst
https://raw.githubusercontent.com/ChampSim/ChampSim/master/config/modules.py
https://raw.githubusercontent.com/ChampSim/ChampSim/master/config/parse.py
https://raw.githubusercontent.com/ChampSim/ChampSim/master/src/plain_printer.cc
https://raw.githubusercontent.com/ChampSim/ChampSim/master/src/json_printer.cc
https://raw.githubusercontent.com/ChampSim/ChampSim/master/src/main.cc
https://raw.githubusercontent.com/ChampSim/ChampSim/master/src/ooo_cpu.cc
https://raw.githubusercontent.com/ChampSim/ChampSim/master/inc/ooo_cpu.h
https://raw.githubusercontent.com/ChampSim/ChampSim/master/inc/core_stats.h
https://raw.githubusercontent.com/ChampSim/ChampSim/master/README.md
https://raw.githubusercontent.com/ChampSim/ChampSim/master/config.sh
https://api.github.com/repos/gem5/gem5/contents/src/cpu/pred?ref=stable
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/bpred_unit.hh
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/bpred_unit.cc
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/conditional.hh
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/tage_sc_l.hh
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/tage_sc_l.cc
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/statistical_corrector.hh
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/tage.hh
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/BranchPredictor.py
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/pred/SConscript
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/BaseO3CPU.py
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/commit.cc
https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/base.cc
https://raw.githubusercontent.com/gem5/gem5/v24.1.0.1/src/cpu/pred/bpred_unit.hh

## CAVEATS
All file contents quoted were fetched live from raw.githubusercontent.com on 2026-09-11. Branch/version notes: ChampSim facts are from `master` (default branch, last push 2026-09-04) — the `develop` branch may differ. gem5 facts are from `stable` (default branch; conditional.hh header says 2025 TUM, and the ConditionalPredictor refactor is verified present at tag v25.1.0.0 but 404s at v25.0.0.0/v24.x — so pin to gem5 ≥ v25.1 for the ConditionalPredictor interface, or use the BPredUnit-virtuals interface (verified verbatim at v24.1.0.1) for older releases. Not verified: (1) I did not fetch docs.chialoops.ai or the CHIA repo — the task asked only for the simulator side; (2) gem5 line numbers cited (e.g. tage_sc_l.cc 404–458, commit.cc 177/841, BaseO3CPU.py 202) are for the current stable tip and will drift; (3) the claim that ChampSim's multi-predictor list keeps only the last return value is read directly from the comma-fold in inc/ooo_cpu.h line ~309 but not runtime-tested; (4) exact stats.txt path prefixes (system.cpu.* vs board.processor...) depend on the user's gem5 config script naming — the stat leaf names (branchPred.condIncorrect, commit.branchMispredicts, ipc) are the verified parts. The GitHub code-search API call for ADD_STAT(ipc returned nothing useful (unauthenticated search), so the ipc location was verified by fetching src/cpu/base.cc directly instead.