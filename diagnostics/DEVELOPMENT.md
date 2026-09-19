# Development plan

**Current phase:** Gate 0 wheat, Agrimate-faithful host (`sheaf/agrimate/`).
Gate 1 and Gate 2 are **blocked**. They stay blocked until Gate 0 is
vetted at a **publishable** level: source-faithful, numerically reliable,
and equal or better than Agrimate on Agrimate’s own wheat targets.

That sequencing is the lesson from the last cycle. Shipping substitution
and a policy sketch on an unpublishable market was a mistake. Do not
repeat it.

Canonical contract: [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md).
Spec map: [`GATE0_SPEC_MATRIX.md`](GATE0_SPEC_MATRIX.md).
Pasteable one-prompt-per-session list: [`GATE0_PROMPTS.md`](GATE0_PROMPTS.md).
This file is the living queue.

## What “publishable Gate 0” means

Agrimate (Kuhla, Kubiczek & Otto 2025, *Ecol. Econ.* 231:108546) is the
bar, not the legacy SHEAF ask/scarcity scores. For **wheat**:

1. **Source fidelity.** Supplier, purchaser, consumer, storage, restrictions,
   timing, and world-price *definition* match the paper/supplement (or an
   approved departure record). Equation-to-code review, not a prompt.
2. **Numerical reliability.** Supplier plans converge. Constraint residuals
   are small. Failed solves are counted and rare enough that they do not
   set the price path. No fill-target, calm pin, scarcity blend, or rival
   markup to make a test pass.
3. **Undisturbed dynamics.** After spin-up, seasonal repeating behaviour
   as Agrimate describes. Not a flat pinned world price.
4. **Reference reproduction.** Same wheat case, data vintage, parameters,
   and output definitions as closely as access allows. If Zenodo
   14022004 / 10688435 are in hand, compare to author series (Fig. 4 and
   regional supply/consumption/stocks). If they are not, say
   “independent implementation,” not “replication.”
5. **Historical performance.** Price *levels and seasonal paths*, not only
   a correlation. Crisis hike ratios *and* quiet-year levels. Stocks,
   consumption, and trade where Agrimate or USDA/FAO report them.
6. **Controlled experiments.** Harvest-only vs harvest+restrictions, as in
   Agrimate’s three scenarios. Domestic vs international responses.

**Pass rule:** items 1–3 must hold before we spend time judging 5.
Item 5 is judged against Agrimate’s published wheat results, not against
legacy SHEAF. A worse Pink-Sheet fit during debugging does **not** restore
L1–L8 (`GATE0_DEPARTURES.md`).

**Wheat only.** Maize and rice are later Agrimate-style single-crop
applications. Do not accept them with inherited wheat knobs, and do not
use them to wave Gate 0 through.

Gate 0 is **not** currently at the publication bar. **G0-N and G0-S are met**
against retrieved author code. **G0-U is the three-scenario validation
workflow** (`diagnostics/GATE0_VALIDATION.md`): undisturbed / harvest-only /
harvest+AMIS, scoring prices **and** supply/stocks. Pink-Sheet scoring stays
G0-H. G1/G2 stay blocked. The only SHEAF differentiator versus an Agrimate
copy (including the Bai/Wada/Puma copy) is that G1 substitution and G2
government games will be added **after** G0-P.

## Sequence (do not skip)

| Stage | Work | Exit |
|---|---|---|
| **G0-N** | Make the supplier programme numerically solvent on the 24-step wheat year. Record residual, runtime, and when the inverse-demand floor binds. | **Feasible** on 2003–11 (failed/fallback 0; residual 0; offer-floor 0). Unconverged scipy **1743/5832** on harvest+AMIS is labelled N5 (`solver.md`); not first-order stationary. Pink-Sheet scoring is G0-H. |
| **G0-S** | Close source gaps that change economics: C.1 ISO list, D.8 vs F.1, ζ0, D.1b, E.27 support, FAOSTAT Food Balance vs USDA (A1–A6). Retrieve Zenodo code/data if available. Unsent questions: `GATE0_AGRIMATE_BRIEF.md`. | **Met for retrieved code.** 27-region C.1 wheat list, author params, p_sto, x_min penalty, E.27, D.1 weights. β/τ_P labelled unused on wheat path (P3). D.30a formula wired (P4); author x1=demand labelled. FAOSTAT FB absent (P10, A1 left). Fig. 4 zip unpacked (P7); not a replication. |
| **G0-U** | Undisturbed / harvest-only / harvest+AMIS. Accounting identities. Score prices **and** USDA supply/stocks. Ukraine / Eastern Africa mechanism panels. OAT diagnostic without retuning. Protocol: `GATE0_VALIDATION.md`. | Three-scenario report in `diagnostics/gate0_agrimate/`; documented seasonal baseline; material balance. |
| **G0-H** | 2006–11 wheat hindcast vs Pink Sheet **and** vs Agrimate Fig. 4 / regional tables if author output exists. Report levels, paths, hike ratios, stocks, consumption, trade. | **P8–P11 done:** `hindcast.md` sourced shortfall; `regional.md` named-node vs PSD; `faostat_fb.md` — FB arrays not in repo, A1 left, USDA default. `pulse.md` 8-run 2008 prescribed-Δ (Ukraine/Russia × {0.5,1.0} × {6,12}m) is clean; not Bai's 36; not G2. |
| **G0-P** | Gate 0 note at publication standard (methods, data, hindcast, limits). No substitution, no government game. | **Note written, not accepted.** `diagnostics/gate0_agrimate/methods.md` is the market-section offer. Items 3 and 5 fail. G1 stays blocked. |
| **G1** | Cross-crop substitution (wheat/rice/maize), distinct from Agrimate origin CES. Disabled G1 recovers G0. | Identity test + spillover experiments. No σ* fit to 2008. |
| **G2** | Government restriction game, distinct from supplier oligopoly and from AMIS/E.4. Disabled G2 recovers E.4 Agrimate. | Mechanism tests on the *accepted* G0 host. Train/hold-out if estimated. |

G1 and G2 each need an approved departure record before code
(`GATE0_DEPARTURES.md`, `GATE0_EXTENSION_PLAN.md`). Assistant-generated
ideas and leftover `dynamic_coupled` / `dynamic_policy` code are **not**
approval.

## Hard stops

- Do not implement or retune Gate 1 (`sheaf/dynamic_coupled.py`) or Gate 2
  (`sheaf/dynamic_policy.py`) while any G0-N…G0-P box is open.
- Do not treat legacy `diagnostics/gate0_*_report.md` or the Overleaf
  ask/scarcity deck as evidence about the new host.
- Do not move maize/rice onto the new host as an acceptance target.
- Do not “fix” unforced prices by pinning them to the 2006 mean.
- Dead-end artifacts (legacy red-team scratch, uncommitted Overleaf WIP
  on the old map) stay in `archive/` or uncommitted. Do not resurrect them
  as the market.

## Now (G0-U)

1. **G0-N (done).** Always-feasible supplier plan; reference run solvent.
2. **G0-S (done against retrieved code).** Zenodo 14022004 in hand. Wheat
   C.1 is 27 author names; params follow `AgrimateParams`; p_sto and x_min
   penalty; E.27 and D.1 from author. Unresolved labelled in
   `GATE0_AGRIMATE_BRIEF.md`. Data 10688435 unpacked for Fig. 4 (P7).
3. **G0-U (this).** Three-scenario runner `scripts/run_agrimate_validation.py`.
   Bai/Wada/Puma workflow structure (scenarios, prices+stocks+supply,
   mechanism panels, OAT). Author defaults unchanged (αI=3.2, not Bai's 10).
   G1/G2 recorded as later recovery tests, not implemented.
   First 2003–11 run is in `diagnostics/gate0_agrimate/` (AMIS Δ now binds:
   491 region-steps; harvest vs harvest+AMIS no longer identical). Undisturbed
   still drifts (annual-mean ratio 1.63); Pink-Sheet corr remains negative.
   That is a G0-H score, not a reason to restore L1–L8. G0-U exit is the
   **workflow**, not publication-quality hindcast.
4. Single-scenario smoke remains `python scripts/run_agrimate_wheat.py`.
5. **P1 (done).** Step identities on 2006 harvest+AMIS.
6. **P2 (done).** Delivery bug: lagged XI was credited to the *exporter*
   as consumer inflow. T* now routes XI to importers. Stocks/who-eats are
   fixed; world-price 1.63 ratio is unchanged (p_w is on XI, not on who
   receives it). Writeup: `diagnostics/gate0_agrimate/undisturbed.md`.
   Remaining non-periodic xd/xi split is labelled, not pinned.
7. **P3 (done).** β=0.05 / τ_P=0.2 exist in author params and are
   computed in `sales_step!`, but the wheat `two_markets` path pins
   `P_loc=1` in the optimizer and offer prices. Host left unwired
   (`GATE0_DEPARTURES` S3, `GATE0_AGRIMATE_BRIEF` item 6).
8. **P4 (done).** D.30a is on the wheat path (`determine_demands`,
   `ε_d_adjust=false`). Host nested CES matches; A_d=1 recovers D.30.
   Inflow still T*+domestic; author x1=demand is labelled (S4).
9. **P5 (done).** Unconverged = 1743/5832 on harvest+AMIS: feasible,
   residual 0, scipy `success=False` (maxiter + ABNORMAL). Tighter
   maxiter moves prices, but 200 vs 400 disagree as much as 40 vs 400.
   Default `plan_maxiter=40` kept. Writeup: `diagnostics/gate0_agrimate/solver.md`.
10. **P6 (done).** Short harvest+AMIS 2006–08 OAT. αI and low p_sto move
    the 2008 hike; Bai αI=10 raises it and blows pidx_max. εc and σ do not
    move world price (S4). `wheat_params()` unchanged (αI=3.2).
    CSV: `diagnostics/gate0_agrimate/score_sensitivity.csv`.
11. **P7 (done).** Zenodo 10688435 `data.zip` fetched (md5
    `2f3809c66e78b72b3c74971051f89529`). Fig. 4 series scored in
    `diagnostics/gate0_agrimate/fig4.md`. Independent implementation,
    **not a replication**: author baseline last/first=1.004 vs host 1.63
    (P2 unexplained); harvest+AMIS hike ×1.62 author vs ×4.54 host;
    Fig. 4 executable is AgrimateEU28+Egypt, FAO anomalies, α_foreign=3.5,
    ζ=1, N_for=6, git `old-demand-dynamics`. Host `AgrimateParams` unchanged.
12. **P8 (done).** G0-H hindcast note: `diagnostics/gate0_agrimate/hindcast.md`.
    Explicit sourced shortfall vs Agrimate Fig. 4, not a retune. 2006 level
    $65 vs Pink $213; hike ×4.54 vs Agrimate ×1.62 vs Pink ×1.88; seasonal
    max/min ~18× vs Agrimate 1.45× vs Pink 1.07× (Sep 2007 $2.8 vs $342).
    Production corr +0.795 vs USDA. Stock level **1.58×** USDA after P2
    (prompt's ~3× was the echo bug). AMIS adds May 2008, not the 2007
    spike. Bai αI=10 not adopted. `wheat_params()` unchanged.
13. **P9 (done).** Regional USDA: `diagnostics/gate0_agrimate/regional.md`.
    Named exporters + Eastern Africa vs `psd_regional_annual()` 2006–11.
    Single-row nodes match production *means*; China 0.50× and Eastern
    Africa 0.10× because `prepare_wheat` `groupby.mean()`s members (A8,
   labelled, not fixed). No xmin/p_sto fit. `wheat_params()` unchanged.
14. **P10 (done).** FAOSTAT Food Balance arrays are **not** in
    `data/faostat_network/` (the path named in the prompt: E0 trade only).
    FoodTradeNetwork P0/R0 are 2015–21 averages, not 2006–11 FB. A1 left.
    USDA stays default. No parallel `WheatData`. Writeup:
    `diagnostics/gate0_agrimate/faostat_fb.md`.
15. **P11 (done).** Prescribed-Δ 8-run on harvest-anomaly wheat, 2008:
    Ukraine and Russia × {0.5, 1.0} × {6, 12} months vs harvest-only.
    `restriction_pulse` (AMIS-style Δ, not a government best-response).
    Slice is **clean**: failed=0, production identical, Δ on one exporter,
    Δ=1.0/12m zeros that exporter's XI; Δ=0.5/12m halves it. 6-month
    Jan–Jun pulses miss NH harvest (Jul–Sep). World price 0.99–1.01×
    harvest-only. Not expanded to Bai's 36-run 2020 grid. Not G2.
    `wheat_params()` unchanged. Writeup:
    `diagnostics/gate0_agrimate/pulse.md`.
16. **P12 (done).** G0-P methods note: `diagnostics/gate0_agrimate/methods.md`.
    Independent Agrimate copy; not a Fig. 4 replication; no substitution;
    no government game. **Recommend reject** as the SHEAF market section
    (item 3 undisturbed 1.63 vs author 1.004; item 5 hike ×4.54 vs
    Agrimate ×1.62 vs Pink ×1.88). `wheat_params()` unchanged. G1/G2
    stay blocked until a later G0-P acceptance. Do not start G1 from
    this note.
17. **R1 (done).** Post-P12 red team: `diagnostics/GATE0_REDTEAM.md`.
    Host does **not** reproduce Agrimate Fig. 4. `tests/agrimate` pass because
    they lock honesty (including host hike > author hike), not a match.
    Data cookbook: `GATE0_DATA.md`. Next queue:
    `GATE0_REPRO_PROMPTS.md` (adaptive). `wheat_params()` unchanged. G1/G2 stay blocked.
18. **R2 (done).** Labelled `fig4_experiment_params()` copies
    Fig. 4 knobs (αI=3.5, ζ=1, N_for=6) without replacing `wheat_params()`.
    2006–08 harvest+AMIS: hike ×2.31→×2.22 vs author ×1.62; moy max/min
    26.8×→13.3× vs 1.51×; unconverged 611→553 / 1944, failed=0.
    Undisturbed last/first 0.618→0.409 vs author 1.006 (wander not fixed).
    FAO/EU28/start-2000 still cannot be set. Note: `fig4_config.md`.
   **Next session:** paste **Next paste** from `GATE0_REPRO_DISPATCH.md`
   (currently **R10**).

Reference command:

```bash
python -m pytest tests/agrimate -q
PYTHONPATH=. python scripts/run_agrimate_validation.py
```

Solver smoke (one harvest+AMIS path):

```bash
PYTHONPATH=. python scripts/run_agrimate_wheat.py
```

Legacy (labelled, not the bar):

```bash
python scripts/score_legacy_crop.py --crop wheat
```

## Prior cycle (legacy ask/scarcity host) — closed

The 2026-08 characterization (A1–A5, red-team, Potsdam note) documented the
**old** sequential map. It is useful as a record of why that map is not
Agrimate. It is not a Gate 0 publication path.

- Artifacts: `diagnostics/gate0_prep/`, `diagnostics/redteam/`,
  `archive/legacy-gate0/`, `overleaf/gate0_discussion/`
- Code: `sheaf/legacy/`, `sheaf/dynamic_crop.py` (Gate 1 still imports this
  copy; do not extend it)

Parked, not next:

| Layer | Status |
|---|---|
| Gate 1 isoelastic substitution | Blocked until G0-P |
| Gate 2 Headey-clock actions | Blocked until G0-P, then G1 identity |
| Annual SPE `sheaf.annual` | Parked |
| `dynamic_grains.py` | Paused |
