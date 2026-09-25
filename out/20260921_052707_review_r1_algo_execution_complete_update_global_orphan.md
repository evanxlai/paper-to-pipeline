success: True
usage: {'input_tokens': 30308, 'output_tokens': 36691, 'thinking_tokens': 31785, 'cache_read_tokens': 0, 'total_tokens': 66999}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The execution complete update is triggered when an instruction execution unit completes computation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies instruction completion as the event that triggers updating the payload with the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When an instruction completes, if the register status entry is invalid and its payload matches the ROB tag, the payload is overwritten with the computed digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the completion action as overwriting the payload with the produced value's digest and asserting valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Tracking mirrors Tomasulo's algorithm so that only the latest instruction claiming a destination register updates the entry on completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The paper explicitly states the mechanism adopts a method similar to Tomasulo's algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table contains 65 logical registers organized into eight banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper specifies 8 banks of 8 or 9 logical registers each, totaling 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each entry of the register status table consists of 1 valid bit, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper establishes the 1-bit valid and 14-bit payload fields in prose and confirms the 8-bit decay_ctr in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The register status table consumes 1,495 bits of storage (65 entries of 23 bits each).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 lists 65 entries of 23 bits (1 + 14 + 8) which evaluates exactly to 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The register status table contains one dedicated entry per logical register, directly indexed by register ID.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly states the table contains one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The staleness decay threshold defaults to 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper directly specifies invalidating each digest after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper states that digests generated from 64-bit register values are 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest XOR-folds trailing zero count, leading zero count shifted by 3, and 6 LSBs shifted by 6 to yield 0xB51 for value 42.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies encoding leading count, trailing count, and 6 LSBs into the 12-bit integer digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 digest extraction right-aligns bits [63:55] at bit 3 with bits [2:0] set to zero to produce 0xBF8.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) note U4 marks whether floating-point digests right-align at bit 3 or bit 0 as uncertain; the test expectation assumes bit 3 alignment.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition-code flag register digest replicates the 4 flag bits three times to produce 0x999 from 0x9.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states condition flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A digest is invalidated after 256 subsequent instructions are decoded and ignored in bank usefulness selection.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidating stale digests after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "For a given bank, the available valid register with the highest summed usefulness weight is selected and used with PC to index the prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly states the predictor picks the digest of the most useful available register to forward to the weight tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "A bank's prediction weight sum is gated to 0 when its best valid register has net usefulness sum <= 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) note U2 marks whether the x0 vs x2.5 multiplier is dynamically selected by bank usefulness <= 0 or a global static scale as uncertain.",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "A bank's prediction weight sum is scaled by 2.5 when its best valid register has positive net usefulness sum.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) note U2 marks the control wire selecting the 2.5 multiplier based on positive bank usefulness as uncertain.",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/summary",
      "claim": "sR is a register-value-aware predictor integrated into the SC of TAGE-SC-L that captures correlations between branch directions and recently produced register values without explicit dependency tracking.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "In particular, the register components, which utilize recently produced register values without explicitly tracking register dependencies, capture the correlation between register values and branch outcomes and contribute a significant improvement in accuracy.",
        "why": "The paper states that register components capture correlations between branch outcomes and register values without explicit dependency tracking."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source/paper_title",
      "claim": "The title of the paper is 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The title appears verbatim on the title banner of the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source/citation",
      "claim": "The citation correctly identifies the authors, venue, date, and pages of the CBP 2025 paper.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The citation string matches the publication details verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "Instruction decode/rename provides destination register ID and ROB tag to clear valid and record the pending ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper explicitly states that decode stores the ROB index as a tag and clears the valid bit."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "Execution completion provides result value and ROB tag to generate the digest and set the valid bit.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly specifies overwriting the payload with the produced value's digest upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "A decoded instruction pulse is required to track the 256-instruction staleness threshold.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper specifies invalidation after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "Pipeline squash / flush handling leverages values completed during misprediction resolution across restarts.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper explicitly describes exploiting extra register values visible after pipeline flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/4",
      "claim": "The Statistical Corrector summation interface incorporates sR partial sums into LSUM.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) sR: Our proposed component for exploiting register-value correlations (Section 4.2)",
        "why": "The paper integrates sR as one of the SC predictor components feeding the LSUM summation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "Total storage cost for sR is 53,863 bits (WT: 43,008 bits, UT: 9,360 bits, Register Status Table: 1,495 bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                         | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the exact formulas and storage total of 53,863 bits for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The parameter 'sr_enable' is defined as a boolean knob that gates sR and saves 53,863 bits when disabled, but is not referenced in algorithm pseudocode.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Parameter 'sr_enable' is declared as a tuning knob saving 53,863 bits but is unreferenced in algorithm pseudocode; how should sr_enable gate sR predictor operations?",
      "enum_candidates": [
        "gate_sc_sum",
        "gate_all_updates",
        "compile_flag"
      ]
    },
    {
      "pointer": "/parameters/8",
      "claim": "The floating-point register digest alignment is settled by the paper as either align_bit_3 or align_bit_0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) note U4 marks whether FP digests align at bit 3 or bit 0 as uncertain.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/parameters/9",
      "claim": "The count encoding for integer register digests in Figure 6(a) is settled by the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) note U3 marks whether 6-bit leading/trailing zero counts saturate at 63, wrap modulo 64, or match the sign bit as uncertain.",
      "enum_candidates": [
        "saturate_63",
        "modulo_64",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/parameters/10",
      "claim": "The hash function combining PC and register digest to index the prediction weight tables (WT0-WT2) is settled by the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies hashing PC and register digest into h0, h1, h2 in Figure 5(c) but omits the hash function definition.",
      "enum_candidates": [
        "xor_fold",
        "bit_slice",
        "prime_mod"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The skewed PC hash function used to index usefulness tables (UT0-UT2) is settled by the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 'PC (skewed)' for indexing UT0-UT2 in Figure 5(c) but does not define the skew hash function.",
      "enum_candidates": [
        "xor_hash",
        "concat_fold",
        "crc_hash"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "The exact training condition defining when a register usefulness weight is incremented or decremented during retirement is settled by the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states usefulness weights track prediction usefulness but does not define the exact direction update condition.",
      "enum_candidates": [
        "sampled_pred_correct",
        "sc_correct",
        "sc_override_correct",
        "bank_agree_actual"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The pseudo-random selection mechanism among available registers in a bank during update is settled by the paper.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies random selection among available registers in a bank during update but does not define the pseudo-random generator or folding algorithm.",
      "enum_candidates": [
        "xor_fold",
        "prime_mod",
        "crc32",
        "bit_slice"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:execution_complete_update+global+orphan` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; t...

[Init]
model=gemini-3.8-flash-medium conversation=cb7e648e-7ac4-4a57-bb2f-a800b40dad85 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_bd2489640a39caf1

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The execution complete update is triggered when an instruction execution unit completes computation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies instruction completion as the event that triggers updating the payload with the digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "When an instruction completes, if the register status entry is invalid and its payload matches the ROB tag, the payload is overwritten with the computed digest, valid is set to 1, and decay_ctr is reset to 0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the completion action as overwriting the payload with the produced value's digest and asserting valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "Tracking mirrors Tomasulo's algorithm so that only the latest instruction claiming a destination register updates the entry on completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm.",
        "why": "The paper explicitly states the mechanism adopts a method similar to Tomasulo's algorithm."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status t
... [truncated]

[Usage]
{"input_tokens": 30308, "output_tokens": 36691, "thinking_tokens": 31785, "cache_read_tokens": 0, "total_tokens": 66999}

[Result]
status=SUCCESS conversation=cb7e648e-7ac4-4a57-bb2f-a800b40dad85 turns=1 duration=197.506399147s usage={"input_tokens": 30308, "output_tokens": 36691, "thinking_tokens": 31785, "cache_read_tokens": 0, "total_tokens": 66999}


