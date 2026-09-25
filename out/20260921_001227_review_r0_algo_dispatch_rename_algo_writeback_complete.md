success: True
usage: {'input_tokens': 28449, 'output_tokens': 23385, 'thinking_tokens': 20074, 'cache_read_tokens': 0, 'total_tokens': 51834}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The dispatch_rename routine is triggered at the decode/rename stage when an instruction writing a destination logical register enters the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It confirms that tracking table updates occur at decode for instructions writing a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Upon dispatch/rename of an instruction writing a destination register, the tracking table entry valid bit is cleared and its payload is set to the 14-bit ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It establishes that dispatch clears the valid bit and stores the ROB index as a tag in the entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Clearing the valid bit prevents in-flight uncommitted register values from being read as digests during branch prediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "It shows that only entries with valid bit set forward digests, ensuring in-flight values are not read."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The reg_tracking_table is a direct-mapped table with 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly states that the tracking structure contains 65 entries for the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry in reg_tracking_table consists of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly defines each entry structure as a 1-bit valid flag, 14-bit payload, and 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total size of reg_tracking_table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 65 entries by 23 bits per entry (1 + 14 + 8) yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The reg_tracking_table is directly indexed by the logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having dedicated entries per logical register defines direct indexing by logical register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default limit for digest decay invalidation is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text explicitly specifies that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The tuning range for decay_instruction_limit is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed decay limit of 256 instructions and does not evaluate or define a legal tuning range such as [64, 1024].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "The decay counter accounts for num_logical_registers * ceil(log2(decay_instruction_limit)) bits in the tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "An 8-bit counter (ceil(log2(256)) = 8) across 65 registers accounts for 65 * 8 bits in the tracking table."
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
        "why": "Table 3 defines the register tracking and usefulness structures for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies an architecture with exactly 65 logical registers across 8 banks and does not define a tuning range such as [32, 128].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/storage_impact",
      "claim": "num_logical_registers scales the UT vector width and reg_tracking_table entry count.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The register count determines the per-bank vector width of the usefulness table entries as well as the tracking table size."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are generated by XOR-folding trailing zero count, leading zero count, and the six LSBs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "It specifies that the integer digest comprises leading zero/one count, trailing zero/one count, and the 6 least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "64-bit floating point digests extract Value[63:55] placed at digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "It confirms extracting the sign and leading exponent bits, matching Value[63:55] mapped to digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag register digests replicate the 4 condition-code bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "It states verbatim that four flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decays and transitions to invalid after 256 instructions are decoded without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "It confirms that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank selection picks the digest of the register with the largest usefulness in the bank, scaling the bank weight sum by 2.5 if positive or gating to 0 if not.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "It confirms selecting the most useful register in the bank to drive the prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed register digests remain valid in the tracking table across pipeline squash redirects caused by branch mispredictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "It confirms that values completed before/during the flush are retained and accessible to subsequent predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "writeback_complete triggers at execution completion when an instruction produces a result value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "It confirms that updating the tracking table entry with the result digest occurs upon instruction execution completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At completion, if the ROB tag matches the in-flight tag and the entry is invalid, the payload is updated with the 12-bit digest zero-extended to uint14, valid is set to 1, and decay_ctr is reset.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "It settles that completing instructions overwrite the payload with the produced value's digest and set the valid bit; uint14 is a host-supplied primitive width conversion matching the 14-bit payload width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "The digest becomes available immediately to front-end branch lookups upon execution completion, prior to instruction retirement.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Overwriting payload and setting valid upon completion rather than retirement enables immediate use of the digest by front-end predictions."
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
model=gemini-3.8-flash-medium conversation=9ca464b4-674e-4485-939e-b7f2db668034 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The dispatch_rename routine is triggered at the decode/rename stage when an instruction writing a destination logical register enters the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It confirms that tracking table updates occur at decode for instructions writing a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Upon dispatch/rename of an instruction writing a destination register, the tracking table entry valid bit is cleared and its payload is set to the 14-bit ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It establishes that dispatch clears the valid bit and stores the ROB index as a tag in the entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Clearing the valid bit prevents in-flight uncommitted register values from being read as digests during branch prediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "It shows that only entries with valid bit set forward digests, ensuring in-flight values are not read."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim
... [truncated]

[Usage]
{"input_tokens": 28449, "output_tokens": 23385, "thinking_tokens": 20074, "cache_read_tokens": 0, "total_tokens": 51834}

[Result]
status=SUCCESS conversation=9ca464b4-674e-4485-939e-b7f2db668034 turns=1 duration=122.264747193s usage={"input_tokens": 28449, "output_tokens": 23385, "thinking_tokens": 20074, "cache_read_tokens": 0, "total_tokens": 51834}


