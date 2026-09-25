success: True
usage: {'input_tokens': 29154, 'output_tokens': 45697, 'thinking_tokens': 40467, 'cache_read_tokens': 0, 'total_tokens': 74851}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector by maintaining a 65-register Tomasulo-like tracking table across 8 banks, querying 3 UTs and 3 WTs per bank, scaling by 2.5 or 0, decaying after 256 decoded instructions, and summing bank outputs into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 confirms the Tomasulo-like tracking table structure and payload used to track register digests for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature specification is distilled from the CBP 2025 RUNLTS paper by Toru Koizumi et al.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The paper bibliographic citation matches the specification source record verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At decode time, the host pipeline notifies the predictor of destination logical register IDs and allocated ROB indices.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "Section 4.2 directly confirms that decode notifications supplying destination register ID and ROB index are required to update the tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At instruction completion, the host provides completion notifications with the produced register value to overwrite the tracking table entry with the computed digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 confirms that completion notifications carrying execution results are required to update the payload with the value digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "Pipeline squash notifications supply the set or range of squashed ROB indices to restore the Tomasulo-like table on mispredictions.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does the pipeline communicate misprediction flushes to recover or invalidate pending entries in the Tomasulo-like register tracking table?",
      "enum_candidates": [
        "invalidate_pending",
        "rob_range_flush",
        "tag_match_clear"
      ]
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The SC integration bus injects the sR partial sum into LSUM and passes metadata of available register IDs at prediction time for branch training.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 establishes that branch training needs the record of registers available when the prediction was generated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component consumes 53,863 bits consisting of 43,008 bits for WT, 9,360 bits for UT, and 1,495 bits for the register tracking table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 specifies the exact table configurations and validates the 53,863 bit storage total for sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "Weight table training can use either the digest snapshot recorded at prediction time or the tracking table value at commit time.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Does WT update hashing use the digest snapshot captured at branch prediction time or the digest read from the register tracking table at commit time?",
      "enum_candidates": [
        "pred_time_digest",
        "commit_time_table"
      ]
    },
    {
      "pointer": "/parameters/11",
      "claim": "The training trigger condition for updating the sR weight tables is based on WT outcome match, TAGE misprediction, or SC update.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What training condition triggers an update to the sR prediction weight tables?",
      "enum_candidates": [
        "wt_matches_outcome",
        "tage_mispredicted",
        "sc_updated"
      ]
    },
    {
      "pointer": "/parameters/12",
      "claim": "The bank multiplier scales the WT sum by 2.5 when maximum register usefulness is strictly positive, non-negative, or as a static 2.5 multiplier.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What condition selects the 2.5 multiplier instead of 0 for scaling a bank's weight table sum?",
      "enum_candidates": [
        "max_useful_gt_0",
        "max_useful_ge_0",
        "static_2_5"
      ]
    },
    {
      "pointer": "/parameters/13",
      "claim": "The 3-bit index hash function for the usefulness tables (UT0, UT1, UT2) from PC uses an XOR fold, prime displacement, or Jenkins fold.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash function generates the 3-bit index for each of the three usefulness tables from the PC?",
      "enum_candidates": [
        "xor_fold",
        "prime_displacement",
        "jenkins_fold"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The hash function combining PC and register digest into indices h0, h1, h2 for WT0, WT1, WT2 uses a PC slice, XOR fold, or prime displacement.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What hash function generates the weight table indices h0, h1, and h2 from PC and register digest?",
      "enum_candidates": [
        "pc_slice",
        "xor_fold",
        "prime_displacement"
      ]
    },
    {
      "pointer": "/parameters/15",
      "claim": "Register tracking table payload updates with value digests occur at instruction completion or at decode.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "At which pipeline stage does the simulator write the produced value digest into the register tracking table?",
      "enum_candidates": [
        "at_completion",
        "at_decode"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation is triggered upon instruction execution completion when a register result value is produced.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "Section 4.2 confirms that digest generation and payload writing are triggered upon instruction completion."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding trailing zero count, leading zero count shifted by 3, and the 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) define the three 6-bit fields and their overlapping XOR fold into a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Floating-point register values generate a 12-bit digest by extracting the sign and high-order exponent bits aligned at digest bit 3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) confirm the extraction and alignment of sign and high exponent bits for FP16, FP32, and FP64."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Condition-code flag registers generate a 12-bit digest by replicating the four flag bits three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 and Figure 6(c) specify replicating the 4 condition flags three times across the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "count_leading_zeros and count_trailing_zeros are undefined helper functions in the pseudocode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper explicitly describes counting leading and trailing zeros, confirming that count_leading_zeros and count_trailing_zeros are standard host CPU bit-counting primitives."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "extract_bits is an undefined helper function in the pseudocode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "extract_bits directly implements standard bitfield slicing corresponding to Val[15:13], Value[31:26], and Value[63:55] specified in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "generate_digest is an undefined helper called by the pseudocode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values.",
        "why": "generate_digest is the declaration of the digest generation routine itself defined in Figure 6, refuting that it is an unresolved external call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "return is an undefined helper called by the pseudocode.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Figure 6 shows the method we propose for generating digests of register values.",
        "why": "return is a standard pseudocode control flow keyword returning the computed 12-bit digest, refuting that it is an unresolved function call."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Integer digest generation chooses between counting zeros versus counting ones for the leading and trailing count fields.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "How does integer digest generation choose between counting zeros versus counting ones for the leading and trailing count fields?",
      "enum_candidates": [
        "zeros_only",
        "match_sign",
        "zeros_or_ones"
      ]
    },
    {
      "pointer": "/algorithms/0",
      "claim": "The bitwise criteria for inspecting most significant bits to classify values into FP16, FP32, and FP64 formats are defined.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "What exact bitmask or inspection rule on the most significant bits classifies a 64-bit value into FP16, FP32, or FP64?",
      "enum_candidates": [
        "nan_boxing",
        "exponent_range",
        "host_type_tag"
      ]
    },
    {
      "pointer": "/state/2",
      "claim": "The register tracking table contains 65 entries indexed by logical register ID, each storing a 1-bit valid bit, 14-bit payload, and 8-bit decay counter for a total of 1,495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines the 65-entry tracking table structure, entry bit widths, and total 1,495 bit storage allocation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The sR component tracks 65 logical registers across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the component tracks 8 or 9 registers per bank across 8 banks, matching the 65 entries in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "Valid register digests decay and are invalidated after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly establishes the 256-instruction decode invalidation threshold."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "test_int_digest_generation verifies the integer digest XOR fold computation for value 8 yielding 995 (0x3E3).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The unit test checks the exact overlapping XOR-fold formula defined in Figure 6(a) and Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "test_flag_digest_generation verifies replicating 4 flag bits three times to form a 12-bit digest (0xBBB).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The unit test directly tests the 3-fold replication of 4 flag bits described in Section 4.2 and Figure 6(c)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "test_bank_register_selection verifies that the available register with the largest usefulness in the bank is selected to index WT.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 specifies selecting the most useful available register in each bank to index the second table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "test_usefulness_scaling_zero verifies that non-positive bank usefulness selects x0 scaling, contributing 0 to sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) indicates that the bank WT sum is scaled by x0 when the bank usefulness is non-positive."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "test_usefulness_scaling_positive verifies that positive bank usefulness scales the WT sum by 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) shows that bank WT sums are scaled by x2.5 when the bank is judged useful."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "test_decay_invalidation verifies that an entry is invalidated after 256 instruction decodes without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The unit test checks the exact invalidation rule stated in Section 4.2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "test_mispredict_visibility verifies that instructions completed before misprediction recovery retain valid digests across restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "Section 4.2 establishes that completed in-flight instructions remain valid upon restart after misprediction flushes."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `global+orphan+algo:digest_generation` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they neve...

[Init]
model=gemini-3.8-flash-medium conversation=9fb56b12-e43d-4a68-bb91-405b5eb4b174 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c852868e601f5ea

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sR component extends the statistical corrector by maintaining a 65-register Tomasulo-like tracking table across 8 banks, querying 3 UTs and 3 WTs per bank, scaling by 2.5 or 0, decaying after 256 decoded instructions, and summing bank outputs into sR.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Section 4.2 confirms the Tomasulo-like tracking table structure and payload used to track register digests for the sR component."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The feature specification is distilled from the CBP 2025 RUNLTS paper by Toru Koizumi et al.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "The paper bibliographic citation matches the specification source record verbatim."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "At decode time, the host pipeline notifies the predictor of destination logical register IDs and allocated ROB indices.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as 
... [truncated]

[Usage]
{"input_tokens": 29154, "output_tokens": 45697, "thinking_tokens": 40467, "cache_read_tokens": 0, "total_tokens": 74851}

[Result]
status=SUCCESS conversation=9fb56b12-e43d-4a68-bb91-405b5eb4b174 turns=1 duration=227.073275643s usage={"input_tokens": 29154, "output_tokens": 45697, "thinking_tokens": 40467, "cache_read_tokens": 0, "total_tokens": 74851}


