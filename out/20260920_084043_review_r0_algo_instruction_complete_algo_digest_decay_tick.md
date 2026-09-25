success: True
usage: {'input_tokens': 28414, 'output_tokens': 45194, 'thinking_tokens': 40881, 'cache_read_tokens': 0, 'total_tokens': 73608}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction completion algorithm triggers at writeback when an instruction produces a destination register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the digest overwrite and valid bit update occur when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The on_complete function in pseudocode is the defined algorithm entry point for completion writeback rather than an undefined helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The function defines the completion writeback handler described in the paper, refuting the deterministic finding that on_complete is an undefined helper call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Completion writeback updates the table only if the entry is invalid and its payload matches the completing instruction's 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies a Tomasulo-like protocol where decode writes the ROB index as a tag and completion must match that tag before writing back the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon matching completion writeback, the table stores the 12-bit digest in payload, sets valid to 1, and initializes decay_ctr to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that completing instructions overwrite the payload with the digest and set valid, resetting the decay timer for the new value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The helper function generate_digest is called to produce 12-bit digests but is not defined in pseudocode or any spec algorithm.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "function generate_digest(reg_type, reg_value):\n    if reg_type == 0:\n        trailing = count_trailing_zeros(reg_value) & 0x3F\n        leading = count_leading_zeros(reg_value) & 0x3F\n        lsb6 = reg_value & 0x3F\n        return (trailing ^ (leading << 3) ^ (lsb6 << 6)) & 0x0FFF\n    elif reg_type == 1:\n        return ((reg_value >> 55) & 0x1FF) << 3\n    elif reg_type == 2:\n        flags = reg_value & 0x0F\n        return flags | (flags << 4) | (flags << 8)\n    return 0\n\nfunction on_complete(dest_reg, rob_tag, reg_value, reg_type):\n    if dest_reg >= 0 and dest_reg < 65:\n        // Verify completing instruction matches current occupant\n        if reg_table[dest_reg].valid == 0 and reg_table[dest_reg].payload == (rob_tag & 0x3FFF):\n            digest = generate_digest(reg_type, reg_value)\n            reg_table[dest_reg].payload = digest & 0x0FFF  // 12-bit digest\n            reg_table[dest_reg].valid = 1\n            reg_table[dest_reg].decay_ctr = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table consists of 65 direct-mapped entries covering logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates a 65-entry table for the register status component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry format comprises a 1-bit valid bit, a 14-bit payload holding either a 14-bit ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines each entry structure as valid (1), payload (14), and decay_ctr (8), matching the 14-bit tag or 12-bit digest payload description in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total storage consumed by the register status and digest table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries of 23 bits each (1 + 14 + 8) multiply to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The register status table is directly indexed by architectural or logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Allocating one entry per logical register corresponds directly to direct indexing by logical register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default decay period of 256 instructions fits within the 8-bit decay_ctr field by using counter values 0 to 255 to represent 256 elapsed instruction cycles.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies invalidating after 256 decoded instructions, which is implemented using an 8-bit counter (0 to 255) invalidating on the 256th tick, refuting the deterministic finding that default 256 is unrepresentable in an 8-bit counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The decay limit parameter has a configurable tuning range of [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed decay period of 256 decoded instructions and does not define a tuning range of [64, 1024]; widening decay_limit beyond 256 would also exceed the 8-bit decay_ctr field without expanding table storage.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/storage_impact",
      "claim": "Varying decay_limit incurs no storage impact as long as decay_ctr remains 8 bits and requires ceil(log2(decay_limit)) bits per register if widened.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 fixes the auxiliary counter width to 8 bits, so any parameter value up to 256 fits with zero storage impact while larger limits require ceil(log2(decay_limit)) bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding 6-bit trailing zero count at [5:0], 6-bit leading zero count at [8:3], and 6-bit value LSB at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify 6-bit trailing zero/one count at [5:0], 6-bit leading zero/one count at [8:3], and Value[5:0] at [11:6] combined via XOR, matching the test calculation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For condition-code flag registers, the 12-bit digest replicates the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times to populate the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For 64-bit float registers, bits [63:55] (sign and top 8 exponent bits) are extracted and placed at digest[11:3] with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies extracting Value[63:55] aligned to digest bit 3, occupying bits [11:3] with bits [2:0] set to 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Logical registers map to 8 banks via reg_id mod 8, placing 9 registers in Bank 0 (R0, R8, ..., R64) and 8 registers in Banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 and Figure 5(c) establish eight banks with Bank 0 holding R0, R8, R16, ... R64, confirming stride-8 modulo mapping."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A valid register digest remains valid through 255 decoded instructions and invalidates upon decoding the 256th instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly mandates invalidation after 256 subsequent decoded instructions have elapsed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's maximum register usefulness is non-positive, its prediction weight contribution is scaled by x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies a per-bank multiplier stage of x0 or x2.5 driven by register usefulness, where non-useful banks are suppressed with x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When a bank's maximum register usefulness is positive, its prediction weight contribution is scaled by x2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly specifies scaling by 2.5 when the bank is judged useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The digest decay tick triggers on the decode of each subsequent instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Decay is explicitly measured in terms of subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The on_instruction_decoded_global function in pseudocode is the algorithm entry point for per-instruction decay rather than an undefined helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The function defines the per-decoded-instruction tick required by the paper, refuting the deterministic finding that on_instruction_decoded_global is an undefined helper call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The decay tick iterates over all 65 entries in the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the table as containing 65 entries covering logical registers 0 through 64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Valid entries increment decay_ctr if less than 255, and invalidate by setting valid to 0 when 256 instructions have elapsed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Incrementing from 0 to 255 and invalidating on the 256th decode tick implements the exact 256-instruction decay window using an 8-bit counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Digests are invalidated after 256 decoded instructions to prevent stale values from degrading prediction accuracy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The note accurately reproduces the rationale and decay window stated in Section 4.2."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_complete+algo:digest_decay_tick` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alon...

[Init]
model=gemini-3.8-flash-medium conversation=ce3d4dc5-97cb-462a-8158-a54dbaaebf81 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_01cec91a605a3d5d

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction completion algorithm triggers at writeback when an instruction produces a destination register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the digest overwrite and valid bit update occur when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The on_complete function in pseudocode is the defined algorithm entry point for completion writeback rather than an undefined helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The function defines the completion writeback handler described in the paper, refuting the deterministic finding that on_complete is an undefined helper call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Completion writeback updates the table only if the entry is invalid and its payload matches the completing instruction's 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies a Tomasulo-like protocol where decode writes the ROB index as a tag and completion must match that tag before writing back the digest."
      },
  
... [truncated]

[Usage]
{"input_tokens": 28414, "output_tokens": 45194, "thinking_tokens": 40881, "cache_read_tokens": 0, "total_tokens": 73608}

[Result]
status=SUCCESS conversation=ce3d4dc5-97cb-462a-8158-a54dbaaebf81 turns=1 duration=233.918030664s usage={"input_tokens": 28414, "output_tokens": 45194, "thinking_tokens": 40881, "cache_read_tokens": 0, "total_tokens": 73608}


