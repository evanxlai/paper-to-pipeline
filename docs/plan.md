# Execution plan

This plan expands the four-week schedule from the accepted proposal into tasks. The proposal text is in [proposal.md](proposal.md). What each loop stage consumes, emits, and is judged by is in [stages.md](stages.md). When a task is done, check its box.

## Week 1: CBP2025 node, harnesses, baseline reproduction

- [ ] Set up the GCP Free Trial project. Follow [gcp-setup.md](gcp-setup.md).
- [ ] Bring up a small test cluster with `chia up` and the Tailscale configuration.
- [ ] Download the CBP2025 trace suite to a GCS bucket.
- [ ] Build the CBP2025 simulator and run one predictor on one trace locally.
- [ ] Write the CBP2025 CHIA node: build, run, and stats tools.
- [ ] Run the RUNLTS artifact through the node. Make sure that the reported BrMisPKI matches the paper (3.197 at 192 KiB).
- [ ] Build ChampSim and gem5 baselines. Record baseline MPKI and IPC per trace.

## Week 2: distill, plan, integrate, and debug to a passing gate

Stage contracts for this section are in [stages.md](stages.md). Nothing here is allowed to
reason about a storage budget; that is week 3's subject.

- [ ] Write the feature-spec JSON schema.
- [ ] Write the distiller prompt. Run it on the RUNLTS paper in paper-only mode.
- [ ] Make sure that the distilled sR spec matches the observed behavior of the artifact.
- [x] Write the port-plan and test-plan JSON schemas (`plan/port_plan.schema.json`, `plan/test_plan.schema.json`). A worked pair against the fixture host is in `loop/tests/fixtures/tinysc.toy.{plan,tests}.json`.
- [ ] Write the planner prompt and the plan node. It reads the host checkout and runs the test suite that checkout already ships, so each existing regression in the test plan carries a verified clean-tree result.
- [ ] Write the plan coverage checks: every spec state element, algorithm, parameter, and host-interface need must map to a code site, or the plan fails before integration starts.
- [ ] Size a performance trace list between the 5-trace smoke set and the 60-trace screening set, so the performance thresholds have signal.
- [ ] Write the `verify_gate` node: build, feature-off baseline preservation, the test plan's correctness entries, the feature-on smoke, and the directional threshold on the performance entries.
- [ ] Write the debug node: diagnosis only, with build/run/test access to reproduce a failure, reporting a root cause back to the implement node.
- [ ] Run plan, then integrate, on ChampSim until the gate passes.
- [ ] Run plan, then integrate, on gem5 TAGE-SC-L until the gate passes.

## Weeks 3 and 4: DSE at scale, ablations, write-up

- [ ] Move the storage budget out of the pre-DSE stages: drop the gate's storage condition and the `budget` argument on distill and integrate, and express the tracks as allowance values in the DSE constraint set.
- [ ] Configure the EvolverNode over the RBias parameters and the host budget split.
- [ ] Run screening DSE (about 60 traces per candidate, 200 to 300 candidates).
- [ ] Promote finalists to the full 105-trace training run.
- [ ] Ablation 1: naive port vs. tuned port, both hosts, both budgets (192 KiB, 64 KiB).
- [ ] Ablation 2: paper-only vs. paper-plus-reference distillation inputs.
- [ ] Stretch: port a second RUNLTS feature (history-length selection or allocation throttling).
- [ ] Collect CHIA profiling data: token cost and compute cost per accepted change.
- [ ] Write the 4-page report.
- [ ] Prepare the loop blocks and the CBP2025 node for upstreaming to mainline CHIA.

## Success criteria

The targets come from the proposal:

- Feature-off ports match each host baseline on MPKI and IPC.
- Before tuning, each port moves its target metric in the direction the paper claims, without regressing beyond noise. The magnitude target below is a post-DSE verdict; pre-DSE it is measured and reported, never gated.
- The tuned ports recover at least 50 percent of the relative MPKI gain that RUNLTS attributes to the register components (sR). Note: the paper gives no scalar for sR alone, so week 1 must first measure it by ablating sR in the artifact. See README section "Fact-check corrections".
- Total spend stays under the $1,300 cap. The target is $1,000.
