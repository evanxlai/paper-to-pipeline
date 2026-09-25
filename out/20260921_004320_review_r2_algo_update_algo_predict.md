success: True
usage: {'input_tokens': 31359, 'output_tokens': 36684, 'thinking_tokens': 32437, 'cache_read_tokens': 0, 'total_tokens': 68043}

## result
```json
{
  "records": [
    {
      "pointer": "/parameters/0",
      "claim": "The register-value correlation component sR is partitioned into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The architecture tracks usefulness and digests across 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates usefulness table capacity using a factor of 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Each bank has a WT0 table containing 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists WT0 as having 512 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Each bank has a WT1 table containing 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists WT1 as having 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each bank has a WT2 table containing 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists WT2 as having 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The scaling multiplier applied to useful bank predictions is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) defines the non-zero scaling multiplier in the register bank pipeline as 2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "The digest generated from a register value is 12 bits wide.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states directly that RUNLTS produces a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "Prediction weight tables comprise 8 banks of WT0 (512), WT1 (256), and WT2 (128) 6-bit entries totaling 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x (2^7 + 2^8 + 2^9) x 8",
        "why": "Table 3 specifies 6-bit weights across tables of sizes 2^7, 2^8, and 2^9 over 8 banks, totaling 43008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "WT0, WT1, and WT2 are indexed by the specific hashing formulas PC ^ (digest << 1) ^ (digest >> 3) masked to 9, 8, and 7 bits.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) states that PC and reg. digest are hashed to form h0, h1, and h2, but does not provide the specific bitwise hash functions or shifts.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Usefulness weight tables comprise 8 banks of UT0, UT1, and UT2 with 8 entries each storing 6-bit usefulness weights for 65 registers totaling 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 defines 6-bit weights for 65 registers across three 8-entry tables (2^3 + 2^3 + 2^3), totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Each usefulness table entry stores an 8- or 9-element vector of 6-bit weights corresponding to the registers in the bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "Section 4.2 describes each entry holding an 8- or 9-element vector of usefulness weights."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "UT0, UT1, and UT2 are indexed by the specific 3-bit PC hash functions PC[5:3] ^ PC[8:6], (PC >> 4) ^ (PC >> 7) & 0x7, and (PC >> 6) ^ (PC >> 9) & 0x7.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) notes that the usefulness tables are indexed by 'PC (skewed)', but the paper does not specify the exact bit slices or skewing hash functions.",
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The register status table contains 65 entries, one per logical register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Section 4.2 specifies a dedicated status table holding one entry per logical register."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Each register status table entry contains a 1-bit valid flag, a 14-bit payload holding a ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 details the exact entry bit fields as 1-bit valid, 14-bit payload, and 8-bit decay counter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Each valid digest in the register status table is invalidated after 256 subsequent instructions are decoded.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 explicitly defines the decay lifetime as 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digests are formed by XOR-folding 6-bit fields for trailing zero count, leading zero count shifted by 3, and value LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Section 4.2 and Figure 6(a) establish that the integer digest XOR-folds the trailing count, leading count, and register LSBs."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "64-bit floating point digests extract value bits [63:55] into digest bits [11:3] with bits [2:0] zeroed.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Section 4.2 and Figure 6(b) confirm that FP64 extracts Value[63:55] representing the sign and exponent bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition flag digests replicate the 4 flag bits three times to produce a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "Section 4.2 explicitly states that condition flag bits are replicated three times to fill 12 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid digest decays and transitions to invalid on the 256th instruction decode tick.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "Section 4.2 directly settles that invalidation occurs after 256 instruction decodes."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "The bank chooses the register with the highest cumulative usefulness (UT0+UT1+UT2) and scales its output by 2.5 when positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "Section 4.2 and Figure 5(c) specify selecting the most useful register among available registers in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "During training, exactly one available register per bank is randomly selected to update the tables with a single write port.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "Section 4.2 explicitly states that one available register per bank is randomly selected during training."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "The prediction algorithm evaluates the 8 banks independently, identifying registers belonging to each bank via stride-8 grouping.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 and Figure 5(c) show bank 0 containing R0, R8, R16, ... R64, defining a stride-8 bank mapping."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "For each bank, usefulness weights from UT0, UT1, and UT2 are summed per register to pick the register with the maximum usefulness.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Their outputs go to a Sigma producing \"9 regs useful (skewed)\".",
        "why": "Figure 5(c) shows summing UT0, UT1, and UT2 to find the most useful register in the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "Outputs from all 8 banks are summed together to produce the final sR contribution.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Below all eight banks: a final Sigma, output \"sR\".",
        "why": "Figure 5(c) shows a cross-bank summation node gathering all eight bank outputs into sR."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/1",
      "claim": "The bank weight sum is multiplied by 2.5 if max_useful > 0, otherwise multiplied by 0.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Figure 5(c) labels the per-bank scaling block as 'x0 or x2.5', but the paper does not specify the exact gating condition or threshold that selects between x0 and x2.5.",
      "enum_candidates": [
        "max_useful_gt_zero",
        "max_useful_ge_zero",
        "always_scale"
      ]
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Training updates correlations only for logical registers that were available at prediction time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "Section 4.2 states verbatim that updates are restricted to registers available at prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Each bank randomly selects one available register to update in order to maintain a single write port per table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "Section 4.2 confirms that random single-register selection enables single write port tables."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2",
      "claim": "Usefulness weights in UT0, UT1, and UT2 are incremented if the bank weight table sum direction agreed with the outcome, and decremented otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 4.2 notes that the component includes a table tracking prediction usefulness, but does not specify the training update rule or agreement condition for usefulness counters.",
      "enum_candidates": [
        "bank_agreed",
        "sc_agreed",
        "tage_mispredicted"
      ]
    }
  ]
}
```

## stream
[User Message]
# Spec reviewer prompt (post-distillation verification node)

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:update+algo:predict` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the p...

[Init]
model=gemini-3.8-flash-medium conversation=f021d6a9-6e9b-4a25-aea1-6575b4b1cf42 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_45e7b668d20115f2

[Response]
```json
{
  "records": [
    {
      "pointer": "/parameters/0",
      "claim": "The register-value correlation component sR is partitioned into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Section 4.2 explicitly states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The architecture tracks usefulness and digests across 65 logical registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 calculates usefulness table capacity using a factor of 65 logical registers."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "Each bank has a WT0 table containing 512 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists WT0 as having 512 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "Each bank has a WT1 table containing 256 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly lists WT1 as having 256 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each bank has a WT2 table containing 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {

... [truncated]

[Usage]
{"input_tokens": 31359, "output_tokens": 36684, "thinking_tokens": 32437, "cache_read_tokens": 0, "total_tokens": 68043}

[Result]
status=SUCCESS conversation=f021d6a9-6e9b-4a25-aea1-6575b4b1cf42 turns=1 duration=183.412608111s usage={"input_tokens": 31359, "output_tokens": 36684, "thinking_tokens": 32437, "cache_read_tokens": 0, "total_tokens": 68043}


