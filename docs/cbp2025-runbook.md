# Running the loop against the CBP2025 host

Every command here was run on the live cluster on 2026-09-22. The timings
are measured, not estimated. Read `hosts/cbp2025/NOTES.md` for what the host
itself looks like, and `docs/stages.md` for what each stage owes the next.

## What the cluster has to look like

```bash
cd ~/chia-hackathon/paper-to-pipeline
source export.sh
chia up cluster/cluster.yaml          # or: chia up --add cluster/cluster.yaml
ray status
```

Four resource tokens have to appear, and each one means a node can do a
particular job.

| token | count | held by | used for |
| --- | --- | --- | --- |
| `cbp2025_host` | 4 | one sim worker | the agent's shell, every build, every test command |
| `cbp2025` | 4 | both sim workers | one `./cbp` process per trace |
| `antigravity_creds` | 2 | a container on the head | every LLM call |
| `evolver` | 2 | the head | the stage 4 search actor |

A missing token does not fail. It hangs. Ray queues the task and waits for a
node that never arrives. Read `ray status` before you submit anything.

Two failure modes have cost real time here. Both are worth knowing.

- A worker that will not join, and reports a timeout during startup plus
  an overloaded GCS, is usually holding its own pinned object-manager port
  from a bring-up that failed part-way. `ray stop` returns before the
  raylet releases it. `worker_start_ray_commands` now waits for port 16801
  to clear.
- A worker with no traces scores every candidate the same and looks
  healthy. The setup commands end with a `test -f` on a real training trace
  for that reason.

## Stage by stage

Run them one at a time first. Each writes artifacts under `out/` with a
timestamp prefix, and each is restartable because the stage before it left
its output on disk.

### Inputs, once

```bash
scripts/fetch_artifacts.sh            # the RUNLTS paper and the kit
agy                                   # sign in to the Gemini CLI on the head
./scripts/install_llm_gateway.sh      # only stage 4 needs this
```

`scripts/fetch_artifacts.sh` also clones the kit to `third_party/cbp2025`.
Stage 2 needs that clone. The deterministic plan checks open the files a
hook point names, they run on the head, and the real checkout is on a
worker. If the two are at different commits, stage 2 refuses to run.

### 1. Distill, about 30 minutes

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage distill
```

Writes `spec/sr.paper_only.json`. Stage 1.5 review is on by default and is
most of the cost. `P2P_SPEC_REVIEW=0` turns it off.

### 2. Baseline, about 1 minute

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage baseline --host cbp2025
```

Builds the pristine kit and runs `experiments/smoke-2.list`, then writes
`hosts/cbp2025/baselines/iso-192KiB.json`. That file is what G2 holds every
port to. It holds the suite aggregate plus a `per_trace` map, because a
`feature_off_baseline` entry runs one `./cbp` command and needs one trace's
numbers to compare against.

Point `--baseline-list` at a bigger list to record more. G2 can only use a
trace that one shell command finishes inside the agent's 300-second cap.

Baselines are stored per `--budget` name, and every later stage reads the
one for the budget it is given. The kit's default host is a 64 KiB-class
TAGE-SC-L (524,615 bits). So it is a fair baseline for `iso-64KiB`, and not
for `iso-192KiB`. Record the `iso-64KiB` one with
`--stage baseline --budget iso-64KiB`.

### 3. Plan, about 6 minutes

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage plan --host cbp2025
```

Writes `plan/sr.cbp2025.plan.json` and `plan/sr.cbp2025.tests.json`. An
unmapped spec item stops the stage from writing either file. A failure here is therefore a report
about coverage, not a crash. `out/*_plan_cbp2025_rounds.json` lists what
each turn got wrong.

The stage resets the host checkout before and after the planning agent runs.
Read `hosts/cbp2025/adapter.py:restore_checkout` for why.

### 4. Integrate, 20 minutes to 3 hours

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage integrate --host cbp2025
```

The agent gets a shell on a fresh copy of the checkout at `~/cbp2025_port`
and works the plan. After each turn, `plan_runner` executes the test plan
and `gate.py` judges it. Six attempts by default
(`P2P_INTEGRATION_ATTEMPTS`).

One gate attempt costs about 8 minutes with `experiments/perf-4.list`: 20
seconds to build, 3 minutes of correctness commands, 30 seconds of smoke,
and 4 minutes of performance traces. `perf-8.list` costs about 16 minutes
more per attempt.

Artifacts: `out/*_gate_cbp2025_<n>.json` per attempt,
`out/*_integrate_cbp2025_<n>.md` per LLM turn, and
`out/*_integrate_cbp2025_diff.patch` at the end.

To resume a run that died partway, set `P2P_CBP2025_PORT_FRESH=0` so the
agent picks up the tree it left.

That happens. One run stopped an hour in on
`RESOURCE_EXHAUSTED (code 429)` from Vertex, after seven retries, with the
port most of the way written. The 429 is a quota on the model, not a fault
in the loop, and `gemini-3.1-pro-high` is the tier most likely to hit it.
Stage 3 records the failure as `backend_error` with the resume instruction
and leaves the tree alone. Resume it, or drop to
`P2P_ANTIGRAVITY_MODEL=gemini-3.8-flash-high`, which has far more headroom.

Since 2026-09-23, every stage waits out a 429 before it gives up.
`llm.run_llm` re-sends the call up to 6 times, after 1, 2, 4, 8, 15 and 15
minutes. The job log shows each wait as `rate-limited (429)`. A quota that
stays spent past that still stops the stage. `P2P_LLM_RATE_LIMIT_RETRIES`
and `P2P_LLM_RATE_LIMIT_BACKOFF` change the count and the first wait.

### 5. Tune, hours to days

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage dse --host cbp2025 --budget iso-64KiB
```

Needs the LLM gateway and `evolve-flows` (see `docs/dse-setup.md`). The
search mutates `sr_params.h` in the ported tree, so stage 3 has to run
first.

You do not pass the gateway's address or token. A Ray job does not get the
submitting shell's environment. So the job's driver reads both from
`~/.config/p2p/gateway.env` on the head. Then it forwards them to the search.
Before any build, the stage sends one small request to every model the
search config names. If one fails, the stage stops with `llm_unreachable`
and names the model and the reason. A search that ends with only its seed
program scored ends as `no_candidates`. Either way the job exits non-zero.

The search config sets the size. `P2P_DSE_CONFIG` picks it, and it has to
travel through `--runtime-env-json`:

| config | iterations | time on this cluster |
| --- | --- | --- |
| `config_adaevolve_smoke_vertex.yaml` | 3 | about 40 minutes |
| `config_adaevolve_medium_vertex.yaml` | 24 | about 4 to 6 hours on `perf-8.list` |
| `config_adaevolve.yaml` (default) | 250 | days, and it needs more trace workers |

`--screening-list` picks the traces each candidate is scored on. The
default is the 60-trace screening set, which costs about fifteen times
`perf-4.list`. Report both numbers with any result. A winner screened on
four traces is a winner on four traces.

The search runs in `~/cbp2025_dse`. The stage copies the ported tree there
as it starts. The evolver overwrites `sr_params.h` on every iteration,
and the port the gate promoted has to stay on disk as the gate saw it.

### 6. Promote, about 2.5 hours

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage promote --host cbp2025 --budget iso-64KiB \
  --promote-from "$(pwd)/out/<run>_summary.json"
```

The search picks its winners on a few traces. Promotion scores the top 3
again on `experiments/promote-16.list`: 16 training traces that are in
neither screening list. The same job runs two references on the same
traces: the kit's default host, and the port with every knob at its
default. That is 5 runs of about 30 minutes each on 4 trace slots.

The result is `out/<run>_promote_cbp2025.json`. Its `verdict` names the
winner and says whether it beats each reference. `vs_baseline` and
`vs_defaults` give the change in each metric, and how many traces went
each way. Report both.

Where the finalists come from:

- **In the same job as the search.** Add `promote` to `--stage`, for
  example `--stage dse promote`. No `--promote-from` is needed.
- **After a finished search.** `--promote-from` takes that job's
  `summary.json`, or an adaevolve output directory that holds
  `checkpoints/`. A search run before promotion existed has no population in
  its summary, so point at its checkpoints instead. They sit under
  `/tmp/ray/session_latest` on the node that ran the evolver, and a Ray
  restart deletes them, so copy them out first.

What the stage refuses, and why:

- A candidate is a finalist only if screening built and scored it, and its
  header still passes every static constraint. The same knob values count
  once. The defaults are never a finalist, because they run anyway.
- It uses the plan in force and the port on disk. Both must be the ones the
  search ran with. Otherwise every header fails the static check, and the
  stage stops with `no_finalists`.
- It will not start while a search is running, because both use
  `~/cbp2025_dse`. It also resets the pristine checkout `~/cbp2025`, as the
  baseline stage does.
- Every variant must run every trace, or its mean is about other traces.
  If a reference or every finalist misses one, the job exits non-zero.

`P2P_DSE_TOP_K` changes the number of finalists. `--promote-list` changes
the traces.

### Several stages in one submission

`--stage` takes more than one stage, and runs them in pipeline order.
Stages 2 to 4 against the spec already on disk:

```bash
chia job submit \
  --runtime-env-json "{\"env_vars\": {\"P2P_DSE_CONFIG\": \"$(pwd)/experiments/config_adaevolve_medium_vertex.yaml\"}}" \
  -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage plan integrate dse --host cbp2025 --budget iso-64KiB \
  --screening-list "$(pwd)/experiments/perf-8.list"
```

`--stage all` is every stage, distill included. Distill rewrites
`spec/sr.paper_only.json`, so do not use `all` to re-run the later stages
over a spec that was refined by hand.

When a job runs integrate, stage 4 only runs for a host the gate promoted.
Spending a search on a refused port measures how a broken feature responds
to its parameters. When stage 4 is in the job, the LLM check also runs at
the start. Then a dead gateway stops the job before planning, not after it.

## Three cheap questions before a long run

Three scripts answer three questions in minutes rather than hours. None of
them is collected by pytest, because each needs a live cluster.

```bash
# Does the host node build and fan out at all? No LLM.
chia job submit -- python "$(pwd)/loop/tests/cbp2025_cluster_smoke.py" --traces 2

# Can the LLM reach the checkout through the MCP shell? One prompt.
chia job submit -- python "$(pwd)/loop/tests/llm_cluster_smoke.py"

# Does the real gate behave against a tree with no port in it? 50 seconds.
chia job submit -- python "$(pwd)/loop/tests/cbp2025_gate_smoke.py" --skip-performance
```

The third one is the important one, and its expected result is a specific
failure. G1, G2 and G4 must pass, because an unported tree is the baseline.
Every `spec_unit_test` must fail, because the test file does not exist until
the integration agent writes it. G5 must fail, because there is no feature.
Anything else is a fault in this machinery rather than in a port.

That script found a real one. Stage 2's planner left a `test_sr.cc`
printing "Test passed" in the checkout while it worked out a compile
command. The port tree was a copy of that checkout. All seven unit tests
then passed against a tree nobody had ported into.

## When stage 3 escalates

The agent sometimes refuses a value it is not allowed to change. Stage 3
then returns `needs_replan`. That is not a failure of the run. It is the one message
that travels backwards through the loop, and the answer is to run stage 2
again:

```bash
cat plan/sr.cbp2025.plan.escalations.json      # what it refused, and why
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage plan --host cbp2025                  # reads them, answers them
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage integrate --host cbp2025
```

Stage 2 inlines every unresolved escalation into the planner prompt and
marks it answered by the plan it writes. This loop raised two escalations so far. Both
were correct, and both traced back to a wrong fact in
`hosts/cbp2025/NOTES.md` rather than to the agent. Read the escalation
first. Correct the notes where that is the real fault.

Add `P2P_CBP2025_PORT_FRESH=0` to the integrate step to carry the port
forward instead of starting over. Carry it forward for a re-plan that
changed the measurement. Start over for one that changed the design.

## Knobs worth knowing

| variable | default | what it changes |
| --- | --- | --- |
| `P2P_HOSTS` | `cbp2025` | which hosts a stage loops over |
| `P2P_LLM_BACKEND` | `antigravity` | the backend whose spend lands on the GCP budget |
| `P2P_ANTIGRAVITY_MODEL` | `gemini-3.1-pro-high` | `agy models` lists what the account can see |
| `P2P_INTEGRATION_ATTEMPTS` | 6 | gate attempts before stage 3 gives up |
| `P2P_CBP2025_PORT_FRESH` | 1 | 0 resumes a stage 3 run on the tree it left |
| `P2P_SPEC_REVIEW` | 1 | 0 skips stage 1.5, which is most of distill's cost |
| `P2P_DSE_CONFIG` | the 250-iteration config | the smoke config runs 3, the medium one 24 |
| `P2P_DSE_TOP_K` | 3 | how many finalists the promote stage scores again |

`--screening-list` and `--baseline-list` are command-line flags rather than
environment variables, so they go after the script name.

Pass them through `chia job submit --runtime-env-json '{"env_vars": {...}}'`.
Exporting them in the submitting shell does not reach the job.
