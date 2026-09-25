success: True
usage: {'input_tokens': 30211, 'output_tokens': 33944, 'thinking_tokens': 29640, 'cache_read_tokens': 0, 'total_tokens': 64155}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Correlations are trained only for logical registers that were available at prediction time, selecting one at random if multiple in a bank were available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly defines the training availability restriction and the random selection rule per bank to enforce a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update_sr function signature defines the entry-point algorithm for training sR tables rather than calling an undefined external policy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The function definition implements the paper's specified training procedure for available register correlations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "When multiple registers in a bank are available at prediction time, random_select picks one available register to update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly prescribes random selection among available registers in the bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "WT counter weights are trained using 6-bit signed saturating counter arithmetic clamped to [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry width as 6 bits per weight, which corresponds to signed saturating counter range [-32, 31]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "UT usefulness weights are trained by incrementing when the WT prediction direction matches the actual branch outcome and decrementing otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are UT usefulness weights updated during training (e.g. incremented when the WT prediction matches the branch outcome, or following the standard TAGE-SC usefulness update rule where weights increment only when the component provides a correct override of the base predictor)?",
      "enum_candidates": [
        "wt_agreement",
        "sc_usefulness",
        "mispredict_only"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "WT tables are indexed by hash functions hash_wt0, hash_wt1, hash_wt2 and UT tables by hash_ut0, hash_ut1, hash_ut2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash functions are used to index the WT tables from (PC, digest) and the UT tables from skewed PC?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions that finished execution prior to branch misprediction resolution preserve their valid digests in the tracking table upon pipeline restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper directly motivates preserving finished execution results across mispredictions to expand visible state after the flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline squash, on_pipeline_squash searches for tracking entries with valid=0 and invalidates them if their pending payload matches a squashed ROB index.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are squashed in-flight instructions handled in the register tracking table upon a pipeline squash when an in-flight speculative instruction that cleared the valid bit is squashed?",
      "enum_candidates": [
        "invalidate_tag_match",
        "checkpoint_restore",
        "clear_on_squash"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "WT tables consist of 8 banks with 3 tables per bank (WT0 of 512 entries, WT1 of 256 entries, WT2 of 128 entries) of 6-bit weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of three tables with 2^7, 2^8, and 2^9 entries using 6-bit weights, totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT tables consist of 8 banks with 3 tables of 8 entries each, storing vectors of 6-bit signed weights across 65 logical registers totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 65 registers across three 2^3-entry tables using 6-bit weights, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table has 65 entries, each holding a valid bit, a 14-bit payload, and an 8-bit decay counter totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies 65 entries each containing a 1-bit valid flag, 14-bit payload, and 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks defaults to 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers defaults to 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms the auxiliary tracking table allocates entries for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt0_entries defaults to 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT0 as a 512-entry table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt1_entries defaults to 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT1 as a 256-entry table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "wt2_entries defaults to 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT2 as a 128-entry table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "ut_entries_per_table defaults to 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) specifies 8 entries each for UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "decay_instructions defaults to 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the digest invalidation lifetime."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "useful_multiplier defaults to 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly labels the usefulness scaling multiplier stage as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "wt_weight_bits defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 sets the WT entry weight width to 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "ut_weight_bits defaults to 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sets the UT entry weight width to 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are generated by XOR-folding trailing zero/one count, leading zero/one count shifted by 3, and register LSB6 shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and the text establish the 12-bit digest structure as the 3-way XOR fold of trailing count [5:0], leading count [8:3], and Value[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag register digests replicate the 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states condition-code flag digests replicate the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A bank selects the available register with the largest summed usefulness and queries WT tables with hash(PC, digest).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies selecting the digest of the most useful available register within the bank to index the WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "When bank usefulness is non-positive, multiplier selects x0 and suppresses bank contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) establishes the bank output multiplier as choosing between x0 and x2.5 based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When bank usefulness is positive, multiplier scales the bank WT sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies scaling by 2.5 when the bank prediction is useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "After 256 instruction decodes without an update, a tracking entry reaches decay count 0 and invalidates its valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Instructions completed before misprediction resolution retain their valid digests and participate in post-restart prediction while squashed instructions are invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explains that execution results finished prior to misprediction resolution remain visible to improve accuracy upon pipeline restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:mispredict_recovery+algo:update_and_train` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone;...

[Init]
model=gemini-3.8-flash-medium conversation=29a8ab56-40c6-42fc-b1e7-f71978d046ec cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Correlations are trained only for logical registers that were available at prediction time, selecting one at random if multiple in a bank were available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly defines the training availability restriction and the random selection rule per bank to enforce a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update_sr function signature defines the entry-point algorithm for training sR tables rather than calling an undefined external policy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The function definition implements the paper's specified training procedure for available register correlations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "When multiple registers in a bank are available at prediction time, random_select picks one available register to update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training meth
... [truncated]

[Usage]
{"input_tokens": 30211, "output_tokens": 33944, "thinking_tokens": 29640, "cache_read_tokens": 0, "total_tokens": 64155}

[Result]
status=SUCCESS conversation=29a8ab56-40c6-42fc-b1e7-f71978d046ec turns=1 duration=178.997268768s usage={"input_tokens": 30211, "output_tokens": 33944, "thinking_tokens": 29640, "cache_read_tokens": 0, "total_tokens": 64155}


