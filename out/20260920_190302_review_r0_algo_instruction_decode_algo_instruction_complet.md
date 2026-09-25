success: True
usage: {'input_tokens': 28463, 'output_tokens': 39904, 'thinking_tokens': 35609, 'cache_read_tokens': 0, 'total_tokens': 68367}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The register tracking table decode update is triggered at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Establishes that tracking table state updates and digest lifetime decay occur sequentially as each instruction is decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The pseudocode defines on_instruction_decode as the decode event handler rather than calling an undefined external helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms that storing the ROB tag and clearing the valid bit are defined actions executed at decode time by this algorithm handler."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay counter decrement loop checks and decrements counters across all 65 logical registers on each decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms that exactly 65 register tracking entries have decay counters that track instruction decay."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "A valid register digest is invalidated when its decay counter reaches zero after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Verbatim establishes that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "An instruction modifying a destination register writes its 14-bit ROB index tag into payload and clears the valid bit at decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms that instructions writing a destination register clear valid and record their ROB index as a tag at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At decode time, marking a destination register pending initializes its decay counter to 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 4.2 states that decay applies to valid digests to discard stale values; does marking a destination register invalid at decode initialize decay_ctr, or is decay_ctr initialized only when the valid digest is written at completion?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction completion handler is triggered upon execution completion or writeback of a value-producing instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that completion of instruction execution triggers writing the produced digest and validating the tracking entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The pseudocode defines on_instruction_complete as the completion event handler rather than calling an undefined external helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Establishes that on_instruction_complete is the top-level callback implementing the completion action described in the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "generate_digest computes a 12-bit digest from the produced register value according to register type.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Verifies that digest generation produces a 12-bit digest parameterized by the 64-bit value and register type."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "A completing instruction updates the tracking table only if the entry is invalid and its tag matches the instruction's ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Tomasulo's tracking requires completing instructions to match the in-flight ROB tag before overwriting register status."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On instruction complete, payload is overwritten with the digest, valid is set to 1, and decay_ctr is initialized.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms that the produced digest is written into the payload and valid is set to 1 upon completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register tracking table contains 65 entries directly indexed by logical register ID (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Confirms one tracking table entry per logical register, corresponding to the 65 logical registers of Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry contains a 1-bit valid flag, a 14-bit payload holding an ROB index tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure with 1-bit valid, 14-bit payload, and 8-bit decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The 8-bit decay counter is initialized to 256 upon allocation.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Table 3 specifies decay_ctr is 8 bits (holding 0 to 255), while Section 4.2 states invalidation occurs after 256 instructions; how is the 256-instruction delay encoded in an 8-bit counter?",
      "enum_candidates": [
        "init_255",
        "init_0_underflow",
        "modulo_256"
      ]
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage cost of the register tracking table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "65 entries multiplied by 23 bits per entry (1 + 14 + 8) equals exactly 1495 bits."
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
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Seven banks of 8 registers plus one bank of 9 registers equals 65 logical registers, matching Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The legal tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the register tracking table to 65 logical registers matching the CBP 2025 traces and does not define a tuning range [32, 128]; should num_logical_registers be fixed by the host ISA architecture rather than tuned?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "Each logical register accounts for 23 bits in the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "1 bit valid plus 14 bits payload plus 8 bits decay_ctr equals 23 bits per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default decay interval is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Verbatim specifies 256 decoded instructions as the digest lifetime before invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The legal tuning range for decay_instructions is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates and documents only 256 instructions for decay invalidation; what is the legal tuning range for decay_instructions and how does changing it impact the 8-bit counter budget in Table 3?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "decay_ctr bit width is ceil(log2(decay_instructions)) bits in the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "With decay_instructions equal to 256, ceil(log2(256)) yields 8 bits, matching Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The 12-bit integer digest computation for trailing zeros = 3, leading zeros = 60, and LSB6 = 8 evaluates to 35.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The test expectation asserts 3 ^ 480 ^ 512 = 35, which arises from arithmetic subtraction 512 - 480 + 3 rather than bitwise XOR which evaluates to 995 (0x3E3); should the test expect 995 or 35?",
      "enum_candidates": [
        "995",
        "35"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "Condition-code flag register digests replicate the 4-bit flag pattern three times to form the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verbatim specifies that condition-code flag digests replicate the four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "Each bank selects the digest of the most useful available register to query weight tables WT0, WT1, and WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Confirms that each bank selects the digest of the most useful register from available registers and forwards it to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "When a bank's register usefulness is non-positive, multiplier selects x0 and the bank contributes 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows a multiplier stage labelled 'x0 or x2.5' but does not specify the wire selecting x0 vs x2.5; is x0 selected when usefulness is non-positive (<= 0), strictly negative (< 0), or based on an external threshold?",
      "enum_candidates": [
        "non_positive",
        "strictly_negative",
        "static_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "When register usefulness is positive, the bank weight table sum is scaled by 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows an 'x0 or x2.5' scaling stage for each bank, but the selection condition and integer truncation or rounding rule for the scaled sum are not detailed in prose; how is the scaling applied to integer predictor weights?",
      "enum_candidates": [
        "truncate",
        "round"
      ]
    },
    {
      "pointer": "/unit_tests/5/expect",
      "claim": "A valid digest decays and is cleared when its decay counter reaches 0 after 256 subsequent decodes without a new write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Directly confirms that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6/expect",
      "claim": "Upon pipeline restart after a misprediction, digests produced by instructions completed prior to branch resolution remain valid.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Establishes that instructions finished by misprediction resolution time provide valid digests visible to the predictor upon restart."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:instruction_decode+algo:instruction_complete` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=291d9503-e1db-4fed-a911-960b1feec238 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The register tracking table decode update is triggered at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Establishes that tracking table state updates and digest lifetime decay occur sequentially as each instruction is decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The pseudocode defines on_instruction_decode as the decode event handler rather than calling an undefined external helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms that storing the ROB tag and clearing the valid bit are defined actions executed at decode time by this algorithm handler."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay counter decrement loop checks and decrements counters across all 65 logical registers on each decode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 confirms that exactly 65 register tracking entries have decay counters that track instruction decay."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "A valid register digest is invalidated when its decay counter reaches zero after 256 dec
... [truncated]

[Usage]
{"input_tokens": 28463, "output_tokens": 39904, "thinking_tokens": 35609, "cache_read_tokens": 0, "total_tokens": 68367}

[Result]
status=SUCCESS conversation=291d9503-e1db-4fed-a911-960b1feec238 turns=1 duration=209.987723223s usage={"input_tokens": 28463, "output_tokens": 39904, "thinking_tokens": 35609, "cache_read_tokens": 0, "total_tokens": 68367}


