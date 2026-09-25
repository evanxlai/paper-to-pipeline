success: True
usage: {'input_tokens': 29573, 'output_tokens': 28536, 'thinking_tokens': 25283, 'cache_read_tokens': 0, 'total_tokens': 58109}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers tracked by the predictor is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the register usefulness tables (UT) for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Weights in prediction and usefulness weight tables are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights across all prediction weight tables (WT) and usefulness weight tables in the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The default scaling multiplier applied to bank predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) literally labels the scaling multiplier applied to the bank prediction summation as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The scaling multiplier stage in sR bank prediction is controlled by individual bank usefulness rather than a global static scale.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the control wire selecting between x0 and x2.5 scaling for the bank prediction summation, leaving it ambiguous whether selection is driven by individual bank usefulness or a global static multiplier.",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "The 6-bit leading and trailing zero/one count fields in integer register digests handle count values 0..64 by saturating at 63, wrapping modulo 64, or counting bits matching the sign bit.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) allocates 6 bits for leading and trailing zero/one counts which can range from 0 to 64, but the paper does not specify whether the count saturates at 63, wraps modulo 64, or counts bits matching the sign bit.",
      "enum_candidates": [
        "saturate",
        "wrap",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "Training updates to the register components are triggered based on bank correctness, overall SC correctness, or TAGE misprediction with SC correctness.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 4.2 states that correlations are updated during training for available registers, but does not specify the exact triggering condition among bank correctness, SC correctness, or TAGE misprediction.",
      "enum_candidates": [
        "bank_correct",
        "sc_correct",
        "tage_mispred_sc_correct"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "On a branch misprediction recovery, in-flight register status table entries are handled by clearing squashed entries, clearing all uncompleted entries, or relying on lazy decay.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 5 notes that recovering the Tomasulo-like table presents challenges left to future work, leaving the exact recovery policy upon pipeline squash unspecified.",
      "enum_candidates": [
        "clear_squashed",
        "clear_all_uncompleted",
        "lazy_decay"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "Floating-point register digest extraction places extracted sign and exponent bits aligned at digest bit position 3 rather than bit 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) indicates FP field alignment at bit 3 based on drawing alignment, but the paper does not explicitly specify whether extracted bits must be right-aligned at digest bit 3 or bit 0.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/1",
      "claim": "At instruction decode, an instruction writing a destination register clears the register's valid bit and stores its ROB index tag in the status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 explicitly describes clearing the valid bit and storing the ROB index as a tag in the register entry at instruction decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "Valid register digests are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that each valid digest is invalidated after 256 subsequent decoded instructions to prevent stale data from degrading predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table contains 65 entries, each consisting of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totalling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the structure and sizing as 65 entries of 1-bit valid, 14-bit payload, and 8-bit decay_ctr (23 bits per entry, totalling 1495 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table is indexed directly by logical register identifier with one entry per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 states that the dedicated tracking table contains exactly one entry per logical register, mapped directly by register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default decay threshold is 256 decoded instructions, tracked with an 8-bit counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly fixes the digest expiration threshold at 256 instructions, which requires an 8-bit counter as confirmed by Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "Register value digests are 12 bits wide and stored in a 14-bit payload field.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 explicitly states that digests are 12 bits wide and the entry payload holds either a 14-bit tag or a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are generated by XOR-folding a 6-bit trailing zero count at [5:0], a 6-bit leading zero count at [8:3], and the 6 LSBs at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) define the integer register digest as the XOR-folding of 6-bit trailing count, 6-bit leading count shifted by 3, and 6 LSBs shifted by 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag register digests are formed by replicating the 4-bit flag value three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly specifies replicating the 4 flag bits three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Double-precision FP register digests place extracted sign and exponent bits [63:55] at digest bit positions [11:3] with bits [2:0] set to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) shows FP fields right-aligned at bit position 3 in the drawing, but does not explicitly specify whether the extracted bits are placed at [11:3] or right-aligned at bit 0.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated and marked unavailable at the 256th instruction decode without updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 subsequent decoded instructions, matching the test expectation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness has its contribution scaled by x0 while a bank with positive usefulness has its contribution scaled by x2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the control wire driving the selection between x0 and x2.5 multipliers, leaving it uncertain whether scaling is selected per bank based on bank usefulness or via a global static multiplier.",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers are available in the same bank at prediction time, training randomly selects exactly one register to update its UT and WT entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states that if multiple registers were available in the same bank, one is randomly selected for update during training so each table needs only a single write port."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+algo:decode_and_decay_update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never...

[Init]
model=gemini-3.8-flash-medium conversation=2537d5c6-c17e-4d05-bfbe-bb38e11221fd cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers tracked by the predictor is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the register usefulness tables (UT) for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Weights in prediction and usefulness weight tables are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights across all prediction weight tables (WT) and usefulness weight tables in the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The default scaling multiplier applied to bank predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) literally labels the scaling multiplier applied to the bank prediction summation as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The scaling multiplier stage in sR bank prediction is controlled by individual bank usefulness rather than a global static scale.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the control wire selecting between x0 and x2.5 scaling for the bank prediction summation, leaving it ambiguous whether selection is driven by individual bank usefulness or a global static multiplier.",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
 
... [truncated]

[Usage]
{"input_tokens": 29573, "output_tokens": 28536, "thinking_tokens": 25283, "cache_read_tokens": 0, "total_tokens": 58109}

[Result]
status=SUCCESS conversation=2537d5c6-c17e-4d05-bfbe-bb38e11221fd turns=1 duration=159.867854489s usage={"input_tokens": 29573, "output_tokens": 28536, "thinking_tokens": 25283, "cache_read_tokens": 0, "total_tokens": 58109}


