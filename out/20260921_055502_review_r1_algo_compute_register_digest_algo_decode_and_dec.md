success: True
usage: {'input_tokens': 30565, 'output_tokens': 34947, 'thinking_tokens': 31832, 'cache_read_tokens': 0, 'total_tokens': 65512}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "compute_register_digest is triggered at instruction execution completion when an instruction produces an architectural register or flag value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that register digest computation and payload update occur when an instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digest encodes count of leading zeros and count of trailing zeros into 6-bit fields capped at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 0..64 leading/trailing bit counts encoded into 6-bit fields, and how are leading/trailing zeros vs ones distinguished?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digest aligns extracted sign and exponent bits at bit position 3 and inspects register values via is_fp64/is_fp32/is_fp16 helpers.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "At which bit position are floating-point sign and exponent fields aligned, and how is the floating-point format classified from the register value?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Flag register digest replicates the 4 condition-code flag bits three times to fill a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly describes replicating the 4 condition-code flag bits three times to form the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "DIGEST_BITS has a default width of 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper states that RUNLTS generates a 12-bit digest for register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "DIGEST_BITS has a configurable tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper exclusively specifies a fixed 12-bit digest and does not define a tuning range [8, 16] for parameter exploration.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The payload field in reg_status_table must be max(14, DIGEST_BITS) bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The entry payload must accommodate either the 14-bit ROB tag or the 12-bit digest, requiring at least max(14, DIGEST_BITS) bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test int_register_digest_xor_folding verifies that trailing count, leading count shifted by 3, and value LSBs shifted by 6 are XOR-folded into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies encoding trailing count, leading count, and 6 LSBs into the 12-bit integer register digest, matching the test's XOR folding verification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test flag_register_digest_replication verifies that a 4-bit flag value 0b1011 replicated three times produces 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper states that the four flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test fp64_register_digest_extraction verifies that FP64 sign and exponent bits [63:55] are placed at digest positions [11:3] with bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Are floating-point register digest fields right-aligned at bit position 3 with bits [2:0] set to 0, or right-aligned at bit position 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test stale_digest_decay_invalidation verifies that an entry's valid bit is cleared after 256 instructions decode without an update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that each digest is invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test bank_usefulness_scaling_and_suppression scales register component contribution by x2.5 for positive bank usefulness and x0 for non-positive bank usefulness.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which signal controls the x0 vs x2.5 multiplier in each register bank, and does non-positive bank usefulness suppress the bank output to x0?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Unit test training_single_port_random_selection verifies that if multiple registers are available in the same bank, exactly one is chosen randomly for update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies randomly selecting one register for update when multiple registers are available within the same bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "decode_and_decay_update is triggered at instruction decode/rename stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper states that register tracking and ROB tag updates occur at the instruction decode stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "decode_and_decay_update advances decay_ctr for valid entries and invalidates stale entries after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly defines advancing the decay tracking per decoded instruction and invalidating each digest after 256 subsequent instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register resets valid, stores its 14-bit ROB index in payload, and resets decay_ctr to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines resetting the valid bit and storing the ROB index tag at decode; inst.writes_reg is supplied by the decode stage of the processor pipeline rather than an internal algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "reg_status_table contains 65 entries corresponding to 64 architectural registers plus 1 condition-code flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies dedicated entries per logical register, totaling 65 entries across integer/floating-point and flag registers as confirmed in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of reg_status_table contains a 1-bit valid flag, 14-bit payload, and 8-bit decay_ctr, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry format and confirms 65 entries of (1 + 14 + 8) = 23 bits each, totaling 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "DECAY_THRESHOLD_INSTS has a default value of 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests after 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "DECAY_THRESHOLD_INSTS has a configurable tuning range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper exclusively specifies a fixed decay threshold of 256 instructions and does not define a tuning range [64, 1024] for parameter exploration.",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:compute_register_digest+algo:decode_and_decay_update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this ...

[Init]
model=gemini-3.8-flash-medium conversation=70585b32-89bf-4fb0-9a35-1acb07687f6f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "compute_register_digest is triggered at instruction execution completion when an instruction produces an architectural register or flag value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that register digest computation and payload update occur when an instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Integer register digest encodes count of leading zeros and count of trailing zeros into 6-bit fields capped at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are 0..64 leading/trailing bit counts encoded into 6-bit fields, and how are leading/trailing zeros vs ones distinguished?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point register digest aligns extracted sign and exponent bits at bit position 3 and inspects register values via is_fp64/is_fp32/is_fp16 helpers.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "At which bit position are floating-point sign and exponent fields aligned, and how is the floating-point format classified from the register value?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Flag register digest replicates the 4 condition-code flag bits three times to fill a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code f
... [truncated]

[Usage]
{"input_tokens": 30565, "output_tokens": 34947, "thinking_tokens": 31832, "cache_read_tokens": 0, "total_tokens": 65512}

[Result]
status=SUCCESS conversation=70585b32-89bf-4fb0-9a35-1acb07687f6f turns=1 duration=179.409179015s usage={"input_tokens": 30565, "output_tokens": 34947, "thinking_tokens": 31832, "cache_read_tokens": 0, "total_tokens": 65512}


