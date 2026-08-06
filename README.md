# GRIST

**Grain Restriction, Interdependence & Strategic Trade** — a country-level,
multi-commodity, game-theoretic network model of global grain trade.

GRIST couples three things that existing network trade models (e.g. PIK's TWIST,
Agrimate) treat only partially:

1. a **trade network** cleared by spatial price equilibrium,
2. **strategic government behaviour** — exporters play an export-restriction game,
3. **cross-commodity substitution** — wheat, rice, and maize markets are linked on
   the demand side, so a shock to one grain spills into the others.

The third point is the reason GRIST exists. Single-commodity strategic-trade
models wall each grain off from the others, and reviewers rightly object that this
overstates price spikes and misses the substitution margin. In GRIST the
no-substitution case is a *special limit* of the model (set the cross-price terms
to zero), and the gap between that limit and the full model is itself a result.

![wheat shock spills into rice and maize only under substitution](figures/fig1_coupling.png)

*A Black Sea wheat shock, shown as the shock-induced price change (shocked minus a
no-shock counterfactual). Wheat jumps in both regimes. Rice and maize move **only**
when buyers can substitute; with substitution switched off they sit flat at zero —
the decoupled, single-commodity limit.*

## How it works

**Market layer** (`SpatialEquilibrium`). One concave quadratic program clears all
grains jointly:

```
maximise  Σ_i [ (Minv_i a_i)·D_i − ½ D_i' Minv_i D_i ]   (consumer benefit)
          − Σ_g Σ_ij K^g_ij f^g_ij                        (transport + policy cost)
s.t.      A^g_i + imports^g_i − exports^g_i − D^g_i = 0   (balance, per grain)
          f ≥ 0, D ≥ 0, no self-trade.
```

Each country carries a linear demand system `D_i = a_i − M_i p_i` with `M_i`
symmetric positive-definite. Symmetry is Slutsky symmetry — it is exactly what
keeps the net-social-payoff objective integrable and the QP concave, so the model
stays fast and globally solvable even with substitution on. Off-diagonal terms of
`M_i` are negative for substitute grains; zero them and the problem separates into
independent single-commodity markets.

**Strategic layer** (`ExportRestrictionGame`). Exporters choose per-grain
export-tax-equivalents (a ban ≈ a large tax) to maximise national welfare
(consumer surplus + producer income − a food-price penalty). Nash is approximated
by iterated best response over the market layer. A convex food-price penalty that
only bites above a tolerated price reproduces the documented pattern: trade is
open in calm periods and restrictions emerge in spikes (2008, 2010–11, 2022).

**Storage.** Market-responsive (competitive) reserves and strategic government
buffer stocks adjust available supply each period before the market clears.

## Quick start

```bash
pip install -r requirements.txt
python demo.py
```

The demo runs a Black Sea wheat shock (Russia −40%, Ukraine −50%) under two
regimes — substitution on (full GRIST) and off (single-commodity limit) — plus a
no-shock counterfactual for each, and writes `grist_results.csv` and four figures.

Minimal use in code:

```python
from grist import build_countries, GristModel

countries, transport, grains, freight = build_countries(substitution=True)
model = GristModel(countries, transport, grains, freight_mult=freight)
df = model.run(periods=12, shocks={5: shock_matrix, 6: shock_matrix})
```

## Layout

```
grist/
  core.py          # demand system, spatial equilibrium, export game, storage, orchestrator
  calibration.py   # the 3-grain prototype dataset (swap this for real data)
demo.py            # Black Sea shock scenario + figures
figures/           # generated example figures
```

## Extending it

- **Grains** — the commodity dimension is an extensible list. Adding barley,
  sorghum, or rye is appending entries to `GRAINS`, `P0`, `OWN_ELAST`, the `RHO`
  substitution matrix, and per-country production/consumption — no re-architecting.
- **Real data** — replace `calibration.py`. Production and consumption from
  FAOSTAT / USDA PSD; the demand system takes baseline `(D0, p0, own_elast)` plus a
  substitutability matrix `rho`; validate baseline flows against BACI / COMTRADE.
- **Chokepoints** — `route_multiplier` scales the cost of a corridor, so a
  Bosphorus / Bab-el-Mandeb / Hormuz disruption enters the same machinery as a
  production shock.
- **Terms-of-trade motive** — `ExportRestrictionGame(revenue_weight=…)` adds an
  export-tax-revenue term; with substitution on, a flatter residual demand curve
  changes the optimal restriction, an interaction unavailable to no-substitution
  or no-strategy models.

## Caveats

This is a **prototype**. The calibration numbers are order-of-magnitude realistic
but illustrative — do not read the magnitudes as estimates. Demand and supply are
linear, production is short-run inelastic within a period, and Nash is an
iterated-best-response approximation on a coarse tax grid. It implements the
*architecture*, not a line-for-line replica of any published model's equations.

## License

MIT — see `LICENSE`.
