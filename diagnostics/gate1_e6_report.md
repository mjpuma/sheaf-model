# Gate 1 E6 — 2021–23 Ukraine-war hold-out

Frozen band σ ∈ {0, 0.3, 0.6}. Same flags as Gate 0 Ukraine:
2021–23, stock seed 2020, FAOSTAT 2019–21, p0 = 2021 Pink Sheet mean.
No σ* selected.

- Identity σ=0 vs Gate 0: **PASS** (max rel |Δp| ≲ 2e-16).
- Wheat AMIS-led (tau > shocks): **PASS** at every σ.
- Maize invented co-spike: **PASS** (stays ×1.01 vs obs ×1.09).
- Rice 2008-scale spike: **PASS** (hike 1.18 < 1.20 rule).
- **Soft:** rice drifts the wrong way (σ=0 ×0.99 → σ=0.6 ×1.18 vs obs
  ×0.91, corr +0.61 → +0.46). Disclose. Do **not** pick σ=0.6 because
  wheat corr rose (+0.69 → +0.75).

## Official-split prices (full = harvest + AMIS)

| Grain | σ | corr | hike model / obs |
|---|---:|---:|---:|
| wheat | 0 | +0.688 | ×1.61 / ×1.57 |
| wheat | 0.3 | +0.700 | ×1.65 / ×1.57 |
| wheat | 0.6 | +0.750 | ×1.69 / ×1.57 |
| rice | 0 | +0.607 | ×0.99 / ×0.91 |
| rice | 0.3 | +0.539 | ×1.08 / ×0.91 |
| rice | 0.6 | +0.457 | ×1.18 / ×0.91 |
| maize | 0 | +0.204 | ×1.01 / ×1.09 |
| maize | 0.3 | +0.228 | ×1.01 / ×1.09 |
| maize | 0.6 | +0.181 | ×1.01 / ×1.09 |

## Soft Δ vs σ=0 (do not select on)

- wheat σ=0.3: Δcorr=+0.012, Δhike=+0.032
- rice σ=0.3: Δcorr=-0.068, Δhike=+0.092
- maize σ=0.3: Δcorr=+0.025, Δhike=+0.001
- wheat σ=0.6: Δcorr=+0.062, Δhike=+0.076
- rice σ=0.6: Δcorr=-0.149, Δhike=+0.187
- maize σ=0.6: Δcorr=-0.022, Δhike=+0.003

Figure: `figures/fig_gate1_e6_ukraine.png`.
Table: `diagnostics/gate1_e6_score.csv`.
