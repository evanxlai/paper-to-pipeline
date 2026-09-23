"""The gem5 host's metrics: which stats to read, and what to make of them.

Two code paths read a gem5 run, and they must agree to the last bit:

  run_traces    the adapter's fan-out. chia's Gem5Node.run_gem5 returns the
                run's whole stats.txt (capture_stats=True), and the adapter
                parses it with `parse_stats_text` and `select` below.
  run_workload  run_workload.py in the agent's shell. It cannot import chia,
                so it reads stats.txt with `parse_stats_file` below, which is
                the same two functions.

G2 compares a feature-off shell run against a baseline recorded through
run_traces at rel_tol 0, so both paths use this module's parser and nothing
else. chia's own parser (Gem5Node.parse_gem5_stats) is not used for metrics,
and that is deliberate. Its line grammar rejects anything after the value
except a `#` comment. A gem5 vector stat with the `pdf` flag prints each row
as `name value pdf% cdf%` (src/base/stats/text.cc:344-413), so chia can read
only the `::total` row of such a stat. The one committed, conditional-only
misprediction count gem5 prints is such a row:
`branchPred.mispredicted_0::DirectCond`. Read with chia's grammar, the only
misprediction count left is `condIncorrect`, which counts every branch type
(see STATS_KEYS). The first cluster run (2026-09-23) derived cond_mpki from
condIncorrect, and cond_mpki came out equal to branch_mpki on all 28
workloads. This module's grammar reads every line chia's reads, with the same
value, and also accepts up to two percentage columns after the value. So
cond_mpki now comes from the DirectCond and IndirectCond rows, and it is
below branch_mpki whenever a non-conditional branch was mispredicted.

Standard library only: this file runs on the worker under conda's python3,
next to the workloads, with no chia and no gem5 on its path.

Every stat name was read in gem5 v25.1.0.0 (commit 7a2b0e4) for a classic
config whose O3 CPU sits at `system.cpu` and whose predictor is the CPU's
`branchPred` param (src/cpu/o3/BaseO3CPU.py:202), and every one appears in a
real stats.txt from this host's first cluster run. Line numbers below are in
that tree.
"""

from __future__ import annotations

import math
import re

# Logical name -> candidate stat names, first present wins. The same shape as
# chia's DEFAULT_STATS_KEYS, and run_gem5 merges this over those defaults, so
# `cycles` and `insts` here replace chia's own candidates. Some names below
# are pdf rows that chia's grammar cannot read, so run_gem5's own result.stats
# lacks them. That is harmless: run_gem5 needs only `cycles` for its status,
# and the adapter derives metrics from result.stats_content with this module.
STATS_KEYS: dict[str, list[str]] = {
    # O3 CPU cycles. BaseCPUStats::numCycles (src/cpu/base.cc:430). Registered
    # on the CPU's own group, so it prints as system.cpu.numCycles. The O3 CPU
    # adds one per tick (src/cpu/o3/cpu.cc:374) and adds skipped cycles when
    # it wakes (cpu.cc:1350). chia's run_gem5 reports "parse_failed" when
    # this one is missing.
    "cycles": ["system.cpu.numCycles"],
    # Committed instructions. commitStats0.numInsts is the thread-0 count at
    # commit, one per macro-instruction (src/cpu/o3/commit.cc:1353-1358,
    # group name at src/cpu/base.cc:1022). Committed only: a squashed
    # instruction never reaches it. It INCLUDES NOPs. simInsts is second, and
    # it is NOT the same count: it sums the threads' numInst
    # (src/cpu/base.cc:858-875, src/cpu/o3/cpu.cc:500-509), which instDone
    # bumps (cpu.cc:1159-1160), and commit skips instDone for NOPs and
    # instruction prefetches (commit.cc:1368-1372). On gapbs_bfs_s the two
    # were 2509944 and 2509105 (loop/tests/fixtures/gem5/). Only a stats.txt
    # without the commitStats0 row falls back to it. The --maxinsts limit
    # counts numInst too (cpu.cc:1165, o3/thread_context.hh:84-97), so a
    # capped run shows a few more instructions here than the limit says.
    # system.cpu.numInsts does not exist: BaseCPUStats never registers its
    # numInsts (src/cpu/base.cc:429-441 against base.hh:696).
    "insts": ["system.cpu.commitStats0.numInsts", "simInsts"],
    # Conditional branches looked up in the direction predictor. Counted at
    # PREDICTION time for every conditional branch fetch sees
    # (src/cpu/pred/bpred_unit.cc:150-152), so it INCLUDES wrong-path
    # branches that are later squashed. Not a denominator for committed
    # rates. Kept for diagnosis.
    "cond_predicted": ["system.cpu.branchPred.condPredicted"],
    # gem5 calls this "conditional branches incorrect", and it is not. It is
    # counted at COMMIT, inside the same `if (hist->mispredict)` block as
    # `mispredicted` (bpred_unit.cc:359-368). squash() sets hist->mispredict
    # for a branch of any type whose direction or target was corrected
    # (bpred_unit.cc:521). So it counts every committed mispredicted
    # branch: conditional, indirect, return, and taken branches that missed
    # the BTB. Committed only, NO wrong-path branches.
    "cond_incorrect": ["system.cpu.branchPred.condIncorrect"],
    # The same count as cond_incorrect, by its honest name. `mispredicted` is
    # a Vector2d of threads x branch types (bpred_unit.cc:667-668, 736-739),
    # printed as mispredicted_0::<type> plus mispredicted_0::total
    # (text.cc:649-715). Committed only, NO wrong-path branches.
    # condIncorrect is the fallback because it is incremented in the same
    # place, and the first cluster run showed the two equal.
    "committed_branch_mispredicts": [
        "system.cpu.branchPred.mispredicted_0::total",
        "system.cpu.branchPred.condIncorrect",
    ],
    # The conditional rows of that same vector: committed conditional
    # branches whose direction or target was corrected. A direction
    # predictor, and so sR, can change most of these, but not all. The row
    # also counts taken conditional branches that missed the BTB. On a BTB
    # miss the front end falls through whatever the direction predictor said
    # (bpred_unit.cc:180-188, 286-293), so no direction predictor removes
    # them. At commit gem5 files those under mispredictDueToBTBMiss and the
    # rest under mispredictDueToPredictor (bpred_unit.cc:359-367). On
    # gapbs_bfs_s the split was 660 and 34082 of 34742: a small floor under
    # cond_mpki. A pdf row, which is why the grammar below reads percentage
    # columns. IndirectCond is 0 on AArch64, which has no conditional
    # indirect branch, and gem5 still prints it.
    "cond_mispredicts_direct": ["system.cpu.branchPred.mispredicted_0::DirectCond"],
    "cond_mispredicts_indirect": ["system.cpu.branchPred.mispredicted_0::IndirectCond"],
    # Committed branches of every type, counted at commit (bpred_unit.cc:359).
    # NO wrong-path branches.
    "committed_branches": ["system.cpu.branchPred.committed_0::total"],
    # Committed conditional branches, from the same vector as above. NO
    # wrong-path branches. The denominator of a conditional mispredict rate.
    "committed_cond_direct": ["system.cpu.branchPred.committed_0::DirectCond"],
    # Committed conditional control instructions (src/cpu/base.cc:1113-1114,
    # called from commit.cc:1377). A plain vector with `nozero` and no pdf
    # (base.cc:1084-1085), so its rows have no percentage columns and even
    # chia's grammar reads them. It matched committed_cond_direct on the
    # fixture (517717). NO wrong-path branches.
    "committed_cond_branches": [
        "system.cpu.commitStats0.committedControl::IsCondControl",
    ],
}

METRIC_KEYS = ("cond_mpki", "branch_mpki", "ipc")

DIRECTIONS = {"cond_mpki": "decrease", "branch_mpki": "decrease", "ipc": "increase"}


# ------------------------------------------------------------------ derive


def _number(stats: dict, key: str):
    """stats[key] as a float, or None when it is missing or not a number.

    None rather than 0, because a metric computed from a stat that was never
    printed is a number nobody measured."""
    value = (stats or {}).get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def derive(stats: dict) -> dict:
    """One run's metrics from its logical stats (the keys of STATS_KEYS).

    A metric whose inputs are missing, or whose denominator is zero, is left
    out. It is never 0: a 0 MPKI from a run that printed no counters would
    look like a perfect predictor, and G2 would compare it as a number.

      cond_mpki    committed conditional mispredictions (DirectCond plus
                   IndirectCond rows) per thousand committed instructions.
                   The number sR is meant to move.
      branch_mpki  committed mispredictions of every branch type per
                   thousand committed instructions.
      ipc          committed instructions per cycle."""
    insts = _number(stats, "insts")
    cycles = _number(stats, "cycles")
    direct = _number(stats, "cond_mispredicts_direct")
    indirect = _number(stats, "cond_mispredicts_indirect")
    mispredicts = _number(stats, "committed_branch_mispredicts")
    out = {}
    if insts and direct is not None and indirect is not None:
        out["cond_mpki"] = 1000.0 * (direct + indirect) / insts
    if insts and mispredicts is not None:
        out["branch_mpki"] = 1000.0 * mispredicts / insts
    if insts is not None and cycles:
        out["ipc"] = insts / cycles
    return out


def aggregate(per_run: list) -> dict:
    """The suite's metrics: an arithmetic mean per metric, over the runs that
    have it. The cbp2025 convention (CBP2025Node.aggregate).

    math.fsum, not sum. fsum is exactly rounded, so the mean does not depend
    on the order the runs finished in. The baseline and every later gate run
    then agree bit for bit on the same numbers."""
    values: dict[str, list] = {}
    for metrics in per_run or []:
        for name, value in (metrics or {}).items():
            number = _number({name: value}, name)
            if number is not None:
                values.setdefault(name, []).append(number)
    return {name: math.fsum(vals) / len(vals)
            for name, vals in _ordered(values).items()}


def _ordered(metrics: dict) -> dict:
    """METRIC_KEYS first, in their order, then any others by name. A fixed
    order keeps the printed lines diffable from one run to the next."""
    first = [k for k in METRIC_KEYS if k in metrics]
    rest = sorted(k for k in metrics if k not in METRIC_KEYS)
    return {k: metrics[k] for k in first + rest}


# ------------------------------------------------------------ metric lines

_METRIC_LINE = re.compile(r"^P2P_METRIC[ \t]+(\S+)[ \t]+(\S+)[ \t]*$", re.M)


def format_metric_lines(metrics: dict) -> str:
    """`P2P_METRIC <name> <value>` lines, one per metric.

    repr() of a float is the shortest string that reads back as the same
    float, so a value survives the trip through the agent's shell exactly.
    G2 compares at rel_tol 0, and a rounded print would fail it."""
    lines = []
    for name, value in _ordered(metrics or {}).items():
        number = _number({name: value}, name)
        if number is not None:
            lines.append(f"P2P_METRIC {name} {number!r}")
    return "\n".join(lines)


def parse_metric_lines(text: str) -> dict:
    """The P2P_METRIC lines in `text`, name -> float. A name printed twice
    keeps its last value. A value that is not a number is skipped."""
    out = {}
    for name, raw in _METRIC_LINE.findall(text or ""):
        try:
            out[name] = float(raw)
        except ValueError:
            continue
    return out


# --------------------------------------------------------------- stats.txt

# chia's line grammar (chia/simulators/gem5.py, _STATS_NUMBER_RE), widened to
# accept up to two percentage columns after the value: the pdf and cdf a
# `pdf` vector prints on each row (text.cc:344-413). The value is still the
# first number after the name. With zero columns it is chia's pattern, so
# every line chia reads, this reads with the same name and value
# (loop/tests/test_gem5_run.py checks that over a real stats.txt). gem5 prints
# a NaN pdf as blank padding, not "nan%" (text.cc:294-298), so `nan` and
# `inf` here are only a guard. A NaN VALUE is still skipped, as chia skips
# it. See the module docstring for why.
_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_STATS_NUMBER_RE = re.compile(
    r"^\s*([A-Za-z0-9_:\.\[\]\-]+)\s+(" + _NUMBER + r")"
    r"(?:\s+(?:" + _NUMBER + r"|nan|-?inf)%){0,2}\s*(?:#.*)?$"
)
# The dump markers gem5 writes around each dump (src/base/stats/text.cc:
# 134-145). chia matches these substrings, so this does too.
_BEGIN, _END = "Begin Simulation Statistics", "End Simulation Statistics"


def _parse_block(lines: list) -> dict:
    out = {}
    for line in lines:
        m = _STATS_NUMBER_RE.match(line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        # chia's conversion, kept as is. For an integer string the two forms
        # give the same float, but copying it removes the question.
        out[key] = float(raw) if ("." in raw or "e" in raw.lower()) else float(int(raw))
    return out


def parse_stats_text(text: str) -> dict:
    """Every readable `name value` pair of the LAST complete dump in `text`,
    or `{}` when there is none.

    Last, because a stats reset or a periodic dump adds blocks and the last
    one is where the run ended. A block with no End marker is dropped. That
    is what a gem5 killed mid-dump leaves, and its numbers are partial."""
    blocks, current, inside = [], [], False
    for line in (text or "").splitlines():
        if _BEGIN in line:
            inside, current = True, []
            continue
        if _END in line and inside:
            inside = False
            blocks.append(current)
            current = []
            continue
        if inside:
            current.append(line)
    parsed = [_parse_block(b) for b in blocks if b]
    return parsed[-1] if parsed else {}


def select(raw: dict, stats_keys: dict | None = None) -> dict:
    """Logical name -> value, first present candidate wins. chia's
    parse_gem5_stats does the same walk over the same STATS_KEYS."""
    out = {}
    for logical, candidates in (stats_keys or STATS_KEYS).items():
        for name in candidates:
            if name in raw:
                out[logical] = raw[name]
                break
    return out


def parse_stats_file(path, stats_keys: dict | None = None) -> dict:
    """The logical stats (keys of STATS_KEYS) of the last dump in a
    stats.txt, or `{}` when the file cannot be read. The file-level twin of
    chia's Gem5Node.parse_gem5_stats_file with stats_block="last"."""
    try:
        with open(path, errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    return select(parse_stats_text(text), stats_keys)
