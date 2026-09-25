success: True
usage: {'input_tokens': 29973, 'output_tokens': 29977, 'thinking_tokens': 25518, 'cache_read_tokens': 0, 'total_tokens': 59950}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a branch misprediction flush, entries in Register_Status_Digest_Table with matching in-flight ROB tags are cleared or restored to a checkpointed state.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Section 5 explicitly leaves recovery of the Tomasulo-like table after flushes as future work and does not specify any squash recovery algorithm."
      },
      "patch": null,
      "open_question": "How should entries in the Register Status Digest Table be recovered on a branch misprediction flush when instructions are aborted?",
      "enum_candidates": [
        "clear_flushed_tags",
        "checkpoint_restore",
        "flash_invalidate",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions that finished execution by the time a misprediction resolves remain valid upon restart, providing extra digests to correct subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 confirms that completed in-flight instructions retain their completed values and expand visible digests upon pipeline restart after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the valid bit and records its 14-bit ROB tag in the Register Status Digest Table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 directly specifies storing the ROB index as a tag and clearing the valid bit at decode, refuting the warning that inst.writes_register is unproduced predictor context rather than a CPU decode pipeline interface."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Valid register digests in the Register Status Digest Table are invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states verbatim that digests are invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Register_Status_Digest_Table contains 65 entries partitioned across 8 banks, with bank 0 containing 9 registers and banks 1-7 containing 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 and Table 3 specify 65 total entries partitioned into eight banks of eight or nine registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry of Register_Status_Digest_Table contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure with 1-bit valid, 14-bit payload, and 8-bit decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "Register_Status_Digest_Table requires 1495 bits of total storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates 23 bits per entry for 65 entries, exactly yielding 23 x 65 = 1495 bits."
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
        "why": "Section 4.2 specifies having exactly one entry per logical register in the dedicated status table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "Register_Prediction_Weight_Tables_WT comprises 8 banks, each containing three sub-tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the prediction weight tables across 8 banks with 2^7, 2^8, and 2^9 entries per bank."
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
        "why": "Table 3 specifies a 6-bit weight width for all prediction weight table entries in sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "Register_Prediction_Weight_Tables_WT consumes 43008 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 arithmetic confirms 6 x (128 + 256 + 512) x 8 = 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "Register_Usefulness_Weight_Tables_UT consists of three 8-entry tables where each entry holds 6-bit weights for all 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three tables of 2^3 entries, each containing 6-bit usefulness weights for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each UT entry contains 6-bit signed weights per register, totaling 390 bits per table entry.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 shows each entry stores a 6-bit weight per register for 65 registers (6 x 65 = 390 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "Register_Usefulness_Weight_Tables_UT total storage is 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates 6 x 65 x 24 = 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default value of num_logical_registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes all register-tracking structures to 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "num_logical_registers has a legal tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper hardcodes 65 logical registers for the evaluated architecture and does not specify or explore any alternative range."
      },
      "patch": null,
      "open_question": "The paper hardcodes 65 logical registers partitioned into 8 banks; what is the legal tuning range for the number of logical registers?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default value of decay_threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes 256 decoded instructions as the invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "decay_threshold has a tuning range of [64, 1024] powers of 2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper only uses 256 instructions (with an 8-bit counter in Table 3) without specifying a tuning range."
      },
      "patch": null,
      "open_question": "The paper hardcodes the decay threshold at 256 instructions; what is the intended search range for tuning this threshold?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The default value of digest_width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that all register digests are generated with a width of 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/range",
      "claim": "digest_width has a tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper specifies only a 12-bit digest format and does not define a tuning range."
      },
      "patch": null,
      "open_question": "The paper designs only a 12-bit digest format; what is the legal range of digest bit widths for tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, 1 trailing zero, 58 leading zeros, and LSB 0x2A produce 12-bit digest 0xB51 via XOR-folding.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify XOR-folding of 6-bit trailing count [5:0], 6-bit leading count [8:3], and 6-bit value slice [11:6], matching 0x01 ^ (0x3A << 3) ^ (0x2A << 6) = 0xB51."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags replicate 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 verbatim states that condition-code flag bits are replicated three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For FP32 registers, Value[31:26] is extracted and placed at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) confirm that FP32 extracts Value[31:26] and positions it at digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest remains valid for 255 decoded instructions and invalidates on the 256th instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 confirms invalidation occurs after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register with maximum positive usefulness in a bank is selected and scales the bank weight sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) confirm argmax selection of the most useful register in a bank and scaling by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "If the maximum usefulness in a bank is non-positive, multiplier stage applies x0 and suppresses the bank contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Figure 5(c) provides a bank multiplier stage of x0 or x2.5 driven by bank usefulness, suppressing non-positive contributions with x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "In-flight instructions completing before a flush completes provide valid digests for restart, while uncompleted flushed instructions do not.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 establishes that instructions finishing execution before flush completion supply visible digests upon pipeline restart."
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
model=gemini-3.8-flash-medium conversation=779d3a3a-56c1-4905-b7e8-d5f89afd044c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a branch misprediction flush, entries in Register_Status_Digest_Table with matching in-flight ROB tags are cleared or restored to a checkpointed state.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Section 5 explicitly leaves recovery of the Tomasulo-like table after flushes as future work and does not specify any squash recovery algorithm."
      },
      "patch": null,
      "open_question": "How should entries in the Register Status Digest Table be recovered on a branch misprediction flush when instructions are aborted?",
      "enum_candidates": [
        "clear_flushed_tags",
        "checkpoint_restore",
        "flash_invalidate",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions that finished execution by the time a misprediction resolves remain valid upon restart, providing extra digests to correct subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 confirms that completed in-flight instructions retain their completed values and expand visible digests upon pipeline restart after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the valid bit and records its 14-bit ROB tag in the Register Status Digest Table.",
      "verdict": "SUPPORTED",
      "e
... [truncated]

[Usage]
{"input_tokens": 29973, "output_tokens": 29977, "thinking_tokens": 25518, "cache_read_tokens": 0, "total_tokens": 59950}

[Result]
status=SUCCESS conversation=779d3a3a-56c1-4905-b7e8-d5f89afd044c turns=1 duration=146.286974879s usage={"input_tokens": 29973, "output_tokens": 29977, "thinking_tokens": 25518, "cache_read_tokens": 0, "total_tokens": 59950}


