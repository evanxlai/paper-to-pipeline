success: True
usage: {'input_tokens': 30498, 'output_tokens': 13568, 'thinking_tokens': 12711, 'cache_read_tokens': 0, 'total_tokens': 44066}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 7-bit leading and trailing zero counts are encoded into 6-bit fields by taking them modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not say whether the count saturates at 63, is taken modulo 64, or counts bits matching the sign bit",
        "why": "The source notes that the diagram is ambiguous regarding how counts up to 64 fit into a 6-bit field."
      },
      "patch": null,
      "open_question": "How are the 7-bit leading and trailing zero counts encoded into the 6-bit INT digest fields?",
      "enum_candidates": [
        "modulo_64",
        "saturate",
        "match_sign"
      ]
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The Tomasulo-like table entries consist of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "This table cell explicitly lists the fields and widths of the register component's auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The three 6-bit fields of the INT digest are XOR-folded together.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "INFERRED - the three fields are XOR-folded, not concatenated.",
        "why": "The XOR folding is inferred from the visual overlap in the diagram rather than explicitly stated, which makes the assumption unsupported."
      },
      "patch": null,
      "open_question": "Are the three 6-bit fields of the INT digest XOR-folded or concatenated in a way not shown?",
      "enum_candidates": [
        "xor_fold",
        "concatenate"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The digest is invalidated when the decay timeout of 256 instructions is reached.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "This explicitly confirms that the decay mechanism invalidates the entry after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "Mispredict recovery restores the Tomasulo table's valid state using the architectural register value.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that the table recovery mechanism on a mispredict is left to future work, so it does not support using the architectural registers."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a branch misprediction?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:digest_register` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper...

[Init]
model=gemini-3.1-pro-high conversation=55c2d672-3649-4ea5-946a-de7b557e44ce cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_6721a3ea132acf19

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 7-bit leading and trailing zero counts are encoded into 6-bit fields by taking them modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not say whether the count saturates at 63, is taken modulo 64, or counts bits matching the sign bit",
        "why": "The source notes that the diagram is ambiguous regarding how counts up to 64 fit into a 6-bit field."
      },
      "patch": null,
      "open_question": "How are the 7-bit leading and trailing zero counts encoded into the 6-bit INT digest fields?",
      "enum_candidates": [
        "modulo_64",
        "saturate",
        "match_sign"
      ]
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The Tomasulo-like table entries consist of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "This table cell explicitly lists the fields and widths of the register component's auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The three 6-bit fields of the INT digest are XOR-folded together.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "INFERRED - the three fields are XOR-folded, not concatenated.",
        "why": "The XOR folding is inferred from the visual overlap in the diagram rather than explicitly stated, which makes the assumption unsupported."
      },
      "patch": null,
      "open_question": "Are the three 6-bit fields of the INT digest XOR-folded or concatenated in a way not shown?",
      "enum_candidates": [
        "xor_fold",
        "concatenate"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The d
... [truncated]

[Usage]
{"input_tokens": 30498, "output_tokens": 13568, "thinking_tokens": 12711, "cache_read_tokens": 0, "total_tokens": 44066}

[Result]
status=SUCCESS conversation=55c2d672-3649-4ea5-946a-de7b557e44ce turns=1 duration=90.459244422s usage={"input_tokens": 30498, "output_tokens": 13568, "thinking_tokens": 12711, "cache_read_tokens": 0, "total_tokens": 44066}


