success: True
usage: {'input_tokens': 28728, 'output_tokens': 30445, 'thinking_tokens': 26279, 'cache_read_tokens': 0, 'total_tokens': 59173}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation triggers at execution or writeback time when an instruction produces a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that when an instruction completes execution, the produced value's digest overwrites the tracking payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest generates a 12-bit digest from a 64-bit register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines digest generation as compressing each 64-bit value into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digests are formed by XOR folding a 6-bit trailing bit count at bits [5:0], a 6-bit leading bit count shifted to bits [8:3], and the 6 LSBs shifted to bits [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "trailing one/zero #    [5:0]         6 bits  count of trailing 0s (or 1s)",
        "why": "Figure 6(a) defines the integer digest structure by XOR-folding trailing count [5:0], leading count [8:3], and Value[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer digest generation, whether trailing or leading zeros versus ones are counted is decided by checking the LSB and MSB respectively.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does integer digest generation choose between counting zeros versus ones based on the edge bit (LSB/MSB), count only zeros, or count whichever run is non-zero?",
      "enum_candidates": [
        "match_edge_bit",
        "zeros_only",
        "max_count"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "When a 64-bit integer contains 64 identical leading or trailing bits, the 6-bit count saturates at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "When a 64-bit integer contains 64 identical bits, does the 6-bit count field saturate at 63 or wrap modulo 64?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating point digests place the sign and exponent bits starting at digest bit 3 with bits [2:0] set to 0, extracting Val[15:13] for FP16, Val[31:26] for FP32, and Val[63:55] for FP64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP64     Value[63:55]      9 bits        [11:3]        sign(63) + exp[62:55]",
        "why": "Figure 6(b) aligns FP16, FP32, and FP64 sign and high exponent bit slices at digest bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition-code flag digests replicate the 4 flag bits three times to fill all 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states condition-code flag digests replicate the 4 flag bits three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "count_leading_zeros, count_leading_ones, count_trailing_zeros, and count_trailing_ones are primitive bitwise operations provided by hardware, while return is a pseudocode keyword.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies leading and trailing zero/one counts as the basic primitive operations used to generate integer digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "Digest generation compresses 64-bit data into a 12-bit signature using XOR folding for integers, alignment at bit 3 for floats, and 3x replication for flags.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The notes summarize the 12-bit digest formats defined in Section 4.2 and Figure 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default number of logical registers tracked by the register components is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Eight banks containing 8 or 9 registers each total 65 logical registers, as confirmed by Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "num_logical_registers has a configurable range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates only a fixed target of 65 logical registers across 8 banks; is num_logical_registers fixed by the ISA or configurable across [32, 128]?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "int_digest_generation_check correctly computes the 12-bit digest as 3 ^ (60 << 3) ^ (8 << 6) = 995 (0x3E3) for integer 0x0000000000000008.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test correctly calculates the 12-bit digest from Figure 6(a) for the given 60 leading zeros, 3 trailing zeros, and LSB of 8."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "fp64_digest_generation_check correctly shifts Val[63:55] = 0x80 to digest bits [11:3] yielding 0x400.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP64     Value[63:55]      9 bits        [11:3]        sign(63) + exp[62:55]",
        "why": "The test matches the FP64 extraction and shift to digest[11:3] specified in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "flag_digest_generation_check replicates nibble 0xB three times to produce digest 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 0b1011 three times produces 0xBBB as required by Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "digest_decay_invalidation invalidates a register digest when 256 instructions are decoded without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test verifies invalidation after 256 decoded instructions as specified in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "bank_usefulness_selection_and_gating selects the most useful register in a bank and scales the bank output by 2.5 if usefulness is positive or gates it to 0 if non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Figure 5(c) and Section 4.2 specify selecting the most useful register in the bank and multiplying WT sum by 2.5 or 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Valid register digests in reg_tracking_table are retained across pipeline squash redirects after branch mispredictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 explicitly relies on retaining completed values across the flush redirect to aid post-squash predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "dispatch_rename triggers at decode/rename when an instruction writing a destination logical register enters the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 establishes that this action occurs at decode for an instruction writing a register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "dispatch_rename clears the valid bit and stores the 14-bit ROB index in the register tracking table payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode directly implements storing the ROB tag and clearing the valid bit at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "decay_ctr is cleared to 0 at dispatch/rename.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does dispatch_rename reset decay_ctr, or is decay_ctr initialized to 0 when the instruction completes and the valid digest is written?",
      "enum_candidates": [
        "at_completion",
        "at_dispatch"
      ]
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Clearing the valid bit prevents in-flight uncommitted values from being read as digests, while the ROB tag allows matching upon completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The notes faithfully explain the purpose of the valid bit and ROB tag mechanism stated in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "reg_tracking_table consists of 65 entries, each with a 1-bit valid field, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of valid(1), payload(14), and decay_ctr(8), totaling 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "reg_tracking_table is directly indexed by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one dedicated entry per logical register corresponds to direct indexing by logical register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "decay_instruction_limit defaults to 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the digest invalidation limit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "decay_instruction_limit has a configurable range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies only a 256-instruction decay limit; what is the legal range and step size for tuning decay_instruction_limit?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The storage impact of decay_instruction_limit is num_logical_registers * ceil(log2(decay_instruction_limit)) bits in the tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates an 8-bit counter (log2(256) = 8) per logical register in the tracking table."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:generate_digest+algo:dispatch_rename` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they...

[Init]
model=gemini-3.8-flash-medium conversation=56e4f943-b15b-40ba-8e62-c237eecaf06c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation triggers at execution or writeback time when an instruction produces a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that when an instruction completes execution, the produced value's digest overwrites the tracking payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest generates a 12-bit digest from a 64-bit register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines digest generation as compressing each 64-bit value into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digests are formed by XOR folding a 6-bit trailing bit count at bits [5:0], a 6-bit leading bit count shifted to bits [8:3], and the 6 LSBs shifted to bits [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "trailing one/zero #    [5:0]         6 bits  count of trailing 0s (or 1s)",
        "why": "Figure 6(a) defines the integer digest structure by XOR-folding trailing count [5:0], leading count [8:3], and Value[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer digest generation, whether trailing or leading zeros versus ones are counted is decided by checking the LSB and MSB resp
... [truncated]

[Usage]
{"input_tokens": 28728, "output_tokens": 30445, "thinking_tokens": 26279, "cache_read_tokens": 0, "total_tokens": 59173}

[Result]
status=SUCCESS conversation=56e4f943-b15b-40ba-8e62-c237eecaf06c turns=1 duration=158.251752648s usage={"input_tokens": 28728, "output_tokens": 30445, "thinking_tokens": 26279, "cache_read_tokens": 0, "total_tokens": 59173}


