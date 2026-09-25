success: True
usage: {'input_tokens': 30040, 'output_tokens': 36691, 'thinking_tokens': 33815, 'cache_read_tokens': 0, 'total_tokens': 66731}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR update algorithm is triggered during branch update/commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper specifies predictor training updating correlations based on available register state and branch outcome."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update algorithm randomly selects one register for update if several registers were available in the same bank at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies randomly selecting one available register per bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Training updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that were available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Usefulness table entries are updated by evaluating whether the bank weight table lookup sum matches the actual branch outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are usefulness table (UT) weights updated during training, and what condition determines whether an entry was useful?",
      "enum_candidates": [
        "bank_correct",
        "sc_correct",
        "tage_mispred_sc_correct"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Random selection of one available register per bank during training ensures each table requires only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that the random selection training method ensures each table needs only a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT comprises 8 banks of 3 usefulness tables each with 8 entries storing 6-bit weights for 65 logical registers totalling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper defines the usefulness table structure as holding vectors of weights reflecting usefulness per bank across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_WT comprises 8 banks with 3 prediction weight tables per bank (WT0 with 512 entries, WT1 with 256 entries, WT2 with 128 entries) storing 6-bit counters totalling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists the three prediction weight table sizes per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component sR is partitioned into 8 banks.",
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
      "claim": "WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 512 entries for WT0."
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
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 256 entries for WT1."
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
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly specifies 128 entries for WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "Each usefulness table has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) explicitly specifies 8 entries each for UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Stale digests are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states the digest decay threshold of 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The register digest size is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register digest length as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests encode counts with leading zeros shifted by 3 and XOR folded with trailing counts and Value[5:0].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 64-bit integer leading and trailing counts bounded or encoded into 6 bits, how is zero vs one count distinguished, and how are the fields combined?",
      "enum_candidates": [
        "saturate",
        "wrap",
        "sign_match"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flag registers produce a 12-bit digest by replicating the 4-bit flag value three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly describes replicating the four flag bits three times to generate the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 register digests place sign and exponent bits at positions [11:3] with bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are floating-point register digest bits right-aligned at bit position 3 leaving bits [2:0] zero, or right-aligned at bit position 0?",
      "enum_candidates": [
        "bit_3",
        "bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated and marked unavailable after 256 subsequent instructions are decoded without register updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank contributions are scaled by x0 when the bank usefulness sum is non-positive and by x2.5 when positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is the x0 vs x2.5 scaling factor dynamically driven per bank by that bank's usefulness sum being positive, or is there a static multiplier?",
      "enum_candidates": [
        "bank_usefulness",
        "static_2.5"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers in a bank are available at prediction time, the update algorithm randomly chooses exactly one register to update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly specifies random selection of one available register per bank during training to preserve single write port access."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A claim...

[Init]
model=gemini-3.8-flash-medium conversation=6d1f5d3a-b18b-4fed-9f9d-733399131b26 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The sR update algorithm is triggered during branch update/commit time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper specifies predictor training updating correlations based on available register state and branch outcome."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The update algorithm randomly selects one register for update if several registers were available in the same bank at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies randomly selecting one available register per bank during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Training updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper explicitly restricts training updates to registers that were available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Usefulness table entries are updated by evaluating whether the bank weight table lookup sum matches the actual branch outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
   
... [truncated]

[Usage]
{"input_tokens": 30040, "output_tokens": 36691, "thinking_tokens": 33815, "cache_read_tokens": 0, "total_tokens": 66731}

[Result]
status=SUCCESS conversation=6d1f5d3a-b18b-4fed-9f9d-733399131b26 turns=1 duration=202.918575223s usage={"input_tokens": 30040, "output_tokens": 36691, "thinking_tokens": 33815, "cache_read_tokens": 0, "total_tokens": 66731}


