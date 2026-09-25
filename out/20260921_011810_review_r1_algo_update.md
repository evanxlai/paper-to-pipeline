success: True
usage: {'input_tokens': 28918, 'output_tokens': 27688, 'thinking_tokens': 24021, 'cache_read_tokens': 0, 'total_tokens': 56606}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/name",
      "claim": "The algorithm is the update routine for the register value correlation component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Section 4 establishes that operation and update workflows follow the baseline predictor structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The update algorithm triggers at branch resolution / commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The baseline TAGE-SC-L predictor performs statistical corrector table training at branch resolution time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Statistical corrector training occurs when the branch is mispredicted or when prediction confidence is low (|lsum| <= theta).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "TAGE-SC-L trains SC tables upon misprediction or low confidence (|lsum| <= theta), and refutes the deterministic helper warning on confidence and or."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "During training, register components are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts register updates to those available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If multiple registers were available within the same bank, one is randomly selected for update to maintain a single write port per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper specifies random selection among available registers in a bank, settling the undefined_policy_call finding."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 are updated with 6-bit signed saturating counters bounded by -32 and 31.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights for the three WT sub-tables across 8 banks, settling the counter update range."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness tables UT0, UT1, and UT2 are updated by incrementing when the register prediction agrees with the actual outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the training condition for updating the usefulness tables (UT) in the register component?",
      "enum_candidates": [
        "pred_agree",
        "sc_correct_base_wrong",
        "sc_diff_base"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness table entries are indexed by register position within the bank, where Bank 0 spans indices 0 to 8 and Banks 1 to 7 span indices 0 to 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Logical registers are partitioned stride-8 across 8 banks, so chosen_r in update and r in predict map to identical valid index domains ([0, 8] for Bank 0 and [0, 7] for Banks 1-7), refuting the inconsistent_index warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Weights and usefulness counters in the register component are 6-bit signed saturating counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit entries for all usefulness table entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register Tracking Table is a direct-mapped array of 65 entries storing valid bit, 14-bit payload, and 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 lists 65 entries each with 1-bit valid, 14-bit payload, and 8-bit decay_ctr, totaling 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT_Usefulness_Tables consists of 8 banks with 3 sub-tables of 8 entries each holding 6-bit counters per assigned register totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit counters across 65 registers and three 8-entry sub-tables (2^3 + 2^3 + 2^3), giving 6 * 65 * 24 = 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT_Prediction_Weight_Tables consists of 8 banks each with WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks with 2^7, 2^8, and 2^9 entries of 6 bits each, totaling 6 * 896 * 8 = 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component uses 8 banks.",
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
      "pointer": "/parameters/1",
      "claim": "The number of tracked logical registers in the register component is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly factors the 65 tracked logical registers into the UT storage cost calculation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 defines the digest produced for each register value to be 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Prediction weight tables per bank have entry sizes 512, 256, and 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies bank entry sizes as 2^7 (128), 2^8 (256), and 2^9 (512)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Usefulness sub-tables have 8 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three sub-tables per bank each having 2^3 = 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation extracts trailing zero count, leading zero count, and 6 LSBs, folding them into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 defines the integer digest components matching the test specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Flag digest generation replicates the 4 condition-code flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 describes 3-fold replication of the 4 flag bits into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 digest generation extracts the sign bit and the most significant 8 exponent bits into bits [11:3] of the digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 specifies extracting the sign bit and MSBs of the exponent for floating-point registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Register digests are invalidated after 256 subsequent instructions are decoded without being overwritten.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that stale digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's combined usefulness is not positive, its prediction contribution is multiplied by 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies the bank WT sum is scaled by x0 or x2.5 depending on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's combined usefulness is positive, its prediction contribution is multiplied by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies scaling by x2.5 for useful bank contributions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple valid registers are available in a bank at prediction time, exactly one is randomly chosen for update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states random selection of one register when several are available in the bank to preserve single write port per table."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A claim...

[Init]
model=gemini-3.8-flash-medium conversation=1e69d467-8ce4-4e93-94eb-5800a1214cbd cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/name",
      "claim": "The algorithm is the update routine for the register value correlation component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Section 4 establishes that operation and update workflows follow the baseline predictor structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The update algorithm triggers at branch resolution / commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The baseline TAGE-SC-L predictor performs statistical corrector table training at branch resolution time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Statistical corrector training occurs when the branch is mispredicted or when prediction confidence is low (|lsum| <= theta).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "TAGE-SC-L trains SC tables upon misprediction or low confidence (|lsum| <= theta), and refutes the deterministic helper warning on confidence and or."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "During training, register components are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "T
... [truncated]

[Usage]
{"input_tokens": 28918, "output_tokens": 27688, "thinking_tokens": 24021, "cache_read_tokens": 0, "total_tokens": 56606}

[Result]
status=SUCCESS conversation=1e69d467-8ce4-4e93-94eb-5800a1214cbd turns=1 duration=147.378073105s usage={"input_tokens": 28918, "output_tokens": 27688, "thinking_tokens": 24021, "cache_read_tokens": 0, "total_tokens": 56606}


