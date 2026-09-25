success: True
usage: {'input_tokens': 33138, 'output_tokens': 22716, 'thinking_tokens': 20967, 'cache_read_tokens': 0, 'total_tokens': 55854}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The recovery algorithm unwinds the InFlightQueue by discarding entries newer than the squash point.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "How exactly should pipeline squash and recovery of the InFlightQueue be implemented? The paper abstracts this away. The current pseudocode uses undefined helpers (elements, remove, reversed) and reads an unproduced property (InFlightQueue.elements) which cannot be safely patched without inventing a queue implementation.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total size of the WPT is 10997 bits for the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits, yielding an overhead of 3.29% and 4.4%, for the 4KB and 32KB configurations.",
        "why": "The paper explicitly states the total bit requirement for the WPT in the 32KB configuration is 10997 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "The InFlightQueue tracks valid, wpt_idx, counter_idx, wormhole_pred, and instruction_age for each in-flight branch.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "What fields should the InFlightQueue store? The paper abstracts the branch predictor's in-flight queue entirely.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The WPT has a default of 7 entries in the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits, yielding an overhead of 3.29% and 4.4%, for the 4KB and 32KB configurations.",
        "why": "Table II gives an entry size of 1571 bits (18+4+1280+3+257+9) for the 32KB config; 10997 total bits divided by 1571 bits per entry mathematically yields exactly 7 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The history vector length is 257 bits for the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "History vector\n101\n257",
        "why": "Table II directly specifies 257 bits for the history vector in the 32KB predictor configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11/default",
      "claim": "The maximum number of in-flight branches defaults to 192.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "What should the maximum number of in-flight branches default to? The paper does not specify the capacity of the queue.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The 4-bit confidence counter increments on correct unique predictions and saturates at 15.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The confidence counter of the corresponding wormhole predictor entry is only updated when its prediction differs from the TAGE prediction. It is increased if the wormhole prediction matched the last outcome of the branch, and decreased otherwise.",
        "why": "The paper defines the increment condition, and Table II specifies a 4-bit size, which natively saturates at 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The saturating prediction counter increments on taken branches and saturates at 15.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "abs(2 × sat value + 1) >= threshold\nWhere sat value is the value of the 5-bit saturating counter.",
        "why": "The absolute value equation implies a signed 5-bit counter, which has a maximum positive value of 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The 3-bit ranking counter increments on reallocation and saturates at 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the statistical corrector deems a branch to be problematic, its entry moves up one spot in the ranking and the statistical corrector continues to identify it as problematic.",
        "why": "The paper states the ranking moves up, and Table II specifies a 3-bit ranking counter, meaning it saturates at 7."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "For the 4KB config, the predictor indexes with bits 0, LPT_TOTAL, LPT_TOTAL-1, and LPT_TOTAL-2, returning a prediction if confidence is positive and the threshold is met.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These bits correspond to locations 0 (most recent), LPT OT AL , LPT OT AL −1 and LPT OT AL − 2 in the local history vector.",
        "why": "The expectation computes index 15 accurately from these four bits (at length 10) and correctly evaluates the threshold and confidence to return True."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "The recovery algorithm flushes entries from the InFlightQueue that are newer than the squash point.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "How should branch mispredict squashes clear the in-flight queue? The paper abstracts the queue flush rules.",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `wormhole`. You are reviewing unit `algo:recover` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. ...

[Init]
model=gemini-3.1-pro-high conversation=2bc789cd-90c6-4dd1-b3c6-b1ac49c9945e cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_95193987b840ccd9

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The recovery algorithm unwinds the InFlightQueue by discarding entries newer than the squash point.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "How exactly should pipeline squash and recovery of the InFlightQueue be implemented? The paper abstracts this away. The current pseudocode uses undefined helpers (elements, remove, reversed) and reads an unproduced property (InFlightQueue.elements) which cannot be safely patched without inventing a queue implementation.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total size of the WPT is 10997 bits for the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits, yielding an overhead of 3.29% and 4.4%, for the 4KB and 32KB configurations.",
        "why": "The paper explicitly states the total bit requirement for the WPT in the 32KB configuration is 10997 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "The InFlightQueue tracks valid, wpt_idx, counter_idx, wormhole_pred, and instruction_age for each in-flight branch.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": null
      },
      "patch": null,
      "open_question": "What fields should the InFlightQueue store? The paper abstracts the branch predictor's in-flight queue entirely.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The WPT has a default of 7 entries in the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits, yielding an o
... [truncated]

[Usage]
{"input_tokens": 33138, "output_tokens": 22716, "thinking_tokens": 20967, "cache_read_tokens": 0, "total_tokens": 55854}

[Result]
status=SUCCESS conversation=2bc789cd-90c6-4dd1-b3c6-b1ac49c9945e turns=1 duration=322.447663801s usage={"input_tokens": 33138, "output_tokens": 22716, "thinking_tokens": 20967, "cache_read_tokens": 0, "total_tokens": 55854}


