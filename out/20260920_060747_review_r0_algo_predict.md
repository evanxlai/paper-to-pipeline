success: True
usage: {'input_tokens': 19801, 'output_tokens': 24506, 'thinking_tokens': 21756, 'cache_read_tokens': 8145, 'total_tokens': 44307}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The pseudocode looks up usefulness in a single UT table and uses a single hash function for all three WT tables.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "The figure explicitly defines three separate usefulness tables whose outputs are summed, and three separate hashes (h0, h1, h2) for the weight tables."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/4/pseudocode",
        "value": "sR_sum = 0\nut_row = UT0[skew(PC)] + UT1[skew(PC)] + UT2[skew(PC)]\nfor bank in 0..7:\n  valid_regs = {r | r % 8 == bank and RegisterDigestTable[r].valid}\n  if valid_regs is empty: continue\n  best_r = argmax_{r in valid_regs} ut_row[r]\n  if ut_row[best_r] > 0:\n    digest = RegisterDigestTable[best_r].payload[11:0]\n    bank_pred = WT0_bank[h0(PC, digest)] + WT1_bank[h1(PC, digest)] + WT2_bank[h2(PC, digest)]\n    sR_sum += bank_pred * sR_multiplier\nreturn sR_sum"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The algorithm uses a 'skew' function to transform the PC for the UT index.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "The paper indicates the PC is skewed for UT lookups but does not provide the mathematical definition for the skew function."
      },
      "patch": null,
      "open_question": "What is the mathematical definition of the skew function applied to the PC for the UT index?",
      "enum_candidates": [
        "A simple XOR fold of the PC bits",
        "No skew (use raw PC bits)",
        "The skewed-associative hash used in Seznec's TAGE"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "A bank's prediction is skipped if the chosen register's usefulness is not strictly positive (ut_row[best_r] > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "The paper shows a choice between multiplying the bank's output by 0 or 2.5, but does not explicitly state the condition for doing so."
      },
      "patch": null,
      "open_question": "What is the exact condition for selecting the x0 multiplier instead of x2.5 for a bank's output?",
      "enum_candidates": [
        "When the most useful register's UT weight is <= 0",
        "When the most useful register's UT weight is < 0",
        "When there are no valid registers available in the bank"
      ]
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The Register Digest Table is organized as a flat array of 65 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a dedicated table that contains one entry per logical register",
        "why": "The paper explicitly confirms there is one entry per logical register (totaling 65)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "The Register Digest Table entry consists of valid (1), payload (14), and decay_ctr (8).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 specifies these exact fields and bit widths for the register state."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "The sR Prediction Weight Table (WT) consists of 8 banks, each containing 3 tables of 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT storage using 8 banks of tables sized 128, 256, and 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The sR Usefulness Weight Table (UT) consists of 3 tables of 8 entries each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the UT storage using three tables of 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The sR_multiplier defaults to 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "Figure 5(c) indicates a multiplier of 2.5 is applied to the output of each bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The sR_multiplier has a valid range of [0.0, 4.0].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "The paper specifies a fixed multiplier of 2.5 and does not establish a valid range for tuning."
      },
      "patch": null,
      "open_question": "What is the allowable tuning range for the sR_multiplier parameter?",
      "enum_candidates": [
        "[0.0, 4.0]",
        "[1.0, 3.0]",
        "[2.5, 2.5] (fixed)"
      ]
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The digest_width defaults to 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value",
        "why": "The text explicitly states the digest width is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/range",
      "claim": "The digest_width has a valid tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value",
        "why": "The paper specifies a 12-bit digest but does not mention [8, 16] as a tuning range."
      },
      "patch": null,
      "open_question": "What is the valid tuning range for the digest_width parameter?",
      "enum_candidates": [
        "[8, 16]",
        "[12, 12] (fixed)",
        "[10, 14]"
      ]
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The exact 12-bit digest value can be computed deterministically for an INT register.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the digest encodes the count of leading zeros (or ones)",
        "why": "The paper does not specify how the 6-bit count fields handle counts up to 64, or how counting ones vs zeros is distinguished, making the exact output ambiguous."
      },
      "patch": null,
      "open_question": "How are the leading and trailing counts encoded into 6 bits, especially for counts >= 64 or to distinguish counting ones vs zeros?",
      "enum_candidates": [
        "Modulo 64 (discards the 64th bit)",
        "Saturate at 63",
        "Count only bits matching the sign bit (max 63)"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "A register's digest is invalidated after 256 instructions are decoded without updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The paper directly specifies the 256-instruction invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The predictor uses the digest of the register with the highest UT weight for the WT lookup.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available",
        "why": "The paper states that the digest of the most useful register is forwarded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "The bank's WT output is multiplied by 0 when the selected best register has a negative UT weight.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "multiplier stage labelled \"x0 or x2.5\"",
        "why": "The paper shows a choice between multiplying the bank's output by 0 or 2.5, but does not explicitly state that a negative UT weight triggers the x0 condition."
      },
      "patch": null,
      "open_question": "What is the exact condition for selecting the x0 multiplier instead of x2.5 for a bank's output?",
      "enum_candidates": [
        "When the most useful register's UT weight is <= 0",
        "When the most useful register's UT weight is < 0",
        "When there are no valid registers available in the bank"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.1-pro-high conversation=35a36999-0b89-47bb-bab1-4f015806ee7a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_2cbf45e4f50cc3ef

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The pseudocode looks up usefulness in a single UT table and uses a single hash function for all three WT tables.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "The figure explicitly defines three separate usefulness tables whose outputs are summed, and three separate hashes (h0, h1, h2) for the weight tables."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/4/pseudocode",
        "value": "sR_sum = 0\nut_row = UT0[skew(PC)] + UT1[skew(PC)] + UT2[skew(PC)]\nfor bank in 0..7:\n  valid_regs = {r | r % 8 == bank and RegisterDigestTable[r].valid}\n  if valid_regs is empty: continue\n  best_r = argmax_{r in valid_regs} ut_row[r]\n  if ut_row[best_r] > 0:\n    digest = RegisterDigestTable[best_r].payload[11:0]\n    bank_pred = WT0_bank[h0(PC, digest)] + WT1_bank[h1(PC, digest)] + WT2_bank[h2(PC, digest)]\n    sR_sum += bank_pred * sR_multiplier\nreturn sR_sum"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "The algorithm uses a 'skew' function to transform the PC for the UT index.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "The paper indicates the PC is skewed for UT lookups but does not provide the mathematical definition for the skew function."
      },
      "patch": null,
      "open_question": "What is the mathematical definition of the skew function applied to the PC for the UT index?",
      "enum_candidates": [
        "A simple XOR fold of the PC bits",
        "No skew (use raw PC bits)",
        "The skewed-associative hash used in Seznec's TAGE"
      ]
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "A bank's prediction is skippe
... [truncated]

[Usage]
{"input_tokens": 19801, "output_tokens": 24506, "thinking_tokens": 21756, "cache_read_tokens": 8145, "total_tokens": 44307}

[Result]
status=SUCCESS conversation=35a36999-0b89-47bb-bab1-4f015806ee7a turns=1 duration=155.597410732s usage={"input_tokens": 19801, "output_tokens": 24506, "thinking_tokens": 21756, "cache_read_tokens": 8145, "total_tokens": 44307}


