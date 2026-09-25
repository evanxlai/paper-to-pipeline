success: True
usage: {'input_tokens': 28553, 'output_tokens': 36354, 'thinking_tokens': 32518, 'cache_read_tokens': 0, 'total_tokens': 64907}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR prediction algorithm triggers during branch prediction / lookup time at fetch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Establishes that valid register digests are forwarded to the register components whenever the predictor queries the table at fetch / prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Logical registers are distributed across 8 banks with stride 8, and only registers with valid == 1 in sR_RegTracker are considered available in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms that the 65 logical registers are partitioned into eight banks of eight or nine registers each, with only valid entries participating in prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "In each bank, the available register with the largest combined usefulness across UT0, UT1, and UT2 is selected to index the bank's weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the predictor determines and selects the most useful available register within the bank to forward to the direction weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Each bank's WT summation is scaled by 2.5 when the bank's selected usefulness is positive and gated to 0 when non-positive or when no registers are available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Confirms that the per-bank weight summation feeds a multiplier stage selecting x0 or x2.5 based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The text 'R(b), R(b+8), ...' in predict_sR is an inline comment illustrating logical register stride rather than a call to an undefined helper function R.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms that R(b) in the pseudocode comment is explanatory notation for the logical register IDs mapped to each bank, refuting the undefined helper finding."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Tables UT0, UT1, and UT2 are indexed at depth 2 by bank-local register index r_local_idx, which spans the same domain [0, 8] as r_idx in update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Settles that each UT entry holds an 8- or 9-element vector indexed by bank-local register offset, refuting the inconsistent index warning."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The exact hash functions hash_ut(PC), hash_wt0(PC, digest), hash_wt1(PC, digest), and hash_wt2(PC, digest) are defined in the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper notes that UT is indexed by 'PC (skewed)' and WT tables are indexed by PC and digest hashed into h0, h1, and h2, but does not provide the concrete hashing or skewing implementations.",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "bit_select"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Bank 0 holds 9 registers (stride 8: 0, 8, ..., 64) and Banks 1-7 hold 8 registers each, with scaling applied per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms that logical registers are partitioned across eight banks with 9 registers in Bank 0 and 8 in the remaining banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT comprises 8 banks of 3 direct-mapped sub-tables (WT0: 512, WT1: 256, WT2: 128 entries of signed 6-bit weights), totaling 7,168 entries and 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Directly specifies 8 banks of three sub-tables with 128, 256, and 512 entries of 6-bit weights totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT comprises 8 banks of 3 sub-tables with 8 entries each, where each entry is a vector of signed 6-bit usefulness counters (9 for Bank 0, 8 for Banks 1-7), totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Directly confirms 6-bit weights across 65 registers and three 8-entry tables, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_RegTracker comprises 65 entries of format { valid: 1 bit, payload: 14 bits, decay_ctr: 8 bits }, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Directly specifies the entry format and 65-entry dimension totaling 23 * 65 = 1,495 bits in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "Parameter num_banks has default value 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Establishes that the default organization contains 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "Parameter num_logical_registers has default value 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Establishes that the total count of logical registers tracked across the banks is 65."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Parameter useful_multiplier has default value 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Confirms the positive usefulness scaling factor of 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Parameter wt_entries_0 has default value 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms WT0 entry count per bank is 2^9 = 512."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Parameter wt_entries_1 has default value 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms WT1 entry count per bank is 2^8 = 256."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Parameter wt_entries_2 has default value 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Confirms WT2 entry count per bank is 2^7 = 128."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Parameter ut_entries_per_subtable has default value 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Confirms each of the three UT sub-tables contains 8 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Condition code flags value 0x9 (0b1001) replicates three times to produce a 12-bit digest of 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Settles that the 4-bit condition code flags are replicated three times to construct the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The expected 12-bit INT digest for trailing_cnt = 4, leading_cnt = 60, and lsb6 = 16 evaluates to 1500 (0x5DC).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The test assertion states that 4 ^ 480 ^ 1024 evaluates to 1500 (0x5DC), whereas bitwise XOR arithmetic yields 1508 (0x5E4). In addition, the paper does not specify test vectors or count encoding semantics for 64-bit integer values.",
      "enum_candidates": [
        "1508",
        "1500"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For FP32 with Val[31:26] = 0b101101, extracting bits [31:26] into digest bits [8:3] with bits [2:0] = 0 produces digest 0x168.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Confirms that FP32 values extract Value[31:26] into digest bits [8:3], yielding (0b101101 << 3) = 0x168."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Register valid bit transitions from 1 to 0 upon reaching 256 decoded instructions without an update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Settles that entries decay and are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Between available registers R0 (usefulness = 14) and R8 (usefulness = 5), R0 is selected as the most useful register in Bank 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the available register with the greatest usefulness is selected to index WT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When the selected register has usefulness <= 0, the bank contribution is multiplied by x0, contributing 0 to sR_sum.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Confirms that non-positive usefulness causes the bank weight sum to be gated by x0."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.8-flash-medium conversation=82ec3c65-d0bb-454c-85c0-77f5883800c4 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR prediction algorithm triggers during branch prediction / lookup time at fetch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Establishes that valid register digests are forwarded to the register components whenever the predictor queries the table at fetch / prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Logical registers are distributed across 8 banks with stride 8, and only registers with valid == 1 in sR_RegTracker are considered available in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Confirms that the 65 logical registers are partitioned into eight banks of eight or nine registers each, with only valid entries participating in prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "In each bank, the available register with the largest combined usefulness across UT0, UT1, and UT2 is selected to index the bank's weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Settles that the predictor determines and selects the most useful available register within the bank to forward to the direction weight tables."
      },
      "patch": null,
      "open_question": null,
      "
... [truncated]

[Usage]
{"input_tokens": 28553, "output_tokens": 36354, "thinking_tokens": 32518, "cache_read_tokens": 0, "total_tokens": 64907}

[Result]
status=SUCCESS conversation=82ec3c65-d0bb-454c-85c0-77f5883800c4 turns=1 duration=192.148488501s usage={"input_tokens": 28553, "output_tokens": 36354, "thinking_tokens": 32518, "cache_read_tokens": 0, "total_tokens": 64907}


