# R4 — Undisturbed xd/xi split

Item 3 still fails. Characterisation only. **Not a pin.**
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3, xmin=0.2. Fig. 4 knobs
are not adopted. L1–L8 stay rejected. No decay knob.
G1/G2 stay blocked. B1 delivery did not move p_w.

Undisturbed 2003–11 (repeating H, no AMIS). Score window
**2006–2011** last/first of the annual-mean
price index. Author Fig. 4 baseline last/first = 1.004.

## Annual XI / XD on the default host

H*=C* every year. Inverse-demand floor binds 0 times. Annual international sales still
wander under constant H:

| year | XD MMT | XI MMT | XI/(XD+XI) | p_w mean | S_p end |
|---:|---:|---:|---:|---:|---:|
| 2003 | 337.0 | 189.3 | 0.360 | 0.955 | 15.9 |
| 2004 | 383.2 | 164.4 | 0.300 | 0.450 | 10.6 |
| 2005 | 285.8 | 254.4 | 0.471 | 0.566 | 12.7 |
| 2006 | 329.0 | 213.4 | 0.393 | 0.202 | 12.6 |
| 2007 | 326.7 | 215.4 | 0.397 | 0.350 | 12.7 |
| 2008 | 317.4 | 225.4 | 0.415 | 0.328 | 12.2 |
| 2009 | 339.8 | 203.4 | 0.374 | 0.317 | 11.2 |
| 2010 | 324.3 | 216.5 | 0.400 | 0.389 | 12.6 |
| 2011 | 358.6 | 186.6 | 0.342 | 0.329 | 9.6 |

XI range 2004–11: 164.4–254.4 MMT (span 89.9; 0.43× mean). That is the open
price-mean channel (`undisturbed.md`).

## Labelled probes (not adopted)

Each probe is the default host with **one** candidate switched.
Defaults recover the live path (`replan_stride=1`, `freeze_q_oth=False`,
ζ=0).

| label | candidate | last/first | XI span MMT | unconverged | failed |
|---|---|---:|---:|---:|---:|
| default | host (Jacobi + rolling + xmin on) | 1.630 | 89.9 | 1583/5832 | 0 |
| xmin_off | xmin penalty off (ζ=1) | 0.548 | 78.0 | 1066/5832 | 0 |
| qoth_freeze | Jacobi D.22 q_oth frozen | 1.019 | 97.8 | 1555/5832 | 0 |
| calendar_replan | rolling year off (January replan) | 0.523 | 71.3 | 42/243 | 0 |

Author last/first = 1.004. Host default = 1.630 (the 1.63 figure).
Nearest labelled probe: **qoth_freeze** (not adopted).

Reading: qoth_freeze 1.019 is within 0.05 of author 1.004 on this window. Other probes move the wrong way (xmin_off 0.548; calendar_replan 0.523). That is the last/first wander *on this labelled probe*, not a sourced Agrimate freeze: author D.22 still updates q_oth and still has last/first ≈ 1. Not adopted. Do not pin. Do not write freeze_q_oth into wheat_params().

XI volume is not the last/first object: qoth_freeze still spans
137.0–234.7 MMT. The 2006–11 mean-price ratio is the D.7 offer mix under
live vs frozen D.22. Author Agrimate updates q_oth; freezing it
here is a diagnostic isolation, not a copy of the paper.
xmin_off and calendar_replan each move last/first *below* 1
(not a pin to 1). Calendar replan also zeros year-end S_p
(N2's original reason for rolling year).

Do not add a decay knob to force last/first = 1. Do not restore
L1–L8. Do not pin.

**Next paste: R5.** Item 3 remains open on the live host after
this characterisation. S4 x1=demand is the next labelled
experiment. R4 does not unlock G1.
