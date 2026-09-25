success: True
usage: {'input_tokens': 31105, 'output_tokens': 21740, 'thinking_tokens': 19440, 'cache_read_tokens': 0, 'total_tokens': 52845}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The algorithm compute_digest reads context variables val and type which are not declared as inputs.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The pseudocode uses 'val' and 'type' but neither declares them as inputs nor are they produced elsewhere, colliding with the requirement that all context must be produced, as flagged by the unproduced_context findings."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "inputs: val, type\nif type == INT:\n  trail = trailing_count(val) % 64\n  lead = leading_count(val) % 64\n  v = val & 0x3F\n  return (trail ^ (lead << 3) ^ (v << 6)) & 0xFFF\nelif type == FP16:\n  return (((val >> 13) & 0x7) << 3) & 0xFFF\nelif type == FP32:\n  return (((val >> 26) & 0x3F) << 3) & 0xFFF\nelif type == FP64:\n  return (((val >> 55) & 0x1FF) << 3) & 0xFFF\nelif type == FLAG:\n  v = val & 0xF\n  return (v | (v << 4) | (v << 8)) & 0xFFF\nreturn 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "For integer registers, the leading and trailing counts are taken modulo 64 and zero/one is not distinguished.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper does not state whether counts are taken modulo 64 or saturate, nor how the zero/one case is distinguished (as noted by U3)."
      },
      "patch": null,
      "open_question": "How should the leading and trailing counts be encoded (e.g., modulo 64, saturate at 63), and how is the zero/one case distinguished?",
      "enum_candidates": [
        "modulo_64",
        "saturate_63"
      ]
    },
    {
      "pointer": "/algorithms/1",
      "claim": "For floating-point registers, the extracted fields are right-aligned at digest bit 3.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The prose does not explicitly state the alignment of the extracted bits, and the figure's alignment is inferred (U4), leaving exact placement ambiguous."
      },
      "patch": null,
      "open_question": "Are the extracted FP fields right-aligned at digest bit 3 or bit 0, and how is the format classification performed for values that are not recognisable floats?",
      "enum_candidates": [
        "bit_3",
        "bit_0"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The Tomasulo table contains one entry per logical register, formatted with a 1-bit valid flag, 14-bit payload, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly lists the auxiliary data for the Register component as having exactly these fields and bit widths per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/14",
      "claim": "The multiplier used when a bank's usefulness is not positive is 0.0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "The diagram specifies that the multiplier can be x0 (0.0) when the register is not the most useful or when usefulness is not positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay test triggers decay 'decay_threshold' times.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper hardcodes exactly 256 instructions for invalidation rather than leaving it as an abstract decay threshold. This patch also resolves the untested_counter_lifecycle warning by explicitly stating the values."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "A register is completed (update_tomasulo) setting its decay_ctr to 256. 256 subsequent instructions are decoded.",
          "expect": "The register's decay_ctr reaches 0, which causes its valid bit in tomasulo_table to be set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The expectation for the INT digest computation asserts nothing mathematically checkable.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The expectation relies on a hedge word ('correct') instead of computing the result explicitly, resulting in a vacuous_test finding. It must state the exact numeric expectation."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x1 (63 leading zeros, 0 trailing zeros), invoking compute_digest.",
          "expect": "compute_digest computes the folded digest (0 ^ (63 << 3) ^ (1 << 6)) = 440 and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predict stage selects the register with the highest usefulness from its bank's usefulness tables, looks up its weights using its digest, and adds the scaled sum to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "This confirms the test's expectation that predict selects the register with the highest usefulness and uses its digest to look up prediction weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "The update stage selects an available register from the mask to adjust the usefulness tables.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that the register is selected randomly when multiple are available, but the test omits this requirement."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/3",
        "value": {
          "name": "update_modifies_tables",
          "given": "update is called after predict has populated inflight_prediction_metadata.",
          "expect": "update reads the chosen digest to adjust wt0, wt1, wt2, and randomly selects one of the available registers from the mask to adjust ut0, ut1, ut2."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "On a squash recovery for an older branch, the Tomasulo table entry for an allocated register becomes valid and its payload is cleared.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper leaves the exact mechanism for recovering the Tomasulo-like table on a branch squash explicitly undefined as future work."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a squash? Specifically, what should the valid bit and payload be set to when an allocated instruction is squashed?",
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
model=gemini-3.1-pro-high conversation=c3273c29-8645-4c75-bdd4-aa040be75ac8 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The algorithm compute_digest reads context variables val and type which are not declared as inputs.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The pseudocode uses 'val' and 'type' but neither declares them as inputs nor are they produced elsewhere, colliding with the requirement that all context must be produced, as flagged by the unproduced_context findings."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "inputs: val, type\nif type == INT:\n  trail = trailing_count(val) % 64\n  lead = leading_count(val) % 64\n  v = val & 0x3F\n  return (trail ^ (lead << 3) ^ (v << 6)) & 0xFFF\nelif type == FP16:\n  return (((val >> 13) & 0x7) << 3) & 0xFFF\nelif type == FP32:\n  return (((val >> 26) & 0x3F) << 3) & 0xFFF\nelif type == FP64:\n  return (((val >> 55) & 0x1FF) << 3) & 0xFFF\nelif type == FLAG:\n  v = val & 0xF\n  return (v | (v << 4) | (v << 8)) & 0xFFF\nreturn 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "For integer registers, the leading and trailing counts are taken modulo 64 and zero/one is not distinguished.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper does not state whether counts are taken modulo 64 or saturate, nor how the zero/one case is distinguished (as noted by U3)."
      },
      "patch": null,
      "open_question": "How should the leading and trailing counts be encoded (e.g., modulo 64, saturate at 63), and how is the zero/one case distinguished?",
      "enum_candidates": [
        "modulo_64",
        "saturate_63"
      ]
    },
    {
      "pointer": "/algorithms/1",
      "claim": "For fl
... [truncated]

[Usage]
{"input_tokens": 31105, "output_tokens": 21740, "thinking_tokens": 19440, "cache_read_tokens": 0, "total_tokens": 52845}

[Result]
status=SUCCESS conversation=c3273c29-8645-4c75-bdd4-aa040be75ac8 turns=1 duration=150.859953944s usage={"input_tokens": 31105, "output_tokens": 21740, "thinking_tokens": 19440, "cache_read_tokens": 0, "total_tokens": 52845}


