# gem5 integration notes for the sR port

Every gem5 fact below was read in gem5 v25.1.0.0 on 2026-09-23. The commit is `7a2b0e413d06c5ce7097104abef3b1d9eaabca91`. Each `file:line` citation points into that tree, relative to the gem5 root. The head holds a read-only copy at `third_party/gem5`. The gem5 node holds the working checkout at `~/gem5`. Run `git -C ~/gem5 rev-parse HEAD` yourself before you trust any of it.

The planning agent and the integration agent both get this file inside their prompt. The timings and the metric values below come from the first cluster run on 2026-09-23, on the 32-vCPU gem5 node, with the clean tree. Two timings are still TODO(measured): an incremental build after a small edit, and a build after a header edit.

This host is gem5's ARM O3 CPU in syscall emulation (SE) mode. Its conditional branch predictor is `TAGE_SC_L_64KB`. That predictor is the same TAGE-SC-L design point as the cbp2025 host, so much of `hosts/cbp2025/NOTES.md` carries over. The plumbing differs. gem5 has a real out-of-order pipeline, and it gives a predictor no register values at all.

The run scripts in `hosts/gem5/run/` are the only way this loop runs gem5. They are fixed. Everything below about running and measuring describes them.

## What you can edit, and what you cannot

| Path | Status |
| --- | --- |
| `src/cpu/pred/**` | Yours. TAGE-SC-L, its statistical corrector (SC), the unit that holds it, `BranchPredictor.py` and the `SConscript`. sR lives here. |
| `src/cpu/o3/commit.cc`, `src/cpu/o3/commit.hh` | Yours for a register-value tap only. See "Register values". |
| `src/cpu/o3/rename.cc`, `src/cpu/o3/rename.hh` | Yours for decode-time writer tracking only. Touch them only for a plan that names that step. |
| Other files in `src/cpu/o3/` | Only what a register-value tap needs, and the plan names each one. |
| `src/cpu/pred/sr_params.h` | Does not exist yet. The port creates it. See "Parameters live in sr_params.h". |
| `src/arch/**`, `src/mem/**`, `SConstruct` | Fixed. An edit there changes what every run measures. |
| `~/p2p_gem5/**` | Fixed. These are the run scripts, the manifest and the workloads. See the trap below. |

One trap in that last row. The adapter installs `~/p2p_gem5` from the repository at the start of stages 2 and 3 and before every baseline recording. It installs it again before every gate attempt (`gate_attempt` in `hosts/gem5/adapter.py`). Each install checks the sha256 of every file it installed before, and it looks for files it did not install. If one file differs, is missing, or is extra, it installs the whole payload again (`install_run_dir`). So the gate always measures the repository's run scripts. An edit there reaches only your own shell runs, and the next gate attempt undoes it. That gate verdict then carries a warning about the reinstall. Do not edit or add anything there.

Plan file paths are relative to the gem5 root, for example `src/cpu/pred/tage_sc_l_64KB.cc`. Stage 2's checks open them in the head's mirror.

## How the CPU reaches the predictor

The CPU is `ArmO3CPU` at its default sizes, at `system.cpu` (`hosts/gem5/run/se_o3.py:247-258`). For example, its ROB holds 192 ops and it commits up to 8 a cycle (`src/cpu/o3/BaseO3CPU.py:127, 188`). The run scripts build the predictor in one fixed way. In effect, se_o3.py does this (`hosts/gem5/run/se_o3.py:267-270`):

```python
system.cpu.branchPred = BranchPredictor(
    conditionalBranchPred=TAGE_SC_L_64KB(),   # --cond-bp, default TAGE_SC_L_64KB
    instShiftAmt=2,
)
```

`BranchPredictor` is the whole unit, C++ class `BPredUnit` (`src/cpu/pred/BranchPredictor.py:199-255`). It holds a BTB, a RAS, an indirect predictor and the conditional predictor. The conditional predictor is a `ConditionalPredictor` (`src/cpu/pred/conditional.hh:57-144`). `TAGE_SC_L_64KB` builds its children from class defaults (`src/cpu/pred/BranchPredictor.py:798-805`). The adapter's fan-out never passes `--cond-bp` (`resolve` in `hosts/gem5/adapter.py`). So every fan-out run, the baseline included, uses `TAGE_SC_L_64KB` with its class defaults.

`instShiftAmt=2` reaches the conditional predictor, its TAGE and its SC through `Parent.instShiftAmt` (`src/cpu/pred/BranchPredictor.py:155-157, 298-300, 621-623`). The loop predictor gets it as an argument (`src/cpu/pred/tage_sc_l.cc:415-417`). Every predictor index therefore uses `pc >> 2`.

The O3 CPU talks to the unit from its branch address calculation stage, class `o3::BAC`. The five calls below are the whole interface. None of them carries a sequence number or a register value.

| Method | Called from | When | TAGE-SC-L body |
| --- | --- | --- | --- |
| `lookup(tid, pc, bp_history)` | `BPredUnit::predict` (`src/cpu/pred/bpred_unit.cc:147-158`) | at fetch, for conditional branches, wrong path included | `TAGE::lookup` calls the virtual `TAGE_SC_L::predict` (`src/cpu/pred/tage.cc:121-129`, `src/cpu/pred/tage_sc_l.cc:404-458`) |
| `updateHistories(tid, pc, uncond, taken, target, inst, bp_history)` | `BPredUnit::predict` (`src/cpu/pred/bpred_unit.cc:310-322`) | right after each prediction, every branch type | speculative history update (`src/cpu/pred/tage_sc_l.cc:541-553`) |
| `squash(tid, bp_history)` | `BPredUnit::squashHistory` (`src/cpu/pred/bpred_unit.cc:428-457`) | for each branch younger than a squash point, youngest first | restores the SC, loop and TAGE histories and deletes the object (`src/cpu/pred/tage_sc_l.cc:530-538`) |
| `update(..., squashed=true, ...)` | `BPredUnit::squash` (`src/cpu/pred/bpred_unit.cc:521-527`) | once, for the mispredicted branch itself | re-applies its histories with the right direction (`src/cpu/pred/tage_sc_l.cc:470-485`) |
| `update(..., squashed=false, ...)` | `BPredUnit::commitBranch` (`src/cpu/pred/bpred_unit.cc:356-381`) | after the branch commits, oldest first | trains the SC, the loop predictor and TAGE, then deletes the object (`src/cpu/pred/tage_sc_l.cc:487-527`) |

The front end is the coupled one. `decoupledFrontEnd` defaults to False (`src/cpu/o3/BaseO3CPU.py:222`), and se_o3.py leaves it alone. So `BAC::updatePC` predicts each branch at fetch with the instruction's own sequence number (`src/cpu/o3/bac.cc:913-927`). Fetch calls it at `src/cpu/o3/fetch.cc:1291`. `branchPlaceholder` belongs to the decoupled front end and never runs here.

Updates and squashes come from `BAC::checkAndUpdateBPUSignals` (`src/cpu/o3/bac.cc:290-360`). It reads commit's signals through the time buffer, one cycle later (`commitToFetchDelay`, `src/cpu/o3/BaseO3CPU.py:85`). Within one cycle the stages tick in this order: bac, fetch, decode, rename, iew, commit (`src/cpu/o3/cpu.cc:380-390`).

`BPredUnit::predict` has the branch's sequence number and keeps it in its `PredictorHistory` (`src/cpu/pred/bpred_unit.cc:121-133`). `lookup` gets only the thread, the PC and the history pointer (`src/cpu/pred/conditional.hh:75`).

### The per-branch history object

`bp_history` is a `TageSCLBranchInfo` (`src/cpu/pred/tage_sc_l.hh:188-202`). It holds three parts:

- `tageBranchInfo`, the TAGE state (`src/cpu/pred/tage.hh:84-96`, `src/cpu/pred/tage_sc_l.hh:89-101`)
- `lpBranchInfo`, the loop predictor state (`src/cpu/pred/ltage.hh:104-118`)
- `scBranchInfo`, a `StatisticalCorrector::BranchInfo` (`src/cpu/pred/statistical_corrector.hh:223-257`)

`TAGE_SC_L::predict` creates it for each conditional branch (`src/cpu/pred/tage_sc_l.cc:407-411`). `TAGE::updateHistories` creates it for an unconditional branch, which never gets a lookup (`src/cpu/pred/tage.cc:136-142`). The object lives until the branch trains at commit or dies in a squash.

The SC's part carries the chooser inputs, `lsum`, `thres`, `predBeforeSC`, and a checkpoint of every SC history. That is the spec's `branch_speculative_state_checkpoint`, and gem5 has it already. `StatisticalCorrector::makeBranchInfo` is virtual (`src/cpu/pred/statistical_corrector.hh:261`, `src/cpu/pred/statistical_corrector.cc:95-99`). A subclass can override it, but a derived `BranchInfo` is a trap. "Where sR's own state lives" says why, and what to do instead.

## Where sR joins the statistical corrector

Read this before you choose a structure. The cbp2025 host taught this loop that sR is one term in the SC's sum and not an override (`hosts/cbp2025/NOTES.md`). The spec says the same in its `statistical_corrector_sum` need. gem5's TAGE-SC-L has that sum.

The sum starts in `StatisticalCorrector::scPredict` and finishes in the 64KB class's `gPredictions`:

```cpp
// src/cpu/pred/statistical_corrector.cc:249-269   StatisticalCorrector::scPredict
bi->predBeforeSC = prev_pred_taken;
int lsum = init_lsum;          // always 0: TAGE_SC_L::predict passes no init_lsum (tage_sc_l.cc:439-447)
lsum += calcBias(...);         // the three bias tables (statistical_corrector.cc:299-322)
scRecordHistState(branch_pc, bi);                  // checkpoint every SC history into bi
int thres = gPredictions(tid, branch_pc, bi, lsum);
bi->lsum = lsum;
bi->thres = thres;
bool scPred = (lsum >= 0);

// src/cpu/pred/tage_sc_l_64KB.cc:105-142   TAGE_SC_L_64KB_StatisticalCorrector::gPredictions
lsum += gPredict(..., bi->bwHist, bwm, bwgehl, ...);           // global backward-branch history
lsum += gPredict(..., bi->pHist, pm, pgehl, ...);              // path history
lsum += gPredict(..., bi->localHistories[1], lm, lgehl, ...);  // first local history
lsum += gPredict(..., bi->localHistories[2], sm, sgehl, ...);  // second local history
lsum += gPredict(..., bi->localHistories[3], tm, tgehl, ...);  // third local history
lsum += gPredict(..., bi->imHist, imm, imgehl, ...);           // second IMLI
lsum += gPredict(..., bi->imliCount, im, igehl, ...);          // IMLI count
int thres = (updateThreshold >> 3) + pUpdateThreshold[getIndUpd(branch_pc)]
    + 12 * (/* one for each of wb, wp, ws, wt, wl, wbw, wi that is >= 0; wim is not counted */);
return thres;
```

The cleanest injection point is one more `lsum += ...` line in `TAGE_SC_L_64KB_StatisticalCorrector::gPredictions`. It goes after the seven `gPredict` terms and before `thres`. That is the gem5 twin of the cbp2025 hook.

The reason is that `gPredictions` runs twice for each conditional branch.

1. At prediction, from `scPredict` (`src/cpu/pred/statistical_corrector.cc:263`).
2. At update, from `condBranchUpdate`, which rebuilds `bi->lsum` and `bi->thres` from `calcBias` and `gPredictions` alone (`src/cpu/pred/statistical_corrector.cc:413-420`).

The rebuild runs because `speculativeHistUpdate` is true. `BranchPredictor.speculativeHistUpdate` defaults to True (`src/cpu/pred/BranchPredictor.py:214-217`). The conditional predictor and the SC inherit it through `Parent` proxies (`src/cpu/pred/BranchPredictor.py:158-161, 680-683`), and se_o3.py does not set it. A term inside `gPredictions` is therefore in LSUM both times. The spec asks for exactly that: sR's total enters LSUM at prediction and again where the host recomputes LSUM at update.

The obvious hook is the wrong one. `scPredict` takes an `int init_lsum = 0` argument (`src/cpu/pred/statistical_corrector.hh:266-270`), and it looks built for this. It is not. `TAGE_SC_L::predict` never passes it (`src/cpu/pred/tage_sc_l.cc:439-447`). The update-time rebuild then drops it, because that rebuild starts from `calcBias` and not from `init_lsum`. An sR term fed through `init_lsum` steers the prediction and then vanishes from the LSUM that trains the thresholds and every weight. Such a port builds, passes G2, and trains against a sum it never predicted with.

Five things follow for the port.

- **The confidence threshold already exists**. The chooser compares `abs(lsum)` with `thres / 4` and `thres / 2`, gated by TAGE's `highConf` and `medConf` (`src/cpu/pred/statistical_corrector.cc:271-293`). Feed sR into LSUM and sR inherits that chooser. Do not invent a second threshold.
- **The update site is the matching one**. `condBranchUpdate` trains only on `scPred != taken || abs(lsum) < thres` (`src/cpu/pred/statistical_corrector.cc:443`). Inside that block it calls `gUpdates` (`src/cpu/pred/statistical_corrector.cc:472`). The 64KB `gUpdates` holds one `gUpdate` call per component (`src/cpu/pred/tage_sc_l_64KB.cc:199-223`). sR's update belongs at the end of `gUpdates`. There it runs under the SC's own condition and sees the rebuilt `bi->lsum`, which includes sR's term.
- **The update knows the branch only through `bi`**. `gUpdates` gets `(tid, pc, taken, bi)` and no sequence number. So sR's prediction-time inputs travel in the SC's `BranchInfo`: the status-table snapshot and the per-bank contributions. The existing components work the same way. `scRecordHistState` copies their histories into `bi` (`src/cpu/pred/statistical_corrector.cc:383-391`, `src/cpu/pred/tage_sc_l_64KB.cc:175-184`), and `gPredictions` reads only the copies. At update, `gPredictions` runs again on those copies with the current tables. That is the spec's "call predict again at update time with the saved snapshot".
- **The existing weights read `bi->lsum`**. Each component's weight update computes `xsum` from `bi->lsum` (`src/cpu/pred/statistical_corrector.cc:235`), and so does the bias weight (`src/cpu/pred/statistical_corrector.cc:453-466`). With the knob on, sR's term changes how every other component trains. The spec wants that.
- **`thres` adapts**. `updateThreshold` and `pUpdateThreshold[]` move each time the SC trains (`src/cpu/pred/statistical_corrector.cc:444-446`). An sR term that adds noise is throttled rather than trusted.

One trap in the pair you copy. The pristine `bw` component, the global backward-branch history, uses one index at prediction and another at update.

- `gPredictions` passes `((branch_pc >> instShiftAmt) << 1) + bi->predBeforeSC` (`src/cpu/pred/tage_sc_l_64KB.cc:109-111`).
- `gUpdates` passes `(pc << 1) + bi->predBeforeSC` (`src/cpu/pred/tage_sc_l_64KB.cc:203-204`).
- `gIndex` and `getIndUpds` shift that value right by `instShiftAmt` again (`src/cpu/pred/statistical_corrector.cc:187-202`).

So `bw` reads one set of table entries and one weight at prediction, and it trains another set at update. The other six components pass the same `pc` both times. Leave the `bw` pair exactly as it is. A fix changes the knob-off `lsum` and the training of every table, and G2 fails at `rel_tol` 0. Do not copy the `bw` pair as sR's template either. Compute sR's table index in one helper, and call it from both the predict term and the update.

`scPredict` builds the sum only for conditional branches (`src/cpu/pred/statistical_corrector.cc:250`). `TAGE_SC_L::update` trains the SC before the loop predictor and TAGE (`src/cpu/pred/tage_sc_l.cc:495-513`).

Every one of those edits sits behind the enable knob. With the knob off, `gPredictions` must return the same `lsum` and the same `thres` as the clean tree. A stray `lsum += 0` changes nothing. An sR weight added to the `thres` formula must also add exactly 0. G2 measures that claim at `rel_tol` 0.

### The alternatives, and why they cost more

1. **`init_lsum`**. It needs an edit in `TAGE_SC_L::predict`, and the update rebuild still drops it. It then also needs an edit in `condBranchUpdate`.
2. **A subclass that overrides `scPredict` and `condBranchUpdate`**. It works. It copies the chooser and the update block, and each copy must stay bit-identical with the knob off.
3. **Changing `pred_taken` after `scPredict` in `TAGE_SC_L::predict`**. That makes sR an override. The spec rules it out, and its `statistical_corrector_sum` fallback is "None". On cbp2025 that design made CycWPPKI 43 percent worse (`hosts/cbp2025/NOTES.md`).

### Where sR's own state lives

sR's tables and its register status table belong with the SC. Two routes keep the gate measuring them.

- **Edit `TAGE_SC_L_64KB_StatisticalCorrector` in place**, behind the knob. No new SimObject is needed. The class stays the default at `src/cpu/pred/BranchPredictor.py:805`, so the gate builds it.
- **Add a subclass** as a new SimObject. The default at `src/cpu/pred/BranchPredictor.py:805` must then name the new class. se_o3.py builds `TAGE_SC_L_64KB()` from class defaults, and the fan-out never passes `--cond-bp`. A port in a class the gate never builds measures nothing.

The register tap needs a path to that state. `TAGE_SC_L` keeps the SC in a private member (`src/cpu/pred/tage_sc_l.hh:168-170`). A forwarding method on `TAGE_SC_L` therefore carries register values from the unit to the SC.

New `BranchInfo` fields have one trap, in how the object dies. `StatisticalCorrector::BranchInfo` declares no destructor, so its destructor is not virtual (`src/cpu/pred/statistical_corrector.hh:223-257`). `TageSCLBranchInfo` gets the object from `sc.makeBranchInfo()`. It frees it with `delete scBranchInfo`, through a base-class pointer (`src/cpu/pred/tage_sc_l.hh:195, 198-201`). The TAGE side declares `virtual ~BranchInfo()` (`src/cpu/pred/tage_sc_l.hh:99-100`), and the SC side does not.

So if `makeBranchInfo` returns a derived struct, that `delete` is undefined behaviour. In practice the derived destructor never runs. A `std::vector` member then leaks on every branch, millions of times in each perf run, in up to 30 runs at once. G2 and the determinism checks do not catch it. No class in the tree overrides the SC's `makeBranchInfo` today, so nothing runs this path yet.

Two choices are safe.

- Add sR's fields to `StatisticalCorrector::BranchInfo` itself. Use scalars and fixed-size arrays, never a `std::vector` or any other owner of heap memory. Then no destructor has work to do.
- For a derived struct, first add `virtual ~BranchInfo() = default;` to `StatisticalCorrector::BranchInfo` (`src/cpu/pred/statistical_corrector.hh:223`). That header is under `src/cpu/pred`, so it is yours. The edit recompiles every TAGE-SC-L and MPP-TAGE file.

Either way, initialize every field. A field read before any write is undefined behaviour, and G2 at `rel_tol` 0 catches the drift it causes.

## Register values: what the host gives you

gem5 gives a predictor no register values. `ConditionalPredictor` sees a PC, the `StaticInst` and the history pointer (`src/cpu/pred/conditional.hh:75-121`). The `StaticInst` names registers but holds no values. The values live in the O3 CPU's physical register file. So the port adds a tap in the CPU.

The design is the planner's decision. The facts it needs follow. The recommendation is a commit-time tap. When an instruction commits, read the values of its destination registers and give them to the predictor. That recommendation has a cost, and the next subsection states it.

### Where an instruction commits

`Commit::commitInsts` retires up to `commitWidth` ops a cycle from the ROB head. For each op it calls `commitHead`, and on success it notifies the `Commit` probe point with the op (`src/cpu/o3/commit.cc:980-991`). By then `commitHead` updated the commit rename map for the op (`src/cpu/o3/commit.cc:1262-1266`). That point, right after `commitHead` returns true, is where a tap reads the op's results.

Facts about what reaches that point:

- Commit works on micro-ops. The probe fires once per op. The instruction count grows only on the last micro-op of a macro-op (`src/cpu/o3/commit.cc:1353-1361`).
- A squashed op never reaches it. The ROB retires squashed ops on a separate path (`src/cpu/o3/commit.cc:954-968`).
- A faulting op never reaches it. `commitHead` returns false and traps (`src/cpu/o3/commit.cc:1185-1248`).
- An SE syscall writes its result to X0 through the thread context, not through a destination operand (`src/arch/arm/faults.cc:830-846`, `src/arch/arm/linux/se_workload.hh:68-80`). A destination-register tap never sees syscall results.

### How to read a committed destination value

```cpp
// head_inst is the o3::DynInstPtr that commitHead() just committed.
const ThreadID tid = head_inst->threadNumber;
for (int i = 0; i < head_inst->numDestRegs(); i++) {
    const RegId &arch = head_inst->destRegIdx(i);    // unflattened, from the StaticInst
    if (!arch.isRenameable())
        continue;                                    // XZR writes and misc registers
    uint64_t value = 0;
    if (arch.regClass().regBytes() == sizeof(RegVal)) {
        value = head_inst->cpu->getArchReg(arch, tid);     // integer and CC registers
    } else {                                               // VecRegClass: 256 bytes on ARM
        std::vector<uint8_t> buf(arch.regClass().regBytes());
        head_inst->cpu->getArchReg(arch, buf.data(), tid);
        std::memcpy(&value, buf.data(), sizeof(value));    // the low 64 bits, the D view
    }
    // hand (head_inst->seqNum, arch.classValue(), arch.index(), value) to the predictor
}
```

The APIs, all public:

| API | What it gives | Where |
| --- | --- | --- |
| `DynInst::numDestRegs()` | destination count | `src/cpu/o3/dyn_inst.hh:687` |
| `DynInst::destRegIdx(i)` | the architectural `RegId`, unflattened | `src/cpu/o3/dyn_inst.hh:696` |
| `DynInst::flattenedDestIdx(i)` | the flattened `RegId` | `src/cpu/o3/dyn_inst.hh:245-251` |
| `DynInst::renamedDestIdx(i)` | the `PhysRegIdPtr` | `src/cpu/o3/dyn_inst.hh:261-267` |
| `DynInst::seqNum`, `cpu`, `threadNumber` | sequence number, `o3::CPU *`, thread | `src/cpu/o3/dyn_inst.hh:124, 130, 319` |
| `o3::CPU::getArchReg(reg, tid)`, `getArchReg(reg, void *, tid)` | the committed value, read through the commit rename map, with no stat update | `src/cpu/o3/cpu.cc:1088-1102` |
| `o3::CPU::getReg(phys, tid)`, `getReg(phys, void *, tid)` | the physical register's value | `src/cpu/o3/cpu.cc:969-1018` |
| `RegId::classValue()`, `index()`, `isRenameable()` | class, index, and false for invalid and misc registers | `src/cpu/reg_class.hh:140-157` |

Two traps in that table.

- `getArchReg` reads through the commit rename map. Called inside `commitHead` before `src/cpu/o3/commit.cc:1262`, it returns the previous writer's value. Called after `commitHead` returns true, it returns this op's value.
- `getReg` bumps the `executeStats` register-read counters on every call (`src/cpu/o3/cpu.cc:971-990`). Those counters print in stats.txt. G2 compares only the metrics, so the bump alone does not fail G2. A tap that does no work with the knob off leaves stats.txt clean, and that is the stronger evidence.

### ARM registers and the spec's 65-register model

The spec numbers 65 logical registers. R0 to R31 are integer, R32 to R63 are FP or SIMD, and R64 is the flags. Map gem5's unflattened `destRegIdx(i)` onto it this way.

| Spec index | gem5 destination `RegId`, unflattened | Source |
| --- | --- | --- |
| R0 to R30 | `IntRegClass`, index 0 to 30, X0 to X30 | `src/arch/arm/regs/int.hh:128-161` |
| R31 | `IntRegClass`, index `int_reg::_SpxIdx`, the stack pointer | `src/arch/arm/regs/int.hh:126, 238` |
| none | an XZR write, which arrives as `InvalidRegClass` | `src/arch/arm/isa/operands.isa:180-184`, `src/cpu/reg_class.hh:288` |
| none | `IntRegClass` `Ureg0` to `Ureg2`, micro-op temporaries | `src/arch/arm/regs/int.hh:116-118` |
| R32 to R63 | `VecRegClass`, index 0 to 31, V0 to V31 | `src/arch/arm/regs/vec.hh:80-83` |
| none | `VecRegClass` index 32 to 43, the special and interleave registers | `src/arch/arm/regs/vec.hh:81-88` |
| R64 | `CCRegClass` `Nz` (index 0), `C` (1), `V` (2) | `src/arch/arm/regs/cc.hh:53-62` |
| none | `CCRegClass` `Ge` (3), `Fp` (4), `Zero` (5) | `src/arch/arm/regs/cc.hh:53-62` |

Notes on that mapping:

- Use the unflattened index. Flattening maps AArch64 X registers onto AArch32 banked storage (`src/arch/arm/regs/int.hh:437-442`, `src/arch/arm/isa.cc:1550-1553`). For example, X15 flattens to `R13Hyp`. Flattened indices are therefore not 0 to 30.
- The stack pointer flattens to `Sp0` at EL0 (`src/arch/arm/regs/int.cc:65-84`). The unflattened `_SpxIdx` is the stable name for it.
- AArch64 FP and SIMD destinations are `VecRegClass`, through the `AA64FpDest` operands (`src/arch/arm/isa/operands.isa:430-450`). `VecElemClass` serves AArch32 VFP (`src/arch/arm/isa/operands.isa:365-373`). The workloads are AArch64 binaries.
- A `VecRegClass` register holds 256 bytes on ARM, because `MaxSveVecLenInBits` is 2048 (`src/arch/arm/types.hh:535-541`, `src/arch/arm/regs/vec.hh:61-65`). The first 8 bytes hold the low 64 bits, the D register.
- The host does not label a value FP16, FP32 or FP64. The spec's FP digest picks the format from the value's upper bits (`generate_digest`), so it needs no label.
- A flags write can span up to three destinations. `Nz` holds `(N << 1) | Z`, and `C` and `V` hold one bit each (`src/arch/arm/isa/insts/data64.isa:44-67`). FCMP writes all three (`src/arch/arm/isa/insts/fp64.isa:902-905`). NZCV is `(Nz << 2) | (C << 1) | V`. An op that writes only `Nz` leaves C and V as they were. A port that builds R64 therefore keeps the last committed `Nz`, `C` and `V`.
- A 32-bit W write is zero-extended into the 64-bit register (`src/arch/arm/isa/operands.isa:220-235`). The tap reads the full 64 bits.

### The cost: a commit tap understates sR

The paper's sR deposits a digest at writeback, the spec's `instruction_writeback`. A commit tap deposits it at commit. Commit runs in program order, so a finished value waits in the ROB until every older op commits. One load that misses in the cache holds back every younger value behind it.

During that wait the paper's sR can already use the value, and the gem5 port cannot. So sR covers fewer branches in gem5 than in the paper. The gem5 result is conservative. It understates what writeback delivery gives, and the plan must say so.

A commit tap also never sees a wrong-path value. The spec lets a wrong-path digest survive a squash (its `pipeline_squash_recovery` notes). That is a second difference to record.

A value does reach the predictor before any younger branch trains. Commit sets `doneSeqNum` to the youngest op it committed (`src/cpu/o3/commit.cc:1012-1013`). BAC trains branches up to it one cycle later (`src/cpu/o3/bac.cc:331-335`, `src/cpu/o3/BaseO3CPU.py:85`). A tap in the commit loop runs in the cycle its op commits.

### The valid bit needs a decode-time claim

The spec clears a register's valid bit at decode, as soon as a younger writer decodes (`instruction_decode`). A commit tap alone cannot clear it that early. Without a decode-time claim, a register keeps its last committed digest while a younger writer is in flight. sR then reads a value the program already replaced.

So a plan that follows the spec's valid bit adds a rename-time hook next to the commit tap. The facts:

- `Rename::renameInsts` renames each op's destinations in `renameDestRegs`, then notifies the `Rename` probe point with the op (`src/cpu/o3/rename.cc:744-757`, point at `src/cpu/o3/rename.cc:202-203`). The op's `seqNum` and `destRegIdx(i)` are both set by then.
- It fires once per renamed op, micro-ops included. That also makes it the spec's `decode_cycle_or_count_tick` pulse.
- A squashed op skips it (`src/cpu/o3/rename.cc:666-677`). A wrong-path op that reaches rename fires it, so its claim needs the flush below.
- A squash that undoes a rename notifies the `SquashInRename` point once per undone mapping (`src/cpu/o3/rename.cc:978-982`). Its argument is `std::pair<InstSeqNum, PhysRegIdPtr>`, the squashed writer's sequence number and its new physical register (`src/cpu/o3/rename.hh:118, 125`).
- The spec's ROB tag is `seqNum & ((1 << SR_ROB_TAG_BITS) - 1)`. At the spec default of 14 bits that spans 16384 ops, and the ROB holds 192 (`src/cpu/o3/BaseO3CPU.py:188`).

An edit in `rename.cc` at the same two places works the same way as the probe points.

### How the predictor receives the values

No existing path carries a register value into the predictor. Each link is closed.

- `ConditionalPredictor` has no such method (`src/cpu/pred/conditional.hh:57-144`).
- `BPredUnit::cPred` is protected (`src/cpu/pred/bpred_unit.hh:403-438`).
- `TAGE_SC_L::statisticalCorrector` is private (`src/cpu/pred/tage_sc_l.hh:168-170`).
- `BAC::bpu` is private (`src/cpu/o3/bac.hh:335-340`), and `o3::CPU::bac` is protected (`src/cpu/o3/cpu.hh:413-415`).

Two routes open one.

**Route A, an edit in commit.cc**. `Commit::Commit` receives `BaseO3CPUParams` (`src/cpu/o3/commit.cc:104`). Its `branchPred` field is the `BPredUnit *` (`src/cpu/o3/BaseO3CPU.py:202-207`), and BAC reads it the same way (`src/cpu/o3/bac.cc:79`). Commit keeps it in a new member, and the tap calls a new public `BPredUnit` method. That method forwards to `cPred` through a new `ConditionalPredictor` virtual with an empty default. `TAGE_SC_L` overrides it and forwards to the SC.

The cost is rebuild time. `commit.hh` is included by `src/cpu/o3/cpu.hh`, so every O3 file recompiles. `conditional.hh` and `bpred_unit.hh` are included by O3 fetch, BAC and FTQ, and by the Minor and simple CPUs.

**Route B, a probe listener, with no O3 edit**. The `Commit` point is a `ProbePointArg<DynInstPtr>` on the CPU's probe manager (`src/cpu/o3/commit.hh:126`, `src/cpu/o3/commit.cc:158-166`). A listener gets the same op as route A, at the same moment.

- The predictor attaches the listener in its own `regProbeListeners()` (`src/sim/sim_object.hh:232`). gem5 calls it after every `regProbePoints()` (`src/python/m5/simulate.py:177-181`).
- It finds the CPU with `SimObject::find("system.cpu")` (`src/sim/sim_object.hh:339`). se_o3.py names the CPU `system.cpu` (`hosts/gem5/run/se_o3.py:257`).
- It connects with `cpu->getProbeManager()->connect<ProbeListenerArg<T, o3::DynInstPtr>>(this, "Commit", &T::onCommit)` (`src/sim/probe/probe.hh:197-205, 237-262`). Keep the returned pointer. Freeing it disconnects the listener.
- The listener type must be exactly `o3::DynInstPtr`. Any other type panics in `addListener` (`src/sim/probe/probe.hh:296-308`). The in-tree `SimpleTrace` example registers a `DynInstConstPtr` listener (`src/cpu/o3/probe/simple_trace.cc:66-74`), which does not match. Do not copy it.
- With the knob off, do not connect at all. The off path then does no work.
- The cost: code in `src/cpu/pred` includes `cpu/o3/dyn_inst.hh`, and the name `system.cpu` is hard-coded. The O3 sources build only with `BUILD_ISA` (`src/cpu/o3/SConscript:45`), which the ARM build sets (`build_opts/ARM:1`).

Two routes that look possible are closed.

- A `ProbeListenerObject` in the config (`src/sim/probe/Probe.py:43-48`) needs an edit to se_o3.py, and the run scripts are fixed.
- A `BranchPredictor` param that points back at the CPU forms a cycle. The CPU's `branchPred` param already points at the unit. gem5 refuses a cycle at instantiate (`src/python/m5/SimObject.py:1300-1309`).

### The writeback alternative

`IEW::writebackInsts` notifies the `ToCommit` point for each op as its execution completes (`src/cpu/o3/iew.cc:1380-1398`, point at `src/cpu/o3/iew.cc:152-153`). That is closer to the spec's `instruction_writeback` trigger. It also sees wrong-path ops, and it needs the flush handling below. A plan that picks it drops the "understates" caveat and takes on the wrong-path one.

## What gem5 has that CBP2025 did not

CBP2025 replays a trace of committed instructions. gem5 runs a real pipeline. Four things follow, and each one changes an interface in the spec.

### 1. A real sequence number

Each dynamic op gets `seqNum` at fetch (`src/cpu/o3/fetch.cc:1010`, `src/cpu/o3/cpu.hh:287`). It is a `uint64_t` (`src/cpu/inst_seq.hh:40`) from one counter per CPU that starts at 1 (`src/cpu/o3/cpu.cc:112`). Wrong-path ops take numbers too. Commit retires in `seqNum` order. gem5's ROB is a list per thread with no index tag (`src/cpu/o3/rob.hh:289`), so `seqNum` modulo `2^rob_tag_bits` is the spec's ROB tag. The spec's `instruction_decode_info` and `instruction_writeback_info` get it directly from the op.

### 2. Squash

A squash reaches the predictor on one path, whatever caused it.

- A mispredicted control op squashes from commit through `bpu->squash(squashed_sn, pc, taken, tid, true)` (`src/cpu/o3/bac.cc:303-313`).
- Any other squash from commit uses `bpu->squash(squashed_sn, tid)` (`src/cpu/o3/bac.cc:314-327`). Memory-order violations, `squashAfter` and traps come this way.
- Decode resteers use the same pair of calls (`src/cpu/o3/bac.cc:337-358`).

`BPredUnit::squash` removes every history whose `seqNum` is above `squashed_sn`, youngest first, and calls `squash` on each (`src/cpu/pred/bpred_unit.cc:403-423, 453`). For a mispredict it then calls `update(..., squashed=true, ...)` on the branch itself (`src/cpu/pred/bpred_unit.cc:489-527`). Tables train only at commit.

The spec's `pipeline_squash_recovery` has a real trigger here, and its flush range is every `seqNum` above `squashed_sn`. The predictor does not receive `squashed_sn` today. The port adds a path: a new virtual called from `BPredUnit::squash`, or the `SquashInRename` point.

### 3. Wrong-path execution

O3 fetches, renames and executes down the predicted path. Wrong-path ops write physical registers and never commit. A commit tap sees only correct-path values. `condPredicted` counts lookups, wrong path included (`src/cpu/pred/bpred_unit.cc:150-153`). The loop's metrics count committed branches only.

### 4. Speculative history

TAGE and SC histories update at prediction time and roll back on a squash.

- Update at prediction: `src/cpu/pred/bpred_unit.cc:310-322`, `src/cpu/pred/tage_base.cc:631-684`, `src/cpu/pred/statistical_corrector.cc:325-350`.
- Roll back on a squash: `src/cpu/pred/tage_sc_l.cc:530-538`, `src/cpu/pred/tage_base.cc:699-735`, `src/cpu/pred/statistical_corrector.cc:393-403`.
- The commit-time call only saves the non-speculative path history (`src/cpu/pred/tage_base.cc:635-643`).

An old comment says TAGE_SC_L updates everything at commit (`src/cpu/pred/BranchPredictor.py:696-697`). The code no longer matches it.

Register state that sR takes at commit is non-speculative, so it needs no rollback. A claim made at rename is speculative, and it needs the flush from item 2.

### The spec's host interfaces, mapped

| Spec need | gem5 source | Notes |
| --- | --- | --- |
| `instruction_decode_info` | `destRegIdx(i)` and `seqNum` at the `Rename` point (`src/cpu/o3/rename.cc:757`) | wrong-path ops rename too |
| `instruction_writeback_info` | the `Commit` point (`src/cpu/o3/commit.cc:991`), or `ToCommit` (`src/cpu/o3/iew.cc:1398`) | commit is the recommendation, and it understates sR |
| `decode_cycle_or_count_tick` | the `Rename` point, once per renamed op | micro-op granularity |
| `branch_speculative_state_checkpoint` | `StatisticalCorrector::BranchInfo` in `scBranchInfo` | lives from lookup to commit or squash |
| `branch_mispredict_flush_range` | every `seqNum` above `squashed_sn` in `BPredUnit::squash` | needs a new path to the predictor |
| `statistical_corrector_sum` | `TAGE_SC_L_64KB_StatisticalCorrector::gPredictions` | runs at prediction and at the update rebuild |

## The enable knob is an environment variable

The run scripts are fixed, so no config flag can reach the port. The gem5 process's environment can. Bind the enable knob as `runtime_env`. Read it once in C++ at construction, into a member that the predict path tests:

```cpp
// in the constructor of the class that owns sR's state
const char *e = std::getenv("SR_SR_ENABLE");
srEnabled = (e != nullptr && e[0] == '1');
```

The gate sets three aliases to the same value for every gem5 run and every test command: the plan's `feature_enable.name`, that name upper-cased, and its `macro` (`enable_env` in `hosts/gem5/adapter.py`). Any one of the three works. For a plan that names `sr_enable` with macro `SR_SR_ENABLE`, the aliases are `sr_enable`, `SR_ENABLE` and `SR_SR_ENABLE`.

How the value travels:

- The gate's fan-out passes it to chia's `Gem5Node.run_gem5`, which merges it over the worker's environment.
- `run_workload.py` passes its own environment to gem5 unchanged (`hosts/gem5/run/run_workload.py:181-190`).
- se_o3.py gives the guest a fixed environment, `GLIBC_TUNABLES=glibc.pthread.rseq=0` and nothing else (`hosts/gem5/run/se_o3.py:91, 306`). The knob is never in the guest's argv or environment, so it cannot move the guest's stack.

One path from the host to the guest remains, through files. gem5 SE mode passes a guest's file open through to the host (`src/sim/syscall_emul.hh:931-944`). It emulates only a short list: `/proc/meminfo`, `/proc/self/maps`, `/etc/passwd`, `/dev/urandom`, `/sys/devices/system/cpu/online`, and paths under `/system/` and `/platform/`. `System.redirect_paths` defaults to an empty list (`src/sim/System.py:119`), and se_o3.py sets none.

- A guest that opens `/proc/self/environ` reads the gem5 process's own environment, and the knob is in it.
- A guest that opens `/proc/self/cmdline` or `/proc/self/stat` reads gem5's argv, with the per-run outdir in it, and gem5's pid.

The current workloads open no `/proc` path. On 2026-09-23 a `qemu-aarch64-static -strace` run covered bzip2, zstd, GAPBS bfs and tc, Lua and SQLite. Each one called `openat` only for its script file, `bench.sql` or `word_freq.lua`. The gate smoke also gave identical numbers with the knob on and off, on an unported tree (`runs/2026-09-23-gem5/README.md`).

The admission rule for a new workload follows from this. Run it under `qemu-aarch64-static -strace` first. If it opens any path under `/proc`, or any file outside its own data directory, do not add it. `hosts/gem5/workloads/check_workloads.py` does not run this check yet, so run it by hand.

Two consequences belong in the plan.

- Off must be the default. The baseline runs with none of the three variables set (`record_baseline` in `hosts/gem5/adapter.py`). A `getenv` result of `nullptr` gives false, and that delivers the default. It is also why the test reads `== '1'` and not `!= '0'`.
- A `compile_time_define` binding costs far more here than on cbp2025. The adapter builds each state with `CCFLAGS_EXTRA` set to `-D<name>=0` or `=1` (`define_env` and `build_env` in `hosts/gem5/adapter.py`). It defines two names only: the plan's `macro` and the upper-cased `feature_enable.name`. It never defines the raw lower-case name, because `-Dsr_enable=0` turns every identifier `sr_enable` in gem5 into `0`. So give the plan an upper-case `macro`. `CCFLAGS_EXTRA` lands on every compile line (`SConstruct:987`), so each flip recompiles all of gem5. Both states define the macro, so a port tests it with `#if` and never with `#ifdef`. Prefer `runtime_env`.

The adapter refuses `python_param`, `constructor_arg` and `other` bindings at build time (`Gem5Executor.build` in `hosts/gem5/adapter.py`). Each of them needs a config change, and the run scripts are fixed.

## Parameters live in sr_params.h

Stage 4 mutates one generated header and nothing else (`params_header` in `loop/dse.py`). The header holds one `#define SR_<PARAMETER_NAME_UPPER_CASED> <value>` per spec parameter. Then it holds one `#define HOST_<NAME>` per plan host knob. Stage 4 refuses gem5 today (`require_searchable` in `loop/dse.py`), and the port still creates the header now.

- Put it at `src/cpu/pred/sr_params.h`. Include it as `#include "cpu/pred/sr_params.h"`, because the build puts `src/` on the include path (`SConstruct:438-439`).
- Create it with exactly the content stage 3's prompt gives under "The params header". The build has to work long before stage 4 runs.
- Every sR tunable comes from an `SR_*` macro. A hard-coded value is a value the search can never move. Do not turn sR's tunables into Python Params. Stage 4 does not write Python, and se_o3.py builds the predictor from class defaults.
- An `enum` parameter arrives as an integer index into its choice list. The mapping sits in a trailing comment. Implement it as an `#if` and `#elif` ladder, or as a `switch`.

The enable knob is the one exception to "everything through the header". It is also `SR_SR_ENABLE` in the header. The gate flips it through the environment, so let the environment win at run time.

### Registering new files

- A new header needs no `SConscript` line. scons finds headers through their includes, and no header in `src/cpu/pred` is listed.
- A new `.cc` needs a `Source('file.cc')` line. The existing ones are at `src/cpu/pred/SConscript:65-89`.
- A new SimObject needs its Python class, with `type`, `cxx_class` and `cxx_header`, in `BranchPredictor.py` or in a new `.py` file. Its name then goes in the `sim_objects` list of the `SimObject(...)` call (`src/cpu/pred/SConscript:44-63`). A new `.py` file gets its own `SimObject('file.py', sim_objects=[...])` call.
- A new debug flag needs a `DebugFlag('Name')` line (`src/cpu/pred/SConscript:90-97`) and `#include "debug/Name.hh"`.
- A gem5 unit test is a `GTest('name.test', 'name.test.cc', ...)` line (`src/SConscript:451-478`, examples at `src/base/SConscript:32-36`). scons builds it as `build/ARM/<dir>/name.test.opt` (`src/SConscript:409-410`). Keep sR's pure logic, such as the digest, the fold and the index functions, in a file with no SimObject in it. A test can then link that file alone.

## Host knobs, and what TAGE-SC-L costs

Stage 4 can shrink TAGE-SC-L to pay for sR only through the plan's `host_knobs`, as on cbp2025. The plan records them, and what they cost, in stage 2.

**gem5 counts no storage for this predictor**. The SC's `getSizeInBits()` returns 0 and says "Not implemented" (`src/cpu/pred/statistical_corrector.cc:493-498`). `TAGEBase::getSizeInBits()` (`src/cpu/pred/tage_base.cc:894-909`) and `LoopPredictor::getSizeInBits()` (`src/cpu/pred/loop_predictor.cc:382-389`) exist, and `TAGE_SC_L` calls neither. The TAGE one also counts 36 tables of 2^10 entries each. The 64KB TAGE allocates two shared banks instead (`src/cpu/pred/tage_sc_l.cc:122-137`), so that count is wrong for it. The loop one does match: 2^5 × (2 × 10 + 4 + 10 + 4 + 1) is 1248 bits. The driver checks a gem5 plan's `host_storage` for self-consistency only, for this reason (`_NO_HOST_STORAGE` in `loop/adopt_a_paper_loop.py`).

**The defaults are CBP2016's 64KB design point**. The gem5 source says it adapted `cbp64KB/predictor.h` (`src/cpu/pred/tage_sc_l_64KB.hh:41-42`). Every size below equals the matching define in the cbp2025 host. The right-hand column comes from `hosts/cbp2025/NOTES.md`, not from gem5. The note under the table names one behaviour that differs.

| gem5 Param | gem5 value | cbp2025 define | cbp2025 value |
| --- | --- | --- | --- |
| `logTagTableSize` | 10 | `LOGG` | 10 |
| `shortTagsSize`, `longTagsSize` | 8, 12 | `TBITS`, `TBITS` + 4 | 8, 12 |
| `shortTagsTageFactor`, `longTagsTageFactor` | 10, 20 | `NBANKLOW`, `NBANKHIGH` | 10, 20 |
| `tagTableCounterBits`, `tagTableUBits` | 3, 1 | `CWIDTH`, `UWIDTH` | 3, 1 |
| `logTagTableSizes[0]`, `logRatioBiModalHystEntries` | 13, 2 | `LOGB`, `HYSTSHIFT` | 13, 2 |
| `numUseAltOnNa`, `useAltOnNaBits` | 16, 5 | `2**LOGSIZEUSEALT`, `ALTWIDTH` | 16, 5 |
| `pathHistBits`, `maxHist` | 27, 3000 | `PHISTWIDTH`, `m[NHIST]` | 27, 3000 |
| `logSizeLoopPred` | 5 | `LOGL` | 5 |
| `loopTableIterBits`, `loopTableTagBits` | 10, 10 | `WIDTHNBITERLOOP`, `LOOPTAG` | 10, 10 |
| `scCountersWidth`, `extraWeightsWidth` | 6, 6 | `PERCWIDTH`, `EWIDTH` | 6, 6 |
| `logBias` | 8 | `LOGBIAS` | 8 |
| `bwnb`, `bwm[0]`, `logBwnb` | 3, 40, 10 | `GNB`, `Gm[0]`, `LOGGNB` | 3, 40, 10 |
| `pnb`, `logPnb` | 3, 9 | `PNB`, `LOGPNB` | 3, 9 |
| `lnb`, `lm[0]`, `logLnb` | 3, 11, 10 | `LNB`, `Lm[0]`, `LOGLNB` | 3, 11, 10 |
| `snb`, `sm[0]`, `logSnb` | 3, 16, 9 | `SNB`, `Sm[0]`, `LOGSNB` | 3, 16, 9 |
| `tnb`, `tm[0]`, `logTnb` | 2, 9, 10 | `TNB`, `Tm[0]`, `LOGTNB` | 2, 9, 10 |
| `im[0]`, `logInb` | 8, 8 | `Im[0]`, `LOGINB` | 8, 8 |
| `imnb`, `imm[0]`, `logImnb` | 2, 10, 9 | `IMNB`, `IMm[0]`, `LOGIMNB` | 2, 10, 9 |
| `numEntriesFirstLocalHistories`, second, third | 256, 16, 16 | `NLOCAL`, `NSECLOCAL`, `NTLOCAL` | 256, 16, 16 |
| `logSizeUp` | 6 | `LOGSIZEUP` | 6 |
| `updateThresholdWidth`, `pUpdateThresholdWidth` | 12, 8 | `WIDTHRES`, `WIDTHRESP` | 12, 8 |
| `chooserConfWidth` | 7 | `CONFWIDTH` | 7 |

The storage matches, but one behaviour does not. gem5 masks each GEHL history with `(1 << length[i]) - 1`, and that `1` is a 32-bit `int` (`src/cpu/pred/statistical_corrector.cc:212, 229`). cbp2025 uses `1ULL << length[i]` (`third_party/cbp2025/cbp2016_tage_sc_l.h:1579, 1599`, in this repository).

- For `bwm[0]`, 40, the gem5 shift is undefined behaviour in C++. An x86 shift uses only the low 5 bits of its count, so the likely result is an 8-bit mask. Nothing here measured it.
- So do not assume that gem5's `bw` table 0 sees 40 bits of history, as the cbp2025 table does.
- In `gPredict` and `gUpdate`, any length of 32 or more is undefined, and 31 overflows the `int` too. An sR table or a GEHL length knob that uses these helpers must stay at 30 bits or less.

So the `predictorsize()` term table in `hosts/cbp2025/NOTES.md` describes this predictor's storage too, written in gem5's names. That table reproduces cbp2025's own function, including its double count of the loop predictor. Whether a gem5 plan keeps that quirk is the planner's call. Record the choice in `measured_by`.

**Every size is a Python Param**. The tables below list each one, where its clean value is set, and the C++ line that copies it. All `BranchPredictor.py` lines are in `src/cpu/pred/BranchPredictor.py`.

TAGE, class `TAGE_SC_L_TAGE_64KB` and its parents:

| Param | Set at `BranchPredictor.py` | Clean value | Sizes | Copied in C++ |
| --- | --- | --- | --- | --- |
| `logTagTableSize` | 516 | 10 | entries per tagged bank, log2 | `src/cpu/pred/tage_sc_l.hh:110` |
| `shortTagsTageFactor` | 517 | 10 | short-tag bank count | `src/cpu/pred/tage_sc_l.hh:111` |
| `longTagsTageFactor` | 518 | 20 | long-tag bank count | `src/cpu/pred/tage_sc_l.hh:112` |
| `shortTagsSize` | 445 | 8 | tag width, short banks | `src/cpu/pred/tage_sc_l.hh:109` |
| `longTagsSize` | 520 | 12 | tag width, long banks | `src/cpu/pred/tage_sc_l.hh:108` |
| `firstLongTagTable` | 522 | 13 | first table with long tags | `src/cpu/pred/tage_sc_l.hh:107` |
| `nHistoryTables` | 461 | 36 | logical tables, history lengths paired | `src/cpu/pred/tage_base.cc:54` |
| `minHist`, `maxHist` | 463, 464 | 6, 3000 | shortest and longest history | `src/cpu/pred/tage_base.cc:58-59` |
| `tagTableCounterBits` | 318 | 3 | tagged counter width | `src/cpu/pred/tage_base.cc:55` |
| `tagTableUBits` | 466 | 1 | useful-bit width | `src/cpu/pred/tage_base.cc:56` |
| `logTagTableSizes` | 468 | `[13]` | bimodal entries, log2 | `src/cpu/pred/tage_base.cc:62` |
| `logRatioBiModalHystEntries` | 312-316 | 2 | bimodal hysteresis sharing | `src/cpu/pred/tage_base.cc:53` |
| `pathHistBits` | 425 | 27 | path history width | `src/cpu/pred/tage_base.cc:60` |
| `numUseAltOnNa`, `useAltOnNaBits` | 424, 429 | 16, 5 | use-alt-on-NA counters | `src/cpu/pred/tage_base.cc:66-67` |
| `logUResetPeriod` | 427 | 10 | useful-bit reset period, log2 | `src/cpu/pred/tage_base.cc:64` |
| `maxNumAlloc` | 426 | 2 | entries allocated per mispredict | `src/cpu/pred/tage_base.cc:68` |

The short banks hold 10 × 2^10 entries with 8-bit tags, and the long banks hold 20 × 2^10 with 12-bit tags (`src/cpu/pred/tage_sc_l.cc:113-137`). The bimodal table is 2^13 prediction bits plus 2^11 hysteresis bits (`src/cpu/pred/tage_base.cc:137-140`).

Loop predictor, class `TAGE_SC_L_64KB_LoopPredictor` and its parents:

| Param | Set at `BranchPredictor.py` | Clean value | Sizes | Copied in C++ |
| --- | --- | --- | --- | --- |
| `logSizeLoopPred` | 710 | 5 | entries, log2 | `src/cpu/pred/loop_predictor.cc:59` |
| `logLoopTableAssoc` | 386 | 2 | ways, log2 | `src/cpu/pred/loop_predictor.cc:64` |
| `loopTableIterBits` | 605 | 10 | iteration counts, two per entry | `src/cpu/pred/loop_predictor.cc:63` |
| `loopTableTagBits` | 604 | 10 | tag width | `src/cpu/pred/loop_predictor.cc:62` |
| `loopTableConfidenceBits` | 603 | 4 | confidence width | `src/cpu/pred/loop_predictor.cc:61` |
| `loopTableAgeBits` | 602 | 4 | age width | `src/cpu/pred/loop_predictor.cc:60` |
| `useDirectionBit` | 608 | True | one direction bit per entry | `src/cpu/pred/loop_predictor.cc:71` |
| `withLoopBits` | 379 | 7 | the WITHLOOP counter | `src/cpu/pred/loop_predictor.cc:70` |

Statistical corrector, class `TAGE_SC_L_64KB_StatisticalCorrector` and its base `StatisticalCorrector`:

| Param | Set at `BranchPredictor.py` | Clean value | Sizes | Copied in C++ |
| --- | --- | --- | --- | --- |
| `logBias` | 753 | 8 | the three bias tables, log2 | `src/cpu/pred/statistical_corrector.cc:56` |
| `bwnb`, `bwm`, `logBwnb` | 755-757 | 3, `[40, 24, 10]`, 10 | global backward-branch GEHL | `src/cpu/pred/statistical_corrector.cc:60-62` |
| `pnb`, `pm`, `logPnb` | 722-726 | 3, `[25, 16, 9]`, 9 | path GEHL | `src/cpu/pred/tage_sc_l_64KB.cc:55-57` |
| `lnb`, `lm`, `logLnb` | 760-762 | 3, `[11, 6, 3]`, 10 | first local GEHL | `src/cpu/pred/statistical_corrector.cc:63-65` |
| `snb`, `sm`, `logSnb` | 728-732 | 3, `[16, 11, 6]`, 9 | second local GEHL | `src/cpu/pred/tage_sc_l_64KB.cc:58-60` |
| `tnb`, `tm`, `logTnb` | 734-738 | 2, `[9, 4]`, 10 | third local GEHL | `src/cpu/pred/tage_sc_l_64KB.cc:61-63` |
| `inb`, `im`, `logInb` | 645, 646, 765 | 1, `[8]`, 8 | IMLI GEHL | `src/cpu/pred/statistical_corrector.cc:66-68` |
| `imnb`, `imm`, `logImnb` | 740-742 | 2, `[10, 4]`, 9 | second IMLI GEHL | `src/cpu/pred/tage_sc_l_64KB.cc:64-66` |
| `numEntriesFirstLocalHistories` | 751 | 256 | first local history table | `src/cpu/pred/statistical_corrector.cc:59` |
| `numEntriesSecondLocalHistories`, `numEntriesThirdLocalHistories` | 744-749 | 16, 16 | second and third local history tables | `src/cpu/pred/tage_sc_l_64KB.cc:53-54` |
| `scCountersWidth` | 674 | 6 | every GEHL and bias counter | `src/cpu/pred/statistical_corrector.cc:73` |
| `extraWeightsWidth` | 670-672 | 6 | the component weights | `src/cpu/pred/statistical_corrector.cc:72` |
| `logSizeUp` | 654-656 | 6 | `pUpdateThreshold` entries, log2 | `src/cpu/pred/statistical_corrector.cc:57-58` |
| `updateThresholdWidth`, `pUpdateThresholdWidth` | 662-668 | 12, 8 | the threshold counters | `src/cpu/pred/statistical_corrector.cc:70-71` |
| `chooserConfWidth` | 658-660 | 7 | the two chooser counters | `src/cpu/pred/statistical_corrector.cc:69` |

Each weight vector has `2^(logSizeUp / 2)` entries (`src/cpu/pred/statistical_corrector.cc:58, 80, 157`). Each GEHL component allocates `2^log` entries per table, and its last two tables use one index bit less (`src/cpu/pred/statistical_corrector.cc:147-149`, `src/cpu/pred/tage_sc_l_64KB.cc:144-148`). That is the half-size table in the cbp2025 formulas.

**The C++ constants are behaviour, not sizes**. None of them sizes a table on its own.

| Constant | Value | Where |
| --- | --- | --- |
| `StatisticalCorrector::MaxOrdinalHistories` | 4, the local history table limit | `src/cpu/pred/statistical_corrector.hh:210` |
| initial `updateThreshold` | `35 << 3` | `src/cpu/pred/statistical_corrector.cc:86` |
| initial bias weights `wb` | 4 | `src/cpu/pred/statistical_corrector.cc:80` |
| initial 64KB GEHL weights `wp`, `ws`, `wt`, `wim` | 7, 7, 7, 0 | `src/cpu/pred/tage_sc_l_64KB.cc:68-71` |
| local history hash shifts | 2, 5, `logTnb` | `src/cpu/pred/tage_sc_l_64KB.cc:80-83` |
| IMLI history table | `1 << im[0]` entries, 256 | `src/cpu/pred/tage_sc_l_64KB.cc:85` |
| `thres` bonus per non-negative weight | 12 | `src/cpu/pred/tage_sc_l_64KB.cc:135-139` |

### How a host knob is wired

A `HOST_*` macro is a C macro. It can drive C++ only. The gate never edits the config, and stage 4 writes only `sr_params.h`. Python defaults live in `BranchPredictor.py`, and stage 4 does not touch it.

So a knob on a Param-sized structure goes through the C++ constructor that copies the Param. The initializer takes the macro instead. For example, `logBias(p.logBias)` at `src/cpu/pred/statistical_corrector.cc:56` becomes `logBias(HOST_LOGBIAS)`. The Python default then no longer matters for that field. At the default value the macro equals it, and G2 holds.

- For the plan's `observed` line, cite the Python declaration, because it holds the clean value. `file` is then `src/cpu/pred/BranchPredictor.py`, and `host_symbol` is the Param's name. The C++ line holds `p.logBias`, not the number.
- `plan_checks` compares `observed` with its whitespace collapsed (`_check_host_knobs` in `loop/plan_checks.py`). A declaration that spans lines, such as `logPnb` at lines 724-726, therefore works. Copy it whole.
- `TAGEBase`, `LoopPredictor` and `StatisticalCorrector` constructors also serve other predictors: TAGE, LTAGE, `TAGE_SC_L_8KB` and the MPP family. A macro wired there changes those classes too. Only `TAGE_SC_L_64KB` runs in this host, so the metrics see only it.
- A list Param such as `bwm` is a poor knob. Its length must equal its count Param (`src/cpu/pred/statistical_corrector.cc:143`).

Before you widen a range, read what else the Param feeds. These asserts are live, because `gem5.opt` keeps asserts (`src/SConscript:681-682`).

- `noSkip` has one entry per table plus one, 37 at the default (`src/cpu/pred/BranchPredictor.py:476-514`). A new `nHistoryTables` needs a new `noSkip` list. The TAGE also asserts both size vectors have `nHistoryTables + 1` entries (`src/cpu/pred/tage_base.cc:122-123`).
- `tagTableUBits` must be 1 or 2 (`src/cpu/pred/tage_base.cc:97`). `histBufferSize` must exceed three times `maxHist` (`src/cpu/pred/tage_base.cc:107`).
- `gIndex` shifts the history by `8 - i` and similar amounts (`src/cpu/pred/statistical_corrector.cc:193-202`). A GEHL table index above 8 makes a shift negative.
- A GEHL history length above 30 hits the 32-bit shift in the note under the size table (`src/cpu/pred/statistical_corrector.cc:212, 229`). The default `bwm[0]` of 40 already does.
- `logSizeUps` is `logSizeUp / 2` (`src/cpu/pred/statistical_corrector.cc:58`).
- The loop predictor's initial age of 7 needs `loopTableAgeBits` of at least 3 (`src/cpu/pred/loop_predictor.cc:80`, `src/cpu/pred/BranchPredictor.py:611`). Its tag and iteration widths cap at 16, and `logSizeLoopPred` must be at least `logLoopTableAssoc` (`src/cpu/pred/loop_predictor.cc:88-91`).
- The 64KB class sizes the third local history's hash shift from `logTnb` (`src/cpu/pred/tage_sc_l_64KB.cc:83`).

## Build

The gate builds with chia's `Gem5Node.build_gem5`. The command is `scons build/ARM/gem5.opt -j30` plus `constants.GEM5_SCONS_ARGS`. That constant holds two flags and no `NAME=value` setting. The gate's build sets no `CC`, no `CXX` and no `PYTHON_CONFIG`.

Your shell builds the same way. Type this, with no variables in front of it:

```sh
cd ~/gem5_port
scons build/ARM/gem5.opt -j30 --ignore-style --linker=gold
```

The binary lands at `build/ARM/gem5.opt`.

Five facts about this build matter for the port.

- gem5 v25.1 reads `CC`, `CXX`, `PYTHON_CONFIG` and `CCFLAGS_EXTRA` from the environment only (`site_scons/gem5_scons/defaults.py:46-103`). For a build, the SConstruct reads only `EXTRAS` from the command line (`SConstruct:874-880`). So `scons CC=...` does nothing.
- The gate's builds and your shell's builds run on the same node with `chia_env` active, and neither sets those variables. So both find the same `gcc` and the same `python3-config`, and every compile line matches. Your build leaves the tree ready for the gate's build, and the gate's build leaves it ready for yours.
- Do not set `CC`, `CXX`, `PYTHON_CONFIG` or `CCFLAGS_EXTRA` in your shell. A new value changes every compile line. Then scons recompiles all of gem5, and the next gate build recompiles all of it again. The one exception is a `compile_time_define` knob, where the gate itself sets `CCFLAGS_EXTRA` (see "The enable knob is an environment variable").
- `--ignore-style` skips gem5's interactive git-hook prompt (`SConstruct:117-118`). `--linker=gold` picks the gold linker (`SConstruct:111-122`).
- `gem5.opt` is `-O3 -g` with asserts and `DPRINTF` tracing kept (`src/SConscript:681-682, 696-704`). The pristine binary loads the system libpython at run time.

Timing:

- A first build from scratch took 670 seconds, about 11 minutes, on the 32-vCPU node (2026-09-23).
- A fresh copy of the tree reuses most of the copied `build/`. In three gate smoke runs, the copy's first build plus about 90 s of gem5 runs took 336 to 376 s in all. Nobody timed that build on its own. No compiler cache is in the loop.
- An incremental build after an edit to one `src/cpu/pred` `.cc` file: TODO(measured).
- An edit to a header costs more. `statistical_corrector.hh` reaches every TAGE-SC-L and MPP-TAGE file. `commit.hh` reaches every O3 file through `src/cpu/o3/cpu.hh`. `conditional.hh` and `bpred_unit.hh` reach O3, Minor and the simple CPUs. Each case is TODO(measured).

The agent's shell allows 1200 seconds per command. A full build took 670 seconds, so even a build from scratch fits in one command. If a build still runs out of time, run the same command again. Do not leave a build running in the background. The gate builds the same tree after your turn, and two scons runs in one tree corrupt it.

## Run and metrics

```sh
python3 ~/p2p_gem5/run_workload.py --gem5 ~/gem5_port/build/ARM/gem5.opt WORKLOAD
```

The full interface (`hosts/gem5/run/run_workload.py:2-37, 237-266`):

```text
python3 run_workload.py [--gem5 BIN] [--run-dir DIR] [--outdir DIR]
    [--maxinsts N] [--cond-bp NAME] [--cpu o3|atomic] [--timeout S] WORKLOAD

--gem5      default $P2P_GEM5_BIN; a relative path is made absolute from the shell's cwd
--run-dir   default $P2P_GEM5_RUN_DIR, else the script's own directory (~/p2p_gem5)
--outdir    default a new directory under <run-dir>/runs/
--maxinsts  default the manifest's max_insts; 0 removes the limit
--cond-bp   default se_o3.py's TAGE_SC_L_64KB
--cpu       default o3; atomic has no branch predictor and derives ipc only
--timeout   default none
```

It prints these lines, in order:

```text
P2P_WORKLOAD <name>
P2P_RUN {...}                  outdir, gem5 exit status, guest exit, wall time, full command
P2P_STAT <logical> <value>     each stat p2p_metrics.STATS_KEYS found
P2P_METRIC <name> <value>      full repr precision
P2P_STATUS ok                  or: P2P_STATUS failed <reason>
```

It exits 0 only for a run where gem5 exited 0, the guest exited 0 or `--maxinsts` stopped it, and every metric derived. The adapter ignores the `P2P_METRIC` lines of any output with a failed `P2P_STATUS` line (`parse_metrics` in `hosts/gem5/adapter.py`).

Three traps in using it:

- A test plan command names no `--gem5`, `--run-dir`, `--maxinsts`, `--cond-bp` or `--cpu`. The gate's shell sets `P2P_GEM5_BIN` to the tree's binary for each state, and `P2P_GEM5_RUN_DIR` to the run dir (`Gem5Executor.shell_env` in `hosts/gem5/adapter.py`). A fixed `--gem5 ~/gem5/...` runs the pristine binary in both states. Any other override changes the run, and it no longer matches the baseline.
- The planner's shell has no `P2P_GEM5_BIN`. To record a clean-tree result there, prefix the same command:

```sh
P2P_GEM5_BIN=$HOME/gem5/build/ARM/gem5.opt python3 ~/p2p_gem5/run_workload.py WORKLOAD
```

- A command that a test plan names also runs in the agents' shells, which stop at 1200 seconds. The planner records its clean-tree result there. Use the smoke list for such commands. A smoke workload took 14 to 31 seconds on the clean tree. The perf list belongs to `run: {"mode": "host_adapter"}`, which fans out one gem5 per workload.

Measured wall times on the clean tree, 2026-09-23:

| Run | Wall time |
| --- | --- |
| one smoke workload, in the cluster smoke's fan-out of all 28 | 14 to 31 s |
| one perf workload, in the cluster smoke's fan-out of all 28 | 136 to 396 s |
| the cluster smoke's fan-out of all 28 workloads, start to end | 398 s |
| one smoke workload, in the baseline recording of all 28 | 12 to 34 s |
| one perf workload, in the baseline recording of all 28 | 146 to 387 s |
| one perf workload, in a fan-out of the 8 in `gem5-perf.list`, measured while a gem5 build shared the node | 221 to 521 s |

The slowest workload each time was `gapbs_tc`. A gem5 build ran on the node during the 8-run fan-out (`runs/2026-09-23-gem5/README.md`). Each of those 8 workloads took 1.3 to 1.7 times longer there than in the cluster smoke. So a busy node slows every run, and a limit needs room above the idle figures. Each of the 8 gave the same instruction and cycle counts in both fan-outs.

The gate gives an entry 900 seconds unless the entry sets `timeout_seconds` (`DEFAULT_TIMEOUT_S` and `run_test_plan` in `loop/plan_runner.py`). On this host, only shell runs use that value as it is. Those are the `correctness` commands and a `run` that names a `command_template` (`Gem5Executor.shell` in `hosts/gem5/adapter.py`). The adapter raises two other limits to a fixed floor.

- A fan-out, `run: {"mode": "host_adapter"}`, gives each gem5 run at least `GEM5_RUN_TIMEOUT_S`, 3600 seconds, whatever the entry says (`Gem5Executor.run_traces`).
- A build gets at least `GEM5_BUILD_TIMEOUT_S`, 5400 seconds (`Gem5Executor.build`).

So a `timeout_seconds` below 3600 on a `smoke` or `performance` entry changes nothing. Only a larger value has an effect. A hung port holds a performance wave for up to an hour. The feature-on and feature-off waves together can hold one gate attempt for two hours.

For an `existing_regression` entry, this host's suite is run_workload.py over the smoke list. A pass condition can match its `P2P_STATUS ok` line and its exit code 0. gem5's own `tests/` tree is not wired into this loop, and nothing here measured it.

To trace a run, copy the command from the `P2P_RUN` line. Add `--debug-flags=TageSCL,Branch` before `--outdir`. The predictor's flags are listed at `src/cpu/pred/SConscript:90-97`.

### The metrics

The run scripts report three names (`hosts/gem5/run/p2p_metrics.py:126-128`). A test plan's `metric_keys` must use exactly these:

| Name | Formula | Better |
| --- | --- | --- |
| `cond_mpki` | 1000 × (`system.cpu.branchPred.mispredicted_0::DirectCond` + `mispredicted_0::IndirectCond`) / committed instructions | decrease |
| `branch_mpki` | 1000 × `system.cpu.branchPred.mispredicted_0::total` / committed instructions | decrease |
| `ipc` | committed instructions / `system.cpu.numCycles` | increase |

Committed instructions are `system.cpu.commitStats0.numInsts`. It counts one per committed macro-instruction, NOPs included (`src/cpu/o3/commit.cc:1353-1358`). `hosts/gem5/run/p2p_metrics.py:50-124` cites the gem5 source of each stat name, and `derive` at lines 149-174 holds the formulas.

`simInsts` is a different count, and the metrics use it only as a fallback. The fallback applies to a stats.txt with no `commitStats0` row.

- `simInsts` and `commitStats0.numInstsNotNOP` leave out NOPs and instruction prefetches. Commit calls `instDone` only for other instructions (`src/cpu/o3/commit.cc:1368-1372`, `src/cpu/o3/cpu.cc:1159-1165`).
- On `gapbs_bfs_s`, `numInsts` is 2,509,944, and `simInsts` is 2,509,105.
- `--maxinsts` counts the number without NOPs (`src/cpu/o3/cpu.cc:1165`). So a capped run shows a few more instructions in the metrics than the limit names.

`cond_mpki` counts committed conditional branches that gem5 mispredicted, per 1000 committed instructions. `branch_mpki` counts committed mispredicted branches of every type. It adds calls, returns, indirect jumps and unconditional branches whose target the BTB missed. The two differ. On `gapbs_bfs_s`, `DirectCond` is 34,742 and the total is 35,711, over 2,509,944 instructions. So `cond_mpki` is 13.84 and `branch_mpki` is 14.23. The gap is larger where many mispredictions are not conditional: 0.72 against 2.19 on `lua_fannkuch`, and 2.95 against 5.27 on `sqlite`. `IndirectCond` is 0 on AArch64, and gem5 prints it anyway.

Do not use `system.cpu.branchPred.condIncorrect` in a pass condition or a plan. gem5 names it "conditional branches incorrect", and it is not. It counts every committed mispredicted branch of every type (`src/cpu/pred/bpred_unit.cc:359-370, 521`), so it equals `mispredicted_0::total`. The first cluster run took `cond_mpki` from it, and `cond_mpki` came out equal to `branch_mpki` on all 28 workloads.

The conditional rows print two percentage columns after the value, for example `mispredicted_0::DirectCond 34742 97.29% 99.12%`. The run scripts' parser reads such a row (`hosts/gem5/run/p2p_metrics.py:235-248`). chia's `Gem5Node.parse_gem5_stats` skips it, so read these rows through the run scripts, never through chia's parser.

Both metrics count committed branches only, never wrong-path ones. sR changes only conditional directions. So `cond_mpki` shows sR's effect most directly. `branch_mpki` also holds the other branch types, which sR does not predict.

`cond_mpki` still has a small floor that no direction predictor can remove. `mispredicted_0::DirectCond` also counts taken conditional branches that missed in the BTB.

- On a BTB miss the front end falls through, whatever the direction predictor said (`src/cpu/pred/bpred_unit.cc:180-188, 286-293`).
- At commit, gem5 files a misprediction of a taken branch with no BTB hit under `mispredictDueToBTBMiss`. It files every other one under `mispredictDueToPredictor` (`src/cpu/pred/bpred_unit.cc:359-367`).
- On `gapbs_bfs_s` the split is 660 and 34,082, out of 34,742.

So a G5 expectation for `cond_mpki` must leave room for that floor. Neither row is in `STATS_KEYS`. For a diagnosis, read `mispredictDueToPredictor_0::DirectCond` from the `stats.txt` in the run's outdir. Changing the metric to that row needs a new baseline recording.

Across several workloads each metric is an arithmetic mean, the cbp2025 convention (`aggregate` in `hosts/gem5/run/p2p_metrics.py`). Across one workload it is that workload's own value. So a single run_workload.py command and a fan-out over a list produce the same key names.

### Determinism, and why `rel_tol` is 0

The same binary on the same workload prints the same numbers. Two fan-outs of the 8 perf workloads on 2026-09-23 gave the same instruction and cycle counts for each one. se_o3.py fixes everything the guest sees.

- The guest's argv, environment, working directory and stdio are fixed by the manifest and se_o3.py (`hosts/gem5/run/se_o3.py:18-50`).
- The guest's stack starts at a fixed base, so a changed environment string moves every stack address (`src/arch/arm/process.cc:96, 355-359, 425-432`, cited at `hosts/gem5/run/se_o3.py:22-27`).
- Every gem5 `Random` object is seeded from the fixed global seed 5489 (`src/base/random.hh:68-95`, `src/base/random.cc:79`).
- A guest file open reaches the host's files, and `/proc/self` holds host state. No current workload opens a `/proc` path. "The enable knob is an environment variable" gives the admission rule for new workloads.

A port can still break determinism in three ways.

- A field read before any write. Initialize everything in `BranchInfo` and in sR's tables.
- Behaviour that depends on pointer values or on `std::unordered_map` iteration order. The host OS randomizes addresses between runs.
- Extra draws from an existing generator on the off path. TAGE, TAGE-SC-L's TAGE and the loop predictor each hold their own `rng` (`src/cpu/pred/tage.hh:82`, `src/cpu/pred/tage_sc_l.hh:86`, `src/cpu/pred/loop_predictor.hh:74`). `TAGE_SC_L::update` draws from the first one for every committed branch (`src/cpu/pred/tage_sc_l.cc:487`). A new `Random::genRandom()` object for sR does not disturb them, because each object keeps its own state.

One trap in how a test plan uses the baseline. A `feature_off_baseline` entry is `feature_state: "off"`. An entry with `feature_state` `"on"` or `"both"` and a `metrics_equal_baseline` condition demands that the feature changes nothing. The `performance` entry demands the opposite, and no port satisfies both. A feature-on regression needs a pass condition about whether the host still works. `P2P_STATUS ok` or an exit code of 0 does that.

## Workloads

The workloads are free, redistributable programs with many branches. `scripts/build_gem5_workloads.sh` builds them on the head as static aarch64 Linux binaries and checks each one under `qemu-aarch64-static`. The adapter installs them on the node.

- The manifest is `~/p2p_gem5/workloads.json`, a copy of `hosts/gem5/workloads.json`. Each entry holds `binary`, `args`, `cwd`, `max_insts`, `approx_insts`, `suite`, `description`, `license` and `source`.
- The binaries and inputs sit in `~/p2p_gem5/workloads/bin/` and `~/p2p_gem5/workloads/data/`. Paths in the manifest are relative to `~/p2p_gem5/workloads/`. An entry with a null `cwd` runs in its binary's directory (`hosts/gem5/run/se_o3.py:346`).
- The manifest holds 28 entries: 14 perf-size workloads and a smoke-size twin of each, named with `_s`. The programs are GAPBS v1.5 (bfs, cc, pr, sssp, bc, tc), bzip2 1.0.8, zstd 1.5.7, Lua 5.4.9 and SQLite 3.53.4. The comment in `experiments/gem5-all.list` lists them.
- Every workload gives the same result on every run, uses no network, reads no file outside its own data directory, and opens no `/proc` path. Each checks its own result and exits 1 on a mismatch, by its list comments. A guest exit code other than 0 fails the run.
- Every `max_insts` is null, so each workload runs to its end. `approx_insts` holds the instruction count under qemu. gem5's committed count on the O3 CPU sits within 1 percent of it for every workload.
- On gem5 a smoke workload runs 2.1 to 6.3 million instructions, and a perf workload 33.7 to 65.5 million.
- gem5's O3 CPU ran 97,000 to 323,000 instructions per second on this node. The perf sizes ran at 165,000 to 323,000. The smoke sizes ran at 97,000 to 261,000, and each wall time includes gem5's own start-up.

Repository workload lists, for a `trace_list` field. Paths are relative to the repository root. Each line names one workload, and `#` starts a comment.

| List | Workloads | For |
| --- | --- | --- |
| `experiments/gem5-smoke.list` | `gapbs_bfs_s`, `sqlite_s` | G4 `smoke`, and a cheap G2 workload. It is also the default list of `--stage baseline --host gem5`. |
| `experiments/gem5-perf.list` | `gapbs_bfs`, `gapbs_sssp`, `gapbs_tc`, `bzip2`, `zstd`, `lua_fannkuch`, `lua_word_freq`, `sqlite` | G5 `performance` |
| `experiments/gem5-all.list` | all 28 | sizing and spot checks, not the gate |

Each list starts with a comment that says why it holds what it holds. Use `gem5-perf.list` for G5 unless you have a reason not to. The gate runs a performance list twice per attempt, feature-on first and then feature-off, one after the other (`_run_performance` in `loop/plan_runner.py`). Each state is one wave of 8 runs on the node's 30 slots, and a wave lasts as long as its slowest run. That is `gapbs_tc`. It took 387 to 396 seconds on the clean tree, and 521 seconds while a gem5 build shared the node. So the performance entry costs about 13 minutes per attempt on a quiet node, and about 18 minutes on a busy one, before the build. The loop allows six attempts.

## The recorded baseline, and what G2 compares against

The recorded baseline is `hosts/gem5/baselines/iso-64KiB.json`. The lead recorded it on 2026-09-23 over `experiments/gem5-all.list`, so its `per_trace` holds all 28 workloads. Any manifest name therefore resolves as `/per_trace/<name>`. A smoke workload is still the cheap choice for a G2 entry, at 12 to 34 seconds a run.

No other gem5 baseline file exists. So stages 2 and 3 on gem5 must run with `--budget iso-64KiB`. The driver's default budget is `iso-192KiB`, and with it the driver finds no gem5 baseline. Stage 2 then skips its check that each `/per_trace/` pointer resolves. Stage 3 stops with `no recorded baseline for gem5/iso-192KiB`.

`--stage baseline --host gem5` restores and builds `~/gem5`. Then it runs the list, `experiments/gem5-smoke.list` by default, with no enable variable set at all. It writes `hosts/gem5/baselines/<budget>.json`.

That document holds the suite means at the top level. It also holds these fields (`record_baseline` in `hosts/gem5/adapter.py`):

- `per_trace`, keyed by workload name, one metrics map each
- `per_trace_stats`, the raw logical stats and the wall time of each run
- `trace_list`, `host_revision`, `isa`, `variant`, `scons_args`, `scons_env`
- `workload_fingerprints`, a hash of each workload's manifest entry, binary, data and the run scripts

A later recording of the same revision keeps earlier `per_trace` entries, as long as each fingerprint still matches. A run that misses a workload leaves the file alone.

Every gate attempt checks the baseline before it measures anything (`check_baseline_current` in `hosts/gem5/adapter.py`).

- The baseline's `host_revision` must equal the commit of `~/gem5`.
- Each workload that the test plan compares against must still match its recorded fingerprint. A `/per_trace/<name>` pointer names one workload. Any other pointer names every workload in the recording.

If either check fails, the stage stops with an error that asks for a new recording. That error never reaches you as a G2 failure. So when G2 reports different numbers, the cause is the port, not a stale baseline.

A `feature_off_baseline` entry runs one workload through the shell, so it points at one `per_trace` entry:

```json
"kind": "feature_off_baseline",
"command": "python3 ~/p2p_gem5/run_workload.py gapbs_bfs_s",
"feature_state": "off",
"pass_condition": {
  "kind": "metrics_equal_baseline",
  "baseline_pointer": "/per_trace/gapbs_bfs_s",
  "rel_tol": 0
}
```

A workload name holds no `/`. A name with a `/` or a `~` in it needs the RFC 6901 escapes `~1` and `~0`.

The baseline comes from the adapter's fan-out, and the G2 entry comes from run_workload.py. Both build the se_o3.py arguments from the same manifest entry and the same run dir. The two argument lists match string for string (`resolve` in `hosts/gem5/adapter.py`, `hosts/gem5/run/run_workload.py:98-137`). Both parse stats.txt with the same parser, `parse_stats_text` and `select` in `hosts/gem5/run/p2p_metrics.py` (lines 3-27 say why). So the same binary gives the same numbers on both paths. Any difference at all is the port leaking into the off path.

## Where your work lives

| Path | Constant | What it is |
| --- | --- | --- |
| `~/gem5` | `GEM5_ROOT` | The pristine checkout. Stage 2's shell runs here. |
| `~/gem5_port` | `GEM5_PORT_ROOT` | Stage 3's copy. The integration agent edits and builds here, and the gate builds and runs here. |
| `~/gem5_dse` | `GEM5_DSE_ROOT` | Stage 4's copy, unused until stage 4 supports gem5. |
| `~/p2p_gem5` | `GEM5_RUN_DIR` | The run scripts, the manifest, the workloads, and `runs/` with one outdir per run. |
| `~/gem5_smoke` | none | The lead's gate smoke copy (`loop/tests/gem5_gate_smoke.py`). No stage uses it, and it is not yours. |

The adapter restores `~/gem5` before and after stage 2 with `git reset --hard` and `git clean -fdx -e /build/` (`restore_checkout` in `hosts/gem5/adapter.py`). The restore keeps `build/`, so the next build of `~/gem5` is incremental and not a 670-second build from scratch. So do not build `~/gem5` after an edit. The edited binary outlives the edit until the next build.

Stage 3's copy includes `.git` and `build/` (`materialize_port_tree` in `hosts/gem5/adapter.py`). Its first build reuses most of the copied `build/`, and it finished in under about 5 minutes in every gate smoke run. Later builds in the same copy are incremental. By default each integration run starts from a fresh copy (`GEM5_PORT_FRESH`).

All five directories sit on one node, the one that advertises `gem5_host`. That node is one c2d-standard-32 with 30 run slots. Your shell runs there, with a limit of 1200 seconds per command (`GEM5_BASH_TOOL_TIMEOUT_S`). Every build and every gem5 run happens there too. A gem5 binary never leaves the node, and each run names it by path.
