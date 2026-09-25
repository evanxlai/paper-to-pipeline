success: True
usage: {'input_tokens': 30079, 'output_tokens': 39063, 'thinking_tokens': 33862, 'cache_read_tokens': 0, 'total_tokens': 69142}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The sR predict algorithm is triggered at branch lookup time when the branch predictor queries the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper explicitly states that the table is queried at prediction time to forward valid digests to the SC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict algorithm partitions logical registers across 8 banks and selects the register with the highest usefulness sum in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the 8-bank organization and explains that the digest of the most useful register among those available is selected."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Predict subscripts the usefulness tables UT0, UT1, UT2 with the absolute register identifier r (0..64) rather than the register index within the bank (0..8 for bank 0, 0..7 for banks 1..7).",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "In /state/1, each usefulness table entry is defined as an 8- or 9-element vector of weights for the registers mapped to that bank, but /algorithms/3/pseudocode indexes UT0, UT1, and UT2 directly with global register identifier r (which reaches 64), causing an out-of-bounds access."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "function predict_sR(PC):\n  sR_sum = 0\n  // Process each of the 8 banks independently\n  for bank_id in 0..7:\n    // Bank registers: r with r % 8 == bank_id, r in 0..64\n    // Bank 0 has 9 registers; Banks 1-7 have 8 registers\n    bank_regs = [r for r in 0..64 if r % 8 == bank_id]\n    \n    // Determine which registers currently have valid digests\n    available_regs = [r for r in bank_regs if reg_status_table[r].valid == 1]\n    \n    if len(available_regs) == 0:\n      continue // Bank contributes 0 if no registers have valid digests\n      \n    // Look up usefulness vector for registers in this bank\n    ut_idx0 = hash_UT(PC, 0) % 8\n    ut_idx1 = hash_UT(PC, 1) % 8\n    ut_idx2 = hash_UT(PC, 2) % 8\n    \n    best_reg = -1\n    max_usefulness = -1000\n    for r in available_regs:\n      reg_pos = r / 8\n      u = sR_UT[bank_id].UT0[ut_idx0][reg_pos] + sR_UT[bank_id].UT1[ut_idx1][reg_pos] + sR_UT[bank_id].UT2[ut_idx2][reg_pos]\n      if u > max_usefulness:\n        max_usefulness = u\n        best_reg = r\n        \n    // Lookup prediction weight tables for best_reg\n    digest = reg_status_table[best_reg].payload & 0xFFF\n    h0 = hash(PC, digest, 0) % 512\n    h1 = hash(PC, digest, 1) % 256\n    h2 = hash(PC, digest, 2) % 128\n    \n    bank_sum = sR_WT[bank_id].WT0[h0] + sR_WT[bank_id].WT1[h1] + sR_WT[bank_id].WT2[h2]\n    \n    // Scale bank contribution: x2.5 if bank usefulness is positive, else x0\n    if max_usefulness > 0:\n      scaled_bank_sum = bank_sum * 2.5 // [assumed: fixed-point / integer 2.5x scaling]\n    else:\n      scaled_bank_sum = 0\n      \n    sR_sum += scaled_bank_sum\n    \n  return sR_sum"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Each bank sum is scaled by x2.5 if that bank's max usefulness is positive, and suppressed to x0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U2 marks the control wire driving the x0 vs x2.5 scaling stage as UNCERTAIN because the figure does not explicitly label it."
      },
      "patch": null,
      "open_question": "Does the x0 vs x2.5 scaling stage select dynamically based on the bank's own usefulness being positive, or is a global static scale of 2.5 applied?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "The sR partial sum is accumulated directly into LSUM alongside the other statistical corrector components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing\n\"LSUM\".",
        "why": "Figure 5(d) literally shows sR summed into LSUM with sB, sG, sP, sC, sI, sL, sS, and sT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The reg_status_table contains 65 entries corresponding to 64 architectural INT/FP registers plus 1 condition-code flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries for the register status auxiliary data structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each reg_status_table entry holds a 1-bit valid flag, a 14-bit payload (storing either a 14-bit ROB index or a 12-bit digest), and an 8-bit saturating decay counter for 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies the exact entry bit widths, matching Section 4.2's description of the 14-bit tag, 12-bit digest, and 256-instruction decay invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The reg_status_table occupies 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The entry bit widths sum to 23 bits per entry, which across 65 entries yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The reg_status_table is directly indexed by logical register identifier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 states that the table contains one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "sR_UT comprises 8 banks where each bank contains 3 usefulness tables (UT0, UT1, UT2) of 8 entries each, storing a vector of 6-bit weights for all registers mapped to that bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 lists 3 tables of 2^3 entries per bank storing 6-bit weights across all 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "Each usefulness entry holds 6-bit signed saturating counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6 bits per weight entry in the usefulness weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "Total storage capacity for sR_UT is 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "6 bits * 65 registers * 24 total entries across UT0..UT2 equals 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "sR_UT tables are indexed by a skewed PC hash.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "Figure 5(c) literally labels the indexing input to the usefulness tables as PC (skewed)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_WT contains 8 banks with 3 prediction weight tables per bank: WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies entry counts 2^7, 2^8, and 2^9 for the 3 WT tables across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each WT entry is a 6-bit signed saturating counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies a 6-bit weight width for the WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "Total storage capacity for sR_WT is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * (128 + 256 + 512 entries) * 8 banks equals 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "WT tables are indexed by hashing the PC together with the selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"PC + reg. digest\",\n    hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) literally shows PC + reg. digest hashed into h0, h1, and h2 to index the three WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 establishes that the component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default entry count for WT0 is 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the largest WT table with 2^9 (512) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default entry count for WT1 is 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the middle WT table with 2^8 (256) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default entry count for WT2 is 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the smallest WT table with 2^7 (128) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default entry count for each usefulness table is 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines 3 usefulness tables per bank with 2^3 (8) entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The register value digest size is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly establishes that each digest is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The 12-bit integer register digest XOR-folds 6 bits of trailing zero count at [5:0], 6 bits of leading zero count at [8:3], and 6 bits of register LSBs at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three field boxes drawn stacked and horizontally offset from one\nanother, joined by two circled-plus (XOR) symbols:",
        "why": "Figure 6(a) literally specifies the three 6-bit fields offset and combined using XOR into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The flag register digest is generated by replicating the 4-bit condition code flags three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly states this replication rule."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For 64-bit FP registers, the extracted 9-bit slice [63:55] is placed at digest bit positions [11:3] with bits [2:0] set to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U4 explicitly marks the right-alignment at bit position 3 as UNCERTAIN, noting an alternative reading where fields are right-aligned at bit 0."
      },
      "patch": null,
      "open_question": "Are floating-point digest bit slices right-aligned at digest bit position 3 or right-aligned at bit position 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest saturates and expires after 256 decoded instructions without update, clearing its valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly specifies invalidation after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank contributions are scaled by x0 when the bank's usefulness sum is non-positive and by x2.5 when positive.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U2 marks the control of the x0 vs x2.5 multiplier as UNCERTAIN because the driving wire is not explicitly labeled."
      },
      "patch": null,
      "open_question": "Does bank contribution scaling select between x0 and x2.5 based on whether the bank's usefulness sum is positive, or is a global static scale applied?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers in a bank are available at prediction time, the training algorithm randomly selects exactly one register to update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly defines the single-port random selection update rule."
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
model=gemini-3.8-flash-medium conversation=fe3447a8-8128-405e-91e9-b343f2db2766 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The sR predict algorithm is triggered at branch lookup time when the branch predictor queries the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper explicitly states that the table is queried at prediction time to forward valid digests to the SC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict algorithm partitions logical registers across 8 banks and selects the register with the highest usefulness sum in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the 8-bank organization and explains that the digest of the most useful register among those available is selected."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Predict subscripts the usefulness tables UT0, UT1, UT2 with the absolute register identifier r (0..64) rather than the register index within the bank (0..8 for bank 0, 0..7 for banks 1..7).",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "In /state/1, each usefulness table entry is defined as an 8- or 9-element vector of weights for the registers mapped to that bank, but /algorithms/3/pseudocode indexes UT0, UT1, and UT2 directly with global register identifier r (which reaches 64), causing an out-of-bounds access."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algor
... [truncated]

[Usage]
{"input_tokens": 30079, "output_tokens": 39063, "thinking_tokens": 33862, "cache_read_tokens": 0, "total_tokens": 69142}

[Result]
status=SUCCESS conversation=fe3447a8-8128-405e-91e9-b343f2db2766 turns=1 duration=202.215529717s usage={"input_tokens": 30079, "output_tokens": 39063, "thinking_tokens": 33862, "cache_read_tokens": 0, "total_tokens": 69142}


