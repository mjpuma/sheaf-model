# Gate 2 beta: endogenous export cuts on the two-week crisis spine

**Date:** 2026-08-27. Mechanism check on the Gate 0 spine — not a new
paper title. “P4/P5” were research questions, not a queue
(`diagnostics/PAPER_STACK.md`).
**Clock:** `diagnostics/GAME_CLOCK.md` (Headey 2011).
**Host:** Gate 0 24-step wheat market in `sheaf/dynamic_crop.py`.
**Not the host:** annual SPE + IBR in `sheaf/core.py` (`demo.py`) — that
is the TWIST-era leftover. Substitution stays **off**. AMIS diary stays
**off**. CropParams / ρ / σ are not retuned. **Gate 0 and Gate 1 are
not re-run.**

## Question

Can **two** exporters, sharing the same slow type, choose state-contingent
`τ_t` so that a harvest shortfall at one of them produces a restriction
at the **neighbor who did not lose harvest**, while climatology keeps
both open?

That is Headey’s cascade in miniature (pressure on remaining Black Sea
exporters). It is **not** “who banned in 2008/10.” Knobs stay
illustrative.

One-player nested year-open-loop grid BR remains as a diagnostic on the
shocked exporter.

## Two timescales

- **Types** (slow): who plays, `gov_stu`, `tau_on`, stock-ratio trigger,
  food-security weight. Analogous to Headey’s “governments care about
  rice” — that does not flip every fortnight unless the government does.
- **Actions** (fast): `τ_{i,t}` on the 24-step clock, responding to
  stocks relative to a normal year at the same calendar step.

## What this beta is

- **Two players, same type:** Russia (synthetic harvest ×0.50) and
  Kazakhstan (climatology harvest). Ukraine is on the market but does
  not play — on this host a Ukraine-only harvest cut does not lean
  Russia enough to fire the stock-ratio gate (Russia is fat). The
  neighbor who *does* fire is the leaner one.
- **State-contingent** `τ_t`: two-pass (open path, then cuts). Shock
  year only. Intensity `tau_on` is a type, not re-optimized every step.
- The cascade here is **harvest diversion**, not ban-on-ban IBR:
  Kazakhstan’s stocks fall because Russia’s harvest fails and demand
  spills, even before Russia’s `τ_t` is applied. Disclose that.
- **Illustrative** knobs.
- Nested **year-open-loop** grid BR still scored on Russia.

## What this beta is not

- A standalone “policy paper” or “tipping paper”
- Cooperative / “just enough” / club of the willing (same layer, different
  objective — later, if ever)
- Tipping, importer panic procurement, or Japan-style reserve
  *announcements* (Headey has those; we do not)
- Sequential fortnight IBR / a proven Nash among many exporters
- Substitution (Gate 1). Do not pick σ*
- An AMIS hindcast. Official Gate 0 / Gate 1 scoring paths stay `use_amis=True`
- Unpausing `sheaf/dynamic_grains.py`
- A split domestic versus export ask inside the market clear
- Scoring who restricted in 2008 or 2010
- A reason to re-run Gate 0 or Gate 1

## Host limitation (disclose)

Gate 0 has **one world/ask price** per crop. A ban does not create a
cheaper domestic CPI. Grain that is not offered stays as **stock**.
World *p* does not enter the food-security term. Annual SHEAF
(`core.py`) has node prices from a spatial QP; do not equate the hosts.

## Action rule (Headey-flavored, illustrative)

Absolute stock floors (`S_t < s`) fire every hungry season in
climatology. The crisis object on this host is the **climatology-relative**
ratio. For exporter *i*, shock year *T*:

\[
\tau_{i,t}
=
\begin{cases}
\tau^{\mathrm{on}} & t\in T \text{ and } S_{i,t}/S^{\mathrm{calm}}_{i,t} < r \\
0 & \text{otherwise.}
\end{cases}
\]

`τ^on = 0.6`, `r = 0.85`, both illustrative. `S^{calm}` is the same
model with climatology harvest and τ ≡ 0.

Nested year BR, for the record (not the headline):

\[
W(\tau)=\sum_{t\in T} p_t X_{i,t}
\;-\;
\alpha\max\bigl(0,\, s^{\mathrm{gov}}_i-\overline{S}_{i,T}\bigr)^2
\]

on `τ ∈ {0, 0.3, 0.6, 0.9}`. Calm ⇒ τ\* = 0; shock ⇒ τ\* = 0.6. That
intensity is what `tau_on` copies.

## Default scenario

| Knob | Value | Class |
|---|---|---|
| Crop | wheat | structural (Gate 0) |
| Exporter (harvest shock) | Russia | illustration |
| Players | Russia, Kazakhstan | illustration; same types |
| Years | 2006–2008 | short window |
| Shock year | 2007 | synthetic |
| Harvest multiplier | 0.50 on **Russia only** | illustration |
| AMIS / LOWESS / flex | off / off / mean | identification |
| `gov_stu` (φ) | 0.48 | illustrative type |
| `fs_stock_weight` (α) | 12 | illustrative type |
| `tau_on` | 0.6 | illustrative type (from nested BR) |
| `stock_ratio_trigger` | 0.85 | illustrative type |
| Year τ grid | 0, 0.3, 0.6, 0.9 | nested diagnostic |

## Hard bars

1. **Calm ⇒ τ_t = 0** for every player (and nested year τ\* = 0).
2. **Russia harvest ×0.50 ⇒ Russia some τ_t > 0.**
3. **Kazakhstan some τ_t > 0** with **no** Kazakh harvest cut.
4. **Kazakhstan’s first on-step ≥ Russia’s** (neighbor lags or ties).
5. **Russia’s cuts reduce Russia’s shipments** vs the open shock path.
6. **`run_crop_dynamics` defaults unchanged.**

## Code

| Path | Role |
|---|---|
| `diagnostics/GAME_CLOCK.md` | Headey clock; Gate 0/1 do not re-run |
| `diagnostics/GATE2_PLAN.md` | this file |
| `sheaf/dynamic_policy.py` | types, year BR, state-contingent τ_t |
| `scripts/score_gate2_beta.py` | calm vs shock + path figure + choropleths |
| `sheaf/maps.py` | Natural Earth 110m choropleths (regular score) |
| `overleaf/gate2_assessment/` | assessment note to zip for Overleaf |
| `tests/test_gate2_policy_beta.py` | hard bars |

Do not estimate knobs on 2008. Do not retune CropParams.
Do not re-run Gate 0 or Gate 1 for this note.
