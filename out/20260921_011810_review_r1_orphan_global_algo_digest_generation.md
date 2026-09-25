success: True
usage: {'input_tokens': 29157, 'output_tokens': 28499, 'thinking_tokens': 24367, 'cache_read_tokens': 0, 'total_tokens': 57656}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The default weight bitwidth for sR prediction weight tables and usefulness tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6-bit weights for both WT and UT in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The weight_bits parameter has a legal tuning range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses 6-bit weights for WT and UT in sR, but does not define or explore an alternative tuning range such as [5, 8].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The decode-stage register tracking table invalidation policy can be selected from choices clear_matching_tags, clear_all_invalid, or no_action.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies that an instruction writing a register clears the valid bit and stores its ROB index as a tag, but does not specify how tags are compared or cleared when instructions complete or squash.",
      "enum_candidates": [
        "clear_matching_tags",
        "clear_all_invalid",
        "no_action"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The usefulness table update condition can be selected from choices pred_agree, sc_correct, or tage_alt_diff.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that correlations are updated for available registers during training, but does not define the precise branch outcome agreement condition that drives usefulness increments or decrements.",
      "enum_candidates": [
        "pred_agree",
        "sc_correct",
        "tage_alt_diff"
      ]
    },
    {
      "pointer": "/summary",
      "claim": "sR extends the statistical corrector of TAGE-SC-L to exploit correlations between register values and branch outcomes without explicitly tracking producer-consumer dependency chains.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper concludes that sR directly captures correlations between register values and branch outcomes without dependency tracking."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A dedicated tracking table monitors 65 logical registers across 8 banks using a Tomasulo-like structure.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers. As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Section 4.2 describes an 8-bank organization with 8 or 9 logical registers per bank, totalling 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Stale digests are invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 specifies that stale digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source citation accurately identifies the RUNLTS CBP 2025 paper.",
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
      "claim": "The host must broadcast backend instruction execution completion with register index, 64-bit result, type, and ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies overwriting the payload with the produced value's digest upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host must provide decode-stage register rename and allocation events to store ROB indices and clear valid bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 explicitly describes decode-stage tagging and valid bit clearing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage cost of the sR component is 53,863 bits, divided among WT tables (43,008 bits), UT tables (9,360 bits), and the register tracking table (1,495 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact entry dimensions and total storage of 53,863 bits for sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digests are computed as an overlapping XOR fold of 6-bit trailing zero/one count, 6-bit leading zero/one count shifted by 3, and 6-bit value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify the 12-bit digest formed from trailing count [5:0], leading count [8:3], and LSBs [11:6] combined via XOR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Leading and trailing identical bit counts wrap modulo 64 into 6 bits rather than saturating at 63 when val has 64 identical bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not state how 64 identical bits are handled in the 6-bit count fields: whether the count saturates at 63, wraps modulo 64, or counts bits following the first bit.",
      "enum_candidates": [
        "saturate",
        "wrap",
        "sign_extend"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register format is supplied via an input parameter rather than dynamically inspecting register value MSBs.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that floating-point formats are classified by inspecting the most significant bits, but does not specify the exact bit inspection logic or encoding used to distinguish FP16, FP32, and FP64.",
      "enum_candidates": [
        "host_tag",
        "msb_box_inspect",
        "opcode_type"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For floating-point registers, extracted sign and exponent bits are placed into digest bits starting at bit 3 (FP16 at [5:3], FP32 at [8:3], FP64 at [11:3]) with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) and Section 4.2 show FP slices aligned at bit 3 leaving bits [2:0] unused."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition-code flag digests replicate the four flag bits three times across all 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 specifies replicating the four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 defines the digest width as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The digest_width_bits parameter has a legal tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper sets the digest width to 12 bits and does not define or explore an alternative tuning range such as [8, 16].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Stale digests are invalidated after 256 decoded instructions using an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 and Table 3 specify 256 instructions and an 8-bit decay counter per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The decay_instruction_limit parameter has a legal tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper establishes 256 instructions for decay invalidation but does not specify an alternative tuning range such as [64, 1024] pow2.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test 0 tests integer digest generation against the specified 12-bit XOR fold of trailing count, leading count, and 6 LSBs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test inputs and expected digest match the 12-bit XOR fold defined in Section 4.2 and Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test 1 tests replication of 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test checks 4-bit flag replication (0x9 -> 0x999) matching Section 4.2 and Figure 6(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test 2 tests extraction and alignment of FP64 sign and exponent bits into digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "The test checks extraction of Value[63:55] shifted to bits [11:3] matching Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test 3 tests digest invalidation via an 8-bit counter decrementing across 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test checks the 256-instruction decay invalidation described in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test 4 tests bank usefulness zero-suppression scaling where a bank with non-positive usefulness selects multiplier x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) indicates that per-bank WT sums are gated by x0 or x2.5 based on usefulness, suppressing banks with non-positive usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Unit test 6 tests random selection of one available register per bank during training to enable single-write-port RAMs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly requires randomly selecting one available register in a bank during update to allow single-port RAMs."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+global+algo:digest_generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=0ea2df8b-331d-4d74-a2b2-e4e66f7e14be cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "The default weight bitwidth for sR prediction weight tables and usefulness tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                        | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly specifies 6-bit weights for both WT and UT in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The weight_bits parameter has a legal tuning range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses 6-bit weights for WT and UT in sR, but does not define or explore an alternative tuning range such as [5, 8].",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The decode-stage register tracking table invalidation policy can be selected from choices clear_matching_tags, clear_all_invalid, or no_action.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies that an instruction writing a register clears the valid bit and stores its ROB index as a tag, but does not specify how tags are compared or cleared when instructions complete or squash.",
      "enum_candidates": [
        "clear_matching_tags",
        "clear_all_invalid",
        "no_action"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The usefulness table update condition can be selected from choices pred_agree, sc_correct, or tage_alt_diff.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that correlations are updated for available registers during training, but do
... [truncated]

[Usage]
{"input_tokens": 29157, "output_tokens": 28499, "thinking_tokens": 24367, "cache_read_tokens": 0, "total_tokens": 57656}

[Result]
status=SUCCESS conversation=0ea2df8b-331d-4d74-a2b2-e4e66f7e14be turns=1 duration=152.51980855s usage={"input_tokens": 29157, "output_tokens": 28499, "thinking_tokens": 24367, "cache_read_tokens": 0, "total_tokens": 57656}


