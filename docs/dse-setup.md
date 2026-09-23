# DSE stage setup (`--stage dse`)

`loop/dse.py` depends on two packages that are not on PyPI and are not part
of this repo. Clone them as siblings of `chia` (matching the existing
`chia-hackathon/{chia,chia-hello-world,paper-to-pipeline}` layout) and
install both into the `chia_env` conda environment used by the head node:

```bash
cd ~/chia-hackathon
git clone https://github.com/ucb-bar/evolve-flows.git
cd evolve-flows
git clone --branch public-release-v1 https://github.com/ucb-bar/skydiscover.git

conda activate chia_env
pip install -e skydiscover
pip install -e .
```

Both must be importable wherever the `EvolverNode` Ray actor actually runs
-- today that's the machine advertising the `evolver` resource, which is the
chia head (see `cluster/cluster.yaml`'s `head_start_ray_commands`).

## The LLM route: everything goes through the gateway

Both adaevolve configs point at the project LLM gateway
(`loop/llm_gateway.py`, documented in `docs/llm-gateway.md`), which forwards
to Vertex AI with a freshly-refreshed bearer per request. Start it once and
export its shared secret:

```bash
./scripts/install_llm_gateway.sh
export P2P_GATEWAY_TOKEN="$(grep P2P_GATEWAY_TOKEN ~/.config/p2p/gateway.env | cut -d= -f2-)"
```

The public Gemini endpoint with a `GEMINI_API_KEY` is **not** a working
alternative on this project: that route draws on a separate AI Studio prepay
pool which is empty and returns `402 prepayment credits depleted`, while
Vertex returns 200 with `traffic_type: ON_DEMAND`. Re-probe both before
assuming otherwise.

Two traps to know about, both verified against `skydiscover/config.py`:

- **The model must be named `google/<model>`, not `gemini-<model>`.** Any
  name starting with `gemini-` matches skydiscover's `_BARE_PREFIX_MAP`, and
  `LLMConfig.__post_init__` then *forcibly overwrites* that model's
  `api_base` with the public `generativelanguage.googleapis.com` endpoint --
  silently discarding the `api_base` you set in the YAML. `google/...` is not
  a registered provider, so it falls through to the openai default, which
  (combined with a custom `api_base`) trips the
  `not (user_set_api_base and is_fallback)` guard and leaves your `api_base`
  intact. It also skips the provider-prefix strip, so Vertex receives the
  name in the `google/gemini-3.8-flash` form its endpoint expects.
- **`${VAR}` in the config is expanded inside the `EvolverNode` actor.**
  `Config.from_yaml` -> `_expand_env_vars` reads `os.environ` in the actor
  process, so `${P2P_GATEWAY_TOKEN}` must arrive through the driver's
  `ray.init(runtime_env={"env_vars": ...})`; exporting it in your shell alone
  is not enough. `loop/constants.py` forwards it, but only if it is set in
  the submitting shell when the driver imports that module.

Vertex model availability is project-specific and **drifts over time**, so it
must be re-probed, not assumed. An earlier version of this doc recorded
`google/gemini-3.8-flash` as serving on location `global` only, 404ing on
`us-central1`; on re-probe (2026-09-20) it returns 200 on both, as do
`google/gemini-2.5-flash`, `google/gemini-3.5-flash` and
`google/gemini-3.1-pro-preview`. Treat any list here as a snapshot.

Set `P2P_DSE_CONFIG` to choose which config `--stage dse` uses; it defaults
to the full 250-iteration `config_adaevolve.yaml`.

### Token expiry on long runs: fixed by the LLM gateway

This used to be an unfixed blocker. It is now handled by
`loop/llm_gateway.py` -- **see `docs/llm-gateway.md`**, which is the
authoritative reference. Summary of what the problem was and why the fix
lives outside this stage:

An ADC access token lives **60 minutes** (measured: `tokeninfo` reports
`expires_in` 3593), and nothing in the search stack refreshes it:

- `Config.from_yaml` expands `${VAR}` **once**, at `run_search` startup.
- `skydiscover/llm/openai.py` then hands that string to
  `openai.OpenAI(api_key=...)`, which freezes it into the client. skydiscover
  has no `token_provider`, no `refresh`, and no `google.auth` usage anywhere.
- Vertex validates the bearer token on **every** request and answers a stale
  one with `HTTP 401 UNAUTHENTICATED` (verified by sending a bogus token), so
  expiry fails hard rather than degrading.

Scale of the problem, from measured timings: build + a 6-trace fan-out took
517s, so a 60-trace screening evaluation is roughly 9-10 min of wall time
(traces run in parallel, so the count matters less than the slowest trace).
At `max_iterations: 250` that is ~37 hours with `max_parallel_iterations: 1`,
or ~5 hours if the parallel-build race below is also fixed. Either way the
token would expire about **6-7 iterations in** -- within the first 3% of the
search.

The fix is a gateway on the head that injects a freshly-refreshed bearer per
request, so `api_key` in these configs is now the gateway's shared secret
(`${P2P_GATEWAY_TOKEN}`), which does not expire. Both adaevolve configs point
at it. Start it with `./scripts/install_llm_gateway.sh` and export the secret
before submitting; `loop/constants.py` forwards it into the actor.

A rejected alternative worth recording: `LLMModelConfig.init_client` would
let you inject a refreshing client in-process, and `llm_pool.py` calls it in
preference to constructing `OpenAILLM`. But it is `Optional[Callable]` and
therefore unreachable from YAML -- it needs a code hook inside the
`EvolverNode` actor, which `run_dse` does not have. That is the concrete
reason the fix is a proxy rather than a config change.

Note also *which* identity ADC resolves to here: this machine's
`application_default_credentials.json` is `type: authorized_user` with a
refresh token -- a personal Google account, not a service account. So a DSE
run authenticates and bills as whoever ran
`gcloud auth application-default login`. A service account would be the right
answer for an unattended multi-hour run, though note it does **not** on its
own fix the expiry: service accounts also mint 1-hour access tokens, so the
refresh mechanism is still required either way.

## What was found wrong in the first draft (fixed, see loop/dse.py)

1. `experiments/config_adaevolve.yaml`'s `llm.models` was a list of bare
   strings; `skydiscover.config` builds each entry as `LLMModelConfig(**m)`,
   which requires a mapping (`- name: ...`). A bare string throws at
   `load_config()` time.
2. `evolve_flows.evolver.node.run_evolver` (the one-shot `ChiaFunction` the
   first draft called) never accepts an `evaluator=` override, so it always
   falls back to a single dummy `workloads=["default"]` -- it cannot fan a
   candidate out across the real screening trace list. Real fan-out needs
   the stateful `EvolverNode` Ray actor with a custom
   `skydiscover.evaluation.chia_evaluator.ChiaEvaluator` subclass, mirroring
   `evolve-flows/examples/alphaevolve-champsim-simple`.
3. `ChiaEvaluator` calls `run_fn(workload=trace)` -- not
   `run_fn(build_artifact, trace)` as the first draft assumed. The build
   artifact has to be stashed by `build_fn` and picked back up by `run_fn`
   out of shared state (a `contextvars.ContextVar`, following the reference
   `ChampSimEvaluator`), since the evaluator never passes it explicitly.
4. `result_mapper_fn` must return a
   `skydiscover.evaluation.evaluation_result.EvaluationResult`, not a plain
   dict, and skydiscover's fitness function reads a `combined_score` metric
   specifically (a bare `{"score": ...}` dict, as the first draft returned,
   is silently ignored).
5. `EvolverNode`/`run_evolver` both request the Ray resource
   `{"evolver": 1.0}` for placement. Nothing in `cluster/cluster.yaml`
   advertised it, so actor creation would have hung forever the same way
   `--stage baseline` hung on the missing `cbp2025` resource. Fixed by
   adding `"evolver":2` to the head node's `ray start --resources`.

## What the first live run found (fixed)

Editing `cluster.yaml` is not enough on its own: a cluster brought up
*before* that edit keeps advertising the old resource set, and
`ray.cluster_resources()` will report no `evolver` at all. Verify with
`ray status` before submitting. To add it to a live cluster without a full
`chia down`/`up` (which would re-download the ~11 GiB trace set), start a
second raylet on the head:

```bash
ray start --address=$HEAD_IP:6379 --resources='{"evolver":2}' \
          --num-cpus=2 --dashboard-agent-listen-port=0
```

Three real bugs surfaced only once this was run against the live cluster:

6. **Trace paths were never prefixed with `P2P_TRACE_DIR`.**
   `helpers.load_trace_list` returns the `.list` entries verbatim
   (`int/sample_int_trace.gz`), and `record_cbp_baseline` prefixes them --
   but the evaluator's `run_fn` passed them through bare, so they resolved
   against the Ray worker's cwd and every `./cbp` invocation failed to open
   its trace. The failure is *quiet*: `aggregate()` returns `n=0`,
   `_map_results` turns that into `combined_score 0.0`, and the search looks
   like it is running while scoring every candidate identically zero.
7. **The evaluator could not be pickled to the actor.** `dse.py` defined its
   `ChiaEvaluator` subclass inside a factory function, so cloudpickle
   serialized the class *by value*, dragging in the module-level
   `ContextVar` and dying with `cannot pickle '_contextvars.ContextVar'
   object`. `evolve_flows.evolver.bridge` registers the evaluator instance
   and generates a shim that calls `evaluate_program`, so the instance
   genuinely has to cross the wire. Fixed by moving the class to module
   scope in `loop/sr_evaluator.py` (pickled by reference), matching the
   reference `champsim_evaluator.py` layout.
8. **`RUNTIME_ENV`'s `PYTHONPATH` was `"."`.** Because the actor re-imports
   `sr_evaluator` by name when unpickling, `loop/` has to be on its path
   too; it is now `".:loop"`.

Verified working against the live cluster after these fixes: the evaluator
end-to-end (build on a `cbp2025` worker -> ContextVar binary handoff ->
6-trace fan-out, 6/6 ok, ~517s -> aggregate -> `combined_score` 141.1), the
`EvolverNode` actor placing on the `evolver` resource, the Vertex-routed
adaevolve config loading (`[llm] OpenAI LLM: google/gemini-3.8-flash`), the
initial program scoring 790.7014 on the single sample trace (which matches
`--stage baseline`'s recorded 0.2647 BrMisPKI exactly -- as it must while the
header is inert), and a successful LLM proposal call (HTTP 200).

## What's still not done

- Every host currently gets screened through the same `CBP2025Node`
  build/run path (`chia_nodes/cbp2025/cbp2025_node.py`) regardless of the
  `host` argument to `run_dse` -- `champsim`/`gem5` host adapters
  (`hosts/__init__.py`) are still unimplemented stubs, so there is no
  per-host budget-bit split or champsim/gem5-native evaluator yet.
- `promote_finalists` (the `promote` stage) scores the top 3 screening
  winners on `experiments/promote-16.list`. It has unit tests
  (`loop/tests/test_promote.py`) but has not yet run on the cluster.
- **`sr_params.h` is inert, so the search landscape is flat.** Nothing in the
  cbp2025 checkout `#include`s it (`grep -rn sr_params ~/cbp2025` on a
  sim_worker returns nothing), so the overlay writes a file no source reads
  and every candidate compiles to a byte-identical binary with an identical
  score. The DSE plumbing is exercised; the *search* is not. Making the
  parameters actually bite is stage-2 integration's job.
- **`config_adaevolve.yaml`'s `max_parallel_iterations: 8` is unsafe as
  written.** The generated shim runs each `evaluate_program` in its own
  thread, so concurrent evaluations issue concurrent `CBP2025Node.build`
  calls -- and every build overlays `sr_params.h` into the *same*
  `~/cbp2025` checkout and runs `make clean && make -j` there. Two builds
  landing on one worker will corrupt each other, and a candidate can be
  scored against another candidate's parameters. The ContextVar handoff
  itself is safe (each shim thread gets its own context); the shared
  checkout directory is not. Either keep `max_parallel_iterations: 1` or
  give each evaluation its own checkout copy before running a real search.
- Cluster stability is the practical limiter, not the DSE code. A run wedged
  with a `CBP2025Node.run` task stuck in `PENDING_NODE_ASSIGNMENT` for 15+
  minutes while `ray status` reported no pending resource demand and all 96
  `cbp2025` slots free; freshly submitted `cbp2025` tasks scheduled in 2.4s
  throughout. It coincided with chia's SSH-tunnel workers churning (repeated
  DEAD `127.0.0.2`/`127.0.0.3` raylets plus a phantom ALIVE one, `cbp2025`
  total drifting 64 -> 96) and a concurrent job whose runtime env failed with
  `Local directory ... for URI gcs://_ray_pkg_*.zip does not exist on the
  cluster`. Check `ray.util.state.list_nodes()` for duplicate/loopback
  `cbp2025` nodes before blaming `loop/dse.py`; killing the detached
  `p2p-dse-evolver-<host>` actor and resubmitting clears it.
