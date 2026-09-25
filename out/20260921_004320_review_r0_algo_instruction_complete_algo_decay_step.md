success: True
usage: {'input_tokens': 28757, 'output_tokens': 31515, 'thinking_tokens': 26897, 'cache_read_tokens': 0, 'total_tokens': 60272}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The instruction completion handler triggers at execution stage when an instruction completes execution and produces a value for register rd.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies updating the register status table entry when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Completion only overwrites the entry if valid is 0 and the stored payload matches the completing instruction's 14-bit ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Tracking in-flight instructions via a Tomasulo-like tag matching the 14-bit ROB index ensures only the pending producer updates the register entry upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "On completion, the payload is updated with the generated 12-bit digest and the valid bit is asserted to 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that completing instructions overwrite the payload with the produced value's digest and set valid to 1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "On completion, the entry's decay counter is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Resetting the decay counter to 0 on entry completion initializes the 256 decoded-instruction freshness window."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The decay step triggers once per decoded instruction at decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Invalidating digests after 256 subsequent instructions have been decoded requires incrementing age counters per decoded instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "For each valid register entry, the 8-bit decay counter increments on each decode tick until reaching 256 elapsed instructions, at which point valid transitions to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The loop increments decay_ctr up to 255 and clears the valid bit on the 256th decode tick, matching the paper's invalidation policy."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table has 65 entries corresponding to logical registers 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the auxiliary data of the sR component as 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each register status table entry contains a 1-bit valid flag, a 14-bit payload holding either a ROB index or digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 details the exact bit widths of each entry in the register status table as valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage cost of the register status table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "23 bits per entry multiplied across 65 logical register entries sums exactly to 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register status table is direct-mapped by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies dedicated 1:1 mapping with one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly sizes the register usefulness tables across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The parameter num_registers has a legal tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates a fixed architecture with 65 logical registers and does not define a tuning range for num_registers; what is the legal range?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "Scaling num_registers scales the usefulness tables by 6 bits * num_registers * 24 and the status table by 23 bits * num_registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 uses 6 bits * 24 entries per register for UT and 23 bits per entry for the status table."
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
        "why": "The paper explicitly specifies 256 subsequent decoded instructions as the invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The parameter decay_threshold has a legal tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes decay threshold at 256 instructions and does not describe parameter sweeps; what is the legal range for decay_threshold?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/storage_impact",
      "claim": "The decay counter width in the register status table is log2(decay_threshold).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "log2(256) is 8 bits, which matches the 8-bit decay_ctr entry width in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines digests to be 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The parameter digest_bits has a legal tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes digest size at 12 bits and does not define an exploration range for digest_bits; what is the legal range?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/storage_impact",
      "claim": "Digest bits affect payload width in the register status table only if digest_bits exceeds 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Because the payload accommodates a 14-bit ROB tag, a digest width <= 14 bits does not expand the 14-bit payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer values, the 12-bit digest is generated by XOR-folding the trailing zero/one count at [5:0], leading zero/one count at [8:3], and value[5:0] at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and the text specify XOR-folding the 6-bit trailing count [5:0], 6-bit leading count [8:3], and 6-bit value LSBs [11:6] into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For 64-bit floating point values, the 12-bit digest places Value[63:55] in digest[11:3] and zeroes bits [2:0].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP64\"  ->  Value[63:55]",
        "why": "Figure 6(b) specifies extracting 9-bit Value[63:55] into digest bits [11:3], producing 0xC00 for sign/exponent bits 0b110000000."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition flags, the 12-bit digest replicates the 4-bit flag value three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states replicating the 4-bit flag value three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest entry invalidates on the 256th subsequent instruction decode tick if no new write occurs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests exactly after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank 0 selects the valid register digest with the highest cumulative usefulness (UT0+UT1+UT2) and scales bank output by 2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) specify selecting the most useful register in the bank and scaling the prediction by x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers in a bank are valid at prediction time, training pseudo-randomly selects one of them to update, accessing a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly dictates random single-register selection among available registers per bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "Prediction weight tables comprise 8 banks, each containing WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries), totaling 7168 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 and Figure 5(c) specify 8 banks with table sizes 2^9 (512), 2^8 (256), and 2^7 (128) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Prediction weight table entries are 6-bit signed saturating weights [-32, 31].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines entries in WT as 6-bit signed weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total size of the prediction weight tables across all banks is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * (128 + 256 + 512) * 8 equals exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "WT0, WT1, and WT2 use 9-bit, 8-bit, and 7-bit indices respectively.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Table capacities of 512, 256, and 128 entries require index widths of 9, 8, and 7 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The table index hash functions use the specific formula (PC ^ (digest << 1) ^ (digest >> 3)).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) notes that PC and reg. digest are hashed to produce indices h0, h1, h2, but does not provide the hashing algorithm or bit shift amounts; what hash function should be used?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_complete+algo:decay_step` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they...

[Init]
model=gemini-3.8-flash-medium conversation=6a1d9069-43db-4c45-96a2-10e85a6d4afc cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The instruction completion handler triggers at execution stage when an instruction completes execution and produces a value for register rd.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies updating the register status table entry when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Completion only overwrites the entry if valid is 0 and the stored payload matches the completing instruction's 14-bit ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Tracking in-flight instructions via a Tomasulo-like tag matching the 14-bit ROB index ensures only the pending producer updates the register entry upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "On completion, the payload is updated with the generated 12-bit digest and the valid bit is asserted to 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that completing instructions overwrite the payload with the produced value's digest and set valid to 1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "On compl
... [truncated]

[Usage]
{"input_tokens": 28757, "output_tokens": 31515, "thinking_tokens": 26897, "cache_read_tokens": 0, "total_tokens": 60272}

[Result]
status=SUCCESS conversation=6a1d9069-43db-4c45-96a2-10e85a6d4afc turns=1 duration=173.587447671s usage={"input_tokens": 28757, "output_tokens": 31515, "thinking_tokens": 26897, "cache_read_tokens": 0, "total_tokens": 60272}


