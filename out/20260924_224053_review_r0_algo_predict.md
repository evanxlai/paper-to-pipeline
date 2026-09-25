success: True
usage: {'input_tokens': 34091, 'output_tokens': 28365, 'thinking_tokens': 26144, 'cache_read_tokens': 0, 'total_tokens': 62456}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The prediction history pattern is formed by extracting specific local history bits for 4KB and 32KB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These bits correspond to locations 0 (most recent), LPT_TOTAL, LPT_TOTAL - 1 and LPT_TOTAL - 2 in the local history vector.",
        "why": "The paper explicitly defines these indices for forming the pattern in the multidimensional history."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The wormhole prediction triggers if the confidence counter is positive and the absolute value of 2*sat_value+1 meets the threshold.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "abs(2 × sat value + 1) >= threshold",
        "why": "The algorithm matches the exact threshold equation provided by the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The predict algorithm relies on 'InFlightQueue.size' and 'push(...)' for speculative state tracking.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The pseudocode uses 'InFlightQueue.push' and 'InFlightQueue.size', but the paper does not define speculative queue management. Are these host-provided primitives, and what stage produces 'size'?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The WPT requires 10997 bits of storage for the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits",
        "why": "The size formula matches the 10997 bit overhead for the 32KB configuration stated in the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The InFlightQueue tracks speculative branches with 4032 bits of storage.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail speculative update structures like InFlightQueue. How should speculative branches be tracked and what is the storage overhead?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The WPT defaults to 7 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits",
        "why": "The 10997 bits overhead divided by the mathematically derived 1571 bits per 32KB entry yields exactly 7 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The tag width is 18 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Table II: Components of each wormhole predictor entry",
        "why": "Table II text confirms the tag field is 18 bits for both configurations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The confidence counter is 4 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a 4-bit confidence counter",
        "why": "The paper explicitly states the confidence counter is 4 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The length counter is 9 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "and a 7- or 9-bit counter to store iteration count",
        "why": "The paper specifies a 9-bit counter for iteration count in the 32KB configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The local history vector is 257 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a 101- or 257-bit vector to store the local history",
        "why": "The paper specifies a 257-bit vector for local history in the 32KB configuration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The prediction threshold is 16.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "A threshold of 16 worked well for the specific workloads.",
        "why": "The paper explicitly defines the default threshold as 16."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The predictor defaults to the 32KB indexing configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We consider two different configurations: 4KB and 32KB.",
        "why": "The 32KB configuration is one of the two explicitly modeled predictor variants in the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "The maximum number of in-flight branches defaults to 192.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not mention the maximum number of in-flight branches. What should be the queue capacity for speculative updates?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "The confidence counter saturates at 15.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "a 4-bit confidence counter",
        "why": "A 4-bit counter inherently saturates at a maximum value of 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "The saturating prediction counters saturate at 15 without wrapping.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "5-bit saturating counters",
        "why": "A 5-bit signed saturating counter has a maximum positive value of 15."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The ranking counter increments when deemed problematic and saturates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the statistical corrector deems a branch to be problematic, its entry moves up one spot in the ranking",
        "why": "The test verifies the ranking increments correctly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "The multidimensional index computation correctly yields 15 for the given history.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These bits correspond to locations 0 (most recent), LPT_TOTAL, LPT_TOTAL - 1 and LPT_TOTAL - 2 in the local history vector.",
        "why": "The test applies the exact bit extraction and indexing math defined by the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The recovery queue flush behavior removes younger entries.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail speculative structures like InFlightQueue. How are pipeline flushes and branch recovery managed?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `wormhole`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. ...

[Init]
model=gemini-3.1-pro-high conversation=fb9d41be-9025-4565-a98d-4c9a0a85d3db cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_95193987b840ccd9

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The prediction history pattern is formed by extracting specific local history bits for 4KB and 32KB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "These bits correspond to locations 0 (most recent), LPT_TOTAL, LPT_TOTAL - 1 and LPT_TOTAL - 2 in the local history vector.",
        "why": "The paper explicitly defines these indices for forming the pattern in the multidimensional history."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The wormhole prediction triggers if the confidence counter is positive and the absolute value of 2*sat_value+1 meets the threshold.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "abs(2 × sat value + 1) >= threshold",
        "why": "The algorithm matches the exact threshold equation provided by the paper."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The predict algorithm relies on 'InFlightQueue.size' and 'push(...)' for speculative state tracking.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The pseudocode uses 'InFlightQueue.push' and 'InFlightQueue.size', but the paper does not define speculative queue management. Are these host-provided primitives, and what stage produces 'size'?",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The WPT requires 10997 bits of storage for the 32KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits",
        "why": "The size formula matches the 10997 bit overhead for the 32KB configuration stated in the paper."
      },
      "patch": null,
      "open_qu
... [truncated]

[Usage]
{"input_tokens": 34091, "output_tokens": 28365, "thinking_tokens": 26144, "cache_read_tokens": 0, "total_tokens": 62456}

[Result]
status=SUCCESS conversation=fb9d41be-9025-4565-a98d-4c9a0a85d3db turns=1 duration=171.779136243s usage={"input_tokens": 34091, "output_tokens": 28365, "thinking_tokens": 26144, "cache_read_tokens": 0, "total_tokens": 62456}


