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
# Worker-side checkout paths (created by cluster worker_setup_commands under
# the cluster.yaml ssh_user's home, which is whatever account the Ray worker
# process runs as -- so default off that account's actual home dir rather
# than a hardcoded user, since ssh_user varies across cluster.yaml edits.
_WORKER_HOME = Path(os.environ.get("P2P_WORKER_HOME", str(Path.home())))
CBP2025_ROOT = os.environ.get("P2P_CBP2025_ROOT", str(_WORKER_HOME / "cbp2025"))
CHAMPSIM_ROOT = os.environ.get("P2P_CHAMPSIM_ROOT", str(_WORKER_HOME / "ChampSim"))
GEM5_ROOT = os.environ.get("P2P_GEM5_ROOT", str(_WORKER_HOME / "gem5"))
HOSTS = tuple(os.environ.get("P2P_HOSTS", "champsim,gem5").split(","))

# ---------------------------------------------------------------- traces
# CBP2025: 105 training traces (Google Drive; see scripts/fetch_artifacts.sh).
# Worker-local dir, laid out <workload>/<name>_trace.gz as the CBP kit expects.
# Off _WORKER_HOME like CBP2025_ROOT above: hardcoding /home/ray assumes the
# Ray worker process runs as a "ray" user, which does not hold for cluster.yaml
# configs (like this project's) that set sim_worker ssh_user to something else.
TRACE_DIR = os.environ.get("P2P_TRACE_DIR", str(_WORKER_HOME / "traces" / "cbp2025"))
SCREENING_LIST = REPO_ROOT / "experiments" / "screening-60.list"
FULL_LIST = REPO_ROOT / "experiments" / "training-105.list"
SMOKE_LIST = REPO_ROOT / "experiments" / "smoke-5.list"
# ChampSim uses its own trace format; separate suite (DPC-3 SPEC or self-traced).
CHAMPSIM_TRACE_DIR = os.environ.get(
    "P2P_CHAMPSIM_TRACE_DIR", str(_WORKER_HOME / "traces" / "champsim")
)

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
# Gemini per the proposal budget; agy effort tier rides on the model id
# (-high/-medium/-low select reasoning effort, not a different model).
# Was gemini-3.1-pro-high until the account moved to GCP/Vertex auth: the Pro
# preview publisher model is not enabled for this project and 404s, while the
# 3.8 Flash family serves fine. `agy models` lists what the account can see;
# availability still has to be smoke-tested per project.
ANTIGRAVITY_MODEL = os.environ.get("P2P_ANTIGRAVITY_MODEL", "gemini-3.8-flash-medium")
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

# ------------------------------------------------------------ spec review
# Stage 1.5: evidence-checked review of the distilled spec before it reaches
# the integration agents. Off-switchable so ablation 2 can measure what the
# stage is worth (distill-only vs distill+review, same yardstick).
SPEC_REVIEW = os.environ.get("P2P_SPEC_REVIEW", "1") == "1"
REVIEW_ROUNDS = int(os.environ.get("P2P_REVIEW_ROUNDS", "3"))
# One reviewer per spec unit; merge the smallest units past this many, so a
# spec with a long algorithm list cannot fan out without bound.
REVIEW_MAX_UNITS = int(os.environ.get("P2P_REVIEW_MAX_UNITS", "12"))
# A string field that keeps less than this fraction of its length counts as a
# regression and must be justified by a patch.
REGRESSION_RATIO = float(os.environ.get("P2P_REGRESSION_RATIO", "0.4"))
# Cap on ambiguities promoted to DSE knobs per round. Each one is a real search
# dimension, so an unbounded reviewer can blow up the evolver's budget faster
# than it adds information.
REVIEW_MAX_PROMOTED = int(os.environ.get("P2P_REVIEW_MAX_PROMOTED", "6"))
# Coverage runs one call per chunk; papers under this size take a single call.
COVERAGE_CHUNK_CHARS = int(os.environ.get("P2P_COVERAGE_CHUNK_CHARS", "60000"))
BUILD_TIMEOUT_S = int(os.environ.get("P2P_BUILD_TIMEOUT", "1800"))
RUN_TIMEOUT_S = int(os.environ.get("P2P_RUN_TIMEOUT", "3600"))
BASH_TOOL_TIMEOUT_S = 300  # short on purpose; long work goes through host nodes

# ---------------------------------------------------------------- dse
DSE_BACKEND = os.environ.get("P2P_DSE_BACKEND", "adaevolve")  # adaevolve|alphaevolve
# Which evolve-flows search config --stage dse hands to run_dse. Overridable so
# a smoke run can use config_adaevolve_smoke{,_vertex}.yaml (3 iterations,
# pop 2) without editing the entrypoint; the default is the full 250-iteration
# search. NOTE the smoke_vertex variant is the only one that works without a
# GEMINI_API_KEY -- see that file's header for why the model must be named
# "google/<model>" rather than "gemini-<model>".
DSE_CONFIG = os.environ.get(
    "P2P_DSE_CONFIG", str(REPO_ROOT / "experiments" / "config_adaevolve.yaml")
)
DSE_MAX_ITERATIONS = int(os.environ.get("P2P_DSE_ITERATIONS", "250"))
DSE_SCREEN_METRIC = "brmispki_50perc_amean"
DSE_PROMOTE_TOP_K = int(os.environ.get("P2P_DSE_TOP_K", "5"))

RUNTIME_ENV = {
    "working_dir": str(REPO_ROOT),
    "excludes": ["../out/", "__pycache__"],
    # "." lets workers import chia_nodes; "loop" is needed too because the
    # stage-3 EvolverNode actor re-imports loop/sr_evaluator.py by name when
    # it unpickles the evaluator (see loop/sr_evaluator.py's docstring).
    # Without it that unpickle dies with ModuleNotFoundError: 'sr_evaluator'.
    "env_vars": {"PYTHONPATH": ".:loop"},
}

# Credentials the stage-3 EvolverNode actor needs in its *own* environment.
# skydiscover's Config.from_yaml expands ${VAR} from os.environ inside the
# actor process, not in the submitting shell -- and on a miss its
# _expand_env_vars leaves the literal text "${GEMINI_API_KEY}" in place
# rather than raising, so the placeholder itself travels to the API as the
# key and comes back as an opaque auth failure instead of "key not set".
# Forwarded only when actually set, so an unset credential stays unset and
# fails loudly rather than becoming an empty string.
#
# GEMINI_API_KEY drives config_adaevolve.yaml (public endpoint, permanent
# key); VERTEX_ACCESS_TOKEN + GCP_PROJECT drive
# config_adaevolve_smoke_vertex.yaml (ADC bearer, expires hourly -- see
# docs/dse-setup.md). Whichever is exported is the route you get.
#
# CAVEAT: Ray writes the resolved runtime_env into its own logs, so anything
# forwarded here is readable in /tmp/ray/session_*/logs/runtime_env*.log on
# the head. Fine for a short-lived ADC token, worth knowing for a permanent
# API key.
for _cred in ("GEMINI_API_KEY", "VERTEX_ACCESS_TOKEN", "GCP_PROJECT"):
    if os.environ.get(_cred):
        RUNTIME_ENV["env_vars"][_cred] = os.environ[_cred]
