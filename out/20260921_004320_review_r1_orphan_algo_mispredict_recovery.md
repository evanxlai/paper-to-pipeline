success: True
usage: {'input_tokens': 27999, 'output_tokens': 26068, 'thinking_tokens': 22965, 'cache_read_tokens': 0, 'total_tokens': 54067}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "Each usefulness table in the register component defaults to 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 = 8 entries for each of the three usefulness tables per register in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default weight width for register component prediction and usefulness tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates a weight width of 6 bits for the prediction weight tables and usefulness tables in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "On a branch misprediction squash, recovery of in-flight register status table entries selects among clear_entry, restore_checkpoint, and no_recovery.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should entries in the register status table allocated to squashed in-flight instructions be recovered upon a branch misprediction flush?",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "Integer register digest generation encodes leading and trailing zero/one counts using sign_match, saturate_63, wrap_64, or zero_only.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading and trailing zero/one counts that reach 64 or differences between zero and one counts encoded in the 6-bit digest fields for integer registers?",
      "enum_candidates": [
        "sign_match",
        "saturate_63",
        "wrap_64",
        "zero_only"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "Floating-point format classification for digest generation selects between nan_box_msb, opcode_type, and exp_range inspection.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Which mechanism is used to inspect the most significant bits and classify floating-point register formats into FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_box_msb",
        "opcode_type",
        "exp_range"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The usefulness table in the register component updates entry usefulness based on pred_agreed, sc_useful, or conf_based conditions.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What criterion determines whether a register's usefulness weight is incremented or updated during branch training?",
      "enum_candidates": [
        "pred_agreed",
        "sc_useful",
        "conf_based"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The hash function computing prediction weight table indices h0, h1, h2 from PC and register digest uses xor_shift, fold_xor, or prime_mult.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash function is used to index prediction weight tables WT0, WT1, and WT2 from the branch PC and selected register digest?",
      "enum_candidates": [
        "xor_shift",
        "fold_xor",
        "prime_mult"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "The hash function computing skewed PC indices for usefulness tables UT0, UT1, UT2 uses pc_bit_xor, prime_mod, or shifted_pc.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What skewing or hashing function produces the skewed PC indices for usefulness tables UT0, UT1, and UT2?",
      "enum_candidates": [
        "pc_bit_xor",
        "prime_mod",
        "shifted_pc"
      ]
    },
    {
      "pointer": "/algorithms/6/notes",
      "claim": "Instructions finished before a misprediction flush retain their digests in the register status table to supply register values to subsequent branches.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 explains that instructions finishing before a misprediction is revealed enlarge the set of values available to the predictor upon restart."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/6/pseudocode",
      "claim": "On a branch misprediction squash, the predictor loops through the register status table and resets any invalid entry whose payload matches a flushed ROB index.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should entries in the register status table allocated to squashed in-flight instructions be recovered upon a branch misprediction flush?",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The register status table contains 65 direct-mapped entries, each having a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, consuming 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data specifies 65 entries each containing a 1-bit valid bit, 14-bit payload, and 8-bit decay counter, totaling 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The predictor tracks 65 logical registers by default.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 sizes both the register status table auxiliary data and usefulness tables for 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The register value digest generated for register components defaults to 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly states that RUNLTS generates a 12-bit digest from each 64-bit register value."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Unit test test_int_digest_generation verifies that a 64-bit integer value with 6 trailing zeros, 57 leading zeros, and LSBs 0 generates a 12-bit digest of 0x1CE via XOR-folding.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) specify that the 12-bit integer digest XOR-folds trailing zero count, leading zero count, and the 6 least significant bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Unit test test_fp64_digest_generation verifies that an FP64 value with bits [63:55] = 0b110000000 produces a 12-bit digest of 0xC00 with bits [11:3] populated.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) specify extracting the sign and leading exponent bits (Value[63:55]) into digest bits [11:3] for FP64 values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Unit test test_flag_digest_replication verifies that condition flag value 0xB is replicated three times to produce 12-bit digest 0xBBB.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 specifies replicating the four condition-code flag bits three times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "Unit test test_stale_digest_decay verifies that a valid digest in the register status table is invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 states that RUNLTS invalidates each digest after 256 subsequent instructions have been decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Unit test test_most_useful_selection verifies that the bank selects the register with the largest cumulative usefulness and scales the bank output by 2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) specify selecting the most useful available register digest in the bank and scaling the bank output by 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Unit test test_training_single_port_random_selection verifies that if multiple registers in a bank are valid at prediction time, exactly one is randomly selected for updates.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 specifies that if several registers were available in a bank, one is randomly chosen for training to require only a single write port per table."
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
model=gemini-3.8-flash-medium conversation=a22ae291-7776-47f5-b393-fd12a739d5a7 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/5",
      "claim": "Each usefulness table in the register component defaults to 8 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 specifies 2^3 = 8 entries for each of the three usefulness tables per register in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default weight width for register component prediction and usefulness tables is 6 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 indicates a weight width of 6 bits for the prediction weight tables and usefulness tables in the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "On a branch misprediction squash, recovery of in-flight register status table entries selects among clear_entry, restore_checkpoint, and no_recovery.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How should entries in the register status table allocated to squashed in-flight instructions be recovered upon a branch misprediction flush?",
      "enum_candidates": [
        "clear_entry",
        "restore_checkpoint",
        "no_recovery"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "Integer register digest generation encodes leading and trailing zero/one counts using sign_match, saturate_63, wrap_64, or zero_only.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How are leading and trailing zero/one counts that reach 64 or differences between zero and one counts encoded in the 6-bit digest fields for integer registers?",
      "enum_candidates":
... [truncated]

[Usage]
{"input_tokens": 27999, "output_tokens": 26068, "thinking_tokens": 22965, "cache_read_tokens": 0, "total_tokens": 54067}

[Result]
status=SUCCESS conversation=a22ae291-7776-47f5-b393-fd12a739d5a7 turns=1 duration=132.476084s usage={"input_tokens": 27999, "output_tokens": 26068, "thinking_tokens": 22965, "cache_read_tokens": 0, "total_tokens": 54067}


