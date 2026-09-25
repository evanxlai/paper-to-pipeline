success: True
usage: {'input_tokens': 33103, 'output_tokens': 28364, 'thinking_tokens': 25203, 'cache_read_tokens': 0, 'total_tokens': 61467}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The bank's contribution is scaled by the useful multiplier only if its maximum usefulness weight is strictly positive (max_u > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The figure indicates an 'x0 or x2.5' multiplier but does not specify the exact condition (such as max_u > 0) that selects the non-zero multiplier, as noted in U2."
      },
      "patch": null,
      "open_question": "What condition selects between the x0 and x2.5 multipliers for a bank's contribution?",
      "enum_candidates": [
        "max_u_greater_than_zero",
        "always_2_5"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The sR_WT structure requires 43,008 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the WT organization and size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The sR_UT structure requires 9,360 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the UT size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "The sR_InFlightState structure requires 16,640 bits of dedicated storage.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies the total storage for the sR component as exactly 53,863 bits (the sum of WT, UT, and RegTable), allocating 0 bits for in-flight state."
      },
      "patch": {
        "op": "replace",
        "pointer": "/state/3",
        "value": {
          "name": "sR_InFlightState",
          "organization": "FIFO queue, one entry per in-flight branch",
          "entry_format": "Bitmask of valid registers at prediction time",
          "size_bits": 0,
          "size_formula": "0",
          "indexing": "ROB index / in-flight branch ID"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks",
        "why": "The paper explicitly states the component uses eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 uses 65 as the number of logical registers for the UT sizing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^9 (512) as one of the WT entry counts."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^8 (256) as one of the WT entry counts."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "WT2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^7 (128) as one of the WT entry counts."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "UT0 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 lists 2^3 (8) as the entry count for the UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "UT1 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 lists 2^3 (8) as the entry count for the UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "UT2 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 lists 2^3 (8) as the entry count for the UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The tables use 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies 6-bit weights for the tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The ROB index tag is 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies a 14-bit tag for the ROB index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The predictor uses 256 in-flight branches.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "capable of storing over 500 instructions.",
        "why": "The paper mentions ROB sizes of around 200 or over 500 instructions, but does not explicitly fix the number of in-flight branches to 256."
      },
      "patch": null,
      "open_question": "What is the exact number of in-flight branches simulated for the target configuration?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The useful multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The figure explicitly labels the multiplier stage with 2.5 as the scaling factor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay counter reaches 0 and clears the valid bit after 255 instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper states invalidation occurs after 256 instructions, not 255. A repair requires modifying the decrement logic, but the allocate_register algorithm is missing from the review scope, so no patch is provided."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The digest for an INT register is generated by counting leading zeros (instead of leading ones) when the value is negative.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "The paper is ambiguous on how the zero/one case is distinguished (e.g., whether it counts zeros strictly, or counts bits matching the MSB), as noted in U3."
      },
      "patch": null,
      "open_question": "Does the INT digest count leading/trailing zeros strictly, or does it count bits matching the MSB/LSB?",
      "enum_candidates": [
        "count_zeros",
        "count_matching_msb_lsb"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Predict evaluates a bank using only the digest of its most useful valid register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly specifies that only the most useful register is forwarded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Update randomly selects one valid register from a bank to modify.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that one register is randomly selected per bank for the update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "On a pipeline squash via recovery, the pending register payload is cleared to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper does not specify the recovery mechanism for squashes and explicitly leaves it to future work."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table (sR_RegTable) state be recovered on a branch misprediction or pipeline squash?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.1-pro-high conversation=5a03c46b-0a24-4546-a796-9e1aa0198829 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The bank's contribution is scaled by the useful multiplier only if its maximum usefulness weight is strictly positive (max_u > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The figure indicates an 'x0 or x2.5' multiplier but does not specify the exact condition (such as max_u > 0) that selects the non-zero multiplier, as noted in U2."
      },
      "patch": null,
      "open_question": "What condition selects between the x0 and x2.5 multipliers for a bank's contribution?",
      "enum_candidates": [
        "max_u_greater_than_zero",
        "always_2_5"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The sR_WT structure requires 43,008 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the WT organization and size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The sR_UT structure requires 9,360 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the UT size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "The sR_InFlightState structure requires 16,640 bits of dedicated storage.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies the total storage fo
... [truncated]

[Usage]
{"input_tokens": 33103, "output_tokens": 28364, "thinking_tokens": 25203, "cache_read_tokens": 0, "total_tokens": 61467}

[Result]
status=SUCCESS conversation=5a03c46b-0a24-4546-a796-9e1aa0198829 turns=1 duration=267.727427327s usage={"input_tokens": 33103, "output_tokens": 28364, "thinking_tokens": 25203, "cache_read_tokens": 0, "total_tokens": 61467}


