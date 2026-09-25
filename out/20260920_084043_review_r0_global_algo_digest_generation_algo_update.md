success: True
usage: {'input_tokens': 31293, 'output_tokens': 38670, 'thinking_tokens': 30676, 'cache_read_tokens': 0, 'total_tokens': 69963}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The register component sR enhances the Statistical Corrector by capturing correlations between recently produced register values and branch directions using 12-bit compressed digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The quote directly confirms that sR integrates into the SC and predicts using short digests that capture correlations between register values and branch directions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Registers are partitioned across eight banks, each choosing the most useful available register to index prediction weight tables, whose positive-usefulness contributions are scaled by 2.5 and decay after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers. As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The quote settles the 8-bank organization and the dual usefulness and direction prediction table structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature specification source is the paper RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title and citation match the header and published proceedings of the CBP 2025 paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "At decode time, an instruction writing a logical register stores its ROB index as a tag and clears the valid bit in the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The quote defines the decode-time host interface requirements for register writes verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "Upon instruction completion, functional units provide the produced value to overwrite the payload with its digest and set the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The quote specifies that writeback/completion overwrites the tag with the value digest and sets the entry valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "The host signals decoded instruction counts to invalidate register digests after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote settles that register digest entries decay and are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "The host provides notifications of squashed ROB tags on branch mispredictions to recover the Tomasulo-like table.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that recovering the Tomasulo-like register status table is future work and does not specify a misprediction recovery interface."
      },
      "patch": null,
      "open_question": "How should the register status and digest table recover its state when in-flight instructions are squashed due to a branch misprediction?",
      "enum_candidates": [
        "flush_all_in_flight",
        "rob_tag_walk",
        "checkpoint"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Component sR requires 53,863 total storage bits consisting of 43,008 WT bits, 9,360 UT bits, and 1,495 auxiliary data bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in Appendix A directly itemizes the exact bit formulas and totals for WT, UT, auxiliary data, and the sum 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation triggers when instruction execution completes and a register value is produced at a functional unit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The quote establishes that completion time is the trigger for digest generation and table update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digests are formed by XOR-folding a 6-bit count of trailing zeros/ones, a 6-bit count of leading zeros/ones shifted by 3, and 6 LSBs shifted by 6 into 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that trailing counts occupy [5:0], leading counts occupy [8:3], and LSB6 occupies [11:6], XOR-folded together."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Pseudocode calls 'bits(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The token 'bits' in the pseudocode occurs only inside the English comment '// Count trailing and leading identical bits (zeros or ones)' and is not a function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Pseudocode calls 'format(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The token 'format' in the pseudocode occurs only inside the English comment '// Inspect MSBs to classify FP format (...)' and is not a function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Pseudocode calls 'generate_digest(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values. RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "'generate_digest' is the signature of the function defined by the algorithm, not an unresolved external call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Pseudocode calls 'return(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "'return' is a standard language control statement returning parenthesized expressions, not an undefined helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The functions count_leading_zeros_or_ones and count_trailing_zeros_or_ones unambiguously compute 6-bit counts of zeros or ones.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper does not define whether the count saturates at 63, counts bits matching the MSB/LSB, or how zeros versus ones are distinguished in 6 bits."
      },
      "patch": null,
      "open_question": "How are identical bits counted and encoded into 6 bits when a 64-bit word can have up to 64 identical leading or trailing bits?",
      "enum_candidates": [
        "count_match_sign",
        "count_zeros_only",
        "saturate_63"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register format is classified into FP16, FP32, or FP64 by inspecting most significant bits, placing the sign bit and top exponent bits at digest bits [5:3], [8:3], and [11:3] respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) define extracting Val[15:13], Value[31:26], and Value[63:55] for FP16, FP32, and FP64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The specific bit inspection rule to classify 64-bit floating-point registers into FP16, FP32, or FP64 is settled.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper states that format classification inspects the MSBs but gives no bit pattern, masking rule, or classification function."
      },
      "patch": null,
      "open_question": "What specific bit pattern check or host architectural metadata classifies a floating-point register into FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_boxing",
        "instruction_type",
        "opcode_metadata"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition-code flag digests replicate the 4 flag bits three times to fill 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly defines the flag digest as a 3-way replication of the 4 flag bits into 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table contains 65 entries covering logical registers R0 to R64, each entry holding 1 valid bit, a 14-bit payload, and an 8-bit decay counter for a total of 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 and Section 4.2 specify 65 entries with valid(1), payload(14), and decay_ctr(8), totaling 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness weight tables UT are partitioned across 8 banks with 3 tables of 8 entries each, storing 6-bit signed weights for all 65 registers totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Section 4.2, Figure 5(c), and Table 3 specify 8 banks with three 8-entry tables holding vectors of 6-bit weights for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction weight tables WT are partitioned across 8 banks, each containing tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit signed weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 explicitly confirm the three table sizes (512, 256, 128) and 6-bit width across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "Parameter num_banks defaults to 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 specifies an 8-bank organization."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Parameter num_logical_registers defaults to 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in Appendix A explicitly uses 65 registers in the storage breakdown."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Parameter wt_weight_width defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6 bits per WT entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Parameter ut_weight_width defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6 bits per UT entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Parameter wt_entries defaults to 512, 256, 128 entries for WT0, WT1, and WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify table sizes 2^9 (512), 2^8 (256), and 2^7 (128)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest calculation on 0x0000000000000008 produces trailing_cnt=3, leading_cnt=60, lsb6=8, and digest=0x3E3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) XOR folds trailing zeros [5:0] (3), leading zeros [8:3] (60 << 3 = 0x1E0), and LSB6 [11:6] (8 << 6 = 0x200), yielding 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Flag digest replication on 0x9 replicates the nibble three times to produce 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 0x9 across three 4-bit fields yields 0x999 as stated in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 digest extraction maps bits [63:55] to digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies extracting Value[63:55] aligned to digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Registers are mapped to banks via modulo 8, placing 9 registers in Bank 0 and 8 registers in Banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Figure 5(c) and Section 4.2 show bank 0 containing R0, R8, ..., R64 and each other bank containing 8 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Digest entries transition from valid to invalid after exactly 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote confirms that validity expires precisely at the 256-instruction mark."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank with non-positive usefulness (sum of UT weights <= 0) has its contribution scaled by x0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows multiplier 'x0 or x2.5', but the paper never defines whether the threshold condition selecting x0 is usefulness <= 0, usefulness < 0, or another threshold."
      },
      "patch": null,
      "open_question": "What exact threshold condition on usefulness selects multiplier x0 versus x2.5 for a bank's contribution?",
      "enum_candidates": [
        "usefulness_gt_0",
        "usefulness_gte_0",
        "confidence_threshold"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank with positive usefulness scales its prediction weight sum by x2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) confirms that a useful bank scales its WT sum by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Update triggers at branch resolution / commit time on SC mispredictions or when |LSUM| is below the update threshold.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L. This section summarizes the novel elements we introduced.",
        "why": "Section 4 establishes that SC update triggers follow the standard TAGE-SC-L policy using update thresholds (itemized in Table 3)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "During training, one register among those available at prediction time is randomly selected per bank to update correlations.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The quote defines the training rule selecting one available register at random per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Pseudocode calls 'UT(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "'UT' refers to the multidimensional usefulness table array defined in state/1, not an undefined helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Pseudocode calls 'if(...)' as an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "'if' in the pseudocode is a standard conditional control expression, not a helper function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Pseudocode calls 'update_sR(...)' as an undefined policy call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "'update_sR' is the declaration signature of algorithm 5 itself, not an unresolved external policy call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Helpers register_index_in_bank and saturating_add are called without definitions in the algorithm.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The bank register index calculation reg_id // 8 and saturating counter arithmetic are used in pseudocode but never explicitly defined."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "function saturating_add(ref_val, delta, min_val, max_val):\n    return min(max_val, max(min_val, ref_val + delta))\n\nfunction register_index_in_bank(reg_id, bank_id):\n    return reg_id // 8\n\nfunction update_sR(branch_pc, actual_dir, sc_correct, pred_snapshot):\n    for b = 0 to 7:\n        valid_regs = pred_snapshot.bank_valid_regs[b]\n        if valid_regs is empty:\n            continue\n        \n        // Training rule: randomly select one available register within the bank\n        reg_to_update = valid_regs[random_choice(len(valid_regs))]\n        sub_idx = register_index_in_bank(reg_to_update, b)\n        \n        idx0 = hash_ut(branch_pc, 0, b)\n        idx1 = hash_ut(branch_pc, 1, b)\n        idx2 = hash_ut(branch_pc, 2, b)\n        \n        // Update usefulness weights in UT (increment if this bank predicted correctly, decrement if wrong)\n        ut_dir = +1 if (sc_correct) else -1\n        UT[b][0][idx0][sub_idx] = saturating_add(UT[b][0][idx0][sub_idx], ut_dir, -32, 31)\n        UT[b][1][idx1][sub_idx] = saturating_add(UT[b][1][idx1][sub_idx], ut_dir, -32, 31)\n        UT[b][2][idx2][sub_idx] = saturating_add(UT[b][2][idx2][sub_idx], ut_dir, -32, 31)\n        \n        // Update prediction weights in WT for this register's digest\n        digest = reg_table[reg_to_update].payload & 0x0FFF\n        h0 = hash_wt(branch_pc, digest, 0) % 512\n        h1 = hash_wt(branch_pc, digest, 1) % 256\n        h2 = hash_wt(branch_pc, digest, 2) % 128\n        \n        wt_dir = +1 if (actual_dir == TAKEN) else -1\n        WT[b][0][h0] = saturating_add(WT[b][0][h0], wt_dir, -32, 31)\n        WT[b][1][h1] = saturating_add(WT[b][1][h1], wt_dir, -32, 31)\n        WT[b][2][h2] = saturating_add(WT[b][2][h2], wt_dir, -32, 31)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness weights in UT are trained by incrementing when sc_correct is true and decrementing when false.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The paper does not state whether UT weights update based on overall SC correctness, individual bank correctness, or TAGE/SC disagreement."
      },
      "patch": null,
      "open_question": "What training condition and direction determine when and how UT usefulness weights are incremented or decremented?",
      "enum_candidates": [
        "sc_correct",
        "bank_correct",
        "tage_sc_disagree"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Functions hash_ut and hash_wt compute indices for the UT and WT tables.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "The paper notes that PC and digest are hashed into h0, h1, and h2, but does not specify the hashing functions or polynomial XOR equations."
      },
      "patch": null,
      "open_question": "What hash functions are used to index the UT and WT tables from PC, register ID, and register digest?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+algo:digest_generation+algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they...

[Init]
model=gemini-3.8-flash-medium conversation=c4c8e62b-63d0-4b2c-9815-b21d7620ebbc cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_01cec91a605a3d5d

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The register component sR enhances the Statistical Corrector by capturing correlations between recently produced register values and branch directions using 12-bit compressed digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The quote directly confirms that sR integrates into the SC and predicts using short digests that capture correlations between register values and branch directions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Registers are partitioned across eight banks, each choosing the most useful available register to index prediction weight tables, whose positive-usefulness contributions are scaled by 2.5 and decay after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers. As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The quote settles the 8-bank organization and the dual usefulness and direction prediction table structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature specification source is the paper RUNLTS: Register-value-aware Predictor Utili
... [truncated]

[Usage]
{"input_tokens": 31293, "output_tokens": 38670, "thinking_tokens": 30676, "cache_read_tokens": 0, "total_tokens": 69963}

[Result]
status=SUCCESS conversation=c4c8e62b-63d0-4b2c-9815-b21d7620ebbc turns=1 duration=199.129306124s usage={"input_tokens": 31293, "output_tokens": 38670, "thinking_tokens": 30676, "cache_read_tokens": 0, "total_tokens": 69963}


