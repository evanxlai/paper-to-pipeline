success: True
usage: {'input_tokens': 29987, 'output_tokens': 25088, 'thinking_tokens': 22011, 'cache_read_tokens': 0, 'total_tokens': 55075}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The update algorithm triggers when an execution unit finishes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that the update is triggered upon instruction execution completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, if the pending entry matches the completing instruction's ROB index, payload is updated with the 12-bit digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that completing instructions match ROB index tags in the table and replace them with the produced digest while asserting the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "ROB index tag matching ensures older out-of-order completing instructions do not overwrite newer speculative dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Confirms the Tomasulo-like tag matching design to prevent out-of-order write-after-write hazards from overwriting younger dependencies."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table contains 65 entries corresponding to 64 architectural INT/FP registers plus 1 condition-code flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Explicitly accounts for 65 entries in the register status table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry format comprises a 1-bit valid flag, a 14-bit payload holding either an in-flight ROB index or a 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Verbatim defines the valid bit and 14-bit tag/12-bit digest payload width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The register status table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The entry size (1 + 14 + 8 = 23 bits) multiplied by 65 entries equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The table is directly indexed by logical register identifier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Confirms a direct one-to-one mapping between logical register IDs and table entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default decay invalidation threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Directly specifies 256 decoded instructions as the digest invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The tuning range for DECAY_THRESHOLD_INSTS is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The tuning range [64, 1024] pow2 is not specified in the paper, which evaluates only the fixed 256-instruction decay threshold.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Directly confirms that the register value digest width is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The parameter range for DIGEST_BITS is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The tuning range [8, 16] is not described in the paper, which evaluates only a 12-bit digest format.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The floating-point digest bit field right-aligns at bit 3 rather than bit 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Whether floating-point register digest slices are right-aligned at digest bit 3 or bit 0 is not stated in the paper text and is declared uncertain in U4.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest XOR-folds 6-bit trailing zero/one count at [5:0], 6-bit leading zero/one count at [8:3], and 6-bit Value[5:0] at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Establishes that the integer digest is formed from leading zero/one count, trailing zero/one count, and the six least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag digest replicates the 4 flag bits three times to produce a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verbatim states the three-fold replication of 4 condition-code flag bits into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 register digest extracts sign and exponent bits [63:55] and places them at bit positions [11:3] with bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Right-aligning the extracted FP bits at bit position 3 (leaving bits [2:0] zero) is read off the diagram and declared uncertain in U4; aligning at bit 0 is an open alternative.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Executing 256 instructions without an update invalidates the register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Confirms that digests expire and are invalidated after 256 decoded instructions without an update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank contribution to sR is scaled by x2.5 if that bank's usefulness is positive and suppressed (scaled by x0) if non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the control wire selecting between x0 and x2.5, leaving it uncertain whether scaling is controlled per-bank by usefulness or represents a static scale as noted in U2.",
      "enum_candidates": [
        "per_bank_usefulness",
        "global_scale_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Training randomly chooses exactly one available register within a bank to update its UT and WT entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Verbatim confirms uniform random selection among available registers within a bank during training to preserve single-write-port operation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Pipeline squash recovery invalidates pending speculative ROB entries by setting decay_ctr to 255.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How squashed in-flight instructions (valid=0 with squashed ROB index tags) are recovered in the Tomasulo-like table on pipeline flush is not specified in the paper and is explicitly cited in Section 5 as an open challenge left for future work.",
      "enum_candidates": [
        "clear_tag",
        "restore_checkpoint",
        "ignore"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Pipeline flush preserves already-completed valid digests so the predictor can exploit completed values immediately upon restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Directly confirms that completed register values available when a misprediction resolves are retained and exploited upon pipeline restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_complete_update+algo:squash_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec...

[Init]
model=gemini-3.8-flash-medium conversation=83c3e7d7-0117-4b13-8e62-6027e041d24f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The update algorithm triggers when an execution unit finishes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that the update is triggered upon instruction execution completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, if the pending entry matches the completing instruction's ROB index, payload is updated with the 12-bit digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that completing instructions match ROB index tags in the table and replace them with the produced digest while asserting the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "ROB index tag matching ensures older out-of-order completing instructions do not overwrite newer speculative dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Confirms the Tomasulo-like tag matching design to prevent out-of-order write-after-write hazards from overwriting younger dependencies."
      },
      "patch": null,
      "
... [truncated]

[Usage]
{"input_tokens": 29987, "output_tokens": 25088, "thinking_tokens": 22011, "cache_read_tokens": 0, "total_tokens": 55075}

[Result]
status=SUCCESS conversation=83c3e7d7-0117-4b13-8e62-6027e041d24f turns=1 duration=140.702072765s usage={"input_tokens": 29987, "output_tokens": 25088, "thinking_tokens": 22011, "cache_read_tokens": 0, "total_tokens": 55075}


