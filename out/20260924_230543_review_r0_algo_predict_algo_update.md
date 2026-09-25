success: True
usage: {'input_tokens': 34696, 'output_tokens': 30076, 'thinking_tokens': 23904, 'cache_read_tokens': 0, 'total_tokens': 64772}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The pseudocode instantiates an 'InflightMetadata' object which is not defined anywhere.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The predictor must collect availability metadata to implement the required training behavior, but the metadata object format is missing."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "sR = 0\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\nmetadata = {\"available_mask\": 0, \"best_r_per_bank\": [0] * num_banks, \"digest_per_bank\": [0] * num_banks}\nfor r in 0 .. num_logical_regs - 1:\n  if tomasulo_table[r].valid == 1:\n    metadata[\"available_mask\"] |= (1 << r)\n\nfor b in 0 .. num_banks - 1:\n  max_u = -999999\n  best_r = -1\n  for r in 0 .. num_logical_regs - 1:\n    if (r % num_banks) == b and tomasulo_table[r].valid == 1:\n      u = ut0[ut_idx0][r] + ut1[ut_idx1][r] + ut2[ut_idx2][r]\n      if u > max_u:\n        max_u = u\n        best_r = r\n  \n  metadata[\"best_r_per_bank\"][b] = best_r\n  if best_r != -1:\n    digest = tomasulo_table[best_r].payload\n    metadata[\"digest_per_bank\"][b] = digest\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    wt_sum = wt0[b][h0] + wt1[b][h1] + wt2[b][h2]\n    if max_u > 0:\n      sR += wt_sum * multiplier_useful\n    else:\n      sR += wt_sum * multiplier_not_useful\n  else:\n    metadata[\"digest_per_bank\"][b] = 0\n\ninflight_prediction_metadata[branch_id % num_inflight_branches] = metadata\nreturn sR"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The per-bank useful multiplier (x2.5) is selected when the bank's max usefulness is strictly positive (max_u > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not label the wire that selects x0 vs x2.5.",
        "why": "This is an UNCERTAIN reading from the source; the figure shows the multipliers but not the exact condition driving the selection."
      },
      "patch": null,
      "open_question": "What is the precise condition that selects the x2.5 multiplier over the x0 multiplier for a given bank?",
      "enum_candidates": [
        "max_u > 0",
        "max_u >= 0",
        "global_useful_bit"
      ]
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "The tomasulo_table entry comprises 1 bit valid, 14 bits payload, and 8 bits decay_ctr, multiplied by 65 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly defines the structure and counts for this table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_formula",
      "claim": "The UT tables each store one 6-bit weight per logical register for 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly defines the UT dimensions, showing three banks of 2^3 entries with 65 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_formula",
      "claim": "The UT tables each store one 6-bit weight per logical register for 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly defines the UT dimensions, showing three banks of 2^3 entries with 65 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/size_formula",
      "claim": "The UT tables each store one 6-bit weight per logical register for 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly defines the UT dimensions, showing three banks of 2^3 entries with 65 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/size_formula",
      "claim": "The WT tables are dimensioned based on the number of banks, entry count, and weight bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly sizes the WT tables according to this formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/5/size_formula",
      "claim": "The WT tables are dimensioned based on the number of banks, entry count, and weight bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly sizes the WT tables according to this formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/6/size_formula",
      "claim": "The WT tables are dimensioned based on the number of banks, entry count, and weight bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly sizes the WT tables according to this formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/7/size_formula",
      "claim": "The predictor maintains a metadata queue sized at num_inflight_branches entries to carry prediction-time state to the update stage.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper requires recovering prediction-time availability during training but does not specify the storage structure or capacity used to queue this metadata."
      },
      "patch": null,
      "open_question": "How is the prediction-time register availability and digest metadata stored and passed to the update stage, and what is its budget?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The number of logical registers tracked by the predictor is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the register components auxiliary data for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The register components are divided into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly multiplies the prediction weight table storage by 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The usefulness weight table 0 has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) directly labels UT0 with 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The usefulness weight table 1 has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly states the entry dimension for the 3 UT tables is 2^3 (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The usefulness weight table 2 has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly states the entry dimension for the 3 UT tables is 2^3 (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "Prediction weight table 0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) explicitly labels WT0 with 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "Prediction weight table 1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) explicitly labels WT1 with 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "Prediction weight table 2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) explicitly labels WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "Usefulness weights are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) labels the UT0 entries as containing 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "Prediction weights are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly indicates prediction weights are 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12/default",
      "claim": "The predictor tracks 128 in-flight branches.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "We used the default configuration, which simulates a processor with a fetch width of 16 and a frontend depth of 10.",
        "why": "The paper describes the simulator frontend but does not explicitly state the maximum number of in-flight branches."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor must support?",
      "enum_candidates": [
        "128",
        "256",
        "512"
      ]
    },
    {
      "pointer": "/parameters/13/default",
      "claim": "The useful bank multiplier is 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "each bank's contribution is scaled by 2.5 when that bank's usefulness is positive and suppressed entirely (x0) when it is not",
        "why": "This value is derived from an INFERRED reading of the figure's layout, and the explicit label 'x0 or x2.5' is too short to serve as a valid quote."
      },
      "patch": null,
      "open_question": "What is the precise scaling factor for a useful bank?",
      "enum_candidates": [
        "2.5"
      ]
    },
    {
      "pointer": "/parameters/14/default",
      "claim": "The not-useful bank multiplier is 0.0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "each bank's contribution is scaled by 2.5 when that bank's usefulness is positive and suppressed entirely (x0) when it is not",
        "why": "This value is derived from an INFERRED reading of the figure's layout, and the explicit label 'x0 or x2.5' is too short to serve as a valid quote."
      },
      "patch": null,
      "open_question": "What is the precise scaling factor for a not-useful bank?",
      "enum_candidates": [
        "0.0"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay counter expires after a symbolic 'decay_threshold' number of instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper explicitly defines the decay threshold as exactly 256 instructions, not an abstract parameter."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "A register is completed (update_tomasulo) setting its decay_ctr to 255. decay_tomasulo is triggered 255 times.",
          "expect": "The register's decay_ctr reaches 0, which causes its valid bit in tomasulo_table to be set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The test for INT digest computation does not specify a concrete input value or its resulting 12-bit digest.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper provides the fields to fold, allowing a concrete test case to be calculated."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F (60 leading zeros, 0 trailing zeros).",
          "expect": "compute_digest computes the folded value 544 and stores it in tomasulo_table with valid=1."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "predict chooses max u, stores choices, and adds scaled sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states the most useful register's digest is chosen to look up the prediction weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "update modifies tables by reading the chosen digest to adjust WT and selecting an available register to adjust UT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper dictates picking from the available registers for the UT update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Squash recovery clears invalid rob.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the squash recovery mechanism of the Tomasulo-like table to future work."
      },
      "patch": null,
      "open_question": "How is the Tomasulo-like table state recovered upon a branch misprediction squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The update algorithm relies on undefined standard arithmetic and list helpers (saturate_add, saturate_sub, append).",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper requires updating the weights but does not provide the explicit arithmetic primitives, requiring them to be inlined."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/6/pseudocode",
        "value": "metadata = inflight_prediction_metadata[branch_id % num_inflight_branches]\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\nwt_max = (1 << (wt_weight_bits - 1)) - 1\nwt_min = -(1 << (wt_weight_bits - 1))\nut_max = (1 << (ut_weight_bits - 1)) - 1\nut_min = -(1 << (ut_weight_bits - 1))\n\nfor b in 0 .. num_banks - 1:\n  # Update Prediction Tables (WT)\n  best_r = metadata[\"best_r_per_bank\"][b]\n  if best_r != -1 and sc_update_needed:\n    digest = metadata[\"digest_per_bank\"][b]\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    if outcome == TAKEN:\n      wt0[b][h0] = min(wt0[b][h0] + 1, wt_max)\n      wt1[b][h1] = min(wt1[b][h1] + 1, wt_max)\n      wt2[b][h2] = min(wt2[b][h2] + 1, wt_max)\n    else:\n      wt0[b][h0] = max(wt0[b][h0] - 1, wt_min)\n      wt1[b][h1] = max(wt1[b][h1] - 1, wt_min)\n      wt2[b][h2] = max(wt2[b][h2] - 1, wt_min)\n  \n  # Update Usefulness Tables (UT)\n  available_in_bank = []\n  for r in 0 .. num_logical_regs - 1:\n    if (r % num_banks) == b and (metadata[\"available_mask\"] & (1 << r)):\n      available_in_bank = available_in_bank + [r]\n  \n  if len(available_in_bank) > 0 and sc_update_needed:\n    rand_r = random_choice(available_in_bank)\n    if was_bank_useful(b, outcome):\n      ut0[ut_idx0][rand_r] = min(ut0[ut_idx0][rand_r] + 1, ut_max)\n      ut1[ut_idx1][rand_r] = min(ut1[ut_idx1][rand_r] + 1, ut_max)\n      ut2[ut_idx2][rand_r] = min(ut2[ut_idx2][rand_r] + 1, ut_max)\n    else:\n      ut0[ut_idx0][rand_r] = max(ut0[ut_idx0][rand_r] - 1, ut_min)\n      ut1[ut_idx1][rand_r] = max(ut1[ut_idx1][rand_r] - 1, ut_min)\n      ut2[ut_idx2][rand_r] = max(ut2[ut_idx2][rand_r] - 1, ut_min)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The utility table (UT) weights are updated based on a 'was_bank_useful' function that determines if a bank contributed correctly.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper states that correlations are updated, but does not define the condition under which a bank's usefulness is considered successful or failed."
      },
      "patch": null,
      "open_question": "What is the exact logic for 'was_bank_useful(b, outcome)'? Does it compare the bank's prediction against the final true outcome, or against the base predictor?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The update algorithm requires the true branch 'outcome' to adjust weights.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Training requires knowing the branch direction, but the paper does not specify how the true outcome is passed from the execution backend to the predictor update function."
      },
      "patch": null,
      "open_question": "The 'outcome' variable is required to update weights but is never produced by any algorithm in the spec. How is the true branch outcome passed to the update stage?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict+algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the p...

[Init]
model=gemini-3.1-pro-high conversation=11fac854-78bd-4ae3-8107-9801ba609b0e cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The pseudocode instantiates an 'InflightMetadata' object which is not defined anywhere.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The predictor must collect availability metadata to implement the required training behavior, but the metadata object format is missing."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "sR = 0\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\nmetadata = {\"available_mask\": 0, \"best_r_per_bank\": [0] * num_banks, \"digest_per_bank\": [0] * num_banks}\nfor r in 0 .. num_logical_regs - 1:\n  if tomasulo_table[r].valid == 1:\n    metadata[\"available_mask\"] |= (1 << r)\n\nfor b in 0 .. num_banks - 1:\n  max_u = -999999\n  best_r = -1\n  for r in 0 .. num_logical_regs - 1:\n    if (r % num_banks) == b and tomasulo_table[r].valid == 1:\n      u = ut0[ut_idx0][r] + ut1[ut_idx1][r] + ut2[ut_idx2][r]\n      if u > max_u:\n        max_u = u\n        best_r = r\n  \n  metadata[\"best_r_per_bank\"][b] = best_r\n  if best_r != -1:\n    digest = tomasulo_table[best_r].payload\n    metadata[\"digest_per_bank\"][b] = digest\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    wt_sum = wt0[b][h0] + wt1[b][h1] + wt2[b][h2]\n    if max_u > 0:\n      sR += wt_sum * multiplier_useful\n    else:\n      sR += wt_sum * multiplier_not_useful\n  else:\n    metadata[\"digest_per_bank\"][b] = 0\n\ninflight_prediction_metadata[branch_id % num_inflight_branches] = metadata\nreturn sR"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The per-bank 
... [truncated]

[Usage]
{"input_tokens": 34696, "output_tokens": 30076, "thinking_tokens": 23904, "cache_read_tokens": 0, "total_tokens": 64772}

[Result]
status=SUCCESS conversation=11fac854-78bd-4ae3-8107-9801ba609b0e turns=1 duration=221.873624285s usage={"input_tokens": 34696, "output_tokens": 30076, "thinking_tokens": 23904, "cache_read_tokens": 0, "total_tokens": 64772}


