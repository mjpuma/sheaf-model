# SHEAF Gate 0 wheat — methods note (G0-P / S6; T1–T3 reaffirm)

**This is the market section offered for acceptance or rejection.**
It is an independent Agrimate copy (Kuhla, Kubiczek & Otto 2025,
*Ecol. Econ.* 231:108546; ODD §D; wheat §E). It is **not** a
replication of Agrimate Fig. 4. It does **not** implement
cross-crop substitution (G1) or a government restriction game (G2).

**Verdict. Not accepted.** DEVELOPMENT items 3 and 5 fail
(undisturbed last/first **1.444** vs author
1.004; harvest+AMIS 2008 hike ×3.71 vs
Agrimate ×1.62 vs Pink
×1.88). G1 and G2 stay blocked.
Do not start them from this note. `wheat_params()` stay
αI=3.2, p_sto=0.1, xmin=0.2.
L1–L8 stay rejected. Bai α_foreign=10 is not adopted. The unforced
world price is not pinned to the 2006 mean. S6 rewrote this note
from S1–S5 CSVs. T1–T3 labelled remaining sourced gaps and did
**not** adopt them. T-queue is exhausted. The NLP runner was not
re-run (not R11).

Numbers are from existing `diagnostics/gate0_agrimate/` CSVs
(spin-up 2003–05, score 2006–11, A8 member-sum). The three-scenario
runner was not re-run for this note (not R11).

## 1. What we implemented

Host: `sheaf/agrimate/`. Executable specification: Zenodo 14022004
retrieved 2026-09-16 (**not copied**). Fig. 4 author series:
Zenodo 10688435 `main_output` NetCDF (P7). Paper text and author
code disagree in labelled places (paper 28 regions vs code 27;
Tbl. D.8 αI=3.5 vs code 3.2); the host follows the retrieved wheat
executable, not a guessed blend.

Lineage is TWIST (Schewe et al. 2017) → Agrimate (Kuhla et al. 2025)
→ this Gate 0 copy. The only planned SHEAF differentiators versus
an Agrimate copy are **later**: G1 substitution and G2 government
games (`GATE0_EXTENSION_PLAN.md`). Disabled G1 must recover this
single-crop run; disabled G2 must recover E.4 AMIS. Those tests
are not this note.

| piece | source | host |
|---|---|---|
| regions | Zenodo `AgrimateRegionsWheat` | 27 names (S1) |
| clock | 24-step year | `STEPS_PER_YEAR` |
| harvest expectation | Eq. D.1 | `expected_harvest` |
| restriction expectation | Eq. D.2 | `expected_restriction` |
| sales | Eq. D.3 | `fulfill_sales`; XI × (1−Δ) |
| supplier plan | D.11–D.21 | fraction map; p_sto; xmin penalty ζ=0 |
| inverse demand | D.7 | world XI* scale; αI=3.2 |
| rivals' XI | D.22 | Jacobi IBR; τ_exp=0.5 |
| purchaser | D.30 + D.30a | nested CES; A_d=1 recovers D.30 |
| consumer | D.35 | εc=0.1 |
| harvest shape | E.27 | author raised-cosine |
| restrictions | Tbl. E.4 / AMIS OECD | prescribed Δ; not a game |
| world price | §5.2 international tx | XI-weighted lagged D.7 offers × p0; not a 2006 pin |
| Nash init | §D.5 | not the dynamic baseline |

Units: quantities million tonnes (MMT); prices a $/t index on D.7.
Process order follows §D.3. Step identities (producer, consumer,
sales, (1−Δ)) hold on the 2006 harvest+AMIS path (P1).

## 2. Parameters (author defaults, not a fit)

Zenodo 14022004 `AgrimateParams`. Tbl. D.8 (αI=3.5, τ=0.2) is
`wheat_table_d8_defaults()`, unused. Bai's fitted α_foreign=10 is
an OAT alternative (P6), not ours.

| knob | value | note |
|---|---:|---|
| αI | 3.2 | code, not Tbl. D.8 3.5 |
| α_nash | 3 | §D.5 init |
| σ | 2 | origin CES |
| εc | 0.1 | D.35 |
| p_sto | 0.1 / Nyear | Tbl. D.8 storage cost |
| xmin | 0.2 | even-spread penalty; ζ=0 on |
| N_for | 3 months | D.1; Fig. 4 used 6 |
| τ | 0.1 yr | F.1 / code |
| β, τ_P | 0.05, 0.2 yr | unused on wheat path (S3) |
| plan_maxiter | 40 | left at 40 (N5 / P5) |

## 3. Data vintage

- **Baseline quantities:** USDA PSD 2007–09 **member-sum then mean**
  (A8 / S1), not FAOSTAT Food Balances E.1 (A1). Never FAOSTAT FBSH
  element 5074 ΔS as a stock level. P10: `data/faostat_network/` is
  E0 trade only. Labelled host reconstruction at
  `data/food_balances/wheat_food_balance_fao.csv` is **not adopted**;
  USDA stays the default (`faostat_fb.md`, `s3_fbsh.md`).
- **Trade pattern:** FAOSTAT E0 2006–07, rescaled to USDA exports (A2).
- **Anomalies:** USDA PSD, LOWESS residual, applied to the 2007–09
  mean harvest.
- **Restrictions:** OECD/AMIS aggregated wheat measures,
  `PolicyMeasure_Name` / `CommodityClass_Name` (E.4). Bans 0.95,
  taxes 0.50. 491 region-steps bind on 2003–11 wheat.
- **Harvest calendars:** `data/crop_calendars/wheat_harvest_months.csv`.
- **Pink Sheet:** scoring only. Not a calibration target.
- **Window:** simulate 2003–11; spin-up 2003–05; score 2006–11.

A_d is not E.30 (A3; F.1 Egypt 0.17 unused because Egypt is inside
Northern Africa). A_c uses income-group proxies (A4). Multi-country
PSD nodes **sum** members within year, then mean 2007–09 (A8, S1):
China H 112.7 and Eastern Africa 3.31 match mapped PSD sums; USA
stays 1.00. The rejected pooled `groupby.mean()` was China 0.50× /
EA 0.10×. Not a parameter fit.

## 4. Three scenarios (G0-U)

Same design as Agrimate’s published wheat experiments.

| name | harvest anomalies | export restrictions |
|---|---|---|
| `undisturbed` | off | off |
| `harvest` | USDA PSD, on | off |
| `harvest_amis` | on | AMIS / Tbl. E.4 |

Command: `PYTHONPATH=. python scripts/run_agrimate_validation.py`.
World price is the XI-weighted mix of lagged D.7 offers × p0
(`volume_weighted_offer_index`). Not D.7 of world XI*. Not a
2006 pin (`world_price.md`). Harvest vs harvest+AMIS differ
when AMIS binds (they were identical before the OECD column
fix).

## 5. Numerical representation

N1 fraction parameterization of D.11–D.21 (equivalent feasible set).
N2 rolling forthcoming-year plan. N3 Jacobi IBR inside the step.
N4 D.7 scaled by world XI*. N5: feasible L-BFGS-B with
`success=False` — harvest+AMIS unconverged
**2304/5832** (N5). P5 on the pre-S1 path was
1743/5832 (maxiter 1033 + ABNORMAL 710); S1 moved the count, not
the diagnosis. First-order stationarity is still not established.
Failed 0; fallback 0; residual 0.
`plan_maxiter=40` kept: 200 vs 400 iters disagree by as much as
40 vs 400, so there is no unique stationary point to adopt
(`solver.md`). Inverse-demand offer floor binds 0 times on the
reference path.

B1 (P2): international delivery now follows E.1 T* to importers.
Pre-fix, lagged XI was credited to the exporter as consumer inflow.
That ballooned exporter stocks; it did **not** cause the 1.444
undisturbed drift (p_w is on XI, not on who receives it).

## 6. What this market section does not do

- Restore L1–L8 (fill-target 0.70, calm pin, scarcity blend,
  ask_rival, prescribed buffer, scarcity-ratio floor, residual ν,
  AR(1) smoother).
- Pin the unforced world price to the 2006 Pink Sheet mean.
- Retune αI, p_sto, xmin, or λ to Pink Sheet or to Bai α_foreign=10.
- Split-calibrate 2008 vs 2022.
- Treat maize or rice as an acceptance target.
- Implement G1 (`sheaf/dynamic_coupled.py`) or G2
  (`sheaf/dynamic_policy.py`). Leftover files on the legacy spine
  are not this host.
- Treat the P11 prescribed-Δ grid as Gate 2. Gate 2 would let
  governments **choose** Δ. This host **prescribes** it.

## 7. Hindcast versus Agrimate Fig. 4 and Pink Sheet

Pass rule: items 1–3 before judging item 5. Item 1 is met for
retrieved code with labelled S3/S4/A1–A8/N5. Item 2 is feasible
but not first-order stationary. Item 3 fails. Item 5 is reported
as an explicit sourced shortfall (`hindcast.md`, `fig4.md`).

### Quiet-year level and 2008 hike

| series | 2006 mean | 2008 hike | crisis peak |
|---|---:|---:|---|
| host harvest+AMIS | $81.5/t | ×3.71 | 2008-06 |
| host harvest-only | $81.5/t | ×3.85 | — |
| host undisturbed | $45.8/t | ×4.87 | — |
| Pink Sheet | $213.5/t | ×1.88 | 2008-03 |
| Agrimate Fig. 4d harvest+AMIS | index 1.183 | ×1.62 | 2008-05 |

Quiet-year host is ~38% of Pink ($81.5 vs
$213.5) and 0.38 vs author 1.18 on
the index. Host hike overshoots Pink **and** Agrimate. Agrimate is
the closer of the two models to Pink on this metric. Peak timing is
wrong: host **2008-06** (harvest-calendar spike);
Pink **2008-03**; author **2008-05**.
Bai αI=10 is the wrong direction (P6 short-window hike ×2.31 → ×3.58,
pidx_max 473). Not adopted. Do not pin 2006 to close the level gap.

### Path, not only correlation

Harvest+AMIS corr vs Pink is **0.014** (near zero).
Month-of-year max/min is **16.8×** vs Pink
**1.07×** vs Agrimate Fig. 4d
**1.45×**. The host shares Agrimate's
northern-harvest calendar (moy corr vs author 0.90)
and inverts Pink (moy corr -0.65).
September 2007: host **$14.3/t** vs Pink
**$342/t**. Correlation alone would hide
this. Figure: `figures/fig6_hindcast_seasonal.png`.

### Undisturbed (item 3)

Seasonal *shape* repeats (year-to-year corr ≈ 0.98). S1 three-scenario
last/first is **1.444** (`prices_three_scenarios.csv`, not
re-run). Author Fig. 4 baseline is **1.004**. D.22 vector+shift of
planned foreign sales is **implemented** (`d22.py`; T2 labelled the
law). Weight 1/12 matches. Freeze is absent in author Julia and is
not a `AgrimateParams` field. Not a price pin. Not a solver switch.
Living D.22 last/first is **0.772** (`score_d22.csv`)
with 2006 mean $456.5/t. Two-sided repeating
[1/1.1, 1.1] still **fails**. Next paste **solver**.

### Production, stocks, consumption

Harvest+AMIS production vs USDA world: corr **0.803**,
level 661.4 vs 519.4 MMT
(ratio 1.273). Ending stocks
**1.65×** USDA after B1 (not the pre-P2 3×
echo). Consumption corr -0.390; level ratio
1.248. Vs Agrimate Fig. 4, production corr
is 0.986 at different levels (USDA vs FAO; region lists differ).
Do not fit xmin or p_sto to the stock gap (`regional.md`).

### Harvest-only vs harvest+AMIS

Production is identical by construction. AMIS wheat Δ binds 491
region-steps (Argentina, China, India, Kazakhstan, Russia, Ukraine,
Northern Africa; max 0.95). The 2007 spike is harvest-driven. On the
member-sum host the largest harvest vs harvest+AMIS price gap is not
a 2008 spring spike (`hindcast.md`).

Ukraine 2007 exports 6.7 → 14.5 MMT with AMIS; consumption 10.09 → 2.83 MMT (sign flipped vs the pre-S1 pooled-mean host). E.4 still moves the exporter. It does not repair world-price path or level.

Fig. 4 NetCDF is a **different experiment** (A7): AgrimateEU28+Egypt,
FAO anomalies, α_foreign=3.5, ζ=1, N_for=6, git `old-demand-dynamics`.
T3 labelled compact FAO-since-2005 annual relative anomalies and the
sourced AgrimateEU28 YAML + Egypt=EGY extra (`t3_fig4_inputs/`).
**Not adopted.** Host C.1 is still AgrimateRegionsWheat; USDA stays
`prepare_wheat`. Egypt is not invented as a live node.
Labelling that mismatch does not make ×3.71 a success.

## 8. Prescribed-Δ pulse (P11, not G2)

Eight 2008 harvest-anomaly runs versus harvest-only: Ukraine and
Russia × {0.5, 1.0} × {6, 12} months (`pulse.md`). AMIS diary off;
`restriction_pulse` overlays one synthetic exporter. Not a
government best-response. Not Bai's 36-run 2020 grid.

Eight 2008 harvest-anomaly runs versus harvest-only: Ukraine and
Russia × {0.5, 1.0} × {6, 12} months (`pulse.md`). AMIS diary off;
`restriction_pulse` overlays one synthetic exporter. Not a
government best-response. Not Bai's 36-run 2020 grid.

Slice is **clean**: failed=0, production identical, Δ on one
exporter. 12-month Δ=1.0 zeros Ukraine and Russia XI
(0.00× / 0.00×).
12-month Δ=0.5 halves it (0.50×).
A January–June 6-month pulse misses NH harvest (Jul–Sep).
Mean world price stays 0.99–1.01× harvest-only. D.3 binds;
it is not a Pink-Sheet lever and not Gate 2.

## 9. Labelled departures

Full register: `diagnostics/GATE0_DEPARTURES.md`. Compact:

| id | what | status |
|---|---|---|
| L1–L8 | legacy ask/scarcity devices | **rejected** |
| A1 | USDA PSD not FAOSTAT FB | labelled; P10 left |
| A2 | E0 shares rescaled to USDA XI | labelled |
| A3 | A_d not E.30 | labelled |
| A7 | Fig. 4 executable ≠ 14022004 wheat | labelled; T3 FAO/EU28 **not adopted** |
| A8 | 2007–09 baseline is member-sum then mean (S1) | **implemented**; USDA S only |
| N1–N4 | fraction map, rolling year, Jacobi, XI* scale | numerical, not economics |
| N5 | unconverged L-BFGS-B 2304/5832 | counted; maxiter 40 kept |
| S1 | 27 not 28 | follows executable |
| S2 | αI=3.2 not D.8 3.5 | follows executable |
| S3 | β/τ_P unused | matches wheat `two_markets` path |
| S4 | D.30a formula wired; x1 still from plan | formula H; x1 gap D |
| B1 | T* delivery, not own-XI echo | coding fix |
| E1/E2 | G1 substitution / G2 game | **not implemented** |
| T2 | D.22 vector+shift / NLopt vs host | D.22 **implemented**; solver labelled |
| T3 | FAO-since-2005 + AgrimateEU28+Egypt | labelled, **not C.1**, not `prepare_wheat` |

## 10. Limits

1. Undisturbed annual-mean drift 1.444 on the S1 CSV; D.22 vector+shift last/first 0.772 (two-sided still fail; not a freeze; 0 `*.jl` in `sheaf/`). Solver still labelled.
2. ~40% of harvest+AMIS plans are unconverged feasible iterates (N5).
3. Off-season world price collapses (16.8× moy max/min vs Agrimate 1.45×).
4. Quiet-year level is not on Agrimate's or Pink's scale.
5. Baseline quantities are USDA, not FAOSTAT FB (A1). A8 member-sum
   is implemented; FAO ΔS is not stocks.
6. Physical inflow remains T* + domestic; author two-market x1=demand
   is labelled, not copied (S4). εc and σ are silent on world price
   in the P6 OAT, as expected under that gap.
7. This is an independent implementation, not a bit-reproduction of
   Fig. 4. T3 labelled FAO-since-2005 + EU28+Egypt arrays; they are
   not WheatData and not C.1.

Open G0-H questions that are **not** retunes of this run: FAO vs USDA
on a window that actually has FB arrays; whether one parameter set
can fit 2008 and 2022 (Bai). Neither is a reason to restore L1–L8.

## 11. Verdict (accept or reject)

Offer this note as the SHEAF wheat market section.

| DEVELOPMENT item | result |
|---|---|
| 1. Source fidelity | Met for retrieved 14022004 code, with labelled gaps |
| 2. Numerical reliability | Feasible (failed=0, residual=0); not first-order stationary (N5) |
| 3. Undisturbed dynamics | **Fail** — last/first 1.444 vs author 1.004 |
| 4. Reference reproduction | Independent implementation, **not** a replication |
| 5. Historical performance | **Fail** — level, hike, path vs Agrimate Fig. 4 and Pink |
| 6. Controlled experiments | Three scenarios + P11 pulse run; AMIS moves the exporter |

**Recommend reject** as the publishable SHEAF market section.
Items 1–3 do not all hold; item 5 is a sourced shortfall. G1 and
G2 stay blocked until a later G0-P acceptance. Do not start G1.
`wheat_params()` unchanged. T-queue (T1–T3) stay not-accepted is
recorded. D.22 vector+shift is **implemented**. Next paste
**solver** (`GATE0_CONTINUE.md`). Do not start G1. Human
acceptance is still required.

## Files

- this note (`methods.md`)
- `hindcast.md`, `fig4.md`, `regional.md`, `s5_score.md`, `item3.md`,
  `faostat_fb.md`, `pulse.md`, `undisturbed.md`, `solver.md`,
  `t1_julia.md`, `t2_delta.md`, `t3_fig4_inputs.md`,
  `stay_not_accepted.md`, `d22.md`, `validation.md`
- `GATE0_DEPARTURES.md`, `GATE0_SPEC_MATRIX.md`, `GATE0_CONTRACT.md`

G1/G2 remain the blocked pair in `GATE0_EXTENSION_PLAN.md`.

