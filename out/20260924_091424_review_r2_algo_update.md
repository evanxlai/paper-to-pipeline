success: True
usage: {'input_tokens': 33040, 'output_tokens': 27828, 'thinking_tokens': 24377, 'cache_read_tokens': 0, 'total_tokens': 60868}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Correlations are updated only for logical registers that were available at prediction time, selecting one randomly if multiple are available in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The pseudocode correctly filters for available registers and picks one randomly per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The update algorithm uses a specific PRNG to randomly select a register and a specific mathematical formula to calculate the utility delta.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper states that a random register is selected and correlations are updated, but provides no PRNG algorithm (random_int) or utility delta formula (calculate_utility_delta)."
      },
      "patch": null,
      "open_question": "How are the calculate_utility_delta and random_int functions implemented for the register component update?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT is organized as 8 banks with 3 tables per bank, storing 6-bit weights for a total of 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the Register component's weight tables as 8 banks of 3 tables with 6-bit entries, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT stores usefulness weights for 65 logical registers across 8 banks and 3 tables, totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the Usefulness weight table for the Register component as 65 vectors of three 8-entry tables with 6-bit weights, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "sR_InFlightState tracks the bitmask of valid registers per in-flight branch and consumes 16640 bits of the predictor's storage budget.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 states the exact total storage for the sR component is 53863 bits, leaving 0 bits for this in-flight state table. However, the prediction algorithm that allocates this state is missing from the provided elements, so the necessary coordinated patch cannot be completed here."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register components are divided into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly shows a multiplier of 8 for the register component weight tables."
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
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 shows a multiplier of 65 for the usefulness tables and auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the weight table sizes as powers of 2, with the largest being 2^9 (512)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the middle weight table size as 2^8 (256)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "WT2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the smallest weight table size as 2^7 (128)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "UT0 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies all three usefulness tables have 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "UT1 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies all three usefulness tables have 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "UT2 has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies all three usefulness tables have 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "Weights in WT and UT are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 indicates a width of 6 bits for both the weight tables and usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The ROB index used as a tag is 14 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper explicitly states the tag payload is 14 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "There are exactly 256 in-flight branches to track.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "In contrast, today's most powerful CPUs have a fetch width of ten instructions and an ROB capable of storing over 500 instructions.",
        "why": "The paper mentions an ROB of over 500 instructions but does not definitively state the number of in-flight branches the predictor is dimensioned for."
      },
      "patch": null,
      "open_question": "What is the exact maximum number of in-flight branches (inflight_branches) the predictor must support?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The digest decay counter walks down to 0 after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies a 256-instruction decay threshold before a digest is invalidated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The count of leading zeros/ones for integer registers is encoded by always counting zeros, producing 0 for a negative number.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones)",
        "why": "As noted in U3, the paper is ambiguous on whether the count distinguishes zeros vs ones with an extra bit, or simply counts bits matching the MSB; this test assumes it always counts zeros without evidence."
      },
      "patch": null,
      "open_question": "For integer registers, how does the digest encode the count of leading/trailing 'zeros (or ones)'? Does it always count zeros, or does it count bits matching the MSB/LSB?",
      "enum_candidates": [
        "always_count_zeros",
        "count_matching_msb"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predictor uses the digest of the most useful available register in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The prose states that the component selects the most useful register's digest for indexing the weight table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Updates select a random register from those available in the bank at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that one available register is randomly selected for the update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A pipeline squash recovery clears the pending payload to 0 while keeping valid=0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the mechanism for recovering the register table after a pipeline squash to future work."
      },
      "patch": null,
      "open_question": "How is the sR_RegTable state correctly recovered upon a pipeline squash?",
      "enum_candidates": [
        "clear_payload",
        "restore_checkpoint",
        "ignore"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A claim...

[Init]
model=gemini-3.1-pro-high conversation=ee83e5a0-ab63-455a-bdb5-e4c1d64f5738 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Correlations are updated only for logical registers that were available at prediction time, selecting one randomly if multiple are available in a bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The pseudocode correctly filters for available registers and picks one randomly per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The update algorithm uses a specific PRNG to randomly select a register and a specific mathematical formula to calculate the utility delta.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper states that a random register is selected and correlations are updated, but provides no PRNG algorithm (random_int) or utility delta formula (calculate_utility_delta)."
      },
      "patch": null,
      "open_question": "How are the calculate_utility_delta and random_int functions implemented for the register component update?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT is organized as 8 banks with 3 tables per bank, storing 6-bit weights for a total of 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the Register component's weight tables as 8 banks of 3 tables with 6-bit entries, totaling 43008 bits."
      },
      "patch": null,
      "open_question": nul
... [truncated]

[Usage]
{"input_tokens": 33040, "output_tokens": 27828, "thinking_tokens": 24377, "cache_read_tokens": 0, "total_tokens": 60868}

[Result]
status=SUCCESS conversation=ee83e5a0-ab63-455a-bdb5-e4c1d64f5738 turns=1 duration=218.498279542s usage={"input_tokens": 33040, "output_tokens": 27828, "thinking_tokens": 24377, "cache_read_tokens": 0, "total_tokens": 60868}


