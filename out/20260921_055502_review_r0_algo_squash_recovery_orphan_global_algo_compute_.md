success: True
usage: {'input_tokens': 32106, 'output_tokens': 38096, 'thinking_tokens': 33271, 'cache_read_tokens': 0, 'total_tokens': 70202}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Pipeline flush allows the branch predictor to exploit register values from in-flight instructions that finished execution prior to pipeline restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explicitly states that instructions finishing execution before restart enlarge the visible register value set available to the predictor after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline flush, in-flight entries matching squashed ROB indices in reg_status_table are invalidated by setting decay_ctr to 255.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper leaves recovery of the Tomasulo-like table to future work and does not specify how squashed in-flight entries are identified or invalidated during a pipeline flush.",
      "enum_candidates": [
        "clear_squashed",
        "clear_all_uncompleted",
        "lazy_decay"
      ]
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table contains 65 entries corresponding to 64 architectural registers plus 1 condition-code flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates 65 entries for the register status tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each status table entry consists of a 1-bit valid flag, a 14-bit payload holding a 14-bit ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper defines the entry fields as a valid bit and a 14-bit tag or 12-bit digest payload, with Table 3 adding an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "The total storage cost of the register status table is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 gives 65 entries of 23 bits (1 + 14 + 8) each, totaling exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "The register status table contains one entry per logical register and is directly indexed by logical register identifier.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper explicitly states that the table provides one dedicated entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/default",
      "claim": "The default instruction decay threshold for invalidating register digests is 256 instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that each digest is invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/range",
      "claim": "The tuning range for DECAY_THRESHOLD_INSTS is [64, 1024] powers of two.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed decay threshold of 256 instructions and does not evaluate or define a range of alternative decay thresholds.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7/storage_impact",
      "claim": "The decay counter width is Log2(DECAY_THRESHOLD_INSTS), defaulting to 8 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the decay counter as 8 bits, which tracks up to 256 instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/default",
      "claim": "The default register digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly states that RUNLTS generates a 12-bit digest from each register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/range",
      "claim": "The tuning range for DIGEST_BITS is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies a fixed 12-bit digest and does not define or evaluate an exploration range for digest width.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8/storage_impact",
      "claim": "The payload field in the status table must hold either a 14-bit tag or a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The paper states that the payload field stores either a 14-bit tag or a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For a 64-bit integer register with value 0x40, the digest is computed by XOR-folding trailing zero count, leading zero count shifted by 3, and LSBs shifted by 6.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) does not define how counts exceeding 63 are encoded (saturation vs wrap vs sign-matching) nor how leading/trailing ones versus zeros are distinguished, as noted in declared ambiguity U3.",
      "enum_candidates": [
        "saturate",
        "wrap",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A condition code flags register digest replicates the 4-bit flag value three times to form a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the 4 flag bits three times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP64 register digest extracts bits [63:55] and places them at bit positions [11:3] with bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) leaves whether floating-point fields are right-aligned at bit 3 or bit 0 unstated, as noted in declared ambiguity U4.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A digest entry is invalidated and cleared to unavailable when 256 instructions execute without that register being updated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that digests are invalidated after 256 subsequent instructions are decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank contribution is scaled by 2.5 when its usefulness sum is positive and suppressed to 0 when non-positive.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) does not label the wire selecting between x0 and x2.5 bank scaling, leaving it uncertain whether bank usefulness drives the multiplier or a static scaling applies, as noted in declared ambiguity U2.",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When multiple registers are available in a bank at prediction time, the update algorithm randomly chooses exactly one register for training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper explicitly states that one available register is randomly selected within a bank for the update."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/default",
      "claim": "The default number of logical registers tracked by sR is 65.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 sizes the sR usefulness table across exactly 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/range",
      "claim": "The tuning range for NUM_LOGICAL_REGS is [32, 128].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper defines sR around a fixed architectural set of 65 logical registers (64 INT/FP registers plus 1 flag register) and does not define a tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1/storage_impact",
      "claim": "NUM_LOGICAL_REGS directly scales UT storage by 6 x NUM_LOGICAL_REGS x 24 bits and status table storage by 23 x NUM_LOGICAL_REGS bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates UT storage as 6 bits times 65 registers times 24 entries, and auxiliary status table storage as 23 bits per register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The sR prediction weight tables and usefulness tables use 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights for all WT tables in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The tuning range for WEIGHT_BITS is [4, 8].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 6-bit weights for sR tables and does not evaluate or define an alternative tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "WEIGHT_BITS linearly scales all WT and UT storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 shows WT and UT capacities are directly proportional to the weight bit width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9/default",
      "claim": "The default scaling factor for useful register banks is 2.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows a multiplier stage labelled x0 or x2.5 but does not label the driving selection wire, leaving the exact condition under which 2.5 applies uncertain, as noted in declared ambiguity U2.",
      "enum_candidates": [
        "bank_usefulness_positive",
        "global_static_scale"
      ]
    },
    {
      "pointer": "/parameters/9/range",
      "claim": "The tuning range for USEFUL_MULTIPLIER is [1.0, 4.0].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper only illustrates scaling by 2.5 (or 0) in Figure 5(c) and does not define a tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "The sR component is an SC sub-predictor correlating branch outcomes with register value digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We extended the SC with components that capture correlations between register values and branch outcomes. The components use digests of currently available register values as their input.",
        "why": "The paper introduces sR as an SC component utilizing register value digests to capture branch outcome correlations."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source/paper_title",
      "claim": "The source paper title is 'RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables",
        "why": "The paper title matches the source title character for character."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The host interface must provide newly produced register values and completion signals from execution units to update digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload is overwritten with the produced value's digest upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting/total_storage_bits",
      "claim": "The total storage cost of the sR component is 53,863 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives 53863 bits as the exact total storage cost of the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/trigger",
      "claim": "Digest computation is triggered when an instruction finishes execution and produces an architectural register value or flag value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper states that digest generation and payload overwrite occur when an instruction completes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "For integer registers, digest is formed by XOR-folding 6-bit trailing zero count, 6-bit leading zero count shifted by 3, and 6-bit LSBs shifted by 6.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(a) does not specify whether leading and trailing bit counts saturate at 63, wrap modulo 64, or match the sign bit, nor how ones versus zeros are distinguished, as noted in declared ambiguity U3.",
      "enum_candidates": [
        "saturate",
        "wrap",
        "match_sign_bit"
      ]
    },
    {
      "pointer": "/algorithms/0/notes",
      "claim": "For floating-point registers, digest extracts sign and exponent MSBs right-aligned at bit position 3.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 6(b) leaves whether floating-point fields are right-aligned at bit 3 or bit 0 unstated, as noted in declared ambiguity U4.",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:squash_recovery+orphan+global+algo:compute_register_digest` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from...

[Init]
model=gemini-3.8-flash-medium conversation=80b4384f-7fbc-4fee-99cc-ea888a02144a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_377f66ffdab2a712

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Pipeline flush allows the branch predictor to exploit register values from in-flight instructions that finished execution prior to pipeline restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explicitly states that instructions finishing execution before restart enlarge the visible register value set available to the predictor after a flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "On a pipeline flush, in-flight entries matching squashed ROB indices in reg_status_table are invalidated by setting decay_ctr to 255.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper leaves recovery of the Tomasulo-like table to future work and does not specify how squashed in-flight entries are identified or invalidated during a pipeline flush.",
      "enum_candidates": [
        "clear_squashed",
        "clear_all_uncompleted",
        "lazy_decay"
      ]
    },
    {
      "pointer": "/state/0/organization",
      "claim": "The register status table contains 65 entries corresponding to 64 architectural registers plus 1 condition-code flag register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly allocates 65 entries for the register status tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/en
... [truncated]

[Usage]
{"input_tokens": 32106, "output_tokens": 38096, "thinking_tokens": 33271, "cache_read_tokens": 0, "total_tokens": 70202}

[Result]
status=SUCCESS conversation=80b4384f-7fbc-4fee-99cc-ea888a02144a turns=1 duration=193.495570266s usage={"input_tokens": 32106, "output_tokens": 38096, "thinking_tokens": 33271, "cache_read_tokens": 0, "total_tokens": 70202}


