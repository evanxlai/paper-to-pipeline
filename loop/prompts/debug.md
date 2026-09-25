# Debug turn (integration attempt {{attempt}})

The deterministic gate rejected your integration. The gate output is below. Fix the causes and stop. Do not restate the plan.

## Gate output

{{gate_feedback}}

## Rules for this turn

1. Reproduce the first failure before you edit. A fix for a failure you have not seen is a guess.
2. A `G2` reason means the feature-off path is not the baseline. Look for state the enable knob does not isolate. Common causes: history updated outside the knob, tables allocated inside a shared structure, a changed seed, a changed order of existing updates.
3. A `G3` reason names a test the plan declared. Fix the implementation. Do not weaken its pass condition. Do not change the string that condition matches. If the test's *command* is wrong about this tree, that is a plan defect, and the next section is how you fix it.
4. A `G5` reason means the feature does not move the metric the paper's way. That is a wiring fault, not a tuning one. Either the mechanism is not reaching the prediction path, or it is not consulting the state the spec says it should. Do not respond by changing a parameter's default.
5. A `G6` reason names a macro whose value never reaches the binary: the port rebuilt with it changed is byte-identical. Find the symbol it should set, from the plan's `host_symbol` and `observed` line for a host knob, or the spec structure it sizes for a feature knob, and make that symbol take its value from the macro. Check that the file the symbol lives in includes `sr_params.h`. Keep the default: with every macro at its default the binary must not change, or G2 fails.
6. Say nothing about storage budgets. Shrink nothing to make room. Resource constraints belong to the tuning stage alone, and no gate condition here weighs one.
7. Before you end the turn, stop every process you started in a terminal of your own, an `http.server` included. One left running keeps the turn from returning, and the gate never sees your fix.

Anything reported as recorded-not-blocking is not a failure and needs no fix.

## If the plan is wrong about this tree

The plan was written against this checkout. It can still be wrong about it. A hook point may name a symbol that has moved, an `observed` block may not match the code, a test command may name a target this tree does not build. Correct that here. Sending it back to the planning stage would re-read the whole tree and re-derive every decision that was already right, so that route is reserved for defects you may not decide.

You have two moves and no others.

**Revise.** Write a `## Plan revision` heading. Follow it with two fenced json blocks: the port plan, then the test plan. Each document must be complete. Never send a diff. Above the heading, say in prose what you changed and which gate reason it answers. Code then re-validates both documents against their schemas and the plan checks. Code also compares them against the pair in force, and writes them only if nothing was weakened. Carry on working after the blocks. The next gate run uses the accepted revision.

A revision may correct any of these: a `hook_points` entry, `structure.choice`, a `spec_map[].realization` and its `hook_ids`, `steps`, `risks`, an `interface_resolutions[].status` and `resolution` with its `fidelity_note`, a `knobs[].host_knob` and `binding`, a `correctness[].command`, any `timeout_seconds`, any `description`. A revision may also add new entries anywhere.

A performance entry's `run` block is a special case. You may correct it when that entry's `baseline.source` is `measure_feature_off`, because the feature-on and feature-off runs both go through it, so a corrected command moves both sides of the comparison. You may not correct it when the source is `recorded`, because the comparison point was measured before your port existed. There, `run` feeds only the measured side, so changing it moves the improvement without moving the bar. Build the target the plan named, or escalate.

**Escalate.** Everything else is frozen. The test plan is the standard you are judged by, and you do not get to lower it. Frozen fields: every `block_threshold` and `warn_threshold`, every `pass_condition`, every `clean_tree_result`, `metric_keys`, `baseline_rel_tol`, the smoke and performance trace sets, a performance entry's `metric`, `direction` and `baseline`, a `knobs[].macro` and `default`, the enable knob's `name`, a `rejected_alternatives` entry, an `open_questions[].assumption`, and `feature_name`, `host` and `host_revision`. Deleting any declared entry is frozen too. A test you drop is a demand the port no longer has to meet.

If a frozen value is genuinely wrong, do not rewrite it. Emit exactly this line:

    PLAN ESCALATION: <json pointer> -- <why the planning stage has to decide this>

Then stop. That ends the attempt. It is recorded as a finding and not as a failure by you. It is the right move for a real measurement-design defect. It is the wrong move for anything you could have fixed in the tree.

Do not hook somewhere the plan does not name without revising the plan first. A deviation nobody recorded is one nobody can diagnose.
