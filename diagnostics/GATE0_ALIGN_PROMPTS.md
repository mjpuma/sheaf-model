# Gate 0 alignment prompts (A-queue)

Paste **exactly one** prompt per session. Template and hard stops:
[`GATE0_CONTINUE.md`](GATE0_CONTINUE.md). Strategy:
[`GATE0_ALIGN.md`](GATE0_ALIGN.md). Do not start G1.

Living next-paste: [`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md).

## Adaptive rule (first match wins)

| If the last run showed… | Next paste | Skip |
|---|---|---|
| `align_inventory.md` **absent** | **A1** | do not implement remaining NLP; do not copy Julia |
| A1 present; `align_scorecards.md` **absent** | **A3** | do not mix Fig. 4 1.004 into Bar A |
| A3 present; A1 marks an implement-now **B** or sourced wheat law | **A4** | one row only; re-measure last/first **and** moy |
| Team sent a 14022004 undisturbed monthly; not scored | **A5** | not Fig. 4 NetCDF; do not vendor Julia |
| Else | **leave labelled** | wait for team series; do not start G1 |

Hard stops do not adapt.

## Shared preamble (prepend to every A-prompt)

```
You are continuing SHEAF Gate 0 wheat: an independent Agrimate copy
(Kuhla et al. 2025; sheaf/agrimate/). Read diagnostics/GATE0_CONTRACT.md,
diagnostics/DEVELOPMENT.md, diagnostics/GATE0_ALIGN.md,
diagnostics/GATE0_ALIGN_PROMPTS.md, diagnostics/GATE0_CONTINUE.md,
diagnostics/gate0_agrimate/rt_solver.md, diagnostics/gate0_agrimate/t2_delta.md,
and this prompt's "Read first" files before editing.

NEVER cheat.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not restore L1–L8. Do not pin the unforced world price to 2006.
- Do not retune αI, p_sto, xmin, or λ to Pink Sheet or Bai α_foreign=10.
- Do not treat FAOSTAT FBSH element 5074 ΔS as a stock level.
- Do not copy author Julia into sheaf/agrimate/.
- Do not write freeze_q_oth into wheat_params().
- Do not freeze D.22 (author still updates).
- wheat_params() stay 14022004 defaults (αI=3.2, ζ=0, N_for=3).
- Fig. 4 knobs stay on fig4_experiment_params(). Exact Fig. 4 is later.
  USDA stays prepare_wheat. Do not invent Egypt.
- Do not treat last/first motion toward 1 as item-3 progress without moy.

Already done (do not re-do):
- D.22 vector+shift live. x1-fixed scipy SLSQP live. rt-solver recorded.
- Clearing loop live (prorata, posted prices, share update, tx index).
- α_adj cap 1 live on prepare_wheat. D.9 stays on Fig. 4 apply_alpha_i.
- Uniform remaining-grain x_init live. Pulse remains (Jan1 cheap / Jan2 empty).
- B1 live months volume-weight the two half-steps (plot.jl basket).
- B2 domestic D.7 live (`(xd + share_imp·Q) / C*`). Pulse remains.
- B3 harvest horizon live (raw now + N_year D.1 slots). Pulse remains.
- Harvest+AMIS three-scenario CSVs are the S1 snapshot; do not clobber.
- Do not raise plan_maxiter. Unconverged 5125/5832 is not a reason to.

Exit: pytest tests/agrimate. One prompt, one PR-sized change.
Rewrite diagnostics/GATE0_REPRO_DISPATCH.md from this run (≤20 lines).
Next session pastes that file's **Next paste**.
```

---

## A1 — Wheat-path inventory (inspect-only)

```
[SHARED PREAMBLE]

Task A1 only. Inspect-only line-by-line of the 14022004 wheat *control
flow* versus sheaf/agrimate/. Do not copy Julia into sheaf/agrimate/.
Do not implement. Do not pin. Do not freeze. Do not retune αI.
Do not start G1. Do not re-run 2003–11. Do not clobber three-scenario CSVs.

Read the author tree (inspect, do not vendor): model.jl, run.jl,
producer.jl, consumer.jl, producer_optimization.jl, initialization.jl,
observation.jl, expected_harvests.jl. Host: model.py, optimize.py,
equations.py, wheat_data.py. Reuse T2 rows for D.22/solver; do not
re-litigate them.

Write diagnostics/gate0_agrimate/align_inventory.md: one row per
mechanism (init, harvest expectation, x1 lock, supplier programme,
transactions, purchaser CES, consumer, delivery/Ndel, D.22, world
price, observation). Columns: author file:line, host file:line,
class (H/B/C/D/E/G), implement-now (yes/no). Rank at most three
implement-now rows. Line-by-line means the loop, not a transcription.

Read first: GATE0_ALIGN.md, t2_delta.md, rt_solver.md, GATE0_SPEC_MATRIX.md.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste A3 if the inventory
exists; else retry A1. Do not start G1.
```

---

## A3 — Split Bar A / Bar B scorecards

```
[SHARED PREAMBLE]

Task A3 only. Split item-3 scoring so Fig. 4 last/first 1.004 is no
longer the 14022004 twin. Write diagnostics/gate0_agrimate/align_scorecards.md.
Bar A: this host (last/first AND moy AND seasonal corr) on wheat_params
USDA C.1. Bar B: Fig. 4 experiment later (labelled; knobs stay on
fig4_experiment_params()). Do not re-run the NLP. Do not retune.
Do not invent Egypt. USDA stays prepare_wheat. Do not start G1.

Read first: GATE0_ALIGN.md, rt_solver.md, fig4.md, item3.md, A1 inventory.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste follows the adaptive
table. Do not start G1.
```

---

## A4 — One inventory row (only if A1 said implement-now)

```
[SHARED PREAMBLE]

Task A4 only. Implement at most one A1 row marked implement-now
(class B, or a sourced 14022004 wheat law the host does not do).
Independent Python. Do not copy Julia. Do not freeze. Do not pin.
Do not raise plan_maxiter. Do not start G1. Re-measure undisturbed
last/first AND moy. Do not clobber harvest+AMIS three-scenario CSVs.

If A1 has no implement-now row, do not invent one. Leave labelled.

Read first: align_inventory.md, rt_solver.md, optimize.py, model.py.

End: rewrite GATE0_REPRO_DISPATCH.md. Do not start G1.
```

---

## A5 — Obtain-or-leave 14022004 twin series

```
[SHARED PREAMBLE]

Task A5 only. Obtain-or-leave a 14022004 wheat undisturbed monthly
world-price series (same executable family as sheaf/agrimate, not
Zenodo 10688435 Fig. 4 NetCDF). Score last/first AND moy against
prices_undisturbed_solver_x1.csv. Label the obtain or the miss.
Do not vendor Julia. Do not adopt Fig. 4 knobs. Do not start G1.

Read first: GATE0_AGRIMATE_BRIEF.md, GATE0_ALIGN.md, rt_solver.md.

End: rewrite GATE0_REPRO_DISPATCH.md. Do not start G1.
```

A2 (team questions) lives in [`GATE0_AGRIMATE_BRIEF.md`](GATE0_AGRIMATE_BRIEF.md).
That is a human paste to the Agrimate team, not an agent session.

Post x-init Bar A queue: [`GATE0_B_PROMPTS.md`](GATE0_B_PROMPTS.md)
(B1 months, B2 domestic others, B3 horizon, B4 leftovers). Do not
paste A1–A4 again.
