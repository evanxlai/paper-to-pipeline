# Execution plan

This plan expands the four-week schedule from the accepted proposal into tasks. The proposal text is in [proposal.md](proposal.md). When a task is done, check its box.

## Week 1: CBP2025 node, harnesses, baseline reproduction

- [ ] Set up the GCP Free Trial project. Follow [gcp-setup.md](gcp-setup.md).
- [ ] Bring up a small test cluster with `chia up` and the Tailscale configuration.
- [ ] Download the CBP2025 trace suite to a GCS bucket.
- [ ] Build the CBP2025 simulator and run one predictor on one trace locally.
- [ ] Write the CBP2025 CHIA node: build, run, and stats tools.
- [ ] Run the RUNLTS artifact through the node. Make sure that the reported BrMisPKI matches the paper (3.197 at 192 KiB).
- [ ] Build ChampSim and gem5 baselines. Record baseline MPKI and IPC per trace.

## Week 2: distillation and integration agents to a passing gate

- [ ] Write the feature-spec JSON schema.
- [ ] Write the distiller prompt. Run it on the RUNLTS paper in paper-only mode.
- [ ] Make sure that the distilled sR spec matches the observed behavior of the artifact.
- [ ] Write the `verify_gate` node: the build check, the baseline-preservation check, and the spec-derived unit tests.
- [ ] Run the integration agent on ChampSim until the gate passes.
- [ ] Run the integration agent on gem5 TAGE-SC-L until the gate passes.

## Weeks 3 and 4: DSE at scale, ablations, write-up

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
- The tuned ports recover at least 50 percent of the relative MPKI gain that RUNLTS attributes to the register components (sR). Note: the paper gives no scalar for sR alone, so week 1 must first measure it by ablating sR in the artifact. See README section "Fact-check corrections".
- Total spend stays under the $1,300 cap. The target is $1,000.
