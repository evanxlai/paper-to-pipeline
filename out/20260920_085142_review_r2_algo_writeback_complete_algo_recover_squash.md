success: True
usage: {'input_tokens': 28427, 'output_tokens': 37674, 'thinking_tokens': 34436, 'cache_read_tokens': 0, 'total_tokens': 66101}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The writeback_complete routine triggers upon instruction execution writeback / completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper triggers the register status table update specifically when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On writeback completion, the entry matching the completing instruction's destination register and pending ROB tag has its valid bit set to 1 and payload updated with the register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies tracking in-flight producers via ROB tags and overwriting the payload with the result digest while setting valid to 1 upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On writeback completion, decay_ctr is assigned the literal value 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 256-instruction decay window tracked in the 8-bit decay_ctr without overflowing the 8-bit unsigned integer range (0..255)?",
      "enum_candidates": [
        "init_255",
        "wrap_zero",
        "offset_256"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus is organized as a 65-entry flat table with one entry per logical register R0..R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly specifies a dedicated table with one entry per logical register, totaling 65 registers across 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each sR_RegStatus entry contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay_ctr field, totaling 23 bits per entry and 1495 bits overall.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data defines each entry as having a 1-bit valid bit, a 14-bit payload, and an 8-bit decay_ctr across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "decay_ctr is initialized to the integer value 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the concrete reset value and countdown rule for decay_ctr given that 256 exceeds the maximum representable value of an 8-bit unsigned field?",
      "enum_candidates": [
        "255",
        "wrap_256",
        "subsample_tick"
      ]
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default digest invalidation period is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly defines the lifetime of each digest as 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/storage_impact",
      "claim": "decay_ctr consumes 8 bits per entry in sR_RegStatus for a 256-instruction decay window.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms that decay_ctr is budgeted at 8 bits per entry for each of the 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly states that RUNLTS produces a 12-bit digest from each 64-bit register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "The payload field in sR_RegStatus requires 14 bits to accommodate either a 14-bit ROB tag or a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies that the entry payload holds either a 14-bit tag or a 12-bit digest, setting the required width to 14 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "generate_digest computes integer register digests by XOR-folding 6-bit trailing zero/one count, 6-bit leading zero/one count shifted by 3, and value[5:0] shifted by 6 into a 12-bit result.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest is formed by overlapping XOR combination of trailing count, leading count, and low 6 value bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "generate_digest computes condition-code flag digests by replicating the 4-bit flag value three times into the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) explicitly specify that the four flag bits are replicated three times to populate the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "generate_digest computes FP32 digests by extracting Value[31:26] and positioning them at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) explicitly map the FP32 sign and high exponent bits Value[31:26] to digest bit positions [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "A digest valid bit is invalidated after exactly 256 subsequent instructions have been decoded without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that RUNLTS invalidates each digest after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/given",
      "claim": "decay_ctr is initialized to 256 and decrements linearly on each instruction decode down to 0 on the 256th step.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does decay_ctr decrement on every individual instruction decode or on multi-instruction blocks, and what is its starting state within an 8-bit counter?",
      "enum_candidates": [
        "255_down_to_0",
        "wrap_256",
        "block_step"
      ]
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "In sR, each bank's prediction weight sum is multiplied by 0 if its usefulness sum is non-positive, and scaled by 2.5 if positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact condition or threshold controls whether a bank's weight output is scaled by 2.5 or gated to 0 in Figure 5(c)?",
      "enum_candidates": [
        "useful_positive",
        "useful_nonzero",
        "valid_reg_present"
      ]
    },
    {
      "pointer": "/unit_tests/5/expect",
      "claim": "Registers that completed writeback before a pipeline flush retain their valid digests across misprediction recovery to aid subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explains that instructions completing execution during a misprediction preserve their produced values across flush recovery to correct subsequent branches."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Completed register values from instructions finished while a mispredicted branch was in-flight remain available upon restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 establishes that execution results completed prior to flush resolution remain valid to enlarge the available value set upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Speculative pending ROB tags from flushed instructions are identified via rob_is_flushed and reset with payload = 0 and decay_ctr = 0 during recover_squash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that recovering the Tomasulo-like table on mispredictions is left to future work, leaving squash recovery rules and helper functions unspecified."
      },
      "patch": null,
      "open_question": "How are pending entries in sR_RegStatus restored or invalidated during pipeline squashes, given that the paper defers Tomasulo-like table recovery to future work?",
      "enum_candidates": [
        "clear_flushed_tags",
        "clear_all_invalid",
        "checkpoint_restore"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:writeback_complete+algo:recover_squash` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; th...

[Init]
model=gemini-3.8-flash-medium conversation=cdc6975c-9c01-4d87-b27b-c48db70f202f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The writeback_complete routine triggers upon instruction execution writeback / completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper triggers the register status table update specifically when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On writeback completion, the entry matching the completing instruction's destination register and pending ROB tag has its valid bit set to 1 and payload updated with the register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies tracking in-flight producers via ROB tags and overwriting the payload with the result digest while setting valid to 1 upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On writeback completion, decay_ctr is assigned the literal value 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 256-instruction decay window tracked in the 8-bit decay_ctr without overflowing the 8-bit unsigned integer range (0..255)?",
      "enum_candidates": [
        "init_255",
        "wrap_zero",
        "offset_256"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus is organiz
... [truncated]

[Usage]
{"input_tokens": 28427, "output_tokens": 37674, "thinking_tokens": 34436, "cache_read_tokens": 0, "total_tokens": 66101}

[Result]
status=SUCCESS conversation=cdc6975c-9c01-4d87-b27b-c48db70f202f turns=1 duration=202.697269299s usage={"input_tokens": 28427, "output_tokens": 37674, "thinking_tokens": 34436, "cache_read_tokens": 0, "total_tokens": 66101}


