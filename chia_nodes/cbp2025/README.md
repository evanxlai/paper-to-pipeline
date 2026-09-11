# CBP2025Node

A CHIA node that wraps the CBP2025 simulator kit from https://github.com/ramisheikh/cbp2025 . It follows the conventions of the in-tree `chia/simulators/champsim.py` node, and it is written for upstreaming into that directory.

## Surface

- `CBP2025Node.build(cbp_root, predictor_sources, timeout_s)`: overlays `{relpath: bytes}` sources onto a checkout, runs `make`, and returns the `cbp` binary as bytes. Pass `predictor_sources=None` for the baseline TAGE-SC-L build.
- `CBP2025Node.run(binary, trace_path, extra_args, timeout_s)`: runs one gz trace through a binary shipped as bytes. One run is single-threaded, so a 32-core worker advertises `{"cbp2025": 32}` and each dispatch consumes 1.0.
- `CBP2025Node.aggregate(results)`: arithmetic means of the scoring-window rows, matching the kit's own `scripts/trace_exec_training_list.py`.

## Metrics

The kit scores on the second half of each trace (the "50 Perc" rows). The two contest metrics are `BrMisPKI` (conditional mispredictions per 1000 instructions, the MPKI column) and `CycWpPKI` (wrong-path cycles per 1000 instructions). `aggregate` reports both plus IPC.

## Not done yet

- The stdout parser covers the two summary rows. Per-category breakdowns and the branch-type table are TODO.
- No caching tags yet. Wire `_chia_tag=f"{candidate}_{trace}"` plus a cache YAML before the DSE stage, so reclaimed spot workers reuse finished runs.
