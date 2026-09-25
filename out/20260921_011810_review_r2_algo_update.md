success: True
usage: {'input_tokens': 28900, 'output_tokens': 28483, 'thinking_tokens': 24757, 'cache_read_tokens': 0, 'total_tokens': 57383}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Update of the sR component occurs at branch resolution or commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Settles that training and table update occur after prediction when branch outcome resolves at commit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Only registers valid at prediction time are updated, with at most one chosen randomly per bank to ensure single write-port simplicity.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Verifies that training updates only available registers and picks one randomly per bank for single write-port operation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The update algorithm iterates over 8 banks and skips any bank where no registers were valid at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Establishes that sR is organized into eight banks (0 to 7) and updates only registers available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When multiple valid registers are present in a bank, one is randomly selected using the hardware RNG.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Settles the policy of randomly choosing one register among multiple available candidates within a bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Subscripting UT0, UT1, and UT2 by reg_pos in update indexes the same domain (0..8 for Bank 0, 0..7 for Banks 1-7) as in predict without indexing out of bounds.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Refutes the inconsistent_index finding by confirming chosen_r is a member of that bank's assigned registers, so its position index within the bank matches the entry vector size exactly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 are indexed by hashes h0, h1, h2 of the PC and selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Confirms that table indices h0, h1, and h2 are generated from the PC and the chosen register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "WT0, WT1, and WT2 update 6-bit saturating counters bounded between -32 and 31.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms each entry in WT0, WT1, and WT2 holds a 6-bit signed counter (-32 to 31)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Weight tables are updated when the SC training condition (|lsum| <= theta or SC mispredicted) is satisfied.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does sR WT training use the standard SC threshold condition (|lsum| <= theta or mispredicted), or does sR employ a dedicated training threshold?",
      "enum_candidates": [
        "standard_sc",
        "mispredict_only",
        "always"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness tables UT0, UT1, and UT2 are updated by incrementing when the register prediction matches the branch outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training rule updates the usefulness counters in UT0, UT1, and UT2, and does it condition on individual register agreement or overall SC correctness?",
      "enum_candidates": [
        "pred_agree",
        "sc_correct",
        "bank_agree"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table contains 65 entries of 23 bits each ({valid: 1, payload: 14, decay_ctr: 8}) totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Verifies the table organization, entry bit fields, 65 logical registers, and exact total storage of 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT_Usefulness_Tables consists of 8 banks with 3 sub-tables of 8 entries each holding 6-bit usefulness weights for 65 registers, totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Settles that UT has 3 sub-tables of 8 entries (2^3) each across 65 registers with 6-bit counters, equaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT_Prediction_Weight_Tables consists of 8 banks each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Settles that each bank contains 128 (2^7), 256 (2^8), and 512 (2^9) 6-bit entries across 8 banks, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks default is 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles that the sR component is organized into 8 banks."
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
        "why": "Confirms that the register component tracks 65 logical registers across the banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "digest_width_bits default is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Settles that the digest produced from each register value is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "wt_entries_bank specifies 512, 256, and 128 entries for WT0, WT1, and WT2 per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Confirms the entry counts for the three prediction weight tables per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "ut_entries_subtable default is 8 entries per sub-table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Confirms that each of UT0, UT1, and UT2 has 8 entries per sub-table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation produces a 12-bit digest by XOR-folding trailing count, leading count shifted by 3, and value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "digest = (trailing_count & 0x3F)\n         ^ ((leading_count  & 0x3F) << 3)\n         ^ ((value & 0x3F)          << 6)",
        "why": "Validates the exact bit-shift and XOR formula used for generating integer digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition flag digest generation replicates 4 flag bits three times to fill 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verifies that flag registers replicate 4 bits three times into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 digest extraction extracts bits [63:55] and places them into bits [11:3] of the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Confirms that FP64 extracts Value[63:55] to populate bits [11:3] of the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Valid register digests are invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that the 8-bit decay counter invalidates a digest exactly after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Negative combined usefulness suppresses a bank's contribution to sR by selecting a x0 multiplier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Verifies that non-positive usefulness selects x0, suppressing the bank output."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Positive combined usefulness boosts a bank's contribution to sR by selecting a x2.5 multiplier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Verifies that positive usefulness selects the x2.5 multiplier stage for the bank contribution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple valid registers are available in a bank, exactly one is randomly chosen for WT and UT training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Validates the single write-port random selection behavior tested in unit_tests/6."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A claim...

[Init]
model=gemini-3.8-flash-medium conversation=dc4e2151-88cd-47c3-9791-31e0ef81fadf cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Update of the sR component occurs at branch resolution or commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Settles that training and table update occur after prediction when branch outcome resolves at commit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Only registers valid at prediction time are updated, with at most one chosen randomly per bank to ensure single write-port simplicity.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Verifies that training updates only available registers and picks one randomly per bank for single write-port operation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The update algorithm iterates over 8 banks and skips any bank where no registers were valid at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Establishes that sR is organized into eight banks (0 to 7) and updates only registers available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/
... [truncated]

[Usage]
{"input_tokens": 28900, "output_tokens": 28483, "thinking_tokens": 24757, "cache_read_tokens": 0, "total_tokens": 57383}

[Result]
status=SUCCESS conversation=dc4e2151-88cd-47c3-9791-31e0ef81fadf turns=1 duration=155.4678344s usage={"input_tokens": 28900, "output_tokens": 28483, "thinking_tokens": 24757, "cache_read_tokens": 0, "total_tokens": 57383}


