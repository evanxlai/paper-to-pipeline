success: True
usage: {'input_tokens': 31208, 'output_tokens': 45016, 'thinking_tokens': 39631, 'cache_read_tokens': 0, 'total_tokens': 76224}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Staleness and tag tracking triggers at instruction decode when an instruction writes a logical destination register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies that tracking triggers at decode for instructions writing a logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, the destination register entry clears its valid bit and stores the allocated 14-bit ROB tag in its payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper confirms that instruction decode stores the ROB index as a tag and clears the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Register value digests are invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies that each digest is invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Staleness decay advances by scanning all 65 logical registers and incrementing each valid entry's decay counter on every decoded instruction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does hardware advance staleness decay by incrementing an 8-bit counter per entry on each instruction decode, or by comparing an entry timestamp against a global instruction count?",
      "enum_candidates": [
        "per_instruction_counter",
        "global_timestamp",
        "periodic_tick"
      ]
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Digests are invalidated after 256 decoded instructions to prevent stale values from polluting predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms that digests are invalidated after 256 decoded instructions to ensure only up-to-date information influences predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table is a direct-mapped table tracking 65 logical registers (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates the status entry structure with a factor of 65 for the logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each status table entry consists of a 1-bit valid flag, a 14-bit payload holding either a 14-bit tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly defines each entry as containing a valid bit and a payload holding either a 14-bit tag or 12-bit digest, matching Table 3's 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The register status table consumes 1495 bits of storage in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying the 23-bit entry structure by 65 entries directly equals the 1495 bits accounted for in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The register status table is directly indexed by logical register index (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having a dedicated entry per logical register defines direct indexing by logical register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "The usefulness weight tables are organized into 8 banks with 3 tables (UT0, UT1, UT2) of 8 entries each, tracking 9 registers in bank 0 and 8 registers in banks 1-7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies the UT structure as three 8-entry tables per bank across 65 total registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "Each entry in the usefulness weight tables holds an 8- or 9-element vector of 6-bit signed usefulness weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper explicitly defines each entry of the first table as holding an eight- or nine-element vector of weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "The usefulness weight tables consume 9360 bits in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Evaluating the Table 3 formula (6 bits * 65 registers * 24 entries) yields exactly 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "The usefulness weight tables are indexed by a 3-bit skewed index derived from PC.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact hash or folding function is used to derive the 3-bit skewed PC index for UT0, UT1, and UT2?",
      "enum_candidates": [
        "pc_xor_bank",
        "pc_slice",
        "xor_fold"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The prediction weight tables are organized into 8 banks, each containing three tables: WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly specifies 8 banks each containing prediction weight tables with 2^7, 2^8, and 2^9 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Prediction weight table entries are 6-bit signed saturating weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights for each entry in the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The prediction weight tables consume 43008 bits in total.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Multiplying 6 bits by the 7,168 entries across the 8 banks yields exactly 43008 bits as listed in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "WT0, WT1, and WT2 are indexed using hashes combining the PC and register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "PC + reg. digest",
        "why": "Figure 5(c) explicitly labels the combined input to the WT hash functions as 'PC + reg. digest'."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default number of logical registers tracked by the register component is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly dimensions the register status table for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default staleness decay threshold is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default register value digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register value digest as 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default weight width in the prediction weight tables is 6 bits.",
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
      "pointer": "/parameters/7",
      "claim": "The register component prediction sum multiplier for useful predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) literally labels the scaling multiplier in the register component as x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation XOR-folds trailing zero count, leading zero count, and the 6 LSBs of the register value.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U3 notes that 6-bit count encoding (saturation at 63 vs modulo 64 vs counting bits matching sign) and distinguishing leading zeros from ones are not specified in the paper.",
      "enum_candidates": [
        "saturate_63",
        "mod_64",
        "count_matching_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 digest generation places the sign and top 8 exponent bits into digest bits [11:3], leaving bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U4 notes that right-alignment of FP digests at bit 3 (leaving bits [2:0] unused) rather than bit 0 is not explicitly defined in the paper.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag digest generation replicates the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the four condition code flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest is invalidated after 256 subsequent decoded instructions without a register rewrite.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies that each digest is invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank usefulness selection selects the available register with the largest usefulness sum and uses its digest to index the prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states that the component selects the most useful register among available registers and forwards its digest to the prediction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Bank contribution is gated to 0 when the best valid register has a non-positive usefulness sum (usefulness <= 0).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U2 notes that the control wire selecting between x0 and x2.5 is not explicitly labelled, leaving it uncertain whether gating is driven by non-positive bank usefulness or a global static scale.",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Bank contribution is scaled by 2.5 when the best valid register has a positive usefulness sum (usefulness > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U2 notes that the wire selecting between x0 and x2.5 is not explicitly labelled, leaving it uncertain whether scaling by 2.5 is conditionally driven by positive bank usefulness or a global static scale.",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Prediction lookup triggers at branch fetch/prediction time when the branch predictor queries the tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that the table is queried and forwards digests to the SC when the branch predictor makes its prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In each bank, only registers with valid status entries are considered as candidates for usefulness selection.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that only entries whose valid bit is set forward their digest for prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The best register search in each bank is performed by a hardware maximum-finding reduction block ('largest') without requiring unproduced pipeline context or external helper routines.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That vector feeds a block labelled \"largest\", whose output is labelled \"Most useful in this bank.\"",
        "why": "Figure 5(c) confirms that candidate selection is performed by a combinational 'largest' block on the usefulness vector, settling that 'INFINITY' in pseudocode is an argmax initialization idiom rather than unproduced pipeline context."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The raw WT sum is scaled by 2.5 if best usefulness is positive (> 0) and gated to 0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U2 notes that the control wire selecting between x0 and x2.5 is not explicitly labelled, leaving it uncertain whether gating is driven by the bank's usefulness being positive or a global static scale.",
      "enum_candidates": [
        "usefulness_positive",
        "static_scale"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "UT indices and WT indices are computed using dedicated hash functions on PC and register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash or folding algorithms are used to map PC and register digest to the UT (3-bit) and WT (9-bit, 8-bit, 7-bit) table indices?",
      "enum_candidates": [
        "xor_fold",
        "pc_digest_concat",
        "crc_hash"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "The sum sR across all 8 banks is forwarded to the SC summing node to compute LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sB, sG, sP, sC, sI, sL, sS, sT, sR",
        "why": "Figure 5(d) explicitly lists sR among the SC component outputs summed to compute LSUM."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decode_dispatch_track+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they n...

[Init]
model=gemini-3.8-flash-medium conversation=1b5e82f5-4b52-4fe6-aee3-c101c9208dc6 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_bd2489640a39caf1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Staleness and tag tracking triggers at instruction decode when an instruction writes a logical destination register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies that tracking triggers at decode for instructions writing a logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, the destination register entry clears its valid bit and stores the allocated 14-bit ROB tag in its payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper confirms that instruction decode stores the ROB index as a tag and clears the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Register value digests are invalidated after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies that each digest is invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Staleness decay advances by scanning all 65 logical registers and incrementing
... [truncated]

[Usage]
{"input_tokens": 31208, "output_tokens": 45016, "thinking_tokens": 39631, "cache_read_tokens": 0, "total_tokens": 76224}

[Result]
status=SUCCESS conversation=1b5e82f5-4b52-4fe6-aee3-c101c9208dc6 turns=1 duration=253.110505013s usage={"input_tokens": 31208, "output_tokens": 45016, "thinking_tokens": 39631, "cache_read_tokens": 0, "total_tokens": 76224}


