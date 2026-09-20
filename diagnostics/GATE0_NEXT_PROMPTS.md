# Gate 0 next development (post-R)

**Where:** this file. Living next-paste:
[`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md).
R-queue menu (exhausted): [`GATE0_REPRO_PROMPTS.md`](GATE0_REPRO_PROMPTS.md).

The R-science first-match table is **exhausted** on this host. G0-P stays
**not accepted.** Remaining gaps are **labelled**, not open R-experiments:

| Gap | Status on live host | What S-queue does |
|---|---|---|
| **A8** mean-of-members | **S1 implemented** (China H 112.7 / EA 3.31) | live host is member-sum |
| **Item 3** wander | last/first **1.444** vs author 1.004; labelled; no sourced D.22 | **S2 done**; freeze not adopted |
| **A1** USDA quantities | **S3 done** (FBSH H/C vs member-sum; China 1.00; moy worsened; not adopted) | USDA stays default; never FAO ΔS as S |
| **A7** cannot-set | FAO cleaned FB reconstruction labelled (not adopted); EU28+Egypt / start-2000 still absent | **S4** inventory; do not invent Egypt |

Do not walk R8…R12 as science. R8 may piggyback tests. R11 stays skipped
while `wheat_params()` are unchanged. R12 / S6 only after items 1–3 move.
Do not open G1/G2.

## Why S1 before item 3

Pass rule: DEVELOPMENT items 1–3 before judging 5. Item-3 sourced freeze
is a **dead end** (R4: `qoth_freeze` 1.019 vs author 1.004; author D.22
still updates `q_oth`; pinning forbidden). Diagnosing last/first on a
0.50× China node is the wrong host. S1 is a data-adapter change (R7
already has the USDA numbers), not a parameter fit. **S2 labelled**
item 3 at 1.444 on the member-sum host; freeze still not sourced.

## Adaptive rule (after each S-session)

Rewrite `GATE0_REPRO_DISPATCH.md` in ≤20 lines from **that run’s
numbers**. Next session pastes **Next paste**, not `S{n+1}`.

Choose **Next paste** from this table, in order, first match wins:

| If the last run showed… | Next paste | Skip |
|---|---|---|
| `prepare_wheat` still `groupby.mean()` | **S1** | do not re-measure item 3 on the 0.50× China node |
| S1 shipped; last/first not re-measured on the new host | **S2** | do not pin; do not write `freeze_q_oth` into `wheat_params()` |
| Item 3 re-measured; author cleaned FB still absent | **S3** | do not treat FAO ΔS as stocks; do not copy 2015–21 FTN |
| A1 left USDA; FAO/EU28 arrays still missing | **S4** | do not invent Egypt; Fig. 4 knobs stay on the comparison object |
| Host data adapter changed (S1) and scores are stale | **S5** | not a forbidden R11 (`wheat_params` unchanged) |
| Live items 1–3 evidence actually changed | **S6** | G1 |
| Tests would still pass a *non*-match | R8 may piggyback | do not weaken identities |

Hard stops do not adapt. L1–L8, 2006 pin, Bai αI=10, maize/rice
acceptance, G1/G2, and **FAO ΔS as stocks** stay off.

## Shared preamble (prepend to every S-prompt)

```
You are continuing SHEAF Gate 0 wheat: an independent Agrimate copy
(Kuhla et al. 2025; sheaf/agrimate/). Read diagnostics/GATE0_CONTRACT.md,
diagnostics/DEVELOPMENT.md, diagnostics/GATE0_VALIDATION.md,
diagnostics/GATE0_REDTEAM.md, diagnostics/GATE0_DATA.md,
diagnostics/GATE0_NEXT_PROMPTS.md, and this prompt's "Read first"
files before editing.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not restore L1–L8 (fill-target, calm pin, scarcity blend, ask_rival).
- Do not pin the unforced world price to the 2006 mean.
- Do not retune αI, p_sto, xmin, or λ to Pink Sheet or to Bai's α_foreign=10.
- Do not treat maize/rice as an acceptance target.
- Author AgrimateParams stay the defaults. Bai's fitted knobs are
  alternatives, not ours. Fig. 4 knobs (αI=3.5, ζ=1, N_for=6) belong
  on a named comparison object, not in wheat_params().
- Do not treat FAOSTAT FBSH Stock Variation (element 5074) as a stock
  level. Only USDA ending_stocks are S.
- Disabled G1 must recover this single-crop run; disabled G2 must recover
  E.4 AMIS. Those tests are later, not this prompt.
- If claim and code diverge, follow the verification protocol in CLAUDE.md
  (locate claim, locate code, counterexample, correctness argument) before
  changing economics. Data adaptations stay labelled in GATE0_DEPARTURES.md.

Exit: pytest tests/agrimate; if you touch the runner, re-run
PYTHONPATH=. python scripts/run_agrimate_validation.py and update
diagnostics/gate0_agrimate/. One prompt, one PR-sized change.
Rewrite diagnostics/GATE0_REPRO_DISPATCH.md from this run (≤20 lines).
Next session pastes that file's **Next paste**, not the next integer.
```

## Status

| ID | Prompt | Status |
|---|---|---|
| P0–P12 | Original Gate 0 queue | **done** (G0-P **not accepted**) |
| R1–R7, R9, R10 | R-science | **done** (labelled; host economics unchanged) |
| R8 | Honest Fig. 4 *score* tests | housekeeping; piggyback, not a science gate |
| R11 | Default three-scenario re-run | **skip** unless `wheat_params()` change (forbidden) |
| R12 | Methods note v2 | wait for items 1–5; use **S6** |
| **S1** | A8 member-sum `prepare_wheat` adapter | **done** |
| **S2** | Item 3 re-measure on S1 host | **done** (1.444 labelled; freeze not adopted) |
| **S3** | A1 after A8 (USDA S only) | **done** (FBSH not adopted; China H 1.00; moy 20.1×→33.0×) |
| **S4** | A7 cannot-set inventory | **next** |
| S5 | Re-score Fig. 4 / hindcast on new host | after adapter change |
| S6 | G0-P methods v2 | only if live items 1–3 changed |
| — | G1 / G2 | **blocked until G0-P accepted** |

---

## S1 — A8 member-sum host adapter (done)

```
[SHARED PREAMBLE]

Task S1 only. Switch prepare_wheat 2007–09 baseline from
groupby(region).mean() to member-sum (same construction as
psd_regional_annual(): sum PSD members within year, then mean over
2007–09). This is the approved A8 data adapter in GATE0_DEPARTURES.md,
not a parameter fit.

Read first: GATE0_DEPARTURES.md A8, a8_sum.md, regional.md,
sheaf/agrimate/wheat_data.py (H_ann / C_ann / X_ann / M_ann / S_ann),
tests/agrimate/test_regional.py, test_a8_sum.py.

Do:
1. USDA PSD ending_stocks only for S. Never FAOSTAT FBSH ΔS
   (element 5074) as a stock level.
2. Keep anomaly construction on the already-summed member series
   (wheat_data.py groupby region+year production.sum).
3. Re-run PYTHONPATH=. python scripts/run_agrimate_validation.py
   (2003–11 three scenarios) and update diagnostics/gate0_agrimate/.
   Also report 2006–08 harvest+AMIS hike and undisturbed last/first.
4. Update GATE0_DEPARTURES A8 to implemented. Update tests that lock
   mean (test_regional, test_a8_sum host_still_uses_mean, notes).
5. Do not retune αI, p_sto, xmin, or λ. wheat_params() stay 14022004
   (αI=3.2, ζ=0, N_for=3). Do not pin. Do not restore L1–L8.
6. Do not adopt FBSH. Do not start G1/G2.

China 2007–09 USDA (R7): H/C/S mean 56.4/53.6/23.3 → sum 112.7/107.1/46.6.
Eastern Africa: 0.33/0.66/0.055 → 3.31/6.55/0.55. USA stays 1.00.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste is S2 if S1 shipped.
```

## S2 — Item 3 re-measure (sourced only; done)

```
[SHARED PREAMBLE]

Task S2 only. After S1, re-measure undisturbed last/first on the
member-sum host. Item 3 still fails on the pre-S1 host (1.630 vs
author 1.004). R4 qoth_freeze 1.019 is a diagnostic isolation, not a
copy: author D.22 still updates q_oth.

Read first: xi_split.md, undisturbed.md, GATE0_DEPARTURES N2/N3/R4,
sheaf/agrimate/model.py q_oth update.

If last/first is still >1.1 and you have no sourced D.22 variant from
retrieved 14022004 wheat code, label and stop. Do not pin the unforced
world price to the 2006 mean. Do not write freeze_q_oth into
wheat_params(). Do not add a decay knob. Do not restore L1–L8.
Do not retune αI.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste S3 if item 3 is
labelled or sourced-fixed.
```

## S3 — A1 after A8 (USDA stocks only; done)

```
[SHARED PREAMBLE]

Task S3 only. Author cleaned wheat_food_balance_fao.csv is still the
A7/A1 cannot-set. Raw FBSH is vendored (R6); prepare_wheat_fbsh was
not adopted (moy worse on the mean-USDA host). After S1, USDA H is
summed, so China H is comparable to FBSH.

Re-score FBSH H/C vs summed-USDA on one harvest+AMIS window if S1
shipped. Keep USDA ending_stocks as S. Never treat FAO ΔS as stocks.
Keep USDA as prepare_wheat default unless items 1–3 improve and moy
does not worsen versus the S1 USDA host. Do not copy 2015–21
FoodTradeNetwork averages. Do not mix FBS 2010+ into FBSH.
Do not retune αI / p_sto / xmin.

Read first: GATE0_DATA.md, faostat_fb.md, fb_wheatdata.md,
GATE0_DEPARTURES.md A1.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste S4.
```

## S4 — A7 cannot-set inventory (next)

```
[SHARED PREAMBLE]

Task S4 only. Fig. 4 NetCDF is AgrimateEU28+Egypt, FAO anomalies,
start 2000. Host remains AgrimateRegionsWheat + USDA + αI=3.2.
fig4_experiment_params() already sets the knobs that can be set
(αI=3.5, ζ=1, N_for=6). FAO cleaned FB / EU28+Egypt split /
start-2000 still cannot-set unless those arrays appear in the repo.

Inventory what is still missing. Do not invent an Egypt node. Do not
put Fig. 4 knobs into wheat_params(). Do not retune. If files appeared,
label a parallel region list; do not silently replace C.1.

Read first: GATE0_DEPARTURES.md A7, fig4_config.md, fig4.md.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste S5.
```

## S5 — Re-score Fig. 4 / hindcast on the new host

```
[SHARED PREAMBLE]

Task S5 only. Allowed because S1 changed the data adapter, not
wheat_params(). Re-score hike, quiet-year index, moy max/min, and
undisturbed last/first against author_fig4/ and Pink Sheet. Update
hindcast.md / fig4.md / regional.md from the new CSVs.
Do not adopt Bai αI=10. Do not restore L1–L8. Do not pin 2006.

This is not R11 (R11 is forbidden while defaults are unchanged).

Read first: GATE0_VALIDATION.md, hindcast.md, fig4.md.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste S6 if items 1–3
evidence changed; else stay not-accepted and do not start G1.
```

## S6 — G0-P methods v2

```
[SHARED PREAMBLE]

Task S6 only. Update the G0-P methods note with S1–S5 evidence.
Still no substitution, no government game. Accept or reject the market
section on DEVELOPMENT items 1–5 as they now stand. Do not start G1
in the same session. Do not pin. Do not retune αI.

Read first: diagnostics/gate0_agrimate/methods.md, GATE0_REDTEAM.md,
DEVELOPMENT.md pass rule (items 1–3 before 5).
```

## Blocked (do not paste until G0-P is accepted)

```
G1 — Cross-crop substitution on the accepted G0 host.
Disabled G1 recovers the single-crop three-scenario run.
Needs an approved GATE0_DEPARTURES record before code.

G2 — Government restriction game.
Disabled G2 recovers E.4 AMIS. Not restriction_pulse.
Needs an approved GATE0_DEPARTURES record before code.
```
