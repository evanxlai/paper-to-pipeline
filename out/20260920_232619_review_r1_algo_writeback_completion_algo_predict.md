success: True
usage: {'input_tokens': 31323, 'output_tokens': 27438, 'thinking_tokens': 23193, 'cache_read_tokens': 0, 'total_tokens': 58761}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The writeback completion handler updates the register status digest table with the computed digest and sets the valid bit when an instruction writing a destination register completes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that instruction completion triggers overwriting the entry's payload with the digest and asserting valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The completion handler checks that the payload matches the instruction's ROB tag while valid is 0 before updating to prevent overwriting newer in-flight register allocations.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Adopting Tomasulo's algorithm requires verifying the ROB tag stored during decode matches the completing instruction before committing the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Checking inst.writes_register relies on host pipeline instruction decode metadata rather than an unproduced internal branch predictor state.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "The paper defines register writing as an architectural attribute of decoded instructions supplied by the execution pipeline interface."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Register_Status_Digest_Table contains 65 entries corresponding to the logical registers, each entry consisting of a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly defines the entry structure with 1 valid bit, 14 payload bits, and 8 decay counter bits across 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The 65 logical registers in Register_Status_Digest_Table are partitioned across eight banks, with bank 0 containing nine registers and banks 1 through 7 containing eight registers each.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The text confirms the 8-bank partitioning where each bank encompasses eight or nine logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Register_Prediction_Weight_Tables_WT comprises eight banks, where each bank contains three direct-mapped sub-tables WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries) with 6-bit signed weights totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 8 banks of sub-tables of sizes 128, 256, and 512 entries storing 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Each WT bank sub-table is indexed by a hash of the branch PC and the selected 12-bit register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\"",
        "why": "Figure 5(c) illustrates hashing PC and the chosen register digest into h0, h1, and h2 to index the three WT tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Register_Usefulness_Weight_Tables_UT contains three tables (UT0, UT1, UT2) of 8 entries each, where each entry stores 6-bit signed weights for all 65 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines three 8-entry tables holding 6-bit weights for all 65 logical registers totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The number of banks in the register component is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default number of logical registers is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies the factor of 65 logical registers across all UT and status table entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The register decay invalidation threshold defaults to 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes the invalidation threshold at 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that the generated digest width is 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The WT weight width is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 lists WT weight width as 6 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The useful multiplier applied to the WT bank summation is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"x0 or x2.5\"",
        "why": "Figure 5(c) directly labels the multiplier stage on the WT output sum as x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The number of entries per usefulness table UT is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\"",
        "why": "Figure 5(c) and Table 3 specify 8 entries (2^3) for each of UT0, UT1, and UT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR folding trailing zeros/ones count at [5:0], leading zeros/ones count shifted to [8:3], and LSB bits [5:0] shifted to [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) defines the exact 3-way XOR overlap of trailing count [5:0], leading count [8:3], and Value[5:0] at [11:6], matching the unit test computation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code flag register digests replicate the 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) explicitly specify 3-fold replication of the 4 flag bits across the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 register digests extract sign and top exponent bits from Value[31:26] positioned at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies extracting Value[31:26] mapped to digest bit positions [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Register digests remain valid for 255 decoded instructions and transition to invalid on the 256th decoded instruction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The text confirms invalidation occurs exactly after 256 decoded instructions without update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank argmax logic selects the valid register with highest usefulness sum and applies the 2.5x scaling when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 states the predictor picks the digest of the most useful available register, and Figure 5(c) specifies the x2.5 multiplier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When the highest usefulness of valid registers in a bank is negative or zero, the multiplier applies x0 suppressing the bank contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"x0 or x2.5\"",
        "why": "Figure 5(c) specifies the alternative multiplier as x0, suppressing the contribution when usefulness is non-positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "In-flight producer instructions that complete prior to pipeline flush completion retain valid digests after the branch flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 confirms that instructions completed before restart leave their values available in the status table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Prediction lookup selects the most useful valid register per bank using UT0, UT1, and UT2 sums, querying WT0, WT1, and WT2 and scaling by 2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 and Figure 5(c) define selecting the most useful register among valid entries per bank and multiplying WT weight sums by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The references to 'as(...)' and 'length(...)' in predict pseudocode are pseudocode idioms, where 'as' is part of an explanatory comment and 'length' is standard sequence cardinality.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Static checker warning for 'as(...)' arose from comment text 'implementable as (wt_sum * 5) >> 1', and 'length(valid_regs)' checks the count of valid registers in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Subscripting UT0, UT1, UT2 with 'r' in predict and 'chosen_reg' in update addresses the identical domain of logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Both 'r' and 'chosen_reg' index the logical register dimension within the 65-register table entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Subscripting WT0, WT1, WT2 with 'h0', 'h1', 'h2' across predict and update addresses identical domains computed from hash_wt0, hash_wt1, and hash_wt2.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\"",
        "why": "Both algorithms compute the indices using hash_wt0/1/2(branch_pc, digest), indexing into the 512, 256, and 128 entry tables respectively."
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
model=gemini-3.8-flash-medium conversation=1ada799d-549c-4ba9-9d0a-d13fa68c468f cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The writeback completion handler updates the register status digest table with the computed digest and sets the valid bit when an instruction writing a destination register completes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that instruction completion triggers overwriting the entry's payload with the digest and asserting valid."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The completion handler checks that the payload matches the instruction's ROB tag while valid is 0 before updating to prevent overwriting newer in-flight register allocations.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Adopting Tomasulo's algorithm requires verifying the ROB tag stored during decode matches the completing instruction before committing the payload."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "Checking inst.writes_register relies on host pipeline instruction decode metadata rather than an unproduced internal branch predictor state.",
      "verdict": "SUPPORTED",
      "evidence": {
        "
... [truncated]

[Usage]
{"input_tokens": 31323, "output_tokens": 27438, "thinking_tokens": 23193, "cache_read_tokens": 0, "total_tokens": 58761}

[Result]
status=SUCCESS conversation=1ada799d-549c-4ba9-9d0a-d13fa68c468f turns=1 duration=146.619558686s usage={"input_tokens": 31323, "output_tokens": 27438, "thinking_tokens": 23193, "cache_read_tokens": 0, "total_tokens": 58761}


