success: True
usage: {'input_tokens': 28132, 'output_tokens': 32125, 'thinking_tokens': 26833, 'cache_read_tokens': 0, 'total_tokens': 60257}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1",
      "claim": "Register tracking table updates are triggered by decode, execution completion, instruction decay steps, and pipeline flushes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly describes triggering tracking table actions on decode, execution completion, and across flushes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decode hook is an external simulator pipeline event rather than an undefined algorithm helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines decode as the pipeline event where instructions writing registers update tracking table tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On decode of an instruction writing a destination register, the table entry's valid bit is cleared and its payload is set to the ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The quote directly confirms clearing the valid bit and storing the ROB index tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The instruction's ROB index is external context supplied by the processor pipeline at decode rather than internally produced predictor state.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper identifies the ROB index as an attribute of the in-flight instruction provided by the host pipeline at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decay step is an architectural timer decremented per decoded instruction rather than an internal learning, allocation, or replacement policy.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper defines invalidation as an elapsed count of decoded instructions, settling the timing of the decay step."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The execution completion hook is an external execution unit callback rather than an undefined algorithm helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies instruction completion in the execution backend as the trigger for updating the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On completion of an instruction matching the in-flight destination register tag, the payload is overwritten with the value digest, valid is set to 1, and decay counter is set to 255.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper confirms setting the valid bit and storing the digest into payload upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The pipeline flush hook is an external simulator event representing pipeline recovery after a misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper references post-flush predictor state, establishing pipeline flush as a host-provided recovery event."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On a pipeline flush, in-flight table entries matching squashed instructions are selectively invalidated using a squashed predicate.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should the Register Tracking Table recover in-flight entries on a pipeline flush, given that the paper leaves recovery of the Tomasulo-like table to future work?",
      "enum_candidates": [
        "clear_matching_tags",
        "clear_all_invalid",
        "no_action"
      ]
    },
    {
      "pointer": "/algorithms/1",
      "claim": "Valid digests completed prior to a flush persist across pipeline squashes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper explains that values completed before the flush remain available to the predictor upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table has 65 entries corresponding to logical registers 0 through 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly specifies 65 entries for the register tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of Register_Tracking_Table contains a 1-bit valid flag, a 14-bit payload holding either a ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The text defines the exact field widths of valid, tag, and digest, and Table 3 confirms decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table requires 1495 bits of total auxiliary storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying 23 bits per entry by 65 entries yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Tracking_Table is directly indexed by logical register index.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper establishes a dedicated one-to-one mapping between logical registers and tracking table entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default value of num_logical_registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates storage using 65 logical registers across all banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The legal tuning range for num_logical_registers is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes num_logical_registers to 65 without specifying a tuning range; what is the legal parameter range for num_logical_registers?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers scales UT storage by 144 bits per register and tracking table storage by 23 bits per register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register | 6 x (2^7 + 2^8 + 2^9) x 8 | 6 x 65 x (2^3 + 2^3 + 2^3) | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 proves UT scales at 6 * 24 = 144 bits per register and tracking table at 23 bits per register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default value of digest_width_bits is 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly fixes the register value digest width to 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The legal tuning range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper defines the digest generation schemes specifically for 12 bits; what is the valid tuning range for digest_width_bits?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Tracking table payload width must accommodate the maximum of rob_idx_bits and digest_width_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper specifies that the payload field holds either the tag or the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default value of decay_instruction_limit is 256.",
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
      "pointer": "/parameters/3",
      "claim": "The legal tuning range for decay_instruction_limit is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper tests only a 256-instruction decay limit; what is the valid parameter range for decay_instruction_limit?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Ceil(log2(decay_limit)) determines the 8-bit width of decay_ctr.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 allocates an 8-bit decay counter per entry, matching log2(256)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default weight table entry counts per bank are 512, 256, and 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 explicitly list 512, 256, and 128 entries for WT0, WT1, and WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The legal choices for wt_entries_bank are 256,128,64 | 512,256,128 | 1024,512,256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper presents only the 512,256,128 entry configuration for WT; what are the legal choices for wt_entries_bank?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "WT size equals sum(entries) * weight_bits * num_banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 calculates WT storage as 6 bits times the sum of table sizes across all 8 banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default value of ut_entries_subtable is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 specify 8 entries (2^3) for each of the three UT subtables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The legal tuning range for ut_entries_subtable is [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes UT subtables at 8 entries without evaluating alternatives; what is the legal tuning range for ut_entries_subtable?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "UT size equals 3 * ut_entries_subtable * num_logical_registers * weight_bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates UT storage as 6 weight bits times 65 registers times 24 total subtable entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer registers produce a 12-bit digest by XOR-folding trailing zero count, leading zero count shifted by 3, and value LSB shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The text and Figure 6(a) show the three 6-bit fields overlapping and XOR-folded to form the 12-bit integer digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition flag registers produce a 12-bit digest by replicating the 4 flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states replicating the 4 flag bits three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "64-bit floating-point registers extract bits [63:55] into digest bits [11:3] with bits [2:0] set to zero.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "FP64     Value[63:55]      9 bits        [11:3]        sign(63) + exp[62:55]",
        "why": "Figure 6(b) specifies extracting 9 bits [63:55] into digest positions [11:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "An active register digest decrements its decay counter per decoded instruction and invalidates upon reaching 256 instructions.",
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
      "pointer": "/unit_tests/4",
      "claim": "When a bank's combined usefulness is negative, its WT sum contribution is multiplied by 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows bank output gated by an x0 multiplier when usefulness is not positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When a bank's combined usefulness is positive, its WT sum contribution is scaled by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows bank output scaled by 2.5 when the bank is judged useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When multiple registers in a bank are available during training, exactly one is randomly selected for updating WT and UT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly describes randomly selecting one available register in the bank during training to require a single write port."
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
model=gemini-3.8-flash-medium conversation=97dba1d5-e3d0-4f5e-9bab-014558f0b6ee cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_7399dd7374e00887

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1",
      "claim": "Register tracking table updates are triggered by decode, execution completion, instruction decay steps, and pipeline flushes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly describes triggering tracking table actions on decode, execution completion, and across flushes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The decode hook is an external simulator pipeline event rather than an undefined algorithm helper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines decode as the pipeline event where instructions writing registers update tracking table tags."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "On decode of an instruction writing a destination register, the table entry's valid bit is cleared and its payload is set to the ROB index tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The quote directly confirms clearing the valid bit and storing the ROB index tag at decode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/
... [truncated]

[Usage]
{"input_tokens": 28132, "output_tokens": 32125, "thinking_tokens": 26833, "cache_read_tokens": 0, "total_tokens": 60257}

[Result]
status=SUCCESS conversation=97dba1d5-e3d0-4f5e-9bab-014558f0b6ee turns=1 duration=174.082883523s usage={"input_tokens": 28132, "output_tokens": 32125, "thinking_tokens": 26833, "cache_read_tokens": 0, "total_tokens": 60257}


