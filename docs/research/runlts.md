# RUNLTS — verified facts

## 1. Citation / venue / links

- **Full citation (as listed by Shioya Lab):** Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya, "RUNLTS: Register-value-aware Predictor Utilizing Nested Large TableS", **Championship Branch Prediction (CBP2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.**
  - Affiliations: Koizumi/Maekawa/Mizuno/Tsumura — Nagoya Institute of Technology; Kuroki/Shioya — The University of Tokyo.
- **It is NOT an ISCA 2026 paper and there is NO arXiv version** (searched; none found). It is a 6-page CBP2025 workshop paper. **RUNLTS won 1st place at CBP2025** (confirmed from official closing remarks; 2nd: Seznec/SiFive "TAGE-SC for CBP2025"; 3rd: ICT-CAS "LVCP").
- **PDF:** https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final44-Koizumi.pdf (fetched, read in full)
- **Slides:** https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-pres44-Koizumi.pptx ; **Talk video:** https://youtu.be/xk8aPo3Bn4o
- **Artifact (source code):** Google Drive, NOT GitHub: https://drive.google.com/file/d/1VcjlfeyKgEqgwvUhXWGCeT4Nul8oGlkO/view?usp=sharing (official link from the CBP2025 workshop program page). It plugs into the **CBP2025 simulation framework**: https://github.com/ramisheikh/cbp2025 — contestant predictor lives in `my_cond_branch_predictor.{h,cc}`; interface hooks (in `cbp.h` / `cond_branch_predictor_interface.cc`): `beginCondDirPredictor()`, `notify_instr_fetch()`, `get_cond_dir_prediction()`, `spec_update()`, `notify_instr_decode()`, `notify_agen_complete()`, `notify_instr_execute_resolve()`, `notify_instr_commit()`, `endCondDirPredictor()`. Traces: 105 training traces via Google Drive folder (see repo README). Budget rule: 192 KiB total (or CBP2016 TAGE-SC-L 64KB + 128KB extra).

## 2. "RBias" — NAME NOT REAL

The string "RBias" appears **nowhere** in the paper (grepped extracted text). The register-value-correlation component is called **"sR" ("Register Components", Sec 4.2 / Fig 5(c))** — one of the statistical-corrector (SC) components. Separately, the SC has conventional TAGE-SC-L **bias** components named `Bias`, `BiasSK`, `BiasBank` (summed into `sB`). "RBias" is presumably a conflation of "Register" + "Bias"; a spec stub should cite **sR**.

## 3. The sR mechanism (implementable detail, all from the paper)

**Overall:** RUNLTS = tuned TAGE-SC (loop predictor dropped) where the SC receives not just PC + branch histories but also **register-value digests** (Fig 2). LSUM = sB + sG + sP + sC + sI + sL + sS + sT + **sR**.

**What it correlates on — digests (Fig 6, Sec 4.2):** a **12-bit digest** per 64-bit register value; scope is **global** — any logical register, whether or not it appears in the branch (explicitly contrasted with Heil et al.'s *local* two-register-difference approach):
- **Integer regs:** XOR-composition of (a) count of trailing zeros-or-ones (~bits [5:0]), (b) count of leading zeros-or-ones (shifted, ~bits [8:3]), (c) `Value[5:0]` (shifted to top bits) — "capturing characteristics of addresses and round numbers."
- **FP regs:** classify format from MSBs, then sign bit + top exponent bits: FP16 → `Val[15:13]`; FP32 → `Value[31:26]`; FP64 → `Value[63:55]`.
- **Condition-code flags:** the 4 flag bits replicated 3x to fill 12 bits.

**Digest availability tracking (Tomasulo-like table):** one entry per logical register (**65 tracked** per Table 3): `{valid(1), payload(14), decay_ctr(8)}`. At decode, a writer instruction stores its **ROB index as a 14-bit tag** in the payload and clears valid; at completion, payload is overwritten with the 12-bit digest and valid is set. On predictor query, only valid entries forward digests. **Staleness rule: a digest is invalidated after 256 subsequent instructions have decoded** (the 8-bit decay_ctr).

**Table organization (Fig 5(c), Table 3):** **8 banks**, each covering 8 or 9 logical registers (bank 0 shows registers R0, R8, R16, …, R64 — i.e., stride-8 interleave; 65 regs total). Per bank, two structures:
- **Usefulness tables (UT):** three tables UT0/UT1/UT2, 8 entries each, indexed by skewed PC; each entry holds a **vector of 8-or-9 six-bit usefulness weights** (one per register in the bank). Summed usefulness selects the **most useful register's digest in the bank** (largest wins) — this selection avoids extra memory ports. Storage: 6 × 65 × (2^3+2^3+2^3) = 9,360 bits.
- **Prediction weight tables (WT):** the chosen digest + PC hashed by h0/h1/h2 into **WT0 = 512 entries, WT1 = 256 entries, WT2 = 128 entries** of 6-bit weights; the three weights are summed, then the bank output is scaled by **x0 or x2.5** based on usefulness. Storage: 6 × (2^7 + 2^8 + 2^9) × 8 banks = 43,008 bits.
- Bank outputs are summed → **sR**, added into LSUM. **sR total storage: 53,863 bits ≈ 6.6 KiB** (WT 43,008 + UT 9,360 + 65-entry register table 1,495).

**Update rules:** correlations are updated **only for logical registers whose digest was available (valid) at prediction time**; if several registers in the same bank were available, **one is chosen at random** for the update — this gives each table a **single write port**.

**Why it works:** hard to exploit values produced <~100 instructions before a branch at predict time; but **immediately after a misprediction flush**, many in-flight instructions have completed, enlarging the visible value set — the scheme "can correct subsequent mispredictions starting with the second one."

**Prediction combination (Fig 5(d)):** standard TAGE-SC style — LSUM vs thresholds; decision table: {table high-conf & |LSUM|>Th/2 → SC(sign of LSUM); |LSUM|>Th/4 & high-conf → Meta1 chooses; otherwise low-conf → SC; table-out for high-conf low-LSUM; Meta2 for mid-conf}. Update thresholds: global (12 bits) + local (8 bits × 64 entries) = 524 bits; meta FirstH(7)/SecondH(7).

## 4. Other RUNLTS components (one paragraph each)

- **Large bimodal base (Sec 3.1.1):** 128K-entry, 20 KiB bimodal (1 prediction bit + 1/4 shared hysteresis bit; Table 2: 163,840 bits) — 16x the 8K-entry CBP5 base — to absorb the huge instruction footprints of JS/server workloads.
- **Novel history lengths (Sec 3.1.2, Fig 4):** 24 lengths chosen by a **second-order arithmetic progression blending into a geometric progression**: {0, 6, 14, 24, 36, 50, 66, 84, 104, 126, 150, 178, 212, 252, 300, 358, 426, 506, 602, 776, 1078, 1606, 2554, 4316}; first differences +6,+8,…,+24 (second difference 2), then ratios ×1.19 stepping up by 0.1 to ×1.69. No skewed-associative tables. Tagged tables: **9 low banks** (4 components; entry = useful/newly(1)+ctr(3)+tag(9), 2^11 entries each; 239,616 bits) + **25 high banks** (19 components; tag(13); 870,400 bits), bank-interleaved via crossbars over GHR slices; final selection "use all / alt / longest."
- **Dynamic allocation throttling (Sec 4.1):** aggressive multi-entry allocation per misprediction needs throttling; they add a **zero-storage thrashing detector** by re-purposing the (ctr == 0 or −1) AND u-bit-set combination (empirically near-unused) as a "newly allocated" marker: on allocation, init ctr to 0/−1 and set u=1; clear u on first reference. Two 16-bit counters (Useful, Decay) track newly-allocated-entries-that-predicted-correctly vs evicted-without-reference; **allocation rate is adjusted from the ratio**. They also argue TAGE's useful-bit beats BATAGE's confidence-based replacement at large scale (BATAGE retains useless entries when scaled up).
- **SC extensions (Sec 3.2):** beyond CBP5 TAGE-SC-L components (sB bias trio with x1/x2 useful scaling; sG global-backward, sP forward-taken-path, sL 256-entry local, sS/sT 16-entry locals — configs like "U=8, M=2, N=3/4/5"): (1) **sC call-stack-based history** [Ishii et al., CBP-3]; (2) **sI = BrIMLI + TaIMLI** [Seznec 2024 HAL RR-9561 cookbook] with **extra weight on useful sI predictions** (U=256, M=3, N=2); (3) **sR** above. Plus FTL++-style pipeline-aware u-bit updates.
- **Storage (Tables 2-3):** table predictor 1,278,385 bits (156.05 KiB) + SC 292,505 bits (35.71 KiB) = **1,570,890 bits = 191.75 KiB**, within the CBP2025 192 KiB budget.

## 5. Reported results

- **Paper numbers (192 KiB, latter halves of the 105 CBP2025 training traces, fetch width 16 / frontend depth 10):** RUNLTS **BrMisPKI 3.197, CycWpPKI 140.3**; without local history: 3.269 / 141.5. Their tuned 192 KiB TAGE-SC-L baseline: 3.408 / 145.2 → **~6.2% MPKI reduction overall**. Other Table-1 rows (all 192 KiB unless noted): GEHL 4.088; 64KiB TAGE-SC-L 3.751; TAGE 3.674; BATAGE 3.667; BATAGE-GSC 3.590; TAGE-GSC 3.533; BATAGE-SC 3.462; TAGE-SC-L[Sheikh/Jain sim] 3.428. Improved 98/105 traces; median gain 0.052 MPKI; first-octile 0.323 MPKI.
- **sR alone:** the paper gives **no single number** for the register component's average MPKI delta. Text: "The register components yielded the largest and broadest gain, improving every trace category" (Fig 7 stacked per-trace breakdown); each of the 7 features individually adds ≥0.005 MPKI avg and helps ≥4/7 of traces. The "~2.5%" figure you asked about does **not** match anything attributed to sR; it exactly matches RUNLTS's **official overall CycWpPKI reduction of −2.5% (full trace set, Avg) vs the 192KB scaled TAGE-SC-L reference** from the CBP2025 closing remarks. Official closing-remarks numbers: BrMisPKI reduction ≈ **−7.2% (training) / −5.3% (full)**; per category (BrMisPKI, full): int −5.2%, fp −10.2%, web −2.8%, media −5.1%, compress −7.1%, infra −8.9%; CycWpPKI (full): Avg −2.5% (int −3.5, fp −5.5, web −1.6, media −2.1, compress −3.5, infra −0.9); with perfect L1(I+D): −4.0% CycWpPKI Avg.

## 6. Closest published related work (for citation fallback)

- T.H. Heil, Z. Smith, J.E. Smith, "Improving branch predictors by correlating on data values," MICRO-32, 1999 (the canonical register/data-value-correlated predictor; *local* scope — value differences of the branch's own operands; tagged backing predictor for hard branches).
- LVCP: Yang Man et al. (ICT-CAS), "LVCP: A Load Value Correlated Predictor for TAGE-SC-L," CBP2025 3rd place — paper https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final15-Man.pdf, code https://drive.google.com/file/d/1Cp733wk5OebY7TbgwGEYGRj89q59vAUM/view?usp=sharing.
- Pruett & Patt, "Branch Runahead," MICRO-54, 2021 (pre-executes producer chains rather than correlating on values).

Local copy of the RUNLTS PDF: /private/tmp/claude-502/-Users-evanlai/d8510fae-cc23-452f-984c-f30b9aac4856/scratchpad/runlts.pdf (extracted text: runlts.txt in same dir).

## SOURCES
https://www.rsg.ci.i.u-tokyo.ac.jp/lab/en/papers/2025/
https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/cbp2025-final44-Koizumi.pdf
https://ericrotenberg.wordpress.ncsu.edu/files/2025/06/CBP2025-Closing-Remarks.pdf
https://ericrotenberg.wordpress.ncsu.edu/cbp2025-workshop-program/
https://ericrotenberg.wordpress.ncsu.edu/cbp2025/
https://raw.githubusercontent.com/ramisheikh/cbp2025/main/README.md
https://api.github.com/search/repositories?q=RUNLTS

## CAVEATS
1) The task's premises are partially wrong and I could not verify them: RUNLTS is a CBP2025 workshop paper (June 21, 2025, w/ ISCA 2025, Tokyo) that WON CBP2025 — it is not ISCA 2026 and has no arXiv version (searches found none). 2) No component named "RBias" exists — grep of the full paper text finds zero occurrences; the register-value-correlation component is named "sR" (Register Components, Sec 4.2). If your spec stub says "RBias", rename or footnote it as sR. 3) The "~2.5% MPKI reduction from RBias alone" claim is unverifiable: the paper gives no scalar for sR's standalone contribution (only a per-trace stacked bar, Fig 7, calling it the "largest and broadest gain"); −2.5% exactly matches RUNLTS's official overall CycWpPKI reduction (full traces) vs the 192KB scaled TAGE-SC-L reference — likely the source of the confusion. 4) The artifact is a Google Drive zip linked from the official CBP2025 program page, not a GitHub repo; GitHub repo search for "RUNLTS" found nothing relevant (code search API required auth, so an obscure mirror could exist). I did not download/inspect the Drive zip contents, so file names inside the RUNLTS artifact are unverified; the framework it targets (ramisheikh/cbp2025, my_cond_branch_predictor.{h,cc} and the notify_*/get_cond_dir_prediction interface) is verified from that repo's README. 5) Some Fig 5(c)/Fig 6 micro-details (exact digest bit placements, x2.5 scaling, WT sizes 512/256/128, stride-8 bank mapping) are read from figure text extraction; the prose confirms the substance but exact bit offsets in Fig 6 could be off by a position. 6) I did not verify the CHIA framework claims in the context blurb (github.com/ucb-bar/chia, docs.chialoops.ai) — out of scope for this task and not fetched.