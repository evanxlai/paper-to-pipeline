success: True
usage: {'input_tokens': 29629, 'output_tokens': 25160, 'thinking_tokens': 21816, 'cache_read_tokens': 0, 'total_tokens': 54789}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Pipeline squash recovery is triggered by a branch misprediction squash or pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper identifies branch misprediction resolution and the resulting pipeline flush as the trigger after which the predictor restarts with retained execution results."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions completed prior to the squash retain their valid digests across the flush to provide correlation for restarted instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper confirms that completed in-flight instructions retain their values across a pipeline flush, enlarging visible values upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline squash, in-flight register entries waiting on flushed wrong-path instructions are identified via is_tag_squashed and cleared.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper explicitly states that recovering the Tomasulo-like table is an open challenge left for future work ('recovering the Tomasulo-like table may present some challenges; we plan to address these in future work') and does not describe how flushed in-flight instructions are tracked, checked, or cleared.",
      "enum_candidates": [
        "rob_tag_age_check",
        "clear_all_uncompleted",
        "no_recovery"
      ]
    },
    {
      "pointer": "/state/0/organization",
      "claim": "reg_status_table is a direct-mapped table of 65 logical registers (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly records 65 entries for the register status table, matching the 65 logical registers across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each reg_status_table entry comprises a 1-bit valid flag, a 14-bit payload holding either a 14-bit ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines the entry fields and bit widths in Section 4.2 and Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "reg_status_table requires 1495 bits of total storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates 23 bits per entry (1 + 14 + 8) multiplied across 65 registers, yielding exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "reg_status_table is directly indexed by logical register index (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies a 1:1 direct mapping between each logical register and its dedicated entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly establishes a 12-bit digest length."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/range",
      "claim": "The tuning range for digest_width is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed digest width of 12 bits and does not discuss or define an allowable search range of [8, 16]; the parameter exploration range should be confirmed.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The default decay threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper fixes the invalidation threshold to 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/range",
      "claim": "The tuning range for decay_threshold_insts is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the invalidation threshold at 256 instructions without mentioning an exploration range of [64, 1024]; the parameter exploration range should be confirmed.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "execution_complete_update is triggered when an instruction execution unit finishes computation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that the update is triggered upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, if valid is 0 and payload matches rob_tag, payload is updated with the generated digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines updating the payload with the digest and asserting valid on completion, with decay_ctr resetting to start counting decoded instructions until 256."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Tomasulo-like tracking ensures only the latest instruction that claimed dest_reg overwrites the payload on completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Adopting Tomasulo's algorithm matches the completing instruction's ROB tag against the entry to prevent out-of-order older instructions from overwriting newer tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation generates digest 0xB51 for val=42 with trailing_zeros=1 and leading_zeros=58.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) is marked UNCERTAIN (U3) regarding count encoding for 64-bit registers into 6-bit fields (saturating at 63 vs modulo 64 vs counting sign-matching bits) and whether zeros vs ones are distinguished.",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "count_sign_matching"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 digest generation shifts 9-bit Val[63:55] left by 3 bits to align at digest bit 3 with bits [2:0] set to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) is marked UNCERTAIN (U4) regarding whether floating-point digest bit fields are right-aligned at bit 3 (leaving bits [2:0] zero) or right-aligned at bit 0.",
      "enum_candidates": [
        "align_bit3",
        "align_bit0"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag digest generation replicates 4-bit flag value 0x9 three times to form 12-bit digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states replicating the four flag bits three times to fill the 12-bit digest, producing 0x999 for input 0x9."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A digest is invalidated and ignored in usefulness selection after 256 subsequent instructions have decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper mandates invalidating each digest after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Bank usefulness selection selects the register with the largest usefulness sum (R8 with +12 vs R0 with +5) to index WT0, WT1, WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies picking the most useful register among available registers in the bank and forwarding its digest to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Bank contribution is gated to 0 via x0 multiplier when net usefulness sum is non-positive (<= 0).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) is marked UNCERTAIN (U2) regarding the signal selecting between x0 and x2.5, including whether a non-positive bank usefulness sum gates the bank contribution to x0.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Bank contribution is scaled by 2.5 when best valid register has positive net usefulness sum.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) is marked UNCERTAIN (U2) regarding whether the 2.5 multiplier is dynamically selected by positive bank usefulness or applied as a static scale factor.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "global_static_scale"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:pipeline_squash_recovery+algo:execution_complete_update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from th...

[Init]
model=gemini-3.8-flash-medium conversation=cecf44c1-674e-40ba-b6cb-66cc1a4e6b30 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_bd2489640a39caf1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "Pipeline squash recovery is triggered by a branch misprediction squash or pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper identifies branch misprediction resolution and the resulting pipeline flush as the trigger after which the predictor restarts with retained execution results."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions completed prior to the squash retain their valid digests across the flush to provide correlation for restarted instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper confirms that completed in-flight instructions retain their values across a pipeline flush, enlarging visible values upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline squash, in-flight register entries waiting on flushed wrong-path instructions are 
... [truncated]

[Usage]
{"input_tokens": 29629, "output_tokens": 25160, "thinking_tokens": 21816, "cache_read_tokens": 0, "total_tokens": 54789}

[Result]
status=SUCCESS conversation=cecf44c1-674e-40ba-b6cb-66cc1a4e6b30 turns=1 duration=138.637667762s usage={"input_tokens": 29629, "output_tokens": 25160, "thinking_tokens": 21816, "cache_read_tokens": 0, "total_tokens": 54789}


