success: True
usage: {'input_tokens': 4049, 'output_tokens': 45016, 'thinking_tokens': 40993, 'cache_read_tokens': 23451, 'total_tokens': 49065}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The scoreboard update and aging algorithm is triggered at decode, execution completion, and instruction decode tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly names decode and instruction completion as the events that update register entries, while invalidation occurs as subsequent instructions decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At instruction decode, an instruction writing a destination register clears the valid bit and stores its ROB index as a 14-bit tag in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "This directly matches the on_decode pseudocode setting valid to 0 and storing the ROB tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On each instruction decoded, the decay counter of each valid register entry decrements and the entry is invalidated when the counter reaches zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The countdown of an 8-bit counter from 255 to 0 on each decoded instruction implements invalidation after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "When an instruction completes execution matching the in-flight ROB tag, the payload is overwritten with the produced register value digest, valid is set to 1, and the decay counter is initialized.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This confirms the state transition in on_execution_complete setting payload to the digest and valid to 1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On misprediction pipeline recovery, in-flight register tags younger than the recovery ROB tag are flushed while completed registers retain valid digests.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The authors state that recovering the Tomasulo-like table on mispredictions is left to future work, leaving the exact squash recovery logic unstated."
      },
      "patch": null,
      "open_question": "How should squashed in-flight registers (with valid=0) in the Tomasulo-like table be recovered upon a branch misprediction squash?",
      "enum_candidates": [
        "keep_invalid",
        "restore_checkpoint"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The helper function generate_digest(reg_type, value) computes a 12-bit register value digest based on register type as required by on_execution_complete.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values. RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper specifies how digests are generated across register types in Figure 6, but the spec called generate_digest without defining it in any algorithm."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function generate_digest(reg_type, value):\n    if reg_type == REG_INT:\n        trailing = count_trailing_zeros(value) & 0x3F\n        leading = count_leading_zeros(value) & 0x3F\n        lsb6 = value & 0x3F\n        return trailing ^ (leading << 3) ^ (lsb6 << 6)\n    elif reg_type == REG_FLAGS:\n        f = value & 0xF\n        return (f << 8) | (f << 4) | f\n    elif reg_type == REG_FP:\n        return ((value >> 55) & 0x1FF) << 3\n    return 0\n\nfunction on_decode(inst):\n    for dest_reg in inst.dest_registers:\n        reg_table[dest_reg].valid = 0\n        reg_table[dest_reg].payload = inst.rob_tag // 14-bit ROB index\n        reg_table[dest_reg].decay_ctr = 255\n\nfunction on_instruction_decoded_tick():\n    // Decrement aging counter every instruction decoded\n    for r = 0 to 64:\n        if reg_table[r].valid == 1:\n            if reg_table[r].decay_ctr > 0:\n                reg_table[r].decay_ctr -= 1\n            if reg_table[r].decay_ctr == 0:\n                reg_table[r].valid = 0 // Invalidate stale digest\n\nfunction on_execution_complete(rob_tag, dest_reg, value, reg_type):\n    if reg_table[dest_reg].valid == 0 and reg_table[dest_reg].payload == rob_tag:\n        reg_table[dest_reg].payload = generate_digest(reg_type, value)\n        reg_table[dest_reg].valid = 1\n        reg_table[dest_reg].decay_ctr = 255\n\nfunction on_pipeline_squash(recover_rob_tag):\n    // On mispredict recovery, in-flight instruction tags are flushed\n    // Completed registers retain valid digests, enabling recovery-path correlation\n    for r = 0 to 64:\n        if reg_table[r].valid == 0:\n            if is_younger_than_or_equal(reg_table[r].payload, recover_rob_tag):\n                // Revert to invalid or architectural state\n                reg_table[r].valid = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Invalidation after 256 decoded instructions ensures only fresh, correlated values influence branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote matches the notes rationale verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table is a Tomasulo-like scoreboard containing 65 entries corresponding to logical registers R0 to R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register.",
        "why": "This confirms the Tomasulo-like design tracking one entry per logical register, corresponding to the 65 tracked registers in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of the Register Tracking Table contains a 1-bit valid flag, a 14-bit payload (holding either a 14-bit in-flight ROB tag or a 12-bit digest), and an 8-bit decay counter, totalling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies this entry structure across 65 registers, giving exactly (1 + 14 + 8) * 65 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The Prediction Weight Tables (WT) consist of 8 banks, each containing tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries), each entry storing one 6-bit signed saturating weight, totalling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies the WT dimensions, yielding 6 * (128 + 256 + 512) * 8 = 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT tables are indexed by hashes of branch PC and the selected 12-bit register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled 'PC + reg. digest', hashed into 'h0', 'h1', 'h2'.",
        "why": "Figure 5(c) demonstrates that hashes of PC and the selected register digest form the indices into the WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default decay threshold is 255 decoded instructions, stored in an 8-bit counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "An 8-bit counter decremented on each instruction decoded counts 256 steps from 255 to 0 before invalidating."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The tuning search range for decay_threshold is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The tuning range [64, 1024] is not stated in the paper, which evaluates only the fixed 256-instruction decay threshold; the legal range should be confirmed during tuning.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default number of tracked registers is 65, organized across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 and Section 4.2 confirm that the architecture tracks 65 logical registers across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The tuning search range for num_tracked_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The tuning range [32, 128] is not stated in the paper, which evaluates a fixed count of 65 logical registers; the legal range should be confirmed during tuning.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest generation XOR-folds trailing zero count at [5:0], leading zero count at [8:3], and LSB6 at [11:6], producing 0x3E3 for input value 0x8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and Section 4.2 define this three-way XOR fold of 6-bit fields, yielding 0x03 ^ (0x3C << 3) ^ (0x08 << 6) = 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Flags register digest generation replicates the 4 condition flag bits three times across the 12-bit digest, producing 0x999 for input value 0x9.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 0x9 across three 4-bit nibbles yields (0x9 << 8) | (0x9 << 4) | 0x9 = 0x999."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Advancing decode ticks by 2 instructions decrements a decay counter initialized at 2 to 0, causing the entry's valid bit to transition to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Decrementation of decay_ctr on each decode tick until hitting 0 triggers invalidation as described in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank with positive usefulness scales its prediction weight table sum by 2.5, whereas a bank with no valid registers contributes 0 to sR_sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) shows each bank's WT sum passing through a 'x0 or x2.5' scaling stage before summation into sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple available registers in a bank are valid at prediction time, training randomly selects exactly one for table updates, requiring a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "This quote matches the test assertion verbatim."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:Register Scoreboard Update and Aging` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they...

[Init]
model=gemini-3.8-flash-medium conversation=ab773b1c-85fc-4d0d-902f-a179d1536f4a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The scoreboard update and aging algorithm is triggered at decode, execution completion, and instruction decode tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly names decode and instruction completion as the events that update register entries, while invalidation occurs as subsequent instructions decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At instruction decode, an instruction writing a destination register clears the valid bit and stores its ROB index as a 14-bit tag in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "This directly matches the on_decode pseudocode setting valid to 0 and storing the ROB tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On each instruction decoded, the decay counter of each valid register entry decrements and the entry is invalidated when the counter reaches zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The countdown of an 8-bit counter from 255 to 0 on each decoded instruction implements invalidation after 256 de
... [truncated]

[Usage]
{"input_tokens": 4049, "output_tokens": 45016, "thinking_tokens": 40993, "cache_read_tokens": 23451, "total_tokens": 49065}

[Result]
status=SUCCESS conversation=ab773b1c-85fc-4d0d-902f-a179d1536f4a turns=1 duration=232.796457754s usage={"input_tokens": 4049, "output_tokens": 45016, "thinking_tokens": 40993, "cache_read_tokens": 23451, "total_tokens": 49065}


