success: True
usage: {'input_tokens': 29807, 'output_tokens': 37949, 'thinking_tokens': 31714, 'cache_read_tokens': 0, 'total_tokens': 67756}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The decay step is invoked once per decoded instruction to track instruction progress.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests after 256 subsequent decoded instructions, establishing the per-decoded-instruction trigger."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "For each valid register in the status table, the 8-bit counter increments each cycle and invalidates the entry upon reaching 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines an 8-bit decay counter per register across 65 entries to count up to 256 instructions before invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Decay invalidation prevents stale digests older than 256 decoded instructions from degrading branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that stale digests degrade accuracy and must be invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Prediction weight tables comprise 8 banks with 3 tables each (WT0: 512, WT1: 256, WT2: 128 entries), totaling 7168 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks containing tables with 2^7 (128), 2^8 (256), and 2^9 (512) entries each, totaling 7168 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each WT entry is a 6-bit signed saturating counter weight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT entry width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "Total storage capacity of the prediction weight tables is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Multiplying 6 bits by (128 + 256 + 512) entries across 8 banks yields exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The index for WT0 is computed specifically as (PC ^ (digest << 1) ^ (digest >> 3)) & 0x1FF.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper notes in Figure 5(c) that PC and the selected register digest are hashed into h0, h1, and h2, but does not provide the specific bit-mixing polynomial or shift amounts.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table is direct-mapped with 65 entries corresponding to logical registers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 states there is one dedicated entry per logical register, matching the 65 entries specified in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each register status table entry contains a 1-bit valid flag, a 14-bit payload for ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 defines the 1-bit valid flag and 14-bit payload, and Table 3 confirms { valid (1), payload (14), decay_ctr (8) }."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register status table requires 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries * (1 + 14 + 8) bits = 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register status table is direct-mapped indexed by logical register ID.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one entry per logical register establishes direct indexing by logical register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "RUNLTS uses a default of 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the register component across 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The parameter num_registers has a valid tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes 65 logical registers based on its target ISA evaluation and does not specify a legal parameter range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "The parameter num_registers scales UT size by 144 bits per register and status table size by 23 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 assigns 6 bits * 24 entries to UT and 23 bits to status table per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default decay threshold is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The parameter decay_threshold has a tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses only the fixed 256-instruction decay threshold and does not specify a tuning exploration range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/storage_impact",
      "claim": "The width of the decay counter in the register status table is log2(decay_threshold).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "An 8-bit counter corresponds to log2(256) bits to track up to 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly establishes that each register digest is 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The digest width has a tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates only a fixed 12-bit digest and does not define a variable range for tuning.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/storage_impact",
      "claim": "A digest width greater than 14 bits affects the payload width in the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Because the payload accommodates either a 14-bit tag or the digest, increasing digest bits beyond 14 would enlarge the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer 0x40, digest generation XOR-folds 6 trailing zeros, 57 leading zeros, and 6 LSBs into 0x1CE.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify XORing trailing zeros [5:0], leading zeros shifted by 3 [8:3], and LSBs shifted by 6 [11:6], yielding 0x006 ^ 0x1C8 ^ 0x000 = 0x1CE."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For FP64 with bits [63:55] = 0b110000000, digest[11:3] receives the slice and bits [2:0] are zero, yielding 0xC00.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Extracting FP64 bits [63:55] placed at digest[11:3] produces 0b110000000_000 = 0xC00, matching Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flags 0b1011 are replicated three times into 12 bits to produce 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 4 condition flags three times produces 0xBBB as stated in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest in register status table entry transitions to invalid on the 256th instruction decode tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank selects the register digest with highest cumulative usefulness and scales the bank output by 2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 specifies selecting the most useful available register digest, and Figure 5(c) specifies the x2.5 bank scaling multiplier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, when multiple registers in a bank are valid, exactly one is randomly chosen for table updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that when multiple registers are available in a bank, one is randomly selected for training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "sR is a neural SC component tracking register digests across 65 registers and 8 banks, scaling useful predictions by 2.5 and invalidating after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The register components yielded the largest and broadest gain, improving every trace category.",
        "why": "The summary faithfully reflects the architecture and performance findings detailed in Sections 4.2 and 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper citation is RUNLTS from CBP 2025 by Koizumi et al.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The citation text matches the published CBP 2025 paper verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "RUNLTS requires host interfaces for completion value forwarding, decode/rename ROB tag registration, and retirement progression counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 defines the required interface interactions at instruction decode, execution completion, and decode progression."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "sR total storage is 53863 bits, consisting of 43008 bits WT, 9360 bits UT, and 1495 bits status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 confirms the exact bit budget breakdown and 53863-bit total for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest is triggered when an instruction finishes execution and produces a result value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 specifies generating and recording the digest when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer digest generation XOR-folds trailing count, leading count shifted by 3, and 6 LSBs shifted by 6 into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) specifies the XOR-folded overlapping bit slices [5:0], [8:3], and [11:6] forming the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Helper function count_trailing_zeros_or_ones counts identical consecutive trailing bits capped at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 'count of trailing zeros (or ones)' in 6 bits but does not clarify whether trailing zeros, trailing ones, or consecutive bits matching the LSB are counted, nor how the 0-64 count is saturated or wrapped into 6 bits.",
      "enum_candidates": [
        "matching_lsb",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Helper function count_leading_zeros_or_ones counts identical consecutive leading bits capped at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 'count of leading zeros (or ones)' in 6 bits but does not clarify whether leading zeros, leading ones, or consecutive bits matching the MSB are counted, nor how the 0-64 count is saturated or wrapped into 6 bits.",
      "enum_candidates": [
        "matching_msb",
        "zeros_only",
        "ones_only"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The generate_digest algorithm uses 'return' as a standard pseudocode language control-flow statement rather than an undefined helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper specifies that digest generation computes and produces a 12-bit digest, which the pseudocode implements using the standard 'return' keyword."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating point format classification is determined by inspecting MSBs via helper functions is_fp16 and is_fp32.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states 'we inspect the most significant bits to classify the format' but does not specify the exact bit tests or MSB patterns that distinguish FP16, FP32, and FP64 within a 64-bit register.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating point digests place Val[15:13] at digest[5:3] for FP16, Value[31:26] at digest[8:3] for FP32, and Value[63:55] at digest[11:3] for FP64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies extracting sign and exponent bits right-aligned at digest bit 3 for each precision."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "FLAG digest replicates the 4 condition flags three times into digest bits [11:8], [7:4], and [3:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) define replicating the 4-bit flag value three times across the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "The produced digest is exactly 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly establishes that register digests are 12 bits wide."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decay_step+global+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; th...

[Init]
model=gemini-3.8-flash-medium conversation=eadcee55-1bdd-4dbf-b62c-7b000db4265f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The decay step is invoked once per decoded instruction to track instruction progress.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests after 256 subsequent decoded instructions, establishing the per-decoded-instruction trigger."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "For each valid register in the status table, the 8-bit counter increments each cycle and invalidates the entry upon reaching 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines an 8-bit decay counter per register across 65 entries to count up to 256 instructions before invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Decay invalidation prevents stale digests older than 256 decoded instructions from degrading branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that stale digests degrade accuracy and must be invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": 
... [truncated]

[Usage]
{"input_tokens": 29807, "output_tokens": 37949, "thinking_tokens": 31714, "cache_read_tokens": 0, "total_tokens": 67756}

[Result]
status=SUCCESS conversation=eadcee55-1bdd-4dbf-b62c-7b000db4265f turns=1 duration=203.970370939s usage={"input_tokens": 29807, "output_tokens": 37949, "thinking_tokens": 31714, "cache_read_tokens": 0, "total_tokens": 67756}


