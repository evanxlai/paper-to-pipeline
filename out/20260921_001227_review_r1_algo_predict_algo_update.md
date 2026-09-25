success: True
usage: {'input_tokens': 31755, 'output_tokens': 42376, 'thinking_tokens': 38247, 'cache_read_tokens': 0, 'total_tokens': 74131}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/0",
      "claim": "The sR component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly establishes that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Sub-table WT0 in each bank of sR_WT contains 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT0 as a 512-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Sub-table WT1 in each bank of sR_WT contains 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT1 as a 256-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Sub-table WT2 in each bank of sR_WT contains 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT2 as a 128-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each of the three usefulness sub-tables (UT0, UT1, UT2) in each bank contains 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly labels UT0, UT1, and UT2 as having 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "A bank's prediction contribution in sR is scaled by 2.5 when selected as useful.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly shows the per-bank prediction weight sum feeding a multiplier of x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The sR component tracks 65 logical registers across all banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input row \"9 regs digest\" listing \"R0  R8  R16  ...  R64\".",
        "why": "Figure 5(c) shows bank 0 tracking 9 registers up to R64 across 8 stride-8 banks, totaling 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT consists of 8 banks with 3 direct-mapped sub-tables of 512, 256, and 128 entries of 6-bit signed counters, totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact storage formula for sR WT across 8 banks with 2^7, 2^8, and 2^9 6-bit counter entries, totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT consists of 8 banks with 3 direct-mapped sub-tables of 8 entries each, storing a vector of 6-bit weights for 65 tracked logical registers, totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit weights across 65 registers and three 8-entry sub-tables, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "reg_tracking_table contains 65 entries, each with a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of valid (1 bit), payload (14 bits), and decay_ctr (8 bits), equaling 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "An entry in reg_tracking_table holds either a 14-bit tag (ROB index) when invalid or a 12-bit register digest when valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 explicitly describes the entry payload as holding either a 14-bit tag or a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The predict algorithm is triggered at branch prediction lookup time to forward digests from valid tracking table entries to the SC register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 confirms that table lookup and forwarding to the register components occurs when the branch predictor queries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Predict selects the available register in each bank having the highest usefulness sum across UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 states that the component selects the digest of the most useful register among those available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "If the selected register's usefulness is positive, the bank's WT weight sum is scaled by 2.5 and added to sR_sum; otherwise the bank contributes 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows each bank's prediction weight sum passing through a multiplier of x0 or x2.5 before the cross-bank sum."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "When multiple registers in a bank are available at prediction time, one is randomly sampled for single-port training update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 explicitly specifies randomly selecting one available register in the bank for the update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "sR update is invoked when the statistical corrector predictor trains.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "Section 1 explains that sR is integrated directly into the SC, meaning its training is conditioned on SC training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Training updates for sR are applied only to logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 explicitly restricts training updates to registers that were available when prediction occurred."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Prediction weight tables (WT) are trained using signed saturating counter increments on taken and decrements on not-taken.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Section 4.2 and Table 3 specify that WT tables follow standard SC component design with 6-bit saturating counters updated according to branch direction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness tables (UT) update their weights using delta +1 if the sampled register's WT prediction matches the branch direction and -1 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that UT tracks prediction usefulness 'as with the SC's existing components', but does not specify the exact mathematical condition for updating UT weights—specifically whether the update delta is determined solely by the sampled register's WT prediction matching the outcome (pred_sign == taken), or whether it depends on whether the register contribution would have corrected an overall misprediction or agreed with the final SC prediction.",
      "enum_candidates": [
        "pred_matches_taken",
        "sc_corrects_tage",
        "agrees_with_sc"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test int_digest_generation_check verifies 12-bit integer digest generation by XORing trailing zeros/ones at [5:0], leading zeros/ones at [8:3], and LSB[5:0] at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest is formed by overlapping trailing count, leading count shifted by 3, and value LSBs shifted by 6 with XOR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test fp64_digest_generation_check verifies that FP64 values extract Value[63:55] placed at digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies that FP64 registers extract Value[63:55] into digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test flag_digest_generation_check verifies that condition code flags replicate the 4-bit flag nibble three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly specifies replicating four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test digest_decay_invalidation verifies that an entry in reg_tracking_table is invalidated after 256 decoded instructions without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test bank_usefulness_selection_and_gating verifies that the register with highest usefulness is selected in each bank and scaled by 2.5 if usefulness > 0, or gated to 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) specify selecting the most useful register in each bank and scaling its WT output by 2.5 when positive, or gating to 0 otherwise."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Unit test post_squash_retention verifies that valid digests produced by completed instructions remain valid in reg_tracking_table across pipeline misprediction flushes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 explains that completed execution values remain visible after a branch misprediction flush so post-flush restart predictions can correlate on them."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict+algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the p...

[Init]
model=gemini-3.8-flash-medium conversation=7dbe7130-e423-47b0-81bd-86756c2ef6b2 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/0",
      "claim": "The sR component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly establishes that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Sub-table WT0 in each bank of sR_WT contains 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT0 as a 512-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Sub-table WT1 in each bank of sR_WT contains 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT1 as a 256-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Sub-table WT2 in each bank of sR_WT contains 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT2 as a 128-entry prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each of the three usefulness sub-tables (UT0, UT1, UT2) in each b
... [truncated]

[Usage]
{"input_tokens": 31755, "output_tokens": 42376, "thinking_tokens": 38247, "cache_read_tokens": 0, "total_tokens": 74131}

[Result]
status=SUCCESS conversation=7dbe7130-e423-47b0-81bd-86756c2ef6b2 turns=1 duration=213.407564311s usage={"input_tokens": 31755, "output_tokens": 42376, "thinking_tokens": 38247, "cache_read_tokens": 0, "total_tokens": 74131}


