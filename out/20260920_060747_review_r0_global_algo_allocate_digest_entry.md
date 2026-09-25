success: True
usage: {'input_tokens': 19910, 'output_tokens': 21709, 'thinking_tokens': 18898, 'cache_read_tokens': 8145, 'total_tokens': 41619}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector to capture correlations between register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes.",
        "why": "Explicitly confirms the component extends the SC for this purpose."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The predictor generates 12-bit digests of register values upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that digests are generated and cached precisely at instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "At prediction time, the component selects the digest of the most useful valid register among those available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms the selection logic for the most useful register digest at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Stale digests are invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Explicitly states the threshold of 256 decoded instructions for invalidating a digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The paper title is RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "Matches the exact paper title provided."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "The predictor needs to observe architectural register writes at decode time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms that register writes must be intercepted at instruction decode to manage valid bits and tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "The predictor needs the register value and type at instruction completion to generate the digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Confirms that generating the correct 12-bit digest requires both the 64-bit value and its type."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "The predictor requires an instruction decode event to track decay.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Confirms that instruction decode events must be tracked to perform invalidations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component requires a total of 53863 storage bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 explicitly lists 53863 bits as the total storage for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "At instruction decode, if an instruction writes logical register R, its valid bit is cleared and the ROB index is stored.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode perfectly aligns with this description of decode-time behavior."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "The payload field temporarily holds a 14-bit tag (ROB index) until the value is produced.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Confirms the payload is sized to store a 14-bit tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Digest Table is a flat array containing one entry per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Confirms the one-to-one mapping."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The table entry format is valid (1), payload (14), decay_ctr (8).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly these fields and bit widths for the auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The total size of the Register Digest Table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "An entry with 1+14+8 = 23 bits across 65 entries calculates exactly to 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The digest width is a tunable parameter with a valid range of [8, 16].",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value",
        "why": "The paper hardcodes a 12-bit digest with fixed bitwise field layouts in Figure 6, which directly contradicts a parameterized width."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/2/range",
        "value": "[12, 12]"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The INT digest output must explicitly state a fully calculated expected value for the test to be closed.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The spec provides the inputs but uses 'correctly' instead of calculating the exact deterministic output value needed for the test expectation."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0/expect",
        "value": "The 12-bit digest is 0x0A8 (computed as 0x000 ^ (61 << 3) ^ (5 << 6), assuming counts of zeros are used)."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A register's valid bit transitions to 0 after 256 instructions are decoded without updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Explicitly confirms the 256 instruction delay for invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predictor selects the register digest in a bank whose UT weight is highest among valid registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms that the register with maximum usefulness is selected."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "If the selected best register in a bank has a negative UT weight, the bank's WT output is multiplied by 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) shows a conditional multiplier of x0 or x2.5 for the bank, but does not state that a negative UT weight is the condition that selects x0."
      },
      "patch": null,
      "open_question": "What exact condition drives the 'x0 or x2.5' multiplier for a register bank's WT output in the sR component?",
      "enum_candidates": [
        "The selected maximum UT weight is negative",
        "The selected maximum UT weight is less than or equal to zero",
        "A separate global usefulness metric evaluates to negative"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+algo:allocate_digest_entry` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never r...

[Init]
model=gemini-3.1-pro-high conversation=06213627-f163-430f-b0f1-4ba6aca94909 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_2cbf45e4f50cc3ef

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector to capture correlations between register values and branch outcomes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes.",
        "why": "Explicitly confirms the component extends the SC for this purpose."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The predictor generates 12-bit digests of register values upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that digests are generated and cached precisely at instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "At prediction time, the component selects the digest of the most useful valid register among those available.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms the selection logic for the most useful register digest at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Stale digests are invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Explicitly states the threshold of 256 decoded instructions for invalidating a digest."
... [truncated]

[Usage]
{"input_tokens": 19910, "output_tokens": 21709, "thinking_tokens": 18898, "cache_read_tokens": 8145, "total_tokens": 41619}

[Result]
status=SUCCESS conversation=06213627-f163-430f-b0f1-4ba6aca94909 turns=1 duration=145.388303417s usage={"input_tokens": 19910, "output_tokens": 21709, "thinking_tokens": 18898, "cache_read_tokens": 8145, "total_tokens": 41619}


