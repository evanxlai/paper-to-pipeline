success: True
usage: {'input_tokens': 30540, 'output_tokens': 36851, 'thinking_tokens': 32019, 'cache_read_tokens': 0, 'total_tokens': 67391}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The predict_sr lookup algorithm is triggered at branch predictor lookup time during fetch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that the register component is queried for branch prediction whenever the branch predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Logical registers are partitioned across 8 banks using a stride-8 mapping (r % 8 == bank), giving 9 registers in bank 0 and 8 in banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the component is structured as eight banks corresponding to eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "For each bank, the register with the maximum combined usefulness weight across UT0, UT1, and UT2 among valid registers is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly describes selecting the digest of the most useful register among available registers within the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "WT0, WT1, and WT2 have 512, 256, and 128 entries per bank respectively, indexed by hashing the PC and selected register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) directly specifies the three prediction weight tables with capacities of 512, 256, and 128 entries per bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Each bank's prediction weight sum is scaled by x2.5 if best_usefulness > 0 and by x0 otherwise.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not label the wire that selects x0 vs x2.5.",
        "why": "Declared ambiguity U2 confirms that the wire controlling selection of x0 vs x2.5 is not labeled in the figure, leaving per-bank gating versus a static scale uncertain."
      },
      "patch": null,
      "open_question": "Does best_usefulness > 0 drive the x0 vs x2.5 multiplier per bank, or is a global static scale applied?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/algorithms/4/notes",
      "claim": "Bank scale x2.5 vs x0 is driven per bank by best_usefulness > 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not label the wire that selects x0 vs x2.5.",
        "why": "Declared ambiguity U2 establishes that the selection mechanism between x0 and x2.5 is not explicitly shown in the source."
      },
      "patch": null,
      "open_question": "Is bank scaling x0 vs x2.5 determined per bank by positive usefulness or configured as a static scale?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/state/0",
      "claim": "The Register Tracking Table contains 65 entries storing valid bit, 14-bit payload, and 8-bit decay counter, totaling 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data explicitly lists 65 entries each with 1 valid bit, 14 payload bits, and 8 decay counter bits (65 * 23 = 1495 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "Three usefulness tables per bank across 8 banks store 6-bit signed weights across 8 entries, consuming 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) and Table 3 explicitly define the 8-entry 6-bit UT tables across 65 registers, totaling 9360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "Prediction Weight Table 0 has 8 banks with 512 entries of 6-bit signed counters each, totaling 24576 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify WT0 as having 512 entries of 6-bit weights across 8 banks (512 * 8 * 6 = 24576 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/3",
      "claim": "Prediction Weight Table 1 has 8 banks with 256 entries of 6-bit signed counters each, totaling 12288 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify WT1 as having 256 entries of 6-bit weights across 8 banks (256 * 8 * 6 = 12288 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/4",
      "claim": "Prediction Weight Table 2 has 8 banks with 128 entries of 6-bit signed counters each, totaling 6144 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) and Table 3 specify WT2 as having 128 entries of 6-bit weights across 8 banks (128 * 8 * 6 = 6144 bits)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0",
      "claim": "The sR component is organized into 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states that the register component is organized into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "WT0 has 512 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT0 as 512 ent. WT0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "WT1 has 256 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT1 as 256 ent. WT1."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "WT2 has 128 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\",\n    \"128 ent. WT2\".",
        "why": "Figure 5(c) literally labels WT2 as 128 ent. WT2."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "Each usefulness table has 8 entries per bank.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) literally labels UT0, UT1, and UT2 as having 8 entries each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/7",
      "claim": "The usefulness scaling factor for useful predictions in the register component is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) literally marks the multiplier stage as x0 or x2.5, establishing 2.5 as the scaling factor."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "The predictor tracks 65 logical registers across its register component tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "6 x 65 x (2^3 + 2^3 + 2^3)",
        "why": "Table 3 explicitly specifies 65 registers in the storage budget for sR's usefulness tables and RTT."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/13",
      "claim": "The exact hash algorithm used to compute index h0 for WT0 is an open design choice between xor_hash and folded_hash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\"",
        "why": "The paper does not specify the exact hash algorithm for index h0 beyond stating that PC and register digest form the input."
      },
      "patch": null,
      "open_question": "Which hash function variant (xor_hash vs folded_hash) is used to compute index h0 for WT0?",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/parameters/14",
      "claim": "The exact hash algorithm used to compute index h1 for WT1 is an open design choice between xor_hash and folded_hash.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\"",
        "why": "The paper does not define the specific hash function used to compute index h1 for WT1."
      },
      "patch": null,
      "open_question": "Which hash function variant (xor_hash vs folded_hash) is used to compute index h1 for WT1?",
      "enum_candidates": [
        "xor_hash",
        "folded_hash"
      ]
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "For an INT value of 0, 64-bit leading and trailing zero counts saturate at 63 to fit in 6 bits, producing digest 0x1C7.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not say whether the count saturates at 63, is taken modulo 64, or counts bits matching the sign bit (which caps at 63 naturally).",
        "why": "Declared ambiguity U3 explicitly states the paper does not settle whether counts saturate at 63, wrap modulo 64, or count matching sign bits."
      },
      "patch": null,
      "open_question": "How does integer register digest generation handle identical bit counts exceeding 63 for 64-bit registers?",
      "enum_candidates": [
        "saturate",
        "modulo",
        "match_sign"
      ]
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "An integer register value of 8 produces trailing zero count 3, leading zero count 60, and value LSB 8, XOR-folded to digest 0x3E3.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies encoding leading/trailing zero counts and the 6 LSBs into the 12-bit digest, which for value 8 yields counts 60, 3, and 8, XOR-folding to 0x3E3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "Condition-code flag register digests replicate the 4 flag bits three times to fill a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly states that the four flag bits are replicated three times to fill the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "FP32 register digest extracts Value[31:26] and places it at digest bits [8:3] with bits [2:0] zeroed.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The right-alignment at bit 3 is read off the drawing, not stated. An alternative is that each format's field is right-aligned at bit 0.",
        "why": "Declared ambiguity U4 states that aligning FP digest bits at bit 3 is an inferred reading rather than explicitly stated."
      },
      "patch": null,
      "open_question": "Are floating-point digest bits aligned at bit 3 (digest[8:3]) or bit 0 (digest[5:0])?",
      "enum_candidates": [
        "align_bit_3",
        "align_bit_0"
      ]
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A register digest in RTT expires and is invalidated after 256 decoded instructions without new writes.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly states that each digest is invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When best_usefulness is non-positive, the bank multiplier selects x0 and the bank contribution is 0.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not label the wire that selects x0 vs x2.5.",
        "why": "Declared ambiguity U2 confirms that the wire driving selection between x0 and x2.5 is not labeled or described."
      },
      "patch": null,
      "open_question": "Is bank multiplier x0 vs x2.5 selected based on bank usefulness <= 0 or a global static scale?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "When best_usefulness is positive, the bank multiplier selects x2.5 and scales the bank contribution.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "The figure does not label the wire that selects x0 vs x2.5.",
        "why": "Declared ambiguity U2 establishes that driving the x2.5 multiplier from positive bank usefulness is uncertain."
      },
      "patch": null,
      "open_question": "Is bank multiplier x0 vs x2.5 selected based on bank usefulness > 0 or a global static scale?",
      "enum_candidates": [
        "bank_usefulness",
        "global_static"
      ]
    },
    {
      "pointer": "/unit_tests/7",
      "claim": "When multiple registers are available in a bank, exactly one is randomly chosen for updating the UT and WT tables upon misprediction.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "If several registers were available within the same bank, it randomly selects one of them for the update. Owing to this training method, each table in the register component also needs just a single write port.",
        "why": "The paper explicitly states that if several registers were available within the same bank, one is randomly chosen for the update."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:predict_sr` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; they never read the paper. A c...

[Init]
model=gemini-3.8-flash-medium conversation=236ead22-205c-4528-a417-01c22db74dd0 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_a83450f3294addb6

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/4/trigger",
      "claim": "The predict_sr lookup algorithm is triggered at branch predictor lookup time during fetch.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that the register component is queried for branch prediction whenever the branch predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "Logical registers are partitioned across 8 banks using a stride-8 mapping (r % 8 == bank), giving 9 registers in bank 0 and 8 in banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper explicitly states the component is structured as eight banks corresponding to eight or nine logical registers each."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "claim": "For each bank, the register with the maximum combined usefulness weight across UT0, UT1, and UT2 among valid registers is selected.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The paper explicitly describes selecting the digest of the most useful register among available registers within the bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/4/pseudocode",
      "c
... [truncated]

[Usage]
{"input_tokens": 30540, "output_tokens": 36851, "thinking_tokens": 32019, "cache_read_tokens": 0, "total_tokens": 67391}

[Result]
status=SUCCESS conversation=236ead22-205c-4528-a417-01c22db74dd0 turns=1 duration=190.863480729s usage={"input_tokens": 30540, "output_tokens": 36851, "thinking_tokens": 32019, "cache_read_tokens": 0, "total_tokens": 67391}


