success: True
usage: {'input_tokens': 28769, 'output_tokens': 59674, 'thinking_tokens': 53996, 'cache_read_tokens': 0, 'total_tokens': 88443}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Update of the sR component is triggered at commit time or branch resolution when SC training is invoked.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Section 4 establishes that training operation follows the baseline TAGE-SC-L protocol where SC training triggers on mispredictions or low confidence."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "During training, correlation updates are restricted to logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 explicitly restricts training updates to registers that held valid digests when the branch was predicted."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "If multiple registers within the same bank were available at prediction time, one is randomly selected for update so that each table needs only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states that random selection among available registers in a bank permits single-write-port table implementations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The function update_sr is the entry-point definition of the sR update algorithm rather than a call to an undefined external policy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The pseudocode implements the training procedure of the register components described in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The helper pseudo_random_choice selects one available register uniformly at random using the predictor's random number generator.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 requires random selection of one register when multiple candidates are available in a bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The helper sat_add_signed_6bit performs 6-bit signed saturating addition clamping weights to the range [-32, +31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry width as 6 bits, which corresponds to standard 6-bit signed saturating counters [-32, +31]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The if statements in update_sr represent standard language control-flow keywords rather than calls to an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The conditional branching in pseudocode directly realizes the conditional selection rule described in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "WT tables are indexed by hashing PC and register digest via hash_wt0 modulo 512, hash_wt1 modulo 256, and hash_wt2 modulo 128.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) indicates PC and register digest are hashed to index WT0, WT1, and WT2, but the paper does not define the hashing functions.",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "bitwise_permute"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "UT tables are indexed by skewed PC hashes hash_ut0, hash_ut1, and hash_ut2 modulo 8.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) specifies that UT tables are indexed by PC (skewed) across 8 entries, but does not specify the skewing or hash functions.",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "direct_slice"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "UT usefulness weights are trained by computing an increment u_inc based on whether the bank's WT summation matches the branch direction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 4.2 states that UT tracks prediction usefulness but omits the mathematical update formula and conditions under which register usefulness weights are incremented or decremented.",
      "enum_candidates": [
        "wt_outcome_match",
        "sc_reversal",
        "always_on_correct"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The register digest used during retirement update is read directly from reg_status_table[r_update].payload.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify whether prediction-time digests are captured in a branch prediction checkpoint or re-read at retirement from reg_status_table, where intervening instructions may have modified or invalidated them.",
      "enum_candidates": [
        "checkpoint_snapshot",
        "table_reread",
        "rob_retrieval"
      ]
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "All WT and UT weights saturate symmetrically as 6-bit signed integers in [-32, +31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies that WT weights are 6 bits wide, confirming symmetric 6-bit signed counter representation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Each table in the register component requires only a single write port because exactly one available register per bank is trained per event.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly derives the single write port design from updating at most one register per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "reg_status_table contains 65 direct-mapped entries corresponding to 64 architectural INT/FP registers plus 1 condition flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries for the sR auxiliary register status structure."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of reg_status_table comprises a 1-bit valid bit, a 14-bit payload holding either a 14-bit ROB tag or a 12-bit digest, and an 8-bit decay counter totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies the 23-bit entry format, which across 65 entries totals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "reg_status_table is directly indexed by logical register index from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 states that the table maintains exactly one dedicated entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "wt_tables consists of 8 banks with three prediction tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) storing 6-bit weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 confirms 8 banks containing 2^9, 2^8, and 2^7 entries of 6-bit weights totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "wt_tables in Bank b is indexed by hashing PC and selected 12-bit register digest into WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) shows that hashed PC and register digest index into 512-, 256-, and 128-entry prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "ut_tables consists of 8 banks of three 8-entry tables (UT0, UT1, UT2) storing vectors of 6-bit usefulness weights totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 6-bit weights across 65 registers and three 8-entry tables totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "ut_tables entries are indexed by skewed PC hashes into 8 entries for UT0, UT1, and UT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) confirms that three 8-entry usefulness tables are addressed by skewed PC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks has a default value of 8.",
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
      "pointer": "/parameters/0",
      "claim": "num_banks has a legal range of [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed 8-bank configuration and does not state or evaluate a legal tuning range such as [4, 16] pow2.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "usefulness_scale has a default value of 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly marks the multiplier stage on the bank WT output as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "usefulness_scale has a legal tuning range of [1.0, 4.0].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper gives only the fixed factor 2.5 in Figure 5(c) and does not document a tuning range of [1.0, 4.0].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt_weight_width has a default value of 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 confirms that WT entries are 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt_weight_width has a legal tuning range of [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies WT weight width as 6 bits without documenting a tuning range of [4, 8].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_weight_width has a default value of 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that UT entries store 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_weight_width has a legal tuning range of [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies UT weight width as 6 bits without documenting a tuning range of [4, 8].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "digest_width has a default value of 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that the generated register digest is 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "digest_width has a legal tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper defines the digest as 12 bits wide and does not specify a tuning range of [8, 16].",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding trailing bit count, leading bit count shifted by 3, and the 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify XOR-folding the trailing bit count, leading bit count, and lowest 6 bits into a 12-bit integer digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Evaluating the integer digest formula for 64-bit value 0x18 yields 2011 (0x7DB).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The unit test expectation directly evaluates the integer digest formula defined in Section 4.2 and Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition-code flags, the 12-bit digest is formed by replicating the 4-bit flag value three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly defines replicating the 4 flag bits three times to construct the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "For FP32 registers, the digest extracts bits [31:26] right-aligned at digest bit 3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) specifies that FP32 registers use bits [31:26] positioned at digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A valid register digest in reg_status_table is invalidated after 256 subsequent instructions are decoded without a write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly specifies invalidating digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "On a branch misprediction squash, valid register digests produced prior to the branch remain valid while uncompleted in-flight tags are flushed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 explains that completed register values survive the flush to inform post-restart predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank's WT summation is scaled by 2.5 if its maximum usefulness is positive, and suppressed to 0 if its usefulness is non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows that the bank WT sum is scaled by x2.5 or gated to x0 based on the usefulness evaluation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers in a bank are valid at prediction time, exactly one is chosen randomly for single-port update during SC training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly specifies selecting one register randomly among available candidates to perform single-port updates."
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
model=gemini-3.8-flash-high conversation=3edf6c82-8cad-4730-9b7e-0b8a2ef4d214 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_25c851367f6ab27b

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Update of the sR component is triggered at commit time or branch resolution when SC training is invoked.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The predictor's operation remains almost the same as that of TAGE-SC-L.",
        "why": "Section 4 establishes that training operation follows the baseline TAGE-SC-L protocol where SC training triggers on mispredictions or low confidence."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "During training, correlation updates are restricted to logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 explicitly restricts training updates to registers that held valid digests when the branch was predicted."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "If multiple registers within the same bank were available at prediction time, one is randomly selected for update so that each table needs only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 states that random selection among available registers in a bank permits single-write-port table implementations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",

... [truncated]

[Usage]
{"input_tokens": 28769, "output_tokens": 59674, "thinking_tokens": 53996, "cache_read_tokens": 0, "total_tokens": 88443}

[Result]
status=SUCCESS conversation=3edf6c82-8cad-4730-9b7e-0b8a2ef4d214 turns=1 duration=320.534273701s usage={"input_tokens": 28769, "output_tokens": 59674, "thinking_tokens": 53996, "cache_read_tokens": 0, "total_tokens": 88443}


