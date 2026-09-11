# Red team / census — parameter discipline, expectations, identification

Adversarial pass on the sitting's "too many parameters" and "hard bounds
would give similar behaviour," plus what expectation Gate 0 actually
forms. Read-only on `sheaf/*.py`. Measurements live in this directory;
scripts under `scripts/scratch/redteam_cen_*.py`. Adjudication is
`../REDTEAM_SYNTHESIS.md`.

CES origin-share reweight is already shipped. Census Jacobians and the
hard-bound scores below are **pre-CES** (`cen03` still records
`ask_comp_elast` as exactly inert). The hard-bound claim is a statement
about the partial-adjustment knobs, not about Armington, so the
qualitative rejection does not depend on CES; the maize +0.71 → +0.22
number is the pre-CES CSV.

## Probe map

| Script | Artifact | Question |
|---|---|---|
| `redteam_cen_01_expectations.py` | `cen01_expectations.csv`, `cen01_lead_profile.csv`, `cen01_summary.json` | What \(H^{\mathrm{exp}}\) is; Agrimate-equivalent \(\phi\); adaptive EWMA |
| `redteam_cen_02_parsimony.py` | `cen02_parsimony.csv`, `cen02_summary.json` | Pooling ladder; hard bounds |
| `redteam_cen_03_identification.py` | `cen03_pairs.csv`, `cen03_norms.csv`, `cen03_jacobian_h010.csv`, `cen03_summary.json` | Collinear knobs; SVD rank |
| `redteam_cen_04_reweight_noop.py` | `cen04_reweight_noop.json` | Dest reweight identity (same fact as opt_01) |

## 1. Expectations are not ten-year foresight

`cen01_lead_profile.csv`. The cover reads \(H^{\mathrm{exp}}\) forward
over the lean window. Mean lead 5.8 / 8.0 / 5.1 steps (wheat / maize /
rice), not 10 years. Share of reads with lead \(\le 6\) steps: 0.79 /
0.51 / 0.84. Agrimate-equivalent \(\phi\) over those leads:
**0.75 / 0.48 / 0.80** against shipped 0.55 / 0.50 / 0.55.

`cen01_expectations.csv`. Round-trip injection of \(H^{\mathrm{exp}}\)
matches baseline bit-for-bit (`round_trip_max_abs = 0` in
`cen01_summary.json`). Static \(\phi \in \{0,1\}\) moves wheat by at
most 0.016 on any official metric. Maize is the active crop: climatology
belief (\(\phi=0\)) lifts 2007/08 +0.30; Agrimate-equivalent \(\phi\)
lifts it +0.27. Adaptive EWMA, the sitting's "stay close unless new
info": worst maize move 0.41 (theta=0.35), which is a retune, not a
defect of the blend. Rice is inert to \(\phi\) at printed precision.

Category **D** (close enough; different kernel, same clock). Confidence
**95–100%**. Synthesis's "at most 0.41 on their probe metric" is the
maize EWMA theta=0.35 cell.

## 2. Hard bounds do not reproduce official scores

Sitting claim (b): "if you have a lot of constraints you get similar
behaviour even with thin expectations" — testable as replacing the three
partial-adjustment gains with their 0/1 corners.

`cen02_parsimony.csv`, arm `hard_bound`, official maize corr +0.7115:

| variant | wheat corr | maize corr | rice corr | maize 2007/08 |
|---|---|---|---|---|
| R0 current | +0.720 | **+0.712** | +0.678 | ×1.97 |
| \(\lambda=1\) (import demand jumps) | +0.745 | +0.547 | +0.655 | ×1.63 |
| \(\lambda_W=1\) (stock hard-clip) | +0.495 | +0.284 | +0.708 | ×2.09 |
| \(\rho=0\) (no price smoothing) | +0.773 | +0.521 | +0.570 | ×2.22 |
| **all three hard bounds together** | +0.633 | **+0.219** | +0.597 | ×1.35 |
| \(\lambda=0\) (no rebuild) | +0.642 | +0.558 | +0.677 | ×1.60 |
| \(\lambda_W=0\) (no capacity) | +0.772 | +0.693 | +0.747 | ×2.04 |

Letter and synthesis: maize corr **+0.71 → +0.22** with all three hard
bounds. Reproduced (`0.2185` in the CSV). Material by the pre-declared
rule (\(|\Delta\mathrm{corr}|>0.05\) or \(|\Delta\mathrm{hike}|>10\%\)):
17 of the hard-bound cells are material (`cen02_summary.json`). The
quantity-side asserts still pass in the all-three row; the knobs are
doing work on the *scores*, not on whether \(\tau\) cuts offers.

Category **H** — their hard-bounds claim is false. Confidence
**95–100%**.

Pooling ladder (same CSV, arm `pooling`): sharing `block_kappa` and
`foresight_phi` is free. Forcing unit-elastic \(\eta\) is material for
maize (−0.15 corr). Sharing \(\omega=0.75\) is material for maize
(−0.23). Sharing STU parameters is not free in general, but R5
(shared \(\sigma^{\mathrm{stu}}=0.18\)) happens to be inside the
tolerance for maize. Deepest free rung that stays inside tolerance on
all three crops is not R6. Category **F** (identification / pooling),
not a defect of the equations.

## 3. Three collinear pairs; `ask_comp_elast` was the dead knob

`cen03_summary.json`, Jacobian of nine official metrics on 18 continuous
`CropParams`, central difference \(h=0.10\):

Stable collinear pairs (\(|\cos|\ge 0.95\) at both \(h=0.10\) and 0.20):

| pair | \(\lvert\cos\rvert\) at \(h=0.10\) |
|---|---|
| `ask_alpha` ~ `ask_target_fill` | 0.961 |
| `block_kappa` ~ `ask_rival` | 0.989 |
| `max_stu` ~ `warehouse_lambda` | 0.980 |

Norms at \(h=0.10\): `trade_w` 4.52 (largest), then `smooth` 2.35,
`ask_target_fill` 2.23, `inv_eta` 2.21, `ask_rival` 2.21.
**`ask_comp_elast` norm = 0** — exactly inert, the dest-reweight
identity. After CES that knob is live; this Jacobian was not re-run.

SVD: 7 of 9 directions capture 99% of metric variance at \(h=0.10\)
(condition 44). The scored data cannot tell 18 knobs apart. The live
identification issue the letter names is `ask_rival` ~ `block_kappa`,
not the dead Armington elasticity.

Category **F** on collinearity of `ask_rival` with `block_kappa`;
**H** that `ask_comp_elast` was inert pre-CES; **B** on pre-fix docs
that claimed it did Armington work. Confidence **95–100%** pre-CES.

## 4. Dest reweight, again

`cen04_reweight_noop.json`: `max_abs_A_eff_minus_A = 2.22e-16`,
`exact_noop_confirmed: true`. Same fact as `optimisation/reweight_noop.csv`.
Category **H**. Confidence **95–100%**.

## What is missing

- Post-CES Jacobian. `ask_comp_elast` is no longer inert; whether it is
  collinear with `ask_rival` or `block_kappa` is not in this directory.
- No fifth census script. Four experiments, four artifacts, closed.

## Classification summary

| Claim | Class | Confidence |
|---|---|---|
| Leads are 5–8 steps; Agrimate-equivalent \(\phi\) 0.75/0.48/0.80 | D | 95–100% |
| Hard bounds together: maize +0.71 → +0.22 | H (claim is false) | 95–100% |
| Three collinear pairs; `ask_comp_elast` was dead | F / H / B | 95–100% pre-CES |
| Dest reweight identity | H | 95–100% |

No change to `sheaf/*.py`. The honest answer to "too many parameters"
is not that some are dead (only `ask_comp_elast` was, and it is not).
It is that three pairs are unidentified and the partial-adjustment
gains are load-bearing.
