success: True
usage: {'input_tokens': 29213, 'output_tokens': 37912, 'thinking_tokens': 33962, 'cache_read_tokens': 0, 'total_tokens': 67125}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest triggers when an instruction completes and produces a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the digest is generated and overwrites the payload when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the digest encodes 6-bit counts of trailing and leading identical bits and the 6 least significant bits, folded via an overlapping XOR tree into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the three 6-bit fields and Figure 6(a) specifies their overlapping XOR fold at 3-bit offsets to form a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "When an integer register has 64 identical bits, the 6-bit leading and trailing bit counts are saturated at 63 rather than wrapped modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies 6-bit fields for the counts but does not state whether a run of 64 identical bits saturates at 63 or wraps modulo 64."
      },
      "patch": null,
      "open_question": "How should the 6-bit count field encode a run of 64 identical leading or trailing bits?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point format classification inspects the most significant bits of the register value to distinguish FP16, FP32, and FP64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper notes that the most significant bits are inspected to classify format, but gives no bit patterns or rules for the classification helper."
      },
      "patch": null,
      "open_question": "What specific bit patterns on the most significant bits determine whether a register value is classified as FP16, FP32, or FP64?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For floating-point registers, the sign bit and high-order exponent bits are placed into digest bits [11:3], leaving digest bits [2:0] as 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) shows the sign and upper exponent slice aligned with LSB at digest bit 3, leaving bits [2:0] unused."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flag registers, the 4 flag bits are replicated three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times across the 12 bits of the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default decay period after which a digest is invalidated is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 subsequent decoded instructions as the invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/range",
      "claim": "decay_instructions has a valid tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper uses only the fixed value of 256 instructions and does not describe or evaluate a tuning parameter range."
      },
      "patch": null,
      "open_question": "What is the legal search range of decay_instructions for parameter tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly fixes the generated digest width at 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "digest_width_bits has a tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper presents only a 12-bit digest format without discussing or exploring alternative digest widths."
      },
      "patch": null,
      "open_question": "What is the legal tuning range of digest_width_bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The parameter unit_tests_3_variant selects between init_255_underflow, init_255_zero_expire, and count_up_to_255 for the 8-bit counter decay semantics.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates an 8-bit decay_ctr but the paper does not specify the counter progression scheme or parameterize it."
      },
      "patch": null,
      "open_question": "Which counter progression scheme should be implemented for the 8-bit decay_ctr to expire after 256 decoded instructions?",
      "enum_candidates": [
        "init_255_underflow",
        "init_255_zero_expire",
        "count_up_to_255"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "INT register value 0x0000000000000008 produces digest 0x3E3 via overlapping XOR folding.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Value 0x8 has 3 trailing zeros, 60 leading zeros, and LSBs 0x08, folding as 0x03 ^ (0x3C << 3) ^ (0x08 << 6) = 0x3E3 per Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A 4-bit FLAG register with value 0x9 replicates across three nibbles to produce digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 4-bit value 0x9 three times into a 12-bit vector directly yields 0x999."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register with bits [31:26] = 0x2B extracts to digest bits [8:3], yielding 0x0158.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) assigns FP32 bits [31:26] to digest bits [8:3], which gives 0x2B << 3 = 0x158 with digest bits [2:0] zeroed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Register R4 is written with decay_ctr = 256 and invalidates when decay_ctr counts down to 0 on the 256th decode step.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines decay_ctr as an 8-bit field which cannot hold 256, and the paper does not specify the counter initialization value or direction."
      },
      "patch": null,
      "open_question": "How should the 8-bit decay_ctr be initialized and updated to expire exactly on the 256th decoded instruction?",
      "enum_candidates": [
        "init_255_underflow",
        "init_255_zero_expire",
        "count_up_to_255"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An sR bank outputs 0 when its usefulness is non-positive and scales its WT sum by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies a per-bank multiplier of x0 or x2.5 driven by bank usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Arithmetic instructions completed speculatively on the wrong path before a pipeline flush retain their valid digests in sR_RegStatus after flush recovery.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper refers to in-flight instructions prior to the branch completing before resolution, and does not specify whether wrong-path speculative writes are retained or rolled back."
      },
      "patch": null,
      "open_question": "Are register digests written by speculative wrong-path instructions retained or invalidated across a pipeline flush?",
      "enum_candidates": [
        "retain",
        "flush"
      ]
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "decode_rename triggers at the instruction decode / rename stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly anchors tag updates and decay tracking to the instruction decode stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a logical register clears the valid bit and stores its ROB index tag into sR_RegStatus, and all valid entries decrement decay_ctr, clearing valid after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies clearing the valid bit and storing the ROB tag at decode, while invalidating digests after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus is a 65-entry flat table directly indexed by logical register ID (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper defines one entry per logical register, totaling 65 entries across the 8 banks (R0..R64) as reflected in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry in sR_RegStatus consists of a 1-bit valid flag, a 14-bit payload holding a ROB tag or digest, and an 8-bit decay_ctr.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines each entry as containing a 1-bit valid bit, a 14-bit payload, and an 8-bit decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage size of sR_RegStatus auxiliary data is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits (1 + 14 + 8) equals exactly 1495 bits as listed in Table 3."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:generate_digest+algo:decode_rename` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they n...

[Init]
model=gemini-3.8-flash-medium conversation=e97b0aa8-37f3-47e3-84b7-25de936580f6 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest triggers when an instruction completes and produces a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the digest is generated and overwrites the payload when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the digest encodes 6-bit counts of trailing and leading identical bits and the 6 least significant bits, folded via an overlapping XOR tree into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the three 6-bit fields and Figure 6(a) specifies their overlapping XOR fold at 3-bit offsets to form a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "When an integer register has 64 identical bits, the 6-bit leading and trailing bit counts are saturated at 63 rather than wrapped modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies 6-bit fields for the counts but does not state whether a 
... [truncated]

[Usage]
{"input_tokens": 29213, "output_tokens": 37912, "thinking_tokens": 33962, "cache_read_tokens": 0, "total_tokens": 67125}

[Result]
status=SUCCESS conversation=e97b0aa8-37f3-47e3-84b7-25de936580f6 turns=1 duration=190.324896763s usage={"input_tokens": 29213, "output_tokens": 37912, "thinking_tokens": 33962, "cache_read_tokens": 0, "total_tokens": 67125}


