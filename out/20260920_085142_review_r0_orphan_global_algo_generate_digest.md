success: True
usage: {'input_tokens': 28698, 'output_tokens': 36531, 'thinking_tokens': 30195, 'cache_read_tokens': 0, 'total_tokens': 65229}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5/default",
      "claim": "Prediction and usefulness weight tables in sR use 6-bit weights by default.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines both the prediction weight table (WT) and usefulness weight table (UT) with a weight width factor of 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/range",
      "claim": "The parameter weight_width_bits has an exploration range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the valid exploration range for weight_width_bits in design space exploration?",
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends the SC perceptron predictor by exploiting correlations between recently produced register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2).",
        "why": "The paper explicitly introduces this mechanism to exploit register-value correlations within the SC predictor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "RUNLTS maintains a 65-entry Tomasulo-like status table tracking valid 12-bit digests or 14-bit tags for logical registers R0-R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper directly describes the Tomasulo-like status table entry format and capacity matching the 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The registers in sR are partitioned across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 specifies that the register component is partitioned into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "For each bank, usefulness tables evaluate register utility and the digest of the most useful available register indexes prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The text explains the selection of the most useful available register digest to forward to the direction weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Bank weight sums are conditionally scaled by 2.5 or suppressed to 0, and summed across 8 banks to contribute to SC LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows each bank's weight sum feeding a multiplier stage selecting x0 or x2.5 before cross-bank summation into sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Digests expire after 256 decoded instructions to prevent stale values from degrading accuracy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes the 256 decoded instruction expiration rule."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper title and publication details correspond to RUNLTS published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The bibliographic details exactly match the publication header and citation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Execution completion bus supplies the produced value to overwrite payload with the digest and set the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 states that completion overwrites the payload with the produced value's digest and marks the entry valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Decode/rename stage clears the valid bit and stores the ROB index as a tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 specifies that decoding an instruction writing a register writes its ROB index and clears valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires decode notifications to invalidate digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that invalidation tracks 256 subsequently decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The SC summation tree integrates sR alongside other SC components into LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing \"LSUM\".",
        "why": "Figure 5(d) explicitly illustrates sR as an input feeding into the LSUM adder tree."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/total_storage_bits",
      "claim": "The total storage cost of the sR component is 53,863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives exactly 53863 bits for the sR component total storage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/storage_breakdown",
      "claim": "Storage breaks down into 43,008 WT bits, 9,360 UT bits, and 1,495 status table bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies 6 * (128 + 256 + 512) * 8 = 43,008 bits for WT, 6 * 65 * 24 = 9,360 bits for UT, and 65 * (1 + 14 + 8) = 1,495 bits for auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/budget_donors",
      "claim": "The 53,863 bits of sR are reclaimed under iso-storage by shrinking tagged table bank counts, reducing high-bank entry capacity, or downsizing base bimodal table entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which specific baseline tables donate storage budget to accommodate sR within the 192 KiB CBP budget?",
      "enum_candidates": [
        "shrink_tagged_banks",
        "reduce_high_bank_entries",
        "downsize_bimodal"
      ]
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest triggers at execution unit writeback / instruction completion when a 64-bit register value is produced.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 states that the payload is overwritten with the produced value's digest upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 12-bit digest is formed by XOR-folding trailing count [5:0], leading count shifted by 3 [8:3], and value[5:0] shifted by 6 [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "bit 5 |  trailing one/zero #   | bit 0",
        "why": "Figure 6(a) defines the overlapping 6-bit fields joined by XOR operations spanning bit positions [5:0], [8:3], and [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer leading and trailing counts select between counting zeros or ones dynamically based on the edge bit of the register.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the integer digest count bits matching the edge bit (LSB for trailing, MSB for leading), count zeros only, or use a dedicated flag bit to indicate 0 vs 1?",
      "enum_candidates": [
        "match_edge_bit",
        "count_zeros_only",
        "count_ones_only"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer leading and trailing counts saturate at 63 rather than wrapping modulo 64 when a 64-bit value has 64 identical bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "When a 64-bit integer register contains 64 identical bits, does the 6-bit count field saturate at 63 or wrap modulo 64?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point format is classified into FP16, FP32, or FP64 by inspecting the most significant bits of the 64-bit value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 explicitly describes format classification by inspecting the MSBs of floating-point registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The exact bit patterns used to inspect MSBs and classify FP format are NaN-boxing checks in the 64-bit register.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific MSB bit patterns or architectural conventions (e.g. NaN-boxing vs instruction opcode tags) are used to classify FP16, FP32, and FP64?",
      "enum_candidates": [
        "nan_boxing",
        "instruction_opcode",
        "fp_status_reg"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For FP32 registers, bits [31:26] are extracted and placed at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) specifies extracting Value[31:26] aligned to digest bit positions [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For FP16 registers, bits [15:13] are extracted and placed at digest bits [5:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP16\"  ->  Val[15:13]",
        "why": "Figure 6(b) specifies extracting Val[15:13] right-aligned to bit 3, occupying digest bits [5:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For FP64 registers, bits [63:55] are extracted and placed at digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies extracting Value[63:55] right-aligned to bit 3, occupying digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flag registers, the 4 flag bits are replicated three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly dictates 3x replication of the four flag bits across the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Register types other than INT, FP, and FLAG fall back to masking the lowest 12 bits of the register value.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are register types outside INT, FP, and FLAG handled during digest generation?",
      "enum_candidates": [
        "raw_lsb",
        "zero_digest",
        "bypass"
      ]
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "Digest width is 12 bits, FP registers leave bits [2:0] at 0, and FLAG registers fill all 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 and Figure 6 show a 12-bit output with FP fields aligned to bit 3 and FLAG replicated across all 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default lifetime for register digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly specifies that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/range",
      "claim": "The parameter decay_instructions has a tuning exploration range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the tuning range for decay_instructions?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/storage_impact",
      "claim": "Table 3 allocates an 8-bit counter (decay_ctr (8)) in the register status table to track the 256-instruction decay interval.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 allocates decay_ctr as an 8-bit field, which provides 2^8 = 256 states to track the 256-instruction lifetime."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly specifies that RUNLTS generates a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The parameter digest_width_bits has an exploration tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the exploration range for digest_width_bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer value 0x0000000000000008 produces digest 0x3E3 via XOR folding of trailing count 3, leading count 60, and value LSB 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "bit 5 |  trailing one/zero #   | bit 0",
        "why": "Figure 6(a) defines XOR folding of the 3 fields, which for 0x8 evaluates to 0x03 ^ (0x3C << 3) ^ (0x08 << 6) = 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A FLAG register with 4-bit value 0x9 replicates to produce digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 establishes 3x replication of the four flag bits, yielding 0x999."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register with bits [31:26] = 0x2B shifts to digest bits [8:3] producing 0x0158.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) specifies extracting Value[31:26] into digest bits [8:3], yielding 0x2B << 3 = 0x158."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "The decay counter is initialized directly with integer literal 256 and decrements down to 0 across 256 decode steps.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Table 3 allocates an 8-bit counter (decay_ctr (8), max 255) while Section 4.2 specifies invalidation after 256 decoded instructions. How is the 256-step interval initialized and counted in 8 bits?",
      "enum_candidates": [
        "init_255_underflow",
        "init_255_zero_expire",
        "count_up_to_255"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness outputs 0 via the x0 multiplier, while a bank with positive usefulness scales WT sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) illustrates per-bank scaling by 2.5 when useful or suppression to 0 when not useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed arithmetic instructions ahead of a mispredicted branch retain their valid digests in the status table following pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 explains that execution results of prior in-flight instructions that finished execution remain visible to the predictor upon pipeline restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+global+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never ...

[Init]
model=gemini-3.8-flash-medium conversation=6ae157e9-d2ab-4650-a8b7-16563b02698e cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5/default",
      "claim": "Prediction and usefulness weight tables in sR use 6-bit weights by default.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines both the prediction weight table (WT) and usefulness weight table (UT) with a weight width factor of 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/range",
      "claim": "The parameter weight_width_bits has an exploration range of [5, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the valid exploration range for weight_width_bits in design space exploration?",
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends the SC perceptron predictor by exploiting correlations between recently produced register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We propose a novel prediction method that exploits correlations between register values and branch directions (Section 4.2).",
        "why": "The paper explicitly introduces this mechanism to exploit register-value correlations within the SC predictor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "RUNLTS maintains a 65-entry Tomasulo-like status table tracking valid 12-bit digests or 14-bit tags for logical registers R0-R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's 
... [truncated]

[Usage]
{"input_tokens": 28698, "output_tokens": 36531, "thinking_tokens": 30195, "cache_read_tokens": 0, "total_tokens": 65229}

[Result]
status=SUCCESS conversation=6ae157e9-d2ab-4650-a8b7-16563b02698e turns=1 duration=176.064993429s usage={"input_tokens": 28698, "output_tokens": 36531, "thinking_tokens": 30195, "cache_read_tokens": 0, "total_tokens": 65229}


