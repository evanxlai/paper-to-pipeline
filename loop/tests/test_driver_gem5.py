"""The driver's gem5 wiring, and proof that the cbp2025 path did not move.

What these pin is the part of adopt_a_paper_loop.py and dse.py that decides
where a host's work goes: which token its shell asks for, how long that
shell may run, which mirror the plan checks read, which recorder --stage
baseline calls and on which list, and which stages refuse gem5 outright.
None of it needs a cluster to be wrong, so none of it should need one to be
checked.

What they do not show is that gem5 works. The gem5 adapter here is a fake
with the surface the design brief gives hosts/gem5/adapter.py, and a fake
that answers is never evidence that the real node builds or runs anything.
docs/gem5-runbook.md is how that gets shown, on the cluster.

No test here starts Ray. Every Ray-facing call is replaced: main()'s
ray.init records that it was reached, the bash tool is a stub, and every
adapter function that would dispatch a ChiaFunction is a recorder.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import adopt_a_paper_loop as loop
import constants as C
import dse
import gate
import helpers

REPO = Path(__file__).resolve().parents[2]
LOOP = REPO / "loop"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
_RealDumper = helpers.Dumper


# ------------------------------------------------------------------ fakes


class FakeGem5Adapter:
    """The hosts/gem5/adapter.py functions the driver calls, recording each
    call in order. The signatures are the design brief's section 3."""

    REVISION = "7a2b0e413d06c5ce7097104abef3b1d9eaabca91"

    def __init__(self):
        self.calls: list[tuple] = []

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]

    def clean_port_tree(self, fresh=True):
        self.calls.append(("clean_port_tree", fresh))
        return {"ok": True, "path": C.GEM5_PORT_ROOT}

    def install_run_dir_on_cluster(self):
        self.calls.append(("install_run_dir_on_cluster",))
        return {"dest": C.GEM5_RUN_DIR, "sha256": "0" * 16, "reused": True}

    def notes(self):
        return "(gem5 notes)"

    def check_baseline_current(self, baseline, test_plan, revision=None):
        self.calls.append(("check_baseline_current",))

    def run_gate(self, baseline, port_plan, test_plan):
        return gate.GateResult(True)

    def restore_host_checkout(self, root=C.GEM5_ROOT):
        self.calls.append(("restore_host_checkout", root))
        return {"root": root, "was_dirty": False, "removed": []}

    def checkout_revision(self):
        self.calls.append(("checkout_revision",))
        return self.REVISION

    def port_diff(self):
        self.calls.append(("port_diff",))
        return "--- patch ---\n+gem5 port\n"

    def record_baseline(self, dump, workload_list, budget):
        self.calls.append(("record_baseline", dump, Path(workload_list), budget))
        return {"n": 2, "per_trace": {}}


class _NullTool:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeResponse:
    def __init__(self, text: str):
        self.result = text
        self.success = True
        self.stream_result = ""
        self.usage = None


class _ReachedCluster(Exception):
    """main() got past every refusal and asked Ray for the cluster."""


@pytest.fixture
def gem5(monkeypatch):
    fake = FakeGem5Adapter()
    monkeypatch.setattr(loop, "_gem5_adapter", lambda: fake)
    return fake


@pytest.fixture
def no_gem5(monkeypatch):
    """A cbp2025 test that reaches the gem5 adapter at all fails."""
    def refuse():
        raise AssertionError("a cbp2025 path reached for the gem5 adapter")
    monkeypatch.setattr(loop, "_gem5_adapter", refuse)


def test_the_fake_matches_the_real_adapter():
    """The fake is only worth what its resemblance to the real module is
    worth. Skipped until hosts/gem5/adapter.py and the run scripts it
    imports exist. Once they do, it has to import, and every function the
    driver calls has to take the arguments the driver passes."""
    import inspect

    for part in ("adapter.py", "run/p2p_metrics.py"):
        if not (REPO / "hosts" / "gem5" / part).exists():
            pytest.skip(f"hosts/gem5/{part} is not written yet")
    from hosts.gem5 import adapter as real

    calls = {
        "clean_port_tree": ((), {"fresh": True}),
        "install_run_dir_on_cluster": ((), {}),
        "notes": ((), {}),
        "run_gate": (({}, {}, {}), {}),
        "restore_host_checkout": ((C.GEM5_ROOT,), {}),
        "checkout_revision": ((), {}),
        "port_diff": ((), {}),
        "record_baseline": ((object(), C.GEM5_SMOKE_LIST, "iso-192KiB"), {}),
    }
    for name, (args, kwargs) in calls.items():
        fn = getattr(real, name, None)
        assert callable(fn), f"hosts/gem5/adapter.py has no {name}()"
        inspect.signature(fn).bind(*args, **kwargs)


# ------------------------------------------------- the lazy import itself


def _module_level_imports(tree: ast.Module) -> list[str]:
    """Every module name imported outside a function or class body."""
    names: list[str] = []

    def visit(stmts):
        for node in stmts:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, ast.Import):
                names.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module or "")
                names.extend(f"{node.module}.{a.name}" for a in node.names)
            for field in ("body", "orelse", "finalbody", "handlers"):
                visit(getattr(node, field, []) or [])

    visit(tree.body)
    return names


@pytest.mark.parametrize("module", ["adopt_a_paper_loop.py", "dse.py"])
def test_no_module_level_import_of_the_gem5_adapter(module):
    """The cbp2025 path is producing the project's main result. A top-level
    import would make every cbp2025 job depend on the gem5 adapter
    importing cleanly."""
    imports = _module_level_imports(ast.parse((LOOP / module).read_text()))
    assert not [n for n in imports if "gem5" in n], imports


def test_cbp2025_stages_run_with_the_gem5_adapter_unimportable(monkeypatch, tmp_path):
    """The real import, blocked: None in sys.modules makes any import of it
    raise. cbp2025's adapter, baseline and plan paths still run."""
    monkeypatch.setitem(sys.modules, "hosts.gem5", None)
    monkeypatch.setitem(sys.modules, "hosts.gem5.adapter", None)
    with pytest.raises(ImportError):
        loop._gem5_adapter()

    monkeypatch.setattr(loop.cbp2025_adapter, "clean_port_tree", lambda fresh=True: {"ok": True})
    assert loop.default_adapter("cbp2025", "iso-192KiB").name == "cbp2025"

    recorded = []
    monkeypatch.setattr(loop, "record_cbp_baseline", lambda *a: recorded.append(a) or {"n": 2})
    dump = _RealDumper(out_dir=tmp_path)
    loop.record_host_baseline(dump, "cbp2025", loop.baseline_list("cbp2025"), "iso-192KiB")
    assert len(recorded) == 1


def test_a_gem5_stage_surfaces_a_broken_adapter(monkeypatch):
    """The other half of the lazy import: a gem5 job with a broken adapter
    fails loudly on the import, not later on a fallback."""
    monkeypatch.setitem(sys.modules, "hosts.gem5", None)
    monkeypatch.setitem(sys.modules, "hosts.gem5.adapter", None)
    with pytest.raises(ImportError):
        loop.default_adapter("gem5", "iso-192KiB")


# ------------------------------------------------------ tokens and limits


def test_shell_resources_per_host():
    assert loop.shell_resources("gem5") == {C.GEM5_HOST_RESOURCE: 0.1}
    assert loop.shell_resources("cbp2025") == {C.CBP2025_HOST_RESOURCE: 0.1}
    assert loop.shell_resources("champsim") == {"champsim": 0.1}


def test_host_shell_resource_table():
    assert loop.HOST_SHELL_RESOURCE["cbp2025"] == C.CBP2025_HOST_RESOURCE
    assert loop.HOST_SHELL_RESOURCE["gem5"] == C.GEM5_HOST_RESOURCE


def test_shell_timeout_per_host():
    assert loop.shell_timeout_s("gem5") == C.GEM5_BASH_TOOL_TIMEOUT_S
    assert loop.shell_timeout_s("cbp2025") == C.BASH_TOOL_TIMEOUT_S
    assert loop.shell_timeout_s("champsim") == C.BASH_TOOL_TIMEOUT_S


def test_checks_root_per_host():
    assert loop.checks_root("gem5") == str(REPO / "third_party" / "gem5")
    assert loop.checks_root("cbp2025") == str(REPO / "third_party" / "cbp2025")
    assert loop.checks_root("champsim") is None


# -------------------------------------------------------- default_adapter


def test_default_adapter_gem5(gem5, monkeypatch):
    loaded = []
    monkeypatch.setattr(helpers, "load_baseline",
                        lambda host, key: loaded.append((host, key)) or {"per_trace": {}})
    adapter = loop.default_adapter("gem5", "iso-64KiB")

    # The port tree before the run dir, both before any shell exists.
    assert gem5.calls == [("clean_port_tree", C.GEM5_PORT_FRESH),
                          ("install_run_dir_on_cluster",)]
    assert adapter.name == "gem5"
    assert adapter.work_dir == C.GEM5_PORT_ROOT
    assert adapter.notes == "(gem5 notes)"
    assert adapter.resources == {C.GEM5_HOST_RESOURCE: 0.1}
    assert adapter.checks_root == str(REPO / "third_party" / "gem5")
    assert adapter.run_gate == gem5.run_gate
    assert adapter.shell_timeout_s == C.GEM5_BASH_TOOL_TIMEOUT_S
    assert adapter.baseline() == {"per_trace": {}}
    assert loaded == [("gem5", "iso-64KiB")]


def test_default_adapter_gem5_keeps_the_tree_to_resume(gem5, monkeypatch):
    monkeypatch.setattr(C, "GEM5_PORT_FRESH", False)
    loop.default_adapter("gem5", "iso-192KiB")
    assert gem5.calls[0] == ("clean_port_tree", False)


@pytest.mark.parametrize("fresh", [True, False])
def test_default_adapter_gem5_takes_a_replans_fresh_over_the_env(gem5, monkeypatch, fresh):
    # replan.py decides per round whether the port tree starts over, and the
    # host's own default must not overrule it in either direction.
    monkeypatch.setattr(C, "GEM5_PORT_FRESH", not fresh)
    loop.default_adapter("gem5", "iso-64KiB", fresh=fresh)
    assert gem5.calls[0] == ("clean_port_tree", fresh)


def test_default_adapter_cbp2025_is_unchanged(no_gem5, monkeypatch):
    cleaned = []
    monkeypatch.setattr(loop.cbp2025_adapter, "clean_port_tree",
                        lambda fresh=True: cleaned.append(fresh) or {"ok": True})
    adapter = loop.default_adapter("cbp2025", "iso-64KiB")

    assert cleaned == [C.CBP2025_PORT_FRESH]
    assert adapter.name == "cbp2025"
    assert adapter.work_dir == C.CBP2025_PORT_ROOT
    assert adapter.notes == loop.cbp2025_adapter.notes()
    assert adapter.resources == {C.CBP2025_HOST_RESOURCE: 0.1}
    assert adapter.checks_root == str(REPO / "third_party" / "cbp2025")
    assert adapter.run_gate is loop.cbp2025_adapter.run_gate
    assert adapter.shell_timeout_s is None


def test_default_adapter_champsim_still_fails_closed(no_gem5):
    adapter = loop.default_adapter("champsim", "iso-192KiB")
    assert adapter.shell_timeout_s is None
    assert adapter.run_gate({}, {}, {}).passed is False


# --------------------------------------------------------------- stage 3


@pytest.fixture
def integrate_run(tmp_path, monkeypatch):
    """integrate() with a scripted model and a stub shell, one attempt."""
    monkeypatch.setattr(C, "PLAN_DIR", tmp_path / "plan")
    monkeypatch.setattr(C, "NUM_INTEGRATION_ATTEMPTS", 1)
    shells: list[dict] = []
    monkeypatch.setattr(loop, "BashTool", lambda **kw: shells.append(kw) or _NullTool(**kw))
    monkeypatch.setattr(loop, "make_llm", lambda *a, **kw: None)
    spec = json.loads((FIXTURES / "tinysc.spec.json").read_text())
    port = json.loads((FIXTURES / "tinysc.toy.plan.json").read_text())
    tests = json.loads((FIXTURES / "tinysc.toy.tests.json").read_text())

    def run(host, shell_timeout_s, reply=lambda prompt: FakeResponse("working")):
        monkeypatch.setattr(loop, "run_llm", lambda _llm, prompt, _tools: reply(prompt))
        adapter = loop.HostAdapter(
            name=host, work_dir="/nowhere", notes="(notes)",
            resources={"some_token": 0.1}, baseline=lambda: {"per_trace": {}},
            run_gate=lambda baseline, port_plan, test_plan: gate.GateResult(True),
            shell_timeout_s=shell_timeout_s,
        )
        dump = _RealDumper(out_dir=tmp_path / "out")
        result = loop.integrate(dump, spec, host, "iso-192KiB",
                                port_plan=port, test_plan=tests, adapter=adapter)
        return result, shells[-1], dump

    return run


def test_default_gem5_adapter_checks_the_baseline_before_any_llm_turn(monkeypatch):
    fake = FakeGem5Adapter()
    monkeypatch.setattr(loop, "_gem5_adapter", lambda: fake)
    adapter = loop.default_adapter("gem5", "iso-64KiB")
    assert adapter.preflight == fake.check_baseline_current
    cbp = loop.HostAdapter(name="x", work_dir="/w", notes="", resources={},
                           baseline=lambda: {}, run_gate=lambda *a: None)
    assert cbp.preflight is None


def test_integrate_shell_uses_the_adapters_limit(integrate_run):
    result, shell, _ = integrate_run("gem5", C.GEM5_BASH_TOOL_TIMEOUT_S)
    assert result["status"] == "passed"
    assert shell["timeout_seconds"] == C.GEM5_BASH_TOOL_TIMEOUT_S
    assert shell["task_options"] == {"resources": {"some_token": 0.1}}


def test_integrate_shell_default_limit_is_unchanged(integrate_run):
    _, shell, _ = integrate_run("cbp2025", None)
    assert shell["timeout_seconds"] == C.BASH_TOOL_TIMEOUT_S


SHELL_NOTE = "## Shell limit"


def _prompt_of(integrate_run, host, shell_timeout_s):
    prompts = []

    def reply(prompt):
        prompts.append(prompt)
        return FakeResponse("working")

    integrate_run(host, shell_timeout_s, reply=reply)
    return prompts[0]


@pytest.mark.parametrize("shell_timeout_s", [None, C.BASH_TOOL_TIMEOUT_S])
def test_integrate_prompt_for_the_default_limit_is_the_prompt_file_as_it_was(
    integrate_run, shell_timeout_s
):
    """cbp2025 is producing the project's main result, so its integrator
    reads the prompt it read before gem5 existed: integrator.md with only
    the host filled in, then the plan sections, then the notes last."""
    prompt = _prompt_of(integrate_run, "cbp2025", shell_timeout_s)
    head = ((C.PROMPTS_DIR / "integrator.md").read_text()
            .replace("{{host_path}}", "/nowhere").replace("{{host_name}}", "cbp2025"))
    assert prompt.startswith(head + "\n\n## Port plan\n\n")
    assert prompt.endswith("\n\n## Host notes\n\n(notes)")
    assert SHELL_NOTE not in prompt
    assert "{{" not in head


def test_integrate_prompt_for_gem5_corrects_the_system_prompts_limit(integrate_run):
    prompt = _prompt_of(integrate_run, "gem5", C.GEM5_BASH_TOOL_TIMEOUT_S)
    assert prompt.endswith(
        f"\n\n## Host notes\n\n(notes)\n\n{SHELL_NOTE}\n\nThis host's shell allows "
        f"{C.GEM5_BASH_TOOL_TIMEOUT_S} seconds per command, not the "
        f"{C.BASH_TOOL_TIMEOUT_S} the system prompt names."
    )
    assert prompt.count(SHELL_NOTE) == 1


def test_the_prompt_files_state_the_default_limit():
    """system.md names 300 seconds for every agent, and integrator.md names
    no limit. The per-host correction is appended by the driver, so neither
    file carries a placeholder that a caller could forget to fill."""
    system = (C.PROMPTS_DIR / "system.md").read_text()
    assert "Each command is capped at 300 seconds." in system
    assert C.BASH_TOOL_TIMEOUT_S == 300
    assert "{{bash_timeout}}" not in system
    assert "{{bash_timeout}}" not in (C.PROMPTS_DIR / "integrator.md").read_text()


def test_shell_limit_note_only_for_a_limit_that_differs():
    assert loop.shell_limit_note(None) == ""
    assert loop.shell_limit_note(C.BASH_TOOL_TIMEOUT_S) == ""
    assert "allows 1200 seconds per command, not the 300" in loop.shell_limit_note(1200)


@pytest.mark.parametrize("host, variable", [
    ("gem5", "P2P_GEM5_PORT_FRESH=0"),
    ("cbp2025", "P2P_CBP2025_PORT_FRESH=0"),
])
def test_backend_failure_names_the_hosts_own_resume_variable(integrate_run, host, variable):
    """Naming cbp2025's variable on a gem5 run would make the resume start
    the gem5 port over, which deletes the tree it meant to keep."""
    def rate_limited(prompt):
        raise RuntimeError("RESOURCE_EXHAUSTED (code 429)")

    result, _, dump = integrate_run(host, None, reply=rate_limited)
    assert result["status"] == "backend_error"
    [record] = dump.dir.glob(f"*integrate_{host}_backend_error.json")
    assert variable in json.loads(record.read_text())["resume"]


# --------------------------------------------------------------- stage 2


@pytest.fixture
def planning(tmp_path, monkeypatch):
    """plan() with a stub shell and a recording make_plan."""
    state = SimpleNamespace(shells=[], tools=[], plans=[],
                            dump=_RealDumper(out_dir=tmp_path / "out"))

    def bash_tool(**kw):
        state.shells.append(kw)
        state.tools.append(_NullTool(**kw))
        return state.tools[-1]

    def make_plan(dump, spec, host, work_dir, notes, **kw):
        state.plans.append({"host": host, "work_dir": work_dir, "notes": notes, **kw})
        return {"hook_points": []}, {"correctness": []}

    monkeypatch.setattr(loop, "BashTool", bash_tool)
    monkeypatch.setattr(loop.plan_node, "make_plan", make_plan)
    monkeypatch.setattr(helpers, "load_baseline", lambda host, key: None)
    return state


def test_plan_gem5_restores_checks_the_mirror_and_widens_the_shell(
    gem5, planning, monkeypatch, capsys
):
    mirror = str(REPO / "third_party" / "gem5")
    monkeypatch.setattr(loop, "_mirror_revision",
                        lambda m: gem5.REVISION if m == mirror else "(wrong mirror)")
    loop.plan(planning.dump, {}, "gem5")

    assert planning.shells == [{
        "name": "gem5_bash", "work_dir": C.GEM5_ROOT,
        "timeout_seconds": C.GEM5_BASH_TOOL_TIMEOUT_S,
        "task_options": {"resources": {C.GEM5_HOST_RESOURCE: 0.1}},
    }]
    assert planning.tools[0].stopped
    [made] = planning.plans
    assert made["work_dir"] == C.GEM5_ROOT
    assert made["revision"] == gem5.REVISION
    assert made["checks_root"] == mirror
    assert made["host_storage_bits"] is None
    # planner.md fills its own limit from this. system.md still says 300,
    # so the notes, the prompt's last section, carry the correction.
    assert made["bash_timeout"] == C.GEM5_BASH_TOOL_TIMEOUT_S
    assert made["notes"] == loop.host_paths("gem5")[1] + loop.shell_limit_note(
        C.GEM5_BASH_TOOL_TIMEOUT_S)
    assert made["notes"].endswith(
        f"This host's shell allows {C.GEM5_BASH_TOOL_TIMEOUT_S} seconds per command, "
        f"not the {C.BASH_TOOL_TIMEOUT_S} the system prompt names.")
    # Restore before and after the planner, on the pristine root only.
    assert gem5.names() == ["restore_host_checkout", "checkout_revision",
                            "install_run_dir_on_cluster", "restore_host_checkout"]
    assert {c[1] for c in gem5.calls if c[0] == "restore_host_checkout"} == {C.GEM5_ROOT}
    assert list(planning.dump.dir.glob("*plan_gem5_checkout_restored.json"))
    out = capsys.readouterr().out
    assert "no host storage measurement for gem5" in out
    assert "statistical_corrector.cc:494" in out


def test_plan_gem5_refuses_a_mirror_at_another_commit(gem5, planning, monkeypatch):
    monkeypatch.setattr(loop, "_mirror_revision", lambda m: "0" * 40)
    with pytest.raises(SystemExit) as refused:
        loop.plan(planning.dump, {}, "gem5")
    message = str(refused.value)
    assert "mirror of the gem5 checkout" in message
    # The mirror is a shallow clone, so the fix fetches the commit by name.
    assert f"fetch --depth 1 origin {gem5.REVISION}" in message
    assert planning.shells == [] and planning.plans == []


@pytest.fixture
def cbp2025_checkout(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(loop.cbp2025_adapter, "restore_host_checkout",
                        lambda root=C.CBP2025_ROOT: calls.append(("restore", root)) or {"root": root})
    monkeypatch.setattr(loop.cbp2025_adapter, "checkout_revision",
                        lambda: calls.append(("revision",)) or "6074966")
    monkeypatch.setattr(loop.cbp2025_adapter, "host_storage_bits",
                        lambda root=C.CBP2025_ROOT: calls.append(("storage", root)) or 524615)
    return calls


def test_plan_cbp2025_is_unchanged(no_gem5, planning, cbp2025_checkout, monkeypatch, capsys):
    monkeypatch.setattr(loop, "_mirror_revision", lambda m: "6074966")
    loop.plan(planning.dump, {}, "cbp2025")

    assert cbp2025_checkout == [("restore", C.CBP2025_ROOT), ("revision",),
                                ("storage", C.CBP2025_ROOT), ("restore", C.CBP2025_ROOT)]
    assert planning.shells == [{
        "name": "cbp2025_bash", "work_dir": C.CBP2025_ROOT,
        "timeout_seconds": C.BASH_TOOL_TIMEOUT_S,
        "task_options": {"resources": {C.CBP2025_HOST_RESOURCE: 0.1}},
    }]
    [made] = planning.plans
    assert made["revision"] == "6074966"
    assert made["checks_root"] == str(REPO / "third_party" / "cbp2025")
    assert made["host_storage_bits"] == 524615
    # The notes as they are on disk, with nothing appended, and the planner
    # prompt's limit filled with the same "300" it always was.
    assert made["notes"] == loop.host_paths("cbp2025")[1]
    assert str(made["bash_timeout"]) == str(C.BASH_TOOL_TIMEOUT_S) == "300"
    assert list(planning.dump.dir.glob("*plan_cbp2025_checkout_restored.json"))
    out = capsys.readouterr().out
    assert "host storage by its own accounting: 524615 bits" in out
    assert "no host storage measurement" not in out


def test_cbp2025_mirror_refusal_text_is_unchanged(no_gem5, planning, cbp2025_checkout,
                                                  monkeypatch):
    """Word for word what the driver said before gem5 was wired in."""
    monkeypatch.setattr(loop, "_mirror_revision", lambda m: "abc1234")
    with pytest.raises(SystemExit) as refused:
        loop.plan(planning.dump, {}, "cbp2025")
    mirror = str(REPO / "third_party" / "cbp2025")
    revision = "6074966"
    assert str(refused.value) == (
        f"the head's mirror of the cbp2025 checkout ({mirror}) is at "
        f"abc1234, and the worker's ({C.CBP2025_ROOT}) is at {revision}. "
        f"The deterministic plan checks read the mirror, so they would "
        f"be about a different tree than the planner. Re-run "
        f"scripts/fetch_artifacts.sh, or `git -C {mirror} fetch && git "
        f"-C {mirror} checkout {revision}`."
    )


def test_plan_champsim_touches_no_checkout(no_gem5, planning, cbp2025_checkout, monkeypatch):
    monkeypatch.setattr(loop, "_mirror_revision",
                        lambda m: pytest.fail("champsim has no mirror to check"))
    loop.plan(planning.dump, {}, "champsim")
    assert cbp2025_checkout == []
    [made] = planning.plans
    assert made["revision"] is None and made["host_storage_bits"] is None
    assert planning.shells[0]["timeout_seconds"] == C.BASH_TOOL_TIMEOUT_S


# -------------------------------------------------------------- baseline


def test_baseline_lists_per_host():
    assert loop.baseline_list("cbp2025") == REPO / "experiments" / "smoke-2.list"
    assert loop.baseline_list("gem5") == C.GEM5_SMOKE_LIST
    assert loop.baseline_list("gem5", "/tmp/x.list") == Path("/tmp/x.list")
    assert loop.baseline_list("cbp2025", "/tmp/x.list") == Path("/tmp/x.list")


def test_gem5_baseline_goes_to_the_gem5_adapter(gem5, monkeypatch, tmp_path):
    monkeypatch.setattr(loop, "record_cbp_baseline",
                        lambda *a: pytest.fail("the cbp2025 recorder ran for gem5"))
    dump = _RealDumper(out_dir=tmp_path)
    result = loop.record_host_baseline(dump, "gem5", C.GEM5_SMOKE_LIST, "iso-64KiB")
    assert result == {"n": 2, "per_trace": {}}
    # The adapter's recorder restores, installs and builds on its own.
    assert gem5.calls == [("record_baseline", dump, C.GEM5_SMOKE_LIST, "iso-64KiB")]


def test_cbp2025_baseline_is_record_cbp_baseline(no_gem5, monkeypatch, tmp_path):
    recorded = []
    monkeypatch.setattr(loop, "record_cbp_baseline",
                        lambda *a: recorded.append(a) or {"n": 2})
    dump = _RealDumper(out_dir=tmp_path)
    smoke = REPO / "experiments" / "smoke-2.list"
    assert loop.record_host_baseline(dump, "cbp2025", smoke, "iso-192KiB") == {"n": 2}
    assert recorded == [(dump, smoke, "iso-192KiB")]


def test_a_host_without_a_recorder_is_refused(no_gem5, tmp_path):
    with pytest.raises(SystemExit, match="no recorder for champsim"):
        loop.record_host_baseline(_RealDumper(out_dir=tmp_path), "champsim",
                                  Path("x.list"), "iso-192KiB")


# ------------------------------------------------------------------ main


@pytest.fixture
def driver(tmp_path, monkeypatch):
    """main() with no cluster behind it. ray.init only counts, the spec is
    absent unless a test writes one, and the evidence lands in tmp."""
    state = SimpleNamespace(ray_init=0, cbp=[], out=tmp_path / "out",
                            spec=tmp_path / "spec.json")

    def ray_init(**kwargs):
        state.ray_init += 1

    monkeypatch.setattr(loop.ray, "init", ray_init)
    monkeypatch.setattr(loop, "start_collector", lambda: None)
    monkeypatch.setattr(helpers, "Dumper", lambda out_dir=None: _RealDumper(state.out))
    monkeypatch.setattr(C, "SPEC_OUT_PATH", state.spec)
    monkeypatch.setattr(C, "HOSTS", ("cbp2025",))
    monkeypatch.setattr(loop, "record_cbp_baseline",
                        lambda dump, trace_list, budget: state.cbp.append((trace_list, budget))
                        or {"n": 2})
    monkeypatch.setattr(dse, "check_llm",
                        lambda *a, **k: pytest.fail("the LLM check ran before a refusal"))

    def run(*argv):
        monkeypatch.setattr("sys.argv", ["adopt_a_paper_loop.py", *argv])
        loop.main()
        [summary] = state.out.glob("*summary.json")
        return json.loads(summary.read_text())

    state.run = run
    return state


def test_baseline_stage_gem5_uses_the_gem5_smoke_list(driver, gem5):
    summary = driver.run("--stage", "baseline", "--host", "gem5")
    assert gem5.calls[-1][0] == "record_baseline"
    assert gem5.calls[-1][2] == C.GEM5_SMOKE_LIST
    assert driver.cbp == []
    assert summary["gem5_baseline"] == {"n": 2, "per_trace": {}}
    assert "cbp2025_baseline" not in summary


def test_baseline_stage_cbp2025_is_unchanged(driver, no_gem5):
    summary = driver.run("--stage", "baseline", "--host", "cbp2025")
    assert driver.cbp == [(REPO / "experiments" / "smoke-2.list", "iso-192KiB")]
    assert summary["cbp2025_baseline"] == {"n": 2}


def test_baseline_stage_default_hosts_is_cbp2025(driver, no_gem5):
    summary = driver.run("--stage", "baseline")
    assert driver.cbp == [(REPO / "experiments" / "smoke-2.list", "iso-192KiB")]
    assert "gem5_baseline" not in summary


def test_baseline_stage_each_host_gets_its_own_default(driver, gem5, monkeypatch):
    monkeypatch.setattr(C, "HOSTS", ("cbp2025", "gem5"))
    summary = driver.run("--stage", "baseline", "--budget", "iso-64KiB")
    assert driver.cbp == [(REPO / "experiments" / "smoke-2.list", "iso-64KiB")]
    assert gem5.calls[-1][2:] == (C.GEM5_SMOKE_LIST, "iso-64KiB")
    assert {"cbp2025_baseline", "gem5_baseline"} <= set(summary)


def test_an_explicit_baseline_list_wins(driver, gem5, tmp_path):
    chosen = tmp_path / "gem5-perf.list"
    driver.run("--stage", "baseline", "--host", "gem5", "--baseline-list", str(chosen))
    assert gem5.calls[-1][2] == chosen


def test_baseline_stage_refuses_a_host_without_a_recorder_before_ray(driver, no_gem5):
    with pytest.raises(SystemExit, match="no recorder for champsim"):
        driver.run("--stage", "baseline", "--host", "champsim")
    assert driver.ray_init == 0


@pytest.mark.parametrize("argv", [
    ["--stage", "dse", "--host", "gem5"],
    ["--stage", "promote", "--host", "gem5", "--promote-from", "out/x_summary.json"],
    ["--stage", "plan", "integrate", "dse", "--host", "gem5"],
    ["--stage", "all", "--host", "gem5"],
])
def test_dse_and_promote_refuse_gem5_before_any_work(driver, gem5, argv):
    with pytest.raises(SystemExit, match="CBP2025 kit"):
        driver.run(*argv)
    assert driver.ray_init == 0
    assert gem5.calls == []


def test_dse_refuses_gem5_among_the_default_hosts(driver, gem5, monkeypatch):
    monkeypatch.setattr(C, "HOSTS", ("cbp2025", "gem5"))
    with pytest.raises(SystemExit, match="cannot search gem5"):
        driver.run("--stage", "dse")
    assert driver.ray_init == 0


def test_dse_for_cbp2025_passes_the_refusal(driver, no_gem5, monkeypatch):
    def reached(**kwargs):
        raise _ReachedCluster
    monkeypatch.setattr(loop.ray, "init", reached)
    with pytest.raises(_ReachedCluster):
        driver.run("--stage", "dse", "--host", "cbp2025")


def _write_spec(driver):
    driver.spec.write_text(json.dumps({"feature_name": "sr"}))


def test_integrate_stage_saves_the_gem5_port_diff(driver, gem5, monkeypatch):
    _write_spec(driver)
    monkeypatch.setattr(loop, "load_plans", lambda host, spec: ({}, {}))
    monkeypatch.setattr(loop, "integrate",
                        lambda dump, spec, h, budget, **kw: {"host": h, "status": "failed"})
    driver.run("--stage", "integrate", "--host", "gem5")
    [patch] = driver.out.glob("*integrate_gem5_diff.patch")
    assert patch.read_text() == "--- patch ---\n+gem5 port\n"


def test_integrate_stage_saves_the_cbp2025_port_diff(driver, no_gem5, monkeypatch):
    _write_spec(driver)
    monkeypatch.setattr(loop, "load_plans", lambda host, spec: ({}, {}))
    monkeypatch.setattr(loop, "integrate",
                        lambda dump, spec, h, budget, **kw: {"host": h, "status": "failed"})
    monkeypatch.setattr(loop.cbp2025_adapter, "port_diff", lambda: "cbp2025 diff")
    driver.run("--stage", "integrate", "--host", "cbp2025")
    [patch] = driver.out.glob("*integrate_cbp2025_diff.patch")
    assert patch.read_text() == "cbp2025 diff"


def test_integrate_stage_writes_no_diff_for_a_host_without_a_port_tree(
    driver, no_gem5, monkeypatch
):
    _write_spec(driver)
    monkeypatch.setattr(loop, "load_plans", lambda host, spec: ({}, {}))
    monkeypatch.setattr(loop, "integrate",
                        lambda dump, spec, h, budget, **kw: {"host": h, "status": "failed"})
    driver.run("--stage", "integrate", "--host", "champsim")
    assert not list(driver.out.glob("*_diff.patch"))


# ---------------------------------------------------- the dse.py refusal


@pytest.mark.parametrize("host", ["gem5", "champsim"])
def test_require_searchable_refuses_every_host_but_cbp2025(host):
    with pytest.raises(SystemExit) as refused:
        dse.require_searchable(host)
    message = str(refused.value)
    assert f"cannot search {host}" in message
    assert "silently search the CBP2025 kit" in message


def test_require_searchable_lets_cbp2025_through():
    assert dse.require_searchable("cbp2025") is None


def test_run_dse_refuses_gem5_before_it_imports_the_evolver(monkeypatch):
    """So the refusal reads the same whether or not evolve-flows is
    installed, and no build is ever dispatched."""
    monkeypatch.setattr(dse, "_evolver_imports",
                        lambda: pytest.fail("run_dse got past the refusal"))
    with pytest.raises(SystemExit, match="CBP2025 kit"):
        dse.run_dse("gem5", {}, "iso-192KiB", "unused.yaml")


def test_promote_finalists_refuses_gem5_before_anything(monkeypatch):
    """Before the trace list, the plan, and the reset of the pristine
    CBP2025 checkout that a gem5 promotion has no business touching."""
    monkeypatch.setattr(dse.helpers, "load_trace_list",
                        lambda path: pytest.fail("promote_finalists got past the refusal"))
    monkeypatch.setattr(dse, "_port_plan",
                        lambda host, spec: pytest.fail("promote_finalists got past the refusal"))
    with pytest.raises(SystemExit, match="CBP2025 kit"):
        dse.promote_finalists("gem5", {}, "iso-192KiB", [])
