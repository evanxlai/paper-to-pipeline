success: True
usage: {'input_tokens': 28950, 'output_tokens': 36502, 'thinking_tokens': 32039, 'cache_read_tokens': 0, 'total_tokens': 65452}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "Register component prediction lookup is triggered at branch lookup time during Fetch / SC evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that valid digests are forwarded to the SC register-value components whenever the branch predictor queries the table at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Register components are partitioned into 8 banks with stride-8 logical register assignment, where Bank 0 tracks 9 registers and Banks 1-7 track 8 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly defines the organization of the register component into eight banks covering 8 or 9 logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "If a bank contains no valid register digests, its contribution to sR is suppressed to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Entries forward digests for prediction only when their valid bit is set, so an empty valid set provides no digest and contributes nothing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "For each bank, the predictor computes the usefulness of each valid assigned register across three usefulness sub-tables (UT0, UT1, UT2) indexed by skewed PC and selects the register digest with the largest usefulness.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states that the component selects the digest of the most useful available register to query the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Each bank queries three prediction weight tables (WT0, WT1, WT2) with sizes 512, 256, and 128 entries indexed by hashes of PC and the chosen register digest, summing their weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies the three WT tables of 512, 256, and 128 entries per bank and sums their outputs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The bank prediction sum is scaled by 2.5 if the selected register usefulness is strictly positive, and zeroed (x0) otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows a multiplier stage labelled 'x0 or x2.5' downstream of the WT sum, but the paper never defines the control condition or threshold that selects between x0 and x2.5.",
      "enum_candidates": [
        "best_usefulness_gt_0",
        "best_usefulness_ge_0",
        "always_2_5"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The outputs from all eight banks are summed together to produce the final sR component output for the SC adder.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "Figure 5(c) shows all eight bank outputs feeding a summation node that outputs sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The expression '(r % 8 == bank)' is an inline clarifying condition and not an invocation of an undefined helper function 'bank'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The text explains the stride-8 bank assignment of 65 registers across 8 banks and is not a function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The text '// 9 bits (512 entries)' is an explanatory comment and not an invocation of an undefined helper function 'bits'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The text is an inline comment documenting the index width for the 512-entry WT0 table shown in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The text '// Query prediction weight tables (WT0, WT1, WT2)' is an explanatory comment and not an invocation of an undefined helper function 'tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The text is an inline section comment naming the prediction weight tables, not a code invocation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The variable 'reg_pos' subscripting UT0, UT1, and UT2 represents the intra-bank register position with identical domains [0, 8] for Bank 0 and [0, 7] for Banks 1-7 in both predict and update algorithms.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Each UT entry stores an 8- or 9-element vector corresponding to the registers assigned to that bank, so intra-bank index positions match across predict and update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table contains 65 direct-mapped entries tracking all logical registers, each entry containing a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines 65 entries formatted as 1-bit valid, 14-bit payload, and 8-bit decay counter (65 * 23 = 1495 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT_Usefulness_Tables comprises 8 banks where Bank 0 tracks 9 registers and Banks 1-7 track 8 registers across three 8-entry sub-tables (UT0, UT1, UT2) of 6-bit signed weights totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies the UT budget as 6-bit weights for 65 registers across three 2^3-entry sub-tables (6 * 65 * 24 = 9360 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT_Prediction_Weight_Tables comprises 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit signed saturating weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies the WT budget as 6-bit weights for tables of 128, 256, and 512 entries across 8 banks (6 * 896 * 8 = 43008 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks has a default value of 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 establishes that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers has a default value of 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly uses 65 registers in the storage breakdown for both UT and Register Tracking Table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "digest_width_bits has a default value of 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "useful_multiplier has a default value of 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly labels the bank multiplier stage with scaling factor 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "wt_entries_bank has a default configuration of '512,256,128'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) specifies WT0 with 512 entries, WT1 with 256 entries, and WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "ut_entries_subtable has a default value of 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies each of the three UT sub-tables having 2^3 = 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest generates a 12-bit output by XOR-folding trailing zero count [5:0], leading zero count shifted by 3 [8:3], and value LSBs shifted by 6 [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify the XOR folding of trailing count, leading count, and 6 LSBs into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag digest is formed by replicating the 4-bit flag value three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly describes replicating the 4 condition flag bits three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 register digest extracts sign and high exponent bits Value[63:55] and places them into digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) show extracting Value[63:55] for FP64 aligned at digest bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest in the Register Tracking Table is invalidated after 256 decoded instructions without being overwritten.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly specifies invalidating each digest after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A negative bank usefulness (-4) causes the bank multiplier to select x0, zeroing the bank contribution to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "While Figure 5(c) provides 'x0 or x2.5', the paper does not specify the exact gating condition or threshold under which x0 is chosen instead of x2.5.",
      "enum_candidates": [
        "zero_on_nonpositive",
        "zero_on_negative",
        "always_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When the x2.5 bank multiplier is active, a WT sum of +10 produces a contribution of +25 via (sum * 5) / 2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies the multiplier factor of 2.5, which scales a WT sum of +10 to +25."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "During training, when multiple registers in a bank were available at prediction time, exactly one is randomly chosen for WT and UT updates, requiring a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly describes random selection of one available register per bank during update to use a single write port."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.8-flash-medium conversation=ac3d821d-1a84-4174-b4ec-364d665b5c21 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "Register component prediction lookup is triggered at branch lookup time during Fetch / SC evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that valid digests are forwarded to the SC register-value components whenever the branch predictor queries the table at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Register components are partitioned into 8 banks with stride-8 logical register assignment, where Bank 0 tracks 9 registers and Banks 1-7 track 8 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly defines the organization of the register component into eight banks covering 8 or 9 logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "If a bank contains no valid register digests, its contribution to sR is suppressed to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Entries forward digests for prediction only when their valid bit is set, so an empty valid set provides no digest and contributes nothing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithm
... [truncated]

[Usage]
{"input_tokens": 28950, "output_tokens": 36502, "thinking_tokens": 32039, "cache_read_tokens": 0, "total_tokens": 65452}

[Result]
status=SUCCESS conversation=ac3d821d-1a84-4174-b4ec-364d665b5c21 turns=1 duration=195.211525448s usage={"input_tokens": 28950, "output_tokens": 36502, "thinking_tokens": 32039, "cache_read_tokens": 0, "total_tokens": 65452}


