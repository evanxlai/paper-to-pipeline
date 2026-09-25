success: True
usage: {'input_tokens': 35511, 'output_tokens': 26421, 'thinking_tokens': 24493, 'cache_read_tokens': 0, 'total_tokens': 61932}

## result
```json
{
  "records": [
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The exact digest computation output for an integer register is deterministic and testable.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones)",
        "why": "The paper does not state how the 7-bit leading/trailing count is encoded into a 6-bit field, nor how zero vs one is distinguished (UNCERTAIN U3), making the exact folded value impossible to state."
      },
      "patch": null,
      "open_question": "How is the 7-bit leading/trailing count (0..64) encoded into the 6-bit field, and how is the zero/one case distinguished?",
      "enum_candidates": ["saturate_63", "modulo_64", "match_msb"]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay threshold is explicitly 256 subsequent instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The unit test uses an unspecified 'decay_threshold' variable instead of the constant 256 stated in the paper. However, the parameter 'decay_threshold' and algorithms 'update_tomasulo' and 'decay_tomasulo' are missing from the elements I was given, so I return the verdict without a patch to avoid a partial, inconsistent edit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The parameter 'amt' is a variable and the branch outcome is an input, not a policy helper.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "By the time a branch resolves and its misprediction is revealed",
        "why": "The linter misinterprets 'amt' as a function and 'host_commit_outcome' as a policy call. I am patching the pseudocode to rename 'amt' to 'amount' and remove the 'host_commit_outcome' call to clear these deterministic findings."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/6/pseudocode",
        "value": "def saturate_add(val, amount, bits):\n  max_v = (1 << (bits - 1)) - 1\n  return max_v if val + amount > max_v else val + amount\n\ndef saturate_sub(val, amount, bits):\n  min_v = -(1 << (bits - 1))\n  return min_v if val - amount < min_v else val - amount\n\ndef was_bank_useful(b, outcome):\n  return host_was_bank_useful(b, outcome)\n\nmetadata = inflight_prediction_metadata[branch_id % num_inflight_branches]\nut_idx0 = hash(PC) % ut0_entries\nut_idx1 = hash(PC) % ut1_entries\nut_idx2 = hash(PC) % ut2_entries\n\nfor b in 0 .. num_banks - 1:\n  # Update Prediction Tables (WT)\n  best_r = metadata.best_r_per_bank[b]\n  if best_r != -1 and sc_update_needed:\n    digest = metadata.digest_per_bank[b]\n    h0 = hash0(PC, digest) % wt0_entries\n    h1 = hash1(PC, digest) % wt1_entries\n    h2 = hash2(PC, digest) % wt2_entries\n    if outcome == TAKEN:\n      wt0[b][h0] = saturate_add(wt0[b][h0], 1, wt_weight_bits)\n      wt1[b][h1] = saturate_add(wt1[b][h1], 1, wt_weight_bits)\n      wt2[b][h2] = saturate_add(wt2[b][h2], 1, wt_weight_bits)\n    else:\n      wt0[b][h0] = saturate_sub(wt0[b][h0], 1, wt_weight_bits)\n      wt1[b][h1] = saturate_sub(wt1[b][h1], 1, wt_weight_bits)\n      wt2[b][h2] = saturate_sub(wt2[b][h2], 1, wt_weight_bits)\n  \n  # Update Usefulness Tables (UT)\n  available_in_bank = []\n  for r in 0 .. num_logical_regs - 1:\n    if (r % num_banks) == b and (metadata.available_mask & (1 << r)):\n      available_in_bank = available_in_bank + [r]\n  \n  if len(available_in_bank) > 0 and sc_update_needed:\n    rand_r = random_choice(available_in_bank)\n    if was_bank_useful(b, outcome):\n      ut0[ut_idx0][rand_r] = saturate_add(ut0[ut_idx0][rand_r], 1, ut_weight_bits)\n      ut1[ut_idx1][rand_r] = saturate_add(ut1[ut_idx1][rand_r], 1, ut_weight_bits)\n      ut2[ut_idx2][rand_r] = saturate_add(ut2[ut_idx2][rand_r], 1, ut_weight_bits)\n    else:\n      ut0[ut_idx0][rand_r] = saturate_sub(ut0[ut_idx0][rand_r], 1, ut_weight_bits)\n      ut1[ut_idx1][rand_r] = saturate_sub(ut1[ut_idx1][rand_r], 1, ut_weight_bits)\n      ut2[ut_idx2][rand_r] = saturate_sub(ut2[ut_idx2][rand_r], 1, ut_weight_bits)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The exact condition for a bank to be considered useful during the UT update is fully defined.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The paper relies on the existing TAGE-SC-L usefulness update without specifying the exact formula. The deterministic finding correctly flags host_was_bank_useful as an undefined helper."
      },
      "patch": null,
      "open_question": "What is the exact boolean condition to determine if a bank was useful (for UT increment)?",
      "enum_candidates": ["bank_correct", "sc_correct", "bank_agrees_with_outcome"]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The per-bank multiplier is chosen based on whether the bank's max usefulness is greater than zero.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The figure does not specify which signal drives the x0 vs x2.5 multiplier (UNCERTAIN U2). Using max_u > 0 is an inferred guess."
      },
      "patch": null,
      "open_question": "What exact condition drives the x2.5 multiplier for a bank? Is it max_u > 0, max_u >= 0, or something else?",
      "enum_candidates": ["max_u_gt_0", "max_u_ge_0", "global_useful"]
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
model=gemini-3.1-pro-high conversation=1a7ecff8-9dae-4fba-b026-606d373ac7bc cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The exact digest computation output for an integer register is deterministic and testable.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones)",
        "why": "The paper does not state how the 7-bit leading/trailing count is encoded into a 6-bit field, nor how zero vs one is distinguished (UNCERTAIN U3), making the exact folded value impossible to state."
      },
      "patch": null,
      "open_question": "How is the 7-bit leading/trailing count (0..64) encoded into the 6-bit field, and how is the zero/one case distinguished?",
      "enum_candidates": ["saturate_63", "modulo_64", "match_msb"]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay threshold is explicitly 256 subsequent instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The unit test uses an unspecified 'decay_threshold' variable instead of the constant 256 stated in the paper. However, the parameter 'decay_threshold' and algorithms 'update_tomasulo' and 'decay_tomasulo' are missing from the elements I was given, so I return the verdict without a patch to avoid a partial, inconsistent edit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The parameter 'amt' is a variable and the branch outcome is an input, not a policy helper.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "By the time a branch resolves and its misprediction is revealed",
        "why": "The linter misinterprets 'amt' as a function and 'host_commit_outcome' as a policy call. I am patching the pseudocode to rename 'amt' to 'amount' and remove the 'host_commit_outcome' call to clear these determini
... [truncated]

[Usage]
{"input_tokens": 35511, "output_tokens": 26421, "thinking_tokens": 24493, "cache_read_tokens": 0, "total_tokens": 61932}

[Result]
status=SUCCESS conversation=1a7ecff8-9dae-4fba-b026-606d373ac7bc turns=1 duration=242.459710624s usage={"input_tokens": 35511, "output_tokens": 26421, "thinking_tokens": 24493, "cache_read_tokens": 0, "total_tokens": 61932}


