success: True
usage: {'input_tokens': 29965, 'output_tokens': 30815, 'thinking_tokens': 26039, 'cache_read_tokens': 0, 'total_tokens': 60780}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a branch misprediction flush, Register_Status_Digest_Table entries with valid == 0 whose payload ROB tag matches a flushed instruction are cleared by setting valid to 0 and payload to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper does not define any algorithm for restoring or clearing in-flight table entries on a misprediction flush, explicitly leaving recovery of the Tomasulo-like table to future work."
      },
      "patch": null,
      "open_question": "How should the Register Status Digest Table be recovered when in-flight instructions are squashed during a branch misprediction flush?",
      "enum_candidates": [
        "tag_match_clear",
        "checkpoint",
        "none"
      ]
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Squash recovery is triggered upon a branch misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper identifies the post-flush restart following a misprediction as the boundary where extra completed values become available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "In-flight instructions finishing execution before a misprediction resolves enlarge the visible register digests available when the pipeline restarts.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explicitly states that instructions completing before branch resolution enlarge the set of values available upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decode_rename_and_decay algorithm reads inst.writes_register as an external instruction property provided by the CPU decode stage rather than an internally generated predictor signal.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper confirms that identifying register-writing instructions occurs at decode as part of pipeline decoding, refuting the unproduced_context warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the valid bit, stores its 14-bit ROB tag in the payload, and resets the decay counter to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that an instruction writing a register writes its ROB index into the table entry and clears valid at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Each valid register digest is tracked by a decay counter incremented on decoded instructions and invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that valid digests are invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The decode_rename_and_decay algorithm triggers at instruction decode / rename stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies decode as the trigger point for tracking register writing instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The decay counter prevents stale register digests from misguiding branch predictions by invalidating them after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that invalidation after 256 decoded instructions ensures only up-to-date information influences future predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Register_Status_Digest_Table contains 65 entries partitioned into 8 banks with Bank 0 holding 9 registers and Banks 1-7 holding 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies 8 banks partitioned across 65 registers with eight or nine registers assigned to each bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each Register_Status_Digest_Table entry consists of a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure as valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "Register_Status_Digest_Table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry (1 + 14 + 8) equals 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "Register_Status_Digest_Table is direct-mapped by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having dedicated entries per logical register directly corresponds to direct-mapped indexing by register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "Register_Prediction_Weight_Tables_WT comprises 8 banks, each containing 3 direct-mapped sub-tables of 512 (WT0), 256 (WT1), and 128 (WT2) entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives WT sizing across 8 banks as tables of 2^7 (128), 2^8 (256), and 2^9 (512) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "Each WT entry is a 6-bit signed saturating counter weight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "Total storage capacity for WT is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * (128 + 256 + 512 entries) * 8 banks equals exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "WT sub-tables WT0, WT1, and WT2 are indexed using hash functions h0 (9 bits), h1 (8 bits), and h2 (7 bits) combining branch PC and selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table sizes of 2^9, 2^8, and 2^7 dictate index widths of 9, 8, and 7 bits respectively from the hashed PC and digest inputs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "Register_Usefulness_Weight_Tables_UT consists of 3 tables (UT0, UT1, UT2) of 8 entries each, with each entry holding 6-bit weights for all 65 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies 3 tables of 2^3 entries, each containing 6-bit weights for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each UT entry contains 6-bit weights for 65 registers, totalling 390 bits per entry.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 establishes that each entry holds 6-bit weights across 65 registers, yielding 390 bits per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "Total storage capacity for UT is 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "6 bits * 65 registers * 24 table entries (8 * 3) equals 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "UT tables are indexed by a 3-bit skewed PC hash addressing 8 entries independently for UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries per UT table, requiring a 3-bit index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the UT and auxiliary status tables using 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default decay threshold for invalidating stale digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the threshold for digest invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default digest width for register values is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper states that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register value of 0x2A produces a 12-bit digest of 0xB51 via XOR folding of trailing zeros, leading zeros, and LSBs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies folding leading zero count, trailing zero count, and 6 LSBs into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A condition code register with 4-bit flag value 0b1011 generates a 12-bit digest by replicating the 4 bits three times to produce 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper directly specifies replicating the four flag bits three times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register extracts Value[31:26] into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign bit and leading exponent bits (Value[31:26] for FP32) into digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest remains valid with decay_ctr = 255 after 255 decoded instructions and invalidates on the 256th decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that invalidation occurs after exactly 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register with the highest usefulness sum in a bank is selected and scaled by x2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies picking the digest of the most useful available register, and Figure 5(c) includes the x0 or x2.5 scaling stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank whose best usefulness is negative applies multiplier x0, contributing 0 to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) defines the bank scaling stage as choosing between x0 and x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Instructions completing prior to misprediction flush completion leave valid digests available upon fetch restart, while uncompleted flushed instructions do not.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper confirms that instructions finishing execution before misprediction resolution enlarge the available values visible upon restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:squash_recovery+algo:decode_rename_and_decay` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=e35fe96a-6551-4e18-9e6c-a96a7db8ee4f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a branch misprediction flush, Register_Status_Digest_Table entries with valid == 0 whose payload ROB tag matches a flushed instruction are cleared by setting valid to 0 and payload to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper does not define any algorithm for restoring or clearing in-flight table entries on a misprediction flush, explicitly leaving recovery of the Tomasulo-like table to future work."
      },
      "patch": null,
      "open_question": "How should the Register Status Digest Table be recovered when in-flight instructions are squashed during a branch misprediction flush?",
      "enum_candidates": [
        "tag_match_clear",
        "checkpoint",
        "none"
      ]
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Squash recovery is triggered upon a branch misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper identifies the post-flush restart following a misprediction as the boundary where extra completed values become available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "In-flight instructions finishing execution before a misprediction resolves enlarge the visible register digests available when the pipeline restarts.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of val
... [truncated]

[Usage]
{"input_tokens": 29965, "output_tokens": 30815, "thinking_tokens": 26039, "cache_read_tokens": 0, "total_tokens": 60780}

[Result]
status=SUCCESS conversation=e35fe96a-6551-4e18-9e6c-a96a7db8ee4f turns=1 duration=153.241909416s usage={"input_tokens": 29965, "output_tokens": 30815, "thinking_tokens": 26039, "cache_read_tokens": 0, "total_tokens": 60780}


