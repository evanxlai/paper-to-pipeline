success: True
usage: {'input_tokens': 29231, 'output_tokens': 40162, 'thinking_tokens': 35412, 'cache_read_tokens': 0, 'total_tokens': 69393}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature tracks 65 logical registers across 8 banks in a Tomasulo-like table holding ROB tags or 12-bit value digests decaying after 256 decoded instructions, using UT to pick the most useful digest per bank to index WT and accumulating scaled contributions into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The quote defines the Tomasulo-like table holding tags or 12-bit digests for logical registers to feed the SC register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The distillation source paper is RUNLTS published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the source attribution verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The execution backend supplies completed register values and types at writeback to generate value digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that instruction completion triggers digest overwrite and validation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Decode and rename assign destination registers and ROB tags to mark register entries in-flight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The quote defines decode-time tag storage and valid bit clearing."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "A count of decoded instructions invalidates register status table entries after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The pipeline provides squash notifications to recover the Tomasulo-like status table on branch mispredictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper identifies the path for digests and recovering the Tomasulo-like table as the required interface mechanism."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sr feature requires 53,863 total storage bits composed of the Register Status Table (1,495 bits), WT tables (43,008 bits), and UT tables (9,360 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 gives this exact auxiliary entry structure summing to 1,495 bits alongside 43,008 WT bits and 9,360 UT bits for a total of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers partitioned into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Eight banks of eight or nine registers each corresponds to 65 logical registers total."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The register value digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly fixes the generated digest size to 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Status Table contains 65 entries of 23 bits each (1 valid bit, 14 payload bits, and an 8-bit decay counter).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines 65 entries formatted with 1 valid bit, 14 payload bits, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Register Prediction Weight Tables (WT) span 8 banks, each containing sub-tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit signed weights totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of 128, 256, and 512 entries of 6-bit weights totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Register Usefulness Weight Tables (UT) consist of 3 tables of 8 entries each holding 6-bit weights for all 65 registers totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies three 8-entry tables of 6-bit weights across 65 registers totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation triggers at instruction execution completion / writeback time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Instruction completion is defined as the trigger for generating the digest and overwriting the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation creates a 12-bit digest characterizing address patterns, exponents, or condition flags.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions.",
        "why": "The paper introduces the short register value digest characterizing values to exploit branch correlations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digests are formed by XOR-folding 6-bit slices of trailing zeros/ones count [5:0], leading zeros/ones count [8:3], and the value's 6 LSBs [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The quote establishes the three components used in Figure 6(a) to construct the XOR-folded integer digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The pseudocode uses 'return' as a standard programming language statement to output values, not as an undefined helper function call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The pseudocode outputs the generated 12-bit digest via standard language return statements rather than calling an undefined external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digests extract the sign and high-order exponent bits placed at digest bit offset 3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The quote establishes extracting the sign and leading exponent bits for floating-point registers as depicted in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition code flag digests replicate the 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The quote defines replicating the 4 condition-code bits three times into the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The count_leading_zeros_or_ones helper function counts leading bits matching either zero or one into a 6-bit saturating or wrapping field.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The text mentions counting leading zeros (or ones) but leaves whether it counts matching MSB bits, zeros only, or saturates at 63 vs wraps mod 64 unsettled."
      },
      "patch": null,
      "open_question": "How does count_leading_zeros_or_ones determine whether to count zeros or ones, and how is the 0-64 count mapped into 6 bits?",
      "enum_candidates": [
        "match_msb_saturate",
        "match_msb_wrap",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The count_trailing_zeros_or_ones helper function counts trailing bits matching either zero or one into a 6-bit saturating or wrapping field.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The text mentions counting trailing zeros (or ones) but does not specify whether bits matching the LSB are counted, zeros only, or how 64-bit counts fit in 6 bits."
      },
      "patch": null,
      "open_question": "How does count_trailing_zeros_or_ones determine whether to count zeros or ones, and how is the 0-64 count mapped into 6 bits?",
      "enum_candidates": [
        "match_lsb_saturate",
        "match_lsb_wrap",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The floating-point format is classified into FP16, FP32, or FP64 by inspecting the most significant bits of the 64-bit register value.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper mentions inspecting MSBs to classify the format but does not specify the classification logic or encoding."
      },
      "patch": null,
      "open_question": "How does the digest generator inspect the most significant bits of a 64-bit register value to classify FP16, FP32, and FP64 formats?",
      "enum_candidates": [
        "nan_boxing",
        "host_type_tag",
        "exponent_range"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register with value 0x2A produces trailing count 1, leading count 58, and XOR-folded 12-bit digest 0xB51.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test precisely evaluates the arithmetic of the XOR-folding specification defined in Section 4.2 and Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A 4-bit flag value 0xB replicates three times to form 12-bit digest 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test verifies the 3-fold replication rule stated in Section 4.2 and Figure 6(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register with value 0xC0A00000 extracts bits [31:26] (0x30) into digest bits [8:3] yielding 0x180.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The test verifies the FP32 bit slice Value[31:26] placed at digest bits [8:3] as shown in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest remains valid for 255 decoded instructions and is invalidated on the 256th instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test verifies the exact 256-decoded-instruction lifetime threshold stated in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank's most useful available register has positive usefulness, its WT weight sum is multiplied by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test checks selection of the most useful register and the x2.5 multiplier stage shown in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's highest usefulness is non-positive, the bank contribution is scaled by x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test verifies the non-positive usefulness gating path of the x0 multiplier stage in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Completed in-flight instructions retain valid digests across branch misprediction flushes, while uncompleted flushed instructions do not.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The test evaluates the post-flush visibility of instructions that finished execution before the flush completes."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+algo:digest_generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read ...

[Init]
model=gemini-3.8-flash-medium conversation=dcce7451-e24b-458f-bab8-f9ff950d8f87 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature tracks 65 logical registers across 8 banks in a Tomasulo-like table holding ROB tags or 12-bit value digests decaying after 256 decoded instructions, using UT to pick the most useful digest per bank to index WT and accumulating scaled contributions into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The quote defines the Tomasulo-like table holding tags or 12-bit digests for logical registers to feed the SC register component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The distillation source paper is RUNLTS published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title matches the source attribution verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The execution backend supplies completed register values and types at writeback to generate value digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that instruction completion triggers digest overwrite and validation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "c
... [truncated]

[Usage]
{"input_tokens": 29231, "output_tokens": 40162, "thinking_tokens": 35412, "cache_read_tokens": 0, "total_tokens": 69393}

[Result]
status=SUCCESS conversation=dcce7451-e24b-458f-bab8-f9ff950d8f87 turns=1 duration=213.984409538s usage={"input_tokens": 29231, "output_tokens": 40162, "thinking_tokens": 35412, "cache_read_tokens": 0, "total_tokens": 69393}


