# Gate 2 beta: endogenous export cuts on the two-week crisis spine

**Date:** 2026-08-27. Paper **P4 beta**, not P4 proper and not P5.
**Clock:** `diagnostics/GAME_CLOCK.md` (Headey 2011).
**Host:** Gate 0 24-step wheat market in `sheaf/dynamic_crop.py`.
**Not the host:** annual SPE + IBR in `sheaf/core.py` (`demo.py`) — that
is the TWIST-era leftover. Substitution stays **off**. AMIS diary stays
**off**. CropParams / ρ / σ are not retuned. **Gate 0 and Gate 1 are
not re-run.**

## Question

Can one exporter, facing the locked Gate 0 market, choose a
**state-contingent** export cut `τ_t` such that a harvest shortfall at
home produces restrictions *inside the year*, and a calm harvest does
not?

That is a mechanism check. It is **not** “who banned in 2008/10.” The
knobs are illustrative on purpose.

A nested year-open-loop grid BR (one intensity for all 24 fortnights of
the shock year) remains as a diagnostic: it asks what single τ they
would pick if they had to. It is not Headey’s object. Headey’s object
has dates.

## Two timescales

- **Types** (slow): who plays, `gov_stu`, `tau_on`, stock-ratio trigger,
  food-security weight. Analogous to Headey’s “governments care about
  rice” — that does not flip every fortnight unless the government does.
- **Actions** (fast): `τ_{i,t}` on the 24-step clock, responding to
  stocks relative to a normal year at the same calendar step.

## What this beta is

- **One player versus the market**, not Nash among several exporters.
- **State-contingent** `τ_t`: two-pass (open path, then cuts). Shock
  year only. Intensity `tau_on` is a type, not re-optimized every step.
- **Illustrative** knobs, locked after the qualitative flip.
- Forcing is a **synthetic** harvest cut on the exporter, on top of
  climatology. Historical 2010 Russia is not the score.
- Nested **year-open-loop** grid BR still scored.

## What this beta is not

- P4 cooperative / “just enough” / club of the willing
- P5 tipping, importer panic procurement, or Japan-style reserve
  *announcements* (Headey has those; we do not, yet)
- Multi-country Nash on either host
- Substitution (Gate 1). Do not pick σ*
- An AMIS hindcast. Official P1/P3 scoring paths stay `use_amis=True`
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
| Exporter | Russia | illustration |
| Years | 2006–2008 | short window |
| Shock year | 2007 | synthetic |
| Harvest multiplier | 0.50 on Russia, shock year only | illustration |
| AMIS / LOWESS / flex | off / off / mean | identification |
| `gov_stu` (φ) | 0.48 | illustrative type |
| `fs_stock_weight` (α) | 12 | illustrative type |
| `tau_on` | 0.6 | illustrative type (from nested BR) |
| `stock_ratio_trigger` | 0.85 | illustrative type |
| Year τ grid | 0, 0.3, 0.6, 0.9 | nested diagnostic |

## Hard bars

1. **Calm ⇒ τ_t = 0** every step (and nested year τ\* = 0).
2. **Shock ⇒ some τ_t > 0** (and nested year τ\* > 0).
3. **Those cuts reduce shipments** vs the open shock path.
4. **P1 identity:** `run_crop_dynamics` defaults unchanged.

## Code

| Path | Role |
|---|---|
| `diagnostics/GAME_CLOCK.md` | Headey clock; Gate 0/1 do not re-run |
| `diagnostics/GATE2_PLAN.md` | this file |
| `sheaf/dynamic_policy.py` | types, year BR, state-contingent τ_t |
| `scripts/score_gate2_beta.py` | calm vs shock + path figure |
| `tests/test_gate2_policy_beta.py` | hard bars |

Do not start P5. Do not estimate knobs on 2008. Do not retune CropParams.
Do not re-run Gate 0 or Gate 1 for this note.
