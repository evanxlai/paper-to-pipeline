success: True
usage: {'input_tokens': 32045, 'output_tokens': 27646, 'thinking_tokens': 25107, 'cache_read_tokens': 0, 'total_tokens': 59691}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "At decode, the algorithm clears the valid bit and stores the ROB index; it also invalidates stale digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. ... RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The logic performs the valid bit clearance and ROB index storage at decode, and the decrement loop correctly takes exactly 256 decodes to invalidate a newly written digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers across all banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly 65 entries for the register table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The decay counter uses 8 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly assigns 8 bits to the decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The payload field, which holds the ROB index, is 14 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly states the payload is 14 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay counter invalidates a digest after 255 subsequent instructions are decoded.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidation happens after 256 subsequent instructions, not 255. The test must be updated to expect exactly 256 decodes, parameterized by decay_ctr_bits to remain consistent with the tuning space."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_walks_down",
          "given": "An instruction completes and writes a register via write_register_digest, setting sR_RegTable decay_ctr to its maximum value of (1 << decay_ctr_bits) - 1. Then (1 << decay_ctr_bits) subsequent instructions are decoded via allocate_register.",
          "expect": "decay_ctr reaches 0 after (1 << decay_ctr_bits) - 1 decodes, and on the next decode the register's valid bit in sR_RegTable is cleared to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The INT digest generation counts leading and trailing zeros exactly, resulting in 0 and 4 for 0xFFFFFFFFFFFFFFF0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper leaves it uncertain (Note U3) whether the count distinguishes zeros from ones, and how it is encoded into 6 bits. Predicting exact counts of 0 and 4 for zeros is unsupported."
      },
      "patch": null,
      "open_question": "How is the 7-bit leading/trailing count encoded into 6 bits, and how is the zero/one case distinguished?",
      "enum_candidates": [
        "saturate",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The register component picks the digest of the most useful register among those available in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test correctly expects the prediction to use the valid register with the highest usefulness weight in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "If multiple registers are available in a bank, the update randomly selects one of them.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The test correctly asserts that exactly one randomly chosen register is updated when multiple are valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "On a pipeline squash, recovery clears the payload of pending writes matching the squashed ROB.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the recovery mechanism of the Tomasulo-like table to future work, so clearing pending writes is an unsupported assumption."
      },
      "patch": null,
      "open_question": "How is the Tomasulo-like table recovered on a branch misprediction/pipeline squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The three fields for integer registers are XOR-folded with specific overlapping offsets: trailing at bit 0, leading at bit 3, value at bit 6.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper does not state how the fields are combined. Note I13 infers XOR-folding with overlaps from the figure, but it is not stated explicitly."
      },
      "patch": null,
      "open_question": "How are the three 6-bit fields for INT registers combined into a 12-bit digest?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The count of leading and trailing bits saturates at 63 and only counts zeros.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "The paper leaves the 7-bit to 6-bit encoding and the zero/one distinction ambiguous (Note U3)."
      },
      "patch": null,
      "open_question": "How is the 7-bit leading/trailing count encoded into 6 bits, and how is the zero/one case distinguished?",
      "enum_candidates": [
        "saturate",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The extracted FP sign and exponent bits are shifted left by 3, right-aligning at bit 3.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The right-alignment at bit 3 is inferred from the drawing, not stated, and Note U4 declares it uncertain."
      },
      "patch": null,
      "open_question": "Are the FP digest bits right-aligned at bit 3, or at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For condition-code flags, the 4 flag bits are replicated three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The prose explicitly describes replicating the 4 bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The recovery algorithm conservatively clears pending writes matching squashed ROBs on a pipeline squash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the recovery mechanism of the Tomasulo-like table to future work."
      },
      "patch": null,
      "open_question": "How is the Tomasulo-like table recovered on a branch misprediction/pipeline squash?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:allocate_register+algo:write_register_digest+algo:recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from...

[Init]
model=gemini-3.1-pro-high conversation=24e33332-8a7a-4a74-a137-68b1f25a4e4d cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "At decode, the algorithm clears the valid bit and stores the ROB index; it also invalidates stale digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. ... RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The logic performs the valid bit clearance and ROB index storage at decode, and the decrement loop correctly takes exactly 256 decodes to invalidate a newly written digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers across all banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly 65 entries for the register table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The decay counter uses 8 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly assigns 8 bits to the decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The payload field, which holds the ROB index, is 14 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly states the payload is 14 bits wide."
      },
      "patch":
... [truncated]

[Usage]
{"input_tokens": 32045, "output_tokens": 27646, "thinking_tokens": 25107, "cache_read_tokens": 0, "total_tokens": 59691}

[Result]
status=SUCCESS conversation=24e33332-8a7a-4a74-a137-68b1f25a4e4d turns=1 duration=247.389825604s usage={"input_tokens": 32045, "output_tokens": 27646, "thinking_tokens": 25107, "cache_read_tokens": 0, "total_tokens": 59691}


