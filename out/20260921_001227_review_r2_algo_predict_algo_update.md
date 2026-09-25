success: True
usage: {'input_tokens': 31749, 'output_tokens': 43290, 'thinking_tokens': 38776, 'cache_read_tokens': 0, 'total_tokens': 75039}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4",
      "claim": "Predictor query occurs during lookup time for conditional branches, querying the tracking table for valid digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that during predictor queries, valid register entries forward their digests to the SC register components for prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Register components are partitioned into 8 banks, with logical registers partitioned modulo 8 such that Bank 0 holds 9 registers (R0..R64) and Banks 1-7 hold 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states that the register component has eight banks, each corresponding to eight or nine logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Usefulness tables (UT) consist of three direct-mapped subtables of 8 entries per bank indexed by skewed PC, storing a vector of weights per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper confirms that each entry in the usefulness table contains a vector of weights corresponding to each register in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The bank selects the register digest exhibiting the maximum usefulness sum across the three UT subtables among available valid registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies that the component selects the most useful register digest among those currently available to forward to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The selected register digest is indexed into three prediction weight tables (WT0 of 512 entries, WT1 of 256 entries, WT2 of 128 entries) per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) confirms each bank uses three prediction weight tables with capacities 512, 256, and 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Each bank scales its WT prediction weight sum by 2.5 if usefulness is positive, and gates it to 0 if not useful.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) documents that the bank weight summation node feeds a per-bank scaling stage that applies x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "The partial sums from all eight banks are summed together to produce the final sR contribution to LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "Figure 5(c) depicts the summation of outputs from all eight banks producing the aggregate sR output."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Specific bit-skewing and hashing algorithms (hash_pc and hash_wt) mapping PC and register digest to UT and WT indices are specified.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies the table dimensions and indexing inputs (PC and 12-bit digest) but omits the exact bitwise hash functions for hash_pc and hash_wt.",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "prime_modulo"
      ]
    },
    {
      "pointer": "/algorithms/5",
      "claim": "The register component trains only on logical registers that were available at prediction time, randomly sampling one register if multiple candidates exist in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The text directly states the training condition and the random single-register selection policy per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Due to random single-register sampling per bank, each table in the register component requires only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly ties the single-register update sampling to the single write port implementation requirement."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Prediction weight tables (WT) are trained using signed 6-bit saturating counter increments or decrements towards the branch outcome within [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry width as 6 bits across all WT subtables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Usefulness table (UT) weights are trained by incrementing when the bank prediction matches the branch direction and decrementing otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that UT tracks prediction usefulness but does not define the exact update rule or delta condition for usefulness counters.",
      "enum_candidates": [
        "pred_correct",
        "tage_mispredicted",
        "sc_disagreed"
      ]
    },
    {
      "pointer": "/algorithms/5",
      "claim": "The register digest used during update training is re-read directly from the tracking table at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies training uses register values available at prediction time, but does not state whether the 12-bit digest is checkpointed in the branch state or re-read from the tracking table at commit.",
      "enum_candidates": [
        "checkpoint_digest",
        "reread_table"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT contains 8 banks, each with 3 direct-mapped subtables (512, 256, 128 entries), totalling 7,168 entries of 6-bit signed counters for 43,008 bits total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the exact entry structure and storage calculation (43,008 bits) for the sR Prediction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT contains 8 banks of 3 direct-mapped subtables of 8 entries each, with Bank 0 storing 9 x 6-bit weights and Banks 1-7 storing 8 x 6-bit weights, totalling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 details the usefulness weight table storage as 6 bits for 65 registers across three 8-entry tables, summing to 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "reg_tracking_table contains 65 entries, each consisting of a 1-bit valid flag, 14-bit payload, and 8-bit decay counter, totalling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms the exact bit breakdown and count for the auxiliary register tracking data."
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
        "why": "The paper explicitly specifies eight banks for the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of entries for WT0 is 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT0 as 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default number of entries for WT1 is 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT1 as 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default number of entries for WT2 is 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly labels WT2 as 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default number of entries per UT subtable is 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly labels UT0, UT1, and UT2 as 8-entry tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default scaling factor for useful register component predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies a 2.5 multiplier for the active output of the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The total number of tracked logical registers is 65 (R0 through R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 establishes that 65 logical registers are tracked in the usefulness tables and tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding trailing zero/one count (bits 5:0), leading zero/one count (bits 8:3), and register value[5:0] (bits 11:6).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper and Figure 6(a) specify the exact 12-bit XOR-folded digest representation for integer registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 register digests extract Value[63:55] placed at digest bits [11:3], leaving bits [2:0] unused.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper and Figure 6(b) confirm extracting the sign and top exponent bits (Value[63:55]) for 64-bit floating point registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition-code flag register digests replicate the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The text directly states that condition flag bits are replicated three times to create the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated when 256 instructions have decoded without an update writing to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states the 256-instruction decay invalidation policy for valid register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank selection picks the maximum usefulness register, scaling the WT prediction by 2.5 if usefulness > 0 and gating to 0 if usefulness <= 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) define selecting the most useful register and gating via x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Valid digests in the tracking table persist across branch misprediction squashes, allowing post-flush branches to exploit completed instruction values.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper confirms that completed instruction values enlarge the set of valid digests retained after a pipeline squash."
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
model=gemini-3.8-flash-medium conversation=f13b13b0-fb91-4336-b3d3-6d2ca599f9ef cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4",
      "claim": "Predictor query occurs during lookup time for conditional branches, querying the tracking table for valid digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that during predictor queries, valid register entries forward their digests to the SC register components for prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Register components are partitioned into 8 banks, with logical registers partitioned modulo 8 such that Bank 0 holds 9 registers (R0..R64) and Banks 1-7 hold 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states that the register component has eight banks, each corresponding to eight or nine logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "Usefulness tables (UT) consist of three direct-mapped subtables of 8 entries per bank indexed by skewed PC, storing a vector of weights per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper confirms that each entry in the usefulness table contains a vector of weights corresponding to each register in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer
... [truncated]

[Usage]
{"input_tokens": 31749, "output_tokens": 43290, "thinking_tokens": 38776, "cache_read_tokens": 0, "total_tokens": 75039}

[Result]
status=SUCCESS conversation=f13b13b0-fb91-4336-b3d3-6d2ca599f9ef turns=1 duration=221.513212179s usage={"input_tokens": 31749, "output_tokens": 43290, "thinking_tokens": 38776, "cache_read_tokens": 0, "total_tokens": 75039}


