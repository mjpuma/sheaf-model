# Gate 0 parameterization — equations, sources, and defensibility

**Status:** locked with `sheaf/dynamic_crop.py` (`CropParams` / `default_crop_params`)  
**Score entry point:** `python scripts/score_subannual_crop.py --crop {wheat,maize,rice}`  
**White paper (Overleaf):** `overleaf/gate0_whitepaper/` — substitution off, strategy off; 2006–11 plus Ukraine-war 2021–23.

This note states (1) what every equation is, (2) how each parameter is set,
and (3) what is structural vs literature vs reduced-form. It is the companion
to README §8.

---

## 1. Classification of ingredients

| Class | Meaning | May we “fit” it to crisis prices? |
|---|---|---|
| **Structural** | Accounting identity, data definition, or Agrimate lineage choice | No — only change with a modeling redesign |
| **Literature** | Taken from published elasticities / STU norms / Agrimate policy map | Only within published ranges |
| **Reduced-form** | Sign-constrained phenomenological weight linking a measured tightness to price | Shared across crops unless a documented crop reason exists; **not** fit crisis-by-crisis |

We do **not** claim a full Deaton–Laroque competitive-storage equilibrium or a
full Agrimate agent microfoundation every step. We claim an Agrimate-*aligned*
stock–trade–ask system whose pieces are economically interpretable.

---

## 2. Equations (what the code actually does)

### 2.1 Clock and harvest (structural)

- \(T_y=24\) steps/year (Agrimate §4.1).
- Annual USDA PSD production for country \(i\) is spread with triangular
  calendar weights (`sheaf/seasonal.py`).
- **Climatology (twin)** is the score-window *mean* seasonal path.
- **Treatment harvest** is that climatology times a per-country LOWESS
  multiplier \(1+a_{i,y}\), \(a_{i,y}=(Y_{i,y}-\hat Y_{i,y})/\hat Y_{i,y}\)
  on a padded PSD history (`detrend_anomalies`, Agrimate's method). Raw year
  totals are **not** used as levels: 2008–11 trend growth inflated the
  in-sample mean, so 2006 wheat looked like −9% vs the mean and only −4% vs
  trend. `shock_mode=full` keeps surpluses (maize 2008 is not identified by
  discarding bumper years).

### 2.1b Demand block: flex vs industrial (structural)

PSD domestic use is split:

\[
C_{i,y}=C^{\mathrm{flex}}_{i,y}+C^{\mathrm{ind}}_{i,y}.
\]

- **Flex** (food + feed): faces isoelastic price response \(\varepsilon\).
- **Industrial / ethanol**: price-**inelastic** in the short run (mandate).

**Identification (parsimonious, not a WASDE ethanol series):**
USDA international PSD reports Feed and FSI, not gallons of ethanol.
For nodes in `industrial_nodes` (default: **USA maize only**),

\[
C^{\mathrm{ind}}_{i,y}=\min\Bigl(C_{i,y},\;
\max\bigl(0,\;\mathrm{FSI}_{i,y}-\overline{\mathrm{FSI}}_{i,2000\text{–}04}\bigr)\Bigr).
\]

That residual is the RFS-era FSI surge (US maize FSI 77 MMT in 2005 → 163 MMT
in 2010; feed actually *fell*). Wheat FSI is flat in this window; rice has no
FSI attribute — both have \(C^{\mathrm{ind}}=0\). We do **not** treat China’s
FSI trend as ethanol.

**Twin demand** (no-mandate climatology): mean flex over the score window,
\(C^{\mathrm{ind}}=0\) (`use_industrial=False`). Official P1 **matched**
treatment uses **mean flex** plus industrial on
(`use_demand=False`, `use_industrial=True` for USA maize). Year-by-year world
food/feed is a sensitivity (`use_demand=True`), not the headline series.
`use_demand` no longer zeroes industrial.

Within-step desired use:

\[
d_{i,t}=C^{\mathrm{flex}}_{i,t}\,(p_t/p_0)^{\varepsilon}+C^{\mathrm{ind}}_{i,t}.
\]

Isolated score legs: `shocks` (harvest + industrial on), `demand` (year-by-year
flex+industrial, no harvest/AMIS), `tau` (AMIS only, industrial off), `full`
(official P1: harvest + AMIS + mean flex + industrial on).

### 2.2 Lean foresight and stock targets (structural + reduced-form speed)

\[
H^{\mathrm{exp}}=\phi H+(1-\phi)H^{\mathrm{seas}},
\quad
L_{i,t}=\max\bigl(0,\,C^{\mathrm{ahead}}+C_t-H^{\mathrm{ahead}}-H^{\mathrm{exp}}_t\bigr),
\quad
T_{i,t}=L_{i,t}+s_i,
\]
with safety \(s_i=\mathtt{stu\_target}\cdot C_i^{\mathrm{ann}}\).

Purchase demand and offers:
\[
d_{i,t}=C^{\mathrm{flex}}_{i,t}(p_t/p_0)^{\varepsilon}+C^{\mathrm{ind}}_{i,t},
\quad
D_{i,t}=\underbrace{\max(0,d-\mathrm{avail})}_{\text{food gap}}
+\lambda\max(0,T-\text{post-food stock}),
\]
\[
O_{i,t}=\max(0,\mathrm{avail}-d-T)\,(1-\tau_{i,t}).
\]

- \(\varepsilon\): **literature** short-run demand elasticity.
- \(\lambda\): **reduced-form** partial-adjustment speed toward the lean target
  (not a full Euler equation).
- \(\tau\): **structural map** from AMIS policy labels → quantity cuts
  (Agrimate-style: ban \(\approx 0.95\), tax \(\approx 0.50\), …).

### 2.3 Capacity (structural: carry + harvest-pipeline)

Warehouse at step \(t\) is
\[
W_{i,t}=\max(\mathtt{max\_stu}\,C_i^{\mathrm{ann}},\,1.5 s_i)
+\mathtt{pipeline\_max\_steps}\cdot C_i^{\mathrm{ann}}/24
+H_{i,t}.
\]
The working-stock term is a **constant** cap (not shrunk as the next harvest
approaches — that dumped grain into the lean month). `pipeline_max_steps=12`
is 6 months of use (wheat/maize, one main pulse); rice uses 0 (multi-crop /
year-round harvest, no extra working buffer). Same-step \(H_{i,t}\) pads \(W\)
only when `pipeline_max_steps>0` (pulse intake). Rice clips toward carry:
padding \(W\) with every monsoon step stored harvest as if it were silos.
`seasonal_buffer_steps` is unused. Excess above \(W_{i,t}\) is **soft-clipped**
with `warehouse_lambda` (defaults to rebuild \(\lambda\)). Capacity ceiling is
\(\mathtt{max\_stu}\,C\) (not \(1.5s\), which accidentally sat above `max_stu`).

### 2.4 Bilateral clear and asks (Agrimate-aligned)

- FAOSTAT E0 → destination shares \(A\) and source shares \(S\) (structural network).
- Ask-reweight \(\tilde A_{ij}\propto A_{ij}(p_0/q_i)^{\gamma}\); Armington min clear
  plus residual pool share \(\nu\).
- FAOSTAT rice E0 in the 2006–07 / 2010–11 crisis files has a **zero Vietnam
  row** (data hole). `load_trade_shares` fills destination mix from 2019–21
  and scales the row to 12% of crisis-window export total (Vietnam's observed
  world-rice-export share). This is a **data repair**, not a 2008 price knob.
- Ask update (reduced-form offer-price adaptation). Survivors also mark up
  when preferred sources are blocked (Agrimate oligopolist channel),
  \(\alpha_r\ge 0\); \(\alpha_r=0\) recovers the own-fill law:
  \[
  q\leftarrow (1-\beta)\,q\exp\bigl(\alpha(\mathrm{fill}-\theta)
  +\alpha_r b\cdot\mathbf{1}_{O>0}\bigr)+\beta p,
  \]
  clipped to \([0.45p_0,\,2.8p_0]\). \(b\) is the preferred-source block
  fraction. Twin identity: \(b=0\) ⇒ own-fill law.

### 2.5 World price (ask-dominated + twin scarcity residual)

Path-matched twin: **seasonal-mean harvest**, **mean flex demand**,
**zero industrial excess**, \(\tau\equiv 0\). Free stocks are
**world-accessible**:
\(\mathrm{free}_t=\sum S_{i,t+1}-\sum L_{i,t}-\sum\tau_{i,t}\max(0,S_{i,t+1}-T_{i,t})\).
Grain withheld by an export cut does not count as market free (otherwise a
ban looks like abundance once \(\eta\) is symmetric).

If the treatment matches the twin on free, unmet anomaly, and preferred-source
blockage (**calm**), \(p^\star=p_0\) (identity). Otherwise
\[
p^{\mathrm{scar}}=p_0\,r^{\eta_{\mathrm{eff}}}(1+\kappa_u\Delta u+\kappa_b b),
\quad
p^\star=\omega\,p^{\mathrm{tr}}+(1-\omega)\,p^{\mathrm{scar}},
\quad
p\leftarrow \rho p+(1-\rho)p^\star,
\]
with \(r=(\mathrm{free}^{\mathrm{twin}}+f)/(\mathrm{free}+f)\),
\(\eta_{\mathrm{eff}}=\eta\) always (symmetric surplus/shortage). Muting
abundance had stored gluts: flex demand never cheapened enough to eat them.

- \(\omega\): **reduced-form** weight on trade-weighted asks (market outcome).
- \(\eta,\kappa_u,\kappa_b\): **reduced-form**, sign-constrained multipliers on
  measured tightness. They are **not** structural elasticities from a
  derived FOC; they are declared as such.

---

## 3. Default parameter table

From `default_crop_params()`:

| Parameter | Wheat | Maize | Rice | Class | Rationale |
|---|---:|---:|---:|---|---|
| \(\varepsilon\) `elast` | −0.15 | −0.25 | −0.20 | literature | Short-run food/feed demand; maize more elastic (feed) |
| `stu_target` | 0.20 | 0.16 | 0.18 | literature | USDA world STU order ~0.15–0.25 |
| `max_stu` | 0.28 | 0.18 | 0.22 | literature | Carry ceiling ≈ PSD STU |
| `pipeline_max_steps` | 12 | 12 | 0 | structural | 6 mo working stocks wheat/maize; rice year-round harvest |
| `seasonal_buffer_steps` | 0 | 0 | 0 | unused | Replaced by harvest-pipeline |
| \(\lambda\) `rebuild_lambda` | 0.08 | 0.08 | 0.08 | reduced-form | ~12%/month toward lean target |
| `warehouse_lambda` | 0.08 | 0.08 | 0.08 | reduced-form | Soft drain of overflow; defaults to rebuild \(\lambda\) |
| \(\eta\) `inv_eta` | 1.00 | 0.85 | 0.95 | reduced-form | Scarcity inverse elasticity |
| \(\rho\) `smooth` | 0.65 | 0.65 | 0.65 | reduced-form | Biweekly price AR smoother |
| \(\omega\) `trade_w` | 0.70 | 0.80 | 0.72 | reduced-form | Asks dominate; scarcity residual |
| \(\kappa_u\) | 2.5 | 2.5 | 2.5 | reduced-form | Unmet-anomaly weight |
| \(\kappa_b\) | 4.0 | 4.0 | 4.5 | reduced-form | Preferred-source blockage |
| \(\alpha,\theta,\gamma,\beta\) | 0.15 / 0.70 / 1.25 / 0.18 | same | same | reduced-form | Ask adaptation (shared) |
| \(\alpha_r\) `ask_rival` | 0.80 | 0.80 | 0.80 | reduced-form | Survivor markup when preferred sources blocked; ≥ 0. Set by isolated-τ non-cut (maize), not 2008 peaks |
| \(\phi\) `foresight_phi` | 0.55 | 0.50 | 0.55 | reduced-form | Blend realized vs seasonal harvest |
| `shock_mode` | full | full | full | structural | Signed LOWESS anomalies on climatology; not raw PSD levels |
| `industrial_nodes` | — | **USA** | — | structural | RFS ethanol residual |
| `ind_base_years` | 2000–04 | 2000–04 | 2000–04 | structural | Pre-Energy Policy Act / pre-RFS FSI |
| `twin_harvest` | seasonal | seasonal | seasonal | structural | Supply-shock identification |

AMIS cut map and FAOSTAT windows are **structural data**, not free parameters.

---

## 4. What is / is not economically defensible

### Defensible

- 24-step clock, calendars, PSD quantities, AMIS quantity cuts, bilateral shares.
- Isoelastic **flex** demand with literature-scale \(\varepsilon\); industrial
  use inelastic (mandate, not a consumer FOC).
- Lean cover until the next harvest pulse (finite foresight, not perfect foresight RE).
- Adaptive exporter asks responding to fill rates (Agrimate-like).
- World price blending trade asks with a twin-relative scarcity residual.
- US maize FSI excess vs 2000–04 as the ethanol/RFS residual (PSD, not gallons).

### Reduced-form (honest limits)

- \(\omega,\eta,\kappa_u,\kappa_b,\lambda,\rho\), ask gains: phenomenological.
- Capacity dump of excess stocks.
- Twin scarcity is a diagnostic device for Level-1 attribution, not a microfounded
  futures market.

### Not claimed

- Full rational-expectations storage equilibrium.
- Endogenous acreage response or a WASDE-style ethanol *gallon* series
  (FSI residual is the PSD-consistent proxy).
- Cross-grain substitution (paused until per-crop Gate 0 is green).
- Level-2 endogenous export game.

---

## 5. How to change a parameter

1. Edit only via `CropParams` / `default_crop_params` (or pass `params=` /
   field overrides into `run_crop_dynamics`).
2. Re-run `scripts/score_subannual_crop.py --crop …` and keep asserts green.
3. Update **this file’s table** in the same commit — undocumented knobs are
   treated as bugs.
4. Do not introduce crisis-specific constants (e.g. “boost \(\kappa_b\) only in
   2010”) without a new structural story.

---

## 6. Snapshot scores (official P1 matched split)

From `scripts/score_subannual_crop.py` after LOWESS harvest anomalies (not raw
PSD levels), rice multi-crop calendar, carry cap = `max_stu` (no \(1.5s\)
ceiling bump), and rice \(H_t\) not padding \(W\) (`pipeline=0`). Headline
`full` = harvest + AMIS + mean flex (+ USA maize industrial).

| Crop | full corr | 2007/08 full / obs | 2010/11 full / obs | MY-end stocks vs PSD | ex-China MY-end | Asserts |
|---|---:|---:|---:|---:|---:|---|
| wheat | +0.72 | ×2.27 / ×1.82 | ×1.45 / ×1.16 | ×1.02 (May) | ×1.09 (China 28%) | PASS |
| maize | +0.71 | ×1.97 / ×1.84 | ×1.70 / ×1.44 | ×1.08 (Aug) | ×1.49 (China 35%) | PASS (τ must not cut) |
| rice | +0.68 | ×1.72 / ×1.84 | ×0.82 / ×0.79 | ×1.05 (Aug) | ×1.14 (China 44%) | PASS (Vietnam autumn pulse kept) |

Agrimate-matched Overleaf table: `overleaf/gate0_agrimate/tables/price_metrics.tex`
(regen: `python scripts/make_agrimate_comparison.py`).

### Closed vs leftover

**Closed this leftover pass**
- Harvest forcing is climatology × LOWESS anomaly (Agrimate). In-sample 2006–11
  means treated 2008–11 trend growth as a 2006 shortfall (wheat 2006 −9% vs
  mean, −4% vs trend).
- Wheat 2006/07 matched ×1.46 (was ×2.08); still below 2008 ×2.27.
- Maize 2008 matched ×1.97 vs obs ×1.84 (was ×2.72). Isolated τ ×1.10, does not cut.
- Maize 2010/11 matched ×1.70 vs obs ×1.44 (was ×0.99). Identified without a
  2011 dummy.
- Rice 2010 matched ×0.82 vs obs ×0.79.
- Rice **world** MY-end is August, not calendar December (×1.05 vs PSD,
  was ×1.63 at Dec). Country stocks scored at USDA local MY-end months
  (`sheaf/marketing_years.py`), not 28-region groupings.

**Leftover (structural, not hidden knobs)**
- **Wheat 2007/08 still high** (×2.27 vs ×1.82). Restriction-led (tau×1.70 >
  harvest×1.20). Not damped with a 2008 dummy.
- **Wheat 2010 hike ratio is production-led** (`shocks`×1.85 > `tau`×1.36).
  Detrending *strengthens* 2010 harvest (Russia drought). The 2009-06→2011-02
  ratio also lifts 2009 via lingering AMIS, so restriction looks weaker on the
  ratio than in levels. No 2010-only knob.
- **Wheat 2006/07** still ×1.46 vs obs ~×0.95 (harvest-only ×1.39). Residual
  of 2006 tightness vs trend, not incineration.
- **Maize 2010/11 a bit high** (×1.70 vs ×1.44). Harvest-only ×1.01.
- **Country stock *levels*:** world MY-end matches; many exporter nodes sit
  on the global safety floor (USA/Canada/Australia wheat ~×0.2). Offer floor
  is `lean + stu_target` with one world STU, so commercial carry is sold down.
  A country-specific price-responsive hold was tried and rejected: it helped
  USA wheat but fattened China maize ~×3. Δstock signs remain ~coin-flip
  (wheat 35/83, maize 42/80, rice 36/64).
- **World excluding China** is the FAO/AMIS tightness series (China 28% of
  PSD wheat stocks, 35% maize, 44% rice). Same crop MY-end month as the world
  bar; China stays a named node. Wheat ×1.09 and rice ×1.14 (ex-China+India
  ×1.17) sit next to the including-China bar. Maize ×1.49 is leftover: the
  world bar is August and China maize USDA MY-end is September, so the
  snapshot under-subtracts China, and local-MY China is separately fat (~×2.8).
  Not a warehouse retune.
- **World consumption vs country-sum PSD** (P1 expansion, not Agrimate Fig. 4):
  wheat ×0.92 corr −0.17 Δcons 3/5; maize ×0.92 corr −0.64 Δcons 2/5;
  rice ×0.86 corr −0.74 Δcons 1/5. Median country-year ratio hides a falling
  model path vs rising PSD. Official split is mean flex + isoelastic
  (\(\varepsilon<0\)); 2006 wheat is ×1.00. Year-by-year food/feed is the
  sensitivity. No warehouse retune. Score from the country table, not
  `load_crop_world` (omits the EU).
- **Vietnam rice** MY-end stocks ~×6 vs PSD already in **2006** (before AMIS).
  Do not attribute that fat to the 2008 ban. India is the AMIS lock on stocks.
- **AMIS shipment signs (P1, not Agrimate observed trade):** τ cuts
  **offers**; cleared shipments are demand-constrained. Wheat Russia
  Aug–Dec 2010 offers ×0.11, ships ×0.79 vs harvest-only; calendar 2010
  still ×2.4 vs PSD. Maize Argentina May 2007 offers ×0.30, ships ×0.99.
  Rice assert window is a 2008 tax; Oct–Dec 2007 ban+harvest signs are
  right. Isolated-τ price bar for maize stands. No warehouse retune.

Substitution and Level 2 stay blocked.

