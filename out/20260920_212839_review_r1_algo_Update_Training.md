success: True
usage: {'input_tokens': 28693, 'output_tokens': 30107, 'thinking_tokens': 26905, 'cache_read_tokens': 0, 'total_tokens': 58800}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Training updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 explicitly restricts training updates to registers that held valid digests at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If several registers were available within the same bank, one is randomly selected for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 defines the conflict-resolution policy when multiple registers in a bank are eligible for training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Prediction weights in WT are 6-bit signed values saturated within [-32, 31] using sat_update_6bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies that prediction weight tables store 6-bit signed weights, matching the [-32, 31] saturating counter bounds."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness weights UT for the chosen register are incremented if the bank prediction sign matches the branch outcome and decremented otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the exact update rule for usefulness weights (UT) in the register component during training?",
      "enum_candidates": [
        "bank_correct",
        "sc_correct",
        "tage_override"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Specific bitwise hashing functions Hash_WT0, Hash_WT1, Hash_WT2, Hash_UT0, Hash_UT1, and Hash_UT2 are defined for indexing WT and UT tables.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific bitwise hash functions are used to index the WT and UT tables from the branch PC and register digests?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Training update is performed at commit time or branch resolution time following baseline TAGE-SC-L operation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Section 4 establishes that training operation follows TAGE-SC-L, where predictor update is triggered upon branch outcome evaluation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Each table in the register component requires only a single write port because at most one register per bank is trained per branch event.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states that random single-register selection per bank guarantees a single write port per table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register tracking table contains 65 entries corresponding to logical registers, each with a 1-bit valid bit, 14-bit payload, and 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries with 1 valid bit, 14 payload bits, and 8 decay counter bits totaling 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The usefulness weight tables (UT) span 8 banks with 3 tables of 8 entries each, storing 6-bit signed weights for all 65 registers totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit weights for 65 registers across three 8-entry tables per bank, giving 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The prediction weight tables (WT) span 8 banks with three tables of 512, 256, and 128 entries of 6-bit weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact entry capacities (128, 256, 512) and 6-bit weight width across 8 banks, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly states that the register component is divided into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Prediction weight tables WT0, WT1, and WT2 have 512, 256, and 128 entries per bank respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry counts as 2^9 (512), 2^8 (256), and 2^7 (128) per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Usefulness weight tables have 8 entries per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines each of the three UT tables per bank as having 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Register digests are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly specifies that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Bank prediction sum is scaled by a multiplier of 2.5 when the bank is judged useful.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) transcription shows that each bank's prediction weight sum is scaled by 2.5 when useful and suppressed (x0) otherwise."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "A total of 65 logical registers are tracked across the 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms that 65 logical registers are tracked in total."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register value digest is generated by XOR-folding trailing count, leading count shifted by 3, and the 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest is formed from trailing count, leading count, and 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags digest is formed by replicating the 4-bit flag value three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 states that the 12-bit flag digest replicates the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A valid register digest decays and becomes invalid when decay_ctr reaches 0 upon advancing decode ticks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 establishes that digest validity is terminated when the decoded instruction lifetime expires."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank with positive usefulness scales its WT sum by 2.5 while a bank without useful or valid registers contributes 0 to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) indicates that useful banks contribute their WT sum scaled by 2.5, whereas non-useful banks contribute 0 (x0)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers in a bank are valid at prediction time, exactly one is randomly chosen for training to require only a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 confirms that exactly one available register per bank is randomly chosen during training to limit write port demand to 1."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:Update (Training)` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the pap...

[Init]
model=gemini-3.8-flash-medium conversation=1d0d57a3-2aa0-4f6b-ac07-576aea45f82c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Training updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 explicitly restricts training updates to registers that held valid digests at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "If several registers were available within the same bank, one is randomly selected for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 defines the conflict-resolution policy when multiple registers in a bank are eligible for training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Prediction weights in WT are 6-bit signed values saturated within [-32, 31] using sat_update_6bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies that prediction weight tables store 6-bit signed weights, matching the [-32, 31] saturating counter bounds."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness weights UT for the chosen register are incremented if the bank prediction sign matches the branch outcome and decremented otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the exact upda
... [truncated]

[Usage]
{"input_tokens": 28693, "output_tokens": 30107, "thinking_tokens": 26905, "cache_read_tokens": 0, "total_tokens": 58800}

[Result]
status=SUCCESS conversation=1d0d57a3-2aa0-4f6b-ac07-576aea45f82c turns=1 duration=162.134135057s usage={"input_tokens": 28693, "output_tokens": 30107, "thinking_tokens": 26905, "cache_read_tokens": 0, "total_tokens": 58800}


