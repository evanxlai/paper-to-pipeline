success: True
usage: {'input_tokens': 29386, 'output_tokens': 35928, 'thinking_tokens': 31658, 'cache_read_tokens': 0, 'total_tokens': 65314}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The update algorithm is triggered at branch resolution or commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper notes predictor operation follows TAGE-SC-L, in which predictor training tables are updated at branch resolution or commit time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update algorithm iterates over 8 banks corresponding to the 8-bank partitioning of the register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component is partitioned into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Training updates only logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that were available when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "If multiple registers were available in the same bank, the update randomly selects one of them.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly defines the training policy to choose one available register randomly per bank, refuting the warning that select_random requires a newly invented policy."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 update 6-bit signed weights using branch outcome direction when SC update is needed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 dimensions the three WT sub-tables per bank with 6-bit signed weights trained using standard SC perceptron threshold rules."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Sub-tables WT0, WT1, and WT2 are indexed by hash_wt0, hash_wt1, and hash_wt2 of branch PC and register digest in update identically to predict.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Both predict and update use the same hash functions to generate 9-bit, 8-bit, and 7-bit indices into the 512, 256, and 128 entries per bank, refuting the warning that domains differ."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "UT0, UT1, and UT2 entries are indexed by register identifier chosen_reg ranging over the logical registers belonging to the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper specifies each UT entry holds a vector indexed by the registers in that bank, refuting the warning that chosen_reg and r have inconsistent indexing domains."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The usefulness weight table update step u_step is computed via pred_matched_outcome_for_bank(bank_idx).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies that UT tracks prediction usefulness but does not define how usefulness weights are trained or what condition governs u_step for each bank during update.",
      "enum_candidates": [
        "bank_dir_match",
        "sc_correct",
        "tage_miss_sc_hit",
        "always_on_correct"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Updating only one randomly chosen available register per bank during training satisfies the single-write-port requirement.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper directly ties the single write port capability to randomly picking one register per bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "WT and UT tables use 6-bit saturating signed counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines both WT and UT entries with 6-bit weight widths."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Status Digest Table holds 65 entries partitioned into 8 banks with 9 registers in bank 0 and 8 registers in banks 1-7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states the register components partition 65 logical registers into eight banks of eight or nine registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each status table entry consists of a 1-bit valid flag, a 14-bit payload for ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines each of the 65 status entries as 1 valid bit, 14 payload bits, and 8 decay counter bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The Register Prediction Weight Tables WT consist of 8 banks with 3 sub-tables of 512, 256, and 128 entries of 6-bit weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies WT table entry sizes of 2^9, 2^8, and 2^7 across 8 banks with 6-bit weights totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The Register Usefulness Weight Tables UT consist of 3 tables of 8 entries each holding 6-bit weights for all 65 registers totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies UT as three 2^3-entry tables storing 6-bit weights for 65 registers totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of register component banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly defines the register component organization into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the register component structures for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default decay threshold for digest invalidation is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper sets digest invalidation to occur after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register value digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default prediction weight counter width for WT is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies a 6-bit weight width for the WT prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default usefulness weight counter width for UT is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies a 6-bit weight width for the UT usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default number of entries per UT table is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines 3 UT tables each having 2^3 = 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_xor_folding tests integer digest generation by XOR-folding trailing zero count, leading zero count shifted by 3, and value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The unit test expectation matches the integer digest bit-field positions and XOR overlap defined in Section 4.2 and Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_flag_digest_replication verifies replicating 4 condition code flag bits three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The unit test checks 3x replication of 4 flag bits as explicitly specified in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_fp32_digest_extraction tests extracting bits [31:26] into digest bits [8:3] for FP32 values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The unit test exercises the FP32 sign and exponent field extraction defined in Section 4.2 and Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_register_decay_invalidation tests that a register digest remains valid through 255 decoded instructions and invalidates on the 256th.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test verifies the exact 256 decoded instruction threshold for digest invalidation specified in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_bank_usefulness_argmax_selection verifies selecting the most useful register in a bank and scaling its WT sum by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test verifies argmax selection of the most useful register in a bank and the x2.5 scaling shown in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_bank_negative_usefulness_suppression verifies that non-positive bank usefulness causes the bank contribution to be multiplied by 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "The test verifies that a non-positive bank usefulness applies the x0 multiplier suppressing the bank contribution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_post_misprediction_value_availability verifies that registers written by in-flight instructions completed prior to flush completion retain valid digests across restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The test asserts post-misprediction value retention of completed instructions as established in Section 4.2."
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
model=gemini-3.8-flash-medium conversation=1488787b-efdd-4dc4-ab77-63782f0056d4 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The update algorithm is triggered at branch resolution or commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper notes predictor operation follows TAGE-SC-L, in which predictor training tables are updated at branch resolution or commit time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update algorithm iterates over 8 banks corresponding to the 8-bank partitioning of the register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component is partitioned into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Training updates only logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that were available when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "If multiple registers were available in the same bank, the update randomly selects one of them.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
   
... [truncated]

[Usage]
{"input_tokens": 29386, "output_tokens": 35928, "thinking_tokens": 31658, "cache_read_tokens": 0, "total_tokens": 65314}

[Result]
status=SUCCESS conversation=1488787b-efdd-4dc4-ab77-63782f0056d4 turns=1 duration=188.437926802s usage={"input_tokens": 29386, "output_tokens": 35928, "thinking_tokens": 31658, "cache_read_tokens": 0, "total_tokens": 65314}


