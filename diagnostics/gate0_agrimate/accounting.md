# G0-U P1 — accounting identities (2006 harvest+AMIS)

Command: `python -m pytest tests/agrimate/test_accounting.py -q`

Short path: wheat 2006 only, 27 regions × 24 steps, harvest anomalies on,
AMIS restrictions on. Author `AgrimateParams`. No model change.


- regions: 27
- steps: 24
- identity checks: 2592
- violations: 0

- In-transit international shipments (Ndel queue) sit in neither S_p nor S_c; that is Agrimate delivery lag, not a stock identity.
- Producer S_p starts at 0. Consumer S_c starts at Ψ·Nyear·C*. δ_loss=0.0.

All four P1 identities hold on this path (atol 1e-8):

1. Producer D.6: `S_p' = max((1-δ)S_p + H - sold_d - sold_i, 0)`.
2. Consumer: `S_c' = max(S_c + inflow - C, 0)` and `C ≤ S_c + inflow`.
3. Sales: `sold_d, sold_i ≥ 0`; `sold_d + sold_i ≤ S_p + H`;
   `sold_i ≤ (1-Δ)(S_p + H - sold_d)` (D.3).
4. `price_index`, stocks, harvest, consumption, sales, inflow finite.

Classification: **H** (not an issue) for this 2006 path.
No economic change. Next prompt is P2 (undisturbed drift).
