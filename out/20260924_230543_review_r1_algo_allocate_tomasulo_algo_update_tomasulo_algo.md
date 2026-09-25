success: True
usage: {'input_tokens': 33168, 'output_tokens': 24150, 'thinking_tokens': 21526, 'cache_read_tokens': 0, 'total_tokens': 57318}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "allocate_tomasulo clears the valid bit and records the ROB index on instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It explicitly describes the decode-time operations matching the pseudocode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "tomasulo_table contains 65 entries of {valid, payload (14), decay_ctr (8)}.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The component sizes and total entry count precisely match the structure described."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The multiplier 65 corresponds to the number of tracked logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay_counter_expires test verifies a 256-step countdown using an 8-bit counter.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The original test initializes the 8-bit counter to 256, which overflows; it must be initialized to 255 and tested for 256 triggers."
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
      "claim": "The digest_computation_int test checks the exact folded digest value for a specific input.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1",
        "value": {
          "name": "digest_computation_int",
          "given": "update_tomasulo is called for an INT instruction with value 0x000000000000000F (60 leading zeros, 0 trailing zeros).",
          "expect": "compute_digest computes the folded value 544 (0 ^ (60 << 3) ^ (15 << 6)) and stores it in tomasulo_table."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "predict selects the digest of the most useful register among those available in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "It explicitly states that the most useful digest is selected and forwarded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "update randomly selects one available register in the same bank to adjust usefulness weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "It explicitly describes the random selection among available registers in a bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "squash_recovery tests that entries allocated by squashed instructions are invalidated based on ROB ID age.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves the recovery logic to future work."
      },
      "patch": null,
      "open_question": "How should the Tomasulo-like table be recovered on a branch squash, as the paper leaves this to future work?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "update_tomasulo seeds the decay counter to wait for 256 subsequent instructions.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "Assigning 256 to an 8-bit counter overflows it; the counter must be seeded at decay_threshold - 1 (255) to correctly span the needed delay."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2",
        "value": {
          "name": "update_tomasulo",
          "trigger": "instruction complete",
          "pseudocode": "if instruction_writes_register:\n  r = instruction.dest_logical_reg\n  rob = instruction.rob_index\n  if tomasulo_table[r].valid == 0 and tomasulo_table[r].payload == rob:\n    tomasulo_table[r].payload = compute_digest(instruction.value, instruction.type)\n    tomasulo_table[r].valid = 1\n    tomasulo_table[r].decay_ctr = (decay_threshold - 1) & ((1 << decay_ctr_bits) - 1)",
          "notes": "Writes the computed digest and sets the valid bit if the entry was waiting for this specific instruction."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "decay_threshold has a direct storage impact.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The storage requirement comes entirely from the 8-bit width of the counter, meaning the threshold parameter value itself has no direct storage impact."
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
      "pointer": "/parameters/11",
      "claim": "decay_ctr is an 8-bit field.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The entry format specifies an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "decay_tomasulo decrements the decay counter and invalidates digests on reaching 0.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "To implement a 256-instruction wait within an 8-bit limit, the algorithm must start at 255 and invalidate the entry on the step after it reaches 0."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3",
        "value": {
          "name": "decay_tomasulo",
          "trigger": "instruction decode",
          "pseudocode": "for r in 0 .. num_logical_regs - 1:\n  if tomasulo_table[r].valid == 1:\n    if tomasulo_table[r].decay_ctr == 0:\n      tomasulo_table[r].valid = 0\n    else:\n      tomasulo_table[r].decay_ctr -= 1",
          "notes": "Decays the validity of each digest. Triggered per decoded instruction. Threshold is 256."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4",
      "claim": "recover_tomasulo rolls back flushed instructions by checking if the ROB ID is younger than the squashed branch.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves the rollback strategy to future work, so the ROB ID age check is unconfirmed."
      },
      "patch": null,
      "open_question": "What logic should be used to recover the Tomasulo-like table during a branch squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The predictor supports 128 in-flight branches.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the maximum number of inflight branches that the predictor must track?",
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
model=gemini-3.1-pro-high conversation=245e06a8-f687-4846-8848-79a065128a0e cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_1edf22bb40bf7b97

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0",
      "claim": "allocate_tomasulo clears the valid bit and records the ROB index on instruction decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "It explicitly describes the decode-time operations matching the pseudocode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "tomasulo_table contains 65 entries of {valid, payload (14), decay_ctr (8)}.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The component sizes and total entry count precisely match the structure described."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "The multiplier 65 corresponds to the number of tracked logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The decay_counter_expires test verifies a 256-step countdown using an 8-bit counter.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The original test initializes the 8-bit counter to 256, which overflows; it must be initialized to 255 and tested for 256 triggers."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_expire
... [truncated]

[Usage]
{"input_tokens": 33168, "output_tokens": 24150, "thinking_tokens": 21526, "cache_read_tokens": 0, "total_tokens": 57318}

[Result]
status=SUCCESS conversation=245e06a8-f687-4846-8848-79a065128a0e turns=1 duration=299.637152406s usage={"input_tokens": 33168, "output_tokens": 24150, "thinking_tokens": 21526, "cache_read_tokens": 0, "total_tokens": 57318}


