# Gate 0 v2: published wheat inputs on develop-consumers

2026-11-09. Host: PIK `develop-substitution-claude`, a snapshot of `develop-consumers`
`f492df93` with no code changes (local commit `2807556`). One consumer per region
(`consumer_A_c_source = nothing`, `consumer_share_source = nothing`,
`A_c_star = :empirical`). Published SLSQP stop, `maxtime = 60`. Inputs: the J10
wheat set that reproduced the Kuhla et al. (2025) 2000–2012 hindcast on the old host
(`agrimate_input_authorbase`). Driver `diagnostics/gate0_v2/gate0_4crop.jl wheat 312
published`, scorer `diagnostics/gate0_v2/score_gate0.py` (reproduces the B_small
J10 numbers exactly). Kilian's 2026 inputs cannot run yet: their `A_c` column is
empty for all four crops.

## Result against the published hindcast

| Bar | New host | Published | Result |
|---|---:|---:|---|
| 2007/08 ratio, within 0.01 of 1.359 | 1.353 | 1.361 | pass |
| 2010/11 ratio, within 0.01 of 1.213 | 1.213 | 1.219 | pass |
| May 2008 peak, within 0.01 of 2.216 | 2.190 | 2.223 | miss (0.026) |
| World stocks within 0.5 %, 2000–2012 | worst +0.508 % (2011) | — | miss (0.008 points) |

Other year-end gaps are within 0.33 % (2007 −0.33 %, mostly Argentina; 2011 +0.51 %,
mostly Argentina). Run time 178 s for 312 steps. Two sequential runs on an idle machine
gave identical values in all 48 numeric NetCDF variables (stored to 4 decimals).

## Comparison with the old host

Initial state: identical in harvests, sales, both storages, baseline price, `A_d`, `ψ`,
`α domestic` and baseline foreign share. Baseline trade is identical after swapping the
two region axes (output orientation only). Baseline consumption has the same annual
totals (relative difference 1e-9) with a slightly different seasonal profile (at most
3.5e-5 relative, India), consistent with the per-consumer Nash baseline on this branch.

Path: identical world price for steps 1–8. From step 9 the hosts drift apart. Before
2006 the gap exceeds the old host's own run-to-run spread at 22 of 192 steps (largest
world-stock gap +0.075 points at step 72, spread 0.003), so part of the difference
is the code, not the clock.

Old host reruns of the published code (`d883c7a`, same inputs, `maxtime = 60`, three
runs in parallel with other jobs, stopped at 216 / 192 / 192 steps):

| Run | 2007/08 ratio | May 2008 peak | Year-end stock gaps |
|---|---:|---:|---|
| clock 1 | 1.344 | 2.187 | 2006 +0.57 %, 2007 +0.66 %, 2008 +0.30 % |
| clock 2 | — | — | 2006 −0.01 %, 2007 −0.12 % |
| clock 3 | — | — | 2006 +0.90 %, 2007 −0.08 % |

The published code misses the 2007/08, peak and stock bars on rerun, by more than
the new host does. The accepted J10 values are one draw from a clock-dependent
range. These reruns shared the machine, so their spread may exceed that of a
run made alone.

## Classification

New host vs published: misses peak and 2011 stocks by small margins inside the
published code's own rerun range. **C** (numerical; clock-dependent SLSQP stop), 80–95.
Part of the pre-2006 drift is a code difference (seasonal baseline consumption is the
only initial difference found); not localized further. **D** (develop-consumers
restructure), 60–80. Bars unchanged.
