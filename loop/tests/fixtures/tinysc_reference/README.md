# A reference port of tinysc into the toy host

This is what a correct execution of `tinysc.toy.plan.json` produces. It exists
so that "the gate passes a good port and fails a bad one" is something the
test suite demonstrates rather than something the docstrings assert -- the
gate is only meaningful if both halves are shown, and a gate nobody has seen
pass is as untrustworthy as one nobody has seen fail.

`test_plan_runner.py` copies these files over a materialized copy of
`fixtures/toyhost` and runs the real `plan_runner` and `gate` against the
result. No agent and no LLM is involved.

Every file here follows the plan: the hook points it names, the enable knob it
names, the macro names `dse.params_header_from_spec` emits, and the exact `ok:`
markers the test plan's pass conditions match. `src/sr_params.h` is literally
that function's output at the spec's defaults.
