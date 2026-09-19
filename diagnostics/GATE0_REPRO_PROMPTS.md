# Gate 0 reproduction prompt list (post-P12)

Paste **exactly one** prompt per session. Do not skip. Do not open G1/G2.
This queue is the red-team follow-up (`GATE0_REDTEAM.md`): close the
**Agrimate Fig. 4 experiment gap**, not a Pink-Sheet fit.

Living queue: [`DEVELOPMENT.md`](DEVELOPMENT.md). Contract:
[`GATE0_CONTRACT.md`](GATE0_CONTRACT.md). Protocol:
[`GATE0_VALIDATION.md`](GATE0_VALIDATION.md). Data:
[`GATE0_DATA.md`](GATE0_DATA.md). Red team:
[`GATE0_REDTEAM.md`](GATE0_REDTEAM.md).

**Now:** paste **R2**. R1 is done. Everything below R2 is later.
P0–P12 stay done. G0-P is **not accepted**.

## Shared preamble (prepend to every prompt)

```
You are continuing SHEAF Gate 0 wheat: an independent Agrimate copy
(Kuhla et al. 2025; sheaf/agrimate/). Read diagnostics/GATE0_CONTRACT.md,
diagnostics/DEVELOPMENT.md, diagnostics/GATE0_VALIDATION.md,
diagnostics/GATE0_REDTEAM.md, diagnostics/GATE0_DATA.md, and this
prompt's "Read first" files before editing.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not restore L1–L8 (fill-target, calm pin, scarcity blend, ask_rival).
- Do not pin the unforced world price to the 2006 mean.
- Do not retune αI, p_sto, xmin, or λ to Pink Sheet or to Bai's α_foreign=10.
- Do not treat maize/rice as an acceptance target.
- Author AgrimateParams stay the defaults. Bai's fitted knobs are
  alternatives, not ours. Fig. 4 knobs (αI=3.5, ζ=1, N_for=6) belong
  on a named comparison object, not in wheat_params().
- Disabled G1 must recover this single-crop run; disabled G2 must recover
  E.4 AMIS. Those tests are later, not this prompt.
- If claim and code diverge, follow the verification protocol in CLAUDE.md
  (locate claim, locate code, counterexample, correctness argument) before
  changing economics. Data adaptations stay labelled in GATE0_DEPARTURES.md.

Exit: pytest tests/agrimate; if you touch the runner, re-run
PYTHONPATH=. python scripts/run_agrimate_validation.py and update
diagnostics/gate0_agrimate/. One prompt, one PR-sized change.
```

## Status

| ID | Prompt | Status |
|---|---|---|
| P0–P12 | Original Gate 0 queue | **done** (G0-P note written, **not accepted**) |
| **R1** | Red team + data cookbook | **done** |
| **R2** | Labelled Fig. 4-config comparison run | **next** |
| R3 | World-price recipe vs author plot | queued |
| R4 | Undisturbed XI-split characterisation | queued |
| R5 | S4 x1=demand labelled experiment | queued |
| R6 | FAOSTAT FB obtain-or-leave | queued / maybe stop |
| R7 | A8 mean-vs-sum sensitivity (do not rewrite host) | queued |
| R8 | Expand Fig. 4 *score* tests (honest FAIL until match) | queued |
| R9 | N5 on the Fig. 4 config | queued |
| R10 | Score Fig. 4 config vs author hike/drift/amplitude | queued |
| R11 | Re-run default three-scenario only if defaults changed (they must not) | queued |
| R12 | Methods note v2 | after R10 |
| — | G1 / G2 | **blocked until G0-P accepted** |

---

## R1 — Red team + data cookbook (done)

```
[SHARED PREAMBLE]

Task R1 only. Full-mode red team of the live host against Agrimate
reproduction. 12 steps. Check tests, archive, and automated downloads.
Write GATE0_REDTEAM.md and GATE0_DATA.md. Do not retune. Do not start G1.
```

## R2 — Labelled Fig. 4 configuration (next)

```
[SHARED PREAMBLE]

Task R2 only. A7: Fig. 4 NetCDF is AgrimateEU28+Egypt, FAO anomalies,
α_foreign=3.5, ζ=1, N_for=6, start 2000, git old-demand-dynamics.
wheat_params() stay 14022004 defaults (αI=3.2, ζ=0, N_for=3).

Add a named comparison constructor (e.g. fig4_experiment_params() and
an optional region/data path) that does **not** replace wheat_params().
If FAOSTAT FB / EU28 lists are not in the repo, label what you can set
(αI, ζ, N_for) and what you cannot (FAO arrays, Egypt split). Run a
short 2006–08 harvest+AMIS on that object versus default. Score hike,
undisturbed last/first if you also run undisturbed, unconverged.
Do not adopt the comparison knobs as defaults. Do not restore L1–L8.

Read first: diagnostics/GATE0_REDTEAM.md Step 7, GATE0_DEPARTURES.md A7,
diagnostics/gate0_agrimate/fig4.md, sheaf/agrimate/params.py.
```

## R3 — World-price recipe

```
[SHARED PREAMBLE]

Task R3 only. Host world price is volume-weighted lagged D.7 offers
(model.py np.dot(xi_lag, p_lag)/vol) × p0. methods.md says “D.7 × p0”.
Fig. 4 author series use plot_wm_price_timeseries.

If Zenodo 14022004 is available locally, diff that function and write
the symbol-by-symbol comparison (claim, code, match/gap). If it is
not, document the gap and add a host-only executable test that the
reported p_w equals the XI-weighted offer mix (not a single D.7 of
world XI*). Do not pin 2006. Do not change wheat_params().

Read first: GATE0_REDTEAM.md Step 6, sheaf/agrimate/model.py (price_index),
sheaf/agrimate/fig4.py world_market_price_index.
```

## R4 — Undisturbed XI split

```
[SHARED PREAMBLE]

Task R4 only. Item 3 still fails: host last/first 1.63 vs author 1.004.
B1 delivery did not move p_w. Remaining candidate: non-periodic xd/xi
under constant H. Characterise annual XI and the xd/xi split on
undisturbed 2003–11 (or 2006–11) without pinning. Report whether Jacobi,
rolling year, or xmin penalty is the wander. Do not add a decay knob
to make last/first = 1. Do not restore L1–L8.

Read first: diagnostics/gate0_agrimate/undisturbed.md, GATE0_REDTEAM.md
Step 5, sheaf/agrimate/model.py q_oth update.
```

## R5 — S4 x1=demand labelled experiment

```
[SHARED PREAMBLE]

Task R5 only. Author two-market x1 is fixed to D.30/D.30a requests;
host still delivers T*+domestic and discards the request vector.
Add a labelled experiment (flag, default off) that uses those requests
as destination weights or as x1, with a test that default=off recovers
today’s path. Do not guess a new CES-rationing rule. Do not retune αI.
If you cannot implement it faithfully from retrieved code, label and
stop.

Read first: GATE0_DEPARTURES.md S4, GATE0_AGRIMATE_BRIEF.md item 7,
sheaf/agrimate/model.py purchaser_demand call.
```

## R6 — FAOSTAT FB (again)

```
[SHARED PREAMBLE]

Task R6 only. A1: USDA PSD not FAOSTAT Food Balances. P10 found no FB
arrays in data/faostat_network/. Follow GATE0_DATA.md. If you can add
2006–11 FB with PROVENANCE.txt, build a parallel WheatData and compare
one harvest+AMIS window to USDA; keep USDA as prepare_wheat default.
If you cannot, leave A1 and stop. Do not copy 2015–21 FoodTradeNetwork
averages as fake 2006–11 FB.

Read first: GATE0_DATA.md, faostat_fb.md, GATE0_DEPARTURES.md A1.
```

## R7 — A8 mean-vs-sum sensitivity

```
[SHARED PREAMBLE]

Task R7 only. prepare_wheat groupby.mean() vs psd_regional_annual() sum
makes China 0.50× and Eastern Africa 0.10×. Do **not** rewrite the
2003–11 host. Write a labelled sensitivity: what China/EA H, C, S
become if members are summed, on 2007–09 means only. No xmin/p_sto fit.

Read first: regional.md, GATE0_DEPARTURES.md A8.
```

## R8 — Honest reproduction score tests

```
[SHARED PREAMBLE]

Task R8 only. Expand tests/agrimate so a Fig. 4 *match* would have to
change assertions deliberately. Keep tests that currently require host
hike > author hike until R10 says otherwise. Add tests that:
(1) wheat_params defaults are 14022004 not Fig. 4 knobs;
(2) sheaf.agrimate still does not import legacy/archive/G1/G2;
(3) author_fig4 CSVs exist and author undisturbed last/first < 1.05.
Do not weaken identity tests to chase Pink Sheet.

Read first: tests/agrimate/test_fig4.py, test_redteam.py, GATE0_REDTEAM.md
Step 2.
```

## R9 — N5 on the Fig. 4 config

```
[SHARED PREAMBLE]

Task R9 only. Repeat the P5 unconverged count on the R2 comparison
object (short window is enough). Failed vs unconverged vs maxiter.
Do not raise plan_maxiter as a default. Do not paper over with L1–L8.

Read first: solver.md, GATE0_DEPARTURES.md N5.
```

## R10 — Score the Fig. 4 config vs author series

```
[SHARED PREAMBLE]

Task R10 only. Using the R2 comparison run (not wheat_params defaults),
score 2006–11 or 2006–08 hike, quiet-year index, moy max/min, and
undisturbed last/first against author_fig4/. Write a short note. If the
config still cannot be built (no FAO/EU28), score the knobs you could
set and list the rest as remaining A7. Do not adopt knobs that happen
to move Pink corr.

Read first: fig4.md, hindcast.md, GATE0_REDTEAM.md Step 7 and 10.
```

## R11 — Default three-scenario runner

```
[SHARED PREAMBLE]

Task R11 only. Re-run PYTHONPATH=. python scripts/run_agrimate_validation.py
**only if** wheat_params() or prepare_wheat defaults changed in R2–R10.
They must not have. If defaults are unchanged, say so and stop without
a multi-year re-run. Update diagnostics/gate0_agrimate/ only if you ran.

Read first: GATE0_VALIDATION.md, GATE0_CONTRACT.md.
```

## R12 — Methods note v2

```
[SHARED PREAMBLE]

Task R12 only. Update the G0-P methods note with R2–R10 evidence.
Still no substitution, no government game. Accept or reject the market
section on DEVELOPMENT items 1–5 as they now stand. Do not start G1
in the same session.

Read first: diagnostics/gate0_agrimate/methods.md, GATE0_REDTEAM.md.
```

## Blocked (do not paste until G0-P is accepted)

```
G1 — Cross-crop substitution on the accepted G0 host.
Disabled G1 recovers the single-crop three-scenario run.
Needs an approved GATE0_DEPARTURES record before code.

G2 — Government restriction game.
Disabled G2 recovers E.4 AMIS. Not restriction_pulse.
Needs an approved GATE0_DEPARTURES record before code.
```
