# Annual SPE prototype (parked)

This is **not** the 2007/08 crisis host. Crisis work uses the 24-step map in
`sheaf/dynamic_crop.py` (README §8).

The annual spatial price equilibrium plus year-level Nash lives here so it
can be pulled in later as a **slow outer loop** (types, yearly diagnostic)
without sitting on `from sheaf import SheafModel`.

```python
from sheaf.annual import SheafModel, build_countries

countries, transport, grains, freight = build_countries(substitution=True)
model = SheafModel(countries, transport, grains, freight_mult=freight)
df = model.run(periods=12, shocks={5: shock_matrix})
```

```bash
python scripts/annual/demo.py
python scripts/annual/score_level1.py   # annual Level-1 path, not Gate 0
```

Tag `annual-spe-in-tree` is the mixed tree before this park. Restore a file
with `git checkout annual-spe-in-tree -- sheaf/core.py` only if you need the
old layout; prefer importing `sheaf.annual`.

AMIS on this host is a **$/t wedge** (`data_usda.amis_tau_schedule`). Gate 0
uses an offer-cut fraction (`dynamic_crop.amis_export_cuts`). Same diary,
two maps.

Node names, `GRAINS`, `RHO`, and `P0` stay in `sheaf/calibration.py` (the
crisis host uses them). `build_countries()` builds the annual `Country`
objects and stays callable as `sheaf.annual.build_countries`.

---

## Mathematical formulation (annual SPE)

Clock: one step per year. Quantities in million tonnes (MMT); prices in $/t.
Implementation: `sheaf/annual/core.py`. τ here is a $/t tax, not an offer
fraction.

### Notation

| Symbol | Meaning |
|---|---|
| $i,j \in \{1,\dots,n\}$ | countries (network nodes) |
| $g,h \in \{1,\dots,G\}$ | grains (wheat, rice, maize) |
| $D_i \in \mathbb{R}^{G}_{\ge 0}$ | consumption vector of country $i$ |
| $a_i \in \mathbb{R}^{G}$ | demand intercept (choke consumption) |
| $p_i \in \mathbb{R}^{G}$ | domestic price vector of country $i$ |
| $f^g_{ij} \ge 0$ | bilateral flow of grain $g$ from $i$ to $j$ |
| $Q^g_i$ | baseline production; $\xi^g_i$ production-shock multiplier |
| $A^g_i$ | available supply after storage |
| $M_i \in \mathbb{R}^{G\times G}$ | country $i$ demand-slope matrix (symmetric PD) |
| $D_{0},\ p_{0}$ | baseline consumption and reference prices |
| $\tau^g_i \ge 0$ | export-tax-equivalent (restriction); $m^g_j$ import tariff |
| $c_{ij},\ \phi_g,\ \psi_{ij}$ | transport cost, grain freight factor, route multiplier |
| $R^g_i,\ \bar R^g_i$ | reserve (stock) level and storage capacity |
| $r,\ t$ | discount rate; time-period index |

### 1. Demand system

$$D_i = a_i - M_i\, p_i, \qquad p_i = M_i^{-1}(a_i - D_i),$$

with $M_i$ symmetric positive-definite. Consumer-benefit potential

$$W_i(D_i) = (M_i^{-1} a_i)^\top D_i - \tfrac12\, D_i^\top M_i^{-1} D_i,
\qquad \nabla_{D_i} W_i = p_i,$$

$$CS_i(D_i) = W_i(D_i) - p_i^\top D_i.$$

Construction: $b_g = -\varepsilon_g D_{0,g}/p_{0,g}$,
$S_{gh}=\sigma\rho_{gh}\sqrt{b_g b_h}$ ($g\neq h$), row-cap, geometric-mean
symmetrise, $M=\mathrm{diag}(b)-S$, $a=D_0+M p_0$. Own elasticities here
are `calibration.OWN_ELAST`, not Gate 0 `CropParams.elast`.

### 2. Market QP

$$\max_{D\ge 0,\ f\ge 0}\ \ \sum_{i} W_i(D_i)\;-\;\sum_{g,i,j} K^g_{ij}\, f^g_{ij}$$

$$A^g_i + \sum_{k} f^g_{ki} - \sum_{k} f^g_{ik} - D^g_i = 0, \qquad f^g_{ii}=0,$$

$$K^g_{ij} = c_{ij}\,\phi_g\,\psi_{ij} + \tau^g_i + m^g_j.$$

KKT: $p^g_j-p^g_i\le K^g_{ij}$ with complementary slackness on flows.
Solver fallback CLARABEL → SCS → OSQP; status must be optimal.

### 3. Storage

Availability $A = Q\xi - \Delta^{\mathrm{mkt}} - \Delta^{\mathrm{gov}}$.
Private storage uses **last year's** realised price (disclosed lag), not
rational-expectations competitive storage. Government buffer: release in
crisis, rebuild in calm. Not the Gate 2 Headey rule.

### 4. Annual export-restriction game

$$\mathcal{W}_i = CS_i + p_i\cdot Q - \sum_g w_{i,g}(p_{i,g}-\bar p_{i,g})_+^2 + \zeta \tau_i\cdot X_i.$$

Nash by iterated best response on a $/t$ grid. Approximate / discretised
because $\mathcal{W}$ is non-concave. Stress gate: game plays only if
$\max p > \mu p^{\mathrm{norm}}$. Producer income uses unshocked $Q$.

### 5. Yearly orchestrator

Each year: expectations → storage → stress gate → market/game → reserve
update. This clock is **not** used for crisis hindcasts.

### 6. Zero-substitution limit

If $\sigma=0$, $M_i=\mathrm{diag}(b)$ and the QP splits into $G$ independent
SPEs. Live-host analogue: Gate 1 $\sigma=0$ identity on the 24-step spine.

`scripts/annual/demo.py` measures substitution spillover on **this** host
(Black Sea wheat shock). It is not a 2007/08 hindcast.
