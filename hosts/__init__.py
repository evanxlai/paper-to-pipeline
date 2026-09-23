"""Host adapters: one build/run/stats surface per simulator, so the gate
and the DSE evaluator stay host-agnostic.

The seam they plug into is `adopt_a_paper_loop.HostAdapter`: name, work_dir,
notes, Ray resources, a baseline getter, a `run_gate`, and optionally the
head-side mirror plan_checks reads (`checks_root`) and the agent's shell
limit (`shell_timeout_s`). Stage 3 holds no per-host branches, so adding a
host is writing one of those and nothing else. `loop/tests/toy_host.py` is a
worked example against a fixture simulator, and
`loop/tests/integrate_smoke.py` runs the real stage against it.

Done:
  cbp2025:  hosts/cbp2025/adapter.py, with hosts/cbp2025/NOTES.md as the
            file the planning and integration agents read. It wraps
            chia_nodes/cbp2025/cbp2025_node.py and is the first host with a
            gate that judges rather than refuses. Exercised end to end by
            loop/tests/cbp2025_gate_smoke.py, which runs the real test plan
            against an UNPORTED copy of the checkout: G1, G2 and G4 must
            pass there, because an unported tree is the baseline, and
            anything else is a fault in the harness rather than in a port.

Wired, not yet proven on the cluster:
  gem5:     hosts/gem5/adapter.py, with hosts/gem5/NOTES.md for the agents.
            gem5 v25.1 ARM in syscall-emulation mode, TAGE_SC_L_64KB as the
            host predictor. It calls chia.simulators.gem5.Gem5Node's raw
            ChiaFunctions pinned to the gem5_host token, and never
            constructs a Gem5Node, whose own bundle names chia's "gem5"
            token and runs one task at a time. Everything lives on the one
            gem5_host node, because a gem5 binary is path-based and stays
            on the node that built it. The run scripts are hosts/gem5/run/,
            and the workloads are free programs built on the head by
            scripts/build_gem5_workloads.sh. The driver wires it into
            --stage baseline, plan and integrate. Stages dse and promote
            refuse it (dse.require_searchable), because the search only
            knows the CBP2025 kit. docs/gem5-runbook.md is the bring-up
            order, and loop/tests/gem5_gate_smoke.py is the gem5 twin of the
            cbp2025 gate smoke above, with the same expected result.

TODO(week 2):
  champsim: wrap chia.simulators.champsim.ChampSimNode
            (build_champsim/run_champsim ship in-tree; binary travels as bytes)
See hosts/<name>/NOTES.md for the integration hook points. Until it exists
`adopt_a_paper_loop.default_adapter` gives champsim a gate that fails
closed, which is the safe direction: an unimplemented check must never read
as a pass.

NOTE: the two stubs this file used to export (build_with_params(host, header)
/ run_one(host, build_artifact, trace)) assumed evolve-flows' evaluator calls
run_fn with the build artifact in hand. It doesn't -- skydiscover's
ChiaEvaluator calls run_fn(workload=trace) with no build reference, and
expects the build's output to be stashed by the caller (see the ContextVar
pattern in loop/sr_evaluator.py, copied from evolve-flows' reference
ChampSimEvaluator). Whoever writes a champsim or gem5 search evaluator should
follow that same shape: a build_fn(program) that stashes state and a
run_fn(*, workload) that reads it back, not a two-argument run_one."""
