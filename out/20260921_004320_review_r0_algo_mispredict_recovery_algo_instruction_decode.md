success: True
usage: {'input_tokens': 28417, 'output_tokens': 30397, 'thinking_tokens': 26941, 'cache_read_tokens': 0, 'total_tokens': 58814}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/6/trigger",
      "claim": "The mispredict recovery algorithm triggers on a branch misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Confirms that the predictor leverages register values following a misprediction flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/notes",
      "claim": "Instructions finished before the flush retain their digests to supply fresh register values to subsequent branches.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Directly states that instructions finished before branch resolution enlarge visible values when restarting after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "On a misprediction flush, entries with valid == 0 whose payload matches a flushed ROB index are cleared to valid=0 and payload=0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly notes that recovering the Tomasulo-like table is left for future work and does not specify how flushed in-flight entries are recovered."
      },
      "patch": null,
      "open_question": "How should the register status table handle flushed in-flight instructions upon a branch misprediction?",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Instruction decode handling triggers at decode when an instruction writing destination register rd is decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms that this logic triggers at decode for an instruction writing a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Decoding an instruction writing a destination register invalidates any previous digest for that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Clearing the valid bit at decode invalidates the previous digest because a new definition is in flight."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On instruction decode, decay counters for valid digests increment and stale digests are invalidated after 256 decoded instructions.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper requires invalidating digests after 256 decoded instructions, but the pseudocode completely omitted decay counter tracking and threshold invalidation."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "function on_decode(rd, rob_index):\n  for r = 0 to 64:\n    if register_status_table[r].valid == 1:\n      register_status_table[r].decay_ctr = register_status_table[r].decay_ctr + 1\n      if register_status_table[r].decay_ctr >= 256:\n        register_status_table[r].valid = 0\n  if rd >= 0 and rd < 65:\n    register_status_table[rd].valid = 0\n    register_status_table[rd].payload = rob_index & 0x3FFF // 14-bit tag\n    register_status_table[rd].decay_ctr = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table has 65 entries corresponding to logical registers 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines 65 entries for the register status table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each register status table entry contains a 1-bit valid flag, a 14-bit payload storing either a 14-bit ROB index or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines each entry as containing valid (1 bit), payload (14 bits), and decay_ctr (8 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register status table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries of 23 bits (1 + 14 + 8) each equal exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register status table is direct-mapped by logical register index r (0 <= r < 65).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one entry per logical register settles direct mapping by register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates the register usefulness table storage using 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The allowable tuning range for num_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only evaluates a fixed configuration of 65 logical registers and does not specify a legal tuning range for num_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default decay threshold for invalidating stale digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Directly states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The allowable tuning range for decay_threshold is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only specifies a single threshold value of 256 instructions and does not define an allowable parameter tuning range for decay_threshold.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "States directly that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The allowable tuning range for digest_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed 12-bit digest width and does not define an allowable parameter range for digest_bits.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding 6-bit trailing zero count, leading zero count shifted by 3, and value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles that integer register digests encode leading zeros, trailing zeros, and the six least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For 64-bit floating point registers, the 12-bit digest extracts bits [63:55] placed at digest bits [11:3] with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6 specifies extracting Value[63:55] to form the FP64 digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag registers generate a 12-bit digest by replicating 4-bit flag values three times across bits [11:8], [7:4], and [3:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verbatim defines flag digest generation as replicating the four flag bits three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated when 256 instruction decode ticks occur without new writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "States that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register component selects the valid register with the highest cumulative usefulness in a bank and scales the bank output by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms selecting the digest of the most useful available register in the component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During branch predictor training, if multiple registers were available in the same bank, exactly one is randomly selected for updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Verbatim specifies random selection of one available register per bank during training."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:mispredict_recovery+algo:instruction_decode` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alon...

[Init]
model=gemini-3.8-flash-medium conversation=5143ced2-4a05-4326-892d-425406a2217b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/6/trigger",
      "claim": "The mispredict recovery algorithm triggers on a branch misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Confirms that the predictor leverages register values following a misprediction flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/notes",
      "claim": "Instructions finished before the flush retain their digests to supply fresh register values to subsequent branches.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Directly states that instructions finished before branch resolution enlarge visible values when restarting after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "On a misprediction flush, entries with valid == 0 whose payload matches a flushed ROB index are cleared to valid=0 and payload=0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly notes that recovering the Tomasulo-like table is left for future work and does not specify how flushed in-flight entries are recovered."
      },
      "patch": null,
      "open_qu
... [truncated]

[Usage]
{"input_tokens": 28417, "output_tokens": 30397, "thinking_tokens": 26941, "cache_read_tokens": 0, "total_tokens": 58814}

[Result]
status=SUCCESS conversation=5143ced2-4a05-4326-892d-425406a2217b turns=1 duration=169.519486344s usage={"input_tokens": 28417, "output_tokens": 30397, "thinking_tokens": 26941, "cache_read_tokens": 0, "total_tokens": 58814}


