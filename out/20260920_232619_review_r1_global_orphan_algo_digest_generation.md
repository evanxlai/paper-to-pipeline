success: True
usage: {'input_tokens': 29894, 'output_tokens': 38716, 'thinking_tokens': 32901, 'cache_read_tokens': 0, 'total_tokens': 68610}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature augments the TAGE-SC-L statistical corrector with correlations between branch directions and backend register values using a Tomasulo-like register status table of 65 logical registers across 8 banks decaying after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly describes the Tomasulo-like tracking table with per-register entries holding ROB tags or digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Register usefulness tables pick the most useful available digest per bank to index bank prediction weight tables with PC, scaling positive usefulness sums by 2.5 or gating to 0 before accumulating into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper confirms that usefulness determines the single selected register digest per bank driving the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The register value mechanism corrects subsequent branch mispredictions starting with the second branch following a misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper verbatim asserts that post-flush value availability allows correcting mispredictions starting with the second one."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature is distilled from the paper RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The full citation exactly matches the title, author list, and publication venue of the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The execution backend must supply completed register values and register formats at writeback to compute the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Instruction completion is the required interface trigger where backend values are converted to digests and recorded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Frontend decode must allocate logical register destinations and store the instruction's ROB tag in the status table while clearing the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that decode passes the ROB index as a tag to the corresponding register status entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "A decoded instruction count is broadcast to advance register status table decay counters to invalidate entries after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper dictates invalidating digests specifically based on the count of 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Branch misprediction squash handling requires pipeline notification of flushed in-flight instructions to update register availability.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Pipeline restart after misprediction requires distinguishing completed in-flight instructions from flushed ones."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total storage consumed by sR components is 53,863 bits (1,495 bits status table + 43,008 bits WT + 9,360 bits UT).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in the paper details the exact breakdown of WT, UT, and auxiliary register status storage summing to 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The exact counting method for leading zeros or ones in integer registers is an enumerated configuration choice between matching MSB with saturation, matching MSB with wrap, zeros only, or ones only.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper states 'the count of leading zeros (or ones)' without specifying whether the bit matching sign bit is counted or how 64-bit counts fit into 6 bits."
      },
      "patch": null,
      "open_question": "Does count of leading zeros (or ones) count bits matching the MSB, count zeros unconditionally, count ones unconditionally, and does it saturate or wrap at 63?",
      "enum_candidates": [
        "match_msb_saturate",
        "match_msb_wrap",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The exact counting method for trailing zeros or ones in integer registers is an enumerated configuration choice between matching LSB with saturation, matching LSB with wrap, zeros only, or ones only.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper states 'the count of trailing zeros (or ones)' without specifying whether bits matching LSB are counted or how overflow into 6 bits is handled."
      },
      "patch": null,
      "open_question": "Does count of trailing zeros (or ones) count bits matching the LSB, count zeros unconditionally, count ones unconditionally, and does it saturate or wrap at 63?",
      "enum_candidates": [
        "match_lsb_saturate",
        "match_lsb_wrap",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "Classification of floating-point formats from 64-bit values is an enumerated choice between NaN boxing, host type tagging, and exponent range check.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper states that format is classified by inspecting most significant bits, but does not provide the concrete classification logic."
      },
      "patch": null,
      "open_question": "How are 64-bit register values classified into FP16, FP32, or FP64 when inspecting the most significant bits?",
      "enum_candidates": [
        "nan_boxing",
        "host_type_tag",
        "exponent_range"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The training update condition for register component WT and UT weights selects among bank_correct, sc_correct, bank_useful, or overall_correct.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper describes which registers are eligible for update and random selection among available registers, but does not specify the exact error threshold or correctness gating condition."
      },
      "patch": null,
      "open_question": "What prediction outcome or threshold triggers weight increments/decrements in WT and UT during training?",
      "enum_candidates": [
        "bank_correct",
        "sc_correct",
        "bank_useful",
        "overall_correct"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "The recovery policy for restoring the register status table following a squash is an enumerated choice among clear_flushed_tags, checkpoint_restore, flash_invalidate, and no_recovery.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly delegates recovery of the Tomasulo-like table on squashes to future work without defining a mechanism."
      },
      "patch": null,
      "open_question": "What recovery mechanism is used to restore valid bits and ROB tags in the register status table after a branch misprediction squash?",
      "enum_candidates": [
        "clear_flushed_tags",
        "checkpoint_restore",
        "flash_invalidate",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation triggers at instruction execution writeback or completion time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies instruction completion as the trigger for generating the digest and storing it in the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "For integer registers, the 12-bit digest is generated by XOR-folding a 6-bit trailing zero/one count [5:0], a 6-bit leading zero/one count shifted by 3 [8:3], and the 6 LSBs of the register shifted by 6 [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper text together with Figure 6(a) defines the three 6-bit fields offset by 3 bits and combined with XOR to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "For floating-point registers, the 12-bit digest extracts the sign bit and high-order exponent bits placed at digest bits [5:3] for FP16, [8:3] for FP32, and [11:3] for FP64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) shows Val[15:13] for FP16, Value[31:26] for FP32, and Value[63:55] for FP64 right-aligned at digest bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "For condition-code flag registers, the 4-bit flag pattern is replicated three times into digest bits [11:8], [7:4], and [3:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Figure 6(c) and the prose confirm three adjacent 4-bit Value[3:0] fields filling all 12 bits of the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Calls to count_leading_zeros_or_ones and count_trailing_zeros_or_ones in digest generation represent host hardware bit-counting primitives, and return is standard language control flow rather than an undefined helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper directly specifies counting leading and trailing zeros or ones as fundamental primitive operations, which correspond to CPU bit-counting instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status table contains 65 direct-mapped entries across 8 banks, each consisting of a 1-bit valid flag, a 14-bit payload (holding ROB tag or 12-bit digest), and an 8-bit saturating decay counter totalling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data row exactly specifies 65 entries with valid(1), payload(14), and decay_ctr(8) fields, summing to 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Register prediction weight tables (WT) comprise 8 banks of 3 direct-mapped sub-tables (WT0: 512 entries, WT1: 256 entries, WT2: 128 entries) storing 6-bit signed weights totalling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 WT column explicitly gives 6-bit weights for tables of size 2^7 (128), 2^8 (256), and 2^9 (512) entries across 8 banks, totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Register usefulness weight tables (UT) comprise 3 tables (UT0, UT1, UT2) of 8 entries each, storing a 6-bit weight per register for all 65 registers totalling 9,360 bits indexed by skewed PC hashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 UT column explicitly lists 3 tables of 2^3 (8) entries with 6-bit weights for 65 registers, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of tracked logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms 65 logical registers across all table accounting entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default register value digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states verbatim that digests are 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_xor_folding tests integer digest generation by XOR-folding trailing zeros, leading zeros, and LSB[5:0] into 0xB51 for value 0x2A.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test inputs and expected output 0x01 ^ (0x3A << 3) ^ (0x2A << 6) = 0xB51 accurately implement Figure 6(a) and the text."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_flag_digest_replication verifies that a 4-bit flag pattern 0xB replicates three times into 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test check replicates the 4-bit pattern three times character-for-character matching the paper specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_fp32_digest_extraction checks that bits [31:26] of an FP32 value are extracted and shifted to digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies Value[31:26] placed at digest bits [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_register_decay_invalidation tests that valid digests remain valid for 255 decoded instructions and transition to invalid on the 256th instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test asserts invalidation after 256 decoded instructions matching Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_bank_usefulness_argmax_selection verifies selecting the register with highest usefulness in a bank and scaling its WT sum by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper and Figure 5(c) define selecting the largest usefulness register and applying the x2.5 multiplier stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_bank_negative_usefulness_suppression verifies that when max usefulness in a bank is non-positive, multiplier x0 is applied suppressing the bank's contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Figure 5(c) designates the per-bank multiplier stage as 'x0 or x2.5', suppressing bank output when usefulness is not positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_post_misprediction_value_availability tests that instructions completed during a misprediction resolution retain valid digests to inform subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The test scenario directly verifies availability of completed in-flight digests immediately following a misprediction flush."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+orphan+algo:digest_generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=856bd7ed-0598-4c74-8619-876932942d99 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature augments the TAGE-SC-L statistical corrector with correlations between branch directions and backend register values using a Tomasulo-like register status table of 65 logical registers across 8 banks decaying after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly describes the Tomasulo-like tracking table with per-register entries holding ROB tags or digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Register usefulness tables pick the most useful available digest per bank to index bank prediction weight tables with PC, scaling positive usefulness sums by 2.5 or gating to 0 before accumulating into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper confirms that usefulness determines the single selected register digest per bank driving the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The register value mechanism corrects subsequent branch mispredictions starting with the second branch following a misprediction flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mi
... [truncated]

[Usage]
{"input_tokens": 29894, "output_tokens": 38716, "thinking_tokens": 32901, "cache_read_tokens": 0, "total_tokens": 68610}

[Result]
status=SUCCESS conversation=856bd7ed-0598-4c74-8619-876932942d99 turns=1 duration=204.201355339s usage={"input_tokens": 29894, "output_tokens": 38716, "thinking_tokens": 32901, "cache_read_tokens": 0, "total_tokens": 68610}


