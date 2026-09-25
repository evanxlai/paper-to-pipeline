success: True
usage: {'input_tokens': 32533, 'output_tokens': 24161, 'thinking_tokens': 20728, 'cache_read_tokens': 0, 'total_tokens': 56694}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The bank's weight table sum is scaled by 2.5 only if the maximum usefulness in that bank is greater than 0 (max_u > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) shows this multiplier, but as note U2 indicates, the control wire for selecting x0 vs x2.5 is not labelled, making the max_u > 0 condition an inference."
      },
      "patch": null,
      "open_question": "What condition selects the x2.5 multiplier for a bank? The diagram shows 'x0 or x2.5' but does not specify the control signal.",
      "enum_candidates": [
        "bank_useful_positive",
        "always_enabled"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Logical registers are distributed across banks by modulo (stride-8) interleaving, checked as (r % num_banks) == b.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "R0  R8  R16  ...  R64",
        "why": "Figure 5(c) lists these registers for bank 0, implying a stride, but this layout detail is marked as an INFERRED reading (I10)."
      },
      "patch": null,
      "open_question": "How are the 65 logical registers mapped to the 8 banks? The figure implies stride-8 interleaving (r % 8 == b), but this is inferred.",
      "enum_candidates": [
        "stride_interleaved",
        "contiguous_blocks"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The component picks the digest of the most useful register among the available valid registers to forward to the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "This explicitly states the core logic of selecting the best register's digest for WT lookup."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT consists of 8 banks, with 3 tables per bank, entries of wt_bits, and total size 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT structure for sR as 8 banks of three tables (sizes 128, 256, 512) with 6-bit entries, totaling exactly 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT has total size 9360 bits, structured as 8 banks with 3 tables of vectors per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 gives the exact dimensions for the sR usefulness table UT, matching 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "sR_InFlightState requires 16640 bits to store a bitmask of valid registers for 256 in-flight branches.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper requires tracking which registers were valid at prediction time, but does not explicitly budget the sizing (256 branches) in Table 3."
      },
      "patch": null,
      "open_question": "How many in-flight branches should the predictor track state for, given it is not explicitly budgeted in the storage tables?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The default number of banks is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks",
        "why": "The prose confirms the register component is organized into 8 banks."
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
        "why": "Table 3 uses 65 as the number of logical registers for sizing the usefulness table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default number of entries for wt0 is 512.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0",
        "why": "Figure 5(c) explicitly labels WT0 with 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default number of entries for wt1 is 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "256 ent. WT1",
        "why": "Figure 5(c) explicitly labels WT1 with 256 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default number of entries for wt2 is 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "128 ent. WT2",
        "why": "Figure 5(c) explicitly labels WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The default number of entries for ut0 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0",
        "why": "Figure 5(c) explicitly labels UT0 with 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default number of entries for ut1 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT1",
        "why": "Figure 5(c) explicitly labels UT1 with 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The default number of entries for ut2 is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "8 ent. UT2",
        "why": "Figure 5(c) explicitly labels UT2 with 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The default weight width (wt_bits) is 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The default ROB index size is 14 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "payload (14)",
        "why": "Table 3 sizes the payload field (which holds the ROB tag) at 14 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The default number of inflight branches is 256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "an ROB capable of storing over 500 instructions.",
        "why": "The paper mentions overall ROB sizes over 500 but does not specify a specific maximum number of in-flight branches for the predictor."
      },
      "patch": null,
      "open_question": "What is the maximum number of in-flight branches the predictor tracks, given the paper only states overall ROB sizes?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "The default useful_multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) shows a multiplier stage of 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The register's valid bit is cleared after 255 subsequent instructions are decoded.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded",
        "why": "The text explicitly states invalidation happens after 256 decoded instructions, not 255."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/0",
        "value": {
          "name": "decay_counter_walks_down",
          "given": "An instruction completes and writes a register via write_register_digest, setting sR_RegTable decay_ctr to 255. Then 256 subsequent instructions are decoded via allocate_register.",
          "expect": "The decay_ctr wraps around (completing 256 steps), and the register's valid bit in sR_RegTable is cleared to 0."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The digest generator uses count_leading_zeros(0) and count_trailing_zeros(4) for the INT value 0xFFFFFFFFFFFFFFF0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "the count of leading zeros (or ones)",
        "why": "Note U3 identifies that the paper does not specify how the zero/one case is distinguished for the leading/trailing counts."
      },
      "patch": null,
      "open_question": "How does the digest generator distinguish whether to count leading zeros or leading ones, as noted in U3?",
      "enum_candidates": [
        "zeros",
        "ones",
        "sign_bits"
      ]
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "predict evaluates the bank using the digest of the valid register with the highest summed usefulness weight.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "This accurately reflects the core register selection logic stated in the text."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "If multiple registers were valid in a bank, only one randomly chosen register has its corresponding sR_UT and sR_WT entries modified.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The text directly confirms that one register is randomly selected for the update when multiple are available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A pipeline squash (recovery) clears a pending register's payload back to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly defers the recovery mechanism for the register table to future work, making the clear-to-0 behavior unsupported."
      },
      "patch": null,
      "open_question": "How should the pending payload in the register table be handled upon a pipeline squash, given the paper defers recovery to future work?",
      "enum_candidates": null
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
model=gemini-3.1-pro-high conversation=325d36bf-a954-49b0-b2f9-5cc376166db5 cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_af48d42af16dc024

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The bank's weight table sum is scaled by 2.5 only if the maximum usefulness in that bank is greater than 0 (max_u > 0).",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "x0 or x2.5",
        "why": "Figure 5(c) shows this multiplier, but as note U2 indicates, the control wire for selecting x0 vs x2.5 is not labelled, making the max_u > 0 condition an inference."
      },
      "patch": null,
      "open_question": "What condition selects the x2.5 multiplier for a bank? The diagram shows 'x0 or x2.5' but does not specify the control signal.",
      "enum_candidates": [
        "bank_useful_positive",
        "always_enabled"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Logical registers are distributed across banks by modulo (stride-8) interleaving, checked as (r % num_banks) == b.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "R0  R8  R16  ...  R64",
        "why": "Figure 5(c) lists these registers for bank 0, implying a stride, but this layout detail is marked as an INFERRED reading (I10)."
      },
      "patch": null,
      "open_question": "How are the 65 logical registers mapped to the 8 banks? The figure implies stride-8 interleaving (r % 8 == b), but this is inferred.",
      "enum_candidates": [
        "stride_interleaved",
        "contiguous_blocks"
      ]
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The component picks the digest of the most useful register among the available valid registers to forward to the weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "This explicitly states the core logic of selecting the best register's digest for WT lookup."
      },
      "patch": null,
 
... [truncated]

[Usage]
{"input_tokens": 32533, "output_tokens": 24161, "thinking_tokens": 20728, "cache_read_tokens": 0, "total_tokens": 56694}

[Result]
status=SUCCESS conversation=325d36bf-a954-49b0-b2f9-5cc376166db5 turns=1 duration=294.755155131s usage={"input_tokens": 32533, "output_tokens": 24161, "thinking_tokens": 20728, "cache_read_tokens": 0, "total_tokens": 56694}


