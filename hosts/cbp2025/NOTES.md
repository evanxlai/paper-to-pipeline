# CBP2025 integration notes for the sR port

Every fact below was read from the CBP2025 kit at commit `607496629452740887dc1b90a46834cc90dda1e0` on 2026-09-22. The kit is at github.com/ramisheikh/cbp2025. The timing numbers come from a real `./cbp` run on this cluster. The planning agent and the integration agent both get this file inside their prompt. Run `git rev-parse HEAD` yourself before you trust any of it.

This is the host the RUNLTS paper itself was written against. The interfaces sR needs are real here, not approximated. That is why it is the first host in this repository with a working gate.

## What you can edit, and what you cannot

| File | Status |
| --- | --- |
| `my_cond_branch_predictor.h` | Yours. Holds `SampleCondPredictor`, the contestant predictor class, and the single `static SampleCondPredictor cond_predictor_impl;` at the bottom. |
| `my_cond_branch_predictor.cc` | Yours. Ships empty at 0 bytes. The build compiles it. Put out-of-line definitions here for a header that grows too large. |
| `cond_branch_predictor_interface.cc` | Yours to edit, inside fixed signatures. Holds the bodies of the nine entry points. |
| `cbp2016_tage_sc_l.h` | Yours, behind the enable knob only. The contest rules allow edits, and this is where the paper's sR belongs. See "Where sR joins the statistical corrector". |
| `cbp.h`, `lib/**` | Fixed. These are the nine entry-point signatures and the simulator. An edit here makes the result meaningless. |
| `sr_params.h` | Does not exist yet. The port creates it. See "Parameters" below. |

## The nine entry points

`cbp.h` declares them. `cond_branch_predictor_interface.cc` defines them. `lib/uarchsim.cc` calls them.

| Entry point | Called for | Body today |
| --- | --- | --- |
| `beginCondDirPredictor()` | once, before simulation | `cbp2016_tage_sc_l.setup(); cond_predictor_impl.setup();` |
| `notify_instr_fetch(seq_no, piece, pc, fetch_cycle)` | every instruction | empty |
| `get_cond_dir_prediction(seq_no, piece, pc, pred_cycle)` | conditional branches | takes `cbp2016_tage_sc_l.predict(...)`, passes it into `cond_predictor_impl.predict(..., tage_sc_l_pred)`, returns the contestant answer |
| `spec_update(seq_no, piece, pc, inst_class, resolve_dir, pred_dir, next_pc)` | every branch, right after its prediction | updates TAGE history, plus `cond_predictor_impl.history_update(...)` for conditional branches |
| `notify_instr_decode(seq_no, piece, pc, DecodeInfo, decode_cycle)` | every instruction, at its decode cycle | empty |
| `notify_agen_complete(seq_no, piece, pc, DecodeInfo, mem_va, mem_sz, agen_cycle)` | loads and stores | empty |
| `notify_instr_execute_resolve(seq_no, piece, pc, pred_dir, ExecuteInfo, execute_cycle)` | every instruction, at its execute cycle | updates both predictors, for conditional branches only |
| `notify_instr_commit(seq_no, piece, pc, pred_dir, ExecuteInfo, commit_cycle)` | every instruction | empty |
| `endCondDirPredictor()` | once, at the end | calls `terminate()` on both |

The three empty ones are where sR lives. `notify_instr_decode` and `notify_instr_execute_resolve` fire for every instruction, not only for branches. `uarchsim_t::eval_decode` and `uarchsim_t::eval_exec` walk the whole window. So sR sees every register write without any change to a fixed signature.

## Where sR joins the statistical corrector

Read this before you choose a structure. An earlier run of this loop did not have
it. That run treated `cbp2016_tage_sc_l.h` as untouchable and ported sR as a
standalone predictor. Its sR overrode the TAGE-SC-L answer on every
disagreement. The port built, matched the baseline with the knob off, and
passed every unit test. It also made CycWPPKI 43 percent worse. The
integration agent escalated, correctly: nothing told it how confident its
own sum had to be before it overrode a strong predictor.

The answer is that sR is not an override. In the paper it is one term in the
statistical corrector's sum, and this host has that sum.

`cbp2016_tage_sc_l.h` around line 1044 builds `LSUM` out of one contribution
per component:

```cpp
LSUM = 0;
LSUM += (2 * ctr + 1);                       // the three bias tables
LSUM += Gpredict(..., GGEHL, ...);           // sG
LSUM += Gpredict(..., PGEHL, ...);           // sP
LSUM += Gpredict(..., LGEHL, ...);           // sL
LSUM += Gpredict(..., SGEHL, ...);           // sS
LSUM += Gpredict(..., TGEHL, ...);           // sT
LSUM += Gpredict(..., IMGEHL, ...);          // sIM
LSUM += Gpredict(..., IGEHL, ...);           // sI
bool SCPRED = (LSUM >= 0);
```

sR is one more `LSUM += ...` line, added before `SCPRED` is computed. That
is the whole hook.

Three things follow, and each one answers a question the spec leaves open.

- **The confidence threshold already exists.** The lines just below compute
  `THRES` from `updatethreshold`, `Pupdatethreshold[INDUPD]` and the
  per-component weight signs. The chooser then compares `abs(LSUM)` against
  `THRES / 4` and `THRES / 2` to decide whether the SC overrides TAGE at
  all. Feed sR into `LSUM` and sR inherits that machinery. Do not invent a
  second threshold.
- **The update site is the matching one.** Around line 1288 the SC updates
  only under its own conditions, and each component's `Gupdate` call sits
  there. sR's weight update belongs in that same block, under the same
  conditions, so it learns on the branches the SC learns on.
- **That update function does not know which instruction it is.** There are
  two overloads named `update`. The outer one takes `seq_no` and `piece`,
  looks up the checkpointed history, and calls the inner one with the
  history alone. The inner one is where the SC update block lives, and it
  never sees the instruction id. The kit's own `pred_time_histories` keys
  prediction-time state by `get_unique_inst_id(seq_no, piece)`. A port that
  does the same has to thread both arguments through the outer call too. Adding a defaulted parameter to the inner overload and
  forgetting the call site compiles, runs, and trains nothing: every lookup
  misses, the weights stay at their initial values, and G5 reports the
  metric moving by exactly 0.0000.
- **`THRES` adapts.** `updatethreshold` moves as the SC is right or wrong, so
  an sR term that adds noise is throttled rather than trusted.

Every one of those edits sits behind the enable knob. With the knob off,
`LSUM` must be built from today's components, in today's order. `THRES` must
come out the same. G2 measures that claim against the recorded baseline at
`rel_tol` 0. A stray `+= 0` that changes nothing is therefore fine, and a
reordered sum is not.

## The other hook: the contestant predictor class

`SampleCondPredictor::predict` already takes the TAGE-SC-L prediction and returns the final direction:

```cpp
bool predict(uint64_t seq_no, uint8_t piece, uint64_t PC, const bool tage_pred)
{
    active_hist.tage_pred = tage_pred;
    pred_time_histories.emplace(get_unique_inst_id(seq_no, piece), active_hist);
    return predict_using_given_hist(seq_no, piece, PC, active_hist, true);
}
```

`predict_using_given_hist` returns `hist_to_use.tage_pred` unchanged. That one line is the whole contestant predictor today. It is a pass-through.

This class is the right home for sR's own state: the register status table, the digest generator, the usefulness tables and the weight tables. It is also where the register-tracking hooks land, because it is the object the interface file already talks to. What it is not is the place to decide the final direction. Leave that to the statistical corrector, for the reason the section above gives.

The feature-off path is then the line that is already there. That is what makes the G2 claim true rather than merely plausible. G2 says the knob-off path is bit-identical to the recorded baseline.

`SampleCondPredictor::update(...)` is the resolve-time hook and `history_update(...)` is the history hook. Both are wired already and both do no real work.

## Register values: what the host gives you

This is the interface the paper needs. Most hosts do not have it. The structures live in `lib/sim_common_structs.h`.

```cpp
struct DecodeInfo {
    InstClass insn_class;
    std::vector<uint64_t> src_reg_info;   // source logical register IDs
    std::optional<uint64_t> dst_reg_info; // destination logical register ID
};

struct ExecuteInfo {
    DecodeInfo dec_info;
    std::optional<bool> taken;
    uint64_t next_pc;
    std::optional<uint64_t> taken_target, mem_va, mem_sz;
    std::optional<uint64_t> dst_reg_value;   // the 64-bit result value
};
```

`lib/uarchsim.cc:populate_execute_info` fills `dst_reg_value` from the trace for every instruction with a valid destination. The result value is real trace data, not a model. `populate_decode_info` fills `src_reg_info` and `dst_reg_info` the same way.

Register numbering comes from `lib/uarchsim.h`:

```
#define RFSIZE  66   // integer: r0-r31.  fp/simd: r32-r63.  flags: r64.
#define RFFLAGS 64
```

The spec talks about 65 logical registers R0 to R64. That is this exact file. One consequence matters for the port. The operand type that the sR digest function needs follows from the register index alone. Index below 32 means integer. Index 32 to 63 means FP or SIMD. Index 64 means flags. The host does not separate FP16 from FP32 from FP64. A port therefore picks one FP digest rule and records that deviation.

## Interfaces the host does not have

1. No ROB tag. There is no rename stage and no ROB. `seq_no` is a per-instruction id that only increases. `get_unique_inst_id(seq_no, piece)` is the kit's own way to make it unique. Use that wherever the spec says "ROB tag". The `pred_time_histories` map in `my_cond_branch_predictor.h` is the checkpoint pattern the kit intends. The kit README states that checkpoint state does not count against the predictor budget.
2. No pipeline squash. The trace is a stream of committed instructions. There is no wrong-path execution and no flush signal. `notify_instr_execute_resolve` fires once per instruction and never unwinds. The spec's squash-recovery algorithm has nothing to hook. It maps to a no-op. That is a `fallback` resolution, not an `exact` one. Say so in the plan, and say what it costs.
3. No decode-count pulse under that name. `notify_instr_decode` fires once per decoded instruction. That is the pulse.
4. Cycle order, not program order. Decode, execute and commit each fire at their own cycle. A register value can therefore arrive after a later branch was already predicted. That is a real machine's behaviour and the reason sR exists. Do not try to repair it by reading values early.

## The enable knob is an environment variable

The kit gives a predictor no command line of its own. `argv` belongs to the simulator. So `getenv` is the only way to change behaviour without a rebuild. Bind the enable knob as `runtime_env`. Read it once in `beginCondDirPredictor()` or in `setup()`, into a member that the predict path tests:

```cpp
void setup() {
    const char* e = getenv("SR_SR_ENABLE");
    sr_enabled = (e != nullptr && e[0] == '1');
}
```

The gate sets three aliases to the same value on every build and every run. Any of the three works. They are the plan's own `feature_enable.name`, that name upper-cased, and its `macro`. The spec names the parameter `sr_enable`, so the three aliases are `sr_enable`, `SR_ENABLE` and `SR_SR_ENABLE`.

Two consequences belong in the plan.

- Off must be the default. A binary that runs with none of those three variables set must behave exactly like the baseline. A `getenv` result of `nullptr` gives `false`, and that is what delivers the default. It is also why the test above reads `== '1'` and not `!= '0'`.
- A `compile_time_define` binding costs more than it looks. The gate does pass the same three variables into `make`, but this Makefile does not forward them. It sets `CPPFLAGS` and then never uses it. It compiles with `$(CC) $(FLAGS)`, and `FLAGS` is a plain `=` assignment that make gives priority over the environment. So a compile-time knob needs a Makefile edit as well, and that edit is a hook point the plan must name. It also costs a full rebuild on every knob flip, about 20 seconds each. Prefer `runtime_env`.

## Parameters live in `sr_params.h`

Stage 4 mutates one generated header and nothing else. It writes `sr_params.h`. That file holds one `#define SR_<PARAMETER_NAME_UPPER_CASED> <value>` per spec parameter. See `loop/dse.py:params_header_from_spec`. Four rules follow.

- The port must `#include "sr_params.h"` from `my_cond_branch_predictor.h`.
- Every tunable must come from an `SR_*` macro. A hard-coded value is a value the search can never move.
- The port must create `sr_params.h` itself, with the spec defaults. The file is not in the checkout, and the build has to work long before stage 4 runs.
- An `enum` parameter arrives as an integer index into its choice list, not as prose. The mapping sits in a trailing comment. Implement it as an `#if` and `#elif` ladder, or as a `switch`.

The enable knob is the one exception to "everything through the header". It is also `SR_SR_ENABLE` in the header. The gate flips it through the environment, so let the environment win at run time.

## Build

```sh
make clean && make      # ~20 s on this cluster's n2-standard-2 workers
```

The build is `g++ -std=c++17 -O3`. It links `lib/libcbp.a` and `-lz`. Three facts about this Makefile matter for the port.

- The `DEPS` line names `cbp.h cond_branch_predictor_interface.h my_cond_branch_predictor.h`. `cond_branch_predictor_interface.h` does not exist, and make does not mind.
- A new header of your own is not in that list. A plain `make` can therefore miss an edit to it. Always run `make clean && make`. That is what the gate does.
- Neither `CPPFLAGS` nor `FLAGS` picks anything up from the environment. `CPPFLAGS` is assigned and then never used. The compile rule reads `$(CC) $(FLAGS)`, and `FLAGS` is a plain `=` assignment. An extra `-D` therefore has to be written into the Makefile.

## Run and metrics

```sh
./cbp <trace.gz>              # single-threaded, one process per trace
./cbp -E 1000000 <trace.gz>   # periodic stats every 1M instructions
```

Output ends with four `DIRECT CONDITIONAL BRANCH PREDICTION MEASUREMENTS` tables: Last 10M, Last 25M, 50 Perc, and Full Simulation. The contest scores the "50 Perc instructions" row. That row covers the second half of the trace. The first half is warmup. The columns are:

```
 Instr  Cycles  IPC  NumBr  MispBr  BrPerCyc  MispBrPerCyc  MR  MPKI  CycWP  CycWPAvg  CycWPPKI
```

The loop's stats adapter reports three names. A test plan `metric_keys` list must use exactly these three:

| name | column | better |
| --- | --- | --- |
| `brmispki_50perc_amean` | MPKI | decrease |
| `cycwppki_50perc_amean` | CycWPPKI | decrease |
| `ipc_50perc_amean` | IPC | increase |

Across several traces these are arithmetic means, which matches `scripts/trace_exec_training_list.py`. Across one trace they are that trace's own values. So a single `./cbp` correctness command and a 60-trace sweep produce the same key names.

The paper's headline claim is about CycWpPKI. The checkout also holds `reference_results_training_set.csv`, the per-trace baseline numbers the contest published.

One trap in how a test plan uses those numbers. An `existing_regression`
entry whose `matches_clean_tree` pattern is a measurement row is a demand
that the run reproduces the clean tree exactly. Give that entry
`feature_state: "off"`. With `"on"` or `"both"` it demands that the feature
changes nothing. The `performance` entry demands the opposite, and no port
satisfies both. A regression meant to run feature-on needs a pass condition
about whether the host still works. An exit code or a test-suite summary
line does that. Its measurement row does not.

## Workloads

Traces are not in the checkout. Two kinds are reachable.

- In the checkout: `sample_traces/int/sample_int_trace.gz` and `sample_traces/fp/sample_fp_trace.gz`. Each is about 1M instructions and takes a few seconds. These suit a correctness command you run from the shell. On the clean tree at this revision the int one gives `MPKI 0.2647`, `CycWPPKI 34.3978` and `IPC 2.9470`.
- On the trace nodes: the 105-trace CBP2025 training set under `$P2P_TRACE_DIR`, which is `~/traces/cbp2025`. The layout is `<workload>/<name>_trace.gz`. A test plan reaches these only through `run: {"mode": "host_adapter"}`, which fans one process out per trace across the cluster. They run 30 MiB to 215 MiB and take one to six minutes each.

Repository trace lists, for a `trace_list` field. Paths are relative to the repository root.

| list | size | for |
| --- | --- | --- |
| `experiments/smoke-2.list` | 2 bundled sample traces, seconds | G4 `smoke` |
| `experiments/perf-4.list` | 4 real traces, about 2 minutes per feature state | G5 `performance` |
| `experiments/perf-8.list` | 8 real traces, about 8 minutes per feature state | a slower, wider G5 |
| `experiments/screening-60.list` | 60 | stage 4 screening, not the gate |
| `experiments/training-105.list` | 105 | stage 4 validation, not the gate |

Use `perf-4.list` unless you have a reason not to. The gate runs a
performance list twice per attempt, feature-on and feature-off. The loop
allows six attempts, so every trace on the list is paid for twelve times.
Four traces is one wave across this cluster's four `cbp2025` slots. The
first full gate run measured eight traces at about 16 minutes of simulator
per attempt. Across six attempts that is an hour and a half.

## The recorded baseline, and what G2 compares against

`--stage baseline` builds the pristine checkout and records `hosts/cbp2025/baselines/<budget>.json`. That document holds the suite aggregate at the top level. It also holds a `per_trace` map, keyed by the trace path exactly as the list writes it. A `feature_off_baseline` entry that runs one `./cbp` command therefore has something exactly comparable to point at:

```json
"pass_condition": {
  "kind": "metrics_equal_baseline",
  "baseline_pointer": "/per_trace/int~1sample_int_trace.gz",
  "rel_tol": 0
}
```

`~1` is the RFC 6901 escape for a `/` inside a pointer token. The `rel_tol` value is 0 because this simulator is deterministic. The same binary on the same trace prints the same numbers. Any difference at all is the port leaking into the off path.

## Where your work lives

Stage 2 reads the pristine checkout at `~/cbp2025`. Stage 3 gets a fresh copy at `~/cbp2025_port` and edits that copy. The pristine tree stays untouched, so the recorded baseline and the plan's clean-tree results keep describing a tree that still exists.

Both trees sit on the one node that advertises `cbp2025_host`, and that is where your shell runs. Trace runs happen on other nodes and receive the built binary as bytes. Nothing you write outside the checkout travels with it.
