success: True
usage: {'input_tokens': 34523, 'output_tokens': 27566, 'thinking_tokens': 24468, 'cache_read_tokens': 0, 'total_tokens': 62089}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The prediction index is calculated using only 4 bits, omitting the additional 4 bits used in the 32KB configuration.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Light grey squares show the bits that are additionally considered to make a prediction in the 32KB predictor. In this case, these additional bits correspond to the bits 1, 2 × LPTOTAL, 2 × LPTOTAL - 1 and 2 × LPTOTAL - 2.",
        "why": "The paper specifies that the larger configuration incorporates 4 additional specific history bits into the index."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "entry_idx = -1\ntag_val = PC & ((1 << tag_bits) - 1)\nfor i in range(num_entries):\n    if WPT[i].tag == tag_val:\n        entry_idx = i\n        break\n\npred = None\ninternal_pred = None\nif entry_idx != -1:\n    entry = WPT[entry_idx]\n    h0 = entry.history & 1\n    hl = (entry.history >> min(entry.length, history_bits - 1)) & 1\n    hl1 = (entry.history >> min(max(entry.length - 1, 0), history_bits - 1)) & 1\n    hl2 = (entry.history >> min(max(entry.length - 2, 0), history_bits - 1)) & 1\n    idx = (h0 << 3) | (hl << 2) | (hl1 << 1) | hl2\n    \n    if num_counters > 16:\n        h1 = (entry.history >> 1) & 1\n        h2l = (entry.history >> min(2 * entry.length, history_bits - 1)) & 1\n        h2l1 = (entry.history >> min(max(2 * entry.length - 1, 0), history_bits - 1)) & 1\n        h2l2 = (entry.history >> min(max(2 * entry.length - 2, 0), history_bits - 1)) & 1\n        idx = (idx << 4) | (h1 << 3) | (h2l << 2) | (h2l1 << 1) | h2l2\n\n    sat_value = entry.counters[idx]\n    internal_pred = (sat_value >= 0)\n    if entry.conf > 0 and abs(2 * sat_value + 1) >= threshold:\n        pred = internal_pred\n\nmeta_idx = rob_index % max_in_flight_branches\nmeta = WPT_InFlight_Meta[meta_idx]\nmeta.valid = 1\nmeta.entry_idx = entry_idx\nmeta.old_history = 0\nmeta.tage_pred = 0\nmeta.wpt_pred = 0\nif entry_idx != -1:\n    meta.old_history = WPT[entry_idx].history\n    meta.tage_pred = get_TAGE_prediction(PC)\n    meta.wpt_pred = internal_pred\n    \n    spec_outcome = pred if pred is not None else meta.tage_pred\n    WPT[entry_idx].history = ((WPT[entry_idx].history << 1) | spec_outcome) & ((1 << history_bits) - 1)\n\nreturn pred"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The WPT structure requires a total of 1065 bits of storage in the 4KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "The wormhole predictor requires 1065 and 10997 bits",
        "why": "The text confirms the 4KB configuration of the wormhole predictor uses exactly 1065 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "A metadata structure tracks in-flight branches for speculative history updates.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The paper does not mention any structures or queues for tracking in-flight branches or speculative state recovery."
      },
      "patch": null,
      "open_question": "How should speculative update recovery and in-flight branch metadata be managed?",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default tag width is 18 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Tag 18 18",
        "why": "Table II confirms the tag width is 18 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2/default",
      "claim": "The confidence counter is 4 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Confidence 4 4",
        "why": "Table II confirms the confidence counter is 4 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3/default",
      "claim": "The ranking counter is 3 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Ranking 3 3",
        "why": "Table II confirms the ranking field is 3 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4/default",
      "claim": "The local history vector is 101 bits for the 4KB configuration.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "History vector 101 257",
        "why": "Table II confirms the history vector is 101 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/5/default",
      "claim": "The history length field is 7 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "History length 7 9",
        "why": "Table II confirms the history length field is 7 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The confidence threshold for prediction is 16.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "A threshold of 16 worked well for the specific workloads.",
        "why": "The text explicitly states the threshold value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The maximum number of in-flight branches is 128.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The paper does not detail speculative execution limits or an in-flight branch queue size."
      },
      "patch": null,
      "open_question": "What should the capacity of the in-flight branch queue be?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Allocating a new entry initializes confidence and ranking to 0, and predict handles zero confidence.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The paper specifies how to allocate an entry but does not explicitly state the initial values for confidence and ranking, nor the exact interactions with an in-flight metadata queue."
      },
      "patch": null,
      "open_question": "What are the exact initial values for a newly allocated entry's confidence and ranking, and how does it interact with the in-flight metadata queue?",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1/expect",
      "claim": "The test expectation explicitly states the correct expected outcome.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "why": "A deterministic finding flags the test expectation as a vacuous_test because it uses the word 'correct' instead of concrete expected values."
      },
      "patch": {
        "op": "replace",
        "pointer": "/unit_tests/1/expect",
        "value": "Because history remains 0, index 0 is used every time. The saturating counter[0] decrements from 0 to -16, saturating at -16. The internal WPT prediction is 0 (since counter < 0). TAGE is 1. WPT prediction matches the outcome, so conf increments from 0 to 15, saturating at 15. The WPT_InFlight_Meta valid bits are set to 1 by predict and cleared to 0 by update, ending at 0."
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "On a branch squash, the local history is recovered from the in-flight metadata.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The paper lacks any discussion of misspeculation recovery or branch squashes."
      },
      "patch": null,
      "open_question": "How should the predictor recover its state upon a branch squash?",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1/pseudocode",
      "claim": "The entry length field is written conditionally during allocation but read unconditionally, leading to potential inconsistency.",
      "verdict": "INCONSISTENT",
      "evidence": {
        "why": "A deterministic finding indicates that entry.length is only assigned inside a conditional branch of allocate, but is read on an unconditional path, requiring it to be assigned in both branches."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/1/pseudocode",
        "value": "if get_SC_problematic(PC) and get_LPTOTAL() > 0:\n    entry_idx = -1\n    tag_val = PC & ((1 << tag_bits) - 1)\n    for i in range(num_entries):\n        if WPT[i].tag == tag_val:\n            entry_idx = i\n            break\n            \n    if entry_idx != -1:\n        WPT[entry_idx].ranking = min(WPT[entry_idx].ranking + 1, (1 << rank_bits) - 1)\n        WPT[entry_idx].length = get_LPTOTAL() & ((1 << length_bits) - 1)\n    else:\n        min_rank = (1 << rank_bits)\n        replace_idx = 0\n        for i in range(num_entries):\n            if WPT[i].ranking < min_rank:\n                min_rank = WPT[i].ranking\n                replace_idx = i\n                \n        WPT[replace_idx].tag = tag_val\n        WPT[replace_idx].conf = 0\n        WPT[replace_idx].ranking = 0\n        WPT[replace_idx].length = get_LPTOTAL() & ((1 << length_bits) - 1)\n        WPT[replace_idx].history = 0\n        for i in range(num_counters):\n            WPT[replace_idx].counters[i] = 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "The recover algorithm restores speculatively updated history from a checkpoint.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "why": "The paper does not detail any mechanisms for speculative history checkpointing or recovery."
      },
      "patch": null,
      "open_question": "How is speculative state checkpointed and recovered?",
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `wormhole`. You are reviewing unit `algo:predict+algo:allocate+algo:recover` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; ...

[Init]
model=gemini-3.1-pro-high conversation=b1a44682-a85b-4356-99e0-08e78356a9ba cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_9e5df7c73518ca18

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The prediction index is calculated using only 4 bits, omitting the additional 4 bits used in the 32KB configuration.",
      "verdict": "CONTRADICTED",
      "evidence": {
        "quote": "Light grey squares show the bits that are additionally considered to make a prediction in the 32KB predictor. In this case, these additional bits correspond to the bits 1, 2 × LPTOTAL, 2 × LPTOTAL - 1 and 2 × LPTOTAL - 2.",
        "why": "The paper specifies that the larger configuration incorporates 4 additional specific history bits into the index."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "entry_idx = -1\ntag_val = PC & ((1 << tag_bits) - 1)\nfor i in range(num_entries):\n    if WPT[i].tag == tag_val:\n        entry_idx = i\n        break\n\npred = None\ninternal_pred = None\nif entry_idx != -1:\n    entry = WPT[entry_idx]\n    h0 = entry.history & 1\n    hl = (entry.history >> min(entry.length, history_bits - 1)) & 1\n    hl1 = (entry.history >> min(max(entry.length - 1, 0), history_bits - 1)) & 1\n    hl2 = (entry.history >> min(max(entry.length - 2, 0), history_bits - 1)) & 1\n    idx = (h0 << 3) | (hl << 2) | (hl1 << 1) | hl2\n    \n    if num_counters > 16:\n        h1 = (entry.history >> 1) & 1\n        h2l = (entry.history >> min(2 * entry.length, history_bits - 1)) & 1\n        h2l1 = (entry.history >> min(max(2 * entry.length - 1, 0), history_bits - 1)) & 1\n        h2l2 = (entry.history >> min(max(2 * entry.length - 2, 0), history_bits - 1)) & 1\n        idx = (idx << 4) | (h1 << 3) | (h2l << 2) | (h2l1 << 1) | h2l2\n\n    sat_value = entry.counters[idx]\n    internal_pred = (sat_value >= 0)\n    if entry.conf > 0 and abs(2 * sat_value + 1) >= threshold:\n        pred = internal_pred\n\nmeta_idx = rob_index % max_in_flight_branches\nmeta = WPT_InFlight_Meta[meta_idx]\nmeta.valid = 1\nmeta.entry_idx = en
... [truncated]

[Usage]
{"input_tokens": 34523, "output_tokens": 27566, "thinking_tokens": 24468, "cache_read_tokens": 0, "total_tokens": 62089}

[Result]
status=SUCCESS conversation=b1a44682-a85b-4356-99e0-08e78356a9ba turns=1 duration=152.058729486s usage={"input_tokens": 34523, "output_tokens": 27566, "thinking_tokens": 24468, "cache_read_tokens": 0, "total_tokens": 62089}


