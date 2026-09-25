success: True
usage: {'input_tokens': 28182, 'output_tokens': 35718, 'thinking_tokens': 30389, 'cache_read_tokens': 0, 'total_tokens': 63900}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm triggers at branch prediction lookup time in the frontend.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that prediction lookup queries the register table and forwards valid digests to the SC at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict pseudocode computes register usefulness by reading and summing weights directly from UT0, UT1, and UT2 rather than calling an undefined external helper 'useful(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'. Their outputs go to a Sigma producing '9 regs useful (skewed)'.",
        "why": "The paper shows usefulness is computed directly by summing weights from hardware tables UT0, UT1, and UT2, refuting the finding that an external helper 'useful(...)' is called."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Registers are partitioned into 8 banks based on logical register ID modulo 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states that the register component is organized into eight banks corresponding to eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Only registers with valid digests in sR_RegStatus are eligible for usefulness evaluation in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies that the most useful register is picked only among available registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The register with the maximum usefulness sum across UT0, UT1, and UT2 within the bank is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'. Their outputs go to a Sigma producing '9 regs useful (skewed)'. That vector feeds a block labelled 'largest', whose output is labelled 'Most useful in this bank.'",
        "why": "The paper illustrates that the summed usefulness vector feeds a 'largest' block to identify the most useful register in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Ties between multiple available registers with identical maximum usefulness are broken in favor of the lower register ID.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper states that the most useful register is picked, but does not define a tie-breaking rule when multiple registers share the highest usefulness score."
      },
      "patch": null,
      "open_question": "How are ties broken during prediction if multiple available registers in a bank share the same maximum usefulness sum?",
      "enum_candidates": [
        "lowest_reg_id",
        "highest_reg_id",
        "random"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "A bank's prediction weight sum is scaled by 2.5 if its maximum usefulness is strictly greater than 0, and scaled by 0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) labels the per-bank scaling stage as 'x0 or x2.5', but does not explicitly document the gating condition or threshold that selects x2.5 over x0."
      },
      "patch": null,
      "open_question": "What explicit condition or threshold controls whether a bank's weight sum is scaled by 2.5 versus suppressed with 0?",
      "enum_candidates": [
        "usefulness_gt_zero",
        "usefulness_ge_zero"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The exact hash functions hash_u0..hash_u2 for UT and hash0..hash2 for WT are specified.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled 'PC + reg. digest', hashed into 'h0', 'h1', 'h2'.",
        "why": "The paper specifies that PC and register digest are hashed into table indices, but does not specify the concrete hash or skew algorithms."
      },
      "patch": null,
      "open_question": "What specific hash and skew functions map PC and register digests to the UT and WT table indices?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "sR is added directly to LSUM in the SC summation tree.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs 'sB, sG, sP, sC, sI, sL, sS, sT, sR' into a Sigma producing 'LSUM'.",
        "why": "Figure 5(d) shows sR entering the summation node along with the other SC component sums to form LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT is organized into 8 banks, each containing 3 direct-mapped tables of 512, 256, and 128 entries with 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT dimensions as 6-bit weights across tables of sizes 128, 256, and 512 entries across 8 banks, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "Within each bank, WT table indices are computed from the PC and the selected 12-bit register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled 'PC + reg. digest', hashed into 'h0', 'h1', 'h2'.",
        "why": "Figure 5(c) shows PC and the selected register digest forming the joint hash inputs to WT0, WT1, and WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT consists of 8 banks with 3 tables of 8 entries each storing 6-bit signed usefulness weights for all 65 registers, totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 details sR_UT storage as 6-bit weights across 65 registers and 3 tables of 8 entries (2^3) each, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "Each entry in sR_UT stores a vector of weights corresponding to the registers mapped to that bank (9 for Bank 0, 8 for Banks 1-7).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper explicitly states that first table entries contain an eight- or nine-element vector of weights for register usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_RegStatus contains 65 entries, each holding a 1-bit valid bit, 14-bit payload, and 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of { valid (1), payload (14), decay_ctr (8) }, totaling 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The 8-bit decay counter in sR_RegStatus is initialized to 256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that digests invalidate after 256 decoded instructions, but an 8-bit counter cannot hold the literal integer 256, and the paper does not specify the counter's initial value or encoding."
      },
      "patch": null,
      "open_question": "How is the 8-bit decay counter initialized and decremented to track 256 instructions given that 256 cannot fit in an unsigned 8-bit field?",
      "enum_candidates": [
        "init_255",
        "wrap_zero",
        "downcount_underflow"
      ]
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default useful_multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) explicitly labels the bank usefulness multiplier as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "useful_multiplier has an allowable tuning range of [1.0, 4.0] with step 0.5.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "The paper provides only the fixed value 2.5 and never defines an allowable tuning range or step size."
      },
      "patch": null,
      "open_question": "Does the paper define an allowable tuning range or step size for useful_multiplier, or is 2.5 fixed?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default num_banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the register component organization as eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "num_banks has an allowable tuning range of [4, 16] powers of 2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper hardcodes 8 banks to match the 65 architectural registers and specifies no alternative bank counts."
      },
      "patch": null,
      "open_question": "Does the paper define an allowable tuning range for num_banks across [4, 16], or is bank count fixed at 8?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default wt_entries configuration per bank is 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: '512 ent. WT0', '256 ent. WT1', '128 ent. WT2'.",
        "why": "Figure 5(c) explicitly gives the entries of WT0, WT1, and WT2 as 512, 256, and 128."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt_entries can be tuned across alternative choices '256,128,64' or '1024,512,256'.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: '512 ent. WT0', '256 ent. WT1', '128 ent. WT2'.",
        "why": "The paper only evaluates 512, 256, and 128 entries for WT and does not mention alternative sizing choices."
      },
      "patch": null,
      "open_question": "Does the paper specify alternative table entry choices for wt_entries?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default ut_entries_per_table is 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'.",
        "why": "Figure 5(c) explicitly defines UT0, UT1, and UT2 as having 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_table has an allowable tuning range of [4, 32] powers of 2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'.",
        "why": "The paper does not explore or specify any tuning range for UT table entry counts."
      },
      "patch": null,
      "open_question": "Does the paper define an allowable tuning range for ut_entries_per_table?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly specifies 12-bit digests generated from 64-bit register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "digest_width_bits has an allowable tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper specifies only 12-bit digests and does not suggest or define any tuning range."
      },
      "patch": null,
      "open_question": "Does the paper define an allowable tuning range for digest_width_bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding trailing zero/one count, leading zero/one count shifted left by 3, and value[5:0] shifted left by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) show the three 6-bit fields overlapping with XOR (+) operators at bit slices [5:0], [8:3], and [11:6], matching the test computation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag register digests are formed by replicating the 4-bit flag value three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly specifies replicating the four flag bits three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 register digests extract bits [31:26] into digest bits [8:3] with the remaining low bits set to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP32     Value[31:26]      6 bits        [8:3]         sign(31) + exp[30:26]",
        "why": "Figure 6(b) specifies extracting Value[31:26] into digest bit positions [8:3], leaving bits [2:0] zero."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest in sR_RegStatus is invalidated after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly defines invalidating each digest after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness contributes 0 to sR via the x0 multiplier, while a bank with positive usefulness multiplies its weight sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) specifies the multiplier stage per bank as 'x0 or x2.5', suppressing non-useful bank outputs and scaling useful bank sums by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Register digests produced by in-flight instructions completed prior to branch misprediction resolution remain valid and available upon restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 explicitly notes that instructions completed before misprediction resolution leave their values available upon restart to assist subsequent predictions."
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
model=gemini-3.8-flash-medium conversation=21ecb647-f425-4bdd-acf3-cbc52e4d1aac cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm triggers at branch prediction lookup time in the frontend.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that prediction lookup queries the register table and forwards valid digests to the SC at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict pseudocode computes register usefulness by reading and summing weights directly from UT0, UT1, and UT2 rather than calling an undefined external helper 'useful(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'. Their outputs go to a Sigma producing '9 regs useful (skewed)'.",
        "why": "The paper shows usefulness is computed directly by summing weights from hardware tables UT0, UT1, and UT2, refuting the finding that an external helper 'useful(...)' is called."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Registers are partitioned into 8 banks based on logical register ID modulo 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states that the register component is organized into eight banks corresponding to eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
... [truncated]

[Usage]
{"input_tokens": 28182, "output_tokens": 35718, "thinking_tokens": 30389, "cache_read_tokens": 0, "total_tokens": 63900}

[Result]
status=SUCCESS conversation=21ecb647-f425-4bdd-acf3-cbc52e4d1aac turns=1 duration=313.805887462s usage={"input_tokens": 28182, "output_tokens": 35718, "thinking_tokens": 30389, "cache_read_tokens": 0, "total_tokens": 63900}


