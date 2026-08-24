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

### 2.3 Capacity (structural fix; was previously indefensible)

Warehouse (carry capacity) is
\[
W_i=\max(\mathtt{max\_stu}\,C_i^{\mathrm{ann}},\,1.5 s_i)
+\mathtt{seasonal\_buffer\_steps}\cdot\max_t H_{i,t}.
\]

**Why:** the old \(W_i=4\,C_i^{\mathrm{ann}}\) allowed multi-year stock
gluts (model stocks \(2\)–\(4\times\) PSD) and killed scarcity signals. The
new form matches observed STU order for the floor and adds a **seasonal
intake buffer** so harvest pulses are not destroyed at the peak month.
Excess above \(W_i\) is dropped (capacity / unmodelled residual use) —
a modeling simplification, not physical spoilage science.

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
**zero industrial excess**, \(\tau\equiv 0\). Free stocks
\(\mathrm{free}_t=\sum S_{i,t+1}-\sum L_{i,t}\).

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
\(\eta_{\mathrm{eff}}=\eta\) if \(r\ge 1\) else \(0.2\eta\) (asymmetric
abundance — convenience-yield style muted response).

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
| `stu_target` | 0.20 | 0.18 | 0.20 | literature | USDA world STU order ~0.15–0.25 |
| `max_stu` | 0.25 | 0.25 | 0.28 | literature | Peak STU + small buffer |
| `seasonal_buffer_steps` | 2.0 | 3.5 | 3.0 | structural | Maize harvest more peaked |
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

## 6. Snapshot scores (post demand/ethanol block)

From `scripts/score_subannual_crop.py` after the industrial-demand block:

| Crop | full corr | demand corr | 2007/08 full / obs | 2010/11 full / obs | Asserts |
|---|---:|---:|---:|---:|---|
| wheat | **+0.74** | −0.04 | ×1.36 / ×1.82 | ×1.22 / ×1.16 | PASS |
| maize | **+0.58** | **+0.46** | ×1.80 / ×1.84 | ×1.17 / ×1.44 | PASS (tau price skip) |
| rice | **+0.81** | +0.29 | ×2.05 / ×1.84 | ×0.85 / ×0.79 | PASS |

Attribution matches the economics: wheat 2010 restriction-sensitive; maize
2007/08 demand+harvest; rice 2008 restriction-led (`tau` corr +0.78).
