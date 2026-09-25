success: True
usage: {'input_tokens': 30542, 'output_tokens': 27064, 'thinking_tokens': 21733, 'cache_read_tokens': 0, 'total_tokens': 57606}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR component is queried at fetch lookup time whenever the branch predictor queries the table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that the register component in the SC is queried for prediction whenever the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The sR prediction lookup iterates over 8 banks corresponding to eight or nine logical registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper directly specifies that the register component is organized into eight banks covering 8 or 9 registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "At lookup time, only registers with valid digests in the RTT participate in bank usefulness evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that only entries with set valid bits forward digests to the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "For each bank, usefulness weights from UT0, UT1, and UT2 are summed per available register to select the most useful register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) shows each bank sums three usefulness tables (UT0, UT1, UT2) to determine register usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Each bank selects the register with the highest usefulness to forward its digest to the prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states that the digest of the most useful available register in the bank is picked and forwarded to the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The selected register's digest and PC index three prediction weight tables (WT0, WT1, WT2) whose outputs are summed per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",",
        "why": "Figure 5(c) shows that the PC and selected register digest index WT0, WT1, and WT2, which are then summed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Each bank's sum is dynamically scaled by x2.5 if its best usefulness is positive, and suppressed (x0) otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) note U2 leaves the driving signal for the x0 versus x2.5 multiplier unlabelled, making it ambiguous whether scaling is dynamically selected per bank by usefulness or applied statically.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The scaled contributions of all 8 banks are summed together to produce the overall sR prediction sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "Figure 5(c) indicates that all eight bank outputs feed a final summation block that produces sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Bank scaling x2.5 versus x0 is driven per bank by best_usefulness > 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U2 in the source declares the wire controlling the x0 vs x2.5 multiplier uncertain, leaving whether it is driven by bank usefulness or global scaling unresolved.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The RTT contains 65 entries corresponding to 65 logical registers (R0..R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper defines the tracking table as having one entry per logical register, matching the 65 registers given in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each RTT entry consists of 1 valid bit, a 14-bit payload holding either an ROB tag or digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly lists the format as valid (1), payload (14), and decay_ctr (8) per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The RTT consumes 1495 bits of storage total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry equals 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT consists of 3 tables per bank across 8 banks with 8 entries each, storing 6-bit signed usefulness weights per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 specify three 8-entry tables per bank storing 6-bit weights for each register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT consumes 9360 bits across all banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the UT storage formula as 6 bits x 65 registers x 24 sets = 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT entries are indexed by skewed PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "Figure 5(c) shows the usefulness tables indexed by skewed PC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT0 comprises 8 banks of 512 entries storing 6-bit signed weights totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"512 ent. WT0\"",
        "why": "Figure 5(c) specifies 512 entries for WT0 per bank, and Table 3 confirms 6-bit weights across 8 banks (8 * 512 * 6 = 24576 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT0 is indexed using an XOR hash of PC, register digest, and bank ID.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The specific hash formulation combining PC, register digest, and bank ID for WT0 indexing is not defined in the paper.",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/state/3",
      "claim": "WT1 comprises 8 banks of 256 entries storing 6-bit signed weights totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"256 ent. WT1\"",
        "why": "Figure 5(c) specifies 256 entries for WT1 per bank, and Table 3 confirms 6-bit weights across 8 banks (8 * 256 * 6 = 12288 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "WT1 is indexed using an XOR hash of PC, register digest, and bank ID.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The specific hash formulation combining PC, register digest, and bank ID for WT1 indexing is not defined in the paper.",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/state/4",
      "claim": "WT2 comprises 8 banks of 128 entries storing 6-bit signed weights totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"128 ent. WT2\"",
        "why": "Figure 5(c) specifies 128 entries for WT2 per bank, and Table 3 confirms 6-bit weights across 8 banks (8 * 128 * 6 = 6144 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "WT2 is indexed using an XOR hash of PC, register digest, and bank ID.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The specific hash formulation combining PC, register digest, and bank ID for WT2 indexing is not defined in the paper.",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks in the sR component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states that the register component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of entries per bank in WT0 is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"512 ent. WT0\"",
        "why": "Figure 5(c) labels WT0 as having 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default number of entries per bank in WT1 is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"256 ent. WT1\"",
        "why": "Figure 5(c) labels WT1 as having 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default number of entries per bank in WT2 is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"128 ent. WT2\".",
        "why": "Figure 5(c) labels WT2 as having 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default number of entries per table in UT is 8.",
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
      "claim": "The scaling multiplier factor for useful bank predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly marks the non-zero scaling factor as x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The predictor tracks 65 logical registers across the banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the register count as 65 in the UT sizing expression."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/13",
      "claim": "The WT0 indexing hash function is an open parameter with variants including xor_hash and folded_hash.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the hash equation used for WT0 indexing.",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The WT1 indexing hash function is an open parameter with variants including xor_hash and folded_hash.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the hash equation used for WT1 indexing.",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register value of 0 saturates leading and trailing zero counts at 63 to produce digest 0x1C7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) note U3 states that count encoding for 64 identical bits is ambiguous between saturating at 63, taking modulo 64, or matching the sign bit.",
      "enum_candidates": [
        "saturate",
        "modulo_64",
        "sign_match"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "An integer register value of 8 produces digest 0x3E3 by XOR folding trailing zeros, leading zeros, and LSBs.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) note U3 notes that how zero versus one counts are distinguished or whether bits matching the MSB/LSB are counted is ambiguous.",
      "enum_candidates": [
        "sign_match",
        "separate_count"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A FLAG register digest replicates 4 condition-code bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper specifies that flag digests are formed by replicating the 4 condition-code bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "An FP32 register produces a digest by extracting bits [31:26] and right-aligning at digest bit 3.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) note U4 marks right-alignment at bit 3 rather than bit 0 as inferred from layout and not stated in text.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An RTT entry invalidates its digest after 256 subsequent decoded instructions without a rewrite.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states directly that digests expire and are invalidated after 256 subsequent instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank with non-positive usefulness selects multiplier x0 and contributes 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) note U2 leaves whether x0 vs x2.5 is driven dynamically per bank by bank usefulness or global scale unlabelled and uncertain.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank with positive usefulness selects multiplier x2.5 and contributes scaled bank sum to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) note U2 leaves whether x0 vs x2.5 is driven dynamically per bank by bank usefulness or global scale unlabelled and uncertain.",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers in a bank are valid at prediction time, one is randomly chosen for training update upon misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that one available register is randomly selected within the bank for update."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict_sr` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A c...

[Init]
model=gemini-3.8-flash-medium conversation=57dec894-8232-4090-b5a6-0747a496bf96 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR component is queried at fetch lookup time whenever the branch predictor queries the table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that the register component in the SC is queried for prediction whenever the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The sR prediction lookup iterates over 8 banks corresponding to eight or nine logical registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper directly specifies that the register component is organized into eight banks covering 8 or 9 registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "At lookup time, only registers with valid digests in the RTT participate in bank usefulness evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that only entries with set valid bits forward digests to the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "For each bank, usefulness weights from UT0, UT1, and UT2 are summed per available reg
... [truncated]

[Usage]
{"input_tokens": 30542, "output_tokens": 27064, "thinking_tokens": 21733, "cache_read_tokens": 0, "total_tokens": 57606}

[Result]
status=SUCCESS conversation=57dec894-8232-4090-b5a6-0747a496bf96 turns=1 duration=130.94941682s usage={"input_tokens": 30542, "output_tokens": 27064, "thinking_tokens": 21733, "cache_read_tokens": 0, "total_tokens": 57606}


