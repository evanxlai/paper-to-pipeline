success: True
usage: {'input_tokens': 31487, 'output_tokens': 23422, 'thinking_tokens': 21232, 'cache_read_tokens': 0, 'total_tokens': 54909}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "allocate_tomasulo executes at instruction decode time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag",
        "why": "The text explicitly states this allocation action happens at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "allocate_tomasulo stores the ROB index as a tag in the payload and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode correctly assigns the ROB index to the payload field and zeroes the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The tomasulo_table size is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines 65 entries containing 1+14+8=23 bits each, summing to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms there are 65 entries in the auxiliary data, representing the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The WT sum is scaled by useful_multiplier based on whether UT usefulness is > 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows an 'x0 or x2.5' multiplier stage, but it is ambiguous whether this is driven dynamically by the bank's own usefulness value being > 0, or if it is a single global static scale.",
      "enum_candidates": ["bank_usefulness_gates", "global_static_scale"]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The tomasulo_table valid bit becomes 0 after the decay timeout expires.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper explicitly states that the entry is invalidated (valid bit cleared) when the timeout completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "Mispredict recovery restores the valid bit to 1 using the architectural register value.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states the predictor leverages extra values visible after a flush, but it does not specify the recovery algorithm for the Tomasulo table on a squash. It does not state whether it explicitly restores squashed entries from the architectural register state.",
      "enum_candidates": ["restore_from_arch_state", "flush_squashed"]
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The decay mechanism triggers on every instruction decode event.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The timeout happens in terms of instructions decoded, supporting the decode tick trigger."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "decode_tick decrements decay_ctr to 0 and immediately invalidates in the same tick.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper explicitly states the timeout is 256 instructions. The original pseudocode invalidates immediately upon hitting 0, yielding only 255 ticks when initialized to 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "def decode_tick():\n    for reg in range(num_logical_regs):\n        if tomasulo_table[reg].valid == 1:\n            if tomasulo_table[reg].decay_ctr == 0:\n                tomasulo_table[reg].valid = 0\n            else:\n                tomasulo_table[reg].decay_ctr -= 1"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default decay timeout is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The parameter's default of 256 matches the paper's literal instruction count for invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "complete_tomasulo executes at instruction complete time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value",
        "why": "The paper confirms the digest payload is overwritten when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "complete_tomasulo verifies that the table payload matches the instruction's ROB index before overwriting the entry.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states that the payload is overwritten at completion, but does not explicitly state that the logic checks if the entry's ROB index still matches the completing instruction. Should it check the ROB index?",
      "enum_candidates": ["check_rob_index", "overwrite_unconditionally"]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "mispredict_recovery iterates over logical registers and restores squashed entries using arch_reg_value and arch_reg_type.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper provides no specific recovery algorithm for squashes, leaving the undefined helpers arch_reg_value and arch_reg_type without a textual basis. How should the table be repaired on a squash?",
      "enum_candidates": ["restore_from_arch_state", "flush_squashed"]
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "The default number of inflight branches is 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper mentions an ROB of over 500 instructions but never specifies a specific limit or default for the number of inflight branches.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The test verifies the update logic for the randomly selected register.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/2/expect",
        "value": "WT and UT entries corresponding to exactly one randomly selected register from the available ones in the bank are modified, and all other entries in the same bank remain equal to their state in predict_snapshots"
      },
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:allocate_tomasulo+algo:decode_tick+algo:complete_tomasulo+algo:mispredict_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream codi...

[Init]
model=gemini-3.1-pro-high conversation=3ac116cb-504a-4540-a4f1-eaf69a8c587a cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_6721a3ea132acf19

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "allocate_tomasulo executes at instruction decode time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag",
        "why": "The text explicitly states this allocation action happens at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "allocate_tomasulo stores the ROB index as a tag in the payload and clears the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The pseudocode correctly assigns the ROB index to the payload field and zeroes the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The tomasulo_table size is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines 65 entries containing 1+14+8=23 bits each, summing to exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms there are 65 entries in the auxiliary data, representing the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The WT sum is scaled by usef
... [truncated]

[Usage]
{"input_tokens": 31487, "output_tokens": 23422, "thinking_tokens": 21232, "cache_read_tokens": 0, "total_tokens": 54909}

[Result]
status=SUCCESS conversation=3ac116cb-504a-4540-a4f1-eaf69a8c587a turns=1 duration=293.297150622s usage={"input_tokens": 31487, "output_tokens": 23422, "thinking_tokens": 21232, "cache_read_tokens": 0, "total_tokens": 54909}


