success: True
usage: {'input_tokens': 32700, 'output_tokens': 18909, 'thinking_tokens': 16750, 'cache_read_tokens': 0, 'total_tokens': 51609}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/6",
      "claim": "The parameter num_counters has a default value of 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry has a table with 16 or 256 5-bit saturating counters to predict the different patterns",
        "why": "The paper explicitly states the table contains 256 counters for the larger 32KB configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The parameter counter_bits has a default value of 5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry has a table with 16 or 256 5-bit saturating counters to predict the different patterns",
        "why": "The paper explicitly describes the counters as being 5-bit saturating counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Wormhole targets branches in nested loops with cross-iteration correlation by folding linear history into a multidimensional matrix.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These are branches with the following two attributes: 1) they are enclosed within nested loops, and 2) they exhibit correlation across iterations of the outer loops. Folding the branch history and interpreting it as a multidimensional piece of information, exposes these cross-iteration correlations",
        "why": "The abstract confirms the predictor targets nested loop branches and folds history into multidimensional information."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The paper title is 'Wormhole: Wisely Predicting Multidimensional Branches'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Wormhole: Wisely Predicting Multidimensional Branches",
        "why": "This is the verbatim title of the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/0",
      "claim": "The host provides the branch_PC to identify the target branch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag: Identifies the target branch via its PC.",
        "why": "The paper explicitly states the predictor entry uses the PC to identify the branch."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/1",
      "claim": "The baseline loop predictor provides the total expected number of iterations (LPT_TOTAL).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Thus, at any point in time, LPT_TOTAL stores the total expected number of iterations for the current innermost loop.",
        "why": "The paper states the loop predictor tracks and provides this total count."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/2",
      "claim": "The baseline statistical corrector provides a signal indicating the branch is frequently mispredicted.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the statistical corrector deems a branch to be problematic, its entry moves up one spot in the ranking",
        "why": "The paper explains that the statistical corrector identifies problematic branches to allocate in Wormhole."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/3",
      "claim": "The base TAGE predictor provides its direction prediction to the wormhole predictor.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The confidence counter of the corresponding wormhole predictor entry is only updated when its prediction differs from the TAGE prediction.",
        "why": "Wormhole needs the base TAGE prediction to determine if its own prediction differs to adjust confidence."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/4",
      "claim": "The resolved branch outcome is provided to update the predictor.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "It is increased if the wormhole prediction matched the last outcome of the branch, and decreased otherwise.",
        "why": "Wormhole requires the actual branch outcome to update its confidence counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces/5",
      "claim": "The host provides a current_age identifier for branches pushed to the InFlightQueue.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not detail an InFlightQueue or instruction age tracking; this is an implementation necessity for speculative updates."
      },
      "patch": null,
      "open_question": "What granularity of instruction age identifier should be used for tracking in-flight speculative state in Wormhole?",
      "enum_candidates": [
        "sequence_number",
        "rob_index",
        "local_counter"
      ]
    },
    {
      "pointer": "/host_interfaces/6",
      "claim": "The host provides a squash_point identifier to flush younger entries on a squash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper omits discussion of speculative state recovery and squash tracking mechanisms."
      },
      "patch": null,
      "open_question": "How does the host signal the boundary for flushing speculative state on a branch squash?",
      "enum_candidates": [
        "squash_age",
        "rob_tail",
        "flush_all"
      ]
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The storage budget donor must state the exact size of the cut to balance the budget deficit.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The deterministic finding flags that total_storage_bits (15029) exceeds the budget, and budget_donors fails to state the exact size of the cut required to balance it."
      },
      "patch": {
        "op": "replace",
        "pointer": "/resource_accounting",
        "value": {
          "total_storage_bits": 15029,
          "storage_breakdown": "WPT: 7 entries * 1571 bits = 10997 bits. InFlightQueue: 192 entries * 21 bits = 4032 bits.",
          "logic_cost_notes": "The paper states 10997 bits for the 32KB configuration. Our total is 15029 bits; we are over the paper's figure by 4032 bits because the paper omitted the in-flight metadata queue (InFlightQueue) required to pass the lookup index and prediction to the commit stage, which is necessary to avoid recomputing indexes with shifted history.",
          "budget_donors": "TAGE components or the statistical corrector can shrink by 4032 bits to pay for this at iso-storage."
        }
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/-",
      "claim": "The spec requires a recovery algorithm to unwind speculative state on a squash.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The deterministic finding notes the spec holds speculative state ('branch_tag') but no algorithm unwinds it, causing the table to drift on squashes."
      },
      "patch": {
        "op": "add",
        "pointer": "/algorithms/-",
        "value": {
          "name": "squash_recovery",
          "trigger": "squash",
          "pseudocode": "for entry in InFlightQueue:\n  if entry.current_age >= squash_point:\n    discard entry\n  else:\n    retain entry"
        }
      },
      "open_question": "Does Wormhole restore the local history vector on a squash by copying from the youngest surviving InFlightQueue entry, or does it simply flush younger entries and leave the WPT unchanged?",
      "enum_candidates": [
        "flush_only",
        "restore_history"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `wormhole`. You are reviewing unit `orphan+global` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper....

[Init]
model=gemini-3.1-pro-high conversation=98edcc8b-d2ab-42ee-861a-9cf4d9842b2d cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_95193987b840ccd9

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/6",
      "claim": "The parameter num_counters has a default value of 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry has a table with 16 or 256 5-bit saturating counters to predict the different patterns",
        "why": "The paper explicitly states the table contains 256 counters for the larger 32KB configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The parameter counter_bits has a default value of 5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry has a table with 16 or 256 5-bit saturating counters to predict the different patterns",
        "why": "The paper explicitly describes the counters as being 5-bit saturating counters."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Wormhole targets branches in nested loops with cross-iteration correlation by folding linear history into a multidimensional matrix.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These are branches with the following two attributes: 1) they are enclosed within nested loops, and 2) they exhibit correlation across iterations of the outer loops. Folding the branch history and interpreting it as a multidimensional piece of information, exposes these cross-iteration correlations",
        "why": "The abstract confirms the predictor targets nested loop branches and folds history into multidimensional information."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The paper title is 'Wormhole: Wisely Predicting Multidimensional Branches'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Wormhole: Wisely Predicting Mul
... [truncated]

[Usage]
{"input_tokens": 32700, "output_tokens": 18909, "thinking_tokens": 16750, "cache_read_tokens": 0, "total_tokens": 51609}

[Result]
status=SUCCESS conversation=98edcc8b-d2ab-42ee-861a-9cf4d9842b2d turns=1 duration=191.883435669s usage={"input_tokens": 32700, "output_tokens": 18909, "thinking_tokens": 16750, "cache_read_tokens": 0, "total_tokens": 51609}


