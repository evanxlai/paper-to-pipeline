success: True
usage: {'input_tokens': 34068, 'output_tokens': 33828, 'thinking_tokens': 31281, 'cache_read_tokens': 0, 'total_tokens': 67896}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/2/default",
      "claim": "The default 256 of max_in_flight_branches does not fit the 1-bit field max_useful_positive.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "why": "The deterministic check flags that the 1-bit max_useful_positive field cannot hold the parameter default. We clear this by widening the field in Snapshot_Buffer to 11 bits (which fits the max range of 1024) and updating its size formula."
      },
      "patch": {
        "op": "replace",
        "pointer": "/state/7",
        "value": {
          "name": "Snapshot_Buffer",
          "organization": "FIFO per in-flight branch",
          "entry_format": "array of num_banks elements: active (1 bit), reg_id (ceil(log2(num_logical_regs)) bits), digest (12 bits), max_useful_positive (11 bits)",
          "size_bits": 63488,
          "size_formula": "max_in_flight_branches * num_banks * (24 + ceil(log2(num_logical_regs)))",
          "indexing": "branch_id % max_in_flight_branches"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_id is called but undefined",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "why": "host_branch_id() is used to get the committing branch ID but is not defined in the spec. We patch by adding it as a host-provided primitive."
      },
      "patch": {
        "op": "add",
        "pointer": "/algorithms/-",
        "value": {
          "name": "host_branch_id",
          "trigger": "called by update",
          "pseudocode": "return branch_id"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_taken is called but undefined",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "why": "host_branch_taken() is used to determine the update direction but is not defined. We patch by adding it."
      },
      "patch": {
        "op": "add",
        "pointer": "/algorithms/-",
        "value": {
          "name": "host_branch_taken",
          "trigger": "called by update",
          "pseudocode": "return taken"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_sc_needs_update policy is undefined",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The spec calls host_sc_needs_update() to gate SC training, but the paper only states operation is almost the same as TAGE-SC-L, leaving the exact threshold and conditions for SC updates ambiguous."
      },
      "patch": null,
      "open_question": "When does the SC require an update? The paper states the predictor operation is almost the same as TAGE-SC-L but does not provide the exact conditions or thresholds for updating the SC. Please provide the explicit SC update policy.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "During training, the update is applied to exactly one available logical register per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The algorithm loops over each bank and applies the weight update only to the single register that was snapshotted as available for that bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The register component is divided into 8 banks",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The prose explicitly states the component uses eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "UT weights are 6 bits wide",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies the UT storage as having 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "WT weights are 6 bits wide",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the WT storage as having 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "UT0 has 8 entries",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2",
        "why": "Figure 5(c) explicitly labels UT0 as having 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10/default",
      "claim": "WT0 has 512 entries",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2",
        "why": "Figure 5(c) explicitly labels WT0 as having 512 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "UT0 requires 3120 bits of storage",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 lists the total UT storage for all three tables as 9360 bits, which is exactly three times 3120 bits, confirming the size of each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4/size_bits",
      "claim": "WT0 requires 24576 bits of storage",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies the WT storage sizes, where the 2^9 term corresponds to WT0's 512 entries per bank, totaling 24576 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "A digest is invalidated after 256 instructions are decoded",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The prose explicitly defines the 256-instruction expiration window for register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "INT register leading/trailing bit counts are encoded up to 60, and the fields are XOR-folded",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "Figure 6(a) implies XOR-folding via overlapping boxes, but does not explicitly state it. Additionally, as noted in U3, the encoding of the 7-bit count (0..64) into a 6-bit field is ambiguous."
      },
      "patch": null,
      "open_question": "How are the 6-bit leading and trailing counts for INT registers encoded given the true count can be up to 64, and are the three fields exactly XOR-folded as overlapping bit ranges?",
      "enum_candidates": [
        "xor_fold_saturate",
        "xor_fold_modulo",
        "xor_fold_sign_match"
      ]
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The bank's contribution is scaled by the usefulness of the most useful register in that bank",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "As noted in U2, Figure 5(c) does not label the wire controlling the x0/x2.5 multiplier. While analogy suggests the bank's usefulness drives it, a global static scale cannot be definitively ruled out from the figure."
      },
      "patch": null,
      "open_question": "What signal controls the x0/x2.5 multiplier for each bank's contribution? Is it driven by the usefulness of the selected register for that bank, or is it a global condition?",
      "enum_candidates": [
        "bank_usefulness",
        "global_usefulness",
        "static_scale"
      ]
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
model=gemini-3.1-pro-high conversation=8e9f8548-38d8-4210-aa11-e3dca450b69c cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_9b64a8d44159f0e1

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/2/default",
      "claim": "The default 256 of max_in_flight_branches does not fit the 1-bit field max_useful_positive.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "why": "The deterministic check flags that the 1-bit max_useful_positive field cannot hold the parameter default. We clear this by widening the field in Snapshot_Buffer to 11 bits (which fits the max range of 1024) and updating its size formula."
      },
      "patch": {
        "op": "replace",
        "pointer": "/state/7",
        "value": {
          "name": "Snapshot_Buffer",
          "organization": "FIFO per in-flight branch",
          "entry_format": "array of num_banks elements: active (1 bit), reg_id (ceil(log2(num_logical_regs)) bits), digest (12 bits), max_useful_positive (11 bits)",
          "size_bits": 63488,
          "size_formula": "max_in_flight_branches * num_banks * (24 + ceil(log2(num_logical_regs)))",
          "indexing": "branch_id % max_in_flight_branches"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_id is called but undefined",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "why": "host_branch_id() is used to get the committing branch ID but is not defined in the spec. We patch by adding it as a host-provided primitive."
      },
      "patch": {
        "op": "add",
        "pointer": "/algorithms/-",
        "value": {
          "name": "host_branch_id",
          "trigger": "called by update",
          "pseudocode": "return branch_id"
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "host_branch_taken is called but undefined",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "why": "host_branch_taken() is used to determine the update direction bu
... [truncated]

[Usage]
{"input_tokens": 34068, "output_tokens": 33828, "thinking_tokens": 31281, "cache_read_tokens": 0, "total_tokens": 67896}

[Result]
status=SUCCESS conversation=8e9f8548-38d8-4210-aa11-e3dca450b69c turns=1 duration=197.597548097s usage={"input_tokens": 34068, "output_tokens": 33828, "thinking_tokens": 31281, "cache_read_tokens": 0, "total_tokens": 67896}


