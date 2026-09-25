success: True
usage: {'input_tokens': 28666, 'output_tokens': 47919, 'thinking_tokens': 42062, 'cache_read_tokens': 0, 'total_tokens': 76585}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register prediction algorithm triggers at lookup time during branch prediction fetch/decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that the register component is queried to provide digests whenever the branch predictor queries the table at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The sR partial sum is forwarded to the SC final adder alongside components sB, sG, sP, sC, sI, sL, sS, and sT to compute LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) sR: Our proposed component for exploiting register-value correlations (Section 4.2)",
        "why": "The paper defines sR as an additive component extending the SC predictor structure to produce LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The prediction algorithm queries 8 banks where bank 0 tracks 9 registers and banks 1 through 7 track 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states that the register component has eight banks tracking eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the register with the largest summed usefulness weight among available registers is selected for weight table lookup.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies that the single most useful available register within the bank is chosen and forwarded to the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Each bank queries three prediction weight tables WT0, WT1, and WT2 sized at 512, 256, and 128 entries respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies that each of the 8 banks contains three weight tables of 2^9 (512), 2^8 (256), and 2^7 (128) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Bank prediction contributions are scaled by a factor of 2.5 when useful and 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) indicates that the per-bank weight summation output passes through a multiplier stage of x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode relies on an undefined helper 'get_registers_for_bank(bank_idx)' to determine the bank-to-register mapping.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper assigns 65 logical registers across 8 banks via stride-8 interleaving, but the pseudocode invokes an undefined helper function without providing its definition."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "function predict_sr(pc: uint64) -> int32:\n    sR = 0\n    for bank_idx in 0..7:\n        // 1. Evaluate usefulness for all registers assigned to this bank\n        // Bank 0 tracks 9 registers (R0, R8, ..., R64); Banks 1-7 track 8 registers each (stride-8 interleaving)\n        bank_regs = [reg for reg in 0..64 if reg % 8 == bank_idx]\n        ut0_idx = hash_ut0(pc)\n        ut1_idx = hash_ut1(pc)\n        ut2_idx = hash_ut2(pc)\n        \n        best_reg = null\n        max_useful = -INFINITY\n        \n        for reg in bank_regs:\n            if register_tracking_table[reg].valid == 1 and register_tracking_table[reg].decay_ctr > 0:\n                useful_weight = ut_tables[bank_idx].UT0[ut0_idx][reg] +\n                                ut_tables[bank_idx].UT1[ut1_idx][reg] +\n                                ut_tables[bank_idx].UT2[ut2_idx][reg]\n                if useful_weight > max_useful:\n                    max_useful = useful_weight\n                    best_reg = reg\n        \n        // 2. Query prediction weight tables if an available register exists\n        if best_reg != null:\n            digest = register_tracking_table[best_reg].payload[11:0]\n            h0 = hash_wt0(pc, digest) // 9 index bits for 512 entries\n            h1 = hash_wt1(pc, digest) // 8 index bits for 256 entries\n            h2 = hash_wt2(pc, digest) // 7 index bits for 128 entries\n            \n            wt_sum = wt_tables[bank_idx].WT0[h0] +\n                     wt_tables[bank_idx].WT1[h1] +\n                     wt_tables[bank_idx].WT2[h2]\n            \n            // Scale bank contribution: x2.5 if useful (when max_useful > 0), else x0\n            if max_useful > 0:\n                bank_contrib = int(wt_sum * 2.5) // fixed-point implementation: (wt_sum * 5) >> 1\n            else:\n                bank_contrib = 0\n            sR += bank_contrib\n        else:\n            sR += 0\n            \n    return sR"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The paper defines the exact threshold condition on usefulness weights that selects between x0 and x2.5 multipliers.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact threshold condition on bank usefulness selects between the x2.5 and x0 multiplier stages?",
      "enum_candidates": [
        "max_useful_gt_0",
        "max_useful_ge_0",
        "static_2_5"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode calls an undefined helper function 'as(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The identifier 'as' is part of an inline code comment describing fixed-point arithmetic equivalence and is not an invoked helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode calls an undefined helper function 'bits(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n \"128 ent. WT2\".",
        "why": "The identifier 'bits' is English text inside inline comments documenting index bit widths and is not an invoked helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode calls an undefined helper function 'predict_sr(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) sR: Our proposed component for exploiting register-value correlations (Section 4.2)",
        "why": "'predict_sr' is the name of the function declared by this algorithm rather than an invoked external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pseudocode calls an undefined helper function 'useful(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The identifier 'useful' is part of an explanatory inline comment and is not an invoked helper function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The wt_tables structure comprises 8 banks of 3 direct-mapped weight tables sized at 512, 256, and 128 entries totaling 7,168 entries and 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 accounts for 8 banks of 6-bit weights with 128, 256, and 512 entries, totalling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The paper specifies the exact mathematical hash functions to index WT0, WT1, and WT2 from branch PC and the 12-bit register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash functions are used to map PC and the 12-bit register digest to index WT0 (9 bits), WT1 (8 bits), and WT2 (7 bits)?",
      "enum_candidates": [
        "xor_fold",
        "prime_displacement",
        "jenkins_fold"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "The ut_tables structure comprises 8 banks, each containing 3 direct-mapped usefulness tables of 8 entries with 6-bit weights across 65 registers, totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 details the usefulness tables as 6-bit weights tracking 65 registers across three 8-entry tables totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The paper specifies the exact hash functions used to index UT0, UT1, and UT2 from branch PC.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash functions are used to produce 3-bit indices for UT0, UT1, and UT2 from the branch PC?",
      "enum_candidates": [
        "pc_slice",
        "xor_fold",
        "prime_displacement"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The register_tracking_table has 65 entries, each with a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries each containing valid (1), payload (14), and decay_ctr (8) bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The num_banks parameter default is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The num_logical_registers parameter default is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that 65 logical registers are tracked in the usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The wt0_entries parameter default is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 includes 2^9 (512) entries per bank for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The wt1_entries parameter default is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 includes 2^8 (256) entries per bank for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The wt2_entries parameter default is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 includes 2^7 (128) entries per bank for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The ut_entries_per_table parameter default is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three tables of 2^3 (8) entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The decay_instructions parameter default is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The useful_multiplier parameter default is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies a scaling multiplier factor of 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The wt_weight_bits parameter default is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 confirms that WT weights are 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The ut_weight_bits parameter default is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that UT weights are 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The test_int_digest_generation expectation asserts that 3 ^ 480 ^ 512 evaluates to 35.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test expectation contains an arithmetic evaluation error (3 ^ 480 ^ 512 evaluates to 995, not 35), rendering the test uncheckable as written."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "test_int_digest_generation",
          "given": "An integer register producing 64-bit value 0x0000000000000008 (trailing zeros = 3, leading zeros = 60, LSB6 = 0x08).",
          "expect": "Computed 12-bit digest equals (3 & 0x3F) ^ ((60 & 0x3F) << 3) ^ ((8 & 0x3F) << 6) = 3 ^ 480 ^ 512 = 995 (0x3E3), correcting the arithmetic evaluation."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code registers replicate their 4-bit flag pattern three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the 4-bit flag pattern three times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "When multiple registers are available in a bank, the bank selects the register with the largest usefulness weight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper establishes that the most useful register among available registers in the bank is picked to query the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank with non-positive usefulness contributes 0 to sR via the x0 multiplier stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) defines the multiplier stage as x0 or x2.5, selecting x0 when usefulness is non-positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with positive usefulness scales its weight sum by 2.5 to contribute to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that a bank's weight sum is scaled by 2.5 when positive usefulness is detected."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A register digest is invalidated and no longer available after 256 decoded instructions without an update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that RUNLTS invalidates each digest after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Values completed by in-flight instructions before branch resolution remain visible upon pipeline restart after misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper notes that instructions finished prior to resolution retain their values across misprediction restart, enlarging visible state."
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
model=gemini-3.8-flash-medium conversation=db00562a-4b3c-4f7b-bea0-9a5e5213a5c5 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register prediction algorithm triggers at lookup time during branch prediction fetch/decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that the register component is queried to provide digests whenever the branch predictor queries the table at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "The sR partial sum is forwarded to the SC final adder alongside components sB, sG, sP, sC, sI, sL, sS, and sT to compute LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) sR: Our proposed component for exploiting register-value correlations (Section 4.2)",
        "why": "The paper defines sR as an additive component extending the SC predictor structure to produce LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The prediction algorithm queries 8 banks where bank 0 tracks 9 registers and banks 1 through 7 track 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states that the register component has eight banks tracking eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each bank, the register with the largest summed usefulness weight among available registers is selected for w
... [truncated]

[Usage]
{"input_tokens": 28666, "output_tokens": 47919, "thinking_tokens": 42062, "cache_read_tokens": 0, "total_tokens": 76585}

[Result]
status=SUCCESS conversation=db00562a-4b3c-4f7b-bea0-9a5e5213a5c5 turns=1 duration=257.61370214s usage={"input_tokens": 28666, "output_tokens": 47919, "thinking_tokens": 42062, "cache_read_tokens": 0, "total_tokens": 76585}


