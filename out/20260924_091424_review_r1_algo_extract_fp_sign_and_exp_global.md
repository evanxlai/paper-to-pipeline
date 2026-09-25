success: True
usage: {'input_tokens': 31914, 'output_tokens': 24278, 'thinking_tokens': 22236, 'cache_read_tokens': 0, 'total_tokens': 56192}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/name",
      "claim": "The extract_fp_sign_and_exp algorithm requires a unit test to verify its logic.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign and exponent bits for floating-point registers, but the spec lacks a unit test to verify this extraction logic."
      },
      "patch": {
        "op": "add",
        "pointer": "/unit_tests/-",
        "value": {
          "name": "extract_fp_sign_and_exp_fp32",
          "given": "An FP32 instruction completes, format is classified as FP32, and val is 0x40490FDB.",
          "expect": "extract_fp_sign_and_exp returns val[31:26], capturing the sign and high-order exponent bits."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The format of a floating-point register (FP16, FP32, FP64) is classified by inspecting its most significant bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format",
        "why": "The paper states the format is classified by inspecting the most significant bits, but does not provide the logic to do so, leaving 'format' unproduced."
      },
      "patch": null,
      "open_question": "How are the most significant bits of a floating-point register value inspected to classify its format as FP16, FP32, or FP64?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The register value 'val' is provided directly by the host upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value",
        "why": "The analyzer incorrectly flags 'val' as a cross-algorithm local; however, the paper confirms the value is produced and provided directly by the host at instruction completion, acting as an argument rather than undeclared state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/logic_cost_notes",
      "claim": "The register value 'val' used for digest generation is provided at instruction completion and does not consume carried state budget.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value",
        "why": "The analyzer warns that 'val' is an unbudgeted carried state. The spec is underspecified because it fails to clarify in the notes that 'val' is provided at instruction completion by the host and therefore free of carried state cost."
      },
      "patch": {
        "op": "replace",
        "pointer": "/resource_accounting/logic_cost_notes",
        "value": "Table 3 of the paper claims 53863 bits for sR. My total is 70503 bits. I am over by 16640 bits. The paper's total exactly covers WT, UT, and RegTable (43008 + 9360 + 1495 = 53863). It omits the 16640 bits needed for sR_InFlightState to snapshot the 65 valid bits per in-flight branch, which the update algorithm requires to know which registers were available at prediction time. Naming the host as the provider does not remove this from the budget at iso-storage. The 'val' variable is provided by the host exactly at instruction completion when the digest is generated, so it is not carried from prediction and consumes no storage budget."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The digest is invalidated after 255 subsequent instructions are decoded.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper states the digest is invalidated after 256 instructions, contradicting the test's expectation of 255. A patch is omitted because updating the test requires synchronous edits to write_register_digest and allocate_register to adjust the counter's lifecycle, but those algorithms are not in my scope."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For integer registers, the digest is generated using the count of leading zeros and trailing zeros.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper specifies encoding the leading and trailing zero counts, which matches the test's expected inputs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predictor selects the single most useful register digest among those available in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states that the most useful available register in the bank is selected and used for the prediction table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component captures correlations between register values and branch directions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes.",
        "why": "The paper introduces the sR component specifically to capture register value correlations, confirming the summary's core description."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper is RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the source section exactly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host provides register values at instruction completion and tracks the ROB index at decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry",
        "why": "The paper explicitly describes using the ROB index at decode, which requires the host to provide it."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/total_storage_bits",
      "claim": "The total storage budget of 53863 bits for the sR component exactly covers WT, UT, and RegTable.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 lists exactly these components and sums to 53863 bits, proving the paper omitted the in-flight snapshot storage from its budget."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:extract_fp_sign_and_exp+global` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never...

[Init]
model=gemini-3.1-pro-high conversation=30511b6c-4d47-454c-9cbf-6f0640d97dbd cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/name",
      "claim": "The extract_fp_sign_and_exp algorithm requires a unit test to verify its logic.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign and exponent bits for floating-point registers, but the spec lacks a unit test to verify this extraction logic."
      },
      "patch": {
        "op": "add",
        "pointer": "/unit_tests/-",
        "value": {
          "name": "extract_fp_sign_and_exp_fp32",
          "given": "An FP32 instruction completes, format is classified as FP32, and val is 0x40490FDB.",
          "expect": "extract_fp_sign_and_exp returns val[31:26], capturing the sign and high-order exponent bits."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The format of a floating-point register (FP16, FP32, FP64) is classified by inspecting its most significant bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format",
        "why": "The paper states the format is classified by inspecting the most significant bits, but does not provide the logic to do so, leaving 'format' unproduced."
      },
      "patch": null,
      "open_question": "How are the most significant bits of a floating-point register value inspected to classify its format as FP16, FP32, or FP64?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The register value 'val' is provided directly by the host upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction complet
... [truncated]

[Usage]
{"input_tokens": 31914, "output_tokens": 24278, "thinking_tokens": 22236, "cache_read_tokens": 0, "total_tokens": 56192}

[Result]
status=SUCCESS conversation=30511b6c-4d47-454c-9cbf-6f0640d97dbd turns=1 duration=190.216148018s usage={"input_tokens": 31914, "output_tokens": 24278, "thinking_tokens": 22236, "cache_read_tokens": 0, "total_tokens": 56192}


