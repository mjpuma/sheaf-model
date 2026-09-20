# Gate 0 red team (post-P12) — 12 steps

Full-mode assessment of the live wheat host (`sheaf/agrimate/`) against
**Agrimate reproduction** (Kuhla et al. 2025, *Ecol. Econ.* 231:108546;
ODD §D; wheat §E; Fig. 4). Not a Pink-Sheet fit. Not the legacy
ask/scarcity host. G1/G2 stay blocked.

Verification protocol: `CLAUDE.md` (locate claim, locate code,
counterexample, correctness argument). Classification letters follow
`CLAUDE.md`. This file is an **inventory**, not a retune and not G0-P
acceptance.

Date: 2026-09-19. Branch base: P12 methods note
(`diagnostics/gate0_agrimate/methods.md`). This run:
`PYTHONPATH=. python -m pytest tests/agrimate -q` → **83 passed**
(10.9 s) before the R1 inventory tests. `wheat_params()` stay αI=3.2,
p_sto=0.1, xmin=0.2, ζ=0, N_for=3. L1–L8 rejected. Bai α_foreign=10
not adopted. Unforced price not pinned to the 2006 mean. The three-
scenario runner was **not** re-run; scores are the committed
`diagnostics/gate0_agrimate/` CSVs.

**Headline.** The host is a source-faithful *independent implementation*
of retrieved Zenodo 14022004 wheat code, with labelled gaps. It does
**not** reproduce Agrimate Fig. 4. Most tests pass *because they lock
that honesty*, not because the price path matches Agrimate. G0-P remains
**not accepted**. Do not start G1.

---

## Step 1 — What “reproduce Agrimate” means here

1. **Claim.** `diagnostics/DEVELOPMENT.md` items 1–6. Pass rule: 1–3
   before judging 5. Item 5 is Agrimate’s published wheat results, not
   legacy SHEAF, not a Bai 2017–25 fit.
2. **Code.** `GATE0_CONTRACT.md`; `GATE0_SPEC_MATRIX.md`;
   `GATE0_VALIDATION.md`.
3. **Match.** The P0–P12 queue executed that protocol. G0-N feasible;
   G0-S met for retrieved code; G0-U workflow exists; G0-H scored a
   sourced shortfall; G0-P note recommends reject.
4. **Counterexample to “we have reproduced Agrimate”.** Host
   harvest+AMIS 2008 hike ×4.54 vs Agrimate Fig. 4d ×1.62 vs Pink
   ×1.88; undisturbed last/first **1.630** vs author **1.004**; 2006
   mean $65.3 vs Pink $213.5 (`score_prices.csv`,
   `score_hindcast_seasonal.csv`, `score_fig4_prices.csv`).
5. **Correctness.** Calling the host “Agrimate-faithful” means
   *equation family and author-code defaults*, not *Fig. 4
   bit-reproduction*. That distinction is already in P7/P8/P12.
   Classification **H** for the claim-as-stated in those notes
   (95–100%, reproduced scores this run). Classification **F** if
   anyone reads README “Agrimate baseline” as Fig. 4 replication
   (reader risk; **G** on README tone, 40–60%).

---

## Step 2 — Test battery: almost all tests pass, reproduction still fails

1. **Claim.** `pytest tests/agrimate` is the Gate 0 exit
   (`GATE0_VALIDATION.md`, `GATE0_CONTRACT.md`).
2. **Code.** 12 modules under `tests/agrimate/` (83 tests at P12).
3. **This run.** 83 passed. What they actually lock:

| File | What it actually locks |
|---|---|
| `test_equations.py` | D.1 weights, E.27 profile sum, D.2, D.3 (1−Δ), D.30a algebra, D.35 clip |
| `test_optimize.py` | feasible fraction plans, xmin soft, grad, N5 counted, maxiter=40 |
| `test_accounting.py` | 2006 harvest+AMIS identities; B1 T* delivery |
| `test_params.py` | β/τ_P unused on wheat path |
| `test_wheat_data.py` | 27 C.1 names; AMIS Δ nonempty 2008 |
| `test_validation.py` | three-scenario flags; OAT lists Bai 10, does not adopt |
| `test_fig4.py` | author CSVs present; author baseline does **not** drift; host hike **>** author |
| `test_hindcast.py` | negative Pink corr; stocks 1.58× not 3×; AMIS adds 2008 not 2007 |
| `test_regional.py` | A8 China 0.50× / EA 0.10× labelled |
| `test_faostat_fb.py` | A1 left; USDA default; raw FBSH vendored |
| `test_pulse.py` | 8-run not 36; not G2; Δ=1 zeros XI |
| `test_methods.py` | G0-P **not accepted**; no G1/G2 import |

4. **Counterexample to “tests imply Fig. 4 match”.**
   `test_fig4_report_is_independent_not_replication` **requires**
   `hike_2008_host > hike_2008_author`. A future “reproduction” would
   have to *change that assertion*, not merely keep 83 green.
   `test_g0_p_is_not_accepted` requires `accepted is False`.
5. **What is not tested (pre-R1).** Zenodo 14022004 Julia is not
   in-repo (cannot diff). FAOSTAT FB pipeline does not exist.
   2003–11 three-scenario path is not a pytest (runtime).
   `fetch_external_data.py` is not called in CI. Archive/legacy is
   not imported (now locked by `test_redteam.py`). Author
   `plot_wm_price_timeseries` vs host `np.dot(xi_lag, p_lag)/vol` is
   not a bit-test.
6. **Correctness.** Tests are doing the right job for an *honest
   copy*. They are the wrong job if the bar is *numeric Fig. 4
   reproduction*. Classification **H** for identity/params tests
   (80–95%). Classification **F** relative to a reproduction bar
   (95–100% that current tests do not require Fig. 4 match).

---

## Step 3 — Source fidelity (item 1)

1. **Claim.** Supplier, purchaser, consumer, storage, restrictions,
   timing, world-price definition match paper/supplement or an
   approved departure (`DEVELOPMENT.md` item 1).
2. **Code.** `GATE0_SPEC_MATRIX.md`;
   `sheaf/agrimate/{equations,optimize,model,harvest,restrictions,params}.py`.
3. **Match (retrieved 14022004).** 27 `AgrimateRegionsWheat`; D.1
   logistic weights N_for=3; E.27 `duration_in_s=1.2`; D.8 p_sto=0.1/Nyear
   and xmin penalty with ζ=0 on; αI=3.2 not Tbl. D.8 3.5; E.4 AMIS OECD
   column names; D.30a formula wired; β/τ_P unused matching wheat
   `two_markets` (S3).
4. **Labelled gaps, not silent bugs.** A1 USDA not FAOSTAT FB. A2 E0
   rescale. A3 A_d not E.30. A7 Fig. 4 executable ≠ 14022004 wheat.
   A8 `groupby.mean()`. S4 inflow still T*; author x1=demand labelled.
   N1–N5 numerical representation.
5. **Counterexample to “paper text = host”.** Paper C.1 said 28; code
   is 27 (S1). Tbl. D.8 αI=3.5; executable 3.2 (S2). Host follows
   code. **H** (95–100%).
6. **Correctness.** Item 1 is met *for retrieved wheat code* with
   those labels. It is **not** met for the Fig. 4 NetCDF experiment
   (Step 7).

---

## Step 4 — Numerical reliability (item 2)

1. **Claim.** Plans converge; residuals small; failed solves rare
   enough that they do not set the price path. No L1–L8 to pass a
   test (`DEVELOPMENT.md` item 2).
2. **Code.** `optimize.solve_supplier_plan`; `solver.md`; N5 in
   `GATE0_DEPARTURES.md`. `score_prices.csv` harvest_amis:
   failed=0, fallback=0, unconverged=1743, plan_residual=0,
   floor_binds=0.
3. **Match.** harvest+AMIS 2003–11: failed=0, fallback=0, residual=0,
   offer-floor 0. **Unconverged 1743/5832** (~30%): 27 regions × 9
   years × 24 steps. `solver.md`: scipy `success=False` (maxiter 1033
   + ABNORMAL 710). `plan_maxiter=40` kept: 200 vs 400 iters disagree
   as much as 40 vs 400.
4. **Counterexample to “failed solves do not set the path”.**
   Unconverged points *are* the accepted path. Raising maxiter
   *moves* pidx (RMSE ~0.17–0.22 in `solver.md`). Item 2’s “converge”
   clause fails; the “failed/rare” clause holds if “failed” means
   infeasible.
5. **Correctness.** Classification **C** (N5), 95–100% on counts
   (CSV this run; solver.md reproduced in P5). Not a reason to
   restore L1–L8 or to pick an arbitrary maxiter. Reproduction of a
   unique Agrimate path is not demonstrated.

**R9 follow-up.** Same split on `fig4_experiment_params()` harvest+AMIS
2006–08 (`solver_fig4.md`). Failed still 0. Unconverged still counted.
Labelled maxiter=200/400 probes move p_w; default cap stays 40.
Fig. 4 knobs not adopted.

---

## Step 5 — Undisturbed dynamics (item 3) — fail

1. **Claim.** After spin-up, seasonal repeating behaviour as Agrimate
   describes. Not a flat pinned world price (`DEVELOPMENT.md` item 3).
2. **Code.** `undisturbed.md`; `author_undisturbed_drift` in
   `fig4.py`; `test_author_baseline_does_not_drift`.
3. **This run (prices_three_scenarios.csv / monthly_world.csv).**
   Host undisturbed annual-mean USD 2011/2006 = **1.630**
   (43.14 → 70.33). Author Fig. 4 baseline on the same window:
   last/first = **1.004** (1.113 → 1.117), seasonal corr **0.991**.
   Host seasonal *shape* still repeats (corr ≈ 0.98 in
   `undisturbed.md`). Inverse-demand floor binds 0. H*=C*=542 MMT.
4. **Counterexample.** Author 1.004 vs host 1.630 on the same
   2006–11 window. B1 (T* delivery) fixed exporter-stock echo;
   **p_w unchanged** (price is on XI, not on who receives it).
   Remaining candidate: non-periodic xd/xi split (annual XI 164–254
   MMT in `undisturbed.md`).
5. **Correctness.** Item 3 **fails**. Classification **open C/D** on
   the split (60–80% that Jacobi + rolling year + xmin penalty can
   wander XI; not proven this run). **H** that pinning 2006 is
   forbidden and would not be Agrimate. Do not pin.

**R4 follow-up (this checkout).** Labelled 2003–11 undisturbed probes
(`xi_split.md`; `wheat_params()` unchanged):

| label | last/first | XI span MMT | note |
|---|---:|---:|---|
| default (live D.22, N2, ζ=0) | **1.630** | 89.9 | item 3 still fails |
| xmin_off (ζ=1) | 0.548 | 78.0 | moves the wrong way |
| qoth_freeze (D.22 EMA off) | **1.019** | 97.8 | ≈ author 1.004 |
| calendar_replan (stride=24) | 0.523 | 71.3 | moves the wrong way; S_p≈0 |
| author Fig. 4 baseline | 1.004 | — | live D.22 on their path |

1. Claim: last/first wander is non-periodic xd/xi (Jacobi / rolling /
   xmin). 2. Code: `model.py` D.22 `q_oth` EMA; N2 every-step replan;
   ζ=0 xmin penalty. 3. Match: D.22 is implemented. 4. Counterexample:
   freeze `q_oth` at XI*_world−XI*_r recovers 1.019; xmin_off and
   calendar_replan overshoot to ~0.53. XI still spans 137–235 MMT
   under the freeze — last/first is the offer-mix mean, not XI
   volume. 5. Correctness: **C** (80–95%) that live D.22 `q_oth` is
   the host last/first channel on this window. **H** (95–100%) that
   freezing it is not Agrimate (author updates q_oth and still has
   last/first ≈ 1) and must not be adopted or pinned. Not B: the EMA
   matches D.22; the wander is the realised XI path feeding it.
   Not a decay knob. Not L1–L8. Next paste **R5**.

---

## Step 6 — World-price object

1. **Claim (methods.md §1).** “D.7 × p0; not a calm pin.”
   **Claim (fig4.md).** Author Fig. 4d is volume-weighted
   international transaction price, “not D.7 on world XI*.” Host
   scores “D.7 × p0 / p0.”
   **Claim (GATE0_SPEC_MATRIX).** “§5.2 international tx … index O(1).”
2. **Code.** `sheaf/agrimate/model.py`: each region’s offer is D.7 of
   `(XI_r + Q_{-r}) / XI*_world`; then
   `p_w = dot(xi_lag, p_lag) / sum(xi_lag)` (lines 266–271);
   `price_usd = price_index * p0` (line 311) with `p0` = 2006 Pink
   mean (`wheat_data.py` line 227). `p0` is a **unit scale**, not a
   path pin (`test_host_index_is_usd_over_p0`: 2006 index mean ≠ 1).
   Author-side extractor: `fig4.world_market_price_index` drops the
   domestic diagonal and volume-weights `q*p`.
3. **Match.** Spec-matrix “international tx index” matches the code’s
   XI-weighted mix of **D.7 offers**. methods.md’s “D.7 × p0” omits
   the volume-weight step. fig4.md’s contrast is real *if* author
   `plot_wm_price_timeseries` weights a different price than D.7
   offers; that Julia is **not vendored**, so the bit-diff is not
   re-run here.
4. **Counterexample to “host reports a single D.7 of world XI*”.**
   Offers are per-region D.7; world price is their XI-weighted mean.
   Counterexample to “2006 pin”: harvest+AMIS 2006 index mean 0.306,
   not 1.
5. **Correctness.** Classification **G** for methods shorthand
   (80–95%). Classification **H** for “not a 2006 pin” (95–100%).
   Open **G/H** on author vs host weight recipe until 14022004
   `plot_wm_price_timeseries` is diffed in-tree (40–60% as a
   reproduction blocker). Do not change `wheat_params()`. Do not pin.

**R3 follow-up (this checkout).** 14022004 Julia is still absent, so
the bit-diff was not run. Host identity is now executable:
`volume_weighted_offer_index` / `lagged_offer_index` replay
`price_index` on 2006 harvest+AMIS; a single D.7 of lagged world XI /
XI* disagrees. methods.md G-shorthand fixed. Writeup:
`diagnostics/gate0_agrimate/world_price.md`. Economics unchanged.

---

## Step 7 — Experiment mismatch (A7) — you cannot reproduce Fig. 4 on the default host

1. **Claim.** P7 scored host vs Zenodo 10688435 Fig. 4 series.
2. **Code.** `author_fig4/netcdf_attrs.json` (this run); `fig4.md`;
   A7 in `GATE0_DEPARTURES.md`. `wheat_params()` vs NetCDF global
   attributes:

| knob | Fig. 4 NetCDF (this file) | Host `wheat_params()` |
|---|---|---|
| region list | AgrimateEU28 + Egypt extra (EU-28 named; Brazil in RoSA) | AgrimateRegionsWheat (Brazil named; Egypt in Northern Africa; EU-27) |
| anomalies | FAO since 2005 | USDA PSD LOWESS |
| α_foreign | 3.5 | 3.2 |
| ζ | 1 (xmin penalty **off**) | 0 (penalty **on**) |
| N_for | 6 months | 3 months |
| start | 2000-01-01 (312 steps) | 2003 spin-up |
| git | `old-demand-dynamics-150-gbfc02cb-dirty` | 14022004 equal-sales-penalty tree |
| p_sto | 0.1 | 0.1 (same) |
| two_markets / pl_opt / ε_d_adjust | true / false / false | same wheat path |

3. **Counterexample.** Even a perfect 14022004 copy would not match
   Fig. 4 output. ζ=1 vs 0 alone changes the xmin quadratic; Fig. 4
   amplitude 1.45× vs host ~18× is the first place to look **on a
   labelled Fig. 4 configuration**, not by retuning αI to Pink or to
   Bai 10.
4. **Correctness.** Classification **F** (95–100%) for “default host
   reproduces Fig. 4.” Allowed next work: a **labelled comparison
   run** that copies the Fig. 4 *experiment* without changing
   `wheat_params()` defaults (see `GATE0_REPRO_PROMPTS.md` R2).
   Forbidden: adopt Bai 10, restore L1–L8, pin 2006.

R2 (this queue) added `fig4_experiment_params()` and scored 2006–08
harvest+AMIS on USDA/EU-27: moy **26.8× → 13.3×**, hike **×2.31 → ×2.22**
(author ×1.62, moy 1.51× on this window). Knobs are **not** adopted as
`wheat_params()`. FAO/EU28 still cannot-set.

**R10.** Same R2 run scored against `author_fig4/` (`fig4_config_score.md`).
Harvest+AMIS 2006 index **1.677 vs author 1.183** (knobs moved away);
hike ×2.22 vs ×1.62; moy 13.3× vs 1.51×; undisturbed last/first 0.409
vs 1.006. Remaining A7 unchanged. Not a match. Not adopted. Next **R9**.

---

## Step 8 — Data vintage, downloads, missing Agrimate inputs

Cookbook: [`GATE0_DATA.md`](GATE0_DATA.md). This run checked the
vendored trees, `scripts/fetch_external_data.py` source, and live
HTTP HEAD/GET (2026-09-19):

| Input | Agrimate E.1 / Fig. 4 | Host | Fetch |
|---|---|---|---|
| Baseline P/C/S | FAOSTAT Food Balances | USDA PSD 2007–09 mean (A1) | `--psd-only` (FAS zip HEAD 200) |
| Trade structure | FAOSTAT E0 | E0 2006–07 rescaled to USDA XI (A2) | **vendored**; no fetch |
| Anomalies | FAO (Fig. 4) | USDA LOWESS | PSD path above |
| Restrictions | AMIS/E.4 | OECD XLSX → CSV | **browser** then `--amis-only` (oecd.org HEAD **403**) |
| Calendars | SAGE / author | hand-curated start/end months; **E.27 raised-cosine** | none (CSV vendored) |
| Pink Sheet | scoring | scoring only | `--prices-only` (WB page HEAD 200) |
| Fig. 4 series | 10688435 NetCDF | extracted CSVs in `author_fig4/` | **manual** Zenodo (record HEAD 200); zip not vendored |
| Author Julia | 14022004 | not copied | record HEAD 200; **not in fetch script**; **not in repo** |
| FAOSTAT FB arrays | E.1.1 | USDA default (A1); **raw FBSH** in `data/faostat_fb/` (R6 obtain); author cleaned still absent | `--faostat-fb` (opt-in; bulk zip 200 this run; JSON API 521) |

`scripts/fetch_external_data.py` contains none of: `zenodo`,
`14022004`, `10688435`, `alpha_i`, `p_sto`, `xmin`. There is **no**
automated download for Zenodo. FAOSTAT Food Balances are opt-in
`--faostat-fb` (raw FBSH wheat 2006–11, not a silent fit; USDA stays
`prepare_wheat` default). Reproduction of the *author experiment* is
not one-command. Laptop `/Users/mjp38/GitHub/sheaf-model/data` is not
mounted on this VM.

`data/crop_calendars/PROVENANCE.txt` described triangular allocation
and `sheaf.dynamic_wheat` twin-pin — the **legacy** host. Live Gate 0
uses `sheaf.agrimate.harvest.step_profile_from_months` (E.27) after
loading start/end months via `sheaf.seasonal.load_harvest_calendar`.
Classification **G** (80–95%); PROVENANCE updated this session to
label the live path.

---

## Step 9 — Archive, leftover G1/G2, silent tuning

1. **Claim.** Dead-end artifacts stay in `archive/`; leftover
   `dynamic_coupled` / `dynamic_policy` are not approval
   (`DEVELOPMENT.md`, `GATE0_EXTENSION_PLAN.md`).
2. **Code.** `archive/legacy-gate0/scratch/` — r0–r5 / ask_rival /
   calm-pin prototypes on the **old** sequential map.
   `diagnostics/redteam/` — same cycle’s scores.
   `diagnostics/gate0_wheat_report.md` and maize/rice reports —
   **legacy**. Still importable: `sheaf/legacy/`,
   `sheaf/dynamic_crop.py`, `sheaf/dynamic_coupled.py`,
   `sheaf/dynamic_policy.py`, `sheaf/dynamic_wheat.py`,
   `sheaf/dynamic_grains.py`.
3. **This run.** AST walk of `sheaf/agrimate/*.py`: **zero** imports
   of `sheaf.legacy`, `sheaf.dynamic_*`, or `archive/`.
   `fetch_external_data.py` has no αI / p_sto / xmin fit. P6 OAT
   lists Bai 10 and does not write it into `wheat_params()`.
4. **Counterexample to “archive is a tuner for Gate 0”.** Nothing
   under `sheaf/agrimate/` imports those trees (`test_redteam.py`).
5. **Correctness.** Classification **H** (95–100%) that live Gate 0
   is not silently tuned from archive. Classification **E** that
   leftover G1/G2 files exist. **Do not run archive scratch as a
   calibrator.**

---

## Step 10 — Historical performance vs Agrimate (item 5) — fail

From `score_hindcast_seasonal.csv` / `score_fig4_prices.csv` /
`score_hindcast_quantities.csv` (2006–11, harvest+AMIS), this run:

| metric | Host | Agrimate Fig. 4 | Pink Sheet |
|---|---:|---:|---:|
| 2006 mean | $65.3 (index 0.306) | index 1.183 | $213.5 |
| 2008 hike | ×4.54 | ×1.62 | ×1.88 |
| crisis peak | 2007-06 | 2008-05 | 2008-03 |
| moy max/min | 17.81× | 1.45× | 1.07× |
| moy corr vs author | 0.91 | 1 | — |
| production corr vs USDA | 0.795 | — | — |
| production corr vs author | 0.986 | 1 | — |
| stocks vs USDA | 1.58× (248 vs 157 MMT) | author 325 vs host 248 MMT | — |
| undisturbed last/first | 1.630 | 1.004 | — |

Calendar matches Agrimate (May–June peak; moy corr 0.91);
**amplitude, level, hike, and peak month do not**. September 2007:
host harvest+AMIS **$2.84/t** vs Pink **$342/t**. AMIS does move
Ukraine (P9/P11). P11 prescribed Δ=1/12m zeros Ukraine/Russia XI
(D.3 binds) without moving 2008 mean price (~1.00× harvest-only).

**Correctness.** Item 5 **fails** vs Agrimate. Classification **F**
(95–100%). Not a reason to restore L1–L8 or adopt Bai 10 (P6: αI=10
raises the spike).

---

## Step 11 — Ranked blockers (allowed vs forbidden)

Allowed under hard stops (labelled, `wheat_params()` defaults unchanged):

1. **A7 labelled Fig. 4 configuration** (EU28+Egypt, FAO if present,
   αI=3.5, ζ=1, N_for=6) as a comparison run — the actual published
   experiment.
2. **Item 3:** characterise the undisturbed XI split (Jacobi, rolling
   year, xmin). Diagnose, do not pin. **R4 done:** live D.22 `q_oth`
   is the last/first channel (freeze 1.019 vs author 1.004); xmin and
   calendar replan overshoot. Not adopted.
3. **S4:** author x1=demand as a labelled experiment, not a guessed
   rationing rule. **R5 done:** `x1_from_demand` default off; 2006
   harvest+AMIS max |Δp_w|=0, Σ inflow 478→908 MMT. Not adopted.
4. **A1:** add FAOSTAT FB *only* with PROVENANCE and a parallel
   WheatData; USDA stays default until G0-P says otherwise.
5. **World-price recipe test** vs author `plot_wm_price_timeseries`
   if 14022004 is available locally.
6. **Tests** that fail if identities regress, and tests that *score*
   Fig. 4 gaps with explicit numbers (already started in P7/P8).

Forbidden (hard stops still on):

- G1 / G2 / `dynamic_policy.py` / `dynamic_coupled.py`
- L1–L8 restore
- Pin unforced p_w to 2006 Pink mean
- Retune αI, p_sto, xmin, λ to Pink or to Bai α_foreign=10
- Maize/rice as acceptance
- Treat P11 pulse grid as Gate 2
- Rewrite A8 (China ×2 / EA ×10) without an approved departure — it
  rescales the 2003–11 host

Complexity-budget: a Fig. 4-config *comparison* is closer to
Agrimate’s published wheat than any Pink-Sheet fit, and closer to
the lineage than opening G1.

---

## Step 12 — What to paste next

**Adaptive**, not a skip-nothing ladder. Menu:
[`GATE0_REPRO_PROMPTS.md`](GATE0_REPRO_PROMPTS.md). Living next-paste:
[`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md) (right now **R6**).
Data cookbook: [`GATE0_DATA.md`](GATE0_DATA.md).

R2 is the only forced first evidence run (A7). After that, the
dispatch picks R10 if knobs moved Fig. 4 metrics, R4/R3 if they did
not, skips R11 while defaults are unchanged, and holds R12 until
items 1–5 actually moved. Hard stops do not adapt.

**R5 done (2026-09-20).** `x1_from_demand` labelled, default off. 2006
harvest+AMIS: max |Δp_w|=0, Σ inflow 478→908 MMT. Not a CES ration.
Not adopted. Julia still absent. Living next-paste is **R6**.
`wheat_params()` stay 14022004. Item 3 still fails on the live host.

---

## Verdict

| DEVELOPMENT item | Red-team result | Class |
|---|---|---|
| 1. Source fidelity | Met for 14022004 wheat code, labelled gaps | H / labelled F |
| 2. Numerical reliability | Feasible; not first-order stationary (N5) | C |
| 3. Undisturbed | **Fail** 1.630 vs 1.004; R4: D.22 q_oth is the last/first channel (freeze 1.019, not adopted) | C; not a pin |
| 4. Reference reproduction | Independent; Fig. 4 is a **different experiment** (A7) | F |
| 5. Historical performance | **Fail** vs Fig. 4 and Pink | F |
| 6. Controlled experiments | Three scenarios + P11; AMIS/D.3 bind | H |

**Do not accept G0-P. Do not start G1.** The shortest honest path
toward Agrimate reproduction is R2 (run the Fig. 4 *experiment*),
not a parameter search on Pink Sheet.
