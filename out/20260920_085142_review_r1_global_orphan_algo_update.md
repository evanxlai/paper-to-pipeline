success: True
usage: {'input_tokens': 30062, 'output_tokens': 48048, 'thinking_tokens': 40073, 'cache_read_tokens': 0, 'total_tokens': 78110}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the Statistical Corrector by capturing correlations between recently produced register values and branch directions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The paper explicitly states that the novel prediction method captures correlations between register values and branch directions by integrating value digests into the SC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The predictor maintains a 65-entry Tomasulo-like register status table tracking whether logical registers R0-R64 hold a 12-bit digest or a 14-bit tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies a dedicated Tomasulo-like table with one entry per logical register holding a valid bit and a 14-bit tag or 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Logical registers are partitioned across 8 banks, each using 3 usefulness tables (UT0-UT2) to select the most useful register to index 3 prediction weight tables (WT0-WT2).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 5(c) shows the register components, which exploit correlations between register values and branch directions. This component is organized into eight banks, each corresponding to eight or nine logical registers. As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The paper defines organizing the component into eight banks with usefulness tables selecting registers for the direction prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Bank weight sums are conditionally scaled by 2.5 if useful or suppressed to 0 if not, and summed into sR to be added into LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that the bank weight summation node feeds an 'x0 or x2.5' multiplier stage before entering the sR cross-bank adder."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Value digests expire after 256 decoded instructions to prevent stale values from degrading accuracy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that each digest is invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source document citation identifies the RUNLTS CBP 2025 conference paper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The source citation matches the title, authors, venue, and publication details verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires writeback and completion signals from the execution unit providing destination register ID and produced value digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that upon instruction completion, the register status table payload is overwritten with the produced value digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires signals at decode notifying when an instruction writing a destination register enters the pipeline and assigning its ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that at decode time, instructions writing registers clear the valid bit and record their ROB index as a tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor interface receives notification of decoded instructions to decrement decay counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Decay tracking requires an instruction decode tick to enforce the 256-instruction invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The signed partial sum output of sR is received by the Statistical Corrector summation tree into LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing \"LSUM\".",
        "why": "Figure 5(d) explicitly lists sR among the component inputs to the adder tree producing LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host interface fallbacks specify computing digests at commit, treating FP as FP64, and decrementing decay counters per fetch block or cycle.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What architectural fallback mechanisms should be employed when host pipelines cannot provide per-instruction writeback snooping or fine-grained decode ticks?",
      "enum_candidates": [
        "commit_digest",
        "per_fetch_block",
        "disable_sr"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage consumed by the sR component is 53,863 bits (43,008 bits WT, 9,360 bits UT, and 1,495 bits auxiliary status table).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 bits x (2^7 + 2^8 + 2^9) x 8 banks = 6 x (128+256+512) x 8 = 43008 bits\n  UT: 6 bits x 65 regs x (2^3 + 2^3 + 2^3) = 9360 bits\n  { valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 in Appendix A itemizes the WT, UT, and auxiliary bits, confirming the total storage cost of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "To maintain iso-storage against baseline TAGE-SC-L, the 53,863 bits are reclaimed by shrinking tagged table banks, reducing high-bank entries, or downsizing bimodal entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which specific baseline predictor structures donate budget to accommodate the 53,863-bit sR component within a fixed 192 KiB capacity?",
      "enum_candidates": [
        "shrink_tagged_banks",
        "reduce_high_bank_entries",
        "downsize_bimodal"
      ]
    },
    {
      "pointer": "/parameters/2",
      "claim": "The sR component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The legal DSE tuning range for num_banks is [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the register banking structure permit power-of-two bank counts other than 8 without modifying the 65-register assignment?",
      "enum_candidates": [
        "4",
        "8",
        "16"
      ]
    },
    {
      "pointer": "/parameters/3",
      "claim": "Each bank of sR has three WT tables with 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify table sizes of 512, 256, and 128 entries for WT0, WT1, and WT2 in each bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The wt_entries parameter accepts alternative candidate configurations '256,128,64', '512,256,128', and '1024,512,256'.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What alternative WT entry sizing configurations are permissible during DSE exploration?",
      "enum_candidates": [
        "512,256,128",
        "256,128,64",
        "1024,512,256"
      ]
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each bank contains three usefulness tables each having 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 confirm each bank contains three usefulness tables of 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The tuning range for ut_entries_per_table is [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the permissible exploration range for UT entry counts per table in tuning?",
      "enum_candidates": [
        "4",
        "8",
        "16",
        "32"
      ]
    },
    {
      "pointer": "/parameters/5",
      "claim": "The weight counter width for WT and UT entries is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in Appendix A explicitly defines the weight width as 6 bits for both WT and UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The weight_width_bits parameter accepts a tuning range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the permissible range of weight counter widths for WT and UT during tuning?",
      "enum_candidates": [
        "5",
        "6",
        "7",
        "8"
      ]
    },
    {
      "pointer": "/parameters/6",
      "claim": "The register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly establishes that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The digest_width_bits parameter has a tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What digest bit-widths within the 14-bit payload capacity are valid candidates for exploration?",
      "enum_candidates": [
        "10",
        "12",
        "14"
      ]
    },
    {
      "pointer": "/parameters/7",
      "claim": "The budget donor choice is configured by an enum with options shrink_tagged_banks, reduce_high_bank_entries, and downsize_bimodal.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which predictor structure should donate storage to offset sR overhead under a fixed budget?",
      "enum_candidates": [
        "shrink_tagged_banks",
        "reduce_high_bank_entries",
        "downsize_bimodal"
      ]
    },
    {
      "pointer": "/parameters/8",
      "claim": "The integer digest leading/trailing count variant choice is configured by an enum with options match_edge_bit, count_zeros_only, and count_ones_only.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should integer leading and trailing bit counters select whether to count zeros or ones when bits are mixed?",
      "enum_candidates": [
        "match_edge_bit",
        "count_zeros_only",
        "count_ones_only"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The integer digest count overflow behavior is configured by an enum with choices saturate and wrap.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Should a 64-bit homogeneous register value count of 64 saturate at 63 or wrap to fit in 6 bits?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "Floating-point format classification is configured by an enum with options nan_boxing, instruction_opcode, and fp_status_reg.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What microarchitectural mechanism determines whether a 64-bit FP register contains FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_boxing",
        "instruction_opcode",
        "fp_status_reg"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The fallback digest variant for unclassified values is configured by an enum with options raw_lsb, zero_digest, and bypass.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What digest pattern should be produced when a floating-point register value cannot be recognized as a valid format?",
      "enum_candidates": [
        "raw_lsb",
        "zero_digest",
        "bypass"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT is organized as 8 banks, each containing 3 direct-mapped tables of 512, 256, and 128 entries of signed 6-bit weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 bits x (2^7 + 2^8 + 2^9) x 8 banks = 6 x (128+256+512) x 8 = 43008 bits",
        "why": "Table 3 and Figure 5(c) confirm the 8-bank organization, table capacities, 6-bit signed weights, and 43,008-bit size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "WT table indexing computes hash0, hash1, and hash2 of PC and digest modulo 512, 256, and 128.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash functions combine PC and register digest to index WT0, WT1, and WT2?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc_hash"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT contains 8 banks of three 8-entry tables, where bank 0 entries hold nine 6-bit weights and banks 1-7 hold eight 6-bit weights totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 bits x 65 regs x (2^3 + 2^3 + 2^3) = 9360 bits",
        "why": "Table 3 in Appendix A establishes the 6-bit weight width across 65 registers and three 8-entry tables totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT table indexing uses hash_u0, hash_u1, and hash_u2 of PC modulo 8.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific skew or hash functions compute the 3-bit indices for UT0, UT1, and UT2 from PC?",
      "enum_candidates": [
        "bit_slice",
        "xor_fold",
        "prime_mod"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "sR_RegStatus is a 65-entry table where each entry contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of { valid (1), payload (14), decay_ctr (8) } totaling 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest formation XOR-folds trailing count at bits [5:0], leading count at bits [8:3], and LSBs at bits [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "trailing one/zero #    [5:0]         6 bits  count of trailing 0s (or 1s)\n  leading one/zero #     [8:3]         6 bits  count of leading  0s (or 1s)\n  Value[5:0]             [11:6]        6 bits  the 6 LSBs of the register",
        "why": "Figure 6(a) transcription defines the 3-field XOR overlap structure at bit offsets 0, 3, and 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Flag register digest replicates 4 condition-code bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly describes replicating the four flag bits three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 register digest extracts bits [31:26] into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP32     Value[31:26]      6 bits        [8:3]         sign(31) + exp[30:26]",
        "why": "Figure 6(b) specifies mapping Value[31:26] into digest bits [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decrements its decay counter on decode steps and clears valid when counting down 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness outputs 0, while a bank with positive usefulness scales its weight sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows the bank weight sum is multiplied by x0 or x2.5 based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed instructions ahead in the ROB retain valid digests across a misprediction pipeline flush recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 explains that execution results of instructions completed before flush resolution remain available upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The update algorithm triggers at branch commit / resolution following TAGE-SC-L operation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L. This section summarizes the novel elements we introduced.",
        "why": "Section 4 establishes that training and update timing inherit the baseline TAGE-SC-L branch resolution/commit protocol."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Only logical registers available at prediction time are trained, and if multiple are available in a bank, one is randomly chosen for single write-port update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states that training updates only available registers and picks one randomly per bank to support single-write-port RAMs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The usefulness table entry weights are incremented when bank prediction matches actual outcome while differing from base prediction, and decremented when bank prediction is incorrect.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact update conditions and step sizes govern the training of register usefulness tables (UT) upon branch outcome resolution?",
      "enum_candidates": [
        "base_diff_conditional",
        "always_on_correct",
        "sc_mispred_only"
      ]
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The update algorithm pseudocode calls undefined helper functions clamp and pseudo_random, hardcodes saturating weight bounds instead of referencing weight_width_bits, and indexes the intra-bank usefulness weight vector with the architectural register ID instead of the intra-bank register index.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/4/pseudocode",
        "value": "function clamp(val, min_val, max_val):\n    if val < min_val:\n        return min_val\n    if val > max_val:\n        return max_val\n    return val\n\nfunction pseudo_random():\n    // 64-bit linear congruential generator using Table 2 RNG seed\n    global rng_seed\n    rng_seed = (rng_seed * 6364136223846793005 + 1) & 0xFFFFFFFFFFFFFFFF\n    return (rng_seed >> 32) & 0xFFFFFFFF\n\nfunction update(PC, actual_taken, sc_needs_update, sc_correct, base_correct):\n    if not sc_needs_update:\n        return\n\n    min_weight = -(1 << (weight_width_bits - 1))\n    max_weight = (1 << (weight_width_bits - 1)) - 1\n\n    for b = 0 to 7:\n        avail = branch_context.sR_available_regs[b]\n        if len(avail) == 0:\n            continue\n\n        // Paper Section 4.2: If multiple registers were available, randomly select one for single-port update\n        reg_to_update = avail[pseudo_random() % len(avail)]\n        digest = sR_RegStatus[reg_to_update].payload & 0x0FFF\n\n        w_idx0 = hash0(PC, digest) % 512\n        w_idx1 = hash1(PC, digest) % 256\n        w_idx2 = hash2(PC, digest) % 128\n\n        // 1. Update WT saturating counter entries: +1 if taken, -1 if not taken\n        step = actual_taken ? +1 : -1\n        sR_WT[b].WT0[w_idx0] = clamp(sR_WT[b].WT0[w_idx0] + step, min_weight, max_weight)\n        sR_WT[b].WT1[w_idx1] = clamp(sR_WT[b].WT1[w_idx1] + step, min_weight, max_weight)\n        sR_WT[b].WT2[w_idx2] = clamp(sR_WT[b].WT2[w_idx2] + step, min_weight, max_weight)\n\n        // 2. Update UT usefulness tables\n        u_idx0 = hash_u0(PC) % 8\n        u_idx1 = hash_u1(PC) % 8\n        u_idx2 = hash_u2(PC) % 8\n\n        reg_slot = reg_to_update >> 3\n\n        bank_pred_taken = (branch_context.sR_bank_sum[b] >= 0)\n        u_step = 0\n        if bank_pred_taken == actual_taken and bank_pred_taken != base_correct:\n            u_step = +1\n        elif bank_pred_taken != actual_taken:\n            u_step = -1\n\n        if u_step != 0:\n            sR_UT[b].UT0[u_idx0][reg_slot] = clamp(sR_UT[b].UT0[u_idx0][reg_slot] + u_step, min_weight, max_weight)\n            sR_UT[b].UT1[u_idx1][reg_slot] = clamp(sR_UT[b].UT1[u_idx1][reg_slot] + u_step, min_weight, max_weight)\n            sR_UT[b].UT2[u_idx2][reg_slot] = clamp(sR_UT[b].UT2[u_idx2][reg_slot] + u_step, min_weight, max_weight)"
      },
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+orphan+algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the ...

[Init]
model=gemini-3.8-flash-medium conversation=26610fb6-45db-408c-90ca-03b0840ce6f8 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the Statistical Corrector by capturing correlations between recently produced register values and branch directions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The paper explicitly states that the novel prediction method captures correlations between register values and branch directions by integrating value digests into the SC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The predictor maintains a 65-entry Tomasulo-like register status table tracking whether logical registers R0-R64 hold a 12-bit digest or a 14-bit tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies a dedicated Tomasulo-like table with one entry per logical register holding a valid bit and a 14-bit tag or 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Logical registers are partitioned across 8 banks, each using 3 usefulness tables (UT0-UT2) to select the most useful
... [truncated]

[Usage]
{"input_tokens": 30062, "output_tokens": 48048, "thinking_tokens": 40073, "cache_read_tokens": 0, "total_tokens": 78110}

[Result]
status=SUCCESS conversation=26610fb6-45db-408c-90ca-03b0840ce6f8 turns=1 duration=225.382784424s usage={"input_tokens": 30062, "output_tokens": 48048, "thinking_tokens": 40073, "cache_read_tokens": 0, "total_tokens": 78110}


