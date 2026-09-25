success: True
usage: {'input_tokens': 28424, 'output_tokens': 34289, 'thinking_tokens': 30325, 'cache_read_tokens': 0, 'total_tokens': 62713}

## result
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The writeback_complete procedure is triggered upon instruction execution writeback / completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload overwrite and valid bit assertion occur when the instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The destination register index is checked against the range of 65 logical registers (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data specifies exactly 65 entries for the register tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "An entry overwrites its payload with the generated 12-bit digest and sets valid to 1 only when valid is 0 and the pending payload matches the completing instruction's 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the Tomasulo-like tag matching protocol where the completing instruction updates the entry containing its ROB tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The decay_ctr field is initialized to the scalar literal value 256 upon writeback completion.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Table 3 defines decay_ctr as an 8-bit field, which cannot hold the literal integer 256 without overflow; the paper specifies invalidation after 256 decoded instructions but does not specify the counter's initial state value or countdown encoding.",
      "enum_candidates": [
        "255",
        "0",
        "wrap_256"
      ]
    },
    {
      "pointer": "/algorithms/2/notes",
      "claim": "When the producer finishes execution, its result digest becomes immediately visible to subsequent branch predictions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit. Whenever the branch predictor queries the table, any entry whose valid bit is set forwards its digest to the register-value components in the SC for prediction.",
        "why": "The paper specifies that completed instructions immediately set valid=1, making their digests available whenever the predictor queries the table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/organization",
      "claim": "sR_RegStatus is a 65-entry flat table with one entry per logical register R0..R64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "The paper states the table contains one entry per logical register, matching the 65 entries in Table 3."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "Each sR_RegStatus entry contains a 1-bit valid flag, a 14-bit payload holding an ROB tag or 12-bit digest, and an 8-bit decay counter.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 explicitly specifies the bit widths for valid, payload, and decay_ctr per entry."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/entry_format",
      "claim": "The 8-bit decay_ctr field is initialized to the integer value 256.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Table 3 fixes decay_ctr at 8 bits (range 0..255); the paper specifies invalidation after 256 instructions but leaves the exact counter initialization and decrementation representation unspecified.",
      "enum_candidates": [
        "init_255",
        "init_0_count_up",
        "mod_256"
      ]
    },
    {
      "pointer": "/state/2/size_bits",
      "claim": "sR_RegStatus consumes 1495 bits of storage.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Multiplying the 23-bit entry format (1 + 14 + 8) by 65 entries yields exactly 1495 bits."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/state/2/indexing",
      "claim": "sR_RegStatus is directly indexed by architectural/logical register ID from 0 to 64.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "We use a dedicated table that contains one entry per logical register.",
        "why": "Direct correspondence between logical registers and table entries establishes indexing by logical register ID."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/default",
      "claim": "The default lifetime before digest invalidation is 256 decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly establishes 256 decoded instructions as the invalidation window; Table 3's 8-bit decay_ctr provides the 256 states needed to track this duration."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/range",
      "claim": "The legal range for decay_instructions is [64, 1024] pow2.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper defines only the fixed design point of 256 instructions; the allowable tuning range and power-of-two constraint are not stated in the paper.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/0/storage_impact",
      "claim": "decay_instructions changes decay_ctr width from 8 bits to log2(decay_instructions) bits in sR_RegStatus (65 * log2(decay_instructions) bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 sets baseline decay_ctr to 8 bits for 256 instructions, establishing log2(decay_instructions) scaling across 65 entries."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/default",
      "claim": "The default digest width is 12 bits.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "RUNLTS generates a 12-bit digest from each 64-bit register value, with the format depending on the register type.",
        "why": "The paper explicitly states that RUNLTS generates a 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/range",
      "claim": "The legal range for digest_width_bits is [8, 16].",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "The paper specifies only a fixed 12-bit digest format; no tuning range between 8 and 16 bits is mentioned.",
      "enum_candidates": null
    },
    {
      "pointer": "/parameters/6/storage_impact",
      "claim": "Sets payload field width in sR_RegStatus to max(14, digest_width_bits).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest.",
        "why": "Because the shared payload must accommodate both the ROB tag and the digest, its width is the maximum of the two."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/0",
      "claim": "generate_digest computes the 12-bit integer digest by XOR-folding trailing 0/1 count, leading 0/1 count shifted left by 3, and value[5:0] shifted left by 6.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(1) For integer registers, the digest encodes the count of leading zeros (or ones), the count of trailing zeros (or ones), and the six least significant bits, effectively capturing characteristics of addresses and round numbers.",
        "why": "Figure 6(a) and the text define the exact 3-field XOR structure spanning digest bit positions [5:0], [8:3], and [11:6]."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/1",
      "claim": "generate_digest replicates 4 condition-code flag bits three times across the 12-bit digest.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(3) For condition-code flags, we replicate the four flag bits three times to fill the 12-bit digest.",
        "why": "The paper explicitly specifies replicating the four flag bits three times to produce the 12-bit digest."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/2",
      "claim": "generate_digest extracts FP32 bits [31:26] into digest bits [8:3].",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "(2) For floating-point registers, we inspect the most significant bits to classify the format and then extract the sign bit along with the most significant bits of the exponent.",
        "why": "Figure 6(b) specifies Value[31:26] positioned at digest bits [8:3] for FP32."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/3",
      "claim": "A valid register digest is invalidated and cleared to valid=0 after 256 subsequent decoded instructions.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Consequently, RUNLTS invalidates each digest after 256 subsequent instructions have been decoded, ensuring that only up-to-date information influences future predictions.",
        "why": "The paper explicitly specifies digest invalidation after exactly 256 decoded instructions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/4",
      "claim": "Each bank scales its weight table sum by 2.5 when usefulness is positive and suppresses output to 0 when non-positive.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "That Sigma feeds a multiplier stage labelled \"x0 or x2.5\".",
        "why": "Figure 5(c) expanded bank 0 explicitly includes the per-bank usefulness multiplier stage labelled 'x0 or x2.5'."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/unit_tests/5",
      "claim": "Completed register digests produced prior to a pipeline flush remain valid and available for subsequent branch predictions upon restart.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited.",
        "why": "The paper explicitly states that instructions finishing execution while a misprediction is in flight retain their values across the flush to benefit subsequent predictions."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/trigger",
      "claim": "The recover_squash routine is triggered upon pipeline misprediction recovery / flush.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper defines post-flush restart as the point where register status visibility is updated."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/5/pseudocode",
      "claim": "Speculative pending register tags of flushed instructions are detected via helper rob_is_flushed and cleared upon pipeline flush.",
      "verdict": "UNSUPPORTED",
      "evidence": null,
      "patch": null,
      "open_question": "Section 5 explicitly leaves recovering the Tomasulo-like table to future work; the paper does not specify the squash recovery algorithm for pending entries or define rob_is_flushed.",
      "enum_candidates": [
        "clear_to_invalid",
        "restore_prior_tag",
        "full_table_flush"
      ]
    },
    {
      "pointer": "/algorithms/5/notes",
      "claim": "Instructions completing execution while a misprediction was in-flight have written their digests, enlarging the valid set upon restart to correct subsequent branches.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "However, we found that by the time a branch resolves and its misprediction is revealed, many in-flight instructions have already finished execution, thereby enlarging the set of values visible to the predictor when it restarts, and this fact can be exploited. By leveraging these extra values after the flush, our scheme can correct subsequent mispredictions starting with the second one.",
        "why": "The paper explicitly confirms that values completed during wrong-path execution enlarge the visible set upon restart to assist subsequent branches."
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

You are a computer-architecture researcher auditing part of a feature spec that another agent distilled from a paper. The feature is `sr`. You are reviewing unit `algo:writeback_complete+algo:recover_squash` (kind: `algorithm`).

You did not write this spec and you cannot see the reasoning that produced it. Judge only what is on the page against what the paper actually says.

Downstream coding agents implement from this spec alone; th...

[Init]
model=gemini-3.8-flash-medium conversation=bf351d8a-9501-4bd8-8772-0e19b8efed97 cwd=/tmp/ray/session_2026-09-18_22-20-14_993598_7975/runtime_resources/working_dir_files/_ray_pkg_e0fc0a5a7eded491

[Response]
```json
{
  "records": [
    {
      "pointer": "/algorithms/2/trigger",
      "claim": "The writeback_complete procedure is triggered upon instruction execution writeback / completion.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper explicitly states that the payload overwrite and valid bit assertion occur when the instruction completes execution."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "The destination register index is checked against the range of 65 logical registers (0 to 64).",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "{ valid (1), payload (14), decay_ctr (8) } x 65",
        "why": "Table 3 auxiliary data specifies exactly 65 entries for the register tracking table."
      },
      "patch": null,
      "open_question": null,
      "enum_candidates": null
    },
    {
      "pointer": "/algorithms/2/pseudocode",
      "claim": "An entry overwrites its payload with the generated 12-bit digest and sets valid to 1 only when valid is 0 and the pending payload matches the completing instruction's 14-bit ROB tag.",
      "verdict": "SUPPORTED",
      "evidence": {
        "quote": "Each entry consists of a valid bit and a payload that can hold either a 14-bit tag or a 12-bit digest. At decode, an instruction that writes a register stores its ROB index as a tag in the corresponding entry and clears the valid bit. When the instruction completes, we overwrite the payload with the digest of the produced value and set the valid bit.",
        "why": "The paper defines the Tomasulo-like tag matching protocol where the completing instruction updates the entry containing its ROB tag."
      },
      "patch": null,
      "open_question": null,
      "enum_candidat
... [truncated]

[Usage]
{"input_tokens": 28424, "output_tokens": 34289, "thinking_tokens": 30325, "cache_read_tokens": 0, "total_tokens": 62713}

[Result]
status=SUCCESS conversation=bf351d8a-9501-4bd8-8772-0e19b8efed97 turns=1 duration=174.587196357s usage={"input_tokens": 28424, "output_tokens": 34289, "thinking_tokens": 30325, "cache_read_tokens": 0, "total_tokens": 62713}


