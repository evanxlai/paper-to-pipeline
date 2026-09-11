"""All knobs for the adopt-a-paper loop, memcpy-example style:
every value is env-overridable with a P2P_ prefix so a `chia job submit
--runtime-env-json '{"env_vars": {...}}'` can retune a run without edits.

Feature naming: the accepted proposal calls the ported feature "RBias".
The RUNLTS paper (CBP2025, Koizumi et al.) names it "sR" (register
components of the statistical corrector). Code uses "sr" everywhere;
docs carry the alias once.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOOP_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = LOOP_DIR / "prompts"
OUT_DIR = REPO_ROOT / "out"

FEATURE_NAME = os.environ.get("P2P_FEATURE_NAME", "sr")

# ---------------------------------------------------------------- inputs
# Paper text (extracted) + optional reference artifact, per the two
# distillation ablation arms.
PAPER_TEXT_PATH = os.environ.get(
    "P2P_PAPER_TEXT", str(REPO_ROOT / "third_party" / "runlts" / "runlts.txt")
)
REFERENCE_ARTIFACT_DIR = os.environ.get(
    "P2P_REFERENCE_ARTIFACT", str(REPO_ROOT / "third_party" / "runlts" / "artifact")
)
DISTILL_MODE = os.environ.get("P2P_DISTILL_MODE", "paper_only")  # or paper_plus_reference
SPEC_SCHEMA_PATH = REPO_ROOT / "spec" / "feature_spec.schema.json"
SPEC_OUT_PATH = REPO_ROOT / "spec" / f"{FEATURE_NAME}.{DISTILL_MODE}.json"

# ---------------------------------------------------------------- hosts
# Worker-side checkout paths (created by cluster worker_setup_commands).
CBP2025_ROOT = os.environ.get("P2P_CBP2025_ROOT", "/home/ray/cbp2025")
CHAMPSIM_ROOT = os.environ.get("P2P_CHAMPSIM_ROOT", "/home/ray/ChampSim")
GEM5_ROOT = os.environ.get("P2P_GEM5_ROOT", "/home/ray/gem5")
HOSTS = tuple(os.environ.get("P2P_HOSTS", "champsim,gem5").split(","))

# ---------------------------------------------------------------- traces
# CBP2025: 105 training traces (Google Drive; see scripts/fetch_artifacts.sh).
# Worker-local dir, laid out <workload>/<name>_trace.gz as the CBP kit expects.
TRACE_DIR = os.environ.get("P2P_TRACE_DIR", "/home/ray/traces/cbp2025")
SCREENING_LIST = REPO_ROOT / "experiments" / "screening-60.list"
FULL_LIST = REPO_ROOT / "experiments" / "training-105.list"
SMOKE_LIST = REPO_ROOT / "experiments" / "smoke-5.list"
# ChampSim uses its own trace format; separate suite (DPC-3 SPEC or self-traced).
CHAMPSIM_TRACE_DIR = os.environ.get("P2P_CHAMPSIM_TRACE_DIR", "/home/ray/traces/champsim")

# ---------------------------------------------------------------- budgets
# Our experiment design tunes at two iso-storage points. Note: the CBP2025
# contest itself has a single 192 KiB budget; 64 KiB is our added
# constrained point (proposal commitment).
BUDGET_TRACKS_BITS = {
    "iso-192KiB": 192 * 1024 * 8,
    "iso-64KiB": 64 * 1024 * 8,
}

# ---------------------------------------------------------------- llm
LLM_BACKEND = os.environ.get("P2P_LLM_BACKEND", "antigravity")  # claude|antigravity|opencode
# Gemini per the proposal budget; agy effort tier rides on the model id.
ANTIGRAVITY_MODEL = os.environ.get("P2P_ANTIGRAVITY_MODEL", "gemini-3.1-pro-high")
OPENCODE_MODEL = os.environ.get("P2P_OPENCODE_MODEL", "google-vertex/gemini-3.1-pro-preview")
CLAUDE_MODEL = os.environ.get("P2P_CLAUDE_MODEL", "claude-opus-4-6")
OPENCODE_VERTEX_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
OPENCODE_VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
LLM_TIMEOUT_SECONDS = int(os.environ.get("P2P_LLM_TIMEOUT", "7200"))

# Resource tokens must match cluster/cluster.yaml available_node_types.
LLM_RESOURCE = {"llm": 1.0}
ANTIGRAVITY_RESOURCE = {"antigravity_creds": 1.0}
OPENCODE_RESOURCE = {"opencode_creds": 1.0}

# ---------------------------------------------------------------- loop
NUM_INTEGRATION_ATTEMPTS = int(os.environ.get("P2P_INTEGRATION_ATTEMPTS", "6"))
BUILD_TIMEOUT_S = int(os.environ.get("P2P_BUILD_TIMEOUT", "1800"))
RUN_TIMEOUT_S = int(os.environ.get("P2P_RUN_TIMEOUT", "3600"))
BASH_TOOL_TIMEOUT_S = 300  # short on purpose; long work goes through host nodes

# ---------------------------------------------------------------- dse
DSE_BACKEND = os.environ.get("P2P_DSE_BACKEND", "adaevolve")  # adaevolve|alphaevolve
DSE_MAX_ITERATIONS = int(os.environ.get("P2P_DSE_ITERATIONS", "250"))
DSE_SCREEN_METRIC = "brmispki_50perc_amean"
DSE_PROMOTE_TOP_K = int(os.environ.get("P2P_DSE_TOP_K", "5"))

RUNTIME_ENV = {
    "working_dir": str(LOOP_DIR),
    "excludes": ["../out/", "__pycache__"],
}
