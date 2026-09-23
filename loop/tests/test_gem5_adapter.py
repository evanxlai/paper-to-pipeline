"""Unit tests for the gem5 host adapter.

Everything here is a part of `hosts/gem5/adapter.py` that decides a gate
verdict or protects a tree, and needs no cluster to exercise: which tree a
restore may touch and what it keeps, what a copy carries, which environment
reaches scons, which binary each state runs, how a run is judged, what
lands in the recorded baseline, what the run dir install notices, when the
gate refuses a stale baseline, and how long each wait on the node lasts.

Each one fails quietly in production. A restore that deletes build/ costs
an 11-minute rebuild. A CC on the scons command line is silently ignored by
gem5 v25.1. A stale binary makes a correctness entry measure the baseline
and pass. A run whose guest failed but whose gem5 exited 0 reads as a clean
smoke. A fan-out that waits on each run before starting the next makes a
perf list take as long as its runs added up.

These are fakes, and a fake is never evidence that the host works. The
cluster scripts are loop/tests/gem5_cluster_smoke.py and
loop/tests/gem5_gate_smoke.py.

The adapter's numbers come from hosts/gem5/run/p2p_metrics.py, and these
tests use that real module. A fake run result carries a whole stats.txt as
text, which is what chia's run_gem5 returns with capture_stats=True, and the
real parser reads it. loop/tests/fixtures/gem5/stats_gapbs_bfs_s.txt is a
real stats.txt from the first cluster run.
"""

import io
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

import constants as C
import helpers
from hosts.gem5 import adapter
from hosts.gem5.run import p2p_metrics

# A real stats.txt from the cluster (gapbs_bfs_s, one dump, trimmed; see the
# README next to it). The counts below are copied from it.
REAL_STATS = Path(__file__).resolve().parent / "fixtures" / "gem5" / "stats_gapbs_bfs_s.txt"
REAL_INSTS = 2509944        # system.cpu.commitStats0.numInsts
REAL_CYCLES = 2583914       # system.cpu.numCycles
REAL_DIRECT_COND = 34742    # system.cpu.branchPred.mispredicted_0::DirectCond
REAL_INDIRECT_COND = 0      # system.cpu.branchPred.mispredicted_0::IndirectCond
REAL_ALL_MISPREDICTS = 35711  # mispredicted_0::total, and condIncorrect


@pytest.fixture(autouse=True)
def no_ray(monkeypatch):
    """Keep every test here off Ray.

    Calling a ChiaFunction locally builds chia's profiler, and the profiler
    looks up its collector actor with ray.get_actor. Ray answers that by
    running ray.init() with no address, which joins whatever cluster
    /tmp/ray/ray_current_cluster names. On the head that is the live
    cluster. So the lookup is stubbed out (no collector means a disabled
    profiler, which is also what the live cluster answers), and a ray.init
    that still happens fails the test instead of connecting."""
    import ray
    from chia.trace import profiler

    monkeypatch.setattr(profiler, "get_collector", lambda namespace=None: None)
    monkeypatch.setattr(profiler, "_profiler", None)

    def refuse(*args, **kwargs):
        raise AssertionError("a gem5 adapter unit test tried to start or join Ray")

    monkeypatch.setattr(ray, "init", refuse)


_PDF_ROW = object()  # marks a row of a pdf vector, printed with two % columns


def stats_text(insts=1_000_000, cycles=500_000, direct=1800, indirect=0, total=2500,
               scales=(1,)):
    """A small stats.txt in the line shapes gem5 v25.1 prints (compare
    REAL_STATS). A scalar is `name value # desc`. A row of a pdf vector such
    as mispredicted_0 is `name value pdf% cdf% # desc`, and that second shape
    is the one chia's own parser cannot read. One dump per entry of
    `scales`, each count multiplied by it; the last dump is the one that
    counts. A count of None leaves its row out."""
    rows = [
        ("simInsts", insts, None),
        ("system.cpu.numCycles", cycles, None),
        ("system.cpu.branchPred.mispredicted_0::DirectCond", direct, _PDF_ROW),
        ("system.cpu.branchPred.mispredicted_0::IndirectCond", indirect, _PDF_ROW),
        ("system.cpu.branchPred.mispredicted_0::total", total, None),
        ("system.cpu.branchPred.condIncorrect", total, None),
        ("system.cpu.commitStats0.numInsts", insts, None),
    ]
    out = []
    for scale in scales:
        out.append("\n---------- Begin Simulation Statistics ----------")
        for name, value, kind in rows:
            if value is None:
                continue
            cols = "     72.00%     99.12%" if kind is _PDF_ROW else " " * 22
            out.append(f"{name:<45} {value * scale:>12}{cols} # (Count)")
        out.append("---------- End Simulation Statistics   ----------")
    return "\n".join(out) + "\n"


GOOD_STATS_TEXT = stats_text()
GOOD_INSTS = 1_000_000.0
# p2p_metrics.derive on GOOD_STATS_TEXT. cond_mpki counts the conditional
# rows only (1800 + 0), branch_mpki every mispredicted branch (2500). Every
# value is exact in binary floating point.
GOOD_METRICS = {"cond_mpki": 1.8, "branch_mpki": 2.5, "ipc": 2.0}
EXIT_OK = "guest says hi\nP2P_EXIT cause=exiting with last active thread context code=0\n"


class FakeRunResult:
    """The fields of chia's Gem5RunResult that the adapter reads.

    `stats_content` is the whole stats.txt, which run_gem5 returns when it is
    called with capture_stats=True. The adapter's metrics come from it.
    `stats` is chia's own parse, and it holds only what chia's grammar can
    read, so a test that passes proves the metrics did not come from it."""

    def __init__(self, name="w", status="ok", returncode=0,
                 stats_content=GOOD_STATS_TEXT, stdout=EXIT_OK, error=""):
        self.workload_name = name
        self.status, self.returncode = status, returncode
        self.stats_content = stats_content
        self.stats = {"cycles": 500_000.0, "insts": GOOD_INSTS}
        self.stdout_tail, self.error_messages = stdout, error
        self.wall_s = 12.5
        self.sim_insts = int(GOOD_INSTS)
        self.num_cycles = 500_000


class Remote:
    """A stand-in for a ChiaFunction: `.chia_remote` and `.options(...)`
    record the call and answer with `respond(*args)`."""

    def __init__(self, respond):
        self.respond, self.calls = respond, []

    def options(self, **kwargs):
        outer = self

        class _Handle:
            @staticmethod
            def chia_remote(*args, **kw):
                outer.calls.append({"args": args, "kwargs": kw, "options": kwargs})
                return outer.respond(*args, **kw)

        return _Handle()

    def chia_remote(self, *args, **kw):
        self.calls.append({"args": args, "kwargs": kw, "options": None})
        return self.respond(*args, **kw)


@pytest.fixture
def identity_get(monkeypatch):
    """get() that hands back what the fake task returned. Every call must
    carry a timeout, because a get() without one waits for ever on a node
    that vanished (adapter._wait). Returns the timeouts, in call order."""
    waits = []

    def fake_get(ref, timeout=None):
        assert timeout is not None, "a get() with no timeout can wait for ever"
        waits.append(timeout)
        return ref

    monkeypatch.setattr(adapter, "get", fake_get)
    return waits


# ------------------------------------------------------------- git fixtures


def _git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(a, cwd=path, capture_output=True, check=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    # gem5's own ignore rules for the paths these tests touch (.gitignore:3,9,13).
    (path / ".gitignore").write_text("build\n*.pyc\nm5out\n")
    (path / "src" / "cpu" / "pred").mkdir(parents=True)
    (path / "src" / "cpu" / "pred" / "tage_sc_l.cc").write_text("// pristine\n")
    run("git", "add", "-A")
    run("git", "commit", "-qm", "initial")
    return path


def _add_build(path, binary=b"pristine gem5"):
    exe = path / "build" / "ARM" / "gem5.opt"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(binary)
    (path / "build" / "ARM" / "gem5.build").mkdir(exist_ok=True)
    (path / "build" / "ARM" / "gem5.build" / "sconsign").write_text("signatures")
    return exe


def _leave_agent_debris(path):
    (path / "src" / "cpu" / "pred" / "test_sr.cc").write_text('int main(){puts("Test passed");}\n')
    (path / "src" / "cpu" / "pred" / "tage_sc_l.cc").write_text("// planner scribbled here\n")
    (path / "m5out").mkdir(exist_ok=True)
    (path / "m5out" / "stats.txt").write_text("stale stats")
    (path / "src" / "__pycache__").mkdir(exist_ok=True)
    (path / "src" / "__pycache__" / "x.cpython-310.pyc").write_bytes(b"pyc")
    (path / "src" / "cpu" / "pred" / "build").mkdir(exist_ok=True)
    (path / "src" / "cpu" / "pred" / "build" / "sr_test.opt").write_text("not the top build")


# ------------------------------------------------------ restore and the copy


def test_restore_keeps_build_and_removes_everything_an_agent_left(tmp_path):
    """build/ is 11 minutes of compiling and holds scons's signature
    database, so the restore keeps it. Everything else an agent left goes,
    including files gem5's .gitignore hides and a build/ that is not the
    top-level one."""
    root = _git_repo(tmp_path / "gem5")
    exe = _add_build(root)
    _leave_agent_debris(root)

    out = adapter.restore_checkout(str(root))

    assert out["ok"] and out["was_dirty"]
    assert exe.read_bytes() == b"pristine gem5"
    assert (root / "build" / "ARM" / "gem5.build" / "sconsign").exists()
    assert not (root / "src" / "cpu" / "pred" / "test_sr.cc").exists()
    assert not (root / "m5out").exists()
    assert not (root / "src" / "__pycache__").exists()
    assert not (root / "src" / "cpu" / "pred" / "build").exists()
    assert (root / "src" / "cpu" / "pred" / "tage_sc_l.cc").read_text() == "// pristine\n"


def test_restore_of_a_missing_tree_is_reported_not_raised(tmp_path):
    out = adapter.restore_checkout(str(tmp_path / "nope"))
    assert out["ok"] is False and "does not exist" in out["error"]


def test_a_fresh_port_tree_carries_build_and_git_but_not_leftovers(tmp_path):
    """build/ and .git travel with the copy. The planner's leftovers must
    not: on cbp2025 a leftover test file satisfied seven unit tests against
    an unported tree."""
    src = _git_repo(tmp_path / "gem5")
    _add_build(src)
    _leave_agent_debris(src)

    out = adapter.materialize_port_tree(str(src), str(tmp_path / "gem5_port"))
    port = tmp_path / "gem5_port"

    assert out["ok"] and out["reused"] is False
    assert (port / ".git").is_dir()
    assert (port / "build" / "ARM" / "gem5.opt").read_bytes() == b"pristine gem5"
    assert (port / "build" / "ARM" / "gem5.build" / "sconsign").exists()
    assert not (port / "src" / "cpu" / "pred" / "test_sr.cc").exists()
    assert not (port / "m5out").exists()
    assert (port / "src" / "cpu" / "pred" / "tage_sc_l.cc").read_text() == "// pristine\n"
    assert out["revision"] == adapter._git(src, "rev-parse", "HEAD").stdout.strip()
    assert not list(tmp_path.glob(".gem5_port.partial-*"))


def test_the_copy_keeps_symlinks_and_mtimes(tmp_path):
    """cp -a, not a dereferencing copy. scons's MD5-timestamp decider
    re-hashes every file whose mtime moved, and a symlink copied as its
    target could point a build at the wrong tree."""
    src = _git_repo(tmp_path / "gem5")
    exe = _add_build(src)
    os.utime(exe, (1_000_000_000, 1_000_000_000))
    (src / "build" / "ARM" / "link").symlink_to("gem5.opt")

    adapter.materialize_port_tree(str(src), str(tmp_path / "port"))
    copied = tmp_path / "port" / "build" / "ARM"

    assert (copied / "link").is_symlink() and os.readlink(copied / "link") == "gem5.opt"
    assert os.stat(copied / "gem5.opt").st_mtime == 1_000_000_000


def test_reset_false_keeps_the_port_and_its_build(tmp_path):
    """What stage 4 needs: the ported tree, port and build output intact."""
    src = _git_repo(tmp_path / "port")
    _add_build(src, b"ported gem5")
    (src / "src" / "cpu" / "pred" / "tage_sc_l.cc").write_text("// the port\n")
    (src / "src" / "cpu" / "pred" / "sr_params.h").write_text("#define SR_NUM_BANKS 8\n")

    out = adapter.materialize_port_tree(str(src), str(tmp_path / "dse"), True, False)
    dse = tmp_path / "dse"

    assert out["ok"]
    assert (dse / "src" / "cpu" / "pred" / "tage_sc_l.cc").read_text() == "// the port\n"
    assert (dse / "src" / "cpu" / "pred" / "sr_params.h").exists()
    assert (dse / "build" / "ARM" / "gem5.opt").read_bytes() == b"ported gem5"


def test_fresh_false_reuses_an_existing_tree_untouched(tmp_path):
    """P2P_GEM5_PORT_FRESH=0 resumes a run that died partway. It has to
    return the tree as the dead run left it."""
    src = _git_repo(tmp_path / "gem5")
    port = tmp_path / "port"
    adapter.materialize_port_tree(str(src), str(port))
    (port / "src" / "cpu" / "pred" / "tage_sc_l.cc").write_text("// half a port\n")
    (port / "src" / "cpu" / "pred" / "sr_params.h").write_text("#define SR_X 1\n")

    out = adapter.materialize_port_tree(str(src), str(port), False)

    assert out["reused"] is True
    assert (port / "src" / "cpu" / "pred" / "tage_sc_l.cc").read_text() == "// half a port\n"
    assert (port / "src" / "cpu" / "pred" / "sr_params.h").exists()


def test_a_missing_source_is_reported_not_raised(tmp_path):
    out = adapter.materialize_port_tree(str(tmp_path / "nope"), str(tmp_path / "port"))
    assert out["ok"] is False and "does not exist" in out["error"]


def test_copying_onto_or_into_the_source_is_refused(tmp_path):
    """A fresh copy starts by deleting its destination. Pointed at its own
    source, it would delete the tree it was about to copy."""
    src = _git_repo(tmp_path / "gem5")
    for dst in (src, src / "inner"):
        out = adapter.materialize_port_tree(str(src), str(dst))
        assert out["ok"] is False and "refusing" in out["error"]
    assert (src / "src" / "cpu" / "pred" / "tage_sc_l.cc").exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode-000 file")
def test_a_failed_copy_leaves_nothing_at_the_destination(tmp_path):
    """A half-copied tree sitting at the destination is exactly what
    fresh=False would pick up and trust."""
    src = _git_repo(tmp_path / "gem5")
    secret = src / "unreadable"
    secret.write_text("x")
    secret.chmod(0)
    try:
        out = adapter.materialize_port_tree(str(src), str(tmp_path / "port"))
    finally:
        secret.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert out["ok"] is False and "cp -a" in out["error"]
    assert not (tmp_path / "port").exists()
    assert not list(tmp_path.glob(".port.partial-*"))


def test_restoring_the_port_or_the_search_tree_is_refused():
    """restore_checkout is reset --hard plus clean -fdx. Pointed at either
    tree, it deletes a port with no other copy."""
    for root in (C.GEM5_PORT_ROOT, C.GEM5_DSE_ROOT, C.GEM5_PORT_ROOT + "/"):
        with pytest.raises(SystemExit) as caught:
            adapter.restore_host_checkout(root)
        assert "refusing to reset" in str(caught.value)


# ------------------------------------------------------------ enable knob


def test_enable_env_matches_the_cbp2025_adapter():
    """Copied, not imported. The two hosts must set the same aliases, or a
    plan written for one silently leaves the other's port off."""
    from hosts.cbp2025 import adapter as cbp

    for enable in ({"name": "sr_enable", "macro": "SR_SR_ENABLE", "binding": "runtime_env"},
                   {"name": "TINYSC_ENABLE"}, {}, None):
        for state in (True, False):
            assert adapter.enable_env(enable, state) == cbp.enable_env(enable, state)


# ------------------------------------------------------ the scons environment


def test_scons_settings_move_from_the_command_line_to_the_environment():
    """gem5 v25.1 reads CC, CXX and PYTHON_CONFIG from the environment only
    (site_scons/gem5_scons/defaults.py:46-103). On the command line they are
    silently ignored, and gem5 links against whatever python3-config is
    first on PATH."""
    cli, env = adapter.split_scons_args(
        "--ignore-style --linker=gold PYTHON_CONFIG=/usr/bin/python3-config "
        "CC=/usr/lib/ccache/gcc CXX=/usr/lib/ccache/g++ EXTRAS=/x"
    )
    assert cli == "--ignore-style --linker=gold EXTRAS=/x"
    assert env == {"PYTHON_CONFIG": "/usr/bin/python3-config",
                   "CC": "/usr/lib/ccache/gcc", "CXX": "/usr/lib/ccache/g++"}


def test_a_compile_time_knob_becomes_ccflags_extra(monkeypatch):
    monkeypatch.setattr(C, "GEM5_SCONS_ARGS", "--ignore-style CC=gcc CCFLAGS_EXTRA=-O2")
    env = adapter.build_env({"sr_enable": "1", "SR_ENABLE": "1", "not-an-id": "1"})
    assert env["CC"] == "gcc"
    assert env["CCFLAGS_EXTRA"] == "-O2 -DSR_ENABLE=1 -Dsr_enable=1"
    assert adapter.build_env(None)["CCFLAGS_EXTRA"] == "-O2"
    monkeypatch.setattr(C, "GEM5_SCONS_ARGS", "--ignore-style")
    assert "CCFLAGS_EXTRA" not in adapter.build_env(None)


def test_a_compile_time_knob_never_defines_the_lower_case_name(fake_scons):
    """CCFLAGS_EXTRA is on every compile line of gem5. -Dsr_enable=0 there
    would turn a member or a Param called sr_enable into 0, and G1 would
    fail in files the agent did not write. The build defines the plan's
    macro and the upper-cased name. The runtime environment still carries
    all three aliases, because an environment variable collides with
    nothing."""
    fe = {"name": "sr_enable", "macro": "SR_SR_ENABLE", "binding": "compile_time_define"}
    assert adapter.define_env(fe, False) == {"SR_SR_ENABLE": "0", "SR_ENABLE": "0"}
    assert adapter.define_env({"name": "TINYSC_ENABLE"}, True) == {"TINYSC_ENABLE": "1"}
    assert adapter.define_env({"name": "sr-enable"}, True) == {}  # not an identifier
    ex = adapter.Gem5Executor("/w/port", fe)
    ex.build(feature_on=True)
    flags = fake_scons.calls[0]["args"][5]["CCFLAGS_EXTRA"].split()
    assert sorted(flags) == ["-DSR_ENABLE=1", "-DSR_SR_ENABLE=1"]
    env = ex.shell_env(True)
    assert sorted(env["CCFLAGS_EXTRA"].split()) == ["-DSR_ENABLE=1", "-DSR_SR_ENABLE=1"]
    assert env["sr_enable"] == env["SR_ENABLE"] == env["SR_SR_ENABLE"] == "1"


class FakeArtifact:
    def __init__(self, binary_path, success=True):
        self.binary_path, self.success = binary_path, success
        self.returncode = 0 if success else 2
        self.build_duration_s, self.base_rev = 3.2, "abc"
        self.stdout_tail = "scons: done building targets."
        self.stderr_tail = "" if success else "error: expected ';'"


def test_scons_build_applies_the_env_for_the_build_only(tmp_path, monkeypatch):
    """build_gem5 takes no environment, so the task sets os.environ around
    the call. It must be put back: Ray reuses the worker process, and a CC
    left behind would leak into the next task."""
    exe = _add_build(tmp_path)
    seen = {}

    def fake_build(root, isa, variant, *, jobs, extra_scons_args, timeout_s):
        seen.update(cc=os.environ.get("CC"), flags=os.environ.get("CCFLAGS_EXTRA"),
                    args=extra_scons_args, jobs=jobs, timeout=timeout_s)
        return FakeArtifact(str(exe))

    monkeypatch.setattr(adapter.Gem5Node, "build_gem5", staticmethod(fake_build))
    monkeypatch.setenv("CC", "the-worker-cc")
    monkeypatch.delenv("CCFLAGS_EXTRA", raising=False)

    out = adapter.scons_build(str(tmp_path), "ARM", "opt", 30, "--ignore-style",
                              {"CC": "ccache-gcc", "CCFLAGS_EXTRA": "-DSR=1"}, 600)

    assert out["ok"] and out["binary"] == str(exe)
    assert seen == {"cc": "ccache-gcc", "flags": "-DSR=1", "args": "--ignore-style",
                    "jobs": 30, "timeout": 600}
    assert os.environ["CC"] == "the-worker-cc"
    assert "CCFLAGS_EXTRA" not in os.environ


FAKE_SCONS = r'''#!/bin/sh
# Stands in for scons: records what it was given, then "builds" the target.
printf 'argv=%s\nCC=%s\nCCFLAGS_EXTRA=%s\n' "$*" "$CC" "$CCFLAGS_EXTRA" > scons_saw.txt
mkdir -p build/ARM && printf 'gem5' > build/ARM/gem5.opt
'''


def test_the_env_reaches_scons_through_chias_real_build_gem5(tmp_path, monkeypatch):
    """The claim scons_build rests on: build_gem5 passes no env of its own,
    so what the task puts in os.environ is what scons sees. Checked with
    chia's real build_gem5, called in-process, and a stand-in scons."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "scons").write_text(FAKE_SCONS)
    (bin_dir / "scons").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    root = tmp_path / "tree"
    root.mkdir()
    monkeypatch.delenv("CCFLAGS_EXTRA", raising=False)

    target = adapter.state_binary_path(str(root), True)
    out = adapter.scons_build(str(root), "ARM", "opt", 4, "--ignore-style --linker=gold",
                              {"CC": "/usr/lib/ccache/gcc", "CCFLAGS_EXTRA": "-DSR_X=1"},
                              60, target)

    assert out["ok"], out["log"]
    saw = (root / "scons_saw.txt").read_text()
    assert "argv=build/ARM/gem5.opt -j4 --ignore-style --linker=gold" in saw
    assert "CC=/usr/lib/ccache/gcc" in saw and "CCFLAGS_EXTRA=-DSR_X=1" in saw
    assert out["binary"] == target and open(target).read() == "gem5"
    assert "CCFLAGS_EXTRA" not in os.environ


def test_scons_build_that_left_no_binary_is_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter.Gem5Node, "build_gem5", staticmethod(
        lambda root, isa, variant, **kw: FakeArtifact(str(tmp_path / "missing"))))
    out = adapter.scons_build(str(tmp_path), "ARM", "opt", 4, "", {}, 60)
    assert out["ok"] is False and "does not exist" in out["log"]


def test_scons_build_copies_a_state_binary(tmp_path, monkeypatch):
    exe = _add_build(tmp_path, b"state on")
    monkeypatch.setattr(adapter.Gem5Node, "build_gem5", staticmethod(
        lambda root, isa, variant, **kw: FakeArtifact(str(exe))))
    target = adapter.state_binary_path(str(tmp_path), True)
    out = adapter.scons_build(str(tmp_path), "ARM", "opt", 4, "", {}, 60, target)
    assert out["binary"] == target
    assert open(target, "rb").read() == b"state on"


def test_scons_build_in_a_missing_tree_is_reported_not_raised(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("no such directory")
    monkeypatch.setattr(adapter.Gem5Node, "build_gem5", staticmethod(boom))
    out = adapter.scons_build(str(tmp_path / "nope"), "ARM", "opt", 4, "", {}, 60)
    assert out["ok"] is False and "could not start" in out["log"]


# ------------------------------------------------------- build state machine


@pytest.fixture
def fake_scons(monkeypatch, identity_get):
    """Every build dispatch, answered with a successful build dict."""

    def respond(root, isa, variant, jobs, cli, env, timeout_s, copy_to=None):
        return {"ok": True, "binary": copy_to or adapter.binary_path(root),
                "log": "built", "env": env}

    remote = Remote(respond)
    monkeypatch.setattr(adapter, "scons_build", remote)
    return remote


@pytest.fixture
def fake_shell(monkeypatch, identity_get):
    remote = Remote(lambda cwd, cmd, env, t: {"exit_code": 0, "output": "", "timed_out": False})
    monkeypatch.setattr(adapter, "host_shell", remote)
    return remote


def test_a_runtime_knob_builds_once_for_both_states(fake_scons):
    """The recommended binding. A second build would produce the same
    binary, and on gem5 an unneeded build is minutes of scons scanning."""
    ex = adapter.Gem5Executor("/w/port", {"name": "sr_enable", "binding": "runtime_env"})
    assert ex.rebuild_per_state is False
    assert ex.build(feature_on=False).ok
    assert ex.build(feature_on=True).ok
    assert len(fake_scons.calls) == 1
    root, isa, variant, jobs, cli, env, timeout_s, copy_to = fake_scons.calls[0]["args"]
    assert (root, isa, variant, jobs) == ("/w/port", C.GEM5_ISA, C.GEM5_VARIANT,
                                          C.GEM5_BUILD_JOBS)
    assert "CCFLAGS_EXTRA" not in env and copy_to is None


def test_a_compile_time_knob_builds_once_per_state_into_separate_binaries(fake_scons):
    """Each state is its own build, defined through CCFLAGS_EXTRA, and each
    lands at its own path so both can exist while runs of both states are in
    flight."""
    ex = adapter.Gem5Executor(
        "/w/port", {"name": "sr_enable", "macro": "SR_SR_ENABLE",
                    "binding": "compile_time_define"})
    assert ex.rebuild_per_state is True
    off = ex.build(feature_on=False)
    on = ex.build(feature_on=True)
    assert len(fake_scons.calls) == 2
    off_env, on_env = (c["args"][5] for c in fake_scons.calls)
    assert "-DSR_SR_ENABLE=0" in off_env["CCFLAGS_EXTRA"]
    assert "-DSR_ENABLE=0" in off_env["CCFLAGS_EXTRA"]
    assert "-DSR_SR_ENABLE=1" in on_env["CCFLAGS_EXTRA"]
    assert off.handle == adapter.state_binary_path("/w/port", False)
    assert on.handle == adapter.state_binary_path("/w/port", True)
    assert off.handle != on.handle


def test_no_binding_at_all_is_one_build(fake_scons):
    ex = adapter.Gem5Executor("/w/port", {})
    ex.build(feature_on=False)
    ex.build(feature_on=True)
    assert len(fake_scons.calls) == 1


def test_a_shell_in_the_other_state_rebuilds_a_compile_time_port(fake_scons, fake_shell):
    """run_test_plan builds feature-off first, then runs a correctness entry
    declaring feature_state "on". With a compile-time knob the tree still
    holds the feature-off binary, so that entry would measure the baseline
    and pass."""
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "compile_time_define"})
    ex.build(feature_on=False)
    ex.shell("python3 run_workload.py x", feature_on=True, timeout_s=60)
    assert len(fake_scons.calls) == 2
    assert "-DK=1" in fake_scons.calls[1]["args"][5]["CCFLAGS_EXTRA"]
    ex.shell("python3 run_workload.py x", feature_on=True, timeout_s=60)
    assert len(fake_scons.calls) == 2


def test_the_build_timeout_is_never_below_the_hosts_own(fake_scons):
    """run_test_plan passes its generic 900 s. A gem5 build in a fresh copy
    can take longer, and a build killed at 900 s reads as a G1 failure of
    the port."""
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    ex.build(feature_on=False, timeout_s=900)
    assert fake_scons.calls[0]["args"][6] == C.GEM5_BUILD_TIMEOUT_S


def test_a_failed_build_is_not_cached_as_a_success(monkeypatch, identity_get):
    remote = Remote(lambda *a: {"ok": False, "log": "error: expected ';'"})
    monkeypatch.setattr(adapter, "scons_build", remote)
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    first = ex.build(feature_on=False)
    assert not first.ok and "expected ';'" in first.log
    assert ex._tree_state is None
    assert not ex.build(feature_on=False).ok
    assert len(remote.calls) == 2


def test_a_build_task_that_raised_is_a_failed_build(monkeypatch):
    """A worker that died under the build must reach the gate as G1 with a
    reason, not as an exception that takes the stage down."""
    monkeypatch.setattr(adapter, "scons_build", Remote(lambda *a: "ref"))

    def dead(ref, timeout=None):
        raise RuntimeError("worker died")

    monkeypatch.setattr(adapter, "get", dead)
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    out = ex.build(feature_on=False)
    assert not out.ok and "worker died" in out.log


def test_an_undeliverable_binding_fails_the_build_with_the_reason(fake_scons):
    """The run scripts are fixed and read no knob. A python_param knob would
    stay off in both states, and G5 would blame the mechanism."""
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "python_param"})
    out = ex.build(feature_on=False)
    assert not out.ok and "python_param" in out.log and "runtime_env" in out.log
    assert fake_scons.calls == []


# --------------------------------------------------------------- the shell


def test_the_shell_sees_the_knob_the_binary_and_the_run_dir(fake_scons, fake_shell,
                                                            monkeypatch):
    monkeypatch.setattr(C, "GEM5_SCONS_ARGS", "--ignore-style CC=/usr/lib/ccache/gcc")
    ex = adapter.Gem5Executor("/w/port", {"name": "sr_enable", "binding": "runtime_env"})
    ex.build(feature_on=False)
    ex.shell("cmd", feature_on=True, env={"EXTRA": "1"}, timeout_s=60)
    call = fake_shell.calls[0]
    cwd, command, env, timeout_s = call["args"]
    assert (cwd, command, timeout_s) == ("/w/port", "cmd", 60)
    assert call["options"] == {"resources": {C.GEM5_HOST_RESOURCE: 1.0}}
    assert env["sr_enable"] == "1" and env["SR_ENABLE"] == "1"
    assert env["P2P_GEM5_BIN"] == adapter.binary_path("/w/port")
    assert env["P2P_GEM5_RUN_DIR"] == C.GEM5_RUN_DIR
    assert env["CC"] == "/usr/lib/ccache/gcc"
    assert env["EXTRA"] == "1"


def test_a_compile_time_shell_points_at_that_states_binary(fake_scons, fake_shell):
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "compile_time_define"})
    ex.build(feature_on=False)
    ex.shell("cmd", feature_on=True, timeout_s=60)
    env = fake_shell.calls[0]["args"][2]
    assert env["P2P_GEM5_BIN"] == adapter.state_binary_path("/w/port", True)
    assert env["CCFLAGS_EXTRA"] == "-DK=1"


def test_a_shell_task_that_raised_is_a_failed_command(fake_scons, monkeypatch):
    monkeypatch.setattr(adapter, "host_shell", Remote(lambda *a: "ref"))
    monkeypatch.setattr(adapter, "get", lambda ref, timeout=None: (_ for _ in ()).throw(
        RuntimeError("gone")) if ref == "ref" else ref)
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    out = ex.shell("cmd", feature_on=False, timeout_s=60)
    assert out.exit_code == -1 and "gone" in out.output


def test_host_shell_kills_the_whole_process_group_on_timeout(tmp_path):
    """subprocess.run kills only the shell. A child that keeps the pipes open
    would make the call wait for it anyway, which for a gem5 is minutes."""
    import time as _time

    t0 = _time.time()
    out = adapter.host_shell(str(tmp_path), "sleep 30 & sleep 30; echo never", {}, 1)
    assert out["timed_out"] and out["exit_code"] == -1
    assert _time.time() - t0 < 20


def test_host_shell_survives_output_that_is_not_utf8(tmp_path):
    out = adapter.host_shell(str(tmp_path), "printf 'a\\377b'", {}, 30)
    assert out["exit_code"] == 0 and out["output"].startswith("a")


def test_the_shell_python_has_no_path_into_the_tree(fake_scons, fake_shell):
    """The two settings go last, so a test plan entry's own env cannot put
    the tree back on the measuring process's path."""
    ex = adapter.Gem5Executor("/w/port", {"name": "sr_enable", "binding": "runtime_env"})
    ex.build(feature_on=False)
    ex.shell("cmd", feature_on=False, timeout_s=60,
             env={"PYTHONPATH": ".", "PYTHONNOUSERSITE": ""})
    env = fake_shell.calls[0]["args"][2]
    assert env["PYTHONPATH"] == "" and env["PYTHONNOUSERSITE"] == "1"


PROBE = """import json, os, sys
print("JSON_FROM", json.__file__)
print("NO_USER_SITE", sys.flags.no_user_site)
here = os.path.realpath(os.getcwd())
print("TREE_ON_PATH", any(p and os.path.realpath(p) == here for p in sys.path))
"""


def test_a_module_left_in_the_tree_never_runs_in_the_measuring_python(
        tmp_path, monkeypatch, identity_get):
    """The G2 command runs with the tree as its cwd, and the Ray worker's
    PYTHONPATH is ".:loop". So a sitecustomize.py or a json.py that an agent
    left in the tree ran inside run_workload.py. This goes through the real
    host_shell, whose env is laid over os.environ, to show that the
    executor's PYTHONPATH replaces the worker's."""
    tree = tmp_path / "gem5_port"
    tree.mkdir()
    (tree / "sitecustomize.py").write_text("print('PLANTED sitecustomize')\n")
    (tree / "json.py").write_text("raise SystemExit('PLANTED json')\n")
    scripts = tmp_path / "p2p_gem5"
    scripts.mkdir()
    (scripts / "probe.py").write_text(PROBE)
    command = f"python3 {scripts / 'probe.py'}"
    monkeypatch.setenv("PYTHONPATH", ".:loop")
    real_shell = adapter.host_shell

    # The control: without the executor's env, the plant does run.
    bare = real_shell(str(tree), command, {}, 60)
    assert "PLANTED" in bare["output"]

    monkeypatch.setattr(adapter, "host_shell", Remote(lambda *a: real_shell(*a)))
    ex = adapter.Gem5Executor(str(tree), {"name": "sr_enable", "binding": "runtime_env"})
    ex._binaries[False] = adapter.binary_path(str(tree))
    ex._tree_state = False
    out = ex.shell(command, feature_on=False, timeout_s=60)
    assert out.exit_code == 0, out.output
    assert "PLANTED" not in out.output
    assert "TREE_ON_PATH False" in out.output
    assert "NO_USER_SITE 1" in out.output
    json_from = re.search(r"^JSON_FROM (.*)$", out.output, re.M).group(1)
    assert not json_from.startswith(str(tree))


# ------------------------------------------------------------ the manifest


@pytest.fixture
def manifest(tmp_path, monkeypatch):
    doc = {"schema": 1, "root": "workloads", "workloads": {
        "bfs": {"binary": "bin/bfs", "args": ["-g", "16", "-n", "1"], "cwd": None,
                "max_insts": None, "approx_insts": None, "suite": "gapbs",
                "description": "d", "license": "BSD", "source": "https://x"},
        "lua": {"binary": "bin/lua", "args": ["bench.lua", "a b"], "cwd": "data/lua",
                "max_insts": 5000000, "approx_insts": None, "suite": "lua",
                "description": "d", "license": "MIT", "source": "https://y"},
    }}
    path = tmp_path / "workloads.json"
    path.write_text(json.dumps(doc))
    monkeypatch.setattr(C, "GEM5_WORKLOADS_MANIFEST", path)
    return path


def test_resolve_builds_worker_paths_from_the_manifest(manifest):
    spec = adapter.resolve("lua")
    base = f"{C.GEM5_RUN_DIR}/workloads"
    assert spec["binary"] == f"{base}/bin/lua"
    assert spec["cwd"] == f"{base}/data/lua"
    assert spec["max_insts"] == 5000000
    assert spec["config_args"] == [
        "--cmd", f"{base}/bin/lua", "--options", "bench.lua 'a b'",
        "--cwd", f"{base}/data/lua", "--maxinsts", "5000000",
    ]
    bfs = adapter.resolve("bfs")
    assert bfs["cwd"] is None
    assert "--cwd" not in bfs["config_args"] and "--maxinsts" not in bfs["config_args"]


def test_resolve_lists_the_known_names_for_an_unknown_one(manifest):
    with pytest.raises(adapter.UnknownWorkloadError) as caught:
        adapter.resolve("sqlite")
    assert "bfs" in str(caught.value) and "lua" in str(caught.value)


def test_resolve_refuses_a_path_that_leaves_the_payload(tmp_path, monkeypatch):
    path = tmp_path / "workloads.json"
    path.write_text(json.dumps({"workloads": {"x": {"binary": "../../etc/passwd"}}}))
    monkeypatch.setattr(C, "GEM5_WORKLOADS_MANIFEST", path)
    with pytest.raises(ValueError):
        adapter.resolve("x")


# ---------------------------------------------------------------- metrics


def test_parse_metrics_requires_an_ok_status():
    """plan_runner's metrics_equal_baseline ignores the exit code. Metrics
    printed by a run that then failed must not be compared as if it ran."""
    lines = "P2P_WORKLOAD bfs\nP2P_METRIC cond_mpki 2.0\nP2P_METRIC ipc 1.5\n"
    assert adapter.parse_metrics(lines + "P2P_STATUS ok\n") == {"cond_mpki": 2.0, "ipc": 1.5}
    assert adapter.parse_metrics(lines + "P2P_STATUS failed guest exited 1\n") == {}
    assert adapter.parse_metrics(lines) == {}
    assert adapter.parse_metrics("Segmentation fault") == {}
    assert adapter.parse_metrics("") == {}
    assert adapter.parse_metrics(None) == {}


# ------------------------------------------------------------- the fan-out


@pytest.fixture
def fan_out(monkeypatch, manifest):
    """Gem5Node.run_gem5 and get(), recording the order of dispatches and
    waits, and answering each workload with `results[name]`."""
    events, calls, results, waits = [], [], {}, []

    class Ref:
        def __init__(self, name):
            self.name = name

    def fake_options(**opts):
        def chia_remote(binary, script, outdir, **kw):
            events.append(("dispatch", kw["workload_name"]))
            calls.append({"binary": binary, "script": script, "outdir": outdir,
                          "options": opts, **kw})
            return Ref(kw["workload_name"])
        return types.SimpleNamespace(chia_remote=chia_remote)

    def fake_get(ref, timeout=None):
        assert timeout is not None, "a get() with no timeout can wait for ever"
        waits.append(timeout)
        if isinstance(ref, Ref):
            events.append(("get", ref.name))
            answer = results.get(ref.name, FakeRunResult(ref.name))
            if isinstance(answer, BaseException):
                raise answer
            return answer
        return ref

    monkeypatch.setattr(adapter.Gem5Node.run_gem5, "options", fake_options)
    monkeypatch.setattr(adapter, "get", fake_get)
    shell = Remote(lambda cwd, cmd, env, t: {
        "exit_code": 0, "timed_out": False,
        "output": "".join(f"{adapter._OUTDIR_MARK}{d}\npanic: predictor exploded\n"
                          for d in re.findall(r"'@@P2P_OUTDIR@@ ([^']+)'", cmd))})
    monkeypatch.setattr(adapter, "host_shell", shell)
    return types.SimpleNamespace(events=events, calls=calls, results=results, shell=shell,
                                 waits=waits)


def _executor_with_binary(feature_enable=None):
    ex = adapter.Gem5Executor("/w/port", feature_enable or
                              {"name": "sr_enable", "binding": "runtime_env"})
    ex._binaries[False] = adapter.binary_path("/w/port")
    ex._tree_state = False
    return ex


def test_run_traces_dispatches_every_run_before_waiting_on_any(fan_out):
    out = _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert out.ok
    assert fan_out.events == [("dispatch", "bfs"), ("dispatch", "lua"),
                              ("get", "bfs"), ("get", "lua")]


def test_run_traces_passes_the_manifest_config_and_stats_keys(fan_out):
    _executor_with_binary().run_traces(["lua"], feature_on=True, timeout_s=77)
    call = fan_out.calls[0]
    assert call["options"] == {"resources": {C.GEM5_HOST_RESOURCE: 1.0}}
    assert call["binary"] == adapter.binary_path("/w/port")
    assert call["script"] == f"{C.GEM5_RUN_DIR}/se_o3.py"
    assert call["config_args"] == adapter.resolve("lua")["config_args"]
    assert call["stats_keys"] is p2p_metrics.STATS_KEYS
    assert call["env"] == {"sr_enable": "1", "SR_ENABLE": "1"}
    assert call["gem5_args"] == ["--redirect-stderr"]
    assert call["cwd"] == call["outdir"]


def test_run_traces_asks_for_the_whole_stats_file(fan_out):
    """The metrics are parsed from the captured stats.txt. Without
    capture_stats=True, run_gem5 returns no stats_content, and every run
    fails for lack of stats."""
    _executor_with_binary().run_traces(["lua"], feature_on=True, timeout_s=60)
    assert fan_out.calls[0]["capture_stats"] is True


def test_the_run_timeout_is_never_below_the_hosts_own(fan_out):
    """plan_runner passes its generic 900 s, or a plan's own timeout_seconds.
    A perf workload took up to 396 s alone on an idle node, and a second job
    on the node doubles that. A run killed early reads as a G4 or G5 failure
    of the port. A limit above the host's own still passes through."""
    ex = _executor_with_binary()
    ex.run_traces(["lua"], feature_on=True, timeout_s=77)
    ex.run_traces(["lua"], feature_on=True, timeout_s=900)
    ex.run_traces(["lua"], feature_on=True, timeout_s=C.GEM5_RUN_TIMEOUT_S + 600)
    assert [c["timeout_s"] for c in fan_out.calls] == [
        C.GEM5_RUN_TIMEOUT_S, C.GEM5_RUN_TIMEOUT_S, C.GEM5_RUN_TIMEOUT_S + 600]


def test_every_run_gets_its_own_outdir_even_across_states(fan_out):
    """The two states of one workload run at the same time on one node. A
    shared outdir would let each read the other's stats.txt."""
    ex = _executor_with_binary()
    ex.run_traces(["bfs", "bfs"], feature_on=True, timeout_s=60)
    ex.run_traces(["bfs"], feature_on=False, timeout_s=60)
    outdirs = [c["outdir"] for c in fan_out.calls]
    assert len(set(outdirs)) == 3
    assert all(d.startswith(f"{C.GEM5_RUN_DIR}/runs/") for d in outdirs)
    assert "-on-" in outdirs[0] and "-off-" in outdirs[2]


@pytest.mark.parametrize("result, why", [
    (FakeRunResult(status="run_failed_1", returncode=1, error="gem5 rc=1"), "run_failed_1"),
    (FakeRunResult(status="timeout", returncode=-1, error="timed out"), "timeout"),
    (FakeRunResult(status="ok", returncode=3), "exited 3"),
    (FakeRunResult(stdout="no exit line here\n"), "P2P_EXIT"),
    (FakeRunResult(stdout="P2P_EXIT cause=exiting with last active thread context code=1\n"),
     "code 1"),
    (FakeRunResult(stats_content=stats_text(direct=None, indirect=None)), "cond_mpki"),
    (FakeRunResult(stats_content=None), "stats.txt did not come back"),
    (None, "returned nothing"),
    (RuntimeError("RayTaskError: worker crashed"), "worker crashed"),
])
def test_a_run_fails_for_each_way_a_gem5_run_can_go_wrong(fan_out, result, why):
    """A run counts only if gem5 said ok and exited 0, se_o3.py reported the
    guest exiting 0, and every metric was derived. A guest that failed while
    gem5 exited 0 would otherwise pass G4."""
    fan_out.results["lua"] = result
    out = _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert out.ok is False
    assert out.failed == ["lua"]
    assert why in out.log_tail
    assert out.metrics == GOOD_METRICS  # the survivor is still scored


def test_an_ok_run_without_its_stats_file_fails_with_a_reason(fan_out):
    """chia said ok, gem5 and the guest exited 0, and chia's own parse has
    the cycles and instructions. None of that is a measurement of the
    predictor. With no stats.txt text there is nothing to derive the metrics
    from, and falling back to chia's parse would bring back the cond_mpki
    that counted every branch type."""
    fan_out.results["lua"] = FakeRunResult("lua", stats_content=None)
    out = _executor_with_binary().run_traces(["lua"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["lua"] and out.metrics == {}
    assert "lua: gem5 exited 0 but its stats.txt did not come back" in out.log_tail


def test_cond_mpki_counts_conditional_branches_only_on_a_real_stats_file(fan_out):
    """The first cluster run printed cond_mpki equal to branch_mpki on all 28
    workloads, because condIncorrect counts every mispredicted branch type.
    On a real stats.txt the two must now differ: cond_mpki comes from the
    DirectCond and IndirectCond rows, and branch_mpki from their total."""
    fan_out.results["bfs"] = FakeRunResult("bfs", stats_content=REAL_STATS.read_text())
    out = _executor_with_binary().run_traces(["bfs"], feature_on=False, timeout_s=60)
    assert out.ok, out.log_tail
    assert out.metrics["cond_mpki"] == \
        1000.0 * (REAL_DIRECT_COND + REAL_INDIRECT_COND) / REAL_INSTS
    assert out.metrics["branch_mpki"] == 1000.0 * REAL_ALL_MISPREDICTS / REAL_INSTS
    assert out.metrics["ipc"] == REAL_INSTS / REAL_CYCLES
    assert out.metrics["cond_mpki"] < out.metrics["branch_mpki"]


def test_a_non_zero_exit_names_the_guest_code(fan_out):
    fan_out.results["lua"] = FakeRunResult(
        status="run_failed_1", returncode=1, error="gem5 rc=1",
        stdout="P2P_EXIT cause=exiting with last active thread context code=1\n")
    out = _executor_with_binary().run_traces(["lua"], feature_on=True, timeout_s=60)
    assert "guest code 1" in out.log_tail


def test_a_run_that_cannot_be_dispatched_fails_by_name(fan_out, monkeypatch):
    def refuse(**opts):
        def chia_remote(*a, **k):
            raise TypeError("cannot pickle the argument")
        return types.SimpleNamespace(chia_remote=chia_remote)

    monkeypatch.setattr(adapter.Gem5Node.run_gem5, "options", refuse)
    out = _executor_with_binary().run_traces(["bfs"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["bfs"]
    assert "could not dispatch" in out.log_tail


def test_a_failed_run_brings_its_stderr_back(fan_out):
    """gem5's fatal and panic lines go to stderr, which run_gem5 drops. The
    adapter redirects it to simerr.txt and reads it back for failures."""
    fan_out.results["lua"] = FakeRunResult(status="run_failed_134", returncode=134)
    out = _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert "panic: predictor exploded" in out.log_tail
    assert len(fan_out.shell.calls) == 1
    command = fan_out.shell.calls[0]["args"][1]
    assert "simerr.txt" in command
    # se_o3.py sends the guest's own stderr here. A workload's self-check
    # prints why it failed there, not to gem5's stderr.
    assert "guest_stderr.txt" in command


def test_a_clean_fan_out_reads_nothing_back(fan_out):
    _executor_with_binary().run_traces(["bfs"], feature_on=False, timeout_s=60)
    assert fan_out.shell.calls == []


def test_an_unknown_workload_fails_by_name_without_crashing(fan_out):
    out = _executor_with_binary().run_traces(["bfs", "nope"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["nope"]
    assert "unknown gem5 workload" in out.log_tail
    assert [c["workload_name"] for c in fan_out.calls] == ["bfs"]


def test_run_traces_without_a_binary_fails_every_workload(monkeypatch, identity_get):
    """A build that produced nothing must not score zero workloads as a clean
    run, and the reason has to be the compiler's."""
    monkeypatch.setattr(adapter, "scons_build",
                        Remote(lambda *a: {"ok": False, "log": "error: no member named sr"}))
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    out = ex.run_traces(["a", "b"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["a", "b"] and out.metrics == {}
    assert "no member named sr" in out.log_tail


def test_run_traces_of_nothing_is_not_a_pass():
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    assert ex.run_traces([], feature_on=True, timeout_s=60).ok is False


def test_a_compile_time_knob_runs_each_state_on_its_own_binary(fake_scons, fan_out):
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "compile_time_define"})
    ex.build(feature_on=False)
    ex.run_traces(["bfs"], feature_on=True, timeout_s=60)
    ex.run_traces(["bfs"], feature_on=False, timeout_s=60)
    assert fan_out.calls[0]["binary"] == adapter.state_binary_path("/w/port", True)
    assert fan_out.calls[1]["binary"] == adapter.state_binary_path("/w/port", False)


# ------------------------------------------------- a node that never answers


def test_every_run_waits_its_own_limit_plus_a_margin(fan_out):
    """A get() with no timeout waits for ever on a node that vanished: Ray
    keeps its tasks waiting for a resource nobody advertises any more."""
    _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert fan_out.waits == [C.GEM5_RUN_TIMEOUT_S + adapter._GET_MARGIN_S] * 2


def test_a_build_and_a_command_wait_their_own_limit_plus_a_margin(
        identity_get, fake_scons, fake_shell):
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    ex.build(feature_on=False)
    ex.shell("cmd", feature_on=True, timeout_s=77)
    assert identity_get == [C.GEM5_BUILD_TIMEOUT_S + adapter._GET_MARGIN_S,
                            77 + adapter._GET_MARGIN_S]


def test_a_run_whose_node_never_answers_fails_by_name_and_cost_one_wait(
        fan_out, monkeypatch):
    """The first run that times out marks the node as stopped. The runs
    after it only get a moment to be already finished, so one lost node
    costs one limit and not one per workload, and nothing hangs."""
    from ray.exceptions import GetTimeoutError

    cancelled = []
    monkeypatch.setattr(adapter, "_cancel_quietly", lambda ref: cancelled.append(ref.name))
    fan_out.results["bfs"] = GetTimeoutError("bfs")
    fan_out.results["lua"] = GetTimeoutError("lua")
    out = _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["bfs", "lua"] and out.metrics == {}
    assert fan_out.waits == [C.GEM5_RUN_TIMEOUT_S + adapter._GET_MARGIN_S,
                             adapter._AFTER_STALL_WAIT_S]
    assert "== bfs: " in out.log_tail and "== lua: " in out.log_tail
    assert out.log_tail.count("lost or stuck") == 2
    assert C.GEM5_HOST_RESOURCE in out.log_tail
    assert cancelled == ["bfs", "lua"]
    # No read-back of simerr.txt from a node that stopped answering.
    assert fan_out.shell.calls == []


def test_a_run_that_finished_before_the_stall_was_noticed_still_counts(
        fan_out, monkeypatch):
    from ray.exceptions import GetTimeoutError

    monkeypatch.setattr(adapter, "_cancel_quietly", lambda ref: None)
    fan_out.results["bfs"] = GetTimeoutError("bfs")
    out = _executor_with_binary().run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    assert out.failed == ["bfs"] and out.metrics == GOOD_METRICS


def test_a_build_or_command_whose_node_never_answers_fails_with_the_reason(monkeypatch):
    from ray.exceptions import GetTimeoutError

    def never(ref, timeout=None):
        assert timeout is not None
        raise GetTimeoutError("timed out")

    monkeypatch.setattr(adapter, "scons_build", Remote(lambda *a: "ref"))
    monkeypatch.setattr(adapter, "host_shell", Remote(lambda *a: "ref"))
    monkeypatch.setattr(adapter, "_cancel_quietly", lambda ref: None)
    monkeypatch.setattr(adapter, "get", never)
    ex = adapter.Gem5Executor("/w/port", {"name": "k", "binding": "runtime_env"})
    built = ex.build(feature_on=False)
    assert not built.ok and "lost or stuck" in built.log
    ex._binaries[False] = adapter.binary_path("/w/port")
    ex._tree_state = False
    ran = ex.shell("cmd", feature_on=False, timeout_s=60)
    # timed_out stays False: plan_runner would replace the reason with a
    # bare "the command timed out", which hides the node.
    assert ran.exit_code == -1 and not ran.timed_out and "lost or stuck" in ran.output
    assert "lost or stuck" in adapter.build_tree("/w/gem5")["log"]


def test_a_helper_the_driver_calls_stops_the_stage_when_the_node_never_answers(
        monkeypatch):
    """Outside a gate there is nothing to fail but the stage. The patch is
    the exception: the driver writes it after the gate loop whatever the
    verdict, so a missing one becomes a note."""
    from ray.exceptions import GetTimeoutError

    def never(ref, timeout=None):
        raise GetTimeoutError("timed out")

    for name in ("install_run_dir", "restore_checkout", "materialize_port_tree",
                 "host_revision", "host_shell"):
        monkeypatch.setattr(adapter, name, Remote(lambda *a, **k: "ref"))
    monkeypatch.setattr(adapter, "build_run_payload", lambda: b"payload")
    monkeypatch.setattr(adapter, "_cancel_quietly", lambda ref: None)
    monkeypatch.setattr(adapter, "get", never)
    for call in (adapter.install_run_dir_on_cluster, adapter.checkout_revision,
                 adapter.restore_host_checkout, adapter.clean_port_tree):
        with pytest.raises(SystemExit) as caught:
            call()
        assert "lost or stuck" in str(caught.value), call.__name__
    assert adapter.port_diff().startswith("[could not read the port diff")


# ------------------------------------- chia's real run_gem5, called in-process

FAKE_GEM5 = r'''#!/usr/bin/env python3
"""Stands in for gem5.opt: writes a stats.txt, prints P2P_EXIT, exits with
the guest's code. Its numbers depend on the knob, so a test can see whether
the knob reached the gem5 process."""
import os, sys
args = sys.argv[1:]
outdir = next(a.split("=", 1)[1] for a in args if a.startswith("--outdir="))
code = int(os.environ.get("FAKE_GUEST_CODE", "0"))
with open(os.path.join(outdir, "host_cwd.txt"), "w") as f:
    f.write(os.getcwd())
with open(os.path.join(outdir, "stats.txt"), "w") as f:
    f.write(STATS_ON if os.environ.get("SR_ENABLE") == "1" else STATS_OFF)
if code:
    # Where se_o3.py sends the guest's stderr (process.errout).
    with open(os.path.join(outdir, "guest_stderr.txt"), "w") as f:
        f.write("bfs: self-check failed\n")
if "--redirect-stderr" in args:
    sys.stderr = open(os.path.join(outdir, "simerr.txt"), "w")
print("panic: fake gem5 says the guest failed" if code else "warn: fake", file=sys.stderr)
print(f"P2P_EXIT cause=exiting with last active thread context code={code}")
sys.exit(code)
'''.replace(
    # Two dumps each, the first a decoy with every count seven times over.
    "STATS_ON", repr(stats_text(direct=1000, scales=(7, 1))), 1,
).replace("STATS_OFF", repr(stats_text(scales=(7, 1))), 1)


@pytest.fixture
def local_gem5(tmp_path, monkeypatch, manifest):
    """run_traces with chia's real Gem5Node.run_gem5 and the real host_shell,
    both called in-process instead of through Ray, and a stand-in gem5."""
    run_dir = tmp_path / "p2p_gem5"
    (run_dir / "runs").mkdir(parents=True)
    monkeypatch.setattr(C, "GEM5_RUN_DIR", str(run_dir))
    fake_bin = tmp_path / "gem5.opt"
    fake_bin.write_text(FAKE_GEM5)
    fake_bin.chmod(0o755)

    real_run = adapter.Gem5Node.run_gem5
    real_shell = adapter.host_shell
    monkeypatch.setattr(real_run, "options", lambda **opts: types.SimpleNamespace(
        chia_remote=lambda *a, **k: real_run(*a, **k)))
    monkeypatch.setattr(adapter, "host_shell", Remote(lambda *a: real_shell(*a)))
    monkeypatch.setattr(adapter, "get", lambda ref, timeout=None: ref)

    ex = adapter.Gem5Executor("/w/port", {"name": "sr_enable", "binding": "runtime_env"})
    ex._binaries[False] = str(fake_bin)
    ex._tree_state = False
    return types.SimpleNamespace(ex=ex, run_dir=run_dir)


def test_real_run_gem5_results_are_judged_and_the_knob_reaches_gem5(local_gem5):
    on = local_gem5.ex.run_traces(["bfs", "lua"], feature_on=True, timeout_s=60)
    off = local_gem5.ex.run_traces(["bfs", "lua"], feature_on=False, timeout_s=60)
    assert on.ok and off.ok, (on.log_tail, off.log_tail)
    assert off.metrics == GOOD_METRICS  # the last dump, not the first
    assert on.metrics["cond_mpki"] == 1.0  # the knob reached the gem5 process
    outdirs = sorted((local_gem5.run_dir / "runs").iterdir())
    assert len(outdirs) == 4
    assert all((d / "host_cwd.txt").read_text() == str(d) for d in outdirs)


def test_real_run_gem5_failure_carries_the_guest_code_and_stderr(local_gem5, monkeypatch):
    monkeypatch.setenv("FAKE_GUEST_CODE", "3")
    out = local_gem5.ex.run_traces(["bfs"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["bfs"]
    assert "run_failed_3" in out.log_tail and "guest code 3" in out.log_tail
    assert "panic: fake gem5 says the guest failed" in out.log_tail
    assert "bfs: self-check failed" in out.log_tail


# -------------------------------------------------------------- the payload


@pytest.fixture
def payload_tree(tmp_path, manifest):
    scripts = tmp_path / "run"
    scripts.mkdir()
    for name in ("se_o3.py", "run_workload.py", "p2p_metrics.py", "__init__.py"):
        (scripts / name).write_text(f"# {name}\n")
    wdir = tmp_path / "gem5_workloads"
    (wdir / "bin").mkdir(parents=True)
    (wdir / "data" / "lua").mkdir(parents=True)
    for exe in ("bfs", "lua"):
        (wdir / "bin" / exe).write_bytes(b"\x7fELF" + exe.encode())
        (wdir / "bin" / exe).chmod(0o755)
    (wdir / "data" / "lua" / "bench.lua").write_text("print(1)\n")
    return types.SimpleNamespace(scripts=scripts, workloads=wdir, manifest=manifest)


def _payload(tree):
    return adapter.build_run_payload(tree.scripts, tree.manifest, tree.workloads)


def test_the_payload_is_deterministic_and_complete(payload_tree):
    """The same files make the same bytes, so an unchanged payload is a
    no-op on the node. mtimes and gzip's own timestamp would otherwise make
    every build of it different."""
    first = _payload(payload_tree)
    os.utime(payload_tree.workloads / "bin" / "bfs", (1, 1))
    assert _payload(payload_tree) == first
    with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as tar:
        names = tar.getnames()
        mode = tar.getmember("workloads/bin/bfs").mode
    for expected in ("se_o3.py", "run_workload.py", "p2p_metrics.py", "workloads.json",
                     "workloads/bin/bfs", "workloads/bin/lua",
                     "workloads/data/lua/bench.lua", "workloads/data/lua"):
        assert expected in names
    assert mode & 0o111


def test_a_missing_workload_build_names_the_script(payload_tree, tmp_path):
    with pytest.raises(SystemExit) as caught:
        adapter.build_run_payload(payload_tree.scripts, payload_tree.manifest,
                                  tmp_path / "not_built")
    assert "scripts/build_gem5_workloads.sh" in str(caught.value)


def test_a_manifest_binary_missing_from_the_payload_is_named(payload_tree):
    (payload_tree.workloads / "bin" / "lua").unlink()
    with pytest.raises(SystemExit) as caught:
        _payload(payload_tree)
    assert "lua" in str(caught.value) and "build_gem5_workloads.sh" in str(caught.value)


def test_install_is_idempotent_and_keeps_runs(payload_tree, tmp_path):
    dest = tmp_path / "p2p_gem5"
    payload = _payload(payload_tree)

    first = adapter.install_run_dir(payload, str(dest))
    assert first["ok"] and first["installed"]
    assert (dest / "se_o3.py").exists() and (dest / "workloads" / "bin" / "lua").exists()
    assert os.access(dest / "workloads" / "bin" / "lua", os.X_OK)
    (dest / "runs" / "old-run").mkdir()

    again = adapter.install_run_dir(payload, str(dest))
    assert again["ok"] and again["installed"] is False

    (payload_tree.workloads / "bin" / "lua").write_bytes(b"\x7fELF new lua")
    changed = adapter.install_run_dir(_payload(payload_tree), str(dest))
    assert changed["installed"] and changed["replaced"] == first["sha256"]
    assert (dest / "workloads" / "bin" / "lua").read_bytes() == b"\x7fELF new lua"
    assert (dest / "runs" / "old-run").is_dir()
    assert not list(dest.glob(".staging-*")) and not list(dest.glob(".replaced-*"))


def test_install_puts_back_a_run_script_that_was_edited(payload_tree, tmp_path):
    """An agent's shell can reach the run dir. An edited se_o3.py that
    survived the next install would reach every gate run and every baseline,
    while the marker still vouched for the payload. So the same payload
    installs again when any installed file differs, and is still a no-op
    when none does."""
    dest = tmp_path / "p2p_gem5"
    payload = _payload(payload_tree)
    assert adapter.install_run_dir(payload, str(dest))["installed"] is True
    original = (dest / "se_o3.py").read_bytes()
    assert adapter.install_run_dir(payload, str(dest))["installed"] is False

    (dest / "se_o3.py").write_text("# an L2 the agent liked better\n")
    out = adapter.install_run_dir(payload, str(dest))
    assert out["ok"] and out["installed"] is True
    assert (dest / "se_o3.py").read_bytes() == original
    assert adapter.install_run_dir(payload, str(dest))["installed"] is False

    (dest / "workloads" / "data" / "lua" / "bench.lua").unlink()
    assert adapter.install_run_dir(payload, str(dest))["installed"] is True
    assert (dest / "workloads" / "data" / "lua" / "bench.lua").read_text() == "print(1)\n"


def test_install_removes_a_file_an_agent_added(payload_tree, tmp_path):
    """An added file needs no edit to change a run. A p2p_metrics package
    next to p2p_metrics.py is imported in its place by run_workload.py, and
    a sitecustomize.py runs in every Python started there. The digests of
    the recorded files alone cannot see either."""
    dest = tmp_path / "p2p_gem5"
    payload = _payload(payload_tree)
    assert adapter.install_run_dir(payload, str(dest))["installed"] is True
    (dest / "runs" / "old-run").mkdir()
    (dest / "p2p_metrics").mkdir()
    (dest / "p2p_metrics" / "__init__.py").write_text("def derive(s): return {}\n")
    (dest / "sitecustomize.py").write_text("print('planted')\n")
    (dest / "workloads" / "bin" / "extra").write_bytes(b"\x7fELF extra")
    (dest / "workloads" / "data" / "elsewhere").symlink_to(tmp_path)

    out = adapter.install_run_dir(payload, str(dest))
    assert out["ok"] and out["installed"] is True
    assert out["drift"]["added"] == ["p2p_metrics/__init__.py", "sitecustomize.py",
                                     "workloads/bin/extra", "workloads/data/elsewhere"]
    assert out["drift"]["changed"] == [] and out["drift"]["missing"] == []
    assert "drifted" in out["why"] and "sitecustomize.py" in out["why"]
    for gone in ("p2p_metrics", "sitecustomize.py", "workloads/bin/extra",
                 "workloads/data/elsewhere"):
        assert not os.path.lexists(dest / gone), gone
    assert (dest / "runs" / "old-run").is_dir()
    assert adapter.install_run_dir(payload, str(dest))["installed"] is False


def test_python_caches_are_cleared_but_force_no_reinstall(payload_tree, tmp_path):
    """run_workload.py imports p2p_metrics from its own directory, so every
    run leaves a __pycache__ in the run dir. Counted as an added file, it
    would make every gate attempt a reinstall and a warning. It is cleared
    instead, because a planted .pyc could hide there. Caches under runs/
    and another install's staging dir are not the install's business."""
    dest = tmp_path / "p2p_gem5"
    payload = _payload(payload_tree)
    adapter.install_run_dir(payload, str(dest))
    for cache in ("__pycache__", "workloads/data/lua/__pycache__", "runs/r1/__pycache__"):
        (dest / cache).mkdir(parents=True)
        (dest / cache / "p2p_metrics.cpython-310.pyc").write_bytes(b"pyc")
    other = dest / ".staging-0123456789ab-99"
    other.mkdir()
    (other / "se_o3.py").write_text("# another install, in progress\n")

    out = adapter.install_run_dir(payload, str(dest))
    assert out["ok"] and out["installed"] is False
    assert sorted(out["purged"]) == ["__pycache__", "workloads/data/lua/__pycache__"]
    assert not (dest / "__pycache__").exists()
    assert not (dest / "workloads" / "data" / "lua" / "__pycache__").exists()
    assert (dest / "runs" / "r1" / "__pycache__").is_dir()
    assert (other / "se_o3.py").is_file()


def test_a_reinstall_says_why(payload_tree, tmp_path):
    dest = tmp_path / "p2p_gem5"
    first = adapter.install_run_dir(_payload(payload_tree), str(dest))
    assert first["installed"] and "no marker" in first["why"]
    (payload_tree.scripts / "se_o3.py").write_text("# a new L2\n")
    changed = adapter.install_run_dir(_payload(payload_tree), str(dest))
    assert changed["installed"] and "payload changed" in changed["why"]
    assert changed["drift"] is None


def test_install_keeps_one_spelling_of_every_path(payload_tree, tmp_path):
    """The guest sees its binary's path. A symlinked, versioned install would
    give that path a second spelling that changes with every payload."""
    dest = tmp_path / "p2p_gem5"
    adapter.install_run_dir(_payload(payload_tree), str(dest))
    assert not dest.is_symlink()
    assert os.path.realpath(dest / "workloads" / "bin" / "bfs") == \
        str(dest / "workloads" / "bin" / "bfs")


def test_a_half_finished_install_is_redone(payload_tree, tmp_path):
    dest = tmp_path / "p2p_gem5"
    payload = _payload(payload_tree)
    adapter.install_run_dir(payload, str(dest))
    (dest / adapter._PAYLOAD_MARKER).unlink()
    out = adapter.install_run_dir(payload, str(dest))
    assert out["installed"] is True


def test_install_refuses_a_member_that_escapes(tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    out = adapter.install_run_dir(buf.getvalue(), str(tmp_path / "p2p_gem5"))
    assert out["ok"] is False and "escapes" in out["error"]
    assert not (tmp_path / "escape.txt").exists()


# --------------------------------------------------------------- port diff


def test_port_diff_leaves_out_build_output_and_the_index_clean(tmp_path):
    """The diff is how a run is reviewed. Build output, gem5 outdirs and
    Python caches in it bury the port, and a staged index left behind would
    be inherited by a resumed run."""
    root = _git_repo(tmp_path / "port")
    _add_build(root, b"ported")
    (root / "src" / "cpu" / "pred" / "tage_sc_l.cc").write_text("// ported\n")
    (root / "src" / "cpu" / "pred" / "sr.hh").write_text("// new file\n")
    (root / "m5out").mkdir()
    (root / "m5out" / "stats.txt").write_text("x")
    (root / "src" / "__pycache__").mkdir()
    (root / "src" / "__pycache__" / "a.cpython-310.pyc").write_bytes(b"x")
    # Even with gem5's .gitignore emptied, the excludes hold.
    (root / ".gitignore").write_text("")

    out = subprocess.run(adapter.port_diff_command(), shell=True, cwd=root,
                         capture_output=True, text=True).stdout

    assert "sr.hh" in out and "// ported" in out
    diffed = re.findall(r"^diff --git a/(\S+)", out, re.M)
    assert "src/cpu/pred/sr.hh" in diffed and ".gitignore" in diffed
    for path in diffed:
        assert not path.startswith(("build/", "m5out/")), path
        assert "__pycache__" not in path and not path.endswith(".pyc"), path
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                            capture_output=True, text=True).stdout
    assert not any(line[0] in "AM" for line in status.splitlines() if line.strip())


# ------------------------------------------------------------------ the gate

GATE_PLAN = {
    "metric_keys": list(p2p_metrics.METRIC_KEYS),
    "correctness": [{
        "id": "feature_off_baseline", "kind": "feature_off_baseline",
        "command": "python3 run_workload.py bfs", "feature_state": "off",
        "pass_condition": {"kind": "metrics_equal_baseline",
                           "baseline_pointer": "/per_trace/bfs", "rel_tol": 0},
    }],
    "performance": [{"id": "p", "metric": "cond_mpki", "direction": "decrease",
                     "trace_list": "x.list", "baseline": {"source": "measure_feature_off"}}],
}


@pytest.fixture
def gate_env(monkeypatch):
    """run_gate with every dispatch faked, recording the order of the steps."""
    import gate

    state = types.SimpleNamespace(order=[], installs=[], revision="rev-1",
                                  prints={"bfs": "fp-bfs", "lua": "fp-lua"})

    def install():
        state.order.append("install")
        return state.installs.pop(0) if state.installs else {
            "ok": True, "installed": False, "dest": C.GEM5_RUN_DIR}

    def revision():
        state.order.append("revision")
        return state.revision

    def run_test_plan(executor, test_plan, port_plan, baseline):
        state.order.append(("run", executor.work_dir))
        return "results"

    monkeypatch.setattr(adapter, "install_run_dir_on_cluster", install)
    monkeypatch.setattr(adapter, "checkout_revision", revision)
    monkeypatch.setattr(adapter, "workload_fingerprint", lambda name: state.prints.get(name))
    monkeypatch.setattr(adapter.plan_runner, "run_test_plan", run_test_plan)
    monkeypatch.setattr(adapter.gate, "check_gate",
                        lambda results: gate.GateResult(False, ["G5 [p] nothing moved"]))
    state.baseline = {"host_revision": "rev-1",
                      "per_trace": {"bfs": GOOD_METRICS, "lua": GOOD_METRICS},
                      "workload_fingerprints": {"bfs": "fp-bfs", "lua": "fp-lua"}}
    return state


def test_every_gate_attempt_installs_the_run_dir_before_it_measures(gate_env):
    """The agent's shell reaches ~/p2p_gem5. Installing only when a stage
    starts let an edit there reach every later attempt of that stage. An
    install that was not a no-op is a warning, so the lead sees it."""
    port_plan = {"feature_enable": {"name": "sr_enable", "binding": "runtime_env"}}
    gate_env.installs = [
        {"ok": True, "installed": False, "dest": "/n/p2p_gem5"},
        {"ok": True, "installed": True, "dest": "/n/p2p_gem5",
         "why": "the installed files drifted from the payload: changed se_o3.py"},
    ]
    first = adapter.run_gate(gate_env.baseline, port_plan, GATE_PLAN)
    second = adapter.run_gate(gate_env.baseline, port_plan, GATE_PLAN)
    assert gate_env.order == ["install", "revision", ("run", C.GEM5_PORT_ROOT)] * 2
    assert first.warnings == []
    assert len(second.warnings) == 1
    assert "installed again" in second.warnings[0] and "se_o3.py" in second.warnings[0]
    assert second.reasons == ["G5 [p] nothing moved"]  # the warning is not a reason


def test_gate_attempt_runs_on_the_tree_it_is_given(gate_env):
    attempt = adapter.gate_attempt(gate_env.baseline, {}, GATE_PLAN, work_dir="/n/gem5_smoke")
    assert ("run", "/n/gem5_smoke") in gate_env.order
    assert attempt.results == "results" and attempt.install["installed"] is False


@pytest.mark.parametrize("change, expected", [
    (lambda env: setattr(env, "revision", "rev-2"), "recorded at revision rev-1"),
    (lambda env: env.prints.update(bfs="fp-bfs-retuned"), "bfs changed after it was recorded"),
    (lambda env: env.baseline["workload_fingerprints"].pop("bfs"),
     "holds no recording of bfs"),
])
def test_a_stale_baseline_stops_the_stage_before_any_gate_runs(gate_env, change, expected):
    """A stale baseline is a setup error. As a G2 reason it would send the
    debug agent after a leak in a correct port, at 25 minutes or more per
    gem5 attempt."""
    change(gate_env)
    with pytest.raises(SystemExit) as caught:
        adapter.run_gate(gate_env.baseline, {}, GATE_PLAN)
    message = str(caught.value)
    assert expected in message
    assert "--stage baseline --host gem5 --budget <budget>" in message
    assert "--baseline-list that names bfs" in message
    assert not any(isinstance(step, tuple) for step in gate_env.order)  # nothing ran


def test_a_workload_the_plan_does_not_compare_against_may_change(gate_env):
    gate_env.prints["lua"] = "fp-lua-retuned"
    adapter.run_gate(gate_env.baseline, {}, GATE_PLAN)
    assert ("run", C.GEM5_PORT_ROOT) in gate_env.order


def test_the_workloads_a_plan_compares_against_follow_its_pointers():
    baseline = {"per_trace": {"a/b": {}, "c": {}}, "workload_fingerprints": {"a/b": 1, "c": 2}}

    def plan(g2_pointer=None, perf=None):
        doc = {"correctness": [], "performance": []}
        if g2_pointer is not None:
            doc["correctness"].append({"pass_condition": {
                "kind": "metrics_equal_baseline", "baseline_pointer": g2_pointer}})
        if perf is not None:
            doc["performance"].append({"baseline": perf})
        return doc

    assert adapter.baseline_workloads(plan("/per_trace/a~1b"), baseline) == {"a/b"}
    assert adapter.baseline_workloads(plan("/per_trace/c/cond_mpki"), baseline) == {"c"}
    # The top level is the aggregate over every workload the recording ran.
    assert adapter.baseline_workloads(plan(""), baseline) == {"a/b", "c"}
    assert adapter.baseline_workloads(
        plan(perf={"source": "recorded", "pointer": "/per_trace/c"}), baseline) == {"c"}
    assert adapter.baseline_workloads(
        plan(perf={"source": "measure_feature_off"}), baseline) == set()
    # A workload the manifest does not know is left to G2 to report.
    assert adapter.baseline_problems(
        {"host_revision": "r"}, plan("/per_trace/not_in_the_manifest_xyz"), "r") == []


# ---------------------------------------------------------------- baseline


@pytest.fixture
def baseline_env(tmp_path, monkeypatch, manifest):
    """Everything record_baseline dispatches, faked, and the baseline file
    moved out of the repository."""
    monkeypatch.setattr(helpers, "baseline_path",
                        lambda host, budget: tmp_path / "baselines" / f"{budget}.json")
    monkeypatch.setattr(adapter, "restore_host_checkout", lambda root=None: {"ok": True})
    monkeypatch.setattr(adapter, "install_run_dir_on_cluster", lambda: {"ok": True})
    monkeypatch.setattr(adapter, "build_tree", lambda root, timeout_s=None: {
        "ok": True, "binary": adapter.binary_path(root), "log": "built"})
    monkeypatch.setattr(adapter, "checkout_revision", lambda: "rev-1")
    prints = {"bfs": "fp-bfs", "lua": "fp-lua"}
    monkeypatch.setattr(adapter, "workload_fingerprint", lambda name: prints.get(name))
    state = types.SimpleNamespace(prints=prints, runs=[], results={})

    def fake_run(binary, names, *, env, timeout_s, label, **kw):
        state.runs.append({"binary": binary, "names": list(names), "env": env,
                           "label": label})
        return [adapter._judge_run(n, f"/runs/{n}", state.results.get(n, FakeRunResult(n)),
                                   True) for n in names]

    monkeypatch.setattr(adapter, "run_workloads", fake_run)
    lists = tmp_path / "lists"
    lists.mkdir()
    (lists / "both.list").write_text("# why these two\nbfs\nlua\n")
    (lists / "bfs.list").write_text("bfs\n")
    (lists / "lua.list").write_text("lua\n")
    state.lists = lists
    state.dump = helpers.Dumper(tmp_path / "out")
    return state


def test_record_baseline_writes_per_trace_and_the_build_config(baseline_env):
    agg = adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    run = baseline_env.runs[0]
    assert run["env"] == {} and run["label"] == "baseline"
    assert run["binary"] == adapter.binary_path(C.GEM5_ROOT)
    assert agg["n"] == 2 and agg["failed"] == []
    assert agg["per_trace"] == {"bfs": GOOD_METRICS, "lua": GOOD_METRICS}
    assert agg["cond_mpki"] == GOOD_METRICS["cond_mpki"]
    assert agg["host_revision"] == "rev-1"
    assert (agg["isa"], agg["variant"], agg["scons_args"]) == (
        C.GEM5_ISA, C.GEM5_VARIANT, C.GEM5_SCONS_ARGS)
    assert agg["per_trace_stats"]["bfs"]["insts"] == GOOD_INSTS
    assert agg["per_trace_stats"]["bfs"]["cond_mispredicts_direct"] == 1800.0
    assert helpers.load_baseline("gem5", "b") == agg


def test_record_baseline_carries_forward_only_matching_entries(baseline_env):
    """A later recording over another list keeps the earlier workloads, but
    only for the same tree and only while the workload is unchanged. A
    retuned workload's old numbers are a baseline for a run nobody can make
    any more."""
    adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    baseline_env.prints["lua"] = "fp-lua-retuned"
    agg = adapter.record_baseline(baseline_env.dump, baseline_env.lists / "bfs.list", "b")
    assert set(agg["per_trace"]) == {"bfs"}

    baseline_env.prints["lua"] = "fp-lua"
    adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    agg = adapter.record_baseline(baseline_env.dump, baseline_env.lists / "bfs.list", "b")
    assert set(agg["per_trace"]) == {"bfs", "lua"}
    assert agg["trace_list"].endswith("bfs.list")


def test_record_baseline_does_not_carry_across_revisions(baseline_env, monkeypatch):
    adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    monkeypatch.setattr(adapter, "checkout_revision", lambda: "rev-2")
    agg = adapter.record_baseline(baseline_env.dump, baseline_env.lists / "bfs.list", "b")
    assert set(agg["per_trace"]) == {"bfs"}


def test_a_partial_baseline_is_not_recorded(baseline_env):
    adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    before = helpers.load_baseline("gem5", "b")
    baseline_env.results["lua"] = FakeRunResult(status="run_failed_1", returncode=1)
    with pytest.raises(SystemExit) as caught:
        adapter.record_baseline(baseline_env.dump, baseline_env.lists / "both.list", "b")
    assert "1 of 2" in str(caught.value) and "left alone" in str(caught.value)
    assert helpers.load_baseline("gem5", "b") == before


def test_an_unknown_workload_stops_the_baseline_before_the_build(baseline_env, tmp_path):
    bad = baseline_env.lists / "bad.list"
    bad.write_text("bfs\nsqlite\n")
    with pytest.raises(SystemExit) as caught:
        adapter.record_baseline(baseline_env.dump, bad, "b")
    assert "sqlite" in str(caught.value)
    assert baseline_env.runs == []


def test_workload_fingerprint_moves_with_the_entry_the_binary_and_the_scripts(
        payload_tree, tmp_path):
    fp = lambda: adapter.workload_fingerprint(
        "lua", payload_tree.manifest, payload_tree.workloads, payload_tree.scripts)
    first = fp()
    assert first == fp() and first is not None
    (payload_tree.scripts / "se_o3.py").write_text("# bigger L2\n")
    second = fp()
    assert second != first
    (payload_tree.workloads / "data" / "lua" / "bench.lua").write_text("print(2)\n")
    third = fp()
    assert third != second
    doc = json.loads(payload_tree.manifest.read_text())
    doc["workloads"]["lua"]["args"] = ["bench.lua", "bigger"]
    payload_tree.manifest.write_text(json.dumps(doc))
    assert fp() != third
    assert adapter.workload_fingerprint("nope", payload_tree.manifest) is None


# ------------------------------------------------ contract with p2p_metrics
# These check the promises the adapter relies on in
# hosts/gem5/run/p2p_metrics.py, not how the module keeps them.


def test_p2p_metrics_has_the_interface_the_adapter_calls():
    assert tuple(p2p_metrics.METRIC_KEYS) == ("cond_mpki", "branch_mpki", "ipc")
    for name in ("cycles", "insts", "cond_predicted", "cond_incorrect",
                 "committed_branch_mispredicts", "cond_mispredicts_direct",
                 "cond_mispredicts_indirect"):
        assert p2p_metrics.STATS_KEYS.get(name), name
    for fn in ("derive", "aggregate", "parse_metric_lines", "parse_stats_text", "select",
               "parse_stats_file", "format_metric_lines"):
        assert callable(getattr(p2p_metrics, fn)), fn
    assert not any(k in p2p_metrics.derive({}) for k in p2p_metrics.METRIC_KEYS)


@pytest.mark.parametrize("text", [REAL_STATS.read_text(), stats_text(scales=(3, 1))],
                         ids=["real", "two-dumps"])
def test_the_shell_path_and_the_fan_out_path_read_the_same_numbers(tmp_path, text):
    """G2 compares a run_workload.py run in the agent's shell against a
    baseline recorded through run_traces, at rel_tol 0. The shell path reads
    stats.txt with parse_stats_file. The fan-out path parses the text
    run_gem5 captured. Both must give the same metrics, bit for bit."""
    path = tmp_path / "stats.txt"
    path.write_text(text)
    shell = p2p_metrics.parse_stats_file(str(path))
    record = adapter._judge_run("bfs", "/o", FakeRunResult("bfs", stats_content=text), True)
    assert record["ok"], record["reason"]
    assert record["stats"] == shell
    assert record["metrics"] == p2p_metrics.derive(shell)
    assert set(record["metrics"]) == set(p2p_metrics.METRIC_KEYS)


def test_chias_own_parse_cannot_give_the_conditional_count():
    """Why the adapter parses stats_content itself and ignores result.stats.
    chia's grammar rejects a row with percentage columns, and the one
    committed, conditional-only misprediction count gem5 prints is such a
    row. If this ever fails, chia learned to read it, and the adapter could
    go back to result.stats."""
    from chia.simulators.gem5 import DEFAULT_STATS_KEYS, Gem5Node

    via_chia = Gem5Node.parse_gem5_stats(
        REAL_STATS.read_text(), {**DEFAULT_STATS_KEYS, **p2p_metrics.STATS_KEYS}, "last")
    assert "cond_mispredicts_direct" not in via_chia
    assert via_chia["committed_branch_mispredicts"] == REAL_ALL_MISPREDICTS


def test_metric_lines_round_trip_exactly_through_parse_metrics():
    metrics = {"cond_mpki": 1 / 3, "branch_mpki": 2 / 7, "ipc": 1.2345678901234567}
    text = f"P2P_WORKLOAD x\n{p2p_metrics.format_metric_lines(metrics)}\nP2P_STATUS ok\n"
    assert adapter.parse_metrics(text) == metrics


# ------------------------------------------------- the gate smoke's own plan


def test_the_gate_smokes_test_plan_is_schema_valid(tmp_path):
    """loop/tests/gem5_gate_smoke.py writes its own test plan. A schema
    change that breaks it should fail here, not after a cluster build."""
    import gem5_gate_smoke

    smoke = tmp_path / "gem5-smoke.list"
    smoke.write_text("bfs\nlua\n")
    plan = gem5_gate_smoke.synthesize_test_plan(
        feature_name="sr", host_revision="7a2b0e4", workload="a/b~c",
        smoke_list=smoke, perf_list=smoke, timeout_s=1200)
    _, errors = helpers.validate_json(json.dumps(plan), C.TEST_PLAN_SCHEMA_PATH,
                                      require_jsonschema=True)
    assert errors == []
    entry = plan["correctness"][0]
    assert entry["pass_condition"]["baseline_pointer"] == "/per_trace/a~1b~0c"
    assert entry["command"] == f"python3 {C.GEM5_RUN_DIR}/run_workload.py 'a/b~c'"
    assert plan["metric_keys"] == list(adapter.METRIC_KEYS)


def test_the_gate_smoke_has_a_tree_of_its_own(monkeypatch):
    """The smoke deletes its tree at every run. ~/gem5_port can hold a
    running agent's tree, or a finished run's resume point."""
    import posixpath

    import gem5_gate_smoke

    root = gem5_gate_smoke.smoke_root()
    assert root == posixpath.join(posixpath.dirname(C.GEM5_ROOT), "gem5_smoke")
    assert gem5_gate_smoke.smoke_root_refusal(root) == ""
    monkeypatch.setattr(C, "GEM5_PORT_ROOT", root)
    assert "port tree" in gem5_gate_smoke.smoke_root_refusal(root)
    monkeypatch.setattr(C, "GEM5_PORT_ROOT", "/n/gem5_port")
    monkeypatch.setattr(C, "GEM5_RUN_DIR", root + "/p2p_gem5")
    assert "run dir" in gem5_gate_smoke.smoke_root_refusal(root)


def test_the_gate_smoke_copies_and_gates_its_own_tree_and_never_the_port(
        tmp_path, monkeypatch):
    """main() end to end on the head, with every cluster step faked. It
    copies the pristine checkout to its own tree, runs the gate's own code
    there, and never names ~/gem5_port to anything that writes."""
    import ray

    import gate
    import gem5_gate_smoke

    workload = helpers.load_trace_list(C.GEM5_SMOKE_LIST)[0]
    calls = []
    baseline = {"host_revision": "rev-1", "per_trace": {workload: GOOD_METRICS}}
    real_dumper = helpers.Dumper
    monkeypatch.setattr(helpers, "Dumper", lambda: real_dumper(tmp_path / "out"))
    monkeypatch.setattr(helpers, "load_baseline", lambda host, budget: baseline)
    monkeypatch.setattr(ray, "init", lambda **kw: None)
    ga = gem5_gate_smoke.gem5_adapter
    monkeypatch.setattr(ga, "checkout_revision", lambda: "rev-1")
    monkeypatch.setattr(ga, "check_baseline_current",
                        lambda b, tp, revision=None: calls.append(("check", revision)))
    monkeypatch.setattr(ga, "restore_host_checkout",
                        lambda root=C.GEM5_ROOT: calls.append(("restore", root)) or {})
    monkeypatch.setattr(ga, "clean_port_tree", lambda *a, **k: calls.append(("clean",)))

    def copy_tree(src, dst, *, fresh=True, reset=True):
        calls.append(("copy", src, dst, fresh, reset))
        return {"ok": True, "path": dst}

    results = types.SimpleNamespace(
        build_ok=True, build_log_tail="", feature_off_metrics=GOOD_METRICS,
        correctness=[types.SimpleNamespace(passed=True, id="feature_off_baseline",
                                           kind="feature_off_baseline", reason="")],
        smoke_ok=True, smoke_failures=[],
        performance=[types.SimpleNamespace(
            block_passed=False, id="perf_cond_mpki", metric="cond_mpki", baseline=1.8,
            measured=1.8, relative_improvement=0.0, n_traces=2, failed_traces=[],
            reason="nothing moved")])

    def gate_attempt(b, port_plan, test_plan, *, work_dir):
        calls.append(("gate", work_dir))
        return ga.GateAttempt({"ok": True, "installed": False}, results,
                              gate.GateResult(False, ["G5 [perf_cond_mpki] nothing moved"]))

    monkeypatch.setattr(ga, "copy_tree", copy_tree)
    monkeypatch.setattr(ga, "gate_attempt", gate_attempt)
    monkeypatch.setattr(sys, "argv", ["gem5_gate_smoke.py", "--budget", "b"])

    assert gem5_gate_smoke.main() == 0
    root = gem5_gate_smoke.smoke_root()
    assert calls == [("check", "rev-1"), ("restore", C.GEM5_ROOT),
                     ("copy", C.GEM5_ROOT, root, True, True), ("gate", root)]
    assert root != C.GEM5_PORT_ROOT
