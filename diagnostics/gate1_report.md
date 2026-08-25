# Gate 1 report

Sensitivity band σ ∈ {0, 0.3, 0.6}, not a 2008 fit. See `diagnostics/GATE1_PLAN.md`.

## Identity

Coupled σ=0 vs independent Gate 0: **PASS**.

## Official-split prices (full = harvest + AMIS)

| Grain | σ | corr | 2008 model / obs | 2010 model / obs |
|---|---:|---:|---:|---:|
| wheat | 0 | +0.720 | ×2.27 / ×1.82 | ×1.45 / ×1.16 |
| rice | 0 | +0.678 | ×1.72 / ×1.84 | ×0.82 / ×0.79 |
| maize | 0 | +0.712 | ×1.97 / ×1.84 | ×1.70 / ×1.44 |
| wheat | 0.3 | +0.724 | ×2.36 / ×1.82 | ×1.50 / ×1.16 |
| rice | 0.3 | +0.674 | ×1.75 / ×1.84 | ×0.82 / ×0.79 |
| maize | 0.3 | +0.670 | ×2.05 / ×1.84 | ×1.52 / ×1.44 |
| wheat | 0.6 | +0.721 | ×2.45 / ×1.82 | ×1.54 / ×1.16 |
| rice | 0.6 | +0.670 | ×1.79 / ×1.84 | ×0.82 / ×0.79 |
| maize | 0.6 | +0.592 | ×2.14 / ×1.84 | ×1.15 / ×1.44 |

## Hard bar: spillover sign (2007/08 full hike vs σ=0)

- wheat σ=0.3: ×1.039  —
- rice σ=0.3: ×1.018  ok
- maize σ=0.3: ×1.042  ok
- wheat σ=0.6: ×1.082  —
- rice σ=0.6: ×1.039  ok
- maize σ=0.6: ×1.085  ok

**Spillover sign:** PASS

## Hard bar: wheat Gate 0 attribution signs

- σ=0: 2008 restriction-led (tau×1.70, shocks×1.20); 2010 production-led (shocks×1.85, tau×1.36)  ok
- σ=0.3: 2008 restriction-led (tau×1.71, shocks×1.21); 2010 production-led (shocks×1.95, tau×1.36)  ok
- σ=0.6: 2008 restriction-led (tau×1.72, shocks×1.22); 2010 production-led (shocks×2.08, tau×1.35)  ok

**Wheat attribution:** PASS

## Hard bar: rice AMIS still carries most of 2008 rice hike

- σ=0: tau×1.75, shocks×0.93, full×1.72, AMIS share 104%  ok
- σ=0.3: tau×1.76, shocks×0.93, full×1.75, AMIS share 100%  ok
- σ=0.6: tau×1.76, shocks×0.93, full×1.79, AMIS share 97%  ok

**Rice AMIS dominance:** PASS

## Soft (do not select σ* on these)

- wheat σ=0.3: Δcorr=+0.004, Δ2008=+0.088, Δ2010=+0.050
- rice σ=0.3: Δcorr=-0.004, Δ2008=+0.031, Δ2010=+0.000
- maize σ=0.3: Δcorr=-0.042, Δ2008=+0.083, Δ2010=-0.177
- wheat σ=0.6: Δcorr=+0.001, Δ2008=+0.187, Δ2010=+0.097
- rice σ=0.6: Δcorr=-0.008, Δ2008=+0.067, Δ2010=-0.000
- maize σ=0.6: Δcorr=-0.119, Δ2008=+0.168, Δ2010=-0.545

Rice 2010 observed ×0.79 (<1). Model σ=0 ×0.82, σ=0.6 ×0.82. No invented rice co-spike.

Maize 2010 is the material soft miss at σ=0.6: hike ×1.70 → ×1.15 (obs ×1.44), corr +0.71 → +0.59. Do **not** treat σ=0.3 as selected because maize 2010 is closer to the data there.

No σ* selected. Band is the result.

Figure: `figures/fig_gate1_substitution.png`.
Table: `diagnostics/gate1_score.csv`.
