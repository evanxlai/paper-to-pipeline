"""Host adapters: one build/run/stats surface per simulator, so the gate
and the DSE evaluator stay host-agnostic.

The seam they plug into is `adopt_a_paper_loop.HostAdapter`: name, work_dir,
notes, spec_path, Ray resources, a baseline getter and a `run_gate`. Stage 3
holds no per-host branches, so adding a host is writing one of those and
nothing else. `loop/tests/toy_host.py` is a worked example against a fixture
simulator, and `loop/tests/integrate_smoke.py` runs the real stage against it.

TODO(week 2): implement. Targets:
  cbp2025:  chia_nodes/cbp2025/cbp2025_node.py (done, loop/dse.py uses it
            directly today; every host is currently screened through it,
            see loop/dse.py's module docstring)
  champsim: wrap chia.simulators.champsim.ChampSimNode
            (build_champsim/run_champsim ship in-tree; binary travels as bytes)
  gem5:     wrap chia.simulators.gem5.Gem5Node
            (build_gem5/run_gem5/parse_gem5_stats; placement-group co-location)
See hosts/<name>/NOTES.md for the integration hook points.

NOTE: the two stubs this file used to export (build_with_params(host, header)
/ run_one(host, build_artifact, trace)) assumed evolve-flows' evaluator calls
run_fn with the build artifact in hand. It doesn't -- skydiscover's
ChiaEvaluator calls run_fn(workload=trace) with no build reference, and
expects the build's output to be stashed by the caller (see the ContextVar
pattern in loop/dse.py's SRParamsEvaluator, copied from evolve-flows'
reference ChampSimEvaluator). Whoever wires up champsim/gem5 here should
follow that same shape: a build_fn(program) that stashes state and a
run_fn(*, workload) that reads it back, not a two-argument run_one."""
