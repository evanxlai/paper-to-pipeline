success: True
usage: {'input_tokens': 28835, 'output_tokens': 40729, 'thinking_tokens': 35886, 'cache_read_tokens': 0, 'total_tokens': 69564}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction_decode algorithm is triggered at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that tracking table tag updates are performed at instruction decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The function on_instruction_decode is an undefined helper primitive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The symbol on_instruction_decode is the definition of the entry point function triggered at decode rather than an undefined external call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the entry's valid bit and stores its 14-bit ROB index tag in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that instructions writing a register clear the valid bit and store the ROB index as a tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Decay counters for valid registers decrement on each decoded instruction and clear valid when reaching zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper establishes that valid register digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "A destination register entry initializes decay_ctr to 256 at decode time while valid is 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does decay counter initialization occur at decode time or upon instruction completion when valid is set, and how is an 8-bit counter initialized without overflowing?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "The table maintains register availability using Tomasulo-like tag tracking where digests decay after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The paper describes using a Tomasulo-like structure to track valid register digests for prediction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register tracking table is direct-mapped with 65 entries indexed by logical register ID (R0 to R64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper specifies one entry per logical register, totaling 65 registers across eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each table entry contains a 1-bit valid flag, a 14-bit payload holding a 14-bit ROB index tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies the 1-bit valid and 14-bit payload fields in prose and confirms the 8-bit decay_ctr in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The 8-bit decay_ctr down-counter is initialized to 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is the 8-bit decay counter initialized and clocked to count 256 instructions given that 256 cannot be represented in an 8-bit unsigned field?",
      "enum_candidates": [
        "init_255",
        "underflow_invalidation",
        "wrap_zero"
      ]
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total storage capacity of the register tracking table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 budgets 23 bits per entry for 65 entries, multiplying out to 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register tracking table is directly indexed by logical register ID (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Allocating one entry per logical register dictates direct indexing by logical register ID."
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
        "why": "The paper specifies eight banks of eight or nine registers each (1x9 + 7x8 = 65), matching Table 3's 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The allowable parameter range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does num_logical_registers have an allowable tuning range, or is it strictly fixed to 65 by the ISA architecture?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "num_logical_registers scales UT entry width and register tracking table storage at 23 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies that tracking table storage scales linearly with register count at 23 bits per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default decay period is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly sets digest lifetime to 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The allowable tuning range for decay_instructions is [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the legal search range for decay_instructions during tuning?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "decay_instructions sets decay_ctr width = ceil(log2(decay_instructions)) bits in the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 budgets an 8-bit counter corresponding to log2(256) for a 256-instruction decay window."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer value 0x8 produces 12-bit digest (3 & 0x3F) ^ ((60 & 0x3F) << 3) ^ ((8 & 0x3F) << 6) = 995 (0x3E3).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values.",
        "why": "Figure 6(a) defines XOR-folding the 6-bit trailing zero count, 3-bit shifted leading zero count, and 6-bit shifted value LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A condition-code register producing 4-bit flag pattern 0b1011 generates 12-bit digest 0b101110111011 (0xBBB) by three-fold replication.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the 4-bit flag value three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Bank 0 selects the most useful register among available registers by summing UT outputs and hashes PC with its digest to query WT tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies selecting the available register with the largest usefulness score within the bank to index the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "When bank usefulness is non-positive, multiplier selects x0 and the bank contributes 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What condition or threshold determines the selection of x0 versus x2.5 for a bank's multiplier in the register component?",
      "enum_candidates": [
        "usefulness_positive",
        "useful_bit",
        "always_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When bank usefulness is positive, multiplier scales WT sum by 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Is bank multiplier scaling by 2.5 selected whenever summed bank usefulness is strictly greater than zero?",
      "enum_candidates": [
        "usefulness_positive",
        "threshold_check",
        "always_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A valid digest invalidates after 256 subsequent instructions are decoded without any new write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper directly specifies invalidating each digest after 256 subsequent instruction decodes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Older in-flight instructions completed before branch misprediction resolution remain valid upon pipeline restart while squashed instructions are invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explains that instructions completing prior to misprediction resolution retain their computed values for the predictor upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction_complete algorithm triggers upon execution complete / writeback for a producing instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies that overwriting the payload with the digest and setting valid occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Instruction completion makes register digests available for subsequent branch predictions prior to commit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that valid digests are forwarded to SC components as soon as completion sets the valid bit, prior to commit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "count_leading_zeros counts leading zero bits for integer register digest generation.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are counts of leading zeros (or ones) computed and distinguished in the 6-bit count field?",
      "enum_candidates": [
        "zeros_only",
        "count_sign_match",
        "zeros_or_ones"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "count_trailing_zeros counts trailing zero bits for integer register digest generation.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are counts of trailing zeros (or ones) computed and distinguished in the 6-bit count field?",
      "enum_candidates": [
        "zeros_only",
        "count_lsb_match",
        "zeros_or_ones"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "generate_digest is an undefined external helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values.",
        "why": "generate_digest is an internal helper defined directly within the same pseudocode block."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "on_instruction_complete is an undefined external helper function.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "on_instruction_complete defines the entry point function for the completion trigger rather than an undefined external helper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "uint12 is an undefined helper primitive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "uint12 represents bit-width truncation to the 12-bit digest width mandated by the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Floating-point register digests are generated by extracting bits [63:55] shifted left by 3 bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the hardware classify FP16, FP32, and FP64 from the register's most significant bits, and how are FP16 and FP32 aligned in the 12-bit digest?",
      "enum_candidates": [
        "classify_by_msb",
        "fp64_only",
        "fp32_fp64"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On instruction complete, payload is overwritten with digest and valid is set to 1 only if valid is 0 and payload matches the ROB index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Tag matching ensures that completing instructions only update the entry if a younger instruction has not overwritten the tag."
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
model=gemini-3.8-flash-medium conversation=7fcaf6bb-7c54-430b-8787-33de6ba2d0cd cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The instruction_decode algorithm is triggered at decode time for every instruction in the execution stream.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper specifies that tracking table tag updates are performed at instruction decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The function on_instruction_decode is an undefined helper primitive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The symbol on_instruction_decode is the definition of the entry point function triggered at decode rather than an undefined external call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "At decode, an instruction writing a destination register clears the entry's valid bit and stores its 14-bit ROB index tag in the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that instructions writing a register clear the valid bit and store the ROB index as a tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Decay counters for valid registers decrement on each decoded instruction and clear vali
... [truncated]

[Usage]
{"input_tokens": 28835, "output_tokens": 40729, "thinking_tokens": 35886, "cache_read_tokens": 0, "total_tokens": 69564}

[Result]
status=SUCCESS conversation=7fcaf6bb-7c54-430b-8787-33de6ba2d0cd turns=1 duration=221.687141813s usage={"input_tokens": 28835, "output_tokens": 40729, "thinking_tokens": 35886, "cache_read_tokens": 0, "total_tokens": 69564}


