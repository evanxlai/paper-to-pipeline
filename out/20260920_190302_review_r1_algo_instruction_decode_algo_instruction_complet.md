success: True
usage: {'input_tokens': 28482, 'output_tokens': 47529, 'thinking_tokens': 42751, 'cache_read_tokens': 0, 'total_tokens': 76011}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction_decode algorithm triggers at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that the register tracking actions are performed at decode for each instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Register availability is maintained using Tomasulo-like tag tracking and digests decay after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes that Tomasulo-like tracking is used and each digest is invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At decode time, the decay counter of each valid register entry is decremented and cleared to invalid when reaching 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating each digest after 256 decoded instructions by counting down and clearing the valid state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When an instruction writes a destination register, its ROB index is stored as a tag and the valid bit is cleared.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "This quote directly confirms clearing valid and storing the ROB index tag upon decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The function on_instruction_decode is the primary trigger handler for the decode stage rather than an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The function definition on_instruction_decode defines the decode-time entry point specified in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register tracking table is a direct-mapped structure containing 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper defines a dedicated table with one entry per logical register, and Table 3 confirms 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry format comprises a 1-bit valid flag, a 14-bit payload holding a ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the bit widths of the valid bit, payload, and decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The 8-bit decay counter is initialized directly to 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "An 8-bit unsigned counter cannot represent the integer value 256 without overflow; the paper does not specify the exact counter initialization and expiry convention (such as initializing to 255 and expiring on underflow, or using an implicit 9th bit).",
      "enum_candidates": [
        "init_255",
        "wrap",
        "extend_9bit"
      ]
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register tracking table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying the 23-bit entry width (1 + 14 + 8) by 65 entries yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The tracking table is directly indexed by logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "A dedicated table with one entry per logical register for 65 registers is indexed directly by register ID."
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
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data shows exactly 65 entries corresponding to the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "The num_logical_registers parameter scales the usefulness table entry width and consumes 23 bits per register in the tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 verifies that each register tracking table entry consumes 1 + 14 + 8 = 23 bits."
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
      "open_question": "The paper fixes the architecture to 65 logical registers and does not define or evaluate a parameter range of [32, 128]; the legal range of num_logical_registers is not settled by the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default decay period is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly gives 256 subsequent instructions as the decay invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "The decay_instructions parameter sets decay_ctr width to ceil(log2(decay_instructions)) bits in the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "For 256 instructions, ceil(log2(256)) = 8 bits, matching the 8-bit counter width given in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The legal tuning range for decay_instructions is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not explore or specify a tuning range of [64, 1024] for decay_instructions, having settled on 256 from preliminary experiments; the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest XOR-folds trailing zero count, leading zero count shifted by 3, and value LSB6 shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify XOR-folding the 6-bit trailing count [5:0], leading count [8:3], and LSB6 [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Leading and trailing zero/one counts of 64 are masked modulo 64 into the 6-bit fields.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "A 64-bit integer register can have 64 identical leading or trailing bits, requiring 7 bits to represent; the paper does not specify whether counts saturate at 63 or wrap modulo 64.",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag registers generate a 12-bit digest by replicating the 4-bit flag pattern three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 states verbatim that condition-code flags replicate the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A bank selects the valid register with highest summed usefulness and queries its weight tables with (PC, digest).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 explicitly describes choosing the most useful available register within the bank to index the direction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "When bank register usefulness is non-positive, the sR bank multiplier scales the weight table sum by x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) includes an explicit x0 or x2.5 multiplier stage following each bank's weight table summation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When bank register usefulness is positive, the sR bank multiplier scales the weight table sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) defines the non-zero multiplier setting as x2.5 for useful bank contributions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A valid digest decays and is invalidated after 256 decodes without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "In-flight instructions completing execution before a branch misprediction resolves remain valid and visible to the predictor upon restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 confirms that instructions completing execution prior to branch resolution provide valid digests visible at pipeline restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction_complete algorithm triggers upon execution completion or writeback for the producing instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies that digest generation and payload writing take place when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Instruction completion makes register digests available for subsequent branch predictions prior to commit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Updating at instruction completion rather than commit makes digests immediately visible to subsequent predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When an instruction completes, if the pending ROB tag matches, the entry is updated with the computed digest and valid is set to 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies overwriting the payload with the produced digest and setting the valid bit upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The function on_instruction_complete is the primary trigger handler for instruction completion rather than an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The function definition on_instruction_complete defines the completion-time entry point specified in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The helper function generate_digest is called to compute register digests but is undefined in the specification.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values. RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 and Figure 6 define the digest generation algorithms for INT, FP, and Flag registers that must be included to implement generate_digest."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "function generate_digest(result_val: uint64, reg_type: RegType) -> uint12:\n    if reg_type == RegType.INT:\n        trailing = count_trailing_zeros(result_val) & 0x3F\n        leading = count_leading_zeros(result_val) & 0x3F\n        lsb6 = result_val & 0x3F\n        return uint12((trailing) ^ (leading << 3) ^ (lsb6 << 6))\n    elif reg_type == RegType.FLAG:\n        flags = result_val & 0xF\n        return uint12(flags | (flags << 4) | (flags << 8))\n    elif reg_type == RegType.FP:\n        return uint12(((result_val >> 55) & 0x1FF) << 3)\n    return 0\n\nfunction on_instruction_complete(rob_index: uint14, dest_reg: uint8, result_val: uint64, reg_type: RegType):\n    // Overwrite payload if ROB tag matches\n    if register_tracking_table[dest_reg].valid == 0 and register_tracking_table[dest_reg].payload == rob_index:\n        digest = generate_digest(result_val, reg_type)\n        register_tracking_table[dest_reg].payload = digest\n        register_tracking_table[dest_reg].valid = 1\n        register_tracking_table[dest_reg].decay_ctr = 256"
      },
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_decode+algo:instruction_complete` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=d139be0f-a43b-4686-8bfe-6c4068f0d920 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction_decode algorithm triggers at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that the register tracking actions are performed at decode for each instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Register availability is maintained using Tomasulo-like tag tracking and digests decay after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes that Tomasulo-like tracking is used and each digest is invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At decode time, the decay counter of each valid register entry is decremented and cleared to invalid when reaching 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating each digest after 256 decoded instructions by counting down and clearing the valid state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseud
... [truncated]

[Usage]
{"input_tokens": 28482, "output_tokens": 47529, "thinking_tokens": 42751, "cache_read_tokens": 0, "total_tokens": 76011}

[Result]
status=SUCCESS conversation=d139be0f-a43b-4686-8bfe-6c4068f0d920 turns=1 duration=250.715312137s usage={"input_tokens": 28482, "output_tokens": 47529, "thinking_tokens": 42751, "cache_read_tokens": 0, "total_tokens": 76011}


