success: True
usage: {'input_tokens': 32869, 'output_tokens': 31767, 'thinking_tokens': 27507, 'cache_read_tokens': 0, 'total_tokens': 64636}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The x0 or x2.5 multiplier is controlled by whether the bank's most useful register has a usefulness greater than 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U2 specifies that the drawing does not label the wire selecting the x0/x2.5 multiplier, making it uncertain whether the bank's own usefulness drives it."
      },
      "patch": null,
      "open_question": "What signal controls the 'x0 or x2.5' multiplier for a bank in the register component? Figure 5(c) shows the multiplier but the selection wire is unlabelled (note U2).",
      "enum_candidates": ["bank_useful_positive", "global_useful_positive"]
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Registers are assigned to banks using a modulo stride, where bank i holds registers r with r % num_banks == i.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note I10 indicates that the bank membership (R0, R8, R16 for bank 0) is inferred from the drawing and not stated explicitly in prose."
      },
      "patch": null,
      "open_question": "How are logical registers mapped to the 8 banks? Figure 5(c) shows R0, R8, R16 for bank 0, implying a modulo stride, but the prose does not confirm this.",
      "enum_candidates": ["modulo_stride", "contiguous_blocks"]
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The UT tables use three distinct hashes of the PC: hash_ut(PC, 0), hash_ut(PC, 1), and hash_ut(PC, 2).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Figure 5(c) labels the UT input simply as 'PC (skewed)' for all three tables, without specifying if they use distinct hash functions."
      },
      "patch": null,
      "open_question": "Do the three UT tables (UT0, UT1, UT2) use the same skewed PC index, or distinct hashes of the PC?",
      "enum_candidates": ["distinct_hashes", "same_skewed_pc"]
    },
    {
      "pointer": "/state/0",
      "claim": "The sR_WT state is organized into 8 banks with 3 tables per bank, storing signed 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 details the storage for sR, showing 8 banks of weight tables sized 128, 256, and 512 entries with 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The sR_UT state consists of 3 tables per bank, sized to cover 65 logical registers with 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies the UT size as 65 logical registers by three 8-entry tables of 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "The in-flight state requires 16,640 bits of storage.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "The total storage cost is 1570890 bits (191.75 KiB), compliant with the CBP2025 rules.",
        "why": "The paper's exact total storage budget of 1570890 bits precisely matches the sum of Tables 2 and 3 without leaving any bits for an additional 16,640-bit in-flight branch queue."
      },
      "patch": {
        "op": "replace",
        "pointer": "/state/3",
        "value": {
          "name": "sR_InFlightState",
          "organization": "FIFO queue, one entry per in-flight branch",
          "entry_format": "Bitmask of valid registers at prediction time",
          "size_bits": 0,
          "size_formula": "0 * inflight_branches * num_logical_regs",
          "indexing": "ROB index / in-flight branch ID"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The predictor uses 8 banks for the register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the register component is divided into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly models storage for 65 logical registers in the UT and auxiliary data tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The WT0 table has a default of 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines the largest WT table size as 2^9 (512) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The WT1 table has a default of 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines the middle WT table size as 2^8 (256) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The WT2 table has a default of 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines the smallest WT table size as 2^7 (128) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The UT0 table has a default of 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 lists three tables of 2^3 (8) entries for the UT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The UT1 table has a default of 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 lists three tables of 2^3 (8) entries for the UT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The UT2 table has a default of 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 lists three tables of 2^3 (8) entries for the UT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The weight width for WT and UT tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly models the weights for both WT and UT as 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The rob_idx_bits parameter dictates a 14-bit payload for the ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly states the payload accommodates a 14-bit tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The default number of in-flight branches to track is 256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper states modern processors have 'an ROB capable of storing over 500 instructions' but does not specify the exact number of in-flight branches the predictor must track in its state."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor tracks at once? The paper mentions ROBs of 'over 500 instructions' but does not fix a parameter for in-flight branches.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The default usefulness multiplier is 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Figure 5(c) shows 'x0 or x2.5', but the paper provides no prose statement at least 12 characters long confirming this scalar value."
      },
      "patch": null,
      "open_question": "What is the exact usefulness multiplier for register components? Figure 5(c) labels a stage 'x0 or x2.5', but the value lacks prose confirmation.",
      "enum_candidates": ["2.5", "2.0", "3.0"]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The digest validity clears after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper dictates invalidating the digest after 256 decoded instructions, matching the test's expectations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The INT register digest uses absolute count of leading zeros and trailing zeros.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U3 states it is uncertain how the leading/trailing counts are encoded (e.g., saturated, modulo 64, or counting sign-bit matches), so the test's exact expected counts cannot be verified."
      },
      "patch": null,
      "open_question": "How are the leading and trailing counts encoded for INT register digests? Note U3 indicates ambiguity over whether the count saturates at 63, wraps modulo 64, or tracks sign-bit matches.",
      "enum_candidates": ["saturate_63", "modulo_64", "sign_bit_matches"]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The register component selects the most useful valid register to index the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper expressly states that only the single most useful register's digest is selected for table lookup."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Training randomly selects one valid register from the bank for the update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies updating only one randomly selected available register per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A pipeline squash clears the pending payload to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper states that recovering the Tomasulo-like table may present challenges and defers the mechanism to future work, without detailing squash behavior."
      },
      "patch": null,
      "open_question": "How does a pipeline squash (recovery) affect the Tomasulo-like table's pending payloads? The paper defers the recovery mechanism to future work.",
      "enum_candidates": ["clear_payload", "restore_checkpoint", "ignore"]
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
model=gemini-3.1-pro-high conversation=f93c7b82-a3ca-4d2e-b5ae-db2e7137cd93 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "The x0 or x2.5 multiplier is controlled by whether the bank's most useful register has a usefulness greater than 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note U2 specifies that the drawing does not label the wire selecting the x0/x2.5 multiplier, making it uncertain whether the bank's own usefulness drives it."
      },
      "patch": null,
      "open_question": "What signal controls the 'x0 or x2.5' multiplier for a bank in the register component? Figure 5(c) shows the multiplier but the selection wire is unlabelled (note U2).",
      "enum_candidates": ["bank_useful_positive", "global_useful_positive"]
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Registers are assigned to banks using a modulo stride, where bank i holds registers r with r % num_banks == i.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Note I10 indicates that the bank membership (R0, R8, R16 for bank 0) is inferred from the drawing and not stated explicitly in prose."
      },
      "patch": null,
      "open_question": "How are logical registers mapped to the 8 banks? Figure 5(c) shows R0, R8, R16 for bank 0, implying a modulo stride, but the prose does not confirm this.",
      "enum_candidates": ["modulo_stride", "contiguous_blocks"]
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The UT tables use three distinct hashes of the PC: hash_ut(PC, 0), hash_ut(PC, 1), and hash_ut(PC, 2).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "Figure 5(c) labels the UT input simply as 'PC (skewed)' for all three tables, without specifying if they use distinct hash functions."
      },
      "patch": null,
      "open_question": "Do the three UT tables (UT0, UT1, UT2) use the same skewed PC index, or distinct hashes of the PC?",
      "enum_candidates": [
... [truncated]

[Usage]
{"input_tokens": 32869, "output_tokens": 31767, "thinking_tokens": 27507, "cache_read_tokens": 0, "total_tokens": 64636}

[Result]
status=SUCCESS conversation=f93c7b82-a3ca-4d2e-b5ae-db2e7137cd93 turns=1 duration=170.481733014s usage={"input_tokens": 32869, "output_tokens": 31767, "thinking_tokens": 27507, "cache_read_tokens": 0, "total_tokens": 64636}


