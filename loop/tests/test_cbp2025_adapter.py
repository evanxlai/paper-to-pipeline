"""Unit tests for the cbp2025 host adapter.

Everything here is about the parts of `hosts/cbp2025/adapter.py` that decide
a gate verdict but need no cluster to exercise: which metric names come out
of one ./cbp run, which environment turns the port on, which Ray resource
token each dispatch asks for, and when the checkout has to be rebuilt.

Those are worth pinning because each one fails *quietly* in production. A
metric under the wrong name reads as a missing measurement, an enable
variable the port does not read leaves the feature off in both gate states,
a dispatch on the wrong token builds a tree nobody edited, and a stale
binary makes a correctness entry measure the baseline and pass.
"""

import pytest

from hosts.cbp2025 import adapter


# One real ./cbp tail, trimmed to the two tables the parser looks at.
CBP_OUTPUT = """\
------------------------------------------------------DIRECT CONDITIONAL BRANCH PREDICTION MEASUREMENTS (Last 10M instructions)-----------------------------------------------------
       Instr       Cycles      IPC      NumBr     MispBr BrPerCyc MispBrPerCyc        MR     MPKI      CycWP   CycWPAvg   CycWPPKI
      997301       338411   2.9470     128874        264   0.3808       0.0008   0.2049%   0.2647      34305   129.9432    34.3978
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------DIRECT CONDITIONAL BRANCH PREDICTION MEASUREMENTS (50 Perc instructions)---------------------------------------------------
       Instr       Cycles      IPC      NumBr     MispBr BrPerCyc MispBrPerCyc        MR     MPKI      CycWP   CycWPAvg   CycWPPKI
      997301       338411   2.9470     128874        264   0.3808       0.0008   0.2049%   0.2647      34305   129.9432    34.3978
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Read 997301 instrs
"""


# ---------------------------------------------------------------- metrics


def test_parse_metrics_uses_the_aggregate_names():
    """One trace and sixty traces must produce the same keys.

    G2 runs a single ./cbp command and compares what comes back against the
    per-trace map `record_cbp_baseline` wrote, which is keyed by the suite
    aggregate's names. Emitting the raw column names here instead would make
    every G2 comparison report both sides missing rather than equal."""
    assert adapter.parse_metrics(CBP_OUTPUT) == {
        "brmispki_50perc_amean": 0.2647,
        "cycwppki_50perc_amean": 34.3978,
        "ipc_50perc_amean": 2.947,
    }
    assert set(adapter.parse_metrics(CBP_OUTPUT)) == set(adapter.METRIC_KEYS)


def test_parse_metrics_reads_the_scoring_window_not_the_first_table():
    """The 50 Perc row is the contest's, and it is not the first table
    printed. A run whose two windows differ must yield the 50 Perc one."""
    output = CBP_OUTPUT.replace("2.9470     128874        264", "9.9999     128874        264", 1)
    assert adapter.parse_metrics(output)["ipc_50perc_amean"] == 2.947


def test_parse_metrics_on_a_crashed_run_is_empty_not_an_exception():
    """A crashed ./cbp has to reach the gate as a failed entry with a
    reason. Raising here would kill the stage that was diagnosing it."""
    assert adapter.parse_metrics("Segmentation fault") == {}
    assert adapter.parse_metrics("") == {}
    assert adapter.parse_metrics(None) == {}


# ------------------------------------------------------------ enable knob


def test_enable_env_sets_every_alias_the_plan_could_have_used():
    enable = {"name": "sr_enable", "macro": "SR_SR_ENABLE", "binding": "runtime_env"}
    assert adapter.enable_env(enable, True) == {
        "sr_enable": "1", "SR_ENABLE": "1", "SR_SR_ENABLE": "1",
    }
    assert adapter.enable_env(enable, False) == {
        "sr_enable": "0", "SR_ENABLE": "0", "SR_SR_ENABLE": "0",
    }


def test_enable_env_without_a_macro_still_sets_the_name():
    enable = {"name": "TINYSC_ENABLE", "binding": "runtime_env"}
    assert adapter.enable_env(enable, True) == {"TINYSC_ENABLE": "1"}


def test_enable_env_of_nothing_is_nothing():
    """An empty dict, not a crash and not a {None: '1'} entry that would
    blow up when it reaches os.environ."""
    assert adapter.enable_env({}, True) == {}
    assert adapter.enable_env(None, True) == {}


# ------------------------------------------------------- build state machine


class FakeBuildResult:
    def __init__(self, success=True, binary=b"cbp-bytes", log="ok"):
        self.success, self.binary, self.log = success, binary, log


@pytest.fixture
def fake_build(monkeypatch):
    """Record every build dispatch: its resources, its env, its cbp_root."""
    calls = []

    class _Handle:
        @staticmethod
        def chia_remote(cbp_root, sources, timeout_s, env=None):
            calls.append({"cbp_root": cbp_root, "sources": sources,
                          "timeout_s": timeout_s, "env": env,
                          "resources": calls_resources[-1]})
            return FakeBuildResult()

    calls_resources = []

    def fake_options(**kwargs):
        calls_resources.append(kwargs.get("resources"))
        return _Handle

    monkeypatch.setattr(adapter.CBP2025Node.build, "options", fake_options)
    monkeypatch.setattr(adapter, "get", lambda ref: ref)
    return calls


def test_a_runtime_knob_builds_once_for_both_states(fake_build):
    """The recommended binding. Rebuilding per state would double every gate
    attempt's build time to produce the identical binary twice."""
    ex = adapter.CBP2025Executor(
        "/tmp/port", {"name": "sr_enable", "binding": "runtime_env"}
    )
    assert ex.rebuild_per_state is False
    assert ex.build(feature_on=False).ok
    assert ex.build(feature_on=True).ok
    assert len(fake_build) == 1


def test_a_compile_time_knob_builds_once_per_state(fake_build):
    ex = adapter.CBP2025Executor(
        "/tmp/port",
        {"name": "sr_enable", "macro": "SR_SR_ENABLE", "binding": "compile_time_define"},
    )
    assert ex.rebuild_per_state is True
    ex.build(feature_on=False)
    ex.build(feature_on=True)
    assert len(fake_build) == 2
    assert fake_build[0]["env"] == {"sr_enable": "0", "SR_ENABLE": "0", "SR_SR_ENABLE": "0"}
    assert fake_build[1]["env"] == {"sr_enable": "1", "SR_ENABLE": "1", "SR_SR_ENABLE": "1"}


def test_the_build_is_pinned_to_the_node_holding_the_checkout(fake_build):
    """CBP2025Node.build's own token is "cbp2025", which the trace-only node
    also advertises. The ported tree exists on one machine, so a build that
    keeps the default token can compile a checkout nobody edited and report
    it green."""
    import constants as C

    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    ex.build(feature_on=False)
    assert fake_build[0]["resources"] == {C.CBP2025_HOST_RESOURCE: 1.0}
    assert fake_build[0]["cbp_root"] == "/tmp/port"


def test_a_shell_in_the_other_state_rebuilds_a_compile_time_port(fake_build, monkeypatch):
    """The failure this exists for: run_test_plan builds feature-off first,
    then runs a correctness entry declaring feature_state "on". With a
    compile-time knob the tree still holds the feature-off binary, so that
    entry measures the baseline and passes."""
    shells = []
    monkeypatch.setattr(
        adapter, "host_shell",
        type("H", (), {"options": staticmethod(lambda **kw: type("R", (), {
            "chia_remote": staticmethod(lambda cwd, cmd, env, t: shells.append(env) or {
                "exit_code": 0, "output": "", "timed_out": False})})())})
    )
    ex = adapter.CBP2025Executor(
        "/tmp/port", {"name": "k", "binding": "compile_time_define"}
    )
    ex.build(feature_on=False)
    assert len(fake_build) == 1
    ex.shell("./cbp t.gz", feature_on=True, timeout_s=60)
    assert len(fake_build) == 2, "the checkout was not rebuilt for the on state"
    assert fake_build[1]["env"]["k"] == "1"
    # ...and not again for a second command in the same state.
    ex.shell("./cbp t.gz", feature_on=True, timeout_s=60)
    assert len(fake_build) == 2


def test_a_shell_never_rebuilds_a_runtime_knob_port(fake_build, monkeypatch):
    shells = []
    monkeypatch.setattr(
        adapter, "host_shell",
        type("H", (), {"options": staticmethod(lambda **kw: type("R", (), {
            "chia_remote": staticmethod(lambda cwd, cmd, env, t: shells.append(env) or {
                "exit_code": 0, "output": "", "timed_out": False})})())})
    )
    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    ex.build(feature_on=False)
    ex.shell("./cbp t.gz", feature_on=True, timeout_s=60)
    ex.shell("./cbp t.gz", feature_on=False, timeout_s=60)
    assert len(fake_build) == 1
    assert shells[0]["k"] == "1" and shells[1]["k"] == "0"


def test_a_failed_build_is_not_cached_as_a_success(fake_build, monkeypatch):
    monkeypatch.setattr(
        adapter.CBP2025Node.build, "options",
        lambda **kw: type("R", (), {"chia_remote": staticmethod(
            lambda *a, **k: FakeBuildResult(success=False, log="error: no")
        )}),
    )
    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    first = ex.build(feature_on=False)
    assert not first.ok and "error: no" in first.log
    assert ex._tree_state is None
    assert not ex.build(feature_on=False).ok


# ----------------------------------------------------------- trace fan-out


def test_run_traces_reports_failures_under_the_names_the_plan_used(monkeypatch):
    """`aggregate` names a failed trace by the absolute path it was given.
    The plan named it relative to the trace dir, and a G5 reason quoting the
    absolute one points at nothing the reader can find in the list."""
    import constants as C

    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    ex._binaries[False] = b"bytes"
    ex._tree_state = False

    class FakeRunResult:
        def __init__(self, trace, success):
            self.trace, self.success, self.log = trace, success, "log tail"

    monkeypatch.setattr(
        adapter.CBP2025Node.run, "options",
        lambda **kw: type("R", (), {"chia_remote": staticmethod(
            lambda binary, trace, extra, timeout, env=None: FakeRunResult(
                trace, "int_13" not in trace)
        )}),
    )
    monkeypatch.setattr(
        adapter.CBP2025Node.aggregate, "chia_remote",
        lambda results: {
            "n": 1, "failed": [f"{C.TRACE_DIR}/int/int_13_trace.gz"],
            "brmispki_50perc_amean": 1.0,
        },
    )
    monkeypatch.setattr(adapter, "get", lambda ref: ref)

    out = ex.run_traces(
        ["int/int_13_trace.gz", "web/web_11_trace.gz"], feature_on=True, timeout_s=60
    )
    assert out.failed == ["int/int_13_trace.gz"]
    assert out.ok is False
    assert out.metrics == {"brmispki_50perc_amean": 1.0}
    assert out.log_tail == "log tail"


def test_run_traces_survives_a_ray_task_that_died(monkeypatch):
    """A killed worker yields None, not a result. aggregate() already counts
    that as a failure; the adapter must not take the gate down reading its
    log first."""
    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    ex._binaries[False] = b"bytes"
    ex._tree_state = False
    monkeypatch.setattr(
        adapter.CBP2025Node.run, "options",
        lambda **kw: type("R", (), {"chia_remote": staticmethod(
            lambda *a, **k: None
        )}),
    )
    monkeypatch.setattr(
        adapter.CBP2025Node.aggregate, "chia_remote",
        lambda results: {"n": 0, "failed": ["a.gz"]},
    )
    monkeypatch.setattr(adapter, "get", lambda ref: ref)
    out = ex.run_traces(["a.gz"], feature_on=True, timeout_s=60)
    assert out.ok is False and out.failed == ["a.gz"]


def test_run_traces_without_a_binary_fails_every_trace(monkeypatch):
    """A build that never produced bytes must not silently score zero
    traces as a clean run."""
    ex = adapter.CBP2025Executor("/tmp/port", {"name": "k", "binding": "runtime_env"})
    monkeypatch.setattr(
        adapter.CBP2025Node.build, "options",
        lambda **kw: type("R", (), {"chia_remote": staticmethod(
            lambda *a, **k: FakeBuildResult(success=False, log="nope")
        )}),
    )
    monkeypatch.setattr(adapter, "get", lambda ref: ref)
    out = ex.run_traces(["a.gz", "b.gz"], feature_on=True, timeout_s=60)
    assert out.ok is False
    assert out.failed == ["a.gz", "b.gz"]
    assert out.metrics == {}


# --------------------------------------------------------- the reset guard


def test_restoring_the_port_tree_is_refused():
    """restore_checkout is `git reset --hard` plus `git clean -fdx`. Pointed
    at the tree stage 3 edits, it deletes an integration run's entire work,
    and there is no other copy of it."""
    import constants as C

    with pytest.raises(SystemExit) as caught:
        adapter.restore_host_checkout(C.CBP2025_PORT_ROOT)
    assert "refusing to reset" in str(caught.value)


# ------------------------------------------------- the port tree lifecycle
# materialize_port_tree decides whether an integration run starts from a
# clean checkout or from the port a previous run left. Getting that wrong
# in either direction is expensive: reset when it should not, and a run's
# work is gone with no other copy; skip the reset when it should not, and
# stage 2's leftovers satisfy stage 3's tests.


import subprocess


def _git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(a, cwd=path, capture_output=True, check=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    (path / "predictor.h").write_text("// pristine\n")
    (path / "lib").mkdir(exist_ok=True)
    run("git", "add", "-A")
    run("git", "commit", "-qm", "initial")
    return path


def test_a_fresh_port_tree_is_the_commit_and_nothing_else(tmp_path):
    """Stage 2's planner has a shell on the source tree and leaves things
    behind. A copy that trusts whatever is there carried a test_sr.cc
    printing "Test passed" into the port and satisfied all seven unit
    tests."""
    src = _git_repo(tmp_path / "src")
    (src / "test_sr.cc").write_text('int main(){puts("Test passed");}\n')
    (src / "cbp").write_text("stale binary")
    (src / "predictor.h").write_text("// planner scribbled here\n")

    out = adapter.materialize_port_tree(str(src), str(tmp_path / "port"))
    port = tmp_path / "port"
    assert out["ok"] and out["reused"] is False
    assert not (port / "test_sr.cc").exists()
    assert not (port / "cbp").exists()
    assert (port / "predictor.h").read_text() == "// pristine\n"


def test_reset_false_keeps_the_port_and_drops_only_the_build(tmp_path):
    """What stage 4 needs: a copy of the ported tree to search in, with the
    port intact. Resetting here would delete the thing being tuned."""
    src = _git_repo(tmp_path / "src")
    (src / "predictor.h").write_text("// the port\n")
    (src / "sr_params.h").write_text("#define SR_NUM_BANKS 8\n")
    (src / "cbp").write_text("stale binary")
    (src / "predictor.o").write_text("stale object")

    out = adapter.materialize_port_tree(
        str(src), str(tmp_path / "dse"), True, False)
    dse = tmp_path / "dse"
    assert out["ok"]
    assert (dse / "predictor.h").read_text() == "// the port\n"
    assert (dse / "sr_params.h").exists()
    assert not (dse / "cbp").exists()
    assert not (dse / "predictor.o").exists()


def test_fresh_false_reuses_an_existing_tree_untouched(tmp_path):
    """P2P_CBP2025_PORT_FRESH=0 is for resuming a run that died partway. It
    has to return the tree as the dead run left it. A Vertex 429 has
    already taken one run down with the port most of the way written."""
    src = _git_repo(tmp_path / "src")
    port = tmp_path / "port"
    adapter.materialize_port_tree(str(src), str(port))
    (port / "predictor.h").write_text("// half a port\n")
    (port / "sr_params.h").write_text("#define SR_NUM_BANKS 8\n")

    out = adapter.materialize_port_tree(str(src), str(port), False)
    assert out["reused"] is True
    assert (port / "predictor.h").read_text() == "// half a port\n"
    assert (port / "sr_params.h").exists()


def test_a_missing_source_is_reported_not_raised(tmp_path):
    out = adapter.materialize_port_tree(
        str(tmp_path / "nope"), str(tmp_path / "port"))
    assert out["ok"] is False and "does not exist" in out["error"]
