success: True
usage: {'input_tokens': 28636, 'output_tokens': 35125, 'thinking_tokens': 32156, 'cache_read_tokens': 0, 'total_tokens': 63761}

## result
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is titled 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' from CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title matches the source specification title and publication context."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component maintains 12-bit digests of 65 logical registers across 8 banks, invalidating stale digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 instructions as the aging threshold for invalidating register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The predictor tracks 65 logical registers across 8 banks for the sR component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly dimensions the usefulness weight table across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Register component training is triggered at instruction commit time or branch resolution time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does RUNLTS trigger the training update of register components at instruction commit time or at branch resolution time?",
      "enum_candidates": [
        "commit_time",
        "branch_resolution_time"
      ]
    },
    {
      "pointer": "/parameters/7",
      "claim": "The usefulness update condition for register components is based on bank direction correctness, reversed base correctness, or SC usefulness.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which specific condition determines whether usefulness weights (UT) in the register component are incremented during training?",
      "enum_candidates": [
        "bank_dir_correct",
        "reversed_base_correct",
        "sc_useful"
      ]
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At decode time, instructions writing destination registers clear the scoreboard valid bit and record their ROB index as a tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper directly specifies tracking in-flight register allocations at decode using the ROB index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register scoreboard contains 65 entries where each entry has 1 valid bit, an 8-bit decay counter, and a 14-bit payload holding either a 14-bit tag or a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The entry bit budget and payload sharing match the paper description and Table 3 entry breakdown."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component consumes 53,863 bits of storage divided into 43,008 bits for WT, 9,360 bits for UT, and 1,495 bits for the auxiliary tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 explicitly records the exact WT formula, matching 43,008 bits and the total of 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation is triggered when functional execution completes producing a register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies updating the scoreboard with the generated digest upon instruction execution completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Integer register digests are formed by XOR-folding a 6-bit count of trailing zeros/ones, a 6-bit count of leading zeros/ones shifted by 3, and the register's 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The prose and Figure 6(a) establish the 12-bit overlapping XOR-fold of the three 6-bit fields."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Condition-code flag digests replicate the 4 flag bits three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper states condition code replication verbatim, matching Figure 6(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Floating-point digests extract format-specific slices right-aligned at bit position 3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The extracted slices in Figure 6(b) correspond to the sign bit and high exponent bits right-aligned at bit 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "How floating-point format classification (FP16 vs FP32 vs FP64) is performed by inspecting most significant bits is unspecified.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does RUNLTS inspect the most significant bits of a 64-bit register value to classify floating-point format as FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_boxing",
        "instruction_type",
        "exponent_bits"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Pseudocode contains a call to undefined helper 'bits(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The occurrence of 'bits (' in the pseudocode is part of an explanatory text comment ('run-lengths of identical bits (zeros or ones)') rather than a helper function invocation, refuting the finding as a false positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For integer value 0x8 with leading_cnt=60, trailing_cnt=3, and val_lsb6=8, the resulting digest is 0x3E3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Evaluating 3 ^ (60 << 3) ^ (8 << 6) yields 0x003 ^ 0x1E0 ^ 0x200 = 0x3E3, matching the Figure 6(a) fold formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For condition flags value 0x9, replication three times yields digest 0x999.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Replicating 4-bit value 0x9 across three nibbles yields (0x9 << 8) | (0x9 << 4) | 0x9 = 0x999."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Decay counter decrements per decode tick, clearing the entry valid bit when reaching 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Decreasing decay counter to 0 invalidates the scoreboard entry to prevent stale digest usage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Bank contributions are scaled by 2.5 when usefulness is positive and suppressed (x0) when non-positive or unavailable.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly illustrates the per-bank sum being scaled by x0 or x2.5 before cross-bank summation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "When multiple registers are available in the same bank at prediction time, exactly one is chosen randomly for update during training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states random selection among available registers in a bank during update."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+global+algo:Digest Generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=94bf96c0-ddb5-46d0-a44a-6fa5d1348811 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_6da967e3400f7bfd

[Response]
```json
{
  "records": [
    {
      "pointer": "/source",
      "claim": "The source paper is titled 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables' from CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title matches the source specification title and publication context."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component maintains 12-bit digests of 65 logical registers across 8 banks, invalidating stale digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 instructions as the aging threshold for invalidating register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The predictor tracks 65 logical registers across 8 banks for the sR component.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly dimensions the usefulness weight table across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Register component training is triggered at instruction commit time or branch resolution time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does RUNLTS trigger the training update of register components at instruction commit time or at branch resolution time?",
      "enum_candidates
... [truncated]

[Usage]
{"input_tokens": 28636, "output_tokens": 35125, "thinking_tokens": 32156, "cache_read_tokens": 0, "total_tokens": 63761}

[Result]
status=SUCCESS conversation=94bf96c0-ddb5-46d0-a44a-6fa5d1348811 turns=1 duration=185.389010447s usage={"input_tokens": 28636, "output_tokens": 35125, "thinking_tokens": 32156, "cache_read_tokens": 0, "total_tokens": 63761}


