success: True
usage: {'input_tokens': 32227, 'output_tokens': 17976, 'thinking_tokens': 15133, 'cache_read_tokens': 0, 'total_tokens': 50203}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The update algorithm correctly subscripts the UT table using the register index.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "",
        "why": "The predict_snapshots entry formats update_reg as 4 bits (which holds the intra-bank index of 0-8), but the pseudocode treats it as a 7-bit logical register and passes it to index_of_reg_in_bank, producing an out-of-bounds index."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "def update(PC, branch_id, outcome):\n    for bank in range(num_banks):\n        if predict_snapshots[branch_id][bank].was_any_valid == 1:\n            # UT update uses the randomly selected register\n            i = predict_snapshots[branch_id][bank].update_reg\n            ut_idx = hash_skewed(PC) % ut_entries\n            \n            update_usefulness(UT[bank][0][ut_idx][i], outcome, ut_width)\n            update_usefulness(UT[bank][1][ut_idx][i], outcome, ut_width)\n            update_usefulness(UT[bank][2][ut_idx][i], outcome, ut_width)\n            \n            # WT update uses the randomly selected register's digest\n            digest = predict_snapshots[branch_id][bank].update_digest\n            h0 = hash(PC, digest, 0) % wt0_entries\n            h1 = hash(PC, digest, 1) % wt1_entries\n            h2 = hash(PC, digest, 2) % wt2_entries\n            \n            update_weight(WT[bank][0][h0], outcome, wt_width)\n            update_weight(WT[bank][1][h1], outcome, wt_width)\n            update_weight(WT[bank][2][h2], outcome, wt_width)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The exact arithmetic and policy for updating usefulness and weight values are defined.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper appeals to a baseline predictor for its update rules but does not provide the concrete increment, decrement, and saturation bounds needed to implement update_usefulness or update_weight."
      },
      "patch": null,
      "open_question": "What are the exact learning rules (increment/decrement values, saturation limits) for update_usefulness and update_weight?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total size of the WT tables is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The formula for the WT storage evaluated directly matches 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "The total size of the UT tables is 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The formula for the UT storage evaluated directly matches 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/organization",
      "claim": "A snapshot of the valid registers must be kept per in-flight branch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Restricting updates to registers available at prediction time logically necessitates storing that snapshot state in a queue across in-flight branches."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The register component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the structure uses eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The weight tables (WT) use 6-bit entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The WT expression in the storage budget uses a factor of 6 for entry width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The WT0 table has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The storage budget lists a table size of 2^9 (512) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The WT1 table has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The storage budget lists a table size of 2^8 (256) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The WT2 table has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The storage budget lists a table size of 2^7 (128) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The usefulness tables (UT) use 6-bit weights per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The UT expression in the storage budget uses a factor of 6 for entry width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "Each of the three UT tables has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The storage budget explicitly states sizes of 2^3 (8) entries for the three usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "The snapshot queue tracks exactly 256 in-flight branches.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "an ROB capable of storing over 500 instructions",
        "why": "The paper states an ROB capacity of over 500 instructions but does not specify the maximum number of in-flight branches that the predictor must track in its snapshot queue."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor tracks snapshots for?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The integer register digest is generated upon instruction completion and stored.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The expectation matches the text explicitly dictating digest creation and storage at instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "A register's digest in the table is invalidated after a certain number of instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states a decay condition where the entry drops its validity after a 256-instruction timeout."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The unit test verifies that only the randomly selected register is updated.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper restricts updates to a randomly selected register, meaning a checkable test must assert that this specific register is updated while the others are not."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/2/expect",
        "value": "WT and UT entries corresponding to predict_snapshots[branch_id][bank].update_reg change, while entries for other register indices in that bank remain unchanged."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "The Tomasulo-like table correctly restores state using architectural values upon branch misprediction.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states the mechanism for table recovery is future work, so any assumption about using architectural values is a guess."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table state be restored upon a branch misprediction, since the paper defers it to future work?",
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
model=gemini-3.1-pro-high conversation=a49d1afd-d7e6-494b-8914-5b181dc7ed18 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_6721a3ea132acf19

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The update algorithm correctly subscripts the UT table using the register index.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "",
        "why": "The predict_snapshots entry formats update_reg as 4 bits (which holds the intra-bank index of 0-8), but the pseudocode treats it as a 7-bit logical register and passes it to index_of_reg_in_bank, producing an out-of-bounds index."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "def update(PC, branch_id, outcome):\n    for bank in range(num_banks):\n        if predict_snapshots[branch_id][bank].was_any_valid == 1:\n            # UT update uses the randomly selected register\n            i = predict_snapshots[branch_id][bank].update_reg\n            ut_idx = hash_skewed(PC) % ut_entries\n            \n            update_usefulness(UT[bank][0][ut_idx][i], outcome, ut_width)\n            update_usefulness(UT[bank][1][ut_idx][i], outcome, ut_width)\n            update_usefulness(UT[bank][2][ut_idx][i], outcome, ut_width)\n            \n            # WT update uses the randomly selected register's digest\n            digest = predict_snapshots[branch_id][bank].update_digest\n            h0 = hash(PC, digest, 0) % wt0_entries\n            h1 = hash(PC, digest, 1) % wt1_entries\n            h2 = hash(PC, digest, 2) % wt2_entries\n            \n            update_weight(WT[bank][0][h0], outcome, wt_width)\n            update_weight(WT[bank][1][h1], outcome, wt_width)\n            update_weight(WT[bank][2][h2], outcome, wt_width)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The exact arithmetic and policy for updating usefulness and weight values are defined.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The predictor's operati
... [truncated]

[Usage]
{"input_tokens": 32227, "output_tokens": 17976, "thinking_tokens": 15133, "cache_read_tokens": 0, "total_tokens": 50203}

[Result]
status=SUCCESS conversation=a49d1afd-d7e6-494b-8914-5b181dc7ed18 turns=1 duration=273.402080611s usage={"input_tokens": 32227, "output_tokens": 17976, "thinking_tokens": 15133, "cache_read_tokens": 0, "total_tokens": 50203}


