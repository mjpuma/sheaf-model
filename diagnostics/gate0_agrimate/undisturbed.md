# G0-U P2 — undisturbed drift

Task: why the three-scenario **undisturbed** world-price annual mean moved
from 0.202 (2006) to 0.329 (2011), ratio 1.63, while Agrimate undisturbed
is repeating seasonal behaviour. Not a Pink-Sheet score. No price pin.

## Two facts that were mixed together

1. **Seasonal shape already repeats.** corr(2006 season, 2011 season) ≈ 0.98
   on the world-price index. CV 1.17 is within-year harvest seasonality
   (index 0.014–3.17), not a random walk.
2. **World H\* = C\* = 542.25 MMT/year.** Inverse-demand floor binds 0 times.
   S_p=0 at t=0 is D.5 δ=ρ=0 Nash and S_p sits near 10–15 MMT after year 1.

The 1.63 figure is 2011 mean / 2006 **trough**, not a unit-root. Do not pin.

## Bug that *was* real (stocks and who eats), and is fixed

Pre-fix, the Ndel queue stored **exporter-indexed** XI and consumer inflow
was `sold_d[s] + XI_s(t−Ndel)`. Measured on 2006 undisturbed:
`max |inflow − sold_d − own XI_lag2| = 3.6e-15`. USA received its own
exports back. Eastern Africa inflow ≈ its tiny domestic sales (C/C* ≈ 0.11).

`purchaser_demand` (D.30) was computed and discarded.

Consequence: exporter **consumer** stocks ate the exportable surplus
(USA/Canada/Australia S_c +163/+127/+85 MMT over 2003–11). World C ≈ 0.90 C*
every year; ΔS_c ≈ H − C. That is not Agrimate undisturbed.

**Sourced fix (E.1, not a knob):** world price is still lagged XI · offer
(exporter-indexed). Consumer arrivals are `dest.T @ XI_lag` with `dest` the
row-normalised international T* (`international_destination_shares`). Empty
export rows keep a self-weight so grain is not deleted. D.30 CES still does
not ration quantities (P4).

After the fix (same 2003–11 undisturbed run):

- Eastern Africa consumption ~6–7 MMT/year on 0.33 MMT harvest (imports arrive).
- World consumption ~539 MMT vs C* 542; ending stocks ~201 MMT vs USDA world
  157 (was ~456 with the echo).
- **World-price series is unchanged** (same 1.63 ratio, same corr). That is
  expected: p_w never depended on who received the grain.

Classification of the echo: **B** (coding bug vs D.3/E.1 delivery). Recorded
as B1 in `GATE0_DEPARTURES.md`. Not L1–L8. Not a pin.

## What still moves the *price mean* (open, not pinned)

Because p_w is inverse demand on **international** volume, the annual mean
moves when the **xd/xi split** is not periodic under constant H. Undisturbed
annual XI still wanders 164–254 MMT (2004 vs 2005) after the delivery fix.
**R4** (`xi_split.md`): live D.22 `q_oth` EMA is the last/first channel on
this host (freeze → 1.019 vs author 1.004 vs live 1.630). xmin_off 0.548
and calendar_replan 0.523 overshoot. Freeze is a diagnostic isolation, not
adopted — author still updates q_oth. Do not pin. Do not add a decay knob.

| Candidate | Price mean | Stock balloon |
|---|---|---|
| S_p=0 Nash | Sourced D.5; S_p stabilises | No |
| Ψ / p_sto | Indirect | Echo blocked destock |
| Floor | 0 binds | No |
| Harvest vs C* | Seasonality | No (H*=C*) |
| Own-XI echo | **No** (p_w on XI) | **Yes — fixed** |
| Non-periodic XI split | volume still wanders | No |
| Live D.22 q_oth EMA | **Yes, last/first 1.630** (R4 freeze 1.019, not adopted) | No |

## What this is not

- Not a world-price pin.
- Not Bai α_foreign=10.
- Not G1/G2.
- Not “undisturbed prices are now flat.” They are still seasonal; stocks
  are no longer an exporter landfill.
