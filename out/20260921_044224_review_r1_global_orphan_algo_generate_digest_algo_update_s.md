success: True
usage: {'input_tokens': 34870, 'output_tokens': 39647, 'thinking_tokens': 34294, 'cache_read_tokens': 0, 'total_tokens': 74517}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR feature captures correlations between register values and branch outcomes without explicitly tracking dataflow dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper explicitly states that the register components capture correlations without tracking register dependencies."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Digest values expire after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text confirms the 256-instruction invalidation threshold for digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature is sourced from the paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The quote confirms the exact title of the publication."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At instruction decode, an instruction writing a register allocates an entry in the tracking table with its ROB index tag and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly details this notification and operation at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At instruction completion, the payload is overwritten with the produced value's digest and the valid bit is set.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the completion-time interface and update behavior."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host provides squash recovery notification to restore or clear in-flight RTT entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the Register Tracking Table recover or invalidate pending entries upon a pipeline squash or branch misprediction?",
      "enum_candidates": [
        "clear_flushed_tags",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total storage of the sR component is 53,863 bits (WT: 43,008 bits, UT: 9,360 bits, RTT: 1,495 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact formula and total storage bits for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default weight bit-width for prediction and usefulness weight tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights for the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The hash function used to index WT and UT tables from PC and register digest is specified in the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "What hash function is used to index WT and UT tables from PC and register digest?",
      "enum_candidates": [
        "xor_fold",
        "crc_hash",
        "prime_mult"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "Digest generation occurs at instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that payload overwrite with the digest occurs at completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The pipeline squash recovery policy for the RTT is specified in the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Which pipeline squash recovery policy is used to clear flushed instructions from the RTT?",
      "enum_candidates": [
        "clear_flushed_tags",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Flag registers produce a 12-bit digest by replicating the four flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states the 3x replication of the 4 flag bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Integer register count encoding for leading and trailing zeros/ones saturates at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "How are 64-bit leading and trailing zero/one counts encoded into the 6-bit count fields in Figure 6(a) when count exceeds 63 or spans 0..64?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Floating-point register digest bits are right-aligned at digest bit 3 leaving bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Are floating-point register digest bits right-aligned at bit 3 or bit 0 in the 12-bit digest?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table has 65 entries corresponding to 65 logical registers across 8 banks, with each entry storing valid (1), payload (14), and decay_ctr (8).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure and 65-entry count."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default number of logical registers tracked by sR is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sizes the Usefulness Table across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The 12-bit digest is right-justified within the 14-bit payload.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "How is the 12-bit completed digest positioned within the 14-bit RTT payload field?",
      "enum_candidates": [
        "right_justified",
        "left_justified",
        "zero_extended"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An all-zero 64-bit integer register saturates leading/trailing counts at 63 producing digest 0x1C7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Does an all-zero 64-bit integer register saturate leading/trailing counts at 63 or wrap modulo 64?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "An integer value of 8 produces digest 0x3E3 via XOR fold of trailing zeros (3), leading zeros (60), and LSBs (8).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Value 8 has counts 3 and 60 that naturally fit within 6 bits, matching the XOR fold formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A FLAG register with value 0b1011 generates digest 0xBBB by replicating the 4 bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 0b1011 three times produces 0xBBB exactly as tested."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "An FP32 value with bits [31:26]=16 is shifted by 3 bits to produce digest 128 (0x080).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Are FP32 extracted bits [31:26] positioned at digest bits [8:3] (aligned at bit 3) or at [5:0] (aligned at bit 0)?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An RTT entry expires and is marked invalid after 256 consecutive decoded instructions without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper defines exact expiration after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When best usefulness is non-positive, the bank multiplier selects x0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Does the bank multiplier select x0 vs x2.5 based on per-bank usefulness sign or a global SC condition?",
      "enum_candidates": [
        "per_bank_usefulness_gating",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When best usefulness is positive, the bank multiplier scales the WT sum by 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "Is the x2.5 scaling factor selected per bank based on positive usefulness or applied globally?",
      "enum_candidates": [
        "per_bank_usefulness_scaling",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "If multiple registers are available in a bank during update, exactly one is randomly chosen to maintain a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper directly describes random selection among available registers to preserve the single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "During update_sr training, if multiple registers were available in a bank, one is randomly selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly specifies this random selection rule during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Usefulness Table weights are trained by incrementing when the register prediction matches the outcome and decrementing otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "open_question": "What training algorithm updates the Usefulness Tables (UT) weights upon branch resolution?",
      "enum_candidates": [
        "direction_match",
        "sc_correction_help",
        "no_ut_update"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness Tables comprise 3 tables per bank across 8 banks with 8 entries each, storing 6-bit signed weights per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the 3 tables of 2^3 entries with 6-bit weights for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction Weight Table WT0 contains 512 entries per bank with 6-bit signed weights across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the 2^9 (512) entry dimension with 6-bit weights across 8 banks for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "Prediction Weight Table WT1 contains 256 entries per bank with 6-bit signed weights across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the 2^8 (256) entry dimension with 6-bit weights across 8 banks for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "Prediction Weight Table WT2 contains 128 entries per bank with 6-bit signed weights across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the 2^7 (128) entry dimension with 6-bit weights across 8 banks for WT2."
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
        "why": "Section 4.2 explicitly specifies that the component is organized into 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of entries in WT0 is 512 per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 2^9 (512) entries for the largest WT table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default number of entries in WT1 is 256 per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 2^8 (256) entries for the medium WT table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default number of entries in WT2 is 128 per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 2^7 (128) entries for the smallest WT table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default number of entries per Usefulness Table is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries for each of the three UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default decay threshold for digest invalidation is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 subsequent instructions have been decoded."
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
        "why": "Figure 5(c) transcription confirms the multiplier stage is labelled x0 or x2.5."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+orphan+algo:generate_digest+algo:update_sr` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=bb2f6328-a7c5-4632-8e6a-365bc3264226 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR feature captures correlations between register values and branch outcomes without explicitly tracking dataflow dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper explicitly states that the register components capture correlations without tracking register dependencies."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Digest values expire after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text confirms the 256-instruction invalidation threshold for digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature is sourced from the paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The quote confirms the exact title of the publication."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At instruction decode, an instruction writing a register allocates an entry in the tracking table with its ROB index tag and clears the valid bit.",
      "verdict": "SUPPORTED",
 
... [truncated]

[Usage]
{"input_tokens": 34870, "output_tokens": 39647, "thinking_tokens": 34294, "cache_read_tokens": 0, "total_tokens": 74517}

[Result]
status=SUCCESS conversation=bb2f6328-a7c5-4632-8e6a-365bc3264226 turns=1 duration=210.570634715s usage={"input_tokens": 34870, "output_tokens": 39647, "thinking_tokens": 34294, "cache_read_tokens": 0, "total_tokens": 74517}


