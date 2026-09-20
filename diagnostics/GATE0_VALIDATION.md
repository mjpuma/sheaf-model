# Gate 0 validation protocol

SHEAF Gate 0 is an independent Agrimate copy (Kuhla, Kubiczek & Otto 2025,
*Ecol. Econ.* 231:108546; ODD §D; wheat §E). This file is the **validation
workflow**, not a score. Scores live in `diagnostics/gate0_agrimate/`.

A separate Agrimate-copy attempt (Bai/Wada/Puma, Sep 2026 progress note) used
the same three-scenario structure on a later window. We take that *workflow*
and run it on the Agrimate wheat case (2006–11). We do not take that note’s
fitted knobs, 2017–2025 paper, or FAO/USDA splice.

The only SHEAF differentiator versus an Agrimate copy is **later**:

| Layer | Status on this host | Recovery |
|---|---|---|
| **G0** | Single-crop wheat, AMIS/E.4 prescribed | This protocol |
| **G1** | Cross-crop substitution — **blocked** until G0-P accepted | Disabled G1 recovers G0 |
| **G2** | Government restriction game — **blocked** until G0-P accepted | Disabled G2 recovers E.4 |

Do not implement G1/G2 here. Do not restore L1–L8 to chase Pink Sheet.

Post-P12 inventory: [`GATE0_REDTEAM.md`](GATE0_REDTEAM.md),
[`GATE0_DATA.md`](GATE0_DATA.md). R-queue exhausted. Post-R development:
[`GATE0_NEXT_PROMPTS.md`](GATE0_NEXT_PROMPTS.md). Next paste:
[`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md) (**S5 done**; G0-P **not accepted**).

## Command

```bash
python -m pytest tests/agrimate -q
PYTHONPATH=. python scripts/run_agrimate_validation.py
```

Fig. 4 author-series score (does **not** re-run the host; P7):

```bash
PYTHONPATH=. python scripts/score_agrimate_fig4.py
```

G0-H hindcast note (does **not** re-run the host; P8 / S5):

```bash
PYTHONPATH=. python scripts/score_agrimate_hindcast.py
```

S5 re-score of Fig. 4 + hindcast + regional notes from existing CSVs
(does **not** re-run the NLP runner; not R11):

```bash
PYTHONPATH=. python scripts/score_agrimate_s5.py
```

Regional USDA table (P9). Harvest is reconstructed from `H_annual`;
consumption/stocks re-run the three scenarios without overwriting
price CSVs:

```bash
PYTHONPATH=. python scripts/score_agrimate_regional.py
```

FAOSTAT FB inventory (P10; does **not** re-run the host or switch USDA):

```bash
PYTHONPATH=. python scripts/score_agrimate_faostat_fb.py
```

FBSH parallel WheatData vs USDA (R6; does **not** switch `prepare_wheat`):

```bash
PYTHONPATH=. python scripts/score_agrimate_fb_wheatdata.py
```

A8 mean-vs-sum table (R7 labelled; S1 implemented the sum; USDA stocks):

```bash
PYTHONPATH=. python scripts/score_agrimate_a8_sum.py
```

G0-P methods note (does **not** re-run the host; P12):

```bash
PYTHONPATH=. python scripts/score_agrimate_methods.py
```

Labelled Fig. 4-config comparison (does **not** change `wheat_params()`; R2):

```bash
PYTHONPATH=. python scripts/score_agrimate_fig4_config.py
```

Single-scenario solver smoke (harvest+AMIS only):

```bash
PYTHONPATH=. python scripts/run_agrimate_wheat.py
```

OAT diagnostic (does **not** retune defaults):

```bash
PYTHONPATH=. python scripts/run_agrimate_validation.py --sensitivity
```

## Three scenarios (G0-U)

Same design as Agrimate’s published wheat experiments and as the Bai note.

| Name | Harvest anomalies | Export restrictions | Agrimate analogue |
|---|---|---|---|
| `undisturbed` | off | off | repeating seasonal baseline |
| `harvest` | USDA PSD, on | off | harvest-only |
| `harvest_amis` | on | AMIS / Tbl. E.4 | harvest + restrictions |

OECD/AMIS aggregated CSV columns are `PolicyMeasure_Name` and
`CommodityClass_Name`. Looking for `Measure`/`Commodity` left Δ = 0 on every
2003–11 wheat step (harvest-only and harvest+AMIS were identical). The loader
now uses the OECD names. Harvest vs harvest+AMIS must differ when AMIS binds.

Spin-up 2003–05; score 2006–11. World price is the international transaction
price already in `model.py`, not a calm pin.

**G0-U exit:** documented seasonal baseline after spin-up (undisturbed
year-to-year drift and seasonal-shape RMSE reported, not forced); failed
solves remain rare; material balance `S ≥ 0`.

## What is scored (G0-H, not prices alone)

Bai’s note calibrated to world prices and listed supply/stocks as the next
stage. Gate 0 scores both from the start.

1. **World prices** vs Pink Sheet: correlation, 2007/08 hike ratio, 2006 level.
   Indexed overlay: `figures/fig2_prices.png`.
2. **Global production, consumption, ending stocks, stock-to-use** vs USDA
   world PSD (`data/usda_world/`). Model is the 27-node sum; USDA is world.
   Level bias from coverage is expected; anomaly correlation is the number.
3. **Regional mechanism** (not a 36-run grid):
   - Ukraine supplier: harvest, producer stocks, exports, consumption.
   - Eastern Africa purchaser: consumer price, inflow, consumption, stocks.
   Comparison is harvest-only vs harvest+AMIS on the historical diary.

FAOSTAT Food Balances remain labelled A1. Bai found FAO anomalies closer to
prices in 2020–24. P10 checked `data/faostat_network/` (E0 only). R6 obtain
vendored raw FBSH wheat 2006–11; R6 ran a labelled `prepare_wheat_fbsh`
parallel vs USDA on 2006–08 harvest+AMIS (**not adopted**; Psi stayed USDA).
S3 re-scored that parallel against member-sum USDA (China H 1.00; moy
20.1×→33.0×; items 1–3 unchanged). **Not adopted.** USDA stays the
default. See `s3_fbsh.md`, `faostat_fb.md`, `fb_wheatdata.md`.

Agrimate Fig. 4 author series: Zenodo 10688435 unpacked (P7). Score in
`diagnostics/gate0_agrimate/fig4.md`. Independent implementation, not a
replication. PDF digitisation was not used. G0-H writeup (P8):
`diagnostics/gate0_agrimate/hindcast.md` — sourced shortfall, not a retune.
P9: `diagnostics/gate0_agrimate/regional.md` — coverage labelled
(A8 member-sum, S1); no stock-level fit.
R7: `diagnostics/gate0_agrimate/a8_sum.md` — 2007–09 H/C/S mean vs
sum (USDA ending stocks, not FAO ΔS); S1 implements the sum.
P10: `diagnostics/gate0_agrimate/faostat_fb.md` — `data/faostat_network/`
is E0 only; A1 left; USDA default. R6 obtain: raw FBSH at
`data/faostat_fb/`; labelled host reconstruction at
`data/food_balances/wheat_food_balance_fao.csv` (not bit-identical;
not adopted).
P11: `diagnostics/gate0_agrimate/pulse.md` — 8-run 2008 prescribed-Δ,
clean; not Bai's 36; not G2.
P12: `diagnostics/gate0_agrimate/methods.md` — G0-P market-section
offer; **not accepted** (items 3 and 5 fail). G1/G2 stay blocked.

## Sensitivity (diagnostic)

One-at-a-time around **author** `AgrimateParams` (αI=3.2, τ=0.1, σ=2, εc=0.1,
p_sto=0.1/Nyear, xmin=0.2). Bai’s α_foreign=10 is an alternative on the αI
axis, not a default. Period-specific split calibration (2008 vs 2022) is an
open G0-H question, not a retune of this wheat run.

`--sensitivity` runs a short 2006–08 harvest+AMIS OAT. It must not change
`wheat_params()`.

## Exporter-at-a-time grid (P11, not G2)

P11 ran the **8-run** 2008 wheat slice: Ukraine and Russia × {0.5, 1.0} ×
{6, 12} months on harvest-anomaly data vs harvest-only. Helper:
`sheaf.agrimate.restrictions.restriction_pulse`. Scorer:
`PYTHONPATH=. python scripts/score_agrimate_pulse.py` (not the default
three-scenario command). Writeup: `diagnostics/gate0_agrimate/pulse.md`.
The slice is **clean** (failed=0, production identical, Δ on one exporter,
Δ=1.0/12m zeros XI). Bai’s 9×2×2=36 2020 grid is **not** run. Gate 2 is a
different mechanism (governments choose Δ). This grid **prescribes** Δ.

## Figures

| File | Question |
|---|---|
| `fig1_coverage_trade.png` | What does the 27-node wheat network look like? |
| `fig2_prices.png` | How do the three scenarios move world price vs Pink Sheet? |
| `fig3_supply_stocks.png` | Do production and stocks follow USDA anomalies? |
| `fig4_ukraine_supplier.png` | Does AMIS move the restricting exporter as expected? |
| `fig5_eastern_africa_purchaser.png` | Does the shock reach a dependent importer? |

Figures wait on the three-scenario baseline. They are diagnostics, not a
publication deck. G0-P (`methods.md`) is written and **not accepted**.

## What we explicitly will not do in G0

- Fit αI, p_sto, xmin, or λ to Pink Sheet or to Bai’s 2022 window.
- Use one-parameter-set failure on 2008 **and** 2022 as a reason to
  split-calibrate the 2006–11 Agrimate case.
- Treat the 36-run exporter grid as Gate 2.
- Open G1 substitution or G2 games before G0-P is accepted (`DEVELOPMENT.md`).
