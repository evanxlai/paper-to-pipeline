success: True
usage: {'input_tokens': 31277, 'output_tokens': 29851, 'thinking_tokens': 26695, 'cache_read_tokens': 0, 'total_tokens': 61128}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "track_register_complete triggers upon instruction completion in the execution/writeback stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The text directly states that register digest tracking and valid bit updates occur when an instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon instruction completion, if the ROB tag matches the in-flight entry, the payload is overwritten with the 12-bit digest and marked valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies overwriting the entry's payload with the digest and setting the valid bit when the producing instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon completion, the RTT entry decay counter is reset to 255 to initiate an instruction countdown window.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 8-bit decay counter initialize to 255 and count down to zero, or does it initialize to another value to span the full 256-instruction decay window?",
      "enum_candidates": [
        "init_255",
        "init_256",
        "underflow_wrap"
      ]
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Digest decay triggers per decoded instruction at the decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that decay tracking operates based on the count of subsequent instructions that have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The decay loop evaluates all 65 tracked logical register entries (R0 through R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data allocates 65 tracking entries, confirming 65 logical registers are tracked."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "An RTT entry is invalidated immediately when decay_ctr reaches 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Does the decay counter invalidate the entry upon decrementing to zero, or upon underflowing past zero?",
      "enum_candidates": [
        "zero_invalidation",
        "underflow_invalidation"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The RTT consists of 65 entries of 23 bits each (1 valid, 14 payload, 8 decay_ctr) totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms the 65-entry organization with 1-bit valid, 14-bit payload, and 8-bit decay counter per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Logical registers are partitioned across 8 banks with eight or nine registers per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The prose confirms that the register component partitions the logical registers across eight banks with 8 or 9 registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT0 comprises 8 banks of 512 entries of 6-bit counters totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit counters with 2^9 = 512 entries per bank across 8 banks for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "WT1 comprises 8 banks of 256 entries of 6-bit counters totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit counters with 2^8 = 256 entries per bank across 8 banks for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "WT2 comprises 8 banks of 128 entries of 6-bit counters totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit counters with 2^7 = 128 entries per bank across 8 banks for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default decay threshold is 256 decoded instructions requiring an 8-bit counter per entry.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text explicitly establishes the 256-instruction decay threshold, matching the 8-bit decay counter allocated in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default number of logical registers is 65, consuming 23 bits in RTT and 144 bits in UT per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the UT storage around 65 registers with three 8-entry 6-bit tables (144 bits per register)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer value of 0 caps leading and trailing zero counts at 63 to fit in 6 bits, producing digest 0x1C7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 64-bit leading and trailing zero/one counts encoded into 6 bits for all-zero or all-one integer registers?",
      "enum_candidates": [
        "saturate",
        "modulo_64",
        "match_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer register digest for value 8 computes 3 trailing zeros, 60 leading zeros, and combines them via XOR fold.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the integer digest distinguish between counting zeros versus counting ones, and does it combine the fields via three-way XOR fold?",
      "enum_candidates": [
        "count_zeros",
        "match_msb_lsb",
        "count_ones"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A 4-bit condition-code flag value is replicated three times to form a 12-bit digest (0xBBB for flags 0b1011).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 12-bit digest is formed by replicating the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "FP32 digest extracts Value[31:26] and places it at digest[8:3] with digest[2:0] remaining zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are floating-point digest bit slices right-aligned at digest bit 3 leaving bits [2:0] zero, or right-aligned at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "At instruction count 255 decay_ctr is 1 and valid is 1, and at instruction count 256 valid transitions to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the 8-bit decay counter count 256 instructions: does it initialize to 255 and expire on underflow, or expire at count zero?",
      "enum_candidates": [
        "underflow_wrap",
        "zero_invalidation",
        "nine_bit_counter"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank with non-positive usefulness (<= 0) selects multiplier x0, contributing exactly 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What driving signal selects between the x0 and x2.5 bank multipliers in the register SC component?",
      "enum_candidates": [
        "usefulness_gated",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank with positive usefulness (> 0) selects multiplier x2.5, scaling its WT sum by 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the x2.5 scaling factor dynamically driven by positive bank usefulness, or statically applied?",
      "enum_candidates": [
        "usefulness_gated",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "If multiple registers in a bank were available at prediction time, one is randomly chosen for SC update upon misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The text directly states that if multiple registers were available in the same bank, one is randomly selected to update the tables."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_register_complete+algo:track_register_decay` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spe...

[Init]
model=gemini-3.8-flash-medium conversation=4586b732-3f81-474a-b7bb-af65d3abec4b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "track_register_complete triggers upon instruction completion in the execution/writeback stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The text directly states that register digest tracking and valid bit updates occur when an instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon instruction completion, if the ROB tag matches the in-flight entry, the payload is overwritten with the 12-bit digest and marked valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies overwriting the entry's payload with the digest and setting the valid bit when the producing instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon completion, the RTT entry decay counter is reset to 255 to initiate an instruction countdown window.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 8-bit decay counter initialize to 255 and count down to zero, or does it initialize to another value to span the full 256-instruction decay window?",
      "enum_candidates": [
        "init_255",
        "init_256",
        "underflow_wrap"
      ]
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Digest decay triggers per decoded instruction at the decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote":
... [truncated]

[Usage]
{"input_tokens": 31277, "output_tokens": 29851, "thinking_tokens": 26695, "cache_read_tokens": 0, "total_tokens": 61128}

[Result]
status=SUCCESS conversation=4586b732-3f81-474a-b7bb-af65d3abec4b turns=1 duration=162.84799115s usage={"input_tokens": 31277, "output_tokens": 29851, "thinking_tokens": 26695, "cache_read_tokens": 0, "total_tokens": 61128}


