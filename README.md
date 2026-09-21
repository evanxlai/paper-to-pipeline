# paper-to-pipeline

An "adopt-a-paper" CHIA loop. Give it a target design, a feature described by a paper, and success criteria. The loop plans the port, integrates the feature into the design behind a deterministic gate, and then tunes the feature and the host budget split under a storage constraint. Only the tuned configuration counts as the verdict.

What each stage consumes, emits, and is judged by is specified in [docs/stages.md](docs/stages.md). One rule shapes the whole pipeline: only the DSE stage knows about resource constraints, so every stage before it is about implementing the feature correctly and nothing else.

Team: Evan Lai, Jan Strzeszynski. Accepted project for the Agentic Approaches to Architecture CHIA Hackathon. The accepted proposal text is in [docs/proposal.md](docs/proposal.md).

Demonstration: port sR, the register-value statistical-corrector component of RUNLTS (winner of CBP2025), into ChampSim and into gem5's TAGE-SC-L. Tune each port at 192 KiB and at 64 KiB of total predictor storage. The proposal calls this component "RBias". The paper names it sR, and this repository uses `sr` everywhere.

## Status: rough first draft

Done:

- The stage contracts, including the plan / integrate / debug split ([docs/stages.md](docs/stages.md)).
- The loop driver, the LLM backend factory, the deterministic gate, and the prompts (`loop/`).
- The CBP2025 CHIA node, written for upstreaming (`chia_nodes/cbp2025/`).
- The feature-spec JSON schema (`spec/feature_spec.schema.json`).
- Cluster configuration YAML for a local head plus GCP spot workers over Tailscale (`cluster/cluster.yaml`).
- Host integration notes with the exact hook points in ChampSim and gem5 (`hosts/*/NOTES.md`).
- Docs: GCP setup, week-by-week plan, ablation matrix, budget tracks.

Not done (marked TODO in the code):

- The plan node and the debug node (stages 2 and 3b in [docs/stages.md](docs/stages.md)). Today a single `integrate` stage plans and implements in one session, and the debug turn resumes that same session instead of being an independent diagnosis-only node.
- The port-plan and test-plan JSON schemas (`plan/*.schema.json`) plus their coverage checks, which are what make an unmapped spec item a planning failure rather than an integration surprise.
- Retiring every budget check from the pre-DSE stages. `gate.py` still carries a storage condition, and `distill`/`integrate` still take a `budget` argument; per the rule above, neither belongs before stage 4.
- Host build/run adapters (`hosts/__init__.py`). The gate fails closed until these exist.
- DSE evaluator wiring against `evolve-flows` (its `ChiaEvaluator` internals are unverified).
- Trace lists (`experiments/*.list`) wait on the trace download.
- Nothing was executed yet against a real simulator. No cluster was brought up,
  and neither ChampSim nor gem5 has been built. Stage 3's machinery *has* been
  run end to end -- LLM call, agent edits, compile, test suite, gate, debug turn
  -- against the fixture host in `loop/tests/fixtures/toyhost`, via
  `python loop/tests/integrate_smoke.py`. That says the stage works; it says
  nothing yet about porting sR into a real model.

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
        |   G4 feature-on smoke clean | G5 performance direction
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
  adopt_a_paper_loop.py  driver: distill | baseline | integrate | dse (plan: TODO)
  constants.py           every knob, env-overridable as P2P_*
  llm.py                 Gemini (antigravity/opencode+vertex) or Claude backends
  llm_gateway.py         OpenAI-compatible proxy to Vertex; refreshes the bearer
  gate.py                the deterministic verify gate (G1..G5)
  dse.py                 evolve-flows wiring for the tuning stage
  prompts/               system, distiller, reviewer, integrator, debug
  tests/integrate_smoke.py  stage 3 end to end against a fixture host, minutes
  tests/fixtures/toyhost/   that fixture: a 300-line C++ predictor sim
chia_nodes/cbp2025/      new CHIA node wrapping the CBP2025 kit (upstream target)
hosts/                   per-host adapters + integration NOTES + recorded baselines
spec/                    feature-spec JSON schema (+ distilled specs land here)
plan/                    port-plan + test-plan schemas (TODO; plans land here)
cluster/cluster.yaml     head + GCP spot workers, fully managed tailnet
experiments/             budgets, ablation matrix, DSE config, trace lists
scripts/                 setup_gcp.sh, fetch_artifacts.sh, install_llm_gateway.sh
docs/                    stage contracts, proposal, plan, GCP guide, gateway, research
```

## Quickstart (when the TODOs close)

1. Follow [docs/gcp-setup.md](docs/gcp-setup.md): Free Trial credit, `scripts/setup_gcp.sh <project>`.
2. Run `scripts/fetch_artifacts.sh`. Then download the 105 training traces to a bucket.
3. Sign in to the Gemini agent CLI once on the head machine: `agy`.
4. Export `HEAD_IP`, `TS_AUTHKEY`, `GCP_PROJECT`, `GCP_PRIVATE_KEY_PATH`, `GOOGLE_CLOUD_PROJECT` (`source export.sh`).
5. Start the LLM gateway once: `./scripts/install_llm_gateway.sh`, then `sudo loginctl enable-linger "$USER"` so it survives logout. The DSE stage reaches Gemini through it, because a raw Vertex token expires an hour into a ~37-hour search. See [docs/llm-gateway.md](docs/llm-gateway.md).
6. `chia up cluster/cluster.yaml`
7. `chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage all`
8. `chia down cluster/cluster.yaml` after each session. Spot workers cost credit while idle.

## References

- CHIA: https://github.com/ucb-bar/chia and https://docs.chialoops.ai (loop conventions copied from `examples/memcpy` and `examples/circt_issue_solver`)
- Evolver: https://github.com/ucb-bar/evolve-flows (AlphaEvolve / AdaEvolve backends)
- CBP2025 kit: https://github.com/ramisheikh/cbp2025 (105 training traces via the Drive folder in its README)
- RUNLTS paper: https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final44-Koizumi.pdf
- Hosts: https://github.com/ChampSim/ChampSim and https://github.com/gem5/gem5 (pin gem5 to v25.1 for the `ConditionalPredictor` interface)
