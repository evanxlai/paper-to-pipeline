success: True
usage: {'input_tokens': 28710, 'output_tokens': 30722, 'thinking_tokens': 25930, 'cache_read_tokens': 0, 'total_tokens': 59432}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The default weight bit width for the sR prediction and usefulness weight tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that weight tables and usefulness tables in sR use 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter weight_bits has an empirical tuning range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes 6-bit weights in Table 3 and does not describe or evaluate alternative bit widths; the range [5, 8] is unverified in the text.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter weight_bits configures the weight storage width for the WT and UT tables of the sR component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 shows that WT and UT storage entries scale directly with the 6-bit weight width, though these tables are accessed in the prediction and update stages rather than digest generation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends TAGE-SC-L by using register-value digests to predict branch outcomes across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The summary accurately captures the role of sR in integrating register-value digests into the SC of TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The specification is derived from the CBP 2025 paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the publication header verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Backend instruction execution completion broadcasts trigger overwriting the tracking payload with the produced value's digest and setting valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies execution completion as the event that writes the digest payload and asserts the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Decode-stage register renaming/allocation clears the register tracking entry valid bit and stores the ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that decode-time writes record the ROB index tag and clear the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host pipeline must provide decoded instruction counts to invalidate stale digests after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper requires invalidation after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total storage consumed by sR is 53,863 bits, partitioned between WT (43,008 bits), UT (9,360 bits), and the register tracking table (1,495 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 enumerates the exact table formulas and sums to 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Tables in the register component require only a single write port due to random single-register selection per bank during updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper states directly that single write ports suffice for each table in the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper defines the digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The parameter digest_width_bits has a tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes digest width to 12 bits and evaluates no other widths; the tuning range [8, 16] is unverified in the text.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default decay limit for digest invalidation is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly sets the decay threshold to 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The decay_instruction_limit parameter has a tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only considers invalidating after 256 instructions; alternative thresholds in [64, 1024] are not evaluated in the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation is triggered upon instruction execution completion in the backend.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper establishes execution completion as the trigger for calculating the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "For integer registers, the digest encodes leading zero/one count, trailing zero/one count, and the 6 LSBs XOR-folded into 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the integer digest components as leading zero/one count, trailing zero/one count, and 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Floating-point digests extract Val[15:13] for FP16, Val[31:26] for FP32, and Val[63:55] for FP64, placed at digest bits [5:3], [8:3], and [11:3] respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign and high exponent bits, which correspond to the exact bit positions depicted in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "For condition flags, the 4-bit flag value is replicated three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper states verbatim that the four flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "The helper functions count_leading_zeros_or_ones and count_trailing_zeros_or_ones invoked in digest_generation must be defined for the algorithm to be implementable.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper requires leading and trailing zero/one counts, but the spec invokes undefined helper functions without providing their implementation."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "function count_leading_zeros_or_ones(val: uint64) -> uint64:\n    match_bit = (val >> 63) & 1\n    cnt = 0\n    for i in range(63, -1, -1):\n        if ((val >> i) & 1) == match_bit:\n            cnt += 1\n        else:\n            break\n    return cnt\n\nfunction count_trailing_zeros_or_ones(val: uint64) -> uint64:\n    match_bit = val & 1\n    cnt = 0\n    for i in range(64):\n        if ((val >> i) & 1) == match_bit:\n            cnt += 1\n        else:\n            break\n    return cnt\n\nfunction generate_digest(val: uint64, reg_type: enum { INT, FP16, FP32, FP64, FLAG }) -> uint12:\n    if reg_type == INT:\n        // Count identical leading/trailing bits\n        trailing_cnt = count_trailing_zeros_or_ones(val) & 0x3F\n        leading_cnt = count_leading_zeros_or_ones(val) & 0x3F\n        val_lsb = val & 0x3F\n        // Overlapping XOR fold into 12 bits\n        digest = trailing_cnt ^ (leading_cnt << 3) ^ (val_lsb << 6)\n        return digest & 0x0FFF\n    elif reg_type == FP16:\n        // Val[15:13] placed at digest[5:3]\n        res_fp16 = ((val >> 13) & 0x7) << 3\n        return res_fp16\n    elif reg_type == FP32:\n        // Val[31:26] placed at digest[8:3]\n        res_fp32 = ((val >> 26) & 0x3F) << 3\n        return res_fp32\n    elif reg_type == FP64:\n        // Val[63:55] placed at digest[11:3]\n        res_fp64 = ((val >> 55) & 0x1FF) << 3\n        return res_fp64\n    elif reg_type == FLAG:\n        // Val[3:0] replicated 3 times into digest[11:0]\n        flags = val & 0xF\n        res_flag = flags | (flags << 4) | (flags << 8)\n        return res_flag\n    return 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Notes specify the overlap structure of integer digests, the bit-3 alignment of FP digests, and the 3-nibble replication of flag digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type. (1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers. (2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent. (3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The notes summarize the structural placement described in Section 4.2 and Figure 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test 0 evaluates integer digest generation on 0x18 yielding trailing count 3, leading count 59, LSB 24, and digest 0x7DB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test verifies the exact folding formula defined for integer registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test 1 tests flag digest replication producing 0x999 from condition flags 0x9.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test directly validates the 3-fold replication of the 4 flag bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test 2 checks that FP64 extraction extracts bits [63:55] into digest bits [11:3] with [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The test validates the placement of the sign and 8 exponent bits into bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test 3 tests decay counter invalidation after 256 instructions have decoded without overwrite.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test directly verifies the 256-instruction invalidation condition."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test 4 tests that negative bank usefulness suppresses bank contribution to sR with a x0 multiplier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "The test validates that usefulness tracking determines whether bank predictions are gated on or off."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Unit test 6 tests that among multiple valid available registers in a bank, exactly one is randomly chosen during training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The test verifies the random selection mechanism among available registers within a bank during updates."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+global+algo:digest_generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=a7aa5cb2-adf5-4e67-88e2-75ac0f9e6bb6 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The default weight bit width for the sR prediction and usefulness weight tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that weight tables and usefulness tables in sR use 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter weight_bits has an empirical tuning range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes 6-bit weights in Table 3 and does not describe or evaluate alternative bit widths; the range [5, 8] is unverified in the text.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The parameter weight_bits configures the weight storage width for the WT and UT tables of the sR component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 shows that WT and UT storage entries scale directly with the 6-bit weight width, though these tables are accessed in the prediction and update stages rather than digest generation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends TAGE-SC-L by using register-value digests to predict branch outcomes across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing
... [truncated]

[Usage]
{"input_tokens": 28710, "output_tokens": 30722, "thinking_tokens": 25930, "cache_read_tokens": 0, "total_tokens": 59432}

[Result]
status=SUCCESS conversation=a7aa5cb2-adf5-4e67-88e2-75ac0f9e6bb6 turns=1 duration=141.743425296s usage={"input_tokens": 28710, "output_tokens": 30722, "thinking_tokens": 25930, "cache_read_tokens": 0, "total_tokens": 59432}


