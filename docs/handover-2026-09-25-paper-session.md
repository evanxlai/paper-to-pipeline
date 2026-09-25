# Handover, 2026-09-25: paper-writing session and a node-loss snapshot

The user asked for everything relevant to be saved and pushed, because the
head node might go down. This file records what a Claude Code session on
2026-09-25 (about 03:50 to 08:40 UTC) learned and decided. Most of it is
about the paper draft. It also records the state of the jobs that were
running when the snapshot was taken.

Every fact below was checked against a file in this repository or in `out/`
during the session, and the source is named. Anything that was not checked
says so.

## 1. What was saved, and where

Two branches were pushed. `main` was left alone, because other Claude
sessions and a running gem5 job were using the same working tree. Each
snapshot commit was built from a temporary git index, so the shared working
tree, its index and its checked-out branch were not touched.

| Branch | Contents |
| --- | --- |
| `snapshot/2026-09-25-main` | The main clone as it stood (`~/chia-hackathon/paper-to-pipeline`). Its parent is `main` at `cb6a99b`. It holds every tracked modification and deletion, every untracked file that is not ignored (`paper/`, `plan/*`, `spec/*`, new tests, `experiments/promote-45.list` and more), and **the whole of `out/`** (about 19 MB of run artifacts), force-added even though `.gitignore` lists `out/`. It also holds `session-context/`, described below. |
| `snapshot/2026-09-25-rerun` | The second clone, `~/chia-hackathon/paper-to-pipeline-rerun`, which was on the local-only branch `rerun-20260924`. Its uncommitted changes and its `out/` (about 1.2 MB) are included. Its parent is `cb6a99b`. |

`session-context/` on the main snapshot holds:

- `claude-memory/`, a copy of Claude Code's auto-memory for this project
  (`~/.claude/projects/-home-laievan-chia-hackathon-paper-to-pipeline/memory/`).
  These files are the user's standing preferences and corrections. They live
  only on this node, so they are lost with it unless copied.
- `HOW-TO-RESTORE.md`, which says how to put the memory back and what was
  left out.

What was **not** pushed, and why:

- **Claude Code session transcripts** (`~/.claude/projects/.../*.jsonl`,
  74 MB). They contain live credentials: a plaintext `P2P_GATEWAY_TOKEN`
  value, 14 strings shaped like Google OAuth access tokens (`ya29.`) and 4
  shaped like Google API keys (`AIza`). The repository is private, but
  pushing live credentials into git history is not reversible in practice.
  Back them up separately (redacted, or to a GCS bucket) if needed.
- **`third_party/`** (245 MB). It holds the RUNLTS and Wormhole PDFs and
  their text, the reference artifact, a gem5 checkout and the gem5 workloads.
  `.gitignore` excludes it on purpose, because it is third-party content.
  `scripts/fetch_artifacts.sh` and `scripts/build_gem5_workloads.sh` rebuild
  it.
- Ray cluster state, and the jobs in flight. A lost head loses those jobs.

## 2. State of the runs at snapshot time (08:30 UTC)

This is read from `out/` as the jobs left it. It was not re-verified beyond
reading the files.

- **gem5, sR, run `20260925_044249`** (a third gem5 integration run) was
  still in progress. Attempt 0 failed to build (G1). Attempt 1 (07:02) moved
  conditional MPKI by exactly 0.0000, so the feature does not reach the
  prediction (G5). The job's driver was pid 504909.
- **gem5, sR, run `20260924_195032`** finished with 6 gated attempts, and
  none passed. Attempts 0 to 2 failed G5 (MPKI 8.1 to 9.5% worse). Attempt 3
  failed G1. Attempt 4 failed G2 (feature-off not baseline-identical) and
  G5. Attempt 5 failed G5 with no change at all.
- **gem5 over all runs**: the earlier run `20260924_153022` failed 2 G5
  attempts. The paper draft still says "two runs and six attempts" and "the
  last attempt did not build", which is now out of date.
- **Wormhole on CBP2025, run `20260925_030602`**: 5 gated attempts, all
  failing G5, with MPKI 1.7 to 2.1% worse on the 4-trace performance list.
- **Wormhole, run `20260925_033703`** (a second job with a plan revision):
  3 gated attempts, all failing G6 (`SR_NUM_BANKS = 7 builds the same binary
  as 8`). The Wormhole port reuses the `SR_` macro namespace, and some knob
  does not reach the binary.
- **Wormhole DSE, `20260925_060226_summary.json`**: a stage 4 and promote
  job for Wormhole at iso-64KiB was started at 06:02. Its end state was not
  checked.
- **sR_hand DSE and promote, `20260925_055032`** (finished 08:03). This is a
  **new result that the paper does not have yet**. It used feature
  `sr_hand`, iso-64KiB with the checkpoint state exempt, a population of 95,
  and 45 promotion traces. Held-out MPKI against the unmodified host was
  −4.21% for the winner (finalist 3, 524,286 bits), −4.06% for sR at the
  paper's defaults (578,478 bits, over budget), and −3.86% and −3.67% for the
  other two finalists. `screening_winner_held` is false. This is an order of
  magnitude larger than the −0.34% in the draft, so find out which port,
  which spec and which hand patch it used before quoting it
  (`out/20260925_054927_handpatch_sr_hand_cbp2025.md` and `..._port.patch`
  look relevant). Not checked in this session.

## 3. The paper

- **Latest draft**: `paper/main.draft-2026-09-25.tex`. This session
  reconstructed it from the user's last full paste plus the sections the user
  asked for. Its header comment lists exactly what changed. The user's own
  working copy, possibly on Overleaf, is the authoritative one.
  `paper/main.tex` is an older draft from 04:37.
- **Sections finished this session**: the abstract's demonstration paragraph
  (it now names gem5 and Wormhole, and the results sentence is a `\todo`), the
  roadmap paragraph closing the Introduction, a fourth contribution (the
  CBP2025 CHIA node), Background (CHIA, TAGE-SC-L, sR, Wormhole, CBP2025 and
  gem5, cut by about 25% and then trimmed further), and Experimental Setup
  (rewritten, then cut by about 25%).

### The user's writing preferences for this paper

All of these are also in `session-context/claude-memory/`.

- Call CBP2025 "CBP2025", never "the kit" or "the CBP2025 kit". The BibTeX
  key `cbp2025kit` stays.
- In paper prose, no run labels (R1–R3) and no gate labels (G1–G6). Say
  "the first search" and "the two longer searches", and "the feature-off
  check", "the smoke check" and "the performance check".
- Setup reports MPKI only: no CycWPPKI on CBP2025, and no IPC on gem5.
- Shorter is better. The user asked three times for cuts of about 25%, and
  for "much shorter" twice.
- Background headings all end with a period.

### Known inconsistencies left in the draft

- Results, the verdict table and Discussion still use R1–R3, G1–G6,
  CycWPPKI and IPC, which Setup no longer defines.
- The abstract says "Championship of Branch Prediction". The name is
  "Championship Branch Prediction", as in the RUNLTS bib entry. "into the
  CBP2025's TAGE-SC-L" should drop "the". Both were suggested, but the user
  had not applied them.
- "The kit's default host" remains in Results (the 192 KiB paragraph).
- Results has no Wormhole subsection, although the abstract and Background
  now introduce Wormhole.
- The gem5 subsection's attempt counts are out of date (see section 2).
- The Wormhole bib entry's venue (MICRO 2014) comes from our spec's source
  field and from memory. The PDF does not print it.

## 4. Findings from this session that the paper should act on

1. **The first sR search ran on a hand-written spec.** Job
   `20260923_032823` (the draft's R1) read `spec/sr.paper_only.json` as
   committed in `d189393` (2026-09-22 21:56). That commit is titled "Refine
   the sR spec by hand, with every width and size as a knob", and its message
   says the spec "is distilled by hand from the paper". The spec's next
   commit is `e506e14` (2026-09-24 00:09), after R1. So R1's stage-1 input
   came from us, which contradicts the Results sentence "R1 used a fully
   loop-produced port". It also undercuts the framing of "twelve knobs" as a
   loop change: they were added by hand in `d189393`. That spec also states
   "sR's sum is one term in the host SC's LSUM" as a host interface, which is
   the same feature-specific answer the threats section already flags for the
   host notes. Which spec R2 and R3 used was not traced.
2. **The gem5 host notes carry the same sR-specific answer.**
   `hosts/gem5/NOTES.md` says "sR is one term in the SC's sum and not an
   override" and tells the agent where the `lsum +=` line goes. The planning
   and integration agents receive that file in their prompts. The threats
   bullet names only the CBP2025 notes.
3. **Stage 3 has no separate root-cause agent.** `loop/adopt_a_paper_loop.py`
   (about lines 835 to 930) opens a single conversation for the whole stage.
   After each failed gate, the same agent gets `loop/prompts/debug.md` with
   the gate's reasons and fixes its own tree. It may also send a complete
   revised plan, which code accepts only if nothing was weakened, or escalate,
   which triggers a stage-2 re-plan. The limit is `NUM_INTEGRATION_ATTEMPTS`
   = 6 gate runs. The debug turn after the sixth failure is never gated,
   which is why a run can have `integrate_<host>_5.md` with no matching gate
   file. The gate's diagnosis strings in `loop/gate.py` are the only outside
   view. The user asked about this, and a fresh-eyes root-cause agent is a
   possible addition to the loop.
4. **Why screening and promotion are separate.** Promotion is a held-out
   test, not a speed trick. The draft's R1 winner was 1.1% better than the
   host on its 8 screening traces and 0.76% worse on the 16 held-out traces
   (`runs/2026-09-23-cbp2025/README.md`). R3's screening winner did not hold
   (`screening_winner_held: false`, +1.0% held out). The new `sr_hand` run
   above did not hold either.

## 5. Facts verified for the Background and Setup sections

- **CHIA has no CBP2025 node upstream.** `ucb-bar/chia` at `16c35e9`
  (`~/chia-hackathon/chia`) has only `chia/simulators/champsim.py` and
  `gem5.py`. `chia_nodes/cbp2025/cbp2025_node.py` (`CBP2025Node`) was
  written in this repository and is meant for upstreaming, but has not been
  upstreamed. `hosts/cbp2025/adapter.py` calls its `build`, `run` and
  `aggregate`.
- **The gem5 host uses CHIA's gem5 node functions**
  (`Gem5Node.build_gem5`, `Gem5Node.run_gem5`) through `.options(resources=
  {"gem5_host": 1})`. It never constructs a `Gem5Node`, and it avoids CHIA's
  default `gem5` resource (`hosts/gem5/adapter.py` docstring).
- **Wormhole** (`third_party/wormhole/wormhole.pdf`, read page by page):
  - It is a side predictor for inner-loop branches that correlate across
    outer-loop iterations. It folds local history into a 2D matrix, uses the
    SC to find problem branches and the loop predictor's `LP_TOTAL` for the
    row length, and overrides the base prediction when confident (§V).
  - The 4 KB configuration is 1,065 bits and the 32 KB one is 10,997 bits
    (§VI-G).
  - MPKI falls by 2.53% and 3.15% against 4 KB and 32 KB ISL-TAGE, and by
    2.6% against 32 KB TAGE-SC-L (§VI-D). The gains are concentrated in four
    of the 40 CBP4 traces.
- **gem5**:
  - The host is v25.1.0.0 (`7a2b0e4`), ARM syscall emulation, `ArmO3CPU` at
    default sizes, with `TAGE_SC_L_64KB`. It gives the predictor no register
    values (`hosts/gem5/NOTES.md`).
  - The 28 workloads are 14 at full size plus a `_s` smoke twin of each,
    from GAPBS (6 kernels), bzip2, zstd, Lua (5 scripts) and SQLite
    (`hosts/gem5/workloads.json`).
  - Stats cover the whole run: nothing resets them, and `max_insts` is null.
  - The gate smoke matched the baseline to the last bit
    (`docs/gem5-runbook.md`).
  - The node is one `c2d-standard-32` with 30 `gem5_host` slots.
- **CBP2025**: commit `6074966`. It scores the second half of each trace
  after a first-half warmup (the "50 Perc" rows, which are not a
  percentile). Metrics are arithmetic means over a list.
- **Cluster**:
  - For R1, two `n2-standard-2` trace workers with 4 trace slots
    (`runs/2026-09-23-cbp2025/README.md`).
  - From `9b88f67` (2026-09-24 07:41) on, `cluster/cluster.yaml` asks for
    16 × `n2-standard-32` on-demand sim workers. It was not confirmed that
    all 16 joined, because Ray was not reachable from the session's shell.
  - R3's search screened about 79 candidates on 60 traces in about 93
    minutes, which only fits the large cluster.
- **Models**:
  - The agent stages use Antigravity with `gemini-3.1-pro-high`. The
    default was `gemini-3.8-flash-medium` from 09-20 07:50 to 09-22 09:49
    (`git log -G ANTIGRAVITY_MODEL -- loop/constants.py`).
  - R1's DSE used `experiments/config_adaevolve_medium_vertex.yaml`:
    `google/gemini-3.8-flash` alone, 24 iterations, population 8, 1 island,
    1 in flight.
  - R2 and R3 used `experiments/config_adaevolve.yaml`: Gemini 3.5 Flash
    and 3.1 Pro Preview at equal weight, population 48, 4 islands, 8 in
    flight. The gateway log `out/llm_gateway.jsonl` shows that pair on 09-24.
    The old Setup text credited all DSE to that pair, which was wrong for
    R1.
- **Trace lists**:
  - `smoke-2` is the two sample traces.
  - `perf-4` is `int_13`, `web_21`, `fp_1` and `infra_8`.
  - R1 screened on `perf-8` and promoted on `promote-16`. R2 and R3 used
    `screening-60` and `promote-45`.
  - On gem5, `gem5-smoke` is `gapbs_bfs_s` and `sqlite_s`, and `gem5-perf`
    is 8 full-size workloads.
- **Mapping the draft's runs to records**:
  - R2 is `out/20260924_181851_promote_cbp2025.json` (population 77,
    finalist 1 at 523,918 bits, −0.34% held-out MPKI).
  - R3 is `out/20260924_203329_promote_cbp2025.json` (population 79, with
    `exempt: ["checkpoint"]`). Its search is
    `out/dse/sr/cbp2025/candidates_20260924_182524.jsonl` (18:25 to 19:58).
