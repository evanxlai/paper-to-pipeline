stats_gapbs_bfs_s.txt is a real gem5 stats.txt, trimmed. It is not made up.

Where it comes from: the first cluster run of the gem5 host on 2026-09-23.
The run was the gapbs_bfs_s workload on gem5 v25.1.0.0 (commit 7a2b0e4), with
the O3 CPU and TAGE_SC_L_64KB, and one stats dump. The full file had 1857
lines (248 KB). Its sha256 was
0e3b7a4a80b8c6a9e15c8366086af03b42659bd0d9f84d4851225d0c56b8e4b5.

How it was trimmed: the file keeps the Begin and End markers of the dump. It
also keeps every line whose name starts with one of these prefixes:

    simInsts
    system.cpu.numCycles
    system.cpu.commitStats0.
    system.cpu.branchPred.
    system.cpu.commit.

Every kept line is byte for byte the line gem5 wrote, in the same order. No
value was changed. The trim only removes lines, so the file holds every stat
that p2p_metrics.STATS_KEYS names. The trim is here and not in the file,
because stats.txt has no comment syntax outside the "#" description column.

loop/tests/test_gem5_run.py reads this file. The numbers it checks:

    system.cpu.commitStats0.numInsts                    2509944
    simInsts                                            2509105 (no NOPs)
    system.cpu.numCycles                                2583914
    system.cpu.branchPred.mispredicted_0::DirectCond      34742
    system.cpu.branchPred.mispredicted_0::IndirectCond        0
    system.cpu.branchPred.mispredicted_0::total           35711
    system.cpu.branchPred.condIncorrect                   35711
