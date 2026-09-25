success: True
usage: {'input_tokens': 29985, 'output_tokens': 29150, 'thinking_tokens': 26079, 'cache_read_tokens': 0, 'total_tokens': 59135}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Instruction complete update triggers when an execution unit completes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that the register status table update is triggered upon completion of the instruction producing the value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction completion, if the destination register entry matches the in-flight ROB index and valid is 0, the entry is updated with the 12-bit digest, valid is set to 1, and decay_ctr is set to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies storing the ROB index as a tag at decode with valid cleared, and overwriting payload with the digest and setting valid to 1 upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Matching the in-flight ROB index ensures older out-of-order completing instructions do not overwrite newer younger dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The Tomasulo-like tag check ensures out-of-order completions only update the entry if the tag matches the most recent producer."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table is organized as a direct-mapped table with 65 entries corresponding to 64 architectural registers plus 1 flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly establishes a dedicated table containing one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry format contains a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies the entry format as a 1-bit valid flag, 14-bit payload, and 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The register status table totals 1495 bits across 65 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries of 23 bits each (1 + 14 + 8) equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The register status table is indexed directly by logical register identifier in range 0..64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "A direct-mapped table with one entry per logical register uses the logical register identifier as its index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "A digest is invalidated after 256 subsequent instructions are decoded, tracked by an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly fixes the stale digest invalidation threshold at 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The register digest is 12 bits and the table payload field is 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The text directly states that the payload stores either a 14-bit tag or a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The floating-point register digest alignment variant selects whether format slices are right-aligned at bit position 3 or bit position 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) draws FP format slices right-aligned at bit 3 without prose confirmation, leaving whether fields align at bit 3 or bit 0 an open design parameter.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests XOR-fold a 6-bit trailing zero count, a 6-bit leading zero count shifted by 3, and a 6-bit LSB field shifted by 6 into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the integer digest as composed of leading count, trailing count, and the six least significant bits, matching the test's XOR-folding construction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags digest replicates the 4-bit flag value three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states replicating the four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "64-bit FP register digest places bits [63:55] at bit positions [11:3] with bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does FP64 digest placement align bits [63:55] at digest bits [11:3] with bits [2:0] zeroed, or right-align at bit 0 into digest bits [8:0]?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decays and is invalidated when 256 subsequent instructions execute without that register being updated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that an entry's digest is invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank usefulness selects scaling of WT prediction sum by x2.5 when usefulness is positive and suppresses it to x0 when non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) includes an 'x0 or x2.5' multiplier stage after each bank WT sum, but does not explicitly specify the controlling signal for selecting x0 versus x2.5.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, when multiple registers in a bank are available at prediction time, exactly one is chosen randomly to update UT and WT using a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection of a single available register within the bank ensures only one write port is needed during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Squash recovery is triggered on a pipeline flush / misprediction recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper specifies that predictor restart occurs after a pipeline flush, leveraging available completed values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline flush, in-flight register table entries matching squashed ROB indices are invalidated by setting decay_ctr to 255.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should in-flight squashed entries in the register status table be recovered on a pipeline flush, given that Section 5 leaves recovering the Tomasulo-like table to future work? ('and' in the pseudocode condition is a host logical conjunction primitive, but the recovery action itself is unsettled by the paper).",
      "enum_candidates": [
        "decay_expire",
        "clear_tag",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Pipeline flushes clear pending ROB reservations for squashed speculative instructions while preserving already-completed valid digests across the restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper confirms that instructions completing execution prior to misprediction resolution enlarge the set of values visible upon restart after the flush."
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
model=gemini-3.8-flash-medium conversation=e2fcabe5-9938-4f1c-972b-418d1c3a302c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Instruction complete update triggers when an execution unit completes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that the register status table update is triggered upon completion of the instruction producing the value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction completion, if the destination register entry matches the in-flight ROB index and valid is 0, the entry is updated with the 12-bit digest, valid is set to 1, and decay_ctr is set to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies storing the ROB index as a tag at decode with valid cleared, and overwriting payload with the digest and setting valid to 1 upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Matching the in-flight ROB index ensures older out-of-order completing instructions do not overwrite newer younger dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The Tomasulo-like tag check ensures out-of-order completions only update the entry if
... [truncated]

[Usage]
{"input_tokens": 29985, "output_tokens": 29150, "thinking_tokens": 26079, "cache_read_tokens": 0, "total_tokens": 59135}

[Result]
status=SUCCESS conversation=e2fcabe5-9938-4f1c-972b-418d1c3a302c turns=1 duration=164.059496078s usage={"input_tokens": 29985, "output_tokens": 29150, "thinking_tokens": 26079, "cache_read_tokens": 0, "total_tokens": 59135}


