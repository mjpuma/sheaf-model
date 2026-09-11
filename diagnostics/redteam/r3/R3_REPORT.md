# R3 — SHEAF Gate 0 expectations and process scheduling vs Agrimate

Red-team pass R3. Scope: `sheaf/dynamic_crop.py::_simulate_window` and
`prepare_crop_run`, audited against Kuhla et al. (2025) Agrimate and its
supplement (`agrimate/Kuhla_2025_Agrimate.txt`,
`agrimate/Kuhla_2025_AgrimateSupplement.txt`), and against SHEAF's own
`README.md` §8.

`sheaf/*.py` and `scripts/*.py` were **not modified**. Every prototype is an
in-memory recompilation of `sheaf/dynamic_crop.py` (technique from
`scripts/scratch/a1b_calm_fixed_point.py`).

**Harness validated first.** The baseline reproduces the briefed official
scores exactly: wheat `+0.720 / ×2.27 / ×1.45`, maize `+0.712 / ×1.97 / ×1.70`,
rice `+0.678 / ×1.72 / ×0.82`, with observed `×1.82/×1.84/×1.84` (2007/08) and
`×1.16/×1.44/×0.79` (2010/11). See `R3_02_PROTOTYPES.md`.

---

## 0. What Agrimate actually specifies (verified from source, not summary)

Everything below was read directly from the supplement, not inherited.

**Process schedule (supplement §D.3, lines 2214–2361).** Nine processes per
step, in this order — the earlier internal summary was right about the order of
the five it listed but omitted *Communication* and mis-placed *Consumption*:

1. **Harvest** (all suppliers) — supplier learns its harvest this step *and its
   expected future harvests*; storage updated for deterioration.
2. **Policy update** (suppliers, after Harvest) — supplier learns policy
   measures (export restrictions) and updates its restriction *forecast*.
3. **Sales** (suppliers, after Policy update) — fulfils demand requests from the
   *previous* step; transaction price is the *previous* step's offer price
   (Eq. D.4: \(p^{(t)}_{r\to s}=p^{(t-1)}_{\mathrm{off},r\to s}\)); storage updated.
4. **Expectation formation** (suppliers, after Sales) — profit-maximising sales
   plan over \(N_{hor}\), using (a) current + expected future harvests,
   (b) current storage, (c) expectations of others' future sales; then adjusted
   by the *expected* export restriction.
5. **Communication** (suppliers, after Expectation formation) — supplier sends
   its planned sales to rival suppliers and receives theirs; uses rivals' plans
   plus its own next-step expected sales to compute **offer prices**, which are
   sent to purchasers *for the next step*.
6. **Delivery** (purchasers) → 7. **Consumption** (consumers) →
   8. **Accounting** (purchasers) → 9. **Procurement** (purchasers) — demand
   requests are sent and received *next* step.

**Harvest expectation (supplement Eq. D.1, lines 2615–2629).** This is the
single most important thing for question (a):

\[
w_k=\frac{1}{1+\exp\!\big(\tfrac{k-N_{for}}{0.17\,\tau_{for}}\big)},\qquad
\hat H_r^{(t+k)}=w_k\,H_r^{(t+k)}+(1-w_k)\,H_r^{*(t+k)}
\]

with \(H^{*}\) the Nash-baseline (climatology) harvest and \(H\) the **realised**
harvest. Defaults (Tbl. D.1, Tbl. F.1): \(N_{year}=24\) — the same clock SHEAF
uses — \(N_{for}=N_{year}/3=6\), \(\tau_{for}=0.2N_{year}=4.8\), \(N_{hor}=24\).
So Agrimate's suppliers have **near-perfect foresight of the realised harvest
out to ~5 steps** (\(w_1=0.998\), \(w_4=0.921\)), a crossover at \(k=6\)
(\(w_6=0.50\)), and essentially none beyond \(k=9\) (\(w_9=0.025\)).

**Restriction expectation (supplement Eq. D.2, lines 2631–2656; main text
296–320).** \(\hat\Delta^{(t+k)}_r=\Delta^{(t)}_r\) iff \(\Delta^{(t)}_r>0\) and
\(\Delta^{(t+m)}_r=\Delta^{(t)}_r\) for all \(m\in[0,k]\), else 0. Confirmed:
restrictions cannot be foreseen; once imposed the issuing region's supplier
knows how long the *current phase* lasts; changes within the horizon are again
unforeseen; re-adaptation happens each time restrictions tighten or relax.

**Three stated differences from competitive storage (main text 350–357).**
Confirmed verbatim: domestic + world market in the objective; **finite
foresight horizon with expectations adapted each step "according to their gain
in information"**; oligopolistic rather than perfectly competitive markets.

---

## 1. Process-order parity table

Column "information available" is what the decision can see at the moment it
is taken.

| # | Agrimate process | SHEAF Gate 0 equivalent (`dynamic_crop.py`) | Information available to Agrimate | Information available to SHEAF | Verdict |
|---|---|---|---|---|---|
| 1 | Harvest: learn \(H^{(t)}\) and \(\{\hat H^{(t+k)}\}\) | `avail = stock + H[:, t]` (L593); `H_exp`, `H_ahead`, `lean_h` precomputed L577–586 | \(H^{(t)}\) exactly; \(\hat H^{(t+k)}\) with lag-decaying \(w_k\) | \(H^{(t)}\) exactly in `avail`; \(\phi H^{(t+k)}+(1-\phi)H^{\mathrm{seas}}\) with \(\phi\) **flat in \(k\)** | **weaker in shape, weaker in total** (see §2a) |
| 2 | Policy update: learn \(\Delta^{(t)}\), forecast \(\hat\Delta^{(t+k)}\) over phase | `cuts[:, t]` applied to current-step offers (L612); no forecast anywhere | current cut **plus** known remaining phase length | current cut only | **weaker** (see §2b) |
| 3 | Sales: fulfil last step's requests at last step's offer price (Eq. D.4) | `_bilateral_clear` on `A_eff` built from the **inherited** ask (L616–618); shipments then valued at the **updated** ask (L667) | allocation and valuation use the *same* price | allocation uses \(q_{t}\), valuation uses \(q_{t+1}\) | **defect** (see §2e) |
| 4 | Expectation formation: \(N_{hor}\) profit-max sales plan, adjusted by \(\hat\Delta\) | static residual rule \(O_{i,t}=\max(0,\mathrm{avail}-d-T)(1-\tau_t)\) (L612); \(T\) from `lean_gap` | own + rivals' expected future sales, own storage, expected restriction | own current availability, own lean gap | **weaker** (D — no intertemporal plan) |
| 5 | Communication: exchange **planned** sales, then set next-step offer prices | ask update L646–651 from own realised `fill` and aggregate `block_frac`; used at \(t{+}1\) | rivals' *planned* \(t{+}1\) sales | own *realised* \(t\) fill + aggregate realised blockage | **weaker in content, equivalent in timing** (see §2d) |
| 6 | Delivery: \(N_{del}=2\)-step shipping lag, consumer price from delivery | shipments arrive same step (`received`, L618) | 2-step delivery queue | none | **weaker** (D; Agrimate reports results insensitive to \(N_{del}\), Tbl. F.1) |
| 7 | Consumption: on consumer price and availability | `consumption = min(desired, max(0, avail - shipped + received))` (L622) | consumer price | \(p_{t-1}\) via `desired_flex` (L595) | **equivalent** |
| 8 | Accounting: update delivery queue | — (no queue) | — | — | **weaker** (D, same as #6) |
| 9 | Procurement: demand requests sent, received next step | `demand = food_need + rebuild` (L610) using \(p_{t-1}\) | offer prices received last step, storage target, future deliveries | \(p_{t-1}\), lean-gap target, safety stock | **equivalent** on the price lag; weaker on future deliveries |

---

## 2. Verdicts

### (a) Does SHEAF have look-ahead it should not have? — **NO.**

**Stated unambiguously: this is not a defect. Classification H, confidence
90–95%.**

*Claim located.* README §8 "Lean foresight and targets":
\(H^{\mathrm{exp}}_{i,t}=\phi H_{i,t}+(1-\phi)H^{\mathrm{seas}}_{i,t}\) and
\(L_{i,t}=\max(0,\sum_{k=0}^{h_t}C_{i,t+k}-\sum_{k=0}^{h_t}H^{\mathrm{exp}}_{i,t+k})\).

*Implementation located.* `_simulate_window` L577–586: `H_exp` is built once,
before the loop, from the **realised** harvest array `H` at weight
`foresight_phi` and the climatological `H_seasonal` at \(1-\phi\);
`lean_h = steps_to_harvest_pulse(H_exp, ...)`;
`H_ahead = rolling_ahead_variable(H_exp, lean_h)` sums \(t{+}1..t{+}h_t\).
So the lean gap at step \(t\) **does** read \(\phi\) of the realised future
harvest at every lag \(k=1..h_t\). Same for `C_ahead` over `C_step`, which on
the official P1 leg is mean flex plus the year-by-year US maize industrial
(RFS) block.

*Do claim and implementation match?* Yes, symbol for symbol.

*Is the realised-harvest component illegitimate?* No — **Agrimate does exactly
the same thing, and more of it.** Eq. D.1 is structurally the same blend of
realised and baseline harvest; the only difference is that Agrimate's weight
decays with lag while SHEAF's is flat. Per CLAUDE.md's reference-frame rule,
Agrimate is the standard against which Gate 0 is judged, so
realised-future-harvest information inside the forward window is legitimate in
kind. A departure would only be a defect if SHEAF used *more* of it.

*Counterexample attempt — does SHEAF use more?* Measured
(`r3_01_lookahead.py`, `r3_lookahead_summary.csv`). Summed absolute
realised-anomaly information \(\sum_k |w_k(H-H^{\mathrm{seas}})|\) inside each
step's own forward window, SHEAF vs Agrimate's schedule:

| crop | \(\phi\) | median \(h_t\) | max \(h_t\) | share of steps \(h_t>6\) | SHEAF info (MMT/step) | Agrimate info | ratio |
|---|---|---|---|---|---|---|---|
| wheat | 0.55 | 5 | 14 | 37.5% | 1.847 | 2.833 | **×0.652** |
| maize | 0.50 | 7 | 19 | 55.6% | 2.291 | 2.529 | **×0.906** |
| rice | 0.55 | 4 | 11 | 30.6% | 0.556 | 0.788 | **×0.706** |

SHEAF uses **35% / 9% / 29% less** realised-harvest look-ahead than its own
reference model. The counterexample fails.

*Correctness argument for the current implementation.* Beyond the parity
argument: (i) the realised harvest enters only through an annual multiplicative
anomaly on a climatological calendar (`_apply_harvest_scalars`), so
within-crop-year "foresight" is foresight of a *scalar that crop-condition
reporting genuinely reveals* (USDA WASDE, AMIS Market Monitor) rather than of a
month-by-month path; (ii) `lean_h` is a global harvest-calendar clock, which
farmers legitimately know; (iii) the twin/`free_twin` reference is indexed at
\(t\), not ahead of it, so it is not a second look-ahead channel.

*The one thing that is genuinely different — the SHAPE.* Because \(\phi\approx
0.5\) is flat and Agrimate's \(w_k\) is a logistic centred on \(N_{for}=6\), the
two schedules **cross at almost exactly \(k=6\)** (figure
`figures/scratch/r3/r3_fig1_lag_weights.png`). SHEAF is *under*-informed at
\(k<6\) (0.55 vs ≈1.0, the horizon where forecasts are real) and
*over*-informed at \(k>6\) (0.55 vs ≈0.0, the horizon where they are not) —
on 37.5% / 55.6% / 30.6% of steps respectively. **Classification D
(economic simplification, disclosed in README), confidence 95%.** It is not
category A or B: the formula is internally correct and the code matches it.

*Sub-finding: lag-0 incoherence.* Within one step, `avail` uses \(H_{i,t}\) at
weight 1.00 while the lean gap subtracts
\(H^{\mathrm{exp}}_{i,t}=\phi H_{i,t}+(1-\phi)H^{\mathrm{seas}}_{i,t}\) — two
different values for the *same already-realised* quantity, mean
\(|(1-\phi)(H_t-H^{\mathrm{seas}}_t)|\) = 0.81 / 0.87 / 0.18 MMT/step. README
documents it this way, so it is **D + G, not B, confidence 95%.** Measured
impact is nil: V2 (lag-0 corrected, everything else held) moves correlation by
≤0.001 and both hike ratios by ≤0.005 on all three crops.

*Noted, out of scope.* `_harvest_anomaly_scalars` LOWESS-detrends a PSD history
running to `max(years)`, so the 2006 trend estimate uses post-2006 data. This
is in-sample smoothing at data-preparation time, and Agrimate does the same
(supplement §E.5). Not a Gate 0 scheduling look-ahead. **H, confidence 80%.**

### (b) Restriction-duration knowledge — **weaker, but structurally inert.**

**Classification D/E, confidence 85%.**

Agrimate Eq. D.2 gives the issuing region's supplier the remaining length of
the current restriction phase; SHEAF's exporter sees only `cuts[:, t]`
(L612, L644, L657). So SHEAF is **strictly less informed**. Three pieces of
evidence bound how much that matters.

1. **The information is nearly degenerate in SHEAF's own AMIS data**
   (`r3_amis_phase_lengths.csv`). Phase = maximal run of a constant nonzero
   cut: wheat 17 phases, median 18 steps; maize 10 phases, median 22; rice 13
   phases, median 26. **98.7–99.7% of all cut-steps sit in phases of ≥6 steps**
   — Agrimate's whole \(N_{for}\). A supplier with Agrimate's rule would, on
   ~99% of restricted steps, expect the current cut to persist through its
   entire forecast horizon. "Knows the duration" and "assumes it persists" are
   the same statement here.
2. **The 2010/11 Russian episode specifically.** SHEAF's Russia wheat cut is
   *continuously* in force from step 44 (2007) to step 131 (2011) at levels
   {0.50, 0.95}. The announced-duration information that was public in
   August 2010 is not the missing signal in this configuration; SHEAF's Russia
   is already treated as permanently restricted across the whole crisis window.
3. **There is no channel for it.** SHEAF's exporter offer is a static residual
   rule with no intertemporal sales plan (row 4 of the parity table). Knowing a
   restriction will persist changes an Agrimate supplier's *plan*; in Gate 0
   there is no plan for it to change. Repairing (b) faithfully therefore means
   adding an intertemporal exporter optimisation, not a patch.

*Prototype anyway (V4).* Weighting each in-force cut in the block signal by
\(\min(1,(m{+}1)/N_{for})\), \(m\) = known remaining phase length,
\(N_{for}=6\) imported from Agrimate (no new free parameter): wheat corr
−0.007, maize **−0.061**, rice +0.015; 2007/08 −0.13 / −0.20 / −0.01. All 12
asserts still pass, but there is no evidence of value. **Not recommended.**

### (c) Fixed blend vs adaptive expectations — **weaker; the brief's framing needs one correction.**

**Classification D, confidence 90%.**

The brief is right that a fixed blend of climatology and realisation "is NOT
adaptive in any sense — it never learns," and `foresight_phi` is indeed a
constant. But the audit should be clear about what Agrimate's "adaptive
expectations … according to their gain in information" *is*: reading Eq. D.1,
it is the **lag-decaying weight re-evaluated at every \(t\)** — as \(t\)
advances, a given calendar date moves from \(k>N_{for}\) (climatology) into
\(k<N_{for}\) (accurate forecast), so the expectation for that date is revised
upward in accuracy every step. It is **not** a learning rate on forecast
errors, and it introduces **no learning parameter**. SHEAF's flat \(\phi\)
omits exactly this: it assigns the same accuracy to a date 1 step away and 14
steps away.

So the honest verdict is: SHEAF's expectation formation is a defensible
bounded-rationality simplification of the *level* of Agrimate's foresight (it
uses less, per §2a), but it drops the *information-gain structure* that is one
of Agrimate's three explicitly stated departures from competitive storage.
That structure is where the prototype (V1) goes.

### (d) Information-exchange round — **weaker in content, equivalent in timing.**

**Classification D/E, confidence 85%.**

Agrimate's Communication (process 5) has suppliers exchange **planned** sales
and then set the offer prices used *next* step. SHEAF's ask update (L646–651)
also runs at the end of step \(t\) and sets the ask used at \(t{+}1\), so the
*timing* is the same. The *content* is not: SHEAF's exporter sees its own
realised `fill` and an aggregate realised `block_frac`, never a rival's
intention. Two consequences: SHEAF's exporters cannot anticipate a rival's
withdrawal (only observe it one step late), and there is no individual-rival
resolution — `block_frac` is a scalar shared by all exporters. This is a real
parity gap and a real reason SHEAF's oligopoly is thinner than Agrimate's, but
nothing in the code contradicts anything in the README. Not a defect.

### (e) Internal coherence of the SHEAF ordering — **one real defect.**

**The p\(^{tr}\) double-update: classification B, confidence 95–100%.**

*Claim located.* README §8, "World price": \(p^{\mathrm{tr}}_t=\sum_i q_{i,t}\,
\mathrm{shipped}_{i,t}/\sum_i \mathrm{shipped}_{i,t}\) — the ask indexed at
\(t\). README §8 "Method of solution" lists step 5 as "ask update
\(\to q_{i,t+1}\)" and step 6 as \(p^{\mathrm{tr}}\). Under README's own
notation, \(p^{\mathrm{tr}}\) must use \(q_{i,t}\), the ask that was in force.

*Implementation located.* `_simulate_window`:
- L616 `A_eff = _ask_reweight_dest(A, ask, ...)` — allocation uses the
  **inherited** ask (recorded as `ask_path[:, t]` at L615).
- L646–651 `ask = ...` — the ask is **updated in place**.
- L667 `p_trade = float(np.dot(ask, shipped) / shipped_sum)` — the **same
  shipments** are valued at the **updated** ask, i.e. \(q_{i,t+1}\).

*They do not match.* The shipments were allocated at \(q_{i,t}\) and are priced
at \(q_{i,t+1}\). Agrimate is explicit that these must coincide (Eq. D.4:
\(p^{(t)}_{r\to s}=p^{(t-1)}_{\mathrm{off},r\to s}\) — the transaction price
*is* the offer price the demand request responded to).

*Counterexample constructed and sized* (`r3_ask_double_update.csv`,
`r3_ask_double_update_signed.csv`):

| crop | mean \|Δp\(^{tr}\)\| $/t | mean rel | max rel | **mean signed rel** | **signed rel, 2007/08 rally** |
|---|---|---|---|---|---|
| wheat | 13.08 | 3.69% | 12.7% | **+0.77%** | **+2.21%** |
| maize | 5.49 | 3.26% | 75.4% | **+0.58%** | **+2.26%** |
| rice | 30.48 | 4.56% | 27.6% | **+3.70%** | **+5.03%** |

The bias is **signed and rally-directional**: during 2007/08 the post-update
ask exceeds the pre-update ask by 2.2–5.0%, because a tightening market drives
`fill` above \(\theta\) and the exponential ask update fires *before* the same
step's shipments are valued. \(p^{\mathrm{tr}}\) enters \(p^\star\) at
\(\omega=0.70\!-\!0.80\), and \(p^\star\) feeds an AR(1) smoother, so the error
compounds along the path. This is a one-step front-run of the world price by
the ask law, not an economic mechanism.

*Correctness argument for the current code (attempted, and it partly holds).*
One can read README step 5 → step 6 as *intending* the updated ask, on the
grounds that \(q\) after the update is "this step's clearing ask." If that is
the intent, the finding is **G** (README's own \(p^{\mathrm{tr}}\) formula is
then wrong) plus a **D** concern (transactions valued at a price that did not
govern the allocation). Either way there is a documented-vs-implemented
mismatch, and Agrimate's Eq. D.4 settles which side the lineage is on. I
record the classification as **B at 95%**, with **G at 100%** as the fallback
if the coauthors state that the updated ask was intended.

*Everything else in the ordering is coherent.* Verified individually:
- `desired_flex` uses the incoming \(p_{t-1}\) (L595) — matches Agrimate, whose
  demand requests carry the previous step's offer price (Eq. D.3–D.4).
  **Equivalent, H.**
- `cuts[:, t]` hits the current step's offers (L612) — Policy update precedes
  Sales in Agrimate D.3. **Equivalent, H.**
- `ask_path[:, t]` is stored *before* the update (L615), so the recorded ask
  series is the pre-update one and `A_eff` uses the same value. **Consistent.**
- `locked` / `free` use the post-trade `stock` with the pre-trade `target`
  (L653–658) — matches README's \(\mathrm{free}_t=\sum_i S_{i,t+1}-\sum_i
  L_{i,t}-\mathrm{locked}_t\). **Equivalent, H.**
- No decision in step \(t\) reads a quantity computed later in step \(t\)
  **except** \(p^{\mathrm{tr}}\).

*Separate G finding.* README §8's notation table gives \(\phi=0.55\)
(maize 0.40); `default_crop_params("maize")` sets `foresight_phi=0.50`.
**G, confidence 100%.**

---

## 3. Prototypes and results

All from `scripts/scratch/r3_02_prototypes.py`; CSVs in this directory.
Baseline row is the validated official score.

| variant | what changes | wheat corr / 07-08 / 10-11 | maize | rice | asserts |
|---|---|---|---|---|---|
| **V0** baseline | — | +0.720 / ×2.27 / ×1.45 | +0.712 / ×1.97 / ×1.70 | +0.678 / ×1.72 / ×0.82 | 12/12 PASS |
| **V1** Agrimate Eq. D.1 expectation | lag-decaying \(w_k\) replaces flat \(\phi\), on the pulse clock, the forward window and lag 0 | **+0.729** / ×2.29 / ×1.44 | **+0.787** / ×2.26 / ×1.64 | +0.677 / ×1.72 / ×0.82 | 12/12 PASS |
| **V2** lag-0 only | full \(H_t\) at lag 0 | +0.721 / ×2.27 / ×1.45 | +0.711 / ×1.97 / ×1.70 | +0.678 / ×1.72 / ×0.82 | 12/12 PASS |
| **V3** pre-update ask in \(p^{tr}\) | `np.dot(ask_path[:, t], shipped)` | +0.680 / **×2.08** / **×1.31** | **+0.733** / **×1.84** / **×1.64** | +0.675 / ×1.55 / ×0.84 | 12/12 PASS |
| **V4** cut-duration weighting | block signal × \(\min(1,(m{+}1)/6)\) | +0.713 / ×2.14 / ×1.48 | +0.650 / ×1.78 / ×1.67 | +0.693 / ×1.71 / ×0.82 | 12/12 PASS |
| **V13** V1 + V3 | both | +0.688 / ×2.09 / ×1.31 | **+0.794** / ×2.08 / ×1.55 | +0.675 / ×1.54 / ×0.85 | 12/12 PASS |

Observed: 2007/08 ×1.82 / ×1.84 / ×1.84; 2010/11 ×1.16 / ×1.44 / ×0.79.

**Assertion impact: none. All four robustness asserts
(`assert_twin_identity`, `assert_amis_raises_price`,
`assert_amis_cuts_exports`, `assert_no_spring_spike`) pass on all three crops
in all six variants — 72 assert runs, 72 passes** (`r3_prototype_asserts.csv`).
V1 in particular does not break the twin identity, which is the non-obvious
result: the calm twin has \(H=H^{\mathrm{seas}}\) so *any* lag schedule
collapses to climatology, which is also why the briefed "\(\phi\) is exactly
inert in the calm twin" finding reproduces and extends — under V1 the whole
weight schedule is inert there too.

**V3 is the correctness fix; V1 is the parity fix.** V3 moves 5 of 6 hike
ratios toward observed (maize 2007/08 lands on ×1.84 exactly, wheat 2007/08
×2.27→×2.08 against ×1.82, wheat 2010/11 ×1.45→×1.31 against ×1.16) and costs
wheat correlation 0.040 and rice 2007/08 0.18 (away from observed). Per
CLAUDE.md the crisis windows are not a fitting target, so these numbers are
reported as the *cost of the fix being visible*, not as its justification —
which is README/Agrimate parity.

**One localised artefact the flat \(\phi\) produces** (`R3_05_BOUNDARY.md`).
Maize V0 has a 33.4% single-step price move at 2006-11 that V1 reduces to
12.8%; wheat and rice are unchanged (12.3→12.6%, 10.9→11.0%). Maize has the
longest forward window (median \(h_t=7\)), so its window is the one that
straddles the calendar-year switch in the annual anomaly multiplier
(`_apply_harvest_scalars`) at full weight \(\phi\). Mechanism is consistent
with the measurement but not proven — the per-boundary mean move is *not*
elevated for maize (1.65%), so this is one large instance, not a systematic
boundary effect. **C (numerical), confidence 70%.**

---

## 4. Falsification

`scripts/scratch/r3_03_falsify.py`. Arguing the other side on each proposal.

**"V1 gives exporters foresight they should not have."** *Partly true, and it
must be said plainly.* V1 does **not** reduce look-ahead — it *increases* the
total, from ×0.65/×0.91/×0.71 of Agrimate's to exactly Agrimate's. Anyone whose
concern is "SHEAF might see too far" should note that V1 raises the weight on
next-step realised harvest from 0.55 to 0.998. The defence is threefold:
(i) Agrimate is the stipulated reference frame and this is its published
schedule with its published defaults; (ii) the part V1 *removes* — 0.55 weight
on realised harvest 10–19 steps out — is the indefensible part, while the part
it *adds* (1–3 months) is the horizon at which crop-condition forecasting
demonstrably works; (iii) V1 changes nothing about *restrictions*, which
Agrimate insists cannot be foreseen and which V1 leaves entirely unforeseen.
**This criticism survives partially and is reported: V1 is a re-shaping toward
the source, not a reduction.**

**"An adaptive expectation adds a learning-rate parameter that buys nothing."**
*Falsified on the parameter count.* V1 adds **no** learning rate. It introduces
\(N_{for}=6\) and \(\tau_{for}=4.8\), both read off supplement Tbl. D.1/F.1, and
it makes `foresight_phi` **exactly** inert — verified: under V1, \(\phi\in
\{0.0,0.55,1.0\}\) gives bit-identical corr and both hike ratios on all three
crops (`r3_v1_phi_inert.csv`). Net free-parameter count is therefore \(-1\).

**"Would this double-count against `foresight_phi`?"** *No — demonstrated
above.* V1 replaces the blend rather than stacking on it. For contrast, \(\phi\)
is **not** inert in the shipped model, and its placement is unflattering: maize
corr is +0.781 at \(\phi=0\), **+0.713 at the shipped \(\phi=0.50\)**, +0.765 at
\(\phi=1\). The shipped default sits at a local *minimum* of maize correlation
among those three values. Reassuringly, that also shows \(\phi\) was not fitted
to maximise crisis fit; less reassuringly, it means the parameter is
load-bearing and poorly placed.

**"V1 is really just a tuned knob."** *Survives for wheat and rice, fails for
maize.* Across Agrimate's own sensitivity range (\(N_{for}\in\{3,6,9\}\),
\(\tau_{for}\in\{2.4,4.8,9.6\}\); Tbl. F.1, where Agrimate reports *no* change
in its own dynamics), SHEAF's spread is: wheat corr 0.009, rice corr 0.000 —
but **maize corr 0.281**, driven entirely by \(N_{for}=9\) giving +0.513, i.e.
*worse* than the V0 baseline. So V1's maize gain holds at \(N_{for}=3\) (+0.785)
and 6 (+0.787) but reverses at 9. **This criticism partly survives: V1 is
robust for wheat and rice and parameter-sensitive for maize, and that must be
disclosed rather than smoothed over.** It is also most of the reason V1 is not
my single recommendation.

**"Most of V1's benefit is available for free."** *This one lands.* Setting
\(\phi=0\) in the shipped model — one default change, no new machinery — gives
maize +0.781 vs V1's +0.787, capturing ~92% of the correlation gain. So V1's
*marginal score value* over a one-line default change is small. Its remaining
value is structural (parity with Agrimate's stated departure from competitive
storage, and removal of a free parameter), not numerical.

**"The p\(^{tr}\) finding is just a naming quibble."** *Falsification
attempted and it does not survive.* If it were a naming issue the numerical
effect would be second-order; measured, the signed rally-window bias is
+2.2 to +5.0% on a quantity carrying \(\omega=0.70\!-\!0.80\) of \(p^\star\),
and correcting it removes 8–10% of wheat and rice 2007/08 amplitude. A 19-point
change in wheat's headline hike ratio is not a quibble. The strongest
surviving counter-argument is the interpretive one in §2e (README's step
ordering could be read as intending \(q_{i,t+1}\)), which changes the
classification from B to G but not the fact of the mismatch or its size.

---

## 5. Complexity budget

Against all ten axes in CLAUDE.md.

| axis | **V3 (recommended)** | V1 (second) | V4 (rejected) |
|---|---|---|---|
| scientific benefit | removes a one-step front-run of the world price; restores README's own \(p^{tr}\) and Agrimate Eq. D.4 | restores Agrimate's stated information-gain structure (one of its three named departures from competitive storage) | none measured |
| computational cost | zero (one array already materialised) | ~2 Python loops over \(T{\times}h_t\) at prepare time | one \(O(n\,N_{for})\) scan per step |
| calibration burden | **none** | **negative**: \(\phi\) deleted, \(N_{for},\tau_{for}\) imported from source | none (\(N_{for}\) imported) |
| interpretability | improves: transaction price = allocation price | improves: "forecast reach", not an opaque blend weight | neutral |
| new parameters | **0** | **−1 net** (+2 sourced, −1 free) | 0 |
| new state variables | **0** | 0 | 0 |
| runtime cost | **0%** | +≈8% of a 3-crop score (~10 s → ~11 s) | +≈5% |
| continuity with lineage | **closer** (Eq. D.4 exactly) | **closer** (Eq. D.1 exactly, same 24-step clock, same defaults) | closer in letter, but the information is degenerate in SHEAF's data |
| publication benefit | high: pre-empts the obvious referee question "why is your transaction price not the price the trade responded to?" | moderate: lets §8 say "Agrimate's Eq. D.1 with its published defaults" instead of defending a free \(\phi\) | low |
| verdict | **passes decisively** | **passes, with the maize \(N_{for}\) sensitivity disclosed** | **fails** |

V1's runtime and the maize sensitivity are the only real costs, and the
sensitivity is the reason it is second rather than first. V4 fails the budget
on scientific benefit alone.

---

## 6. Recommendation

**One change: value the step's shipments at the ask that allocated them.**
In `_simulate_window`, compute \(p^{\mathrm{tr}}_t\) from `ask_path[:, t]`
(the pre-update ask) rather than from the in-place-updated `ask` — i.e. move
the \(p^{\mathrm{tr}}\) computation above the ask update, or index the stored
pre-update ask.

- **Classification: B (coding bug)** — the implementation does not do what
  README §8's \(p^{\mathrm{tr}}\) formula says, and Agrimate Eq. D.4 is
  explicit that the transaction price is the offer price the demand request
  responded to. Fallback classification **G** at 100% if the coauthors state
  that \(q_{i,t+1}\) was intended, in which case README's formula is the thing
  to change.
- **Confidence: 95%** — directly reproduced and quantified (signed rally bias
  +2.2%/+2.3%/+5.0%; corrected variant runs clean on all 12 asserts). Not 100%
  because the README's step-5-before-step-6 ordering leaves the *intent*
  arguable, not the mismatch.
- **Complexity budget: passes on every axis** — zero new parameters, zero new
  state, zero runtime, moves SHEAF closer to Agrimate.
- **Cost, stated openly:** wheat correlation −0.040 and rice 2007/08 −0.18;
  5 of 6 hike ratios move toward observed. Not a fitting argument in either
  direction.

**Secondary, warranted but not urgent:** adopt Agrimate Eq. D.1 (V1) in place
of the flat `foresight_phi`, disclosing the maize \(N_{for}\) sensitivity. This
answers (a), (c) and the lag-0 incoherence at once and *removes* a free
parameter. Defer if the coauthors prefer the smaller footprint of simply
re-examining \(\phi\), since \(\phi=0\) captures ~92% of V1's maize gain.

**Not recommended:** V4 / restriction-duration knowledge (no measured value,
information degenerate in SHEAF's AMIS phases, and a faithful version needs an
intertemporal exporter sales plan) and any change based on the lag-0
incoherence alone (measured impact ≤0.001 correlation).

---

## 7. Artifacts

Scripts (`scripts/scratch/`): `r3_01_lookahead.py`, `r3_02_prototypes.py`,
`r3_03_falsify.py`, `r3_04_signed_and_figs.py`, `r3_05_maize_spike.py`.

Reports (this directory): `R3_01_LOOKAHEAD.md`, `R3_02_PROTOTYPES.md`,
`R3_03_FALSIFY.md`, `R3_04_SIGNED.md`, `R3_05_BOUNDARY.md`.

CSVs: `r3_lookahead_summary.csv`, `r3_lookahead_lagweights.csv`,
`r3_prototype_scores.csv`, `r3_prototype_asserts.csv`,
`r3_v1_nfor_sensitivity.csv`, `r3_v1_phi_inert.csv`,
`r3_ask_double_update.csv`, `r3_ask_double_update_signed.csv`,
`r3_amis_phase_lengths.csv`, `r3_boundary_artefact.csv`.

Figures: `figures/scratch/r3/r3_fig1_lag_weights.png`,
`figures/scratch/r3/r3_fig2_price_paths.png`.

**What was run vs what was reasoned.** Run: harness validation against the
three official baselines; the look-ahead information measurement; all six
prototype variants with full score and 72 assert runs; the \(N_{for}\)/
\(\tau_{for}\) sensitivity grid; the \(\phi\)-inertness test; the signed and
unsigned \(p^{tr}\) gap; AMIS phase-length statistics; the boundary-artefact
measurement. Reasoned (not executed): the Agrimate process-order and equation
extraction (read from the supplied text, cited by line); the claim that
crop-condition forecasting is empirically reliable at 1–3 months; the
attribution of the maize 2006-11 artefact to the calendar-year anomaly switch
(consistent with, but not proven by, the measurement); the judgement that
repairing (b) requires an intertemporal exporter sales plan.
