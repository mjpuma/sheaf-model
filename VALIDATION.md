# Validating SHEAF against the 2007/08 and 2010/11 crises

The benchmark is Kuhla, Kubiczek & Otto, *Understanding agricultural market
dynamics in times of crisis: the dynamic agent-based network model Agrimate*
(Ecological Economics 231, 2025). Agrimate hindcasts wheat through both crises,
reproducing monthly world price hikes and annual regional supply/consumption/stock
changes. Crucially, it **imposes** the historical export restrictions as exogenous
forcing (read from the AMIS policy database, bans ≈ 95% and taxes ≈ 50% quantity
cuts) and leaves endogenous restriction dynamics to future work. That is the gap
SHEAF fills.

## Two levels

**Level 1 — reproduction (matched to Agrimate).** Drive SHEAF with observed
production anomalies *plus* the observed restrictions as exogenous `tau`, and match
the published targets: the annual world-price hike, the sign of regional supply and
stock anomalies, and the production-vs-restriction attribution (Agrimate finds
2007 production-led, 2010/11 restriction-led). This checks the market + storage
core. Honest ceiling: SHEAF is an annual-ish equilibrium model, so it targets
annual magnitudes, not Agrimate's bi-weekly out-of-equilibrium rationing. Temporal
resolution is not where SHEAF competes.

**Level 2 — endogenous prediction (SHEAF's unique test).** Drive SHEAF with
production anomalies *only*, switch the strategic game on, and let it choose
restrictions. Score against history: did it predict the right restrictors (Russia,
Ukraine, Kazakhstan, Argentina, ...), roughly the right timing/severity, and the
right prices? Neither Agrimate (restrictions exogenous) nor a no-strategy model can
be evaluated on this. Calibrating the food-security weights and price triggers so
the game reproduces the observed cascade is the scientific contribution.

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

1. **Per-country PSD** (production, consumption, stocks) — local export, same schema
   as the world files; drives the node-level calibration and the Level-2 anomalies.
   *(source identified: USDA PSD, local)*
2. **AMIS export-restriction timeline** — forcing for Level 1, ground truth for
   Level 2. Available through the Agrimate collaboration.
3. ~~Baseline bilateral trade network~~ — **done**, via FAOSTAT `E0` matrices
   (`sheaf/data_faostat.py`), including the crisis-year windows.
4. **Observed world price series** (deflated) — the Level-1 price target.
