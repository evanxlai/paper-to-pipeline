# CBP2025 host, 2026-09-22

The artifacts behind the claims in the repository README. Copied out of
`out/`, which is timestamped and untracked, so that the runs that produced
a claim can be read from the repository alone. Nothing here is regenerated
by a later run.

Every file keeps its `out/` timestamp prefix, which is also the run id.
The cluster was one GCP head, two `n2-standard-2` trace workers, and the
CBP2025 kit at commit `607496629452740887dc1b90a46834cc90dda1e0`. Every
stage went through `chia job submit`.

## The runs, in order

| run | stage | outcome |
| --- | --- | --- |
| `093656` | baseline | Built the pristine kit, ran both bundled sample traces, wrote `hosts/cbp2025/baselines/iso-192KiB.json`. |
| `093916` | plan | Accepted on turn 0. No schema errors, no coverage findings. |
| `103740` | plan | Re-planned against the 4-trace gate list. One repair turn: turn 0 covered one of the seven spec unit tests. |
| `104954` | integrate | Built, matched the baseline with the knob off, passed all seven unit tests and both regressions, smoke clean. G5 measured CycWPPKI 43 percent worse. Escalated `/host_interfaces/4`. |
| `130623` | plan | Read that escalation and answered it. `/host_interfaces/4` moved from `fallback` to `exact`. |
| `131818` | integrate | sR now added into the statistical corrector's `LSUM`. G5 measured exactly 0.0000. G2 failed on a baseline pointer the agent is not allowed to change, and it escalated that. |
| `140845` | plan | Answered the pointer escalation, and named the outer `update` overload as a hook point. |
| `143148` | integrate | Stopped by `RESOURCE_EXHAUSTED (429)` from Vertex after seven retries, with the port most of the way written. A model quota, not a fault in the loop. The tree survived. |
| `153419` | integrate | Resumed on that tree with `P2P_CBP2025_PORT_FRESH=0`. First run with G2 passing, and the first where the feature reaches the metric at all: 388.07 to 633.70 CycWPPKI, IPC down 29 percent. Escalated `/correctness/1/feature_state`. |

## What to read first

`20260922_104954_gate_cbp2025_0.json` and
`20260922_104954_plan_escalation_cbp2025.json`, together.

That pair is the loop working. A deterministic gate measured a port that
passed every other check and made the metric 43 percent worse. The agent
did not weaken a test to get past it. It named the value that was not
its to decide, `/host_interfaces/4`, and said why: the plan told it to
override the TAGE-SC-L prediction, and nothing told it how confident its
own sum had to be first.

That escalation was correct, and the fault was in
`hosts/cbp2025/NOTES.md`. The notes said `cbp2016_tage_sc_l.h` was off
limits. In the paper, sR is one term inside that file's statistical
corrector sum, and the adaptive threshold the agent asked for is already
there.

`20260922_131818_*` is the same shape a second time: a correct escalation
about a genuinely wrong frozen value, caused by a documentation gap rather
than by the agent.

`20260922_153419_*` is a third. An `existing_regression` entry asked for
the clean tree's exact measurement row with the feature on. The
`performance` entry in the same plan asked for that row to change. No port
satisfies both, and the agent said so instead of picking one.

Three escalations, three correct, none of them the agent's fault. Two of
the three classes now fail at stage 2 instead, in a repair turn, through
checks added to `loop/plan_checks.py`. The third is recorded in
`hosts/cbp2025/NOTES.md`, which is where the wrong fact was.

## What each file is

- `*_summary.json` - the stage's own return value.
- `*_gate_cbp2025_<n>.json` - one integration attempt's verdict, with every
  blocking reason and every non-blocking warning.
- `*_plan_escalation_cbp2025.json` - the value stage 3 refused, its reason,
  and the gate output it was refusing under.
- `*_plan_cbp2025_rounds.json` - what each planning turn got wrong, which
  is how to tell a plan accepted first time from one that needed repair.
- `*_integrate_cbp2025_diff.patch` - the port, as the agent left it.
- `*_cbp2025_baseline.json` - the recorded baseline G2 holds every port to.
- `*_plan_cbp2025_escalations_answered.json` - which escalations a plan run
  had in front of it.

The full LLM transcripts (`*_integrate_cbp2025_<n>.md`, a few tens of KiB
each) stay in `out/` and are not copied here.
