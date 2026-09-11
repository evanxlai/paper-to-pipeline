# Debug turn (integration attempt {{attempt}})

The deterministic gate rejected your integration. The gate output is below. Fix the causes and stop. Do not restate the plan.

## Gate output

{{gate_feedback}}

## Rules for this turn

1. Reproduce the first failure with the build or run tools before you edit.
2. If the feature-off metrics differ from the baseline, look for state that the enable knob does not isolate. Common causes: history updates outside the knob, table allocation in shared structures, and changed random seeds.
3. If a unit test fails, fix the implementation. Do not edit the test.
4. When the storage account exceeds the budget, shrink the feature tables or the donor structures named in the spec. Record the new split in PORT_NOTES.md.
