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

    captured = {}

    def fake_chia_remote(binary, trace_path, extra_args, timeout_s):
        captured["trace_path"] = trace_path
        return object()

    monkeypatch.setattr(sr_evaluator.CBP2025Node.run, "chia_remote", fake_chia_remote)

    ev = sr_evaluator.SRParamsEvaluator(
        "/nonexistent/cbp2025", ["int/sample_int_trace.gz"], str(tmp_path), 60, 60
    )
    try:
        sr_evaluator._eval_binary.set(b"fake-binary")
        ev._run(workload="int/sample_int_trace.gz")
    finally:
        sr_evaluator._eval_binary.set(None)
        ev.close()

    assert captured["trace_path"] == f"{C.TRACE_DIR}/int/sample_int_trace.gz"


def test_run_leaves_absolute_trace_path_alone(skydiscover, tmp_path, monkeypatch):
    import sr_evaluator

    captured = {}
    monkeypatch.setattr(
        sr_evaluator.CBP2025Node.run, "chia_remote",
        lambda b, t, e, s: captured.setdefault("trace_path", t),
    )
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
