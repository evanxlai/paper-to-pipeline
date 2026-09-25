success: True
usage: {'input_tokens': 28195, 'output_tokens': 35677, 'thinking_tokens': 29442, 'cache_read_tokens': 0, 'total_tokens': 63872}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm is triggered at branch prediction lookup time in the fetch/frontend stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "It confirms that register digests are queried and forwarded to SC register components at branch prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Predict iterates over 8 banks of register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "It directly states that the register component is divided into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Logical registers R0 through R64 are assigned to banks via a stride-8 mapping (bank b contains registers where r mod 8 == b).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input row \"9 regs digest\" listing \"R0  R8  R16  ...  R64\".",
        "why": "It explicitly demonstrates that bank 0 maps registers R0, R8, R16 up to R64 in stride-8 order."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Only registers whose valid bit is set in sR_RegStatus forward digests and participate in bank evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "It confirms that validity in the Tomasulo-like register status table gates forwarding to prediction components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The pseudocode accesses sR_UT tables directly inline and does not invoke an undefined helper function 'useful(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "It establishes that usefulness weights are retrieved directly from the three tables UT0, UT1, UT2 and summed, refuting the deterministic finding."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Usefulness for available registers in a bank is computed by summing outputs from three usefulness tables and picking the register with the largest usefulness.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That vector feeds a block labelled \"largest\", whose output is labelled \"Most useful in this bank.\"",
        "why": "It shows that the summed usefulness vector feeds the 'largest' block to select the most useful register in that bank."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "A bank's WT weight sum is scaled by 2.5 if its usefulness is positive, and suppressed to 0 otherwise.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "It shows that each bank's WT summation output feeds a per-bank multiplier of x0 or x2.5."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The UT table index functions hash_u0, hash_u1, and hash_u2 compute entries from PC.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "The paper notes that the UT tables take skewed PC inputs, but does not specify the mathematical hashing or skewing functions."
      },
      "patch": null,
      "open_question": "What specific hash/skew functions map PC to the 8-entry indices of UT0, UT1, and UT2?",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "bit_slice"
      ]
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "The WT table index functions hash0, hash1, and hash2 compute entries from PC and the 12-bit register digest.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "The paper indicates that PC and register digest are hashed into h0, h1, h2, but does not specify the hash expressions."
      },
      "patch": null,
      "open_question": "What specific hashing functions combine PC and the 12-bit register digest to index WT0 (512 entries), WT1 (256 entries), and WT2 (128 entries)?",
      "enum_candidates": [
        "xor_fold",
        "shift_xor",
        "prime_modulo"
      ]
    },
    {
      "pointer": "/algorithms/3/notes",
      "claim": "The sum sR is added directly to LSUM in the SC summation tree.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Inputs \"sB, sG, sP, sC, sI, sL, sS, sT, sR\" into a Sigma producing \"LSUM\".",
        "why": "It confirms that sR enters the summation node that produces LSUM alongside the other SC components."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/organization",
      "claim": "sR_WT is organized into 8 banks, each containing three direct-mapped weight tables of 512, 256, and 128 entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "It confirms that each bank contains WT0 with 512 entries, WT1 with 256 entries, and WT2 with 128 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/entry_format",
      "claim": "Each sR_WT entry is a signed 6-bit weight counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "The WT entry width is explicitly listed as 6 bits in the storage breakdown."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/size_bits",
      "claim": "Total storage capacity of sR_WT across all 8 banks is 43008 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "WT: 6 bits x (2^7 + 2^8 + 2^9) x 8 banks = 6 x (128+256+512) x 8 = 43008 bits",
        "why": "The total WT bit budget calculation matches 43008 bits exactly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0/indexing",
      "claim": "Within each bank, WT tables are indexed by hashing PC with the selected 12-bit register digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Selected digest plus PC form the input labelled \"PC + reg. digest\", hashed into \"h0\", \"h1\", \"h2\".",
        "why": "It states that the index inputs to WT0, WT1, and WT2 are hashes of PC combined with the selected register digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/organization",
      "claim": "sR_UT consists of 8 banks with three 8-entry direct-mapped usefulness tables per bank, storing vectors of 6-bit usefulness weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "It confirms that each bank contains three 8-entry usefulness tables storing 6-bit weight vectors."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/entry_format",
      "claim": "sR_UT stores 9 weights per entry in Bank 0 and 8 weights per entry in Banks 1 through 7.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry of the first table holds an eight- (or nine-) element vector of weights reflecting the usefulness of each register.",
        "why": "It explicitly states the vector lengths of eight or nine elements per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/size_bits",
      "claim": "The total storage cost of sR_UT is 9360 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "UT: 6 bits x 65 regs x (2^3 + 2^3 + 2^3) = 9360 bits",
        "why": "It verifies the total bit count of the sR_UT tables across all 65 logical registers and 3 tables of 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1/indexing",
      "claim": "sR_UT tables are directly indexed by PC hashes/skews.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input \"PC (skewed)\".",
        "why": "It confirms that the usefulness tables UT0, UT1, and UT2 are addressed by skewed PC values."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus contains 65 flat entries, one for each logical register R0 to R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "It confirms the flat table contains an entry for every logical register (totaling 65 registers)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each entry of sR_RegStatus contains a 1-bit valid flag, a 14-bit payload, and an 8-bit decay counter initialized to 256.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 auxiliary data explicitly defines the entry structure as { valid (1), payload (14), decay_ctr (8) }."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "The total size of sR_RegStatus is 1495 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Evaluating (1 + 14 + 8) * 65 equals exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "sR_RegStatus is directly indexed by architectural/logical register ID (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "It specifies that each entry corresponds directly to a logical register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The default useful_multiplier scaling factor for a useful bank is 2.5.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) specifies 2.5 as the scaling factor applied to useful banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "The tuning range for useful_multiplier is [1.0, 4.0] step 0.5.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "The paper hard-codes the multiplier value as 2.5 and never defines an exploration range."
      },
      "patch": null,
      "open_question": "The paper fixes useful_multiplier to 2.5 in Figure 5(c); the tuning range [1.0, 4.0] step 0.5 is not specified in the paper and needs confirmation as a search dimension.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The default num_banks parameter is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "It explicitly states that the register component has eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/2",
      "claim": "The tuning range for num_banks is [4, 16] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "The paper does not explore alternative bank counts; the tuning range is unsourced."
      },
      "patch": null,
      "open_question": "The paper uses an 8-bank organization; the tuning range [4, 16] pow2 is unsourced and should be verified as a valid search space.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The default wt_entries per bank configuration is 512, 256, 128.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three prediction weight tables: \"512 ent. WT0\", \"256 ent. WT1\", \"128 ent. WT2\".",
        "why": "Figure 5(c) explicitly gives the entries of WT0, WT1, and WT2 as 512, 256, and 128."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "The parameter wt_entries has tuning choices 256,128,64 | 512,256,128 | 1024,512,256.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "The paper designs RUNLTS with fixed table sizes of 128, 256, and 512 entries and does not propose alternative entry size combinations."
      },
      "patch": null,
      "open_question": "The paper defines only 512, 256, and 128 entries per bank; alternative configuration choices are not discussed in the text.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The default ut_entries_per_table parameter is 8.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "Figure 5(c) states that each usefulness table has 8 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/4",
      "claim": "The tuning range for ut_entries_per_table is [4, 32] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Three usefulness tables: \"9x6bit 8 ent. UT0\", \"8 ent. UT1\", \"8 ent. UT2\".",
        "why": "The paper specifies 8 entries per table without mentioning an exploration range."
      },
      "patch": null,
      "open_question": "The paper specifies exactly 8 entries per UT table; the parameter exploration range [4, 32] is not established in the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The default digest_width_bits is 12.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "Section 4.2 states that RUNLTS generates a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6",
      "claim": "The tuning range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The digest width is fixed at 12 bits throughout the paper, with no exploration range mentioned."
      },
      "patch": null,
      "open_question": "The paper fixes the register digest width to 12 bits; the tuning range [8, 16] is unsourced.",
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "An integer register digest is computed by XOR-folding a 6-bit trailing count, 6-bit leading count shifted by 3, and 6 LSBs shifted by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and Section 4.2 establish the 12-bit digest structure as XOR-folded trailing count at [5:0], leading count at [8:3], and Value[5:0] at [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "A condition-code flag register digest is computed by replicating the 4 flag bits three times to fill the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "It confirms that 4 flag bits are replicated three times to create the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "An FP32 register digest extracts Value[31:26] and maps it to digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "\"For FP32\"  ->  Value[31:26]",
        "why": "Figure 6(b) specifies that FP32 registers extract bits [31:26] occupying digest positions 8 through 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A register digest is invalidated after 256 subsequent instructions are decoded without further writes to that register.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "It states directly that each digest is invalidated after 256 subsequent decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank with non-positive usefulness outputs 0, while a bank with positive usefulness outputs floor(WT_sum * 2.5).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "It confirms that bank weight contributions are either scaled by 2.5 when useful or suppressed by 0."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Upon pipeline flush recovery following a branch misprediction, digests produced by instructions that completed writeback remain valid for subsequent predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "It establishes that instructions completed before the flush retain their produced values to aid subsequent predictions upon restart."
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
model=gemini-3.8-flash-medium conversation=cab6484a-2c7a-481b-a721-695d1e333b22 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/3/trigger",
      "claim": "The predict algorithm is triggered at branch prediction lookup time in the fetch/frontend stage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "It confirms that register digests are queried and forwarded to SC register components at branch prediction time."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Predict iterates over 8 banks of register components.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "It directly states that the register component is divided into eight banks."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Logical registers R0 through R64 are assigned to banks via a stride-8 mapping (bank b contains registers where r mod 8 == b).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Input row \"9 regs digest\" listing \"R0  R8  R16  ...  R64\".",
        "why": "It explicitly demonstrates that bank 0 maps registers R0, R8, R16 up to R64 in stride-8 order."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/3/pseudocode",
      "claim": "Only registers whose valid bit is set in sR_RegStatus forward digests and participate in bank evaluation.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Whenever the branch predictor queries the table, any entry whose valid bit is set forwards it
... [truncated]

[Usage]
{"input_tokens": 28195, "output_tokens": 35677, "thinking_tokens": 29442, "cache_read_tokens": 0, "total_tokens": 63872}

[Result]
status=SUCCESS conversation=cab6484a-2c7a-481b-a721-695d1e333b22 turns=1 duration=166.372559292s usage={"input_tokens": 28195, "output_tokens": 35677, "thinking_tokens": 29442, "cache_read_tokens": 0, "total_tokens": 63872}


