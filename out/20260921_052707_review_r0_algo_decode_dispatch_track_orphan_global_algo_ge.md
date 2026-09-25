success: True
usage: {'input_tokens': 31587, 'output_tokens': 34359, 'thinking_tokens': 28505, 'cache_read_tokens': 0, 'total_tokens': 65946}

## result
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The feature is distilled from the paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "Matches the publication title and citation verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component captures correlations between branch directions and recently produced register values without explicit dependency tracking.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "Settles the purpose and dependency-free correlation mechanism of the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Logical registers are partitioned across 8 banks corresponding to eight or nine registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles the 8-bank partitioning across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Each bank uses 3 Usefulness Weight Tables with 8 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines three usefulness weight tables per register with 2^3 (8) entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A bank's prediction weight sum is conditionally scaled by 2.5 if its register is useful, or gated by 0 if not.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What signal selects the x0 vs x2.5 multiplier in Figure 5(c) (e.g. positive net usefulness of the bank's selected register versus a global static scale)?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default value of parameter sr_enable matches one of the declared choices in its range.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "/parameters/0/default declares boolean True whereas /parameters/0/range specifies string choices ['true', 'false'], so the default value fails membership in the declared choices."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/0/default",
        "value": "true"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/storage_impact",
      "claim": "Disabling sr_enable saves 53,863 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the total storage consumption of the sR component as 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default number of logical registers tracked by sR is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that sR tracks 65 logical registers across its usefulness weight tables and auxiliary status entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The tuning range for num_logical_regs is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed count of 65 logical registers and does not define a tuning range for num_logical_regs.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The default staleness decay threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that digest validity expires after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/range",
      "claim": "The tuning range for decay_threshold_insts is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed staleness decay threshold of 256 decoded instructions and does not define a tuning range for decay_threshold_insts.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Settles that each register digest is 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/range",
      "claim": "The tuning range for digest_width is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper defines a fixed 12-bit digest format and does not define a tuning range for digest_width.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "reg_status_table is a direct-mapped table with one entry per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Settles the organization of one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry of reg_status_table consists of a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry format fields and widths."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "reg_status_table total storage size is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 registers multiplied by 23 bits per entry equals 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "prediction_weight_tables comprises 8 banks each containing 3 tables of 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines 8 banks of WT tables with sizes 2^9 (512), 2^8 (256), and 2^7 (128) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "prediction_weight_tables entries are 6-bit weights.",
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
      "pointer": "/state/2/size_bits",
      "claim": "Total storage size of prediction_weight_tables is 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits multiplied by (128 + 256 + 512) entries across 8 banks equals 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "Instruction decode/rename stores the ROB index as a tag and clears the valid bit in the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles the interface requirement and actions performed at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "Execution completion overwrites the payload with the produced value's digest and sets the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles the interface requirement and actions performed on instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "A decoded instruction count is needed to invalidate digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that digest staleness tracking is governed by decoded instruction count up to 256."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/total_storage_bits",
      "claim": "The total storage for the sR component is 53,863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact total storage bit count of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/storage_breakdown",
      "claim": "sR storage breakdown is WT: 43,008 bits, UT: 9,360 bits, and Status Table: 1,495 bits, totaling 53,863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Matches the arithmetic breakdown of WT, UT, and auxiliary fields in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register leading and trailing zero/one counts saturate at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are integer leading and trailing identical bit counts encoded into 6 bits (saturating at 63, modulo 64, or counting sign-matching bits), and how are zeros vs ones distinguished?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the digest encodes the count of leading zeros (or ones), trailing zeros (or ones), and the six least significant bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles the components encoded into integer register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digests are right-aligned to bit 3, leaving bits [2:0] zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are floating-point register digest fields positioned with their LSB at bit 3 leaving bits [2:0] zero, or right-aligned at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For floating-point registers, format classification selects the sign bit and most significant exponent bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Settles the extraction of the sign bit and MSBs of the exponent for FP registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition-code flag digests replicate the four flag bits three times to fill 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles the 3-fold replication of 4-bit condition flags into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "decode_dispatch_track triggers at instruction decode / dispatch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that decode triggers register status table tag allocation and invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the valid bit and stores the ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles the destination register entry update behavior at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Digests are invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that digests are invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_generation encodes leading and trailing zero counts as unsigned integers directly into 6-bit fields without saturation or sign-matching differences.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are integer leading and trailing counts formatted in the digest bit fields (saturating at 63, modulo 64, or counting identical bits matching the MSB/LSB)?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_fp64_digest_generation expects FP64 digest bits [2:0] to be zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are floating-point register digest fields positioned with their LSB at bit 3 leaving bits [2:0] zero, or right-aligned at bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_flag_digest_generation expects 4-bit flag 0x9 replicated three times to equal 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles that replicating 4-bit flag 0x9 three times produces 0x999."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_staleness_invalidation invalidates reg_status_table valid bit after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that validity is cleared exactly after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_bank_usefulness_selection selects the register with the highest usefulness sum among available registers in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the digest of the most useful available register within the bank is picked to index the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_multiplier_gating gates bank contribution to 0 when usefulness sum is <= 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What signal selects the x0 vs x2.5 multiplier in Figure 5(c) (e.g. positive net usefulness of the bank's selected register versus a global static scale)?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_multiplier_activation scales bank prediction weight sum by 2.5 when usefulness sum is > 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What signal selects the x0 vs x2.5 multiplier in Figure 5(c) (e.g. positive net usefulness of the bank's selected register versus a global static scale)?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decode_dispatch_track+orphan+global+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from t...

[Init]
model=gemini-3.8-flash-medium conversation=c39a5c1f-9f45-44f9-bea0-604e74354f02 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_bd2489640a39caf1

[Response]
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The feature is distilled from the paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "Matches the publication title and citation verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component captures correlations between branch directions and recently produced register values without explicit dependency tracking.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "Settles the purpose and dependency-free correlation mechanism of the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Logical registers are partitioned across 8 banks corresponding to eight or nine registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles the 8-bank partitioning across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
 
... [truncated]

[Usage]
{"input_tokens": 31587, "output_tokens": 34359, "thinking_tokens": 28505, "cache_read_tokens": 0, "total_tokens": 65946}

[Result]
status=SUCCESS conversation=c39a5c1f-9f45-44f9-bea0-604e74354f02 turns=1 duration=192.377023682s usage={"input_tokens": 31587, "output_tokens": 34359, "thinking_tokens": 28505, "cache_read_tokens": 0, "total_tokens": 65946}


