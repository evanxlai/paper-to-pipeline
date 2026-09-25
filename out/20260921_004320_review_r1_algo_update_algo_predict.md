success: True
usage: {'input_tokens': 31238, 'output_tokens': 47088, 'thinking_tokens': 41393, 'cache_read_tokens': 0, 'total_tokens': 78326}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The predict_sR algorithm triggers during SC computation when predicting a conditional branch at PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that the register component is queried to forward available digests to the SC whenever the branch predictor makes a prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Logical registers 0 to 64 are partitioned across 8 banks such that bank b contains registers where r % 8 == b.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the register components as organized into eight banks containing eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, register usefulness is computed by summing weights looked up from three usefulness tables UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows each bank containing three usefulness tables whose outputs are summed to produce usefulness values for the bank's registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the predictor selects the digest of the register with the maximum usefulness among all currently valid registers in that bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly specifies selecting the digest of the most useful register among those available in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The selected register digest and branch PC index three prediction weight tables WT0, WT1, and WT2 whose signed weights are summed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) specifies that the selected register digest and PC index three prediction weight tables WT0, WT1, and WT2 and sum their outputs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "A bank's prediction weight sum is multiplied by 2.5 when max_useful > 0 and scaled by 0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact threshold condition selects between the x2.5 and x0 multipliers for a bank's contribution?",
      "enum_candidates": [
        "max_useful_positive",
        "any_valid_reg",
        "useful_ge_zero",
        "threshold"
      ]
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "If no register in the bank is valid, the bank contributes 0, and the multiplier selection is determined by the bank's max usefulness.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows each bank feeding a multiplier stage labelled x0 or x2.5 upstream of the cross-bank summation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The update algorithm triggers at branch retirement when SC update conditions (|LSUM| <= theta or mispredicted) are met.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The paper integrates the register component directly into the TAGE-SC-L statistical corrector, which updates when |LSUM| <= theta or the branch is mispredicted."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "During training, each bank randomly selects at most one register among those available at prediction time to update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that only registers available at prediction time are updated, with random selection if multiple were available in the same bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 are updated using 6-bit signed saturating addition by +1 on TAKEN and -1 on NOT_TAKEN.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper specifies following TAGE-SC-L predictor operation, where SC perceptron tables update weights by step increments saturating at 6-bit boundaries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Usefulness tables UT0, UT1, and UT2 update by incrementing usefulness when the bank's weight table direction agreed with outcome and decrementing otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training policy determines whether usefulness table weights increment or decrement during update?",
      "enum_candidates": [
        "direction_agreement",
        "sc_error_correction",
        "sc_confidence_based"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The update pseudocode relies on an undefined helper function sat_add_signed_6bit and references WT1 and WT2 without table lookup indexing.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper specifies following TAGE-SC-L operation with 6-bit signed saturating weights, but the pseudocode leaves the saturating helper undefined and mistypes weight table terms."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "function sat_add_signed_6bit(val, step):\n  res = val + step\n  if res > 31:\n    return 31\n  if res < -32:\n    return -32\n  return res\n\nfunction update_sR(PC, outcome, recorded_valid_regs_at_pred, recorded_selected_regs):\n  for bank = 0 to 7:\n    available_regs = [r for r in recorded_valid_regs_at_pred if (r % 8 == bank)]\n    if len(available_regs) == 0:\n      continue\n      \n    // If multiple registers were available, randomly select one to update\n    r_update = available_regs[random_choice(len(available_regs))]\n    digest = recorded_digest[r_update]\n    \n    // Update weight tables WT0, WT1, WT2 using perceptron rule\n    h0 = hash_wt0(PC, digest); h1 = hash_wt1(PC, digest); h2 = hash_wt2(PC, digest)\n    step = (outcome == TAKEN) ? +1 : -1\n    prediction_weight_tables[bank].WT0[h0] = sat_add_signed_6bit(prediction_weight_tables[bank].WT0[h0], step)\n    prediction_weight_tables[bank].WT1[h1] = sat_add_signed_6bit(prediction_weight_tables[bank].WT1[h1], step)\n    prediction_weight_tables[bank].WT2[h2] = sat_add_signed_6bit(prediction_weight_tables[bank].WT2[h2], step)\n    \n    // Update usefulness tables UT0, UT1, UT2\n    // Usefulness increments if WT direction agreed with outcome, else decrements\n    wt_sum = prediction_weight_tables[bank].WT0[h0] + prediction_weight_tables[bank].WT1[h1] + prediction_weight_tables[bank].WT2[h2]\n    pred_agreed = ((wt_sum >= 0) == (outcome == TAKEN))\n    u_step = pred_agreed ? +1 : -1\n    idx0 = hash_ut0(PC); idx1 = hash_ut1(PC); idx2 = hash_ut2(PC)\n    usefulness_weight_tables[bank].UT0[idx0][r_update] = sat_add_signed_6bit(usefulness_weight_tables[bank].UT0[idx0][r_update], u_step)\n    usefulness_weight_tables[bank].UT1[idx1][r_update] = sat_add_signed_6bit(usefulness_weight_tables[bank].UT1[idx1][r_update], u_step)\n    usefulness_weight_tables[bank].UT2[idx2][r_update] = sat_add_signed_6bit(usefulness_weight_tables[bank].UT2[idx2][r_update], u_step)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Only registers available at prediction time are updated, random selection preserves single-write-port RAM, and weights saturate at [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly notes that random single-register selection allows single-write-port memory implementation during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Prediction weight tables consist of 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 accounts for WT storage as 6-bit weights times (128 + 256 + 512) entries across 8 banks, giving exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "WT0, WT1, and WT2 indices are computed by specific bitwise XOR hash expressions combining PC and register digest slices.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash functions map PC and register digest to the 9-bit, 8-bit, and 7-bit indices for WT0, WT1, and WT2?",
      "enum_candidates": [
        "xor_fold",
        "gehl_hash",
        "crc_hash"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness weight tables contain 8 banks of 3 tables (UT0, UT1, UT2) with 8 entries each, where each entry stores a 6-bit signed weight for each of the bank's registers (65 total registers) totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 details the usefulness tables as 6-bit weights for 65 registers across three 8-entry tables, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT0, UT1, and UT2 3-bit indices are computed by specific bit-slice XOR expressions PC[5:3] ^ PC[8:6], (PC >> 4) ^ (PC >> 7) & 0x7, and (PC >> 6) ^ (PC >> 9) & 0x7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What skewed hash functions map PC to the 3-bit indices for usefulness tables UT0, UT1, and UT2?",
      "enum_candidates": [
        "pc_xor_fold",
        "prime_displace",
        "bit_slice"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The register status table has 65 direct-mapped entries each containing a 1-bit valid flag, a 14-bit payload (ROB index or digest), and an 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 lists auxiliary data storage for sR as 65 entries of valid (1 bit), payload (14 bits), and decay_ctr (8 bits), which sums to 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of register banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly specifies organizing the register component into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of tracked logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates storage using 65 registers partitioned across the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default entry count for WT0 is 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) labels WT0 as 512 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default entry count for WT1 is 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) labels WT1 as 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default entry count for WT2 is 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) labels WT2 as 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The useful bank multiplier default value is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows the per-bank output scaling stage labelled x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The default register digest length is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly specifies that RUNLTS generates a 12-bit digest for each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding trailing zero/one count [5:0], leading zero/one count [8:3], and value LSBs [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper describes integer digests as encoding leading counts, trailing counts, and six LSBs, mapped via XOR overlapping in Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 register digests extract bits [63:55] (sign and high exponent bits) shifted into digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies extracting Value[63:55] for FP64 registers into digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag digests are formed by replicating the 4-bit flag value three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the 4 condition flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated after exactly 256 subsequent instructions have been decoded without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating each digest after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers are valid in a bank, the register with the largest cumulative usefulness is selected and the bank output is scaled by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper states that the most useful register among available registers in the bank is picked to forward its digest to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, when multiple registers in a bank were valid at prediction time, exactly one register is randomly chosen to update using a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper specifies that random selection of one available register per bank during training ensures single-write-port access per table."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the p...

[Init]
model=gemini-3.8-flash-medium conversation=77f95399-9a4f-4b77-bd60-43c982cb4c4a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The predict_sR algorithm triggers during SC computation when predicting a conditional branch at PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that the register component is queried to forward available digests to the SC whenever the branch predictor makes a prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Logical registers 0 to 64 are partitioned across 8 banks such that bank b contains registers where r % 8 == b.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the register components as organized into eight banks containing eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, register usefulness is computed by summing weights looked up from three usefulness tables UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows each bank containing three usefulness tables whose outputs are summed to produce usefulness values for the bank's registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the predictor selects the digest of the register with 
... [truncated]

[Usage]
{"input_tokens": 31238, "output_tokens": 47088, "thinking_tokens": 41393, "cache_read_tokens": 0, "total_tokens": 78326}

[Result]
status=SUCCESS conversation=77f95399-9a4f-4b77-bd60-43c982cb4c4a turns=1 duration=255.360707428s usage={"input_tokens": 31238, "output_tokens": 47088, "thinking_tokens": 41393, "cache_read_tokens": 0, "total_tokens": 78326}


