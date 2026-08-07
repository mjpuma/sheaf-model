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

## Data alignment (AgRichter Scale)

Forcing and validation targets come from USDA PSD, aligned to the schema in the
AgRichter Scale repo (`mjpuma/AgRichterScale`, `USDAdata/`). `sheaf/data_usda.py`
reads that schema, converts to MMT, builds LOWESS-detrended production anomalies
(the same detrending Agrimate uses), and computes stock-to-use ratios for storage
calibration. `scripts/validate_forcing.py` builds the forcing and checks it against
both crises (see `figures/fig5_usda_forcing.png`).

What ships here is the **world-aggregate** series, enough to derive the forcing and
validate the global price/supply/stock response. Note that the world wheat anomaly
in 2010 is only about −4%, which understates the ~−33% Russian regional loss that
actually triggered the ban — a reminder that Level 2 (predicting *who* restricts)
requires the **per-country** PSD series, which load from a local export in the same
schema.

## Remaining external inputs

1. **Per-country PSD** (production, consumption, stocks) — local export, same schema
   as the world files; drives the network calibration and the Level-2 anomalies.
2. **AMIS export-restriction timeline** — forcing for Level 1, ground truth for
   Level 2. Available through the Agrimate collaboration.
3. **Baseline bilateral trade network** (BACI / COMTRADE, or the Agrimate baseline)
   — SHEAF's transport/route structure and baseline flows.
4. **Observed world price series** (deflated) — the Level-1 price target.
