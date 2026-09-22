"""The CBP2025 kit as a production host for stages 2, 3 and 4.

`adapter.py` holds the three things the loop needs and nothing else: a shell
that runs on the machine holding the checkout, a `plan_runner.HostExecutor`
over it, and the `HostAdapter` stage 3 drives. `NOTES.md` is the file the
planning and integration agents read.
"""
