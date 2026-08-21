# SHEAF Audit — Phase 2 Agent 6: Calibration & Data Pipelines

Standalone report. Scratch reproductions under `/tmp/sheaf_audit_agent6/`.
Read-only against `sheaf/*.py`, `demo.py`, and `scripts/*.py` throughout.

**Scope.** Prototype calibration (`sheaf/calibration.py`), USDA world PSD adapter
(`sheaf/data_usda.py`), FAOSTAT trade-network adapter (`sheaf/data_faostat.py`),
vendored provenance, and diagnostic scripts. Agent 7 already covered validation
design and policy-parameter identification; overlaps are noted, not re-adjudicated.

**Terminological separation used throughout.**

| Layer | What it is | What it is not |
|---|---|---|
| **Prototype calibration** | Hand-entered `calibration.py` DATA + globals used by `demo.py` / `build_countries()` | An empirical estimate; a hindcast input |
| **Empirical adapters** | `data_usda.py`, `data_faostat.py` + vendored CSVs | Wired into the runnable model path |
| **Validation data** | Intended Level-1/2 inputs in VALIDATION.md (per-country PSD, AMIS, prices) | Present in this repository (except wheat E0 windows + world PSD) |

Phase 1 items touching this remit (esp. Agent 3 **S15**) are treated as
hypotheses and independently re-checked below.

---

## Part A — Architecture of the three data layers

```
┌─────────────────────────────┐     ┌──────────────────────────────┐
│  calibration.py (prototype) │     │  data_usda.py (world PSD)    │
│  Q, D0, stocks, ε, ρ, w, p̄ │     │  anomalies, SUR, forcing     │
│  haversine transport c_ij   │     │  scripts/validate_forcing.py │
└─────────────┬───────────────┘     └──────────────┬───────────────┘
              │                                    │
              ▼                                    ▼
        demo.py / SheafModel              figures only (no SheafModel)
              ▲
              │ (NOT connected)
┌─────────────┴───────────────┐
│  data_faostat.py (E0 wheat) │
│  scripts/build_network.py   │
└─────────────────────────────┘
```

Verified call graph (`rg` across `*.py`):

- `build_countries` ← `demo.py`, `sheaf/__init__.py` only.
- `load_crop_world` / `detrend_anomalies` / `stock_to_use` ← `scripts/validate_forcing.py` only.
- `crisis_forcing` ← **never called** by any script or demo.
- `load_trade_matrix` / `aggregate_to_nodes` ← `scripts/build_network.py` only.
- `demo.py` imports neither `data_usda` nor `data_faostat`.

---

## Part B — Parameter-sourcing classification table

Sourcing codes: **O** = directly observed in repo data; **D** = derived from
observed data; **L** = literature-calibrated (cited); **I** = internally
calibrated to model targets; **P** = illustrative prototype (disclosed);
**A** = arbitrary / software default; **U** = currently unsourced (claimed
source not present or not cited).

| Parameter | Symbol / location | Value (shipped) | Source class | Notes |
|---|---|---|---|---|
| Grains list | `GRAINS` | wheat, rice, maize | P | Extensible by design |
| Reference prices | `P0` | 250, 400, 200 $/t | P / U | No citation; order-of-magnitude |
| Own-price elasticities | `OWN_ELAST` / ε | −0.25, −0.20, −0.30 | P / U | README §7 claims “demand-system literature”; no citation or source table |
| Substitutability | `RHO` / ρ | off-diag 0.30/0.40/0.20 | P / U | Same; `subst_scale=0.6` is A |
| Freight multipliers | `FREIGHT_MULT` | 1.00, 1.10, 0.95 | P / A | Scales haversine costs; not from freight data |
| Global prod/cons anchors | `GLOBAL_PROD/CONS` | 780 / 520 / 1150 MMT | P | Equal by construction; wheat ~23% above USDA 2019–21 mean |
| Named Q, D0 | `DATA[*].prod/cons` | 16×3 each | P | Hand-entered; RoW closes residual |
| RoW Q, D0 | residual | see Finding 2 | D (from P) | `GLOBAL − named sum`; always non-negative here |
| Lat/lon | `DATA[*].lat/lon` | country centroids | P | RoW fixed at (20,20) — A |
| Transport costs | `c_ij` | `0.0025·km + 8` | A / P | Haversine; **not** FAOSTAT E0 |
| Import tariffs | `Country.tariff` | all 0 | A | Field exists; never set in calibration |
| Export grain set | `export_grains` | hand lists | P | Defines who plays the game |
| Food-security weights | `fs_w` / w | hand per exporter | P / I* | *VALIDATION.md intends Level-2 calibration; not performed |
| Price triggers | `pt` / p̄ | hand; many `INF` | P / I* | Same |
| Private γ | `mkt` / γ | hand or 0 | P | Only countries with `mkt=` key |
| Private stock init | `0.15·Q` | rule | A | When `mkt` present |
| Private capacity | `0.5·Q` | rule | A | When `mkt` present |
| Private deadband | `mkt_cost` | 8 $/t all | A | Country default; never overridden |
| Gov stocks R0 | `gov.stock` | India/China/Egypt only | P | Not from `stock_to_use` |
| Gov target SUR | `gov.ratio` | hand | P | Docstring of `stock_to_use` claims calibration use; unwired |
| Gov price trigger | `gov.trig` | hand / INF | P | |
| Gov release/build frac | defaults | 0.5 / 0.10 | A | `core.py` Country defaults |
| τ_max, grid, iters, tol | game defaults | 120, 5, 3, 3.0 | A | |
| stress_trigger, κ, r | model defaults | 1.12, 0.5, 0.05 | A | |
| World production series | USDA CSV | 1960–2025 | O | Vendored; kt→MMT |
| Production anomalies | LOWESS | 1+anom | D | From world series |
| Stock-to-use | ending/cons | series | D | Computed; unused by calibration |
| Crisis forcing ξ | `crisis_forcing` | multipliers | D | API exists; unused by scripts/demo |
| Bilateral E0 (wheat) | FAOSTAT | 3 windows | O | Unit-agnostic magnitudes |
| E0 rice/maize | — | **absent** in vendor | U (upstream) | Docstring overclaims vendored coverage |
| Node map / EU list | `SHEAF_NODE_MAP` | 16 + RoW | P / A | Fixed EU-27; GBR→RoW |
| Per-country PSD | — | **missing** | U | VALIDATION.md remaining input #1 |
| AMIS restrictions | — | **missing** | U | Remaining #2 |
| Price series | — | **missing** | U | Remaining #4 |

\*Overlap with Agent 7: `fs_weight` / `p_target` are the intended Level-2 fit
parameters; this agent confirms they are **prototype hand values**, not the
output of any calibration routine in the repo.

---

## FINDING 1 — Runnable model is disconnected from USDA/FAOSTAT adapters

**Finding.** The only end-to-end model path (`demo.py` → `build_countries` →
`SheafModel`) never reads USDA or FAOSTAT. README §7 states in the present
indicative that “Production Q, baseline consumption D0, and stocks S0 come from
USDA PSD (`sheaf/data_usda.py`)” and that the baseline network “is built from
the FAOSTAT bilateral matrices.” That describes an intended architecture, not
the implemented one. Caveats (README L322–323) correctly call the numbers
illustrative; §7 does not.

**Classification:** G (primary), F (secondary — empirical calibration not yet
wired). **Severity:** High (for any reader treating §7 as a data claim).
**Confidence:** 95–100%.

**Evidence.**

- Mathematical/economic claim: README §7 L236–240; VALIDATION.md L42–64.
- Code: `demo.py` imports only `build_countries`; `rg` shows `data_usda` /
  `data_faostat` used only by diagnostic scripts.
- Numerical: `crisis_forcing()` has zero callers; `stock_to_use` never enters
  `Country` construction.

**Attempt to falsify.** “§7 describes the *pipeline design*, and Caveats
disclaim the prototype.” Partially succeeds for Caveats, but §7’s present
tense (“come from”, “is built”) is still false of the runnable code path.
VALIDATION.md is more careful (“reads… builds…”) about the adapters themselves.

**Falsification result:** Claim as written is false of the implementation;
Caveats correctly disclose the prototype. Net: documentation inconsistency.

**Recommended action.** Soften README §7 to subjunctive / “intended”; state
explicitly that `calibration.py` is the active parameter source until replaced.
Optionally add a one-line assert or stub in `build_countries` docstring pointing
at the adapters.

**Complexity-budget:** Documentation only. **Changes published results:** No
(model output unchanged); changes how results may be described.

**Phase 1 S15:** CONFIRMED that storage params are not sourced from
`stock_to_use` (independent re-check).

---

## FINDING 2 — Rest-of-World closes quantity balance correctly; wheat global anchor is high vs USDA

**Finding.** RoW construction `row = GLOBAL − sum(named)` yields non-negative
production and consumption for all three grains, and world net export sums to
machine zero. Named countries cover ~82%/97%/90% of GLOBAL production
(wheat/rice/maize) but only ~69%/89%/82% of consumption — so RoW is a large
structural net importer by construction (wheat net −101.6 MMT). Separately,
`GLOBAL_PROD` wheat = 780 MMT is ~22% above USDA 2019–21 world mean (636 MMT)
and ~59% above 2007 crisis-era world production (491 MMT). Rice and maize
globals are within ~3–5% of 2019–21 USDA means.

**Classification:** H for accounting identity; P/G for wheat level (illustrative
disclosed, but wheat is outside “order-of-magnitude” comfort relative to the
crisis years the validation plan targets). **Severity:** Low–medium (prototype);
would become High if used as empirical baseline for 2007/10 hindcasts without
rescaling. **Confidence:** 95–100%.

**Evidence.**

```
Named prod sum: [642.1, 505.2, 1034.5]
GLOBAL_PROD:    [780.0, 520.0, 1150.0]
RoW prod:       [137.9,  14.8,  115.5]
Sum of nets + RoW: ~0 (float)
USDA wheat 2019–21 mean prod 636.3 → GLOBAL/USDA = 1.226
USDA wheat 2007 prod 490.9 → GLOBAL/USDA = 1.589
```

**Attempt to falsify.** “RoW could go negative if named sum exceeds GLOBAL.”
Not observed in shipped DATA; all RoW entries ≥ 0. “Order-of-magnitude” for
wheat 780 vs 636 is still the same 10² MMT scale — true, but the crisis-era gap
is large enough to distort shock magnitudes if GLOBAL were used as the Level-1
baseline without replacement.

**Falsification result:** Accounting claim holds. Magnitude claim is acceptable
only under the prototype disclaimer; not as a 2007/10 calibration.

**Recommended action.** When replacing the prototype, set GLOBAL (or drop it)
from USDA world or summed per-country PSD for the study window. No new data
needed beyond already-identified per-country PSD.

**Complexity-budget:** Favourable. **Changes results:** Yes, once empirical
baseline replaces prototype.

---

## FINDING 3 — Private/gov storage parameters are illustrative and unwired from SUR

**Finding.** `data_usda.stock_to_use` correctly computes ending stocks /
consumption and `validate_forcing.py` plots wheat SUR, but `build_countries`
initialises private stocks as `0.15·production` and capacities as `0.5·production`
for countries with a `mkt` entry, and sets government stocks/ratios only for
India, China, and Egypt by hand. World SUR from USDA (wheat 2007: 0.23;
2019–21: 0.42) is never mapped into `gov_target_ratio` or `mkt_stock`.
Prototype total stocks (gov+mkt) are roughly 198 / 159 / 204 MMT vs USDA ending
stocks ~274 / 185 / 300 MMT (2019–21) — same order of magnitude, different
composition (China alone holds 100 MMT gov stock in each grain).

**Classification:** F relative to VALIDATION.md’s “stock-to-use … for storage
calibration” wording; H relative to calibration.py’s own “illustrative”
disclaimer. **Severity:** Medium for a claimed empirical storage calibration;
Low for the prototype demo. **Confidence:** 95–100%.

**Code evidence.** `calibration.py:153–157`; `data_usda.py:92–95`; no call path
from SUR → Country.

**Attempt to falsify.** “SUR is only a diagnostic, not a claimed input.”
VALIDATION.md L45 and `stock_to_use` docstring both say “for storage
calibration.” That claim is unimplemented.

**Falsification result:** Unwiring confirmed. Phase 1 S15 CONFIRMED.

**Recommended action.** Either (a) wire `gov_target_ratio` / initial stocks to
USDA SUR (world or per-country when available), or (b) reword VALIDATION.md /
docstring to “diagnostic only.” Prefer (a) once per-country PSD exists — no new
external data type required.

**Complexity-budget:** Low (formula mapping). **Changes results:** Yes for
storage dynamics; demo Black Sea story may shift.

---

## FINDING 4 — LOWESS implementation is correct (matches non-robust statsmodels)

**Finding.** Hand-rolled `_lowess` (local linear, tricube weights, no robust
iterations) reproduces `statsmodels.nonparametric.smoothers_lowess.lowess(..., it=0)`
to ~1e-13 relative error on the full wheat production series. Constant and
linear series recover exactly. Crisis wheat anomalies:

| Year | SHEAF LOWESS | statsmodels it=0 | statsmodels it=3 (default robust) |
|---|---|---|---|
| 2006 | −4.08% | −4.08% | −4.11% |
| 2007 | −2.48% | −2.48% | −2.50% |
| 2010 | −4.05% | −4.05% | −4.19% |

`frac = window_years / n` with `window_years=10` → frac≈0.1515, k=10 on n=66 —
consistent with the docstring’s Agrimate-style ~10-year window. Difference vs
robust LOWESS is ≤0.15 pp at crisis years — immaterial for world-aggregate
forcing.

**Classification:** H. **Severity:** None. **Confidence:** 95–100%.

**Attempt to falsify.** “Missing robust iterations invalidate Agrimate
comparability.” Numerically the crisis anomalies barely move. “Edge-case
outlier not downweighted” — true of non-robust LOWESS by design; not a bug
relative to the stated algorithm.

**Falsification result:** Implementation is correct for the stated estimator.

**Recommended action.** None required. Optional docstring note: “non-robust
(it=0); Agrimate if using robust LOWESS differs by <0.2 pp here.”

**Complexity-budget:** N/A. **Changes results:** No.

---

## FINDING 5 — Crisis forcing is correctly derived but only world-aggregate; scripts do not score it

**Finding.** `crisis_forcing` returns `1 + anomaly` multipliers that match
direct `detrend_anomalies` output. World wheat anomaly ~−4% in 2006 and 2010
matches VALIDATION.md’s own caveat (L66–69). `scripts/validate_forcing.py`
plots production, anomalies, and SUR with crisis shading and prints anomalies —
it does **not** call `SheafModel`, does **not** call `crisis_forcing`, and does
**not** compare against any Agrimate or price target. Naming and VALIDATION.md
L45–46 (“checks it against both crises”) overstate what the script does.

**Classification:** H for the forcing math; G for script/VALIDATION wording; F
for absence of an executable hindcast (overlap Agent 7 Finding 5 — independently
verified). **Severity:** Medium (process), High (if cited as validation).
**Confidence:** 95–100%.

**Numerical reproduction (multipliers):**

```
       wheat   rice  maize
2006   0.959   0.994  0.965
2007   0.975   1.006  1.050
2010   0.960   0.987  0.976
```

**Attempt to falsify.** “Shaded crisis windows constitute a check.” Visual
alignment ≠ quantitative validation. The printed anomalies are the check’s
entire content.

**Falsification result:** Forcing construction OK; validation claim not met.

**Recommended action.** Rename or re-scope script as diagnostic; keep
VALIDATION.md’s honesty about needing per-country PSD for Level 2. No new data
collection beyond already-listed remaining inputs.

**Complexity-budget:** Docs/script naming. **Changes results:** No.

---

## FINDING 6 — FAOSTAT loader preserves totals; drops are tiny; row keying docstring is stale

**Finding.** For all three vendored wheat windows, `aggregate_to_nodes` preserves
matrix sum exactly (`diff=0`). ISO3 drops: Timor-Leste (`TLS`) in 2006/10
(~0% value); FAOSTAT column code `276` in 2019–21 (~1.00% of total value). Code
276 is **absent** from `country_conversion_table.csv` (Sudan=206, South
Sudan=277). `rescale_to_total` preserves structure (correlation 1.0).

Caveat: E0 row indices in the vendored files are already ISO3 codes, not
country names as the module docstring (L19) states. `_to_iso3` therefore
depends on ISO3 ∈ `valid_iso3` from the conversion table; any ISO3 present in
E0 but missing from the table is dropped (TLS case), even though the label is
already ISO3.

**Classification:** H for sum preservation and small drop fractions; G for
docstring keying description; C/B minor for ISO3-already-valid blind spot.
**Severity:** Low (vendored wheat). **Confidence:** 95–100%.

**Attempt to falsify.** “1% drop of code 276 biases Egypt shares.” Egypt shares
are computed after drop; 276 is an importer column (top sources: Russia,
Romania, …), so exporter ranking among named nodes is essentially unaffected.
TLS exports are 0.

**Falsification result:** No material bias in shipped wheat diagnostics from
drops. Docstring inaccuracy stands.

**Recommended action.** Extend `_to_iso3` to accept any `[A-Z]{3}` label even if
absent from the conversion table; add alias for code 276 once identified
upstream. Docstring: say rows may be names **or** ISO3.

**Complexity-budget:** Tiny. **Changes results:** Negligible for current demo.

---

## FINDING 7 — Node aggregation systematically pools Kazakhstan (and GBR) into RoW; intra-EU inflates EU share

**Finding.** `SHEAF_NODE_MAP` has 16 named nodes; Kazakhstan (`KAZ`) is not
among them. KAZ is **4.6% of world wheat E0** in 2006–07 and **~40% of RoW
exports** that year (15–31% of RoW in other windows). VALIDATION.md Level 2
explicitly lists Kazakhstan among restrictors to predict — but under the current
node map that agent is observationally merged into RestOfWorld, which has
`export=()` in the prototype and never plays the restriction game.

UK (`GBR`) is excluded from `EU_ISO3` (EU-27 list). In 2006–07 / 2010–11 crisis
windows that is anachronistic (UK was in the EU); GBR is ~2% of world E0 those
years, pooled into RoW.

Intra-EU trade sits on the EU→EU diagonal: **50–62% of EU’s row sum** is
internal. Using row sums as “% of world exports” without stripping the diagonal
(as `build_network.py` panel A does) inflates EU’s apparent world export share
(~28–32%) vs international-only share (~20% in 2019–21 after zeroing diagonals).

**Classification:** F / E for Kazakhstan omission relative to Level-2 design; G
for export-share plot not excluding intra-node trade; D for EU-27 choice if
disclosed. **Severity:** High for Level-2 “who restricts” claims involving
Kazakhstan; Medium for network descriptive plots. **Confidence:** 95–100%.

**Evidence.** Independent reproduction of Egypt sources matches VALIDATION.md
and Agent 7: Russia **37.3% → 45.7% → 52.4%** across 2006–07 / 2010–11 / 2019–21
(H, 95–100% — confirmed).

**Attempt to falsify.** “RoW can carry Kazakhstan’s restrictions via a RoW
export role.” Prototype sets `export=()` on RoW; even if enabled, RoW conflates
KAZ with many other countries — Level-2 country identity is unidentified.

**Falsification result:** Kazakhstan cannot be a Level-2 scoring target under
the current node set.

**Recommended action.** Add KAZ (and optionally GBR-as-EU for pre-Brexit
windows) to `SHEAF_NODE_MAP` / prototype DATA before Level-2 claims. Strip
diagonal (or report extra-EU only) in exporter-share figures. Existing FAOSTAT
data suffice — no new collection.

**Complexity-budget:** Small (one node + calibration row). **Changes results:**
Yes for Level-2 identity scoring; Egypt diagnostic unchanged.

---

## FINDING 8 — Trade network never enters the spatial-equilibrium cost matrix

**Finding.** FAOSTAT E0 is used only for diagnostic plots. The model’s
`transport` matrix is pure haversine geography: `c_ij = 0.0025·d_km + 8`, then
scaled by `FREIGHT_MULT`. Tariffs are identically zero for all countries.
Baseline flows from E0 are never used as starting points, priors, or
constraints. README §7’s claim that the “baseline network (transport structure
c_ij and baseline flows)” comes from FAOSTAT is false of the implementation:
c_ij is geometric; baseline flows are not an input at all (equilibrium flows
are endogenous).

**Classification:** G (README §7); E/D as modeling choice if disclosed (distance
proxy vs trade-cost calibration). **Severity:** Medium for documentation; Low
for prototype intentional simplicity. **Confidence:** 95–100%.

**Attempt to falsify.** “`bilateral_shares` could be fed in later; architecture
allows it.” True as future work; false as a present-tense data claim.

**Falsification result:** Disconnection confirmed.

**Recommended action.** Document c_ij as gravity/distance proxy; if trade costs
are to be calibrated, use existing E0 + USDA totals via `rescale_to_total` /
shares — data already in repo for wheat.

**Complexity-budget:** Docs free; cost calibration is a real project but uses
existing data. **Changes results:** Only if costs are recalibrated.

---

## FINDING 9 — Prototype country×grain quantities are internally consistent; exporter ranking only loosely matches FAOSTAT

**Finding.** Within the prototype: (i) GLOBAL_PROD = GLOBAL_CONS; (ii) RoW
residual closes; (iii) every named net export is finite; (iv) structural
importers (D0>Q) include Egypt, China, Mexico, Indonesia, Nigeria, etc., as
intended. Comparing prototype **net** wheat exports to FAOSTAT 2019–21
international export shares: Russia is #1 in both; USA/Canada/Australia/Ukraine/
Argentina appear as major exporters in both; but prototype Russia net (+45 MMT)
is very large vs USA (+15), whereas FAOSTAT international shares are closer
(Russia 18%, USA 15%, Canada 14%). EU prototype net (+10) understates EU’s
international role if intra-EU is excluded from FAOSTAT comparison differently.
This is acceptable under “illustrative,” not as an empirical calibration.

**Classification:** H for internal consistency; P for external realism.
**Severity:** Low under prototype disclaimer. **Confidence:** 90–95%.

**Attempt to falsify.** “Net export ≠ gross export share, so ranking comparison
is invalid.” Partially true — net understates re-export hubs — but Russia vs USA
ordering gap is still large.

**Falsification result:** Internal OK; external only OOM-illustrative.

**Recommended action.** Replace with per-country USDA PSD when available
(already identified; do not invent a new source).

---

## FINDING 10 — Parameters that cannot be identified from the two crisis episodes (calibration view)

Focus: parameters **other than** the policy pair (w, p̄) that Agent 7 analysed
in depth. Overlap noted where relevant.

| Parameter group | Identifiable from 2007/08 + 2010/11 as proposed? | Why |
|---|---|---|
| Own-price ε_g | Weakly / not uniquely | Annual price+quantity points are few; linear demand underdetermined; no cited micro estimates wired in |
| ρ / subst_scale | Partially (bonus rice test) | Only if rice policy held fixed (Agent 7); cross-grain price comovement is one noisy signal |
| Transport c_ij, FREIGHT_MULT | No | No freight / CIF-FOB targets in remaining inputs; distance is imposed |
| Tariffs | N/A | Fixed at 0; not in estimation set |
| mkt_gamma, mkt_cost | Very weakly | Storage anomalies are Level-1 targets but SUR path is one series per grain; many γ’s |
| gov release/build fracs, triggers | Weakly | Same; China/India/Egypt gov stocks not separately observed in world PSD |
| τ_max, grid | Not economic IDs | Numerical bounds (Agent 2 remit) |
| fs_weight, p_target | Set-identified at best | Agent 7 Findings 1–4 — adopt as hypothesis independently checked only for “not calibrated in repo” (CONFIRMED) |
| Who-restricts with world ξ only | No | Cross-section of shocks is flat (Agent 7 F5) — CONFIRMED structurally: world anomaly applies uniformly |

**Classification:** F. **Severity:** High for any claim of unique empirical
calibration from two episodes alone. **Confidence:** 85–95% (structural
arguments + data inventory; not a full information-matrix calculation).

**Recommended action.** Keep ε, ρ as literature-sourced with citations (or
sensitivity bands); fit only a pooled policy layer (Agent 7’s pooling
suggestion is compatible); use per-country PSD before claiming restrictor
identity. Do **not** recommend new exotic datasets — USDA per-country PSD,
AMIS, and single-year FAOSTAT (upstream) already listed in VALIDATION.md suffice.

**Complexity-budget:** Favourable if pooling reduces free parameters.
**Changes results:** Yes for how calibration is reported.

---

## FINDING 11 — USDA world accounting residual is nonzero (data property, not a SHEAF bug)

**Finding.** For world PSD columns used here,
`beginning_stocks + production − consumption − ending_stocks` is not identically
zero (wheat max |resid| ≈ 28 MMT; maize ≈ 36 MMT). This is expected: the four
TY attributes do not encode trade/other disappearance as a closed identity at
world level in this extract. SHEAF’s loader correctly converts kt→MMT and does
not claim a closed four-column identity.

**Classification:** H (loader); E/F only if someone treated the four columns as
a closed world balance without trade. **Severity:** Low. **Confidence:** 90–95%.

**Recommended action.** None for the adapter. When building per-country
balances, use full PSD supply-utilization including trade.

---

## FINDING 12 — Units are consistent within each layer; E0 magnitudes are correctly treated as unit-agnostic

**Finding.** Calibration and USDA paths both use MMT and $/t. E0 matrix sums are
~1e14 (not MMT); module docstring and `rescale_to_total` / `bilateral_shares`
correctly treat magnitudes as unit-agnostic. No evidence of mixing kt with MMT
inside `load_crop_world` (`_KT_TO_MMT = 1e-3` applied uniformly).

**Classification:** H. **Severity:** None. **Confidence:** 95–100%.

**Attempt to falsify.** “Forgetting rescale would blow QP costs.” True if
someone fed raw E0 as tonnage into the model — but nothing currently does.

**Falsification result:** Units OK in implemented paths.

---

## Positive confirmations (category H summary)

| Item | Result | Conf. |
|---|---|---|
| RoW residual closes GLOBAL balance | Exact | 99% |
| LOWESS = statsmodels it=0 | Bit-level agreement | 99% |
| crisis_forcing = 1 + anomaly | Exact | 99% |
| FAOSTAT aggregate sum preserved | Exact | 99% |
| Egypt Russia share path | 37.3→45.7→52.4% | 99% |
| Tariffs all zero; mkt_cost all 8 | Exact | 99% |
| Vendored rice/maize E0 absent | `list_windows` → [] | 99% |
| Adapters unused by demo | Call-graph | 99% |
| Prototype labeled illustrative | calibration docstring + Caveats | 99% |

---

## Phase 1 hypotheses touched (independent verdicts)

| Hypothesis | Verdict |
|---|---|
| S15: storage params illustrative, not from `stock_to_use` | **CONFIRMED** |
| Agent 7: README §7 present-tense overclaim vs missing inputs | **CONFIRMED** (this agent’s Finding 1) |
| Agent 7: Egypt network diagnostic correct | **CONFIRMED** |
| Agent 7: world forcing non-identifying for who-restricts | **CONFIRMED** structurally; not re-run of Agent 7’s SHEAF experiments |
| Agent 7: Level-2 circularity / (w,p̄) set ID | **NOT RE-LITIGATED** — out of remit beyond “not calibrated in repo” |

---

## Recommended priority list (calibration/data only)

1. **Docs:** Align README §7 with Caveats and the actual `calibration.py` source
   of truth (Finding 1, 8).
2. **Node set:** Add Kazakhstan before any Level-2 restrictor-identity claim
   (Finding 7); fix export-share plots to exclude intra-node trade.
3. **Wire or reword:** `stock_to_use` → storage targets vs “diagnostic only”
   (Finding 3).
4. **Replace prototype Q/D0** with per-country USDA PSD for the study window
   (Finding 2, 9) — data source already identified.
5. **ISO3 passthrough** in `_to_iso3` + document E0 keying (Finding 6).
6. **Do not** collect new data types beyond VALIDATION.md’s remaining list.

---

## Complexity-budget rollup

No finding in this report warrants a new model mechanism. Highest scientific
value per unit cost: documentation honesty (Findings 1, 5, 8), adding KAZ to the
node map (Finding 7), and replacing hand Q/D0 with already-identified USDA
per-country PSD. Recalibrating ε/ρ from two crises alone is **not** recommended
(Finding 10).

---

AGENT 6 COMPLETE
