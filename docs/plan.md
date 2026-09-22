# Execution plan

This plan expands the four-week schedule from the accepted proposal into tasks. The proposal text is in [proposal.md](proposal.md). What each loop stage consumes, emits, and is judged by is in [stages.md](stages.md). When a task is done, check its box.

## Week 1: CBP2025 node, harnesses, baseline reproduction

- [x] Set up the GCP Free Trial project (`a3-chia-hack26ath-7728`). Application-default credentials, Compute Engine and Cloud Storage APIs are all in place. Follow [gcp-setup.md](gcp-setup.md).
- [ ] Bring up a small test cluster with `chia up` and the Tailscale configuration.
- [x] Download the CBP2025 trace suite to a GCS bucket. All 105 training traces (14.0 GiB) are in `gs://a3-chia-hack26ath-7728-cbp2025/cbp2025/<workload>/`, in `us-central1` to match the cluster zone. The set was checked object-for-object against `experiments/training-105.list`; per-workload counts are int 37, web 26, infra 16, fp 14, compress 8, media 4. `cluster/cluster.yaml` syncs workers from this bucket rather than Google Drive.
- [x] Build the CBP2025 simulator and run one predictor on one trace locally (`third_party/cbp2025`, needs `zlib1g-dev`). The kit's shipped `SampleCondPredictor` returns `tage_pred` unchanged, so a default build is the TAGE-SC-L baseline. Running it on `int_0_trace.gz` reproduces the organizer's `reference_results_training_set.csv` row exactly on every field: 40000041 instr, 14701131 cycles, IPC 2.7209, 205309 mispredicts, MPKI 5.1327, CycWPPKI 250.3935. That validates the build and the downloaded trace at once.
- [x] Write the CBP2025 CHIA node: build, run, and stats tools (`chia_nodes/cbp2025/cbp2025_node.py`).
- [ ] Run the RUNLTS artifact through the node. Make sure that the reported BrMisPKI matches the paper (3.197 at 192 KiB).
- [ ] Build ChampSim and gem5 baselines. Record baseline MPKI and IPC per trace.
- [ ] Measure the sR-only gain by ablating sR in the RUNLTS artifact. The paper gives no scalar for sR alone, so without this number the "recover 50 percent of the sR gain" success criterion has no yardstick. See README section "Fact-check corrections".

## Week 2: distill, plan, integrate, and debug to a passing gate

Stage contracts for this section are in [stages.md](stages.md). Nothing here is allowed to
reason about a storage budget; that is week 3's subject.

- [x] Write the feature-spec JSON schema (`spec/feature_spec.schema.json`).
- [x] Write the distiller prompt (`loop/prompts/distiller.md`). Run it on the RUNLTS paper in paper-only mode; the draft spec is `spec/sr.paper_only.json`.
- [ ] Make sure that the distilled sR spec matches the observed behavior of the artifact.
- [x] Write the port-plan and test-plan JSON schemas (`plan/port_plan.schema.json`, `plan/test_plan.schema.json`). A worked pair against the fixture host is in `loop/tests/fixtures/tinysc.toy.{plan,tests}.json`.
- [x] Write the planner prompt and the plan node (`loop/prompts/planner.md`, `loop/plan_node.py`). It reads the host checkout and runs the test suite that checkout already ships, so each existing regression in the test plan carries a verified clean-tree result.
- [x] Write the plan coverage checks (`loop/plan_checks.py`): every spec state element, algorithm, parameter, host-interface need and unit test must map to something in the plan pair, or the plan fails before integration starts.
- [ ] Size a performance trace list between the 5-trace smoke set and the 60-trace screening set, so the performance thresholds have signal.
- [x] Write the `verify_gate` node (`loop/gate.py` judging, `loop/plan_runner.py` measuring): build, feature-off baseline preservation, the test plan's correctness entries, the feature-on smoke, and the directional threshold on the performance entries. Both halves are shown against the fixture host -- a correct port passes and a knob that fails to gate is caught.
- [ ] Write the debug node: diagnosis only, with build/run/test access to reproduce a failure, reporting a root cause back to the implement node.
- [ ] Run plan, then integrate, on ChampSim until the gate passes.
- [ ] Run plan, then integrate, on gem5 TAGE-SC-L until the gate passes.

## Weeks 3 and 4: DSE at scale, ablations, write-up

- [ ] Finish moving the storage budget out of the pre-DSE stages. Done: the gate's storage condition is gone and `integrate` takes a baseline key rather than a budget. Left: `distill` still passes one to `spec_checks`, whose `budget_fit` check compares the spec against an allowance and fails stage 1 closed. Then express the tracks as allowance values in the DSE constraint set.
- [ ] Configure the EvolverNode over the sR parameters and the host budget split.
- [ ] Run screening DSE (about 60 traces per candidate, 200 to 300 candidates).
- [ ] Promote finalists to the full 105-trace training run.
- [ ] Ablation 1: naive port vs. tuned port, both hosts, both budgets (192 KiB, 64 KiB).
- [ ] Ablation 2: paper-only vs. paper-plus-reference distillation inputs.
- [ ] Stretch: port a second RUNLTS feature (history-length selection or allocation throttling).
- [ ] Collect CHIA profiling data: token cost and compute cost per accepted change.
- [ ] Write the 4-page report.
- [ ] Prepare the loop blocks and the CBP2025 node for upstreaming to mainline CHIA.

## The loop's own test suite

`loop/tests/` holds unit tests for the loop's machinery, not for any port. Nothing
runs them automatically -- there is no CI and the driver never invokes pytest -- so
run them by hand after changing anything under `loop/`:

```
python3 -m pytest loop/tests -q
```

The tests that need skydiscover/evolve-flows skip where it is absent
([dse-setup.md](dse-setup.md)). Separately, `python loop/tests/integrate_smoke.py`
drives stage 3 end to end against the fixture host; it takes minutes and runs a
real agent, so it is not part of the fast suite.

## Success criteria

The targets come from the proposal:

- Feature-off ports match each host baseline on MPKI and IPC.
- Before tuning, each port moves its target metric in the direction the paper claims, without regressing beyond noise. The magnitude target below is a post-DSE verdict; pre-DSE it is measured and reported, never gated.
- The tuned ports recover at least 50 percent of the relative MPKI gain that RUNLTS attributes to the register components (sR). Note: the paper gives no scalar for sR alone, so week 1 must first measure it by ablating sR in the artifact. See README section "Fact-check corrections".
- Total spend stays under the $1,300 cap. The target is $1,000.
