success: True
usage: {'input_tokens': 29055, 'output_tokens': 35171, 'thinking_tokens': 30765, 'cache_read_tokens': 0, 'total_tokens': 64226}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction_decode operation triggers at the decode stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Establishes that the decode-time table updates occur when an instruction is decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Each decoded instruction increments the decay counter of all valid register entries and invalidates any entry whose counter reaches 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Confirms that entries are invalidated once 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When an instruction writing destination register rd decodes, register_status_table[rd] clears the valid bit and stores the 14-bit ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Directly defines that at decode the valid bit is cleared and the ROB index tag is written into the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Storing the ROB index tag at decode invalidates any previous register digest because a new definition is now in flight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Verifies that clearing the valid bit upon decode marks in-flight writes and invalidates earlier digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register_status_table contains 65 entries corresponding to logical registers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms the register status table tracks 65 logical registers across 8 banks (one bank of 9 registers and seven banks of 8 registers)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry format comprises a 1-bit valid flag, a 14-bit payload holding either an ROB index tag or digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data specifies the exact 23-bit structure consisting of valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage cost of register_status_table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines 65 entries of 23 bits each, which evaluates to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register_status_table is direct-mapped by logical register index r for 0 <= r < 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Confirms direct-mapped 1-to-1 indexing per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers tracked by the register components is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sR usefulness table entry expression explicitly scales across 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The legal tuning range for num_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes 65 logical registers to match the evaluated CPU architecture and does not specify a legal tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "num_registers scales UT size by 6 bits * num_registers * 24 and register_status_table by 23 bits * num_registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms 6-bit weights across 3 tables of 8 entries each (24 entries total) per register, and 23 bits per register in auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default decay threshold for invalidating stale digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Explicitly specifies 256 decoded instructions as the invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The legal tuning range for decay_threshold is powers of two from 64 to 1024.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper uses a fixed decay threshold of 256 instructions with an 8-bit counter and does not specify an architectural parameter sweep range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/storage_impact",
      "claim": "log2(decay_threshold) determines the width of the decay counter in register_status_table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates 8 bits for decay_ctr, corresponding to log2(256)."
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
        "why": "Confirms the baseline digest size is 12 bits across all value formats."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The legal tuning range for digest_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed 12-bit digest structure and does not provide an exploration range for digest width.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/storage_impact",
      "claim": "digest_bits affects payload width in register_status_table if it exceeds 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Demonstrates that the payload is sized to the maximum of the tag width (14) and digest width (12)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer value with 6 trailing zeros, 57 leading zeros, and LSBs 0 produces a 12-bit digest of 0x1CE via XOR-folding.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Matches the XOR-folding of trailing count, leading count shifted by 3, and value LSBs shifted by 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A 64-bit floating-point value with bits [63:55] equal to 0b110000000 yields a 12-bit digest of 0xC00.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Confirms FP64 digest extraction uses value bits [63:55] aligned to digest bits [11:3] with low bits zeroed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag register value 0xB produces a 12-bit digest of 0xBBB by three-fold replication.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verifies that the four flag bits are replicated three times into digest bits [11:8], [7:4], and [3:0]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest transitions from valid to invalid on the 256th instruction decode tick if no new writes occur.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Confirms invalidation occurs after exactly 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank 0 selects the available register with the largest cumulative usefulness across UT0-UT2 and scales its weight sum by 2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms selection of the most useful register in the bank and per-bank scaling by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers in a bank are valid at prediction time, training randomly selects exactly one for updates using a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Confirms single-port pseudo-random selection among available registers within a bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The instruction_complete algorithm triggers upon instruction execution completion when writing a value to destination register rd.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that the digest update triggers at execution completion of the writing instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "On instruction complete matching the stored ROB index tag, the entry payload is overwritten with the computed digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that instruction completion validates the entry and stores the digest into payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "FP digest extraction takes bits [63:55] for FP64, bits [31:26] for FP32, and bits [15:13] for FP16, each shifted by 3 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Establishes extraction of the sign bit and top exponent bits for each floating-point width into digest bits [11:3], [8:3], and [5:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Condition code flag digest replicates the 4 flag bits across three nibbles.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Confirms flags replication: flags | (flags << 4) | (flags << 8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Integer register digest generation counts trailing and leading zeros unconditionally rather than counting ones when sign or LSB is 1.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 'count of leading zeros (or ones), the count of trailing zeros (or ones)' but does not define how the zero vs one condition is selected, nor how counts of 64 saturate or truncate into 6-bit fields.",
      "enum_candidates": [
        "zeros_only",
        "match_sign_and_lsb",
        "saturate_63"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Completion updates payload with the 12-bit digest and asserts the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that completion writes the digest and marks the register valid."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_decode+algo:instruction_complete` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=f19134fb-e345-4e85-abc5-834586cf8b97 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction_decode operation triggers at the decode stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Establishes that the decode-time table updates occur when an instruction is decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Each decoded instruction increments the decay counter of all valid register entries and invalidates any entry whose counter reaches 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Confirms that entries are invalidated once 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When an instruction writing destination register rd decodes, register_status_table[rd] clears the valid bit and stores the 14-bit ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Directly defines that at decode the valid bit is cleared and the ROB index tag is written into the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algori
... [truncated]

[Usage]
{"input_tokens": 29055, "output_tokens": 35171, "thinking_tokens": 30765, "cache_read_tokens": 0, "total_tokens": 64226}

[Result]
status=SUCCESS conversation=f19134fb-e345-4e85-abc5-834586cf8b97 turns=1 duration=183.579221113s usage={"input_tokens": 29055, "output_tokens": 35171, "thinking_tokens": 30765, "cache_read_tokens": 0, "total_tokens": 64226}


