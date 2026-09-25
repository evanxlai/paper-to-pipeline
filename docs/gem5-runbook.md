# Running the loop against the gem5 host

This runbook brings up the gem5 host and runs stages 2 and 3 on it. The
lead ran steps 3, 5, 6 and 7 on the real cluster on 2026-09-23, and their
timings come from that run. Step 5 also runs the install of step 4. Steps
1, 2, 4, 8 and 9 have no measured timing yet, and each one says
TODO(measured).

The only gem5 baseline is `hosts/gem5/baselines/iso-64KiB.json`. So every
gem5 command below that reads a baseline names `--budget iso-64KiB`. The
driver's default budget, `iso-192KiB`, has no gem5 baseline file.

Read `hosts/gem5/NOTES.md` for the host itself. Read `docs/stages.md` for
what each stage owes the next. The CBP2025 twin of this file is
`docs/cbp2025-runbook.md`.

## The host in one paragraph

The host is gem5 v25.1.0.0, ARM, in syscall emulation mode. Its branch
predictor is `TAGE_SC_L_64KB`. One node holds everything: the pristine
checkout `~/gem5`, the port tree `~/gem5_port`, the run scripts and the
workloads in `~/p2p_gem5`. A gem5 binary stays on the node that built it, so
the shell, every build and every run ask for the same token.

## What the cluster must look like

```bash
cd ~/chia-hackathon/paper-to-pipeline
source export.sh
ray status
```

These tokens must appear for a gem5 run.

| token | count | held by | used for |
| --- | --- | --- | --- |
| `gem5_host` | 30 | the one `gem5_node` machine | the agent's shell, every build, every workload run |
| `antigravity_creds` | 2 | a container on the head | every LLM call |

A missing token does not fail. It hangs. Ray queues the task and waits for a
node that never arrives. Read `ray status` before you submit anything.

The node is one `c2d-standard-32` with a 300 GB disk and Ubuntu 22.04. It
advertises 30 run slots on 32 vCPUs. Each gem5 run is one process on one
core, and two cores stay free for the shell and the raylet.

Do not use chia's default `gem5` token. The old `host_worker` still
advertises it until the next full bring-up. A task that asks for it can land
on a node with no gem5 on it.

## Order of operations

Run the steps in this order. Each step needs the step before it.

1. Build the workloads on the head.
2. Add the gem5 node to the cluster.
3. Build the pristine checkout.
4. Install the run directory on the node.
5. Run the cluster smoke.
6. Record the baseline.
7. Run the gate smoke.
8. Plan with `--host gem5`.
9. Integrate with `--host gem5`.

### 1. Build the workloads, TODO(measured)

```bash
scripts/build_gem5_workloads.sh
```

The script builds each workload as a static aarch64 Linux binary with the
head's cross compiler. Then it runs each one under `qemu-aarch64-static` as
a first check. The output goes to `third_party/gem5_workloads/`, which git
ignores. `hosts/gem5/workloads.json` names every workload and its arguments.

The adapter packs this directory into the payload for step 4. If the
directory is missing, step 4 stops and names this script.

### 2. Add the gem5 node, TODO(measured)

```bash
PATH="$(pwd)/cluster/sshwrap:$PATH" chia up cluster/cluster.yaml
ray status
```

Plain `chia up`, not `chia up --add`. The gem5 node's build dependencies and
its `v25.1.0.0` clone of `~/gem5` live in `gcp_nodes.gem5_node.setup_commands`,
because that is the only bring-up phase with a configurable timeout
(`setup_timeout`, set to 3600 there). `worker_setup_commands`, where they used
to live, is capped at a hardcoded 600 s that no config key can raise, and the
apt install plus the clone did not fit. Neither phase builds gem5; step 3 does.

The two commands run cloud setup on different sets of machines:

| command | which IPs get `gcp_nodes.*.setup_commands` |
| --- | --- |
| `chia up` | every discovered instance, new or existing |
| `chia up --add` | only freshly provisioned instances |

So `--add` against an existing `gem5_node` skips the provisioning phase
entirely and the node joins with no gem5 on it. The two assertions in
`available_node_types.gem5_host.worker_setup_commands` exist to make that fail
loudly instead of silently. The commands are idempotent (`test -d ~/gem5 ||`),
so a full `chia up` re-running them over the other node types costs only time.

`cluster/sshwrap/ssh` is not optional on a cold boot. chia probes a new node
with `ssh -o ConnectTimeout=30` inside a 30-second subprocess timeout; a
still-booting GCP VM black-holes the connect, the subprocess timeout wins, and
`SSHClient.run` converts it to `SSHError` — which `wait_for_ssh` does not
catch, so the retry loop aborts on its first probe and the node is reported
FAILED with none of its `ssh_timeout` budget spent. The wrapper prepends
`ConnectTimeout=8` so the probe fails cleanly inside `ssh` and the loop
retries. Read the comment in the file itself.

If only some workers fail to start, repair them with `chia up --add` again —
but not the gem5 node, for the reason above. If the gem5 node is the one that
failed, re-run the full `chia up`.

### 3. Build the pristine checkout, 670 seconds

```bash
chia job submit -- python -c "
import sys; sys.path[:0] = ['$(pwd)', '$(pwd)/loop']
import ray, constants as C
from hosts.gem5 import adapter as gem5
ray.init(address='auto', runtime_env=C.RUNTIME_ENV)
result = gem5.build_tree(C.GEM5_ROOT)
print({k: v for k, v in result.items() if k != 'log'})
print(result.get('log', '')[-4000:])
sys.exit(0 if result.get('ok') else 1)
"
```

This runs `scons build/ARM/gem5.opt` in `~/gem5` on the gem5 node. The job
log shows the build record: the scons command, the binary path, the time
and the tail of the build output. A failed build fails the job. The first
build from scratch took 670 seconds, about 11 minutes, on 32 vCPUs.

Every tree uses the same scons arguments, from `constants.GEM5_SCONS_ARGS`.
They are two flags and nothing else.

```text
--ignore-style --linker=gold
```

gem5 v25.1 reads `CC`, `CXX` and `PYTHON_CONFIG` from the environment only
(`site_scons/gem5_scons/defaults.py:46-103`). The loop sets none of them.
Every build on the node runs with `chia_env` active, the gate's builds and
the agents' shells alike. So every build finds the same `gcc` and the same
`python3-config`, and an agent's build matches the gate's build. No compiler
cache is in the loop.

Scons records its arguments. A tree built with other arguments rebuilds from
scratch. The limit is `P2P_GEM5_BUILD_TIMEOUT`, 5400 seconds by default.

If `P2P_GEM5_SCONS_ARGS` holds a `NAME=value` setting, the adapter moves it
into the environment of the gate's builds. The agents' shells do not get
it. Their builds then differ from the gate's, and each switch recompiles
all of gem5. So keep the default.

A copy of the tree at a new path reuses most of the copied `build/`. In
three gate smoke runs, the copy's first build plus about 90 s of gem5 runs
took 336 to 376 s in all. Nobody timed that build on its own.

### 4. Install the run directory, TODO(measured)

```bash
chia job submit -- python -c "
import sys; sys.path[:0] = ['$(pwd)', '$(pwd)/loop']
import ray, constants as C
from hosts.gem5 import adapter as gem5
ray.init(address='auto', runtime_env=C.RUNTIME_ENV)
print(gem5.install_run_dir_on_cluster())
"
```

This step unpacks the run scripts and the workload payload into
`~/p2p_gem5` on the node. The run scripts are `se_o3.py`,
`run_workload.py` and `p2p_metrics.py`, from `hosts/gem5/run/`.

The install records the sha256 of every file it unpacks. On the next
install it checks every one of those files again, and it looks for files it
did not unpack. If the payload is the same and nothing differs, the install
does nothing. If one file differs, is missing or is extra, it installs the
whole payload again. So an edit that an agent made in `~/p2p_gem5` does not
survive the next install.

The baseline, plan and integrate stages also run this install before they
measure anything. Stage 3 runs it again before every gate attempt. When
that install was not a no-op, the gate verdict carries a warning line that
says why. So a stale payload on the node cannot reach a baseline or a gate.

### 5. Run the cluster smoke, 398 seconds for 28 runs

```bash
chia job submit -- python "$(pwd)/loop/tests/gem5_cluster_smoke.py"
```

The script installs the run directory and builds the pristine tree. Then it
runs every workload in the manifest once, with the feature off. It prints
the instructions, cycles, metrics and wall time of each workload.

The first run passed all 28 workloads on gem5's O3 CPU, and every workload
passed its own self-check. These are the numbers.

| measure | value |
| --- | --- |
| the fan-out of all 28, start to end | 398 s |
| one smoke workload | 14 to 31 s, 2.1 to 6.3 M instructions |
| one perf workload | 136 to 396 s, 33.7 to 65.5 M instructions |
| O3 speed, every workload | 97 K to 323 K instructions per second |
| O3 speed, perf sizes | 165 K to 323 K instructions per second |
| slowest workload | `gapbs_tc`, 396 s |

The script also flags a workload where `cond_mpki` equals `branch_mpki`.
`cond_mpki` counts committed conditional
mispredictions only, and `branch_mpki` counts every branch type. The first
run printed them equal, because it read gem5's `condIncorrect`, which counts
every type. `hosts/gem5/NOTES.md` explains the fix.

The job log shows "No available ports" lines while the 28 runs start. They
are harmless. See the known gaps below.

### 6. Record the baseline, 12 to 387 seconds a run

The baseline on disk came from this command. It covers all 28 workloads, so
a G2 entry can point at any of them.

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage baseline --host gem5 --budget iso-64KiB \
  --baseline-list "$(pwd)/experiments/gem5-all.list"
```

The stage restores and builds `~/gem5`, then runs the list with the feature
off. On 2026-09-23 it wrote `hosts/gem5/baselines/iso-64KiB.json`. That
file is what G2 holds every gem5 port to. In that recording a smoke
workload took 12 to 34 seconds, and a perf workload took 146 to 387
seconds.

The file holds the suite mean plus a `per_trace` map keyed by workload name.
A `feature_off_baseline` entry runs one workload, so it points at one entry
in that map, in the form `/per_trace/<workload>`.

Both flags matter. Without `--budget`, the stage writes `iso-192KiB.json`,
which no gem5 step reads. Without `--baseline-list`, the stage runs only
`experiments/gem5-smoke.list` for gem5. For cbp2025 the default list stays
`experiments/smoke-2.list`. An explicit `--baseline-list` wins, for every
host the stage runs for. So pair it with `--host`.

A separate recording of `gem5-perf.list` took up to 521 seconds per
workload, for `gapbs_tc`. A gem5 build shared the node during that
recording. The same 8 workloads took 1.3 to 1.7 times longer there than in
the cluster smoke. Their instruction and cycle counts did not change.

A second list keeps the first list's `per_trace` entries, for the same gem5
revision and the same workload fingerprints. A run that misses a workload
writes its evidence under `out/`, and the baseline file stays as it was.

Stages 2 and 3 read the baseline for their own `--budget`. Stage 4 refuses
gem5, so for gem5 the budget name only picks the file. Give the baseline,
plan, integrate and gate smoke steps the same `--budget`.

Record the baseline again after any change to `hosts/gem5/run/*.py`,
`hosts/gem5/workloads.json` or the workload payload, and after a new gem5
commit. The fingerprint hashes the bytes of every run script, so a comment
edit counts too. Every gate attempt checks the baseline's revision, and
the fingerprint of each workload that the test plan compares against. If
one differs, the stage stops and asks for a new recording. It does not
report a G2 failure against the port.

### 7. Run the gate smoke, 336 seconds

```bash
chia job submit -- python "$(pwd)/loop/tests/gem5_gate_smoke.py" \
  --budget iso-64KiB
```

This script runs the real test plan runner and the real gate on a copy of
`~/gem5` with no port in it. The copy is the smoke's own tree,
`~/gem5_smoke`. The script deletes it and copies it again at every run, and
it never touches `~/gem5_port`. So a smoke run is safe while stage 3 runs,
and after it stops.

The script writes its own small test plan. The gate runs through the same
code as stage 3's `run_gate`. So the smoke also covers the install and the
baseline check that come before every gate attempt. G1, G2 and G4 must
pass, because an unported tree is the baseline. G5 must fail, because there
is no feature. Any other result is a fault in this machinery, not in a
port.

The first run on 2026-09-23 gave that result
(`runs/2026-09-23-gem5/20260923_1048_gem5_gate_smoke.txt`). G2 matched the
baseline to the last bit. The knob on and the knob off gave identical
numbers. The gate attempt took 336 seconds, from the start of the build to
the verdict. That run used an earlier version of the script, which copied
into `~/gem5_port`.

The 336 seconds include the copy's first build. That is less than one full
670-second build, so that build did not compile all of gem5 from scratch.
The log does not split the time, and it does not say why the build was
shorter. Steps 3 and 9 still plan for a full build.

### 8. Plan, TODO(measured)

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage plan --host gem5 --budget iso-64KiB
```

The stage writes `plan/sr.gem5.plan.json` and `plan/sr.gem5.tests.json`. It
does these things around the planning agent.

- It resets and cleans `~/gem5` before and after the agent runs. The reset
  keeps `build/`, so the agent can run the pristine binary.
- It reads the commit of `~/gem5` on the node. The plan checks read the
  head's mirror at `third_party/gem5`, and the stage stops unless both are at
  the same commit.
- It installs the run directory, so the agent can run workloads through
  `run_workload.py`.
- It gives the agent a shell on `~/gem5` with a limit of 1200 seconds for
  each command. The planner prompt states the same limit.
- It reads the baseline for `--budget`. Without `iso-64KiB` it finds none,
  and then it skips its check that each `/per_trace/` pointer resolves.

The stage measures no host storage for gem5. The statistical corrector's
`getSizeInBits()` returns 0 in v25.1, and `TAGE_SC_L` prints no size total.
So the plan checks test `host_storage` for internal agreement only.

If the mirror is at another commit, the stage prints the fix. The mirror is a
shallow clone, so the fix fetches the commit by name.

```bash
git -C third_party/gem5 fetch --depth 1 origin <commit>
git -C third_party/gem5 checkout <commit>
```

### 9. Integrate, TODO(measured) per gate attempt

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage integrate --host gem5 --budget iso-64KiB
```

Without `--budget iso-64KiB` the stage finds no baseline and stops before
the agent starts.

The agent gets a shell on a fresh copy of the checkout at `~/gem5_port`,
with a limit of 1200 seconds for each command. The integrator prompt states
that limit. The copy includes `build/`, and its first build reuses most of
it. In the gate smoke, that build plus about 90 s of gem5 runs took 336 to 376 s
in all. Later builds in the same copy are incremental.

After each turn, `plan_runner` runs the test plan and `gate.py` judges it.
The default is six attempts (`P2P_INTEGRATION_ATTEMPTS`). Two things come
before each attempt measures anything.

- The run directory is installed again, as in step 4.
- The baseline is checked against the revision of `~/gem5` and the
  workload fingerprints, as in step 6. A stale baseline stops the stage
  with a message to record it again.

No gate attempt on a port ran on the cluster yet. The measured parts give
an estimate for one attempt with `gem5-perf.list` as the performance list.

- The build: under about 5 minutes for the first build in a fresh copy,
  measured inside the gate smoke.
- The performance entry: two waves, feature-on and then feature-off. Each
  wave lasts as long as `gapbs_tc`, 387 to 396 seconds on a quiet node and
  521 seconds while a gem5 build shared it. That is about 13 to 18
  minutes.
- The smoke and G2 entries: under a minute for each run.

The plan's `timeout_seconds` cannot shorten a fan-out run or a build. Each
gem5 run in a fan-out gets at least 3600 seconds
(`P2P_GEM5_RUN_TIMEOUT`), and each build at least 5400 seconds
(`P2P_GEM5_BUILD_TIMEOUT`). So a hung port can hold one performance wave
for an hour, and one attempt for two hours. Only the shell entries, such as
G2, use `timeout_seconds` or its 900-second default as they are.

These are the artifacts under `out/`.

- `*_gate_gem5_<n>.json` for each gate attempt.
- `*_integrate_gem5_<n>.md` for each LLM turn.
- `*_integrate_gem5_diff.patch` at the end. The patch leaves out `build/`
  and other build output.

To resume a run that stopped partway, set `P2P_GEM5_PORT_FRESH=0`. Then the
agent picks up the tree it left. After a backend failure, the stage writes
`*_integrate_gem5_backend_error.json`, and that file names this variable.

```bash
chia job submit \
  --runtime-env-json '{"env_vars": {"P2P_GEM5_PORT_FRESH": "0"}}' \
  -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage integrate --host gem5 \
  --budget iso-64KiB
```

## Several stages in one submission

`--stage` takes more than one stage and runs them in pipeline order.

```bash
chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" \
  --stage baseline plan integrate --host gem5 --budget iso-64KiB \
  --baseline-list "$(pwd)/experiments/gem5-all.list"
```

The `--baseline-list` keeps all 28 workloads in the new recording. Without
it, a changed fingerprint drops every workload outside the smoke list.

Do not use `--stage all` for gem5. It includes stages 4 and 4b, and both
refuse gem5.

## What stages 4 and 4b do with gem5

They refuse it. The search builds and runs only through `CBP2025Node`. So a
gem5 search runs the CBP2025 kit and reports the result as gem5's. Nothing
in that result shows the mix-up.

The driver refuses before `ray.init`, so a bad command fails in seconds.
`dse.run_dse` and `dse.promote_finalists` refuse again on their own. So no
other caller can go around the refusal. The refusal also covers a gem5 host
in `P2P_HOSTS`, for any job that includes stage 4 or 4b.

## Known gaps

- `chia job submit` runs its entry point through a shell on the head. So
  `$VAR` and `$(...)` inside a quoted command expand on the head, before
  the job starts. The steps above use `$(pwd)` on purpose, for the head's
  repository path. When a path must name the node's home, write it out in
  full or read it inside Python on the node. A `$HOME` in the command names
  the head's home.
- In CHIA's SSH-tunnel mode the gem5 node gets 25 Ray worker ports, 30000
  to 30024. That is fewer than its 30 run slots. When a burst of runs
  starts, Ray logs "No available ports" while it starts workers. In the
  28-run cluster smoke every task still ran. A task waits for a free
  worker, and it does not fail.
- No automatic check stops a new workload from opening a `/proc` path. gem5
  SE mode passes such an open through to the host, so the guest can read
  gem5's own environment, the knob included. The current workloads open
  none. `hosts/gem5/NOTES.md` gives the admission rule, a manual
  `qemu-aarch64-static -strace` check.
- The pristine build and install commands in steps 3 and 4 are inline
  scripts. The driver has no stage for them.

## Knobs worth knowing

| variable | default | what it changes |
| --- | --- | --- |
| `P2P_HOSTS` | `cbp2025` | which hosts a stage loops over without `--host` |
| `P2P_GEM5_PORT_FRESH` | 1 | 0 resumes a stage 3 run on the tree it left |
| `P2P_GEM5_BASH_TIMEOUT` | 1200 | the agents' shell limit on the gem5 node, in seconds |
| `P2P_GEM5_BUILD_JOBS` | 30 | the scons job count |
| `P2P_GEM5_BUILD_TIMEOUT` | 5400 | the least time one gem5 build gets, in seconds, whatever the plan says |
| `P2P_GEM5_RUN_TIMEOUT` | 3600 | the least time one fan-out workload run gets, in seconds, whatever the plan says |
| `P2P_GEM5_SCONS_ARGS` | see step 3 | the scons arguments for every tree |
| `P2P_GEM5_WORKLOADS_DIR` | `third_party/gem5_workloads` | where the head finds the built payload |

Pass them through `chia job submit --runtime-env-json '{"env_vars": {...}}'`.
The submitting shell's own environment does not reach the job.
