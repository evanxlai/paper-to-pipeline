success: True
usage: {'input_tokens': 30269, 'output_tokens': 31817, 'thinking_tokens': 27488, 'cache_read_tokens': 0, 'total_tokens': 62086}

## result
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "Verbatim title of the source paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends the SC by capturing correlations between recently produced architectural register values and branch outcomes using an 8-bank organization across 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles the 8-bank organization and register mapping of the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The sR_RegTracker contains 65 entries, each with a 1-bit valid bit, 14-bit payload, and 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data row establishes the exact entry structure, register count, and bit widths."
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
        "why": "Table 3 dimensions the usefulness table for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The number of logical registers has a legal tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The legal range of num_logical_registers is not settled by the paper, which assumes a fixed 65-register architectural model; whether the predictor structure can be tuned across [32, 128] depends on ISA constraints.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default value of decay_interval is 255.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The default value of 255 collides with the declared range constraint '[64, 1024] pow2' requiring a power of two, and contradicts the paper's specification of 256 decoded instructions."
      },
      "patch": {
        "op": "replace",
        "pointer": "/parameters/2/default",
        "value": 256
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The decay interval has a parameter range of [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies invalidation after 256 instructions; whether the decay interval parameter range [64, 1024] pow2 is valid for tuning is not settled by the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest generation triggers when an instruction completes execution and writes a value to a destination register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Settles that digest generation and payload update take place upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, the 12-bit digest encodes the trailing zeros/ones count, leading zeros/ones count, and 6 LSBs of the value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Directly defines the three 6-bit fields used to generate integer register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For floating-point registers, the digest extracts bits [15:13] for FP16, bits [31:26] for FP32, and bits [63:55] for FP64, shifted to bit position 3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Matches the extracted sign and exponent slices transcribed in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For condition-code flags, the 12-bit digest is formed by replicating the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Verbatim definition of the flags digest format."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The pseudocode in generate_digest uses standard language keywords and operators without calling undefined helper functions 'and', 'cnt', or 'return'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values.",
        "why": "Settles that 'and' is a boolean operator, 'cnt' is a local loop variable, and 'return' is a language control keyword, refuting the undefined helper findings."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Floating-point format classification tests whether upper register bits are zero using (val >> 16) == 0 and (val >> 32) == 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are floating-point formats (FP16, FP32, FP64) classified from the 64-bit register value, given standard NaN-boxing conventions?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "Leading and trailing identical bit counts saturate at 63 to fit in 6 bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 6-bit count of leading/trailing identical bits (spanning 0 to 64) saturate at 63 or wrap modulo 64?",
      "enum_candidates": [
        "saturate",
        "wrap"
      ]
    },
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The track_decode algorithm triggers at instruction decode time for any instruction producing a register write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Establishes that instruction decode time is the trigger for updating tracker state on a register write."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode time, the register tracker marks the destination register invalid and writes the allocated ROB tag into the payload.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Confirms clearing valid and storing ROB tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decay counter is initialized at decode time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does the 256-instruction decay counter start counting down at instruction decode or upon instruction completion/writeback when the digest becomes valid?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test digest_generation_flags verifies that a 4-bit flag value 0x9 replicates into a 12-bit digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Confirms replication of 4 flag bits three times produces 0x999 from 0x9."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test digest_generation_int_xor_fold verifies the 3-way XOR fold of trailing count, 3-bit shifted leading count, and 6-bit shifted value LSBs.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and Section 4.2 establish the 3-way XOR-folded structure tested here."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test digest_generation_fp32 verifies that Value[31:26] is mapped to digest bits [8:3] with bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) assigns Value[31:26] to digest bit positions [8:3], leaving bits [2:0] zeroed."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test decay_invalidation_after_256_instructions verifies that an entry transitions to invalid after 256 instructions decoded without a write to the register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Verbatim requirement for invalidating digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test bank_usefulness_selection verifies that the available register with the largest summed usefulness in a bank is selected to index WT0-WT2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Establishes that the most useful available register in the bank is selected to index the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Unit test bank_usefulness_multiplier_gating verifies that a bank's output is multiplied by x0 when its selected register has non-positive usefulness.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) transcription confirms the multiplier stage scales bank output by x0 or x2.5 based on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The update condition for UT usefulness counters is an architectural parameter resolved across sampled_pred_correct, sc_correct, sc_override_correct, and bank_agree_actual.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training condition determines whether a register is marked useful during UT update?",
      "enum_candidates": [
        "sampled_pred_correct",
        "sc_correct",
        "sc_override_correct",
        "bank_agree_actual"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The index hash function for UT0-UT2 is an architectural parameter resolved across xor_fold, prime_mod, crc32, and bit_slice.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash function generates the 3-bit index for UT0-UT2 from the branch PC?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc32",
        "bit_slice"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "The hash function combining branch PC and register digest into WT indices h0-h2 is an architectural parameter resolved across xor_fold, prime_mod, and bit_select.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What specific hash function combines branch PC and register digest into table indices h0, h1, h2 for WT0-WT2?",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "bit_select"
      ]
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires host interfaces for register writeback/completion broadcast, instruction decode notification, fetch branch PC, and branch commit outcome.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Confirms the host pipeline interactions needed at decode and completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component consumes 53,863 total storage bits, comprising 43,008 bits for WT, 9,360 bits for UT, and 1,495 bits for RegTracker auxiliary data.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 defines the exact storage formula and totals 53,863 bits for the sR component."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_decode+orphan+global+algo:generate_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec ...

[Init]
model=gemini-3.8-flash-medium conversation=713056ab-a135-4531-9328-97d82d75aa3a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6b89e3e73086103a

[Response]
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "Verbatim title of the source paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component extends the SC by capturing correlations between recently produced architectural register values and branch outcomes using an 8-bank organization across 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Settles the 8-bank organization and register mapping of the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The sR_RegTracker contains 65 entries, each with a 1-bit valid bit, 14-bit payload, and 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data row establishes the exact entry structure, register count, and bit widths."
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
        "why": "Table 3 dimensions the usefulness table for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/
... [truncated]

[Usage]
{"input_tokens": 30269, "output_tokens": 31817, "thinking_tokens": 27488, "cache_read_tokens": 0, "total_tokens": 62086}

[Result]
status=SUCCESS conversation=713056ab-a135-4531-9328-97d82d75aa3a turns=1 duration=159.555436035s usage={"input_tokens": 30269, "output_tokens": 31817, "thinking_tokens": 27488, "cache_read_tokens": 0, "total_tokens": 62086}


