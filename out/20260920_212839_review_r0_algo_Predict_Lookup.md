success: True
usage: {'input_tokens': 28237, 'output_tokens': 31778, 'thinking_tokens': 28271, 'cache_read_tokens': 0, 'total_tokens': 60015}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Predict (Lookup) is triggered at fetch / lookup time when computing Statistical Corrector inputs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 states that the register table forwards valid digests to the SC register components whenever the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The lookup iterates across 8 register banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 establishes that the register component is partitioned into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "In algorithm predict_sR, indexing UT at depth 4 with register variable r operates over the same register domain for bank b as chosen_reg in Update (Training).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Section 4.2 establishes that each bank entry holds a vector of usefulness weights for the registers of that bank, so r and chosen_reg reference registers within the same bank domain."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Usefulness is computed by summing weights from three 8-entry usefulness tables (UT0, UT1, UT2) indexed by skewed PC hashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) specifies three 8-entry usefulness tables per bank indexed by PC."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The register with the highest usefulness among available valid registers is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 specifies selecting the digest of the most useful available register within the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Prediction weights are looked up from three weight tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) specifies WT0, WT1, and WT2 capacities as 512, 256, and 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The bank weight sum is scaled by 2.5 when positive usefulness is detected, and masked with 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows each bank's prediction weight sum feeding an output scaling stage of x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry in the Register Tracking Table contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay_ctr across 65 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the auxiliary scoreboard state as 65 entries with valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "The payload stores either a 14-bit ROB tag when invalid or a 12-bit register value digest when valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 states that the payload holds either a 14-bit tag or a 12-bit digest depending on whether the valid bit is clear or set."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "The Usefulness Weight Tables (UT) comprise 8 banks tracking 65 registers across three 8-entry tables per bank with 6-bit signed weights totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines UT storage as 6-bit weights for 65 registers across three 2^3-entry tables, yielding 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The Prediction Weight Tables (WT) consist of 8 banks each having three tables of 512, 256, and 128 entries with 6-bit weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of 128, 256, and 512 entries storing 6-bit weights totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default number of register banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly specifies that the component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default prediction weight table entry sizes are 512, 256, and 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) labels the three prediction weight tables per bank as having 512, 256, and 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default usefulness table entry count per table is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 specify 8 entries per usefulness table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "decay_threshold default value is 256, but decay_ctr is an 8-bit field with maximum representable value 255.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "Section 4.2 specifies invalidation after 256 decoded instructions while Table 3 allocates an 8-bit decay_ctr (max value 255); an initial default of 255 provides 256 distinct count states (255 down to 0) to span 256 steps without exceeding the 8-bit field limit."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/3/default",
        "value": 255
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "bank_useful_multiplier default is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly labels the bank output multiplier as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "num_tracked_registers default is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 indicates 65 entries in the register tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XORing trailing zeros/ones count, leading zeros/ones count shifted by 3, and the lowest 6 value bits shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "Section 4.2 and Figure 6(a) specify the 12-bit integer digest format by XORing the 6-bit trailing count, 6-bit leading count at bit 3, and 6-bit value slice at bit 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags digest replicates the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) establish that condition-code flags replicate the 4 bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Digests in the scoreboard decay with decoded instructions and invalidate when the decay counter expires.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that digests are invalidated after subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A bank with positive usefulness scales its weight sum by 2.5, while an invalid or non-positive bank contributes 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies multiplying bank output by 2.5 when useful or 0 when not useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers are available in the same bank, one is randomly selected for updates to allow single-write-port tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 describes randomly selecting one register among available ones in a bank during training."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:Predict (Lookup)` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the pape...

[Init]
model=gemini-3.8-flash-medium conversation=8a0bc60d-1c35-4fed-ae2c-41f8bb93dbb8 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "Predict (Lookup) is triggered at fetch / lookup time when computing Statistical Corrector inputs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 states that the register table forwards valid digests to the SC register components whenever the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The lookup iterates across 8 register banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 establishes that the register component is partitioned into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "In algorithm predict_sR, indexing UT at depth 4 with register variable r operates over the same register domain for bank b as chosen_reg in Update (Training).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Section 4.2 establishes that each bank entry holds a vector of usefulness weights for the registers of that bank, so r and chosen_reg reference registers within the same bank domain."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Usefulness is computed by summing weights from three 8-ent
... [truncated]

[Usage]
{"input_tokens": 28237, "output_tokens": 31778, "thinking_tokens": 28271, "cache_read_tokens": 0, "total_tokens": 60015}

[Result]
status=SUCCESS conversation=8a0bc60d-1c35-4fed-ae2c-41f8bb93dbb8 turns=1 duration=168.015625462s usage={"input_tokens": 28237, "output_tokens": 31778, "thinking_tokens": 28271, "cache_read_tokens": 0, "total_tokens": 60015}


