"""Host adapters: one build/run/stats surface per simulator, so the gate
and the DSE evaluator stay host-agnostic.

TODO(week 2): implement. Targets:
  cbp2025:  chia_nodes/cbp2025/cbp2025_node.py (done, use directly)
  champsim: wrap chia.simulators.champsim.ChampSimNode
            (build_champsim/run_champsim ship in-tree; binary travels as bytes)
  gem5:     wrap chia.simulators.gem5.Gem5Node
            (build_gem5/run_gem5/parse_gem5_stats; placement-group co-location)
See hosts/<name>/NOTES.md for the integration hook points.
"""


def build_with_params(host: str, params_header: str):
    raise NotImplementedError(f"host adapter not written yet: {host}")


def run_one(host: str, build_artifact, trace: str):
    raise NotImplementedError(f"host adapter not written yet: {host}")
