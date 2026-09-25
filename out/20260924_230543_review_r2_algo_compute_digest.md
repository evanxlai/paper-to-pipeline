success: True
usage: {'input_tokens': 31898, 'output_tokens': 23116, 'thinking_tokens': 20458, 'cache_read_tokens': 0, 'total_tokens': 55014}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The algorithm receives 'type' and 'val' from the calling context.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The spec uses 'type' and 'val' but neither is declared as state. The deterministic findings (unproduced_context, cross_algorithm_local) flag this. The elements provided lack the calling algorithm and a signature field, so the missing inputs cannot be patched here."
      },
      "patch": null,
      "open_question": "How are 'type' and 'val' passed to compute_digest, given the spec language lacks argument passing and they are not in state?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The integer leading/trailing count is taken modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not say whether the count saturates at 63, is taken modulo 64, or counts bits matching the sign bit (which caps at 63 naturally).",
        "why": "The source identifies this as an unresolved ambiguity (U3), making 'modulo 64' an unsupported guess."
      },
      "patch": null,
      "open_question": "How does the 6-bit count field encode counts up to 64 for integer registers?",
      "enum_candidates": [
        "modulo_64",
        "saturate_63",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The integer digest computation does not distinguish between counting zeros and counting ones.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "does not say how the zero/one case is distinguished - whether one extra bit encodes which, or whether the count is simply of bits equal to the MSB (resp. LSB).",
        "why": "The source identifies this as an unresolved ambiguity (U3), so the spec's choice to ignore the zero/one distinction is unsupported."
      },
      "patch": null,
      "open_question": "How is the zero/one case distinguished in the leading/trailing count?",
      "enum_candidates": [
        "extra_bit",
        "count_matches_msb",
        "ignore_distinction"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The floating-point extracted fields are right-aligned at bit 3 of the digest.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The right-alignment at bit 3 is read off the drawing, not stated. An alternative is that each format's field is right-aligned at bit 0.",
        "why": "The source identifies this alignment as uncertain (U4), so right-alignment at bit 3 is just an inferred guess."
      },
      "patch": null,
      "open_question": "Are the floating-point extracted fields right-aligned at bit 3 or bit 0 in the digest?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The floating-point format (FP16, FP32, FP64) is provided externally via the 'type' variable.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the format-classification step (\"we inspect the most significant bits to classify the format\") is described only in prose; the figure does not show how the classification is performed",
        "why": "The paper requires classifying the format by inspecting the MSBs, but does not specify how. The spec sidesteps this by assuming 'type' already contains the specific FP format, which is unsupported."
      },
      "patch": null,
      "open_question": "How are the most significant bits inspected to classify a floating-point value into FP16, FP32, or FP64?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The integer digest fields are combined by XOR-folding with 3-bit overlaps.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the three fields are XOR-folded, not concatenated. Three 6-bit fields would need 18 bits if concatenated, but the digest is 12 bits and the boxes are drawn overlapping with (+) between them.",
        "why": "The source infers the XOR-folding structure (I13) from the overlapping boxes in Figure 6(a), making it a deduced candidate rather than a stated fact."
      },
      "patch": null,
      "open_question": "How are the three 6-bit fields for integer registers combined into a 12-bit digest?",
      "enum_candidates": [
        "xor_fold",
        "other_hash"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The condition-code flag digest replicates the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The pseudo-code masks the lowest 4 bits and shifts them into the 12-bit result three times, directly matching the prose."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Tomasulo-like table allocates a 23-bit entry per logical register (65 total).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the auxiliary data structure exactly as specified in the spec, confirming the 1495-bit total size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/14",
      "claim": "The contribution multiplier for a bank that is not useful defaults to 0.0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) indicates that when a bank is not useful, its contribution is scaled by x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The digest is invalidated after a generic decay_threshold of triggers.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper specifies exactly 256 instructions, not a generic threshold."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "A register is completed (update_tomasulo). 256 subsequent instructions are decoded.",
          "expect": "The register's digest is invalidated, causing its valid bit in tomasulo_table to be set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The expected folded digest value for the test case is explicitly stated.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The test expectation uses the hedge word 'correct' instead of stating the concrete numeric value required by the algorithm for 0x000000000000000F."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F, invoking compute_digest.",
          "expect": "compute_digest computes the folded value 544 and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The register component predicts by selecting the digest of the most useful available register in each bank and forwarding it to the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The text explicitly states that the digest with the highest usefulness score is chosen to access the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "During training, if multiple registers were available in a bank, one is randomly selected to update the usefulness table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that the update randomly picks one available register in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "On branch squash recovery, the Tomasulo-like table entry for an allocated register is reset to valid with a cleared payload.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves the mechanism for recovering the table on squashes to future work, so the spec's specific recovery behavior is invented."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a branch misprediction squash, given the paper leaves this to future work?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:compute_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper....

[Init]
model=gemini-3.1-pro-high conversation=c8368c64-9faf-4121-8048-48130468f5bd cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The algorithm receives 'type' and 'val' from the calling context.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The spec uses 'type' and 'val' but neither is declared as state. The deterministic findings (unproduced_context, cross_algorithm_local) flag this. The elements provided lack the calling algorithm and a signature field, so the missing inputs cannot be patched here."
      },
      "patch": null,
      "open_question": "How are 'type' and 'val' passed to compute_digest, given the spec language lacks argument passing and they are not in state?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The integer leading/trailing count is taken modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not say whether the count saturates at 63, is taken modulo 64, or counts bits matching the sign bit (which caps at 63 naturally).",
        "why": "The source identifies this as an unresolved ambiguity (U3), making 'modulo 64' an unsupported guess."
      },
      "patch": null,
      "open_question": "How does the 6-bit count field encode counts up to 64 for integer registers?",
      "enum_candidates": [
        "modulo_64",
        "saturate_63",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The integer digest computation does not distinguish between counting zeros and counting ones.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "does not say how the zero/one case is distinguished - whether one extra bit encodes which, or whether the count is simply of bits equal to the MSB (resp. LSB).",
        "why": "The source identifies this as an unr
... [truncated]

[Usage]
{"input_tokens": 31898, "output_tokens": 23116, "thinking_tokens": 20458, "cache_read_tokens": 0, "total_tokens": 55014}

[Result]
status=SUCCESS conversation=c8368c64-9faf-4121-8048-48130468f5bd turns=1 duration=205.146252919s usage={"input_tokens": 31898, "output_tokens": 23116, "thinking_tokens": 20458, "cache_read_tokens": 0, "total_tokens": 55014}


