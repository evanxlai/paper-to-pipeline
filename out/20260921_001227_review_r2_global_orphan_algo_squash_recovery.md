success: True
usage: {'input_tokens': 29426, 'output_tokens': 28987, 'thinking_tokens': 24022, 'cache_read_tokens': 0, 'total_tokens': 58413}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component integrates into the statistical corrector of TAGE-SC-L to exploit correlations between recent register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The quote directly confirms that sR exploits correlations between register value digests and branch directions within the SC of TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Register values are compressed into 12-bit digests and validity is tracked in a dedicated table with instruction-age decay invalidation after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The passage states verbatim that register digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR mechanism is especially effective immediately following branch mispredictions / pipeline squashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "While the register value components can contribute to prediction accuracy when the instructions that generate register values are sufficiently distant, they are particularly effective immediately after a branch misprediction.",
        "why": "The quote directly confirms that sR provides special utility immediately following a branch misprediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The citation and title identify RUNLTS published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The quote establishes the authors, paper title, and CBP 2025 conference proceedings citation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Instruction decode/dispatch must record destination register index and allocated ROB index into the tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The quote establishes that decode logic stores the ROB index as a tag and clears the valid bit for the destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Functional execution completion writes back the value digest and sets the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The quote establishes that completion overwrites the payload with the produced value's digest and marks the entry valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "A decoded instruction count pulse/tick advances the age decay tracking.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote establishes that tracking table entries expire after 256 decoded instructions, requiring decoded instruction counting."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host supplies a pipeline flush notification specifying a squashed ROB index range to selectively clear invalid pending entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the host interface provide an explicit squashed ROB index range or mask to clear in-flight tracking entries on a pipeline flush, or does the predictor flash-invalidate invalid entries or perform no recovery?",
      "enum_candidates": [
        "rob_mask_clear",
        "flash_clear",
        "no_recovery"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component consumes 53,863 bits of total storage comprising 43,008 WT bits, 9,360 UT bits, and 1,495 auxiliary tracking bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact bit budgets: WT (43,008 bits), UT (9,360 bits), auxiliary tracking data (1,495 bits), and row total 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default weight width for sR prediction and usefulness tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies a 6-bit weight width across all WT and UT tables of sR; the unreferenced_param warning is refuted because weight_width defines table entry sizing and storage accounting rather than squash recovery execution logic."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "SC training update occurs at branch instruction commit.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does SC training update occur at branch commit or at execution resolution?",
      "enum_candidates": [
        "at_commit",
        "at_resolution"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "SC training update condition uses pred_sign_eq_taken as the default trigger variant.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Under what condition are sR weight tables updated during training?",
      "enum_candidates": [
        "pred_sign_eq_taken",
        "corrects_tage",
        "tage_mispred_only"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "Squash recovery policy defaults to clear_flushed with alternatives no_recovery and flash_invalidate.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which recovery policy should be applied to reg_tracking_table on a pipeline flush?",
      "enum_candidates": [
        "clear_flushed",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "Integer register digest zero/one counter overflow handling defaults to saturation.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "When counting 64 identical bits for an integer register value, does the 6-bit counter saturate at 63 or wrap modulo 64?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "Floating-point register format classification defaults to NaN-boxing inspection.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are FP operand widths (FP16, FP32, FP64) distinguished from 64-bit register values when generating digests?",
      "enum_candidates": [
        "nan_boxing",
        "host_type_tag"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "Secondary squash recovery parameter selects among rob_mask_clear, flash_clear, and no_recovery.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What mechanism clears in-flight speculative entries upon a pipeline squash redirect?",
      "enum_candidates": [
        "rob_mask_clear",
        "flash_clear",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/6",
      "claim": "Squash recovery is triggered upon pipeline squash or branch misprediction redirect.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "While the register value components can contribute to prediction accuracy when the instructions that generate register values are sufficiently distant, they are particularly effective immediately after a branch misprediction.",
        "why": "The quote establishes that misprediction events and the post-flush restart are the operational trigger points for utilizing and managing register digest availability."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6",
      "claim": "Squash recovery iterates through all 65 register entries and clears invalid entries matching flushed ROB tags using flushed_rob_mask.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should squashed in-flight register entries be invalidated in the Tomasulo-like tracking table given that Section 5 defers table recovery to future work?",
      "enum_candidates": [
        "rob_mask_clear",
        "flash_clear",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/6",
      "claim": "Valid digests from instructions that completed before a misprediction squash remain valid across the pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The passage confirms that instructions finished prior to branch resolution enlarge the set of valid values visible when fetch restarts."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table contains 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates tracking state for 65 entries corresponding to logical registers R0 through R64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Each tracking entry format consists of a 1-bit valid bit, a 14-bit payload holding a ROB tag or digest, and an 8-bit decay counter, totalling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The quote settles the exact bit widths of valid (1 bit) and payload (14-bit tag or 12-bit digest), and Table 3 confirms decay_ctr is 8 bits (23 bits x 65 = 1,495 bits total)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Prediction weight table WT0 contains 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) and Table 3 specify 512 (2^9) entries for WT0 in each of the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Prediction weight table WT1 contains 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) and Table 3 specify 256 (2^8) entries for WT1 in each of the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Prediction weight table WT2 contains 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) and Table 3 specify 128 (2^7) entries for WT2 in each of the 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Usefulness weight tables UT0, UT1, and UT2 have 8 entries per subtable.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies three 8-entry (2^3) usefulness weight tables per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The instruction decay threshold for invalidating stale digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The quote settles that the default age limit for digest invalidation is 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest folds trailing count, leading count shifted by 3, and value LSBs shifted by 6 with XOR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The quote together with Figure 6(a) confirms the 12-bit digest format XOR-combining trailing count [5:0], leading count [8:3], and Value[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 register digest extracts sign and high-order exponent bits from Value[63:55] placed at digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The quote and Figure 6(b) confirm extracting Value[63:55] covering the sign and high exponent bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag register digest replicates 4 condition code bits three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The quote establishes that the 4 condition-code bits are replicated 3 times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Tracking entry decay counter triggers invalidation when age reaches 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The passage confirms that entries transition from valid to invalid upon decoding 256 subsequent instructions without a write."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank selects the register with largest usefulness and scales WT sum by 2.5x when usefulness is positive, suppressing output to 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The quote confirms picking the most useful register digest, and Figure 5(c) confirms the 'largest' block and 'x0 or x2.5' multiplier stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed register values retain valid digests across misprediction squashes to aid immediate post-flush branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The quote establishes that instructions completing before branch resolution keep their produced values available to accelerate post-flush branch predictions."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+orphan+algo:squash_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never ...

[Init]
model=gemini-3.8-flash-medium conversation=09bd8631-3966-48e7-abb6-92a40837e2ab cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component integrates into the statistical corrector of TAGE-SC-L to exploit correlations between recent register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2). Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "The quote directly confirms that sR exploits correlations between register value digests and branch directions within the SC of TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Register values are compressed into 12-bit digests and validity is tracked in a dedicated table with instruction-age decay invalidation after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The passage states verbatim that register digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR mechanism is especially effective immediately following branch mispredictions / pipeline squashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "While the register value components can contribute to prediction accuracy when the instructions that generate register valu
... [truncated]

[Usage]
{"input_tokens": 29426, "output_tokens": 28987, "thinking_tokens": 24022, "cache_read_tokens": 0, "total_tokens": 58413}

[Result]
status=SUCCESS conversation=09bd8631-3966-48e7-abb6-92a40837e2ab turns=1 duration=145.374038212s usage={"input_tokens": 29426, "output_tokens": 28987, "thinking_tokens": 24022, "cache_read_tokens": 0, "total_tokens": 58413}


