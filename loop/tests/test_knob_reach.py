"""G6, and the operator's pin: proving a knob reaches the build, and saying
so when the port is known not to.

Run 20260924_102657 is the case behind both. Its port passed G1 to G5 with
all 19 host knobs wired to nothing -- a debug turn restored the host file
with `git checkout` and never re-applied them -- and with two storage-costed
sR knobs no source file read. With every knob at its default a wired and an
unwired port build the same binary, so no condition before G6 can see this.
Stage 4's preflight saw it, after stage 3 had passed.

The builds here are fakes that ignore the macros a test names, the way an
unwired port does. dse.preflight, gate.check_knob_reach and dse.pin_knobs
are the real code.
"""

import json
import re
from pathlib import Path

import pytest

import constraints as K
import dse
import gate

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def spec():
    return json.loads((REPO / "spec" / "sr.paper_only.json").read_text())


@pytest.fixture
def host():
    doc = json.loads((FIXTURES / "cbp2025.host_knobs.json").read_text())
    return {"host_knobs": doc["host_knobs"], "host_storage": doc["host_storage"]}


def _fake_build(inert: set):
    """A build whose binary ignores the macros in `inert`."""
    def build(header):
        values, _ = K.parse_header(header)
        return json.dumps({m: v for m, v in values.items() if m not in inert},
                          sort_keys=True).encode()
    return build


def _sized_feature_knob(spec):
    """A numeric feature knob some size_formula reads, found rather than
    named: the distiller renames knobs from run to run."""
    sized = " ".join(str(e.get("size_formula", "")) for e in spec["state"])
    for knob in K.feature_knobs(spec):
        if (re.search(rf"\b{re.escape(knob.name)}\b", sized)
                and K.alternate_value(knob) is not None and knob.type != "bool"):
            return knob
    pytest.skip("the current spec declares no numeric knob a size_formula reads")


# ------------------------------------------------------------------ G6


def test_g6_fails_the_gate_once_per_inert_storage_knob():
    report = {"blocking": ["HOST_LOGG = 9 builds the same binary as 10: nothing reads it",
                           "HOST_LOGB = 12 builds the same binary as 13: nothing reads it"],
              "warnings": ["SR_VARIANT = 1 builds the same binary as 0: nothing reads it"]}
    before = gate.GateResult(True, measurements=[{"id": "perf"}])
    after = gate.check_knob_reach(before, report)
    assert not after.passed
    assert after.reasons == [f"G6 {b}" for b in report["blocking"]]
    assert after.warnings == [f"G6 {report['warnings'][0]}"]
    # What G5 measured survives G6, so a port failing only G6 still records it.
    assert after.measurements == before.measurements


def test_an_inert_knob_that_costs_nothing_does_not_fail_g6():
    report = {"blocking": [], "warnings": ["SR_VARIANT = 1 builds the same binary as 0"]}
    after = gate.check_knob_reach(gate.GateResult(True), report)
    assert after.passed and after.reasons == [] and len(after.warnings) == 1


def test_a_host_without_g6_keeps_its_verdict():
    before = gate.GateResult(True)
    assert gate.check_knob_reach(before, None) is before


def test_g6_names_every_host_knob_of_a_port_that_wired_none(spec, host):
    """The shape of run 20260924_102657: the feature wired, the host not."""
    unwired = {k.macro for k in K.host_knobs(host)}
    report = dse.preflight(_fake_build(unwired), spec, host, dse.params_header(spec, host))
    after = gate.check_knob_reach(gate.GateResult(True), report)
    costed = {k["macro"] for k in report["knobs"]
              if k["origin"] == "host" and k["costs_storage"]}
    assert costed and not after.passed
    assert {r.split()[1] for r in after.reasons} == costed


def test_g6_passes_a_port_that_wired_everything(spec, host):
    report = dse.preflight(_fake_build(set()), spec, host, dse.params_header(spec, host))
    assert gate.check_knob_reach(gate.GateResult(True), report).passed


# ------------------------------------------------------------------ pins


def test_a_pinned_knob_is_skipped_by_the_preflight_instead_of_blocking(spec, host):
    knob = _sized_feature_knob(spec)
    unpinned = dse.preflight(_fake_build({knob.macro}), spec, host,
                             dse.params_header(spec, host))
    assert any(b.startswith(knob.macro + " ") for b in unpinned["blocking"])

    spec2, host2, _ = dse.pin_knobs(spec, host, [knob.macro])
    pinned = dse.preflight(_fake_build({knob.macro}), spec2, host2,
                           dse.params_header(spec2, host2))
    assert pinned["blocking"] == []
    assert next(k for k in pinned["knobs"] if k["macro"] == knob.macro)["result"] == "pinned"


def test_a_pinned_knob_cannot_move_and_is_still_charged_at_its_default(spec, host):
    """The pin must not become a way to save storage. The search cannot
    propose another value, and the default's bits stay in the total."""
    knob = _sized_feature_knob(spec)
    spec2, host2, _ = dse.pin_knobs(spec, host, [knob.macro])
    storage = [K.storage_constraint("ample", 10 ** 9)]
    moved = dse.params_header(spec2, host2, {knob.name: K.alternate_value(knob)})
    assert not K.check_static(moved, spec2, host2, storage).ok
    charged = K.check_static(dse.params_header(spec2, host2), spec2, host2, storage)
    unpinned = K.check_static(dse.params_header(spec, host), spec, host, storage)
    assert charged.ok and charged.metrics == unpinned.metrics


def test_pinning_copies_and_records_every_pin(spec, host):
    knob = _sized_feature_knob(spec)
    spec_before, host_before = json.dumps(spec), json.dumps(host)
    _, host2, pinned = dse.pin_knobs(spec, host, [knob.macro, "HOST_LOGG"])
    assert json.dumps(spec) == spec_before and json.dumps(host) == host_before
    assert [p["macro"] for p in pinned] == [knob.macro, "HOST_LOGG"]
    logg = next(k for k in host2["host_knobs"] if k["name"].upper() == "LOGG")
    assert logg["range"] == f"[{logg['default']}, {logg['default']}]"


def test_a_pin_on_a_name_that_is_no_knob_is_refused(spec, host):
    """A typo in P2P_DSE_PIN must not silently pin nothing."""
    with pytest.raises(SystemExit, match="SR_NO_SUCH_KNOB"):
        dse.pin_knobs(spec, host, ["SR_NO_SUCH_KNOB"])


def test_no_pins_leaves_both_documents_alone(spec, host):
    spec2, host2, pinned = dse.pin_knobs(spec, host, ())
    assert spec2 is spec and host2 is host and pinned == []
