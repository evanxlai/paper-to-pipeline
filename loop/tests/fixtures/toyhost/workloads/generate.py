#!/usr/bin/env python3
"""Regenerate the toy host's workloads. Committed output, deterministic input.

The mix is chosen so the two gate questions have different answers:

* a bimodal predictor indexed by PC alone does well on the biased branches and
  badly on the two history-correlated ones, so the recorded baseline has real
  headroom;
* that headroom is only reachable by a predictor that consults global branch
  history, which is exactly what the feature under test adds. A port that
  builds, stays baseline-identical with its knob off, and still does not move
  the metric is therefore a port whose mechanism is wrong, not one that merely
  needs tuning.

Branches are emitted round-robin over the PCs so global history is a clean
function of position in the stream.
"""

import random
from pathlib import Path

HERE = Path(__file__).resolve().parent


def emit(path: Path, rounds: int, seed: int) -> None:
    rng = random.Random(seed)
    lines = []
    for i in range(rounds):
        # Period-4 pattern: bimodal oscillates, history-indexed nails it.
        lines.append(("0x400100", int(i % 4 in (0, 1))))
        # Alternating: the worst case for a two-bit counter.
        lines.append(("0x400200", i % 2))
        # Strongly taken: bimodal already correct.
        lines.append(("0x400300", int(rng.random() < 0.95)))
        # Strongly not-taken: bimodal already correct.
        lines.append(("0x400400", int(rng.random() < 0.05)))
        # Unpredictable: neither predictor can help.
        lines.append(("0x400500", int(rng.random() < 0.5)))
    body = "".join(f"{pc} {taken}\n" for pc, taken in lines)
    path.write_text(
        "# <pc_hex> <taken>; regenerate with workloads/generate.py\n" + body
    )


if __name__ == "__main__":
    emit(HERE / "smoke.trace", rounds=200, seed=1)
    emit(HERE / "bias.trace", rounds=1200, seed=2)
