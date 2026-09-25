success: True
usage: {'input_tokens': 28404, 'output_tokens': 36449, 'thinking_tokens': 30061, 'cache_read_tokens': 0, 'total_tokens': 64853}

## result
```json
{
  "records": [
    {
      "pointer": "/state/0",
      "claim": "The register status and digest table is a direct-mapped table of 65 entries corresponding to 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly states that the dedicated tracking table contains one entry per logical register, which totals 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of the register status table consists of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry format of the auxiliary register status table as 1 bit valid, 14 bits payload, and 8 bits decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries of 23 bits each (1 + 14 + 8) multiply out to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table is indexed directly by architectural/logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one dedicated entry per logical register establishes direct indexing by register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The usefulness weight table (UT) is partitioned into 8 banks with 3 tables (UT0, UT1, UT2) of 8 entries each, where Bank 0 covers 9 registers and Banks 1-7 cover 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) specifies three 8-entry tables with Bank 0 having 9 registers and subsequent banks having 8."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Each UT entry stores 6-bit signed saturating weights for each register assigned to that bank, totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit weights across 65 registers and three 8-entry tables, equaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT0, UT1, and UT2 are indexed by a specific skewed hash function hash_ut(PC, table_id, bank_id) mod 8.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) labels the UT input as 'PC (skewed)' into 8-entry tables, but the paper does not define the bitwise hash or skew function hash_ut.",
      "enum_candidates": [
        "xor_fold",
        "linear",
        "prime_mod"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The prediction weight table (WT) consists of 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit signed weights, consuming 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT configuration as 8 banks of 128, 256, and 512 entries of 6-bit weights, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT0, WT1, and WT2 are indexed by specific hash functions combining PC and the selected 12-bit register digest modulo table size.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) states that PC and reg digest are hashed into h0, h1, h2, but does not specify the hashing algorithm."
      },
      "patch": null,
      "open_question": "What bitwise hash function hash_wt should combine the branch PC and 12-bit register digest to index WT0, WT1, and WT2?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc32"
      ]
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly fixes the register component organization to eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The parameter num_banks has a tunable search range of [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper only implements 8 banks and does not define a tuning range across power-of-two bank counts."
      },
      "patch": null,
      "open_question": "The paper fixes the architecture to 8 banks; is the parameter range [4, 16] pow2 an intended search dimension for tuning or should num_banks be fixed at 8?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the register component budgeting based on 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The parameter num_logical_registers has a legal architectural range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The paper hardcodes 65 logical registers for CBP2025 traces and does not evaluate other register counts."
      },
      "patch": null,
      "open_question": "The paper hardcodes 65 logical registers for CBP2025; is the range [32, 128] intended for porting to other ISAs or should num_logical_registers be fixed at 65?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default usefulness multiplier for useful bank contributions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly specifies 2.5 as the scaling multiplier when usefulness is positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The parameter useful_multiplier has a tunable range of [1.0, 4.0].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The paper uses only 2.5 and does not state or explore a range between 1.0 and 4.0."
      },
      "patch": null,
      "open_question": "The paper specifies a fixed multiplier of 2.5; is the range [1.0, 4.0] an intended search space for the tuning stage?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default WT weight width is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies 6 bits per WT weight."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The parameter wt_weight_width has a tunable range of [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The paper specifies 6 bits for WT weights and does not evaluate alternative widths."
      },
      "patch": null,
      "open_question": "The paper fixes WT weight width to 6 bits; is [4, 8] an intended exploration range for tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default UT weight width is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies 6 bits per UT register weight."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter ut_weight_width has a tunable range of [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The paper specifies 6 bits for UT weights and does not evaluate alternative widths."
      },
      "patch": null,
      "open_question": "The paper fixes UT weight width to 6 bits; is [4, 8] an intended exploration range for tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default WT entry count configuration is 512, 256, and 128 entries across the three tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) specifies WT0 with 512 entries, WT1 with 256 entries, and WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The parameter wt_entries has choices: 256,128,64 | 512,256,128 | 1024,512,256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The paper does not mention alternative halved or doubled table entry capacities."
      },
      "patch": null,
      "open_question": "The paper specifies 512, 256, 128 entries; are 256,128,64 and 1024,512,256 intended search candidates for tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The register prediction algorithm triggers at branch fetch / prediction time during the SC evaluation phase.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 states that whenever the branch predictor queries the table, valid entries forward digests to SC components to make predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "For each bank, the register component selects the valid register with the highest sum of usefulness weights from UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 explains that the component picks the digest of the most useful register among available registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Bank contribution is scaled by 2.5 when the selected register usefulness is positive, and suppressed (x0) otherwise, with bank contributions summing into sR to feed SC LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing \"LSUM\".",
        "why": "Figure 5(d) shows sR summing directly with other SC components into LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The identifier 'predict_sR' represents an undefined external helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The identifier 'predict_sR' is the name of the prediction routine itself defined on line 1 of the pseudocode, not an external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The word 'suppressed' represents a call to an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The occurrence of 'suppressed' in pseudocode was in an inline comment explaining the x0 multiplier, not an executable function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The functions registers_of_bank(b) and register_index_in_bank(r, b) are undefined in the spec and need explicit register stride arithmetic.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/4/pseudocode",
        "value": "function predict_sR(branch_pc):\n    sR_sum = 0\n    for b = 0 to 7:\n        // Bank 0 covers 9 registers (k=0..8: R0, R8, ..., R64); Banks 1-7 cover 8 registers (k=0..7: R[b + 8*k])\n        num_regs_in_bank = 9 if b == 0 else 8\n        bank_valid_regs = []\n        for k = 0 to num_regs_in_bank - 1:\n            r = b + 8 * k\n            if reg_table[r].valid == 1:\n                bank_valid_regs.append((r, k))\n        \n        if len(bank_valid_regs) == 0:\n            continue // Bank contribution is 0 (x0)\n        \n        // Query UT0, UT1, UT2 for this bank\n        idx0 = hash_ut(branch_pc, 0, b)\n        idx1 = hash_ut(branch_pc, 1, b)\n        idx2 = hash_ut(branch_pc, 2, b)\n        \n        best_reg = NULL\n        max_useful = -9999\n        for (r, k) in bank_valid_regs:\n            u = UT[b][0][idx0][k] + UT[b][1][idx1][k] + UT[b][2][idx2][k]\n            if u > max_useful:\n                max_useful = u\n                best_reg = r\n        \n        // Record chosen register and bank availability for training update\n        pred_snapshot.bank_valid_regs[b] = [r for (r, k) in bank_valid_regs]\n        pred_snapshot.selected_reg[b] = best_reg\n        pred_snapshot.max_useful[b] = max_useful\n        \n        // Select digest and compute bank WT contribution\n        if max_useful > 0:\n            digest = reg_table[best_reg].payload & 0x0FFF\n            h0 = hash_wt(branch_pc, digest, 0) % 512\n            h1 = hash_wt(branch_pc, digest, 1) % 256\n            h2 = hash_wt(branch_pc, digest, 2) % 128\n            \n            w_sum = WT[b][0][h0] + WT[b][1][h1] + WT[b][2][h2]\n            bank_contrib = floor(w_sum * 2.5)\n            sR_sum += bank_contrib\n        else:\n            // Non-useful bank contribution is suppressed by multiplying by 0\n            pass\n            \n    return sR_sum"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The bank contribution scaling w_sum * 2.5 uses the floor function for integer conversion.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) labels the multiplier as 2.5 without specifying whether hardware truncation, floor, or rounding is used."
      },
      "patch": null,
      "open_question": "How should the product w_sum * 2.5 be rounded to integer in hardware?",
      "enum_candidates": [
        "floor",
        "trunc",
        "round_nearest"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer register value 0x8, the 12-bit digest is generated by XOR-folding trailing zero count (bits [5:0]), leading zero count shifted by 3 (bits [8:3]), and value[5:0] shifted by 6 (bits [11:6]), producing 0x3E3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "trailing one/zero #    [5:0]         6 bits  count of trailing 0s (or 1s)",
        "why": "Figure 6(a) transcription establishes the bit positions and overlap of trailing count, leading count, and value bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For condition-code flag registers, the 4-bit flag value is replicated three times across the 12-bit digest, turning 0x9 into 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly specifies 3x replication of the four flag bits to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For FP64 registers, the sign bit and top 8 exponent bits (value bits [63:55]) are extracted and mapped to digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP64     Value[63:55]      9 bits        [11:3]        sign(63) + exp[62:55]",
        "why": "Figure 6(b) transcription maps Value[63:55] of FP64 registers directly to digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Logical registers map to 8 banks via stride-8 indexing (r mod 8), placing 9 registers in Bank 0 (R0, R8, ..., R64) and 8 registers in Banks 1-7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Bank 0's register list \"R0, R8, R16, ... R64\" is a stride-8 sequence, i.e. bank i holds the logical registers r with r mod 8 == i.",
        "why": "Figure 5(c) transcription confirms stride-8 register bank assignment across the 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A register digest entry is invalidated (valid bit transitions to 0) after exactly 256 instructions have been decoded since it was written.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly defines the decay invalidation period as 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When the maximum usefulness among valid registers in a bank is non-positive (<= 0), the bank's WT contribution is suppressed (multiplied by 0).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that a bank's contribution is scaled by x0 when its usefulness is non-positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When the maximum usefulness among valid registers in a bank is positive (> 0), the bank's WT weight sum is scaled by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that a bank's contribution is scaled by 2.5 when its usefulness is positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.8-flash-medium conversation=52f04288-d314-46d0-b252-efbc05e6bd5a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_01cec91a605a3d5d

[Response]
```json
{
  "records": [
    {
      "pointer": "/state/0",
      "claim": "The register status and digest table is a direct-mapped table of 65 entries corresponding to 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly states that the dedicated tracking table contains one entry per logical register, which totals 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of the register status table consists of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry format of the auxiliary register status table as 1 bit valid, 14 bits payload, and 8 bits decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries of 23 bits each (1 + 14 + 8) multiply out to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table is indexed directly by architectural/logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one dedicated entry per logical register establishes direct indexing by register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_c
... [truncated]

[Usage]
{"input_tokens": 28404, "output_tokens": 36449, "thinking_tokens": 30061, "cache_read_tokens": 0, "total_tokens": 64853}

[Result]
status=SUCCESS conversation=52f04288-d314-46d0-b252-efbc05e6bd5a turns=1 duration=172.249374726s usage={"input_tokens": 28404, "output_tokens": 36449, "thinking_tokens": 30061, "cache_read_tokens": 0, "total_tokens": 64853}


