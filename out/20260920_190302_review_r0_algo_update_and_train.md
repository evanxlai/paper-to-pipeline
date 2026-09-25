success: True
usage: {'input_tokens': 28653, 'output_tokens': 35688, 'thinking_tokens': 31890, 'cache_read_tokens': 0, 'total_tokens': 64341}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR update and training procedure is triggered at branch commit / SC update time when the SC threshold requires training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Establishes that SC components in RUNLTS inherit standard TAGE-SC-L training triggers at branch commit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Correlations are trained only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Directly specifies the restriction that training only applies to registers available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "When multiple registers are available in a bank, one is randomly selected for training to enforce a single write-port constraint.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Confirms that random selection among available bank registers is required by the paper rather than an undefined policy."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Weight updates in WT and UT use 6-bit signed saturating counter arithmetic clamping to [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms that table weights are 6-bit signed values adhering to standard SC saturating counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update_sr function implements the training procedure for the sR register component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Establishes the training behavior implemented by the update routine for register components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The register digest used to train the WT tables is read from the register tracking table payload at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does training retrieve the register digest that was captured at prediction time, or does it re-read the register tracking table at commit time?",
      "enum_candidates": [
        "pred_time_digest",
        "commit_time_table"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Register usefulness table (UT) weights are incremented or decremented based on whether the WT prediction sum matches the actual branch outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training condition determines when register usefulness weights in UT are incremented or decremented?",
      "enum_candidates": [
        "wt_matches_outcome",
        "tage_mispredicted",
        "sc_updated"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Single write-port enforcement per table during training is achieved by randomly selecting one available register per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Directly connects the random selection among available registers to the single write port design constraint."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "wt_tables consists of 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Gives the exact structure and bit count of 6 bits x (128 + 256 + 512) entries x 8 banks = 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "ut_tables consists of 8 banks with three 8-entry tables tracking vectors across 65 registers with 6-bit weights totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Verifies that usefulness tables track 65 registers across three 8-entry tables with 6-bit weights totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "register_tracking_table contains 65 entries, each with a 1-bit valid flag, 14-bit payload, and 8-bit decay counter initialized to 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms the exact entry layout and number of entries for the register tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks defaults to 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "States that the register component is organized into 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers defaults to 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms tracking across 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt0_entries defaults to 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The term 2^9 specifies 512 entries per bank for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt1_entries defaults to 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The term 2^8 specifies 256 entries per bank for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "wt2_entries defaults to 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The term 2^7 specifies 128 entries per bank for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "ut_entries_per_table defaults to 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The terms 2^3 specify 8 entries per UT table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "useful_multiplier defaults to 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Labels the bank usefulness scaling multiplier stage as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "wt_weight_bits defaults to 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms the weight width for prediction weight tables is 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "ut_weight_bits defaults to 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Confirms the weight width for usefulness tables is 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_generation expects that evaluating 3 ^ 480 ^ 512 results in 35.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0/expect",
        "value": "Computed 12-bit digest equals (3 & 0x3F) ^ ((60 & 0x3F) << 3) ^ ((8 & 0x3F) << 6) = 3 ^ 480 ^ 512 = 995 (0x3E3)."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_flag_digest_generation tests that a 4-bit condition-code register replicates three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Directly confirms that condition-code flag digests replicate the 4 bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_bank_register_selection tests that the bank selects the register with the largest usefulness weight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Verifies that the most useful register among available registers is selected to query the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_usefulness_scaling_zero tests that non-positive usefulness causes the bank contribution to scale by x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Specifies that the bank output is multiplied by x0 when not selected as useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_usefulness_scaling_positive tests that positive usefulness scales the bank output by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Confirms that positive usefulness scales the bank contribution by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_decay_invalidation tests that register digests invalidate after 256 instruction decodes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Directly establishes the 256-instruction decode threshold for digest invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_mispredict_visibility tests that in-flight instructions completed before misprediction resolution remain visible upon pipeline restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Establishes that instructions finished before branch resolution remain visible to the predictor after restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update_and_train` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the pape...

[Init]
model=gemini-3.8-flash-medium conversation=a245dfc6-a98c-4050-8e08-b55ff9f0a33b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR update and training procedure is triggered at branch commit / SC update time when the SC threshold requires training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Establishes that SC components in RUNLTS inherit standard TAGE-SC-L training triggers at branch commit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Correlations are trained only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Directly specifies the restriction that training only applies to registers available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "When multiple registers are available in a bank, one is randomly selected for training to enforce a single write-port constraint.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Confirms that random selection among available bank registers is required by the paper rather than an undefined policy."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Weight updates in WT and UT use 6-bit signed saturating counter arithmetic clamping to [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) 
... [truncated]

[Usage]
{"input_tokens": 28653, "output_tokens": 35688, "thinking_tokens": 31890, "cache_read_tokens": 0, "total_tokens": 64341}

[Result]
status=SUCCESS conversation=a245dfc6-a98c-4050-8e08-b55ff9f0a33b turns=1 duration=186.697615302s usage={"input_tokens": 28653, "output_tokens": 35688, "thinking_tokens": 31890, "cache_read_tokens": 0, "total_tokens": 64341}


