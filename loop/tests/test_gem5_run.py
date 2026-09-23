"""Unit tests for the gem5 run scripts (hosts/gem5/run/).

No gem5 here. p2p_metrics is pure Python and is tested directly, on made-up
dumps and on a real stats.txt from the first cluster run
(fixtures/gem5/stats_gapbs_bfs_s.txt, see the README next to it).
run_workload.py is run as a subprocess against a fake gem5: a small script
that records how it was called, writes a stats.txt and prints a P2P_EXIT
line. se_o3.py imports m5, so only its argument handling and exit mapping
are tested, with a stub m5 package. A fake is never evidence that the host
works. These tests pin the logic that decides a verdict and fails quietly:

  - a metric computed from a missing stat reads as a measurement,
  - a rounded P2P_METRIC value fails G2 at rel_tol 0,
  - a stats grammar that drops the pdf rows loses the only conditional-only
    misprediction count, and cond_mpki silently becomes branch_mpki (what
    the first cluster run showed on all 28 workloads),
  - a grammar that reads a line chia reads, but with another value, makes
    the two parsers disagree on the same stats.txt,
  - a guest argv built differently from adapter.resolve moves the guest's
    stack, so the shell run and the baseline measure different programs.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

from hosts.gem5.run import p2p_metrics as M

RUN_DIR_SRC = Path(__file__).resolve().parents[2] / "hosts" / "gem5" / "run"
RUN_WORKLOAD = RUN_DIR_SRC / "run_workload.py"
SE_O3 = RUN_DIR_SRC / "se_o3.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gem5" / "stats_gapbs_bfs_s.txt"

BP = "system.cpu.branchPred"
BEGIN = "\n---------- Begin Simulation Statistics ----------\n"
END = "\n\n---------- End Simulation Statistics   ----------\n"


# ------------------------------------------------------------ stats.txt


def gem5_line(name, value, pdf=None, cdf=None, desc="d", unit="Count"):
    """One stats.txt row as gem5's ScalarPrint writes it with spaces on
    (src/base/stats/text.cc:286-317): name in 40, value in 12, then pdf and
    cdf in 10 each (blank when NaN), then the description and unit."""
    pdf_s = "" if pdf is None else f"{pdf:.2f}%"
    cdf_s = "" if cdf is None else f"{cdf:.2f}%"
    return f"{name:<40} {value:>12} {pdf_s:>10} {cdf_s:>10} # {desc} ({unit})"


def stats_block(insts, cycles, direct, other, cond_predicted, extra=()):
    """One dump in gem5 v25.1's layout. `direct` committed conditional
    mispredictions plus `other` mispredicted returns. condIncorrect and
    mispredicted_0::total both count all of them, as gem5 v25.1 does. The
    per-type rows carry pdf and cdf columns, blank when the vector is all
    zero (text.cc:360-361)."""
    total = direct + other

    def pct(n):
        return 100.0 * n / total if total else None

    rows = [
        gem5_line("simSeconds", "0.000100", unit="Second"),
        gem5_line("simInsts", str(insts)),
        gem5_line("system.cpu.numCycles", str(cycles), unit="Cycle"),
        gem5_line("system.cpu.ipc", "nan"),
        gem5_line("system.cpu.commitStats0.numInsts", str(insts)),
        gem5_line("system.cpu.commitStats0.committedControl::IsCondControl", "900"),
        gem5_line(f"{BP}.committed_0::DirectCond", "900", 75.0, 75.0),
        gem5_line(f"{BP}.committed_0::Return", "300", 25.0, 100.0),
        gem5_line(f"{BP}.committed_0::total", "1200"),
        gem5_line(f"{BP}.mispredicted_0::DirectCond", str(direct), pct(direct), pct(direct)),
        gem5_line(f"{BP}.mispredicted_0::IndirectCond", "0", pct(0), pct(direct)),
        gem5_line(f"{BP}.mispredicted_0::Return", str(other), pct(other), pct(total)),
        gem5_line(f"{BP}.mispredicted_0::total", str(total)),
        gem5_line(f"{BP}.condPredicted", str(cond_predicted)),
        gem5_line(f"{BP}.condIncorrect", str(total)),
        *extra,
    ]
    return BEGIN + "\n".join(rows) + END


# 10 conditional and 2 return mispredictions in 4000 instructions and 8000
# cycles: cond_mpki 2.5, branch_mpki 3.0, ipc 0.5.
STD = stats_block(4000, 8000, 10, 2, 1500)
STD_METRICS = {"cond_mpki": 2.5, "branch_mpki": 3.0, "ipc": 0.5}
TWO_DUMPS = stats_block(10, 20, 1, 0, 5) + STD


def test_parse_stats_file_reads_the_last_complete_dump(tmp_path):
    # A third block with no End marker is what a gem5 killed mid-dump
    # leaves. It must not be read.
    torn = BEGIN + gem5_line("system.cpu.numCycles", "1") + "\n"
    path = tmp_path / "stats.txt"
    path.write_text(TWO_DUMPS + torn)
    stats = M.parse_stats_file(path)
    assert stats == {
        "cycles": 8000.0,
        "insts": 4000.0,
        "cond_predicted": 1500.0,
        "cond_incorrect": 12.0,
        "committed_branch_mispredicts": 12.0,
        "cond_mispredicts_direct": 10.0,
        "cond_mispredicts_indirect": 0.0,
        "committed_branches": 1200.0,
        "committed_cond_direct": 900.0,
        "committed_cond_branches": 900.0,
    }
    assert M.derive(stats) == STD_METRICS


def test_parse_stats_text_reads_pdf_rows_and_skips_nan():
    raw = M.parse_stats_text(TWO_DUMPS)
    assert raw[f"{BP}.mispredicted_0::DirectCond"] == 10.0
    assert raw[f"{BP}.mispredicted_0::Return"] == 2.0
    assert raw[f"{BP}.mispredicted_0::total"] == 12.0
    # A NaN value is not a number anybody measured. chia skips it too.
    assert "system.cpu.ipc" not in raw


def test_an_all_zero_vector_still_reads_as_zero():
    """With no mispredictions gem5 prints the pdf and cdf as blank padding
    (text.cc:294-298, 360-361). The rows must still read, as 0, so a
    perfect run gives cond_mpki 0 and not a missing metric."""
    stats = M.select(M.parse_stats_text(stats_block(4000, 8000, 0, 0, 1500)))
    assert stats["cond_mispredicts_direct"] == 0.0
    assert stats["cond_mispredicts_indirect"] == 0.0
    assert M.derive(stats) == {"cond_mpki": 0.0, "branch_mpki": 0.0, "ipc": 0.5}


def test_parse_stats_file_missing_or_empty(tmp_path):
    assert M.parse_stats_file(tmp_path / "nope.txt") == {}
    (tmp_path / "empty.txt").write_text("")
    assert M.parse_stats_file(tmp_path / "empty.txt") == {}


def test_insts_falls_back_to_siminsts():
    text = STD.replace("system.cpu.commitStats0.numInsts", "system.cpu.commitStats0.renamed")
    assert M.select(M.parse_stats_text(text))["insts"] == 4000.0


def test_stats_keys_cover_the_required_names():
    for logical in ("cycles", "insts", "cond_predicted", "cond_incorrect",
                    "committed_branch_mispredicts", "cond_mispredicts_direct",
                    "cond_mispredicts_indirect"):
        assert M.STATS_KEYS[logical], logical
    # chia's run_gem5 reports parse_failed without this one.
    assert M.STATS_KEYS["cycles"][0] == "system.cpu.numCycles"
    assert M.STATS_KEYS["cond_mispredicts_direct"] == [f"{BP}.mispredicted_0::DirectCond"]
    assert M.STATS_KEYS["cond_mispredicts_indirect"] == [f"{BP}.mispredicted_0::IndirectCond"]


# ---------------------------------------------- the line grammar


def one_line(line):
    """The raw dict of a dump holding just `line`."""
    return M.parse_stats_text(BEGIN + line + END)


@pytest.mark.parametrize("line, value", [
    # No percentage column: a scalar, and a vector's ::total row.
    ("a.b                    2509944                       # d (Count)", 2509944.0),
    # One column: what a row with a NaN cdf, or spaces off, can look like.
    ("a.b::X 12 97.29% # d (Count)", 12.0),
    ("a.b::X 12 97.29%", 12.0),
    # Two columns, as gem5 prints every pdf row.
    ("a.b::X        34742     97.29%     99.12% # d (Count)", 34742.0),
    ("a.b::X 0 0.00% 100.00%", 0.0),
    # nan% and inf% columns. gem5 prints blanks for a NaN pdf, so these
    # are a guard, but the value is still read.
    ("a.b::X 0 nan% nan% # d", 0.0),
    ("a.b::X 0 nan% # d", 0.0),
    ("a.b::X 3 inf% -inf% # d", 3.0),
    # Value forms chia's number pattern takes.
    ("a.b 1.029471 # d", 1.029471),
    ("a.b 1.5e3 0.00% 100.00%", 1500.0),
    ("a.b -.5 # d", -0.5),
    ("a.b 7#d", 7.0),
    # gem5's own layout, with the pdf blank and the cdf present.
    (gem5_line("a.b::X", "5", None, 50.0), 5.0),
])
def test_grammar_reads_zero_one_or_two_percentage_columns(line, value):
    name = line.split()[0]
    assert one_line(line) == {name: value}


@pytest.mark.parametrize("line", [
    # A real row from the same run (system.cpu.dcache): a NaN value.
    "system.cpu.dcache.avgBlocked::no_wbuffers          nan                  "
    "     # average number of cycles each access was blocked ((Cycle/Count))",
    "a.b::X 1 2.00% 3.00% 4.00% # three columns",
    "a.b::X 1 2 # a second number with no percent sign",
    "a.b::X 1 2.00%3.00% # no space between the columns",
    "a.b 1 junk",
    "a.b nan% # no value",
])
def test_grammar_rejects_what_is_not_a_stat_row(line):
    assert one_line(line) == {}


# ---------------------------------------- a real stats.txt from the node

# The fixture's numbers, read off the file (fixtures/gem5/README.txt).
REAL_INSTS = 2509944        # system.cpu.commitStats0.numInsts
REAL_SIM_INSTS = 2509105    # simInsts: no NOPs, so it differs
REAL_CYCLES = 2583914       # system.cpu.numCycles
REAL_DIRECT = 34742         # mispredicted_0::DirectCond
REAL_TOTAL = 35711          # mispredicted_0::total, and condIncorrect


def real_text():
    return FIXTURE.read_text()


def test_real_stats_find_every_stats_key_by_its_first_name():
    """Every name in STATS_KEYS is one gem5 v25.1 really prints for this
    config, not only the fallbacks."""
    raw = M.parse_stats_text(real_text())
    for logical, candidates in M.STATS_KEYS.items():
        assert candidates[0] in raw, (logical, candidates[0])
    stats = M.parse_stats_file(FIXTURE)
    assert set(stats) == set(M.STATS_KEYS)
    assert stats["insts"] == REAL_INSTS
    assert raw["simInsts"] == REAL_SIM_INSTS
    assert stats["cycles"] == REAL_CYCLES
    assert stats["cond_mispredicts_direct"] == REAL_DIRECT
    assert stats["cond_mispredicts_indirect"] == 0.0
    assert stats["committed_branch_mispredicts"] == REAL_TOTAL
    assert stats["cond_incorrect"] == REAL_TOTAL
    assert stats["committed_cond_direct"] == stats["committed_cond_branches"] == 517717


def test_real_stats_every_row_reads():
    """Every line between the markers is a stat row, and each one reads:
    scalars, vector rows with two percentage columns, and distributions."""
    body = [ln for ln in real_text().splitlines()
            if ln.strip() and "Simulation Statistics" not in ln]
    assert len(body) == 470
    assert len(M.parse_stats_text(real_text())) == len(body)


def test_real_stats_derive():
    metrics = M.derive(M.parse_stats_file(FIXTURE))
    assert metrics["cond_mpki"] == 1000.0 * REAL_DIRECT / REAL_INSTS
    assert metrics["branch_mpki"] == 1000.0 * REAL_TOTAL / REAL_INSTS
    assert metrics["ipc"] == REAL_INSTS / REAL_CYCLES
    # The whole point of the new keys: returns, calls and indirect jumps
    # were mispredicted too, so the conditional rate is the smaller one.
    assert metrics["cond_mpki"] < metrics["branch_mpki"]
    # What the cluster smoke table printed for this run.
    assert round(metrics["branch_mpki"], 4) == 14.2278
    assert round(metrics["ipc"], 4) == 0.9714


def test_grammar_reads_everything_chias_reads():
    """For every line chia's grammar matches, ours matches with the same
    name and the same value. With zero percentage columns the two patterns
    are the same, so this must hold on any stats.txt. It is checked here
    over a real one, plus the made-up rows above."""
    gem5 = pytest.importorskip("chia.simulators.gem5")
    lines = real_text().splitlines() + TWO_DUMPS.splitlines() + [
        "a.b 1.5e3 # d", "a.b -.5", "a.b 7#d", "a.b nan # d"]
    matched = 0
    for line in lines:
        theirs = gem5._STATS_NUMBER_RE.match(line)
        if not theirs:
            continue
        ours = M._STATS_NUMBER_RE.match(line)
        assert ours, line
        assert ours.group(1, 2) == theirs.group(1, 2), line
        matched += 1
    assert matched >= 170  # the fixture's rows without percentage columns
    # The same through both whole parsers: every logical stat chia finds,
    # ours finds with the same value. Ours finds the pdf rows on top, and
    # those are exactly the keys chia cannot read.
    for text in (real_text(), TWO_DUMPS):
        theirs = gem5.Gem5Node.parse_gem5_stats(text, M.STATS_KEYS, "last")
        ours = M.select(M.parse_stats_text(text))
        assert {k: ours[k] for k in theirs} == theirs
        assert set(ours) - set(theirs) == {
            "cond_mispredicts_direct", "cond_mispredicts_indirect",
            "committed_cond_direct"}


# ------------------------------------------------------------- derive

FULL = {"insts": 4000.0, "cycles": 8000.0, "cond_mispredicts_direct": 10.0,
        "cond_mispredicts_indirect": 0.0, "committed_branch_mispredicts": 12.0,
        "cond_incorrect": 12.0}


def test_derive_full_inputs():
    assert M.derive(FULL) == STD_METRICS
    # IndirectCond counts toward cond_mpki when a target ISA has one.
    assert M.derive({**FULL, "cond_mispredicts_indirect": 2.0})["cond_mpki"] == 3.0


def test_cond_mpki_never_falls_back_to_cond_incorrect():
    """condIncorrect counts every branch type in gem5 v25.1. A cond_mpki
    built from it is branch_mpki under another name."""
    stats = {k: v for k, v in FULL.items() if k != "cond_mispredicts_direct"}
    assert "cond_mpki" not in M.derive(stats)
    assert M.derive(stats)["branch_mpki"] == 3.0


@pytest.mark.parametrize("drop, gone", [
    ("insts", {"cond_mpki", "branch_mpki", "ipc"}),
    ("cycles", {"ipc"}),
    ("cond_mispredicts_direct", {"cond_mpki"}),
    ("cond_mispredicts_indirect", {"cond_mpki"}),
    ("committed_branch_mispredicts", {"branch_mpki"}),
])
def test_derive_leaves_out_a_metric_whose_input_is_missing(drop, gone):
    stats = dict(FULL)
    del stats[drop]
    out = M.derive(stats)
    assert set(out) == set(M.METRIC_KEYS) - gone
    assert all(v != 0 for v in out.values())


def test_derive_zero_denominators_and_junk():
    assert M.derive({}) == {}
    assert M.derive({"insts": 0.0, "cycles": 0.0, "cond_mispredicts_direct": 1.0,
                     "cond_mispredicts_indirect": 0.0,
                     "committed_branch_mispredicts": 1.0}) == {}
    assert M.derive({"insts": "x", "cycles": 10, "cond_mispredicts_direct": None,
                     "cond_mispredicts_indirect": 0.0}) == {}
    assert M.derive({"insts": float("nan"), "cycles": 10.0}) == {}
    # Zero mispredicts is a real measurement, and it stays.
    assert M.derive({"insts": 10.0, "cycles": 5.0, "cond_mispredicts_direct": 0.0,
                     "cond_mispredicts_indirect": 0.0,
                     "committed_branch_mispredicts": 0.0}) == {
        "cond_mpki": 0.0, "branch_mpki": 0.0, "ipc": 2.0}


def test_metric_names_and_directions():
    assert M.METRIC_KEYS == ("cond_mpki", "branch_mpki", "ipc")
    assert M.DIRECTIONS == {"cond_mpki": "decrease", "branch_mpki": "decrease",
                            "ipc": "increase"}


# ---------------------------------------------------------- aggregate


def test_aggregate_is_a_mean_over_runs_that_have_the_metric():
    runs = [{"cond_mpki": 1.0, "ipc": 1.0}, {"cond_mpki": 3.0}, {},
            {"cond_mpki": 5.0, "ipc": 2.0, "extra": 7.0}]
    assert M.aggregate(runs) == {"cond_mpki": 3.0, "ipc": 1.5, "extra": 7.0}
    assert list(M.aggregate(runs)) == ["cond_mpki", "ipc", "extra"]
    assert M.aggregate([]) == {}


def test_aggregate_does_not_depend_on_run_order():
    values = [0.1, 1e16, 0.3, -1e16, 0.7, 1.0 / 3.0]
    runs = [{"ipc": v} for v in values]
    forward = M.aggregate(runs)["ipc"]
    assert M.aggregate(list(reversed(runs)))["ipc"] == forward
    assert forward == math.fsum(values) / len(values)


# ------------------------------------------------------- metric lines


def test_metric_lines_round_trip_at_full_precision():
    metrics = {"ipc": 1.0 / 3.0, "branch_mpki": 0.1 + 0.2,
               "cond_mpki": 2.718281828459045e-300, "z_extra": 123456789.00000001}
    text = M.format_metric_lines(metrics)
    lines = text.splitlines()
    assert [ln.split()[1] for ln in lines] == ["cond_mpki", "branch_mpki", "ipc", "z_extra"]
    back = M.parse_metric_lines("noise\n" + text + "\nP2P_STATUS ok\n")
    assert back == {k: float(v) for k, v in metrics.items()}
    for k, v in metrics.items():
        assert back[k] == v  # bit-identical, not approximately


def test_format_skips_missing_values_and_parse_keeps_last():
    assert M.format_metric_lines({"ipc": None, "cond_mpki": float("inf")}) == ""
    text = "P2P_METRIC ipc 1.5\nP2P_METRIC ipc 2.5\nP2P_METRIC ipc oops\n  P2P_METRIC x 1"
    assert M.parse_metric_lines(text) == {"ipc": 2.5}


# --------------------------------------------------- run_workload.py

FAKE_GEM5 = textwrap.dedent('''\
    #!{python}
    """A stand-in for gem5.opt: records its call, writes a stats.txt."""
    import json, os, shutil, sys, time
    argv = sys.argv[1:]
    outdir = next(a.split("=", 1)[1] for a in argv if a.startswith("--outdir="))
    mode = os.environ.get("FAKE_GEM5_MODE", "ok")
    with open(os.path.join(outdir, "fake_call.json"), "w") as f:
        json.dump({{"argv": sys.argv, "cwd": os.getcwd(),
                    "knob": os.environ.get("SR_FAKE_KNOB")}}, f)
    if mode == "sleep":
        time.sleep(30)
    if "--redirect-stderr" in argv:
        with open(os.path.join(outdir, "simerr.txt"), "w") as f:
            f.write("warn: fake gem5\\n" + ("fatal: boom\\n" if mode == "crash" else ""))
    if mode != "no_stats" and mode != "crash":
        if os.environ.get("FAKE_STATS_FILE"):
            shutil.copy(os.environ["FAKE_STATS_FILE"], os.path.join(outdir, "stats.txt"))
        else:
            with open(os.path.join(outdir, "stats.txt"), "w") as f:
                f.write(os.environ["FAKE_STATS"])
    code = int(os.environ.get("FAKE_GUEST_CODE", "0"))
    if mode == "crash":
        sys.exit(1)
    if mode != "no_exit_line":
        print("P2P_EXIT cause=exiting with last active thread context code=%d" % code)
    sys.exit(code)
''')


@pytest.fixture
def run_dir(tmp_path):
    """An installed run dir: se_o3.py, workloads.json and the payload."""
    rd = tmp_path / "p2p_gem5"
    (rd / "workloads" / "bin").mkdir(parents=True)
    (rd / "workloads" / "data" / "foo").mkdir(parents=True)
    (rd / "workloads" / "bin" / "foo").write_text("not really an ELF")
    (rd / "workloads" / "bin" / "bar").write_text("not really an ELF")
    (rd / "se_o3.py").write_text("# the real one is never run here\n")
    manifest = {"schema": 1, "root": "workloads", "workloads": {
        "foo": {"binary": "bin/foo", "args": ["-g", "10", "-n", "a b", 3],
                "cwd": "data/foo", "max_insts": 5000, "approx_insts": None,
                "suite": "t", "description": "t", "license": "t", "source": "t"},
        "bar": {"binary": "bin/bar", "args": ["-q"], "cwd": None,
                "max_insts": None, "approx_insts": None, "suite": "t",
                "description": "t", "license": "t", "source": "t"},
    }}
    (rd / "workloads.json").write_text(json.dumps(manifest))
    return rd


@pytest.fixture
def fake_gem5(tmp_path):
    path = tmp_path / "gem5.opt"
    path.write_text(FAKE_GEM5.format(python=sys.executable))
    path.chmod(0o755)
    return path


def run(args, env_extra=None, script=RUN_WORKLOAD, drop=(), cwd=None):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("P2P_GEM5_", "FAKE_", "SR_FAKE"))}
    # The fake gem5 writes the mispredicted_0 rows, so a good run derives
    # every metric, cond_mpki included.
    env["FAKE_STATS"] = STD
    env.update(env_extra or {})
    for k in drop:
        env.pop(k, None)
    proc = subprocess.run([sys.executable, str(script), *args], capture_output=True,
                          text=True, env=env, timeout=60, cwd=cwd)
    return proc.returncode, proc.stdout + proc.stderr


def call_record(output):
    run_line = next(ln for ln in output.splitlines() if ln.startswith("P2P_RUN "))
    outdir = json.loads(run_line[len("P2P_RUN "):])["outdir"]
    return outdir, json.loads((Path(outdir) / "fake_call.json").read_text())


def test_ok_run_prints_the_lines_in_order_and_exits_0(run_dir, fake_gem5):
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir), "foo"])
    assert rc == 0, out
    lines = out.splitlines()
    assert lines[0] == "P2P_WORKLOAD foo"
    assert lines[-1] == "P2P_STATUS ok"
    metric_idx = [i for i, ln in enumerate(lines) if ln.startswith("P2P_METRIC ")]
    assert metric_idx == list(range(metric_idx[0], metric_idx[0] + 3))
    assert M.parse_metric_lines(out) == STD_METRICS
    assert "P2P_STAT insts 4000.0" in lines
    assert "P2P_STAT cond_mispredicts_direct 10.0" in lines


def test_real_stats_through_the_shell_path(run_dir, fake_gem5):
    """The shell path prints, to the last bit, what the adapter's path
    derives from the same real stats.txt (select over parse_stats_text of
    the captured text). G2 compares the two at rel_tol 0."""
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir), "foo"],
                  {"FAKE_STATS_FILE": str(FIXTURE)})
    assert rc == 0, out
    adapter_side = M.derive(M.select(M.parse_stats_text(FIXTURE.read_text())))
    assert set(adapter_side) == set(M.METRIC_KEYS)
    assert M.parse_metric_lines(out) == adapter_side
    assert f"P2P_METRIC cond_mpki {1000.0 * REAL_DIRECT / REAL_INSTS!r}" in out.splitlines()


@pytest.mark.parametrize("given", ["./gem5.opt", "gem5.opt"])
def test_a_relative_gem5_path_works(run_dir, fake_gem5, given):
    """gem5 runs with the outdir as its cwd. A relative --gem5 must still
    name the binary relative to the caller's cwd, not the outdir's."""
    rc, out = run(["--gem5", given, "--run-dir", str(run_dir), "foo"],
                  cwd=fake_gem5.parent)
    assert rc == 0, out
    outdir, call = call_record(out)
    assert call["argv"][0] == str(fake_gem5)
    run_line = next(ln for ln in out.splitlines() if ln.startswith("P2P_RUN "))
    assert json.loads(run_line[len("P2P_RUN "):])["command"].startswith(
        shlex.quote(str(fake_gem5)) + " ")


def test_gem5_command_matches_run_gem5_and_adapter_resolve(run_dir, fake_gem5):
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir), "foo"],
                  {"SR_FAKE_KNOB": "1"})
    assert rc == 0, out
    outdir, call = call_record(out)
    rd = str(run_dir)
    assert call["argv"] == [
        str(fake_gem5), "--redirect-stderr", f"--outdir={outdir}", f"{rd}/se_o3.py",
        "--cmd", f"{rd}/workloads/bin/foo",
        "--options", shlex.join(["-g", "10", "-n", "a b", "3"]),
        "--cwd", f"{rd}/workloads/data/foo",
        "--maxinsts", "5000",
    ]
    # gem5 runs in the outdir, as run_gem5 is called with cwd=outdir, and
    # the host environment reaches it unchanged (that is the knob's route).
    assert os.path.realpath(call["cwd"]) == os.path.realpath(outdir)
    assert call["knob"] == "1"
    assert Path(outdir).parent == run_dir / "runs"


def test_config_args_equal_the_adapters(run_dir):
    """Byte-for-byte the same guest argv, cwd and limit as run_traces."""
    try:
        from hosts.gem5 import adapter
    except Exception as e:  # chia or ray missing on this machine
        pytest.skip(f"hosts.gem5.adapter does not import here: {e}")
    rw = _load_run_workload()
    doc = json.loads((run_dir / "workloads.json").read_text())
    for name in ("foo", "bar"):
        ours = rw.config_args(rw.resolve(name, str(run_dir), doc))
        theirs = adapter.resolve(name, str(run_dir), run_dir / "workloads.json")
        assert ours == theirs["config_args"], name


def _load_run_workload():
    spec = importlib.util.spec_from_file_location("run_workload_under_test", RUN_WORKLOAD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_config_args_overrides():
    rw = _load_run_workload()
    spec = {"binary": "/r/w/bin/foo", "args": ["-x"], "cwd": None, "max_insts": 5000}
    assert rw.config_args(spec) == ["--cmd", "/r/w/bin/foo", "--options", "-x",
                                    "--maxinsts", "5000"]
    assert "--maxinsts" not in rw.config_args(spec, maxinsts=0)
    assert rw.config_args(spec, maxinsts=7)[-2:] == ["--maxinsts", "7"]
    assert rw.config_args(spec, cond_bp="LTAGE", cpu="atomic")[-4:] == [
        "--cond-bp", "LTAGE", "--cpu", "atomic"]


def test_defaults_come_from_the_environment(run_dir, fake_gem5, tmp_path):
    out_dir = tmp_path / "chosen_out"
    rc, out = run(["--outdir", str(out_dir), "bar"],
                  {"P2P_GEM5_BIN": str(fake_gem5), "P2P_GEM5_RUN_DIR": str(run_dir)})
    assert rc == 0, out
    outdir, call = call_record(out)
    assert outdir == str(out_dir)
    # No cwd in the manifest: se_o3.py picks the binary's directory, so
    # run_workload.py passes no --cwd, exactly as adapter.resolve does.
    assert call["argv"][4:] == ["--cmd", f"{run_dir}/workloads/bin/bar", "--options", "-q"]


def test_run_dir_defaults_to_the_scripts_own_dir(run_dir, fake_gem5):
    for name in ("run_workload.py", "p2p_metrics.py"):
        shutil.copy(RUN_DIR_SRC / name, run_dir / name)
    rc, out = run(["bar"], {"P2P_GEM5_BIN": str(fake_gem5)},
                  script=run_dir / "run_workload.py", drop=("P2P_GEM5_RUN_DIR",))
    assert rc == 0, out
    _, call = call_record(out)
    assert call["argv"][5] == f"{run_dir}/workloads/bin/bar"


def test_unknown_workload_names_the_known_ones(run_dir, fake_gem5):
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir), "nope"])
    assert rc == 2
    assert out.splitlines()[0] == "P2P_WORKLOAD nope"
    status = [ln for ln in out.splitlines() if ln.startswith("P2P_STATUS")]
    assert status == ["P2P_STATUS failed unknown gem5 workload 'nope'. "
                      "workloads.json has: bar, foo"]


def test_no_gem5_binary(run_dir):
    rc, out = run(["--run-dir", str(run_dir), "foo"], drop=("P2P_GEM5_BIN",))
    assert rc == 2
    assert "P2P_STATUS failed no gem5 binary" in out


@pytest.mark.parametrize("mode, code, reason", [
    ("ok", "3", "gem5 exited 3: the guest exited with code 3"),
    ("no_exit_line", "0", "without a P2P_EXIT line"),
    ("crash", "0", "gem5 exited 1 before the simulation ended"),
    ("no_stats", "0", "the stats did not derive cond_mpki, branch_mpki, ipc"),
])
def test_failures_exit_1_with_a_reason(run_dir, fake_gem5, mode, code, reason):
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir), "foo"],
                  {"FAKE_GEM5_MODE": mode, "FAKE_GUEST_CODE": code})
    assert rc == 1, out
    status = [ln for ln in out.splitlines() if ln.startswith("P2P_STATUS")]
    assert len(status) == 1 and status[0].startswith("P2P_STATUS failed "), out
    assert reason in status[0]
    assert out.splitlines()[-1] == status[0]
    if mode == "crash":
        # Echoed diagnostics are indented, so no echoed line can pass for
        # one of the P2P_ lines.
        assert "  | fatal: boom" in out.splitlines()


def test_timeout_kills_gem5_and_exits_124(run_dir, fake_gem5):
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir),
                   "--timeout", "1", "foo"], {"FAKE_GEM5_MODE": "sleep"})
    assert rc == 124, out
    assert "P2P_STATUS failed gem5 timed out after 1.0s" in out


def test_atomic_needs_only_ipc(run_dir, fake_gem5):
    only_counts = ("\n---------- Begin Simulation Statistics ----------\n"
                   + gem5_line("system.cpu.numCycles", "9000") + "\n"
                   + gem5_line("system.cpu.commitStats0.numInsts", "4500") + "\n"
                   + "\n---------- End Simulation Statistics   ----------\n")
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir),
                   "--cpu", "atomic", "--maxinsts", "0", "foo"],
                  {"FAKE_STATS": only_counts})
    assert rc == 0, out
    assert M.parse_metric_lines(out) == {"ipc": 0.5}
    _, call = call_record(out)
    assert "--maxinsts" not in call["argv"]
    assert call["argv"][-2:] == ["--cpu", "atomic"]


def test_stale_stats_in_a_reused_outdir_are_not_read(run_dir, fake_gem5, tmp_path):
    out_dir = tmp_path / "reused"
    out_dir.mkdir()
    (out_dir / "stats.txt").write_text(STD)
    rc, out = run(["--gem5", str(fake_gem5), "--run-dir", str(run_dir),
                   "--outdir", str(out_dir), "foo"], {"FAKE_GEM5_MODE": "no_stats"})
    assert rc == 1
    assert "P2P_METRIC" not in out


# --------------------------------------------------------- se_o3.py


def test_se_o3_is_valid_python():
    compile(SE_O3.read_text(), str(SE_O3), "exec")


@pytest.fixture
def se_o3(monkeypatch):
    """se_o3.py imported against a stub m5. Only the argument handling and
    the exit mapping are exercised: nothing here builds a system."""
    m5 = types.ModuleType("m5")
    objects = types.ModuleType("m5.objects")
    params = types.ModuleType("m5.params")
    names = ("ArmAtomicSimpleCPU", "ArmO3CPU", "BranchPredictor", "Cache",
             "ConditionalPredictor", "DDR3_1600_8x8", "MemCtrl", "Process", "Root",
             "SEWorkload", "SrcClockDomain", "System", "SystemXBar", "VoltageDomain")
    for name in names:
        setattr(objects, name, type(name, (), {}))
    params.AddrRange = type("AddrRange", (), {})
    m5.objects, m5.params = objects, params
    for mod in (m5, objects, params):
        monkeypatch.setitem(sys.modules, mod.__name__, mod)
    spec = importlib.util.spec_from_file_location("se_o3_under_test", SE_O3)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # __name__ is not __m5_main__: main() does not run
    return mod


def test_se_o3_takes_a_dash_leading_single_token_option(se_o3):
    args = se_o3.parse_args(["--cmd", "/w/bin/bar", "--options", "-q"])
    assert args.options == "-q"
    args = se_o3.parse_args(["--cmd", "/w/bin/foo", "--options", "-g 10 -n 'a b' 3",
                             "--cwd", "/w/data/foo", "--maxinsts", "5000"])
    assert shlex.split(args.options) == ["-g", "10", "-n", "a b", "3"]
    assert (args.cwd, args.maxinsts, args.cond_bp, args.cpu) == (
        "/w/data/foo", 5000, "TAGE_SC_L_64KB", "o3")
    assert se_o3.parse_args(["--cmd", "/x", "--options", ""]).options == ""


def test_se_o3_exit_status(se_o3):
    assert se_o3.exit_status(se_o3.GUEST_EXIT_CAUSE, 0) == 0
    assert se_o3.exit_status(se_o3.GUEST_EXIT_CAUSE, 3) == 3
    assert se_o3.exit_status(se_o3.MAX_INSTS_CAUSE, 0) == 0
    assert se_o3.exit_status("simulate() limit reached", 0) == se_o3.UNEXPECTED_EXIT_STATUS
    assert se_o3.UNEXPECTED_EXIT_STATUS != 0
    assert se_o3.GUEST_ENV == ["GLIBC_TUNABLES=glibc.pthread.rseq=0"]


def test_se_o3_reads_no_knob_from_the_host():
    source = SE_O3.read_text()
    assert "os.environ" not in source and "getenv" not in source
