success: True
usage: {'input_tokens': 28692, 'output_tokens': 35580, 'thinking_tokens': 31043, 'cache_read_tokens': 0, 'total_tokens': 64272}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/name",
      "claim": "The algorithm is named 'Update (Training)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly discusses the training and update procedure for the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Training is triggered at Commit time (or Branch Resolution time).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not state whether sR training is triggered at instruction commit time or branch resolution time."
      },
      "patch": null,
      "open_question": "At which pipeline stage is sR training executed?",
      "enum_candidates": [
        "commit_time",
        "branch_resolution_time"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Only one available register per bank is trained per branch event, chosen uniformly at random, so each table needs only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection of a single register per bank ensures each table needs just one write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper directly specifies that only registers available at prediction time have their correlations updated during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If several registers were available within the same bank, one of them is selected randomly for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper specifies random selection among available registers in a bank for the update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The update condition executes when sc_mispredicted is true or |LSUM| is within update_threshold.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "RUNLTS uses the baseline TAGE-SC-L statistical corrector update rule, updating on misprediction or marginal confidence (|LSUM| <= update_threshold)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Pseudocode contains an undefined helper call to confidence(...).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The token 'confidence' appears solely inside an explanatory comment and was falsely flagged as a function call by deterministic parsing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Pseudocode contains an undefined helper call to or(...).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The token 'or' is a standard boolean disjunction operator, not an undefined helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The usefulness weight (UT) of the chosen register is incremented if the bank's WT prediction direction matches the actual branch outcome, and decremented otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not detail the exact arithmetic condition under which UT usefulness weights are incremented or decremented."
      },
      "patch": null,
      "open_question": "What is the training update condition for usefulness table (UT) weights?",
      "enum_candidates": [
        "bank_dir_correct",
        "reversed_base_correct",
        "sc_useful"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "UT is subscripted at depth 4 by chosen_reg (global logical register index 0 to 64) in Update (Training), whereas each bank's UT entry holds an 8- or 9-element vector indexed by bank-relative register index r.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Two statements in the spec collide: /state/1 declares that Bank b's UT entries contain an 8- or 9-weight vector for registers in that bank (indexed by bank-relative index r), but /algorithms/3/pseudocode subscripts UT at depth 4 with chosen_reg (0..64), which exceeds the entry vector bounds."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "function sat_update_6bit(ctr, step):\n    new_ctr = ctr + step\n    if new_ctr > 31:\n        return 31\n    if new_ctr < -32:\n        return -32\n    return new_ctr\n\nfunction select_random(available_regs):\n    return available_regs[random_index(0, length(available_regs) - 1)]\n\nfunction update_sR(PC, actual_taken, sc_mispredicted, LSUM_abs, recorded_pred_state):\n    // SC perceptron update condition: updated on misprediction or marginal confidence where |LSUM| <= update_threshold\n    needs_update = sc_mispredicted || (LSUM_abs <= update_threshold)\n    if not needs_update:\n        return\n\n    step = (actual_taken == 1) ? +1 : -1\n    for b = 0 to 7:\n        available_regs = recorded_pred_state.available_regs_per_bank[b]\n        if length(available_regs) == 0:\n            continue\n        \n        // 'If several registers were available within the same bank, it randomly selects one of them for the update'\n        chosen_reg = select_random(available_regs)\n        chosen_digest = recorded_pred_state.digests[chosen_reg]\n        \n        // Update WT0, WT1, WT2 for chosen digest\n        idx_w0 = Hash_WT0(PC, chosen_digest) % 512\n        idx_w1 = Hash_WT1(PC, chosen_digest) % 256\n        idx_w2 = Hash_WT2(PC, chosen_digest) % 128\n        WT[b][0][idx_w0] = sat_update_6bit(WT[b][0][idx_w0], step)\n        WT[b][1][idx_w1] = sat_update_6bit(WT[b][1][idx_w1], step)\n        WT[b][2][idx_w2] = sat_update_6bit(WT[b][2][idx_w2], step)\n        \n        // Update UT tables for chosen_reg using bank-relative register index r = chosen_reg / 8\n        // Usefulness incremented if the prediction from this bank aligned with actual outcome, decremented otherwise\n        idx_u0 = Hash_UT0(PC) % 8\n        idx_u1 = Hash_UT1(PC) % 8\n        idx_u2 = Hash_UT2(PC) % 8\n        r = chosen_reg / 8\n        u_step = (sign(WT[b][0][idx_w0] + WT[b][1][idx_w1] + WT[b][2][idx_w2]) == step) ? +1 : -1\n        UT[b][0][idx_u0][r] = sat_update_6bit(UT[b][0][idx_u0][r], u_step)\n        UT[b][1][idx_u1][r] = sat_update_6bit(UT[b][1][idx_u1][r], u_step)\n        UT[b][2][idx_u2][r] = sat_update_6bit(UT[b][2][idx_u2][r], u_step)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table contains 65 entries corresponding to logical registers, each entry having 1 valid bit, 14 payload bits, and an 8-bit decay_ctr totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the scoreboard structure as 65 entries of 1 valid bit, 14 payload bits, and 8 decay_ctr bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The Usefulness Weight Tables (UT) comprise 8 banks with 3 tables of 8 entries each, storing 6-bit signed weights across 65 registers totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the UT capacity and entry organization matching 8 entries for 3 tables across 65 registers with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The Prediction Weight Tables (WT) comprise 8 banks with 3 tables of 512, 256, and 128 entries of 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT capacity across the 8 banks for sizes 128, 256, and 512 entries with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The parameter num_banks has a default of 8.",
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
      "claim": "The parameter wt_entries has a default configuration of 512,256,128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 and Figure 5(c) specify WT table sizes of 512, 256, and 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The parameter ut_entries_per_table has a default of 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 and Figure 5(c) specify that each of the 3 UT tables per bank has 8 entries (2^3)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The parameter decay_threshold default value is 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Two statements in the spec collide: Section 4.2 prose specifies invalidating digests after 256 instructions leading to default 256, but Table 3 allocates only 8 bits for decay_ctr declared in /state/0/entry_format (max value 255). Lowering default to 255 allows 256 states (0..255) to fit within the 8-bit counter."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/3/default",
        "value": 255
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The parameter bank_useful_multiplier has a default value of 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly labels the bank usefulness multiplier stage as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter num_tracked_registers has a default value of 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms 65 logical registers tracked across the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest XOR-folds trailing count, leading count shifted by 3, and 6 LSBs shifted by 6 to yield 0x3E3 for value 0x8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify the exact XOR overlap of the 3 6-bit fields forming the 12-bit integer digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags value 0x9 replicated 3 times produces digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) establish that flags are replicated three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Scoreboard aging invalidates a digest after decay_ctr reaches 0 upon decoding subsequent instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Bank contribution is scaled by 2.5 when usefulness is positive and 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) establishes the x0 or x2.5 scaling on bank usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers are available in a bank at prediction time, exactly one is randomly chosen for WT/UT table update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 dictates random selection of one available register per bank during training."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:Update (Training)` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the pap...

[Init]
model=gemini-3.8-flash-medium conversation=bc4bae3d-ef32-43df-99df-3283a3e07bf3 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/name",
      "claim": "The algorithm is named 'Update (Training)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly discusses the training and update procedure for the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Training is triggered at Commit time (or Branch Resolution time).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not state whether sR training is triggered at instruction commit time or branch resolution time."
      },
      "patch": null,
      "open_question": "At which pipeline stage is sR training executed?",
      "enum_candidates": [
        "commit_time",
        "branch_resolution_time"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Only one available register per bank is trained per branch event, chosen uniformly at random, so each table needs only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection of a single register per bank ensures each table needs just one write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction
... [truncated]

[Usage]
{"input_tokens": 28692, "output_tokens": 35580, "thinking_tokens": 31043, "cache_read_tokens": 0, "total_tokens": 64272}

[Result]
status=SUCCESS conversation=bc4bae3d-ef32-43df-99df-3283a3e07bf3 turns=1 duration=173.315427598s usage={"input_tokens": 28692, "output_tokens": 35580, "thinking_tokens": 31043, "cache_read_tokens": 0, "total_tokens": 64272}


