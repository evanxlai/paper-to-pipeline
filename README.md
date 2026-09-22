# paper-to-pipeline

An "adopt-a-paper" CHIA loop. Give it a target design, a feature described by a paper, and success criteria. The loop plans the port. It integrates the feature into the design behind a deterministic gate. It then tunes the feature and the host budget split under a storage constraint. Only the tuned configuration counts as the verdict.

What each stage consumes, emits, and is judged by is specified in [docs/stages.md](docs/stages.md). One rule shapes the whole pipeline: only the DSE stage knows about resource constraints, so every stage before it is about implementing the feature correctly and nothing else.

Team: Evan Lai, Jan Strzeszynski. Accepted project for the Agentic Approaches to Architecture CHIA Hackathon. The accepted proposal text is in [docs/proposal.md](docs/proposal.md).

Demonstration: port sR, the register-value statistical-corrector component of RUNLTS (winner of CBP2025), into the CBP2025 kit's TAGE-SC-L. Tune the port at 192 KiB and at 64 KiB of total predictor storage. ChampSim and gem5 are the next two hosts, and the loop holds no per-host branches, so adding one is writing an adapter. The proposal calls this component "RBias". The paper names it sR, and this repository uses `sr` everywhere.

## Status: running end to end on a real cluster

The loop runs against a real host, on a real CHIA cluster, through
`chia job submit`. The host is the CBP2025 kit. That is the simulator the
RUNLTS paper itself was written against, so sR hooks into interfaces that
exist rather than into approximations of them.
[docs/cbp2025-runbook.md](docs/cbp2025-runbook.md) has the commands and the
measured timings.

What has run, with artifacts in the repository:

- **Stage 2 (plan).** `plan/sr.cbp2025.{plan,tests}.json`, written by an
  agent with an MCP shell on the checkout node and accepted by
  `loop/plan_checks.py`. It recorded the clean-tree summary as
  `" Read 997301 instrs "`, trailing space included, so it ran the command
  rather than guessing at it.
- **Baseline.** `hosts/cbp2025/baselines/iso-192KiB.json`, built from the
  pristine kit and fanned out over the cluster.
- **Stage 3 (integrate).** The agent ported sR and the port built. It
  matched the recorded baseline exactly with the knob off. It passed all
  seven spec unit tests and both existing regressions, and ran the smoke
  traces clean. G5 then failed: CycWPPKI moved from 388.07 to 554.61,
  which is 43 percent worse. The agent escalated `/host_interfaces/4` rather than
  weakening a test, and the escalation was right. See below.
- **The escalation loop.** Stage 3's escalation reached stage 2, which
  re-planned `/host_interfaces/4` from `fallback` to `exact` and moved the
  hook into the statistical corrector's own sum.

### What the first failed port taught

This is the part worth reading. The port was correct by every check except
the one that matters, and the cause was a wrong fact in
`hosts/cbp2025/NOTES.md`: it said `cbp2016_tage_sc_l.h` was off limits.

In the paper, sR is not a predictor that overrides TAGE-SC-L. It is one term
in the statistical corrector's sum. The host has that sum. It also has the
adaptive threshold that gates the corrector against TAGE. Kept out of that
file, the agent built the only other thing available: a standalone
predictor that flipped the TAGE answer on disagreement. Overriding a strong
predictor with an untrained one costs 43 percent. The agent then escalated exactly the right question: nothing
told it how confident its own sum had to be.

Three things about that are the point of the whole design. The gate caught
it, in plain code, with no model in the loop. The agent did not weaken a
test to get past it. And the fix belonged to the planning stage, which is
where the escalation sent it.

### Still open

- Host adapters for champsim and gem5 (`hosts/__init__.py`). Their gate
  fails closed, which is the safe direction.
- The debug node (stage 3b in [docs/stages.md](docs/stages.md)). The debug
  turn resumes the integration session instead of running as an
  independent diagnosis-only node. So there is not yet a single writer on
  the tree, the way the contract describes.
- Retiring the last budget from the pre-DSE stages. `distill` still reaches
  `spec_checks`, whose `budget_fit` check compares the spec's accounted
  storage against an allowance. Per the rule above that comparison belongs
  to stage 4 alone.
- Storage accounting inside the DSE evaluator. Nothing rejects an
  over-budget candidate yet, so the iso-budget claim rests on the search
  prompt alone.
- G5 compares the port against its own feature-off run. G2 proves that run
  is the baseline on one sample trace, not on the performance traces. That
  leaves a narrow gap: a port that leaks only on the larger traces sets its
  own bar.

## Fact-check corrections to the proposal

Research against primary sources (2026-09-11) corrected four premises. Full notes with sources are in [docs/research/](docs/research/).

1. RUNLTS is a CBP2025 workshop paper (June 2025, with ISCA-52), not ISCA 2026. It won first place. There is no arXiv version.
2. No component named "RBias" exists in the paper. The register-value component is sR (Section 4.2). It adds about 6.6 KiB and the paper calls it the largest single gain, without a scalar number.
3. The training suite is 105 traces, about 14 GiB compressed, not 673 traces at 160 GiB. The full post-contest set on Zenodo is 72.69 GiB compressed. Compute cost drops accordingly.
4. The "~2.5 percent from RBias" figure in the proposal matches the official overall CycWpPKI reduction of RUNLTS on the full set. It is not an sR-only number. Week 1 therefore adds an sR-off ablation of the artifact to measure the real yardstick.

None of these change the loop design. They change the demonstration numbers and the trace budget.

## How the loop works

```
paper (+ optional artifact)          docs/research/ has the verified APIs
        |
        v
[1] distill (LLM node) ----------> spec/sr.<mode>.json  (schema-checked by code)
        |
        v
[1.5] spec review ---------------> evidence-checked spec (spec_review.py)
        |
        v
[2] plan (LLM node; reads the model, runs the tests it already ships)
        |
        +--> plan/sr.<host>.plan.json   how this feature goes into this model
        +--> plan/sr.<host>.tests.json  correctness tests + performance tests
        |
        v
[3] integrate (coding agent + BashTool on the host container)
        |   implement from the plan, then run the test plan
        |        |
        |        +-- anything fails --> [3b] debug node: root-cause report,
        |        |                           diagnosis only, never edits ---+
        |        +----------------- back to the implement node <------------+
        v
    verify gate (gate.py, plain code; agents never self-report success)
        |   G1 build | G2 feature-off == baseline | G3 correctness tests
        |   G4 feature-on smoke clean | G5 performance block_threshold:
        |      direction, plus no-regression on companion metrics.
        |      A warn_threshold shortfall is reported and does not block.
        v
[4] DSE (evolve-flows evolver mutates sr_params.h)
        |   the only stage with a constraint set; iso-budget is one allowance
        |   value, not a special mode
        |   screening fan-out over ~60 traces per candidate on spot workers
        v
    full 105-trace validation of finalists -> tuned-vs-baseline verdict
```

CHIA mechanics: every step is a `@ChiaFunction` dispatched over Ray. Agents touch hosts only through MCP tools (`BashTool` plus the host nodes' build/run/stats). Promotion decisions are programmatic edges. `start_collector()` profiles token and compute cost per accepted change (`chia viz-profile`).

## Repository map

```
loop/                    the CHIA loop (head driver + nodes + prompts)
  adopt_a_paper_loop.py  driver: distill | baseline | plan | integrate | dse
  constants.py           every knob, env-overridable as P2P_*
  llm.py                 Gemini (antigravity/opencode+vertex) or Claude backends
  llm_gateway.py         OpenAI-compatible proxy to Vertex; refreshes the bearer
  plan_node.py           stage 2: the planning agent, validate + one repair turn
  plan_checks.py         stage 2: deterministic coverage checks over a plan pair
  plan_runner.py         runs a test plan against a host; feeds the gate
  gate.py                the deterministic verify gate (G1..G5), judging only
  dse.py                 evolve-flows wiring for the tuning stage
  prompts/               system, distiller, reviewer, planner, integrator, debug
  tests/integrate_smoke.py  stage 3 end to end against a fixture host, minutes
  tests/fixtures/toyhost/   that fixture: a 300-line C++ predictor sim
  tests/fixtures/tinysc_reference/  a correct port of it, so the gate is shown
                            passing a good port and failing a bad one
  tests/cbp2025_cluster_smoke.py  build + trace fan-out on the real cluster
  tests/llm_cluster_smoke.py      one prompt, one MCP shell, one real command
  tests/cbp2025_gate_smoke.py     the real gate against a tree with no port
chia_nodes/cbp2025/      new CHIA node wrapping the CBP2025 kit (upstream target)
hosts/                   per-host adapters + integration NOTES + recorded baselines
  cbp2025/adapter.py     the working one: executor, gate, port-tree lifecycle
  cbp2025/NOTES.md       what the planning and integration agents read
spec/                    feature-spec JSON schema (+ distilled specs land here)
plan/                    port-plan + test-plan schemas (plans land here too)
cluster/cluster.yaml     head + GCP spot workers, fully managed tailnet
experiments/             budgets, ablation matrix, DSE config, trace lists
scripts/                 setup_gcp.sh, fetch_artifacts.sh, install_llm_gateway.sh
docs/                    stage contracts, proposal, plan, GCP guide, gateway, research
  cbp2025-runbook.md     how to run every stage, with measured timings
```

## Quickstart

1. Follow [docs/gcp-setup.md](docs/gcp-setup.md): Free Trial credit, `scripts/setup_gcp.sh <project>`.
2. Run `scripts/fetch_artifacts.sh`. Then download the 105 training traces to a bucket.
3. Sign in to the Gemini agent CLI once on the head machine: `agy`.
4. Export `HEAD_IP`, `TS_AUTHKEY`, `GCP_PROJECT`, `GCP_PRIVATE_KEY_PATH`, `GOOGLE_CLOUD_PROJECT` (`source export.sh`).
5. Start the LLM gateway once: `./scripts/install_llm_gateway.sh`, then `sudo loginctl enable-linger "$USER"` so it survives logout. The DSE stage reaches Gemini through it, because a raw Vertex token expires an hour into a ~37-hour search. See [docs/llm-gateway.md](docs/llm-gateway.md).
6. `chia up cluster/cluster.yaml`
7. `chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage all`
8. `chia down cluster/cluster.yaml` after each session. Idle workers cost credit.

Run the stages one at a time the first time, and run the three harness
checks before the long ones. Both are in
[docs/cbp2025-runbook.md](docs/cbp2025-runbook.md), with measured timings.

## References

- CHIA: https://github.com/ucb-bar/chia and https://docs.chialoops.ai (loop conventions copied from `examples/memcpy` and `examples/circt_issue_solver`)
- Evolver: https://github.com/ucb-bar/evolve-flows (AlphaEvolve / AdaEvolve backends)
- CBP2025 kit: https://github.com/ramisheikh/cbp2025 (105 training traces via the Drive folder in its README)
- RUNLTS paper: https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final44-Koizumi.pdf
- Hosts: https://github.com/ChampSim/ChampSim and https://github.com/gem5/gem5 (pin gem5 to v25.1 for the `ConditionalPredictor` interface)
