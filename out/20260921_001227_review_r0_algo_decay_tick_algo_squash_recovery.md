success: True
usage: {'input_tokens': 28717, 'output_tokens': 32392, 'thinking_tokens': 28808, 'cache_read_tokens': 0, 'total_tokens': 61109}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "The decay_tick procedure is triggered once per decoded instruction and invalidates register tracking entries whose decay counter reaches 255 (after 256 decoded instructions).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This passage directly establishes that register digests are invalidated after 256 instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The decay loop iterates across all 65 logical register tracking table entries from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies that the tracking table consists of 65 entries corresponding to logical registers R0 through R64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The reg_tracking_table contains 65 entries, each comprising a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry structure and 65-entry count, yielding 65 * (1 + 14 + 8) = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The payload field holds an in-flight ROB index tag while valid is 0 and holds the produced register digest when valid is 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This explains the dual role of the payload field based on the state of the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default limit before invalidating a stale register digest is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This establishes 256 as the decay instruction limit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The tuning range for decay_instruction_limit is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed decay threshold of 256 instructions and does not define a tuning range for decay_instruction_limit.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default number of logical registers tracked by the predictor is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly records 65 logical register tracking entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The legal tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed count of 65 logical registers matching the evaluation architecture and does not define a tuning range for num_logical_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default entry count for WT0 in each register component bank is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 512 entries for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The legal tuning range for wt0_entries is [128, 2048] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 512 entries for WT0 and does not define an exploration range for wt0_entries.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default entry count for WT1 in each register component bank is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 256 entries for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The legal tuning range for wt1_entries is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 256 entries for WT1 and does not define an exploration range for wt1_entries.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default entry count for WT2 in each register component bank is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 128 entries for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The legal tuning range for wt2_entries is [32, 512] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 128 entries for WT2 and does not define an exploration range for wt2_entries.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default entry count per subtable in the register usefulness table (UT) is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) specifies 8 entries each for UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The legal tuning range for ut_entries_per_subtable is [4, 64] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 8 entries per subtable and does not define an exploration range for ut_entries_per_subtable.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest XOR-folds the trailing count, leading count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "This text confirms the three constituent fields used in integer digest generation depicted in Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For FP64 registers, bits [63:55] of the register value are extracted to form digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies extracting Value[63:55] aligned to digest bits [11:3] for 64-bit floating point registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition-code flags, the 4-bit condition code is replicated three times to create a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "This text confirms three-fold replication of the 4-bit flag nibble."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A tracking entry is invalidated after 256 instructions are decoded without intervening writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This establishes that exactly 256 subsequent decoded instructions trigger invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register bank selects the register with the largest usefulness and scales its WT sum by 2.5 if positive, or gates to 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies selecting the most useful register in the bank and scaling the WT sum by x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Digests of instructions that completed execution prior to a branch misprediction remain valid across the pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "This confirms that values from instructions completing before branch resolution remain retained and visible to post-flush predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6",
      "claim": "The register tracking table recovers from pipeline flushes by selectively clearing entries whose in-flight ROB indices are marked in the flushed ROB mask.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should invalid tracking entries awaiting values from squashed instructions be updated or recovered upon a branch misprediction redirect?",
      "enum_candidates": [
        "clear_flushed",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The bitmask test method test(...) in squash_recovery is undefined and requires concrete bit-testing logic.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/6/pseudocode",
        "value": "function squash_recovery(flushed_rob_mask: bitmask):\n    for r in 0 .. 64:\n        if reg_tracking_table[r].valid == 0:\n            rob_idx = reg_tracking_table[r].payload\n            // Check whether rob_idx is marked in flushed_rob_mask\n            if ((flushed_rob_mask >> rob_idx) & 1) != 0:\n                // Speculative producer instruction was squashed; invalidate tracking entry\n                reg_tracking_table[r].valid = 0\n                reg_tracking_table[r].payload = 0\n                reg_tracking_table[r].decay_ctr = 0"
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decay_tick+algo:squash_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=615c1f2d-03cb-4725-970c-4f38607a9483 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "The decay_tick procedure is triggered once per decoded instruction and invalidates register tracking entries whose decay counter reaches 255 (after 256 decoded instructions).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This passage directly establishes that register digests are invalidated after 256 instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The decay loop iterates across all 65 logical register tracking table entries from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies that the tracking table consists of 65 entries corresponding to logical registers R0 through R64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The reg_tracking_table contains 65 entries, each comprising a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry structure and 65-entry count, yielding 65 * (1 + 14 + 8) = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The payload field holds an in-flight ROB index tag while valid is 0 and holds the produced register digest when valid is 1.",
      "verdict": "SUPPORTED",
   
... [truncated]

[Usage]
{"input_tokens": 28717, "output_tokens": 32392, "thinking_tokens": 28808, "cache_read_tokens": 0, "total_tokens": 61109}

[Result]
status=SUCCESS conversation=615c1f2d-03cb-4725-970c-4f38607a9483 turns=1 duration=158.744158946s usage={"input_tokens": 28717, "output_tokens": 32392, "thinking_tokens": 28808, "cache_read_tokens": 0, "total_tokens": 61109}


