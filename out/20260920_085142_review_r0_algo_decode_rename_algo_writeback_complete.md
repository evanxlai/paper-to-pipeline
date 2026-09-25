success: True
usage: {'input_tokens': 28495, 'output_tokens': 33923, 'thinking_tokens': 31032, 'cache_read_tokens': 0, 'total_tokens': 62418}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/0/default",
      "claim": "The default value of decay_instructions is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the period after which a digest is invalidated. Refuting the deterministic finding: lowering the default to 255 contradicts the paper text, and widening decay_ctr to 9 bits contradicts Table 3; an 8-bit counter has 256 distinct states (0 to 255) to track 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/range",
      "claim": "The tuning range for decay_instructions is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates only the fixed invalidation period of 256 decoded instructions and does not mention or define an alternative tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default value of digest_width_bits is 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly specifies generating a 12-bit digest for each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The tuning range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only uses 12-bit digests and does not evaluate or define a parameter range for digest_width_bits.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus is organized as a 65-entry flat table with one entry per logical register R0..R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies a dedicated table with one entry per logical register, confirmed as 65 registers by Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "sR_RegStatus requires 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary storage assigns 23 bits per entry across 65 registers, yielding exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry format consists of a 1-bit valid flag, a 14-bit payload holding either a ROB tag or digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines each entry as containing a valid bit, a 14-bit payload, and Table 3 confirms an 8-bit decay_ctr."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "decode_rename is triggered at the instruction decode and rename stage for each decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper indicates that tracking and invalidation logic operate at instruction decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "During decode, any valid digest advances its decay counter and is invalidated when 256 decoded instructions have elapsed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a register clears the valid bit and stores its ROB index as a tag in payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies clearing valid and writing the ROB index into the entry upon decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "writeback_complete is triggered upon instruction execution writeback and completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that entry updates happen when an instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Upon completion, matching the pending ROB tag causes payload to be overwritten with the 12-bit digest and valid set to 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper describes adopting Tomasulo-like tag matching to overwrite the entry with the produced value digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "writeback_complete sets decay_ctr to literal value 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 8-bit decay_ctr initialized and decremented to represent the 256-instruction decay window without overflowing an 8-bit unsigned field?",
      "enum_candidates": [
        "init_255",
        "wrap_around",
        "up_counter"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "generate_digest computes the INT register digest by XOR-folding trailing bit count, leading bit count shifted by 3, and value[5:0] shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies encoding leading count, trailing count, and six LSBs into the 12-bit integer digest via XOR folding."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "generate_digest replicates 4-bit flag register values three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states replicating the four flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "generate_digest extracts bits [31:26] for FP32 and places them into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper specifies extracting the sign bit and high exponent bits, which Figure 6(b) assigns to digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest is invalidated on the 256th decode step following its update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states invalidation occurs after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Each bank scales its weight table sum by 2.5 if usefulness is positive and suppresses output to 0 if non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows per-bank prediction sums gated by an 'x0 or x2.5' multiplier controlled by bank usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "An instruction that completes writeback before misprediction recovery retains its valid digest in sR_RegStatus after pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explains that instructions completing writeback before misprediction resolution enlarge the set of valid digests available upon flush recovery."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:decode_rename+algo:writeback_complete` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; the...

[Init]
model=gemini-3.8-flash-medium conversation=6d173611-3bae-44b9-af53-2b42946bcd71 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/0/default",
      "claim": "The default value of decay_instructions is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the period after which a digest is invalidated. Refuting the deterministic finding: lowering the default to 255 contradicts the paper text, and widening decay_ctr to 9 bits contradicts Table 3; an 8-bit counter has 256 distinct states (0 to 255) to track 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/range",
      "claim": "The tuning range for decay_instructions is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates only the fixed invalidation period of 256 decoded instructions and does not mention or define an alternative tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default value of digest_width_bits is 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly specifies generating a 12-bit digest for each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The tuning range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only uses 12-bit digests and does not evaluate or 
... [truncated]

[Usage]
{"input_tokens": 28495, "output_tokens": 33923, "thinking_tokens": 31032, "cache_read_tokens": 0, "total_tokens": 62418}

[Result]
status=SUCCESS conversation=6d173611-3bae-44b9-af53-2b42946bcd71 turns=1 duration=164.775246375s usage={"input_tokens": 28495, "output_tokens": 33923, "thinking_tokens": 31032, "cache_read_tokens": 0, "total_tokens": 62418}


