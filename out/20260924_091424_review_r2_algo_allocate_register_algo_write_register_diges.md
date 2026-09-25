success: True
usage: {'input_tokens': 31523, 'output_tokens': 20587, 'thinking_tokens': 18638, 'cache_read_tokens': 0, 'total_tokens': 52110}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "At decode, the ROB index is stored as a tag and the valid bit is cleared.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states this behavior at instruction decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "There are 65 logical registers tracked by the predictor.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries for the register component table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The decay counter requires 8 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly defines the decay_ctr field as 8 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "The ROB tag payload size is 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a payload that can hold either a 14-bit tag or a 12-bit digest",
        "why": "The paper states the payload can hold a 14-bit tag, determining the ROB index width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The decay counter walks down and invalidates the digest after exactly 256 instruction decodes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The test verifies the digest is invalidated exactly 256 decodes after the counter is initialized."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For integer registers, the digest encodes a zero-count and the three fields are XOR-folded into 12 bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper states the inputs, but how the 'zeros (or ones)' count is encoded in 6 bits and how the fields pack into 12 bits is ambiguous."
      },
      "patch": null,
      "open_question": "How are the INT fields packed into 12 bits, and how is the 'zeros (or ones)' count encoded?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For floating-point registers, the extracted sign and exponent fields are right-aligned at bit 3 of the digest.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The text specifies what is extracted, but the alignment at bit 3 is only a visual inference from the diagram, and the classification method is missing."
      },
      "patch": null,
      "open_question": "Are the extracted FP fields right-aligned at bit 3 as drawn, or aligned differently? How is the FP format classified?",
      "enum_candidates": ["align_at_bit_3", "align_at_bit_0"]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For condition-code flags, the 4-bit value is replicated three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The prose exactly dictates this replication logic."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The integer digest matches a specific XOR-folded zero-count result.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "Because the exact encoding of the integer digest counts is ambiguous, the precise numeric expectation of this test is unsupported."
      },
      "patch": null,
      "open_question": "What is the precise expected integer digest for a given value, considering the 'or ones' ambiguity?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The predictor selects the digest of the most useful register among those available in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The text explicitly confirms this selection behavior."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "During update, only one randomly chosen available register in the bank is modified.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The random selection of one available register per bank is explicitly stated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Pipeline squash recovery clears pending writes matching squashed ROBs.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper delegates the recovery mechanism to future work, so a specific squash-handling logic is unsupported."
      },
      "patch": null,
      "open_question": "What is the expected mechanism for recovering the register table on a pipeline squash?",
      "enum_candidates": ["clear_squashed_robs", "full_rat_snapshot", "clear_all_pending"]
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "A pipeline squash specifically clears the payload of the squashed register allocation.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Because recovery is left as future work, a test asserting exact squash clearing behavior is unsupported."
      },
      "patch": null,
      "open_question": "Should a squash clear the pending payload, or is the recovery behavior different?",
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
model=gemini-3.1-pro-high conversation=2b3b08d5-8330-4a2c-ad45-d3231b9f6152 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "At decode, the ROB index is stored as a tag and the valid bit is cleared.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states this behavior at instruction decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "There are 65 logical registers tracked by the predictor.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries for the register component table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The decay counter requires 8 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly defines the decay_ctr field as 8 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "The ROB tag payload size is 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a payload that can hold either a 14-bit tag or a 12-bit digest",
        "why": "The paper states the payload can hold a 14-bit tag, determining the ROB index width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The decay counter walks down and invalidates the digest after exactly 256 instruction decodes.",
      "verdict": "SUP
... [truncated]

[Usage]
{"input_tokens": 31523, "output_tokens": 20587, "thinking_tokens": 18638, "cache_read_tokens": 0, "total_tokens": 52110}

[Result]
status=SUCCESS conversation=2b3b08d5-8330-4a2c-ad45-d3231b9f6152 turns=1 duration=177.732497984s usage={"input_tokens": 31523, "output_tokens": 20587, "thinking_tokens": 18638, "cache_read_tokens": 0, "total_tokens": 52110}


