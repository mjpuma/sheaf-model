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
- **Maize only:** `shock_mode="shortfalls_only"` sets
  \(H=\min(H^{\mathrm{PSD}},H^{\mathrm{seas}})\).  
  **Why:** over 2006–11, maize production co-moves with Pink Sheet prices
  (\(\mathrm{corr}(P,p)\approx +0.92\)) — a demand/ethanol regime. Feeding raw
  PSD harvests into a supply-scarcity price law creates the wrong sign.
  Passing only shortfalls is a reduced-form filter, not a claim that
  bumper crops never happen.

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
d_{i,t}=C_{i,t}(p_t/p_0)^{\varepsilon},
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

Path-matched twin: same \(C_{i,t}\), \(\tau\equiv 0\), harvest =
seasonal mean (or realized if `twin_harvest="realized"`). Free stocks
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
| `stu_target` | 0.20 | 0.16 | 0.20 | literature | USDA world STU order ~0.15–0.25 |
| `max_stu` | 0.25 | 0.25 | 0.28 | literature | Peak STU + small buffer |
| `seasonal_buffer_steps` | 2.0 | 2.0 | 3.0 | structural | Hold ~2–3 peak harvest steps |
| \(\lambda\) `rebuild_lambda` | 0.08 | 0.08 | 0.08 | reduced-form | ~12%/month toward lean target |
| \(\eta\) `inv_eta` | 1.00 | 1.00 | 0.95 | reduced-form | Scarcity inverse elasticity |
| \(\rho\) `smooth` | 0.65 | 0.65 | 0.65 | reduced-form | Biweekly price AR smoother |
| \(\omega\) `trade_w` | 0.70 | 0.65 | 0.72 | reduced-form | Asks dominate; maize needs more block channel for AMIS lift |
| \(\kappa_u\) | 2.5 | 3.0 | 2.5 | reduced-form | Unmet-anomaly weight |
| \(\kappa_b\) | 4.0 | 5.5 | 4.5 | reduced-form | Preferred-source blockage (rice/maize bans) |
| \(\alpha,\theta,\gamma,\beta\) | 0.15 / 0.70 / 1.25 / 0.18 | same | same | reduced-form | Ask adaptation (shared) |
| \(\phi\) `foresight_phi` | 0.55 | 0.40 | 0.55 | reduced-form | Maize less weight on realized H (demand regime) |
| `shock_mode` | full | **shortfalls_only** | full | structural choice | See §2.1 |
| `twin_harvest` | seasonal | seasonal | seasonal | structural | Supply-shock identification |

AMIS cut map and FAOSTAT windows are **structural data**, not free parameters.

---

## 4. What is / is not economically defensible

### Defensible

- 24-step clock, calendars, PSD quantities, AMIS quantity cuts, bilateral shares.
- Isoelastic food demand with literature-scale \(\varepsilon\).
- Lean cover until the next harvest pulse (finite foresight, not perfect foresight RE).
- Adaptive exporter asks responding to fill rates (Agrimate-like).
- World price blending trade asks with a twin-relative scarcity residual.
- Maize shortfall filter given the observed \(P\)–\(p\) co-movement.

### Reduced-form (honest limits)

- \(\omega,\eta,\kappa_u,\kappa_b,\lambda,\rho\), ask gains: phenomenological.
- Capacity dump of excess stocks.
- Twin scarcity is a diagnostic device for Level-1 attribution, not a microfounded
  futures market.

### Not claimed

- Full rational-expectations storage equilibrium.
- Endogenous acreage / ethanol demand block (maize Level 1 uses consumption
  paths + shortfall filter instead).
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

## 6. Snapshot scores (post-parameterization)

From `scripts/score_subannual_crop.py` after the 2026-08-24 retune:

| Crop | full corr | 2007/08 full / obs | 2010/11 full / obs | Asserts |
|---|---:|---:|---:|---|
| wheat | **+0.68** | ×1.38 / ×1.82 | ×1.08 / ×1.16 | PASS |
| maize | **+0.36** | ×1.97 / ×1.84 | ×1.06 / ×1.44 | PASS |
| rice | **+0.80** | ×2.21 / ×1.84 | ×0.85 / ×0.79 | PASS |

Maize remains the hardest Level-1 case without an explicit demand block;
`shortfalls_only` + blockage-weighted price is the documented compromise.
