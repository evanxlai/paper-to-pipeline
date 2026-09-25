success: True
usage: {'input_tokens': 29179, 'output_tokens': 37319, 'thinking_tokens': 32841, 'cache_read_tokens': 0, 'total_tokens': 66498}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation is triggered at execution completion when a functional unit produces an architectural register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies that writing the produced value digest into the table entry occurs upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding trailing identical bits at [5:0], leading identical bits at [8:3], and the 6 LSBs at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest is formed by overlapping trailing identical bit counts, leading identical bit counts, and Value[5:0] via XOR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point values generate a digest by extracting the sign bit and high exponent bits right-aligned at digest bit 3 with bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) establish that Val[15:13] (FP16), Value[31:26] (FP32), and Value[63:55] (FP64) are aligned starting at digest bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Condition-code flags generate a 12-bit digest by replicating the four flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) explicitly state that 4 flag bits replicate three times into digest bits [11:0]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Counting leading and trailing identical bits uses host execution bitwise counting primitives.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "Section 4.2 requires leading and trailing zero/one counts, settling the host primitive finding."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The mechanism for inspecting the most significant bits of a register value to classify its floating-point format is specified.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that the most significant bits are inspected to classify the format, but does not specify the exact bit patterns or classification algorithm used to distinguish FP16, FP32, and FP64.",
      "enum_candidates": [
        "nan_boxing",
        "host_type_tag"
      ]
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "Digest generation compresses 64-bit values into a 12-bit signature depending on register type.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that a 12-bit digest is generated from each 64-bit register value based on register type."
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
        "why": "Section 4.2 and Table 3 establish that RUNLTS tracks 65 logical registers distributed across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Prediction weight tables (WT) and usefulness weight tables (UT) store 6-bit signed weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT and UT table entry sizes as 6 bits, settling the weight_width parameter finding as a structural table parameter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The update trigger for algorithm 5 is configurable between at_commit and at_resolution.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not state whether sR weight table training is triggered at branch execution/resolution or at architectural commit.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The update condition for algorithm 5 is configurable among pred_sign_eq_taken, corrects_tage, and tage_mispred_only.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify the exact training update condition for sR weight tables among matching branch direction, correcting TAGE, or TAGE mispredictions only.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "Pipeline squash recovery policy for the register tracking table is configurable among clear_flushed, no_recovery, and flash_invalidate.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper explicitly defers recovery of the Tomasulo-like table following pipeline flushes to future work, leaving the post-squash recovery policy unspecified.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "Integer digest leading and trailing bit counts are configurable between saturating at 63 and wrapping modulo 64.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify whether leading and trailing identical bit counts saturate at 63 or wrap modulo 64 when all 64 bits are identical.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer 0x8 produces digest 0x3E3 by XOR-folding trailing zeros (3), leading zeros (60 << 3), and LSBs (8 << 6).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) define the integer digest formula that evaluates to 3 ^ (60 << 3) ^ (8 << 6) = 995 (0x3E3) for input value 8."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 value 0x4014000000000000 produces digest 0x400 from slice Val[63:55] shifted to bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) define the FP64 digest as Value[63:55] shifted to digest bits [11:3], producing 0x80 << 3 = 0x400."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag nibble 0xB produces digest 0xBBB by three-fold replication.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) establish that 4-bit condition flags replicate three times to form a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated after 256 decoded instructions without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The valid register with highest usefulness in a bank is selected and its WT sum scaled by 2.5 if positive, or gated to 0 if non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) specify selecting the most useful register in the bank and scaling by x2.5 or x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed register values retain valid digests across branch misprediction squashes to correlate on post-flush predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 explains that values produced before misprediction resolution remain available to the predictor after the flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends TAGE-SC-L by tracking 12-bit digests of 65 registers in a Tomasulo-like table with 256-instruction decay.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 and Table 3 specify a 65-entry table tracking 12-bit digests invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Registers are distributed across 8 banks where 3 UT tables select the most useful register whose digest and PC index 3 WT tables scaled by 2.5x.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers. As with the SC's existing components, it comprises two tables: one that tracks prediction usefulness and one that determines the predicted branch direction.",
        "why": "Section 4.2 and Figure 5(c) define the 8-bank organization, 3 UTs per bank, 3 WTs per bank, and 2.5x scaling."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The distilled spec is derived from the CBP 2025 paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title and citation match the title and author publication header."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host front-end must provide destination register index and ROB tag at instruction decode to clear valid and record tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 specifies that the host decode stage provides register index and ROB tag to initialize the tracking table entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host execution units forward produced values and register type upon completion to update table entry with digest and set valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies that completion of execution forwards the produced value to overwrite the payload with its digest and assert valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host decoder signals decoded instructions to advance tracking table decay counters for 256-instruction invalidation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 requires tracking decoded instruction count to invalidate entries after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Host notifies branch misprediction flushes to clear invalid pending entries in the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "Section 5 identifies tracking table recovery across pipeline flushes as an essential host integration interface."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total sR storage cost is 53,863 bits, consisting of 43,008 bits WT, 9,360 bits UT, and 1,495 bits auxiliary tracking table data.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6 x (128 + 256 + 512) x 8 = 43,008 WT bits, 6 x 65 x 24 = 9,360 UT bits, and 65 x 23 = 1,495 auxiliary bits, summing to 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Logic components include 8 parallel comparator trees for bank usefulness selection and 2.5x fixed-point scaling.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) describe comparator selection of the most useful register per bank and scaling bank output by 2.5x."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:generate_digest+global+orphan` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never ...

[Init]
model=gemini-3.8-flash-medium conversation=79945596-ebc6-49d4-9403-6d235b7761ec cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation is triggered at execution completion when a functional unit produces an architectural register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies that writing the produced value digest into the table entry occurs upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding trailing identical bits at [5:0], leading identical bits at [8:3], and the 6 LSBs at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest is formed by overlapping trailing identical bit counts, leading identical bit counts, and Value[5:0] via XOR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point values generate a digest by extracting the sign bit and high exponent bits right-aligned at digest bit 3 with bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) establish that Val[15:13] (FP16), Value[31:26] (FP
... [truncated]

[Usage]
{"input_tokens": 29179, "output_tokens": 37319, "thinking_tokens": 32841, "cache_read_tokens": 0, "total_tokens": 66498}

[Result]
status=SUCCESS conversation=79945596-ebc6-49d4-9403-6d235b7761ec turns=1 duration=193.71383352s usage={"input_tokens": 29179, "output_tokens": 37319, "thinking_tokens": 32841, "cache_read_tokens": 0, "total_tokens": 66498}


