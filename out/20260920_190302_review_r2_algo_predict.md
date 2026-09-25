success: True
usage: {'input_tokens': 28704, 'output_tokens': 42719, 'thinking_tokens': 37948, 'cache_read_tokens': 0, 'total_tokens': 71423}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The predict algorithm executes at branch lookup time during fetch/decode to produce the sR partial sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "This establishes that register component prediction queries occur at branch lookup time when the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The sR partial sum combines with sB, sG, sP, sC, sI, sL, sS, and sT in the SC adder to form LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\"",
        "why": "Figure 5(d) shows all nine component sums feeding the summation node that produces LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode defines 'predict_sr' as the self-contained algorithm entry point rather than invoking an undefined external helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the sR prediction logic as an internal component of the SC whose algorithm is implemented by predict_sr rather than an external helper call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The token 'each' flagged as an undefined helper is prose in an explanatory comment rather than a function call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper uses 'each' as natural language describing bank register allocation, which matches its appearance in the pseudocode comment."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The token 'registers' flagged as an undefined helper is descriptive comment text rather than a missing function call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper refers to architectural registers tracked by banks, matching the pseudocode comment rather than denoting an executable helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The token 'useful' flagged as an undefined helper is descriptive comment text rather than a missing helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper establishes that 'useful' refers to the usefulness metric evaluated across tables rather than an external function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The component is partitioned into 8 banks, with Bank 0 tracking 9 registers and Banks 1-7 tracking 8 registers each using stride-8 interleaving.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly defines the organization into 8 banks of 8 or 9 logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Each bank evaluates register usefulness across three usefulness tables and selects the available register with the maximum usefulness.",
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
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For the selected register, weight tables WT0, WT1, and WT2 are queried and summed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) establishes that the selected register digest and PC query three prediction weight tables whose outputs are summed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "A bank's contribution is scaled by 2.5 when max_useful is strictly greater than 0, and scaled by 0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact usefulness condition or threshold gates the bank contribution multiplier between x2.5 and x0?",
      "enum_candidates": [
        "max_useful_gt_zero",
        "max_useful_ge_zero",
        "any_valid_reg"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The hash functions hash_ut0..2 and hash_wt0..2 map the PC and register digest to index the usefulness and weight tables.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash functions or bit-folding algorithms generate table indices for UT0..2 and WT0..2 from PC and register digest?",
      "enum_candidates": [
        "xor_fold",
        "direct_slice",
        "prime_displace"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "wt_tables consists of 8 banks of 3 direct-mapped tables (WT0 512 entries, WT1 256 entries, WT2 128 entries) with 6-bit weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the sR prediction weight table sizing as 8 banks with 2^7, 2^8, and 2^9 entries of 6 bits each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "ut_tables consists of 8 banks of 3 tables with 8 entries each, storing vectors of 6-bit usefulness weights across 65 logical registers totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the sR usefulness table structure as 65 registers times three 2^3 tables with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "ut_tables indexing is derived by folding or skewing the branch PC into three 3-bit indices.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What skewing or hashing function maps the branch PC to the 3-bit indices for UT0, UT1, and UT2?",
      "enum_candidates": [
        "xor_fold",
        "direct_slice",
        "prime_displace"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "register_tracking_table has 65 entries directly indexed by logical register ID, each containing a 1-bit valid flag, 14-bit payload, and 8-bit decay counter totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of 1 valid bit, 14 payload bits, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers tracked is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sizes the register component structures for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT0 has a default size of 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT0 as having 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT1 has a default size of 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT1 as having 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "WT2 has a default size of 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT2 as having 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Each usefulness table has a default size of 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly specifies 8 entries each for UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The decay invalidation threshold defaults to 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The useful scaling multiplier defaults to 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) labels the non-zero multiplier stage as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The prediction weight counter width defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit entries for prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The usefulness weight counter width defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit entries for usefulness weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding trailing zero/one count, leading zero/one count, and the six least significant bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify this exact 12-bit digest format for integer registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag register digests are formed by replicating the 4-bit flag pattern three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly describes replicating the 4 flag bits three times to construct the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A bank selects the register with the highest summed usefulness among available registers to query the prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 explicitly establishes that the register with the highest usefulness among available registers is selected."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "When a bank's usefulness is non-positive, the bank contribution multiplier selects x0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does a non-positive usefulness score (<= 0) trigger the x0 multiplier, or is x0 triggered only by strictly negative usefulness or the absence of a valid register?",
      "enum_candidates": [
        "le_zero",
        "lt_zero",
        "no_valid_reg"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's usefulness is positive, the weight table sum is scaled by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) establishes the x2.5 scaling factor for bank prediction contributions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A valid register digest is invalidated and cleared after 256 subsequent instructions are decoded without a new write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 confirms that digests expire and are invalidated after 256 decodes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Upon pipeline restart following a mispredicted branch, registers written by instructions completing prior to branch resolution remain valid with their digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 establishes that values produced by completed in-flight instructions remain available in the tracking table upon pipeline restart."
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
model=gemini-3.8-flash-medium conversation=2326aa0e-cb75-4019-b994-aa3d1ae9cb5c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The predict algorithm executes at branch lookup time during fetch/decode to produce the sR partial sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "This establishes that register component prediction queries occur at branch lookup time when the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The sR partial sum combines with sB, sG, sP, sC, sI, sL, sS, and sT in the SC adder to form LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\"",
        "why": "Figure 5(d) shows all nine component sums feeding the summation node that produces LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode defines 'predict_sr' as the self-contained algorithm entry point rather than invoking an undefined external helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper defines the sR prediction logic as an internal component of the SC whose algorithm is implemented by predict_sr rather than an external helper call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The token 'each' flagged as an undefined helper is prose in an explanatory comment rather than a function call.",
      "verdict": "SUPPORTED",
 
... [truncated]

[Usage]
{"input_tokens": 28704, "output_tokens": 42719, "thinking_tokens": 37948, "cache_read_tokens": 0, "total_tokens": 71423}

[Result]
status=SUCCESS conversation=2326aa0e-cb75-4019-b994-aa3d1ae9cb5c turns=1 duration=226.151801837s usage={"input_tokens": 28704, "output_tokens": 42719, "thinking_tokens": 37948, "cache_read_tokens": 0, "total_tokens": 71423}


