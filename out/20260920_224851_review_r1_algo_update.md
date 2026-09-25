success: True
usage: {'input_tokens': 28727, 'output_tokens': 31185, 'thinking_tokens': 27551, 'cache_read_tokens': 0, 'total_tokens': 59912}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "sR component training update is triggered at branch commit / retirement time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not state whether sR and SC predictor updates take place at retirement/commit time or upon branch execution/resolution in the backend.",
      "enum_candidates": [
        "commit",
        "resolution"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "sR training update is gated on whether SC mispredicted or produced a weak prediction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that predictor operation follows TAGE-SC-L but does not explicitly specify the threshold or gating condition for triggering sR component updates.",
      "enum_candidates": [
        "mispred_or_weak",
        "mispred_only",
        "always"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "During training, correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that held valid digests when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "If multiple registers were available in a bank, one is randomly selected for training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies selecting one available register per bank at random during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Prediction weight tables WT0, WT1, and WT2 are updated with signed direction (+1/-1) saturating in the range [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit signed weights across the three WT sub-tables per bank, which saturate between -32 and 31 under perceptron direction updates."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness counters in sR_UT are updated for the randomly sampled register using u_delta based on sampled_pred_correct.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the training rule or correctness criterion for updating register usefulness weights in sR_UT, leaving sampled_pred_correct undefined.",
      "enum_candidates": [
        "pred_correct",
        "corrects_sc",
        "selected_only"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness tables UT0, UT1, and UT2 are indexed at depth 2 by intra-bank register subindex r_idx.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper specifies that each UT row contains a vector of 8 or 9 weights for the bank's registers, confirming r_idx indexes the bank register vector matching r_local_idx in predict."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Random selection of one available register per bank allows tables in the register component to require only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms that random selection within each bank during training avoids the need for multi-ported SRAM arrays."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT contains 8 banks each with WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) storing signed 6-bit weights, totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact formula for sR WT storage: 6 bits times (128 + 256 + 512) entries times 8 banks, totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT contains 8 banks of three 8-entry sub-tables storing 6-bit usefulness weights for each of the 65 logical registers, totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit weights across 65 registers and three 8-entry tables per bank, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_RegTracker contains 65 entries storing a 1-bit valid flag, 14-bit payload, and 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 auxiliary entries of 23 bits each (1 valid + 14 payload + 8 decay_ctr), summing to 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component sR is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly defines the register component organization into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "A total of 65 logical registers are partitioned across the banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that 65 logical registers are tracked in the usefulness and auxiliary tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Sub-table WT0 contains 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: '512 ent. WT0', '256 ent. WT1', '128 ent. WT2'.",
        "why": "Figure 5(c) transcription confirms that WT0 has 512 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Sub-table WT1 contains 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: '512 ent. WT0', '256 ent. WT1', '128 ent. WT2'.",
        "why": "Figure 5(c) transcription confirms that WT1 has 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Sub-table WT2 contains 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: '512 ent. WT0', '256 ent. WT1', '128 ent. WT2'.",
        "why": "Figure 5(c) transcription confirms that WT2 has 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Each usefulness sub-table contains 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: '9x6bit 8 ent. UT0', '8 ent. UT1', '8 ent. UT2'.",
        "why": "Figure 5(c) transcription explicitly defines UT0, UT1, and UT2 as having 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The 6-bit count of leading/trailing zeros saturates at 63 rather than wrapping modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify whether the 6-bit leading and trailing zero counts saturate at 63 or wrap modulo 64 when evaluated on 64-bit integer registers.",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Condition code flags replicate the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 4 condition-code flag bits are replicated three times to generate the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer register digests are formed by XOR-folding trailing zero count, leading zero count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The paper prose and Figure 6(a) show the three 6-bit fields overlapping and joined by circled plus (XOR) operators into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 digest extracts Value[31:26] positioned at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper prose and Figure 6(b) position the 6-bit slice Value[31:26] at digest bit positions [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly establishes the 256-instruction invalidation threshold for stale digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Within each bank, the available register with the largest summed usefulness across UT0, UT1, and UT2 is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper states that the component selects the most useful available register, and Figure 5(c) shows summing UT0-UT2 to find the largest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Bank WT output is gated by a multiplier of x0 when summed usefulness is non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) transcription confirms that the bank's WT summation output feeds into a 'x0 or x2.5' multiplier stage."
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
model=gemini-3.8-flash-medium conversation=2861e076-f370-4f9a-8546-2c23ff8c5dfa cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "sR component training update is triggered at branch commit / retirement time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not state whether sR and SC predictor updates take place at retirement/commit time or upon branch execution/resolution in the backend.",
      "enum_candidates": [
        "commit",
        "resolution"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "sR training update is gated on whether SC mispredicted or produced a weak prediction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that predictor operation follows TAGE-SC-L but does not explicitly specify the threshold or gating condition for triggering sR component updates.",
      "enum_candidates": [
        "mispred_or_weak",
        "mispred_only",
        "always"
      ]
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "During training, correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that held valid digests when the prediction was made."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "If multiple registers were available in a bank, one is randomly selected for training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies 
... [truncated]

[Usage]
{"input_tokens": 28727, "output_tokens": 31185, "thinking_tokens": 27551, "cache_read_tokens": 0, "total_tokens": 59912}

[Result]
status=SUCCESS conversation=2861e076-f370-4f9a-8546-2c23ff8c5dfa turns=1 duration=168.150305958s usage={"input_tokens": 28727, "output_tokens": 31185, "thinking_tokens": 27551, "cache_read_tokens": 0, "total_tokens": 59912}


