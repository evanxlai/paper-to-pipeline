#!/usr/bin/env python3
"""Check every gem5 workload under qemu-aarch64-static, on the head.

scripts/build_gem5_workloads.sh runs this after it installs the payload.
It is plain standard-library Python, like the gem5 run scripts, so it runs
under the head's system python3 or chia_env's.

For each entry in hosts/gem5/workloads.json it checks four things:

  static   `file` says the binary is a static aarch64 ELF. gem5's SE mode
           can load a dynamic binary only with the guest's loader and
           libraries in place, and the node has neither.
  exit     the program exits 0. Every program here checks its own result
           and exits non-zero when the check fails.
  repeat   two runs print the same bytes. A program that reads the clock,
           the environment or /dev/urandom shows up here, although only
           partly: qemu's clock moves between runs, but a fixed seed that
           happens to repeat does not.
  expected the output equals the copy in expected.json, recorded with the
           same args. This catches a toolchain or source change that still
           exits 0.

qemu runs the guest with the same fixed environment the gem5 run scripts
give it (GUEST_ENV) and nothing from the host, so a check here and a run
on gem5 start the program the same way.

Two optional measurements help the lead size the workloads:

  --count-insts   counts guest instructions exactly by running qemu one
                  instruction per translation block and counting its exec
                  log lines. About 0.4 M instructions per second. The
                  count is qemu's, not gem5's: the two differ a little at
                  startup (IFUNC choices follow the CPU's feature bits).
                  It writes the count to each entry's approx_insts.
  --native DIR    runs native x86-64 builds of the same programs from DIR
                  and compares their output with the aarch64 output. A
                  match means the cross compiler and qemu computed what
                  an independent build computed.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
import time
from pathlib import Path

# The guest environment that hosts/gem5/run/se_o3.py uses by default. glibc
# 2.35 registers rseq at startup, and this tunable turns that off. The
# point here is to match gem5, not to work around qemu.
GUEST_ENV = {"GLIBC_TUNABLES": "glibc.pthread.rseq=0"}
QEMU = "qemu-aarch64-static"
RUN_TIMEOUT_S = 900


def load_manifest(path: Path) -> dict:
    doc = json.loads(path.read_text())
    if doc.get("schema") != 1 or "workloads" not in doc:
        raise SystemExit(f"{path}: not a schema-1 workloads manifest")
    return doc


def resolve(payload: Path, entry: dict) -> tuple[Path, Path, list[str]]:
    """The binary, the working directory and argv[1:] for one entry. The
    cwd rule matches the run scripts: null means the binary's directory."""
    binary = payload / entry["binary"]
    cwd = payload / entry["cwd"] if entry.get("cwd") else binary.parent
    return binary, cwd, [str(a) for a in entry.get("args", [])]


def run_once(cmd: list[str], cwd: Path) -> dict:
    t0 = time.monotonic()
    p = subprocess.run(cmd, cwd=cwd, env=GUEST_ENV, capture_output=True,
                       timeout=RUN_TIMEOUT_S)
    return {"rc": p.returncode, "stdout": p.stdout.decode(errors="replace"),
            "stderr": p.stderr.decode(errors="replace"),
            "wall_s": time.monotonic() - t0}


def count_insts(binary: Path, cwd: Path, args: list[str]) -> int:
    """Exact guest instruction count from qemu's exec log.

    -singlestep makes every translation block one instruction long, and
    nochain makes qemu log every block it executes. So each "Trace" line is
    one executed guest instruction. The log goes to stderr, and the
    programs here write nothing to stderr when they succeed."""
    cmd = [QEMU, "-singlestep", "-d", "nochain,exec", "-D", "/dev/stderr",
           str(binary), *args]
    p = subprocess.Popen(cmd, cwd=cwd, env=GUEST_ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    n, tail = 0, b"\n"
    assert p.stderr is not None
    while True:
        chunk = p.stderr.read(1 << 20)
        if not chunk:
            break
        # Carry the last bytes over, so a marker split across two chunks
        # still counts once.
        buf = tail + chunk
        n += buf.count(b"\nTrace ")
        tail = buf[-6:]
    if p.wait() != 0:
        raise RuntimeError(f"{binary.name} exited {p.returncode} under "
                           "single-step counting")
    return n


def result_line(stdout: str) -> str:
    """The line of a run's output worth showing in the table: the last one
    that carries a result. GAPBS ends with zeroed timing lines, and every
    driver ends with PASS, and neither tells two runs apart."""
    lines = [ln.strip() for ln in stdout.splitlines()]
    useful = [ln for ln in lines if ln and "Time:" not in ln
              and not ln.startswith("Verification")
              and ln not in ("PASS", "FAIL")]
    return (useful or lines or [""])[-1]


def file_check(binary: Path) -> str | None:
    """None if `file` calls this a static aarch64 ELF, else what it said."""
    out = subprocess.run(["file", "-b", str(binary)], capture_output=True,
                         text=True).stdout.strip()
    ok = "ARM aarch64" in out and "statically linked" in out
    return None if ok else out


def check_one(name: str, entry: dict, payload: Path, expected: dict,
              update: bool, native: Path | None, count: bool) -> dict:
    binary, cwd, args = resolve(payload, entry)
    res = {"name": name, "problems": [], "notes": []}
    if not binary.is_file():
        res["problems"].append(f"missing binary {binary}")
        return res
    bad = file_check(binary)
    if bad:
        res["problems"].append(f"not a static aarch64 ELF: {bad}")

    first = run_once([QEMU, str(binary), *args], cwd)
    second = run_once([QEMU, str(binary), *args], cwd)
    res["wall_s"] = (first["wall_s"], second["wall_s"])
    res["stdout"] = first["stdout"]
    res["last_line"] = result_line(first["stdout"])
    for r in (first, second):
        if r["rc"] != 0:
            res["problems"].append(
                f"exit {r['rc']}: {(r['stdout'] + r['stderr'])[-400:]!r}")
            break
    if first["stdout"] != second["stdout"]:
        res["problems"].append("two runs printed different output")

    want = expected.get(name)
    if update:
        res["notes"].append("expected output recorded")
    elif want is None:
        res["problems"].append(
            "no expected output; rerun with --update-expected")
    elif [str(a) for a in want.get("args", [])] != args:
        res["problems"].append(
            "expected output was recorded with other args "
            f"{want.get('args')}; rerun with --update-expected")
    elif want.get("stdout") != first["stdout"]:
        res["problems"].append(
            f"output differs from expected.json: got {first['stdout']!r}")

    if native is not None:
        nat_bin = native / binary.name
        nat = subprocess.run([str(nat_bin), *args], cwd=cwd, env=GUEST_ENV,
                             capture_output=True, timeout=RUN_TIMEOUT_S)
        nat_out = nat.stdout.decode(errors="replace")
        if nat.returncode != 0:
            res["problems"].append(f"native build exited {nat.returncode}")
        elif nat_out != first["stdout"]:
            res["problems"].append(
                f"native x86-64 output differs: {nat_out!r}")
        else:
            res["notes"].append("matches native x86-64")

    if count and not res["problems"]:
        try:
            res["insts"] = count_insts(binary, cwd, args)
        except (RuntimeError, subprocess.SubprocessError) as e:
            res["problems"].append(str(e))
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--payload", type=Path, required=True,
                    help="directory holding bin/ and data/")
    ap.add_argument("--expected", type=Path, required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--update-expected", action="store_true")
    ap.add_argument("--count-insts", action="store_true")
    ap.add_argument("--native", type=Path, default=None,
                    help="directory of native x86-64 builds to compare with")
    ap.add_argument("names", nargs="*", help="only these workloads")
    a = ap.parse_args()
    # Absolute, because each guest runs in its own cwd, and qemu exits 1
    # without a word when the binary path does not resolve from there.
    a.payload = a.payload.resolve()
    if a.native is not None:
        a.native = a.native.resolve()

    doc = load_manifest(a.manifest)
    entries = doc["workloads"]
    names = a.names or list(entries)
    unknown = [n for n in names if n not in entries]
    if unknown:
        raise SystemExit(f"unknown workloads {unknown}; known: "
                         f"{sorted(entries)}")
    expected = (json.loads(a.expected.read_text())
                if a.expected.is_file() else {})

    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        futs = [pool.submit(check_one, n, entries[n], a.payload, expected,
                            a.update_expected, a.native, a.count_insts)
                for n in names]
        results = [f.result() for f in futs]

    print(f"{'workload':<22} {'result':<6} {'qemu s':>13} "
          f"{'qemu insts':>12}  result")
    failed = 0
    for r in results:
        ok = not r["problems"]
        failed += not ok
        wall = r.get("wall_s")
        wall_s = f"{wall[0]:6.2f}/{wall[1]:6.2f}" if wall else "-"
        insts = f"{r['insts']:,}" if "insts" in r else "-"
        print(f"{r['name']:<22} {'ok' if ok else 'FAIL':<6} {wall_s:>13} "
              f"{insts:>12}  {r.get('last_line', '')[:60]}")
        for p in r["problems"]:
            print(f"    problem: {p}")
        for note in r["notes"]:
            print(f"    note: {note}")

    if a.update_expected and not failed:
        rec = dict(expected)
        for r in results:
            rec[r["name"]] = {"args": resolve(a.payload,
                                              entries[r["name"]])[2],
                              "stdout": r["stdout"]}
        # Drop entries for workloads the manifest no longer has.
        rec = {k: rec[k] for k in sorted(rec) if k in entries}
        a.expected.write_text(json.dumps(rec, indent=2) + "\n")
        print(f"wrote {a.expected}")
    elif a.update_expected:
        print("not writing expected output: fix the failures first")

    if a.count_insts and not failed:
        for r in results:
            entries[r["name"]]["approx_insts"] = r["insts"]
        a.manifest.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote approx_insts (qemu counts) into {a.manifest}")

    print(f"{len(results) - failed}/{len(results)} workloads passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
