success: True
usage: {'input_tokens': 29152, 'output_tokens': 38049, 'thinking_tokens': 32892, 'cache_read_tokens': 0, 'total_tokens': 67201}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector with 8 banks of register-value correlation tables, indexing 3 weight tables with a 12-bit register digest hashed with PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper establishes that the register component is organized into eight banks feeding weight tables using register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper is RUNLTS published at CBP 2025 by Toru Koizumi et al.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The bibliographic citation verbatim identifies the authors, paper title, and CBP 2025 publication venue."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "The host must notify the predictor of each decoded instruction, including destination logical register ID and allocated ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that instruction decode events must deliver the ROB index and destination register to the tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "The host must signal instruction completion with the produced result value and register type to update the tracking table with a digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper requires instruction completion to deliver the produced value so its digest can overwrite the entry payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "On a misprediction flush, in-flight instructions completed prior to resolution retain their values while squashed instructions are cleared.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper specifies that values produced by completed in-flight instructions remain available to the predictor after a misprediction flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "The statistical corrector integrates sR partial sums into LSUM and restricts training updates to registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper specifies that training updates are gated on register availability at branch prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The total storage cost of the sR component is 53,863 bits, comprising 43,008 bits of WT, 9,360 bits of UT, and 1,495 bits of tracking table auxiliary data.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in the paper explicitly specifies 53,863 bits total broken down into 43,008 WT bits, 9,360 UT bits, and 1,495 auxiliary bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "Training updates for register correlations can obtain the register digest from a prediction-time snapshot or by reading the tracking table at retirement.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper specifies that training updates are limited to registers available at prediction time, but does not specify whether the digest is snapshotted or read from the table at retirement."
      },
      "patch": null,
      "open_question": "Does register correlation table training use the digest snapshot from prediction time or re-read the register tracking table at commit?",
      "enum_candidates": [
        "pred_time_digest",
        "commit_time_table"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "Register component weight tables are updated during training when the weight table prediction matches the outcome, when TAGE mispredicts, or when SC updates.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper states that correlations are updated for available registers, but does not define the SC training filter condition."
      },
      "patch": null,
      "open_question": "Under what branch outcome or misprediction condition are the register component weight tables updated during training?",
      "enum_candidates": [
        "wt_matches_outcome",
        "tage_mispredicted",
        "sc_updated"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "Each register bank sum is scaled by 2.5 when the bank's maximum usefulness is strictly positive, non-negative, or statically scaled.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows a multiplier stage of x0 or x2.5 but does not define whether the gating condition is strictly greater than zero, greater than or equal to zero, or static."
      },
      "patch": null,
      "open_question": "What precise usefulness threshold selects between the x0 and x2.5 scaling factors for each register bank?",
      "enum_candidates": [
        "max_useful_gt_0",
        "max_useful_ge_0",
        "static_2_5"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The index hashing function for register usefulness tables (UT) uses an XOR fold of the PC bits.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "Figure 5(c) indicates that PC is skewed to index the usefulness tables, but does not specify the skewing hash function."
      },
      "patch": null,
      "open_question": "What specific hash function generates the skewed PC index for the register usefulness tables (UT)?",
      "enum_candidates": [
        "xor_fold",
        "prime_displacement",
        "jenkins_fold"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The index hashing function for register weight tables (WT) hashes the branch PC and selected register digest using a simple bit-slice concatenation or fold.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "Figure 5(c) indicates that PC and register digest are hashed to produce indices h0, h1, h2 for WT0, WT1, WT2, but does not define the hash algorithms."
      },
      "patch": null,
      "open_question": "What hash algorithm computes the indices h0, h1, and h2 from branch PC and the selected register digest?",
      "enum_candidates": [
        "pc_slice",
        "xor_fold",
        "prime_displacement"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "Register tracking table decay counters decrement on every decoded instruction starting immediately at completion or at decode.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidation after 256 subsequent decoded instructions, but does not specify whether the countdown begins at instruction decode or register writeback completion."
      },
      "patch": null,
      "open_question": "Does the 256-instruction decay counter start decrementing when the producer instruction is decoded or when its result completes execution?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation is triggered upon instruction execution completion when a register result value is produced.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper establishes that digest computation and table update take place when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flags, the 12-bit digest replicates the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 12-bit digest encodes leading counts, trailing counts, and six least significant bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper explicitly specifies that integer digests encode leading counts, trailing counts, and six least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer digest generation counts only zeros rather than zeros or ones, and truncates counts modulo 64 instead of saturating.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper notes counting leading/trailing zeros or ones without specifying whether counting adapts to the sign bit or saturates into 6 bits."
      },
      "patch": null,
      "open_question": "Does integer digest generation count only zeros or bits matching the MSB/LSB, and does a count of 64 saturate at 63 or truncate modulo 64?",
      "enum_candidates": [
        "count_zeros",
        "count_identical",
        "saturate_63",
        "modulo_64"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point format classification inspects register most significant bits to determine FP16, FP32, or FP64 precision.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper states that MSBs are inspected to classify FP format but does not specify the exact bit patterns or test functions used to identify FP16, FP32, or FP64."
      },
      "patch": null,
      "open_question": "What specific bit inspection logic or encoding distinguishes FP16, FP32, and FP64 values in a 64-bit floating-point register?",
      "enum_candidates": [
        "nan_boxing",
        "reg_type_tag",
        "msb_range"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The pseudocode references undefined helper functions generate_digest, return, count_leading_zeros, count_trailing_zeros, and extract_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "While generate_digest is the defined function and return is a language keyword, the leading/trailing zero counters and bit extraction represent standard architectural primitives rather than missing algorithmic specifications."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table contains 65 entries, each consisting of a 1-bit valid bit, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 in the paper specifies the entry format as a 1-bit valid bit, 14-bit payload, and 8-bit decay counter across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The register tracking table and usefulness tables track 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates 65 tracking table entries, matching the 65 registers tracked by the UT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Register digests are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that RUNLTS invalidates each digest after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register producing 0x8 produces a 12-bit digest equal to 3 ^ (60 << 3) ^ (8 << 6) = 995 (0x3E3).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test expectation correctly applies the overlapping XOR fold of trailing zeros (3), leading zeros (60), and 6 LSBs (8) per Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A condition-code register producing 4-bit flag pattern 0b1011 generates 12-bit digest 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating the 4-bit pattern 0b1011 three times produces 0b101110111011 (0xBBB)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Bank 0 selects the available register with highest summed usefulness across its UT tables to index WT prediction tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper establishes that the digest of the most useful register among those available in the bank is selected to index the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "When a bank's selected register has non-positive usefulness, its contribution to sR is scaled by 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that a bank's prediction weight sum feeds a multiplier stage selecting x0 or x2.5, suppressing non-useful bank contributions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's selected register has positive usefulness, its contribution to sR is scaled by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies that each bank's prediction weight sum is scaled by 2.5 when selected by the usefulness logic."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A register entry's valid bit is cleared and its digest invalidated after 256 subsequent instructions are decoded without a new write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Upon misprediction recovery, completed in-flight instructions retain valid digests while speculative squashed instructions are invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper explains that values completed prior to misprediction resolution remain visible upon pipeline restart to correct subsequent branches."
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
model=gemini-3.8-flash-medium conversation=1f93bdcb-ecd8-4c49-938e-65115f554338 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector with 8 banks of register-value correlation tables, indexing 3 weight tables with a 12-bit register digest hashed with PC.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper establishes that the register component is organized into eight banks feeding weight tables using register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper is RUNLTS published at CBP 2025 by Toru Koizumi et al.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The bibliographic citation verbatim identifies the authors, paper title, and CBP 2025 publication venue."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "The host must notify the predictor of each decoded instruction, including destination logical register ID and allocated ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that instruction decode events must deliver the ROB index and destination register to the tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates
... [truncated]

[Usage]
{"input_tokens": 29152, "output_tokens": 38049, "thinking_tokens": 32892, "cache_read_tokens": 0, "total_tokens": 67201}

[Result]
status=SUCCESS conversation=1f93bdcb-ecd8-4c49-938e-65115f554338 turns=1 duration=196.822357069s usage={"input_tokens": 29152, "output_tokens": 38049, "thinking_tokens": 32892, "cache_read_tokens": 0, "total_tokens": 67201}


