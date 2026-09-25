success: True
usage: {'input_tokens': 30692, 'output_tokens': 35248, 'thinking_tokens': 30387, 'cache_read_tokens': 0, 'total_tokens': 65940}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The update_sr algorithm triggers at branch retirement / commit time when the branch outcome is resolved.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Training updates occur at retirement when the branch outcome resolves, consistent with baseline TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The sR update triggers conditionally when SC mispredicts or when the SC prediction confidence is low (|lsum| <= update_threshold).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The update gating follows the baseline TAGE-SC-L statistical corrector update rule on misprediction or low confidence."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The algorithm iterates over 8 banks and updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Training is explicitly restricted to logical registers that were available when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "If multiple valid registers were available in a bank, one register is chosen uniformly at random for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Random selection among available registers in the bank ensures each table requires only a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The position of a register within a bank's usefulness vector is determined by upd_reg // 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Distributing 65 logical registers across 8 banks with stride-8 places register r in bank (r % 8) at vector index (r // 8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness and weight tables are indexed by specific modulo hash functions of PC, table index, bank ID, and register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "While the paper specifies that PC and register digest are hashed to index UT ('PC (skewed)') and WT ('h0, h1, h2'), the concrete hash functions and folding polynomials are not specified in the text.",
      "enum_candidates": [
        "xor_fold",
        "crc_hash",
        "prime_mult"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Weight tables WT0, WT1, WT2 are updated by incrementing on taken and decrementing on not-taken, saturating to 6-bit signed values [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Weight tables store signed direction counters trained in the direction of the actual branch outcome."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness counters in UT0, UT1, UT2 are rewarded (+1) if the bank's register weight prediction matched branch outcome, else penalized (-1), saturating in [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Usefulness tables track whether the register prediction was correct and useful, saturating as 6-bit counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Weights and usefulness counters are 6-bit signed values saturated at [-32, 31], and random register selection guarantees a single write port per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states the single write port guarantee and Table 3 confirms 6-bit signed counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register Tracking Table (RTT) consists of 65 entries of 23 bits each (valid: 1 bit, payload: 14 bits, decay_ctr: 8 bits), totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data row for sR explicitly specifies 65 entries with valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness tables consist of UT0, UT1, UT2 across 8 banks with 8 entries each storing 6-bit signed weights for all 65 registers, totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the UT capacity across 65 registers and 3 tables with 8 entries (2^3) each storing 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction Weight Table 0 (WT0) has 8 banks with 512 entries per bank of 6-bit signed counters, totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 512 entries for WT0 per bank, and Table 3 confirms 6-bit weights across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "Prediction Weight Table 1 (WT1) has 8 banks with 256 entries per bank of 6-bit signed counters, totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 256 entries for WT1 per bank, and Table 3 confirms 6-bit weights across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "Prediction Weight Table 2 (WT2) has 8 banks with 128 entries per bank of 6-bit signed counters, totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 128 entries for WT2 per bank, and Table 3 confirms 6-bit weights across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The sR component is organized into a default of 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly defines the component as being organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Prediction Weight Table 0 has a default of 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) gives 512 entries for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Prediction Weight Table 1 has a default of 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) gives 256 entries for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Prediction Weight Table 2 has a default of 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) gives 128 entries for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each Usefulness Table (UT0, UT1, UT2) has a default of 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly labels UT0, UT1, and UT2 as having 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The digest decay expiration threshold is 256 instructions decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 directly gives 256 decoded instructions as the digest invalidation lifetime."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The bank usefulness scale factor has a default of 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly provides 2.5 as the scaling multiplier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The total number of logical registers tracked across all banks is 65 (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data accounts for exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For an INT register with value 0, trailing and leading zeros count saturates at 63, yielding digest 0x1C7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) allocates 6 bits for leading/trailing count fields, but a 64-bit integer register can have up to 64 identical bits. As declared in source ambiguity U3, the paper does not specify whether the count saturates at 63, wraps modulo 64, or counts bits matching the sign bit.",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For INT register value 8, trailing zeros is 3, leading zeros is 60, LSB is 8, and XOR folding produces digest 0x3E3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) specifies the XOR combination of trailing count [5:0], leading count [8:3], and Value[5:0] [11:6], which for value 8 evaluates to 3 ^ (60 << 3) ^ (8 << 6) = 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For a FLAG register with condition-code bits 0b1011 (11), replicating 4 bits three times yields digest 0xBBB (3003).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times to construct the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "For FP32 registers, the extracted 6-bit field Val[31:26] is placed right-aligned at digest bit 3 with digest[2:0]=0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "As noted in source ambiguity U4, the alignment of floating-point fields at digest bit 3 is inferred from drawing geometry rather than stated in prose, and right-alignment at bit 0 remains an alternative interpretation.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An RTT entry remains valid through 255 decoded instructions and expires (valid=0) after 256 instructions without new writes.",
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
      "pointer": "/unit_tests/5",
      "claim": "When best_usefulness <= 0, the bank multiplier selects x0 and contributes 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "As noted in source ambiguity U2, Figure 5(c) shows a multiplier stage of 'x0 or x2.5' but does not explicitly label the control wire driving the selection based on bank usefulness versus a static scale factor.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When best_usefulness > 0, the bank multiplier selects x2.5 and scales the bank WT sum by 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "As noted in source ambiguity U2, the exact gating condition selecting x2.5 over x0 based on the sign of bank usefulness is inferred from structural analogy rather than explicitly drawn.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers are valid at prediction time in a bank, exactly one is chosen randomly for update in UT and WT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The text directly states that one register is randomly selected when multiple registers are available within the same bank."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update_sr` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A cl...

[Init]
model=gemini-3.8-flash-medium conversation=b4c856bd-2ece-4fa5-972d-a61ec6e1af0a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The update_sr algorithm triggers at branch retirement / commit time when the branch outcome is resolved.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Training updates occur at retirement when the branch outcome resolves, consistent with baseline TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The sR update triggers conditionally when SC mispredicts or when the SC prediction confidence is low (|lsum| <= update_threshold).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The update gating follows the baseline TAGE-SC-L statistical corrector update rule on misprediction or low confidence."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The algorithm iterates over 8 banks and updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Training is explicitly restricted to logical registers that were available when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "If multiple valid registers were available in a bank, one register is chosen uniformly at random for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
 
... [truncated]

[Usage]
{"input_tokens": 30692, "output_tokens": 35248, "thinking_tokens": 30387, "cache_read_tokens": 0, "total_tokens": 65940}

[Result]
status=SUCCESS conversation=b4c856bd-2ece-4fa5-972d-a61ec6e1af0a turns=1 duration=168.799682577s usage={"input_tokens": 30692, "output_tokens": 35248, "thinking_tokens": 30387, "cache_read_tokens": 0, "total_tokens": 65940}


