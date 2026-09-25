success: True
usage: {'input_tokens': 29781, 'output_tokens': 49939, 'thinking_tokens': 44601, 'cache_read_tokens': 0, 'total_tokens': 79720}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/2/default",
      "claim": "The default decay interval counter value is 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "A default value of 256 cannot fit into the 8-bit unsigned 'decay_ctr' field declared in /state/2/entry_format, which has a maximum representable value of 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/2/default",
        "value": 255
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The legal tuning range for decay_interval is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The legal tuning range for decay_interval is not specified in the paper, which evaluates only a fixed 256-instruction decay interval.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "track_decode triggers at instruction decode time for any instruction producing a register write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that decode of an instruction writing a register allocates the tracker entry with the ROB tag and clears the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "track_decode initializes decay_ctr to 256 upon allocating an entry.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Assigning decay_ctr = 256 collides with the 8-bit field width declared for decay_ctr in /state/2/entry_format (maximum value 255)."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function on_decode(dst_reg_id, rob_tag):\n    if dst_reg_id < 65:\n        sR_RegTracker[dst_reg_id].valid = 0\n        sR_RegTracker[dst_reg_id].payload = rob_tag & 0x3FFF\n        sR_RegTracker[dst_reg_id].decay_ctr = 255"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "track_decode invalidates the previous valid digest for dst_reg_id and sets the in-flight ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that the entry's valid bit is cleared and overwritten with the in-flight ROB tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegTracker is a direct-mapped array of 65 entries indexed by logical register ID.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Settles that the tracker table holds one entry per logical register (65 entries total)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each sR_RegTracker entry contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Settles the exact entry layout of valid (1 bit), payload (14 bits), and decay counter (8 bits) across 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage cost of sR_RegTracker is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Settles the total tracker storage budget as 65 * (1 + 14 + 8) = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Settles that the baseline predictor tracks 65 logical registers across its usefulness tables and tracker."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The legal tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The legal tuning range for num_logical_registers is not specified in the paper, which evaluates only a fixed 65-register configuration.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "num_logical_registers linearly scales UT storage by 24 * 6 bits and RegTracker storage by 23 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Settles that each logical register contributes 6 * 24 = 144 bits of UT storage and 23 bits of auxiliary tracker storage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest triggers on execution complete / writeback when a producer instruction writes a 64-bit value to a destination register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles that value digest generation occurs at producer instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest combines trailing zero/one count, leading zero/one count, and 6 LSBs via XOR folding into a 12-bit digest for INT registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles the composition of integer register digests using leading/trailing zero/one counts and the 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest extracts format-specific sign and exponent bits for FP registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Settles that floating-point digests extract the sign bit and leading exponent bits based on classified format."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest replicates 4-bit condition code flags three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles that 4 condition flag bits are replicated three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "count_trailing_zeros_or_ones and count_leading_zeros_or_ones helper functions are defined to compute integer leading and trailing identical bit counts.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": null,
        "why": "The pseudocode invokes helper functions count_trailing_zeros_or_ones and count_leading_zeros_or_ones without defining their implementation or bit-matching semantics."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "function count_trailing_zeros_or_ones(val):\n    bit = val & 1\n    cnt = 0\n    while cnt < 64 and ((val >> cnt) & 1) == bit:\n        cnt = cnt + 1\n    return cnt\n\nfunction count_leading_zeros_or_ones(val):\n    bit = (val >> 63) & 1\n    cnt = 0\n    while cnt < 64 and ((val >> (63 - cnt)) & 1) == bit:\n        cnt = cnt + 1\n    return cnt\n\nfunction is_fp16(val):\n    return (val >> 16) == 0\n\nfunction is_fp32(val):\n    return (val >> 32) == 0\n\nfunction generate_digest(val, reg_type):\n    if reg_type == INT:\n        // 6-bit counts of trailing and leading identical bits, 6 LSBs of value\n        trailing_cnt = count_trailing_zeros_or_ones(val) & 0x3F\n        leading_cnt = count_leading_zeros_or_ones(val) & 0x3F\n        lsb6 = val & 0x3F\n        // 3-way XOR fold with 3-bit horizontal overlap offsets\n        digest = trailing_cnt ^ (leading_cnt << 3) ^ (lsb6 << 6)\n        return digest & 0xFFF\n    else if reg_type == FP:\n        // Inspect format: FP16 uses Val[15:13], FP32 uses Val[31:26], FP64 uses Val[63:55]\n        if is_fp16(val):\n            fp_res = (val[15:13] & 0x7) << 3\n            return fp_res\n        else if is_fp32(val):\n            fp_res = (val[31:26] & 0x3F) << 3\n            return fp_res\n        else: // FP64\n            fp_res = (val[63:55] & 0x1FF) << 3\n            return fp_res\n    else if reg_type == FLAGS:\n        // 4-bit condition flags replicated 3 times into 12 bits\n        flags4 = val & 0xF\n        flags_res = flags4 | (flags4 << 4) | (flags4 << 8)\n        return flags_res\n    else:\n        return 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "Leading and trailing identical bit counts for integer registers saturate at 63 to fit in 6 bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) specifies 6-bit fields for leading and trailing identical bit counts, but the paper does not specify whether a count of 64 identical bits saturates at 63 or wraps modulo 64.",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Condition code flags value 0x9 produces the 12-bit digest 0x999 via 3-way replication.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles that 4-bit condition flag values replicate three times into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer register digest XOR-folds 6 bits of trailing count, 6 bits of leading count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles the 3-field XOR-folding structure of integer register digests with 3-bit overlap offsets."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register digest extracts Value[31:26] into digest bits [8:3] with bits [2:0] set to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Settles the extraction of sign and leading exponent bits for FP32 values into digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register tracker entry is invalidated after 256 subsequent instructions have been decoded without writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that tracker entries are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Each bank selects the register digest with the largest summed usefulness among available registers in that bank to index its weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the available register with the highest usefulness in the bank is selected and forwarded to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank's prediction weight sum is multiplied by x0 when its selected register usefulness is non-positive, gating its contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Settles that bank weight sums are gated by 0 or scaled by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "sR extends the Statistical Corrector by capturing correlations between recently produced architectural register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes.",
        "why": "Settles that sR is an SC extension capturing register-value correlations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The 65 logical registers are partitioned across 8 banks with 8 or 9 registers per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles the 8-bank organization across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The specification is distilled from the CBP 2025 paper RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "Settles the title and primary source of the distilled specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires a writeback/completion broadcast providing destination register ID, produced 64-bit value, register type, and ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles that instruction completion must supply the produced value and mark the entry valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires decode notification with destination register ID and allocated ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that instruction decode must supply the destination register ID and ROB tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Branch commit update criteria require tracking which registers were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Settles that update criteria require knowing which registers were valid/available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage cost for the sR component is 53863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Settles the storage breakdown in Table 3 where sR total storage is 53863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The storage breakdown consists of 43008 bits of WT, 9360 bits of UT, and 1495 bits of RegTracker auxiliary storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Settles the auxiliary tracker storage of 65 * 23 = 1495 bits complementing the WT and UT tables in Table 3."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_decode+global+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; ...

[Init]
model=gemini-3.8-flash-medium conversation=95f78ff8-3764-42a5-9819-dfcdfbdec115 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/2/default",
      "claim": "The default decay interval counter value is 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "A default value of 256 cannot fit into the 8-bit unsigned 'decay_ctr' field declared in /state/2/entry_format, which has a maximum representable value of 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/2/default",
        "value": 255
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The legal tuning range for decay_interval is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The legal tuning range for decay_interval is not specified in the paper, which evaluates only a fixed 256-instruction decay interval.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "track_decode triggers at instruction decode time for any instruction producing a register write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that decode of an instruction writing a register allocates the tracker entry with the ROB tag and clears the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "track_decode initializes decay_ctr to 256 upon allocating an entry.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Assigning decay_ctr = 256 collides with the 8-bit field width declared for decay_ctr in /state/2/entry_format (maximum value 255)."
      },
      "patch": {
        "op": "replace",
... [truncated]

[Usage]
{"input_tokens": 29781, "output_tokens": 49939, "thinking_tokens": 44601, "cache_read_tokens": 0, "total_tokens": 79720}

[Result]
status=SUCCESS conversation=95f78ff8-3764-42a5-9819-dfcdfbdec115 turns=1 duration=280.275581953s usage={"input_tokens": 29781, "output_tokens": 49939, "thinking_tokens": 44601, "cache_read_tokens": 0, "total_tokens": 79720}


