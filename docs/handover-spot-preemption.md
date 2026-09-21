# Handover: sim_worker spot preemption blocking `--stage baseline`

Written 2026-09-20 by an assistant session that got the baseline job running
once, then watched the cluster it depends on get pulled out from under it.
Picking this back up should start with "make the fleet survive a preemption
cycle," not with re-running the job again.

## Symptom

`chia job submit -- python "$(pwd)/loop/adopt_a_paper_loop.py" --stage baseline`
eventually hangs forever with:

```
Error: No available node types can fulfill resource request {'CPU': 1.0, 'cbp2025': 1.0}. Add suitable node types to this cluster to resolve this issue.
```

repeated every ~35s from the Ray autoscaler. `chia list nodes` shows the two
nodes that carried the `cbp2025` resource as `DEAD` ("health check failed
due to missing too many heartbeats").

## What's actually happening (confirmed, not guessed)

`cluster/cluster.yaml`'s `sim_worker` GCP node group is `machine_type:
e2-small`, `count: 2`, `spot: true`. These are the VMs backing the
`cbp2025_worker` Ray node type (`resources: {"cbp2025": 32}`,
`compatible_ips: ["@sim_worker:0", "@sim_worker:1"]`).

Checking `gcloud compute operations list --project "$GCP_PROJECT" --filter="targetLink~sim-worker"`
shows a repeating insert -> preempt cycle. Two confirmed preemption events in
the ~24h before this doc was written:

- `sim-worker-0`/`sim-worker-1` preempted 2026-09-18 15:38-15:39 (after being
  up since 15:11 — ~27min lifetime)
- `sim-worker-0`/`sim-worker-1` preempted again 2026-09-19 22:32-22:34 (after
  being up since 22:18 — **~14-16min lifetime**), which is what killed the
  `--stage baseline` run submitted right after they came up
  (`raysubmit_neA4TPPjkigAsHp2`, stopped manually — see below).

When both `sim_worker` VMs get reclaimed, the Ray raylets on them go DEAD and
never come back — Chia's autoscaler does **not** appear to auto-relaunch
GCP spot instances that get preempted (at least not observed doing so in this
session; worth verifying against Chia's autoscaler source before assuming).
The cluster is then permanently missing the `cbp2025` resource until someone
manually runs `chia up cluster/cluster.yaml --add -y` again.

This is a **recurring pattern, not a one-off cloud blip** — lifetimes have
been getting shorter (27min -> ~15min across two observed cycles), which is
consistent with `us-central1-a` spot capacity for `e2-small` being under
contention, though that's speculation from two data points, not confirmed.

## What was fixed this session (separate, already-solved issue)

Not the preemption problem, but blocking in the same path: `cluster.yaml`'s
`sim_worker`/`host_worker` GCP nodes had their `ssh_user` changed from `chia`
to `laievan` at some point (visible in the working-tree diff, uncommitted).
`worker_setup_commands` clone/build checkouts under that user's home, but
`loop/constants.py` hardcoded worker-side paths as `/home/ray/...`. Fixed by
deriving `CBP2025_ROOT` / `CHAMPSIM_ROOT` / `GEM5_ROOT` from `Path.home()`
at runtime instead (see `loop/constants.py:34-43`, already committed to the
working tree, not yet committed to git). This fix is verified working — the
build step (`CBP2025Node.build`) found `~/cbp2025` and started running before
the nodes died.

## Current cluster state (as of end of this session)

- `raysubmit_neA4TPPjkigAsHp2` (the baseline job that got stranded) was
  manually stopped via `chia job stop`.
- `gcloud compute instances list --project "$GCP_PROJECT"` shows only
  `chia-head` and `chia-paper2pipeline-host-worker-0` running. **Both
  sim-worker instances are gone** — do not assume they exist; check before
  submitting anything that needs `cbp2025`.
- `--stage integrate` was also test-submitted (deliberately, to confirm a
  different, expected gap) and correctly fails fast with `no recorded
  baseline for champsim/iso-192KiB; run --stage baseline` — that's an
  unrelated, already-understood TODO (see "Known unrelated gaps" below), not
  something to debug.

## Suggested next steps, roughly in order

1. **Decide whether `e2-small` spot is fit for purpose.** These are meant to
   be "cheap spot cores for the CBP2025 screening fan-out" per the comment
   in `cluster.yaml`, but the repeated sub-30-minute preemptions mean any
   `baseline`/`dse` run that takes longer than that will never finish
   cleanly. Options: bigger/less-contested machine type, a different zone,
   `spot: false` for at least one of the two (loses cost savings), or
   accepting spot but building real resilience (next point).
2. **Check whether Chia's autoscaler is supposed to auto-relaunch preempted
   GCP spot nodes and isn't, or whether that's just not implemented.** Look
   at `chia up`'s autoscaler loop / the GCP provider code
   (`~/chia-hackathon/chia/chia/...` — this session found `chia`'s source
   checked out at `/home/laievan/chia-hackathon/chia`, separate from this
   repo). If it's supposed to self-heal and isn't, that's a chia bug worth
   fixing or reporting upstream. If it's not implemented, either add a
   watchdog (e.g. `chia list nodes` polling + `chia up --add -y` on DEAD
   detection) or make peace with manual babysitting for now.
3. **Once the fleet is stable, resubmit `--stage baseline`** and let it run
   to completion uninterrupted before touching `integrate`/`dse` again.
4. Re-provisioning nodes currently requires an interactive `y` confirmation
   (`chia up cluster/cluster.yaml --add`) that auto-mode tooling can't answer
   non-interactively without `-y`, and `-y` was blocked by this session's
   permission classifier as a "Blind Apply" (spends money / touches shared
   GCP state without a human in the loop). Whoever picks this up should run
   the provisioning step themselves interactively, not try to force `-y`
   through automation.

## Known unrelated gaps (do not treat as bugs to fix under this issue)

- `_run_gate` in `loop/adopt_a_paper_loop.py` is a hardcoded stub that always
  returns `passed=False` — stage 2 (`integrate`) can never pass yet. This is
  documented as a TODO in the file's own docstring.
- No code path records a `champsim`/`gem5` baseline — only `cbp2025`'s
  baseline gets recorded by `--stage baseline`
  (`record_cbp_baseline` in `adopt_a_paper_loop.py`). `integrate` needs a
  per-host baseline recorder before it can even reach the gate stub.
- Per user direction (2026-09-20 session), the eventual gate's pass
  criteria should **not** be a fixed "must beat baseline" comparison — it
  should be dynamically determined per feature. Exact design still
  undecided; don't build a fixed baseline-comparison gate assuming that's
  the target shape.

## Handy commands used this session

```bash
# cluster health
chia status --chia-cluster cluster/cluster.yaml
chia list nodes --chia-cluster cluster/cluster.yaml

# GCP instance state / history
gcloud compute instances list --project "$GCP_PROJECT"
gcloud compute operations list --project "$GCP_PROJECT" --limit=30 --sort-by=~startTime --filter="targetLink~sim-worker"

# job introspection
chia job list          # dumps full JobDetails for every job ever submitted on this head
chia job status <id>
chia job logs <id>
chia job stop <id>

# re-provision missing GCP nodes (interactive confirmation, run by a human)
chia up cluster/cluster.yaml --add
```
