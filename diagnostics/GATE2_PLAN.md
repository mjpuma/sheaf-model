# Gate 2 beta: endogenous export cuts on the two-week crisis spine

**Date:** 2026-08-26. Paper **P4 beta**, not P4 proper and not P5.
**Host:** Gate 0 24-step wheat market in `sheaf/dynamic_crop.py`.
**Not the host:** annual SPE + IBR in `sheaf/core.py` (`demo.py`).
Substitution stays **off**. AMIS diary stays **off**. CropParams / ρ / σ
are not retuned.

## Question

Can one exporter, facing the locked Gate 0 market, choose a discrete
export-cut intensity τ such that a harvest shortfall at home produces a
restriction, and a calm harvest does not?

That is a mechanism check. It is **not** “who banned in 2008/10.” The
knobs below are illustrative on purpose: they are locked after the
qualitative calm/shock flip is visible, not estimated from AMIS, Pink
Sheet, or USDA.

## What this beta is

- **One player versus the market**, not Nash among several exporters.
- **Open-loop** τ: a single intensity applied to that exporter’s offers
  for every step of a designated shock year (zero otherwise). No
  fortnight-by-fortnight best response.
- **Illustrative** food-security weight and government buffer. Not
  estimated.
- Forcing is a **synthetic** harvest cut on the exporter, on top of
  climatology. Historical 2010 Russia is not the score.

## What this beta is not

- P4 cooperative / “just enough” / club of the willing
- P5 tipping or cooperation weights
- Multi-country Nash (annual `ExportRestrictionGame` stays on `core.py`)
- Substitution (Gate 1). Do not pick σ*
- An AMIS hindcast. Official P1/P3 scoring paths stay `use_amis=True`
  exogenous and `play_game` off
- Unpausing `sheaf/dynamic_grains.py`
- A split domestic versus export ask inside the market clear
- Scoring who restricted in 2008 or 2010

## Host limitation (disclose)

Gate 0 has **one world/ask price** per crop. A ban does not create a
cheaper domestic CPI for the exporter’s consumers. Grain that is not
offered stays as **stock**. Food-security in the objective is therefore
a **local stock-to-buffer penalty**, not a penalty on world *p* (a
world-*p* penalty would punish the government for the same spike the ban
causes). Export revenue still uses world *p* × shipments. Demand still
sees world *p*.

Annual SHEAF (`core.py`) has node prices from a spatial QP, which is why
that game can use consumer surplus at *pᵢ*. Do not equate the two hosts.

## Objective (illustrative)

For exporter *i*, wheat, shock year *T*:

\[
W(\tau)=\sum_{t\in T} p_t X_{i,t}
\;-\;
\alpha\max\bigl(0,\, s^{\mathrm{gov}}_i-\overline{S}_{i,T}\bigr)^2
\]

- \(X_{i,t}\): cleared shipments (not offers)
- \(\overline{S}_{i,T}\): mean end-of-step stock over the shock year
- \(s^{\mathrm{gov}}_i=\phi\,C^{\mathrm{ann}}_i\): illustrative government
  buffer, **not** Gate 0 competitive safety (`stu_target × C_ann`)
- \(\alpha\): `fs_stock_weight` (illustrative)

τ grid: \(\{0, 0.3, 0.6, 0.9\}\). Best response = argmax *W* on that grid.

### Why not a per-step safety gap?

Gate 0 competitive safety is `stu_target × C_ann` (wheat: 0.20 × 37.8 MMT
≈ 7.55 MMT). The harvest calendar already drives Russia’s hungry-season
trough to ~4.7 MMT **in climatology**. A per-step
\(\sum_t \max(0, s_i-S_{i,t})^2\) therefore makes a calm government
restrict: it is fighting the seasonal sawtooth, not a crisis. Mean
stocks, by contrast, sit near 22 MMT in climatology and near 14 MMT
after a 50% harvest cut — that is the object that separates the two
scenarios. \(\phi=0.48\) places \(s^{\mathrm{gov}}\) between those means.

Terms of trade alone (\(\alpha=0\)) already produce the qualitative flip:
calm revenue is maximised at τ=0; shock revenue peaks at τ=0.6. The
locked \(\alpha=12\) leaves that interior shock BR in place while putting
a visible food-security penalty on the shocked path and zero penalty on
climatology. Raising \(\alpha\) far enough (or \(\phi\)) corners the
shock BR at τ=0.9; that is a knob, not a result.

## Default scenario

| Knob | Value | Class |
|---|---|---|
| Crop | wheat | structural (Gate 0) |
| Exporter | Russia | illustration |
| Years | 2006–2008 | short window |
| Shock year | 2007 | synthetic |
| Harvest multiplier | 0.50 on Russia, shock year only | illustration |
| AMIS | off | identification |
| LOWESS shocks | off (climatology, then synthetic cut) | identification |
| Mean flex, industrial | official Gate 0 wheat defaults | frozen |
| `gov_stu` (φ) | 0.48 | illustrative; locked after the flip |
| `fs_stock_weight` (α) | 12 | illustrative; locked after the flip |
| τ grid | 0, 0.3, 0.6, 0.9 | illustrative |

## Hard bars

1. **Calm ⇒ τ\* = 0.** Climatology harvest, no AMIS, no synthetic cut.
2. **Shock ⇒ τ\* > 0.** Same knobs, Russia harvest ×0.50 in 2007.
3. **τ cuts that exporter’s shipments** relative to τ=0 under the shock.
4. **P1 identity:** `run_crop_dynamics` defaults unchanged (AMIS still
   exogenous when this module is not called).

## Code

| Path | Role |
|---|---|
| `diagnostics/GATE2_PLAN.md` | this file |
| `sheaf/dynamic_policy.py` | knobs, welfare, grid BR |
| `sheaf/dynamic_crop.py` `simulate_prep` | run prep with overridden H/τ |
| `scripts/score_gate2_beta.py` | calm vs shock table + figure |
| `tests/test_gate2_policy_beta.py` | hard bars 1–3 |

Do not start P5. Do not estimate α or φ on 2008. Do not retune CropParams.
