success: True
usage: {'input_tokens': 28012, 'output_tokens': 24384, 'thinking_tokens': 21627, 'cache_read_tokens': 0, 'total_tokens': 52396}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_complete algorithm triggers upon instruction execution completion or writeback.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that updating the tracker entry with the produced value digest occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When an instruction completes, if its destination register is valid and its ROB tag matches the pending tag, the payload is updated with the 12-bit digest, valid is set to 1, and the decay counter is initialized.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that completed instructions overwrite the payload with the produced value digest and set the valid bit following tag matching."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "The digest is written and valid bit set only if the completing instruction matches the pending ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Tomasulo's algorithm enforces that only completing instructions whose tags match the pending register reservation update the register state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegTracker is organized as an array of 65 entries indexed by logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Auxiliary data: { valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data row explicitly defines 65 tracker entries corresponding to the logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each sR_RegTracker entry contains a 1-bit valid bit, a 14-bit payload holding an in-flight ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Directly defines the valid bit and 14-bit tag / 12-bit digest payload, while Table 3 confirms decay_ctr is 8 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "sR_RegTracker occupies 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Auxiliary data: { valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry (1 + 14 + 8) equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "sR_RegTracker is directly indexed by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Confirms that each logical register has a dedicated entry in the table, indexed by register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default decay interval is 255.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "/parameters/2/range specifies powers of two in [64, 1024], which contradicts the default value of 255; 256 is the power of two required to clear the parameter range constraint and match the paper's 256-instruction decay period."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/2/default",
        "value": 256
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The decay interval parameter defines the number of decoded instructions after which a digest is invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Establishes that digest invalidation is governed by a decay period of 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The decay_step algorithm triggers at instruction decode time and is evaluated per decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Because decay is counted in terms of decoded instructions, the decay step is evaluated on each decoded instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "For each decoded instruction, the decay counter of each valid register entry is decremented, and the valid bit is cleared when the counter reaches zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Specifies that digest validity expires after 256 decoded instructions, implemented via decrementing the per-entry decay counter to zero."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Digest invalidation prevents stale digests beyond 256 decoded instructions from biasing branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Verbatim justifies the 256-instruction decay by noting stale digests degrade prediction accuracy and must not influence future predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For condition-code flags, the 4-bit flag value is replicated three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Directly supports replicating the 4-bit flag value three times to generate the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding trailing zero/one count, leading zero/one count shifted by 3, and the 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Matches the three 6-bit fields and XOR-folding structure for integer register digests depicted in Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For FP32 registers, the 6-bit slice Value[31:26] is mapped to digest bits [8:3] with bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Confirms the FP32 format extraction of Value[31:26] positioned at digest bits [8:3] as shown in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decrements its decay counter on each decoded instruction and transitions to invalid after 256 instructions without a write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Directly validates the test case assertion that a digest expires and is marked invalid after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register with the highest summed usefulness across UT0-UT2 in a bank is selected and its digest is used to index WT0-WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms selecting the most useful register in the bank by summing usefulness weights to index the second table."
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
model=gemini-3.8-flash-medium conversation=c4733f5b-376b-4934-9602-fee24d85b743 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_complete algorithm triggers upon instruction execution completion or writeback.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that updating the tracker entry with the produced value digest occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When an instruction completes, if its destination register is valid and its ROB tag matches the pending tag, the payload is updated with the 12-bit digest, valid is set to 1, and the decay counter is initialized.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that completed instructions overwrite the payload with the produced value digest and set the valid bit following tag matching."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "The digest is written and valid bit set only if the completing instruction matches the pending ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Tomasulo's algorithm enforces that only completing instructions whose tags match the pending register reservation update the register state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "c
... [truncated]

[Usage]
{"input_tokens": 28012, "output_tokens": 24384, "thinking_tokens": 21627, "cache_read_tokens": 0, "total_tokens": 52396}

[Result]
status=SUCCESS conversation=c4733f5b-376b-4934-9602-fee24d85b743 turns=1 duration=133.146328598s usage={"input_tokens": 28012, "output_tokens": 24384, "thinking_tokens": 21627, "cache_read_tokens": 0, "total_tokens": 52396}


