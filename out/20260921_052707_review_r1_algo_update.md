success: True
usage: {'input_tokens': 29398, 'output_tokens': 33977, 'thinking_tokens': 29481, 'cache_read_tokens': 0, 'total_tokens': 63375}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The update routine is triggered at branch commit / retirement when SC update conditions are met.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "It establishes that sR update timing and gating follow the established TAGE-SC-L commit-time SC update rules."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Only logical registers that held a valid digest at prediction time are eligible for update training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "It explicitly limits training updates to registers that were available when the prediction was generated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "If multiple registers are available in the same bank, one is randomly selected for training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "It settles that multi-register availability within a bank is arbitrated by random selection."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 contain 512, 256, and 128 entries respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "It specifies the exact entry counts for the three prediction weight tables per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Usefulness tables are updated based on whether the chosen register's weight table sum agrees with the actual branch direction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are the register usefulness table (UT) weights updated during training, and what condition determines the update direction?",
      "enum_candidates": [
        "pred_agrees",
        "sc_mispredict",
        "sc_reversal",
        "unconditional"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Specific hash functions hash_wt0..2 and hash_ut0..2 map branch PC, bank, and digest to table indices.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash or fold functions map the branch PC, bank, and digest to the indices for WT0-WT2 and UT0-UT2?",
      "enum_candidates": [
        "xor_fold",
        "bit_slice",
        "crc",
        "prime_mod"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Selecting at most one register per bank during update guarantees that each UT and WT bank requires only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "It directly confirms that the single-register-per-bank training policy ensures a single write port per table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "Usefulness tables are organized into 8 banks with 3 tables of 8 entries each, tracking 9 registers in bank 0 and 8 in banks 1-7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "It confirms the 8-bank organization tracking eight or nine logical registers per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "Usefulness table entries contain 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "It confirms that the usefulness entries in bank 0 contain 9 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "The usefulness weight tables consume 9360 bits in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The arithmetic expression in Table 3 defines the exact UT storage of 9360 bits (6 bits * 65 registers * 24 entries)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "Usefulness tables are indexed using a 3-bit folded/skewed index derived from PC.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific folding or hash algorithm derives the 3-bit skewed PC index for the 8-entry usefulness tables?",
      "enum_candidates": [
        "xor_fold",
        "bit_slice",
        "modulo",
        "prime_fold"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "Prediction weight tables consist of 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "It defines the WT table composition and entry counts per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Prediction weight entries are 6-bit signed weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The leading factor of 6 in Table 3 specifies that WT weights are 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The prediction weight tables consume 43008 bits in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The formula in Table 3 yields 43008 bits (6 * 896 entries * 8 banks)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "WT tables are indexed by 9-bit, 8-bit, and 7-bit hashes of the PC and register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact hash functions compute the 9-bit, 8-bit, and 7-bit indices h0, h1, and h2 from PC and register digest?",
      "enum_candidates": [
        "xor_hash",
        "bit_concat",
        "crc",
        "mult_hash"
      ]
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "It establishes that the register component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The parameter range for num_banks is [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify an allowable exploration range for num_banks; only the 8-bank configuration is stated, so the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The default decay invalidation threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "It explicitly states that RUNLTS invalidates each digest after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/range",
      "claim": "The parameter range for decay_threshold_insts is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify an allowable exploration range for decay_threshold_insts; only the 256-instruction threshold is stated, so the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "It defines the register digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/range",
      "claim": "The parameter range for digest_width is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify an allowable exploration range for digest_width; only the 12-bit format is stated, so the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The default WT weight width is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "The entry width multiplier of 6 in Table 3 defines the WT weight width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/range",
      "claim": "The parameter range for wt_weight_width is [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify an allowable exploration range for wt_weight_width; only the 6-bit width is stated, so the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default UT weight width is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "The entry width multiplier of 6 in Table 3 establishes that UT weights are 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The parameter range for ut_weight_width is [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify an allowable exploration range for ut_weight_width; only the 6-bit width is stated, so the parameter range itself needs correction.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest generation XOR-folds trailing zero count, leading zero count, and the low 6 register bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading/trailing identical bit counts encoded and combined with Value[5:0] in integer register digest generation, given the 6-bit count field ambiguity flagged in U3?",
      "enum_candidates": [
        "xor_fold",
        "saturate_63",
        "mod_64",
        "count_sign_bits"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Floating point register digests are right-aligned at bit 3 with bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the floating-point register digest right-aligned at bit 3 with bits [2:0] set to zero, or right-aligned at bit 0, given the ambiguity flagged in U4?",
      "enum_candidates": [
        "bit3_aligned",
        "bit0_aligned"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag digests are generated by replicating the 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "It directly states that condition code flag digests are formed by 3x replication of the four flag bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A register digest is marked invalid after 256 instructions are decoded without a rewrite to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "It confirms that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The register with the highest usefulness weight sum in a bank is selected to forward its digest to the prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "It confirms that the most useful register among those available is chosen to forward its digest to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank's prediction contribution is gated to zero (x0 multiplier) when its usefulness sum is non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What wire selects between x0 and x2.5 multiplier in Figure 5(c), and is the contribution gated when the bank's usefulness is non-positive, as flagged in U2?",
      "enum_candidates": [
        "usefulness_sign",
        "static_scale",
        "global_useful"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank's prediction contribution is scaled by 2.5 when its usefulness sum is positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the x2.5 multiplier activated and applied to the WT prediction sum, and does it depend on positive bank usefulness, as flagged in U2?",
      "enum_candidates": [
        "usefulness_positive",
        "static_scale",
        "dynamic_confidence"
      ]
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
model=gemini-3.8-flash-medium conversation=0d042d85-95cb-4718-970b-fc357dbed622 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_bd2489640a39caf1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The update routine is triggered at branch commit / retirement when SC update conditions are met.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "It establishes that sR update timing and gating follow the established TAGE-SC-L commit-time SC update rules."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Only logical registers that held a valid digest at prediction time are eligible for update training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "It explicitly limits training updates to registers that were available when the prediction was generated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "If multiple registers are available in the same bank, one is randomly selected for training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "It settles that multi-register availability within a bank is arbitrated by random selection."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 contain 512, 256, and 128 entries respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "I
... [truncated]

[Usage]
{"input_tokens": 29398, "output_tokens": 33977, "thinking_tokens": 29481, "cache_read_tokens": 0, "total_tokens": 63375}

[Result]
status=SUCCESS conversation=0d042d85-95cb-4718-970b-fc357dbed622 turns=1 duration=174.990156699s usage={"input_tokens": 29398, "output_tokens": 33977, "thinking_tokens": 29481, "cache_read_tokens": 0, "total_tokens": 63375}


