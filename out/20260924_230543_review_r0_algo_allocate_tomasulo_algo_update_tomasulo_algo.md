success: True
usage: {'input_tokens': 31991, 'output_tokens': 31740, 'thinking_tokens': 28268, 'cache_read_tokens': 0, 'total_tokens': 63731}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Allocation clears the valid bit and stores the producer's ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode correctly assigns the ROB index to payload and sets valid to 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Allocation in the tomasulo table happens at instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states the allocation occurs at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "The table has one entry per logical register containing a 1-bit valid flag, 14-bit payload/tag, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies the entry format with these exact fields and sizes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "The table size is the sum of its fields multiplied by the number of logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 scales the bit sizes by 65, corresponding to the logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The number of logical registers tracked is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly states the auxiliary data is replicated 65 times, matching the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The unit test for the decay counter must assert the values over its lifecycle step by step.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The finding untested_counter_lifecycle requires the test to state the intermediate counter value rather than just its terminal effect."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expires",
          "given": "update_tomasulo sets decay_ctr to 255. decay_tomasulo is triggered 256 times.",
          "expect": "After 255 triggers, decay_ctr is 0 and valid is 1. On the 256th trigger, valid is set to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The integer digest test must use a concrete input value and state the exact expected arithmetic result.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits",
        "why": "The finding vacuous_test requires the expectation to state the exact computed result instead of the hedge word 'correct'."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F.",
          "expect": "compute_digest computes the folded value 544 (0 ^ (60 << 3) ^ (15 << 6)) and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predict step selects the single most useful register in a bank and looks up its prediction weights using its digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test correctly expects predict to choose the register with the highest usefulness and use its digest for the WT lookups."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "Update randomly selects one of the available registers to adjust the usefulness weights.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states the selection among available registers must be random, whereas the test just says 'selects'."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/3/expect",
        "value": "update reads the chosen digest to adjust wt0, wt1, wt2, and randomly selects one available register from the mask to adjust ut0, ut1, ut2."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Squash recovery invalidates entries allocated by squashed instructions.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper leaves recovery as future work, so the tested rollback behavior is an unsupported assumption."
      },
      "patch": null,
      "open_question": "What is the correct recovery mechanism for the Tomasulo table on a squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The update to the digest and valid bit happens when the instruction completes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper clearly states that the update happens upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The exact compute_digest logic for counting zeroes/ones and classifying floating point formats is not fully defined.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones)... For floating-point registers, we inspect the most significant bits to classify the format",
        "why": "The paper does not detail whether counts saturate, wrap, or track the sign bit, nor does it explain the FP classification logic for non-floats."
      },
      "patch": null,
      "open_question": "How are 6-bit leading/trailing counts handled for 64-bit bounds, and what is the exact mechanism for classifying FP formats?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay counter initialization must seed the counter such that it can span 256 instructions in an 8-bit field.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The finding ambiguous_counter_span flags that a 256 lifespan in an 8-bit counter cannot be seeded with 256. It must be seeded with 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "if instruction_writes_register:\n  r = instruction.dest_logical_reg\n  rob = instruction.rob_index\n  if tomasulo_table[r].valid == 0 and tomasulo_table[r].payload == rob:\n    tomasulo_table[r].payload = compute_digest(instruction.value, instruction.type)\n    tomasulo_table[r].valid = 1\n    tomasulo_table[r].decay_ctr = (decay_threshold - 1) & ((1 << decay_ctr_bits) - 1)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The decay_threshold parameter does not scale storage.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The finding storage_param_unaccounted flags that the parameter incorrectly claims a storage impact despite not being used in any size formula."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/10",
        "value": {
          "name": "decay_threshold",
          "type": "int",
          "default": 256,
          "range": "[1, 1024]",
          "storage_impact": "None."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11/default",
      "claim": "The decay counter field is 8 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly assigns 8 bits to the decay_ctr field."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "Decay is triggered on every instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper explicitly ties the invalidation countdown to instruction decodes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The decay counter must decrement 255 times and invalidate the register on the 256th decode.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The finding ambiguous_counter_span requires an encoding spanning exactly 256 decodes using a max value of 255. The counter must reach 0 on the 255th decode and invalidate on the 256th."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/pseudocode",
        "value": "for r in 0 .. num_logical_regs - 1:\n  if tomasulo_table[r].valid == 1:\n    if tomasulo_table[r].decay_ctr == 0:\n      tomasulo_table[r].valid = 0\n    else:\n      tomasulo_table[r].decay_ctr -= 1"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Recovery of the Tomasulo-like table on branch squash invalidates entries allocated by younger instructions.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the recovery strategy to future work, so the assumed rollback strategy is not supported."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a branch squash, given the paper defers this to future work?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12/default",
      "claim": "The number of inflight branches supported is 128.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "simulates a processor with a fetch width of 16 and a frontend depth of 10.",
        "why": "The paper details simulation parameters and instruction capacities but does not state a specific 128 limit for the number of in-flight branches."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor metadata must support?",
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
model=gemini-3.1-pro-high conversation=89bdd584-c683-4760-b693-4fbb5874bb44 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Allocation clears the valid bit and stores the producer's ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode correctly assigns the ROB index to payload and sets valid to 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Allocation in the tomasulo table happens at instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states the allocation occurs at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "The table has one entry per logical register containing a 1-bit valid flag, 14-bit payload/tag, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies the entry format with these exact fields and sizes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "The table size is the sum of its fields multiplied by the number of logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 scales the bit sizes by 65, corresponding to the logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": n
... [truncated]

[Usage]
{"input_tokens": 31991, "output_tokens": 31740, "thinking_tokens": 28268, "cache_read_tokens": 0, "total_tokens": 63731}

[Result]
status=SUCCESS conversation=89bdd584-c683-4760-b693-4fbb5874bb44 turns=1 duration=431.394346405s usage={"input_tokens": 31991, "output_tokens": 31740, "thinking_tokens": 28268, "cache_read_tokens": 0, "total_tokens": 63731}


