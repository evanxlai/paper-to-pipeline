success: True
usage: {'input_tokens': 30023, 'output_tokens': 34426, 'thinking_tokens': 28504, 'cache_read_tokens': 0, 'total_tokens': 64449}

## result
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature enhances the Statistical Corrector in TAGE-SC-L by exploiting correlations between branch directions and backend register values using 12-bit digests of 65 logical registers across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "This passage directly establishes that sR captures register value correlations via short digests integrated into the SC of TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A Tomasulo-like architectural register status table tracks registers with a valid bit and a payload holding either a 14-bit ROB tag or a 12-bit digest that decays after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The quote defines the Tomasulo-like table tracking registers with valid bits, 14-bit ROB tags, and 12-bit digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Each bank's prediction weight sum is scaled by x2.5 or gated to x0 and accumulated across 8 banks into sR, which corrects subsequent branches starting with the second one after a flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper explicitly states that the mechanism corrects subsequent mispredictions starting with the second branch after a misprediction flush."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/source",
      "claim": "The source paper is RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables published at CBP 2025.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Toru Koizumi, Toshiki Maekawa, Masanari Mizuno, Maru Kuroki, Tomoaki Tsumura, and Ryota Shioya. 2025. RUNLTS: Register-value-aware Predictor Utilizing Nested Large Tables. In Proceedings of the 6th Championship Branch Prediction (CBP 2025), in conjunction with ISCA 2025, June 21, 2025, Tokyo, Japan, pp. 1-6.",
        "why": "This citation matches the paper metadata and publication venue exactly."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires writeback register values and types (INT, FP, FLAG) to generate 12-bit digests upon instruction completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "This confirms the interface need for completed register writeback values and formats to generate digests and set valid bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires decode-time register destination allocation and ROB tag assignment.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit.",
        "why": "This directly confirms the requirement for decode-time register destination and ROB tag signals from the frontend."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The predictor requires tracking decoded instruction count to invalidate register digests after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "This confirms the interface need to track decoded instructions for digest invalidation."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/host_interfaces",
      "claim": "The pipeline interface requires squash and flush handling for recovering in-flight tags in the register status table.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The authors identify recovering the Tomasulo-like table on squashes as an interface and pipeline integration challenge."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/resource_accounting",
      "claim": "The sR component consumes 53,863 bits (1,495 bits status table + 43,008 bits WT + 9,360 bits UT).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 in the paper details the exact breakdown of WT, UT, auxiliary status table storage, and total 53,863 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/8",
      "claim": "Leading zero/one count handling for 64-bit values in integer registers has semantic ambiguity explored via tuning variants.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper specifies encoding leading zeros or ones in a 6-bit field without detailing saturation or zero/one selection, justifying the tuning parameter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/9",
      "claim": "Trailing zero/one count handling for integer registers has semantic ambiguity explored via tuning variants.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper does not detail trailing zero/one selection and saturation bounds in 6 bits, justifying this tuning parameter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/10",
      "claim": "Floating-point format classification from register MSBs has unspecified classification rules explored via tuning variants.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The paper describes inspecting MSBs to classify the floating-point format without giving the classification bit pattern, justifying this tuning parameter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/11",
      "claim": "Bank usefulness update condition explores tuning options for training the usefulness weight tables.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time. If several registers were available within the same bank, it randomly selects one of them for the update.",
        "why": "The paper does not specify the exact direction or accuracy predicate gating usefulness updates, justifying this search dimension."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/12",
      "claim": "Recovery policy for Tomasulo-like table entries on branch misprediction squashes explores tuning options.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Integrating the path for sending register digests from the execution unit to the predictor and recovering the Tomasulo-like table may present some challenges; we plan to address these in future work.",
        "why": "The paper explicitly leaves recovery of the status table on squash to future work, making squash handling policies tuning candidates."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/13",
      "claim": "Prediction weight table update gating condition explores tuning options for training WT entries.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "During training, we update the correlations only for logical registers that were available at prediction time.",
        "why": "The paper omits the specific SC linear sum threshold or misprediction condition under which WT weights train, justifying this parameter."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0",
      "claim": "Digest generation triggers at instruction execution writeback or completion time.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The trigger corresponds directly to instruction completion when register values become available."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "Helper functions count_leading_zeros_or_ones and count_trailing_zeros_or_ones are called without being defined in the specification.",
      "verdict": "UNDERSPECIFIED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The paper requires counts of leading and trailing zeros or ones, but the spec's pseudocode calls these helper functions without defining their implementation."
      },
      "patch": {
        "op": "replace",
        "pointer": "/algorithms/0/pseudocode",
        "value": "function count_trailing_zeros_or_ones(val_64bit):\n  lsb = val_64bit & 1\n  cnt = 0\n  for i from 0 to 63:\n    if ((val_64bit >> i) & 1) == lsb:\n      cnt = cnt + 1\n    else:\n      break\n  res = cnt & 0x3F\n  return res\n\nfunction count_leading_zeros_or_ones(val_64bit):\n  msb = (val_64bit >> 63) & 1\n  cnt = 0\n  for i from 63 down to 0:\n    if ((val_64bit >> i) & 1) == msb:\n      cnt = cnt + 1\n    else:\n      break\n  res = cnt & 0x3F\n  return res\n\nfunction generate_digest(reg_type, val_64bit, fp_format = null):\n  if reg_type == INT:\n    trailing_cnt = count_trailing_zeros_or_ones(val_64bit) & 0x3F // 6 bits [5:0]\n    leading_cnt  = count_leading_zeros_or_ones(val_64bit) & 0x3F  // 6 bits [8:3]\n    lsb_6        = val_64bit & 0x3F                               // 6 bits [11:6]\n    digest = trailing_cnt ^ (leading_cnt << 3) ^ (lsb_6 << 6)\n    res = digest & 0xFFF // 12-bit digest\n    return res\n  else if reg_type == FP:\n    // format classified from MSBs if not explicitly supplied\n    if fp_format == null:\n      if (val_64bit >> 16) == 0xFFFFFFFFFFFF:\n        fp_format = FP16\n      else if (val_64bit >> 32) == 0xFFFFFFFF or (val_64bit >> 32) == 0:\n        fp_format = FP32\n      else:\n        fp_format = FP64\n    if fp_format == FP16:\n      res = ((val_64bit >> 13) & 0x7) << 3 // bits [5:3]\n      return res\n    else if fp_format == FP32:\n      res = ((val_64bit >> 26) & 0x3F) << 3 // bits [8:3]\n      return res\n    else if fp_format == FP64:\n      res = ((val_64bit >> 55) & 0x1FF) << 3 // bits [11:3]\n      return res\n  else if reg_type == FLAG:\n    flag_4bit = val_64bit & 0xF\n    res = (flag_4bit << 8) | (flag_4bit << 4) | flag_4bit // replicate 3 times: [11:8], [7:4], [3:0]\n    return res\n  return 0"
      },
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/0/pseudocode",
      "claim": "The pseudocode uses the built-in language control statement 'return' rather than invoking an undefined external helper function named 'return(...)'.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The keyword 'return' is the standard control-flow primitive of the pseudocode to produce the generated digest, and the finding was a false positive caused by parentheses around the return expression."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/0",
      "claim": "The register status digest table has 65 entries partitioned into 8 banks, with each entry containing a 1-bit valid flag, 14-bit payload, and 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 auxiliary data specifies 65 entries each with valid (1), payload (14), and decay_ctr (8)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/1",
      "claim": "The prediction weight tables (WT) consist of 8 banks with 3 sub-tables per bank of 512, 256, and 128 entries containing 6-bit weights.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives the WT entry counts 2^9 (512), 2^8 (256), and 2^7 (128) per bank with 6-bit weights across 8 banks totaling 43,008 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2",
      "claim": "The usefulness weight tables (UT) consist of 3 tables of 8 entries each, where each entry stores 6-bit weights for all 65 registers.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "sR: Register                     | 6 x (2^7 + 2^8 + 2^9) x 8                        | 6 x 65 x (2^3 + 2^3 + 2^3)    | { valid (1), payload (14), decay_ctr (8) } x 65 | 53863",
        "why": "Table 3 gives UT structure as 6 bits x 65 registers x (2^3 + 2^3 + 2^3) = 9,360 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/1",
      "claim": "num_logical_registers defaults to 65 logical registers across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "This component is organized into eight banks, each corresponding to eight or nine logical registers.",
        "why": "Seven banks with 8 registers plus one bank with 9 registers establish the 65 logical registers tracked."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/3",
      "claim": "digest_width defaults to 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly specifies 12 bits as the digest width."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "Integer register digest generation correctly XOR-folds trailing count, leading count, and low 6 bits into a 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "The test expectation matches the XOR-folding of trailing count, leading count shifted by 3, and low 6 bits shifted by 6."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "Condition code register digest replicates the 4-bit flag three times across all 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The test replicates 4-bit flag value 0xB three times to yield 0xBBB, directly matching the paper's specification."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "FP32 register digest extracts sign and high exponent bits Value[31:26] aligned at digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "The test verifies extracting Value[31:26] placed at digest bits [8:3], matching the format shown in Figure 6(b)."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest decays and is invalidated on the 256th decoded instruction following its write.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The test validates that the valid bit resets to 0 after exactly 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "A bank selects the available register with highest usefulness and scales its prediction sum by x2.5 when usefulness is positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test checks selection of the most useful register and application of the bank's x2.5 multiplier."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "When maximum usefulness within a bank is non-positive, the bank contribution is suppressed by multiplier x0.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Unlike the existing components, this component picks the digest of the most useful register among those available and forwards it to the second table.",
        "why": "The test checks gating bank contributions to 0 via the x0 branch of the multiplier when usefulness is negative."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/6",
      "claim": "Completed register values from in-flight instructions before pipeline flush become available to predict subsequent branches starting with the second one.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The test validates that instructions completed prior to flush completion retain valid digests for subsequent branch predictions."
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
model=gemini-3.8-flash-medium conversation=c2660fc4-93c1-43e4-8eb8-bfed3ef7984a cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_9c84d392000a3168

[Response]
```json
{
  "records": [
    {
      "pointer": "/summary",
      "claim": "The sr feature enhances the Statistical Corrector in TAGE-SC-L by exploiting correlations between branch directions and backend register values using 12-bit digests of 65 logical registers across 8 banks.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Our method generates a short digest characterizing each register value and improves prediction accuracy by capturing correlations between these digests and branch directions. We implemented this method by integrating it into the statistical corrector (SC) of the existing TAGE-SC-L predictor.",
        "why": "This passage directly establishes that sR captures register value correlations via short digests integrated into the SC of TAGE-SC-L."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "A Tomasulo-like architectural register status table tracks registers with a valid bit and a payload holding either a 14-bit ROB tag or a 12-bit digest that decays after 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "To keep track of which logical registers hold a valid digest at prediction time, RUNLTS adopts a method similar to Tomasulo's algorithm. We use a dedicated table that contains one entry per logical register. Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "The quote defines the Tomasulo-like table tracking registers with valid bits, 14-bit ROB tags, and 12-bit digests."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/summary",
      "claim": "Each bank's prediction weight sum is scaled by x2.5 or gated to x0 and accumulated across 8 banks into sR, which corrects subsequent branches starting with the second one after a flush.",
      "verd
... [truncated]

[Usage]
{"input_tokens": 30023, "output_tokens": 34426, "thinking_tokens": 28504, "cache_read_tokens": 0, "total_tokens": 64449}

[Result]
status=SUCCESS conversation=c2660fc4-93c1-43e4-8eb8-bfed3ef7984a turns=1 duration=172.034284283s usage={"input_tokens": 30023, "output_tokens": 34426, "thinking_tokens": 28504, "cache_read_tokens": 0, "total_tokens": 64449}


