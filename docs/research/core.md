# CHIA framework core — verified API map (ucb-bar/chia @ main, 2026-09-11)

All snippets below were pulled from the actual repo (shallow clone of `github.com/ucb-bar/chia` and `github.com/ucb-bar/evolve-flows`) and the docs sources in `docs/` (which are the source of docs.chialoops.ai — confirmed live at `https://docs.chialoops.ai/en/latest/getting-started/quickstart.html`).

## 0. Identity / install

- Paper: "CHIA: An open-source framework for principled, agentic AI-driven hardware/software co-design research", Cui et al. 2026, arXiv 2606.27350. UC Berkeley (ucb-bar).
- PyPI dist is **`chialoops`** ("chia" name is taken), import package and console script are **`chia`** (`pyproject.toml`: `[project.scripts] chia = "chia.cli.main:main"`, version 1.0.1, BSD-3-Clause).
- Requires **Python 3.10.19** exactly (matches Docker images). Install: `pip install -e /path/to/chia` in a conda env.
- Runtime substrate is **Ray** (scheduling, actors, ObjectRefs, fault tolerance). MCP via **FastMCP** (FastAPI+uvicorn tool servers). Docker for worker containers.

## 1. How a loop is defined

**Language: plain Python.** A "CHIA project" = a **loop** (Python orchestration script, the graph) + a **cluster** (YAML file, the machines/workers). There is NO YAML/DSL for the loop itself; YAML is only for (a) the cluster and (b) cache/bypass config.

Core primitive: the `@ChiaFunction` decorator (`chia/base/ChiaFunction.py`). Minimal real loop, verbatim from `examples/hello-world/hello-world-s1.py`:

```python
from chia.base.ChiaFunction import ChiaFunction, get

@ChiaFunction()
def print_hello_world():
    print("Hello World (#1) from a remote call!")

def main():
    get(print_hello_world.chia_remote())

if __name__ == "__main__":
    main()
```

Execution surface of a `@ChiaFunction` (from `docs/user_guides/chia_function.rst`):
- `fn(...)` — local call in the caller's process (still profiled/bypassable/cacheable).
- `fn.chia_remote(*args)` — async dispatch onto a worker satisfying `resources`; returns a Ray `ObjectRef` immediately.
- `fn.chia_remote_blocking(*args)` — remote + blocks, returns unwrapped value (this is what you register on tools).
- `fn.options(num_cpus=4, scheduling_strategy="SPREAD", resources={...}).chia_remote(...)` — per-call override; accepts anything Ray `.options()` accepts, incl. `max_retries` (default 3) and `PlacementGroupSchedulingStrategy`.
- `ChiaCallRemote(fn, *args, **kwargs)` — functional form, TypeErrors if fn isn't a ChiaFunction.
- `get(ref)` — collect. `chia_wait(tracked, num_returns=1, pending_timeout=120, retry=True)` — `ray.wait` replacement over `TrackedRef(ref, submit_fn=..., label=...)` that detects wedged `PENDING_NODE_ASSIGNMENT` tasks and resubmits. `chia_cancel(ref, force=True)` — kills spawned subprocesses on remote nodes then cancels (process-leak prevention).
- Reserved per-call kwargs: `_chia_tag` (cache/bypass key), `_chia_setup`/`_chia_setup_args`, `_chia_cleanup`/`_chia_cleanup_args` (worker-side hooks; cleanup runs in `finally`).
- `chia_actor(some_actor)` wraps a Ray actor handle with the same `.chia_remote` surface (no profiling/bypass/cache on actors).
- Resource tagging: `@ChiaFunction(resources={"chipyard": 1})` — worker must advertise the label; matches `available_node_types.<name>.resources` in cluster.yaml.

Library-node convention: plain Python class holding config/state, with `@staticmethod @ChiaFunction(resources={...})` (or bound-method) members as the dispatchable nodes, e.g. `ChiselBuildNode.build`, called as `cb_node.build.chia_remote(cb_node)` (self passed explicitly).

Cluster YAML (separate file, `chia up cluster.yaml`) — verbatim schema from `examples/hello-world/cluster.yaml`: `provider: {head_ip: ...}`, `auth: {ssh_user, ssh_private_key}`, `available_node_types: {<name>: {resources: {...}, num_workers, compatible_ips: [...], worker_setup_commands: [...], docker: {image, container_name, run_options, pull_timeout, pull_before_run}}}`, plus `head_env_commands`, `head_setup_commands`, `head_start_ray_commands`, `worker_start_ray_commands`. `${VAR}` interpolates from env. Cloud nodes under `aws_nodes`/`gcp_nodes`; tailscale is the default cross-firewall transport (`chia/cluster/tailnet.py`), SSH reverse tunnel fallback (`chia/cluster/tunnel.py`).

## 2. Programmatic vs agentic edges

Direct quote (`docs/concepts/overview.rst`): "CHIA treats both **programmatic** and **agentic** edges as first-class primitives".

- **Programmatic edge**: passing an `ObjectRef` returned by `chia_remote` straight into another `chia_remote` call as an argument. "Passing a ref directly without `get()` tells Ray that this task depends on that one, forming an explicit edge in the task graph" (`docs/user_guides/chia_function.rst`). Any argument may be `T` or `ObjectRef[T]`.

```python
bin_ref   = compile_program.chia_remote(c_src)
build_ref = cb_node.build.chia_remote(cb_node)
result = get(verilator_node.run.chia_remote(
    verilator_node, build_ref, bin_ref, "helloworld.riscv", "/home/ray"))
```

- **Agentic edge**: a `ChiaTool` (MCP server on a worker) handed to an agent node's `prompt` via `tools=[...]`; the agent decides which tools to call and when (`docs/user_guides/chia_tool.rst`). `ChiaTool` base: `chia/base/tools/ChiaTool.py` (also `_ToolServerActor`, `_PortRegistry`, `ToolInfo` in that file). Endpoint: `http://{host}:{port}/{name}/mcp`.
  - Define via `setup()` idiom: subclass `ChiaTool`, define `setup(self, ...)` that calls `self.mcp.add_tool(self.method, name=f"{self.name}_...")`. Construction deploys the server immediately; `tool.stop()` shuts it down (important — it holds its resource slot). Explicit idiom: `super().__init__(name, task_options=...)` → `self.mcp.add_tool(...)` → `super().__post_init__()`.
  - Placement via `task_options={"resources": {"chipyard": 1}}`.
  - Bridge back to programmatic: register `self.mcp.add_tool(fn.chia_remote_blocking)` so a tool call fans out real scheduled cluster work.
  - Every LLM/agent node's `prompt(user_message, tools: Optional[List[ChiaTool]])` accepts tools; the method docstring is the tool description the model sees.

Verbatim quickstart agentic wiring (`docs/getting-started/quickstart.rst` step 4 / `examples/hello-world/hello-world-s4.py`):

```python
from chia.models.opencode import *
from chia.base.tools.BashTool import *

llm = OpenCodeLLM("opencode/big-pickle")
chipyBash = BashTool("chipyard_bash", CHIPYARD_PATH,
                     task_options={"resources": {"chipyard": 1}})
resp: QueryResult = get(llm.prompt.chia_remote(llm, LLM_RTL_PROMPT, tools=[chipyBash]))
chipyBash.stop()
```

## 3. Node types

### 3a. Model/LLM nodes — `chia/models/` (exact class names)
Base: `chia/base/llm_call.py` — `LLMCallBase(ABC)` (ctor: `system_message`, `dangerously_skip_permissions=UNSET`, `config=UNSET`; abstract `prompt(user_message, tools=[]) -> QueryResult`) and `@dataclass QueryResult(result: str, returncode: int, stderr: str, stream_result: str, success: bool = False)`.

- `chia/models/claude.py`: `ClaudeCodeLLM(LLMCallBase)` — wraps `claude --print` CLI; ctor defaults `model="claude-sonnet-4-6"`, `backend="cli"` (or experimental `"api"` via Anthropic SDK), `resume_session`, `dangerously_skip_permissions=True`. Also `ClaudeCodeQueryResult(QueryResult)` with `session_transcript` bytes for cross-worker `--resume`. Typed error hierarchy (`RateLimitError`, `BillingError`, `MaxOutputTokensError`, ...).
- `chia/models/codex.py`: `CodexLLM`; `chia/models/copilot.py`: `CopilotLLM`; `chia/models/opencode.py`: `OpenCodeLLM`; `chia/models/antigravity.py`: `AntigravityLLM` (Google Antigravity `agy` CLI — **Gemini agent path**; mounts `~/.gemini` sign-in per memcpy docs).
- **Gemini API wiring**: `chia/models/vertex.py` — `VertexGeminiLLM(LLMCallBase)`: Gemini-on-Vertex via `google-genai`, client-side MCP tool execution loop (connects to each ChiaTool's MCP server, translates to Gemini `function_declarations`, sanitizes JSON schema keys Gemini rejects, loops on `function_call`/`function_response`). Ctor: `model, system_message, timeout_seconds=600, retries=3, project (or $GOOGLE_CLOUD_PROJECT), location (or $GOOGLE_CLOUD_LOCATION, default us-central1), max_tokens=16000, max_tool_iterations=100`. Its `prompt` is `@ChiaFunction(resources={"vertex_creds": 0.01})`. Marked "experimental" (warns). Same file: `VertexGenericLLM(OpenAICompatLLM)` for non-Gemini Vertex MaaS models (e.g. `meta/llama-3.1-8b-instruct-maas`).
- `chia/models/bedrock.py`: `BedrockLLM`; `chia/models/openai_compat.py`: `OpenAICompatLLM`; `chia/models/openai_providers.py`: `OpenAILLM`, `FireworksLLM`, `GroqLLM`, `OpenRouterLLM`, `NvidiaLLM`; `chia/models/ollama.py`: `OllamaLLM(OpenAICompatLLM)`; `chia/models/vllm.py`: `VLLMLLM(OpenAICompatLLM)`.
- Docs note (`docs/api/models.rst`): non-agent providers are turned into a "very primitive agent" (query→tool call→query loop); for serious work they recommend the agent CLIs.

### 3b. Tool nodes — `chia/base/tools/`
`ChiaTool.py` (base), `BashTool.py` (`BashTool(ChiaTool)`, single `run_command(command: str) -> str`), `AsyncJobTool.py` (`AsyncJobTool(ChiaTool)` — submit/status split for long jobs), `AsyncBashTool.py` (`AsyncBashTool(AsyncJobTool)`), `ChiaToolTemplate.py` (copyable starting point), `util.py`. Note: there is no class literally named "ChiaTools"; build/run/stats functionality lives on the simulator nodes (below), not on the tool base. Return types: str/dict/pydantic/TypedDict/dataclass/list/None/MCP Image/Audio all serialize.

### 3c. Evolver nodes — OUT-OF-TREE, repo `github.com/ucb-bar/evolve-flows`
(described in-tree at `docs/case-studies/architectural-discovery-basic.rst`)
- `evolve_flows/evolver/node.py`:
  - `run_evolver` — `@ChiaFunction(resources={"evolver": 1.0})` one-shot entry: `run_evolver(evolver_input: EvolverInput, build_fn, run_fn, result_mapper_fn) -> EvolverResult`.
  - `EvolverNode` — `@ray.remote(max_concurrency=2)` **stateful Ray actor** (typically detached): methods `run_search(evolver_input, build_fn, run_fn, result_mapper_fn, evaluator: Optional[ChiaEvaluator] = None)`, `get_status()`, `stop()`. Launched as:
    ```python
    evolver = EvolverNode.options(name="adaevolve-prefetcher-simple-evolver",
        lifetime="detached", resources={"evolver": 1.0}, runtime_env=RUNTIME_ENV).remote()
    ```
- `evolve_flows/evolver/types.py`: `@dataclass EvolverInput(config_path, initial_program, config_content=None, resource_tag=None)`, `EvolverResult(best_program, best_metrics, iteration_count, terminal_status, population, metrics_log_path, error_message)`, `EvolverStatus(state, iteration, best_score, best_metrics, best_program)`.
- `evolve_flows/evolver/bridge.py`: `run_skydiscover(...)` bridges to **SkyDiscover** (`github.com/ucb-bar/SkyDiscover`, git submodule `skydiscover` @ branch `public-release-v1`); `ChiaEvaluator` is imported from `skydiscover.evaluation.chia_evaluator`.
- **Three-function evaluator interface** (`build_fn`, `run_fn`, `result_mapper_fn`) — the ChiaEvaluator calls build once/candidate, fans out run_fn across workloads via CHIA scheduling, aggregates via result_mapper_fn; build failures score 0.0.
- **Backend selection is YAML**: `search.type: "alphaevolve"` (Google Cloud AlphaEvolve API; needs GCP project + Gemini Enterprise license + `gcloud auth application-default login`, config keys `alphaevolve: {project_id, engine_id, credentials_file}`, `idle_timeout_s` default 1800) or `search.type: "adaevolve"` (local SkyDiscover; supports AdaEvolve, OpenEvolve, EvoX, GEPA). AdaEvolve LLM config is OpenAI-compatible; default Gemini: `llm.api_base: "https://generativelanguage.googleapis.com/v1beta/openai/"`, `api_key: ${GEMINI_API_KEY}`, models e.g. `gemini-3.5-flash`, `gemini-3.1-pro-preview`; provider prefixes `openai/gpt-...`, `anthropic/claude-...`, `deepseek/`, `mistral/`, `cohere/`. Other config keys: `max_iterations`, `file_suffix`, `checkpoint_interval`, `random_seed`, `search.database.{population_size,num_islands,...}`, `prompt.system_message`, `diff_based_generation`, `max_parallel_iterations`.
- Example flow: `examples/alphaevolve-champsim-simple/` (`run_flow.py`, `champsim_evaluator.py` — `class ChampSimEvaluator(ChiaEvaluator)`, `result_mapper.py`, `cluster.yaml`, `config_adaevolve.yaml`, `config_alphaevolve.yaml`). `run_flow.py` subcommands: `python run_flow.py [--config ...]`, `python run_flow.py status`, `python run_flow.py stop` (works because the actor is detached). Outputs `best_prefetcher.cc` + `chia_eval_log.jsonl`.

### 3d. Gate/verify constructs
No class named Gate/Verifier exists. The gating primitives are:
- **Bypass conditions**: `bypass.set_cond("fn_name", cond)` where `cond(tag, data_path, *args, **kwargs) -> bool` runs on the caller at dispatch time, last step after `bypass: true` flag + provider/data check + tag regex. Falsy → run for real (see §5).
- `chia_wait`'s stuck-task detection/resubmission, and loop-level checks written in plain Python (e.g. memcpy's `classify_run` in `examples/memcpy/helpers.py`: build failed / sim failed / incorrect → debug LLM node, ≤ NUM_DEBUG_ATTEMPTS).

## 4. In-tree simulator/tool nodes — exact module paths

- **gem5**: `chia/simulators/gem5.py` — `Gem5Node` with `@staticmethod @ChiaFunction(resources={"gem5": 1.0})` members `build_gem5`, `run_gem5`, `capture_gem5_source_state`, `restore_gem5_source_state`, plus `parse_gem5_stats`, `parse_gem5_stats_file`, `spawn_tool(...)` (yields a `Gem5ToolServer`); dataclasses `Gem5BuildArtifact`, `Gem5RunResult`, `Gem5SourceState`, enums `Gem5Isa`, `Gem5Variant`. Placement-group co-location via `require_colocated=True` default; context-manager support.
- **ChampSim**: `chia/simulators/champsim.py` — `ChampSimNode` with `@staticmethod @ChiaFunction(resources={"champsim": 1.0})` members `build_champsim(champsim_root, prefetcher_src, module_name, *, cache_level="L2C", timeout_s=600, incremental=False) -> ChampSimBuildResult` and `run_champsim(binary: bytes, trace, *, warmup_instructions=5_000_000, simulation_instructions=25_000_000, timeout_s=300) -> ChampSimRunResult`, plus `capture_champsim_source_state`/`restore_champsim_source_state`; dataclasses `CachePrefetchStats`, `CacheStats`, `ChampSimBuildResult`, `ChampSimRunResult`, `ChampSimSourceState`. Binary (~5MB) travels as bytes so build/run need not co-locate (`ChampSimNode(require_colocated=False)`). Exports in `chia/simulators/__init__.py`.
- **Chipyard**: `chia/chipyard/` — `chisel_build_node.py` (`ChiselBuildNode.build`, resources `{"chipyard": 1}`), `verilator_run_node.py` (`VerilatorRunNode.run`, resource `verilator_run`), `cosim_node.py` (`CosimNode`), `spike_build_node.py` (`SpikeBuildNode`), `riscv_build_node.py` (`RiscvBuildNode`), `riscv_dv_gen_node.py` (`RiscvDvGenNode`, `GenSpec`), `riscv_objdump_node.py` (`RiscvObjdumpNode`), `torture_run_node.py` (`TortureRunNode`), `firemarshal_node.py` (`FireMarshalNode`), `chipyard_hammer.py` (`ChipyardHammerNode(ColocatedNode)`), `macrocompiler.py`, `state_def.py` (`BuildTarget`, `BuildArtifact`, `RunResult`, `CosimResult`, `SpikeResult`, ...).
- **CIRCT**: `chia/chipyard/circt.py` — module-level `@ChiaFunction(resources={"circt": 1})` functions: `firtool_lower_chirrtl_to_hw`, `circt_opt_run`, `circt_opt_lower_hw_to_verilog`, `rebuild_circt_opt_with_custom_pass`, `list_circt_passes`, `chisel_elaborate_to_chirrtl`, `circt_ninja_build`, `circt_warm_build`; plus agent tools `BuildTool(AsyncJobTool)` and `LitTool(AsyncJobTool)`.
- **Hammer (VLSI)**: `chia/vlsi/hammer.py` — `HammerNode(ColocatedNode)` with `@ChiaFunction(resources={"hammer": 1})` members; results `HammerResult`, `HammerCollectResult`, `HammerMatchResult`, `HammerCollectFsResult`. Also `chia/vlsi/sram_cacti/` (CACTI SRAM: `cacti_runner.py`, `cacti_macrocompiler.py`, `lef_gen.py`, `liberty_gen.py`, `sram_characterize.py`).
- **Verilator**: `chia/chipyard/verilator_run_node.py` (`VerilatorRunNode`) — Verilator is a run target of Chipyard builds (`BuildTarget.VERILATOR`), image `ghcr.io/ucb-bar/chia-verilator-run:latest`.
- **FireSim**: `chia/firesim/` — `build_node.py`, `run_node.py`, `suite_runner.py`, `workloads.py`, `spec_parser.py`, `config.py`, `chia_functions.py` (FPGA; CLI `chia firesim-build/-run/-upload-workload/-cleanup`).
- **ESP**: `chia/esp/esp_workspace.py` (`EspWorkspaceNode(ColocatedNode)`).
- **Databases**: `chia/database/` — `sqlite_node.py` (`SQLiteNode(DatabaseNode)`, `SQLiteQueryTool(ChiaTool)`), `postgres_node.py` (`PostgresNode`, `PostgresQueryTool(ChiaTool)`), `base.py` (`DatabaseNode(ColocatedNode)`).
- **GitHub**: `chia/github/` — `github_issues_node.py`, `github_pulls_node.py`, `github_client.py`.
- Co-location helper: `chia/base/colocated.py` — `ColocatedNode`, `PinnedChiaFn`.
- Docker images (ghcr.io/ucb-bar): `chia-chisel-build`, `chia-verilator-run`, `chia-champsim`, `chia-opencode`, etc.; Dockerfiles under `dockerfiles/` (Gem5Dockerfile, ChampSimDockerfile, ChipyardDockerfile, ClaudeCodeDockerfile, ...).

## 5. Caching / bypass (`docs/user_guides/caching_and_bypass.rst`, `chia/base/cache.py`, `chia/base/bypass.py`)

Key = per-call `_chia_tag` (e.g. `_chia_tag=f"iter{i}_opt{j}"`). Cache = write path; bypass = read/replay path. Configured in one YAML passed to the loop (NOT the cluster yaml):

```yaml
bypass:
  simple_add: { bypass: true }
  run_verilator_test: { bypass: true, tags: ["iter0_.*"] }
  simple_multiply: true                       # shorthand
  summarize_perf: { bypass: true, data: /path/to/recorded_perf.md }
cache:
  run_verilator_test: { cache: true, tags: ["iter.*"] }
  build_megaboom: true
```

API:
- `Bypass(yaml_path=...)` (None → no-op). `bypass.set_provider("fn_name", provider)` where `provider(tag, data_path, *args, **kwargs)` runs ON THE WORKER with the real function's scheduling — the call still dispatches through Ray (deliberate: tests orchestration cheaply). `bypass.set_cond("fn_name", cond)` gates at dispatch time. `data:` path with no provider → file contents served as str via a head-pinned Ray actor (`BypassFileServer`) so no shared FS needed. Bypassed only if `bypass: true` AND (provider OR data).
- `start_cache(size=4, units="GB", cache_dir_path=..., yaml_path=...)` on the driver after `ray.init()`; cache is a named Ray actor on head — access via `get(get_active_cache().has.chia_remote(tag))` / `.read.chia_remote(tag)` (returns `(hit, value)`). Writing is automatic for `cache: true` functions keyed by `_chia_tag`; on-disk pickled `(tag, data)` LRU that warm-starts across runs. Reading is manual: register a bypass provider that reads the cache. Canonical populate-then-replay pattern with a `cache_hit` cond: `examples/bypass_cache/bypass_cache_loop.py` (+ `bypass_cache.yaml`, `cluster.yaml`) — run twice, cold then warm.

## 6. Profiling (`chia/trace/`, `docs/user_guides/profiling.rst`, `chia/trace/PROFILER.MD`)

- `from chia.trace.profiler import start_collector, stop_collector, get_profiler`. `start_collector(log_dir=...)` after `ray.init()` spawns `ProfileCollectorActor` (named actor, head-pinned, num_cpus=0), appends JSONL to `{log_dir}/ChiaProfileCollector.log` (default `/tmp/ray/{job_id}/`). Every `@ChiaFunction` call auto-instruments; no collector → all no-ops. Namespace-scoped: parallel driver processes each get their own collector/log.
- Events: `dispatch` (worker ip/id, resources, `obj_ref_deps` dependency edges via `id(value)`→call_id matching, interned scalars skipped), `complete` (`exec_time_s` + `extra` metadata), `local_start`/`local_end`, custom via `get_profiler().log_event("checkpoint", iteration=3)`.
- `get_profiler().add_info({...})` (thread-local) merges into the current call's `complete` event. **Token/compute cost per change**: every LLM backend calls `profiler.add_info(self._last_metadata)` after each prompt (`chia/models/claude.py:500`, and same in codex/copilot/vertex/opencode/antigravity/openai_compat/bedrock). For Claude the metadata includes `model`, `tools` (name/host/port/node), `cost_usd` (from CLI `total_cost_usd`), `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`. Simulator nodes attach domain metrics the same way (`verilator_run_node.py`: `simulation_cycles`, `test_binary`; `chisel_build_node.py` build info).
- Rendering: `chia viz-profile <log...> --format {svg,png,pdf,html,table}` (dependency graph, interactive HTML timeline, or CSV aggregation; `--run N`, `--gap-threshold SEC`, `--funcs`). Static call-graph from source without running: `chia viz <source.py> [--func NAME]`. Metrics streaming: `chia/trace/metrics.py` — `MetricsLogger` with `TensorBoardBackend` / `WandbBackend` / `NullBackend`.

## 7. Running a loop / CLI (`chia/cli/main.py`, `docs/user_guides/reference.rst`)

- `chia up <cluster.yaml>` (flags `-y`, `--dry-run`, `--add` to grow a live cluster), `chia down <cluster.yaml>`.
- Submit the loop: `chia job submit --working-dir . -- python hello-world.py` (proxies `ray job submit`; `--submission-id NAME` to name it; `chia job stop <id> [--kill-tracked-pids --grace-period 25]` kills tracked subprocesses via the PID registry actor first). `--chia-cluster path/to/cluster.yaml` targets a specific cluster on shared machines.
- Alternatively plain `python run_flow.py` with `ray.init(address="HEAD:6379", namespace=..., runtime_env={"working_dir": str(FLOW_DIR), "env_vars": {...}})` — the evolve-flows example does exactly this (forwards `GEMINI_API_KEY` etc. through `runtime_env.env_vars`).
- `chia status` / `chia list` / `chia ray <anything>` — Ray passthrough. FireSim: `chia firesim-build/-run/-upload-workload/-cleanup`. Ray dashboard at `http://<head>:8265`.

## 8. Out-of-tree loop repo conventions (what your hackathon repo should look like)

Two proven templates:
1. **evolve-flows style** (separate installable package): repo root `pyproject.toml` + `evolve_flows/` package (nodes/types/bridge) + `examples/<flow-name>/` with `run_flow.py` (entry, argparse subcommands run/status/stop), `cluster.yaml`, one or more `config_*.yaml` (search backend config), evaluator + result_mapper modules. Installed with `pip install -e .` next to `pip install -e /path/to/chia`. Loops import `from chia.base.ChiaFunction import ChiaFunction` and library nodes (`from chia.simulators.champsim import ChampSimNode`).
2. **in-repo example style** (`examples/memcpy/`, per `docs/user_guides/memcpy_example.rst` — "a good starting point for building your own generate, build, simulate, debug loops"): `memcpy_loop.py` (orchestration), `llm.py` (LLM node construction + failure formatters; `--llm {claude,opencode,antigravity}` picks `ClaudeCodeLLM`/`OpenCodeLLM`/`AntigravityLLM`), `helpers.py` (run classification, out/ dumper), `constants.py` (all knobs/resources/paths), `prompts/*.md` (`${VAR}` placeholders substituted at load), `cluster.yaml`, `env.yml`, test program source. Run: `chia up examples/memcpy/cluster.yaml` then `chia job submit -- python "$(pwd)/examples/memcpy/memcpy_loop.py"`.

Support: user forum groups.google.com/g/chialoops; leads Angela Cui, Ferran Hermida-Rivera, Jack Toubes, Sagar Karandikar (Berkeley). Status: beta.

## SOURCES
https://api.github.com/repos/ucb-bar/chia/git/trees/main?recursive=1
https://raw.githubusercontent.com/ucb-bar/chia/main/README.md
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/getting-started/quickstart.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/getting-started/chia-basics.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/getting-started/installation.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/concepts/overview.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/chia_function.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/chia_tool.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/caching_and_bypass.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/profiling.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/memcpy_example.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/reference.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/api/models.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/api/agents_models.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/api/base.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/index.rst
https://github.com/ucb-bar/chia (shallow clone @ main: chia/base/ChiaFunction.py, chia/base/bypass.py, chia/base/cache.py, chia/base/llm_call.py, chia/base/tools/ChiaTool.py, chia/models/*.py, chia/simulators/gem5.py, chia/simulators/champsim.py, chia/chipyard/*.py, chia/vlsi/hammer.py, chia/trace/PROFILER.MD, chia/cli/main.py, pyproject.toml, examples/hello-world/*, examples/memcpy/*, examples/bypass_cache/*, docs/case-studies/architectural-discovery-basic.rst)
https://api.github.com/repos/ucb-bar/evolve-flows/git/trees/main?recursive=1
https://github.com/ucb-bar/evolve-flows (shallow clone @ main: evolve_flows/evolver/node.py, evolve_flows/evolver/types.py, evolve_flows/evolver/bridge.py, examples/alphaevolve-champsim-simple/run_flow.py, examples/alphaevolve-champsim-simple/config_adaevolve.yaml, examples/alphaevolve-champsim-simple/champsim_evaluator.py, .gitmodules, README.md)
https://docs.chialoops.ai/en/latest/getting-started/quickstart.html

## CAVEATS
1) EvolverNode / AlphaEvolve / AdaEvolve are NOT in the ucb-bar/chia tree — they live in ucb-bar/evolve-flows (verified by clone) with the actual `ChiaEvaluator` base class in the SkyDiscover git submodule (git@github.com:ucb-bar/skydiscover.git @ branch public-release-v1); I did not fetch SkyDiscover itself, so `skydiscover.evaluation.chia_evaluator.ChiaEvaluator`'s internals (exact constructor/EvaluationResult schema) are known only from its usage sites (ChampSimEvaluator subclass, bridge.py, docs) — verify against that repo before coding against it. 2) There is no class named "ChiaTools" — the MCP tool base is `ChiaTool` (chia/base/tools/ChiaTool.py); build/run/stats methods live on simulator nodes (Gem5Node.build_gem5/run_gem5/parse_gem5_stats, ChampSimNode.build_champsim/run_champsim). 3) No dedicated gate/verify node class exists; gating = Bypass.set_cond + ordinary Python control flow in the loop. 4) Gemini is wired three ways (VertexGeminiLLM raw API — flagged experimental in-source; AntigravityLLM agent CLI; AdaEvolve's OpenAI-compat endpoint with GEMINI_API_KEY) — there is no file named gemini.py. 5) docs.chialoops.ai was spot-checked (quickstart page loads and matches the repo rst); I read the rst sources from the repo rather than every rendered page — cluster_config_reference.rst, logical_workers.rst, docker_images.rst, google_auth.rst and the other case-study pages were not read in full. 6) Everything quoted reflects main as of 2026-09-11 (chialoops 1.0.1, self-described beta); the repo mentions readonly evolve-flows import name `from evolve_flows import EvolverNode, run_evolver` in its README whose `EvolverNode(config_path=...)` usage snippet does NOT match the actual actor API in node.py (actor takes no ctor args) — trust node.py, not the README snippet.