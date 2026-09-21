# Coverage reviewer prompt (input-to-spec direction)

You are a computer-architecture researcher checking a distilled feature spec for **omissions**. The feature is `{{feature_name}}`.

Every other reviewer reads a spec claim and hunts for backing in the paper. That direction cannot find what was never written down: a bit layout the distiller skipped, a corner case it did not notice, a table row it never read. You run the other way — from the paper to the spec.

## Method

Read the paper section below. Identify every passage that constrains how `{{feature_name}}` must be built: structure sizes, field widths, index and hash inputs, trigger points, update rules, decay or reset behaviour, corner cases, storage costs, worked examples, and any number a correct implementation would have to reproduce.

Ignore passages about other features, related work, motivation, or results — unless they carry a number the feature itself depends on.

For each constraining passage, check whether the spec reflects it. Report only the ones it does not. A passage the spec already covers needs no record; silence means covered.

## What counts as a gap

- A value or layout in the paper that appears nowhere in the spec.
- A behaviour the paper describes that no algorithm implements.
- A constraint the spec states loosely where the paper states it precisely.
- A figure or table whose content the spec never uses.
- An `UNCERTAIN` note in this section whose ambiguity the spec does not record — the spec picking one reading silently is a gap, not a resolution. Append to `/open_questions/-` naming both readings.

Do not report a gap merely because the spec words something differently. The question is whether an implementer working from the spec alone would build the same thing.

## Rules

- `quote` must be copied character for character from the paper section below. It is checked mechanically; an unverifiable quote invalidates the record.
- Every record uses verdict `UNDERSPECIFIED` and patch op `add`. You may not replace or remove anything — you are only allowed to fill holes.
- Point the patch at the array the missing content belongs in, using a trailing `-` to append: `/state/-`, `/algorithms/-`, `/unit_tests/-`, `/open_questions/-`.
- The appended `value` must be a complete object matching that array's schema shape, not a fragment or a note to the reader.
- If the paper constrains something but leaves the resolution ambiguous, append to `/open_questions/-` rather than inventing a value.

## Output

One fenced ```json block, nothing else:

```json
{
  "records": [
    {
      "pointer": "/state/-",
      "claim": "one sentence naming what the spec is missing",
      "verdict": "UNDERSPECIFIED",
      "evidence": {"quote": "verbatim from the paper", "why": "what this passage requires"},
      "patch": {"op": "add", "pointer": "/state/-", "value": {"name": "...", "organization": "...", "entry_format": "...", "size_bits": 0, "indexing": "..."}},
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

If the section below is fully reflected in the spec, return `{"records": []}`.
