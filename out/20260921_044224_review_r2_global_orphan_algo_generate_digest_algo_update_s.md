success: True
usage: {'input_tokens': 34858, 'output_tokens': 37332, 'thinking_tokens': 31856, 'cache_read_tokens': 0, 'total_tokens': 72190}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component is a register-value-aware statistical corrector component that captures correlations between recently computed register values and conditional branch directions without explicitly tracking dataflow dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper explicitly states that the register components utilize recently produced register values without explicitly tracking dependencies to capture correlations with branch outcomes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The citation correctly references the CBP 2025 paper describing RUNLTS.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the publication title verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host interface notifies the predictor at instruction decode when an instruction writes an architectural register, supplying the logical register ID and ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that instructions writing registers record their ROB index as a tag at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host interface notifies the predictor at instruction completion with the produced register value and sets entry validity.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that on instruction completion the payload receives the digest and the valid bit is set."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host interface provides pipeline squash notification allowing RTT to recover entries on branch mispredictions.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the Register Tracking Table (RTT) recovered or flushed on a pipeline squash?",
      "enum_candidates": [
        "clear_flushed_tags",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage budget consumed by the sR component across WT, UT, and RTT is 53,863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in Appendix A explicitly itemizes the storage formula and confirms a total of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Weight counters in WT and UT use 6-bit precision.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the weight width as 6 bits for both WT and UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The indexing function for WT and UT hashes PC and register digests into table indices.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash function algorithm is used to hash PC, table ID, bank ID, and register digest into table indices?",
      "enum_candidates": [
        "xor_fold",
        "crc_hash",
        "prime_mult"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "The RTT tag is allocated at instruction decode time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies tag allocation at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "RTT recovery behavior on pipeline squashes.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does RTT handle in-flight tags when a pipeline squash occurs?",
      "enum_candidates": [
        "clear_flushed_tags",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation is triggered at execution/completion time of an instruction producing a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies completion time as the point where the digest is produced and written to payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Integer digest encoding saturates 0..64 leading/trailing bit counts to 6 bits (0..63).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 0..64 leading and trailing identical bits encoded into 6-bit count fields in Figure 6(a), and how are zeros vs ones distinguished?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Floating-point digest fields are right-aligned at digest bit 3 leaving bits 2:0 zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are extracted floating-point format fields right-aligned at digest bit 3 or right-aligned at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Condition-code flag register digest replicates the 4 flag bits three times to fill 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 4 condition-code flag bits are replicated three times to create the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table contains 65 entries, each with a 1-bit valid flag, 14-bit payload, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 states each entry contains a valid bit and 14-bit payload, and Table 3 confirms { valid (1), payload (14), decay_ctr (8) } x 65."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The sR component tracks 65 logical registers partitioned into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies 8 banks of 8 or 9 registers, and Table 3 explicitly uses 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The 12-bit digest is right-justified within the 14-bit RTT payload field.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 12-bit digest aligned within the 14-bit RTT payload entry?",
      "enum_candidates": [
        "right_justified",
        "left_justified",
        "zero_extended"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation for 64 zeros saturates leading and trailing zero counts at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the integer digest generator encode count values when a register contains all zeros or all ones?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer digest generation for value 8 tests leading zeros=60, trailing zeros=3, and LSB=8.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the integer count field encode trailing/leading zeros specifically, or identical bits matching LSB/MSB?",
      "enum_candidates": [
        "match_edge_bit",
        "count_zeros_only",
        "separate_zero_one_bit"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag digest generation replicates 4 condition-code bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "FP32 digest generation places extracted bits at digest[8:3] leaving digest[2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the FP32 sign and exponent field right-aligned at digest bit 3 or at digest bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "RTT entries expire and are invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests expire after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Bank prediction output is suppressed by selecting multiplier x0 when best usefulness is non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What condition on bank usefulness selects multiplier x0 versus x2.5?",
      "enum_candidates": [
        "usefulness_positive",
        "usefulness_nonnegative",
        "static_scaling"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Bank prediction output is scaled by x2.5 when best usefulness is positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What threshold determines whether the bank's usefulness triggers the x2.5 scaling factor?",
      "enum_candidates": [
        "usefulness_positive",
        "usefulness_nonnegative",
        "static_scaling"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple valid registers exist in a bank, exactly one is randomly chosen for update during training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that when multiple registers are available in a bank, one is randomly chosen for update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "During training, sR correlations are updated only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly specifies this training constraint."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Each bank randomly selects at most one available register for update, requiring only a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper confirms random single-register selection per bank to guarantee a single write port per table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5",
      "claim": "Usefulness tables are updated with +1 if the register prediction matched the actual branch direction and -1 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training condition and delta are used to update usefulness weights in the UT tables?",
      "enum_candidates": [
        "reg_pred_matches_outcome",
        "sc_correct_with_reg",
        "tage_mispred_only"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "UT consists of 3 tables per bank across 8 banks, each containing 8 entries storing 6-bit weights for each register in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 specify 3 tables of 8 entries each per bank, with 6-bit weights for all registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "WT0 has 8 banks of 512 entries storing 6-bit signed weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\"",
        "why": "Figure 5(c) and Table 3 define WT0 with 512 (2^9) entries and 6-bit weights per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "WT1 has 8 banks of 256 entries storing 6-bit signed weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\"",
        "why": "Figure 5(c) and Table 3 define WT1 with 256 (2^8) entries and 6-bit weights per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "WT2 has 8 banks of 128 entries storing 6-bit signed weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"128 ent. WT2\"",
        "why": "Figure 5(c) labels WT2 with 128 entries and Table 3 confirms 2^7 entries per bank with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The sR component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly specifies eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\"",
        "why": "Figure 5(c) labels WT0 as 512 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\"",
        "why": "Figure 5(c) labels WT1 as 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"128 ent. WT2\"",
        "why": "Figure 5(c) labels WT2 as 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each UT table contains 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly labels UT0, UT1, and UT2 with 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The decay threshold for register digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly defines the digest expiration threshold as 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The usefulness multiplier scale factor for bank predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "Figure 5(c) explicitly labels the bank multiplier with scale factor x2.5."
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
model=gemini-3.8-flash-medium conversation=6caff04c-ee98-4abd-82d9-235922f2aa2b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component is a register-value-aware statistical corrector component that captures correlations between recently computed register values and conditional branch directions without explicitly tracking dataflow dependencies.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper explicitly states that the register components utilize recently produced register values without explicitly tracking dependencies to capture correlations with branch outcomes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The citation correctly references the CBP 2025 paper describing RUNLTS.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the publication title verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host interface notifies the predictor at instruction decode when an instruction writes an architectural register, supplying the logical register ID and ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that instructions writing registers record their ROB index as a tag at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
   
... [truncated]

[Usage]
{"input_tokens": 34858, "output_tokens": 37332, "thinking_tokens": 31856, "cache_read_tokens": 0, "total_tokens": 72190}

[Result]
status=SUCCESS conversation=6caff04c-ee98-4abd-82d9-235922f2aa2b turns=1 duration=182.62556658s usage={"input_tokens": 34858, "output_tokens": 37332, "thinking_tokens": 31856, "cache_read_tokens": 0, "total_tokens": 72190}


