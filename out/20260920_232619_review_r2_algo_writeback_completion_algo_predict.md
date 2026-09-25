success: True
usage: {'input_tokens': 31339, 'output_tokens': 30026, 'thinking_tokens': 26166, 'cache_read_tokens': 0, 'total_tokens': 61365}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "Writeback completion triggers at instruction completion stage to update the register status digest table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that updating the payload with the digest and setting the valid bit occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Completion updates verify the entry holds the matching ROB tag before writing the 12-bit digest, setting valid to 1, and resetting decay_ctr.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies using Tomasulo-like tag matching with the instruction's ROB index stored at decode and overwritten with the digest on completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The completion stage checks `inst.writes_register` supplied by the execution pipeline interface.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines the mechanism specifically for instructions that write a register, which is information provided by the processor pipeline framework."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Status_Digest_Table contains 65 entries corresponding to logical registers, partitioned across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper states that the register component is partitioned into eight banks covering eight or nine logical registers each, totaling 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Each entry of Register_Status_Digest_Table has 1 valid bit, 14 payload bits, and an 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies entry fields of 1 valid bit, 14 payload bits, and 8 decay counter bits across 65 entries, totaling 65 * 23 = 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Register_Prediction_Weight_Tables_WT contains 8 banks with 3 sub-tables per bank sized at 512, 256, and 128 entries of 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 gives the WT storage breakdown as 8 banks of 2^7, 2^8, and 2^9 entries with 6-bit weights, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Register_Usefulness_Weight_Tables_UT contains 3 tables of 8 entries each, where each entry stores 6-bit weights for all 65 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly calculates UT storage as 3 tables of 2^3 entries with 6-bit weights for each of the 65 registers, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The register component uses 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states in Section 4.2 that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers across its tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly dimensions the auxiliary status data and usefulness weight tables for 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default decay threshold for digest invalidation is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper states directly that each digest is invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The register value digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper directly specifies generating a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The prediction weight width in WT is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines each prediction weight entry in WT as 6 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The useful bank prediction multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) explicitly specifies the bank output multiplier as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "Each of the three UT tables has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 states that the three UT tables each have 2^3 = 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation XOR-folds trailing zero count at [5:0], leading zero count at [8:3], and value LSBs at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper Section 4.2 and Figure 6(a) specify 6-bit trailing count at [5:0], leading count at [8:3], and LSBs at [11:6] combined via XOR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Flag register digest generation replicates the 4-bit flag pattern three times to fill 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper directly states that the four flag bits are replicated three times to create the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 digest generation extracts bits [31:26] (sign and high exponent) into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) define extracting Value[31:26] at digest positions [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest entry transitions to invalid on the 256th decoded instruction following its write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies digest invalidation after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank argmax logic selects the register with the highest usefulness sum, applying the 2.5 multiplier when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper specifies selecting the most useful available register and scaling by 2.5 in Figure 5(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When the most useful register in a bank has non-positive usefulness, the multiplier stage suppresses output by applying x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows that bank output is either scaled by 2.5 or suppressed with x0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Values produced by instructions completed prior to pipeline flush completion remain valid for post-flush predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 establishes that instructions completed during misprediction resolution enlarge the set of valid values visible when fetch restarts."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "Prediction lookup filters for valid registers whose digests are forwarded to the register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper states that only entries with valid bit set forward digests during predictor query."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "For each bank, usefulness tables UT0, UT1, and UT2 are indexed at depth 2 by logical register identifier `r` to find the most useful available register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "The paper defines UT entries as vectors of weights for each register of the bank, confirming that indexing by `r` in predict and `chosen_reg` in update share the same domain of bank registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "WT0, WT1, and WT2 are indexed by hash functions h0 (9-bit), h1 (8-bit), and h2 (7-bit) derived from branch PC and the selected digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 and Figure 5(c) specify WT table depths of 512, 256, and 128 entries per bank indexed by PC and register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3",
      "claim": "The bank weight sum is scaled by 2.5 when best usefulness is positive and summed across banks into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) illustrates per-bank scaling by x0 or x2.5 before summing into sR; the pseudocode comment notes integer shift arithmetic rather than calling an external function."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:writeback_completion+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they ne...

[Init]
model=gemini-3.8-flash-medium conversation=487a85dc-73f1-4058-96b9-b289f4f12446 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2",
      "claim": "Writeback completion triggers at instruction completion stage to update the register status digest table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that updating the payload with the digest and setting the valid bit occurs when the instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Completion updates verify the entry holds the matching ROB tag before writing the 12-bit digest, setting valid to 1, and resetting decay_ctr.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper specifies using Tomasulo-like tag matching with the instruction's ROB index stored at decode and overwritten with the digest on completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "The completion stage checks `inst.writes_register` supplied by the execution pipeline interface.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines the mechanism specifically for instructions that write a register, which is information provided by the processor pipeline framework."
      },
      "patch": null,
      "open_question": null,
      "
... [truncated]

[Usage]
{"input_tokens": 31339, "output_tokens": 30026, "thinking_tokens": 26166, "cache_read_tokens": 0, "total_tokens": 61365}

[Result]
status=SUCCESS conversation=487a85dc-73f1-4058-96b9-b289f4f12446 turns=1 duration=161.636495175s usage={"input_tokens": 31339, "output_tokens": 30026, "thinking_tokens": 26166, "cache_read_tokens": 0, "total_tokens": 61365}


