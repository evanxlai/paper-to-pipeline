success: True
usage: {'input_tokens': 33573, 'output_tokens': 25962, 'thinking_tokens': 23487, 'cache_read_tokens': 0, 'total_tokens': 59535}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The update algorithm reads context fields ('entry.length', 'meta.old_history', 'meta.tage_pred', 'meta.wpt_pred') unconditionally.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The spec states these fields are conditionally written by the producer stages but reads them unconditionally in 'update', creating a contradiction when paths are skipped (as flagged by deterministic findings)."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "meta_idx = rob_index % max_in_flight_branches\nmeta = WPT_InFlight_Meta[meta_idx]\nif not meta.valid or meta.entry_idx == -1:\n    return\n\nentry = WPT[meta.entry_idx]\n\nif meta.wpt_pred is not None and meta.tage_pred is not None:\n    if meta.wpt_pred != meta.tage_pred:\n        if meta.wpt_pred == outcome:\n            entry.conf = min(entry.conf + 1, (1 << conf_bits) - 1)\n        else:\n            entry.conf = max(entry.conf - 1, 0)\n\nif meta.old_history is not None and entry.length is not None:\n    old_hist = meta.old_history\n    h0 = old_hist & 1\n    hl = (old_hist >> min(entry.length, history_bits - 1)) & 1\n    hl1 = (old_hist >> min(max(entry.length - 1, 0), history_bits - 1)) & 1\n    hl2 = (old_hist >> min(max(entry.length - 2, 0), history_bits - 1)) & 1\n    idx = (h0 << 3) | (hl << 2) | (hl1 << 1) | hl2\n\n    sat_value = entry.counters[idx]\n    if outcome == 1:\n        entry.counters[idx] = min(sat_value + 1, (1 << (counter_bits - 1)) - 1)\n    else:\n        entry.counters[idx] = max(sat_value - 1, -(1 << (counter_bits - 1)))\n\nmeta.valid = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The saturating counter index is formed using bits 0, LPT_TOTAL, LPT_TOTAL - 1, and LPT_TOTAL - 2 from the local history vector.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "locations 0 (most recent), LPT OT AL , LPT OT AL −1 and LPT OT AL − 2",
        "why": "The index calculation precisely extracts these four bit positions using the entry.length (LPT_TOTAL) to form a 4-bit index."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The confidence counter is updated only when the WPT prediction differs from the TAGE prediction, incrementing on a match with outcome and decrementing otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "only updated when its prediction differs from the TAGE prediction. It is increased if the wormhole prediction matched the last outcome of the branch, and decreased otherwise.",
        "why": "The pseudocode's conditional updates to entry.conf perfectly match these stated rules."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The update algorithm uses the actual branch outcome.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper implies the use of the actual branch outcome, but does not explicitly detail the pipeline handshake that supplies it to the predictor."
      },
      "patch": null,
      "open_question": "How is the actual branch outcome delivered to the update algorithm, given it is not explicitly produced by any state or step in the spec?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The confidence counter is 4 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Table II: Components of each wormhole predictor entry (all sizes in bits).",
        "why": "Table II explicitly lists the Confidence counter as 4 bits for both predictor sizes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The local history vector is 101 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Table II: Components of each wormhole predictor entry (all sizes in bits).",
        "why": "Table II specifies the local history vector is 101 bits for the 4KB configuration, which matches the spec's default."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5",
      "claim": "The expected number of iterations (History length) is 7 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Table II: Components of each wormhole predictor entry (all sizes in bits).",
        "why": "Table II specifies the History length field is 7 bits for the 4KB configuration, matching the spec default."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The predictor tracks up to 128 maximum in-flight branches for metadata.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not state the size of the speculative in-flight branch queue; this is an implementation parameter."
      },
      "patch": null,
      "open_question": "The paper does not specify the number of in-flight branches to track for speculative updates. The range for max_in_flight_branches needs to be corrected as it is not settled by the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The Wormhole Prediction Table (WPT) allocates a total of 1065 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Table III: Storage of the different predictors.",
        "why": "Table III specifies the storage overhead for the 4KB configuration as 134 bytes (1072 bits), which accommodates the 1065 bits required for 5 entries computed by the sizing formula."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "A circular queue tracking in-flight branch metadata is required.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not detail the speculative in-flight update queue (WPT_InFlight_Meta) or its sizing."
      },
      "patch": null,
      "open_question": "The paper does not detail the speculative in-flight update queue (WPT_InFlight_Meta) or its sizing, which is required for implementation.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "When confidence is 0, the external prediction returns None.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole prediction is prioritized above the base ISL-TAGE prediction as long as the confidence counter of the entry is positive",
        "why": "Confirms that when confidence is 0, the prediction is not prioritized and correctly yields None."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The test expectation verifies the saturating counter and confidence updates over a sequence without explicitly stating the outcome.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": null,
        "why": "The test expectation uses vague language ('correct', 'correctly') that cannot be automatically checked."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1/expect",
        "value": "Because history remains 0, index 0 is used every time. The saturating counter[0] decrements from 0 to -16, saturating at -16. The internal WPT prediction is 0 (since counter < 0). TAGE is 1. WPT prediction matches the outcome (0), so conf increments from 0 to 15, saturating at 15. The WPT_InFlight_Meta queue entries are populated by predict with valid=1 and cleared by update by setting valid=0."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "The predictor recovers speculative history from WPT_InFlight_Meta upon a pipeline squash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": null,
        "why": "The paper does not detail the speculative history recovery mechanism on a pipeline squash."
      },
      "patch": null,
      "open_question": "The paper does not detail the speculative history recovery mechanism on a pipeline squash.",
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
model=gemini-3.1-pro-high conversation=b7b8f4fa-c5cd-4234-95d8-bac7db5c1dee cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_9e5df7c73518ca18

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The update algorithm reads context fields ('entry.length', 'meta.old_history', 'meta.tage_pred', 'meta.wpt_pred') unconditionally.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "quote": null,
        "why": "The spec states these fields are conditionally written by the producer stages but reads them unconditionally in 'update', creating a contradiction when paths are skipped (as flagged by deterministic findings)."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/2/pseudocode",
        "value": "meta_idx = rob_index % max_in_flight_branches\nmeta = WPT_InFlight_Meta[meta_idx]\nif not meta.valid or meta.entry_idx == -1:\n    return\n\nentry = WPT[meta.entry_idx]\n\nif meta.wpt_pred is not None and meta.tage_pred is not None:\n    if meta.wpt_pred != meta.tage_pred:\n        if meta.wpt_pred == outcome:\n            entry.conf = min(entry.conf + 1, (1 << conf_bits) - 1)\n        else:\n            entry.conf = max(entry.conf - 1, 0)\n\nif meta.old_history is not None and entry.length is not None:\n    old_hist = meta.old_history\n    h0 = old_hist & 1\n    hl = (old_hist >> min(entry.length, history_bits - 1)) & 1\n    hl1 = (old_hist >> min(max(entry.length - 1, 0), history_bits - 1)) & 1\n    hl2 = (old_hist >> min(max(entry.length - 2, 0), history_bits - 1)) & 1\n    idx = (h0 << 3) | (hl << 2) | (hl1 << 1) | hl2\n\n    sat_value = entry.counters[idx]\n    if outcome == 1:\n        entry.counters[idx] = min(sat_value + 1, (1 << (counter_bits - 1)) - 1)\n    else:\n        entry.counters[idx] = max(sat_value - 1, -(1 << (counter_bits - 1)))\n\nmeta.valid = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The saturating counter index is formed using bits 0, LPT_TOTAL, LPT_TOTAL - 1, and LPT_TOTAL - 2 from the local history vector.",
... [truncated]

[Usage]
{"input_tokens": 33573, "output_tokens": 25962, "thinking_tokens": 23487, "cache_read_tokens": 0, "total_tokens": 59535}

[Result]
status=SUCCESS conversation=b7b8f4fa-c5cd-4234-95d8-bac7db5c1dee turns=1 duration=253.494547241s usage={"input_tokens": 33573, "output_tokens": 25962, "thinking_tokens": 23487, "cache_read_tokens": 0, "total_tokens": 59535}


