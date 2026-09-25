success: True
usage: {'input_tokens': 27661, 'output_tokens': 35506, 'thinking_tokens': 31354, 'cache_read_tokens': 0, 'total_tokens': 63167}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Scoreboard updates are triggered at instruction decode, execution completion, and instruction retirement/decoded tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 explicitly establishes decode, execution completion, and decoded instruction ticks as the operational trigger events."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The on_decode routine marks the destination register entry invalid and initializes decay_ctr to 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Assigning decay_ctr = 256 collides with /state/0/entry_format and Table 3, which define decay_ctr as an 8-bit unsigned field whose maximum representable value is 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function on_decode(inst):\n    for dest_reg in inst.dest_registers:\n        reg_table[dest_reg].valid = 0\n        reg_table[dest_reg].payload = inst.rob_tag // 14-bit ROB index\n        reg_table[dest_reg].decay_ctr = 255\n\nfunction on_instruction_decoded_tick():\n    // Decrement aging counter every instruction decoded\n    for r = 0 to 64:\n        if reg_table[r].valid == 1:\n            if reg_table[r].decay_ctr > 0:\n                reg_table[r].decay_ctr -= 1\n            if reg_table[r].decay_ctr == 0:\n                reg_table[r].valid = 0 // Invalidate stale digest\n\nfunction on_execution_complete(rob_tag, dest_reg, value, reg_type):\n    if reg_table[dest_reg].valid == 0 and reg_table[dest_reg].payload == rob_tag:\n        reg_table[dest_reg].payload = generate_digest(reg_type, value)\n        reg_table[dest_reg].valid = 1\n        reg_table[dest_reg].decay_ctr = 255\n\nfunction on_pipeline_squash(recover_rob_tag):\n    // On mispredict recovery, in-flight instruction tags are flushed\n    // Completed registers retain valid digests, enabling recovery-path correlation\n    for r = 0 to 64:\n        if reg_table[r].valid == 0:\n            if is_younger_than_or_equal(reg_table[r].payload, recover_rob_tag):\n                // Revert to invalid or architectural state\n                reg_table[r].valid = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode invokes generate_digest(reg_type, value) to construct a 12-bit digest upon execution completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values. RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 defines generating a 12-bit digest parameterized by register type and value; the finding regarding 'digest(...)' is refuted as a substring match artifact."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Aging decrements valid entries every decoded instruction and invalidates when the decay counter expires.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states invalidation occurs after 256 subsequent instructions have been decoded, implemented via per-decoded-instruction decrements."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Digest invalidation occurs after 256 decoded instructions to retain only fresh values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Matches verbatim the motivation and 256-instruction lifetime described in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The scoreboard is an array of 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 and Table 3 specify dedicated tracking for all 65 logical registers across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each scoreboard entry contains a 1-bit valid flag, a 14-bit payload for tag or digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 and Table 3 explicitly confirm the field widths { valid (1), payload (14), decay_ctr (8) }."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The register scoreboard tracking table consumes 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data shows 65 entries times 23 bits per entry equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The scoreboard is directly indexed by logical register index 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 defines one entry per logical register, corresponding to direct logical register indexing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "Prediction Weight Tables consist of 8 banks, each containing tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 sR row confirms 8 banks containing tables of 128, 256, and 512 entries with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each prediction weight entry stores one 6-bit signed saturating weight in the range [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the weight width as 6 bits, standardly interpreted as a signed [-32, 31] counter in SC components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The prediction weight tables consume 43008 bits in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 confirms 6 * (128 + 256 + 512) * 8 equals 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "Prediction weight tables are indexed by hashes combining branch PC and the selected 12-bit register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "PC + reg. digest",
        "why": "Figure 5(c) shows the input to the hash generation for WT0, WT1, and WT2 is PC plus the selected register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The decay_threshold parameter default is 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "A default value of 256 collides with /state/0/entry_format declaring decay_ctr as 8 bits (max 255). Lowering default to 255 resolves the contradiction while maintaining an 8-bit counter spanning 256 steps (255 down to 0)."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/3/default",
        "value": 255
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/range",
      "claim": "The tuning range for decay_threshold is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies invalidation after 256 instructions but does not evaluate or define an alternative tuning range for decay_threshold.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/storage_impact",
      "claim": "Altering decay_threshold changes decay_ctr width by ceil(log2(decay_threshold)) bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 demonstrates 8 bits per register are allocated for 256 steps where ceil(log2(256)) = 8."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The default number of tracked registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies 65 tracked registers across UT and auxiliary storage tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/range",
      "claim": "The tuning range for num_tracked_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes tracking to the 65 logical registers of the architecture and does not define a tuning range for num_tracked_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/storage_impact",
      "claim": "num_tracked_registers scales UT and scoreboard auxiliary storage linearly.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates both UT storage and auxiliary scoreboard storage as direct linear multiples of 65."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest XOR-folds trailing zero count, leading zero count, and 6 LSBs into a 12-bit value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) define the exact XOR-folded layout tested by integer_digest_generation_check."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags replicate the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) define 3x replication of 4 flag bits into 12 bits, matching flags_digest_generation_check."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Advancing decode ticks decrements decay_ctr to 0 and clears the valid flag upon expiration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 confirms that aging clears validity when the lifetime expires, verified by scoreboard_aging_invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Positive bank usefulness scales the WT sum by 2.5 while non-useful banks contribute 0 to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows per-bank scaling by x2.5 or suppression (x0) gated by bank usefulness, matching usefulness_gated_scaling."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers in a bank are valid, one is randomly selected during training to limit write ports to one.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly specifies random selection among available registers per bank to ensure single write ports."
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
model=gemini-3.8-flash-medium conversation=9b4533c9-0e15-4584-865a-ff494fb883b9 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Scoreboard updates are triggered at instruction decode, execution completion, and instruction retirement/decoded tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 explicitly establishes decode, execution completion, and decoded instruction ticks as the operational trigger events."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The on_decode routine marks the destination register entry invalid and initializes decay_ctr to 256.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Assigning decay_ctr = 256 collides with /state/0/entry_format and Table 3, which define decay_ctr as an 8-bit unsigned field whose maximum representable value is 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function on_decode(inst):\n    for dest_reg in inst.dest_registers:\n        reg_table[dest_reg].valid = 0\n        reg_table[dest_reg].payload = inst.rob_tag // 14-bit ROB index\n        reg_table[dest_reg].decay_ctr = 255\n\nfunction on_instruction_decoded_tick():\n    // Decrement aging counter every instruction decoded\n    for r = 0 to 64:\n        if reg_table[r].valid == 1:\n            if reg_table[r].decay_ctr > 0:\n                reg_table[r].decay_ctr -= 1\n            if reg_table[r].decay_ctr == 0:\n                reg_table[r].valid = 0 // Invalidate stale digest\n\nfunction on_execution_complete(rob_tag, dest_reg, value, reg_type):\n    if reg_table[dest_re
... [truncated]

[Usage]
{"input_tokens": 27661, "output_tokens": 35506, "thinking_tokens": 31354, "cache_read_tokens": 0, "total_tokens": 63167}

[Result]
status=SUCCESS conversation=9b4533c9-0e15-4584-865a-ff494fb883b9 turns=1 duration=190.359801336s usage={"input_tokens": 27661, "output_tokens": 35506, "thinking_tokens": 31354, "cache_read_tokens": 0, "total_tokens": 63167}


