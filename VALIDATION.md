# Validating SHEAF against the 2007/08 and 2010/11 crises

The benchmark is Kuhla, Kubiczek & Otto, *Understanding agricultural market
dynamics in times of crisis: the dynamic agent-based network model Agrimate*
(Ecological Economics 231, 2025). Agrimate hindcasts wheat through both crises,
reproducing monthly world price hikes and annual regional supply and stock
changes (Fig. 4; Egypt consumption is a path panel, not the global/regional bar). Crucially, it **imposes** the historical export restrictions as exogenous
forcing (read from the AMIS policy database, bans ≈ 95% and taxes ≈ 50% quantity
cuts) and leaves endogenous restriction dynamics to future work. That is the gap
SHEAF fills.

## Gate 0 — Agrimate-aligned reproduction first

**Gate 0 is green** (per-crop asserts PASS; official scores in
`diagnostics/gate0_*_report.md`; writeup `overleaf/gate0_whitepaper/`).
Substitution has its own note (Gate 1). The endogenous game is a
**layer on this spine**, not a sequel paper that waits on a queue.
Do not retune Gate 0 leftovers with crisis knobs.

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

**Within-year timing (required for Hard):** harvest calendars + lean foresight +
FAOSTAT bilateral (Armington) trade + **ask-dominated** world prices each step
(`sheaf/dynamic_crop.py`). Twin path is an identity diagnostic, not the main
price law. Asserts: twin identity, AMIS price lift, key exporter cut under ban,
no spring spike.

**Per-crop first (locked 2026-08-24):** prove wheat, maize, and rice **separately**
before substitution or Level 2. Plan:
[`diagnostics/GATE0_PER_CROP_PLAN.md`](diagnostics/GATE0_PER_CROP_PLAN.md).
Score with `python scripts/score_subannual_crop.py --crop {wheat,maize,rice}`.

Provisional annual Level-1 scripts (`score_level1.py`, crisis-era annual SPE)
remain useful for **data plumbing** only; they are not Gate 0. Full
interrogation of the annual wrong-sign episode:
`diagnostics/LEVEL1_INTERROGATION.md`. Multi-grain spillover scripts are demoted
until all three single-crop Gate 0 reports are green.

## Two levels

**Level 1 — reproduction (matched to Agrimate).** Drive SHEAF with observed
production anomalies *plus* the observed restrictions as exogenous `tau`, and match
the published targets: the annual world-price hike, the sign of regional supply and
stock anomalies, and the production-vs-restriction attribution (Agrimate finds
2007 production-led, 2010/11 restriction-led). This checks the market + storage
core. Honest ceiling under the *old* annual SPE clock: annual magnitudes only,
not Agrimate's bi-weekly dynamics — **that clock is retired for Gate 0**; see
ARCHITECTURE.md (24 steps/yr). Temporal resolution is where SHEAF now competes.

**Level 2 — endogenous restriction calibration (SHEAF's unique test).**
Drive the **Gate 0 24-step spine** with production anomalies *only*, let
governments choose **actions** `τ_{i,t}` on that clock, and keep **types**
(food-security weights, who plays) slow — Headey (2011), not the annual
Nash in `sheaf/core.py`. Fit types on a declared training window, then
score restrictors / timing / severity / prices on a **held-out** window.
The one-player beta with labeled illustrative knobs is a mechanism check,
not that score (`diagnostics/GAME_CLOCK.md`). Neither Agrimate (restrictions
exogenous) nor a no-strategy model can be evaluated on the same margin.

**Gate 0 and Gate 1 do not need to be re-run** to host this layer: Gate 0 is
substitution off / game off (AMIS diary); Gate 1 is substitution on / game
off. Headey does not change CropParams or σ. Collaborator “P4/P5”
questions are variants of this layer, not extra papers
(`diagnostics/PAPER_STACK.md`).

**Bonus — multi-commodity.** 2007/08 is the natural substitution test: rice spiked
on its own export-ban panic (India, Vietnam) partly linked to wheat. Agrimate runs
each grain separately and does not model cross-commodity substitution; SHEAF runs
them jointly, so the cross-grain linkage is a signal the separate runs cannot
produce.

## Research questions (not a paper queue)

Collaborator feedback listed *uses* of SHEAF, not five manuscripts.
Full note: [`diagnostics/PAPER_STACK.md`](diagnostics/PAPER_STACK.md).

Gate 0 (hindcast) and Gate 1 (substitution) are the writeups that exist.
“Who restricts,” “just enough / club,” “tipping,” and “emergent network”
are questions that may share a note, become an appendix, or never stand
alone. They are not a sequence. Level 2 in this file is the **positive**
game on the 24-step spine (“who restricted, when?”). Normative variants
(club, tipping) are the same layer with a different objective. Do not
re-run Gate 0 or Gate 1 to start them (`diagnostics/GAME_CLOCK.md`).

**Next:** more than one government on that clock — still a mechanism
check, not a 2008 score, not a new title.

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

