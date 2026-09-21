# Gate 0 alignment strategy (post rt-solver)

**Yes, a new strategy is needed.** Not a new science: still Gate 0 wheat,
still an independent Python copy, still no G1/G2, still no 2006 pin,
still no αI retune. The *process* that got us here is what failed.

Working with the Agrimate team, with 14022004 Julia in hand, is the
reason we can change process now. It is not a reason to vendor `*.jl`
into `sheaf/agrimate/` or to treat Fig. 4 NetCDF as the 14022004 twin.

## Situation (evidence, not mood)

| bar | live host | Agrimate |
|---|---|---|
| G0-P | **not accepted** | — |
| Item 3 last/first | 0.812 (`score_solver_x1.csv`) | Fig. 4 baseline **1.004** |
| Undisturbed moy | **2374×** | Fig. 4 baseline **1.32×** (S1 undisturbed was 27×) |
| Hike 2008 | ×3.71 (S1 CSV, not re-run) | Fig. 4d ×1.62 |
| Unconverged | 1091/5832 x1-SLSQP; 2304/5832 S1 harvest+AMIS | NLopt `maxtime=60` |
| Source | 14022004 wheat_params, USDA C.1 27 | Fig. 4 is a *different* git + knobs + regions + FAO |

D.22 then x1-SLSQP were the “remaining sourced deltas.” They moved
last/first 1.444 → 0.772 → 0.812 (undershoot) and *worsened* seasonal
collapse (27× → 1792× → 2374×). `rt_solver.md`: last/first is a weak
repeating statistic; 1.004 is Zenodo 10688435 Fig. 4 (A7), not this
executable. Implementing the next NLP fragment against that 1.004
target is the same mistake.

## What failed

One mechanism per prompt, scored as “closer to Fig. 4 last/first = 1.”
That mixed DEVELOPMENT item 1 (14022004 source fidelity) with item 4
(Fig. 4 experiment) and used item 3’s last/first as if it were
amplitude. T1/T2 inspected **D.22 and the solver algorithm only**.
They did not inventory the wheat *loop* (init, purchase, transactions,
delivery, world price).

## What to do instead

Split two bars. Do not mix them in one last/first number.

**Bar A — 14022004 wheat executable** (this host). Independent Python
of `agrimate-equal-sales-penalty` (`two_markets=true`, αI=3.2, ζ=0,
N_for=3) on USDA C.1. Score repeating by last/first **and** moy
max/min **and** seasonal corr. The twin series is a 14022004
undisturbed monthly path (ask the team), not Fig. 4 NetCDF.

**Bar B — Fig. 4 experiment** (later). AgrimateEU28+Egypt, FAO since
2005, αI=3.5, ζ=1, N_for=6, start 2000, `old-demand-dynamics`. Knobs
stay on `fig4_experiment_params()`. Egypt is not invented on C.1.

## Is a line-by-line assessment needed?

**Yes, scoped. No, not a Julia transcription.**

Needed (next session, **A1**): one inspect-only inventory of the
wheat *control flow* against the 14022004 tree still on disk
(`model.jl`, `run.jl`, `producer.jl`, `consumer.jl`,
`producer_optimization.jl`, `initialization.jl`, `observation.jl`,
`expected_harvests.jl`) versus `sheaf/agrimate/{model,optimize,equations,wheat_data}.py`.
One row per mechanism: author file:line, host file:line, class
(H/B/C/D/E/G), implement-now? **Do not copy `*.jl` into sheaf.**

Not needed: pasting NLopt/Julia into Python; re-doing T2’s D.22
file:line; implementing remaining NLP fragments before the inventory;
a line-by-line of GitLab 2023 one-market code (not the wheat path).

The team collaboration is for **Bar A twin series** and for questions
only the authors can close (which git is Fig. 4d? what is the plotted
world price?). Questions: `GATE0_AGRIMATE_BRIEF.md`. Do not wait to
start A1.

## What not to do next

- Do not implement another solver fragment (horizon `N_hor+1`,
  quantity inequalities, `x_init`, domestic others) until A1 ranks it.
- Do not freeze D.22. Do not pin 2006. Do not retune αI.
- Do not start G1/G2. Do not restore L1–L8.
- Do not treat last/first motion toward 1 as item-3 progress.

Pasteable queue: [`GATE0_ALIGN_PROMPTS.md`](GATE0_ALIGN_PROMPTS.md).
Living next-paste: [`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md).
