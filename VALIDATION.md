# Validating SHEAF against the 2007/08 and 2010/11 crises

The benchmark is Kuhla, Kubiczek & Otto, *Understanding agricultural market
dynamics in times of crisis: the dynamic agent-based network model Agrimate*
(Ecological Economics 231, 2025). Agrimate hindcasts wheat through both crises,
reproducing monthly world price hikes and annual regional supply/consumption/stock
changes. Crucially, it **imposes** the historical export restrictions as exogenous
forcing (read from the AMIS policy database, bans ≈ 95% and taxes ≈ 50% quantity
cuts) and leaves endogenous restriction dynamics to future work. That is the gap
SHEAF fills.

## Gate 0 — Agrimate-aligned reproduction first

**Nothing in Level-2 (endogenous game) proceeds until Gate 0 is green.**

**Clock (locked):** **24 time steps per year** (~15.2 days), matching Agrimate
(Kuhla et al. 2025 §4.1). Not annual. Not 26 fortnights by default — see
[ARCHITECTURE.md](ARCHITECTURE.md) for why 24 (month tiling + harvest calendars
+ monthly Pink Sheet targets) and when 26 would be considered.

**Dynamics (locked):** sub-annual, out-of-equilibrium stock–trade adjustment
(Agrimate/acclimate-style). Annual spatial price equilibrium is demoted to a
reference/diagnostic, not the heartbeat. We are validating **crisis shock
paths**, not annual equilibrium magnitudes alone.

| Gate | Criterion | Notes |
|---|---|---|
| Hard | Monthly wheat world price signs/timing for 2007/08 and 2010/11 vs Pink Sheet | Agrimate’s published bar |
| Soft | Annual regional supply & stock-to-use signs | Agrimate Fig. 4 style |
| Soft | Attribution: 2007 production/stock-led vs 2010 restriction-led | shocks vs AMIS legs |
| Block | No Level-2 fitting until Hard is green | |

**Within-year timing (required for Hard):** harvest calendars with peak months +
lean-horizon foresight + **path-matched twin** liquid-free pricing
(`sheaf/dynamic_wheat.py`). Fake Mar–Apr lean-season spikes and drifting
no-force baselines are Gate 0 failures (see `assert_twin_identity`,
`assert_no_spring_spike`, `assert_amis_raises_price`). Score with
`python scripts/score_subannual_wheat.py`. Hike *signs* and crisis peak months
(± a few months) are the Hard bar; absolute hike magnitudes remain open.

Provisional annual Level-1 scripts (`score_level1.py`, crisis-era annual SPE)
remain useful for **data plumbing** only; they are not Gate 0. Full
interrogation of the annual wrong-sign episode:
`diagnostics/LEVEL1_INTERROGATION.md`.

## Two levels

**Level 1 — reproduction (matched to Agrimate).** Drive SHEAF with observed
production anomalies *plus* the observed restrictions as exogenous `tau`, and match
the published targets: the annual world-price hike, the sign of regional supply and
stock anomalies, and the production-vs-restriction attribution (Agrimate finds
2007 production-led, 2010/11 restriction-led). This checks the market + storage
core. Honest ceiling under the *old* annual SPE clock: annual magnitudes only,
not Agrimate's bi-weekly dynamics — **that clock is retired for Gate 0**; see
ARCHITECTURE.md (24 steps/yr). Temporal resolution is where SHEAF now competes.

**Level 2 — endogenous restriction calibration (SHEAF's unique test).** Drive SHEAF
with production anomalies *only*, switch the strategic game on, and let it choose
restrictions. **Fit** food-security weights and price triggers so the model
reproduces the observed cascade on a declared training window, then score
restrictors / timing / severity / prices on a **held-out** window (or pooled
structural parameters — see audit Finding P7-F4). This is a calibration-and-
identification exercise, not an a-priori prediction claim. Neither Agrimate
(restrictions exogenous) nor a no-strategy model can be evaluated on the same
margin. Acquiring AMIS timelines and per-country PSD remains a prerequisite;
the shipped repo does not yet run this pipeline end-to-end.

**Bonus — multi-commodity.** 2007/08 is the natural substitution test: rice spiked
on its own export-ban panic (India, Vietnam) partly linked to wheat. Agrimate runs
each grain separately and does not model cross-commodity substitution; SHEAF runs
them jointly, so the cross-grain linkage is a signal the separate runs cannot
produce.

## Data alignment

Each input is drawn from the source that reports it as a genuine measured
quantity — not a residual — across two of Michael's repositories.

**Production, consumption, reserves → USDA PSD (AgRichter Scale).**
`sheaf/data_usda.py` reads the AgRichter `USDAdata/` schema, converts to MMT,
builds LOWESS-detrended production anomalies (the detrending Agrimate uses), and
computes stock-to-use ratios for storage calibration. `scripts/validate_forcing.py`
builds the forcing and checks it against both crises (`figures/fig5_usda_forcing.png`).
Reserves come from here specifically because USDA reports stocks as a real series.

**Bilateral trade network → FAOSTAT (FoodTradeNetwork).**
`sheaf/data_faostat.py` reads the processed `E0` matrices, keys them to ISO3 via
the repo's country conversion table, and aggregates to a node set. It handles the
three keyings present across files (FAOSTAT codes, ISO3, or names) and the matched
2-year windows, so the actual **2006–07 and 2010–11 crisis networks** are available,
not just one baseline. `scripts/build_network.py` reconstructs the wheat network and
validates it against history (`figures/fig6_network.png`): Egypt's Russia dependence
rises 37% → 46% → 52% across the windows — the vulnerability behind the 2010/11
Egypt episode.

**Reserves are NOT taken from FAOSTAT.** FAOSTAT does not measure stocks; in a
food-balance pipeline the "reserves" are the residual (production + imports −
exports − utilisation) and absorb every accounting error. `data_faostat` supplies
the network only, and P0/R0 come from USDA. Absolute E0 magnitudes are treated as
unit-agnostic (use `bilateral_shares` for structure, `rescale_to_total` to pin the
scale to a USDA total).

Caveat that the data itself surfaces: the *world* wheat anomaly in 2010 is only
about −4%, which understates the ~−33% Russian regional loss that triggered the
ban — a reminder that Level 2 (predicting *who* restricts) needs the **per-country**
PSD series, loaded from a local export in the same schema.

## Remaining external inputs

1. ~~**Per-country PSD**~~ — **done** (2026-08-22). Official FAS bulk ZIP under
   `data/usda_psd/` (`psd_grains_country_year.csv`; loader
   `sheaf.data_usda.load_psd_country`). See `data/usda_psd/PROVENANCE.txt`.
2. ~~**AMIS export-restriction timeline**~~ — **done** (2026-08-22). OECD/AMIS
   export-restrictions workbook under `data/amis_policies/` (loader
   `sheaf.data_usda.load_amis_restrictions`). See `data/amis_policies/PROVENANCE.txt`.
   Refresh the XLSX from the OECD page in a browser if a newer release appears
   (unattended fetch is Cloudflare-blocked).
3. ~~Baseline bilateral trade network~~ — **done**, via FAOSTAT `E0` matrices
   (`sheaf/data_faostat.py`), including the crisis-year windows.
   **Kazakhstan** is a named SHEAF node (`SHEAF_NODE_MAP["Kazakhstan"]=KAZ`).
4. ~~**Observed world price series** (deflated)~~ — **done** (2026-08-22).
   World Bank Pink Sheet annual prices under `data/world_prices/`
   (`pink_sheet_grains_annual.csv`; loader `sheaf.data_usda.load_price_series`,
   MUV-deflated 2010 USD by default). See `data/world_prices/PROVENANCE.txt`.
   Score the Level-1 hindcast with `python scripts/score_level1.py`
   (`diagnostics/level1_price_score.csv`, `figures/fig10_level1_price_score.png`).

Refresh helpers: `python scripts/fetch_external_data.py`
(`--psd-only` / `--amis-only` / `--prices-only`).

