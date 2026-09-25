success: True
usage: {'input_tokens': 30016, 'output_tokens': 29660, 'thinking_tokens': 27043, 'cache_read_tokens': 0, 'total_tokens': 59676}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction complete update is triggered when an execution unit finishes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies that the update trigger occurs upon instruction completion when the produced value is available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, the algorithm matches the ROB index tag against the payload of the destination register entry before writing the 12-bit digest and setting the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies using Tomasulo's algorithm where in-flight instructions hold ROB index tags in the payload until completion overwrites the payload with the produced value digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The decode and decay update is triggered at the instruction decode/rename stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly ties the register status table tag allocation and digest tracking to the instruction decode stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "For each decoded instruction, valid register entries advance their decay counter and are invalidated after 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that valid digests are tracked across decoded instructions and invalidated after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction that writes a destination register clears the valid bit and stores its ROB index as a tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that whether an instruction writes a register is decoded at the decode stage by the CPU frontend, refuting the warning that this context requires a predictor producing algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The reg_status_table contains 65 entries corresponding to logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies a dedicated table with one entry per logical register, matching the 65 logical registers across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry of reg_status_table has a 1-bit valid flag, 14-bit payload, and 8-bit decay_ctr totaling 1495 bits across 65 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the exact bit widths for the valid, payload, and decay counter fields across all 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default value for DECAY_THRESHOLD_INSTS is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The parameter DECAY_THRESHOLD_INSTS has a legal exploration range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies invalidating each digest after 256 instructions, but does not define an exploration or tuning range for DECAY_THRESHOLD_INSTS.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default register digest bit width DIGEST_BITS is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly states that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The parameter DIGEST_BITS has a legal exploration range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a 12-bit digest throughout and does not define an exploration or tuning range for DIGEST_BITS.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest XOR-folding encodes trailing zeros at bits [5:0], leading zeros at bits [8:3], and LSBs at bits [11:6].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U3 notes that encoding 0..64 leading or trailing identical bits in a 6-bit field is not specified (e.g. saturating at 63, wrapping modulo 64, or counting bits matching the sign bit), nor how zeros versus ones are distinguished.",
      "enum_candidates": [
        "saturate",
        "wrap",
        "count_matching_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flags register digest replicates the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 12-bit digest for condition-code flags is formed by replicating the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Floating-point double precision digest extraction places bits [63:55] at digest positions [11:3] with bits [2:0] set to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U4 notes that right-alignment of floating-point fields at digest bit 3 versus bit 0 is uncertain from the drawing.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest expires and is invalidated at the 256th instruction decode following its update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that each digest is invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank's contribution is scaled by x0 when its usefulness sum is non-positive and by x2.5 when positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Declared ambiguity U2 notes that whether the x0 vs x2.5 multiplier is selected per bank by that bank's usefulness or applied as a single global static scale is uncertain.",
      "enum_candidates": [
        "per_bank_usefulness",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers are available in the same bank at commit, training randomly selects exactly one register to update using a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly describes randomly selecting one register among available bank registers during training to maintain single-port updates."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_complete_update+algo:decode_and_decay_update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from t...

[Init]
model=gemini-3.8-flash-medium conversation=e8e6cbb0-a256-4c09-88ec-b2fb355ea986 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction complete update is triggered when an execution unit finishes producing the result value for an instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies that the update trigger occurs upon instruction completion when the produced value is available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, the algorithm matches the ROB index tag against the payload of the destination register entry before writing the 12-bit digest and setting the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies using Tomasulo's algorithm where in-flight instructions hold ROB index tags in the payload until completion overwrites the payload with the produced value digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The decode and decay update is triggered at the instruction decode/rename stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly ties the register status table tag allocation and digest tracking to the inst
... [truncated]

[Usage]
{"input_tokens": 30016, "output_tokens": 29660, "thinking_tokens": 27043, "cache_read_tokens": 0, "total_tokens": 59676}

[Result]
status=SUCCESS conversation=e8e6cbb0-a256-4c09-88ec-b2fb355ea986 turns=1 duration=142.146665329s usage={"input_tokens": 30016, "output_tokens": 29660, "thinking_tokens": 27043, "cache_read_tokens": 0, "total_tokens": 59676}


