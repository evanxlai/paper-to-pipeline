success: True
usage: {'input_tokens': 33988, 'output_tokens': 31913, 'thinking_tokens': 26554, 'cache_read_tokens': 0, 'total_tokens': 65901}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The prediction weight tables and usefulness weight tables use 6-bit counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 6-bit weights for all WT and UT tables in the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sr feature integrates into the statistical corrector of TAGE-SC-L to capture correlations between register values and branch directions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes. The components use digests of currently available register values as their input.",
        "why": "Section 4.2 explicitly describes extending the SC with components correlating register values to branch outcomes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The specification models the RUNLTS register-value-aware predictor published in CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the publication name in the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "At decode of an instruction writing an architectural register, the predictor records the ROB index as a tag and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 states that instructions writing a register store their ROB index as a tag at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "When an instruction completes execution, the predictor overwrites the RTT payload with the value digest and sets the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 details that instruction completion updates the payload with the digest and sets the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "The host provides decoded instruction count progression to invalidate RTT digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 confirms valid digests expire after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "The host supplies flushed ROB tags on pipeline squashes to invalidate stale pending reservations in RTT.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should RTT in-flight reservations be recovered or invalidated on a misprediction squash given Section 5 leaves Tomasulo-table recovery as future work?",
      "enum_candidates": [
        "tag_match_invalidate",
        "invalidate_all_pending",
        "no_rollback"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total storage budget for the sR component is 53,863 bits (43,008 bits WT, 9,360 bits UT, 1,495 bits RTT).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact bit formula and 53,863 bit total for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flags, the 4-bit flag value is replicated three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly defines replicating the 4 flag bits three times for FLAG digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, leading and trailing bit counts saturate at 63 to fit within 6-bit fields.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U3, how are 0..64 identical leading or trailing bits encoded into 6 bits, and how are zeros vs ones distinguished?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digests are right-aligned at digest bit 3 leaving bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U4, is the FP slice placed at digest[8:3] with [2:0] zeroed, or right-aligned at digest[5:0]?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The RTT consists of 65 entries storing valid (1 bit), payload (14 bits), and decay_ctr (8 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 auxiliary data specifies { valid (1), payload (14), decay_ctr (8) } x 65 for RTT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The predictor tracks 65 logical registers across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the component tracks eight or nine registers per bank across eight banks (8*7 + 9 = 65)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An INT value of 0 produces leading and trailing bit counts saturated at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U3, does an all-zero 64-bit value saturate leading/trailing counts at 63 or wrap modulo 64 to 0?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "An INT register with value 8 produces digest 0x3E3 via XOR folding of trailing count, leading count, and value LSBs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "bit 5 |  trailing one/zero #   | bit 0",
        "why": "Figure 6(a) LITERAL specifies XOR folding of trailing [5:0], leading [8:3], and value LSBs [11:6], evaluating to 3 ^ (60 << 3) ^ (8 << 6) = 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A FLAG register with value 0b1011 produces 0xBBB by replicating the 4 bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 establishes 3-fold replication of 4 flag bits yielding 0xBBB for input 11."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "An FP32 value places Val[31:26] at digest[8:3] with digest[2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U4, does FP32 extraction align at bit 3 leaving bits [2:0] zeroed, or right-align at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An RTT entry expires and clears valid after 256 consecutive instructions without update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 specifies that digests invalidate after 256 subsequent instructions are decoded."
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
      "open_question": "Per ambiguity U2, is the bank multiplier x0 vs x2.5 driven dynamically per bank by the sign of best_usefulness or statically globally?",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank with positive usefulness selects multiplier x2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U2, is the x2.5 multiplier driven by bank usefulness being positive or a global scale?",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers are valid in a bank during update, one is chosen at random.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 states that training randomly selects one available register per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The predictor selects the most useful valid register in each bank using the sum of UT0, UT1, and UT2 weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 describes selecting the most useful available register in each bank to forward to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The bank sum multiplier selects x2.5 if best_usefulness > 0 and x0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per ambiguity U2, what signal drives the x0 vs x2.5 multiplier selection for each bank?",
      "enum_candidates": [
        "bank_usefulness",
        "static_scale"
      ]
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness tables have 8 entries per bank across 3 tables storing 6-bit weights for all registers in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) LITERAL specifies 8-entry tables UT0, UT1, and UT2 with 6-bit weights per register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction table WT0 has 8 banks of 512 entries storing 6-bit signed weights totaling 24,576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 allocates 6 bits x 2^9 entries x 8 banks = 24,576 bits for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "Prediction table WT1 has 8 banks of 256 entries storing 6-bit signed weights totaling 12,288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 allocates 6 bits x 2^8 entries x 8 banks = 12,288 bits for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "Prediction table WT2 has 8 banks of 128 entries storing 6-bit signed weights totaling 6,144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 allocates 6 bits x 2^7 entries x 8 banks = 6,144 bits for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component uses 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Table WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 2^9 (512) entries per bank for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Table WT1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 2^8 (256) entries per bank for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Table WT2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 2^7 (128) entries per bank for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each usefulness table has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) LITERAL specifies 8 entries each for UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The bank scaling factor applied to useful predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) LITERAL explicitly labels the multiplier stage as x0 or x2.5."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+global+algo:generate_digest+algo:predict_sr` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec al...

[Init]
model=gemini-3.8-flash-medium conversation=95ff9b0e-ac4f-4e65-b799-51dcd78ff02f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The prediction weight tables and usefulness weight tables use 6-bit counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 6-bit weights for all WT and UT tables in the register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sr feature integrates into the statistical corrector of TAGE-SC-L to capture correlations between register values and branch directions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes. The components use digests of currently available register values as their input.",
        "why": "Section 4.2 explicitly describes extending the SC with components correlating register values to branch outcomes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The specification models the RUNLTS register-value-aware predictor published in CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the publication name in the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "At decode of an instruction writing an architectural register, the predictor records the ROB index as a tag and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At deco
... [truncated]

[Usage]
{"input_tokens": 33988, "output_tokens": 31913, "thinking_tokens": 26554, "cache_read_tokens": 0, "total_tokens": 65901}

[Result]
status=SUCCESS conversation=95ff9b0e-ac4f-4e65-b799-51dcd78ff02f turns=1 duration=166.714700566s usage={"input_tokens": 33988, "output_tokens": 31913, "thinking_tokens": 26554, "cache_read_tokens": 0, "total_tokens": 65901}


