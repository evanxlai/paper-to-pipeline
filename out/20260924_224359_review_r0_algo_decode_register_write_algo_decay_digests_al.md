success: True
usage: {'input_tokens': 35783, 'output_tokens': 28386, 'thinking_tokens': 24252, 'cache_read_tokens': 0, 'total_tokens': 64169}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "decode_register_write stores the ROB index and clears the valid bit",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly describes recording the ROB index and clearing the valid bit at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Tomasulo_table has 65 entries with valid, payload, and decay_ctr fields",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the Tomasulo-like table entries and gives the precise bit widths for the valid, payload, and decay_ctr fields."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_logical_regs is 65",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly 65 entries for the auxiliary data, corresponding to the total number of logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "decay_ctr_init is 255",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper specifies invalidating after 256 instructions, but the counter is explicitly sized at 8 bits (max 255), making the exact initialization and implementation ambiguous."
      },
      "patch": null,
      "open_question": "Should the 8-bit decay counter be initialized to 255 (giving 255 steps) or use a different internal encoding to achieve exactly 256 steps?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "decay_counter_walk decrements for 255 steps until invalidation",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The unit test expects 255 steps, but the paper specifies 256. Since 256 steps do not naturally fit in a simple 8-bit counter, the exact behavior is unsupported."
      },
      "patch": null,
      "open_question": "How should the 256-instruction decay be accurately simulated given the 8-bit storage constraint?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "predict_and_snapshot randomly selects one of the available registers in a bank for the snapshot buffer",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The test's expectation of randomly selecting reg 0 or 8 for the snapshot buffer exactly matches the paper's random selection rule."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "training_updates targets only the specific register that was selected at prediction time",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The training updates only the targeted register's weights and the selected bank's WT, exactly as described."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "mispredict_recovery fully unwinds and restores the Tomasulo_table using host validities",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The exact mechanism for restoring the Tomasulo-like table after a misprediction is explicitly deferred to future work."
      },
      "patch": null,
      "open_question": "How exactly should the Tomasulo table be recovered after a misprediction flush?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "digest_generation counts leading/trailing bits matching the MSB/LSB respectively for INT registers",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "The paper leaves it uncertain (U3) whether the counts match the MSB/LSB, saturate at 63, or are taken modulo 64."
      },
      "patch": null,
      "open_question": "For INT registers, how exactly are the leading/trailing bits counted? Do they match the sign bit, and do they saturate at 63?",
      "enum_candidates": [
        "match_sign",
        "saturate_63",
        "modulo_64"
      ]
    },
    {
      "pointer": "/algorithms/1",
      "claim": "decay_digests decrements a counter and invalidates on reaching zero",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The pseudocode implements a 255-step decay to fit the 8-bit field, but the paper specifies 256 steps, leaving the exact encoding ambiguous."
      },
      "patch": null,
      "open_question": "How should the 256-step decay be implemented mathematically within an 8-bit counter?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "complete_register_write extracts FP fields and right-aligns them at bit 3",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent",
        "why": "The paper is uncertain (U4) on how the format is classified and whether the extracted FP fields are right-aligned at bit 3 or bit 0 in the digest."
      },
      "patch": null,
      "open_question": "How is the FP format classified, and are the extracted bits right-aligned at bit 3 or bit 0 in the resulting digest?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/parameters/2",
      "claim": "max_in_flight_branches is 256",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "flushed due to branch mispredictions often exceeds one hundred instructions",
        "why": "The paper mentions a >500 instruction ROB but does not specify max in-flight branches. The deterministic finding claiming this 256 default doesn't fit the 1-bit max_useful_positive field is arithmetically false, as the parameter is only used for array sizing and indexing, not stored in that field."
      },
      "patch": null,
      "open_question": "What should the maximum number of in-flight branches be?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "mispredict_recovery unwinds the Snapshot_Buffer and rebuilds Tomasulo_table from the host",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The exact recovery mechanism is deferred to future work, making the host-driven rebuild an unsupported assumption."
      },
      "patch": null,
      "open_question": "How should mispredict recovery restore the Tomasulo-like table?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/7",
      "claim": "Snapshot_Buffer records available registers and usefulness for training",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "A snapshot buffer structure is conceptually necessary to record the available registers and their context for subsequent training updates."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_banks is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper directly specifies exactly eight banks for the register components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "predict applies the 2.5 multiplier based on the bank's max_usefulness being > 0",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "The paper's figure shows the x0/x2.5 multiplier, but it is explicitly uncertain (U2) whether it is driven by per-bank usefulness or a single global static scale."
      },
      "patch": null,
      "open_question": "Is the 2.5 multiplier applied independently based on each bank's usefulness, or is it a single global scale?",
      "enum_candidates": [
        "per_bank_usefulness",
        "global_scale"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "UT0 has 8 entries and 6-bit weights",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) literally specifies 8 entries and 6-bit weights for UT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "UT1 has 8 entries",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT1",
        "why": "Figure 5(c) literally specifies 8 entries for UT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "UT2 has 8 entries",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT2",
        "why": "Figure 5(c) literally specifies 8 entries for UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "WT0 has 512 entries per bank",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) literally specifies 512 entries for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/5",
      "claim": "WT1 has 256 entries per bank",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) literally specifies 256 entries for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/6",
      "claim": "WT2 has 128 entries per bank",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) literally specifies 128 entries for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "sr_useful_scale is 2.5",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) explicitly marks the scaling factor as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "ut_weight_bits is 6",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) explicitly states the UT weights are 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "ut0_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) literally specifies 8 entries for UT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "ut1_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT1",
        "why": "Figure 5(c) literally specifies 8 entries for UT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "ut2_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT2",
        "why": "Figure 5(c) literally specifies 8 entries for UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "wt0_entries is 512",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) literally specifies 512 entries for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "wt1_entries is 256",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) literally specifies 256 entries for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "wt2_entries is 128",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) literally specifies 128 entries for WT2."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decode_register_write+algo:decay_digests+algo:complete_register_write+algo:mispredict_recovery+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actual...

[Init]
model=gemini-3.1-pro-high conversation=a6658fa0-8358-41a8-a076-b36ee995c1a6 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_9b64a8d44159f0e1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "decode_register_write stores the ROB index and clears the valid bit",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly describes recording the ROB index and clearing the valid bit at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Tomasulo_table has 65 entries with valid, payload, and decay_ctr fields",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the Tomasulo-like table entries and gives the precise bit widths for the valid, payload, and decay_ctr fields."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_logical_regs is 65",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly 65 entries for the auxiliary data, corresponding to the total number of logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "decay_ctr_init is 255",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper specifies invalidating after 256 instructions, but the counter is explicitly sized at 8 bits (max 255), making the exact initialization and implementation ambiguous."
      },
      "patch": null,
      "open_question": "Should the 8-bit decay counter be initialized
... [truncated]

[Usage]
{"input_tokens": 35783, "output_tokens": 28386, "thinking_tokens": 24252, "cache_read_tokens": 0, "total_tokens": 64169}

[Result]
status=SUCCESS conversation=a6658fa0-8358-41a8-a076-b36ee995c1a6 turns=1 duration=273.249984885s usage={"input_tokens": 35783, "output_tokens": 28386, "thinking_tokens": 24252, "cache_read_tokens": 0, "total_tokens": 64169}


