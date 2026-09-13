# Gate 1 report

Sensitivity band σ ∈ {0, 0.3, 0.6}, not a 2008 fit. See `diagnostics/GATE1_PLAN.md`.

## Identity

Coupled σ=0 vs independent Gate 0: **PASS**.

## Official-split prices (full = harvest + AMIS)

| Grain | σ | corr | 2008 model / obs | 2010 model / obs |
|---|---:|---:|---:|---:|
| wheat | 0 | +0.687 | ×2.09 / ×1.82 | ×1.31 / ×1.16 |
| rice | 0 | +0.676 | ×1.54 / ×1.84 | ×0.84 / ×0.79 |
| maize | 0 | +0.792 | ×2.05 / ×1.84 | ×1.52 / ×1.44 |
| wheat | 0.3 | +0.688 | ×2.16 / ×1.82 | ×1.38 / ×1.16 |
| rice | 0.3 | +0.683 | ×1.59 / ×1.84 | ×0.84 / ×0.79 |
| maize | 0.3 | +0.731 | ×2.12 / ×1.84 | ×1.45 / ×1.44 |
| wheat | 0.6 | +0.681 | ×2.24 / ×1.82 | ×1.43 / ×1.16 |
| rice | 0.6 | +0.648 | ×1.52 / ×1.84 | ×0.83 / ×0.79 |
| maize | 0.6 | +0.634 | ×2.19 / ×1.84 | ×1.20 / ×1.44 |

## Hard bar: spillover sign (2007/08 full hike vs σ=0)

- wheat σ=0.3: ×1.033  —
- rice σ=0.3: ×1.029  ok
- maize σ=0.3: ×1.034  ok
- wheat σ=0.6: ×1.072  —
- rice σ=0.6: ×0.984  FAIL sign
- maize σ=0.6: ×1.069  ok

**Spillover sign:** FAIL

## Hard bar: wheat Gate 0 attribution signs

- σ=0: 2008 restriction-led (tau×1.61, shocks×1.15); 2010 production-led (shocks×1.79, tau×1.28)  ok
- σ=0.3: 2008 restriction-led (tau×1.62, shocks×1.16); 2010 production-led (shocks×1.89, tau×1.30)  ok
- σ=0.6: 2008 restriction-led (tau×1.63, shocks×1.18); 2010 production-led (shocks×2.00, tau×1.30)  ok

**Wheat attribution:** PASS

## Hard bar: rice AMIS still carries most of 2008 rice hike

- σ=0: tau×1.55, shocks×0.92, full×1.54, AMIS share 101%  ok
- σ=0.3: tau×1.56, shocks×0.94, full×1.59, AMIS share 94%  ok
- σ=0.6: tau×1.56, shocks×0.96, full×1.52, AMIS share 109%  ok

**Rice AMIS dominance:** PASS

## Soft (do not select σ* on these)

- wheat σ=0.3: Δcorr=+0.001, Δ2008=+0.069, Δ2010=+0.067
- rice σ=0.3: Δcorr=+0.007, Δ2008=+0.045, Δ2010=-0.005
- maize σ=0.3: Δcorr=-0.061, Δ2008=+0.071, Δ2010=-0.061
- wheat σ=0.6: Δcorr=-0.006, Δ2008=+0.150, Δ2010=+0.116
- rice σ=0.6: Δcorr=-0.028, Δ2008=-0.024, Δ2010=-0.015
- maize σ=0.6: Δcorr=-0.159, Δ2008=+0.141, Δ2010=-0.317

Rice 2010 observed ×0.79 (<1). Model σ=0 ×0.84, σ=0.6 ×0.83. A large σ-driven rice co-spike in 2010/11 would be a miss against the data, not a substitution win.

No σ* selected. Band is the result.

Figure: `/Users/mjp38/GitHub/sheaf-model/figures/fig_gate1_substitution.png`.
Table: `/Users/mjp38/GitHub/sheaf-model/diagnostics/gate1_score.csv`.
