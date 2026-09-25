success: True
usage: {'input_tokens': 28616, 'output_tokens': 30887, 'thinking_tokens': 27014, 'cache_read_tokens': 0, 'total_tokens': 59503}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The update algorithm is triggered at commit time or branch execution resolution.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does training of the sR register component occur at commit time or at branch execution resolution?",
      "enum_candidates": [
        "at_commit",
        "at_resolution"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Only registers valid at prediction time are eligible for training, and when multiple registers in a bank are available, one is randomly sampled for update to require only a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly specifies that training is restricted to registers available at prediction time, with random selection within each bank to need only a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The helper function sat_update performs saturating counter updates within bounds [-32, 31].",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "function sat_update(val: int, delta: int, min_val: int, max_val: int) -> int:\n    new_val = val + delta\n    if new_val < min_val:\n        return min_val\n    if new_val > max_val:\n        return max_val\n    return new_val\n\nfunction update(pc: uint64, taken: bool, sc_train_needed: bool, selected_regs: array of 8 ints, sampled_regs: array of 8 ints):\n    if not sc_train_needed:\n        return\n\n    for bank in 0 .. 7:\n        r_train = sampled_regs[bank]\n        if r_train == -1:\n            continue\n\n        // 1. Train usefulness tables (UT) for the sampled register\n        idx0 = hash_pc(pc, 0, bank) % 8\n        idx1 = hash_pc(pc, 1, bank) % 8\n        idx2 = hash_pc(pc, 2, bank) % 8\n\n        // Get prediction with sampled register's digest\n        digest = reg_tracking_table[r_train].payload & 0x0FFF\n        h0 = hash_wt(pc, digest, 0) % 512\n        h1 = hash_wt(pc, digest, 1) % 256\n        h2 = hash_wt(pc, digest, 2) % 128\n        pred_sign = (sR_WT[bank].WT0[h0] + sR_WT[bank].WT1[h1] + sR_WT[bank].WT2[h2]) >= 0\n\n        useful_delta = (pred_sign == taken) ? +1 : -1\n        sR_UT[bank].UT0[idx0][r_train] = sat_update(sR_UT[bank].UT0[idx0][r_train], useful_delta, -32, 31)\n        sR_UT[bank].UT1[idx1][r_train] = sat_update(sR_UT[bank].UT1[idx1][r_train], useful_delta, -32, 31)\n        sR_UT[bank].UT2[idx2][r_train] = sat_update(sR_UT[bank].UT2[idx2][r_train], useful_delta, -32, 31)\n\n        // 2. Train Prediction Weight Tables (WT)\n        weight_delta = taken ? +1 : -1\n        sR_WT[bank].WT0[h0] = sat_update(sR_WT[bank].WT0[h0], weight_delta, -32, 31)\n        sR_WT[bank].WT1[h1] = sat_update(sR_WT[bank].WT1[h1], weight_delta, -32, 31)\n        sR_WT[bank].WT2[h2] = sat_update(sR_WT[bank].WT2[h2], weight_delta, -32, 31)"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "For each bank, a single register from those available at prediction time is selected and updated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 states that one register is chosen at random per bank among those available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Usefulness tables are trained with useful_delta set to +1 when the prediction sign matches the actual branch outcome and -1 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How is useful_delta computed when updating sR usefulness table (UT) weights?",
      "enum_candidates": [
        "pred_sign_eq_taken",
        "corrects_tage",
        "tage_mispred_only"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT consists of 8 banks with 3 direct-mapped sub-tables of 512, 256, and 128 entries of 6-bit counters, totaling 43,008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the prediction weight table storage as 6-bit weights across 8 banks of 2^7, 2^8, and 2^9 entries, totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT consists of 8 banks of 3 sub-tables with 8 entries each, tracking 65 logical registers using 6-bit counters, totaling 9,360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the UT storage formula as 6-bit counters across 65 registers and three 2^3-entry sub-tables, totaling 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "reg_tracking_table holds 65 entries, each comprising a 1-bit valid flag, 14-bit payload, and 8-bit decay counter, totaling 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 lists auxiliary storage for sR as 65 entries each with valid (1), payload (14), and decay_ctr (8), totaling 1,495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "num_banks has default value 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "wt0_entries has default value 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^9 (512) entries for the largest sub-table of each WT bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "wt1_entries has default value 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^8 (256) entries for the second sub-table of each WT bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt2_entries has default value 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists 2^7 (128) entries for the third sub-table of each WT bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_subtable has default value 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries for each of the three UT sub-tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "useful_multiplier has default value 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) labels the scaling multiplier on the register bank output as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "num_logical_registers has default value 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies that 65 registers are tracked across the usefulness tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation encodes leading bit count, trailing bit count, and 6 least significant bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 states that integer digests combine leading bit count, trailing bit count, and the six LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "FP64 digest extracts the sign bit and high-order exponent bits from Value[63:55].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 specifies extracting the sign bit and the most significant exponent bits to construct floating-point digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition-code flag digest replicates the 4-bit condition code three times to produce 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly describes replicating the four condition code flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Register digest entries are invalidated after 256 subsequent instructions have been decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly states that digests are invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The predictor selects the digest of the most useful available register in each bank and forwards it to the second table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 states that the digest of the most useful available register is selected and forwarded to the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Valid register digests survive pipeline squash redirects to aid branch prediction immediately after a flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 explains that completed register values available after a branch flush remain accessible to correct subsequent predictions."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A claim...

[Init]
model=gemini-3.8-flash-medium conversation=d6a4a51b-49bc-4118-b2b6-f9d622c80ce9 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e3cee5b7bf5e9944

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The update algorithm is triggered at commit time or branch execution resolution.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does training of the sR register component occur at commit time or at branch execution resolution?",
      "enum_candidates": [
        "at_commit",
        "at_resolution"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Only registers valid at prediction time are eligible for training, and when multiple registers in a bank are available, one is randomly sampled for update to require only a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 explicitly specifies that training is restricted to registers available at prediction time, with random selection within each bank to need only a single write port."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "The helper function sat_update performs saturating counter updates within bounds [-32, 31].",
      "verdict": "UNDERSPECIFIED",
      "evidence": null,
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/5/pseudocode",
        "value": "function sat_update(val: int, delta: int, min_val: int, max_val: int) -> int:\n    new_val = val + delta\n    if new_val < min_val:\n        return min_val\n    if new_val > max_val:\n        return max_val\n    return new_val\n\nfunction update(pc: uint64, taken:
... [truncated]

[Usage]
{"input_tokens": 28616, "output_tokens": 30887, "thinking_tokens": 27014, "cache_read_tokens": 0, "total_tokens": 59503}

[Result]
status=SUCCESS conversation=d6a4a51b-49bc-4118-b2b6-f9d622c80ce9 turns=1 duration=158.210898474s usage={"input_tokens": 28616, "output_tokens": 30887, "thinking_tokens": 27014, "cache_read_tokens": 0, "total_tokens": 59503}


