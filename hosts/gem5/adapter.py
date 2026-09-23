"""gem5 v25.1 (ARM, syscall emulation), as stages 2 and 3 and the verify gate
see it.

This is hosts/cbp2025/adapter.py moved to a simulator whose binary cannot
travel. A CBP2025 build is small, so that host ships it to the trace nodes
as bytes. A gem5.opt is built with -g (src/SConscript:681), and
chia.simulators.gem5 is path-based because such a binary is too large to
ship per run: a run names a binary on the filesystem of the node that built
it. So there is one token here, not the cbp2025 pair:

  gem5_host   exactly one node. The pristine checkout, the port tree, the
              search tree, the run scripts and the workloads all live on it.
              The agent's shell, every build, every run and every command a
              test plan names ask for this token, because each of them
              reads a path that exists only there. The node advertises 30 of
              it, so 30 single-threaded gem5 runs fan out side by side.

It is not chia's own "gem5" token, and nothing here constructs a Gem5Node.
Gem5Node's placement group reserves a {"gem5": 1} bundle, which runs one
task at a time and names a token another node may still advertise. The raw
class attributes are dispatched with `.options(resources=...)` instead, the
way the cbp2025 adapter uses CBP2025Node.

What this file deliberately does not decide: which workloads to run, which
metrics to compare, at what tolerance, or what counts as the feature
working. All of that is in the test plan, because a gate condition hardcoded
here is one the plan cannot state and a reader cannot audit. What stays is
what no plan can express: how to build this host, how to flip its knob, how
to run a workload, and how to get numbers out of a run.

Storage is not one of the gate's questions. Only the DSE stage knows about
resource constraints (docs/stages.md), so nothing here carries a budget. The
`budget` argument of `record_baseline` is the name of the file G2 reads, as
it is for record_cbp_baseline, and nothing more.

Every hazard the cbp2025 adapter handles has a twin below. Where it went:

  pristine tree vs port tree    restore_host_checkout, clean_port_tree
  restore refusing the port     restore_host_checkout (and the search tree)
  agent leftovers               restore_checkout, materialize_port_tree
  port diff hygiene             port_diff
  a fresh executor per attempt  run_gate
  compile-time vs runtime knob  Gem5Executor.build / _ensure_tree_state
  a build that left no binary   scons_build, Gem5Executor.run_traces
  a Ray task that died          run_workloads, and every get() in the executor

Three more that only this host has, because its run scripts and workloads
sit in a directory the agent's shell can reach, and its node can vanish:

  an edit to the run dir        install_run_dir, reinstalled by every run_gate
  a baseline that went stale    check_baseline_current, called by run_gate
  a node that never answers     _wait, which every get() goes through

gem5 facts below cite REPO/third_party/gem5 at v25.1.0.0 (7a2b0e4).
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import posixpath
import re
import shlex
import shutil
import signal
import subprocess
import tarfile
import time
import uuid
from pathlib import Path
from typing import Mapping, NamedTuple, Optional, Sequence

from chia.base.ChiaFunction import ChiaFunction, get
from chia.simulators.gem5 import Gem5Node
from ray.exceptions import GetTimeoutError

import constants as C
import gate
import helpers
import plan_runner
from hosts.gem5.run import p2p_metrics

HOST = "gem5"
HERE = Path(__file__).resolve().parent
NOTES_PATH = HERE / "NOTES.md"
# The run scripts: se_o3.py, run_workload.py, p2p_metrics.py. Installed on the
# node next to the workloads by install_run_dir.
RUN_SCRIPTS_DIR = HERE / "run"
# The head's read-only mirror of the worker's checkout. Stage 2's
# deterministic plan checks open hook-point files here, so it has to be at
# the worker's commit.
MIRROR_ROOT = C.REPO_ROOT / "third_party" / "gem5"

# The names p2p_metrics derives, which are therefore the only names a test
# plan's `metric_keys` may use. One run through run_workload.py and a fan-out
# of sixty runs through run_traces produce the same keys, so a G2 entry that
# runs one workload compares like with like against `per_trace`.
METRIC_KEYS = tuple(p2p_metrics.METRIC_KEYS)

# gem5 v25.1 reads these from the process environment and not from the scons
# command line. EnvDefaults copies them out of os.environ
# (site_scons/gem5_scons/defaults.py:46-103). The only command-line variable
# the SConstruct still reads is EXTRAS (SConstruct:875), and the kconfig
# release note says `scons NAME=value` stopped working
# (RELEASE-NOTES.md:803-807). So `CC=... CXX=...` in GEM5_SCONS_ARGS does
# nothing on the command line, and the adapter moves those settings into the
# build's environment instead.
_SCONS_ENV_VARS = frozenset({
    "CC", "CXX", "PROTOC", "PYTHON_CONFIG", "CCFLAGS_EXTRA",
    "GEM5PY_CCFLAGS_EXTRA", "GEM5PY_LINKFLAGS_EXTRA", "LINKFLAGS_EXTRA",
})

# Bindings this host can deliver, and how. A runtime_env knob reaches the
# port through the gem5 process's environment, so one binary serves both
# states. A define reaches it through CCFLAGS_EXTRA, so each state is its own
# build. The rest cannot be delivered at all: the run scripts are fixed and
# read no knob, and a Python param or a constructor argument would have to be
# set in se_o3.py.
_DEFINE_BINDINGS = frozenset({"compile_time_define", "build_config"})
_UNDELIVERABLE_BINDINGS = frozenset({"python_param", "constructor_arg", "other"})
_C_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# `git clean -x` ignores .gitignore, which is the point: it removes what an
# agent left even when gem5's .gitignore hides it (m5out, *.pyc; see
# .gitignore:9,13). `-e /build/` is the one exception. With -x, git still
# honours patterns given by -e, and the leading slash anchors it to the top
# level, so a `build/` an agent made under src/ is still removed. Checked on
# git 2.34 with a scratch repository.
_CLEAN_ARGS = ("clean", "-fdx", "-e", "/build/")

# stderr goes to <outdir>/simerr.txt (src/python/m5/main.py:116-137,
# 424-449). run_gem5 captures stderr and then drops it: its result holds only
# a stdout tail. gem5's fatal() and panic() messages go to stderr, and they
# are the one line a debug turn needs, so they have to land somewhere the
# adapter can read back.
_GEM5_ARGS = ("--redirect-stderr",)

# se_o3.py prints exactly one of these when the simulation ends.
_EXIT_LINE = re.compile(r"^P2P_EXIT cause=(?P<cause>.*) code=(?P<code>\S+)\s*$", re.M)
# run_workload.py ends with `P2P_STATUS ok` or `P2P_STATUS failed <reason>`.
_STATUS_LINE = re.compile(r"^P2P_STATUS\s+(\S+)", re.M)

_PAYLOAD_MARKER = ".p2p_payload.json"
# A fixed mtime and owner for every payload member, so the same files always
# produce the same bytes and install_run_dir can skip an unchanged payload.
_PAYLOAD_MTIME = 946684800  # 2000-01-01

# How long a get() waits past the task's own limit before it calls the node
# lost. Every task here has a limit of its own (a run, a build, a shell
# command), and each kills its process group when that limit passes. So a
# task that is still silent this long after its limit never started, or its
# node is gone. Ray does not fail a task whose node disappeared: it keeps it
# waiting for a resource nobody advertises any more, and a get() with no
# timeout then waits for ever.
_GET_MARGIN_S = 300
# The limit for a short task that has none of its own: an install, a
# restore, a copy, a revision read. It still needs a gem5_host slot, and when
# every slot is busy, one frees within one run's limit.
_SHORT_TASK_LIMIT_S = C.GEM5_RUN_TIMEOUT_S
# After one run of a fan-out timed out, how long each later run gets to be
# already finished. Waiting the full limit again for each of them would turn
# one lost node into a wait of hours per workload.
_AFTER_STALL_WAIT_S = 1


class UnknownWorkloadError(LookupError):
    """A workload name that hosts/gem5/workloads.json does not have."""


class Gem5NodeTimeout(RuntimeError):
    """A gem5 task gave no result long after its own limit.

    A RuntimeError, so every place that already turns a failed task into a
    failed build, command or workload does the same with this one."""


def _cancel_quietly(ref) -> None:
    """Take an abandoned task off the node, best effort.

    A run that never got a slot would otherwise start later, hold that slot
    and write an outdir after the gate moved on. ray.cancel only sends a
    request, so a lost node cannot make this block."""
    try:
        import ray

        ray.cancel(getattr(ref, "ref", ref))
    except Exception:  # noqa: BLE001 - the verdict is already decided
        pass


def _wait(ref, limit_s: float, what: str, wait_s: Optional[float] = None):
    """get(ref), waiting at most the task's own limit plus _GET_MARGIN_S.

    `wait_s` replaces that wait when the caller already knows the node
    stopped answering. A timeout raises Gem5NodeTimeout with a reason that
    names the node, and the task is cancelled."""
    wait = int(limit_s) + _GET_MARGIN_S if wait_s is None else wait_s
    try:
        return get(ref, timeout=wait)
    except GetTimeoutError:
        _cancel_quietly(ref)
        raise Gem5NodeTimeout(
            f"{what} gave no result after {wait}s. The {C.GEM5_HOST_RESOURCE} node is "
            f"lost or stuck, or another job holds every {C.GEM5_HOST_RESOURCE} slot."
        ) from None


# --------------------------------------------------------------- remote work


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 1.0})
def host_shell(cwd: str, command: str, env: dict | None, timeout_s: int) -> dict:
    """One shell command on the node that holds the checkouts.

    `output` is the command's own stdout and stderr and nothing else. It is
    not prefixed with the command line: a `stdout_excludes` pass condition is
    matched against this text, so an echoed command would let the entry fail
    on a word that appears only in its own invocation.

    Two changes from the cbp2025 version, both because a gem5 command runs
    for minutes and prints what its guest prints:

    - The command gets its own process group, and a timeout kills the group.
      subprocess.run kills only the shell. A gem5 under it then keeps
      running, holds the captured pipes open, and the call waits for it to
      finish anyway. chia.simulators.gem5._run_logged does the same thing
      for the same reason.
    - Output is decoded with errors="replace". A guest that prints a byte
      that is not UTF-8 would otherwise raise here, and the gate would lose
      the whole entry to a decoding error.

    Returns a dict rather than raising, for plan_runner's reason: a hung or
    crashed test is a gate failure with a diagnosis."""
    merged = {**os.environ, **{k: str(v) for k, v in (env or {}).items()}}
    try:
        proc = subprocess.Popen(
            command, shell=True, cwd=cwd, env=merged, text=True, errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
    except OSError as e:
        return {"exit_code": -1, "output": f"[could not run {command!r}: {e}]",
                "timed_out": False}
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        return {
            "exit_code": -1,
            "output": f"{out or ''}{err or ''}\n[{command!r} timed out after {timeout_s}s]",
            "timed_out": True,
        }
    return {"exit_code": proc.returncode, "output": out + err, "timed_out": False}


def _git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _remove_tree(path: Path) -> None:
    """Delete a directory tree, a file or a symlink, without following links."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 1.0})
def restore_checkout(root: str) -> dict:
    """Put a checkout back to the commit it claims to be at, keeping build/.

    An agent with a shell leaves things behind. On the cbp2025 host, stage
    2's planner once left a `test_sr.cc` printing "Test passed" in the
    checkout, it travelled into the port tree, and seven spec unit tests
    passed against a tree nobody had ported into. `reset --hard` plus
    `clean -fdx` is the only reliable answer, because there is no list of
    "files an agent might leave".

    build/ is the exception, and it is kept on purpose. The pristine build
    took 670 s on the 32-vCPU node (2026-09-23), and scons keeps its
    signature database inside it (build/<ISA>/gem5.build/sconsign,
    SConstruct:573-581), so a deleted build/ is a full rebuild. Keeping it is safe for the sources: scons
    decides by content (Decider "MD5-timestamp",
    site_scons/gem5_scons/defaults.py:109), so a source file the reset
    reverted is recompiled on the next build.

    What build/ can still hide is a binary an agent built from a source it
    then deleted. The source goes, the binary stays. A test plan command
    must therefore build its own test from source rather than run a path
    under build/ that it did not just build."""
    if not Path(root).is_dir():
        return {"ok": False, "root": root, "error": f"{root} does not exist on this node"}
    before = _git(root, "status", "--porcelain").stdout
    _git(root, "reset", "--hard", "HEAD")
    removed = _git(root, *_CLEAN_ARGS).stdout
    return {
        "ok": True,
        "root": root,
        "was_dirty": bool(before.strip()),
        "removed": [line for line in removed.splitlines() if line.strip()],
        "kept": ["build/"],
        "revision": _git(root, "rev-parse", "HEAD").stdout.strip(),
    }


def _copy_refusal(source: Path, target: Path) -> str:
    """Why copying `source` to `target` would destroy something, or ""."""
    src = os.path.realpath(source)
    dst = os.path.realpath(target)
    pristine = os.path.realpath(C.GEM5_ROOT)
    if dst == src:
        return f"{target} is {source} itself"
    if dst.startswith(src + os.sep) or src.startswith(dst + os.sep):
        return f"{target} and {source} contain one another"
    if dst == pristine:
        return (f"{target} is the pristine checkout {C.GEM5_ROOT}, and a fresh "
                f"copy starts by deleting what is there")
    return ""


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 1.0})
def materialize_port_tree(
    src: str, dst: str, fresh: bool = True, reset: bool = True
) -> dict:
    """Lay down the tree stage 3 may edit, as a copy of the pristine
    checkout reset to the commit the plan was written against.

    The agent never edits `src`. Stage 2 read that tree to record
    `host_revision` and every clean-tree result, and `--stage baseline`
    builds it to produce the numbers G2 compares against. An agent editing
    it in place would leave both describing a tree that no longer exists.

    The copy takes `.git` and `build/`. `.git` so the port tree answers
    `git rev-parse HEAD` and `git diff`, which is how a run is reviewed
    afterwards. `build/` makes the copy's first build mostly incremental:
    in three gate smoke runs on 2026-09-23, that build plus about 90 s of
    gem5 runs took 336 to 376 s in all, against 670 s for a build from scratch.
    build/ carries the build's configuration (build/<ISA>/gem5.build), and
    scons rebuilds whatever differs.

    It is `cp -a`, not shutil.copytree. A gem5 build/ is many thousands of
    files and many gigabytes (the size and the copy time are
    TODO(measured); the result's `copy_s` records the time). `cp -a` copies
    it in one native process. It keeps
    symlinks as symlinks, hard links as hard links, and every mode and
    mtime. copytree(symlinks=True) keeps the links and the mtimes too, but it
    copies each hard link as a separate file and pays Python's per-file
    overhead. The mtimes matter: with "MD5-timestamp" scons re-hashes every
    file whose mtime moved, which is correct but slow. The copy lands in a
    staging directory first and is renamed into place, so a copy that fails
    or dies partway never sits at `dst`, where `fresh=False` would reuse it.

    A fresh tree is then reset and cleaned rather than trusted, keeping
    build/ (see restore_checkout for what the planner left the first time).
    With `reset=False` the copy is kept exactly as the source had it, build
    output included. That is what the search tree wants: the port is the
    thing being tuned.
    """
    source, target = Path(src), Path(dst)
    if not source.exists():
        return {"ok": False, "error": f"{src} does not exist on this node"}
    refusal = _copy_refusal(source, target)
    if refusal:
        return {"ok": False, "error": f"refusing to copy {src} to {dst}: {refusal}"}
    if fresh and (target.exists() or target.is_symlink()):
        _remove_tree(target)
    created = not target.exists()
    copy_s = 0.0
    if created:
        staging = target.with_name(f".{target.name}.partial-{os.getpid()}")
        if staging.exists() or staging.is_symlink():
            _remove_tree(staging)
        t0 = time.time()
        proc = subprocess.run(["cp", "-a", "--", str(source), str(staging)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            if staging.exists():
                _remove_tree(staging)
            return {"ok": False,
                    "error": f"cp -a {src} {dst} failed (exit {proc.returncode}): "
                             f"{(proc.stderr or proc.stdout)[-2000:]}"}
        os.rename(staging, target)
        copy_s = time.time() - t0
    # Only a tree we just laid down. Resetting an existing one would delete
    # the port it holds, which is the opposite of what `fresh=False` is for:
    # that flag exists so a run which died partway can pick up its tree.
    removed = ""
    if created and reset:
        _git(target, "reset", "--hard", "HEAD")
        removed = _git(target, *_CLEAN_ARGS).stdout
    return {
        "ok": True,
        "path": str(target),
        "reused": not created,
        "copy_s": round(copy_s, 1),
        "revision": _git(target, "rev-parse", "HEAD").stdout.strip()
                    or "(not a git checkout)",
        "cleaned": [line for line in removed.splitlines() if line.strip()],
    }


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 0.1})
def host_revision(root: str) -> str:
    """The commit a checkout is at, read on the node that has it.

    Stage 2 asks the planning agent to record this itself, and this is what
    the answer is checked against."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
    )
    return proc.stdout.strip() or "(not a git checkout)"


def _extract_payload(payload: bytes, dest: Path) -> list:
    """Unpack a payload tarball into `dest`. Returns the regular files."""
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
        members = tar.getmembers()
        for m in members:
            parts = Path(m.name).parts
            if m.name.startswith("/") or ".." in parts:
                raise ValueError(f"payload member {m.name!r} escapes the run dir")
        # The "data" filter refuses links that point outside `dest` and drops
        # setuid bits. It keeps the owner's execute bit.
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:  # pragma: no cover - Python older than 3.10.12
            tar.extractall(dest)
    return sorted(m.name for m in members if m.isfile())


def _file_digests(root: Path, names) -> dict:
    """sha256 of each named file under `root`, or None for one that is gone."""
    out = {}
    for name in names:
        try:
            out[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        except OSError:
            out[name] = None
    return out


def _install_scratch(name: str) -> bool:
    """A staging dir, a trash dir or a marker being written, by some install."""
    return name.startswith((".staging-", ".replaced-", f".{_PAYLOAD_MARKER}."))


def _not_payload(name: str) -> bool:
    """A top-level name in the run dir that no payload owns: runs/, the
    marker, and the scratch of an install that may be running now."""
    return name in ("runs", _PAYLOAD_MARKER) or _install_scratch(name)


def _purge_caches(root: Path) -> list:
    """Delete every __pycache__ in the run dir, apart from runs/.

    run_workload.py imports p2p_metrics from its own directory, so every run
    leaves a __pycache__ here. Counted as an added file, it would make every
    install a reinstall. Left alone, it is the one place a planted .pyc could
    hide. Python rebuilds the cache from the checked sources."""
    removed = []
    for dirpath, dirnames, _ in os.walk(root):
        here = Path(dirpath)
        if here == root:
            dirnames[:] = [d for d in dirnames if not _not_payload(d)]
        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")
            _remove_tree(here / "__pycache__")
            removed.append((here / "__pycache__").relative_to(root).as_posix())
    return removed


def _present_files(root: Path) -> set:
    """Every entry under `root` that is not a directory, as a relative path.

    Leaves out runs/, the marker and install scratch at the top level. A
    symlink to a directory counts as a file: os.walk lists it with the
    directories and does not descend it, and it is an entry the payload
    never had."""
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel = here.relative_to(root)
        if here == root:
            dirnames[:] = [d for d in dirnames if not _not_payload(d)]
            filenames = [f for f in filenames if not _not_payload(f)]
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        out.update((rel / d).as_posix() for d in dirnames if (here / d).is_symlink())
        out.update((rel / f).as_posix() for f in filenames)
    return out


def _drift(root: Path, previous: dict) -> dict:
    """How the run dir differs from what the last install recorded.

    `changed` has other contents, `missing` is gone, and `added` is a file
    the payload does not have. An added file needs no edit to change a run:
    a p2p_metrics/__init__.py next to p2p_metrics.py is imported in its
    place, and a sitecustomize.py runs in every Python that starts there."""
    recorded = previous.get("file_sha256") or {}
    now = _file_digests(root, recorded)
    gone_entries = {e for e in previous.get("entries", []) if not (root / e).exists()}
    return {
        "changed": sorted(n for n, d in now.items() if d is not None and d != recorded[n]),
        "missing": sorted({n for n, d in now.items() if d is None} | gone_entries),
        "added": sorted(_present_files(root) - set(recorded)),
    }


def _describe_drift(drift: dict, limit: int = 10) -> str:
    parts = []
    for kind in ("changed", "added", "missing"):
        names = drift.get(kind) or []
        if names:
            more = f" and {len(names) - limit} more" if len(names) > limit else ""
            parts.append(f"{kind} {', '.join(names[:limit])}{more}")
    return "; ".join(parts)


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 1.0})
def install_run_dir(payload: bytes, dest: str) -> dict:
    """Unpack the run scripts and workloads into `dest` on this node.

    Idempotent by content: the marker file records the payload's sha256 and
    the sha256 of every file it unpacked. The same payload a second time is
    a no-op only while every one of those files still has its recorded
    contents and no other file sits next to them. That is the common case,
    because stages 2 and 3 install at every start and run_gate installs at
    every attempt. The check is the guard that matters: an agent's shell can
    reach this directory. An edit to se_o3.py or p2p_metrics.py, or an added
    file that shadows one, would otherwise reach every gate run and every
    baseline while the marker still vouched for the payload. `why` and
    `drift` in the result say what forced a reinstall.

    __pycache__ directories are deleted first and never counted (see
    _purge_caches).

    `dest` stays a real directory, and every guest-visible path keeps one
    spelling. That matters for G2. The guest's argv[0] is the binary's path,
    and it sits on the guest's initial stack. The baseline and the gate's own
    runs have to present the same string, or the stack moves and the metrics
    move with it. A versioned directory behind a symlink would give every
    path two spellings, one of which changes with each payload.

    So the install is atomic per entry, not as a whole. The new payload is
    unpacked into a staging directory. The marker is removed. Each top-level
    entry is swapped in with a rename, and every other top-level entry is
    moved out, apart from runs/ and the scratch of an install in progress.
    The marker is written last. A task that dies partway leaves no marker,
    so the next install redoes the work instead of trusting a half-installed
    directory.

    `runs/`, where every gem5 outdir goes, is never touched. Do not install
    a changed payload while runs are in flight: their guests read files
    from `workloads/`."""
    digest = hashlib.sha256(payload).hexdigest()
    root = Path(dest)
    marker = root / _PAYLOAD_MARKER
    try:
        previous = json.loads(marker.read_text()) if marker.is_file() else {}
    except (OSError, ValueError):
        previous = {}
    record = {"ok": True, "dest": str(root), "sha256": digest, "bytes": len(payload)}
    try:
        purged = _purge_caches(root) if root.is_dir() else []
    except OSError as e:
        return {**record, "ok": False, "error": f"could not clear __pycache__: {e}"}
    record["purged"] = purged
    recorded = previous.get("file_sha256") or {}
    drift = None
    if not previous:
        why = "no marker: a first install, or one that died partway"
    elif previous.get("sha256") != digest:
        why = (f"the payload changed (sha256 {str(previous.get('sha256'))[:12]} -> "
               f"{digest[:12]})")
    elif not recorded or set(recorded) != set(previous.get("files", [])):
        why = "the marker lists no per-file digests to check against"
    else:
        drift = _drift(root, previous)
        if not any(drift.values()):
            return {**record, "installed": False,
                    "entries": previous.get("entries", []),
                    "files": previous.get("files", [])}
        why = f"the installed files drifted from the payload: {_describe_drift(drift)}"

    staging = root / f".staging-{digest[:12]}-{os.getpid()}"
    trash = root / f".replaced-{digest[:12]}-{os.getpid()}"
    try:
        root.mkdir(parents=True, exist_ok=True)
        (root / "runs").mkdir(exist_ok=True)
        for scratch in (staging, trash):
            if scratch.exists():
                _remove_tree(scratch)
        staging.mkdir()
        files = _extract_payload(payload, staging)
        entries = sorted(p.name for p in staging.iterdir())
        if "runs" in entries or _PAYLOAD_MARKER in entries:
            raise ValueError("a payload must not carry runs/ or the marker file")
        # Every top-level name the new payload does not own: an entry an
        # older payload had, and anything an agent added.
        stale = sorted(n for n in os.listdir(root)
                       if n not in entries and not _not_payload(n))
        marker.unlink(missing_ok=True)
        trash.mkdir()
        for name in entries + stale:
            here = root / name
            if here.exists() or here.is_symlink():
                os.rename(here, trash / name)
            if name in entries:
                os.rename(staging / name, here)
        tmp = root / f".{_PAYLOAD_MARKER}.{os.getpid()}"
        tmp.write_text(json.dumps({
            "sha256": digest, "entries": entries, "files": files,
            "file_sha256": _file_digests(root, files),
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }, indent=2))
        os.replace(tmp, marker)
    except (OSError, ValueError, tarfile.TarError) as e:
        return {**record, "ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        for scratch in (staging, trash):
            if scratch.exists():
                shutil.rmtree(scratch, ignore_errors=True)
    return {**record, "installed": True, "entries": entries, "files": files,
            "replaced": previous.get("sha256"), "why": why,
            "drift": ({k: v[:20] for k, v in drift.items()} if drift else None)}


@ChiaFunction(resources={C.GEM5_HOST_RESOURCE: 1.0})
def scons_build(
    root: str, isa: str, variant: str, jobs: int, scons_args: str,
    env: dict | None, timeout_s: int, copy_to: str | None = None,
) -> dict:
    """Gem5Node.build_gem5 on this node, with `env` in the build's
    environment. Returns a dict, never raises.

    build_gem5 takes no environment, and gem5 v25.1 reads CC, CXX,
    PYTHON_CONFIG and CCFLAGS_EXTRA only from the environment (see
    _SCONS_ENV_VARS). So this task sets them in its own os.environ, calls
    build_gem5 in-process (a ChiaFunction called directly runs locally), and
    puts os.environ back. build_gem5's subprocess inherits the environment
    because it passes no env of its own. Ray runs one task at a time in a
    worker process, so nothing else sees the change.

    Two checks build_gem5 does not make. scons can report success without
    the binary the caller asked for, and a later run would then fail with a
    bare "No such file". And with `copy_to`, the binary is copied to a path
    of its own, so a compile-time knob's two states can both exist at once.
    """
    applied = {k: str(v) for k, v in (env or {}).items()}
    saved = {k: os.environ.get(k) for k in applied}
    command = f"scons build/{isa}/gem5.{variant} -j{jobs} {scons_args}".strip()
    base = {"root": root, "command": command, "env": applied}
    os.environ.update(applied)
    try:
        art = Gem5Node.build_gem5(root, isa, variant, jobs=jobs,
                                  extra_scons_args=scons_args, timeout_s=timeout_s)
    except Exception as e:  # a missing tree raises inside Popen
        return {**base, "ok": False, "binary": None,
                "log": f"[the build could not start in {root}: {type(e).__name__}: {e}]"}
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    log = art.stdout_tail + (f"\n{art.stderr_tail}" if art.stderr_tail else "")
    out = {**base, "ok": bool(art.success), "binary": art.binary_path,
           "returncode": art.returncode, "duration_s": round(art.build_duration_s, 1),
           "base_rev": art.base_rev, "log": log}
    if not out["ok"]:
        return out
    if not os.path.isfile(art.binary_path):
        return {**out, "ok": False,
                "log": log + f"\n[scons exited 0 but {art.binary_path} does not exist]"}
    if copy_to:
        tmp = f"{copy_to}.tmp-{os.getpid()}"
        try:
            shutil.copy2(art.binary_path, tmp)
            os.replace(tmp, copy_to)
        except OSError as e:
            return {**out, "ok": False,
                    "log": log + f"\n[could not copy the binary to {copy_to}: {e}]"}
        out["binary"] = copy_to
    return out


# ------------------------------------------------------------------ head side


def split_scons_args(args: Optional[str] = None) -> tuple:
    """GEM5_SCONS_ARGS as (command-line flags, environment settings).

    A NAME=value word whose NAME gem5 reads from the environment goes to the
    environment. Everything else (the flags, EXTRAS=) stays on the command
    line."""
    cli, env = [], {}
    for word in shlex.split(C.GEM5_SCONS_ARGS if args is None else args):
        key, sep, value = word.partition("=")
        if sep and key in _SCONS_ENV_VARS:
            env[key] = value
        else:
            cli.append(word)
    return shlex.join(cli), env


def build_env(define: Optional[Mapping[str, str]] = None) -> dict:
    """The environment every build and every shell on this host gets.

    The same one everywhere, because scons folds CC and CCFLAGS into every
    object's signature. A shell command that runs scons with a different CC
    would recompile all of gem5, and so would the next gate build after it.

    `define` is a compile-time knob's state, as define_env returns it. Each
    name becomes `-D<name>=0` or `-D<name>=1` in CCFLAGS_EXTRA (appended
    to every compile line, SConstruct:987). The knob is defined in both
    states, so a port must test it with `#if`, not `#ifdef`."""
    _, env = split_scons_args()
    if define:
        flags = " ".join(f"-D{k}={v}" for k, v in sorted(define.items())
                         if _C_IDENTIFIER.match(k))
        env["CCFLAGS_EXTRA"] = f"{env.get('CCFLAGS_EXTRA', '')} {flags}".strip()
    return env


def _manifest(path: Optional[Path] = None) -> dict:
    return json.loads(Path(path or C.GEM5_WORKLOADS_MANIFEST).read_text())


def workloads(path: Optional[Path] = None) -> dict:
    """The manifest's workload table, name -> entry."""
    return dict(_manifest(path).get("workloads") or {})


def _payload_relpath(rel: str, what: str) -> str:
    """A manifest path, checked to stay inside the payload."""
    if not rel or posixpath.isabs(rel) or ".." in Path(rel).parts:
        raise ValueError(f"{what} {rel!r} must be a relative path inside the payload")
    return rel


def resolve(name: str, run_dir: Optional[str] = None,
            manifest: Optional[Path] = None) -> dict:
    """One workload as the gem5 node sees it: absolute binary, argv, cwd,
    instruction limit, and the se_o3.py arguments that run it.

    Paths are joined as strings and never resolved. The guest sees the
    binary's path as argv[0], and run_workload.py builds the same string
    from the same manifest. The two have to agree byte for byte, or a G2
    run through the shell and the baseline recorded through run_traces put
    different strings on the guest's stack."""
    doc = _manifest(manifest)
    table = doc.get("workloads") or {}
    if name not in table:
        raise UnknownWorkloadError(
            f"unknown gem5 workload {name!r}. {Path(manifest or C.GEM5_WORKLOADS_MANIFEST).name} "
            f"has: {', '.join(sorted(table)) or '(none)'}"
        )
    entry = table[name]
    base = posixpath.join(run_dir or C.GEM5_RUN_DIR, doc.get("root") or "workloads")
    binary = posixpath.join(base, _payload_relpath(entry.get("binary"), f"{name}.binary"))
    cwd = entry.get("cwd")
    cwd = posixpath.join(base, _payload_relpath(cwd, f"{name}.cwd")) if cwd else None
    args = [str(a) for a in (entry.get("args") or [])]
    max_insts = entry.get("max_insts")
    config_args = ["--cmd", binary, "--options", shlex.join(args)]
    if cwd:
        config_args += ["--cwd", cwd]
    if max_insts:
        config_args += ["--maxinsts", str(int(max_insts))]
    return {"name": name, "binary": binary, "args": args, "cwd": cwd,
            "max_insts": max_insts, "config_args": config_args}


def build_run_payload(
    run_scripts_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    workloads_dir: Optional[Path] = None,
) -> bytes:
    """The run dir as a tar.gz, built on the head: the run scripts,
    workloads.json, and the workload payload under the manifest's root.

    The bytes are deterministic. Members are sorted, and each gets a fixed
    mtime and owner, and gzip gets mtime 0. So an unchanged payload hashes
    the same and install_run_dir skips it. Every manifest workload is
    checked against the payload here, so a stale workload build fails on
    the head with its name, not as thirty gem5 runs that cannot find a
    binary."""
    scripts = Path(run_scripts_dir or RUN_SCRIPTS_DIR)
    manifest_path = Path(manifest_path or C.GEM5_WORKLOADS_MANIFEST)
    payload_dir = Path(workloads_dir or C.GEM5_WORKLOADS_DIR)
    missing_scripts = [n for n in ("se_o3.py", "run_workload.py", "p2p_metrics.py")
                       if not (scripts / n).is_file()]
    if missing_scripts:
        raise SystemExit(f"{scripts} has no {', '.join(missing_scripts)}; the run "
                         f"scripts are part of the payload")
    if not manifest_path.is_file():
        raise SystemExit(f"{manifest_path} does not exist; it names the workloads")
    if not all((payload_dir / sub).is_dir() for sub in ("bin", "data")):
        raise SystemExit(f"{payload_dir}/bin and {payload_dir}/data do not both exist. "
                         f"Run scripts/build_gem5_workloads.sh first.")
    doc = _manifest(manifest_path)
    root = doc.get("root") or "workloads"
    problems = []
    for name, entry in sorted((doc.get("workloads") or {}).items()):
        try:
            rel = _payload_relpath(entry.get("binary"), f"{name}.binary")
            if not (payload_dir / rel).is_file():
                problems.append(f"{name}: {payload_dir / rel} is missing")
            if entry.get("cwd"):
                rel = _payload_relpath(entry["cwd"], f"{name}.cwd")
                if not (payload_dir / rel).is_dir():
                    problems.append(f"{name}: {payload_dir / rel} is missing")
        except ValueError as e:
            problems.append(f"{name}: {e}")
    if problems:
        raise SystemExit("the workload payload does not match workloads.json. Run "
                         "scripts/build_gem5_workloads.sh.\n  " + "\n  ".join(problems))

    def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mtime = _PAYLOAD_MTIME
        if info.isdir():
            info.mode = 0o755
        elif info.isfile():
            info.mode = 0o755 if info.mode & 0o100 else 0o644
        return info

    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in sorted(scripts.glob("*.py")):
                tar.add(path, arcname=path.name, filter=normalize)
            tar.add(manifest_path, arcname="workloads.json", filter=normalize)
            for sub in ("bin", "data"):
                top = payload_dir / sub
                for dirpath, dirnames, filenames in os.walk(top):
                    # install_run_dir deletes every __pycache__ it finds, so
                    # one in the payload would be "missing" at every install.
                    dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
                    here = Path(dirpath)
                    arc = posixpath.join(root, sub, here.relative_to(top).as_posix())
                    tar.add(here, arcname=posixpath.normpath(arc), recursive=False,
                            filter=normalize)
                    for f in sorted(filenames):
                        tar.add(here / f, arcname=posixpath.normpath(posixpath.join(arc, f)),
                                recursive=False, filter=normalize)
    return buf.getvalue()


def install_run_dir_on_cluster() -> dict:
    """Build the payload here and install it at GEM5_RUN_DIR on the node.

    A no-op when the node already holds exactly this payload. The result's
    `installed` says whether it had to install, and `why` says what forced
    it."""
    payload = build_run_payload()
    try:
        result = _wait(install_run_dir.chia_remote(payload, C.GEM5_RUN_DIR),
                       _SHORT_TASK_LIMIT_S, "installing the run dir")
    except Exception as e:  # noqa: BLE001 - reported below with the node's name
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if not result or not result.get("ok"):
        raise SystemExit(
            f"could not install the gem5 run dir at {C.GEM5_RUN_DIR}: "
            f"{(result or {}).get('error')}. Is the {C.GEM5_HOST_RESOURCE} node up?"
        )
    return result


def binary_path(root: str) -> str:
    """Where scons puts gem5 for this ISA and variant: build/<ISA>/gem5.<variant>
    (src/SConscript:406-410, 676, 740)."""
    return f"{root}/build/{C.GEM5_ISA}/gem5.{C.GEM5_VARIANT}"


def state_binary_path(root: str, feature_on: bool) -> str:
    """A compile-time knob's per-state copy of the binary. It sits in build/,
    so restore keeps it and port_diff leaves it out."""
    return f"{binary_path(root)}.p2p-feature-{'on' if feature_on else 'off'}"


def build_tree(root: str, timeout_s: int = C.GEM5_BUILD_TIMEOUT_S) -> dict:
    """Build `root` on the node with the one build configuration every tree
    uses (GEM5_ISA, GEM5_VARIANT, GEM5_BUILD_JOBS, GEM5_SCONS_ARGS)."""
    cli, _ = split_scons_args()
    try:
        result = _wait(scons_build.chia_remote(
            root, C.GEM5_ISA, C.GEM5_VARIANT, C.GEM5_BUILD_JOBS, cli, build_env(),
            timeout_s, None,
        ), timeout_s, f"the build of {root}")
    except Exception as e:
        return {"ok": False, "root": root, "binary": None,
                "log": f"[the build task failed: {type(e).__name__}: {e}]"}
    return result or {"ok": False, "root": root, "binary": None,
                      "log": "[the build task returned nothing]"}


def enable_env(feature_enable: dict, feature_on: bool) -> dict:
    """The environment that turns the port on or off.

    Every alias the plan could plausibly have used is set to the same value,
    because getting this wrong is silent: a port reading a name the gate does
    not set stays off in both states, G2 passes trivially, and G5 reports
    that the mechanism never reached the metric. The aliases are the plan's
    `feature_enable.name`, that name upper-cased, and its `macro`.

    The same function as the cbp2025 adapter's, copied rather than imported
    so this host does not load the CBP2025 node. A unit test holds the two
    equal."""
    value = "1" if feature_on else "0"
    names = {
        (feature_enable or {}).get("name"),
        ((feature_enable or {}).get("name") or "").upper() or None,
        (feature_enable or {}).get("macro"),
    }
    return {n: value for n in names if n}


def define_env(feature_enable: dict, feature_on: bool) -> dict:
    """The macros a compile-time knob defines: the plan's `macro` and the
    upper-cased `name`. Never the raw name when it has lower-case letters.

    CCFLAGS_EXTRA is on every compile line of gem5. `-Dsr_enable=0` there
    turns every identifier spelled sr_enable into 0, in gem5 and in the
    port: a member, a local, or a Param, which also lands in a generated
    params header. The port then fails G1 with "expected unqualified-id" in
    files the agent did not write. An upper-case name follows the macro
    convention, so it is far less likely to collide. The runtime environment
    keeps all three aliases (enable_env), because an environment variable
    collides with no identifier."""
    value = "1" if feature_on else "0"
    names = {
        (feature_enable or {}).get("macro"),
        ((feature_enable or {}).get("name") or "").upper() or None,
    }
    return {n: value for n in names if n and _C_IDENTIFIER.match(n)}


def parse_metrics(output: str) -> dict:
    """The P2P_METRIC lines of one run_workload.py run, or `{}`.

    `{}` unless the output carries a `P2P_STATUS` line and every such line
    says ok. A failed run can still print metrics derived from whatever
    stats gem5 wrote. plan_runner's metrics_equal_baseline condition does not
    look at the exit code, so metrics from a failed run would otherwise be
    compared as if the run had worked. `{}` is how a crashed run reaches the
    gate as a failed entry rather than as an exception."""
    text = output or ""
    statuses = _STATUS_LINE.findall(text)
    if not statuses or any(s != "ok" for s in statuses):
        return {}
    return dict(p2p_metrics.parse_metric_lines(text))


# ------------------------------------------------------------------ fan-out


def _exit_line(stdout: str) -> Optional[tuple]:
    """(cause, code) from the last P2P_EXIT line, or None."""
    hits = list(_EXIT_LINE.finditer(stdout or ""))
    return (hits[-1]["cause"], hits[-1]["code"]) if hits else None


def _outdir(name: str, label: str) -> str:
    """A gem5 outdir no other run can share.

    The two states of one workload run at the same time on the same node, and
    so can two executors. A name built from the workload and the state alone
    lets them overwrite one another's stats.txt, and each would then read a
    number the other produced."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{C.GEM5_RUN_DIR}/runs/{stamp}-{label}-{safe}-{uuid.uuid4().hex[:8]}"


def _judge_run(name: str, outdir: Optional[str], result, require_metrics: bool) -> dict:
    """One run's verdict. A run succeeds only if gem5 said ok and exited 0,
    se_o3.py reported the guest exiting 0, and the stats derive every metric.
    """
    record = {"name": name, "outdir": outdir, "ok": False, "reason": "",
              "metrics": {}, "stats": {}, "status": None, "returncode": None,
              "wall_s": None, "sim_insts": None, "num_cycles": None,
              "stdout_tail": "", "stderr_tail": ""}
    if isinstance(result, BaseException):
        record["reason"] = f"the run task failed: {type(result).__name__}: {result}"
        return record
    if result is None:
        # What a Ray task whose worker died can leave behind. Reading an
        # attribute off it would take the gate down instead of reporting
        # the failure it exists to report.
        record["reason"] = "the run task returned nothing (did its worker die?)"
        return record
    stats_text = getattr(result, "stats_content", None)
    record.update(
        status=result.status, returncode=result.returncode, wall_s=result.wall_s,
        sim_insts=result.sim_insts, num_cycles=result.num_cycles,
        # Parsed here from the captured stats.txt, never taken from
        # result.stats: see run_workloads.
        stats=(p2p_metrics.select(p2p_metrics.parse_stats_text(stats_text))
               if stats_text else {}),
        stdout_tail=result.stdout_tail or "",
    )
    # The guest's exit code travels as gem5's own, and a run that exits 0 is
    # also checked here: a zero from a gem5 that never reached the end of the
    # simulation is not evidence the workload ran.
    exit_info = _exit_line(result.stdout_tail)
    guest = (f" (guest code {exit_info[1]}, cause: {exit_info[0]})" if exit_info
             else "")
    if result.status != "ok":
        record["reason"] = f"gem5 status {result.status}: {result.error_messages}{guest}"
        return record
    if result.returncode != 0:
        record["reason"] = f"gem5 exited {result.returncode}{guest}"
        return record
    if exit_info is None:
        record["reason"] = ("gem5 exited 0 without a P2P_EXIT line, so se_o3.py never "
                            "reported the end of the simulation")
        return record
    cause, code = exit_info
    if code != "0":
        record["reason"] = f"the guest exited with code {code} ({cause})"
        return record
    if not stats_text:
        record["reason"] = "gem5 exited 0 but its stats.txt did not come back"
        return record
    metrics = dict(p2p_metrics.derive(record["stats"]))
    record["metrics"] = metrics
    missing = [k for k in p2p_metrics.METRIC_KEYS if k not in metrics]
    if require_metrics and missing:
        record["reason"] = (f"the stats did not derive {', '.join(missing)} "
                            f"(logical stats found: {', '.join(sorted(record['stats']))})")
        return record
    record["ok"] = True
    return record


_OUTDIR_MARK = "@@P2P_OUTDIR@@ "


def _attach_stderr(records: list) -> None:
    """Read back simerr.txt for the runs that failed, in one dispatch.

    Best effort: the verdict is already decided, and a failure to read the
    diagnostics must not change it."""
    wanted = [r for r in records if r.get("outdir")]
    if not wanted:
        return
    script = "; ".join(
        f"echo {shlex.quote(_OUTDIR_MARK + r['outdir'])}; "
        f"tail -c 2000 {shlex.quote(r['outdir'] + '/simerr.txt')} 2>/dev/null "
        f"|| echo '(no simerr.txt: gem5 did not get as far as redirecting stderr)'; "
        # se_o3.py sends the guest's own stderr here, which is where a
        # workload's self-check prints why it failed.
        f"tail -c 1000 {shlex.quote(r['outdir'] + '/guest_stderr.txt')} 2>/dev/null "
        f"|| true"
        for r in wanted
    )
    try:
        # cwd "/" because it always exists. The run dir may not, and a
        # missing cwd would lose every tail to one OSError.
        out = _wait(host_shell.options(resources={C.GEM5_HOST_RESOURCE: 0.1})
                    .chia_remote("/", script, {}, 120), 120, "reading back simerr.txt")
    except Exception:
        return
    tails, current = {}, None
    for line in (out or {}).get("output", "").splitlines():
        if line.startswith(_OUTDIR_MARK):
            current = line[len(_OUTDIR_MARK):]
            tails[current] = []
        elif current is not None:
            tails[current].append(line)
    for r in wanted:
        r["stderr_tail"] = "\n".join(tails.get(r["outdir"], []))


def run_workloads(
    binary: str, names: Sequence[str], *, env: Optional[Mapping[str, str]],
    timeout_s: int, label: str, extra_config_args: Sequence[str] = (),
    require_metrics: bool = True,
) -> list:
    """One gem5 run per workload, all dispatched before any is awaited.

    Returns one record per name, in order (see _judge_run). The fan-out is
    the whole reason a gate finishes in minutes: waiting on each run before
    starting the next would make a perf list take as long as its runs added
    up. Every get() is guarded, so one run that raised or whose worker died
    is one failed workload, and the others still count.

    Every get() also has a timeout, `timeout_s` plus _GET_MARGIN_S, counted
    from when that get() starts. That is long enough even for a list longer
    than the node's slots. The runs are awaited in dispatch order. So when a
    run of a later wave is awaited, the wave before it is over, the run got
    its slot before its own get() started, and its own limit bounds the
    wait. When one run times out, the node stopped answering, and the runs
    after it only get _AFTER_STALL_WAIT_S to be already finished. A lost
    node then costs one limit, not one per workload."""
    config_script = f"{C.GEM5_RUN_DIR}/se_o3.py"
    dispatched = []
    for name in names:
        try:
            spec = resolve(name)
        except (UnknownWorkloadError, ValueError, OSError) as e:
            dispatched.append((name, None, None, str(e)))
            continue
        outdir = _outdir(name, label)
        try:
            ref = Gem5Node.run_gem5.options(
                resources={C.GEM5_HOST_RESOURCE: 1.0}
            ).chia_remote(
                binary, config_script, outdir,
                workload_name=name,
                config_args=[*spec["config_args"], *extra_config_args],
                gem5_args=list(_GEM5_ARGS),
                stats_keys=p2p_metrics.STATS_KEYS,
                # The whole stats.txt comes back, and p2p_metrics parses it,
                # the same parser run_workload.py uses in the agent's shell.
                # chia's own parser cannot read the conditional-only
                # misprediction row (see p2p_metrics' docstring), so
                # result.stats is only what chia needs to call the run ok.
                capture_stats=True,
                # The host process's cwd, not the guest's: se_o3.py fixes
                # that. The outdir keeps a relative path in the worker's
                # environment from resolving against the repository.
                cwd=outdir,
                env=dict(env or {}),
                timeout_s=timeout_s,
            )
        except Exception as e:
            dispatched.append((name, None, None,
                               f"could not dispatch the run: {type(e).__name__}: {e}"))
            continue
        dispatched.append((name, outdir, ref, None))

    records = []
    stalled = ""  # the first timeout's reason, once there is one
    for name, outdir, ref, error in dispatched:
        if error is not None:
            record = _judge_run(name, None, None, require_metrics)
            record["reason"] = error
            records.append(record)
            continue
        try:
            result = _wait(ref, timeout_s, f"the run of {name}",
                           wait_s=_AFTER_STALL_WAIT_S if stalled else None)
        except Gem5NodeTimeout as timeout:
            if stalled:
                result = Gem5NodeTimeout(f"the run of {name} was not finished either, "
                                         f"and it was not waited for. Earlier: {stalled}")
            else:
                stalled, result = str(timeout), timeout
        except Exception as e:
            result = e
        records.append(_judge_run(name, outdir, result, require_metrics))
    # Reading simerr.txt back needs the same node. After a stall that is one
    # more wait on a node that stopped answering, for tails that do not exist.
    if not stalled:
        _attach_stderr([r for r in records if not r["ok"]])
    return records


def _failure_tail(records: list, limit: int = 4000) -> str:
    parts = []
    for r in records:
        if r["ok"]:
            continue
        parts.append(f"== {r['name']}: {r['reason']}")
        if r.get("stderr_tail"):
            parts.append(r["stderr_tail"][-1500:])
        if r.get("stdout_tail"):
            parts.append(r["stdout_tail"][-500:])
    return "\n".join(parts)[-limit:]


# ------------------------------------------------------------------ executor


class Gem5Executor:
    """plan_runner.HostExecutor over one gem5 tree on the gem5 node."""

    name = HOST

    def __init__(
        self,
        work_dir: str,
        feature_enable: dict,
        metric_keys: Sequence[str] = METRIC_KEYS,
        rebuild_per_state: Optional[bool] = None,
    ):
        self.work_dir = str(work_dir)
        self.feature_enable = feature_enable or {}
        self.metric_keys = tuple(metric_keys)
        binding = self.feature_enable.get("binding")
        # A binding the fixed run scripts cannot deliver fails the build with
        # the reason. Treating it as a define instead would leave the port
        # off in both states, and G5 would report a mechanism that never
        # reached the metric, which sends the debug turn after the wrong bug.
        self.undeliverable = binding if binding in _UNDELIVERABLE_BINDINGS else None
        # Whether flipping the knob costs a rebuild. Derived from the plan's
        # own `binding`, because the gate must measure the port the plan
        # describes. On gem5 a define is expensive: CCFLAGS_EXTRA is on every
        # compile line, so each state is a full recompile, about 11 minutes
        # on the node. ccache is not in the loop to soften it.
        if rebuild_per_state is None:
            rebuild_per_state = binding in _DEFINE_BINDINGS
        self.rebuild_per_state = bool(rebuild_per_state)
        self._binaries: dict = {}
        self._build_logs: dict = {}
        # Which state the gem5.opt in the tree was built for, as opposed to
        # which states we hold a binary for. A run gets its binary by path
        # and does not care, but a shell command may run whatever is in the
        # tree, so the two are tracked separately.
        self._tree_state: Optional[bool] = None
        self._last_build_error: str = ""

    # --------------------------------------------------------------- build
    def _build_key(self, feature_on: bool) -> bool:
        return feature_on if self.rebuild_per_state else False

    def build(self, *, feature_on: bool, timeout_s: int = C.GEM5_BUILD_TIMEOUT_S,
              force: bool = False):
        if self.undeliverable:
            return plan_runner.BuildOutcome(ok=False, log=(
                f"the plan binds its enable knob as {self.undeliverable!r}, which the "
                f"gem5 host cannot set: the run scripts are fixed and read no knob. "
                f"Bind it as runtime_env (read with getenv in C++) or as "
                f"compile_time_define."
            ))
        key = self._build_key(feature_on)
        # The cache is only good while the tree still holds that build. With
        # a compile-time knob the tree swaps state under us, and then a
        # cached "hit" would report success for a gem5.opt built the other way.
        if not force and key in self._binaries and self._tree_state == key:
            return plan_runner.BuildOutcome(
                ok=True, log=self._build_logs[key], handle=self._binaries[key]
            )
        define = define_env(self.feature_enable, key) if self.rebuild_per_state else None
        copy_to = state_binary_path(self.work_dir, key) if self.rebuild_per_state else None
        cli, _ = split_scons_args()
        # plan_runner passes its generic 900 s. A gem5 build's limit is a
        # property of this host, and a test plan has no field for it, so the
        # host's own limit is the floor.
        limit = max(int(timeout_s or 0), C.GEM5_BUILD_TIMEOUT_S)
        try:
            result = _wait(scons_build.chia_remote(
                self.work_dir, C.GEM5_ISA, C.GEM5_VARIANT, C.GEM5_BUILD_JOBS, cli,
                build_env(define), limit, copy_to,
            ), limit, f"the build of {self.work_dir}")
        except Exception as e:
            result = {"ok": False, "log": f"[the build task failed: {type(e).__name__}: {e}]"}
        result = result or {"ok": False, "log": "[the build task returned nothing]"}
        if not result.get("ok"):
            self._tree_state = None
            return plan_runner.BuildOutcome(ok=False, log=result.get("log") or "")
        self._binaries[key] = result["binary"]
        self._build_logs[key] = result.get("log") or ""
        self._tree_state = key
        return plan_runner.BuildOutcome(ok=True, log=self._build_logs[key],
                                        handle=result["binary"])

    def _ensure_tree_state(self, feature_on: bool) -> None:
        """Make the gem5.opt in the tree be the one this state needs.

        A no-op for a runtime_env knob, where one binary serves both states.
        Not a no-op for a compile-time knob: a correctness entry declaring
        `feature_state: "on"` would otherwise run whichever binary the last
        build left, and the last build is the feature-off one run_test_plan
        starts with. The entry would then measure the baseline and pass."""
        key = self._build_key(feature_on)
        if not self.rebuild_per_state or self._tree_state == key:
            return
        self.build(feature_on=feature_on, force=True)

    def _binary_for(self, feature_on: bool) -> Optional[str]:
        """The binary a run in this state needs, building it if only the
        other state exists so far. A failure records the compiler output in
        `_last_build_error`, because the only thing run_traces could say
        otherwise is that every workload failed, which reads as a broken
        workload list rather than a port that does not compile."""
        key = self._build_key(feature_on)
        if key not in self._binaries:
            outcome = self.build(feature_on=feature_on)
            if not outcome.ok:
                self._last_build_error = outcome.log
        return self._binaries.get(key)

    # --------------------------------------------------------------- shell
    def shell_env(self, feature_on: bool,
                  env: Optional[Mapping[str, str]] = None) -> dict:
        """What a test plan command sees: the build environment (so a scons
        in the command builds the way the gate does), the knob, where
        run_workload.py finds gem5 and the run dir, and a Python that
        imports nothing from the tree.

        The command runs with the tree as its cwd, and the Ray worker's
        PYTHONPATH is ".:loop" (constants.RUNTIME_ENV). Python puts those
        entries before the standard library. So a sitecustomize.py, or a
        scratch json.py, that an agent left in the tree would run inside the
        measuring run_workload.py, and could print metrics that match the
        baseline. An empty PYTHONPATH counts as unset, PYTHONNOUSERSITE
        keeps ~/.local out too, and run_workload.py adds its own directory
        for p2p_metrics. These two go last, so an entry's `env` cannot put
        the tree back. The fan-out path never had this exposure: each of its
        gem5 runs has a new, empty outdir as its cwd, so "." names nothing."""
        key = self._build_key(feature_on)
        define = define_env(self.feature_enable, key) if self.rebuild_per_state else None
        binary = self._binaries.get(key) or (
            state_binary_path(self.work_dir, key) if self.rebuild_per_state
            else binary_path(self.work_dir))
        return {
            **build_env(define),
            **enable_env(self.feature_enable, feature_on),
            "P2P_GEM5_BIN": binary,
            "P2P_GEM5_RUN_DIR": C.GEM5_RUN_DIR,
            **(env or {}),
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
        }

    def shell(
        self, command: str, *, feature_on: bool,
        env: Optional[Mapping[str, str]] = None, timeout_s: int = C.GEM5_RUN_TIMEOUT_S,
    ):
        # The knob is applied here, not by the runner, because only the host
        # knows how a value reaches it. On this host that is the gem5
        # process's environment, which run_workload.py passes on unchanged
        # and se_o3.py keeps away from the guest. host_shell lays this env
        # over os.environ, so its PYTHONPATH replaces the worker's.
        self._ensure_tree_state(feature_on)
        try:
            out = _wait(
                host_shell.options(resources={C.GEM5_HOST_RESOURCE: 1.0})
                .chia_remote(self.work_dir, command, self.shell_env(feature_on, env),
                             timeout_s),
                timeout_s, f"the command {command!r}",
            )
        except Exception as e:
            out = {"exit_code": -1, "timed_out": False,
                   "output": f"[the shell task failed: {type(e).__name__}: {e}]"}
        out = out or {"exit_code": -1, "timed_out": False,
                      "output": "[the shell task returned nothing]"}
        return plan_runner.ShellOutcome(
            exit_code=out["exit_code"], output=out["output"], timed_out=out["timed_out"],
        )

    def parse_metrics(self, output: str) -> dict:
        return parse_metrics(output)

    # ---------------------------------------------------------- trace runs
    def run_traces(
        self, traces: Sequence[str], *, feature_on: bool,
        timeout_s: int = C.GEM5_RUN_TIMEOUT_S,
    ):
        """This host's fan-out: one gem5 run per workload on the gem5 node,
        30 at a time, aggregated with p2p_metrics.aggregate (an arithmetic
        mean, like the cbp2025 suite aggregate)."""
        traces = list(traces)
        if not traces:
            return plan_runner.TraceOutcome(
                ok=False, metrics={}, failed=[],
                log_tail="no workloads were named, and running nothing is not a pass",
            )
        binary = self._binary_for(feature_on)
        if not binary:
            state = "on" if feature_on else "off"
            return plan_runner.TraceOutcome(
                ok=False, metrics={}, failed=traces,
                log_tail=f"the host did not build with the feature {state}, so no "
                         f"workload was run:\n{self._last_build_error[-3000:]}",
            )
        # plan_runner passes its generic 900 s, or a plan's own
        # timeout_seconds, and neither knows what a gem5 run costs. A perf
        # workload took up to 396 s alone on an idle node (2026-09-23), and a
        # second job sharing the node doubles that. A run killed early reads
        # as a G4 or G5 failure of the port, so the host's own limit is the
        # floor, the same way build() floors its build limit.
        limit = max(int(timeout_s or 0), C.GEM5_RUN_TIMEOUT_S)
        records = run_workloads(
            binary, traces, env=enable_env(self.feature_enable, feature_on),
            timeout_s=limit, label="on" if feature_on else "off",
        )
        good = [r["metrics"] for r in records if r["ok"]]
        failed = [r["name"] for r in records if not r["ok"]]
        wanted = set(p2p_metrics.METRIC_KEYS) | set(self.metric_keys)
        metrics = ({k: v for k, v in p2p_metrics.aggregate(good).items() if k in wanted}
                   if good else {})
        return plan_runner.TraceOutcome(
            ok=not failed, metrics=metrics, failed=failed,
            log_tail=_failure_tail(records),
        )


# ------------------------------------------------------------------- adapter


def _same_path(a: str, b: str) -> bool:
    return os.path.normpath(os.path.abspath(a)) == os.path.normpath(os.path.abspath(b))


def _node_call(ref, what: str):
    """_wait for a head-side helper the driver calls outside any gate. A
    node that stopped answering ends the stage with a message, because no
    attempt can make progress without it."""
    try:
        return _wait(ref, _SHORT_TASK_LIMIT_S, what)
    except Gem5NodeTimeout as e:
        raise SystemExit(str(e)) from None


def restore_host_checkout(root: str = C.GEM5_ROOT) -> dict:
    """Undo whatever the last agent left in the pristine checkout.

    Refuses the port tree and the search tree outright. restore_checkout is
    `git reset --hard` plus `git clean -fdx`, which on GEM5_PORT_ROOT would
    delete an integration run's entire work with no copy anywhere, and on
    GEM5_DSE_ROOT the port the search is tuning. Every call site today passes
    the pristine root, and this is here so that a future one that does not
    fails loudly.

    The gate smoke's tree (~/gem5_smoke, see loop/tests/gem5_gate_smoke.py)
    is deliberately not on the list. The list protects work that exists
    nowhere else. The smoke tree holds no agent's work: the smoke deletes it
    and copies it again from the pristine checkout at every run. A restore
    there loses nothing, and refusing it would take a path that only the
    script owns into this module."""
    for protected, what in ((C.GEM5_PORT_ROOT, "the tree stage 3 edits"),
                            (C.GEM5_DSE_ROOT, "the tree stage 4 searches in")):
        if _same_path(root, protected):
            raise SystemExit(
                f"refusing to reset {root}: that is {what}, and restoring it would "
                f"delete the port. Only {C.GEM5_ROOT} is restorable."
            )
    return _node_call(restore_checkout.chia_remote(root), f"restoring {root}")


def copy_tree(src: str, dst: str, *, fresh: bool = True, reset: bool = True) -> dict:
    """materialize_port_tree on the node, waited on with a timeout. Returns
    its result; the caller decides what a failure means."""
    return _node_call(materialize_port_tree.chia_remote(src, dst, fresh, reset),
                      f"copying {src} to {dst}")


def clean_port_tree(fresh: bool = True) -> dict:
    """Put a pristine copy of the checkout, build/ included, where stage 3 may
    edit it."""
    result = copy_tree(C.GEM5_ROOT, C.GEM5_PORT_ROOT, fresh=fresh)
    if not result.get("ok"):
        raise SystemExit(
            f"could not materialize the gem5 port tree: {result.get('error')}. Is the "
            f"cluster up, and does {C.GEM5_ROOT} exist on the {C.GEM5_HOST_RESOURCE} node?"
        )
    return result


def dse_tree(fresh: bool = True) -> str:
    """A copy of the ported tree for stage 4 to search in, without a reset,
    because the port is the thing being tuned."""
    result = copy_tree(C.GEM5_PORT_ROOT, C.GEM5_DSE_ROOT, fresh=fresh, reset=False)
    if not result.get("ok"):
        raise SystemExit(
            f"could not copy the ported gem5 tree for the search: {result.get('error')}. "
            f"Run --stage integrate first; {C.GEM5_PORT_ROOT} has to exist on the "
            f"{C.GEM5_HOST_RESOURCE} node."
        )
    return result["path"]


def checkout_revision() -> str:
    return _node_call(host_revision.chia_remote(C.GEM5_ROOT),
                      f"reading the revision of {C.GEM5_ROOT}")


def mirror_revision(mirror: Optional[Path] = None) -> str:
    """The commit of the head's mirror (REPO/third_party/gem5), or why there
    is none."""
    mirror = Path(mirror or MIRROR_ROOT)
    if not mirror.exists():
        return f"(absent: {mirror})"
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=mirror,
                          capture_output=True, text=True)
    return proc.stdout.strip() or "(not a git checkout)"


def notes() -> str:
    return NOTES_PATH.read_text()


# ---------------------------------------------------------------------- gate


def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def baseline_pointers(test_plan: dict) -> list:
    """Every pointer through which the test plan reads the recorded
    baseline: a metrics_equal_baseline condition (G2), and a performance
    entry whose baseline source is "recorded". plan_runner reads no other."""
    out = []
    for entry in (test_plan or {}).get("correctness") or []:
        pc = entry.get("pass_condition") or {}
        if pc.get("kind") == "metrics_equal_baseline":
            out.append(pc.get("baseline_pointer") or "")
    for entry in (test_plan or {}).get("performance") or []:
        base = entry.get("baseline") or {}
        if base.get("source") == "recorded":
            out.append(base.get("pointer") or "")
    return out


def baseline_workloads(test_plan: dict, baseline: dict) -> set:
    """The workloads whose recorded numbers the test plan compares against.

    `/per_trace/<name>` names one. Any other pointer, the top level
    included, reads numbers from every workload the recording measured, so
    it names all of them. Tokens are split and unescaped the way
    plan_runner._resolve does it (RFC 6901)."""
    names = set()
    for pointer in baseline_pointers(test_plan):
        tokens = [_unescape(t) for t in pointer.lstrip("/").split("/") if t]
        if len(tokens) >= 2 and tokens[0] == "per_trace":
            names.add(tokens[1])
        else:
            names |= set(baseline.get("workload_fingerprints") or {})
            names |= set(baseline.get("per_trace") or {})
    return names


def baseline_problems(baseline: dict, test_plan: dict,
                      revision: Optional[str] = None) -> list:
    """Why the recorded baseline no longer describes what the gate would
    run, one string per problem, or [] when it still does.

    Two things decide a workload's numbers apart from the port. The
    pristine revision is one: the baseline was built from GEM5_ROOT at
    `host_revision`. workload_fingerprint is the other: the manifest entry,
    the binary, its data and the run scripts. A workload the manifest does
    not know is left to G2, which reports it as the plan's own mistake."""
    problems = []
    revision = checkout_revision() if revision is None else revision
    recorded_at = (baseline or {}).get("host_revision")
    if recorded_at != revision:
        problems.append(f"it was recorded at revision {recorded_at or '(none)'}, and "
                        f"{C.GEM5_ROOT} is at {revision}")
    prints = (baseline or {}).get("workload_fingerprints") or {}
    for name in sorted(baseline_workloads(test_plan, baseline or {})):
        now = workload_fingerprint(name)
        if now is None:
            continue
        if name not in prints:
            problems.append(f"it holds no recording of {name}, which the test plan "
                            f"compares against")
        elif prints[name] != now:
            problems.append(f"{name} changed after it was recorded (its manifest "
                            f"entry, binary, data or the run scripts)")
    return problems


def check_baseline_current(baseline: dict, test_plan: dict,
                           revision: Optional[str] = None) -> None:
    """Raise SystemExit when the recorded baseline is stale.

    A stale baseline is a setup error, not a port failure. Without this
    check it reaches the gate as a G2 failure: "differs from baseline, the
    knob-off path is not baseline-identical". The debug turns then hunt a
    leak in a correct port, at 25 minutes or more per gem5 attempt. This
    nearly happened on 2026-09-23, when the cond_mpki definition changed
    after the first recordings."""
    problems = baseline_problems(baseline, test_plan, revision)
    if not problems:
        return
    names = sorted(baseline_workloads(test_plan, baseline or {}))
    raise SystemExit(
        "the recorded gem5 baseline no longer describes what the gate would run: "
        + "; ".join(problems)
        + ". That is a setup error, not a port failure, so no gate ran. Re-record "
          "it with `python loop/adopt_a_paper_loop.py --stage baseline --host gem5 "
          "--budget <budget>`, where <budget> names the baseline file this stage "
          "reads"
        + (f", and a --baseline-list that names {', '.join(names)}" if names else "")
        + ". Then run the stage again."
    )


def reinstall_warning(install: dict) -> str:
    """The gate warning for an install that was not a no-op, or ""."""
    if not (install or {}).get("installed"):
        return ""
    return (f"the run dir {install.get('dest')} was installed again before this gate "
            f"attempt, because {install.get('why') or 'it did not match the payload'}. "
            f"This attempt measured the payload's files. Any run since the previous "
            f"install used the files as they were then.")


class GateAttempt(NamedTuple):
    install: dict                         # install_run_dir's record
    results: plan_runner.TestPlanResults
    verdict: gate.GateResult


def gate_attempt(baseline: dict, port_plan: dict, test_plan: dict, *,
                 work_dir: str = C.GEM5_PORT_ROOT) -> GateAttempt:
    """run_gate's work, with what it measured on the way. The gate smoke
    calls this with its own tree, so it runs the same code as stage 3.

    First, every attempt, the run dir is installed again. It is a no-op
    when nothing changed. When the agent's shell edited a run script, or
    added a file next to one, between attempts, this undoes it before the
    gate measures, and the verdict carries a warning line for the lead.
    Second, the recorded baseline is checked against the pristine revision
    and the workload files (check_baseline_current). A stale one ends the
    stage with SystemExit rather than reaching the debug agent as a G2
    reason."""
    install = install_run_dir_on_cluster()
    check_baseline_current(baseline, test_plan)
    executor = Gem5Executor(
        work_dir=work_dir,
        feature_enable=(port_plan or {}).get("feature_enable") or {},
        metric_keys=(test_plan or {}).get("metric_keys") or METRIC_KEYS,
    )
    results = plan_runner.run_test_plan(executor, test_plan, port_plan, baseline)
    verdict = gate.check_gate(results)
    note = reinstall_warning(install)
    if note:
        verdict.warnings.append(note)
    return GateAttempt(install, results, verdict)


def run_gate(baseline: dict, port_plan: dict, test_plan: dict) -> gate.GateResult:
    """Run the test plan against the port tree, then let gate.check_gate
    judge it. Every condition and every threshold comes from the plan.

    A fresh executor per attempt on purpose: the agent has edited the tree
    since the last one, so a cached binary is a measurement of the previous
    attempt wearing this attempt's verdict. See gate_attempt for the
    install and the baseline check that come first."""
    return gate_attempt(baseline, port_plan, test_plan).verdict


# Build output, gem5 run output and Python caches, which `git add -AN .` would
# otherwise pull into the recorded patch. gem5's .gitignore already hides
# build, *.pyc and m5out (.gitignore:3,9,13). The excludes do not rely on it,
# because an agent can edit .gitignore too. `*` in a pathspec matches across
# `/`, so `*.pyc` covers every directory.
_DIFF_EXCLUDES = " ".join(
    f"':(exclude){pattern}'"
    for pattern in ("build", "m5out", "*/m5out/*", "*.pyc", "*__pycache__*")
)


def port_diff_command() -> str:
    """The shell command port_diff runs in the port tree.

    `add -AN` is what makes a file the agent created show up at all. The
    index is reset afterwards, so the tree is left exactly as it was found:
    a run that resumes with P2P_GEM5_PORT_FRESH=0 must not inherit a staged
    index it did not make."""
    return (
        f"git add -AN -- . {_DIFF_EXCLUDES} >/dev/null 2>&1; "
        f"echo '--- diffstat ---'; git diff --stat -- . {_DIFF_EXCLUDES}; "
        f"echo '--- patch ---'; git diff -- . {_DIFF_EXCLUDES}; "
        f"git reset -q >/dev/null 2>&1 || true"
    )


def port_diff() -> str:
    """What the agent changed in the port tree, as a patch.

    A node that does not answer gives a note in place of the patch. The
    driver writes the diff after the gate loop, whatever the verdict, and
    that record must not be lost to an exception."""
    try:
        out = _wait(
            host_shell.options(resources={C.GEM5_HOST_RESOURCE: 0.1})
            .chia_remote(C.GEM5_PORT_ROOT, port_diff_command(), {}, 300),
            300, f"the diff of {C.GEM5_PORT_ROOT}",
        )
    except Exception as e:  # noqa: BLE001
        return f"[could not read the port diff: {type(e).__name__}: {e}]"
    return (out or {}).get("output", "[the diff task returned nothing]")


# ----------------------------------------------------------------- baseline


def workload_fingerprint(name: str, manifest: Optional[Path] = None,
                         workloads_dir: Optional[Path] = None,
                         run_scripts_dir: Optional[Path] = None) -> Optional[str]:
    """A hash of everything that decides one workload's numbers apart from
    gem5 itself: its manifest entry, its binary, its data directory, and the
    run scripts. None for a name the manifest does not have.

    record_baseline carries per_trace entries forward only when this still
    matches. Workload sizes get retuned after the first measurements, and
    se_o3.py's cache sizes change every workload at once. A carried entry
    from before either change would be a baseline for a run nobody can make
    any more."""
    table = workloads(manifest)
    if name not in table:
        return None
    entry = table[name]
    payload_dir = Path(workloads_dir or C.GEM5_WORKLOADS_DIR)
    scripts = Path(run_scripts_dir or RUN_SCRIPTS_DIR)
    h = hashlib.sha256(json.dumps(entry, sort_keys=True).encode())
    files = [payload_dir / str(entry.get("binary") or "")]
    if entry.get("cwd"):
        files += sorted(p for p in (payload_dir / entry["cwd"]).rglob("*") if p.is_file())
    files += sorted(scripts.glob("*.py"))
    for f in files:
        h.update(str(f.name).encode())
        h.update(f.read_bytes() if f.is_file() else b"<missing>")
    return h.hexdigest()


def _repo_relative(path: Path) -> str:
    path = Path(path)
    if path.is_absolute() and path.is_relative_to(C.REPO_ROOT):
        return str(path.relative_to(C.REPO_ROOT))
    return str(path)


def record_baseline(
    dump: helpers.Dumper, workload_list: Path, budget: str = "iso-192KiB"
) -> dict:
    """Build the pristine checkout and run the list with the feature off.

    The pristine tree, not the port: stage 3 edits a copy, so a baseline
    recorded after an integration run still describes the host. The runs get
    no enable environment at all, not even "0", so nothing a port could read
    is set.

    What lands on disk is the suite aggregate plus a `per_trace` map keyed by
    workload name. A G2 entry runs one workload through the shell, so it
    needs a comparison point for one workload (`/per_trace/<name>`), and
    pointing it at a mean over several is a comparison between two different
    things.

    The rules are record_cbp_baseline's. per_trace entries from an earlier
    recording of the same revision carry forward, so a perf-list recording
    keeps the smoke workload G2 points at. Here they carry only while
    workload_fingerprint still matches. After a partial run the evidence
    goes to out/ and hosts/gem5/baselines/<budget>.json is left alone,
    because every later stage reads that file without knowing which run
    wrote it."""
    try:
        names = helpers.load_trace_list(Path(workload_list))
    except OSError as e:
        raise SystemExit(f"cannot read the workload list {workload_list}: {e}")
    if not names:
        raise SystemExit(f"{workload_list} names no workloads")
    try:
        for name in names:
            resolve(name)
    except (UnknownWorkloadError, ValueError) as e:
        raise SystemExit(f"{workload_list}: {e}")

    # Fingerprints now, next to the install, from the same files the payload
    # is built from. Computed after the runs instead, they described whatever
    # the files held by then: on 2026-09-23 an edit to p2p_metrics.py landed
    # mid-recording, the recorded fingerprints matched no run, and the smoke
    # entries G2 points at were dropped from the next recording.
    previous = helpers.load_baseline(HOST, budget) or {}
    prints = {n: workload_fingerprint(n)
              for n in {*names, *(previous.get("per_trace") or {})}}
    dump.json("gem5_baseline_restore.json", restore_host_checkout(C.GEM5_ROOT))
    dump.json("gem5_baseline_install.json", install_run_dir_on_cluster())
    build = build_tree(C.GEM5_ROOT)
    dump.json("gem5_baseline_build.json", {k: v for k, v in build.items() if k != "log"})
    if not build.get("ok"):
        raise SystemExit("baseline gem5 build failed:\n" + (build.get("log") or "")[-4000:])

    records = run_workloads(build["binary"], names, env={},
                            timeout_s=C.GEM5_RUN_TIMEOUT_S, label="baseline")
    good = [r for r in records if r["ok"]]
    agg = dict(p2p_metrics.aggregate([r["metrics"] for r in good])) if good else {}
    agg.update({
        "n": len(good),
        "failed": [r["name"] for r in records if not r["ok"]],
        "trace_list": _repo_relative(workload_list),
        "host_revision": checkout_revision(),
        "isa": C.GEM5_ISA,
        "variant": C.GEM5_VARIANT,
        "scons_args": C.GEM5_SCONS_ARGS,
        "scons_env": build_env(),
        "per_trace": {r["name"]: r["metrics"] for r in good},
        "per_trace_stats": {r["name"]: {**r["stats"], "wall_s": r["wall_s"]} for r in good},
        "workload_fingerprints": {n: prints[n] for n in names},
    })
    # And the files must still be what was installed. If they changed during
    # the runs, nobody can say which version the numbers describe.
    moved = sorted(n for n in names if workload_fingerprint(n) != prints[n])
    if moved:
        dump.json("gem5_baseline.json", agg)
        raise SystemExit(
            f"the run scripts or workload files changed while the baseline ran "
            f"({', '.join(moved)}), so {helpers.baseline_path(HOST, budget)} was left "
            f"alone. Re-record once nothing is editing them. The measurement is in "
            f"{dump.dir}."
        )
    if all(previous.get(k) == agg[k] for k in ("host_revision", "isa", "variant")):
        old_prints = previous.get("workload_fingerprints") or {}
        for name, metrics in (previous.get("per_trace") or {}).items():
            if name in agg["per_trace"]:
                continue
            now = prints.get(name)
            if now is not None and old_prints.get(name) == now:
                agg["per_trace"][name] = metrics
                agg["workload_fingerprints"][name] = now
                if name in (previous.get("per_trace_stats") or {}):
                    agg["per_trace_stats"][name] = previous["per_trace_stats"][name]
    dump.json("gem5_baseline.json", agg)
    if agg["failed"]:
        dump.text("gem5_baseline_failures.txt", _failure_tail(records, limit=20000))
    if len(good) != len(names):
        raise SystemExit(
            f"baseline ran {len(good)} of {len(names)} workloads; failed: {agg['failed']}. "
            f"A baseline over a different workload set than the plan will name is not a "
            f"baseline, so {helpers.baseline_path(HOST, budget)} was left alone. The "
            f"measurement is in {dump.dir}."
        )
    helpers.record_baseline(HOST, budget, agg)
    return agg
