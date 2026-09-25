success: True
usage: {'input_tokens': 28601, 'output_tokens': 33919, 'thinking_tokens': 29582, 'cache_read_tokens': 0, 'total_tokens': 62520}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction decode trigger only activates when an instruction writing a destination register is decoded.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Digest decay tracks every decoded instruction, so the decode stage trigger must fire for every decoded instruction rather than only instructions writing a destination register."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/trigger",
        "value": "lookup time / decode stage: on each decoded instruction (with destination register rd, if any)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On each instruction decode, decay counters of all valid register status entries increment, and any entry reaching 256 decoded instructions is invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly requires each valid digest to be invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When an instruction writing destination register rd decodes, the entry's valid bit is cleared and its payload stores the 14-bit ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper describes storing the ROB index as a tag in the entry and clearing the valid bit at decode time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "Clearing the valid bit on decode invalidates any previous digest because a new definition is in flight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Clearing the valid bit at decode ensures stale digests are not read while a new value is being computed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The instruction completion trigger activates when an instruction completing execution writes a value to register rd.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the completion action as occurring when the instruction completes execution and produces its value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Upon completion, the entry is updated only if it is currently invalid and its payload matches the completing instruction's 14-bit ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "Tomasulo's algorithm requires matching the in-flight tag before updating the architectural register status to ensure younger definitions are not overwritten."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Upon completion, the payload is overwritten with the 12-bit digest of the produced value and the valid bit is asserted.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that completing instructions overwrite the payload with the digest and set the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Digest generation is invoked via an undefined helper function generate_digest without algorithm specification.",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/4/pseudocode",
        "value": "function generate_digest(reg_type, val_64bit):\n  if reg_type == 0: // INT\n    trail = count_trailing_zeros(val_64bit) & 0x3F\n    lead = count_leading_zeros(val_64bit) & 0x3F\n    lsb = val_64bit & 0x3F\n    return (trail & 0x3F) ^ ((lead & 0x3F) << 3) ^ ((lsb & 0x3F) << 6)\n  else if reg_type == 1: // FP64\n    return ((val_64bit >> 55) & 0x1FF) << 3\n  else if reg_type == 2: // FP32\n    return ((val_64bit >> 26) & 0x3F) << 3\n  else if reg_type == 3: // FP16\n    return ((val_64bit >> 13) & 0x7) << 3\n  else if reg_type == 4: // FLAGS\n    flags = val_64bit & 0xF\n    return flags | (flags << 4) | (flags << 8)\n  return 0\n\nfunction on_complete(rd, rob_index, val_64bit, reg_type):\n  if rd >= 0 and rd < 65:\n    if register_status_table[rd].valid == 0 and register_status_table[rd].payload == (rob_index & 0x3FFF):\n      digest = generate_digest(reg_type, val_64bit)\n      register_status_table[rd].payload = digest\n      register_status_table[rd].valid = 1\n      register_status_table[rd].decay_ctr = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The integer digest calculation counts leading and trailing zeros rather than ones or sign-matching bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the integer digest count leading/trailing zeros, leading/trailing ones, or bits matching the sign bit?",
      "enum_candidates": [
        "zeros",
        "ones",
        "sign_matching"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Leading and trailing counts exceeding 63 bits wrap or saturate into the 6-bit count fields.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading and trailing bit counts (range 0 to 64) encoded into the 6-bit count fields in the integer digest?",
      "enum_candidates": [
        "saturate",
        "truncate_mod64",
        "sign_matching"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table has 65 entries corresponding to logical registers 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates 65 status entries for sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry contains a 1-bit valid flag, a 14-bit payload holding either an ROB index tag or a 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry bit breakdown with valid (1 bit), payload (14 bits), and decay_ctr (8 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register status table consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 23 bits per entry by 65 entries equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "The register status table is direct-mapped by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Having one entry per logical register defines direct-mapped indexing by logical register index."
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
        "why": "Eight banks containing eight or nine registers each sum to exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The parameter num_registers has tuning range [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the legal search range for num_registers during tuning, given that the paper only evaluates an architecture with 65 logical registers?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default digest decay threshold is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 decoded instructions as the digest invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The parameter decay_threshold has tuning range [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the legal tuning range for decay_threshold, given that the paper evaluates only a fixed threshold of 256?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The default register digest size is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly defines the register value digest size as 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The parameter digest_bits has tuning range [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What is the legal tuning range for digest_bits, given that the paper only evaluates 12-bit digests?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register value produces a 12-bit digest by XOR-folding its 6-bit trailing zero count, 6-bit leading zero count shifted left by 3, and 6 LSBs shifted left by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) specifies the XOR-folded layout of trailing count at [5:0], leading count at [8:3], and LSBs at [11:6], matching the test computation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A 64-bit floating point value produces a 12-bit digest with bits [63:55] placed in digest bits [11:3] and bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies FP64 extracting Value[63:55] into digest bits [11:3] with unused bits at [2:0], matching the test expectation 0xC00."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "A condition flag register value produces a 12-bit digest by replicating its 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times across the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decays from valid to invalid on the 256th instruction decode tick without subsequent writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test matches the paper's specification of invalidating each digest after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank selects the available register digest with the highest cumulative usefulness to index prediction weight tables, scaling output by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies selecting the digest of the most useful register, and Figure 5(c) shows bank output scaling of x0 or x2.5 based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, when multiple registers in a bank were available at prediction time, one is pseudo-randomly selected for update so only one write port is accessed per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that training randomly selects one available register per bank to maintain a single write port per table."
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
model=gemini-3.8-flash-medium conversation=21ace53b-ae01-442b-babe-03a38df51e08 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The instruction decode trigger only activates when an instruction writing a destination register is decoded.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Digest decay tracks every decoded instruction, so the decode stage trigger must fire for every decoded instruction rather than only instructions writing a destination register."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/3/trigger",
        "value": "lookup time / decode stage: on each decoded instruction (with destination register rd, if any)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "On each instruction decode, decay counters of all valid register status entries increment, and any entry reaching 256 decoded instructions is invalidated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly requires each valid digest to be invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "When an instruction writing destination register rd decodes, the entry's valid bit is cleared and its payload stores the 14-bit ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding e
... [truncated]

[Usage]
{"input_tokens": 28601, "output_tokens": 33919, "thinking_tokens": 29582, "cache_read_tokens": 0, "total_tokens": 62520}

[Result]
status=SUCCESS conversation=21ace53b-ae01-442b-babe-03a38df51e08 turns=1 duration=178.068588148s usage={"input_tokens": 28601, "output_tokens": 33919, "thinking_tokens": 29582, "cache_read_tokens": 0, "total_tokens": 62520}


