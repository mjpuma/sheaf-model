# A4 — what the cover rule is doing that an Euler condition would not

Read-only measurement. `sheaf/*.py` and `scripts/*.py` untouched; everything
here comes from `scripts/scratch/a4_storage.py` and the CSVs already in
this directory. No storage law is proposed.

Official scored path: `run_crop_dynamics(crop, start_year=2006, end_year=2011,
use_amis=True, use_shocks=True, use_demand=False)` — 144 steps.

Reproduce:

```bash
python scripts/scratch/a4_storage.py
```

Artifacts: `implied_carry.csv`, `implied_carry_summary.csv`,
`offer_price_scatter_stats.csv`, `floor_country_table.csv`,
`floor_decomposition.csv`, `floor_probes.csv`, `reconstruction_check.csv`,
and `figures/scratch/a4/`. The script also writes `target_binding.csv`;
that file is **not** in the tree (missing CSV, noted below).

**Status: measurement, not recommendation.** The cover rule stays
\(T = L + s\). This pass sizes the implied carry, locates the exporter
floor, and records whether the rejected China-maize experiment is
reproducible.

## 0. Reconstruction (prerequisite)

The scratch copy of the storage partition
(`avail = S + H`, `desired` at lagged \(p\), \(T = L + s\),
\(O = \max(0, \mathrm{avail}-d-T)(1-\tau)\)) reproduces `res.offers`
to machine precision (`reconstruction_check.csv`):

| crop | max\|Δoffers\| MMT | n | T | `stu_target` | `max_stu` |
|---|---|---|---|---|---|
| wheat | 0.0 | 18 | 144 | 0.20 | 0.28 |
| maize | 0.0 | 18 | 144 | 0.16 | 0.18 |
| rice  | 0.0 | 18 | 144 | 0.18 | 0.22 |

The implied-\(r\) and floor numbers below are therefore numbers on the
shipped cover rule, not on a transcription of it. Confidence **95–100%**.

## Printable paragraph (what the cover rule is and is not)

Gate 0 holds grain because a lean-season cover target \(T = L + s\)
withholds it from the offer, not because an Euler condition says the
expected capital gain beats the carry. \(L\) is the gap from expected
harvest to expected use over the steps to the next harvest pulse;
\(s = \mathtt{stu\_target}\times C^{\mathrm{ann}}\) is one world
stock-to-use times domestic annual use. Everything above \(T\) after
food/feed/industrial use is offered, then cut by \(\tau\). There is no
interest rate, no \(E[p]\), and no commercial store-versus-sell agent.
That is a TWIST-like stylised hold — TWIST put stocks inside the
clearing condition as schedules, not as a decision (Schewe, Otto and
Frieler 2017) — one step simpler than Agrimate's finite-horizon
commercial supplier, who chooses sell versus store from expected profit
after policy is known (Kuhla, Kubiczek and Otto 2025). It is not
Deaton–Laroque competitive storage, and Deaton–Laroque is not the
lineage test.

## 1. Implied \(r\) (Task 1)

On every (country, step) where the cover holds at least 0.05 MMT and
some other country has at least 0.05 MMT of unmet purchase demand, solve

\[
q_{t+1} = (1+r)\,q_t
\]

for the per-step implied return, using the realised next ask as a
perfect-foresight stand-in for \(E_t[q_{t+1}]\). (The same inversion on
the world price is in the CSV as `implied_r_step_world`; medians below
are on the ask.) Physical carry of \(1.5\) $/t per step and a 5%/yr
reference rate are **not** model parameters; they only label
`implied_r_step_ask_carry` and the convenience-yield columns.

Pooled withholding country-steps (`implied_carry.csv`, 5 234 rows):

| crop | n | median \(r\)/step | p10 | p90 | min | max | share \(r<0\) | share \(r\) below carry | ask-clip share |
|---|---|---|---|---|---|---|---|---|---|
| wheat | 1969 | 0.000 | −0.041 | +0.059 | −0.089 | +0.181 | 0.46 | 0.54 | 0.07 |
| maize | 1641 | +0.0077 | −0.030 | +0.035 | −0.096 | +0.826 | 0.35 | 0.52 | 0.00 |
| rice  | 1624 | 0.000 | −0.040 | +0.041 | −0.092 | +0.342 | 0.44 | 0.64 | 0.23 |

A 5%/yr reference is \(r \approx 0.0020\) per step. Median implied \(r\)
is at or below that for wheat and rice, slightly above it for maize, and
the sign is a coin-flip: 35–46% of withholding steps have a *negative*
perfect-foresight return. Country-level `share_r_negative`
(`implied_carry_summary.csv`) spans 0.38–0.68 (wheat), 0.28–0.51
(maize), 0.26–1.00 (rice). Dropping ask-clip artefacts does not repair
the sign: wheat no-clip share negative 0.48, maize 0.35, rice 0.52.

By episode, wheat is the clearest illustration that the cover is not an
arbitrage: calm median \(r = -0.010\) (share negative 0.61); 2007/08
median \(+0.021\) (share negative 0.23). The rule withholds in both
regimes.

Named exporters, median \(r\)/step and share negative:

| crop | country | n | median \(r\) | p10 | p90 | share \(r<0\) |
|---|---|---|---|---|---|---|
| wheat | USA | 140 | 0.000 | −0.047 | +0.078 | 0.44 |
| wheat | Canada | 140 | −0.002 | −0.043 | +0.069 | 0.53 |
| wheat | Australia | 136 | +0.002 | −0.051 | +0.066 | 0.40 |
| maize | USA | 95 | +0.008 | −0.034 | +0.072 | 0.32 |
| maize | Argentina | 95 | −0.001 | −0.050 | +0.083 | 0.51 |
| maize | China | 93 | +0.010 | −0.037 | +0.035 | 0.31 |
| rice | India | 143 | 0.000 | −0.049 | +0.041 | 0.36 |
| rice | Thailand | 142 | 0.000 | −0.050 | +0.040 | 0.42 |
| rice | Vietnam | 133 | 0.000 | −0.045 | +0.045 | 0.44 |

The maize max \(+0.83\)/step is a one-step ask jump, not a carry; p90
across maize countries is \(+0.02\) to \(+0.08\). Nothing in the
distribution is a stable 5%/yr required return.

**Classification.** The cover rule's implied shadow value is inconsistent
with a storage Euler on the scored path. That is **D** (disclosed
target-stock heuristic, not a miscoded FOC) relative to Agrimate's
commercial supplier, **E** relative to Deaton–Laroque (wrong lineage
test). Confidence **95–100%** on the numbers; **80–95%** that an Euler
would not *fix the scores* — A4 does not score an Euler prototype; that
is the red-team FOC pass, which costs the crisis
(`foc_scores.csv`, see `redteam/optimisation/REDTEAM_OPTIMISATION.md`).

## 2. Offers against \(\Delta p\) (Task 2)

Scatter of offers on \(p_{t+1}-p_t\), pooled and seasonally adjusted by
step-of-year fixed effects (`offer_price_scatter_stats.csv`):

| crop | subset | n country-steps | corr raw (country) | corr seas-adj (country) | corr raw (world) | corr seas-adj (world) |
|---|---|---|---|---|---|---|
| wheat | pooled | 2574 | −0.13 | −0.28 | −0.38 | −0.65 |
| wheat | 2007/08 | 792 | −0.09 | −0.10 | −0.25 | −0.52 |
| wheat | calm | 1026 | −0.22 | −0.05 | −0.62 | −0.15 |
| maize | pooled | 2574 | ~0 | −0.06 | ~0 | −0.17 |
| rice | pooled | 2574 | −0.04 | +0.01 | −0.12 | +0.02 |

This is descriptive, not decisive. Cover covaries with the harvest
calendar by construction (\(L\) is a lean-season object), so a raw
negative correlation of offers with next-step price changes can be the
calendar, not an arbitrage failure. The Frisch–Waugh seasonal adjustment
does not flip wheat's sign. Competitive storage would put *holdings*,
not offers, on expected appreciation; the scatter is offered because
that is the diagnostic the sitting named. **H** on the measurement;
**D** that it is not an Euler test. Confidence **80–95%**.

## 3. Lineage (Task 3)

Order as `CLAUDE.md` requires: TWIST → Agrimate → SHEAF Gate 0. Deaton–
Laroque is not the first benchmark.

| Model | What storage actually is | Source in-repo |
|---|---|---|
| TWIST (Schewe et al. 2017) | Two stocks inside \(S(P)=D(P)\). Schedules, not a decision. No \(E[p]\), no discount, no deadband. TWIST did not solve a storage Euler | README lineage sentence; `GATE0_DISCUSSION.md` §4; phase-1 storage note (TWIST reconstructed, not re-derived from the paper here) |
| Agrimate (Kuhla et al. 2025) | Commercial supplier: finite-horizon expected-profit NLP, policy known *before* sell-vs-store. Strategic storage is a different agent (partial-adjustment refill) | `GATE0_DISCUSSION.md` §6; `GATE0_FLOWS.md` S4; synthesis scorecard |
| SHEAF Gate 0 | Cover \(T=L+s\); leftover offered. No \(r\), no \(E[p]\), no commercial agent | `sheaf/dynamic_crop.py` (reconstruction above); this directory |

Gate 0 is continuous with TWIST's stylised hold and discontinuous with
Agrimate's commercial supplier. That is **E** (design intent), and it is
the remaining Agrimate gap the letter names. Confidence **80–95%** on
the Agrimate description (from the in-repo citation of the paper, not a
fresh derivation of their NLP); **95–100%** that Gate 0 has no Euler.

## 4. Exporter safety-floor leftover

Three candidate causes, which the note currently does not distinguish:
(a) the cover rule itself, (b) one world `stu_target` on domestic use,
(c) the offer equation selling the whole surplus above \(T\).

Median model/PSD stock at the USDA local MY-end month, `psd_stock > 1`
MMT (`floor_country_table.csv`):

| crop | thin (floor) | fat |
|---|---|---|
| wheat | Australia 0.12, Canada 0.15, USA 0.27 | China 1.73, India 2.06 |
| maize | Argentina 0.28 | China 2.79, Brazil 3.28, EU 3.41, Ukraine 4.33 |
| rice | USA 0.09, Indonesia 0.65 | India 1.44, Vietnam 5.95 |

Additive split of \(\log(S/S^{\mathrm{PSD}})\) at that month
(`floor_decomposition.csv`):

\[
\log\frac{S}{S^{\mathrm{PSD}}}
= \log\frac{S}{T}
+ \log\frac{T}{s}
+ \bigl[\log\sigma - \log\mathrm{STU}^{\mathrm{PSD,totuse}}\bigr]
+ \log(1 - \text{export share}).
\]

The last two pieces are the world-`stu_target` × domestic-use
construction. Wheat exporters:

| country | \(\log(S/S^{\mathrm{PSD}})\) | below \(T\) | lean | target level | domestic-only base | export share |
|---|---|---|---|---|---|---|
| Canada | −1.91 | −0.53 | 0 | −0.22 | **−1.17** | 0.69 |
| Australia | −1.86 | −0.42 | 0 | −0.20 | **−1.19** | 0.70 |
| USA | −1.32 | −0.32 | 0 | −0.41 | **−0.66** | 0.48 |

Lean is zero at the scored month for those three: they rest at \(s\),
not at a lean-season \(L\). The largest piece is domestic-only base
(safety on \(C^{\mathrm{ann}}\), while PSD STU is on total use including
exports). Maize Argentina is the same pattern (domestic-only −1.16,
export share 0.69). China maize is the opposite of a floor:
\(\log(S/T) = +1.47\) (stocks ~4× the cover target) with almost no
exports (share 0.006), so leftover that nobody takes stays in the
country.

Diagnostic probes, none of them a proposed default (`floor_probes.csv`):

| probe | wheat USA | wheat Canada | wheat Australia | maize China | maize Argentina |
|---|---|---|---|---|---|
| baseline | 0.27 | 0.15 | 0.12 | 2.79 | 0.28 |
| `stu_target` +0.10 (`max_stu` held) | 0.40 | 0.25 | 0.16 | 2.99 | 0.32 |
| both +0.10 | 0.41 | 0.25 | 0.20 | 2.98 | 0.38 |
| both ×2 | 0.56 | 0.37 | 0.29 | 3.23 | 0.45 |
| offer damp 30% (uniform synthetic cut) | 0.32 | 0.24 | 0.36 | 3.66 | 0.90 |
| REBASE: \(s_i = \sigma\times(\mathrm{dom}+\mathrm{exports})\) | **0.55** | **0.60** | **0.60** | 2.83 | **1.10** |
| S3: \(s_i =\) PSD country STU \(\times\) dom use | **0.84** | **0.71** | **0.75** | 2.78 | 0.52 |

**Cause, distinguished.** The thin-exporter leftover (USA/Canada/Australia
wheat; Argentina maize) is caused primarily by **one world `stu_target`
applied to domestic use only** (b), and secondarily by
**offer-everything-above-\(T\)** (c). REBASE, which keeps the cover rule
and the world STU but multiplies total use, does most of the lifting.
A 30% synthetic offer cut — the clean probe of (c) — moves USA wheat
only 0.27 → 0.32. Raising the cover *level* without changing the
domestic-only base (the +0.10 and ×2 rows) helps less than REBASE.
The cover rule is the object they rest at; the missing Euler is not
the cause of the floor. China maize is fat *above* \(T\), so a higher
cover or a store-versus-sell FOC is aimed at the wrong mechanism there.

Classification **H** on the three-way split (direct decomposition plus
labelled probes). Confidence **80–95%**. `target_binding.csv` (share of
steps offering / at \(T\) / short) was written by the script and is
absent from this directory, so the step-level binding shares are not
reproduced here.

## 5. The rejected China-maize experiment (Task 4)

`GATE0_PARAMETERIZATION.md`, `GATE0_DISCUSSION.md` (S3), and
`GATE0_FLOWS.md` all assert that a country-specific price-responsive
hold was tried and rejected: it helped USA wheat and fattened China
maize ~×3. **No CSV or script in the tree records that experiment as
stated.**

What A4 *does* record, and is reproducible, is the S3 *shape* probe
(country STU from PSD × domestic use), not a price-responsive hold:

- USA wheat 0.27 → 0.84. The "helped USA wheat" clause is reproduced.
- China maize 2.79 → 2.78. Already ~×2.8 at baseline (local MY-end in
  `floor_country_table.csv`; parameterization leftover already names
  ~×2.8). S3 does not fatten it further.
- Doubling world `stu_target` and `max_stu` takes China maize to 3.23,
  which is the ~×3 *level*, as a different probe, not as the rejected
  hold.

So the sitting-era rejection survives as a remark. Closest reproducible
object: S3 country STU, which does the USA-wheat half and not the
China-maize fattening half, because China is already fat. A distinct
price-responsive hold (hold more when \(p\) is low) is not in
`gate0_prep/`. Category **F**, confidence **95–100%** that the
experiment is not in the measurement record; **80–95%** that S3 as
coded here is not that experiment.

Do not revive S3 from this file. The letter already treats storage as
the remaining Agrimate gap; A4's job is to say *which* storage object
is the gap (the missing store-versus-sell decision, not the exporter
floor's world STU, and not an unreproduced China hold).

## Classification summary

| Claim | Class | Confidence |
|---|---|---|
| Reconstruction of offers is exact | H | 95–100% |
| Implied \(r\) is a coin-flip of signs; not a 5%/yr carry | D (vs Agrimate commercial); E (vs Deaton–Laroque) | 95–100% |
| Offer–\(\Delta p\) scatter is descriptive | H / D | 80–95% |
| Lineage is TWIST stylised hold, not Agrimate NLP, not Deaton–Laroque | E | 80–95% / 95–100% |
| Exporter floor is world STU × domestic use, then offer-the-residual; not the missing Euler | H | 80–95% |
| China-maize price-responsive hold is only in prose | F | 95–100% |
| Cover-rule paragraph above is what the code does | H | 95–100% |

No change to `sheaf/*.py`. Complexity-budget: do not adopt an Euler or
clone Agrimate's supplier from this measurement. The FOC that would
close the Agrimate gap was prototyped on the ask law and rejected on
scores (`REDTEAM_OPTIMISATION.md`).
