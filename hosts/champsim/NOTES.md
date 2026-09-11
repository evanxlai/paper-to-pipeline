# ChampSim integration notes for the sR port

Facts below were read from ChampSim `master` on 2026-09-11. The integration agent gets this file inside its prompt.

## Module system

A branch predictor is a C++ class in `branch/<name>/<name>.{h,cc}`. The class name must equal the directory basename (`config/modules.py`). It inherits `champsim::modules::branch_predictor` (`inc/modules.h`). Hook methods are optional and detected at compile time:

```cpp
void initialize_branch_predictor();                    // optional
bool predict_branch(champsim::address ip, champsim::address predicted_target,
                    bool always_taken, uint8_t branch_type);   // use this 4-arg overload
void last_branch_result(champsim::address ip, champsim::address branch_target,
                        bool taken, uint8_t branch_type);
```

`branch_type` values: `BRANCH_DIRECT_JUMP`, `BRANCH_INDIRECT`, `BRANCH_CONDITIONAL`, `BRANCH_DIRECT_CALL`, `BRANCH_INDIRECT_CALL`, `BRANCH_RETURN`, `BRANCH_OTHER`.

Select it in the config JSON with `{"branch_predictor": "sr"}`, then `./config.sh my_config.json && make`. An out-of-tree module dir works with `./config.sh --branch-dir DIR`. That flag lets this repo keep the module outside the ChampSim checkout.

## Constraints that shape the port

1. No TAGE ships in ChampSim `master`. The four in-tree predictors are `bimodal`, `gshare`, `perceptron`, and `hashed_perceptron` (the default). The port must bring its own TAGE-SC-L base.
2. A `"branch_predictor"` list does not compose. All listed modules get update calls, but only the LAST module's `predict_branch` return value is used (comma-fold in `inc/ooo_cpu.h`). Modules cannot see each other's predictions.
3. Therefore the clean pattern is ONE module that owns both parts: instantiate the base TAGE-SC-L as a member, compute its prediction, then apply the sR statistical-corrector term inside `predict_branch`. Feed both parts from `last_branch_result`.
4. `predict_branch` is invoked for every instruction, and `last_branch_result` runs right after prediction in program order. There is no squash path in trace-driven ChampSim, so the sR digest table updates at `last_branch_result` time.
5. Register values: ChampSim traces carry source and destination register IDs but the host does not model register values the way the CBP2025 trace reader does. This is the `host_interfaces` fallback case in the spec. Options: derive digests from load values in the trace records, or approximate with a value-free proxy. Record the deviation in PORT_NOTES.md.

## Enable knob

Add a constructor-read environment knob or a constexpr config in `sr_params.h` (`SR_SR_ENABLE`). With the knob off, `predict_branch` must return the base prediction unmodified and `last_branch_result` must update only the base predictor.

## Metrics

Plain output prints, per CPU: `cumulative IPC: ...` and `Branch Prediction Accuracy: ...% MPKI: ...`, plus per-type `Branch type MPKI` lines. Pass `--json` for machine-readable output with `instructions`, `cycles`, and a `mispredict` map. Stats cover the simulation phase only, not warmup.

## Run shape

```sh
bin/champsim --warmup-instructions 200000000 --simulation-instructions 500000000 trace.champsimtrace.xz
```

Traces are ChampSim-format (`.champsimtrace.xz`), for example the DPC-3 SPEC set. They are separate from the CBP2025 traces.
