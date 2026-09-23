#!/usr/bin/env python3
"""Run one manifest workload on gem5 and print its metrics.

    python3 run_workload.py [--gem5 BIN] [--run-dir DIR] [--outdir DIR] \
        [--maxinsts N] [--cond-bp NAME] [--cpu o3|atomic] [--timeout S] WORKLOAD

This is the gem5 host's command for the agent's shell and for any test plan
entry that runs one workload. It prints, in this order:

    P2P_WORKLOAD <name>
    P2P_RUN {...}                  outdir, gem5 exit status, guest exit, wall time
    P2P_STAT <logical> <value>     each stat of p2p_metrics.STATS_KEYS found
    P2P_METRIC <name> <value>      p2p_metrics.derive, full precision
    P2P_STATUS ok | P2P_STATUS failed <reason>

and exits 0 only when gem5 exited 0, se_o3.py reported the guest exiting 0
(or --maxinsts stopping it), and every metric derived. The adapter's
parse_metrics reads the P2P_METRIC lines only when every P2P_STATUS says ok.

It must reproduce the adapter's run_traces exactly, because G2 compares a
feature-off run from here with a baseline recorded there at rel_tol 0. So:

  - the se_o3.py arguments are built the way adapter.resolve builds them,
    string for string (the guest sees --cmd as argv[0], and a different
    string moves its stack),
  - the gem5 command line is the one Gem5Node.run_gem5 builds, with the
    adapter's `--redirect-stderr`, and gem5 runs with the outdir as its cwd,
  - the stats are parsed with p2p_metrics.parse_stats_file. The adapter
    parses run_gem5's captured stats.txt with the same two functions, not
    with chia's parser, which cannot read the conditional-only rows.

The environment passes to gem5 unchanged. That is how the enable knob
reaches the port's C++, and se_o3.py keeps it away from the guest.

Standard library only, plus p2p_metrics from this file's own directory: it
runs on the worker under conda's python3, with no chia on its path.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import shlex
import signal
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import p2p_metrics  # noqa: E402

# The adapter's gem5 args (hosts/gem5/adapter.py _GEM5_ARGS). gem5 then
# writes its stderr, where fatal() and panic() go, to <outdir>/simerr.txt.
GEM5_ARGS = ("--redirect-stderr",)
# se_o3.py prints exactly one of these when the simulation ends.
EXIT_PREFIX = "P2P_EXIT cause="
TAIL_BYTES = 2000

EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_SETUP_FAILED = 2
EXIT_TIMEOUT = 124


class SetupError(Exception):
    """A problem found before gem5 starts: the run never happened."""


# ------------------------------------------------------------- the manifest


def _payload_relpath(rel, what: str) -> str:
    """A manifest path, checked to stay inside the payload. The adapter
    applies the same check, so a manifest one side rejects the other does
    too."""
    if not rel or not isinstance(rel, str) or posixpath.isabs(rel) \
            or ".." in rel.split("/"):
        raise SetupError(f"{what} {rel!r} must be a relative path inside the payload")
    return rel


def load_manifest(run_dir: str) -> dict:
    path = posixpath.join(run_dir, "workloads.json")
    try:
        with open(path) as f:
            return json.load(f)
    except OSError as e:
        raise SetupError(f"cannot read {path}: {e}. Is the run dir installed?")
    except ValueError as e:
        raise SetupError(f"{path} is not valid JSON: {e}")


def resolve(name: str, run_dir: str, doc: dict) -> dict:
    """One workload's se_o3.py arguments, built as adapter.resolve builds
    them. Paths are joined as strings and never normalized or resolved:
    the adapter does not, and the guest must see the same bytes."""
    table = doc.get("workloads") or {}
    if name not in table:
        raise SetupError(f"unknown gem5 workload {name!r}. workloads.json has: "
                         f"{', '.join(sorted(table)) or '(none)'}")
    entry = table[name]
    base = posixpath.join(run_dir, doc.get("root") or "workloads")
    binary = posixpath.join(base, _payload_relpath(entry.get("binary"), f"{name}.binary"))
    cwd = entry.get("cwd")
    cwd = posixpath.join(base, _payload_relpath(cwd, f"{name}.cwd")) if cwd else None
    args = [str(a) for a in (entry.get("args") or [])]
    max_insts = entry.get("max_insts")
    return {"name": name, "binary": binary, "args": args, "cwd": cwd,
            "max_insts": max_insts}


def config_args(spec: dict, *, maxinsts=None, cond_bp=None, cpu=None) -> list:
    """The arguments after se_o3.py. Identical to adapter.resolve's
    `config_args` when no override is given, so a default run here and a
    run_traces run of the same workload start the same guest.

    `maxinsts` None keeps the manifest's limit. 0 removes it. N replaces
    it. `cond_bp` and `cpu` are added only when given, so the default
    command line carries no argument the adapter does not pass."""
    out = ["--cmd", spec["binary"], "--options", shlex.join(spec["args"])]
    if spec["cwd"]:
        out += ["--cwd", spec["cwd"]]
    limit = spec["max_insts"] if maxinsts is None else maxinsts
    if limit:
        out += ["--maxinsts", str(int(limit))]
    if cond_bp:
        out += ["--cond-bp", cond_bp]
    if cpu:
        out += ["--cpu", cpu]
    return out


def default_outdir(run_dir: str, name: str) -> str:
    """A fresh directory under <run-dir>/runs/, named like the adapter's
    outdirs. Two shells running the same workload at once must not share
    one stats.txt."""
    safe = "".join(c if (c.isalnum() or c in "_.-") else "_" for c in name)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return posixpath.join(run_dir, "runs", f"{stamp}-shell-{safe}-{uuid.uuid4().hex[:8]}")


# --------------------------------------------------------------- the run


def exit_line(stdout: str):
    """(cause, code) from the last P2P_EXIT line, or None."""
    found = None
    for line in (stdout or "").splitlines():
        if line.startswith(EXIT_PREFIX) and " code=" in line:
            cause, _, code = line[len(EXIT_PREFIX):].rpartition(" code=")
            found = (cause, code.strip())
    return found


def _tail_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - TAIL_BYTES))
            return f.read().decode(errors="replace")
    except OSError:
        return ""


def _print_tail(label: str, text: str) -> None:
    """Echo a diagnostic, every line indented. A line of guest or gem5
    output can then never start with P2P_ and be read as one of ours."""
    text = (text or "").strip("\n")
    if not text:
        return
    print(f"--- {label} (last {TAIL_BYTES} bytes) ---")
    for line in text[-TAIL_BYTES:].splitlines():
        print(f"  | {line}")


def run_gem5(cmd: list, outdir: str, timeout_s):
    """Run gem5 with this process's environment, unchanged.

    gem5 stays in this process group, so a caller that kills the group kills
    gem5 too. SIGTERM, SIGINT and SIGHUP to this process are passed on to
    gem5 before it exits, so an interrupted shell does not leave a gem5 run
    holding a CPU for an hour."""
    proc = subprocess.Popen(cmd, cwd=outdir, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, errors="replace")

    def forward(signum, _frame):
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        raise SystemExit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, forward)
    started = time.monotonic()
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        timed_out = True
    return proc.returncode, stdout or "", stderr or "", timed_out, time.monotonic() - started


def judge(rc: int, stdout: str, metrics: dict, required, timed_out: bool,
          timeout_s) -> tuple:
    """(ok, reason). The adapter's _judge_run, applied to one shell run."""
    if timed_out:
        return False, f"gem5 timed out after {timeout_s}s"
    exit_info = exit_line(stdout)
    if rc != 0:
        if exit_info and exit_info[1] != "0":
            return False, (f"gem5 exited {rc}: the guest exited with code "
                           f"{exit_info[1]} ({exit_info[0]})")
        if exit_info:
            return False, f"gem5 exited {rc} after the simulation ended ({exit_info[0]})"
        return False, f"gem5 exited {rc} before the simulation ended"
    if exit_info is None:
        return False, ("gem5 exited 0 without a P2P_EXIT line, so se_o3.py never "
                       "reported the end of the simulation")
    if exit_info[1] != "0":
        return False, f"the guest exited with code {exit_info[1]} ({exit_info[0]})"
    missing = [k for k in required if k not in metrics]
    if missing:
        return False, f"the stats did not derive {', '.join(missing)}"
    return True, ""


def parse_args(argv):
    p = argparse.ArgumentParser(prog="run_workload.py",
                                description=__doc__.splitlines()[0])
    p.add_argument("workload", metavar="WORKLOAD", help="a name in workloads.json")
    p.add_argument("--gem5", default=os.environ.get("P2P_GEM5_BIN"),
                   help="gem5 binary (default: $P2P_GEM5_BIN)")
    p.add_argument("--run-dir", default=os.environ.get("P2P_GEM5_RUN_DIR") or HERE,
                   help="dir holding se_o3.py, workloads.json and workloads/ "
                        "(default: $P2P_GEM5_RUN_DIR, else this script's dir)")
    p.add_argument("--outdir", default=None,
                   help="gem5 outdir (default: a new dir under <run-dir>/runs/)")
    p.add_argument("--maxinsts", type=int, default=None,
                   help="instruction limit (default: the manifest's; 0 = none)")
    p.add_argument("--cond-bp", default=None,
                   help="conditional predictor class (default: se_o3.py's)")
    p.add_argument("--cpu", choices=("o3", "atomic"), default=None,
                   help="o3 (se_o3.py's default) or atomic, to count instructions")
    p.add_argument("--timeout", type=float, default=None,
                   help="kill gem5 after S seconds (default: no limit)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    # Absolute, because gem5 runs with the outdir as its cwd, and Popen looks
    # up a relative program path from that cwd, not from ours. The check
    # below would pass and the start would then fail. The binary's path
    # never reaches the guest, so this changes nothing it sees.
    if args.gem5:
        args.gem5 = os.path.abspath(args.gem5)
    print(f"P2P_WORKLOAD {args.workload}", flush=True)

    try:
        if not args.gem5:
            raise SetupError("no gem5 binary: pass --gem5 or set P2P_GEM5_BIN")
        if not os.path.isfile(args.gem5) or not os.access(args.gem5, os.X_OK):
            raise SetupError(f"{args.gem5} is not an executable file")
        if args.maxinsts is not None and args.maxinsts < 0:
            raise SetupError(f"--maxinsts must be 0 or more, got {args.maxinsts}")
        # An absolute run dir is used exactly as given, because the adapter
        # joins GEM5_RUN_DIR as a string and the guest's argv[0] must match
        # it byte for byte. A relative one is made absolute, since se_o3.py
        # refuses a relative --cmd (the host cwd would leak into the guest).
        run_dir = args.run_dir if posixpath.isabs(args.run_dir) \
            else os.path.abspath(args.run_dir)
        script = posixpath.join(run_dir, "se_o3.py")
        if not os.path.isfile(script):
            raise SetupError(f"{script} does not exist. Is the run dir installed?")
        spec = resolve(args.workload, run_dir, load_manifest(run_dir))
        # Absolute, because gem5 runs with the outdir as its cwd and would
        # resolve a relative --outdir a second time from there. The outdir
        # never reaches the guest, so this changes nothing it sees.
        outdir = os.path.abspath(args.outdir) if args.outdir \
            else default_outdir(run_dir, args.workload)
        os.makedirs(outdir, exist_ok=True)
        # A reused outdir can hold the last run's files. A gem5 that dies
        # before its first dump would then leave the old stats.txt to be
        # read as this run's numbers.
        for stale in ("stats.txt", "simerr.txt", "guest_stdout.txt", "guest_stderr.txt"):
            try:
                os.remove(os.path.join(outdir, stale))
            except FileNotFoundError:
                pass
    except (SetupError, OSError) as e:
        print(f"P2P_STATUS failed {e}", flush=True)
        return EXIT_SETUP_FAILED

    # The command Gem5Node.run_gem5 builds:
    #   gem5 [gem5_args] --outdir=<outdir> config_script [config_args]
    cmd = [args.gem5, *GEM5_ARGS, f"--outdir={outdir}", script,
           *config_args(spec, maxinsts=args.maxinsts, cond_bp=args.cond_bp,
                        cpu=args.cpu)]
    try:
        rc, stdout, stderr, timed_out, wall = run_gem5(cmd, outdir, args.timeout)
    except OSError as e:
        print(f"P2P_STATUS failed could not start gem5: {e}", flush=True)
        return EXIT_SETUP_FAILED

    stats = p2p_metrics.parse_stats_file(os.path.join(outdir, "stats.txt"))
    metrics = p2p_metrics.derive(stats)
    # atomic has no branch predictor, so only ipc can derive. Its point is
    # the instruction count, which P2P_STAT insts carries.
    required = ("ipc",) if args.cpu == "atomic" else p2p_metrics.METRIC_KEYS
    ok, reason = judge(rc, stdout, metrics, required, timed_out, args.timeout)
    exit_info = exit_line(stdout)

    print("P2P_RUN " + json.dumps({
        "outdir": outdir, "gem5_rc": rc, "wall_s": round(wall, 3),
        "exit_cause": exit_info[0] if exit_info else None,
        "exit_code": exit_info[1] if exit_info else None,
        "command": shlex.join(cmd),
    }, sort_keys=True))
    for name, value in stats.items():
        print(f"P2P_STAT {name} {value!r}")
    text = p2p_metrics.format_metric_lines(metrics)
    if text:
        print(text)
    if not ok:
        _print_tail("gem5 stdout", stdout)
        _print_tail("gem5 stderr before redirect", stderr)
        _print_tail("simerr.txt", _tail_file(os.path.join(outdir, "simerr.txt")))
        _print_tail("guest stderr", _tail_file(os.path.join(outdir, "guest_stderr.txt")))
        print(f"P2P_STATUS failed {reason}", flush=True)
        return EXIT_TIMEOUT if timed_out else EXIT_RUN_FAILED
    print("P2P_STATUS ok", flush=True)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
