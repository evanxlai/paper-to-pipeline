# From Paper to Pipeline: A CHIA Loop for Porting and Tuning of Published Design Features

**Team:** Evan Lai, Jan Strzeszynski · Agentic Approaches to Architecture CHIA Hackathon
**Status:** Accepted (August 2026). Source of record: `CHIA_Hackathon_Proposal_2026.pdf` / `proposal (2).tex`.

## Overview of the task

Evaluating a feature from a recent paper on your own infrastructure is a labor-intensive step in computer architecture research. Two things make it expensive: first, a reference implementation may not exist, and when it does, it targets a different tool, framework, or baseline design. Second, a feature cannot be evaluated fairly without tuning it to the host: published parameterizations are optimized for a different design under different constraints, so an untuned port measures the quality of the port, not of the idea. Design-space exploration under matched budgets (iso-storage, iso-area/power, compile time) is therefore integral to the evaluation, not a finishing step.

We propose an "adopt-a-paper" CHIA loop that automates both halves: given (i) a **target design** *A*, (ii) a **feature** *F* specified by a paper, with reference artifacts as optional inputs, and (iii) **success criteria** as regression and feature tests, the loop integrates *F* into *A* and then autonomously explores the joint design space of *F*'s parameters and the host's budget allocation to render an iso-budget verdict. This generalizes CHIA's gem5–BOOM alignment and evolutionary-discovery case studies into a reusable capability.

We scope this project to performance-model hosts, where evaluation is cheap and parallel; because agents touch the host only through its build/run/stats tools, the same loop design would carry to RTL and compiler hosts, with only the tool nodes and gate metrics (correctness plus timing/area/power; compile time) changing.

## Methodology (loop design and execution plan)

**Loop design.** The loop is a directed cyclic graph of CHIA nodes. All verification and promotion decisions are *programmatic edges*; LLM agents (Gemini via CHIA model nodes) act only through *agentic edges* to sandboxed ChiaTools (build, run, stats), so success is enforced by deterministic gates in the loop — never self-reported by an agent. Three stages:

- **Feature distillation (LLM node).** An agent reads the paper, including reference artifacts if provided, and emits a structured *feature spec*: state and data structures added, algorithms, interfaces to the host, resource accounting, and tunable parameters. Downstream agents implement against the spec, so the loop does not require a reference implementation to exist.
- **Integration behind a deterministic verify gate.** A coding agent implements the feature *F* in the existing design *A*, iterating via agentic edges to the host's build/sim/stats tools — many hosts (gem5, ChampSim, Chipyard, Verilator, Hammer, CIRCT) already ship as CHIA nodes. The gate: the code builds; with *F* disabled, *A*'s baseline metrics (here, MPKI/IPC) are preserved; spec-derived unit tests pass. The gate is the only level-specific element of the loop.
- **Distributed iso-budget DSE — the core of the loop.** An integrated feature is only a candidate; the verdict comes from tuning. An EvolverNode (AlphaEvolve/AdaEvolve) proposes parameterizations of *F* and iso-budget rebalances of the host; CHIA fans screening evaluations out across a GCP cluster with caching/bypass to reuse prior results and fault-tolerant workers, promoting winners to full-suite validation. Only the tuned configuration is compared against the baseline. CHIA profiling reports token and compute cost per accepted change.

**Demonstration.** We instantiate the loop in a domain with open artifacts and (relatively) cheap, parallel evaluation: we port **RBias**, the register-value–correlation predictor component of RUNLTS (ISCA 2026), into (a) **ChampSim** and (b) **gem5**'s TAGE-SC-L — cross-tool *and* cross-design — and tune at iso-storage (192 KiB, 64 KiB), reporting MPKI/IPC. Because RUNLTS ships an open artifact, we can also ablate the loop's inputs: paper-only vs. paper-plus-reference. To execute that artifact we will contribute a **new CHIA node wrapping the CBP2025 simulator**; it reproduces the paper's gains (the yardstick for our targets) and validates the distilled spec against observed behavior. Stretch goal: a second feature from the same paper (history-length selection or allocation throttling).

**Execution plan:** week 1: CBP2025 node, harnesses, baseline reproduction; week 2: distillation + integration agents to a passing gate; weeks 3–4: DSE at scale, ablations, write-up and upstreaming.

## Expected results

1. An open-source CHIA loop with three composable blocks — feature-spec distiller, regression-gated integration node, iso-budget DSE node — plus a new CBP2025 simulator node. The blocks are level-agnostic by construction: swapping the tool nodes and gate metrics would extend the same loop to RTL hosts (existing Chipyard/Verilator/Hammer nodes, PPA gates) and compiler hosts (CIRCT) — a natural follow-on beyond this project's scope.
2. Working ports of RBias into ChampSim and gem5 whose feature-off behavior matches each host baseline.
3. Recovery of a meaningful fraction of the paper's reported gain after autonomous tuning (RUNLTS reports ~2.5% average MPKI reduction from RBias; we target ≥50% of the relative gain on the new hosts), with two ablations: *naive port vs. tuned port*, quantifying how much of a fair evaluation depends on DSE, and *paper-only vs. paper-plus-reference inputs*, quantifying how far the loop gets without reference code.
4. A 4-page report, the released loop and results, and blocks suitable for upstreaming into mainline CHIA.

## Cost estimate (target: $1,000; cap $1,300)

Trace-driven evaluation parallelizes well: a full 673-trace CBP2025 run for ~9 predictors takes ~4 h on 64 cores (≈250 core-hours). We budget a screening subset (~60 traces, ~20 core-hours per candidate) for 200–300 DSE candidates plus full-suite validation of finalists: ~6–8k core-hours. On GCP c2d spot (~$0.01–0.02/core-hour) this is **$150–350 of compute**, plus **$30–50** for trace storage (~160 GiB) and head-node/VM overhead. Agentic LLM usage (distillation, integration iterations, DSE proposal agents) accounts for the remainder: **$400–700 in Gemini API credits**. Total: **$600–1,100**, within the $100–$1,500 target.
