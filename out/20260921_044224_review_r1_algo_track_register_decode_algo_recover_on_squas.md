success: True
usage: {'input_tokens': 30796, 'output_tokens': 29654, 'thinking_tokens': 26290, 'cache_read_tokens': 0, 'total_tokens': 60450}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The track_register_decode procedure is triggered during the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly places the register tracking operation at the instruction decode stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a register clears the valid bit and records its 14-bit ROB tag in the RTT entry.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper directly specifies clearing the valid bit and storing the ROB index as a tag upon decoding a register-writing instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Destination registers and ROB tags read by track_register_decode are standard architectural inputs provided by the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper identifies the decode stage of the processor as the producer supplying destination registers and ROB indices."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The RTT consists of 65 entries corresponding to 65 logical registers divided across 8 banks, with 9 registers in Bank 0 and 8 in Banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies that the register component is organized into eight banks of eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each RTT entry consists of a 1-bit valid flag, a 14-bit payload, and an 8-bit instruction decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the exact entry format of 1 valid bit, 14 payload bits, and 8 decay counter bits across all 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total storage capacity of the Register Tracking Table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 65 entries by 23 bits per entry (1 + 14 + 8) yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default decay threshold for invalidating stale register digests is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies 256 subsequent decoded instructions as the digest invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default number of logical registers tracked by the predictor is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies exactly 65 logical registers across the usefulness tables and RTT auxiliary data."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/storage_impact",
      "claim": "Each logical register requires 23 bits in the RTT and 144 bits across the usefulness tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 shows each register requires 23 bits of auxiliary RTT state and 3 tables of 8 entries with 6-bit weights (144 bits) in UT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction Weight Table 0 has 8 banks with 512 entries per bank and 6-bit signed weights totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of 2^9 (512) 6-bit entries for WT0, totaling 24576 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "Prediction Weight Table 1 has 8 banks with 256 entries per bank and 6-bit signed weights totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of 2^8 (256) 6-bit entries for WT1, totaling 12288 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "Prediction Weight Table 2 has 8 banks with 128 entries per bank and 6-bit signed weights totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of 2^7 (128) 6-bit entries for WT2, totaling 6144 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For an integer register with all zero bits, leading and trailing zero counts cap at 63 to fit in 6-bit fields.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U3 identifies that the paper does not specify how 6-bit count fields represent counts from 0 to 64 for 64-bit words, such as saturating at 63, taking modulo 64, or counting bits matching the sign bit.",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "sign_match"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Integer register digests are formed by XOR-folding trailing zero counts at [5:0], leading zero counts at [8:3], and the 6 LSBs at [11:6].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U3 notes that the encoding of leading/trailing counts is ambiguous, and the overlapping bit alignment and XOR-folding formula are inferred from figure geometry rather than explicitly stated in prose.",
      "enum_candidates": [
        "xor_fold",
        "concat",
        "match_extremes"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Flag register digests are generated by replicating the 4 condition-code bits three times into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the 4 condition-code bits are replicated three times to construct the 12-bit flag digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "FP32 register digests extract bits [31:26] and place them right-aligned at digest bit 3 with digest bits [2:0] set to zero.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U4 states that right-alignment of floating-point digest slices at bit 3 is read off figure drawing geometry rather than stated, with right-alignment at bit 0 remaining an unruled-out reading.",
      "enum_candidates": [
        "align_bit3",
        "align_bit0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A valid RTT entry remains valid through instruction count 255 and is invalidated at instruction count 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper defines digest invalidation as occurring exactly after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's usefulness sum is non-positive, the bank multiplier selects x0 to contribute zero to sR.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U2 notes that Figure 5(c) does not explicitly label the control wire driving the bank multiplier between x0 and x2.5, leaving whether it is gated by the bank usefulness sign or a global scale unsettled.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "static_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When a bank's usefulness sum is positive, the bank multiplier scales the bank's WT output by x2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Ambiguity U2 notes that Figure 5(c) leaves the driving signal for x0 vs x2.5 bank scaling unlabelled, making bank usefulness gating an inference rather than a settled specification.",
      "enum_candidates": [
        "bank_usefulness_sign",
        "static_2_5"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers in a bank were available at prediction time, exactly one is chosen randomly for training update upon misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly specifies randomly selecting one available register in the bank to perform single-port table training updates."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "The recover_on_squash routine recovers RTT entries by clearing pending payloads matching flushed ROB tags on a pipeline flush.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 5 explicitly leaves recovering the Tomasulo-like table on branch mispredictions and squashes as future work, so the pipeline flush recovery algorithm for RTT entries is not settled by the paper.",
      "enum_candidates": [
        "clear_flushed_tags",
        "flash_invalidate",
        "no_recovery"
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
model=gemini-3.8-flash-medium conversation=f371ad54-3460-436e-b01e-01e24573c334 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The track_register_decode procedure is triggered during the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly places the register tracking operation at the instruction decode stage."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "At decode, an instruction writing a register clears the valid bit and records its 14-bit ROB tag in the RTT entry.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper directly specifies clearing the valid bit and storing the ROB index as a tag upon decoding a register-writing instruction."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Destination registers and ROB tags read by track_register_decode are standard architectural inputs provided by the instruction decode stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper identifies the decode stage of the processor as the producer supplying destination registers and ROB indices."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The RTT consists of 65 entries corresponding to 65 logical registers divid
... [truncated]

[Usage]
{"input_tokens": 30796, "output_tokens": 29654, "thinking_tokens": 26290, "cache_read_tokens": 0, "total_tokens": 60450}

[Result]
status=SUCCESS conversation=f371ad54-3460-436e-b01e-01e24573c334 turns=1 duration=141.437933591s usage={"input_tokens": 30796, "output_tokens": 29654, "thinking_tokens": 26290, "cache_read_tokens": 0, "total_tokens": 60450}


