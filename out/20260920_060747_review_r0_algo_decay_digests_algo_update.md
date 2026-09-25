success: True
usage: {'input_tokens': 20746, 'output_tokens': 17684, 'thinking_tokens': 15649, 'cache_read_tokens': 8147, 'total_tokens': 38430}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "Digest decay is triggered on every instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that the invalidation happens based on the number of subsequent instructions that have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Digest Table contains 65 entries, with an entry format including an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the register auxiliary data as 65 entries, each with a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The sR Prediction Weight Table (WT) consists of 8 banks, each containing three tables of 512, 256, and 128 entries with 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the dimensions of the sR WT, confirming 8 banks of tables with 128, 256, and 512 entries, and 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default decay period is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text directly states that digests are invalidated after 256 subsequent instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The digest width generated from a register value is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The text specifies the digest is exactly 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The expected result of the INT digest generation test is concretely defined.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper defines the bitwise inputs to the digest, allowing a concrete expected value to be calculated, but the spec's test expectation is vacuous."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "INT Digest Generation",
          "given": "An INT register value of 0x0000000000000005.",
          "expect": "The resulting 12-bit digest is 0x0A8 (XOR of trailing count 0 at bits 5:0, leading count 61 at bits 8:3, and value 5 at bits 11:6)."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The valid bit for a register's digest transitions to 0 after 256 instructions without updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper confirms that a digest is invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predictor selects the digest of the register with the highest usefulness weight in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The text specifies that the most useful register is chosen to supply its digest to the WT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank's WT output is multiplied by 0 if its selected best register has a negative UT weight.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper confirms usefulness weights exist, but does not explicitly state the condition (such as a negative weight) that triggers the x0 path shown in Figure 5(c)."
      },
      "patch": null,
      "open_question": "What condition selects the x0 versus x2.5 multiplier for a bank's output?",
      "enum_candidates": [
        "x2.5 is used if the selected register's usefulness weight is non-negative (>= 0), otherwise x0.",
        "x2.5 is used if the selected register's usefulness weight is strictly positive (> 0), otherwise x0.",
        "The multiplier is fixed at 2.5 and x0 is only used when no valid register is available in the bank."
      ]
    },
    {
      "pointer": "/algorithms/5",
      "claim": "The exact update policies for the WT and UT are specified.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper states which registers to update, but omits the precise arithmetic rules or conditions for updating the WT and UT weights."
      },
      "patch": null,
      "open_question": "What are the exact update rules for the WT and UT weights in the register component?",
      "enum_candidates": [
        "WT is updated like a standard SC weight, and UT is incremented on correct prediction and decremented on incorrect.",
        "WT and UT are updated using the exact same formulas as the base TAGE-SC-L usefulness and weight components.",
        "UT is incremented if the bank's WT prediction matches the branch outcome, and decremented otherwise."
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The sR Usefulness Weight Table (UT) has 3 tables of 8 entries, with each entry holding 65 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 details the dimensions of the sR UT as three 8-entry tables, each holding 65 6-bit weights."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decay_digests+algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read...

[Init]
model=gemini-3.1-pro-high conversation=41d488ce-b119-4cf7-881d-ec50a03a1d45 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_2cbf45e4f50cc3ef

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3",
      "claim": "Digest decay is triggered on every instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that the invalidation happens based on the number of subsequent instructions that have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Digest Table contains 65 entries, with an entry format including an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly sizes the register auxiliary data as 65 entries, each with a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The sR Prediction Weight Table (WT) consists of 8 banks, each containing three tables of 512, 256, and 128 entries with 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the dimensions of the sR WT, confirming 8 banks of tables with 128, 256, and 512 entries, and 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default decay period is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Th
... [truncated]

[Usage]
{"input_tokens": 20746, "output_tokens": 17684, "thinking_tokens": 15649, "cache_read_tokens": 8147, "total_tokens": 38430}

[Result]
status=SUCCESS conversation=41d488ce-b119-4cf7-881d-ec50a03a1d45 turns=1 duration=120.953579179s usage={"input_tokens": 20746, "output_tokens": 17684, "thinking_tokens": 15649, "cache_read_tokens": 8147, "total_tokens": 38430}


