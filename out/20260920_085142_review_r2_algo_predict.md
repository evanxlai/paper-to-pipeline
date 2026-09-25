success: True
usage: {'input_tokens': 28193, 'output_tokens': 41795, 'thinking_tokens': 37737, 'cache_read_tokens': 0, 'total_tokens': 69988}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm is triggered at branch prediction lookup time in fetch/frontend and accesses available register digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 confirms that the register components are queried at branch prediction time using any available valid register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The register component partitions logical registers R0 through R64 across 8 banks using register ID modulo 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the register component has eight banks mapping eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In each bank, the predict algorithm identifies available registers by checking whether sR_RegStatus[r].valid is 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 states that only entries whose valid bit is set forward their digests to the predictor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict algorithm selects the register with the highest usefulness sum across the three usefulness tables (UT0, UT1, UT2) among available registers in each bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 explicitly specifies that the component picks the digest of the most useful register among those available in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Register usefulness is evaluated inline from three 8-entry UT tables per bank without calling an external helper function named useful(...).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Section 4.2 defines usefulness as weights stored directly in vectors within table entries, which the pseudocode sums directly without external helper calls."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Each bank scales its weight table sum by 2.5 when deemed useful (max_useful > 0) and suppresses output to 0 when not useful.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) shows that each bank's weight table sum passes through a per-bank multiplier stage selecting x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The hash functions hash_u0, hash_u1, hash_u2 for UT and hash0, hash1, hash2 for WT compute index addresses from PC and register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not define the bit-level hash and skew functions (hash_u0, hash_u1, hash_u2, hash0, hash1, hash2) for indexing UT and WT tables from the PC and digest.",
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "The scaled outputs of all banks are summed together to form sR, which is added directly to LSUM in the SC summation tree.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs 'sB, sG, sP, sC, sI, sL, sS, sT, sR' into a Sigma producing 'LSUM'.",
        "why": "Figure 5(d) shows that sR is an input alongside the other SC components into the final summation producing LSUM."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "sR_WT consists of 8 banks, each containing three weight tables with 512 (WT0), 256 (WT1), and 128 (WT2) entries of 6-bit saturating signed counters, totalling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 defines the WT configuration as 8 banks of three tables with 2^7, 2^8, and 2^9 entries of 6-bit weights, giving 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "sR_UT consists of 8 banks with three 8-entry tables (UT0, UT1, UT2) storing 6-bit usefulness weights for each assigned logical register, totalling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the UT storage formula multiplying 6 bits by 65 registers across three 2^3-entry tables, totalling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "sR_RegStatus is a 65-entry table where each entry comprises a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter, totalling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 defines sR auxiliary data as 65 entries of 1-bit valid, 14-bit payload, and 8-bit decay counter, totalling 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default value of useful_multiplier is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) establishes the active scaling multiplier factor as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "useful_multiplier has an exploration tuning range of [1.0, 4.0] with step 0.5.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper evaluates only the fixed design multiplier of 2.5 and does not specify a parameter tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "num_banks has a default value of 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 specifies that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "num_banks has an exploration tuning range of [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the architecture to eight banks and does not specify a legal tuning range for the number of banks.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt_entries has a default value of '512,256,128'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies table entry counts of 2^9 (512), 2^8 (256), and 2^7 (128) per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "wt_entries has a tuning range of choices '256,128,64 | 512,256,128 | 1024,512,256'.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not define alternative table size choices for WT0, WT1, and WT2 beyond 512, 256, and 128.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_table has a default value of 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines the three UT tables as each having 2^3 (8) entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "ut_entries_per_table has an exploration tuning range of [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper does not specify a parameter tuning range for UT table entry counts.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "digest_width_bits has a default value of 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 explicitly establishes 12 bits as the digest width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "digest_width_bits has an exploration tuning range of [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper fixes the register digest width to 12 bits and does not define a tuning range.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register values generate a 12-bit digest by XOR-folding trailing zero/one count at [5:0], leading zero/one count at [8:3], and value LSBs [5:0] at [11:6].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 states that integer digests encode leading counts, trailing counts, and six LSBs in the overlapping bit positions shown in Figure 6(a)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition-code flag values generate a 12-bit digest by replicating the 4-bit value three times.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly specifies that condition-code flag digests replicate the four flag bits three times."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 register values generate a digest by extracting bits [31:26] and positioning them at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) define FP32 digest extraction as extracting bits [31:26] and aligning them to digest bits [8:3]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly states that digests are invalidated after 256 subsequent instructions have decoded."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness multiplies WT output by 0, while a useful bank multiplies by 2.5, and results sum across banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled 'x0 or x2.5'.",
        "why": "Figure 5(c) specifies the per-bank multiplier selecting between x0 and x2.5 depending on usefulness."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Register digests written by instructions completed before pipeline flush recovery remain valid for subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "Section 4.2 confirms that values produced by completed in-flight instructions before the branch resolution remain valid across the pipeline flush."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A clai...

[Init]
model=gemini-3.8-flash-medium conversation=b60b619f-d7bd-44a4-88d3-1dab116f8698 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm is triggered at branch prediction lookup time in fetch/frontend and accesses available register digests.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 confirms that the register components are queried at branch prediction time using any available valid register digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The register component partitions logical registers R0 through R64 across 8 banks using register ID modulo 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 states that the register component has eight banks mapping eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "In each bank, the predict algorithm identifies available registers by checking whether sR_RegStatus[r].valid is 1.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "Section 4.2 states that only entries whose valid bit is set forward their digests to the predictor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The predict algorithm selects the regis
... [truncated]

[Usage]
{"input_tokens": 28193, "output_tokens": 41795, "thinking_tokens": 37737, "cache_read_tokens": 0, "total_tokens": 69988}

[Result]
status=SUCCESS conversation=b60b619f-d7bd-44a4-88d3-1dab116f8698 turns=1 duration=287.593725461s usage={"input_tokens": 28193, "output_tokens": 41795, "thinking_tokens": 37737, "cache_read_tokens": 0, "total_tokens": 69988}


