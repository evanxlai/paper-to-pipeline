"""gem5 v25.1 (ARM, syscall emulation) as a production host for stages 2 and 3.

`adapter.py` holds what the loop needs and nothing else: a shell on the node
that holds the checkouts, the tree lifecycle (restore, copy, revision), the
build, a `plan_runner.HostExecutor` over one tree, the `HostAdapter` pieces
stage 3 drives, and `record_baseline` for `--stage baseline`. `run/` holds the
run scripts the adapter installs on that node, `workloads.json` names the
workloads, and `NOTES.md` is the file the planning and integration agents
read.

It copies hosts/cbp2025/ on purpose. Every hazard that host met in a real run
has a twin here, and the adapter's docstrings say where each one went.
"""
