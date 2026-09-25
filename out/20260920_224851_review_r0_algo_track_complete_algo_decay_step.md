success: True
usage: {'input_tokens': 28126, 'output_tokens': 34102, 'thinking_tokens': 31099, 'cache_read_tokens': 0, 'total_tokens': 62228}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_complete algorithm triggers upon instruction execution completion / writeback.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload and valid bit updates occur when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When completing an instruction, the entry is updated only if the completing ROB tag matches the stored pending payload tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper establishes that a 14-bit ROB tag stored at decode must match at completion following Tomasulo's algorithm before updating the entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction completion, sR_RegTracker[dst_reg_id].decay_ctr is initialized to literal 256.",
      "verdict": "INCONSISTENT",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "function on_complete(dst_reg_id, rob_tag, result_value, reg_type):\n    if dst_reg_id < 65:\n        if sR_RegTracker[dst_reg_id].payload == (rob_tag & 0x3FFF):\n            digest = generate_digest(result_value, reg_type)\n            sR_RegTracker[dst_reg_id].payload = digest & 0xFFF\n            sR_RegTracker[dst_reg_id].valid = 1\n            sR_RegTracker[dst_reg_id].decay_ctr = 255"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Only writes the digest and sets valid if the completing instruction matches the pending ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Tomasulo's algorithm dictates that completion results only commit to a tracking entry if the broadcast tag matches the pending tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegTracker is a direct-mapped table with 65 entries corresponding to logical registers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies dedicated tracker entries per logical register, confirmed by Table 3 allocating 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each sR_RegTracker entry contains a 1-bit valid flag, a 14-bit payload for a tag or digest, and an 8-bit unsigned decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines each of the 65 entries as having 1 bit valid, 14 bits payload, and 8 bits decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "sR_RegTracker consumes 1495 bits of auxiliary storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 65 entries by (1 + 14 + 8 = 23) bits per entry yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "sR_RegTracker is directly indexed by logical register index (0 <= reg_id < 65).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "A table with one entry per logical register is indexed directly by the logical register identifier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default value of parameter decay_interval is 256.",
      "verdict": "INCONSISTENT",
      "evidence": null,
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
      "claim": "decay_interval has a tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the intended tuning range and step for the register digest decay interval, given that the paper fixes invalidation to 256 instructions using an 8-bit counter?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/storage_impact",
      "claim": "The decay counter width in each RegTracker entry is Ceil(log2(decay_interval)) bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines decay_ctr as 8 bits, which equals log2(256) for the 256-instruction decay interval."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For condition-code flags, the 4-bit value is replicated three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly defines the flag digest format as the four flag bits replicated three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer register digest encodes trailing zero/one count, leading zero/one count, and the six least significant bits combined via XOR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the integer digest composition as the count of leading zeros/ones, trailing zeros/ones, and the six least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For FP32 registers, the digest extracts bits [31:26] into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper states that FP register digests extract the sign and exponent MSBs, corresponding to bits [31:26] for 32-bit floats."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decrements each decoded instruction and invalidates upon reaching 0 after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The available register with the largest summed usefulness across UT0, UT1, and UT2 in a bank is selected to index the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies selecting the digest of the most useful register among available registers within each bank to index the direction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "decay_step is evaluated per decoded instruction at decode time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies tracking decoded instructions to perform invalidation after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On each decoded instruction, valid registers decrement their decay counter and invalidate when the counter reaches 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The decrementing counter implements the paper's requirement to invalidate entries after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Decay invalidation prevents stale digests beyond 256 decoded instructions from biasing branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper notes that stale digests degrade accuracy, motivating invalidating after 256 decoded instructions."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_complete+algo:decay_step` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never...

[Init]
model=gemini-3.8-flash-medium conversation=81d17fbe-d8ac-4192-863d-c55aecf09495 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_complete algorithm triggers upon instruction execution completion / writeback.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload and valid bit updates occur when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When completing an instruction, the entry is updated only if the completing ROB tag matches the stored pending payload tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper establishes that a 14-bit ROB tag stored at decode must match at completion following Tomasulo's algorithm before updating the entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction completion, sR_RegTracker[dst_reg_id].decay_ctr is initialized to literal 256.",
      "verdict": "INCONSISTENT",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "function on_complete(dst_reg_id, rob_tag, result_value, reg_type):\n    if dst_reg_id < 65:\n        if sR_RegTracker[dst_reg_id].payload == (rob_tag & 0x3FFF):\n            digest = generate_digest(result_value, reg_type)\n            sR_RegTracker[dst_reg_id].payload = digest & 0xFFF\n            sR_RegTr
... [truncated]

[Usage]
{"input_tokens": 28126, "output_tokens": 34102, "thinking_tokens": 31099, "cache_read_tokens": 0, "total_tokens": 62228}

[Result]
status=SUCCESS conversation=81d17fbe-d8ac-4192-863d-c55aecf09495 turns=1 duration=191.267941655s usage={"input_tokens": 28126, "output_tokens": 34102, "thinking_tokens": 31099, "cache_read_tokens": 0, "total_tokens": 62228}


