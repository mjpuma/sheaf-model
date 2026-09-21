# Red team — solver last/first 0.812 and the continued mismatch

CSV recompute. **Not** an NLP re-run. Not a freeze. Not a pin.
Not L1–L8. Not an αI retune. Not Fig. 4. Do not copy Julia.
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3, plan_maxiter=40.
G1/G2 stay blocked. D.22 and x1-SLSQP stay live.

## Verification protocol (CLAUDE.md)

1. **Claim.** `solver_x1.md`: live x1-fixed scipy SLSQP on the
   14022004 wheat path; undisturbed last/first **0.812** vs
   author Fig. 4 baseline **1.004**; quiet-year USD ~$305 vs
   S1 $46; item 3 still fail. Class H on the solver.

2. **Implementation (inspected, not re-run).**
   `solve_supplier_plan(..., x1=)` locks step 0 and SLSQP-s
   the rest (`optimize.py`). Live `AgrimateSim.run` builds D
   from last CES requests. R5 inflow stays T* (default off).
   Score object: `prices_undisturbed_solver_x1.csv`.

3. **Match (measurement).** Independent recompute of that CSV
   on 2006–11: last/first **0.812**, 2006 mean
   $304.92/t, 2011 mean
   $247.53/t. USD ratio equals
   the committed `score_solver_x1.csv` row. Not a scoring bug.

4. **Counterexample to “0.812 means we are close to Agrimate.”**
   last/first is the ratio of *annual means*. On the same
   window the host month-of-year max/min is
   **2374×** vs author baseline
   **1.32×**. Window min/max $0.33–$1772/t. Seasonal *shape*
   still repeats (corr 0.987;
   author 0.991). Amplitude
   does not. S1 undisturbed moy was 27×; D.22 1792×; solver
   2374×. Sourced D.22+x1 moved last/first 1.444→0.772→0.812
   (undershoot) while *worsening* the collapse. Two-sided
   item 3 [1/1.1, 1.1] still **fail**.

5. **Counterexample to “1.004 is this host’s twin.”** Author
   1.004 is Zenodo 10688435 Fig. 4 *baseline* (A7):
   AgrimateEU28+Egypt, FAO since 2005, α_foreign=3.5, ζ=1,
   N_for=6, start 2000, git `old-demand-dynamics`. Host is
   14022004 `wheat_params()` (αI=3.2, ζ=0, N_for=3), USDA
   C.1 27, start 2003. Fig. 4 knobs stay on
   `fig4_experiment_params()`. Not adopted.

6. **Counterexample to class H on the remaining programme.**
   x1 lock + SLSQP *family* match sourced wheat. Remaining
   14022004 deltas (inspect-only; 0 `*.jl` in sheaf):
   - Horizon: author `H=vcat(harvest, expected)` length
     `N_hor+1`, free `n=2:N_hor+1` (`producer_optimization.jl`
     68–72). Host free block is `N_hor-1`.
   - Variables: author quantities + availability inequality
     (97–108). Host fractions, S≥0 identically (N1).
   - Start: author overwrites `x_init` with uniform remaining
     stock (`producer_optimization.jl` 349–351) and retries
     on `XTOL` (367–385); `maxtime=60`. Host uses the previous
     plan; `plan_maxiter=40` (N5).
   - Current profit: author `revenue_curve` of demand requests
     (producer.jl 106–117; optimization 79–82). Host D.7 on
     the locked x1 as well.
   - Domestic D.7: author `(xd + x_oth_dom) / X*_C` with
     `x_oth_dom` a share of expected foreign others
     (producer.jl 160; initialization.jl 151). Host `xd/XD*`,
     no others.
   - Shipments: author `determine_transactions_two_markets`.
     Host `fulfill_sales` then T* inflow (R5 off).
   - Price object: host XI-weighted lagged D.7 offers; Fig. 4d
     is bilateral international transaction price.
   Unconverged **1091/5832** still accepted (N5). Not a unique
   Agrimate maximizer.

7. **Falsification attempts.**
   - Scoring bug: **fails** (CSV last/first matches 0.812).
   - x1 not locked: **fails** (`test_optimize.py` + live `x1=`).
   - $305 is a 2006 pin: **fails** (Pink ~$213; path min $0.33).
   - 0.812 vs 1.004 is *only* a remaining solver bug: **fails**
     as the exclusive story (A7 comparator + amplitude).
   - Closer last/first is item-3 progress: **fails** (two-sided
     bar; moy 27×→2374×).
   A coding bug in last_ask reconstruction is **not
   established**. Remaining labelled C/D are enough to keep
   last/first off 1.004 on this object.

8. **Change.** This note. No economics. No retune. Harvest+AMIS
   three-scenario CSVs untouched. Next paste **leave labelled**.
   Exact Fig. 4 is later. Do not start G1.

## Live recompute (undisturbed, 2006–11, CSV)

| object | last/first | moy max/min | 2006 mean |
|---|---:|---:|---:|
| Host D.22 + x1-SLSQP | 0.812 | 2374× | $304.92/t |
| D.22 only | 0.772 | 1792× | — |
| S1 three-scenario undisturbed | 1.444 | 26.9× | $45.82/t |
| Author Fig. 4 baseline | 1.004 | 1.32× | 1.113 (index) |

G0-P item 3 is **fail** (two-sided [1/1.1, 1.1]).
Host seasonal corr 0.987; author 0.991.
Unconverged 1091/5832; failed 0. NLP not re-run.

## Classification

| finding | class | confidence |
|---|---|---|
| 0.812 recomputes from the committed path | **H** | 95–100% |
| two-sided item 3 still fail vs Fig. 4 1.004 | **H** | 95–100% |
| last/first is a weak repeating statistic (moy 2374×) | **G** | 80–95% |
| Fig. 4 1.004 is a different experiment (A7) | **E** | 80–95% |
| remaining 14022004 NLP deltas listed above | **C**/**D** | 95–100% inspect |
| `solver_x1.md` class H overstated the remaining programme | **G** | 80–95% |
| x1-lock / SLSQP family as independent Python | **H** | 80–95% |
| freeze / 2006 pin / αI retune as the fix | **H** (do not) | 95–100% |

**Next paste: leave labelled.** Do not copy Julia. Do not write
`freeze_q_oth` into `wheat_params()`. Do not start G1.

