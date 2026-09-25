success: True
usage: {'input_tokens': 32870, 'output_tokens': 25492, 'thinking_tokens': 23033, 'cache_read_tokens': 0, 'total_tokens': 58362}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "At decode, a register-writing instruction clears the valid bit and stores its ROB index in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode accurately implements the invalidation and tag storage described."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "tomasulo_table has 65 entries, each with 1 valid bit, 14 payload bits, and 8 decay_ctr bits, totalling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly lists the dimensions of the auxiliary data for sR, matching the size formula and total bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 shows the table is scaled for exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The unit test initializes the decay counter to decay_threshold (256), which does not fit in the 8-bit counter.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper dictates a 256-instruction lifetime. Because the hardware counter is 8 bits, it must be initialized to 255 to expire after 256 decodes."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "A register is completed (update_tomasulo) setting its decay_ctr to 255. decay_tomasulo is triggered 256 times.",
          "expect": "After 255 triggers, decay_ctr is 0 and valid is 1. On the 256th trigger, valid is set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The expected value of the digest computation for value 0x000000000000000F is unspecified.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The test expectation leans on a hedge word. Given value 15 (60 leading zeros, 0 trailing), the digest must explicitly evaluate to 544 based on the XOR folding."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F (60 leading zeros, 0 trailing zeros).",
          "expect": "compute_digest computes the folded value 544 and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "predict selects the register with the highest usefulness to look up weights and sums them.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test precisely verifies the selection of the most useful register's digest for weight lookup."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "update randomly selects one available register from the bank to adjust usefulness correlations.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The test validates the random selection of one available register for the usefulness update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "squash recovery clears the payload of entries allocated by squashed instructions and sets them valid.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves recovery to future work, so the test's expectation is an invented behavior."
      },
      "patch": null,
      "open_question": "What is the correct recovery behavior for tomasulo_table on a branch squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "When an instruction completes, it overwrites the payload with the digest, sets valid, and initializes decay_ctr.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The pseudocode mirrors the described behavior for completing instructions and triggering the decay timeout."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "decay_threshold defaults to 256 and has no direct storage impact.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The default value of 256 collides with the 8-bit capacity of decay_ctr, and the storage_impact description collides with the requirement to state 'None'."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/10",
        "value": {
          "name": "decay_threshold",
          "type": "int",
          "default": 256,
          "range": "[1, 1024]",
          "storage_impact": "None. The 8-bit counter is seeded at 256 - 1 and the span is 255, assuming decay_ctr_bits is large enough."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The decay counter width is 8 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms decay_ctr is exactly 8 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tomasulo decrements the decay counter and invalidates the entry on reaching 0, triggered per decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Decrementing the counter per decoded instruction and invalidating at 0 implements the 256-instruction lifetime."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "recover_tomasulo assumes a lightweight rollback based on ROB ID age.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves recovery to future work, making the provided rollback algorithm an invention."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a branch squash, given the paper leaves it as future work?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The default number of inflight branches is 128.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "We used the default configuration, which simulates a processor with a fetch width of 16 and a frontend depth of 10.",
        "why": "The paper does not state the capacity of the branch metadata queue or the maximum number of inflight branches."
      },
      "patch": null,
      "open_question": "What is the maximum number of inflight branches the predictor must support, which sizes the inflight_prediction_metadata?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:allocate_tomasulo+algo:update_tomasulo+algo:decay_tomasulo+algo:recover_tomasulo` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding...

[Init]
model=gemini-3.1-pro-high conversation=dbf7336e-3bf7-44cb-b5f2-5449259755d7 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "At decode, a register-writing instruction clears the valid bit and stores its ROB index in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode accurately implements the invalidation and tag storage described."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "tomasulo_table has 65 entries, each with 1 valid bit, 14 payload bits, and 8 decay_ctr bits, totalling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly lists the dimensions of the auxiliary data for sR, matching the size formula and total bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 shows the table is scaled for exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The unit test initializes the decay counter to decay_threshold (256), which does not fit in the 8-bit counter.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper dictates a 256-instruction lifetime. Because the hardware counter is 8 bits, it must be initialized to 255 to expire after 256 decodes."
      },
      
... [truncated]

[Usage]
{"input_tokens": 32870, "output_tokens": 25492, "thinking_tokens": 23033, "cache_read_tokens": 0, "total_tokens": 58362}

[Result]
status=SUCCESS conversation=dbf7336e-3bf7-44cb-b5f2-5449259755d7 turns=1 duration=141.442900821s usage={"input_tokens": 32870, "output_tokens": 25492, "thinking_tokens": 23033, "cache_read_tokens": 0, "total_tokens": 58362}


