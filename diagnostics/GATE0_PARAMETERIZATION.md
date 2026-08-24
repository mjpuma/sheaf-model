# Gate 0 parameterization — equations, sources, and defensibility

**Status:** locked with `sheaf/dynamic_crop.py` (`CropParams` / `default_crop_params`)  
**Score entry point:** `python scripts/score_subannual_crop.py --crop {wheat,maize,rice}`

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
- Annual USDA PSD production for country \(i\), year \(y\) is spread with
  triangular calendar weights (`sheaf/seasonal.py`).
- Harvest forcing is **full** year-by-year PSD (no shortfall filter).
  Demand-driven maize is identified by the industrial block below, not by
  discarding bumper harvests.

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
\(C^{\mathrm{ind}}=0\). Treatment uses year-by-year flex + industrial.
This is the identification that was missing: the old twin held *realized*
consumption fixed, so ethanol never appeared as scarcity.

Within-step desired use:

\[
d_{i,t}=C^{\mathrm{flex}}_{i,t}\,(p_t/p_0)^{\varepsilon}+C^{\mathrm{ind}}_{i,t}.
\]

Isolated score legs: `shocks` (harvest only), `demand` (flex+industrial only),
`tau` (AMIS only), `full` (all three).

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
is 6 months of use (wheat/maize, one main pulse); rice uses 0 (year-round
tropical harvest, no extra working buffer). `seasonal_buffer_steps` is unused
(peak-harvest multiples stored gluts as if they were carry). Excess above
\(W_{i,t}\) is dropped.

### 2.4 Bilateral clear and asks (Agrimate-aligned)

- FAOSTAT E0 → destination shares \(A\) and source shares \(S\) (structural network).
- Ask-reweight \(\tilde A_{ij}\propto A_{ij}(p_0/q_i)^{\gamma}\); Armington min clear
  plus residual pool share \(\nu\).
- Ask update (reduced-form offer-price adaptation):
  \[
  q\leftarrow (1-\beta)\,q\exp\bigl(\alpha(\mathrm{fill}-\theta)\bigr)+\beta p,
  \]
  clipped to \([0.45p_0,\,2.8p_0]\).

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
| \(\eta\) `inv_eta` | 1.00 | 0.85 | 0.95 | reduced-form | Scarcity inverse elasticity |
| \(\rho\) `smooth` | 0.65 | 0.65 | 0.65 | reduced-form | Biweekly price AR smoother |
| \(\omega\) `trade_w` | 0.70 | 0.80 | 0.72 | reduced-form | Asks dominate; scarcity residual |
| \(\kappa_u\) | 2.5 | 2.5 | 2.5 | reduced-form | Unmet-anomaly weight |
| \(\kappa_b\) | 4.0 | 4.0 | 4.5 | reduced-form | Preferred-source blockage |
| \(\alpha,\theta,\gamma,\beta\) | 0.15 / 0.70 / 1.25 / 0.18 | same | same | reduced-form | Ask adaptation (shared) |
| \(\phi\) `foresight_phi` | 0.55 | 0.50 | 0.55 | reduced-form | Blend realized vs seasonal harvest |
| `shock_mode` | full | full | full | structural | Year-by-year PSD harvest |
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

## 6. Snapshot scores (post stock-identity pass)

From `scripts/score_subannual_crop.py` after carry+pipeline warehouse,
symmetric \(\eta\), and accessible free stocks:

| Crop | full corr | 2007/08 full / obs | 2010/11 full / obs | MY-end stocks vs PSD | Asserts |
|---|---:|---:|---:|---:|---|
| wheat | +0.49 | ×1.44 / ×1.82 | ×1.04 / ×1.16 | ×0.72 (May) | PASS |
| maize | +0.45 | ×1.75 / ×1.84 | ×1.81 / ×1.44 | ×0.52 (Aug) | PASS (tau price skip) |
| rice | +0.37 | ×1.58 / ×1.84 | ×1.90 / ×0.79 | ×1.10 (Dec) | PASS |

Wheat 2007/08 hike moved toward obs (was ×1.36). Attribution labels are
`production` / `demand` / `restriction` (ethanol only exists as maize
industrial use, not as a wheat/rice label).

### Closed vs leftover

**Closed**
- Peak-harvest warehouse multiples that stored gluts as carry (maize was ~5×
  PSD on calendar Dec, which is post-harvest not MY-end).
- Abundance mute \(0.2\eta\) that prevented flex demand from eating surplus.
- Export-ban grain counted as world-free (ban looked like abundance).
- Wheat 2010 hike labeled “demand/ethanol”.
- Rice Dec STU now ×1.10 vs PSD (was ~3×). Wheat May STU ×0.72 (order-of-magnitude OK).

**Leftover (structural, not hidden knobs)**
- **Calendar Dec ≠ PSD marketing-year end.** Maize Dec is still ~3.7× Aug PSD
  because Dec is post-harvest peak; comparable month is Aug (×0.52, thin).
- **No convenience-yield / futures smoothing:** model May wheat prices spike
  vs a nearly flat Pink Sheet seasonality → monthly corr fell (0.74 → 0.49).
- **Wheat 2010 isolated restriction** does not carry the hike (`tau`×0.87);
  isolated demand with growing C and tight stocks does. Full-path 2010 hike
  ratio is OK (×1.04 vs ×1.16) but the attribution is not restriction-led.
- **Isolated maize \(\tau\)** can cut the trade-weighted ask (other exporters
  fill; ask-composition). Offer-cut assert binds; world-price lift is skipped.
- **Rice 2010** model hike ×1.90 vs obs ×0.79 (false tightness). Demand twin
  with year-by-year C and a tight cap over-states scarcity after 2008.
- **2007 stock-draw sign** (wheat MY-end rose; PSD fell) — not closed.

Substitution and Level 2 stay blocked.
