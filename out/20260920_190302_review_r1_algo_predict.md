success: True
usage: {'input_tokens': 28711, 'output_tokens': 37748, 'thinking_tokens': 32831, 'cache_read_tokens': 0, 'total_tokens': 66459}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1",
      "claim": "The register predictor predict_sr is queried at lookup time during the fetch/decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The quote establishes that valid register digests are forwarded to query the SC register components when the branch predictor performs its lookup."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The register component is organized into 8 banks with stride-8 interleaving, tracking 9 registers in Bank 0 and 8 registers in Banks 1-7 for a total of 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The quote confirms that the component is partitioned across eight banks each containing eight or nine logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the predictor selects the digest of the most useful register among those currently available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The quote explicitly confirms the intra-bank selection mechanism that selects the most useful available register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Register usefulness within a bank is computed by summing weights across three 8-entry usefulness tables (UT0, UT1, UT2).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "The quote from Figure 5(c) confirms that each bank evaluates usefulness by reading three 8-entry usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For the selected register in each bank, three prediction weight tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) are indexed using PC and register digest, and their outputs are summed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The quote from Figure 5(c) establishes the three weight tables and their per-bank entry capacities."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The index hash functions hash_ut0, hash_ut1, hash_ut2 for the usefulness tables and hash_wt0, hash_wt1, hash_wt2 for the weight tables are fully specified.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash functions are used to compute indices for UT0, UT1, UT2 from PC and WT0, WT1, WT2 from PC and the 12-bit register digest?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "A bank's prediction weight sum is scaled by 2.5 if its maximum register usefulness is strictly positive (max_useful > 0) and is scaled by 0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact condition controls selection between scaling a bank's contribution by 2.5 versus 0?",
      "enum_candidates": [
        "gt_zero",
        "ge_zero",
        "any_valid",
        "always_2_5"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Registers are eligible for prediction selection only if their valid bit is set and their decay counter has not expired.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote confirms that digests are invalidated after the decay period so that only non-decayed, valid digests influence predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The bank contributions across all 8 banks are summed together to produce the final sR prediction value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "The quote from Figure 5(c) demonstrates that the outputs of all eight banks feed a final adder to produce sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The token 'predict_sr' represents a function definition header rather than an undefined external helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "The quote shows that sR is the output signal generated by the register component, matching the predict_sr procedure definition."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The tokens 'each', 'registers', and 'useful' in the pseudocode are natural language words inside inline comments rather than undefined executable helper function calls.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The quote verifies that 'each' and 'registers' are descriptive architectural terms used to explain bank sizing, which appear in pseudocode comments rather than as helper calls."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The sR partial sum is forwarded to the SC final adder alongside sB, sG, sP, sC, sI, sL, sS, and sT to produce LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing \"LSUM\".",
        "why": "The quote from Figure 5(d) explicitly lists sR alongside the other eight SC components entering the adder that outputs LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The prediction weight tables (wt_tables) comprise 8 banks of 3 direct-mapped tables (512, 256, and 128 entries) storing 6-bit weights, totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The quote from Table 3 specifies the exact table dimensions and 6-bit weight width across all 8 banks, yielding 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The usefulness tables (ut_tables) comprise three 8-entry tables per bank storing 6-bit usefulness weights for all 65 logical registers, totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The quote from Table 3 specifies 6-bit weights across three 8-entry tables for all 65 logical registers, yielding 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table contains 65 entries, each consisting of a 1-bit valid flag, 14-bit payload, and 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The quote from Table 3 confirms the 65-entry tracking table structure with 23 bits per entry, totaling 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The quote confirms that the register component is structured with eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers tracked across all banks is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The quote from Table 3 confirms that 65 logical registers are tracked in total."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Weight table WT0 has a default size of 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The quote from Figure 5(c) confirms that WT0 has 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Weight table WT1 has a default size of 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The quote from Figure 5(c) confirms that WT1 has 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Weight table WT2 has a default size of 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "The quote from Figure 5(c) confirms that WT2 has 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Each usefulness table (UT0, UT1, UT2) has a default size of 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "The quote from Figure 5(c) specifies 8 entries for each usefulness table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The digest decay period defaults to 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote explicitly establishes 256 decoded instructions as the decay threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The multiplier applied to useful bank weight sums defaults to 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The quote from Figure 5(c) confirms the 2.5 multiplier factor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "Each prediction weight in the WT tables defaults to a width of 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The quote from Table 3 specifies 6-bit counter weights for all WT entries in sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "Each usefulness weight in the UT tables defaults to a width of 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The quote from Table 3 specifies 6-bit weights for all UT entries in sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest generation computes a 12-bit digest by XOR-folding trailing zero count, leading zero count shifted by 3, and the 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The quote establishes that integer digests combine leading count, trailing count, and 6 LSBs as illustrated in Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag register digest replicates the 4-bit flag value three times to fill a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The quote directly specifies three-fold replication of the 4-bit condition-code field."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A bank selects the register with the highest summed usefulness weight among available registers and uses its digest along with PC to query WT0, WT1, and WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The quote confirms that the most useful available register in the bank is selected to index the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank contributes 0 to sR when the selected register's usefulness weight is non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does non-positive usefulness (useful <= 0) select the x0 multiplier, or is x0 selected only when no valid registers exist in the bank?",
      "enum_candidates": [
        "le_zero",
        "lt_zero",
        "no_valid_reg"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank scales its weight sum by 2.5 when the selected register's usefulness weight is positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What threshold on register usefulness selects the 2.5 scaling multiplier?",
      "enum_candidates": [
        "gt_zero",
        "ge_zero",
        "any_valid"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A register digest is invalidated and no longer available for prediction after 256 subsequent instructions have decoded without an update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote confirms invalidation of the digest after 256 instruction decodes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Instructions that completed execution before branch misprediction resolution retain valid digests across pipeline restart, whereas squashed instructions are invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The quote confirms that instructions completing execution prior to branch misprediction resolution remain visible to the predictor upon restart."
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
model=gemini-3.8-flash-medium conversation=9b18bfac-453f-455a-a1be-3b1b9ab70499 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1",
      "claim": "The register predictor predict_sr is queried at lookup time during the fetch/decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The quote establishes that valid register digests are forwarded to query the SC register components when the branch predictor performs its lookup."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The register component is organized into 8 banks with stride-8 interleaving, tracking 9 registers in Bank 0 and 8 registers in Banks 1-7 for a total of 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The quote confirms that the component is partitioned across eight banks each containing eight or nine logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the predictor selects the digest of the most useful register among those currently available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The quote explicitly confirms the intra-bank selection mechanism that selects the most useful available register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
   
... [truncated]

[Usage]
{"input_tokens": 28711, "output_tokens": 37748, "thinking_tokens": 32831, "cache_read_tokens": 0, "total_tokens": 66459}

[Result]
status=SUCCESS conversation=9b18bfac-453f-455a-a1be-3b1b9ab70499 turns=1 duration=205.263204498s usage={"input_tokens": 28711, "output_tokens": 37748, "thinking_tokens": 32831, "cache_read_tokens": 0, "total_tokens": 66459}


