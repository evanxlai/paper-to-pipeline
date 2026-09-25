success: True
usage: {'input_tokens': 28446, 'output_tokens': 25571, 'thinking_tokens': 21944, 'cache_read_tokens': 0, 'total_tokens': 54017}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "dispatch_rename is triggered at the decode/rename stage when an instruction writing a destination logical register enters the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that the tracking table update occurs at decode for an instruction that writes a register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, dispatch_rename clears the valid bit and records the 14-bit ROB index in the entry payload for destination registers < 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that the instruction stores its ROB index as a tag and clears the valid bit in the dedicated entry for that logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Clearing the valid bit prevents in-flight uncommitted values from being read as digests while the ROB tag enables matching upon completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The Tomasulo-like tag matching protocol ensures in-flight registers remain invalid until the producer completes and matches tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "writeback_complete is triggered at execution completion when an instruction produces a result value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper identifies instruction completion as the trigger for overwriting payload with the generated digest and setting valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The expression uint14(digest) represents a primitive host integer type conversion to the 14-bit payload width rather than an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines payload as a 14-bit field, confirming uint14 is the primitive 14-bit unsigned integer type matching the signature and hardware width rather than an undefined algorithmic helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon execution completion, if the ROB tag matches the pending entry, the payload is updated with the generated digest, valid is set to 1, and decay_ctr is reset.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies overwriting the tracking payload with the produced digest and marking the entry valid upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Once execution completes, the digest becomes immediately available to front-end branch lookups prior to instruction retirement.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper confirms that any entry with valid set immediately forwards its digest to the SC during prediction lookups."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "reg_tracking_table is a direct-mapped table with 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies one entry per logical register, matching the 65 total registers tracked across the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry contains a 1-bit valid flag, a 14-bit payload (holding either a 14-bit ROB tag or a 12-bit digest), and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly describes the 1-bit valid and 14-bit payload fields, with Table 3 confirming the 8-bit decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register tracking table requires 1495 bits of total storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry (1 + 14 + 8) equals exactly 1495 bits as specified in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register tracking table is directly indexed by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "A dedicated table with one entry per logical register is indexed directly by the logical register identifier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default invalidation threshold for decay_instruction_limit is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the digest invalidation limit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "decay_instruction_limit has a legal tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only evaluates a fixed invalidation limit of 256 instructions and does not define a tuning range for decay_instruction_limit.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "decay_instruction_limit requires num_logical_registers * ceil(log2(decay_instruction_limit)) bits of storage in the tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates an 8-bit counter (ceil(log2(256)) = 8) for each of the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly establishes a fixed count of 65 logical registers across all register tracking and usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "num_logical_registers has a configurable range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes 65 logical registers (R0 through R64) based on the ISA and does not define a configurable range for num_logical_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/storage_impact",
      "claim": "num_logical_registers scales the usefulness weight table width and the tracking table entry count.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 demonstrates that both the UT storage and the auxiliary tracking table scale directly by the number of logical registers (65)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding trailing zero/one count [5:0], leading zero/one count [8:3], and Value[5:0] at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest XORs trailing count at [5:0], leading count at [8:3], and LSBs at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For 64-bit floating point registers, the digest extracts Value[63:55] shifted to bits [11:3] with bits [2:0] zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) confirm extracting the sign bit and high-order exponent bits (bits [63:55] for FP64) aligned at digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition-code flags, the 4-bit nibble is replicated three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly defines replicating the four condition code flag bits three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest is invalidated when 256 instructions have been decoded without new writes to the register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Each bank selects the register with largest usefulness and scales its weight contribution by 2.5 if usefulness > 0 or gates it to 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) define selecting the most useful register digest per bank and applying the 'x0 or x2.5' scaling based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Valid register digests in the tracking table are preserved across branch misprediction squashes so post-flush predictions can use completed values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 states that completed values enlarged by finished in-flight execution are retained across pipeline flushes and visible when the predictor restarts."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:dispatch_rename+algo:writeback_complete` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; t...

[Init]
model=gemini-3.8-flash-medium conversation=057448f7-5ef5-43da-ada3-373fda5b63b3 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "dispatch_rename is triggered at the decode/rename stage when an instruction writing a destination logical register enters the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that the tracking table update occurs at decode for an instruction that writes a register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, dispatch_rename clears the valid bit and records the 14-bit ROB index in the entry payload for destination registers < 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that the instruction stores its ROB index as a tag and clears the valid bit in the dedicated entry for that logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Clearing the valid bit prevents in-flight uncommitted values from being read as digests while the ROB tag enables matching upon completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The Tomasulo-like tag matching protocol ensures in-flight registers remain invalid until the producer completes and matches tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "
... [truncated]

[Usage]
{"input_tokens": 28446, "output_tokens": 25571, "thinking_tokens": 21944, "cache_read_tokens": 0, "total_tokens": 54017}

[Result]
status=SUCCESS conversation=057448f7-5ef5-43da-ada3-373fda5b63b3 turns=1 duration=131.478873908s usage={"input_tokens": 28446, "output_tokens": 25571, "thinking_tokens": 21944, "cache_read_tokens": 0, "total_tokens": 54017}


