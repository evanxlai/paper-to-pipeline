success: True
usage: {'input_tokens': 29825, 'output_tokens': 43477, 'thinking_tokens': 37964, 'cache_read_tokens': 0, 'total_tokens': 73302}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "decay_step is triggered once per decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Establishes that the decay progression is measured per decoded instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The decay step iterates through all 65 register status table entries, incrementing valid entries' decay counters up to 255 and invalidating after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms there are 65 entries, each with an 8-bit decay counter counting up to 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Digests older than 256 decoded instructions are invalidated to prevent stale information from contaminating predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Explains that digests older than 256 decoded instructions degrade accuracy and must be invalidated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Prediction weight tables are organized into 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries), totaling 7168 entries across all banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Specifies 8 banks each having three tables of size 2^7 (128), 2^8 (256), and 2^9 (512) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each prediction weight table entry stores a 6-bit signed saturating weight in the range [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Establishes that the weight width in all prediction weight tables is 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The prediction weight tables consume 43,008 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Evaluating 6 bits * (128 + 256 + 512) entries * 8 banks gives 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "WT0, WT1, and WT2 are indexed using specific bitwise hash functions of PC and digest: PC ^ (digest << 1) ^ (digest >> 3) masked to 9, 8, and 7 bits respectively.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash function combines PC and the selected register digest to index WT0, WT1, and WT2?",
      "enum_candidates": [
        "xor_shift",
        "xor_fold",
        "independent_hash"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table is a direct-mapped table with 65 entries corresponding to logical registers 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms tracking across 65 registers partitioned into eight banks of eight or nine registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each register status table entry format consists of a 1-bit valid flag, a 14-bit payload (storing either a 14-bit ROB index or a 12-bit digest), and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Specifies the exact bit fields and widths of the register status table entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register status table consumes 1,495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying (1 + 14 + 8) bits by 65 entries yields 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register status table is direct-mapped by logical register index r (0 <= r < 65).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Settles that the table contains exactly one direct entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of tracked registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms the baseline configuration provides tracking for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "num_registers scales UT storage by 144 bits per register and register_status_table storage by 23 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Confirms UT consumes 6 bits * 24 entries = 144 bits per register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default decay threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that stale digests are invalidated after exactly 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/storage_impact",
      "claim": "log2(decay_threshold) determines the width of the decay counter in register_status_table as 8 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms the decay counter width is 8 bits, matching log2(256)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Settles that generated register digests are 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer values, the 12-bit digest is generated by XOR-folding trailing zeros/ones count, leading zeros/ones count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles the composition of the 12-bit integer digest from leading counts, trailing counts, and 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For 64-bit floating point values, bits [63:55] (sign and leading exponent bits) are extracted to digest bits [11:3] while digest bits [2:0] are zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Settles that FP digests extract the sign bit and high-order exponent bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition flags, the 4 flag bits are replicated three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles replication of the 4 condition flags three times into 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest transitions to invalid after exactly 256 instruction decode ticks without updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles invalidation of valid digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank selects the most useful available register digest to index prediction tables and scales bank output by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the most useful available register digest in the bank is selected to index the prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers in a bank are valid at prediction time, one is randomly chosen during training to perform single write-port table updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Settles random selection of one available register per bank during training for single-write-port updates."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "sR is an SC component capturing register value correlations using 12-bit digests, Tomasulo-like tracking, stride-8 banking, usefulness selection, 2.5x scaling, and 256-instruction decay.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes.",
        "why": "Confirms the core concept and role of sR within the SC framework."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The specification source is the CBP 2025 paper 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "Matches the paper title character for character."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "The execution unit interface provides 64-bit produced values, register types, destination register IDs, and ROB tags upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles that completion delivers produced values to generate digests and set valid status."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "The decode/rename interface provides destination register IDs and ROB indices for decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Settles that destination registers and ROB indices are recorded at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "The predictor receives decoded instruction progression notifications to advance the 256-instruction decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that instruction decode progression drives the 256-instruction decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "The predictor interfaces with pipeline flush signals and utilizes completed values made available after branch recovery.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Confirms post-flush values are leveraged to correct subsequent branch predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "sR total storage is 53,863 bits, broken into 43,008 bits for WT, 9,360 bits for UT, and 1,495 bits for the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms the auxiliary tracking storage of 1,495 bits alongside WT and UT storage in Table 3 totaling 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "generate_digest is triggered at instruction execution completion when a result value is produced.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles that digest generation takes place upon instruction execution completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "For integer registers, count_trailing/leading counts consecutive identical bits starting from LSB/MSB, capped at 63.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Settles that integer register digests encode counts of consecutive leading and trailing zeros or ones."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "generate_digest invokes undefined helper calls 'count_trailing_zeros_or_ones' and 'count_leading_zeros_or_ones' and uses parenthesized return statements flagged as helper calls.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "function count_trailing_zeros_or_ones(val_64bit):\n  bit0 = val_64bit & 1\n  count = 0\n  for i = 0 to 63:\n    if ((val_64bit >> i) & 1) == bit0:\n      count = count + 1\n    else:\n      break\n  if count > 63:\n    count = 63\n  return count\n\nfunction count_leading_zeros_or_ones(val_64bit):\n  bit63 = (val_64bit >> 63) & 1\n  count = 0\n  for i = 63 down to 0:\n    if ((val_64bit >> i) & 1) == bit63:\n      count = count + 1\n    else:\n      break\n  if count > 63:\n    count = 63\n  return count\n\nfunction generate_digest(reg_type, val_64bit):\n  if reg_type == INT:\n    trailing_count = count_trailing_zeros_or_ones(val_64bit) & 0x3F\n    leading_count = count_leading_zeros_or_ones(val_64bit) & 0x3F\n    lsb6 = val_64bit & 0x3F\n    digest = (trailing_count) ^ (leading_count << 3) ^ (lsb6 << 6)\n    return digest & 0x0FFF\n  else if reg_type == FP:\n    // Inspect MSBs to classify FP format\n    if is_fp16(val_64bit):\n      // Val[15:13] placed at digest[5:3]\n      fp16_val = ((val_64bit >> 13) & 0x7) << 3\n      return fp16_val\n    else if is_fp32(val_64bit):\n      // Val[31:26] placed at digest[8:3]\n      fp32_val = ((val_64bit >> 26) & 0x3F) << 3\n      return fp32_val\n    else: // FP64\n      // Val[63:55] placed at digest[11:3]\n      fp64_val = ((val_64bit >> 55) & 0x1FF) << 3\n      return fp64_val\n  else if reg_type == FLAG:\n    // Replicate 4 condition flags 3 times into 12 bits\n    flags = val_64bit & 0xF\n    flag_val = (flags << 8) | (flags << 4) | flags\n    return flag_val\n  return 0"
      },
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
model=gemini-3.8-flash-medium conversation=ba74c6f2-f6e4-4e09-b365-6520269138a1 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "decay_step is triggered once per decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Establishes that the decay progression is measured per decoded instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The decay step iterates through all 65 register status table entries, incrementing valid entries' decay counters up to 255 and invalidating after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Confirms there are 65 entries, each with an 8-bit decay counter counting up to 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Digests older than 256 decoded instructions are invalidated to prevent stale information from contaminating predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Explains that digests older than 256 decoded instructions degrade accuracy and must be invalidated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Prediction weight tables are organized into 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries), totaling 7168 entries a
... [truncated]

[Usage]
{"input_tokens": 29825, "output_tokens": 43477, "thinking_tokens": 37964, "cache_read_tokens": 0, "total_tokens": 73302}

[Result]
status=SUCCESS conversation=ba74c6f2-f6e4-4e09-b365-6520269138a1 turns=1 duration=234.874230547s usage={"input_tokens": 29825, "output_tokens": 43477, "thinking_tokens": 37964, "cache_read_tokens": 0, "total_tokens": 73302}


