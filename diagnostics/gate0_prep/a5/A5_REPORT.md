# A5 — Which channel carries which crisis?

Channel ablation of the Gate 0 crisis spine (`sheaf/dynamic_crop.py`),
measured on the official scoring legs and the four robustness assertions.

**Status: measurement, not recommendation.** `default_crop_params` was not
touched; every ablation is a keyword override through `run_crop_dynamics`.
Several ablations score *better* than the official run on some crop/metric
(flagged below). Per `CLAUDE.md` those are readings off a decomposition, not
proposals — nothing here is fit to a crisis window.

Reproduce:

```bash
python scripts/scratch/a5_ablation.py     # grid + inert scan  (~22 s)
python scripts/scratch/a5_verify.py       # override landing + twin shift
python scripts/scratch/a5_ask_rival.py    # library asserts + ask_rival sweep
python scripts/scratch/a5_figs.py         # figures
```

Artifacts: `ablation_grid.csv` (headline grid), `assert_detail.csv`,
`twin_shift.csv`, `delta_scan.csv`, `ask_rival_sweep.csv`,
`ask_rival_fine_maize.csv`,
`figures/scratch/a5/fig_a5_hike_ablation.png`,
`figures/scratch/a5/fig_a5_ask_rival_sign.png`.

## Method and harness validation

- Legs: `full` = `use_amis=True, use_shocks=True, use_demand=False`;
  `shocks` = `use_amis=False, use_shocks=True, use_demand=False`.
  Window 2006–2011, `use_industrial` left at its default (`None` ⇒ on for
  maize only).
- Metrics: monthly `corr(model_price, obs_price)` against
  `load_price_series_monthly(deflated=True)`, and hike ratio = 3-month-mean
  peak / 3-month-mean base for 2006-06→2008-03 and 2009-06→2011-02.
  `_corr` and `_hike` are **imported** from
  `scripts/score_subannual_crop.py`, not reimplemented.
- **Baseline reproduces the official reports exactly** — wheat `full`
  corr `+0.720`, 2007/08 ×`2.27`, 2010/11 ×`1.45`; `shocks` `+0.400`, ×`1.20`,
  ×`1.85`; maize `+0.712` / ×`1.97` / ×`1.70`; rice `+0.678` / ×`1.72` / ×`0.82`.
  All nine baseline (corr, hike, hike) triples match
  `diagnostics/gate0_{wheat,maize,rice}_report.md` to the printed 3 digits.
  Confidence 95–100% (direct reproduction).
- Assertions: the library functions call `run_crop_dynamics` with no
  override hook, so they cannot be parameterised. `scripts/scratch/a5_ablation.py`
  transcribes L900–1013 with identical windows, floors and tolerances plus a
  `**ov` pass-through, returning `(bool, statistic)` instead of raising. At
  baseline the **unmodified library assertions all pass for all three crops**
  and the transcription agrees (`a5_ask_rival.py` §1). Confidence 95–100%
  at the default point; 80–95% that the transcription is faithful off-default
  (same code path, but only the default point is cross-validated).
- Overrides verified to land: for each ablation, the field is read back off
  `res.params` (`a5_verify.py` §1). All seven field names map to real
  `CropParams` fields (L77–138); none failed to map.

### On the efficiency note (prep rebuild) — partial correction

The instruction's reasoning is right that you must go through
`run_crop_dynamics`, but for a different reason than "the twin moves".
`simulate_prep` reads `prep.params` (L874), and there is no way to inject
params into an existing prep, so a prep cannot be reused across ablations
regardless.

Measured (`twin_shift.csv`): of the nine ablations, only
**`rebuild_lambda=0.0` actually moves the calm twin** (max |Δ`free_twin`| =
10.7 / 42.9 / 5.1 MMT for wheat / maize / rice; max |Δ`unmet_twin`| ≈ 0.41–0.50).
The other eight leave `free_twin` and `unmet_twin` bit-identical or within
3e-14. Two analytic reasons, both confirmed numerically:

1. The twin is simulated with `free_twin=None`, which pins `p_star = p0`
   (L656–658). Every price-formation knob (`trade_w`, `unmet_kappa`,
   `block_kappa`, `inv_eta`) is therefore *structurally* inert in the twin.
   `ask_alpha` is inert to 3e-14 because with `p ≡ p0`, no cuts and
   `fill ≈ ask_target_fill`, the ask update has nothing to bite on.
2. `foresight_phi` is inert in the twin *by construction*: the twin is run
   with `H_for_twin = H_seas` and `H_seasonal = H_seas`, so
   `H_exp = φ·H_seas + (1-φ)·H_seas = H_seas` for any φ (L563–565, L799–806).

So the "an ablation changes the twin too" caveat is real but applies to
exactly one of these nine parameters. Confidence 95–100% (reproduced).

## Results

Assertion columns: `twin` = `assert_twin_identity`, `τ↑p` =
`assert_amis_raises_price` (with the measured isolated-τ lift in the crop's
primary ban window), `spring` = `assert_no_spring_spike`, `cut` =
`assert_amis_cuts_exports`. Assertion runs are shock-free and
`use_industrial=False`, so they are the same for both legs.

#### wheat (observed: 2007/08 ×1.82, 2010/11 ×1.16)

| ablation | full corr | full 07/08 | full 10/11 | shocks corr | shocks 07/08 | shocks 10/11 | twin | τ↑p | spring | cut |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | +0.720 | 2.27 | 1.45 | +0.400 | 1.20 | 1.85 | PASS | PASS (+67.5%) | PASS | PASS |
| `trade_w=1.0` | +0.188 | 1.41 | 1.84 | −0.378 | 0.58 | 1.01 | PASS | PASS (+142.5%) | PASS | PASS |
| `trade_w=0.0` | +0.562 | 1.43 | 1.03 | +0.404 | 1.15 | 1.53 | PASS | PASS (+76.0%) | PASS | PASS |
| `ask_rival=0.0` | +0.685 | 1.53 | 1.52 | +0.400 | 1.20 | 1.85 | PASS | PASS (+26.9%) | PASS | PASS |
| `block_kappa=0.0` | +0.690 | 1.92 | 1.37 | +0.400 | 1.20 | 1.85 | PASS | PASS (+31.3%) | PASS | PASS |
| `unmet_kappa=0.0` | +0.684 | 2.24 | 1.45 | +0.475 | 1.17 | 1.52 | PASS | PASS (+67.6%) | PASS | PASS |
| `foresight_phi=0.0` | +0.724 | 2.28 | 1.46 | +0.408 | 1.22 | 1.85 | PASS | PASS (+67.5%) | PASS | PASS |
| `foresight_phi=1.0` | +0.721 | 2.27 | 1.43 | +0.403 | 1.19 | 1.86 | PASS | PASS (+67.5%) | PASS | PASS |
| `ask_alpha=0.0` | +0.516 | 2.29 | 0.98 | +0.570 | 1.19 | 1.33 | PASS | PASS (+133.7%) | PASS | PASS |
| `rebuild_lambda=0.0` | +0.642 | 2.13 | 1.49 | +0.426 | 1.14 | 1.57 | PASS | PASS (+112.0%) | PASS | PASS |

#### maize (observed: 2007/08 ×1.84, 2010/11 ×1.44)

| ablation | full corr | full 07/08 | full 10/11 | shocks corr | shocks 07/08 | shocks 10/11 | twin | τ↑p | spring | cut |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | +0.712 | 1.97 | 1.70 | +0.271 | 1.11 | 1.01 | PASS | PASS (+1.9%) | PASS | PASS |
| `trade_w=1.0` | +0.454 | 0.91 | 1.23 | −0.373 | 0.76 | 1.01 | PASS | **FAIL (−26.7%)** | PASS | PASS |
| `trade_w=0.0` | +0.423 | 1.57 | 1.67 | +0.246 | 1.16 | 2.13 | PASS | PASS (+34.3%) | PASS | PASS |
| `ask_rival=0.0` | +0.414 | 1.43 | 1.11 | +0.271 | 1.11 | 1.01 | PASS | **FAIL (−18.7%)** | PASS | PASS |
| `block_kappa=0.0` | +0.572 | 1.67 | 1.38 | +0.271 | 1.11 | 1.01 | PASS | **FAIL (−12.2%)** | PASS | PASS |
| `unmet_kappa=0.0` | +0.780 | 2.05 | 1.49 | +0.304 | 1.18 | 1.31 | PASS | PASS (+1.1%) | PASS | PASS |
| `foresight_phi=0.0` | +0.781 | 2.28 | 1.63 | +0.366 | 1.32 | 1.03 | PASS | PASS (+1.9%) | PASS | PASS |
| `foresight_phi=1.0` | +0.765 | 2.22 | 1.60 | +0.374 | 1.33 | 1.02 | PASS | PASS (+1.9%) | PASS | PASS |
| `ask_alpha=0.0` | +0.600 | 2.42 | 1.01 | +0.666 | 1.22 | 1.49 | PASS | PASS (+83.9%) | PASS | PASS |
| `rebuild_lambda=0.0` | +0.558 | 1.60 | 1.59 | +0.273 | 1.22 | 1.32 | PASS | PASS (+1.4%) | PASS | PASS |

#### rice (observed: 2007/08 ×1.84, 2010/11 ×0.79)

| ablation | full corr | full 07/08 | full 10/11 | shocks corr | shocks 07/08 | shocks 10/11 | twin | τ↑p | spring | cut |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | +0.678 | 1.72 | 0.82 | −0.115 | 0.93 | 1.06 | PASS | PASS (+92.4%) | PASS | PASS |
| `trade_w=1.0` | +0.751 | 2.33 | 1.00 | −0.538 | 0.67 | 0.81 | PASS | PASS (+163.1%) | PASS | PASS |
| `trade_w=0.0` | +0.249 | 0.84 | 0.41 | −0.087 | 0.89 | 0.98 | PASS | PASS (+23.9%) | PASS | PASS |
| `ask_rival=0.0` | +0.342 | 1.01 | 0.91 | −0.115 | 0.93 | 1.06 | PASS | PASS (+21.8%) | PASS | PASS |
| `block_kappa=0.0` | +0.688 | 1.38 | 0.83 | −0.115 | 0.93 | 1.06 | PASS | PASS (+66.5%) | PASS | PASS |
| `unmet_kappa=0.0` | +0.677 | 1.73 | 0.82 | −0.120 | 0.94 | 1.07 | PASS | PASS (+92.2%) | PASS | PASS |
| `foresight_phi=0.0` | +0.678 | 1.73 | 0.82 | −0.128 | 0.95 | 1.11 | PASS | PASS (+92.4%) | PASS | PASS |
| `foresight_phi=1.0` | +0.677 | 1.72 | 0.82 | −0.095 | 0.91 | 1.03 | PASS | PASS (+92.4%) | PASS | PASS |
| `ask_alpha=0.0` | +0.644 | 1.87 | 0.81 | −0.164 | 0.90 | 1.08 | PASS | PASS (+97.0%) | PASS | PASS |
| `rebuild_lambda=0.0` | +0.677 | 1.49 | 0.80 | −0.105 | 1.04 | 1.22 | PASS | PASS (+66.2%) | PASS | PASS |

### Ablations that score better than the official run (measurements, NOT proposals)

- maize `foresight_phi=0.0` corr +0.781 and `unmet_kappa=0.0` corr +0.780 vs
  baseline +0.712.
- rice `trade_w=1.0` corr +0.751 vs +0.678, and 2007/08 ×2.33 vs observed ×1.84
  (overshoot, so "better corr" and "better hike" disagree).
- wheat `foresight_phi=0.0` corr +0.724 vs +0.720 (inside noise of the metric).

None of these is a recommendation. Two of them (`trade_w=1.0` for maize,
which breaks the τ sign condition; `unmet_kappa=0.0`, which removes a
sign-constrained scarcity term) trade a scored correlation for a property
the model claims to hold. This is exactly the trade the complexity-budget
rule exists to refuse without a coauthor decision.

## The ask_rival / maize verdict

**Yes. `ask_rival=0.0` makes isolated maize export restrictions LOWER the
world price, and `assert_amis_raises_price` fails for maize.** The
isolated-τ price in the Argentina window (2007-05 → 2008-06) is
**−18.7%** below the no-AMIS path, against a floor of 0.0.

The full sweep (`ask_rival_sweep.csv`, `ask_rival_fine_maize.csv`) shows
the parameter is *pinned by that condition*, not free:

| `ask_rival` | 0.0 | 0.2 | 0.4 | 0.6 | 0.70 | 0.74 | 0.75 | 0.76 | **0.80** | 1.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| maize lift | −18.7% | −15.1% | −10.7% | −5.1% | −1.85% | −0.42% | −0.05% | +0.33% | **+1.88%** | +10.9% |
| wheat lift | +26.9% | +31.3% | +38.5% | +48.5% | +56.2% | — | — | — | **+67.5%** | +98.2% |
| rice lift | +21.8% | +33.0% | +52.0% | +78.9% | +87.3% | — | — | — | **+92.4%** | +96.9% |

Findings:

1. The zero crossing for maize is at `ask_rival ≈ 0.751` (linear
   interpolation between 0.75 → −0.05% and 0.76 → +0.33%). The default 0.80
   clears it by 0.049 in the parameter and by +1.88 pp in the statistic.
   This is a *boundary* value, i.e. roughly the least markup that satisfies
   the sign condition on a 0.01 grid — which is what the docstring at
   L118–121 claims ("0.80 is the smallest shared value at which isolated
   maize τ does not cut world price (0.40 still cuts)"). **The docstring's
   claim is reproduced**: 0.40 gives −10.7%. Confidence 95–100%.
2. **Only maize binds.** Wheat and rice satisfy their +5% floors even at
   `ask_rival = 0.0` (+26.9%, +21.8%). So the single degree of freedom
   `ask_rival` is set by one sign condition on one crop, and there is
   essentially no slack: the honest description is "one constrained
   parameter", not "one knob tuned on three crops". Confidence 95–100%.
3. `ask_rival` and `block_kappa` are **exactly** inert on any restriction-free
   path. With `use_amis=False`, `cuts ≡ 0` ⇒ `block_frac ≡ 0` (L628–631),
   so `rival ≡ 0` and the `block_kappa` term in `p_scar` vanishes (L676–677).
   Measured: the `shocks` leg is bit-identical to baseline (max |Δ| =
   0.000e+00 on corr and both hikes, all three crops) under both ablations.
   These two parameters therefore cannot manufacture a price response out of
   a harvest shock; they act only when a restriction is on. Confidence
   95–100% (analytic + reproduced).
4. `trade_w=1.0` also breaks the maize sign condition (−26.7%), and
   `block_kappa=0.0` breaks it too (−12.2%). So the maize sign condition is
   carried jointly by the rival markup *and* the blockage term in the
   scarcity price, and needs a nonzero scarcity weight to see the latter.
   Wheat and rice never fail it under any ablation run here.

Mechanism, stated plainly: an Argentine maize quota withdraws offers. On the
own-fill law alone (L632–636), the surviving exporters see *higher* fill
against unchanged demand and, through `_ask_reweight_dest`, the trade-weighted
average ask can fall — so a restriction reads as loosening. The rival markup
`exp(ask_rival · block_frac)` and the `block_kappa · block_frac` term in
`p_scar` are what make a blocked preferred source register as scarcity
rather than as slack. Maize is where this matters because Argentina is a
small share of a US-dominated export network, so the blockage is small
relative to the fill effect. Confidence 80–95% (code inspection plus the
targeted sweep; I did not decompose `p_trade` step-by-step to attribute the
fall between `fill` and the destination reweighting).

## Which channel carries which episode

Read as Δ(hike ratio) on the `full` leg vs baseline. Caveat first: the hike
ratio is peak/base, so an ablation can move it through the *base* window —
these attributions are about the ratio the scoring uses, not about a
structural variance decomposition. Confidence 80–95% on the rankings,
60–80% on any causal reading of them.

| crop | 2007/08 carried by | 2010/11 carried by |
|---|---|---|
| wheat | restriction markup — `ask_rival=0` −0.74, `block_kappa=0` −0.35; the ask/scarcity **blend** also matters (either `trade_w` corner costs ≈−0.84) | own-fill ask adaptation — `ask_alpha=0` −0.47, `trade_w=0` −0.42; restriction knobs move it little (`ask_rival=0` +0.07) |
| maize | scarcity price and the restriction terms — `trade_w=1` −1.06, `ask_rival=0` −0.54, `rebuild_lambda=0` −0.37, `block_kappa=0` −0.30 (removing foresight *raises* it, +0.31) | ask dynamics — `ask_alpha=0` −0.69, `ask_rival=0` −0.59, `block_kappa=0` −0.32, `unmet_kappa=0` −0.21; `trade_w=0` −0.03 (insensitive to dropping asks from `p*`) |
| rice | offer-price/ask channel — `trade_w=0` −0.88, `ask_rival=0` −0.71, `block_kappa=0` −0.34; `trade_w=1` *raises* it +0.61 | nothing much — observed is a ×0.79 *decline* and the model's ×0.82 is unmoved by every ablation except `trade_w=0` (0.41, which overshoots the decline) |

Consistent with the official per-crop attribution
(`gate0_*_report.md`: wheat 2007/08 restriction-led, wheat 2010/11
production-led, rice 2007/08 restriction-led, maize demand-led in both),
with two refinements this ablation adds:

- **The restriction channel is the 2007/08 channel in all three crops**, and
  it is carried by the two blockage-conditional terms (`ask_rival`,
  `block_kappa`) rather than by the quantity cut alone. Turning both off
  leaves the harvest-only path untouched (point 3 above), so the 2007/08
  hike is not being produced by a harvest shock in disguise.
- **2010/11 is an ask-dynamics episode, not a restriction episode**, for
  wheat and maize: `ask_alpha=0` is the single largest loss in both
  (−0.47, −0.69). Note wheat's `full` 2010/11 hike (×1.45) is *below* its
  `shocks` hike (×1.85) at baseline — restrictions raise the 2010 base
  window as well as the peak, which is why removing restriction knobs can
  *increase* the measured 2010/11 ratio.

## Inert parameters

**No parameter in this set is inert everywhere.** All nine ablations move at
least one crop/leg/metric well outside floating-point noise
(`delta_scan.csv`; smallest max |Δ| across the whole grid is
`foresight_phi=1.0` at 0.253, on maize 2007/08). So the honest answer to
"too many knobs" is *not* "some are dead code" — it is the decomposition
above. Confidence 95–100% for the negative claim over the ablations run;
this says nothing about the 16 `CropParams` fields not ablated here.

Two near-inert *cells*, worth recording because they are candidates for
crop-level simplification rather than removal:

| parameter | crop | max abs delta over all metrics | reading |
|---|---|---|---|
| `unmet_kappa` | rice | 0.0071 | the unmet-anomaly term does essentially nothing for rice; it is active for wheat (0.34) and maize (0.30) |
| `foresight_phi` | wheat | 0.0196 | harvest foresight barely matters for wheat; for rice 0.051; for maize 0.304 |

And three *structural* inertness results, which are the useful version of
the parameter-count answer (all analytic, confirmed numerically, confidence
95–100%):

1. `unmet_kappa`, `block_kappa` and `inv_eta` are exactly inert whenever
   `trade_w = 1` (they enter only `p_scar`, L672–678).
2. `ask_rival` and `block_kappa` are exactly inert on any restriction-free
   path (`cuts ≡ 0`).
3. `foresight_phi` is exactly inert in the calm twin and in any run where
   `H = H_seas`, since `H_exp = φH + (1−φ)H_seas` collapses (L563–565).

So the effective parameter count is smaller than 25 *conditionally*: the
calm twin that anchors `assert_twin_identity` is a function of far fewer
knobs than the treatment path, which is itself a defensible answer to the
overparameterisation criticism.

## Assertion failures

Across 30 (crop × ablation) cells × 4 assertions = 120 assertion
evaluations, **exactly three fail, all of them `assert_amis_raises_price`
on maize**: `ask_rival=0.0` (−18.7%), `block_kappa=0.0` (−12.2%),
`trade_w=1.0` (−26.7%). `assert_twin_identity`, `assert_no_spring_spike`
and `assert_amis_cuts_exports` pass in all 30 cells.

That pattern is itself informative: the quantity-side asserts (offers cut,
twin flat, no spring artefact) are robust to every price-channel ablation,
while the one *sign* assert is the binding constraint. Confidence 95–100%
(reproduced; subject to the transcription caveat above).

## Classification

| # | Finding | Class | Confidence |
|---|---|---|---|
| 1 | `ask_rival` is a constrained parameter, not a free one: pinned near 0.751 by the maize sign condition; default 0.80 has +1.88 pp margin | **H** (not an issue — the self-description at L118–121 is accurate) | 95–100% |
| 2 | `ask_rival` / `block_kappa` exactly inert on restriction-free paths ⇒ the restriction channel cannot fabricate a harvest-shock response | **H** | 95–100% |
| 3 | 2007/08 is restriction-carried in all three crops; 2010/11 is ask-dynamics-carried for wheat/maize and flat for rice | **H** (documents existing behaviour) | 80–95% |
| 4 | No parameter is globally inert; three conditional-inertness identities exist | **H** | 95–100% |
| 5 | `unmet_kappa` for rice and `foresight_phi` for wheat are near-inert; they are still nonzero and still sign-constrained | **D** (economic simplification candidate, needs a coauthor decision, not a defect) | 80–95% |
| 6 | The four library assertions cannot be run under parameter overrides — they hard-code `run_crop_dynamics(crop, ...)` with no `**overrides` pass-through (L900–1013), so any future sensitivity study must transcribe them | **G** (documentation/testability gap; the assertions are correct as written) | 95–100% |
| 7 | `prepare_crop_run` silently drops unknown keyword overrides (L720–724). `run_crop_dynamics(..., trade_weight=1.0)` returns a path bit-identical to baseline with no error — a typo'd sensitivity study silently reports the baseline | **B** (coding bug: contradicts "Pass `params=` or field overrides", L850) | 95–100% (reproduced in `a5_verify.py` §1) |

Findings 6 and 7 are reported, not patched, per the read-only ground rule.

## Adjudication of finding 1 (added by the lead reviewer, after A2)

**Finding 1 is reclassified H → F.** Not because the measurement was wrong
— it reproduces exactly — but because the test it measured was not
comparing like with like, which A5 had no way to know.

A2e/A2f found that `assert_amis_raises_price` compared an unpinned τ leg
against a baseline leg pinned at exactly `p0` by the calm branch in
`_simulate_window`, while the ask law's own quiet level is 0.66 / 0.71 /
0.96 × `p0`. The maize lift was therefore biased down by about 27 pp. The
test was repaired in commit `cafb8ba` by perturbing the baseline harvest by
1e-6, which takes it out of the matched regime so both legs share a price
law. `scripts/scratch/adjudicate_ask_rival.py` then located the crossing
under both versions:

| crop | floor | crossing, test as A5 found it | crossing, corrected test |
|---|---|---|---|
| maize | +0.00 | **0.755** | clears at 0.0 (+0.0467) |
| wheat | +0.05 | clears at 0.0 | clears at 0.0 (+0.4876) |
| rice | +0.05 | clears at 0.0 | clears at 0.0 (+0.1599) |

A5's 0.751 estimate is confirmed at 0.755 on a finer bisection, so the two
passes agree on every number they share. What changes is the reading. On the
corrected test **no crop's sign condition binds at any positive
`ask_rival`**, so the condition does not select 0.80 and the code comment
claiming it does was wrong (fixed in `cafb8ba`).

Two caveats against over-reading this in the other direction. Maize's
corrected margin at `ask_rival = 0` is only +0.047, so the condition is
nearly binding rather than comfortably slack. And `ask_rival` is not thereby
shown to be spurious — A2f measured the cost of dropping it as maize corr
+0.712 → +0.414 and rice 2007/08 ×1.72 → ×1.01 against an observed ×1.84.

The finding that survives is narrower and more awkward than either pass
alone: a parameter that materially sets crisis amplitude has no independent
justification for its value. Category **F** (empirical limitation),
confidence 95–100%. It is an open decision, not a defect to patch — see
`diagnostics/POTSDAM_RESPONSE.md` §2.

**Findings 6 and 7 are now fixed** in `cafb8ba`, after the user asked for
fixes rather than a report: `prepare_crop_run` raises `TypeError` on unknown
overrides, and all four assertions take `**overrides`. Finding 7's silent
drop is worth noting as the reason this adjudication was possible at all —
A5 caught it precisely because it verified its overrides had landed.

## What I did not do

- Did not run the `demand` or `tau` legs under ablation (out of A5 scope;
  the official attribution table already covers them at baseline).
- Did not ablate the other 16 `CropParams` fields (`inv_eta`, `smooth`,
  `ask_beta`, `ask_target_fill`, `ask_comp_elast`, `warehouse_lambda`,
  `stu_target`, `max_stu`, `residual_subst`, `elast`, `pipeline_max_steps`,
  `harvest_pulse_frac`, `seasonal_buffer_steps`, `twin_harvest`,
  `shock_mode`, `industrial_nodes`/`ind_base_years`), so the inertness
  claim is scoped to the nine run.
- Did not decompose `p_trade` to separate the `fill` effect from the
  `_ask_reweight_dest` destination reweighting in the maize sign mechanism.
- No interaction terms: every ablation is one-at-a-time, so nothing here
  bounds joint effects.
