# Toy host integration notes

This host is a fixture. It exists so stage 3 can be exercised end to end —
LLM call, code edits through the bash tool, compile, test suite, gate,
debug turn — in seconds, without a simulator checkout or a trace download.
It is not a model of anything real. Everything below is verified fact about
*this* tree.

## Layout

```
Makefile            `make` -> build/toysim ; `make test` -> build/toytest, then runs it
src/params.h        every knob, read from the environment via param(name, fallback)
src/predictor.h/.cpp  ToyPredictor: predict(pc) then update(pc, taken), once per branch
src/sim.cpp         trace loop and stats; you should not need to touch it
tests/test_predictor.cpp  the host's own suite
workloads/*.trace   "<pc_hex> <taken>" per line
```

`LIB_SRCS` in the Makefile is a wildcard over `src/*.cpp`, and `TEST_SRCS` a
wildcard over `tests/*.cpp`, so new source and test files are picked up with no
Makefile edit.

## Hook points

There is exactly one, and it is `ToyPredictor`:

- `ToyPredictor::predict(uint64_t pc)` returns the baseline bimodal
  prediction. A feature that overrides predictions does it here, on the way
  out.
- `ToyPredictor::update(uint64_t pc, bool taken)` is called once per branch,
  immediately after `predict()` for that same branch, with the resolved
  outcome. Feature state is trained here.

There is no squash path and no speculation: the outcome is known one call
after the prediction. Add feature state as private members of `ToyPredictor`,
or as a separate class that `ToyPredictor` owns.

## Knobs and the enable flag

`src/params.h` exposes `param("NAME", fallback)`, which reads a `long` from the
environment. Add one accessor per knob next to `bimodal_entries()`. The enable
flag follows the same shape and **must default to off**, so an unconfigured run
of `build/toysim` reproduces the recorded baseline exactly. Name it exactly as
the spec names it: for the sR-style corrector this repository ports here, that
is `TINYSC_ENABLE`.

## Build and run

Builds take about a second, so the bash tool runs them directly; there is no
separate build or run tool on this host.

```sh
make                               # build/toysim
make test                          # build/toytest and run it
./build/toysim workloads/smoke.trace
TINYSC_ENABLE=1 ./build/toysim workloads/bias.trace
```

## Stats

`build/toysim` prints exactly one line of JSON on stdout and exits 0:

```
{"branches": N, "mispredicts": N, "instructions": N, "cycles": N, "mpki": F, "ipc": F}
```

The gate parses that line. Do not change the key names, do not print anything
else on stdout, and keep the run deterministic — the feature-off equality check
compares these numbers against a recorded baseline with zero tolerance.
