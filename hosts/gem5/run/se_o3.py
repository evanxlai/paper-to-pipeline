"""gem5 config script: one ARM guest binary in syscall emulation (SE) mode.

gem5 runs it as

    <gem5.opt> [--redirect-stderr] --outdir=D se_o3.py --cmd /abs/bin \
        [--options "a b"] [--cwd /abs/dir] [--maxinsts N] \
        [--cond-bp TAGE_SC_L_64KB] [--cpu o3|atomic]

Both ways the loop runs a workload come through here: the adapter's
run_traces (via chia's Gem5Node.run_gem5) and run_workload.py in the agent's
shell. They build the same arguments from the same manifest entry.

A classic config on purpose, not the stdlib board. Every stat then starts
with `system.cpu`, which is the prefix chia's run_gem5 looks for
(`system.cpu.numCycles`, or it reports "parse_failed") and the prefix
p2p_metrics.STATS_KEYS names.

Determinism. G2 compares a feature-off run with a recorded baseline at
rel_tol 0, so two runs of one workload must be identical. The guest sees
only what this script and the manifest fix:

  - argv, env and cwd. The guest's initial stack holds argv, envp and
    argv[0] as AT_EXECFN, at a fixed base of 0x7fffff0000
    (src/arch/arm/process.cc:96, 355-359, 425-432). A different env string
    moves every stack address. So the guest env is GUEST_ENV below and never
    the host's. The enable knob lives in the HOST environment of the gem5
    process, where the port's C++ reads it. It is never in the guest's argv
    or env, so it cannot move the guest's stack. One path remains, through
    files. SE mode passes a guest's open() to the host, apart from a short
    emulated list (src/sim/syscall_emul.hh:931-944), and
    System.redirect_paths is empty (src/sim/System.py:119). So a guest that
    opened /proc/self/environ would read gem5's own env, knob included, and
    /proc/self/cmdline or /proc/self/stat would show gem5's argv (with the
    per-run outdir) and pid. No current workload opens a /proc path (a
    qemu-aarch64-static -strace check when the workloads were built). A new
    workload must pass the same check: see hosts/gem5/NOTES.md, "The enable
    knob is an environment variable".
  - stdio. The guest's stdout and stderr go to files in the outdir, and its
    stdin is /dev/null. glibc sizes a stdio buffer from fstat() of the fd,
    and the host fd would otherwise be a pipe under run_gem5 and something
    else in a shell. Files make both paths see the same kind of fd.
  - randomness. getrandom() draws from gem5's PRNG with the fixed global
    seed 5489 (src/sim/syscall_emul.hh:3261-3275, src/base/random.cc:79).
    The AT_RANDOM bytes are zero (src/arch/arm/process.cc:418).
  - paths. --cmd and --cwd must be absolute, so no host cwd leaks in.
    readlink("/proc/self/exe") returns realpath(--cmd)
    (src/sim/syscall_emul.hh:1095-1118), so the run dir must be the same
    path on every run. Both callers use GEM5_RUN_DIR.

This script reads no P2P_* or SR_* variable. The knob belongs to the port.

gem5 v25.1.0.0 (commit 7a2b0e4) facts this file relies on, file:line in that
tree, are cited where each is used.
"""

import argparse
import json
import os
import shlex
import sys

import m5
import m5.objects
from m5.objects import (
    ArmAtomicSimpleCPU,
    ArmO3CPU,
    BranchPredictor,
    Cache,
    ConditionalPredictor,
    DDR3_1600_8x8,
    MemCtrl,
    Process,
    Root,
    SEWorkload,
    SrcClockDomain,
    System,
    SystemXBar,
    VoltageDomain,
)
# AddrRange is a param type, not a SimObject. m5.params exports it
# (src/python/m5/params/__init__.py:114, param_types.py:515).
from m5.params import AddrRange

# glibc 2.35 registers an rseq area at startup. gem5 v25.1 maps AArch64
# syscall 293 (rseq) to ignoreWarnOnceFunc (src/arch/arm/linux/se_workload.cc:
# 789), which returns 0 (src/sim/syscall_emul.cc:91-103). So rseq is not
# fatal, but glibc then believes the kernel keeps its rseq area current, and
# gem5 never writes it. The tunable makes glibc skip the call and record that
# registration failed, which is the truth. Either way the run is
# deterministic. This way the guest's view matches gem5's.
GUEST_ENV = ["GLIBC_TUNABLES=glibc.pthread.rseq=0"]

# Names are relative to the outdir: gem5 opens a non-standard output name
# with simout.resolve() (src/sim/fd_array.cc:313-317).
GUEST_STDOUT = "guest_stdout.txt"
GUEST_STDERR = "guest_stderr.txt"
GUEST_STDIN = "/dev/null"

# The causes this script expects from m5.simulate().
#   exit_group() / exit() of the last thread: exitSimLoop with the guest's
#   status & 0xff as the code (src/sim/syscall_emul.cc:250).
GUEST_EXIT_CAUSE = "exiting with last active thread context"
#   max_insts_any_thread: a LocalSimLoopExitEvent with code 0
#   (src/cpu/base.cc:774-779, 852, src/sim/sim_events.cc:165-168).
MAX_INSTS_CAUSE = "a thread reached the max instruction count"
# Any other cause is not a finished workload. gem5 exits with this.
UNEXPECTED_EXIT_STATUS = 1

# Clocks and memory: configs/common/Options.py defaults (--sys-clock 1GHz
# at :124-127, --cpu-clock 2GHz at :340-343). Memory is 2 GiB, not that
# file's 512MiB (:155-158), so a perf-sized workload has headroom. SE mode
# takes every guest page from this range. DDR3_1600_8x8 is 8 GiB of devices
# (src/mem/DRAMInterface.py:287-304). A smaller range only warns
# (src/mem/dram_interface.cc:688-692).
SYS_CLOCK = "1GHz"
CPU_CLOCK = "2GHz"
MEM_SIZE = "2GiB"

# ARM instructions are 4 bytes, so the low two PC bits carry nothing. The
# param's own help text says to shift by 2 on Arm
# (src/cpu/pred/BranchPredictor.py:205-214), and gem5's Arm core configs do
# (configs/common/cores/arm/O3_ARM_v7a.py:155, neoverse_v2.py:229). The
# conditional predictor, its TAGE and SC, and the BTB inherit it through
# Parent.instShiftAmt (BranchPredictor.py:129-130, 155-156, 298-299).
INST_SHIFT_AMT = 2


# Classic caches with configs/common/Caches.py's values (:52-78) and
# configs/common/Options.py's sizes and associativities (:191-197). They are
# defined here, not imported, because this script is installed outside the
# gem5 tree and cannot import configs/common.
class L1ICache(Cache):
    size = "32KiB"
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    is_read_only = True
    writeback_clean = True


class L1DCache(Cache):
    size = "64KiB"
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20


class L2Cache(Cache):
    size = "2MiB"
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    write_buffers = 8


def _glue_option_values(argv, names=("--options",)):
    """`--options VALUE` -> `--options=VALUE`, before argparse sees it.

    Both callers pass the guest's argv as two tokens, `--options` and one
    string. argparse reads a following token that starts with "-" and holds
    no space as another flag, so a workload whose only argument is `-q`
    would fail with "expected one argument". The `=` form is always a value.
    """
    out, i = [], 0
    while i < len(argv):
        if argv[i] in names and i + 1 < len(argv):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def parse_args(argv):
    argv = _glue_option_values(list(argv))
    p = argparse.ArgumentParser(prog="se_o3.py", description=__doc__.splitlines()[0])
    p.add_argument("--cmd", required=True, help="absolute path of the guest binary")
    p.add_argument("--options", default="",
                   help="guest argv after argv[0], split with shlex")
    p.add_argument("--cwd", default=None,
                   help="guest working directory (default: the directory of --cmd)")
    p.add_argument("--maxinsts", type=int, default=0,
                   help="stop after N instructions (0 = no limit)")
    p.add_argument("--cond-bp", default="TAGE_SC_L_64KB",
                   help="conditional predictor class in m5.objects")
    p.add_argument("--cpu", choices=("o3", "atomic"), default="o3",
                   help="o3 (default), or atomic to count instructions fast")
    return p.parse_args(argv)


def fail(message):
    """Stop before simulating, with a reason and a non-zero status.

    An int, always. gem5's main() returns SystemExit.code cast to int
    (src/sim/main.cc:86-94), and a string or None there fails the cast."""
    print(f"se_o3.py: {message}", file=sys.stderr, flush=True)
    sys.exit(2)


def conditional_predictor(name):
    """The class named by --cond-bp, checked to be a conditional predictor.

    BranchPredictor.conditionalBranchPred takes a ConditionalPredictor
    (src/cpu/pred/BranchPredictor.py:240-242). A whole-unit class such as
    GshareBP subclasses BranchPredictor instead (:1162) and cannot go there.

    An abstract class (TAGE_SC_L, TAGEBase's users) is refused here too.
    gem5 would otherwise fail later, at instantiate (src/python/m5/
    SimObject.py:1322-1323). Each class records its own `abstract` in
    _value_dict, False unless it says so (SimObject.py:175-176, 189)."""

    def concrete(c):
        return (isinstance(c, type) and issubclass(c, ConditionalPredictor)
                and not getattr(c, "_value_dict", {}).get("abstract", False))

    cls = getattr(m5.objects, name, None)
    if concrete(cls):
        return cls
    known = sorted(n for n, c in vars(m5.objects).items() if concrete(c))
    fail(f"--cond-bp {name!r} is not a concrete conditional predictor class "
         f"in m5.objects. Known: {', '.join(known)}")


def build_system(args, guest_argv, guest_cwd):
    system = System()
    # A system clock and a CPU clock, each with its own voltage domain, as
    # configs/deprecated/example/se.py:199-222 wires them. The CPU and
    # everything under it (its caches and its L2 bus) take the CPU clock.
    # The system bus and the memory controller take the system clock.
    system.voltage_domain = VoltageDomain()
    system.clk_domain = SrcClockDomain(clock=SYS_CLOCK,
                                       voltage_domain=system.voltage_domain)
    system.cpu_voltage_domain = VoltageDomain()
    system.cpu_clk_domain = SrcClockDomain(clock=CPU_CLOCK,
                                           voltage_domain=system.cpu_voltage_domain)

    cpu_cls = ArmO3CPU if args.cpu == "o3" else ArmAtomicSimpleCPU
    # O3 needs timing mode and atomic needs atomic mode. Each class says
    # which (src/cpu/o3/BaseO3CPU.py:62-63,
    # src/cpu/simple/BaseAtomicSimpleCPU.py:54-55).
    system.mem_mode = cpu_cls.memory_mode()
    system.mem_ranges = [AddrRange(MEM_SIZE)]

    # system.cpu, so every CPU stat is system.cpu.* (see the module docstring).
    # ArmO3CPU and ArmAtomicSimpleCPU: src/arch/arm/ArmCPU.py:46-47, 62-63.
    # The ISA-prefixed names are what m5.objects exports in v25.1.
    system.cpu = cpu_cls()
    system.cpu.clk_domain = system.cpu_clk_domain

    if args.cpu == "o3":
        # The conditional predictor is one component of the unit.
        # BranchPredictor (cxx BPredUnit) holds a BTB, a RAS and an indirect
        # predictor with defaults, and conditionalBranchPred has no default
        # (src/cpu/pred/BranchPredictor.py:199-248). The O3 CPU takes the
        # unit in its branchPred param (src/cpu/o3/BaseO3CPU.py:202-206).
        # Its stats are then system.cpu.branchPred.*.
        system.cpu.branchPred = BranchPredictor(
            conditionalBranchPred=conditional_predictor(args.cond_bp)(),
            instShiftAmt=INST_SHIFT_AMT,
        )

    system.membus = SystemXBar()
    if args.cpu == "o3":
        # Private L1I and L1D, an L2 bus, and a private L2, all under the
        # CPU (src/cpu/BaseCPU.py:197-229). With no walker caches the ARM
        # MMU's table walker port ("mmu.walker.port",
        # src/arch/arm/ArmMMU.py:127-128) joins the L2 bus too (BaseCPU.py:
        # 211-212). The ports left to connect are then the L2's mem_side.
        system.cpu.addTwoLevelCacheHierarchy(L1ICache(), L1DCache(), L2Cache())
    # ArmInterrupts has no ports, so this only creates the object
    # (BaseCPU.py:173-176, 310-333).
    system.cpu.createInterruptController()
    # For O3: the L2's mem_side. For atomic, with no caches: icache_port,
    # dcache_port and the walker port straight to the bus
    # (BaseCPU.py:168, 178-195, 307).
    system.cpu.connectAllPorts(system.membus.cpu_side_ports,
                               system.membus.cpu_side_ports,
                               system.membus.mem_side_ports)
    system.system_port = system.membus.cpu_side_ports

    # One memory controller with one DDR3 interface (src/mem/MemCtrl.py:57-70,
    # src/mem/AbstractMemory.py:51), as configs/learning_gem5/part1/
    # simple-arm.py:52-55 wires it.
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8(range=system.mem_ranges[0])
    system.mem_ctrl.port = system.membus.mem_side_ports

    # The guest process (src/sim/Process.py:34-75). executable and cmd[0]
    # are the same string: gem5 loads `executable` (src/sim/process.cc:124,
    # 576) and puts cmd[0] on the stack as argv[0] and AT_EXECFN. cwd is set
    # because the param's default is the HOST's getcwd() (Process.py:72).
    process = Process()
    process.executable = args.cmd
    process.cmd = [args.cmd] + guest_argv
    process.cwd = guest_cwd
    process.env = list(GUEST_ENV)
    process.input = GUEST_STDIN
    process.output = GUEST_STDOUT
    process.errout = GUEST_STDERR

    # The only SE workload that accepts an arm64 Linux ELF is ArmEmuLinux
    # (src/arch/arm/ArmSeWorkload.py:37-48). init_compatible picks it and
    # raises for a file that is not an object gem5 can load
    # (src/sim/Workload.py:145-177).
    system.workload = SEWorkload.init_compatible(args.cmd)
    system.cpu.workload = process
    if args.maxinsts > 0:
        # "terminate when any thread reaches this inst count"
        # (src/cpu/BaseCPU.py:139-141), scheduled at init (src/cpu/base.cc:
        # 331-336).
        system.cpu.max_insts_any_thread = args.maxinsts
    system.cpu.createThreads()
    return system


def exit_status(cause, code):
    """gem5's process exit status for the way the simulation ended.

    The guest's own code when the guest exited. 0 when --maxinsts stopped
    it, since that is the requested end. UNEXPECTED_EXIT_STATUS for any
    other cause, even with code 0, because such a run did not finish the
    workload and must not read as a success."""
    if cause == GUEST_EXIT_CAUSE:
        return int(code) & 0xFF
    if cause == MAX_INSTS_CAUSE:
        return 0
    return UNEXPECTED_EXIT_STATUS


def main(argv):
    args = parse_args(argv)
    if not os.path.isabs(args.cmd):
        fail(f"--cmd must be an absolute path, got {args.cmd!r}")
    if not os.path.isfile(args.cmd):
        fail(f"--cmd {args.cmd} does not exist")
    guest_cwd = args.cwd if args.cwd is not None else os.path.dirname(args.cmd)
    if not os.path.isabs(guest_cwd):
        fail(f"--cwd must be an absolute path, got {guest_cwd!r}")
    if not os.path.isdir(guest_cwd):
        fail(f"--cwd {guest_cwd} is not a directory")
    if args.maxinsts < 0:
        fail(f"--maxinsts must be 0 or more, got {args.maxinsts}")
    try:
        guest_argv = shlex.split(args.options)
    except ValueError as e:
        fail(f"--options {args.options!r} does not split with shlex: {e}")

    system = build_system(args, guest_argv, guest_cwd)
    print("P2P_CONFIG " + json.dumps({
        "cpu": args.cpu,
        "cond_bp": args.cond_bp if args.cpu == "o3" else None,
        "argv": [args.cmd] + guest_argv,
        "cwd": guest_cwd,
        "env": GUEST_ENV,
        "maxinsts": args.maxinsts,
    }, sort_keys=True), flush=True)

    # No local name needed: Root keeps its one instance itself, and
    # instantiate() finds it there (src/sim/Root.py:35-53).
    Root(full_system=False, system=system)
    m5.instantiate()
    event = m5.simulate()
    # getCause() and getCode() are GlobalSimLoopExitEvent's
    # (src/sim/sim_events.hh:98-99, bound in src/python/pybind11/event.cc:
    # 140-141).
    cause, code = event.getCause(), event.getCode()

    # Dump now, so stats.txt is complete before the P2P_EXIT line says the
    # run ended. gem5 would otherwise dump from an atexit handler during
    # interpreter shutdown (src/python/m5/simulate.py:260-262). That second
    # dump is then skipped, because gem5 allows one global dump per tick
    # (src/python/m5/stats/__init__.py:406-414). So stats.txt holds one block.
    m5.stats.dump()

    status = exit_status(cause, code)
    print(f"P2P_EXIT cause={cause} code={code}", flush=True)
    # A SystemExit leaving the config script becomes gem5's exit status:
    # m5.main() lets it propagate (src/python/m5/main.py:687) and gem5's C++
    # main returns its code (src/sim/main.cc:86-94).
    sys.exit(status)


# gem5 runs a config script with __name__ == "__m5_main__"
# (src/python/m5/main.py:663), not "__main__".
if __name__ in ("__m5_main__", "__main__"):
    main(sys.argv[1:])
