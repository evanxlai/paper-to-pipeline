# Ablation matrix

The proposal commits to two ablations. Each cell below is one loop run. The run directory name encodes the cell, for example `results/champsim-192k-tuned-paperonly/`.

## Ablation 1: naive port vs. tuned port

This ablation measures how much of a fair evaluation depends on DSE.

| Host | Budget | Naive (paper defaults) | Tuned (DSE winner) |
|---|---|---|---|
| ChampSim | 192 KiB | run | run |
| ChampSim | 64 KiB | run | run |
| gem5 TAGE-SC-L | 192 KiB | run | run |
| gem5 TAGE-SC-L | 64 KiB | run | run |

The naive arm takes the parameter defaults from the distilled spec with no host rebalance. The tuned arm takes the DSE winner at the same total budget.

## Ablation 2: paper-only vs. paper-plus-reference

This ablation measures how far the loop gets without reference code. Both arms run the full loop from distillation through the gate.

| Input mode | Distilled spec | Gate result | Tuned MPKI delta |
|---|---|---|---|
| paper_only | `spec/sr.paper_only.json` | record | record |
| paper_plus_reference | `spec/sr.paper_plus_reference.json` | record | record |

## Yardstick

The CBP2025 node runs the unmodified RUNLTS artifact at 192 KiB. It won CBP2025 at BrMisPKI 3.197 on the training traces, against 3.408 for the authors' tuned 192 KiB TAGE-SC-L. The paper gives no scalar for the sR component alone, so week 1 adds an sR-off ablation of the artifact to measure it. That measured delta anchors the target: the tuned ports must recover at least 50 percent of it.
