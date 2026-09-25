success: True
usage: {'input_tokens': 28000, 'output_tokens': 33819, 'thinking_tokens': 30574, 'cache_read_tokens': 0, 'total_tokens': 61819}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "Each register usefulness weight table has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries for each of the three usefulness weight tables across the 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Prediction and usefulness weights in the register component are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that the prediction weight tables in the register component store 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The parameter algorithms_6_pseudocode_variant selects the policy for recovering register status table entries upon a branch misprediction flush.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper explicitly defers recovery of the Tomasulo-like table to future work and does not specify a recovery scheme for squashed instructions.",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The parameter algorithms_0_pseudocode_variant configures the integer digest encoding when a 64-bit value contains 64 identical leading or trailing bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 6-bit fields for leading and trailing zero/one counts of 64-bit integers but does not specify how 64 identical bits or the distinction between zero and one counts is encoded.",
      "enum_candidates": [
        "sign_match",
        "saturate_63",
        "wrap_64",
        "zero_only"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "The parameter algorithms_0_pseudocode_variant_2 selects the method used to classify floating-point register formats from the most significant bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper notes that the most significant bits are inspected to classify the floating-point format but does not specify the classification logic.",
      "enum_candidates": [
        "nan_box_msb",
        "opcode_type",
        "exp_range"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The parameter algorithms_2_pseudocode_variant determines the selection condition between scaling by 2.5 and suppression by 0 for register bank outputs.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) shows a multiplier stage labelled 'x0 or x2.5' but does not specify the control signal or threshold that selects between x2.5 and x0.",
      "enum_candidates": [
        "pred_agreed",
        "sc_useful",
        "conf_based"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The parameter state_0_variant selects the hash function mapping PC and register digest to prediction weight table indices h0, h1, and h2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) indicates that PC and register digest are hashed to produce indices h0, h1, and h2, but does not state the hashing functions.",
      "enum_candidates": [
        "xor_shift",
        "fold_xor",
        "prime_mult"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "The parameter state_1_variant selects the indexing function for register usefulness tables indexed by PC (skewed).",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) specifies 'PC (skewed)' as index input to UT0, UT1, and UT2, but does not provide the skewing or indexing function.",
      "enum_candidates": [
        "pc_bit_xor",
        "prime_mod",
        "shifted_pc"
      ]
    },
    {
      "pointer": "/algorithms/6/notes",
      "claim": "Completed instructions finished prior to a branch misprediction resolution retain their digests across the pipeline flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "This passage establishes that instructions completing before branch misprediction resolution retain their values to enlarge the visible digest set upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "On a squash, in-flight register status table entries whose payload matches a flushed ROB index are cleared by resetting valid to 0 and payload to 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not detail the recovery algorithm for invalidating or restoring squashed instructions in the register status table, noting that table recovery is left to future work.",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/state/2/organization",
      "claim": "The register status table contains 65 entries corresponding to logical registers 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies that the register status table auxiliary entry structure is replicated for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry of the register status table contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the fields of each entry as a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The register status table auxiliary data consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Each entry is 23 bits (1 + 14 + 8) and replicating across 65 entries yields 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 dimensions the register component usefulness tables across 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "Each register value digest is 12 bits in size.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly specifies that register value digests are 12 bits wide."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer digest generation derives a 12-bit digest by XOR-folding trailing zero/one count, leading zero/one count, and the six least significant bits of the register value.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 states that the integer digest comprises leading count, trailing count, and the 6 LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "For 64-bit floating-point registers, digest generation extracts the sign bit and high-order exponent bits from bits [63:55] to place into digest bits [11:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 establishes extracting the sign bit and most significant exponent bits from MSBs for FP digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "For condition flags, the four flag bits are replicated three times to construct a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 confirms verbatim that the four flag bits are replicated three times to fill 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A digest entry is invalidated after 256 subsequent instructions have been decoded without new writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 specifies that digests are invalidated after 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A register bank selects the available register with the largest usefulness weight across its usefulness tables to index its prediction weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 confirms that the component selects the most useful available register within the bank to forward to prediction tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, if multiple registers were available in a bank at prediction time, one is randomly chosen for update so each table needs only a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 specifies random selection among available registers in a bank during training to allow single-write-port tables."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `orphan+algo:mispredict_recovery` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never rea...

[Init]
model=gemini-3.8-flash-medium conversation=6d5565b8-c59a-4926-8668-3d8f2f1fedd7 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "Each register usefulness weight table has 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 (8) entries for each of the three usefulness weight tables across the 65 registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Prediction and usefulness weights in the register component are 6 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates that the prediction weight tables in the register component store 6-bit weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "The parameter algorithms_6_pseudocode_variant selects the policy for recovering register status table entries upon a branch misprediction flush.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper explicitly defers recovery of the Tomasulo-like table to future work and does not specify a recovery scheme for squashed instructions.",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The parameter algorithms_0_pseudocode_variant configures the integer digest encoding when a 64-bit value contains 64 identical leading or trailing bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies 6-bit fields for leading and trailing zero/one counts of 64-bit integers but does not specify how 64 identical bits or the distinction between zero and one counts is encoded.",
      "enum_candidates": [
... [truncated]

[Usage]
{"input_tokens": 28000, "output_tokens": 33819, "thinking_tokens": 30574, "cache_read_tokens": 0, "total_tokens": 61819}

[Result]
status=SUCCESS conversation=6d5565b8-c59a-4926-8668-3d8f2f1fedd7 turns=1 duration=192.243717264s usage={"input_tokens": 28000, "output_tokens": 33819, "thinking_tokens": 30574, "cache_read_tokens": 0, "total_tokens": 61819}


