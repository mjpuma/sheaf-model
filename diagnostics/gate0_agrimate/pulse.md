# G0-H/P — 2008 exporter pulse grid (P11)

**Prescribed Δ, not Gate 2.** `restriction_pulse` on harvest-anomaly
wheat, 2008 only, versus harvest-only. Governments do not choose Δ.
`sheaf/dynamic_policy.py` is not imported. `wheat_params()` stay
αI=3.2, p_sto=0.1, xmin=0.2. L1–L8 stay rejected. Bai α_foreign=10
not adopted. AMIS diary is **off**; each run has one synthetic pulse.

Window: 2008 (no 2003–11 re-run). Pulse start 2008-01-01.
Grid: Ukraine, Russia × {0.5, 1.0} × {6, 12} months = **8 runs**
+ harvest-only. Bai's 9×2×2=36 2020 grid is **not** run.
This 8-run slice is **clean**
(failed=0, production identical, Δ on one exporter, Δ=1.0/12m
cuts that exporter's XI). Do not expand to 36 in this prompt
either way — one PR-sized change.

## Harvest-only 2008 (baseline)

Mean world price $217.9/t; max $607.5. Failed 0;
unconverged 202 of 24*27.
Harvest-only Ukraine XI 11.2 MMT (this row's quantity columns).
Russia harvest-only XI is the denominator on the Russia rows.
Exporter columns below are vs this path, not vs Pink Sheet.

## Pulse vs harvest-only

| run | Δ steps | mean p $/t | vs H | exports | vs H | consumption vs H | failed | unconv |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ukraine_0.5_6m | 12 | 216.9 | 1.00 | 10.9 | 0.97 | 1.00 | 0 | 213 |
| Ukraine_0.5_12m | 24 | 218.6 | 1.00 | 5.6 | 0.50 | 1.00 | 0 | 213 |
| Ukraine_1_6m | 12 | 216.6 | 0.99 | 10.5 | 0.93 | 1.00 | 0 | 207 |
| Ukraine_1_12m | 24 | 218.2 | 1.00 | 0.0 | 0.00 | 1.00 | 0 | 196 |
| Russia_0.5_6m | 12 | 218.8 | 1.00 | 14.1 | 0.92 | 0.99 | 0 | 209 |
| Russia_0.5_12m | 24 | 220.8 | 1.01 | 7.7 | 0.50 | 0.98 | 0 | 215 |
| Russia_1_6m | 12 | 219.1 | 1.01 | 12.8 | 0.84 | 0.98 | 0 | 207 |
| Russia_1_12m | 24 | 221.1 | 1.01 | 0.0 | 0.00 | 0.98 | 0 | 203 |

Δ=1.0 is a complete international cut (D.3 `(1−Δ)`), stronger than
E.4's 0.95 ban. Intensity 0.5 matches E.4 export tax. 6-month
pulses occupy 12 of 24 steps; 12-month pulses occupy the year.

Ukraine Δ=1 / 12m exports vs harvest-only: 0.00×.
Russia Δ=1 / 12m: 0.00×.

## What the slice shows

D.3 `(1−Δ)` binds on the prescribed exporter: 12-month Δ=1.0
zeros Ukraine and Russia XI; 12-month Δ=0.5 halves them
(Ukraine 0.50× / Russia 0.50×). A 6-month pulse from 2008-01-01 only
cuts annual XI by a few percent to mid-teens (Ukraine 0.97 / 0.93, Russia 0.92 / 0.84): wheat harvest calendars
are Jul–Aug (Ukraine) and Jul–Sep (Russia), so Jan–Jun is
mostly the lean half of the year. Mean world price stays
0.99–1.01× harvest-only; the ~$608 max is the host seasonal
spike (P8), not a restriction spike. Unsold grain stays in stocks (Ukraine Δ=1/12m ending stocks 2.20× harvest-only).
Consumption barely moves. Unconverged scipy (N5) is counted;
failed=0.

This is **clean** as a mechanism
check. It is not a Pink-Sheet fit, not a reason to restore L1–L8,
not Gate 2, and not a reason to expand to Bai's 36-run 2020 grid
in this PR.

## Not Gate 2, not the 36-run grid

- Gate 2 would let governments **choose** Δ. Disabled G2 recovers
  E.4 AMIS. This grid **prescribes** Δ.
- Bai 2020: 9 exporters × 2 intensities × 2 durations. Not run.
- Default three-scenario host is unchanged (AMIS diary still E.4).

## Files

- `score_pulse.csv` — harvest-only + 8 pulses

Next: P12 methods note is `methods.md` (written; not accepted; G1 blocked).

