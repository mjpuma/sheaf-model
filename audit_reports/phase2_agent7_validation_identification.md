# SHEAF Audit — Phase 2 Agent 7: Validation Methodology & Parameter Identification

Standalone report. Scratch code in `/tmp/sheaf_audit_agent7/` (e01–e07). Read-only against the repository throughout.

---

## Part A — Terminological classification (summary)

| VALIDATION.md item | What it actually is | Not |
|---|---|---|
| **Level 1** (L14–21): observed anomalies + observed τ, match Agrimate's published targets | **In-sample reproduction / cross-model benchmarking** — and only *validation* if no parameter is adjusted to hit the targets (unstated) | hindcast in the strict sense; out-of-sample |
| **Level 2** (L23–29): anomalies only, game on, "score against history" + "calibrating the food-security weights and price triggers so the game reproduces the observed cascade" | **Calibration / parameter tuning**, with in-sample fit reported | "endogenous prediction" (its own heading) |
| **Bonus** (L31–35): rice substitution test | Genuine out-of-sample test *if* rice policy params are held fixed | currently unspecified |

Level 2's own sentence contains both halves of a circle: fit to the cascade, then score the cascade.

---

## FINDING 1 — Level 2 is circular as written

**Classification:** F (primary), G (secondary). **Severity:** High. **Confidence:** 95–100% (document text + demonstrated below).

**Evidence:** VALIDATION.md:28–29 makes fitting `fs_weight`/`p_target` to the observed cascade "the scientific contribution"; L26–27 then scores "the right restrictors… roughly the right timing/severity, and the right prices" from the same run. README:242–243 asserts in the present indicative that these parameters "are calibrated so the game endogenously reproduces the historical restriction cascade" — no calibration routine exists anywhere; `calibration.py:36–98` holds hand-entered `fs_w`/`pt` with `INF` sentinels.

**Contamination map.** Fitted, therefore carrying no independent information: (i) identity of restrictors; (ii) restriction magnitude; (iii) restrictors' *domestic* prices — `p_target` **is** the domestic price target, and the optimum is essentially "restrict until p ≤ p̄" (shipped Russia: p̄=265, realised p=260.03). Conditionally informative: world/importer price magnitude, within-episode timing, and cross-grain spillover — but only if τ magnitudes are *not* also fit, which VALIDATION.md:26 says they are.

**Falsification attempted:** "prices are a separate output, so they still test the model." **Result: fails.** Model output is a deterministic function of τ; within each τ-equivalence class the world wheat price spread is **0.00e+00** (E02, 63 parameter points). Conditional on the fitted τ, price is a consequence of the fit, not a prediction.

**Recommended action:** Declare a fitted/held-out partition *before* fitting. Fit on: restrictor identity + magnitude, wheat + maize only. Hold out: rice restriction behaviour, non-restricting importers' price response, cross-grain spillover. Report the *identified set*, not a point calibration. Rewrite the Level 2 heading from "prediction" to "calibration"; soften README:242–243 to the subjunctive.

**Complexity budget:** Zero new parameters/state/runtime. Purely a reporting discipline. High publication benefit (converts an unfalsifiable claim into a stated set).

**Changes expected published results:** Yes — the headline "SHEAF predicts who restricts" becomes "SHEAF admits a parameterisation consistent with the observed cascade."

---

## FINDING 2 — `fs_weight`/`p_target` are demonstrably non-identified on the fitted margin

**Classification:** F. **Severity:** High. **Confidence:** 95–100% (direct reproduction).

**Economic mechanism:** Φ = w·(p−p̄)₊². The one-sided quadratic is a *target-hitting* device: above a threshold w, the government restricts until p ≤ p̄ and w drops out of the solution entirely. `core.py:332`, grid at `core.py:340`.

**Numerical reproduction (E02, Russia wheat, demo Black Sea shock, `game_grid=7`):**
- 63 distinct (w, p̄) pairs → **6** distinct model outputs. Within each class the wheat price spread is exactly **0.00e+00**.
- Class containing the shipped calibration: **10 members**, w ∈ [1.0, 30.0] (30×), p̄ ∈ [230, 265].
- Binary observable "who restricts": only **2** distinct values over the entire plane.
- Plateau: rows w = 9, 14, 20, 30 identical for every p̄ — `fs_weight` wholly unidentified above ≈9.
- Sharp margin: at w=6, p̄ 280→300 (7%) flips Russia from restricting to not.
- E03: (w=30, p̄=270) vs shipped (w=6, p̄=265) gives **max|diff| = 0.0** across price, consumption, net_export, availability, export_tax, stocks, importer/exporter price, total_trade — 12 periods × 17 countries × 3 grains, bit-identical.

**Falsification attempted (E07):** "this is an artifact of the coarse 7-point τ grid."
**Result: partially succeeds, main claim survives.** At `game_grid=13` (τ step 10) the 10 members separate into **3** distinct τ vectors; at `game_grid=25` (step 5), into **5**. So exact bit-identity *is* a grid artifact. But at both refinements the **binary observable — the thing VALIDATION.md proposes to score — remains 1/10 distinct**, and the world wheat price spread across the whole class is **1.20 $/t (grid 13) / 1.24 $/t (grid 25)**, i.e. **1.7% of the 72 $/t shock signal**. Non-identification of the fit target is not a grid artifact.

**Recommended action:** See Finding 4 (pooling). Minimally: report the identified set (63 runs ≈ 7 min for one country).

**Complexity budget:** Reporting only; no new parameters. Favourable.

**Changes expected published results:** Yes — no point estimate of `fs_weight` is defensible; only intervals/sets are.

---

## FINDING 3 — A second crisis episode adds almost no identifying information

**Classification:** F. **Severity:** High. **Confidence:** 90–95% (reproduced on synthetic 2010/11 analogues, not the real forcing — which the repo cannot supply).

**Numerical reproduction (E06):** Take the 10 parameter vectors indistinguishable on episode 1 (Russia −40%, Ukraine −50%), then run episode 2:
- Ep2 (RUS −33%, UKR −15%): splits **10 → {9, 1}**.
- Ep2b (RUS −33% only): splits **10 → {6, 4}**.

A second crisis eliminates at most 40% of the candidate set (≈1.3 bits). Note also that the *shipped* calibration (w=6, p̄=265) is the single member that predicts **no** restriction under the ep2 analogue — a train/test exercise would reject the shipped point calibration while accepting 9 alternatives indistinguishable from it on episode 1.

**Falsification attempted:** "the two episodes differ in mechanism (Agrimate: 2007 production-led, 2010/11 restriction-led — VALIDATION.md:17–18), so they should be informative." **Result: the mechanism differs, but the *identifying* variation does not** — the same countries (Russia, Ukraine) restrict in both, so the same (w, p̄) cells are exercised twice at different shock magnitudes.

**Recommended action:** Do not describe any two-episode exercise as "cross-validation" and never report a standard error from it. Report it as two directional hold-out exercises with the surviving-set size stated.

**Complexity budget:** Zero cost. **Changes results:** Yes — bounds how strongly any train/test claim can be stated.

---

## FINDING 4 — 28 free policy parameters vs. ≤28 binary observations; the obstacle is the parameterisation, not the data

**Classification:** F. **Severity:** High. **Confidence:** 90–95% (exact parameter count; observation count from AMIS scope reasoning).

**Evidence:** `fs_weight`/`p_target` are per-(country, grain) (`core.py:170–171`, stacked `core.py:405–406`). E04 count: **14 exporter–grain pairs → 28 free policy parameters**; plus 16 `mkt_gamma`, 11 `mkt_cost`, 18 government params, 13 demand/freight, 10 global scalars ≈ **96 hand-set numbers total**. The Level-2 observable is 14 exporter-grain pairs × 2 episodes = **28 binary cells**, mostly zeros.

**Consequence:** leave-one-country-out is *structurally impossible* in the naive form — the held-out country's (w, p̄) is unconstrained by training, so its prediction is whatever prior you plug in, not a test.

**Recommended action (the single highest-value change I identify):** **Pool the policy parameters.** E.g. p̄_{i,g} = α_g · p0_g (common tolerated markup) and w_{i,g} = ω · s_{i,g} (grain g's share of i's staple consumption, already in `calibration.py` as `cons`). That is **~4 free parameters instead of 28**, and it makes LOCO meaningful (fit on 15 countries, predict the 16th) and the model falsifiable.

**Complexity budget:** Strongly favourable on every axis — *fewer* parameters, lower calibration burden, more interpretable, no new state, no runtime cost, moves toward TWIST/Agrimate parsimony, and a fitted structural relationship is itself a publishable result whereas 28 hand-set numbers are not.

**Changes expected published results:** Yes — likely degrades in-sample fit but is the only route to a defensible out-of-sample claim.

---

## FINDING 5 — Neither Level 1 nor Level 2 is executable with the repository's data; world-aggregate forcing is non-identifying *in principle*

**Classification:** F (with a minor G). **Severity:** High. **Confidence:** 95–100% (data inventory verified; structural argument is deductive).

**Data inventory (verified):** USDA = **world aggregate only**, 3 crops, 4 variables (`data/usda_world/`, `data_usda.py:33`). FAOSTAT = **wheat only**, 3 windows, and those are **2-year averages** (`Wheat_Avg_2006_2007E0.csv`) — `list_windows('rice')` and `list_windows('maize')` both return `[]`, despite `data_faostat.py:27–28` stating the crisis windows "exist for wheat, rice, and maize" (true upstream, not of the vendored sample — minor **G**). **No price series and no AMIS restriction timeline anywhere.** VALIDATION.md:71–81 is honest that 3 of its 4 required inputs are missing; README §7 is not.

**Structural argument:** with world-aggregate forcing, ξ^g_i is *identical across i*. Therefore all cross-sectional variation in "who restricts" comes from time-invariant baseline heterogeneity and the free policy parameters — the forcing contributes **zero** cross-sectional information, and because the heterogeneity is time-invariant the same countries restrict in every stressed year. Per-country PSD is not a refinement; it is the only source of exogenous cross-episode variation.

**Numerical reproduction (E04/E05):** driving SHEAF with the repo's own world anomalies (wheat 2006 −4.08%, 2007 −2.48%, 2010 −4.05%) applied uniformly produced restrictions only in 2010 {Russia, Ukraine} and 2012 {Russia, Ukraine, Argentina} — **missing 2007/08 entirely and producing a false positive in 2012**.

**Falsification attempted:** "the 2-year-average FAOSTAT windows still capture rerouting." **Result: fails** — averaging a pre-crisis with a crisis year cannot resolve within-crisis rerouting; single-year matrices are needed (available upstream).

**Positive check (H, 95–100%):** VALIDATION.md:57's Egypt claim reproduces exactly — Russia's share of Egyptian wheat imports **37.3% → 45.7% → 52.4%** across the three windows. This is a genuine *data* validation. `validate_forcing.py`, by contrast, shades crisis windows and prints anomalies but performs no comparison against any target — despite its name and VALIDATION.md:45–46's "checks it against both crises" (**G, low**).

**Recommended action:** Acquire per-country PSD, the AMIS timeline, single-year FAOSTAT matrices, and a deflated price index before any Level-1/Level-2 claim. Rename/re-scope `validate_forcing.py` as a diagnostic.

**Complexity budget:** Data acquisition only. **Changes results:** Yes — no hindcast result currently exists to change.

---

## Part D — Feasible validation designs (assessment)

| Design | Verdict |
|---|---|
| Train 07/08 → test 10/11 | Feasible only with missing data. Weak: n=1 test episode, ~5 binary predictions, surviving set shrinks 10→6 at best (E06). |
| Train 10/11 → test 07/08 | Worse — smaller training set (Russia, Ukraine only); India/Vietnam rice params would be unconstrained by training, so "prediction" would be prior-driven. |
| Leave-one-crisis-out, n=2 | Mathematically two splits with one training observation each. **Not cross-validation.** Never report a CV standard error. |
| Leave-one-country-out | **Impossible as parameterised** (Finding 4). Becomes meaningful only after pooling. |
| **Held-out grain (rice)** | **Best available genuine out-of-sample test**, and the one only SHEAF can run. Fit wheat+maize, hold rice params at the pooled prior, check whether the rice restriction and price spike emerge. Caveat: 2007/08 rice was panic-driven; SHEAF has no consumer-expectations channel, so a failure would be ambiguous. Needs rice network + per-country rice PSD (not vendored). |
| **Parameter sensitivity / identified set** | **Feasible today, zero new data.** E02/E03 are a working prototype. This is the *minimum* the paper must contain. |
| Posterior / pseudo-posterior | **Not appropriate — recommend against.** The likelihood is a step function of the parameters (63 points → 6 outputs); with ≤28 binary observations and 28 free parameters, any credible interval would be prior-driven and carry no coverage. It would manufacture false precision. Report the identified *set* instead. Defensible only *after* pooling to ~4 parameters. |

---

## Part E — Recommended metrics

1. **World price** — RMSE/MAPE on the *shock-induced deviation* (shocked − no-shock counterfactual) vs. the deflated observed deviation from its LOWESS trend (machinery exists, `data_usda.detrend_anomalies`). Report an "amplitude ratio" (model dev / observed dev) as a single judgeable number. Use deviations, not levels — E04 shows large model-internal price drift.
2. **Domestic prices** — **do not score restrictors' domestic prices** (pinned by p̄). Score the *price wedge* (world − domestic), which is the actual insulation mechanism (Martin & Anderson 2012, already cited), plus non-restricting importers' prices. Correlation + RMSE across countries.
3. **Production** — not a model output (`core.py:425`, exogenous). State this; do not score.
4. **Consumption** — % deviation vs. LOWESS trend; **sign-agreement rate + Spearman rank correlation** across countries (levels are calibration-dependent).
5. **Stocks** — sign agreement + RMSE on Δ(stock-to-use) (`data_usda.stock_to_use`), computed on shocked-minus-counterfactual so any shock-independent drift cancels.
6. **Trade rerouting** — cosine similarity (or 1 − ½·L1) between model and FAOSTAT importer-source share vectors, and more usefully the *change* across windows. Requires single-year matrices.
7. **Who restricts** — precision/recall/F1 **plus Matthews correlation or balanced accuracy** (28 cells, ~6–9 positives — raw accuracy is meaningless). Report the confusion matrix, an exact (Fisher) p-value, and the score of a trivial baseline ("top-3 wheat exporters restrict") that the model must beat.
8. **Timing** — annual resolution only (VALIDATION.md:19–21 concedes this): |onset year error| and duration error, reported as a ~6-row table, not a summary statistic.
9. **Magnitude** — score the *implied export-quantity cut* (1 − X_model/X_counterfactual) against AMIS/Agrimate's ban ≈95% / tax ≈50% mapping (VALIDATION.md:6–8), **not** τ (unobservable, incommensurable units). Include grid discretisation in the error budget.
10. **Cross-grain spillover (the headline differentiator)** — **substitution attribution ratio** R_g = [Δp_g(σ>0) − Δp_g(σ=0)] / Δp_wheat(σ>0). This is fig1_coupling.png as a number. Measured (E05): at shipped σ=0.6, **R_rice = 26.4%, R_maize = 14.2%**, scaling near-linearly (σ = 0/0.2/0.4/0.6/0.8/1.0 → R_rice = 0.0/8.2/17.0/26.4/34.8/43.9%). Empirical counterpart is a one-sided bound: observed rice/maize deviation in a wheat-shock year, net of their own production anomalies (available in-repo), must be ≥ R_g × observed wheat deviation.

---

## FINDING 6 — `subst_scale = 0.6` is unsourced and the headline result is monotone in it

**Classification:** F/G. **Severity:** Medium. **Confidence:** 95–100% (reproduced).

**Evidence:** `calibration.py:120` hard-codes `subst_scale = 0.6` with no citation; `RHO` (`calibration.py:22–24`) likewise. README:240–241 claims (ε, ρ) "come from the demand-system literature." **Numerical (E05):** R_rice rises monotonically 0.0 → 43.9% as σ goes 0 → 1. So "substitution materially changes outcomes" is currently a statement about one hand-set number.

**Falsification attempted:** "σ is disciplined by the diagonal-dominance rescale, so it can't be arbitrary." **Result: fails** — the rescale bounds PD, not magnitude; σ=1.0 runs fine and roughly doubles the reported spillover.

**Recommended action:** Cite ε and ρ to source, or report R_g as a function of σ (a one-line sensitivity band) rather than a point number. **Complexity budget:** zero cost, high credibility gain. **Changes results:** Yes — the headline spillover becomes a band, not a number.

---

## Part F — Minimum evidence for the two strongest claims

**Claim 1 — endogenous game beats Agrimate's exogenous restrictions.**
Would require: (a) SHEAF, given only production anomalies, classifies restrictors better than a stated null ("top-k exporters restrict" / "whoever restricted last time"); (b) resulting prices at least as accurate as Agrimate's published hindcast, which had restrictions handed to it; (c) policy parameters not fitted to the test episode.
**Currently shown:** no — no hindcast is run at all.
**Currently showable:** **no, and not merely for want of data.** A 28-parameter policy layer fitted to ≤28 binary cells cannot outperform anything at a standard a referee should accept. Acquiring AMIS + per-country PSD would *not* fix this. Pooling to ~4 parameters (Finding 4) makes it testable with the same data. Honest first-paper fallback: state it as a **capability** claim plus the identified set.

**Claim 2 — substitution materially changes outcomes vs. the σ=0 limit.**
The §6 limiting-case proposition is a *mathematical* statement about the model, and demo.py exhibits it correctly — I reproduced exactly 0.00 rice/maize deviation at σ=0 (E05). Reporting "SHEAF reduces to G independent single-commodity models at σ=0; the deviation at our calibration is R_rice = 26%, R_maize = 14% (band 8–44% over σ ∈ [0.2, 1.0])" is honest, checkable, and **acceptable for a first paper as a mechanism demonstration**.
What is *not* defensible without historical grounding is the stronger claim that single-commodity models are materially wrong about the world (README:27–28 currently asserts reviewers "rightly object that this overstates price spikes" — an empirical conclusion the paper does not have; **G, medium**). That test is close to reach: the repo already has rice/maize world production anomalies for both crisis years; it needs only one additional public dataset (a deflated grain price index).

---

## Open / unresolved

- Ep2/ep2b in E06 are *synthetic* 2010/11 analogues, not the real forcing (which the repo cannot supply) — Finding 3's magnitude is illustrative, its direction is structural.
- I did not independently verify Phase 1's S5 (storage drift) or S7 (autarky drain); the large baseline price swings in E04 are consistent with S5 but I treated them only as a reason to score deviations rather than levels.
- Joint identification across *multiple* countries' (w, p̄) simultaneously was not swept (only Russia, with others at shipped values); the reported non-identification is therefore a lower bound on the true dimensionality of the identified set.
