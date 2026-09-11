# CHIA example dissection: `examples/memcpy` and `examples/circt_issue_solver`

Repo: `github.com/ucb-bar/chia` (main @ tree sha `16c35e92aaaf9511c6453bf94cd5cf589698f4e3`, fetched 2026-09-11). Repo description: "An open framework for designing and deploying custom AI-driven HW/SW co-design flows fast". All snippets below are verbatim from raw.githubusercontent.com files.

---

## 1. Complete file listings

### `examples/memcpy/` (8 files + prompts/)
```
examples/memcpy/README.md            (11447 B)
examples/memcpy/__init__.py          (0 B, empty)
examples/memcpy/cluster.yaml         (6925 B)
examples/memcpy/constants.py         (10408 B)
examples/memcpy/helpers.py           (8092 B)
examples/memcpy/llm.py               (13766 B)
examples/memcpy/memcpy.c             (1573 B)
examples/memcpy/memcpy_loop.py       (13669 B)   <- main driver
examples/memcpy/test_build.py        (6654 B)
examples/memcpy/prompts/debug.md     (931 B)
examples/memcpy/prompts/implement.md (2171 B)
```
(`out/` is created at runtime, git-ignored.)

### `examples/circt_issue_solver/` (16 files + prompts/)
```
examples/circt_issue_solver/.gitignore                   (88 B)
examples/circt_issue_solver/README.md                    (8735 B)
examples/circt_issue_solver/circt_issue_loop.py          (14336 B)  <- issue-flow driver (head)
examples/circt_issue_solver/circt_util.py                (9209 B)   <- worker git/build/lit helpers
examples/circt_issue_solver/cluster.yaml                 (4213 B)   <- Claude backend
examples/circt_issue_solver/cluster_antigravity.yaml     (4505 B)   <- Gemini via agy CLI
examples/circt_issue_solver/cluster_opencode_vertex.yaml (5115 B)   <- OpenCode + Gemini on Vertex
examples/circt_issue_solver/config.py                    (86 B)     <- GITHUB_REPO = "llvm/circt"
examples/circt_issue_solver/db.py                        (4333 B)   <- SQLite persistence (head)
examples/circt_issue_solver/env.yml                      (775 B)    <- conda env "circtissues"
examples/circt_issue_solver/fix_issues_submit.sh         (2419 B)   <- job-submit wrapper
examples/circt_issue_solver/issue_task.py                (15441 B)  <- per-issue pipeline (worker)
examples/circt_issue_solver/review_loop.py               (8545 B)   <- PR-review-flow driver
examples/circt_issue_solver/review_submit.sh             (1316 B)
examples/circt_issue_solver/review_task.py               (9980 B)   <- per-PR pipeline (worker)
examples/circt_issue_solver/triage.py                    (3673 B)   <- issue selection heuristics
examples/circt_issue_solver/prompts/assess.md            (4390 B)
examples/circt_issue_solver/prompts/fix.md               (2162 B)
examples/circt_issue_solver/prompts/regression.md        (2003 B)
examples/circt_issue_solver/prompts/reproduce.md         (1884 B)
examples/circt_issue_solver/prompts/review.md            (3117 B)
examples/circt_issue_solver/prompts/review_assess.md     (3301 B)
examples/circt_issue_solver/prompts/system.md            (4489 B)
examples/circt_issue_solver/prompts/writeup.md           (1729 B)
```
`.gitignore` (verbatim): `issues.db`, `issues.db-journal`, `issue_logs/`, `issue_logs_to_pr/`, `__pycache__/`, `*.pyc`, `review_logs`.

---

## 2. CHIA's core API surface (as used by both examples)

CHIA is **built on Ray**. There is no declarative "loop graph" DSL — the loop is plain Python control flow in a driver script; nodes are Ray-dispatched functions/methods. Key primitives (all confirmed in use):

- `chia.base.ChiaFunction` module: `ChiaFunction` (decorator), `get`, `chia_wait`, `TrackedRef`.
  - `@ChiaFunction(resources={"<token>": N})` decorates a plain function into a dispatchable node. Call pattern: `get(fn.options(resources={...}).chia_remote(args...))` or just `get(fn.chia_remote(args...))`. `chia_remote` returns a ref; `get()` blocks on it (Ray `get` wrapper that also does session-tracking for LLM objects).
  - `chia_wait(tracked_refs, num_returns=1, pending_timeout=S, retry=True)` — wait-with-stuck-detection over `TrackedRef(ref=..., submit_fn=..., label=...)` objects (auto-resubmit on hang).
- Custom Ray **resource tokens** are the scheduling mechanism: each container node type in `cluster.yaml` advertises tokens (`{"chipyard": 1}`, `{"circt": 1}`, `{"llm": 2}`, `{"verilator_run": 1}`, `{"opencode_creds": 1}`, `{"antigravity_creds": 1}`), and each dispatch names the token it consumes. Fractional tokens (0.01…1.0) let a long-lived tool actor coexist with builds on the same container.
- `chia.base.tools.BashTool.BashTool(name, work_dir, timeout_seconds, task_options)` — an MCP tool server (subclass of `chia.base.tools.ChiaTool.ChiaTool`) deployed as a Ray actor into a target container; it registers one MCP tool named `f"{name}_run_command"` (`self.mcp.add_tool(self.run_command, name=f"{name}_run_command")`). `task_options={"resources": {...}}` or a `NodeAffinitySchedulingStrategy` pins where it runs. The LLM CLI (running on a *different* container) reaches it **over HTTP MCP**. Tools have `.stop()` for teardown. Async variants exist: `chia/base/tools/AsyncBashTool.py`, `AsyncJobTool.py`; domain tools `BuildTool` / `LitTool` live in `chia/chipyard/circt.py` (async: start call returns immediately, agent polls `build_status` / `lit_status` until `done=true`).
- `chia.base.llm_call`: `LLMCallBase` (abstract `prompt(user_message, tools: Optional[List[ChiaTool]])`) and `QueryResult` dataclass — fields `result: str`, `returncode: int`, `stderr: str`, `stream_result: str`, `success: bool = False`. Backends additionally expose `session_transcript` (bytes: Claude `.jsonl` / Antigravity SQLite `.db`) and `usage` (token/cost, antigravity+opencode).
- LLM backends in `chia/models/`: `claude.py` (`ClaudeCodeLLM`), `antigravity.py` (`AntigravityLLM`, Google's `agy` CLI), `opencode.py` (`OpenCodeLLM`, `AdditionalModelProvider`), plus `codex.py`, `copilot.py`, `bedrock.py`, `vertex.py`, `openai_compat.py`, `ollama.py`, `vllm.py`. Each backend's `.prompt` is itself a ChiaFunction, so it is dispatched onto the container holding the backend's credential resource: `get(llm.prompt.options(resources={"llm": 1.0}).chia_remote(llm, prompt, tools))`.
- Prebuilt domain nodes: `chia.chipyard.chisel_build_node.ChiselBuildNode`, `chia.chipyard.verilator_run_node.VerilatorRunNode`, `chia.chipyard.state_def` (`BuildTarget`, `BuildArtifact`, `RunResult`), `chia.github.github_issues_node.GithubIssuesNode`, `chia.github.github_pulls_node.GithubPullsNode`, `chia.database.sqlite_node.SQLiteNode`.
- CLI: `chia up <cluster.yaml>` / `chia down <cluster.yaml>` / `chia job submit [--runtime-env-json JSON] -- python <abs path to driver>` / `chia job logs <id>` (also runnable as `python -m chia.cli.main up ...`). Ray dashboard at :8265 (memcpy cluster uses :8081).

---

## 3. Anatomy — `examples/memcpy`

**Loop**: implement (LLM writes a RoCC memcpy accelerator in Chisel into a chipyard checkout) ∥ test build (cross-compile `memcpy.c`) → chisel build → verilator run → classify → on failure, debug turn (same resumed LLM session) → rebuild/rerun, up to `NUM_DEBUG_ATTEMPTS` (default 3).

**Where the "loop graph" is defined**: `memcpy_loop.py::run_loop()` — plain Python `for attempt in range(NUM_DEBUG_ATTEMPTS + 1):` with branches on `artifact.success` and `classify_run(run)`. Verbatim core of the loop:

```python
def run_loop(llm_backend: str = "claude") -> dict:
    ray.init(address="auto", runtime_env=RUNTIME_ENV)
    dump = Dumper(OUT_DIR)
    ...
    chipyard_bash = BashTool(
        name="chipyard_bash",
        work_dir=CHIPYARD_PATH,
        timeout_seconds=300,
        task_options={"resources": {"chipyard": CHIPYARD_BASH_RESOURCE}},
    )
    ...
    llm = make_llm(llm_backend, chipyard_bash)

    # ----- parallel phase: test build || implement ----------------------
    test_ref = build_test.options(
        resources={"chipyard": TEST_BUILD_RESOURCE}
    ).chia_remote(source_content, CHIPYARD_TESTS_DIR, TEST_NAME, TEST_BUILD_TIMEOUT_SECONDS)

    impl = implement(llm, chipyard_bash)
    ...
    test = get(test_ref)
    ...
    for attempt in range(NUM_DEBUG_ATTEMPTS + 1):
        collect_chisel_diff(dump, attempt)
        artifact = chisel_build(dump, attempt)
        if not artifact.success:
            ...
            feedback = format_build_failure(artifact, attempt + 1)
            dbg = debug(llm, chipyard_bash, feedback)
            ...
            continue
        run = verilator_run(dump, attempt, artifact, test.riscv_name,
                             test.riscv_content, dramsim_ini)
        outcome = classify_run(run)
        if outcome.passed:
            status = "passed"
            break
        ...
        feedback = format_sim_failure(run, outcome, test.dump, attempt + 1)
        dbg = debug(llm, chipyard_bash, feedback)
    summary["status"] = status
    dump.json("summary.json", summary)
```

**A node definition** — verbatim, a custom `@ChiaFunction` node (`test_build.py`):
```python
from chia.base.ChiaFunction import ChiaFunction

@ChiaFunction(resources={"chipyard": 0.05})
def build_test(
    source_content: bytes,
    tests_dir: str,
    test_name: str,
    timeout_seconds: int = 900,
) -> TestBuildResult:
```
And a prebuilt node used via a wrapper (`memcpy_loop.py::chisel_build`):
```python
node = ChiselBuildNode(
    chipyard_path=CHIPYARD_PATH,
    config=BUILD_CONFIG,
    config_package=BUILD_CONFIG_PACKAGE,
    target=BuildTarget.VERILATOR,
    make_jobs=CHISEL_BUILD_MAKE_JOBS,
    timeout_seconds=CHISEL_BUILD_TIMEOUT_SECONDS,
)
artifact = get(
    node.build.options(resources={"chipyard": CHISEL_BUILD_RESOURCE}).chia_remote(node)
)
```
`VerilatorRunNode().run` is dispatched similarly with `resources={"verilator_run": VERILATOR_RUN_RESOURCE}` and kwargs `plusargs={"+loadmem": riscv_name}`, `timeout_cycles=`, `timeout_seconds=`, `dramsim_ini_files=`.

**Prompts**: `prompts/implement.md` and `prompts/debug.md`, loaded in `llm.py` with a hand-rolled `${VAR}` substitution (NOT `str.format`, so Scala/MLIR braces survive):
```python
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

def _load_prompt(name: str, **subs: str) -> str:
    text = (PROMPTS_DIR / name).read_text()
    for key, val in subs.items():
        text = text.replace("${" + key + "}", val)
    return text

_IMPLEMENT_TASK = _load_prompt("implement.md", BUILD_CONFIG=BUILD_CONFIG,
    DATA_SIZE=str(DATA_SIZE), CHIPYARD_SRC_PATH=CHIPYARD_SRC_PATH)
```

**Agent/model config** — verbatim, `llm.py::make_llm` (the three backends):
```python
def make_llm(backend: str, chipyard_bash: BashTool):
    if backend == "antigravity":
        return AntigravityLLM(
            model=ANTIGRAVITY_MODEL,                 # default "gemini-3.1-pro-high"
            system_message=LLM_SYSTEM_MESSAGE,
            timeout_seconds=LLM_TIMEOUT_SECONDS,
            logging_name="memcpy_generator",
            resume_session=True,   # implement + every debug call share one conversation
        )
    if backend == "opencode":
        return OpenCodeLLM(
            model=OPENCODE_MODEL,                    # "provider/model", e.g. google-vertex/gemini-3.1-pro-preview
            system_message=LLM_SYSTEM_MESSAGE,
            timeout_seconds=LLM_TIMEOUT_SECONDS,
            logging_name="memcpy_generator",
            additional_providers=_opencode_providers(OPENCODE_MODEL),
            # Restrict opencode to ONLY the chipyard_bash MCP tool. Its built-in
            # write/edit/bash tools act on the opencode container's own FS, not
            # the chipyard container — deny all, allow just this MCP server.
            config={"*": "deny", f"{chipyard_bash.name}_*": "allow"},
        )
    return ClaudeCodeLLM(
        model=LLM_MODEL,                             # default "claude-opus-4-6"
        system_message=LLM_SYSTEM_MESSAGE,
        timeout_seconds=LLM_TIMEOUT_SECONDS,
        logging_name="memcpy_generator",
        resume_session=True,   # implement + every debug call share one session
        projects_cwd=None,     # derive from the llm worker's CWD
        extra_cli_args=list(LLM_EXTRA_CLI_ARGS),     # ["--effort", "max"]
    )
```
OpenCode Vertex provider block (`llm.py::_vertex_provider`):
```python
return AdditionalModelProvider(
    id="google-vertex",
    npm="@ai-sdk/google-vertex",
    name="Google Vertex AI",
    models=[model_id],
    options={"project": OPENCODE_VERTEX_PROJECT, "location": OPENCODE_VERTEX_LOCATION},
)
```

**How the LLM call is dispatched + how tools reach the agent** (`llm.py::_run_llm`):
```python
def _run_llm(llm, prompt: str, chipyard_bash: BashTool) -> QueryResult:
    if isinstance(llm, OpenCodeLLM):
        resources = {"opencode_creds": OPENCODE_RESOURCE}
    elif isinstance(llm, AntigravityLLM):
        resources = {"antigravity_creds": ANTIGRAVITY_RESOURCE}
    else:
        resources = {"llm": LLM_RESOURCE}
    return get(
        llm.prompt.options(resources=resources).chia_remote(llm, prompt, [chipyard_bash])
    )
```
The tools list (3rd arg to `prompt`) is a list of `ChiaTool` instances; the CLI on the llm container talks to those MCP servers (running on the chipyard container) over HTTP. Session persistence: reusing ONE `ClaudeCodeLLM` instance + `resume_session=True` makes each `get()` sync the transcript onto the instance (`@_session_tracked` wrapper mentioned in comments), so debug calls `--resume` the implement conversation. Antigravity does the same via `--conversation` (SQLite conversation db carried on the result). OpenCode calls are currently independent.

**Success / verification** (`helpers.py::classify_run`) — deterministic, no LLM:
```python
@dataclass
class Outcome:
    passed: bool          # design built AND memcpy test fully correct
    kind: str             # "pass" | "build_failure" | "runtime" | "timeout" | "incorrect"
    detail: str

def classify_run(run: RunResult) -> Outcome:
    combined = f"{run.log}\n{run.out}"
    if run.returncode is None or run.returncode < 0:
        return Outcome(False, "timeout", "simulation timed out (no clean exit)")
    if run.returncode != 0:
        return Outcome(False, "runtime", f"simulator exited with rc={run.returncode}")
    num_correct = _parse_num_correct(combined)   # regex r"MEMCPY Num Correct:\s*(\d+)"
    ...
    if num_correct == DATA_SIZE:
        return Outcome(True, "pass", f"{num_correct}/{DATA_SIZE} elements correct")
```
The C test prints `MEMCPY Num Correct: %d`; pass iff N == DATA_SIZE (100, kept in sync between `constants.py` and `memcpy.c`).

**Results/stats collection** (`helpers.py`): `Dumper(OUT_DIR)` writes every artifact to `out/` with a `%Y%m%d_%H%M%S_` filename prefix (`dump.text/.bytes/.json`); `dump_llm()` persists `success`, `usage`, `result`, and `stream_result` per LLM call as `<name>.md`; per-attempt chipyard git diffs captured by `@ChiaFunction collect_diff` (tracked + untracked via `git diff --no-index /dev/null <f>`, root + submodules); final `summary.json` = `{timestamp, config, llm_backend, attempts: [{attempt, build_success, kind, detail}...], status}`. State hygiene: `@ChiaFunction reset_chipyard` does `git checkout -- . && git clean -fd` at run start (containers are reused).

**Runtime env** (`constants.py`, critical for imports on workers):
```python
RUNTIME_ENV = {
    "working_dir": str(EXAMPLE_DIR),
    "py_modules": [str(_REPO_ROOT / "chia")],
    "excludes": ["out/", "__pycache__", ".mypy_cache"],
}
```
`working_dir` = the example dir so flat modules (`constants`, `helpers`, `llm`, `test_build`) import top-level on workers; `py_modules` ships the head's current `chia` package ahead of the image's baked install.

**Run commands** (README, verbatim):
```bash
chia up   examples/memcpy/cluster.yaml
chia job submit -- python "$(pwd)/examples/memcpy/memcpy_loop.py"   # run from the repo root
chia down examples/memcpy/cluster.yaml
# backend select:
chia job submit -- python "$(pwd)/examples/memcpy/memcpy_loop.py" --llm claude|opencode|antigravity
# env knobs go through the job runtime env (job does NOT inherit the shell):
chia job submit \
  --runtime-env-json '{"env_vars": {"MEMCPY_NUM_DEBUG_ATTEMPTS": "5"}}' \
  -- python "$(pwd)/examples/memcpy/memcpy_loop.py"
```
Absolute driver path is required (job entrypoint runs from $HOME). Do NOT pass `--working-dir` (conflicts with the loop's own RUNTIME_ENV).

**cluster.yaml** (memcpy) — 4 node types on `${THIS_MACHINE}` (`${THIS_MACHINE}`/`${USER}` filled in by `chia up`): `chisel_build` (`resources: {"chipyard": 1}`, image `ghcr.io/ucb-bar/chia-chisel-build:latest`, `worker_setup_commands: ["source /home/ray/chipyard/env.sh"]`), `verilator_run` (`{"verilator_run": 1}`, `ghcr.io/ucb-bar/chia-verilator-run:latest`), `llm` (`{"llm": 1}`, `ghcr.io/ucb-bar/chia-claude-code:latest`, mounts `-v ${HOME}/.claude:/home/ray/.claude`, creates `/home/ray/llm_env` as the CLI cwd), `opencode` (`{"opencode_creds": 1}`, `ghcr.io/ucb-bar/chia-opencode:latest`, mounts `${HOME}/.config/gcloud` + `GOOGLE_CLOUD_PROJECT` + `VERTEX_LOCATION=global`), `antigravity` (`{"antigravity_creds": 1}`, `ghcr.io/ucb-bar/chia-antigravity:latest`, mounts `${HOME}/.gemini`). Head: `head_env_commands: ["source ~/.bashrc && conda activate chia_env"]`; `head_start_ray_commands` runs `ray start --head --port=6379 --dashboard-port=8081 ...`.

---

## 4. Anatomy — `examples/circt_issue_solver`

**Two flows**, each = head driver + worker task module:
- Issue flow: `circt_issue_loop.py` (head: triage → fan-out → persist) → `issue_task.py::run_issue_remote` (worker: assess → reproduce → fix → verify → regression-repair → writeup).
- Review flow: `review_loop.py` (head: fetch PR feedback/diff from GitHub → fan-out → persist) → `review_task.py::run_review_round_remote` (worker: review_assess triage turn → reset → review/fix turn → verify → replies).

**Where the "loop" is defined**: again plain Python. Head fan-out with retry (verbatim, `circt_issue_loop.py`):
```python
    def _submit(c):
        return run_issue_remote.chia_remote(c.to_markdown(), c.number, CFG,
                                            resume=resume_by_num.get(c.number))

    tracked, tr_issue = [], {}
    for c in candidates:
        tr = TrackedRef(ref=_submit(c), submit_fn=(lambda c=c: _submit(c)),
                        label=f"issue_{c.number}")
        tracked.append(tr)
        tr_issue[id(tr)] = c

    pending = tracked
    try:
        while pending:
            done, pending = chia_wait(pending, num_returns=1,
                                      pending_timeout=PENDING_TIMEOUT_S, retry=True)
            for tr in done:
                issue = tr_issue[id(tr)]
                try:
                    _persist(issue, get(tr.ref))
                except Exception:
                    logger.exception("issue #%d failed", issue.number)
    finally:
        db.close_db()
```

**Config convention**: parameters are module-level globals in the driver, not env vars ("Parameters — globals, not env vars (project convention). GITHUB_TOKEN is the one exception: a secret"). Everything the worker needs is packed into a plain `CFG` dict — including the *prompt text read at head side* — because the worker module "MUST NOT import head-only modules (db / triage) or read files at import time — all config arrives in the `cfg` dict":
```python
_P = FLOW_DIR / "prompts"
CFG = {
    "tag": CIRCT_TAG, "tool_targets": TOOL_TARGETS, "repro_dir": REPRO_DIR,
    "repro_path": REPRO_PATH, "require_repro": REQUIRE_REPRO,
    "backend": LLM_BACKEND, "model": LLM_MODEL,
    "vertex": {"project": OPENCODE_VERTEX_PROJECT, "location": OPENCODE_VERTEX_LOCATION},
    "build_jobs": BUILD_JOBS, "timeouts": TIMEOUTS,
    "system_prompt":  (_P / "system.md").read_text(),
    "assess_prompt":  (_P / "assess.md").read_text(),
    "repro_prompt":   (_P / "reproduce.md").read_text(),
    "fix_prompt":     (_P / "fix.md").read_text(),
    "regression_prompt": (_P / "regression.md").read_text(),
    "writeup_prompt": (_P / "writeup.md").read_text(),
}
```
Key globals: `TOOL_TARGETS = ("circt-opt", "firtool", "circt-translate", "arcilator", "circt-lec", "circt-bmc")`, `REPRO_PATH = "/workspace/circt/.circtissues/repro.sh"`, `MAX_ISSUES=20`, `TRIAGE_POOL=2000`, `BUILD_JOBS=16`, `TIMEOUTS = {"assess": 1800, "repro": 1800, "fix": 7200, "regression": 3600, "writeup": 1200}`, `PENDING_TIMEOUT_S=1800`, `LLM_MODEL="claude-opus-4-6"`, `ANTIGRAVITY_MODEL="gemini-3.1-pro-high"`, `OPENCODE_MODEL="google-vertex/gemini-3.1-pro-preview"`.

**py_modules shipping** (so worker code updates need no image rebuild):
```python
_CHIA_PKG = FLOW_DIR.parent.parent / "chia"
_PY_MODULES = [str(FLOW_DIR / "circt_util.py"),
               str(FLOW_DIR / "issue_task.py"),
               str(_CHIA_PKG)]
ray.init(address="auto",
         runtime_env={"py_modules": _PY_MODULES,
                      "excludes": ["**/__pycache__", "**/*.pyc"]},
         logging_level=logging.WARNING)
```

**The per-issue node definition** (verbatim head of `issue_task.py`):
```python
@ChiaFunction(resources={"circt": 1})
def run_issue_remote(issue_md: str, number: int, cfg: dict,
                     resume: dict | None = None, assess_only: bool = False) -> dict:
```
Inside it, tools are created pinned to *this* worker node via NodeAffinity, and each LLM phase is a **fresh, stateless** `claude --print` session (context is inlined into each prompt, no `--resume` across phases):
```python
    node = ray.get_runtime_context().get_node_id()
    here = {"scheduling_strategy": NodeAffinitySchedulingStrategy(node_id=node, soft=False)}
    ...
        bash = BashTool(name=f"bash_{number}", work_dir=circt_util._CIRCT_SOURCE_TREE,
                        task_options=here, timeout_seconds=300)
        build = BuildTool(name=f"build_{number}", num_cpus=cfg["build_jobs"], task_options=here)
        lit = LitTool(name=f"lit_{number}", task_options=here)
        agent_tools = [bash, build, lit]
```
(`BuildTool`/`LitTool` come from `chia.chipyard.circt` — async: agent calls build/run_lit which return immediately, then polls `build_status`/`lit_status` until `done=true`. Bash is capped at 300 s per call precisely to force long work through the async tools.)

**The per-phase LLM turn** (verbatim `_turn`, Claude branch — the agent/model config for this example):
```python
        else:
            llm = ClaudeCodeLLM(
                model=cfg["model"], system_message=cfg["system_prompt"],
                timeout_seconds=cfg["timeouts"][phase],
                extra_cli_args=["--effort", "max"],
                resume_session=True, projects_cwd=None,
            )
        cli = get(llm.prompt.options(resources={"llm": 1.0}).chia_remote(llm, prompt, tools))
        transcript = getattr(cli, "session_transcript", None) or b""
        logs[phase] = {
            "result": cli.result, "stream": cli.stream_result,
            "stderr": cli.stderr, "success": bool(getattr(cli, "success", False)),
            "transcript": transcript if isinstance(transcript, (bytes, bytearray)) else b"",
            "transcript_ext": "db" if backend == "antigravity" else "jsonl",
            "usage": getattr(cli, "usage", None),
        }
```
Antigravity branch: `AntigravityLLM(model=cfg["model"], system_message=cfg["system_prompt"], timeout_seconds=cfg["timeouts"][phase], resume_session=True)` (comment: "`agy --print --output-format stream-json`; the system prompt is folded into the user message and effort rides on the model id"; `resume_session=True` only so the SQLite conversation db comes back for logging — a new LLM per phase, nothing is actually resumed). OpenCode branch builds `AdditionalModelProvider(id="google-vertex", npm="@ai-sdk/google-vertex", ...)` and `perms = {"*": "deny", **{f"{t.name}_*": "allow" for t in tools}}` passed as `config=perms`.

**Prompt substitution** (worker side): `string.Template.safe_substitute` with `$var` placeholders (`$issue`, `$repro`, `$diff`, `$failures`, `$failure_log`, `$verdict`, `$pr`, `$review`, `$actionable`) — "Template/safe_substitute (not str.format) so MLIR/shell braces in the prompts and issue body don't blow up substitution."

**Gating between phases via parsed footers**: each decision prompt forces an exact machine-readable footer, parsed with a regex, defaulting to "proceed" if unparseable. `assess.md` ends with `DECISION: CLEAR | NOT_A_BUG | UNCLEAR` (+ `BUG:`/`EXPECTED:`/`REASON:` lines); parser `_assess_decision` regex: `r"(?im)^\s*DECISION:\s*(CLEAR|UNCLEAR|NOT[_ ]?A[_ ]?BUG)\b"`. `review_assess.md` ends with `DECISION: ACTIONABLE | NO_CHANGES` (+ `ACTIONABLE:` summary line that is "the ONLY context that carries forward").

**Success / verification** — deterministic, no LLM (`issue_task.py`):
```python
        def _verify():
            diff = circt_util.circt_capture_diff(cfg["tag"])
            rebuild = circt_util.circt_ninja_build(cfg["tool_targets"], num_cpus=cfg["build_jobs"])
            repro_after = circt_util.circt_run_script(cfg["repro_path"])
            repro_fixed = rebuild["success"] and repro_after["exit_code"] == 0
            lit_res = circt_util.circt_run_lit(tuple(tps), filter_out=circt_util._LIT_GATE_FILTER_OUT)
            return diff, rebuild, repro_after, repro_fixed, lit_res
```
Repro contract (enforced by `reproduce.md` + `circt_run_script`): **`repro.sh` MUST exit 0 iff the bug is FIXED** — the same script gates reproduction (nonzero on clean tree → else `no_repro`) and the fix (zero after patch). Regression gate = whole lit suite minus baseline-red dirs (`_LIT_GATE_EXCLUDE_DIRS = ("CAPI",)`, `_LIT_GATE_FILTER_OUT = "circt-tblgen"`). If repro green but lit red → one `regression` turn with failing tests + focused log inlined, then re-verify. Final `status = "fixed" if (repro_fixed and lit_res["success"]) else "attempted"`; other statuses: `not_a_bug`, `unclear`, `no_repro`, `error`.

**Worker git/state helpers** (`circt_util.py`, all `@ChiaFunction(resources={"circt": 1})`): `circt_trust_source` (git safe.directory), `circt_git_reset(ref)` (`git reset --hard` + `git clean -fd`, NOT `-x` so the warm build survives), `circt_apply_diff(diff_text)`, `circt_write_files({relpath: content}, base_dir)` (`.sh` chmod 755), `circt_run_script(path) -> {exit_code, log_tail, timed_out}`, `circt_capture_diff(ref) -> {diff, files, added, removed}`. Re-exports `_CIRCT_SOURCE_TREE`, `circt_ninja_build`, `circt_run_lit`, `circt_warm_build` from `chia.chipyard.circt`.

**Results/stats collection**: head `_persist()` writes `issue_logs/issue_<N>/` containing `issue.md`, `fix.diff`, `pr_writeup.md`, `verdict.json` (status/reproduced/build_ok/fixed/lit_* /added/removed/test_paths/notes + per-phase `llm_usage`), per-phase `llm_<phase>.md` (stream transcript), `llm_<phase>.stderr`, raw session transcript `llm_<phase>.jsonl` (Claude) or `.db` (Antigravity SQLite), `repro/` (the agent's `.circtissues` artifacts, files ≤256 KB), `verify_build.log`, `verify_repro.log`, `verify_lit.log`; plus one row in `issues.db` via `db.py` (`SQLiteNode(path, pin_to_current_node=True)`, `attempts` table — schema in db.py; `db.attempted_numbers()` feeds triage dedup). Review flow persists to `review_logs/issue_<N>_pr_<M>/` (`review_feedback.md`, `replies.md`, `updated.diff`, `verdict.json`, `llm_*.md/.jsonl`, `verify_*.log`).

**Triage** (`triage.py`, head-only): `GithubIssuesNode(repo, state="open").recent(n=pool, fetch_comments=False)`, regex filters (feature-request titles out; requires a fenced code block + a tool-command or crash-signal regex), drops already-attempted and issues with an open PR (`node.linked_pull_requests(issue.number, open_only=True)`), random shuffle, re-fetch survivors with comments via `node.get_issue(number)`.

**Run commands** (verbatim, README + env.yml):
```bash
conda env create -f env.yml          # first time  (name: circtissues; python 3.10.19; ray[default]==2.54.0; pip -e ../..)
conda activate circtissues
export GITHUB_TOKEN=...               # read access to GITHUB_REPO
export CHIA_HEAD=$(hostname)          # the host to bring the cluster up on

chia up cluster.yaml                  # 2 LLM + 2 CIRCT containers on one host

# Issue flow (submit as a job so driver logs show in the dashboard):
./fix_issues_submit.sh --max-issues 2
./fix_issues_submit.sh --issue 10568             # one specific issue, skip triage
NO_WAIT=1 ./fix_issues_submit.sh --max-issues 5  # detach; watch the dashboard

# Review flow (PR number : paired issue number):
./review_submit.sh --pr 10648:7388

chia down cluster.yaml
```
`fix_issues_submit.sh` is a thin wrapper: `exec chia job submit --address http://localhost:8265 [--no-wait] --runtime-env-json '{"env_vars": {"GITHUB_TOKEN": "...", "GOOGLE_CLOUD_PROJECT": "..."}}' -- python "$FLOW_DIR/circt_issue_loop.py" "$@"`. Other driver flags: `--backend {claude,antigravity,opencode}` (`--antigravity` alias), `--model <id>`, `--vertex-project/--vertex-location`, `--assess-only N`, `--replay-regression N`.

**cluster.yaml** (circt, Claude variant): 2 node types — `circt_llm` (`resources: {"llm": 2}` → 2 concurrent prompts per container, `min/max_workers: 2`, image `ghcr.io/ucb-bar/chia-claude-code:latest`, mounts `~/.claude`, run_setup copies `.claude.json` and sets `skipDangerousModePermissionPrompt: true` in settings.json) and `circt_worker` (`{"circt": 1}` each, ×2, image `ghcr.io/ucb-bar/chia-circt:latest`, pinned at firtool-1.148.0, git identity + safe.directory + `pip install lit` in run_setup). Host from `${CHIA_HEAD}` env; `head_setup_commands: conda activate circtissues`. `cluster_antigravity.yaml` and `cluster_opencode_vertex.yaml` are identical except the llm image (`chia-antigravity` mounting `~/.gemini`; `chia-opencode` mounting `~/.config/gcloud` + `GOOGLE_CLOUD_PROJECT` + `VERTEX_LOCATION=global`). Note the **resource name `llm` stays the same across backends** in this example (unlike memcpy which uses distinct `opencode_creds`/`antigravity_creds` tokens so all three can coexist in one cluster).

---

## 5. Antigravity / OpenCode / Gemini specifics (as configured in the examples)

- `AntigravityLLM` (`chia/models/antigravity.py`): drives Google's Antigravity CLI `agy` with `--print --output-format stream-json`. No API key path — OAuth state in `~/.gemini` mounted into the container (`agy` sign-in on host first). Effort tier rides on the model id suffix (`gemini-3.1-pro-high`); system prompt is folded into the user message. Gemini Pro is served ONLY from the `global` location — `~/.gemini/antigravity-cli/settings.json` needs `"gcp": {"location": "global"}` or agy fails with "Selected model is not supported in the selected location". `resume_session=True` → one conversation resumed via `--conversation`, transcript = SQLite `.db` carried on the result.
- `OpenCodeLLM` (`chia/models/opencode.py`): provider-agnostic (`provider/model` ids like `anthropic/claude-opus-4-6`, `openai/gpt-5`, `google-vertex/gemini-3.1-pro-preview`); `additional_providers=[AdditionalModelProvider(...)]` (re)declares a provider to pin options (Vertex project/location) and register models opencode's catalog may lack; `config={"*": "deny", "<toolname>_*": "allow"}` is opencode's permission block used to disable its built-in file/bash tools (they'd act on the LLM container's FS, not the target container). Vertex auth = Google ADC mounted (`gcloud auth application-default login` + `set-quota-project`), `GOOGLE_CLOUD_PROJECT` forwarded through cluster yaml AND the job runtime env. Session persistence "in development" — each call independent.
- `ClaudeCodeLLM` (`chia/models/claude.py`): `model`, `system_message`, `timeout_seconds`, `logging_name`, `resume_session` (session threading via `@_session_tracked`), `projects_cwd` (None → derive from worker CWD), `extra_cli_args` (e.g. `["--effort", "max"]`). Credentials = host `~/.claude` mounted; `settings.json` must have accepted the bypass-permissions disclaimer (circt cluster sets `skipDangerousModePermissionPrompt=True` in run_setup_commands).

---

## 6. Conventions to copy for a new example

1. **Directory shape**: `examples/<name>/` containing `README.md` (flow diagram, components table, tunables table, run commands), `<name>_loop.py` (head driver, plain-Python loop), `cluster.yaml` (+ one `cluster_<backend>.yaml` per alternative backend), `prompts/*.md` (one file per LLM phase; `system.md` if there's a shared system prompt), `constants.py` OR driver-global params, optional `helpers.py` / `llm.py` / `<task>.py` worker modules, `env.yml` (conda env with `pip -e ../..`), `.gitignore` for `out|*_logs|*.db`, `__init__.py` only if imported as a package. Shared collateral goes in `examples/common/` (e.g. `common_nodes.py`, `dramsim_ini/`).
2. **Two config styles exist**: memcpy uses `constants.py` with every knob `MEMCPY_*`-env-overridable (`os.environ.get("MEMCPY_X", default)`); circt uses module-level globals in the driver + a `CFG` dict passed to workers ("globals, not env vars" per its own comment; secrets like GITHUB_TOKEN are the only env vars, forwarded via `--runtime-env-json {"env_vars": ...}`). Pick one; both are canon.
3. **Head/worker split**: head driver does `ray.init(address="auto", runtime_env={...})`; ship the example's flat modules via `working_dir` (memcpy style) or ship specific worker `.py` files + the `chia` package via `py_modules` (circt style). Worker task modules must not import head-only modules or read files at import time — pass prompts/config in a dict.
4. **Nodes**: `@ChiaFunction(resources={"<container-token>": frac})` for custom nodes; prebuilt nodes from `chia.chipyard.*` / `chia.github.*` / `chia.database.*`; dispatch always `get(fn.options(resources={...}).chia_remote(...))`. Never-raise contract: nodes return result dataclasses/dicts with `success`/`returncode`; the driver branches.
5. **Tools for the agent**: instantiate `BashTool(name=..., work_dir=<target tree>, timeout_seconds=..., task_options=<resources or NodeAffinity>)` (+ async `BuildTool`/`LitTool`-style tools for long ops); pass them as the list argument to `llm.prompt`; MCP tool names are `f"{name}_<method>"`; call `.stop()` in a `finally`. For OpenCode, deny built-ins: `config={"*": "deny", f"{tool.name}_*": "allow"}`.
6. **LLM dispatch**: build the backend object (ClaudeCodeLLM/AntigravityLLM/OpenCodeLLM), dispatch `llm.prompt` onto the credential-holding container's resource (`{"llm": 1.0}` etc.). Choose per run via a `--llm`/`--backend` argparse flag with per-backend default models. One reused instance + `resume_session=True` = threaded session (Claude/Antigravity); fresh instance per phase = stateless phases with context inlined.
7. **Prompts**: markdown files with placeholders; substitute with `string.Template.safe_substitute` (`$var`) or manual `${VAR}` replace — never `str.format` (code braces). Decision phases end with an exact `DECISION:` footer parsed by regex, defaulting to the safe branch.
8. **Verification is deterministic code, never the LLM**: a parseable success line (memcpy: `MEMCPY Num Correct: N`), an exit-0-iff-fixed repro script, and/or a test-suite gate; classify into a small closed status set (`passed/build_failed/...`, `fixed/attempted/no_repro/unclear/not_a_bug/error`).
9. **Persistence**: timestamped flat files in `out/` (memcpy Dumper) or per-item artifact dirs `*_logs/<item>/` + a `SQLiteNode` DB on the head (circt). Always save: per-phase LLM `result` + `stream_result` + raw `session_transcript`, `usage`, diffs (+/- counts), verify logs, and a machine-readable `verdict.json`/`summary.json`.
10. **State hygiene**: containers are reused — reset the working tree at the start of every run (git checkout/clean or reset --hard + clean -fd, preserving warm gitignored build dirs); capture diffs read-only (untracked via `git diff --no-index`).
11. **Cluster yaml**: one docker node type per concern, each advertising a custom resource token; images from `ghcr.io/ucb-bar/chia-*:latest`; credentials mounted from the host home (`~/.claude`, `~/.gemini`, `~/.config/gcloud`); `${THIS_MACHINE}`/`${CHIA_HEAD}`/`${USER}` placeholders; standard `head_start_ray_commands` (`ray start --head --port=6379 ...`) and `worker_start_ray_commands` (`ray start --address=$RAY_HEAD_IP:6379 ...`).
12. **Launch**: `chia up <cluster.yaml>` → `chia job submit [--runtime-env-json ...] -- python "<ABSOLUTE path>/loop.py" [flags]` (or a `*_submit.sh` wrapper that injects secrets) → `chia down <cluster.yaml>`. Absolute driver path; env for the job goes through `--runtime-env-json env_vars`, not the shell.

## SOURCES
https://api.github.com/repos/ucb-bar/chia/git/trees/main?recursive=1
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/README.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/memcpy_loop.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/llm.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/constants.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/helpers.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/test_build.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/cluster.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/memcpy.c
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/__init__.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/prompts/implement.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/memcpy/prompts/debug.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/README.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/circt_issue_loop.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/issue_task.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/circt_util.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/review_loop.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/review_task.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/triage.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/db.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/config.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/env.yml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/.gitignore
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/fix_issues_submit.sh
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/review_submit.sh
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/cluster.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/cluster_antigravity.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/cluster_opencode_vertex.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/system.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/assess.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/reproduce.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/fix.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/regression.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/writeup.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/review.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/circt_issue_solver/prompts/review_assess.md
https://raw.githubusercontent.com/ucb-bar/chia/main/chia/base/tools/BashTool.py
https://raw.githubusercontent.com/ucb-bar/chia/main/chia/base/llm_call.py
https://api.github.com/repos/ucb-bar/chia

## CAVEATS
All files in both example directories were fetched from raw.githubusercontent.com at main and read in full; every quoted snippet is verbatim. Caveats: (1) I did NOT fetch https://docs.chialoops.ai or the full sources of chia/models/claude.py, chia/models/antigravity.py, chia/models/opencode.py, chia/base/ChiaFunction.py, or chia/chipyard/circt.py — statements about ClaudeCodeLLM/AntigravityLLM/OpenCodeLLM constructor args, @_session_tracked, chia_remote/options semantics, and BuildTool/LitTool async polling are taken from how the examples call them plus the examples' own in-code comments (all constructor kwargs quoted are exactly as used in the examples, so they are real); if you need the full parameter lists of those classes, fetch chia/models/*.py and chia/base/ChiaFunction.py (paths and sizes confirmed in the repo tree listing in the report). (2) chia/base/tools/BashTool.py and chia/base/llm_call.py WERE fetched in full, so QueryResult fields and the "{name}_run_command" MCP naming are verified. (3) The GitHub tree API returned truncated:false, so the file listings are complete for the commit at fetch time (main tree sha 16c35e92aaaf9511c6453bf94cd5cf589698f4e3); the repo may move. (4) examples/memcpy/__init__.py is genuinely empty (0 bytes). (5) The 'run/launch' commands are quoted from the example READMEs and submit scripts; I did not execute chia or bring up any cluster.