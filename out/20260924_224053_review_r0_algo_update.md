success: True
usage: {'input_tokens': 33534, 'output_tokens': 27830, 'thinking_tokens': 24954, 'cache_read_tokens': 0, 'total_tokens': 61364}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The update logic is triggered at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies that counters are updated, but does not explicitly state whether this occurs speculatively at predict time, at resolution, or at commit time. When should the update trigger?",
      "enum_candidates": [
        "commit",
        "resolution"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The confidence counter is updated only when its prediction differs from TAGE, increased if it matched the outcome, and decreased otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The confidence counter of the corresponding wormhole predictor entry is only updated when its prediction differs from the TAGE prediction. It is increased if the wormhole prediction matched the last outcome of the branch, and decreased otherwise.",
        "why": "This explicitly defines the conditional update rule for the confidence counter, which matches the pseudocode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The 5-bit prediction saturating counters are incremented on TAKEN and decremented on NOT TAKEN.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper mentions 'a table which uses saturating counters to assign confidence to this prediction' but does not specify their exact update rule (e.g., increment on taken, decrement on not-taken). How should these prediction counters be updated?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Branch context is popped from an InFlightQueue using is_empty and pop_oldest helpers.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the microarchitectural tracking of in-flight branches. The spec assumes an InFlightQueue accessed with pop_oldest() and is_empty(), which triggers undefined helper warnings since the producer is missing. How should in-flight state be managed and passed to update?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The size of the 32KB configuration's wormhole predictor is 10997 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits",
        "why": "The paper explicitly states the bit requirement for the wormhole predictor in the 32KB configuration is 10997 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_formula",
      "claim": "The size of the WPT is the sum of its entry components multiplied by the number of entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag 18 18\nConf. 4 4\nSat. counters 5 (x 16) 5 (x 256)\nRanking 3 3\nHistory vector 101 257\nHistory length 7 9",
        "why": "Table II lists all the fields that make up a single wormhole predictor entry, supporting the size formula's summation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "A WPT entry consists of a tag, confidence counter, ranking, length, history, and saturating counters.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag 18 18\nConf. 4 4\nSat. counters 5 (x 16) 5 (x 256)\nRanking 3 3\nHistory vector 101 257\nHistory length 7 9",
        "why": "Table II explicitly lists these exact fields as the components of a wormhole predictor entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The WPT is a fully associative structure.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states WPT entries are ranked and the lowest ranking is replaced when full, but does not explicitly state if the table is fully associative or set-associative.",
      "enum_candidates": [
        "fully_associative",
        "set_associative"
      ]
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The WPT is indexed by fully associative search by branch PC.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper mentions identifying the target branch via its PC (Tag field), but does not explicitly confirm a fully associative search by PC.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "In-flight branches are tracked in a FIFO queue with max_in_flight_branches entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail how speculative state or in-flight branches are tracked. A FIFO InFlightQueue is assumed for implementation.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default number of WPT entries is 7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper states the total bits (10997 for 32KB) and the bits per entry (1571 for 32KB), which divides to 7 entries, but does not state the number of entries explicitly.",
      "enum_candidates": [
        "5",
        "7"
      ]
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The default width of the confidence counter is 4 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag 18 18\nConf. 4 4\nSat. counters 5 (x 16) 5 (x 256)",
        "why": "Table II lists the 'Conf.' field as 4 bits for both predictor sizes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The default length of the local history vector is 257 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Ranking 3 3\nHistory vector 101 257\nHistory length 7 9",
        "why": "Table II lists the 'History vector' as 257 bits for the 32KB predictor configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default threshold for prioritizing the wormhole prediction is 16.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "A threshold of 16 worked well for the specific workloads.",
        "why": "The paper explicitly states the value 16 for the threshold used in the confidence equation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11/default",
      "claim": "The default maximum number of in-flight branches is 192.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not discuss the microarchitecture of the host processor or the size of its instruction window / in-flight branch queue. What should the default be?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0/expect",
      "claim": "The confidence counter saturates at 15.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag 18 18\nConf. 4 4\nSat. counters 5 (x 16) 5 (x 256)",
        "why": "The confidence counter is specified as 4 bits wide, so it naturally saturates at 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The prediction counters are 5-bit saturating counters that saturate at 15.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "abs(2 × sat value + 1) >= threshold\nWhere sat value is the value of the 5-bit saturating counter.",
        "why": "The paper states it is a 5-bit counter, and the equation's use of abs() implies a signed two's complement representation, which saturates at 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2/expect",
      "claim": "The ranking counter is 3 bits wide and saturates at 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Ranking 3 3\nHistory vector 101 257\nHistory length 7 9",
        "why": "Table II specifies the ranking counter is 3 bits wide, which saturates at 7."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3/expect",
      "claim": "Predicting with a matching pattern computes the correct index and prioritizes the True prediction when confidence and sat_value meet thresholds.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole prediction is prioritized above the base ISL-TAGE prediction as long as the confidence counter of the entry is positive and the saturating counter for the pattern matches the equation:\nabs(2 × sat value + 1) >= threshold",
        "why": "With sat_value=10, the equation evaluates to 21 >= 16. Combined with positive confidence, the prediction is prioritized and evaluates to True."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4/expect",
      "claim": "A recover action flushes entries from the InFlightQueue that are younger than the squash point.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the microarchitectural recovery mechanism for the queue on a branch misprediction.",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `wormhole`. You are reviewing unit `algo:update` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A...

[Init]
model=gemini-3.1-pro-high conversation=e56fe8e6-c7df-4180-9573-8dcc7fd31b5c cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_95193987b840ccd9

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/1/trigger",
      "claim": "The update logic is triggered at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies that counters are updated, but does not explicitly state whether this occurs speculatively at predict time, at resolution, or at commit time. When should the update trigger?",
      "enum_candidates": [
        "commit",
        "resolution"
      ]
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The confidence counter is updated only when its prediction differs from TAGE, increased if it matched the outcome, and decreased otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The confidence counter of the corresponding wormhole predictor entry is only updated when its prediction differs from the TAGE prediction. It is increased if the wormhole prediction matched the last outcome of the branch, and decreased otherwise.",
        "why": "This explicitly defines the conditional update rule for the confidence counter, which matches the pseudocode."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The 5-bit prediction saturating counters are incremented on TAKEN and decremented on NOT TAKEN.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper mentions 'a table which uses saturating counters to assign confidence to this prediction' but does not specify their exact update rule (e.g., increment on taken, decrement on not-taken). How should these prediction counters be updated?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "Branch context is popped from an InFlightQueue using is_empty and pop_oldest helpers.",
      "verdict": "UNSUPPORTED"
... [truncated]

[Usage]
{"input_tokens": 33534, "output_tokens": 27830, "thinking_tokens": 24954, "cache_read_tokens": 0, "total_tokens": 61364}

[Result]
status=SUCCESS conversation=e56fe8e6-c7df-4180-9573-8dcc7fd31b5c turns=1 duration=255.146095844s usage={"input_tokens": 33534, "output_tokens": 27830, "thinking_tokens": 24954, "cache_read_tokens": 0, "total_tokens": 61364}


