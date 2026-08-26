# Gate 1 E5 — maize 2010 collapse

Official split, σ=0.6 counterfactuals. CropParams / ρ structure / σ grid
frozen. Restoration = share of (σ=0 − σ=0.6) maize 2010 hike closed.

| Run | maize 2010 | restore | maize 2008 | maize corr |
|---|---:|---:|---:|---:|
| σ=0 | ×1.70 | 100% | ×1.97 | +0.712 |
| σ=0.6 | ×1.15 | 0% | ×2.14 | +0.592 |
| σ=0.6 zero ρ_rm | ×1.39 | 43% | ×2.09 | +0.657 |
| σ=0.6 freeze rice | ×1.16 | 2% | ×2.13 | +0.594 |
| σ=0.6 zero ρ_wm | ×1.63 | 87% | ×2.02 | +0.677 |

σ=0 maize 2010 ×1.70; σ=0.6 ×1.15; obs ×1.44.

## Classification

The 2010 hike *ratio* collapse is **not** cheap rice pulling demand off maize
in 2011. Holding rice on the σ=0 path restores **2%**. Zero rice–maize ρ
restores **43%** (secondary). Zero wheat–maize ρ restores **87%**.

Decompose the hike window (3-month means):

| Run | maize Jun 2009 ($/t) | maize Feb 2011 ($/t) | hike |
|---|---:|---:|---:|
| σ=0 | 182 | 310 | ×1.70 |
| σ=0.6 | 283 | 327 | ×1.15 |
| σ=0.6 zero ρ_wm | 199 | 323 | ×1.63 |

The 2011 *peak is slightly higher* under substitution. The ratio falls
because wheat–maize ρ keeps maize expensive through 2009 after the 2008
spillover (base 182 → 283). This is hike-window arithmetic, not an inverted
2010 demand sign.

**Leftover class:** wheat–maize feed substitution at σ=0.6 lifts 2008–09
maize *levels*; the 2010/11 peak/base metric then looks like a collapse.
Disclose in P3. Do not retune ρ. Do not crown σ=0.3. Do not treat ×1.15 as
“substitution inverted maize in 2010.”

Figure: `figures/fig_gate1_e5_maize.png`.
Table: `diagnostics/gate1_e5_score.csv`.
