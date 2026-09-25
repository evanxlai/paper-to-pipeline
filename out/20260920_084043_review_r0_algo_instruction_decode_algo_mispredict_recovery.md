success: True
usage: {'input_tokens': 29452, 'output_tokens': 42065, 'thinking_tokens': 38363, 'cache_read_tokens': 0, 'total_tokens': 71517}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "At decode time, an instruction writing a destination register triggers an update to the register table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that the trigger event occurs at instruction decode when an instruction writes a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode of an instruction writing a destination register, the register entry valid bit is cleared to 0 and its payload receives the 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that decode sets the destination register entry valid bit to 0 and writes the producing ROB tag into the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The function on_decode is an undefined helper function called by the algorithm.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that on_decode is the declaration of the decode event handler itself rather than an undefined external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The instruction decode algorithm advances decay counters and invalidates valid register digests after 256 decoded instructions.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that decoded instructions must increment decay counters for valid digests and invalidate entries that reach 256 instructions."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function on_decode(dest_reg, rob_tag):\n    for r = 0 to 64:\n        if reg_table[r].valid == 1:\n            reg_table[r].decay_ctr = reg_table[r].decay_ctr + 1\n            if reg_table[r].decay_ctr >= 256:\n                reg_table[r].valid = 0\n    if dest_reg >= 0 and dest_reg < 65:\n        reg_table[dest_reg].valid = 0\n        reg_table[dest_reg].payload = rob_tag & 0x3FFF  // 14-bit ROB tag\n        reg_table[dest_reg].decay_ctr = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "Upon misprediction recovery, registers with valid == 0 matching flushed ROB tags have their payload cleared to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Settles that table recovery on misprediction flushes is explicitly omitted from RUNLTS and left to future work."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like register status table recover entries matching flushed ROB tags on a branch misprediction?",
      "enum_candidates": [
        "clear_matching_tags",
        "checkpoint_rat",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The pseudocode calls undefined helpers named and and on_mispredict_recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Settles that on_mispredict_recovery is the handler definition and and is a built-in boolean operator rather than an undefined function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/notes",
      "claim": "Registers whose producer completed prior to or during the flush remain valid and immediately become available to subsequent restart predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Settles that instructions finishing prior to branch recovery leave their valid register digests visible for subsequent restart predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The auxiliary register table is a direct-mapped table of 65 entries storing a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Settles the 65-entry direct-mapped structure and the exact entry bit breakdown (1 + 14 + 8) * 65 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The register usefulness weight tables comprise 8 banks with 3 tables of 8 entries each, with Bank 0 storing 9 signed 6-bit weights and Banks 1-7 storing 8 signed 6-bit weights totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Settles the storage organization of 65 registers across 3 tables of 8 entries each using 6-bit weights (6 * 65 * 24 = 9360 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register prediction weight tables comprise 8 banks each having WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Settles the exact table capacities across the 8 banks and 6-bit weights totaling 43008 bits."
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
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles that the predictor configuration tracks 65 registers (9 registers in Bank 0 and 8 registers in Banks 1-7)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The parameter num_logical_registers has a tunable range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles that the paper hardcodes 65 logical registers and specifies no parameter range."
      },
      "patch": null,
      "open_question": "What is the legal tuning range of num_logical_registers, and how does bank assignment partition registers when the count is not 65?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "Digest values are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that digest lifetime is bounded to exactly 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The parameter decay_limit has a tunable range of [64, 1024] while stored in an 8-bit decay_ctr.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Settles that decay_ctr is strictly an 8-bit field, which cannot represent values up to 1024 without altering hardware storage."
      },
      "patch": null,
      "open_question": "The parameter range [64, 1024] exceeds the maximum value representable by an 8-bit counter (255); what is the legal range of decay_limit and how is the 256 limit encoded in 8 bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding 6-bit trailing zero count, 6-bit leading zero count shifted by 3, and 6-bit LSB shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles the three 6-bit components and their encoding into the integer register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For flag registers, the 4-bit value is replicated three times to produce the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles that the 4-bit flag value is replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For 64-bit floating point registers, the digest extracts bits [63:55] and places them into digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Settles that the sign bit and high-order exponent bits of FP64 registers are extracted to form the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Logical registers are mapped to banks by register ID modulo 8, with Bank 0 holding 9 registers and Banks 1-7 holding 8 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles that 65 registers map across eight banks with Bank 0 holding nine registers and Banks 1-7 holding eight."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A valid digest remains valid through 255 decoded instructions and transitions to invalid on the 256th instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that digest validity expires after exactly 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank whose maximum usefulness is non-positive has its prediction contribution scaled by x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Settles that bank prediction output is gated by a multiplier stage supporting scaling by x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank with positive usefulness scales its weight sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Settles that bank prediction output is scaled by 2.5 when positive usefulness is established."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_decode+algo:mispredict_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alon...

[Init]
model=gemini-3.8-flash-medium conversation=cbbbf4db-afd2-4029-8fd4-c25311317e7a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_01cec91a605a3d5d

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "At decode time, an instruction writing a destination register triggers an update to the register table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that the trigger event occurs at instruction decode when an instruction writes a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode of an instruction writing a destination register, the register entry valid bit is cleared to 0 and its payload receives the 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that decode sets the destination register entry valid bit to 0 and writes the producing ROB tag into the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The function on_decode is an undefined helper function called by the algorithm.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that on_decode is the declaration of the decode event handler itself rather than an undefined external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1
... [truncated]

[Usage]
{"input_tokens": 29452, "output_tokens": 42065, "thinking_tokens": 38363, "cache_read_tokens": 0, "total_tokens": 71517}

[Result]
status=SUCCESS conversation=cbbbf4db-afd2-4029-8fd4-c25311317e7a turns=1 duration=215.812537385s usage={"input_tokens": 29452, "output_tokens": 42065, "thinking_tokens": 38363, "cache_read_tokens": 0, "total_tokens": 71517}


