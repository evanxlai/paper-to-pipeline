success: True
usage: {'input_tokens': 28142, 'output_tokens': 32546, 'thinking_tokens': 28898, 'cache_read_tokens': 0, 'total_tokens': 60688}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At instruction decode, an instruction writing a destination register clears the entry valid bit, stores its ROB index as a 14-bit tag in the payload, and sets the decay counter to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that instructions writing a register clear the valid bit and store their ROB index as a tag in the tracking table at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "When an instruction completes execution and matches the in-flight ROB index tag, the payload is overwritten with the produced value's digest, the valid bit is set to 1, and the decay counter is initialized to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies overwriting the payload with the produced value's digest and setting the valid bit upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Digest invalidation decay steps on instruction retirement or decode via an ambiguous event handler 'instruction_retired_or_decoded_step'.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that invalidation countdown occurs per decoded instruction, contradicting stepping on instruction retirement."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "on decode(inst):\n    // Invalidate stale digests after 256 decoded instructions\n    for r = 0 to 64:\n        if Register_Tracking_Table[r].valid == 1:\n            if Register_Tracking_Table[r].decay_ctr == 0:\n                Register_Tracking_Table[r].valid = 0\n            else:\n                Register_Tracking_Table[r].decay_ctr -= 1\n\n    if inst writes dst_reg:\n        Register_Tracking_Table[dst_reg].valid = 0\n        Register_Tracking_Table[dst_reg].payload = inst.rob_idx & 0x3FFF\n        Register_Tracking_Table[dst_reg].decay_ctr = 255\n\non execution_complete(inst, dst_reg, result_val, reg_type):\n    // Match in-flight tag\n    if Register_Tracking_Table[dst_reg].valid == 0 and Register_Tracking_Table[dst_reg].payload == (inst.rob_idx & 0x3FFF):\n        Register_Tracking_Table[dst_reg].payload = generate_digest(result_val, reg_type)\n        Register_Tracking_Table[dst_reg].valid = 1\n        Register_Tracking_Table[dst_reg].decay_ctr = 255\n\non pipeline_flush(squashed_rob_mask):\n    for r = 0 to 64:\n        if Register_Tracking_Table[r].valid == 0 and squashed(Register_Tracking_Table[r].payload):\n            Register_Tracking_Table[r].payload = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On a pipeline flush, in-flight entries with valid bit 0 whose payload matches a squashed instruction have their payload cleared to 0 via a squashed helper.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that recovering the Tomasulo-like table after flushes is left to future work and defines no squash recovery mechanism."
      },
      "patch": null,
      "open_question": "How should entries in the register tracking table be updated or restored when speculative instructions are squashed by a pipeline flush?",
      "enum_candidates": [
        "no_recovery",
        "invalidate_squashed",
        "checkpoint_restore"
      ]
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Entries completed by execution remain valid across pipeline flushes if the producing instruction was not squashed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper notes that values completed before branch resolution remain visible and usable to the predictor after restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table is a direct-mapped array of 65 entries covering logical registers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Eight banks containing eight or nine registers each total 65 logical registers, matching the 65 entries indexed directly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry format consists of a 1-bit valid flag, a 14-bit payload holding an ROB index or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines the valid bit and 14-bit tag / 12-bit digest payload, with Table 3 confirming the 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry (1 + 14 + 8) equals exactly 1495 bits as listed in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Eight banks of eight or nine registers total 65 logical registers, confirmed by the 65 multiplier in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly specifies generating a 12-bit digest for register values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default decay instruction limit is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default prediction weight table sizes per bank are 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 and Figure 5(c) specify WT sizes of 2^9 (512), 2^8 (256), and 2^7 (128) entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default usefulness table subtable size is 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 and Figure 5(c) specify 2^3 = 8 entries for each of the three usefulness sub-tables per register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest calculation computes bitwise XOR of trailing zeros/ones count, leading zeros/ones count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The unit test checks the exact XOR-folded layout of trailing count, leading count, and 6 LSBs defined in Section 4.2 and Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag digest replicates 4 flag bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 4-bit value 0x9 three times produces 0x999, matching the paper's specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 digest extracts sign and high exponent bits Val[63:55] placed at digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Extracting Val[63:55] and placing them at digest bits [11:3] directly follows Section 4.2 and Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Digest valid bit transitions to 0 after exactly 256 decoded instructions without being overwritten.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The unit test verifies entry invalidation when the 256 decoded instruction limit is reached."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A register bank with negative usefulness selects the x0 multiplier, suppressing that bank's contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows per-bank scaling by x0 or x2.5, where negative usefulness selects x0 zero suppression."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A register bank with positive usefulness selects the x2.5 multiplier, boosting that bank's contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows per-bank scaling by x2.5 when bank usefulness is positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "During training, when multiple registers in a bank are available at prediction time, exactly one is randomly chosen for WT and UT updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that one available register per bank is randomly chosen to enable single write port tables."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:register_tracking_update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read ...

[Init]
model=gemini-3.8-flash-medium conversation=c28059c6-906d-4418-8507-2cffe5684c3c cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At instruction decode, an instruction writing a destination register clears the entry valid bit, stores its ROB index as a 14-bit tag in the payload, and sets the decay counter to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that instructions writing a register clear the valid bit and store their ROB index as a tag in the tracking table at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "When an instruction completes execution and matches the in-flight ROB index tag, the payload is overwritten with the produced value's digest, the valid bit is set to 1, and the decay counter is initialized to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies overwriting the payload with the produced value's digest and setting the valid bit upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Digest invalidation decay steps on instruction retirement or decode via an ambiguous event handler 'instruction_retired_or_decoded_step'.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that invalidation countdown occ
... [truncated]

[Usage]
{"input_tokens": 28142, "output_tokens": 32546, "thinking_tokens": 28898, "cache_read_tokens": 0, "total_tokens": 60688}

[Result]
status=SUCCESS conversation=c28059c6-906d-4418-8507-2cffe5684c3c turns=1 duration=172.227850212s usage={"input_tokens": 28142, "output_tokens": 32546, "thinking_tokens": 28898, "cache_read_tokens": 0, "total_tokens": 60688}


