"""The CBP2025 kit, as stage 3 and the verify gate see it.

`loop/tests/toy_host.py` is the same three objects against a fixture that
lives on one machine. This is the production version, and the whole
difference is that nothing here is local: the checkout is on a cluster node,
the traces are on two of them, and the process asking the questions is the
head. So every method below is a Ray dispatch, and which token it asks for is
the only interesting decision in the file.

Two tokens, and the split is the thing to understand:

  cbp2025_host   exactly one node -- the one holding the checkout. The
                 agent's shell, the build, and any command a test plan
                 names all ask for this. They have to agree on a machine,
                 because a build that lands somewhere else compiles a tree
                 nobody edited and the gate cannot tell the difference.
  cbp2025        every node holding the traces. Only trace runs ask for it.
                 That is safe because `CBP2025Node.run` receives the built
                 binary as bytes: a trace run never reads the checkout, so
                 it may run anywhere, and the fan-out is the whole reason
                 the gate finishes in minutes.

What this file deliberately does not decide: which workloads to run, which
metrics to compare, at what tolerance, or what counts as the feature
working. All of that is in the test plan, because a gate condition hardcoded
here is one the plan cannot state and a reader cannot audit. What stays is
what no plan can express -- how to build this host, how to flip its knob,
and how to get numbers out of its stdout.

Storage is not one of the gate's questions. Only the DSE stage knows about
resource constraints (docs/stages.md), so nothing here carries a budget.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Optional, Sequence

from chia.base.ChiaFunction import ChiaFunction, get

import constants as C
import gate
import helpers
import plan_runner
from chia_nodes.cbp2025.cbp2025_node import CBP2025Node, _parse_measurement_rows

HOST = "cbp2025"
NOTES_PATH = Path(__file__).resolve().parent / "NOTES.md"

# The three names `CBP2025Node.aggregate` reports, which are therefore the
# only names a test plan's `metric_keys` may use. `parse_metrics` below emits
# the same three off a single run so that one trace and sixty traces produce
# the same keys -- a correctness entry comparing a single-trace command
# against a recorded baseline would otherwise be comparing `mpki` against
# `brmispki_50perc_amean` and reporting both as missing.
METRIC_KEYS = (
    "brmispki_50perc_amean",
    "cycwppki_50perc_amean",
    "ipc_50perc_amean",
)

# _parse_measurement_rows' 50perc row -> the aggregate's names.
_ROW_TO_METRIC = {
    "mpki": "brmispki_50perc_amean",
    "cycwppki": "cycwppki_50perc_amean",
    "ipc": "ipc_50perc_amean",
}


# What this host's budget does not count. The kit's README: "The amount of
# state needed to checkpoint histories will NOT be counted towards the
# predictor budget." TAGE-SC-L's own checkpoint map (pred_time_histories) is
# not in its predictorsize() either, so charging a port's equivalent would
# hold the feature to a rule the baseline is not held to. Stage 4's storage
# constraint reads this (dse.budget_exempt, constraints.storage_bits).
BUDGET_EXEMPT = ("checkpoint",)


# --------------------------------------------------------------- remote work


@ChiaFunction(resources={C.CBP2025_HOST_RESOURCE: 1.0})
def host_shell(cwd: str, command: str, env: dict | None, timeout_s: int) -> dict:
    """One shell command on the node that owns the checkout.

    `output` is the command's own stdout and stderr and nothing else. It is
    deliberately not prefixed with the command line: a `stdout_excludes`
    pass condition is matched against this text, so an echoed command would
    let the entry fail on a word that appears only in its own invocation.
    The failing entry's id and command are already in the test plan.

    Returns a dict rather than raising, for plan_runner's reason: a hung or
    crashed test is a gate failure with a diagnosis, and an exception here
    would instead take down the stage that was trying to diagnose it.

    Output is decoded with errors="replace", as gem5's host_shell already
    does. The run of 2026-09-24 had the integration agent leave a helper
    script holding one non-UTF-8 byte in the port tree; `git diff` prints an
    untracked text file inline, so port_diff raised UnicodeDecodeError
    instead of returning, and save_port calls it unguarded when a round
    ends -- after the gate, before stage 4."""
    merged = {**os.environ, **{k: str(v) for k, v in (env or {}).items()}}
    try:
        proc = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True, text=True,
            errors="replace", timeout=timeout_s, env=merged,
        )
    except subprocess.TimeoutExpired as e:
        # The partial output on a timeout is bytes whatever text= says.
        partial = "".join(
            s.decode("utf-8", "replace") if isinstance(s, bytes) else (s or "")
            for s in (e.stdout, e.stderr))
        return {
            "exit_code": -1,
            "output": f"{partial}\n[{command!r} timed out after {timeout_s}s]",
            "timed_out": True,
        }
    except OSError as e:
        return {"exit_code": -1, "output": f"[could not run {command!r}: {e}]",
                "timed_out": False}
    return {
        "exit_code": proc.returncode,
        "output": proc.stdout + proc.stderr,
        "timed_out": False,
    }


def _git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


@ChiaFunction(resources={C.CBP2025_HOST_RESOURCE: 1.0})
def restore_checkout(root: str) -> dict:
    """Put a checkout back to the commit it claims to be at.

    An agent with a shell leaves things behind. Stage 2's planner is allowed
    to build the host and run its suite, so object files and a binary are
    expected. What is not expected is source: on the first real stage-2 run
    the planner wrote a `test_sr.cc` containing
    `int main(){ std::cout << "Test passed"; }` while working out the
    compile command for the spec unit tests, and left it there. That file
    then travelled into the port tree, and all seven `spec_unit_test`
    entries passed G3 against a tree nobody had ported into.

    `git clean -fdx` plus `reset --hard` is the only reliable answer,
    because there is no list of "files an agent might leave" to enumerate.
    Nothing of value is lost: the kit's sample traces are tracked, and build
    output is meant to be rebuilt."""
    before = _git(root, "status", "--porcelain").stdout
    _git(root, "reset", "--hard", "HEAD")
    removed = _git(root, "clean", "-fdx").stdout
    return {
        "root": root,
        "was_dirty": bool(before.strip()),
        "removed": [line for line in removed.splitlines() if line.strip()],
        "revision": _git(root, "rev-parse", "HEAD").stdout.strip(),
    }


@ChiaFunction(resources={C.CBP2025_HOST_RESOURCE: 1.0})
def materialize_port_tree(
    src: str, dst: str, fresh: bool = True, reset: bool = True
) -> dict:
    """Lay down the tree stage 3 is allowed to edit, as a copy of the
    pristine checkout, reset to the commit the plan was written against.

    The agent never edits `src`. Stage 2 read that tree to record
    `host_revision` and every clean-tree result in the test plan, and
    `--stage baseline` builds it to produce the numbers G2 compares against;
    an agent editing it in place would leave both describing a tree that no
    longer exists, and the next baseline run would measure the port.

    The copy is then reset and cleaned rather than trusted. See
    `restore_checkout` for what stage 2 actually left behind the first time
    this ran, and why "copy whatever is there" is not good enough. It also
    removes the build output, which matters on its own: a first attempt that
    never compiled anything could otherwise still run ./cbp.

    `.git` travels with the copy so the port tree answers `git rev-parse
    HEAD` and `git diff` the same way -- the diff is how a run is reviewed
    afterwards, and a copy without history cannot produce one."""
    source, target = Path(src), Path(dst)
    if not source.exists():
        return {"ok": False, "error": f"{src} does not exist on this node"}
    if fresh and target.exists():
        shutil.rmtree(target)
    created = not target.exists()
    if created:
        shutil.copytree(source, target, symlinks=True)
    # Only a tree we just laid down. Resetting an existing one would delete
    # the port it holds, which is the opposite of what `fresh=False` is for:
    # that flag exists so a run which died partway can pick up the tree it
    # left.
    removed = ""
    if created and reset:
        _git(target, "reset", "--hard", "HEAD")
        removed = _git(target, "clean", "-fdx").stdout
    elif created:
        # Copying a tree that already holds a port: keep the source, drop
        # only the build output so the first build is this tree's own.
        for stale in (*target.glob("*.o"), *target.glob("lib/*.o"),
                      target / "cbp", target / "lib" / "libcbp.a"):
            if stale.exists():
                stale.unlink()
    return {
        "ok": True,
        "path": str(target),
        "reused": not created,
        "revision": _git(target, "rev-parse", "HEAD").stdout.strip()
                    or "(not a git checkout)",
        "cleaned": [line for line in removed.splitlines() if line.strip()],
    }


_PRINTSIZE_OFF = "//#define PRINTSIZE"
_SIZE_RE = re.compile(r"\((TAGE|LOOP|SC|TOTAL) (\d+)")


@ChiaFunction(resources={C.CBP2025_HOST_RESOURCE: 1.0})
def measure_host_storage(cbp_root: str, timeout_s: int = 600) -> dict:
    """The host predictor's storage in bits, by its own accounting.

    TAGE-SC-L carries `predictorsize()`, which sums every table from the
    same defines that size them, and prints it at setup when `PRINTSIZE` is
    defined. This builds a scratch copy with that one line switched on and
    runs the bundled int sample trace just long enough to read the line.
    The checkout itself is never touched.

    Stage 2 compares the plan's `host_storage.baseline_bits` with this, so
    the number stage 4 costs every candidate against is the host's own
    rather than one the planner recalled. Measured on this kit at commit
    6074966: TAGE 463917, LOOP 1248, SC 59450, TOTAL 524615. The loop
    predictor's 1248 bits are counted twice, once alone and once inside the
    SC figure, because `predictorsize()` keeps accumulating into the same
    variable; the total above is that function's, double count included."""
    import tempfile

    source = Path(cbp_root)
    with tempfile.TemporaryDirectory(prefix="p2p_hostsize_") as scratch:
        tree = Path(scratch) / "tree"
        shutil.copytree(source, tree, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "*.o", "cbp"))
        header = tree / "cbp2016_tage_sc_l.h"
        text = header.read_text()
        if _PRINTSIZE_OFF not in text:
            return {"ok": False, "error": f"no '{_PRINTSIZE_OFF}' line in {header.name}"}
        header.write_text(text.replace(_PRINTSIZE_OFF, "#define PRINTSIZE", 1))
        try:
            build = subprocess.run("make clean && make -j", shell=True, cwd=tree,
                                   capture_output=True, text=True, timeout=timeout_s)
            if build.returncode != 0:
                return {"ok": False, "error": "build failed",
                        "log": (build.stdout + build.stderr)[-2000:]}
            run = subprocess.run(
                ["./cbp", "sample_traces/int/sample_int_trace.gz"], cwd=tree,
                capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timed out after {timeout_s}s"}
        parts = {k.lower(): int(v) for k, v in _SIZE_RE.findall(run.stdout + run.stderr)}
        if "total" not in parts:
            return {"ok": False, "error": "no '(TOTAL N bits' line in the output",
                    "log": (run.stdout + run.stderr)[-2000:]}
        return {"ok": True, "bits": parts["total"], "parts": parts,
                "measured_by": "predictorsize() in cbp2016_tage_sc_l.h, built with "
                               "PRINTSIZE on a scratch copy of the checkout"}


def host_storage_bits(cbp_root: str = C.CBP2025_ROOT) -> Optional[int]:
    """`measure_host_storage` on the checkout node, or None if it failed.

    None skips the stage-2 comparison rather than failing the stage: the plan
    still has to be self-consistent, and the reason is printed."""
    result = get(measure_host_storage.chia_remote(cbp_root))
    if not result.get("ok"):
        print(f"[plan] could not measure the host's storage: {result.get('error')}")
        return None
    return result["bits"]


@ChiaFunction(resources={C.CBP2025_HOST_RESOURCE: 0.1})
def host_revision(cbp_root: str) -> str:
    """The commit the host checkout is at, read on the node that has it.

    Stage 2 asks the planning agent to record this itself, and this is what
    the answer is checked against: a `host_revision` the planner invented
    means every clean-tree result in its test plan is about a tree nobody
    ran."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cbp_root, capture_output=True, text=True
    )
    return proc.stdout.strip() or "(not a git checkout)"


# ------------------------------------------------------------------ executor


def parse_metrics(output: str) -> dict:
    """The "50 Perc instructions" row of one ./cbp run, under the same names
    the suite aggregate uses. `{}` when the output holds no such row, which
    is how a crashed run reaches the gate as a failed entry rather than as an
    exception."""
    rows = _parse_measurement_rows(output or "")
    row = rows.get("50perc")
    if not row:
        return {}
    return {name: row[field] for field, name in _ROW_TO_METRIC.items() if field in row}


def enable_env(feature_enable: dict, feature_on: bool) -> dict:
    """The environment that turns the port on or off.

    Every alias the plan could plausibly have used is set to the same value,
    because getting this wrong is silent: a port reading a name the gate does
    not set stays off in both states, G2 passes trivially, and G5 then
    reports that the mechanism never reached the metric. The aliases are the
    plan's own `feature_enable.name`, that name upper-cased, and its `macro`
    (`SR_<NAME>`) when the enable knob is also a spec parameter and therefore
    also a #define in the header stage 4 mutates.
    """
    value = "1" if feature_on else "0"
    names = {
        (feature_enable or {}).get("name"),
        ((feature_enable or {}).get("name") or "").upper() or None,
        (feature_enable or {}).get("macro"),
    }
    return {n: value for n in names if n}


class CBP2025Executor:
    """plan_runner.HostExecutor over a CBP2025 checkout on a cluster node."""

    name = HOST

    def __init__(
        self,
        work_dir: str,
        feature_enable: dict,
        metric_keys: Sequence[str] = METRIC_KEYS,
        trace_dir: str = C.TRACE_DIR,
        rebuild_per_state: Optional[bool] = None,
    ):
        self.work_dir = str(work_dir)
        self.trace_dir = str(trace_dir)
        self.feature_enable = feature_enable or {}
        self.metric_keys = tuple(metric_keys)
        # Whether flipping the knob costs a rebuild. A plan that binds the
        # enable knob at compile time has to be rebuilt per state; one that
        # reads it with getenv() does not, and rebuilding anyway would double
        # every gate attempt's build time for nothing. Derived from the
        # plan's own `binding` rather than assumed, because the gate must
        # measure the port the plan describes and not the one it expected.
        if rebuild_per_state is None:
            rebuild_per_state = self.feature_enable.get("binding") != "runtime_env"
        self.rebuild_per_state = bool(rebuild_per_state)
        self._binaries: dict[bool, bytes] = {}
        self._build_logs: dict[bool, str] = {}
        # Which state the ./cbp sitting in the checkout was built for, as
        # opposed to which states we hold bytes for. A trace run gets its
        # binary as bytes and does not care, but a shell command runs
        # whatever is in the tree, so the two have to be tracked separately.
        self._tree_state: Optional[bool] = None
        self._last_build_error: str = ""

    # --------------------------------------------------------------- build
    def _build_key(self, feature_on: bool) -> bool:
        return feature_on if self.rebuild_per_state else False

    def build(self, *, feature_on: bool, timeout_s: int = C.BUILD_TIMEOUT_S,
              force: bool = False):
        key = self._build_key(feature_on)
        # The cache is only good while the tree still holds that build. With
        # a compile-time knob the tree swaps state under us, and then a
        # cached "hit" would report success for a ./cbp built the other way.
        if not force and key in self._binaries and self._tree_state == key:
            return plan_runner.BuildOutcome(
                ok=True, log=self._build_logs[key], handle=self._binaries[key]
            )
        env = enable_env(self.feature_enable, key) if self.rebuild_per_state else {}
        result = get(
            CBP2025Node.build.options(resources={C.CBP2025_HOST_RESOURCE: 1.0})
            .chia_remote(self.work_dir, None, timeout_s, env)
        )
        if not result.success:
            self._tree_state = None
            return plan_runner.BuildOutcome(ok=False, log=result.log)
        self._binaries[key] = result.binary
        self._build_logs[key] = result.log
        self._tree_state = key
        return plan_runner.BuildOutcome(ok=True, log=result.log, handle=result.binary)

    def _ensure_tree_state(self, feature_on: bool) -> None:
        """Make the ./cbp in the checkout be the one this state needs.

        A no-op for the `runtime_env` binding this host recommends, where one
        binary serves both states. It is not a no-op for a plan that binds
        the enable knob at compile time: there, a correctness entry declaring
        `feature_state: "on"` would otherwise run whichever binary the last
        build happened to leave behind -- and the last build is the
        feature-off one `run_test_plan` starts with. The entry would then
        measure the baseline and pass, which is the worst kind of wrong."""
        key = self._build_key(feature_on)
        if not self.rebuild_per_state or self._tree_state == key:
            return
        self.build(feature_on=feature_on, force=True)

    def _binary_for(self, feature_on: bool) -> Optional[bytes]:
        """The binary a run in this state needs.

        Builds it when the plan's knob is compile-time and only the other
        state has been built so far. A failure records the compiler output
        in `_last_build_error`, because the only thing `run_traces` can
        otherwise say is that every trace failed -- which reads as a broken
        trace list rather than as a port that does not compile in this
        state."""
        key = self._build_key(feature_on)
        if key not in self._binaries:
            outcome = self.build(feature_on=feature_on)
            if not outcome.ok:
                self._last_build_error = outcome.log
        return self._binaries.get(key)

    # --------------------------------------------------------------- shell
    def shell(
        self, command: str, *, feature_on: bool,
        env: Optional[Mapping[str, str]] = None, timeout_s: int = C.RUN_TIMEOUT_S,
    ):
        # The knob is applied here, not by the runner, because only the host
        # knows how a value reaches it. On this host that is an environment
        # variable the predictor reads in beginCondDirPredictor().
        self._ensure_tree_state(feature_on)
        merged = {**enable_env(self.feature_enable, feature_on), **(env or {})}
        out = get(
            host_shell.options(resources={C.CBP2025_HOST_RESOURCE: 1.0})
            .chia_remote(self.work_dir, command, merged, timeout_s)
        )
        return plan_runner.ShellOutcome(
            exit_code=out["exit_code"], output=out["output"],
            timed_out=out["timed_out"],
        )

    def parse_metrics(self, output: str) -> dict:
        return parse_metrics(output)

    # ---------------------------------------------------------- trace runs
    def run_traces(
        self, traces: Sequence[str], *, feature_on: bool,
        timeout_s: int = C.RUN_TIMEOUT_S,
    ):
        """This host's native fan-out: one ./cbp process per trace, spread
        over every node advertising `cbp2025`, aggregated the way the kit's
        own scripts/trace_exec_training_list.py aggregates a suite."""
        binary = self._binary_for(feature_on)
        if not binary:
            state = "on" if feature_on else "off"
            return plan_runner.TraceOutcome(
                ok=False, metrics={}, failed=list(traces),
                log_tail=f"the host did not build with the feature {state}, so "
                         f"no trace was run:\n{self._last_build_error[-3000:]}",
            )
        env = enable_env(self.feature_enable, feature_on)
        refs = [
            CBP2025Node.run.options(resources={C.CBP2025_RESOURCE: 1.0})
            .chia_remote(binary, f"{self.trace_dir}/{t}", (), timeout_s, env)
            for t in traces
        ]
        results = [get(r) for r in refs]
        agg = get(CBP2025Node.aggregate.chia_remote(results))
        # aggregate() names failures by absolute path; the plan named them
        # relative to the trace dir, and a gate reason quoting the other one
        # does not match anything the reader can look up in the list.
        prefix = self.trace_dir.rstrip("/") + "/"
        failed = [f[len(prefix):] if f.startswith(prefix) else f
                  for f in agg.get("failed", [])]
        metrics = {k: v for k, v in agg.items() if k not in ("n", "failed")}
        tail = ""
        for r in results:
            # `None` is what a Ray task that died leaves behind. aggregate()
            # already counts it as a failure; this loop only wants its log,
            # and a None here would take the gate down with an AttributeError
            # instead of reporting the failure it was built to report.
            if r is None or not r.success:
                tail = (getattr(r, "log", "") or "")[-2000:]
        return plan_runner.TraceOutcome(
            ok=(not failed and agg.get("n") == len(traces)),
            metrics=metrics, failed=failed, log_tail=tail,
        )


# ------------------------------------------------------------------- adapter


def restore_host_checkout(root: str = C.CBP2025_ROOT) -> dict:
    """Undo whatever the last agent left in the pristine checkout.

    Refuses the port tree outright. `restore_checkout` is `git reset --hard`
    plus `git clean -fdx`, which on `CBP2025_PORT_ROOT` would delete an
    integration run's entire work with no copy anywhere. Every call site
    today passes the pristine root, and this is here so that a future one
    that does not fails loudly instead of quietly."""
    if Path(root).resolve() == Path(C.CBP2025_PORT_ROOT).resolve():
        raise SystemExit(
            f"refusing to reset {root}: that is the tree stage 3 edits, and "
            f"restoring it would delete the port. Only {C.CBP2025_ROOT} is "
            f"restorable."
        )
    return get(restore_checkout.chia_remote(root))


def dse_tree(fresh: bool = True) -> str:
    """A copy of the ported tree for stage 4 to search in.

    Copied without a reset, because the port is the thing being tuned.
    Stage 4 overlays a candidate `sr_params.h` on every iteration, so
    searching in the ported tree itself would leave the integration's own
    header holding whichever candidate ran last."""
    result = get(materialize_port_tree.chia_remote(
        C.CBP2025_PORT_ROOT, C.CBP2025_DSE_ROOT, fresh, False
    ))
    if not result.get("ok"):
        raise SystemExit(
            f"could not copy the ported tree for the search: "
            f"{result.get('error')}. Run --stage integrate first; "
            f"{C.CBP2025_PORT_ROOT} has to exist on the "
            f"{C.CBP2025_HOST_RESOURCE} node."
        )
    return result["path"]


def header_build(root: str, header_name: str, env: dict | None):
    """`build(header_text) -> bytes | None` over one tree, the callable
    dse.preflight takes. The header is overlaid onto `root` in place, so
    `root` must be a copy: the DSE tree for stage 4, the reach tree for G6."""
    def build(header_text: str):
        result = get(CBP2025Node.build.options(
            resources={C.CBP2025_HOST_RESOURCE: 1.0}
        ).chia_remote(root, {header_name: header_text.encode()},
                      C.BUILD_TIMEOUT_S, env))
        return result.binary if result.success else None
    return build


def knob_reach(spec: dict, port_plan: dict) -> dict:
    """G6's measurement: stage 4's preflight, on a fresh copy of the port.

    Built with the feature on, as stage 4 builds, because a port that binds
    the enable knob at compile time may compile the feature's code out when
    it is off, and every SR_* knob would then read as inert. The header is
    regenerated from the plan in force, not read off the tree, because that
    regenerated file is the one stage 4 will overlay."""
    import dse

    result = get(materialize_port_tree.chia_remote(
        C.CBP2025_PORT_ROOT, C.CBP2025_REACH_ROOT, True, False
    ))
    if not result.get("ok"):
        return {"blocking": [f"could not copy the port tree to check its knobs: "
                             f"{result.get('error')}"], "warnings": [], "knobs": []}
    env = enable_env((port_plan or {}).get("feature_enable") or {}, True)
    build = header_build(result["path"], dse.params_header_name(spec), env)
    return dse.preflight(build, spec, port_plan, dse.params_header(spec, port_plan))


def clean_port_tree(fresh: bool = True) -> dict:
    """Put a pristine copy of the checkout where stage 3 may edit it."""
    result = get(materialize_port_tree.chia_remote(
        C.CBP2025_ROOT, C.CBP2025_PORT_ROOT, fresh
    ))
    if not result.get("ok"):
        raise SystemExit(
            f"could not materialize the cbp2025 port tree: {result.get('error')}. "
            f"Is the cluster up, and does {C.CBP2025_ROOT} exist on the "
            f"{C.CBP2025_HOST_RESOURCE} node?"
        )
    return result


def checkout_revision() -> str:
    return get(host_revision.chia_remote(C.CBP2025_ROOT))


def notes() -> str:
    return NOTES_PATH.read_text()


def run_gate(baseline: dict, port_plan: dict, test_plan: dict) -> gate.GateResult:
    """Run the test plan against the port tree, then let gate.check_gate
    judge it. Every condition and every threshold comes from the plan.

    A fresh executor per attempt on purpose: the agent has edited the tree
    since the last one, so a cached binary is a measurement of the previous
    attempt wearing this attempt's verdict."""
    executor = CBP2025Executor(
        work_dir=C.CBP2025_PORT_ROOT,
        feature_enable=(port_plan or {}).get("feature_enable") or {},
        metric_keys=(test_plan or {}).get("metric_keys") or METRIC_KEYS,
    )
    results = plan_runner.run_test_plan(executor, test_plan, port_plan, baseline)
    return gate.check_gate(results)


# Build output and the agent's own scratch files, which `git add -AN .`
# would otherwise pull into the recorded patch. The first real run produced
# a 21-file diff that was mostly object files.
_DIFF_EXCLUDES = " ".join(
    f"':(exclude){pattern}'"
    for pattern in ("*.o", "*.a", "cbp", "test_sr", "*.patch", "*_out.txt")
)


def port_diff() -> str:
    """What the agent changed, as a patch.

    `git diff` in the port tree: materialize_port_tree copies `.git`
    precisely so this works. `add -AN` is what makes a file the agent
    created show up at all, and the index is reset afterwards so the tree is
    left exactly as it was found -- a run that resumes with
    P2P_CBP2025_PORT_FRESH=0 must not inherit a staged index it did not
    make."""
    command = (
        f"git add -AN -- . {_DIFF_EXCLUDES} >/dev/null 2>&1; "
        f"echo '--- diffstat ---'; git diff --stat -- . {_DIFF_EXCLUDES}; "
        f"echo '--- patch ---'; git diff -- . {_DIFF_EXCLUDES}; "
        f"git reset -q >/dev/null 2>&1 || true"
    )
    out = get(
        host_shell.options(resources={C.CBP2025_HOST_RESOURCE: 0.1})
        .chia_remote(C.CBP2025_PORT_ROOT, command, {}, 180)
    )
    return out["output"]
