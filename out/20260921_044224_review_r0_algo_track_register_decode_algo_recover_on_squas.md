success: True
usage: {'input_tokens': 30819, 'output_tokens': 28852, 'thinking_tokens': 24800, 'cache_read_tokens': 0, 'total_tokens': 59671}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Register tracking at decode is triggered during the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies that register tracking begins at instruction decode when an instruction writes a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "An instruction writing a destination register clears the valid bit and records its ROB tag in the RTT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper establishes that instructions writing a register clear the entry's valid bit and record their ROB index as a tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Destination register specifiers read by track_register_decode are external instruction metadata supplied by the processor decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The operation is driven by pipeline decode events where destination registers are properties of the decoded instruction rather than internal state written by another predictor algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decay counter in the RTT entry is initialized to zero upon instruction decode.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the RTT decay counter initialize to zero at decode or upon completion when the valid digest is written?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The Register Tracking Table contains 65 entries corresponding to 65 logical registers partitioned across 8 banks with 9 registers in bank 0 and 8 in banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states the component comprises 8 banks of eight or nine logical registers each, totaling 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each RTT entry consists of 1 valid bit, a 14-bit payload, and an 8-bit decay counter, totaling 1495 bits for 65 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 entries of 1 valid bit, 14 payload bits, and 8 decay counter bits, which equals 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "The 12-bit completed value digest is right-justified within the 14-bit RTT payload field.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 12-bit completed digest positioned or aligned within the 14-bit payload field?",
      "enum_candidates": [
        "right_justified",
        "left_justified",
        "zero_extended"
      ]
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default digest decay threshold is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies that active digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The parameter decay_threshold_insts has a legal exploration range of [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed threshold of 256 instructions and does not define a tuning range for decay_threshold_insts.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default number of logical registers tracked by the register component is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 bits x 65 regs x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sizes the register component usefulness tables across exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The parameter num_logical_registers has an architectural exploration range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper assumes a fixed ISA with 65 logical registers across 8 banks and does not define an exploration range for num_logical_registers.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "An integer register with 64 zero bits caps its leading and trailing zero counts at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per source ambiguity U3, how are runs of 64 identical bits encoded into the 6-bit count fields of the integer digest?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "count_matching_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "Integer register digests fold trailing counts, leading counts, and 6 LSBs using overlapping XOR combinations.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per source ambiguity U3, the paper does not specify how the zero versus one condition is distinguished in leading and trailing count fields.",
      "enum_candidates": [
        "count_zeros",
        "count_ones",
        "count_matching_edge"
      ]
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "Condition-code flag register digests replicate the 4 flag bits three times to produce a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "Extracted FP32 sign and exponent bits are right-aligned at digest bit position 3 with digest bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per source ambiguity U4, is the floating-point digest field right-aligned at bit position 3 leaving bits [2:0] unused, or right-aligned at bit position 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "An active RTT digest expires and invalidates when 256 consecutive decoded instructions pass without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper directly specifies invalidating digests after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "The decay counter operates as a countdown timer decrementing towards zero on each decoded instruction.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the RTT decay mechanism decrement a countdown timer towards zero or increment an instruction counter towards the threshold?",
      "enum_candidates": [
        "countdown",
        "countup"
      ]
    },
    {
      "pointer": "/unit_tests/5/expect",
      "claim": "A bank multiplier selects x0 when the bank's register usefulness sum is non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per source ambiguity U2, what signal drives the bank multiplier selection between x0 and x2.5 in the register component?",
      "enum_candidates": [
        "bank_usefulness_sign",
        "static_scaling"
      ]
    },
    {
      "pointer": "/unit_tests/6/expect",
      "claim": "A bank multiplier selects x2.5 when the bank's register usefulness sum is positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Per source ambiguity U2, what signal drives the bank multiplier selection between x0 and x2.5 in the register component?",
      "enum_candidates": [
        "bank_usefulness_sign",
        "static_scaling"
      ]
    },
    {
      "pointer": "/unit_tests/7/expect",
      "claim": "During training, when multiple registers in the same bank are available, exactly one is randomly chosen for updating.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that multiple available registers in a bank are resolved by randomly selecting one for training to maintain a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "Pipeline squash recovery clears speculative in-flight RTT entries matching flushed ROB tags.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the Register Tracking Table recovered on a pipeline squash, given that the paper leaves recovering the Tomasulo-like table to future work?",
      "enum_candidates": [
        "clear_flushed_tags",
        "no_recovery",
        "flash_invalidate"
      ]
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The conditional expression in recover_on_squash uses standard boolean conjunction syntax rather than an undefined helper call.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The syntax is standard boolean conjunction rather than a missing helper call, though the paper defers table recovery to future work."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "Prediction Weight Table 0 consists of 8 banks of 512 entries storing 6-bit signed weights totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage budget with 8 banks containing 2^9 (512) entries of 6 bits for WT0, totaling 24576 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "WT0 is indexed by a hash function of PC, selected register digest, and bank ID modulo 512.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash algorithm is used to compute index h0 from the PC and selected register digest?",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/state/3/organization",
      "claim": "Prediction Weight Table 1 consists of 8 banks of 256 entries storing 6-bit signed weights totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage budget with 8 banks containing 2^8 (256) entries of 6 bits for WT1, totaling 12288 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/indexing",
      "claim": "WT1 is indexed by a hash function of PC, selected register digest, and bank ID modulo 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash algorithm is used to compute index h1 from the PC and selected register digest?",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/state/4/organization",
      "claim": "Prediction Weight Table 2 consists of 8 banks of 128 entries storing 6-bit signed weights totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage budget with 8 banks containing 2^7 (128) entries of 6 bits for WT2, totaling 6144 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/indexing",
      "claim": "WT2 is indexed by a hash function of PC, selected register digest, and bank ID modulo 128.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash algorithm is used to compute index h2 from the PC and selected register digest?",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_register_decode+algo:recover_on_squash` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alo...

[Init]
model=gemini-3.8-flash-medium conversation=22575263-368a-4f9c-a23e-22c2f7a6489b cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "Register tracking at decode is triggered during the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly specifies that register tracking begins at instruction decode when an instruction writes a destination register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "An instruction writing a destination register clears the valid bit and records its ROB tag in the RTT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper establishes that instructions writing a register clear the entry's valid bit and record their ROB index as a tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Destination register specifiers read by track_register_decode are external instruction metadata supplied by the processor decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The operation is driven by pipeline decode events where destination registers are properties of the decoded instruction rather than internal state written by another predictor algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim"
... [truncated]

[Usage]
{"input_tokens": 30819, "output_tokens": 28852, "thinking_tokens": 24800, "cache_read_tokens": 0, "total_tokens": 59671}

[Result]
status=SUCCESS conversation=22575263-368a-4f9c-a23e-22c2f7a6489b turns=1 duration=159.516190377s usage={"input_tokens": 30819, "output_tokens": 28852, "thinking_tokens": 24800, "cache_read_tokens": 0, "total_tokens": 59671}


