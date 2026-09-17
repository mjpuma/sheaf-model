# Gate 0 prompt list

Paste **exactly one** prompt per session. Do not skip. Do not open G1/G2.
Living queue: [`DEVELOPMENT.md`](DEVELOPMENT.md). Contract:
[`GATE0_CONTRACT.md`](GATE0_CONTRACT.md). Protocol:
[`GATE0_VALIDATION.md`](GATE0_VALIDATION.md).

**Now:** paste **P5**. Everything above P5 is done. Everything below P5
is later.

## Shared preamble (prepend to every prompt)

```
You are continuing SHEAF Gate 0 wheat: an independent Agrimate copy
(Kuhla et al. 2025; sheaf/agrimate/). Read diagnostics/GATE0_CONTRACT.md,
diagnostics/DEVELOPMENT.md, diagnostics/GATE0_VALIDATION.md, and this
prompt's "Read first" files before editing.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not restore L1–L8 (fill-target, calm pin, scarcity blend, ask_rival).
- Do not pin the unforced world price to the 2006 mean.
- Do not retune αI, p_sto, xmin, or λ to Pink Sheet or to Bai's α_foreign=10.
- Do not treat maize/rice as an acceptance target.
- Author AgrimateParams stay the defaults. Bai's fitted knobs are
  alternatives, not ours.
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
| P0 | G0-N solvent supplier programme | **done** |
| P0b | G0-S author-code alignment (27 regions, p_sto, x_min, E.27, D.1) | **done** |
| P0c | Three-scenario workflow + AMIS column fix | **done** |
| P1 | Accounting identities each step | **done** |
| P2 | Diagnose undisturbed drift (do not pin) | **done** |
| **P3** | Wire or label β/τ_P from author code | **done** (unwired; wheat path pins P_loc=1) |
| **P4** | Wire or label D.30a upper-tier purchaser | **done** (formula wired; x1 still from plan) |
| P5 | Characterize unconverged scipy (do not paper over) | **next** |
| P6 | Run OAT sensitivity; do not retune | queued |
| P7 | Unpack Zenodo 10688435; score vs Agrimate Fig. 4 | queued (G0-H) |
| P8 | Honest 2006–11 hindcast writeup (levels and paths) | queued (G0-H) |
| P9 | Regional USDA supply/stocks (not only world) | queued (G0-H) |
| P10 | FAOSTAT FB vs USDA (A1) — only if data exist | queued / maybe defer |
| P11 | Exporter-at-a-time pulse grid (not G2) | optional G0-H/P |
| P12 | G0-P methods note | after P8 |
| — | G1 substitution / G2 restriction game | **blocked until G0-P** |

---

## P1 — Accounting identities (next)

```
[SHARED PREAMBLE]

Task P1 only. Add executable accounting tests for sheaf/agrimate/.

Read first: sheaf/agrimate/equations.py (fulfill_sales, update_producer_storage),
sheaf/agrimate/model.py (the step loop), tests/agrimate/test_accounting.py.

For every region and step of a short run (2006 only is enough):
1. Producer: S_p' = max((1-δ) S_p + H - sold_d - sold_i, 0) matches
   update_producer_storage.
2. Consumer: S_c' = max(S_c + inflow - consumption, 0); consumption ≤
   S_c + inflow.
3. Sales: sold_d, sold_i ≥ 0; sold_d + sold_i ≤ S_p + H; international
   sales respect (1-Δ).
4. No NaNs in price_index, stocks, harvest, consumption.

Do not change the economic model to make a test pass. If an identity
fails, record it with a concrete counterexample in
diagnostics/gate0_agrimate/ (new accounting.md) and classify per
GATE0_DEPARTURES.md. pytest tests/agrimate must stay green.

This is G0-U material balance, not a Pink-Sheet retune.
```

## P2 — Undisturbed drift

```
[SHARED PREAMBLE]

Task P2 only. The three-scenario run shows undisturbed post-spin-up
annual-mean price ratio last/first = 1.63, seasonal-shape RMSE 0.16,
CV 1.17 (diagnostics/gate0_agrimate/validation.md). Agrimate undisturbed
is repeating seasonal behaviour, not a flat pin and not a random walk.

Read first: README/supplement §D.5 Nash vs dynamic; sheaf/agrimate/model.py
init (S_p=0, Nash-tiled plans); harvest.py; GATE0_DEPARTURES N2/N3.

Diagnose why the undisturbed price mean drifts across 2006–11. Candidates
to check, not assume: initial S_p=0; consumer stock Ψ; p_sto; rolling
horizon; Jacobi IBR; inverse-demand floor; harvest profile vs C*.

Deliver a short writeup in diagnostics/gate0_agrimate/undisturbed.md:
mechanism, evidence, whether it is a bug vs a labelled simplification.
If you have a sourced fix that is in Agrimate author code, implement it.
If not, do not invent a pin or a decay knob. Re-run the three-scenario
script only if you change the host.

Do not score Pink Sheet as the success criterion.
```

## P3 — β / τ_P local price

```
[SHARED PREAMBLE]

Task P3 only. Author params include beta_loc=0.05 (and τ_P=0.2 in the
paper). Host field exists, not wired (GATE0_DEPARTURES S3;
GATE0_AGRIMATE_BRIEF item 6).

Locate the mechanism in retrieved Zenodo 14022004 (not copied into this
repo) and in supplement §D. If the author executable uses it on the
wheat path, wire it symbol-for-symbol and add tests. If the author
wheat path does not use it, leave it unwired and write that evidence
into GATE0_AGRIMATE_BRIEF.md and GATE0_DEPARTURES.md.

Do not guess a local-price rule. Do not change αI.
```

## P4 — D.30a upper-tier purchaser

```
[SHARED PREAMBLE]

Task P4 only. Lower-tier CES D.30 is implemented. Upper-tier D.30a
(commodity vs compound good, ε_d, A_d) is not (GATE0_DEPARTURES S4).

Same rule as P3: find it in author code + supplement; implement if the
wheat executable uses it; otherwise label and stop. Tests for budget
exhaustion / limiting case when the upper tier is off. Do not refit A_d
to Pink Sheet.
```

## P5 — Unconverged scipy

```
[SHARED PREAMBLE]

Task P5 only. 2003–11 harvest+AMIS: failed=0, fallback=0, residual=0,
but unconverged ≈ 1743/5832 (scipy success=False on a still-feasible
point).

Characterize whether those points move the price path vs a tighter
solve (more iters, different start, grad check). Report in
diagnostics/gate0_agrimate/solver.md. Improve reliability only if you
can show the current accepted point is not a local/feasible substitute
for the intended optimum. Do not add a penalty that restores L1–L8.
Do not drop unconverged from the count.
```

## P6 — OAT sensitivity (diagnostic)

```
[SHARED PREAMBLE]

Task P6 only. Run
PYTHONPATH=. python scripts/run_agrimate_validation.py --sensitivity
(short 2006–08 harvest+AMIS OAT). Do not pass --sensitivity-extended
unless the short run is cheap and complete.

Write diagnostics/gate0_agrimate/score_sensitivity.csv and a short
section in validation.md. α_foreign=10 is Bai's alternative, not our
default. wheat_params() must be unchanged after the run. Summarize
which parameters move 2008 hike vs which do not. No retune.
```

## P7 — Agrimate Fig. 4 author series (G0-H starts here)

```
[SHARED PREAMBLE]

Task P7 only. Pass rule: G0-U items 1–3 in DEVELOPMENT.md should be
honestly reported before judging historical fit. If P2 is still "drift
unexplained", say so and still compare, but do not claim replication.

Zenodo data 10688435 (150 MB) was not unpacked. If the zip is in the
environment or can be fetched, unpack enough to get Agrimate Fig. 4
wheat world-price / regional supply-consumption-stocks series. Score
our three scenarios against those series (not only Pink Sheet). If the
zip is absent, write "independent implementation, Fig. 4 series not
in hand" and stop. Do not digitise the PDF as if it were author output
unless you label it as a digitisation with error bars.
```

## P8 — Honest hindcast writeup

```
[SHARED PREAMBLE]

Task P8 only. Write the G0-H score as a note, not a retune.

Use diagnostics/gate0_agrimate/ three-scenario outputs. Report:
- quiet-year (2006) price *level* vs Pink Sheet (currently ~65 vs 213)
- 2007/08 hike ratio vs obs (currently ~×4.5 vs ×1.88)
- seasonal path, not only corr
- production anomaly corr (currently +0.80)
- stock *level* bias (~3× USDA world) vs stock anomaly corr (~+0.94)
- harvest-only vs harvest+AMIS attribution
- comparison to Agrimate published wheat Fig. 4 if P7 succeeded

Comparable to Agrimate, or an explicit sourced shortfall. Do not restore
L1–L8. Do not adopt Bai α_foreign=10 because it might raise the spike.
```

## P9 — Regional USDA tables

```
[SHARED PREAMBLE]

Task P9 only. Global scores use USDA world vs 27-node sums. Add a
regional table: model annual harvest/consumption/ending stocks vs
psd_regional_annual() for named exporters (USA, Russia, Ukraine, EU-27,
Argentina, Australia, Canada, India, China) and Eastern Africa, 2006–11.
Write CSV + a short section. Coverage gaps stay labelled. No parameter
fit to close the stock-level gap.
```

## P10 — FAOSTAT Food Balances (A1)

```
[SHARED PREAMBLE]

Task P10 only. Baseline quantities are USDA PSD, labelled A1. Bai found
FAO anomalies closer to prices in 2020–24. Do not switch the 2006–11
host to FAO unless FAOSTAT Food Balance arrays are actually in the repo
or you can add them with a PROVENANCE.txt.

If you add them: build a parallel WheatData, run three scenarios, compare
to the USDA-forced run. Keep USDA as default until G0-P says otherwise.
If you cannot add them, leave A1 and stop.
```

## P11 — Exporter pulse grid (optional, not G2)

```
[SHARED PREAMBLE]

Task P11 only. Optional G0-H/P experiment. restriction_pulse already
exists. Run a small prescribed-Δ grid on harvest-anomaly data, 2008
start: Ukraine and Russia × {0.5, 1.0} × {6, 12} months. Compare each
to harvest-only. This is AMIS-style Δ, not a government best-response.
Do not implement sheaf/dynamic_policy.py. Do not expand to Bai's full
36-run 2020 grid unless this 8-run wheat-2008 slice is clean.
```

## P12 — G0-P methods note

```
[SHARED PREAMBLE]

Task P12 only. Wheat Gate 0 methods note at publication standard:
what we implemented, data vintage, three scenarios, hindcast vs
Agrimate, labelled departures, limits. No substitution. No government
game. This note is what you accept or reject as the SHEAF market
section. Do not start G1 in the same session.
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
