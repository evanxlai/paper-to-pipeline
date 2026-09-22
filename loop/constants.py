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

# ---------------------------------------------------------------- plans
# Stage 2 artifacts, one pair per host: plan/<feature>.<host>.plan.json (how
# the feature goes into this model) and plan/<feature>.<host>.tests.json (how
# the gate will know it worked). Schema-checked by code, like the feature
# spec, and both record the host revision they were written against so a plan
# cannot be applied to a tree whose hook points nobody read.
PLAN_DIR = REPO_ROOT / "plan"
PORT_PLAN_SCHEMA_PATH = PLAN_DIR / "port_plan.schema.json"
TEST_PLAN_SCHEMA_PATH = PLAN_DIR / "test_plan.schema.json"
# One repair turn, like distill. Rounds exist in stage 1.5 because resolving
# one ambiguity spawns the next; stage 2's failures are a fixed deterministic
# list -- a spec item is either mapped or it is not -- so a second turn buys
# nothing a first turn with the whole finding list could not.
PLAN_REPAIR_TURNS = int(os.environ.get("P2P_PLAN_REPAIR_TURNS", "1"))
# The stage-2 twin of SPEC_ALLOW_ERRORS. An unmapped spec item is not a gap
# the integration agent notices and asks about; it is one the agent fills by
# guessing, and a guess that builds and runs is indistinguishable from a port.
PLAN_ALLOW_GAPS = os.environ.get("P2P_PLAN_ALLOW_GAPS", "0") == "1"
# How many times stage 3 may revise the plan pair it was handed, before it has
# to live with it (plan_revision.py). Small on purpose: the revisions this
# exists for are factual corrections about the tree, and a run that needs a
# fourth one is not correcting the plan any more -- it is rewriting it a line
# at a time to fit whatever it built, which is what the stage-2 re-run is for.
# Each revision also costs a gate run, so a generous budget spends the
# integration attempts on planning instead of on porting.
PLAN_REVISIONS = int(os.environ.get("P2P_PLAN_REVISIONS", "3"))

# ---------------------------------------------------------------- hosts
# Worker-side checkout paths (created by cluster worker_setup_commands under
# the cluster.yaml ssh_user's home, which is whatever account the Ray worker
# process runs as -- so default off that account's actual home dir rather
# than a hardcoded user, since ssh_user varies across cluster.yaml edits.
_WORKER_HOME = Path(os.environ.get("P2P_WORKER_HOME", str(Path.home())))
CBP2025_ROOT = os.environ.get("P2P_CBP2025_ROOT", str(_WORKER_HOME / "cbp2025"))
CHAMPSIM_ROOT = os.environ.get("P2P_CHAMPSIM_ROOT", str(_WORKER_HOME / "ChampSim"))
GEM5_ROOT = os.environ.get("P2P_GEM5_ROOT", str(_WORKER_HOME / "gem5"))
HOSTS = tuple(os.environ.get("P2P_HOSTS", "cbp2025").split(","))

# Where stage 3 puts the port. NOT CBP2025_ROOT: stage 2 reads that checkout
# to record `host_revision` and every clean-tree result in the test plan, and
# --stage baseline builds it to produce the numbers G2 compares against. An
# integration agent editing it in place would leave both of those describing
# a tree that no longer exists, and the next baseline run would measure the
# port instead of the host. The adapter copies CBP2025_ROOT here at the start
# of stage 3, so every attempt also starts from a clean tree.
CBP2025_PORT_ROOT = os.environ.get(
    "P2P_CBP2025_PORT_ROOT", str(_WORKER_HOME / "cbp2025_port")
)
# Whether stage 3 throws that tree away and copies a fresh one at the start
# of a run. On by default, because every attempt should begin from the same
# place and a tree carrying a previous run's half-port is a tree nobody can
# reason about. Turn it off to resume a run that died partway: the plan, the
# gate and the baseline are unchanged, so the agent picks up the tree it
# left and the next gate attempt judges it the same way.
CBP2025_PORT_FRESH = os.environ.get("P2P_CBP2025_PORT_FRESH", "1") == "1"

# Ray resource tokens, matching cluster/cluster.yaml available_node_types.
#
# Two, not one, and the split is load-bearing. CBP2025_RESOURCE is held by
# every node that has the traces on disk, and a trace run asks for it: a run
# receives the binary as bytes, so it never needs the checkout.
# CBP2025_HOST_RESOURCE is held by exactly one node -- the one that has the
# checkout -- and the agent's shell, the build, and any test command ask for
# that one instead. With a single token Ray could put the shell on one node
# and the build on another, and the build would compile a tree nobody edited.
CBP2025_RESOURCE = os.environ.get("P2P_CBP2025_RESOURCE", "cbp2025")
CBP2025_HOST_RESOURCE = os.environ.get("P2P_CBP2025_HOST_RESOURCE", "cbp2025_host")

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
# The list the verify gate's performance entries are meant to use: big enough
# to carry signal, small enough that six integration attempts do not spend an
# hour in the simulator. See its header for how the traces were chosen.
PERF_LIST = REPO_ROOT / "experiments" / "perf-8.list"
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
#
# Back to gemini-3.1-pro-high. It 404'd for a while after the account moved
# to GCP/Vertex auth, which is why this said gemini-3.8-flash-medium, and it
# serves again as of 2026-09-22 (smoke-tested with
# loop/tests/llm_cluster_smoke.py, which reaches the host checkout through
# the MCP shell and reads a real commit back). Stage 3 writes a
# multi-hundred-line C++ predictor from a spec, and the Flash tiers are the
# wrong tool for that.
#
# `agy models` lists what the account can see. Seeing a model listed is not
# the same as the project being entitled to it, so smoke-test after any
# change here rather than forty minutes into a planning run.
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

# ------------------------------------------------------------ llm gateway
# loop/llm_gateway.py: an OpenAI-compatible reverse proxy that injects a
# freshly-refreshed Vertex bearer per request, so consumers survive past the
# ~1h ADC token lifetime. Runs on the head as a systemd --user unit; see
# docs/llm-gateway.md. Bound to the head's VPC IP, so the shared secret is
# mandatory -- anything that can reach the port can spend the project's
# Vertex credits.
GATEWAY_HOST = os.environ.get("P2P_GATEWAY_HOST", os.environ.get("HEAD_IP", "127.0.0.1"))
GATEWAY_PORT = int(os.environ.get("P2P_GATEWAY_PORT", "8900"))
GATEWAY_URL = os.environ.get("P2P_GATEWAY_URL", f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/v1")
GATEWAY_TOKEN = os.environ.get("P2P_GATEWAY_TOKEN", "")

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
# Cap on ambiguities promoted to DSE knobs, counted across the WHOLE spec and
# therefore across rounds -- not per round. Each one is a real search
# dimension, so an unbounded reviewer can blow up the evolver's budget faster
# than it adds information, and a per-round cap silently multiplies by
# REVIEW_ROUNDS.
REVIEW_MAX_PROMOTED = int(os.environ.get("P2P_REVIEW_MAX_PROMOTED", "6"))
# Independent reviewers re-ask the same question in different words every
# round, and exact-string dedup never fires on a reword. Two questions about
# the same spec location whose *topic* signatures -- the spec identifiers and
# the numbers they mention -- overlap by this fraction are treated as one.
# Comparing full prose instead barely dedups at all: the shared content of two
# reworded questions is the identifiers, not the sentence around them.
REVIEW_QUESTION_SIMILARITY = float(
    os.environ.get("P2P_REVIEW_QUESTION_SIMILARITY", "0.5")
)
# A spec whose own arithmetic contradicts itself must not reach the
# integration agents: they implement from it alone, and a contradiction there
# becomes a silent wrong answer in the simulator rather than a build failure.
# The stage therefore fails closed on any remaining `error` finding, the same
# way it already fails closed on a schema error. Set to 1 only to inspect a
# known-bad spec deliberately.
SPEC_ALLOW_ERRORS = os.environ.get("P2P_SPEC_ALLOW_ERRORS", "0") == "1"
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
# _expand_env_vars leaves the literal text "${P2P_GATEWAY_TOKEN}" in place
# rather than raising, so the placeholder itself travels as the key and comes
# back as an opaque auth failure instead of "key not set". Forwarded only
# when actually set, so an unset credential stays unset and fails loudly
# rather than becoming an empty string.
#
# P2P_GATEWAY_TOKEN is the current route: both adaevolve configs point at the
# LLM gateway (loop/llm_gateway.py), which owns Vertex token refresh, so the
# secret the actor needs is the gateway's shared secret -- not a Google
# credential, and it does not expire. GEMINI_API_KEY is kept only for a
# config that still targets the public endpoint; note that endpoint is
# unfunded on this project (402 prepayment credits depleted).
#
# CAVEAT: Ray writes the resolved runtime_env into its own logs, so anything
# forwarded here is readable in /tmp/ray/session_*/logs/runtime_env*.log on
# the head. That now applies to a long-lived shared secret rather than a
# 60-minute token, so rotate it (edit the gateway env file and restart)
# rather than treating it as permanent.
for _cred in ("P2P_GATEWAY_TOKEN", "GEMINI_API_KEY", "GCP_PROJECT"):
    if os.environ.get(_cred):
        RUNTIME_ENV["env_vars"][_cred] = os.environ[_cred]

# Not a credential, but it has to travel the same way and for the same
# reason: the adaevolve configs name the gateway as ${P2P_GATEWAY_URL}, and
# skydiscover expands that inside the EvolverNode actor rather than in the
# submitting shell. Always forwarded, because unlike a secret there is
# nothing to leak, and on a miss _expand_env_vars leaves the literal text
# "${P2P_GATEWAY_URL}" in place as a host name.
RUNTIME_ENV["env_vars"]["P2P_GATEWAY_URL"] = GATEWAY_URL
