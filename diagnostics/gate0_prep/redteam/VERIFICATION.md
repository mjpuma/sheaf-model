# Verification of commit `929cec4` (CES origin competition)

Independent check of the Agrimate-redteam synthesis pass. Not a re-run of
the red team. Reproduce: this file plus
`python scripts/score_subannual_crop.py --crop {wheat,maize,rice}`.

## Verdict

**The CES fix is correct and the claimed official scores reproduce.** Do
not revert it. Do not adopt the exporter FOC. Deck not touched.

## A. Destination reweighting was dead code — **pass** (H on the algebra; B on the pre-fix claim)

Commit `929cec49`. Live law in `sheaf/dynamic_crop.py`:

- `_ask_reweight_dest` L508–521 still multiplies each destination row by
  \(r_i=(p_0/q_i)^\gamma\) and renormalises the row.
- `_ask_reweight_src` L524–537 (new) multiplies each source column by the
  same \(r_i\) and renormalises the importer.

Algebra. Let \(r_i\) be constant along exporter \(i\)'s row. Then

\[
\tilde A_{ij}
= \frac{A_{ij}\,r_i}{\sum_k A_{ik}\,r_i}
= \frac{A_{ij}\,r_i}{r_i\sum_k A_{ik}}
= A_{ij}
\]

whenever the row is not identically zero. Direct check: random
row-stochastic \(A\), \(\max|\tilde A-A|=2.8\times10^{-16}\). Census
`cen04_reweight_noop.json` and R2 already had the same identity
(\(\max|A_{\mathrm{eff}}-A|\sim10^{-16}\)). Category **B** on the
pre-fix documentation (the note, `ask_comp_elast`, Agrimate-Eq.-8c
analogue all claimed cheaper origins gained share). Confidence **95–100%**.

The dest call is still in `_simulate_window` L645 and
`dynamic_coupled.py`; it is a no-op, kept for callers. Harmless (**H**).

## A continued. New law is the CES origin-mix FOC — **pass**, scoped (H, 95–100%)

Expenditure min of a CES aggregator over origins gives quantity shares

\[
\tilde S_{ij}
= \frac{S_{ij}\,q_i^{-\gamma}}{\sum_k S_{kj}\,q_k^{-\gamma}}
= \frac{S_{ij}(p_0/q_i)^\gamma}{\sum_k S_{kj}(p_0/q_k)^\gamma}.
\]

`_ask_reweight_src` is exactly that (column-normalised). A CES price index
in the denominator cancels after renormalisation, so using \(p_0\) rather
than importer \(j\)'s CES index does not change the mix. Direct check:
`max |S_eff − hand FOC| = 0`; cheapest origin gains share, dearest loses.

This is Agrimate Eq. 8c *lower tier* (purchaser source mix), which R2 had
already identified as the intended object and as applied to the wrong
matrix. It is **not** Agrimate's nested CES-with-budget, and \(\gamma=1.25\)
is not Agrimate's \(\sigma=2\). Clearing remains
`min(O A, S_eff D)` plus residual pool. Category **H** that the shipped
channel is the CES origin-mix FOC; **D** remainder vs the full Agrimate
purchaser. Confidence **95–100%** / **80–95%**.

## B. Twelve asserts — **pass** (12/12)

Re-run `assert_twin_identity`, `assert_amis_raises_price`,
`assert_amis_cuts_exports`, `assert_no_spring_spike` on wheat, maize,
rice. All raise-free. Confidence **95–100%**.

## B. Official full-leg scores — **pass** (9/9 at printed precision)

`run_crop_dynamics(..., use_amis=True, use_shocks=True, use_demand=False)`,
2006–2011, `_corr` / `_hike` imported from
`scripts/score_subannual_crop.py`. Live numbers match the committed
`diagnostics/gate0_*_score.csv` bit-for-bit.

| crop | corr claimed | live | 07/08 claimed | live | 10/11 claimed | live | result |
|---|---|---|---|---|---|---|---|
| wheat | +0.728 | +0.727608 | ×2.28 | 2.283611 | ×1.45 | 1.452988 | **pass** |
| maize | +0.778 | +0.778054 | ×2.20 | 2.202916 | ×1.59 | 1.592104 | **pass** |
| rice  | +0.678 | +0.678356 | ×1.72 | 1.721260 | ×0.82 | 0.820520 | **pass** |

Pre-fix (foc_scores `mode=ask`, same helpers): wheat +0.719861 / 2.267 /
1.447; maize +0.711534 / 1.972 / 1.699; rice +0.677741 / 1.722 / 0.820.
Rice and wheat 2010/11 are unchanged at the printed three digits.
Maize moved because the twin is rebuilt under the same law (CES is inert
only when all asks equal \(p_0\); on the twin, asks still differ by fill).
Not a retune. Confidence **95–100%**.

Letter supporting number, also reproduced: `ask_rival=0` maize corr
**+0.520235** (claimed +0.520); rice 2007/08 **×1.014** (claimed ×1.01).

## C. Letter / synthesis overreach

These do **not** contradict A1–A3 on the calm pin (25/34/19%), the lost
`ask_rival` justification (clears at 0, maize +4.7%), the τ attribution
flip (maize ×1.09 pinned → ×1.69 like-for-like), or the \(p^{\mathrm{tr}}\)
fallback (≤12 $/t). Those match the earlier measurements.

Overreach / staleness:

1. **FOC endpoints mixed (G).** Synthesis FOC table is internally
   consistent on the *pre-CES* ask law: maize +0.712 → +0.339
   (`foc_scores.csv` `mode=foc`). The letter and `DEVELOPMENT.md` write
   +0.78 → +0.34, which is post-CES CES-ask start and pre-CES FOC end.
   Like-for-like with CES kept is `foc+ces` maize **+0.468**. Qualitative
   rejection stands either way. Exporter FOC was **not** shipped (diff is
   only `_ask_reweight_src`).
2. **"Parity" with Agrimate sourcing (D, not H if read as identical).**
   Same channel class (price-responsive origin mix). Not the same
   elasticity, not a purchaser budget, not CES clearing.
3. **Newsvendor \(10^{5}\)–\(10^{6}\) (G, mild).**
   `cover_newsvendor.csv`: rice ratios are \(10^{5}\)–\(10^{6}\); wheat /
   maize USA-scale ratios are \(10^{1}\)–\(10^{2}\). Still not a
   competitive-storage optimum. A4 implied-carry sign flip (~40–55%
   negative \(r\)) supports the "coin-flip of signs" sentence.
4. **A5 / census / residual pool were measured pre-CES.** A5 baselines
   are +0.720 / +0.712 / +0.678. Census `cen03` still records
   `ask_comp_elast` as exactly inert. Residual shares 12 / 4 / **47%**
   (`clr_residual_pool.csv`) were not re-measured after the fix. The
   restriction-led 2007/08 claim is still the like-for-like τ column in
   the new per-crop reports (wheat ×2.00, maize ×1.69, rice ×1.70);
   A5 itself was not re-run.
5. **Stale docs (G).** `GATE0_PARAMETERIZATION.md` §2.4 and
   `GATE0_FLOWS.md` still describe destination-share reweight
   \(\tilde A\). Not updated here.

Missing write-up, not a missing finding: **A4** has CSVs only
(`gate0_prep/a4/`); no `A4_REPORT.md`. A1 and A5 reports exist and the
letter's use of them is consistent.

## D. Specialist artifacts vs synthesis

No markdown reports under `redteam/{optimisation,clearing,census}/` —
only CSVs/JSON. No contradiction that would reverse the CES ship or the
FOC reject.

- Census `cen04` and opt `reweight_noop.csv`: dest identity. Agrees.
- Clearing `clr_u1_mechanism.csv`: source-reweight prototype (U1) is the
  object that shipped. Two-sided unmet and tatonnement prototyped, not
  adopted. Agrees.
- Opt `summary_best_configs.csv`: higher-corr ω configs exist (wheat
  +0.80, maize +0.82). Synthesis correctly did not retune. Agrees.
- Opt `foc_scores.csv` `mode=ces` maize +0.712: monkeypatch CES
  *without* rebuilding the twin. Live code does rebuild; official maize
  +0.778 is the right number. Not a disagreement once that is named.
- A3 report: gap 0.3–0.9% of desired use after dropping spin-up; letter
  compresses the 4% maize 2007/08 max. Inclination "record, do not
  adopt" agrees.

## E. `DEVELOPMENT.md`

CES ship and FOC reject were already in the "Red team vs Agrimate"
section. The **Now** table still had A3/A4/A5 as "running". Updated:
A3/A5 done, A4 measurements-done / write-up open, RT row for the CES
fix and the tested-and-rejected exporter FOC. Deck still deferred.

## Classification summary

| Claim | Class | Confidence |
|---|---|---|
| Dest reweight is the identity; `ask_comp_elast` was inert | H (algebra); B (pre-fix docs) | 95–100% |
| `_ask_reweight_src` is the CES origin-mix FOC | H (scoped); D vs full Agrimate purchaser | 95–100% / 80–95% |
| Twelve asserts pass | H | 95–100% |
| Nine printed official scores | H | 95–100% |
| Exporter FOC prototyped, not shipped, costs the crisis | H (decision); G (letter's mixed endpoints) | 95–100% / 80–95% |
| Letter vs A1–A3 (pin, rival, τ flip, \(p^{\mathrm{tr}}\) fallback) | H — no contradiction | 95–100% |
| Storage still the Agrimate gap | D/E, as synthesised | 80–95% |
