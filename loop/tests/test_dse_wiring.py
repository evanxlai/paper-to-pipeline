"""Regression tests for the two stage-3 DSE bugs that were invisible locally.

Both of these passed every import check and every unit test that existed, and
both only surfaced against a live cluster -- one as a 10-minute hang, the
other as a search that appeared to run while scoring every candidate zero.
They are cheap to pin down here, so they should never come back silently.

`sr_evaluator` needs skydiscover/evolve-flows (not on PyPI, see
docs/dse-setup.md), so the tests that import it skip rather than fail where it
is not installed. They declare that by taking the `skydiscover` fixture below;
the `params_header_from_spec` tests need only `dse` and always run.
"""

import pytest

import dse


@pytest.fixture
def skydiscover():
    """Skip the requesting test when evolve-flows is absent.

    This is a fixture rather than a module-level `importorskip` so that a
    missing skydiscover only skips the tests that actually import
    `sr_evaluator`, not the whole file (which would silently drop the header
    tests as well).
    """
    return pytest.importorskip(
        "skydiscover", reason="skydiscover/evolve-flows not installed (docs/dse-setup.md)"
    )


def capture_run(monkeypatch, sr_evaluator):
    """Intercept the evaluator's trace dispatch and record its arguments.

    `_run` reaches Ray through `CBP2025Node.run.options(resources=...)`, and
    the resource override is not decoration: the trace nodes and the node
    holding the ported checkout advertise different tokens. Patching
    `chia_remote` alone therefore misses, and the test dispatches a real Ray
    task against whatever cluster happens to be up. That is how these two
    tests started failing with "No module named 'chia_nodes'" from a worker
    rather than with an assertion.
    """
    captured = {}

    class _Handle:
        @staticmethod
        def chia_remote(binary, trace_path, extra_args, timeout_s, env=None):
            captured.update(
                binary=binary, trace_path=trace_path, extra_args=extra_args,
                timeout_s=timeout_s, env=env,
            )
            return object()

    def fake_options(**kwargs):
        captured["resources"] = kwargs.get("resources")
        return _Handle

    monkeypatch.setattr(sr_evaluator.CBP2025Node.run, "options", fake_options)
    monkeypatch.setattr(sr_evaluator.CBP2025Node.run, "chia_remote", _Handle.chia_remote)
    return captured


@pytest.fixture
def spec():
    """A minimal spec exercising each parameter type the header renderer emits."""
    return {
        "feature_name": "vtag",
        "parameters": [
            {"name": "table_entries", "type": "int", "default": 64, "range": "[8, 256]"},
            {"name": "weight_scale", "type": "float", "default": 1.5, "range": "[0.0, 4.0]"},
            {"name": "use_skew", "type": "bool", "default": True, "range": "true|false"},
            {
                "name": "hash_variant",
                "type": "enum",
                "default": "XOR fold of the PC bits",
                "range": "choices: XOR fold of the PC bits|No skew|Skewed-associative",
            },
        ],
    }


# --------------------------------------------------------------- header render

def test_header_renders_one_define_per_parameter(spec):
    lines = [l for l in dse.params_header_from_spec(spec).splitlines()
             if l.startswith("#define")]
    assert len(lines) == len(spec["parameters"])
    assert lines[0].startswith("#define SR_TABLE_ENTRIES 64")


def test_enum_renders_as_c_safe_index_not_prose(spec):
    """Enum choices are free-text sentences; emitting them literally would not
    compile. They must become an integer index, with the mapping in a comment."""
    line = next(l for l in dse.params_header_from_spec(spec).splitlines()
                if "HASH_VARIANT" in l)
    assert line.startswith("#define SR_HASH_VARIANT 0")
    assert "0=XOR fold of the PC bits" in line
    # The prose must not leak into the macro body, only into the comment.
    body = line.split("//")[0]
    assert "XOR fold" not in body


def test_bool_renders_lowercase_for_c(spec):
    line = next(l for l in dse.params_header_from_spec(spec).splitlines()
                if "USE_SKEW" in l)
    assert line.startswith("#define SR_USE_SKEW true")


def test_overrides_replace_defaults(spec):
    header = dse.params_header_from_spec(spec, {"table_entries": 128})
    assert "#define SR_TABLE_ENTRIES 128" in header


def test_feature_scopes_its_header_and_evolver_actor():
    sr = {"feature_name": "sr"}
    wormhole = {"feature_name": "wormhole"}

    assert dse.params_header_name(sr) == "sr_params.h"
    assert dse.params_header_name(wormhole) == "wormhole_params.h"
    assert dse.evolver_actor_name("cbp2025", "sr") != \
        dse.evolver_actor_name("cbp2025", "wormhole")


# ------------------------------------------------- bug 1: relative trace paths

def test_run_prefixes_relative_trace_with_trace_dir(skydiscover, tmp_path, monkeypatch):
    """helpers.load_trace_list returns entries verbatim ('int/x_trace.gz').

    Passing those through bare made every ./cbp invocation resolve the trace
    against the Ray worker's cwd and fail to open it -- which aggregate() turns
    into n=0 and _map_results turns into combined_score 0.0. The search then
    looks healthy while learning nothing, so this must stay pinned.
    """
    import constants as C
    import sr_evaluator

    captured = capture_run(monkeypatch, sr_evaluator)

    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["int/sample_int_trace.gz"], str(tmp_path), 60, 60,
        feature_env={"SR_SR_ENABLE": "1"},
    )
    try:
        sr_evaluator._eval_binary.set(b"fake-binary")
        ev._run(workload="int/sample_int_trace.gz")
    finally:
        sr_evaluator._eval_binary.set(None)
        ev.close()

    assert captured["trace_path"] == f"{C.TRACE_DIR}/int/sample_int_trace.gz"
    assert captured["resources"] == {C.CBP2025_RESOURCE: 1.0}
    # The search tunes a feature that has to be switched on. The port
    # defaults its enable knob off because G2 requires that, so a screening
    # run with an empty environment measures the baseline 250 times.
    assert captured["env"] == {"SR_SR_ENABLE": "1"}


def test_run_leaves_absolute_trace_path_alone(skydiscover, tmp_path, monkeypatch):
    import sr_evaluator

    captured = capture_run(monkeypatch, sr_evaluator)
    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["/abs/t.gz"], str(tmp_path), 60, 60
    )
    try:
        sr_evaluator._eval_binary.set(b"fake-binary")
        ev._run(workload="/abs/t.gz")
    finally:
        sr_evaluator._eval_binary.set(None)
        ev.close()

    assert captured["trace_path"] == "/abs/t.gz"


def test_run_without_a_build_raises(skydiscover, tmp_path):
    """run_fn is never handed the build artifact, so a missing binary means the
    build/run ordering broke -- fail loudly rather than dispatching garbage."""
    import sr_evaluator

    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["int/x.gz"], str(tmp_path), 60, 60
    )
    try:
        sr_evaluator._eval_binary.set(None)
        with pytest.raises(RuntimeError, match="no binary available"):
            ev._run(workload="int/x.gz")
    finally:
        ev.close()


# ------------------------------------------- bug 2: evaluator must pickle

def test_evaluator_is_module_scope_so_it_pickles_by_reference(skydiscover, tmp_path):
    """The evaluator instance is pickled to the EvolverNode actor: bridge.py
    registers it and generates a shim that calls evaluate_program on it.

    A class defined inside a factory function is pickled *by value*, which
    drags in the module-level ContextVar and dies with "cannot pickle
    '_contextvars.ContextVar' object". Module scope pickles by reference
    instead. Assert on the round-trip, not just on __qualname__, so this also
    catches any future unpicklable attribute stored on the instance.
    """
    from ray import cloudpickle
    import sr_evaluator

    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["int/x.gz"], str(tmp_path), 60, 60
    )
    try:
        revived = cloudpickle.loads(cloudpickle.dumps(ev))
        assert type(revived) is sr_evaluator.SRParamsEvaluator
        assert revived.workloads == ["int/x.gz"]
        # The bound methods travel as run_search arguments too.
        for fn in (ev._build, ev._run, ev._map_results):
            cloudpickle.loads(cloudpickle.dumps(fn))
    finally:
        ev.close()


def test_evaluator_class_is_not_nested_in_a_function(skydiscover, tmp_path):
    """Guards the structural property directly: a '<locals>' in the qualname
    means someone moved the class back inside a factory, which reintroduces
    by-value pickling even if the ContextVar happens to be gone."""
    import sr_evaluator

    assert "<locals>" not in sr_evaluator.SRParamsEvaluator.__qualname__


# ------------------------------------------------- the profiler's wrapper
# start_collector() is on for the whole job, so every ChiaFunction result
# arrives wrapped. chia's get() unwraps it and every other caller in this
# repository goes through get(). skydiscover's ChiaEvaluator awaits the
# ObjectRef itself, so the wrapper reaches the evaluator intact. The first
# stage-4 run died on that before evaluating a single candidate.


def test_unwrap_strips_a_profiled_result(skydiscover):
    import sr_evaluator
    from chia.trace.profiler import _ProfiledResult

    class Build:
        success = True
        binary = b"bytes"

    wrapped = _ProfiledResult(
        value=Build(), worker_ip="10.0.0.1", worker_id="w", node_id="n",
        exec_time_s=1.0,
    )
    assert sr_evaluator._unwrap(wrapped).success is True


def test_unwrap_passes_an_unwrapped_result_through(skydiscover):
    """The profiler can be off. The evaluator has to work either way."""
    import sr_evaluator

    class Build:
        success = False

    plain = Build()
    assert sr_evaluator._unwrap(plain) is plain
    assert sr_evaluator._unwrap(None) is None


def test_map_results_unwraps_every_run(skydiscover, tmp_path):
    """aggregate() reads .success and .metrics off each run. A wrapped run
    makes every candidate score zero, which reads as a healthy search that
    learns nothing rather than as a bug."""
    import sr_evaluator
    from chia.trace.profiler import _ProfiledResult

    class Run:
        success = True
        trace = "int/a.gz"
        metrics = {"50perc": {"mpki": 2.0, "cycwppki": 40.0, "ipc": 1.5}}

    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent", ["int/a.gz"], str(tmp_path), 60, 60)
    try:
        wrapped = _ProfiledResult(
            value=Run(), worker_ip="i", worker_id="w", node_id="n",
            exec_time_s=1.0,
        )
        out = ev._map_results([wrapped])
    finally:
        ev.close()
    assert out.metrics["combined_score"] > 0
    assert out.metrics["brmispki_50perc_amean"] == 2.0
