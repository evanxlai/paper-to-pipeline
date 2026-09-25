success: True
usage: {'input_tokens': 33746, 'output_tokens': 31906, 'thinking_tokens': 28164, 'cache_read_tokens': 0, 'total_tokens': 65652}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_sc_needs_update() is used to decide if the SC weights should be trained",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper does not state the exact condition for updating the SC; it just defers to the TAGE-SC-L baseline, leaving the policy undefined in this text."
      },
      "patch": null,
      "open_question": "What is the specific condition for updating the SC (host_sc_needs_update)?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_id() and host_branch_taken() are provided by the host simulator",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "We evaluated the proposed branch predictor and compared it against existing predictors using the CBP2025 simulator",
        "why": "The paper mentions the simulator but does not define these specific host interface primitives."
      },
      "patch": null,
      "open_question": "Are host_branch_id() and host_branch_taken() standard primitives provided by the host environment?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT0 is an 8-entry table storing weights for 65 logical registers",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3's sizing formula confirms there are 8 (2^3) entries per UT component, spanning all 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "UT1 is an 8-entry table storing weights for 65 logical registers",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the second UT component (UT1) also has 8 entries spanning 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "UT2 is an 8-entry table storing weights for 65 logical registers",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the third UT component (UT2) also has 8 entries spanning 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "WT0 is organized into 8 banks",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 shows the weight tables (WT) are distributed across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/5",
      "claim": "WT1 is organized into 8 banks",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 shows the weight tables (WT) are distributed across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/6",
      "claim": "WT2 is organized into 8 banks",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 shows the weight tables (WT) are distributed across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/7",
      "claim": "The max_useful_positive field in Snapshot_Buffer must accommodate the default max_in_flight_branches of 256",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "this verdict needs no quote",
        "why": "A deterministic finding reports that the 256 default for max_in_flight_branches does not fit the 1-bit max_useful_positive field; widening the field to 9 bits clears the contradiction."
      },
      "patch": {
        "op": "replace",
        "pointer": "/state/7",
        "value": {
          "name": "Snapshot_Buffer",
          "organization": "FIFO per in-flight branch",
          "entry_format": "array of num_banks elements: active (1 bit), reg_id (ceil(log2(num_logical_regs)) bits), digest (12 bits), max_useful_positive (9 bits)",
          "size_bits": 59392,
          "size_formula": "max_in_flight_branches * num_banks * (22 + ceil(log2(num_logical_regs)))",
          "indexing": "branch_id % max_in_flight_branches"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The number of banks is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks",
        "why": "Section 4.2 explicitly states there are eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The maximum number of in-flight branches defaults to 256",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "an ROB capable of storing over 500 instructions",
        "why": "The paper implies a deep pipeline but never specifies the exact parameter or default of 256 for max_in_flight_branches."
      },
      "patch": null,
      "open_question": "What is the intended maximum number of in-flight branches (max_in_flight_branches) for the design?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "ut_weight_bits is 6",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 states the UT weights are 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "ut0_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 shows each of the three UT tables has 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "ut1_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the entries for UT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "ut2_entries is 8",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the entries for UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "wt_weight_bits is 6",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 states the WT weights are 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "wt0_entries is 512",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) labels WT0 with 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11/default",
      "claim": "wt1_entries is 256",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) labels WT1 with 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12/default",
      "claim": "wt2_entries is 128",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) labels WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The digest is invalidated after 255 instructions have been decoded",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper specifies invalidation happens after 256 instructions, not 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_walk",
          "given": "Instruction A writes logical register 5. decode_register_write sets its decay_ctr to decay_ctr_init and valid to 0. It completes immediately, triggering complete_register_write which sets valid to 1. Then 256 unrelated instructions are decoded, triggering decay_digests 256 times.",
          "expect": "decay_ctr decrements on each decay_digests call. On the 256th call, decay_ctr expires and Tomasulo_table[5].valid is set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The bank's prediction contribution is scaled by a multiplier (x2.5) if max_useful_positive is true.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "The figure shows the 'x0 or x2.5' multiplier but does not explicitly connect it to the bank's local usefulness signal (U2 ambiguity)."
      },
      "patch": null,
      "open_question": "What exact signal controls the 'x0 or x2.5' multiplier for a bank's contribution?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_usefulness_positive"
      ]
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The UT usefulness weights are trained by incrementing them based on branch outcome (taken/not taken)",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "reflecting the usefulness of each register",
        "why": "The paper states the UT tracks usefulness, but does not specify how these weights are incremented or decremented during training."
      },
      "patch": null,
      "open_question": "How exactly are the usefulness weights in the UT updated during training?",
      "enum_candidates": [
        "branch_direction",
        "prediction_correctness"
      ]
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "The predictor recovers the Tomasulo table on a misprediction by clearing squashed snapshots and restoring valid registers.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly declines to define a recovery mechanism for the Tomasulo table."
      },
      "patch": null,
      "open_question": "What is the intended misprediction recovery mechanism for the Tomasulo table, given it was left to future work?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "The INT digest resolves zero/one ambiguity by counting leading and trailing bits that match the MSB and LSB.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "The paper does not explain how zeros versus ones are distinguished or how 64 fits into a 6-bit count field (U3 ambiguity)."
      },
      "patch": null,
      "open_question": "How are the leading/trailing zero/one counts encoded in 6 bits, and how is the zero/one distinction represented?",
      "enum_candidates": [
        "match_sign_bit",
        "saturate_63",
        "modulo_64"
      ]
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
model=gemini-3.1-pro-high conversation=677ff5ed-8780-450c-871d-e8e40e7db132 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_9b64a8d44159f0e1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_sc_needs_update() is used to decide if the SC weights should be trained",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "The paper does not state the exact condition for updating the SC; it just defers to the TAGE-SC-L baseline, leaving the policy undefined in this text."
      },
      "patch": null,
      "open_question": "What is the specific condition for updating the SC (host_sc_needs_update)?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_id() and host_branch_taken() are provided by the host simulator",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "We evaluated the proposed branch predictor and compared it against existing predictors using the CBP2025 simulator",
        "why": "The paper mentions the simulator but does not define these specific host interface primitives."
      },
      "patch": null,
      "open_question": "Are host_branch_id() and host_branch_taken() standard primitives provided by the host environment?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT0 is an 8-entry table storing weights for 65 logical registers",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3's sizing formula confirms there are 8 (2^3) entries per UT component, spanning all 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "UT1 is an 8-entry table storing weights for 65 logical registers",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the second UT co
... [truncated]

[Usage]
{"input_tokens": 33746, "output_tokens": 31906, "thinking_tokens": 28164, "cache_read_tokens": 0, "total_tokens": 65652}

[Result]
status=SUCCESS conversation=677ff5ed-8780-450c-871d-e8e40e7db132 turns=1 duration=265.975813891s usage={"input_tokens": 33746, "output_tokens": 31906, "thinking_tokens": 28164, "cache_read_tokens": 0, "total_tokens": 65652}


