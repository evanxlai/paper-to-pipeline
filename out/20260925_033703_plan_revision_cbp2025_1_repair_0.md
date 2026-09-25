success: True
usage: {'input_tokens': 2667690, 'output_tokens': 145934, 'thinking_tokens': 60309, 'cache_read_tokens': 9557076, 'total_tokens': 2813624}

## result
I have reverted the plan to its exact original state and only appended the `makefile_cppflags` hook point required to properly thread the `compile_time_define` flags from G6 into the compiler.

## Plan revision

```json
{
  "feature_name": "sr_hand",
  "host": "cbp2025",
  "host_revision": "607496629452740887dc1b90a46834cc90dda1e0",
  "spec_inputs_used": "paper_only",
  "structure": {
    "choice": "A separate SampleCondPredictor instance (cond_predictor_impl) for tracking registers and containing the tables, called from cbp2016_tage_sc_l.h's SC update and predict blocks via global helper functions (sr_predict, sr_update). This keeps sR as an SC term contributing to LSUM before the threshold check, while housing its state correctly.",
    "rejected_alternatives": [
      {
        "alternative": "A standalone predictor that overrides TAGE-SC-L on disagreement.",
        "why_rejected": "It made CycWPPKI 43 percent worse because it overrode a strong predictor without knowing its own confidence. sR must be an SC term.",
        "source": "hosts/cbp2025/NOTES.md 'Where sR joins the statistical corrector'"
      }
    ]
  },
  "hook_points": [
    {
      "id": "sr_params_header",
      "file": "sr_params.h",
      "symbol": "sr_params.h",
      "action": "create",
      "change": "Define SR_* macros and HOST_* macros per the generated params_header for stage 4."
    },
    {
      "id": "my_predictor_h",
      "file": "my_cond_branch_predictor.h",
      "symbol": "SampleCondPredictor",
      "action": "modify",
      "observed": "SampleCondPredictor returns hist_to_use.tage_pred unchanged. The class has empty setup and update, and a pred_time_histories map to store per-branch history keyed by get_unique_inst_id(seq_no, piece).",
      "change": "#include \"sr_params.h\". Add sR state (WT, UT, reg_status table), checkpoint structure `sr_checkpoint`, and `sr_enabled`. Populate `sr_enabled` via `getenv` in `setup`. Implement register tracking hooks (`notify_decode`, `notify_execute`). Provide `sr_predict` and `sr_update` methods."
    },
    {
      "id": "my_predictor_cc",
      "file": "my_cond_branch_predictor.cc",
      "symbol": "sr_predict",
      "action": "modify",
      "observed": "Empty file at 0 bytes.",
      "change": "Provide out-of-line implementations of SampleCondPredictor's tracking/update logic to avoid bloating the header. Define global functions `extern int32_t sr_predict(uint64_t seq_no, uint8_t piece, uint64_t PC)` and `extern void sr_update(uint64_t seq_no, uint8_t piece, uint64_t PC, bool resolveDir, int LSUM)` that wrap `cond_predictor_impl`."
    },
    {
      "id": "interface_cc",
      "file": "cond_branch_predictor_interface.cc",
      "symbol": "notify_instr_decode and notify_instr_execute_resolve",
      "action": "modify",
      "observed": "The 9 interface functions wrap cbp2016_tage_sc_l and cond_predictor_impl, with notify_instr_decode and notify_instr_execute_resolve empty or forwarding to update.",
      "change": "In notify_instr_decode, call cond_predictor_impl.notify_decode(seq_no, piece, pc, _decode_info). In notify_instr_execute_resolve, call cond_predictor_impl.notify_execute(seq_no, piece, pc, _exec_info) before the branch updates."
    },
    {
      "id": "tage_sc_l_h",
      "file": "cbp2016_tage_sc_l.h",
      "symbol": "PREDICTOR::predict and PREDICTOR::update",
      "action": "modify",
      "observed": "LSUM is built from bias and GEHL tables, then SCPRED = (LSUM >= 0). update(PC, resolveDir, pred_taken, nextPC, hist_to_use) updates weights under (SCPRED != resolveDir || abs(LSUM) < THRES).",
      "change": "Declare `extern int32_t sr_predict(...)` and `extern void sr_update(...)`. In predict, add `LSUM += sr_predict(seq_no, piece, PC)` before `SCPRED = (LSUM >= 0)`. Modify inner update to take `seq_no` and `piece`, explicitly pass them from the outer update, and call `sr_update` inside the SC update block (passing `LSUM` and `resolveDir`)."
    },
    {
      "id": "makefile_cppflags",
      "file": "Makefile",
      "symbol": "FLAGS",
      "action": "modify",
      "observed": "FLAGS = -std=c++17 -L./lib $(LIBS) $(OPT)\nCPPFLAGS = -std=c++17 $(OPT)",
      "change": "Append `$(foreach var,$(filter SR_% HOST_%,$(.VARIABLES)),-D$(var)=$($(var)))` to CPPFLAGS, and append `$(CPPFLAGS)` to `FLAGS`, so that compile_time_define knobs passed by G6 reach the compiler."
    }
  ],
  "spec_map": [
    {
      "spec_pointer": "/state/0",
      "spec_item": "sr_wt",
      "hook_ids": [
        "my_predictor_h"
      ],
      "realization": "A 3D array or vector of vectors in SampleCondPredictor."
    },
    {
      "spec_pointer": "/state/1",
      "spec_item": "sr_ut",
      "hook_ids": [
        "my_predictor_h"
      ],
      "realization": "A 3D array in SampleCondPredictor."
    },
    {
      "spec_pointer": "/state/2",
      "spec_item": "reg_status",
      "hook_ids": [
        "my_predictor_h"
      ],
      "realization": "An array of RegStatus structs tracking valid, payload, and decay_ctr."
    },
    {
      "spec_pointer": "/state/3",
      "spec_item": "sr_checkpoint",
      "hook_ids": [
        "my_predictor_h",
        "my_predictor_cc"
      ],
      "realization": "A struct stored per-branch."
    },
    {
      "spec_pointer": "/algorithms/0",
      "spec_item": "fold",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "A helper function for compressing the data payload."
    },
    {
      "spec_pointer": "/algorithms/1",
      "spec_item": "sat_update",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "A helper function for saturated counters."
    },
    {
      "spec_pointer": "/algorithms/2",
      "spec_item": "prng_next",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "A pseudo-random number generator step."
    },
    {
      "spec_pointer": "/algorithms/3",
      "spec_item": "wt_index",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "Computes the index for Weight Table."
    },
    {
      "spec_pointer": "/algorithms/4",
      "spec_item": "ut_index",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "Computes the index for Useful Table."
    },
    {
      "spec_pointer": "/algorithms/5",
      "spec_item": "generate_digest",
      "hook_ids": [
        "my_predictor_cc",
        "interface_cc"
      ],
      "realization": "Called during execution to build the digest."
    },
    {
      "spec_pointer": "/algorithms/6",
      "spec_item": "decode_allocate",
      "hook_ids": [
        "my_predictor_cc",
        "interface_cc"
      ],
      "realization": "Allocates register tracking structure at decode."
    },
    {
      "spec_pointer": "/algorithms/7",
      "spec_item": "writeback_digest",
      "hook_ids": [
        "my_predictor_cc",
        "interface_cc"
      ],
      "realization": "Writes back the finished digest."
    },
    {
      "spec_pointer": "/algorithms/8",
      "spec_item": "predict",
      "hook_ids": [
        "tage_sc_l_h",
        "my_predictor_h",
        "my_predictor_cc"
      ],
      "realization": "Called during TAGE-SC-L's predict. Accumulates usefulness and calculates weights. Saves checkpoint per branch."
    },
    {
      "spec_pointer": "/algorithms/9",
      "spec_item": "update",
      "hook_ids": [
        "tage_sc_l_h",
        "my_predictor_h",
        "my_predictor_cc"
      ],
      "realization": "Called during TAGE-SC-L's update, inside the SC training block. Retrieves checkpoint, updates UT (sign_flip rule only for simplicity, per structure) and WT tables."
    },
    {
      "spec_pointer": "/algorithms/10",
      "spec_item": "squash_recovery",
      "hook_ids": [
        "my_predictor_cc"
      ],
      "realization": "Squash recovery logic."
    }
  ],
  "steps": [
    {
      "title": "Add params header, makefile edit, and enable knob",
      "hook_ids": [
        "sr_params_header",
        "makefile_cppflags",
        "my_predictor_h"
      ],
      "detail": "Create sr_params.h and add it to DEPS.",
      "verify": "The host builds (G1)."
    },
    {
      "title": "Add register tracking and decay",
      "hook_ids": [
        "my_predictor_h",
        "my_predictor_cc",
        "interface_cc"
      ],
      "detail": "Track valid, payload, and decay counter for logic registers.",
      "verify": "The host builds (G1)."
    },
    {
      "title": "Add WT, UT, checkpoint structures and prediction integration",
      "hook_ids": [
        "my_predictor_h",
        "my_predictor_cc",
        "tage_sc_l_h"
      ],
      "detail": "Allocate tables and checkpoint history, hook predict into LSUM.",
      "verify": "The host builds (G1)."
    },
    {
      "title": "Add update integration",
      "hook_ids": [
        "my_predictor_h",
        "my_predictor_cc",
        "tage_sc_l_h"
      ],
      "detail": "Hook update into TAGE-SC-L SC.",
      "verify": "Gate off-metrics match baseline (G2), smoke tests pass (G4)."
    }
  ],
  "risks": [
    {
      "risk": "CBP2025 traces do not decode wrong-path instructions.",
      "mitigation": "Squash recovery is empty because there is no wrong-path state to recover."
    }
  ],
  "interface_resolutions": [
    {
      "spec_pointer": "/host_interfaces/0",
      "need": "decode-time destination register and in-flight tag",
      "status": "exact",
      "rationale": "Provided by decode hook.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/1",
      "need": "execute-time result value, at the cycle the value is produced",
      "status": "exact",
      "rationale": "Provided by execute hook.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/2",
      "need": "which 64-bit lane of a wide register a piece writes",
      "status": "exact",
      "rationale": "Provided by decode/execute.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/3",
      "need": "register class of each logical register",
      "status": "exact",
      "rationale": "Provided by hooks.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/4",
      "need": "SC sum and SC training step",
      "status": "exact",
      "rationale": "Provided by hooks.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/5",
      "need": "per-branch checkpoint lifetime",
      "status": "exact",
      "rationale": "Provided by predictor.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/6",
      "need": "flush notification with the squashed tags",
      "status": "exact",
      "rationale": "Not needed directly.",
      "resolution": "Not needed directly.",
      "fidelity_note": ""
    },
    {
      "spec_pointer": "/host_interfaces/7",
      "need": "clock_cycle",
      "status": "fallback",
      "rationale": "Host does not provide exact cycle.",
      "resolution": "Use decay counters attached to register status, decremented on each decode, instead of a global cycle counter.",
      "fidelity_note": "Fidelity loss: Decay happens per decode rather than per cycle."
    },
    {
      "spec_pointer": "/host_interfaces/8",
      "need": "global_history",
      "status": "exact",
      "rationale": "Not needed directly; sR integrates tightly with TAGE-SC-L which manages its own history.",
      "resolution": "Not needed directly; sR integrates tightly with TAGE-SC-L which manages its own history.",
      "fidelity_note": ""
    }
  ],
  "knobs": [
    {
      "spec_pointer": "/parameters/0",
      "spec_parameter": "num_banks",
      "macro": "SR_NUM_BANKS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 8
    },
    {
      "spec_pointer": "/parameters/1",
      "spec_parameter": "num_logical_regs",
      "macro": "SR_NUM_LOGICAL_REGS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 65
    },
    {
      "spec_pointer": "/parameters/2",
      "spec_parameter": "wt0_entries",
      "macro": "SR_WT0_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 512
    },
    {
      "spec_pointer": "/parameters/3",
      "spec_parameter": "wt1_entries",
      "macro": "SR_WT1_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 256
    },
    {
      "spec_pointer": "/parameters/4",
      "spec_parameter": "wt2_entries",
      "macro": "SR_WT2_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 128
    },
    {
      "spec_pointer": "/parameters/5",
      "spec_parameter": "ut0_entries",
      "macro": "SR_UT0_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 8
    },
    {
      "spec_pointer": "/parameters/6",
      "spec_parameter": "ut1_entries",
      "macro": "SR_UT1_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 8
    },
    {
      "spec_pointer": "/parameters/7",
      "spec_parameter": "ut2_entries",
      "macro": "SR_UT2_ENTRIES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 8
    },
    {
      "spec_pointer": "/parameters/8",
      "spec_parameter": "wt_bits",
      "macro": "SR_WT_BITS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 6
    },
    {
      "spec_pointer": "/parameters/9",
      "spec_parameter": "ut_bits",
      "macro": "SR_UT_BITS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 6
    },
    {
      "spec_pointer": "/parameters/10",
      "spec_parameter": "decay_ctr_bits",
      "macro": "SR_DECAY_CTR_BITS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 8
    },
    {
      "spec_pointer": "/parameters/11",
      "spec_parameter": "tag_bits",
      "macro": "SR_TAG_BITS",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 14
    },
    {
      "spec_pointer": "/parameters/12",
      "spec_parameter": "max_inflight_branches",
      "macro": "SR_MAX_INFLIGHT_BRANCHES",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 1024
    },
    {
      "spec_pointer": "/parameters/13",
      "spec_parameter": "useful_multiplier",
      "macro": "SR_USEFUL_MULTIPLIER",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 2.5
    },
    {
      "spec_pointer": "/parameters/14",
      "spec_parameter": "useful_threshold",
      "macro": "SR_USEFUL_THRESHOLD",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": 0
    },
    {
      "spec_pointer": "/parameters/15",
      "spec_parameter": "ut_update_rule",
      "macro": "SR_UT_UPDATE_RULE",
      "host_knob": "constexpr",
      "binding": "compile_time_define",
      "default": "sign_flip"
    }
  ],
  "feature_enable": {
    "name": "sr_enable",
    "macro": "SR_SR_ENABLE",
    "binding": "runtime_env",
    "default_off": "Absent from environment or empty means off.",
    "off_path": "Does not invoke tracking logic."
  },
  "host_knobs": [
    {
      "name": "logg",
      "macro": "HOST_LOGG",
      "host_symbol": "LOGG",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGG 10\t\t\t/* logsize of the  banks in the  tagged TAGE tables */",
      "type": "int",
      "default": 10,
      "range": "[8, 12]",
      "binding": "compile_time_define",
      "description": "logsize of the banks in the tagged TAGE tables"
    },
    {
      "name": "tbits",
      "macro": "HOST_TBITS",
      "host_symbol": "TBITS",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define TBITS 8\t\t\t//minimum width of the tags  (low history lengths), +4 for high history lengths",
      "type": "int",
      "default": 8,
      "range": "[6, 12]",
      "binding": "compile_time_define",
      "description": "minimum width of the tags"
    },
    {
      "name": "nbanklow",
      "macro": "HOST_NBANKLOW",
      "host_symbol": "NBANKLOW",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define NBANKLOW 10\t\t\t// number of banks in the shared bank-interleaved for the low history lengths",
      "type": "int",
      "default": 10,
      "range": "[4, 16]",
      "binding": "compile_time_define",
      "description": "number of banks in the shared bank-interleaved for the low history lengths"
    },
    {
      "name": "nbankhigh",
      "macro": "HOST_NBANKHIGH",
      "host_symbol": "NBANKHIGH",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define NBANKHIGH 20\t\t\t// number of banks in the shared bank-interleaved for the  history lengths",
      "type": "int",
      "default": 20,
      "range": "[8, 32]",
      "binding": "compile_time_define",
      "description": "number of banks in the shared bank-interleaved for the high history lengths"
    },
    {
      "name": "cwidth",
      "macro": "HOST_CWIDTH",
      "host_symbol": "CWIDTH",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define CWIDTH 3\t\t\t// predictor counter width on the TAGE tagged tables",
      "type": "int",
      "default": 3,
      "range": "[2, 4]",
      "binding": "compile_time_define",
      "description": "predictor counter width on the TAGE tagged tables"
    },
    {
      "name": "uwidth",
      "macro": "HOST_UWIDTH",
      "host_symbol": "UWIDTH",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define UWIDTH 1\t\t\t// u counter width on the TAGE tagged tables",
      "type": "int",
      "default": 1,
      "range": "[1, 2]",
      "binding": "compile_time_define",
      "description": "u counter width on the TAGE tagged tables"
    },
    {
      "name": "logb",
      "macro": "HOST_LOGB",
      "host_symbol": "LOGB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGB 13\t\t\t// log of number of entries in bimodal predictor",
      "type": "int",
      "default": 13,
      "range": "[10, 15]",
      "binding": "compile_time_define",
      "description": "log of number of entries in bimodal predictor"
    },
    {
      "name": "hystshift",
      "macro": "HOST_HYSTSHIFT",
      "host_symbol": "HYSTSHIFT",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define HYSTSHIFT 2\t\t//log of number of entries in bimodal predictor",
      "type": "int",
      "default": 2,
      "range": "[1, 3]",
      "binding": "compile_time_define",
      "description": "log of number of entries in bimodal predictor"
    },
    {
      "name": "percwidth",
      "macro": "HOST_PERCWIDTH",
      "host_symbol": "PERCWIDTH",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define PERCWIDTH 6\t\t//Statistical corrector  counter width 5 -> 6 : 0.6 %",
      "type": "int",
      "default": 6,
      "range": "[4, 8]",
      "binding": "compile_time_define",
      "description": "Statistical corrector counter width"
    },
    {
      "name": "logbias",
      "macro": "HOST_LOGBIAS",
      "host_symbol": "LOGBIAS",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGBIAS 8",
      "type": "int",
      "default": 8,
      "range": "[6, 10]",
      "binding": "compile_time_define",
      "description": "LOGBIAS"
    },
    {
      "name": "loggnb",
      "macro": "HOST_LOGGNB",
      "host_symbol": "LOGGNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGGNB 10\t\t// 1 1K + 2 * 512-entry tables",
      "type": "int",
      "default": 10,
      "range": "[8, 12]",
      "binding": "compile_time_define",
      "description": "LOGGNB"
    },
    {
      "name": "logpnb",
      "macro": "HOST_LOGPNB",
      "host_symbol": "LOGPNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGPNB 9\t\t// 1 512 + 2 * 256-entry tables",
      "type": "int",
      "default": 9,
      "range": "[7, 11]",
      "binding": "compile_time_define",
      "description": "LOGPNB"
    },
    {
      "name": "loglnb",
      "macro": "HOST_LOGLNB",
      "host_symbol": "LOGLNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGLNB 10\t\t// 1 1K + 2 * 512-entry tables",
      "type": "int",
      "default": 10,
      "range": "[8, 12]",
      "binding": "compile_time_define",
      "description": "LOGLNB"
    },
    {
      "name": "logsnb",
      "macro": "HOST_LOGSNB",
      "host_symbol": "LOGSNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGSNB 9\t\t// 1 512 + 2 * 256-entry tables",
      "type": "int",
      "default": 9,
      "range": "[7, 11]",
      "binding": "compile_time_define",
      "description": "LOGSNB"
    },
    {
      "name": "logtnb",
      "macro": "HOST_LOGTNB",
      "host_symbol": "LOGTNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGTNB 10\t\t// 1 1K + 2 * 512-entry tables",
      "type": "int",
      "default": 10,
      "range": "[8, 12]",
      "binding": "compile_time_define",
      "description": "LOGTNB"
    },
    {
      "name": "loginb",
      "macro": "HOST_LOGINB",
      "host_symbol": "LOGINB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGINB 8",
      "type": "int",
      "default": 8,
      "range": "[6, 10]",
      "binding": "compile_time_define",
      "description": "LOGINB"
    },
    {
      "name": "logimnb",
      "macro": "HOST_LOGIMNB",
      "host_symbol": "LOGIMNB",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGIMNB 9\t\t// 1 512 + 2 * 256-entry tables",
      "type": "int",
      "default": 9,
      "range": "[7, 11]",
      "binding": "compile_time_define",
      "description": "LOGIMNB"
    },
    {
      "name": "logl",
      "macro": "HOST_LOGL",
      "host_symbol": "LOGL",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define LOGL 5",
      "type": "int",
      "default": 5,
      "range": "[3, 7]",
      "binding": "compile_time_define",
      "description": "LOGL"
    },
    {
      "name": "ewidth",
      "macro": "HOST_EWIDTH",
      "host_symbol": "EWIDTH",
      "file": "cbp2016_tage_sc_l.h",
      "observed": "#define EWIDTH 6",
      "type": "int",
      "default": 6,
      "range": "[4, 8]",
      "binding": "compile_time_define",
      "description": "EWIDTH"
    }
  ],
  "host_storage": {
    "measured_by": "accounting",
    "baseline_bits": 524615,
    "terms": [
      {
        "name": "Bimodal",
        "bits": "(1 << LOGB) * (2 + 1)"
      },
      {
        "name": "TAGE tags",
        "bits": "((1 << LOGG) * NHIST * (TBITS + 1)) + ((1 << LOGG) * NBANKHIGH * 4)"
      },
      {
        "name": "TAGE counters",
        "bits": "(1 << LOGG) * NHIST * CWIDTH"
      },
      {
        "name": "TAGE useful",
        "bits": "(1 << LOGG) * NHIST * UWIDTH"
      },
      {
        "name": "SC Bias",
        "bits": "(1 << LOGBIAS) * PERCWIDTH"
      },
      {
        "name": "SC GEHL",
        "bits": "((1 << LOGGNB) * (PERCWIDTH)) + 2 * ((1 << LOGPNB) * (PERCWIDTH)) + ((1 << LOGLNB) * (PERCWIDTH)) + 2 * ((1 << LOGSNB) * (PERCWIDTH)) + ((1 << LOGTNB) * (PERCWIDTH)) + ((1 << LOGINB) * (PERCWIDTH)) + 2 * ((1 << LOGIMNB) * (PERCWIDTH))"
      },
      {
        "name": "SC Global tables",
        "bits": "0"
      },
      {
        "name": "Local history",
        "bits": "(1 << LOGL) * LNB"
      },
      {
        "name": "ITAGE",
        "bits": "(1 << LOGINB) * PERCWIDTH"
      },
      {
        "name": "Other state",
        "bits": "2 * NHIST"
      }
    ]
  },
  "open_questions": [
    {
      "question": "WT hashes h0-h2 and skewed UT hashes are not defined in the paper.",
      "assumption": "Implement the `fold` based hashes defined in the spec's pseudocode."
    },
    {
      "question": "How usefulness counters are trained.",
      "assumption": "Use the `sign_flip` rule (SC's own usefulness rule)."
    },
    {
      "question": "The x0/x2.5 control signal is drawn but not specified.",
      "assumption": "Gate on the winner's summed usefulness >= `useful_threshold` (0)."
    },
    {
      "question": "Leading/trailing counts can be 64.",
      "assumption": "Use `count & 0x3F` as described in the spec."
    },
    {
      "question": "FP format classification.",
      "assumption": "Classify based on upper zero bits per AArch64 zero-extension."
    },
    {
      "question": "Where decay counting starts.",
      "assumption": "Start counting when the digest is written."
    },
    {
      "question": "Whether sR's usefulness adds to the SC threshold THRES.",
      "assumption": "Leave THRES as the host computes it without adding sR usefulness."
    },
    {
      "question": "Recovery of status table on a flush.",
      "assumption": "Do nothing, as CBP2025 has no wrong-path execution."
    }
  ]
}
```

```json
{
  "feature_name": "sr_hand",
  "host": "cbp2025",
  "host_revision": "607496629452740887dc1b90a46834cc90dda1e0",
  "metric_keys": [
    "brmispki_50perc_amean",
    "cycwppki_50perc_amean",
    "ipc_50perc_amean"
  ],
  "smoke": {
    "traces": [
      "sample_traces/int/sample_int_trace.gz",
      "sample_traces/fp/sample_fp_trace.gz"
    ]
  },
  "correctness": [
    {
      "id": "existing_regression_int",
      "kind": "existing_regression",
      "description": "Does the host still work with the feature off.",
      "command": "./cbp sample_traces/int/sample_int_trace.gz | tail -n 15",
      "feature_state": "off",
      "timeout_seconds": 60,
      "clean_tree_result": {
        "exit_code": 0,
        "passed": true,
        "recorded_at": "2026-09-24T20:39:16-07:00",
        "summary": " Read 997301 instrs "
      },
      "pass_condition": {
        "kind": "matches_clean_tree",
        "pattern": "( Read 997301 instrs )"
      }
    },
    {
      "id": "existing_regression_fp",
      "kind": "existing_regression",
      "description": "Does the host still work with the feature off.",
      "command": "./cbp sample_traces/fp/sample_fp_trace.gz | tail -n 15",
      "feature_state": "off",
      "timeout_seconds": 60,
      "clean_tree_result": {
        "exit_code": 0,
        "passed": true,
        "recorded_at": "2026-09-24T20:39:32-07:00",
        "summary": " Read 997741 instrs "
      },
      "pass_condition": {
        "kind": "matches_clean_tree",
        "pattern": "( Read 997741 instrs )"
      }
    },
    {
      "id": "off_baseline_int",
      "kind": "feature_off_baseline",
      "description": "Collect exact baseline MPKI to prove the feature bypass is complete.",
      "command": "./cbp sample_traces/int/sample_int_trace.gz | grep MISPRED_PER_1K_INST",
      "feature_state": "off",
      "timeout_seconds": 60,
      "clean_tree_result": null,
      "pass_condition": {
        "kind": "metrics_equal_baseline",
        "baseline_pointer": "/per_trace/int~1sample_int_trace.gz",
        "rel_tol": 0.0
      }
    },
    {
      "id": "off_baseline_fp",
      "kind": "feature_off_baseline",
      "description": "Collect exact baseline MPKI to prove the feature bypass is complete.",
      "command": "./cbp sample_traces/fp/sample_fp_trace.gz | grep MISPRED_PER_1K_INST",
      "feature_state": "off",
      "timeout_seconds": 60,
      "clean_tree_result": null,
      "pass_condition": {
        "kind": "metrics_equal_baseline",
        "baseline_pointer": "/per_trace/fp~1sample_fp_trace.gz",
        "rel_tol": 0.0
      }
    },
    {
      "id": "ut_0",
      "kind": "spec_unit_test",
      "description": "digest_int_small",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/0",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_int_small: PASS"
      }
    },
    {
      "id": "ut_1",
      "kind": "spec_unit_test",
      "description": "digest_int_negative",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/1",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_int_negative: PASS"
      }
    },
    {
      "id": "ut_2",
      "kind": "spec_unit_test",
      "description": "digest_int_all_zero_and_all_one",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/2",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_int_all_zero_and_all_one: PASS"
      }
    },
    {
      "id": "ut_3",
      "kind": "spec_unit_test",
      "description": "digest_fp_formats",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/3",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_fp_formats: PASS"
      }
    },
    {
      "id": "ut_4",
      "kind": "spec_unit_test",
      "description": "digest_flags",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/4",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_flags: PASS"
      }
    },
    {
      "id": "ut_5",
      "kind": "spec_unit_test",
      "description": "decay_invalidates_after_256_decodes",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/5",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "decay_invalidates_after_256_decodes: PASS"
      }
    },
    {
      "id": "ut_6",
      "kind": "spec_unit_test",
      "description": "writeback_only_from_newest_producer",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/6",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "writeback_only_from_newest_producer: PASS"
      }
    },
    {
      "id": "ut_7",
      "kind": "spec_unit_test",
      "description": "wide_register_uses_low_lane",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/7",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "wide_register_uses_low_lane: PASS"
      }
    },
    {
      "id": "ut_8",
      "kind": "spec_unit_test",
      "description": "predict_selects_most_useful_register",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/8",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "predict_selects_most_useful_register: PASS"
      }
    },
    {
      "id": "ut_9",
      "kind": "spec_unit_test",
      "description": "predict_centred_weights",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/9",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "predict_centred_weights: PASS"
      }
    },
    {
      "id": "ut_10",
      "kind": "spec_unit_test",
      "description": "predict_gate_closed",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/10",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "predict_gate_closed: PASS"
      }
    },
    {
      "id": "ut_11",
      "kind": "spec_unit_test",
      "description": "predict_empty_bank",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/11",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "predict_empty_bank: PASS"
      }
    },
    {
      "id": "ut_12",
      "kind": "spec_unit_test",
      "description": "wt_index_uses_every_digest_bit",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/12",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "wt_index_uses_every_digest_bit: PASS"
      }
    },
    {
      "id": "ut_13",
      "kind": "spec_unit_test",
      "description": "fold_xor_folds_every_bit",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/13",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "fold_xor_folds_every_bit: PASS"
      }
    },
    {
      "id": "ut_14",
      "kind": "spec_unit_test",
      "description": "decode_allocate_claims_register",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/14",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "decode_allocate_claims_register: PASS"
      }
    },
    {
      "id": "ut_15",
      "kind": "spec_unit_test",
      "description": "squash_recovery_keeps_completed_digests",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/15",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "squash_recovery_keeps_completed_digests: PASS"
      }
    },
    {
      "id": "ut_16",
      "kind": "spec_unit_test",
      "description": "prng_next_is_deterministic",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/16",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "prng_next_is_deterministic: PASS"
      }
    },
    {
      "id": "ut_17",
      "kind": "spec_unit_test",
      "description": "update_trains_one_register_per_bank",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/17",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "update_trains_one_register_per_bank: PASS"
      }
    },
    {
      "id": "ut_18",
      "kind": "spec_unit_test",
      "description": "update_usefulness_sign_flip",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/18",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "update_usefulness_sign_flip: PASS"
      }
    },
    {
      "id": "ut_19",
      "kind": "spec_unit_test",
      "description": "no_training_when_sc_confident_and_right",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/19",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "no_training_when_sc_confident_and_right: PASS"
      }
    },
    {
      "id": "smoke_int",
      "kind": "existing_regression",
      "description": "Does the host still work with the feature on.",
      "command": "./cbp sample_traces/int/sample_int_trace.gz | tail -n 15",
      "feature_state": "both",
      "timeout_seconds": 60,
      "clean_tree_result": {
        "exit_code": 0,
        "passed": true,
        "recorded_at": "2026-09-24T20:39:16-07:00",
        "summary": " Read 997301 instrs "
      },
      "pass_condition": {
        "kind": "matches_clean_tree",
        "pattern": "( Read 997301 instrs )"
      }
    }
  ],
  "performance": [
    {
      "id": "perf_mpki",
      "description": "Main performance claim on MPKI",
      "metric": "brmispki_50perc_amean",
      "direction": "decrease",
      "trace_list": "experiments/perf-4.list",
      "baseline": {
        "source": "measure_feature_off"
      },
      "run": {
        "mode": "host_adapter"
      },
      "block_threshold": {
        "min_relative_improvement": 0.0,
        "no_regression": [
          {
            "metric": "ipc_50perc_amean",
            "direction": "increase",
            "max_relative_regression": 0.005
          }
        ]
      },
      "warn_threshold": {
        "target_relative_improvement": 0.0034,
        "claim_source": "0.34% MPKI on promote-45 from spec source.provenance"
      }
    }
  ]
}
```

## stream
[User Message]
Your plan revision was rejected and nothing was written. The plan pair in force is still the one you were given. Fix every item below and emit the revision again, in full, under a `## Plan revision` heading as two fenced json blocks, the port plan then the test plan. Do not emit a diff or a partial document.

## Schema errors

- port plan: host_storage: 'measured_by' is a required property
- port plan: host_storage: 'terms' is a required property
- port plan: open_questions/0: Additional propert...

[Tools Offered]
cbp2025_bash

[Init]
model=gemini-3.1-pro-high conversation=8cd2e846-cf0c-4d2b-b6f9-821e4550771e cwd=/tmp/ray/session_2026-09-24_08-12-17_468811_18524/runtime_resources/working_dir_files/_ray_pkg_949ed19fbd38fdd2

[Step: system_message] state=DONE

[Step: checkpoint] state=DONE

[Usage]
{"input_tokens": 52830, "output_tokens": 266, "thinking_tokens": 0, "cache_read_tokens": 7899, "total_tokens": 53096}

[Tool Call: run_command]
Args: {"CommandLine": "cat << 'EOF' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/response.py\nimport json\n\nwith open('/tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/port_plan_raw.json') as f:\n    text = f.read()\n\nimport re\nm = re.search(r'```json\\n(.*?)\\n```', text, re.DOTALL)\nport_plan_obj = json.loads(m.group(1))\n\n# Find the real exact original plan in transcript, since prompt 0 seems corrupted in the transcript logic we used previously.\nEOF\npython3 /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/respo\u2026"}

[Tool Call: run_command]
Args: {"CommandLine": "cat << 'EOF' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/response.py\nimport json\n\nwith open('/tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/port_plan_raw.json') as f:\n    text = f.read()\n\nimport re\nm = re.search(r'```json\\n(.*?)\\n```', text, re.DOTALL)\nport_plan_obj = json.loads(m.group(1))\n\n# Find the real exact original plan in transcript, since prompt 0 seems corrupted in the transcript logic we used previously.\nEOF\npython3 /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/respo\u2026"}

[Usage]
{"input_tokens": 61057, "output_tokens": 182, "thinking_tokens": 0, "cache_read_tokens": 0, "total_tokens": 61239}

[Tool Call: run_command]
Args: {"CommandLine": "head -n 5 /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/brain/8cd2e846-cf0c-4d2b-b6f9-821e4550771e/.system_generated/logs/transcript_full.jsonl > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/early_transcript.jsonl"}

[Tool Result]
head: cannot open '/tmp/agy_home_o8srsznm/.gemini/antigravity-cli/brain/8cd2e846-cf0c-4d2b-b6f9-821e4550771e/.system_generated/logs/transcript_full.jsonl' for reading: No such file or directory


[Usage]
{"input_tokens": 6125, "output_tokens": 141, "thinking_tokens": 0, "cache_read_tokens": 55259, "total_tokens": 6266}

[Tool Call: run_command]
Args: {"CommandLine": "ls -la /tmp/agy_home_778ap5xx/.gemini/antigravity-cli/brain/8cd2e846-cf0c-4d2b-b6f9-821e4550771e/.system_generated/logs/"}

[Tool Result]
total 1508
drwxr-xr-x 3 user 1002    4096 Sep 24 20:46 .
drwxr-xr-x 5 user 1002    4096 Sep 24 21:13 ..
drwxr-xr-x 4 user 1002    4096 Sep 24 20:46 chunks
-rw-r--r-- 1 user 1002  478754 Sep 24 22:16 transcript.jsonl
-rw-r--r-- 1 user 1002 1044002 Sep 24 22:16 transcript_full.jsonl


[Usage]
{"input_tokens": 6518, "output_tokens": 210, "thinking_tokens": 0, "cache_read_tokens": 55243, "total_tokens": 6728}

[Tool Call: run_command]
Args: {"CommandLine": "python3 -c 'import json; lines = open(\"/tmp/agy_home_778ap5xx/.gemini/antigravity-cli/brain/8cd2e846-cf0c-4d2b-b6f9-821e4550771e/.system_generated/logs/transcript_full.jsonl\").readlines(); d=json.loads(lines[0]); print(d[\"content\"])' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/first_prompt.txt"}

[Tool Call: run_command]
Args: {"CommandLine": "python3 -c 'import json; lines = open(\"/tmp/agy_home_778ap5xx/.gemini/antigravity-cli/brain/8cd2e846-cf0c-4d2b-b6f9-821e4550771e/.system_generated/logs/transcript_full.jsonl\").readlines(); d=json.loads(lines[0]); print(d[\"content\"])' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/first_prompt.txt"}

[Usage]
{"input_tokens": 6808, "output_tokens": 588, "thinking_tokens": 0, "cache_read_tokens": 55225, "total_tokens": 7396}

[Tool Call: run_command]
Args: {"CommandLine": "cat << 'EOF' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/extract.py\nimport json\nimport re\n\nwith open('/tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/first_prompt.txt') as f:\n    text = f.read()\n\nmatches = list(re.finditer(r'```json\\n(.*?)\\n```', text, re.DOTALL))\nport_plan_obj = json.loads(matches[0].group(1))\ntest_plan_text = matches[1].group(1)\n\nport_plan_obj['hook_points'].append({\n  \"id\": \"makefile_cppflags\",\n  \"file\": \"Makefile\",\n  \"symbol\": \"FLAGS\",\n  \"action\": \"modify\",\n  \"observ\u2026"}

[Tool Call: run_command]
Args: {"CommandLine": "cat << 'EOF' > /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/extract.py\nimport json\nimport re\n\nwith open('/tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/first_prompt.txt') as f:\n    text = f.read()\n\nmatches = list(re.finditer(r'```json\\n(.*?)\\n```', text, re.DOTALL))\nport_plan_obj = json.loads(matches[0].group(1))\ntest_plan_text = matches[1].group(1)\n\nport_plan_obj['hook_points'].append({\n  \"id\": \"makefile_cppflags\",\n  \"file\": \"Makefile\",\n  \"symbol\": \"FLAGS\",\n  \"action\": \"modify\",\n  \"observ\u2026"}

[Usage]
{"input_tokens": 7464, "output_tokens": 103, "thinking_tokens": 0, "cache_read_tokens": 55219, "total_tokens": 7567}

[Tool Call: run_command]
Args: {"CommandLine": "cat /tmp/agy_home_o8srsznm/.gemini/antigravity-cli/scratch/response.md"}

[Tool Result]
<truncated 964 lines>
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "digest_flags: PASS"
      }
    },
    {
      "id": "ut_5",
      "kind": "spec_unit_test",
      "description": "decay_invalidates_after_256_decodes",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/5",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "decay_invalidates_after_256_decodes: PASS"
      }
    },
    {
      "id": "ut_6",
      "kind": "spec_unit_test",
      "description": "writeback_only_from_newest_producer",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/6",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "writeback_only_from_newest_producer: PASS"
      }
    },
    {
      "id": "ut_7",
      "kind": "spec_unit_test",
      "description": "wide_register_uses_low_lane",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/7",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "wide_register_uses_low_lane: PASS"
      }
    },
    {
      "id": "ut_8",
      "kind": "spec_unit_test",
      "description": "predict_selects_most_useful_register",
      "command": "./cbp sample_traces/int/sample_int_trace.gz",
      "feature_state": "on",
      "test_file": "my_cond_branch_predictor.cc",
      "spec_pointer": "/unit_tests/8",
      "pass_condition": {
        "kind": "stdout_matches",
        "pattern": "predict_selects_most_useful_register: PASS"
      }
    },
    {
      "id": "ut_9",
      "kind": "spec_unit_test",
      "
... [truncated]

[Response]
I have reverted the plan to its exact original state and only appended the `makefile_cppflags` hook point required to properly thread the `compile_time_define` flags from G6 into the compiler.

## Plan revision

```json
{
  "feature_name": "sr_hand",
  "host": "cbp2025",
  "host_revision": "607496629452740887dc1b90a46834cc90dda1e0",
  "spec_inputs_used": "paper_only",
  "structure": {
    "choice": "A separate SampleCondPredictor instance (cond_predictor_impl) for tracking registers and containing the tables, called from cbp2016_tage_sc_l.h's SC update and predict blocks via global helper functions (sr_predict, sr_update). This keeps sR as an SC term contributing to LSUM before the threshold check, while housing its state correctly.",
    "rejected_alternatives": [
      {
        "alternative": "A standalone predictor that overrides TAGE-SC-L on disagreement.",
        "why_rejected": "It made CycWPPKI 43 percent worse because it overrode a strong predictor without knowing its own confidence. sR must be an SC term.",
        "source": "hosts/cbp2025/NOTES.md 'Where sR joins the statistical corrector'"
      }
    ]
  },
  "hook_points": [
    {
      "id": "sr_params_header",
      "file": "sr_params.h",
      "symbol": "sr_params.h",
      "action": "create",
      "change": "Define SR_* macros and HOST_* macros per the generated params_header for stage 4."
    },
    {
      "id": "my_predictor_h",
      "file": "my_cond_branch_predictor.h",
      "symbol": "SampleCondPredictor",
      "action": "modify",
      "observed": "SampleCondPredictor returns hist_to_use.tage_pred unchanged. The class has empty setup and update, and a pred_time_histories map to store per-branch history keyed by get_unique_inst_id(seq_no, piece).",
      "change": "#include \"sr_params.h\". Add sR state (WT, UT, reg_status table), checkpoint structure `sr_checkpoint`, and `sr_enabled`. Populate `sr_enabled` via `getenv` in `setup`. Implement register tracking hooks (`notify_decode`, `noti
... [truncated]

[Usage]
{"input_tokens": 10312, "output_tokens": 12854, "thinking_tokens": 0, "cache_read_tokens": 55284, "total_tokens": 23166}

[Result]
status=SUCCESS conversation=8cd2e846-cf0c-4d2b-b6f9-821e4550771e turns=5 duration=5472.772104306s usage={"input_tokens": 2667690, "output_tokens": 145934, "thinking_tokens": 60309, "cache_read_tokens": 9557076, "total_tokens": 2813624}


