success: True
usage: {'input_tokens': 28914, 'output_tokens': 33839, 'thinking_tokens': 29369, 'cache_read_tokens': 0, 'total_tokens': 62753}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "During training, correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to logical registers that were valid and available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If several registers were available within the same bank, one is randomly selected for update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper specifies random selection among available registers within the same bank during update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Updating at most one randomly selected register per bank ensures that each table in the register component requires only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection per bank satisfies the single write port design constraint."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In UT0, UT1, and UT2, 'reg_pos' denotes the index of the chosen register within its bank (0 to 8 for Bank 0, 0 to 7 for Banks 1 to 7), accessing the corresponding element of the bank's usefulness vector.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Because chosen_r is selected from the bank's available registers, its index within the bank addresses the exact same vector dimension as during prediction, refuting the index domain mismatch warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness tables UT0, UT1, UT2 are updated based on whether the register's individual prediction agrees with the actual branch direction ((w0 + w1 + w2 >= 0) == taken).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that correlations are updated for available registers, but does not specify the training policy or condition for updating the usefulness tables (UT0, UT1, UT2).",
      "enum_candidates": [
        "pred_agree",
        "sc_correct",
        "tage_alt_diff"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Register component weights and usefulness counters are 6-bit signed saturating counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit signed counter weights for both WT and UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table contains one entry per logical register across 65 total entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper defines the Register Tracking Table as having one entry per logical register, totaling 65 entries in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of the Register Tracking Table consists of a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data gives the exact entry structure, which across 65 registers totals 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT_Usefulness_Tables consists of 8 banks with Bank 0 tracking 9 registers and Banks 1 to 7 tracking 8 registers each, containing three 8-entry sub-tables per bank of 6-bit weights totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the exact UT organization: 6-bit weights across 65 registers and three 8-entry (2^3) sub-tables, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT sub-tables are indexed by a skewed PC hash.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows skewed PC hashing providing the index into the three 8-entry UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT_Prediction_Weight_Tables consists of 8 banks each containing three tables: WT0 with 512 entries, WT1 with 256 entries, and WT2 with 128 entries of 6-bit weights, totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 confirms 8 banks of WT0 (512 = 2^9), WT1 (256 = 2^8), and WT2 (128 = 2^7) entries of 6-bit counters totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT tables are indexed by hashes h0, h1, and h2 computed from PC and the selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) shows the PC and the selected register digest combined and hashed into h0, h1, and h2 to index WT0, WT1, and WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component default number of banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 defines the register component organization as exactly eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The valid parameter range for num_banks is [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses a fixed configuration of 8 banks and does not explore or specify alternative bank counts.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms the design tracks exactly 65 logical registers across INT, FP, and flag registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The valid parameter range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the register tracking to 65 logical registers dictated by the architecture and does not specify a variable legal range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that RUNLTS generates a 12-bit digest from each 64-bit register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The valid parameter range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifically designs a 12-bit digest and does not define or evaluate other digest bit widths.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default wt_entries_bank entry counts are 512, 256, and 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify WT table entry counts of 512, 256, and 128 entries for WT0, WT1, and WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The valid choices for wt_entries_bank include 256,128,64 | 512,256,128 | 1024,512,256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes WT table sizes to 512, 256, and 128 entries without defining alternative configuration choices.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default number of entries per UT sub-table is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 confirm each UT sub-table contains 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The valid parameter range for ut_entries_subtable is [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes UT sub-tables to 8 entries and does not explore alternative capacities.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding trailing zero/one count (bits [5:0]), leading zero/one count (bits [8:3]), and value bits [5:0] (bits [11:6]).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify the exact XOR-folded bit-field composition for integer digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag digests replicate the four flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) define flag digests as a three-fold replication of the 4 flag bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 registers extract the sign bit and top 8 exponent bits (Val[63:55]) into digest bits [11:3] with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) show Val[63:55] extracted into digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "RUNLTS invalidates each register digest after 256 subsequent instructions have been decoded using an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly prescribes invalidating digests after 256 decoded instructions, tracked via the 8-bit decay counter in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's combined usefulness is not positive, the multiplier selects x0 to suppress that bank's contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows the bank's WT summation passing through a multiplier of x0 or x2.5, selecting x0 when usefulness is not positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's combined usefulness is positive, the multiplier selects x2.5, multiplying the bank's prediction weight sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Reading: each bank's contribution is scaled by 2.5 when that bank's usefulness is positive and suppressed entirely (x0) when it is not; the eight scaled per-bank contributions are then summed to give sR.",
        "why": "Figure 5(c) defines scaling the bank's prediction weight sum by 2.5 when bank usefulness is positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple valid registers are available in a bank at prediction time, exactly one is randomly selected during training for update, requiring a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 proves that random selection of one register per bank guarantees single write port operation during update."
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
model=gemini-3.8-flash-medium conversation=3028209f-4bf0-4d46-991a-850257b5c422 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "During training, correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to logical registers that were valid and available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If several registers were available within the same bank, one is randomly selected for update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper specifies random selection among available registers within the same bank during update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Updating at most one randomly selected register per bank ensures that each table in the register component requires only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection per bank satisfies the single write port design constraint."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In UT0, UT1, and UT2, 'reg_pos' denotes the index of the chosen register within its bank (0 to 8 for Bank 0, 0 to 7 for Banks 1 to 7), accessing the corresponding el
... [truncated]

[Usage]
{"input_tokens": 28914, "output_tokens": 33839, "thinking_tokens": 29369, "cache_read_tokens": 0, "total_tokens": 62753}

[Result]
status=SUCCESS conversation=3028209f-4bf0-4d46-991a-850257b5c422 turns=1 duration=184.99272945s usage={"input_tokens": 28914, "output_tokens": 33839, "thinking_tokens": 29369, "cache_read_tokens": 0, "total_tokens": 62753}


