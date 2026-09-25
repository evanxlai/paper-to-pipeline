success: True
usage: {'input_tokens': 31694, 'output_tokens': 22043, 'thinking_tokens': 19806, 'cache_read_tokens': 0, 'total_tokens': 53737}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The algorithm extracts the sign and exponent bits for FP16, FP32, and FP64 formats.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper and Figure 6(b) explicitly define the bit slices to extract for each format."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The predictor classifies the floating-point format by inspecting the most significant bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format",
        "why": "The paper does not define the logic or thresholds used to distinguish between FP16, FP32, and FP64 based on the most significant bits, leaving the format variable under-specified."
      },
      "patch": null,
      "open_question": "How should the predictor classify the format (FP16, FP32, FP64) of a 64-bit floating-point register value by inspecting its most significant bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The digest invalidation occurs after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The test correctly checks that the 8-bit decay counter walks down from its maximum value to 0 over 255 decodes, clearing the valid bit on the 256th, matching the paper's specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The INT digest generation counts leading and trailing zeros.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "The paper says it counts zeros or ones but does not define how it distinguishes between the two cases, nor whether the count wraps or saturates."
      },
      "patch": null,
      "open_question": "How does the INT digest generation encode the count of leading/trailing zeros (or ones)? Does it use an extra bit to encode which was counted, or does it always count bits matching the sign bit?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The predictor evaluates a bank by selecting the valid digest of the single most useful register in that bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test correctly expects the predictor to select register 8 over register 0 because it has a higher usefulness weight, as specified by the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "sR captures correlations between register values and branch outcomes using a Tomasulo-like table and per-bank selection.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The summary accurately reflects the prose description of the register component's structure, digest tracking, and purpose."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source/paper_title",
      "claim": "The paper title is RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the source document exactly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0/need",
      "claim": "The predictor needs the register values upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value",
        "why": "The paper states that the digest is generated and stored into the payload when the instruction completes, which requires the host to provide the value then."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1/need",
      "claim": "The predictor needs the destination logical register ID and ROB index at decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry",
        "why": "The paper explicitly states the ROB index is stored at decode for the register being written, which requires both the ROB index and the logical register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2/need",
      "claim": "The host provides the instruction type classification (INT, FP, FLAG).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format",
        "why": "The paper implies the predictor determines the format by inspecting the register value rather than relying on a host-provided classification, but the exact mechanism is undefined."
      },
      "patch": null,
      "open_question": "Does the host provide the instruction type classification (INT, FP, FLAG) to the predictor, or does the predictor deduce it from the register value or opcode?",
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3/need",
      "claim": "The predictor needs notification of pipeline squash with squashed ROB indices.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The paper mentions a Tomasulo-like method but does not explicitly state how it recovers from squashes or if the host must provide squashed ROB indices."
      },
      "patch": null,
      "open_question": "How does the register tracking table recover its state after a pipeline squash? Does the host provide squashed ROB indices?",
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage budget for sR is 70503 bits, which includes 16640 bits for sR_InFlightState.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly states the total storage for the sR component is 53863 bits and only budgets for the WT, UT, and RegTable. The 16640 bits for sR_InFlightState are unbudgeted."
      },
      "patch": {
        "op": "replace",
        "pointer": "/resource_accounting",
        "value": {
          "total_storage_bits": 53863,
          "storage_breakdown": "sR_WT: 43008 bits, sR_UT: 9360 bits, sR_RegTable: 1495 bits",
          "logic_cost_notes": "Table 3 of the paper claims 53863 bits for sR. The paper's total exactly covers WT, UT, and RegTable (43008 + 9360 + 1495 = 53863). The 'val' variable is free because it is provided by the host exactly at instruction completion when the digest is generated, so it is not carried from prediction. We omit the 16640 bits for sR_InFlightState from the budget to match the paper's stated total.",
          "budget_donors": ""
        }
      },
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:extract_fp_sign_and_exp+global` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never...

[Init]
model=gemini-3.1-pro-high conversation=d2657080-e242-41d5-8194-c364ca3d748a cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The algorithm extracts the sign and exponent bits for FP16, FP32, and FP64 formats.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper and Figure 6(b) explicitly define the bit slices to extract for each format."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The predictor classifies the floating-point format by inspecting the most significant bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format",
        "why": "The paper does not define the logic or thresholds used to distinguish between FP16, FP32, and FP64 based on the most significant bits, leaving the format variable under-specified."
      },
      "patch": null,
      "open_question": "How should the predictor classify the format (FP16, FP32, FP64) of a 64-bit floating-point register value by inspecting its most significant bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The digest invalidation occurs after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The test correctly checks that the 8-bit decay counter walks down from its maximum value to 0 over 255 decodes, clearing the valid bit on the 256th, matching the paper's specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
 
... [truncated]

[Usage]
{"input_tokens": 31694, "output_tokens": 22043, "thinking_tokens": 19806, "cache_read_tokens": 0, "total_tokens": 53737}

[Result]
status=SUCCESS conversation=d2657080-e242-41d5-8194-c364ca3d748a turns=1 duration=174.466868386s usage={"input_tokens": 31694, "output_tokens": 22043, "thinking_tokens": 19806, "cache_read_tokens": 0, "total_tokens": 53737}


