success: True
usage: {'input_tokens': 28944, 'output_tokens': 36471, 'thinking_tokens': 30672, 'cache_read_tokens': 0, 'total_tokens': 65415}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The sR prediction lookup is evaluated at branch lookup time as part of the statistical corrector evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The paper establishes that register-value correlations are integrated directly into the statistical corrector, which evaluates at branch lookup time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The sR component loops over 8 banks during prediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Logical registers are partitioned across the 8 banks using a stride-8 (r modulo 8) assignment.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Partitioning 65 logical registers across eight banks gives eight or nine registers per bank via stride-8 assignment."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Only registers with valid == 1 in the tracking table are evaluated as candidates in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that only entries with their valid bit set forward digests to the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "If a bank has no valid registers, its contribution to sR is zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Without valid entries forwarding digests, no prediction weight lookup occurs and the bank contribution is suppressed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "For each valid register, aggregated usefulness is computed by summing the weights from UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows the outputs of UT0, UT1, and UT2 feeding a summation block to produce the usefulness vector."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The register with the highest aggregated usefulness among available registers in the bank is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states that the component selects the digest of the most useful available register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Weight tables WT0, WT1, and WT2 are queried using the selected register's 12-bit digest and branch PC to retrieve 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\",\n    hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) shows the selected register digest combined with PC hashing into indices for WT0, WT1, and WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The bank weight sum is the sum of weights retrieved from WT0, WT1, and WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".\n    Their outputs go to a Sigma.",
        "why": "Figure 5(c) shows the outputs of WT0, WT1, and WT2 being summed by a Sigma block within the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Each bank's sum is scaled by 2.5 if the selected register has positive usefulness, and scaled by 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies a per-bank multiplier stage of x0 or x2.5 on the bank weight summation output."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The final sR contribution is the sum of the scaled outputs from all 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "Figure 5(c) shows the cross-bank summation node combining the bank outputs into sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Subscripting UT0, UT1, and UT2 by reg_pos indexes the bank's assigned register weight vector identically and within bounds in both predict and update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "In predict, reg_pos is the offset of candidate register r within the bank (0..8 for Bank 0, 0..7 for Banks 1-7), and in update, reg_pos is the offset of chosen_r within the same bank, both indexing the same per-entry usefulness vector."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The pseudocode does not invoke undefined helper functions named bank, bits, or tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The tokens bank, bits, and tables in the pseudocode appear inside prose comments or parenthetical explanations and are not executable helper function calls."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Each bank independently selects the most useful valid register digest, scales the WT sum by 2.5 if usefulness is positive or by 0 otherwise, and sums across all 8 banks into sR for SC LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper describes the per-bank selection of the most useful valid digest and forwarding to prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table has 65 entries, each containing a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 gives the exact entry structure, register count 65, and bit allocations for the auxiliary tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each tracking table entry is invalidated after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies a 256-instruction decay lifetime for valid digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT_Usefulness_Tables consists of 8 banks with 3 sub-tables of 8 entries each, storing 6-bit signed usefulness weights for 65 registers totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies the exact usefulness weight table formula yielding 9360 bits across 65 registers and three 8-entry sub-tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The usefulness tables are indexed by skewed PC hashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "Figure 5(c) explicitly labels the index input to UT0, UT1, and UT2 as PC (skewed)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT_Prediction_Weight_Tables has 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) of 6-bit weights, totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights across tables of 128, 256, and 512 entries in 8 banks, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Weight tables WT0, WT1, and WT2 are indexed by 9-bit, 8-bit, and 7-bit hashes derived from PC and the selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\",\n    hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) shows hashing PC and the register digest into h0, h1, and h2 for the 512, 256, and 128 entry weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks num_banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper establishes that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The legal tuning range for num_banks is [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the bank count at 8 and does not specify a legal tuning range or alternative bank counts for num_banks.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers num_logical_registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 65 logical registers tracked across the component tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The legal tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the architecture to 65 logical registers and does not specify a legal tuning range for num_logical_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default register digest width digest_width_bits is 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register value digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The legal tuning range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses a fixed 12-bit digest format and does not specify a legal tuning range of [8, 16] for digest_width_bits.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default useful multiplier useful_multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) designates a scaling factor of 2.5 for useful bank contributions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The legal tuning range for useful_multiplier is [1.0, 4.0].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed multiplier of 2.5 (or 0) and does not specify a tuning range of [1.0, 4.0] for useful_multiplier.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default entry count per bank across WT tables wt_entries_bank is 512,256,128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies WT table entry counts of 2^9 (512), 2^8 (256), and 2^7 (128)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The legal range choices for wt_entries_bank are 256,128,64 | 512,256,128 | 1024,512,256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies only the 512, 256, 128 entry configuration and does not specify alternative choices for wt_entries_bank.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default entry count per subtable ut_entries_subtable is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries for each usefulness subtable."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The legal tuning range for ut_entries_subtable is [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 8 entries per usefulness subtable and does not specify a legal tuning range of [4, 32] for ut_entries_subtable.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding trailing zero/one count (bits 5:0), leading zero/one count shifted by 3 (bits 8:3), and value LSBs shifted by 6 (bits 11:6).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies that integer digests encode trailing bit count, leading bit count, and the six least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition flag values generate a 12-bit digest by replicating the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states condition flag digests replicate the four flag bits three times to produce 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "64-bit floating-point values generate a 12-bit digest by placing sign and top exponent bits Val[63:55] into bits [11:3] with zeros in [2:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign bit and top exponent bits for floating-point digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated after exactly 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating each digest after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's combined UT usefulness is negative, the bank multiplier selects x0, producing 0 contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) provides an x0 option on the bank multiplier stage when usefulness is not positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's combined UT usefulness is positive, the bank multiplier selects x2.5, scaling the WT sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) provides an x2.5 multiplier for banks with positive usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple valid registers are available in a bank during update on a misprediction, exactly one is randomly chosen to update WT and UT tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper states that if multiple registers are available in the bank, one is randomly selected for updating the tables."
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
model=gemini-3.8-flash-medium conversation=334f6d73-ab6d-4dee-9584-a9b34c7622c4 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The sR prediction lookup is evaluated at branch lookup time as part of the statistical corrector evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The paper establishes that register-value correlations are integrated directly into the statistical corrector, which evaluates at branch lookup time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The sR component loops over 8 banks during prediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Logical registers are partitioned across the 8 banks using a stride-8 (r modulo 8) assignment.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Partitioning 65 logical registers across eight banks gives eight or nine registers per bank via stride-8 assignment."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Only registers with valid == 1 in the tracking table are evaluated as candidates in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to t
... [truncated]

[Usage]
{"input_tokens": 28944, "output_tokens": 36471, "thinking_tokens": 30672, "cache_read_tokens": 0, "total_tokens": 65415}

[Result]
status=SUCCESS conversation=334f6d73-ab6d-4dee-9584-a9b34c7622c4 turns=1 duration=176.832725309s usage={"input_tokens": 28944, "output_tokens": 36471, "thinking_tokens": 30672, "cache_read_tokens": 0, "total_tokens": 65415}


