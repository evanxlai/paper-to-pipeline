success: True
usage: {'input_tokens': 28734, 'output_tokens': 33395, 'thinking_tokens': 28292, 'cache_read_tokens': 0, 'total_tokens': 62129}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tick is triggered at the decode stage and invoked once for each instruction decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies tracking freshness and triggering digest invalidation based on subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tick increments the 8-bit decay counter for valid entries across all 65 registers and invalidates entries when the counter reaches 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines an 8-bit decay counter per register entry, which counts up to 256 decoded instructions before invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "Stale register digests degrade accuracy and are evicted after 256 instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text directly establishes that stale digests degrade accuracy and must be invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table is a direct-mapped table with 65 entries corresponding to logical registers R0 through R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The text establishes a dedicated direct-mapped tracking entry for each of the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Each tracking table entry consists of a 1-bit valid flag, a 14-bit payload holding either an in-flight ROB index or a 12-bit digest, and an 8-bit unsigned decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The text details the valid bit and 14-bit payload format, with Table 3 confirming the 8-bit decay counter field."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The total storage cost of the register tracking table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 establishes that 65 entries of 23 bits (1 + 14 + 8) each equal 1495 bits of auxiliary storage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table is directly indexed by logical register index from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The dedicated 1:1 correspondence between logical registers and tracking entries specifies direct indexing by register index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default value of decay_instruction_limit is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text explicitly states 256 decoded instructions as the invalidation limit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "decay_instruction_limit has a tuning exploration range of [64, 1024] in powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed threshold of 256 decoded instructions and does not evaluate or define an exploration range for tuning decay_instruction_limit.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "decay_instruction_limit impacts tracking table storage by num_logical_registers * ceil(log2(decay_instruction_limit)) bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 budgets an 8-bit counter per entry to represent counters up to 256 across all 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The division into 8 banks of 8 or 9 registers confirms 65 logical registers in total, matching Table 3's factor of 65."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "num_logical_registers has a tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates an architecture with exactly 65 logical registers (R0 through R64) and does not define a tuning range for num_logical_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "num_logical_registers scales the UT vector width and reg_tracking_table entry count.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper establishes that the usefulness vector width per entry and the tracking table size directly scale with the number of registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "wt0_entries has a default value of 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) explicitly specifies 512 entries for WT0 in each register component bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "wt0_entries has a tuning range of [128, 2048] in powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper hardcodes WT0 to 512 entries without stating an exploration range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "wt0_entries storage impact equals num_banks * wt0_entries * weight_width bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 calculates WT storage as 8 banks times 6-bit weights times the sum of table entry counts including 2^9 entries for WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt1_entries has a default value of 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) explicitly labels WT1 as having 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt1_entries has a tuning range of [64, 1024] in powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes WT1 entry count to 256 and does not define a tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt1_entries storage impact equals num_banks * wt1_entries * weight_width bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 accounts for 2^8 entries of 6 bits each across 8 banks for WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt2_entries has a default value of 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) explicitly labels WT2 as having 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt2_entries has a tuning range of [32, 512] in powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes WT2 to 128 entries per bank without providing a tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt2_entries storage impact equals num_banks * wt2_entries * weight_width bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 accounts for 2^7 entries of 6 bits each across 8 banks for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_subtable has a default value of 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) specifies 8 entries per subtable for UT0, UT1, and UT2, confirmed by 2^3 in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_subtable has a tuning range of [4, 64] in powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not define an exploration range for UT entries per subtable.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_subtable storage impact equals num_logical_registers * 3 * ut_entries_per_subtable * weight_width bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates UT storage as 6-bit weights across 65 registers and three 8-entry subtables (2^3 + 2^3 + 2^3)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation produces digest 995 (0x3E3) for value 0x8 by XOR-folding trailing zero count, leading zero count shifted by 3, and value[5:0] shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and the text establish the 3-field XOR structure: trailing zeros at [5:0], leading zeros at [8:3], and LSB[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 digest generation places Val[63:55] at digest bits [11:3] yielding digest 0x400 for value 0x4014000000000000.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies extracting Value[63:55] aligned to digest bits [11:3] for 64-bit floats."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition-code flag digest generation replicates 4-bit nibble 0xB three times to form 12-bit digest 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The text directly states that the 4-bit condition code is replicated 3 times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Decoding 256 instructions without writes to a register causes its decay counter to saturate/exceed 255 and its valid bit to transition from 1 to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text specifies invalidating the digest entry after 256 instructions have been decoded without new writes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank register selection picks the register with the largest usefulness, scaling WT output by 2.5 if usefulness is positive or gating to 0 if non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Figure 5(c) specifies selecting the largest usefulness value in each bank and scaling by 2.5 or suppressing by 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Digests of instructions that completed execution before a squash remain valid across pipeline squashes to assist post-recovery predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The text states that values from instructions finished before the misprediction is revealed remain available to the predictor upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6",
      "claim": "Squash recovery is triggered on pipeline squash or branch misprediction redirect.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The text establishes that predictor recovery logic engages when a branch misprediction is revealed and the pipeline flushes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6",
      "claim": "squash_recovery invalidates in-flight tracking entries whose ROB index matches a flushed instruction bitmask.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 5 explicitly states that recovering the Tomasulo-like table is future work; the paper does not specify how flushed in-flight entries are identified or whether a flushed ROB bitmask is used. Additionally, the 'if(...)' syntax flagged in the deterministic findings represents a built-in language conditional rather than an undefined helper function. How should in-flight entries be handled upon squash?",
      "enum_candidates": [
        "rob_mask_clear",
        "flash_clear",
        "no_recovery"
      ]
    },
    {
      "pointer": "/algorithms/6",
      "claim": "Valid digests from instructions that finished execution before the squash remain valid across pipeline flushes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The text explicitly confirms that finished values are preserved across the flush to assist predictions after recovery."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decay_tick+algo:squash_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=591c38fc-81bf-44be-a11a-16645ad25efc cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tick is triggered at the decode stage and invoked once for each instruction decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies tracking freshness and triggering digest invalidation based on subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tick increments the 8-bit decay counter for valid entries across all 65 registers and invalidates entries when the counter reaches 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines an 8-bit decay counter per register entry, which counts up to 256 decoded instructions before invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "Stale register digests degrade accuracy and are evicted after 256 instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Preliminary experiments revealed that stale digests degrade prediction accuracy. Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text directly establishes that stale digests degrade accuracy and must be invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table is a dire
... [truncated]

[Usage]
{"input_tokens": 28734, "output_tokens": 33395, "thinking_tokens": 28292, "cache_read_tokens": 0, "total_tokens": 62129}

[Result]
status=SUCCESS conversation=591c38fc-81bf-44be-a11a-16645ad25efc turns=1 duration=169.076201866s usage={"input_tokens": 28734, "output_tokens": 33395, "thinking_tokens": 28292, "cache_read_tokens": 0, "total_tokens": 62129}


