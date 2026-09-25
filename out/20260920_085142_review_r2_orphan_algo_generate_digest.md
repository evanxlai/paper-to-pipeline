success: True
usage: {'input_tokens': 29077, 'output_tokens': 35564, 'thinking_tokens': 31520, 'cache_read_tokens': 0, 'total_tokens': 64641}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The weight width for the sR component's prediction weight tables and usefulness weight tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6-bit weights for both WT and UT entries in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Budget donor structures for resource accounting are selected among tagged banks and bimodal table.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which predictor structure donates storage budget if resource accounting constraints are exceeded?",
      "enum_candidates": [
        "shrink_tagged_banks",
        "reduce_high_bank_entries",
        "downsize_bimodal"
      ]
    },
    {
      "pointer": "/parameters/8",
      "claim": "Integer digest generation selects whether to count leading and trailing zeros versus ones by matching the edge bit.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the integer digest generator select between counting leading/trailing zeros versus ones?",
      "enum_candidates": [
        "match_edge_bit",
        "count_zeros_only",
        "count_ones_only"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "Integer digest leading and trailing bit counts saturate at 63 when identical bits exceed 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 6-bit leading and trailing bit count saturate at 63 or wrap modulo 64 when a 64-bit register has 64 identical bits?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "Floating-point format classification distinguishes FP16, FP32, and FP64 using NaN-boxing.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the floating-point register digest classifier determine whether a register holds FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_boxing",
        "instruction_opcode",
        "fp_status_reg"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "Register values that are not integer, floating-point, or flag use raw LSBs for the digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What digest value should be generated for register types other than integer, floating-point, or flag?",
      "enum_candidates": [
        "raw_lsb",
        "zero_digest",
        "bypass"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The sR hash function combining PC and register digest into index h0 uses an XOR fold.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash function combines the PC and selected register digest into indices h0, h1, and h2 for the sR weight tables?",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "bit_slice"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The sR secondary hash function for index h2 uses an XOR fold.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What secondary hash or folding method is used for computing the sR weight table index h2?",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "prime_modulo"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "Integer digest leading and trailing bit counts saturate at 63 rather than wrapping.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the integer digest handle 64 identical leading or trailing bits when fitting into a 6-bit field?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/parameters/18",
      "claim": "The decay counter is initialized to 255 upon instruction completion.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What initial value is loaded into the 8-bit decay counter when an instruction completes and sets valid=1?",
      "enum_candidates": [
        "255",
        "0",
        "wrap_256"
      ]
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default number of decoded instructions before digest invalidation is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes that RUNLTS invalidates each digest after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The digest width generated from each 64-bit register value is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly defines the digest width as 12 bits for all register types."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The decay counter initialization and expiration behavior follows the init_255_underflow variant.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 8-bit decay counter initialized and clocked to count 256 instructions before invalidation?",
      "enum_candidates": [
        "init_255_underflow",
        "init_255_zero_expire",
        "count_up_to_255"
      ]
    },
    {
      "pointer": "/parameters/16",
      "claim": "The decay counter invalidation variant resolves to init_255_underflow.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 8-bit decay counter clocked and expired across 256 instructions?",
      "enum_candidates": [
        "init_255_underflow",
        "init_255_zero_expire",
        "count_up_to_255"
      ]
    },
    {
      "pointer": "/parameters/17",
      "claim": "Register digests produced during wrong-path execution are retained upon pipeline flush recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 states that extra values produced by finished instructions are leveraged after the flush, confirming digests are retained across pipeline flushes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation and valid bit assertion trigger upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies that writing the digest payload and setting valid occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 12-bit digest is formed by XOR-folding 6 bits of trailing identical bits at [5:0], 6 bits of leading identical bits shifted to [8:3], and 6 LSBs of value shifted to [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify the integer digest as an overlapping XOR fold of trailing bit count, leading bit count, and 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For floating-point registers, format classification extracts sign and leading exponent bits, placing FP16 bits [15:13] at digest[5:3], FP32 bits [31:26] at digest[8:3], and FP64 bits [63:55] at digest[11:3], leaving bits [2:0] zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) establish the format-specific bit extractions right-aligned at digest bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flag registers, the 4-bit flag value is replicated three times across bits [11:0] to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) explicitly define replicating the 4-bit flag value three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "The digest generator produces a 12-bit digest where FP digest bits [2:0] are zero and flag replication fills [11:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 and Figure 6 define the 12-bit format constraints summarized in the algorithm notes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register value with trailing zeros = 3, leading zeros = 60, and value[5:0] = 8 produces digest 0x3E3 via XOR folding.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The unit test computes (0x03) ^ (0x3C << 3) ^ (0x08 << 6) = 0x3E3, matching the overlapping XOR fold in Figure 6(a) and Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A flag register with 4-bit value 0x9 produces digest 0x999 via three-fold replication.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test verifies the 3-fold replication of 4 flag bits into 12 bits specified in Section 4.2 and Figure 6(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register value with bits [31:26] = 0x2B produces digest 0x0158 by shifting to digest[8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The test verifies extraction of bits [31:26] and placement into digest[8:3] as specified in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated when 256 subsequent instructions are decoded without further writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes that each digest is invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Each bank's weight table output is scaled by 2.5 when selected register usefulness is positive, and suppressed with a x0 multiplier when non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly includes a per-bank multiplier stage of x0 or x2.5 applied to the WT summation output."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A register digest produced during wrong-path execution remains valid and available to subsequent predictions upon pipeline flush recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 explicitly confirms that register values produced prior to misprediction resolution are retained and leveraged after the flush."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read th...

[Init]
model=gemini-3.8-flash-medium conversation=46a81afe-55e3-4103-85dd-2bbbf9b0e17e cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The weight width for the sR component's prediction weight tables and usefulness weight tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6-bit weights for both WT and UT entries in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Budget donor structures for resource accounting are selected among tagged banks and bimodal table.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which predictor structure donates storage budget if resource accounting constraints are exceeded?",
      "enum_candidates": [
        "shrink_tagged_banks",
        "reduce_high_bank_entries",
        "downsize_bimodal"
      ]
    },
    {
      "pointer": "/parameters/8",
      "claim": "Integer digest generation selects whether to count leading and trailing zeros versus ones by matching the edge bit.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the integer digest generator select between counting leading/trailing zeros versus ones?",
      "enum_candidates": [
        "match_edge_bit",
        "count_zeros_only",
        "count_ones_only"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "Integer digest leading and trailing bit counts saturate at 63 when identical bits exceed 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 6-bit leading and trailing bit count saturate at 63 or wrap modulo 64 when a 64-bit register has 64 identical bi
... [truncated]

[Usage]
{"input_tokens": 29077, "output_tokens": 35564, "thinking_tokens": 31520, "cache_read_tokens": 0, "total_tokens": 64641}

[Result]
status=SUCCESS conversation=46a81afe-55e3-4103-85dd-2bbbf9b0e17e turns=1 duration=177.525089287s usage={"input_tokens": 29077, "output_tokens": 35564, "thinking_tokens": 31520, "cache_read_tokens": 0, "total_tokens": 64641}


