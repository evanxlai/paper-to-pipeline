success: True
usage: {'input_tokens': 31281, 'output_tokens': 34626, 'thinking_tokens': 29866, 'cache_read_tokens': 0, 'total_tokens': 65907}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_register_complete logic triggers at instruction execution / writeback stage when an instruction completes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload overwrite and valid bit update occur upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, if destination register is valid, RTT overwrites payload with the generated 12-bit digest and sets the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies overwriting the payload with the produced value's digest and asserting the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The RTT entry payload can store a 14-bit in-flight ROB tag or a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines the RTT entry payload size as accommodating a 14-bit tag or 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay window reset upon completion is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly defines the invalidation window as 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The decay counter ticks per decoded instruction during the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper defines the decay lifetime in terms of subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "RTT entries decay and are invalidated across all 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies 65 RTT entries each containing a decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Stale digests are invalidated when their decay counter expires.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating register digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "RTT has 65 entries partitioned across 8 banks, with Bank 0 holding 9 registers and Banks 1 to 7 holding 8 registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the 8-bank organization with eight or nine logical registers per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each RTT entry consists of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data defines the RTT entry structure as 1 valid bit, 14 payload bits, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "RTT consumes 1495 bits of total storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 65 entries by (1 + 14 + 8) bits per entry yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "RTT is directly indexed by logical register ID.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper states the table contains one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "WT0 comprises 8 banks of 512 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 allocates 8 banks with 2^9 (512) entries for the largest WT component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "WT0 entries are 6-bit signed counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that WT entries are 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "WT0 consumes 24576 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * 512 entries * 8 banks equals 24576 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "WT0 is indexed by a hash function hashing PC, selected register digest, and bank ID modulo 512.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What concrete hash function combines PC and selected register digest to index WT0 entries?",
      "enum_candidates": [
        "xor_fold",
        "crc",
        "prime_mod"
      ]
    },
    {
      "pointer": "/state/3/organization",
      "claim": "WT1 comprises 8 banks of 256 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 allocates 8 banks with 2^8 (256) entries for the medium WT component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/entry_format",
      "claim": "WT1 entries are 6-bit signed counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights for WT entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/size_bits",
      "claim": "WT1 consumes 12288 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * 256 entries * 8 banks equals 12288 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3/indexing",
      "claim": "WT1 is indexed by a hash function hashing PC, selected register digest, and bank ID modulo 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What concrete hash function combines PC and selected register digest to index WT1 entries?",
      "enum_candidates": [
        "xor_fold",
        "crc",
        "prime_mod"
      ]
    },
    {
      "pointer": "/state/4/organization",
      "claim": "WT2 comprises 8 banks of 128 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 allocates 8 banks with 2^7 (128) entries for the smallest WT component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/entry_format",
      "claim": "WT2 entries are 6-bit signed counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that WT entries are 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/size_bits",
      "claim": "WT2 consumes 6144 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "6 bits * 128 entries * 8 banks equals 6144 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/indexing",
      "claim": "WT2 is indexed by a hash function hashing PC, selected register digest, and bank ID modulo 128.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What concrete hash function combines PC and selected register digest to index WT2 entries?",
      "enum_candidates": [
        "xor_fold",
        "crc",
        "prime_mod"
      ]
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default decay threshold is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper fixes the invalidation threshold at 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The decay threshold parameter has a tuning range of [64, 1024].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed decay threshold of 256 instructions; what is the legal tuning range for decay_threshold_insts?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies 65 logical registers for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The number of logical registers parameter has a tuning range of [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates an architecture with 65 logical registers; what is the legal tuning range for num_logical_registers across target architectures?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "INT zero digest generation saturates leading and trailing zero counts at 63.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading and trailing zero/one counts exceeding 63 encoded into the 6-bit count fields for 64-bit INT registers?",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "sign_match"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "INT digest generation combines trailing count, leading count, and LSBs via XOR folding.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading zero/one counts encoded and combined with trailing counts and register value bits?",
      "enum_candidates": [
        "xor_fold",
        "concat",
        "add"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag digest generation replicates the four condition-code bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 12-bit digest is formed by replicating the 4 flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "FP32 digest extracts bits [31:26] and right-aligns them at bit 3 leaving bits [2:0] zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Should the extracted floating-point bit slice be right-aligned at digest bit 3 or bit 0?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "An RTT entry remains valid for 255 decoded instructions and is invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states that digests are invalidated after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's usefulness is non-positive, its multiplier selects x0 and contributes 0 to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What signal selects between multiplier x0 and x2.5 for each bank in the register component?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When a bank's usefulness is positive, its multiplier selects x2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What condition drives the bank multiplier selection of x2.5 versus x0 for the bank's weight sum?",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers in a bank are available at prediction time, one is randomly chosen for training update.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that one available register within the bank is randomly selected for the update."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:track_register_complete+algo:track_register_decay` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spe...

[Init]
model=gemini-3.8-flash-medium conversation=c4be4a27-d8f4-430c-979e-acc3321f4fec cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The track_register_complete logic triggers at instruction execution / writeback stage when an instruction completes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload overwrite and valid bit update occur upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "On instruction complete, if destination register is valid, RTT overwrites payload with the generated 12-bit digest and sets the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies overwriting the payload with the produced value's digest and asserting the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The RTT entry payload can store a 14-bit in-flight ROB tag or a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines the RTT entry payload size as accommodating a 14-bit tag or 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay window reset upon completion is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates 
... [truncated]

[Usage]
{"input_tokens": 31281, "output_tokens": 34626, "thinking_tokens": 29866, "cache_read_tokens": 0, "total_tokens": 65907}

[Result]
status=SUCCESS conversation=c4be4a27-d8f4-430c-979e-acc3321f4fec turns=1 duration=175.595110085s usage={"input_tokens": 31281, "output_tokens": 34626, "thinking_tokens": 29866, "cache_read_tokens": 0, "total_tokens": 65907}


