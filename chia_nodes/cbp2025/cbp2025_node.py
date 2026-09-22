"""CBP2025Node: a CHIA node wrapping the CBP2025 simulator kit
(github.com/ramisheikh/cbp2025). Intended for upstreaming into
chia/simulators/ next to champsim.py and gem5.py, whose conventions it
copies: staticmethod ChiaFunctions, dataclass results, and the built
binary travelling as bytes so build and run workers need not co-locate.

Simulator facts this wraps (verified against the kit's sources):
- Contestant code: my_cond_branch_predictor.{h,cc}; the nine free
  functions in cbp.h are fixed and cond_branch_predictor_interface.cc
  is editable.
- Build: `make` at the repo root (g++ -std=c++17 -O3, links lib/libcbp.a, -lz).
- Run: `./cbp <trace.gz>`, single-threaded per trace; parallelism is
  one process per trace.
- Scoring: warmup is the first half of each trace; the contest metrics
  are the "50 Perc" rows: BrMisPKI and CycWpPKI.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from chia.base.ChiaFunction import ChiaFunction

CBP_RESOURCE = "cbp2025"


@dataclass
class CBP2025BuildResult:
    success: bool
    log: str
    binary: bytes = b""


@dataclass
class CBP2025RunResult:
    success: bool
    trace: str
    log: str
    returncode: int
    # Parsed "50 Perc instructions" row (the scoring window) plus full-run rows.
    metrics: dict = field(default_factory=dict)


# One row of the DIRECT CONDITIONAL BRANCH PREDICTION MEASUREMENTS table:
# Instr Cycles IPC NumBr MispBr BrPerCyc MispBrPerCyc MR MPKI CycWP CycWPAvg CycWPPKI
_ROW_FIELDS = (
    "instr", "cycles", "ipc", "numbr", "mispbr", "brpercyc",
    "mispbrpercyc", "mr", "mpki", "cycwp", "cycwpavg", "cycwppki",
)


def _parse_measurement_rows(log: str) -> dict:
    """Extract the per-window measurement rows from cbp stdout."""
    out: dict = {}
    section = re.search(
        r"DIRECT CONDITIONAL BRANCH PREDICTION MEASUREMENTS(.*?)(?:\n\s*\n[A-Z]|\Z)",
        log,
        re.S,
    )
    if not section:
        return out
    for label, key in (
        (r"50\s*Perc\s*instructions", "50perc"),
        (r"Full\s*Simulation", "full"),
    ):
        # Jump past the label's own trailing "---" banner dashes (on the same
        # line) and the column-header row to the first line that actually
        # starts with a digit -- that's the data row.
        m = re.search(label + r"[\s\S]*?\n[ \t]*(\d[^\n]*)", section.group(1))
        if not m:
            continue
        # MR is printed as e.g. "0.2049%"; strip the percent sign before
        # float() rather than excluding it from the value charset (excluding
        # it truncated the row before the trailing MPKI/CycWP* columns).
        vals = [v.rstrip("%") for v in m.group(1).split()]
        if len(vals) >= len(_ROW_FIELDS):
            out[key] = {f: float(v) for f, v in zip(_ROW_FIELDS, vals)}
    return out


class CBP2025Node:
    """Build/run/stats for the CBP2025 kit. All methods are dispatchable
    ChiaFunctions; call e.g. `get(CBP2025Node.build.chia_remote(root, srcs))`.
    """

    @staticmethod
    @ChiaFunction(resources={CBP_RESOURCE: 1.0})
    def build(
        cbp_root: str,
        predictor_sources: dict[str, bytes] | None = None,
        timeout_s: int = 1800,
        env: dict | None = None,
    ) -> CBP2025BuildResult:
        """Overlay predictor_sources ({relpath: content}) onto the checkout,
        `make clean && make`, and return the cbp binary as bytes.
        Passing predictor_sources=None builds the checkout as-is
        (baseline TAGE-SC-L).

        `env` is merged over the worker's environment for both make
        invocations. It exists for a predictor whose knobs are compile-time:
        the kit's Makefile passes CPPFLAGS through, so a port can write
        `CPPFLAGS += -DSR_ENABLE=$(SR_ENABLE)` and have one value per build.
        A predictor whose knobs are read with getenv() at run time wants the
        same dict on `run` instead, and does not need this."""
        root = Path(cbp_root)
        for rel, content in (predictor_sources or {}).items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        run_env = {**os.environ, **{k: str(v) for k, v in (env or {}).items()}}
        proc = subprocess.run(
            ["make", "clean"], cwd=root, capture_output=True, text=True,
            timeout=timeout_s, env=run_env,
        )
        proc = subprocess.run(
            ["make", "-j"], cwd=root, capture_output=True, text=True,
            timeout=timeout_s, env=run_env,
        )
        log = proc.stdout + proc.stderr
        binary = root / "cbp"
        if proc.returncode != 0 or not binary.exists():
            return CBP2025BuildResult(success=False, log=log)
        return CBP2025BuildResult(success=True, log=log, binary=binary.read_bytes())

    @staticmethod
    @ChiaFunction(resources={CBP_RESOURCE: 1.0})
    def run(
        binary: bytes,
        trace_path: str,
        extra_args: tuple = (),
        timeout_s: int = 3600,
        env: dict | None = None,
    ) -> CBP2025RunResult:
        """Run one trace through a cbp binary shipped as bytes.
        Fractional-resource note: each run is single-threaded, so the
        cluster yaml advertises {"cbp2025": <ncores>} per worker and the
        loop dispatches with resources={"cbp2025": 1.0} per trace.

        `env` is merged over the worker's environment. The kit gives a
        predictor no command line of its own -- argv belongs to the
        simulator -- so an environment variable read in
        beginCondDirPredictor() is the only way to change a predictor's
        behaviour without rebuilding, which is what a verify gate flipping
        a feature on and off needs."""
        with tempfile.TemporaryDirectory(prefix="cbp_run_") as td:
            exe = Path(td) / "cbp"
            exe.write_bytes(binary)
            exe.chmod(0o755)
            try:
                proc = subprocess.run(
                    [str(exe), *extra_args, trace_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    env={**os.environ, **{k: str(v) for k, v in (env or {}).items()}},
                )
            except subprocess.TimeoutExpired as e:
                return CBP2025RunResult(
                    success=False, trace=trace_path,
                    log=(e.stdout or "") + (e.stderr or ""), returncode=-1,
                )
        log = proc.stdout + proc.stderr
        metrics = _parse_measurement_rows(log)
        return CBP2025RunResult(
            success=(proc.returncode == 0 and "50perc" in metrics),
            trace=trace_path,
            log=log,
            returncode=proc.returncode,
            metrics=metrics,
        )

    @staticmethod
    @ChiaFunction()
    def aggregate(results: list) -> dict:
        """Arithmetic means over per-trace 50perc rows, matching the kit's
        scripts/trace_exec_training_list.py aggregation (amean of
        50PercMPKI a.k.a. BrMisPKI, and 50PercCycWPPKI)."""
        ok = [r for r in results if r is not None and r.success]
        fails = [r.trace for r in results if r is None or not r.success]
        if not ok:
            return {"n": 0, "failed": fails}
        n = len(ok)
        return {
            "n": n,
            "failed": fails,
            "brmispki_50perc_amean": sum(r.metrics["50perc"]["mpki"] for r in ok) / n,
            "cycwppki_50perc_amean": sum(r.metrics["50perc"]["cycwppki"] for r in ok) / n,
            "ipc_50perc_amean": sum(r.metrics["50perc"]["ipc"] for r in ok) / n,
        }
