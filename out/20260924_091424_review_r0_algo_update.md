success: True
usage: {'input_tokens': 32701, 'output_tokens': 22628, 'thinking_tokens': 19268, 'cache_read_tokens': 0, 'total_tokens': 55329}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The algorithm selects exactly one available register at random per bank for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "This explicitly confirms the logic to pick a random valid register from each bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The weight (WT) and usefulness (UT) tables are updated by adding a specific utility delta.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper states the predictor updates correlations but does not provide the arithmetic formulas used for updating WT or UT."
      },
      "patch": null,
      "open_question": "What is the exact arithmetic update rule (utility delta) applied to the UT and WT tables during training?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The register components are updated at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper discusses training using registers available at prediction time, but does not explicitly name the pipeline stage (e.g. commit vs. resolve) when the predictor is updated."
      },
      "patch": null,
      "open_question": "At what pipeline stage is the register predictor trained?",
      "enum_candidates": [
        "commit",
        "resolve"
      ]
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "sR_WT total size is calculated as num_banks * (wt0_entries + wt1_entries + wt2_entries) * wt_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage as the sum of three tables' entries (128, 256, 512) multiplied by 6 bits and 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "sR_UT stores a vector of signed weights, one per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) indicates that the usefulness table entry contains a 6-bit weight for each of the 9 logical registers in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_formula",
      "claim": "sR_UT size is computed as num_logical_regs * (ut0_entries + ut1_entries + ut2_entries) * wt_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies the UT size as 6 bits times 65 total logical registers times the sum of the three UT tables (8 entries each)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "sR_UT is indexed by the skewed PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "PC (skewed)",
        "why": "Figure 5(c) shows the skewed PC as the index into the usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "sR_InFlightState is organized as a FIFO queue tracking one entry per in-flight branch.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper requires updating only registers available at prediction time, but does not describe the specific hardware structure (such as a FIFO queue) used to buffer this state until training."
      },
      "patch": null,
      "open_question": "What hardware structure is used to buffer the 'available at prediction time' valid bits until the branch trains?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default number of banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks",
        "why": "The prose directly states the register component uses eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies the register state array tracks exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default number of entries for WT0 is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) labels WT0 as having 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The default number of entries for WT1 is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) labels WT1 as having 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The default number of entries for WT2 is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) labels WT2 as having 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The default number of entries for UT0 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) labels the UT0 table as having 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default number of entries for UT1 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT1",
        "why": "Figure 5(c) labels the UT1 table as having 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default number of entries for UT2 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT2",
        "why": "Figure 5(c) labels the UT2 table as having 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default bit width for weights is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the weight tables (WT) use 6 bits per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "The default rob_idx_bits is 14.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies the ROB index tag fits in 14 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11/default",
      "claim": "The default inflight_branches is 256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper does not state the exact number of in-flight branches that the predictor must track simultaneously."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches to provision for in the register valid state tracking?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay counter walks down and invalidates the register after 255 instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper explicitly states invalidation occurs after 256 subsequent instructions, not 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_walks_down",
          "given": "An instruction completes and writes a register via write_register_digest, setting sR_RegTable decay_ctr to 255. Then 256 subsequent instructions are decoded via allocate_register.",
          "expect": "decay_ctr reaches -1, and the register's valid bit in sR_RegTable is cleared to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The integer digest generation counts leading zeros explicitly.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper states 'leading zeros (or ones)' and source note U3 marks the exact counting semantics as uncertain."
      },
      "patch": null,
      "open_question": "How does integer digest generation determine whether to count leading/trailing zeros or ones?",
      "enum_candidates": [
        "zeros",
        "ones",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Prediction selects the most useful valid register's digest to index the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly confirms the predictor uses usefulness to select the digest for the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "During update, exactly one randomly chosen valid register per bank is updated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper confirms that a single valid register is chosen randomly for each bank's update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A branch recovery squash clears the payload of an uncompleted register allocation to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper does not detail the recovery procedure for the Tomasulo-like register tracking table during a branch squash."
      },
      "patch": null,
      "open_question": "How does the register tracker handle pipeline flushes? Does it clear pending ROB indices in the payload?",
      "enum_candidates": [
        "clear_payload",
        "ignore"
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
model=gemini-3.1-pro-high conversation=9ccbf96a-6a73-4e66-87e0-0d67409157a6 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The algorithm selects exactly one available register at random per bank for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "This explicitly confirms the logic to pick a random valid register from each bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The weight (WT) and usefulness (UT) tables are updated by adding a specific utility delta.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper states the predictor updates correlations but does not provide the arithmetic formulas used for updating WT or UT."
      },
      "patch": null,
      "open_question": "What is the exact arithmetic update rule (utility delta) applied to the UT and WT tables during training?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The register components are updated at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "N/A",
        "why": "The paper discusses training using registers available at prediction time, but does not explicitly name the pipeline stage (e.g. commit vs. resolve) when the predictor is updated."
      },
      "patch": null,
      "open_question": "At what pipeline stage is the register predictor trained?",
      "enum_candidates": [
        "commit",
        "resolve"
      ]
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "sR_WT total size is calculated as num_banks * (wt0_entries + wt1_entries + wt2_entries) * wt_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 d
... [truncated]

[Usage]
{"input_tokens": 32701, "output_tokens": 22628, "thinking_tokens": 19268, "cache_read_tokens": 0, "total_tokens": 55329}

[Result]
status=SUCCESS conversation=9ccbf96a-6a73-4e66-87e0-0d67409157a6 turns=1 duration=270.071411116s usage={"input_tokens": 32701, "output_tokens": 22628, "thinking_tokens": 19268, "cache_read_tokens": 0, "total_tokens": 55329}


