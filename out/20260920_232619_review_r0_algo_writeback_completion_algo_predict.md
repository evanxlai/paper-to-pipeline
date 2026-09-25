success: True
usage: {'input_tokens': 31325, 'output_tokens': 35625, 'thinking_tokens': 30821, 'cache_read_tokens': 0, 'total_tokens': 66950}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The writeback completion algorithm is triggered when an instruction completes execution in the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the update to the register status table occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Writeback completion checks whether an instruction writes a logical register as an architectural signal from the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that instructions writing a register interact with the table, which refutes the unproduced context finding because writes_register is an architectural instruction attribute delivered by the pipeline."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The completing instruction updates the table only if valid is 0 and the payload matches the 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Adopting Tomasulo's algorithm requires verifying that the stored tag matches the completing instruction's ROB tag so younger in-flight writes are not clobbered."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When completing, the entry payload is overwritten with the 12-bit digest, decay counter is reset to 0, and valid bit is set to 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper directly specifies writing the digest payload and asserting valid, with decay_ctr reset to start tracking subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Status_Digest_Table contains 65 entries corresponding to logical registers, divided into 8 banks with 9 registers in bank 0 and 8 registers in banks 1-7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states the table tracks logical registers across 8 banks of eight or nine registers each, totalling 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry in Register_Status_Digest_Table has 1 valid bit, a 14-bit payload, and an 8-bit decay counter for a total of 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly accounts for 65 entries with 1 valid bit, 14-bit payload, and 8-bit decay counter summing to 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Status_Digest_Table is direct-mapped by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper defines a direct mapping of one dedicated entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Register_Prediction_Weight_Tables_WT is organized into 8 banks with three direct-mapped sub-tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks each containing sub-tables of 2^9=512, 2^8=256, and 2^7=128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "WT entry format uses 6-bit signed saturating weights, occupying 43008 bits total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage formula with 6-bit weights totalling exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "WT sub-tables are indexed by hashing branch PC and the selected 12-bit register digest into h0 (9 bits), h1 (8 bits), and h2 (7 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\". Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) shows hashing PC and the register digest into index signals h0, h1, h2 matching the address widths of WT0, WT1, WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Register_Usefulness_Weight_Tables_UT consists of 3 tables of 8 entries each, where each entry contains 6-bit weights for all 65 registers, totalling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms 3 tables of 2^3=8 entries holding 6-bit weights for all 65 registers totalling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "UT tables are indexed by a 3-bit skewed PC hash.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows the skewed PC input addressing 8-entry usefulness tables UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks default is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly establishes an 8-bank organization for the register components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers default is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly sizes the register tables across 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "decay_threshold default is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper directly specifies invalidating digests after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "digest_width default is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "wt_weight_width default is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the weight width of prediction table WT as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "useful_multiplier default is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly labels the bank output multiplier stage as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "ut_entries_per_table default is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 specify 8 entries per usefulness table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_xor_folding produces 0xB51 for value 0x2A by XOR folding trailing zeros count, leading zeros count shifted by 3, and value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) defines the three 6-bit fields overlapping with XOR at bit offsets 0, 3, and 6, which yields 0x01 ^ (0x3A << 3) ^ (0x2A << 6) = 0xB51."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_flag_digest_replication produces 0xBBB for flag 0xB by replicating the 4-bit value three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper specifies 3-way replication of the 4 flag bits, producing 0b101110111011 = 0xBBB."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_fp32_digest_extraction extracts Value[31:26] positioned at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies extracting Value[31:26] into digest bits [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_register_decay_invalidation invalidates an entry after exactly 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_bank_usefulness_argmax_selection selects the register with maximum usefulness in the bank and scales WT sum by 2.5 when usefulness > 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Argmax selection forwards the most useful register to WT, and positive usefulness enables the 2.5x multiplier stage shown in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_bank_negative_usefulness_suppression suppresses bank output to 0 via x0 multiplier when best usefulness is negative or zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that bank contribution is scaled by x0 when the bank's usefulness is non-positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_post_misprediction_value_availability makes digests of instructions completing before pipeline flush available to subsequent branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explicitly notes that completed in-flight producer values are retained across flush and visible upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "predict_sr iterates over 8 banks, finds available valid registers, and sums combined usefulness from UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\". Their outputs go to a Sigma producing \"9 regs useful (skewed)\".",
        "why": "Figure 5(c) shows summing outputs of UT0, UT1, UT2 across banks, and subscripting by register r ranges over the same logical register domain [0, 64] as chosen_reg in update, refuting the inconsistent index warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "predict_sr selects the register with highest usefulness (argmax) and indexes WT0, WT1, WT2 using hash functions h0, h1, h2 of PC and register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\". Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) shows argmax selecting the digest for hashing into WT0, WT1, WT2; h0, h1, h2 have identical domains in predict and update, refuting the inconsistent index warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "predict_sr applies a 2.5x multiplier to the WT weight sum when best usefulness is positive, and 0x multiplier otherwise, summing over all 8 banks to produce sR_sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows the per-bank WT sum routed through the x0/x2.5 multiplier into the final adder producing sR, and refutes undefined helper findings since length is a host list primitive and 'as' is parsed from an explanatory code comment."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:writeback_completion+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they ne...

[Init]
model=gemini-3.8-flash-medium conversation=388a7f26-ca5a-4937-af6a-151ef2f87e4b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The writeback completion algorithm is triggered when an instruction completes execution in the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the update to the register status table occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Writeback completion checks whether an instruction writes a logical register as an architectural signal from the pipeline.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that instructions writing a register interact with the table, which refutes the unproduced context finding because writes_register is an architectural instruction attribute delivered by the pipeline."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The completing instruction updates the table only if valid is 0 and the payload matches the 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry
... [truncated]

[Usage]
{"input_tokens": 31325, "output_tokens": 35625, "thinking_tokens": 30821, "cache_read_tokens": 0, "total_tokens": 66950}

[Result]
status=SUCCESS conversation=388a7f26-ca5a-4937-af6a-151ef2f87e4b turns=1 duration=183.886785283s usage={"input_tokens": 31325, "output_tokens": 35625, "thinking_tokens": 30821, "cache_read_tokens": 0, "total_tokens": 66950}


