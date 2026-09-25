success: True
usage: {'input_tokens': 33390, 'output_tokens': 43055, 'thinking_tokens': 38262, 'cache_read_tokens': 0, 'total_tokens': 76445}

## result
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is titled RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables presented at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title verbatim matches the source specification reference."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component integrates into the statistical corrector (SC) using register-value digests to correlate branch outcomes with recently produced register values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To exploit correlations with register values, we feed not only the PC and branch history but also register-value digests into the SC.",
        "why": "The paper explicitly states that register-value digests are provided to the SC to exploit correlations with register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A dedicated table tracking register status invalidates digests after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms that each digest is invalidated after 256 decoded instructions to prevent degradation from stale data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "When a bank's usefulness is positive, its weight sum is scaled by 2.5, otherwise suppressed to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) illustrates a multiplier stage of 'x0 or x2.5' per bank but does not label the wire selecting between x0 and x2.5; whether positive bank usefulness or another condition drives this selection is unresolved in the paper text.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/host_interfaces",
      "claim": "When an instruction writing a logical register is decoded, it writes its ROB index as a tag and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies the decode interface requirements for instructions producing register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "When an instruction completes execution, the payload is overwritten with the produced value digest and the valid bit is set.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the completion interface signaling the receipt of the register digest and setting valid to 1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host interface tracks decoded instructions to invalidate digests after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms the necessity of tracking 256 decoded instructions to invalidate stale entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage cost of sR is 53,863 bits, comprising 43,008 bits of WT, 9,360 bits of UT, and 1,495 bits of auxiliary data.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 accounts for all components of sR, providing the exact formulas and total storage of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "NUM_BANKS defaults to 8 banks for the register component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper establishes that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT0_ENTRIES defaults to 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 establishes that the largest WT table has 2^9 (512) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT1_ENTRIES defaults to 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 establishes that the intermediate WT table has 2^8 (256) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "WT2_ENTRIES defaults to 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 establishes that the smallest WT table has 2^7 (128) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "UT_ENTRIES defaults to 8 entries per usefulness table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 establishes three usefulness tables with 2^3 (8) entries each per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "DIGEST_BITS defaults to 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly states that the register digest length is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "reg_status_table contains 65 entries, each with a 1-bit valid flag, 14-bit payload, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure as valid (1 bit), payload (14 bits), and decay_ctr (8 bits) across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT stores 6-bit signed weights across 3 tables of 8 entries for each of the 65 registers partitioned across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 establishes that UT consists of three 8-entry tables of 6-bit weights for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_WT comprises 8 banks of three prediction tables with 512, 256, and 128 entries of 6-bit counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 establishes that WT consists of 8 banks each having tables of 2^7, 2^8, and 2^9 entries of 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flags, the digest is generated by replicating the 4-bit flag register three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper directly specifies the 3x replication of the four flag bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digest generation masks count of trailing zeros and leading zeros to 6 bits with & 0x3F without distinguishing zeros versus ones.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 6-bit count fields encoded for registers having up to 64 identical bits, and does the implementation count zeros only or dynamically count bits matching the MSB and LSB?",
      "enum_candidates": [
        "saturate",
        "modulo",
        "match_sign"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digest generation places extracted sign and exponent bits right-aligned at bit position 3 with bits [2:0] set to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) draws FP slices right-aligned at bit position 3, but the text does not state whether FP fields are positioned at digest[11:3] leaving bits [2:0] as zero or right-aligned at bit 0.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In predict_sR, usefulness tables UT0, UT1, and UT2 are indexed directly by logical register id r ranging 0..64, contradicting the declared table entry dimension of 9 elements.",
      "verdict": "INCONSISTENT",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "function predict_sR(PC):\n  sR_sum = 0\n  for bank_id in 0..7:\n    bank_regs = [r for r in 0..64 if r % 8 == bank_id]\n    available_regs = [r for r in bank_regs if reg_status_table[r].valid == 1]\n    if len(available_regs) == 0:\n      continue\n    ut_idx0 = hash_UT(PC, 0) % 8\n    ut_idx1 = hash_UT(PC, 1) % 8\n    ut_idx2 = hash_UT(PC, 2) % 8\n    best_reg = -1\n    max_usefulness = -1000\n    for r in available_regs:\n      reg_pos = r // 8\n      u = sR_UT[bank_id].UT0[ut_idx0][reg_pos] + sR_UT[bank_id].UT1[ut_idx1][reg_pos] + sR_UT[bank_id].UT2[ut_idx2][reg_pos]\n      if u > max_usefulness:\n        max_usefulness = u\n        best_reg = r\n    digest = reg_status_table[best_reg].payload & 0xFFF\n    h0 = hash(PC, digest, 0) % 512\n    h1 = hash(PC, digest, 1) % 256\n    h2 = hash(PC, digest, 2) % 128\n    bank_sum = sR_WT[bank_id].WT0[h0] + sR_WT[bank_id].WT1[h1] + sR_WT[bank_id].WT2[h2]\n    if max_usefulness > 0:\n      scaled_bank_sum = bank_sum * 2.5\n    else:\n      scaled_bank_sum = 0\n    sR_sum += scaled_bank_sum\n  return sR_sum"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In predict_sR, bank contribution is scaled by 2.5 if max_usefulness is positive, otherwise 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) leaves the selection wire for the x0 or x2.5 multiplier unlabelled, making whether max_usefulness > 0 controls the multiplier an unresolved inference.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test int_register_digest_xor_folding assumes trailing and leading zero counts are counted as zeros and placed without sign-matching.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Whether the 6-bit count fields in Figure 6(a) count zeros exclusively or match the sign/LSB bit, and how 64-bit counts are capped or encoded, is left uncertain in the paper.",
      "enum_candidates": [
        "saturate",
        "modulo",
        "match_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test flag_register_digest_replication verifies that a 4-bit flag register value is replicated three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the 4 flag bits three times to create the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test fp64_register_digest_extraction assumes FP64 bits [63:55] are shifted left by 3 bits to digest[11:3].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) does not state whether FP64 bits [63:55] are placed at digest[11:3] leaving digest[2:0] zero, or right-aligned at digest bit 0.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test stale_digest_decay_invalidation verifies that an entry is invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly defines digest invalidation after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test bank_usefulness_scaling_and_suppression assumes non-positive usefulness scales by x0 while positive usefulness scales by x2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the wire selecting between x0 and x2.5; whether bank usefulness is the driver is inferred rather than explicitly specified.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Unit test training_single_port_random_selection verifies that if several registers in a bank are available, one is randomly chosen for update to enable a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly specifies random selection of one available register per bank during training to allow a single write port."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+algo:compute_register_digest+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alon...

[Init]
model=gemini-3.8-flash-medium conversation=f193f1b8-a810-40e3-b65f-7158ece014ea cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is titled RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables presented at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title verbatim matches the source specification reference."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component integrates into the statistical corrector (SC) using register-value digests to correlate branch outcomes with recently produced register values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To exploit correlations with register values, we feed not only the PC and branch history but also register-value digests into the SC.",
        "why": "The paper explicitly states that register-value digests are provided to the SC to exploit correlations with register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A dedicated table tracking register status invalidates digests after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms that each digest is invalidated after 256 decoded instructions to prevent degradation from stale data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "When a bank's usefulness is positive, its weight sum is scaled by 2.5, otherwise suppressed to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": 
... [truncated]

[Usage]
{"input_tokens": 33390, "output_tokens": 43055, "thinking_tokens": 38262, "cache_read_tokens": 0, "total_tokens": 76445}

[Result]
status=SUCCESS conversation=f193f1b8-a810-40e3-b65f-7158ece014ea turns=1 duration=238.571187364s usage={"input_tokens": 33390, "output_tokens": 43055, "thinking_tokens": 38262, "cache_read_tokens": 0, "total_tokens": 76445}


