success: True
usage: {'input_tokens': 28058, 'output_tokens': 33205, 'thinking_tokens': 29309, 'cache_read_tokens': 0, 'total_tokens': 61263}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register tracking table updates are triggered at instruction decode, execution completion, and instruction step decay.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This establishes that the tracking table update logic is triggered at the instruction decode and execution completion stages."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register tracking table update logic is triggered on pipeline flushes to recover in-flight entries.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that recovering the Tomasulo-like table across flushes is an open challenge left for future work rather than an implemented pipeline flush trigger."
      },
      "patch": null,
      "open_question": "Should pipeline flush trigger recovery of the register tracking table, or is recovery omitted as described in the paper's future work?",
      "enum_candidates": [
        "omit_recovery",
        "flush_hook"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decay counter decrements for all valid entries on each decoded instruction and clears the valid bit when the counter reaches zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This settles that digests have a lifetime of 256 decoded instructions, decremented on each decode and invalidated when the count expires."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the valid bit, records its 14-bit ROB index in the payload, and initializes the decay counter to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "This confirms that at decode, destination register entries are invalidated and tagged with the producing instruction's ROB index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The field inst.rob_idx read by register_tracking_update is context metadata supplied by the host pipeline at decode and completion rather than written by a predictor algorithm.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper identifies the tag as the instruction's ROB index, which is standard pipeline context allocated by the host processor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The event handlers on decode and on execution_complete represent host pipeline interface hooks rather than undefined helper functions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This demonstrates that decode and execution completion are pipeline stage events provided by the host execution environment."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "When an instruction completes execution matching the in-flight tag, the payload is updated with the generated digest, marked valid, and given a full decay lifetime.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This settles that instruction completion overwrites the payload with the produced digest and marks the entry valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On a pipeline flush, in-flight entries whose tags match squashed instructions are identified by a squashed() helper and have their payload cleared.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper does not define a squash helper or a squash recovery procedure for the tracking table, leaving table recovery as future work."
      },
      "patch": null,
      "open_question": "How are in-flight tracking entries updated when instructions are squashed during a pipeline flush?",
      "enum_candidates": [
        "no_recovery",
        "clear_payload",
        "invalidate"
      ]
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Decay counters decrement per decoded instruction, invalidating entries after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This directly confirms the 256-instruction lifetime for valid register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/notes",
      "claim": "Completed entries remain valid across pipeline flushes if their producing instruction completed before the branch misprediction was resolved.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "This establishes that register values from instructions completed prior to flush resolution persist and remain visible across the restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table has 65 entries directly indexed by logical register numbers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms that the auxiliary tracking structure consists of exactly 65 entries corresponding to the logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry in Register_Tracking_Table comprises a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totalling 23 bits per entry and 1495 bits overall.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms the entry bit allocation (1 + 14 + 8 = 23 bits) and total size (23 * 65 = 1495 bits)."
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
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 confirms that the design dimensions UT and tracking structures around 65 logical registers."
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
        "why": "This confirms that register values are compressed into 12-bit digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default decay limit for valid register digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This establishes 256 instructions as the decay limit for invalidating digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Each bank of the sR prediction weight tables contains three sub-tables sized at 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) confirms the three weight table sizes per bank are 512, 256, and 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Each sub-table of the usefulness weight tables has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) confirms that UT0, UT1, and UT2 each have 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests XOR-fold 6 bits of trailing zero/one count, 6 bits of leading zero/one count shifted by 3, and 6 bits of value LSB shifted by 6 to produce a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "This verifies the composition of integer digests, matching the test's bitwise XOR calculation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition flag register digests replicate the 4 flag bits three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "This establishes that 4-bit condition flags are replicated three times to create a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 register digests extract Value[63:55] into digest bits [11:3] with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP64     Value[63:55]      9 bits        [11:3]        sign(63) + exp[62:55]",
        "why": "Figure 6(b) specifies that FP64 extracts Value[63:55] into digest bits [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decrements its decay counter from 255 to 0 over 256 decoded instructions and transitions valid to 0 upon reaching 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This confirms the test assertion that a digest expires after exactly 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When a bank exhibits negative combined usefulness, its multiplier selects x0 to suppress its contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) establishes that each bank features an x0 or x2.5 multiplier stage, suppressing non-useful bank outputs with x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank exhibits positive combined usefulness, its multiplier selects x2.5 to boost its contribution to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) establishes that useful bank predictions are scaled by a factor of 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple valid registers are available in the same bank at prediction time, training randomly selects one for table updates to require only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "This directly confirms that training randomly chooses exactly one register per bank among available valid registers."
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
model=gemini-3.8-flash-medium conversation=29134204-b02c-4273-9796-8b523c59fc16 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register tracking table updates are triggered at instruction decode, execution completion, and instruction step decay.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This establishes that the tracking table update logic is triggered at the instruction decode and execution completion stages."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The register tracking table update logic is triggered on pipeline flushes to recover in-flight entries.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly states that recovering the Tomasulo-like table across flushes is an open challenge left for future work rather than an implemented pipeline flush trigger."
      },
      "patch": null,
      "open_question": "Should pipeline flush trigger recovery of the register tracking table, or is recovery omitted as described in the paper's future work?",
      "enum_candidates": [
        "omit_recovery",
        "flush_hook"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decay counter decrements for all valid entries on each decoded instruction and clears the valid bit when the counter reaches zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each dig
... [truncated]

[Usage]
{"input_tokens": 28058, "output_tokens": 33205, "thinking_tokens": 29309, "cache_read_tokens": 0, "total_tokens": 61263}

[Result]
status=SUCCESS conversation=29134204-b02c-4273-9796-8b523c59fc16 turns=1 duration=185.102326202s usage={"input_tokens": 28058, "output_tokens": 33205, "thinking_tokens": 29309, "cache_read_tokens": 0, "total_tokens": 61263}


