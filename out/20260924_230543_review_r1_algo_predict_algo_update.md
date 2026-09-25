success: True
usage: {'input_tokens': 4152, 'output_tokens': 29076, 'thinking_tokens': 24487, 'cache_read_tokens': 31543, 'total_tokens': 33228}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The predict algorithm uses the selected register's usefulness (max_u) being positive to gate the 2.5x multiplier.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The figure does not explicitly label what signal selects the 'x0 or x2.5' multiplier. It could be the selected register's usefulness, the sum of all usefulness values in the bank, or a single global static scale.",
      "enum_candidates": [
        "max_u_positive",
        "sum_u_positive",
        "global_static"
      ]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The pseudocode uses undefined helpers 'append', 'saturate_add', 'saturate_sub', 'was_bank_useful', and an unproduced variable 'outcome'.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/6/pseudocode",
        "value": "def saturate_add(val, amt, bits):\n  max_v = (1 << (bits - 1)) - 1\n  return max_v if val + amt > max_v else val + amt\n\ndef saturate_sub(val, amt, bits):\n  min_v = -(1 << (bits - 1))\n  return min_v if val - amt < min_v else val - amt\n\ndef was_bank_useful(b, outcome):\n  return host_was_bank_useful(b, outcome)\n\noutcome = host_commit_outcome(branch_id)\nmetadata = inflight_prediction_metadata[branch_id % num_inflight_branches]\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\n\nfor b in 0 .. num_banks - 1:\n  # Update Prediction Tables (WT)\n  best_r = metadata.best_r_per_bank[b]\n  if best_r != -1 and sc_update_needed:\n    digest = metadata.digest_per_bank[b]\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    if outcome == TAKEN:\n      wt0[b][h0] = saturate_add(wt0[b][h0], 1, wt_weight_bits)\n      wt1[b][h1] = saturate_add(wt1[b][h1], 1, wt_weight_bits)\n      wt2[b][h2] = saturate_add(wt2[b][h2], 1, wt_weight_bits)\n    else:\n      wt0[b][h0] = saturate_sub(wt0[b][h0], 1, wt_weight_bits)\n      wt1[b][h1] = saturate_sub(wt1[b][h1], 1, wt_weight_bits)\n      wt2[b][h2] = saturate_sub(wt2[b][h2], 1, wt_weight_bits)\n  \n  # Update Usefulness Tables (UT)\n  available_in_bank = []\n  for r in 0 .. num_logical_regs - 1:\n    if (r % num_banks) == b and (metadata.available_mask & (1 << r)):\n      available_in_bank = available_in_bank + [r]\n  \n  if len(available_in_bank) > 0 and sc_update_needed:\n    rand_r = random_choice(available_in_bank)\n    if was_bank_useful(b, outcome):\n      ut0[ut_idx0][rand_r] = saturate_add(ut0[ut_idx0][rand_r], 1, ut_weight_bits)\n      ut1[ut_idx1][rand_r] = saturate_add(ut1[ut_idx1][rand_r], 1, ut_weight_bits)\n      ut2[ut_idx2][rand_r] = saturate_add(ut2[ut_idx2][rand_r], 1, ut_weight_bits)\n    else:\n      ut0[ut_idx0][rand_r] = saturate_sub(ut0[ut_idx0][rand_r], 1, ut_weight_bits)\n      ut1[ut_idx1][rand_r] = saturate_sub(ut1[ut_idx1][rand_r], 1, ut_weight_bits)\n      ut2[ut_idx2][rand_r] = saturate_sub(ut2[ut_idx2][rand_r], 1, ut_weight_bits)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The tomasulo_table has one entry per logical register (65), containing a 1-bit valid flag, 14-bit payload, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines exactly this format and entry count scaling for the auxiliary state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The ut0 table stores 6-bit weights for 65 registers across 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the exact dimensions for the three UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The ut1 table stores 6-bit weights for 65 registers across 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the exact dimensions for the three UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "The ut2 table stores 6-bit weights for 65 registers across 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the exact dimensions for the three UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "The wt0 table stores 6-bit weights across 512 entries per bank, replicated across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact dimensions for the three WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/5",
      "claim": "The wt1 table stores 6-bit weights across 256 entries per bank, replicated across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact dimensions for the three WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/6",
      "claim": "The wt2 table stores 6-bit weights across 128 entries per bank, replicated across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact dimensions for the three WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/7",
      "claim": "The inflight prediction metadata tracks masks and digests for branches.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the exact layout or size of the inflight prediction metadata queue.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly scales the auxiliary data cost by 65."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The number of register banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks",
        "why": "The prose explicitly states the component is divided into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "ut0_entries is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three terms of 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "ut1_entries is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three terms of 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut2_entries is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three terms of 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "wt0_entries is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives WT sizes with terms 128, 256, and 512."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "wt1_entries is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives WT sizes with terms 128, 256, and 512."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "wt2_entries is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives WT sizes with terms 128, 256, and 512."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "ut_weight_bits is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies the UT weight width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "wt_weight_bits is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the WT weight width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The number of inflight branches tracked is 128.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor metadata queue should support?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/13",
      "claim": "The usefulness multiplier is 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the multiplier value 2.5 robustly defined in the text beyond the figure label?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/14",
      "claim": "The non-useful multiplier is 0.0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the non-useful multiplier value exactly 0.0 robustly defined in the text?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay counter expires after a symbolic decay_threshold.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper specifies exactly 256 instructions for invalidation rather than an unspecified threshold."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "A register is completed (update_tomasulo) setting its decay_ctr to 255. 256 subsequent instructions are decoded.",
          "expect": "The register's decay_ctr reaches 0, which causes its valid bit in tomasulo_table to be set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The digest computation test for INT registers relies on a vague hedge word.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F, invoking compute_digest.",
          "expect": "compute_digest computes the folded value 544 and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "predict selects the most useful register and uses its digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "picks the digest of the most useful register among those available and forwards it to the second table",
        "why": "The prose confirms the predictor uses the digest of the single most useful register in a bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "update modifies WT and randomly selects one available register to update UT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states the random selection for training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Squash recovery correctly clears invalid entries in the Tomasulo table.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper mentions recovering the Tomasulo-like table as future work and does not detail the squash recovery mechanics.",
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
model=gemini-3.1-pro-high conversation=0c7353f1-c74b-4758-9e1f-b3c08ffe0b1a cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The predict algorithm uses the selected register's usefulness (max_u) being positive to gate the 2.5x multiplier.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The figure does not explicitly label what signal selects the 'x0 or x2.5' multiplier. It could be the selected register's usefulness, the sum of all usefulness values in the bank, or a single global static scale.",
      "enum_candidates": [
        "max_u_positive",
        "sum_u_positive",
        "global_static"
      ]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The pseudocode uses undefined helpers 'append', 'saturate_add', 'saturate_sub', 'was_bank_useful', and an unproduced variable 'outcome'.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/6/pseudocode",
        "value": "def saturate_add(val, amt, bits):\n  max_v = (1 << (bits - 1)) - 1\n  return max_v if val + amt > max_v else val + amt\n\ndef saturate_sub(val, amt, bits):\n  min_v = -(1 << (bits - 1))\n  return min_v if val - amt < min_v else val - amt\n\ndef was_bank_useful(b, outcome):\n  return host_was_bank_useful(b, outcome)\n\noutcome = host_commit_outcome(branch_id)\nmetadata = inflight_prediction_metadata[branch_id % num_inflight_branches]\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\n\nfor b in 0 .. num_banks - 1:\n  # Update Prediction Tables (WT)\n  best_r = metadata.best_r_per_bank[b]\n  if best_r != -1 and sc_update_needed:\n    digest = metadata.digest_per_bank[b]\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    if outcome == TAKEN:\n      wt0[b][h0] = saturate_add(wt0[b][h0], 1, wt_weight_bits)\n      wt1[b][h1] = saturate_add(wt1[b][h
... [truncated]

[Usage]
{"input_tokens": 4152, "output_tokens": 29076, "thinking_tokens": 24487, "cache_read_tokens": 31543, "total_tokens": 33228}

[Result]
status=SUCCESS conversation=0c7353f1-c74b-4758-9e1f-b3c08ffe0b1a turns=1 duration=549.995075551s usage={"input_tokens": 4152, "output_tokens": 29076, "thinking_tokens": 24487, "cache_read_tokens": 31543, "total_tokens": 33228}


