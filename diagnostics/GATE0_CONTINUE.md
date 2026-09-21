# Gate 0 continuation (post-S6)

**Where:** this file. Living next-paste:
[`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md).
S-queue: [`GATE0_NEXT_PROMPTS.md`](GATE0_NEXT_PROMPTS.md) (**S1–S6 done**;
G0-P **not accepted**). R-queue exhausted.

G0-P was rewritten from S1–S5 evidence and **still rejected**. Items 2
and 3 fail. G1/G2 stay blocked. T1–T3 **done** (labelled, not adopted).
T-queue is exhausted. Next paste **stay not-accepted**. Do not start G1.

## Adaptive rule

Rewrite `GATE0_REPRO_DISPATCH.md` in ≤20 lines. Next session pastes
**Next paste**, not `T{n+1}`. First match wins:

| If the last run showed… | Next paste | Skip |
|---|---|---|
| Obtain failed (GitLab/Zenodo unreachable; no inspectable tree) | **T1** | do not adopt `freeze_q_oth`; do not pin |
| Julia inspected; D.22 / solver **differs**; T2 note **absent** | **T2** | label sourced delta only; do not copy Julia into `sheaf/agrimate/` |
| T3 FAO/EU28 extract **present**, labelled, not adopted | **stay not-accepted** | do not start G1; do not invent Egypt; FAO not `prepare_wheat` |
| T2 labelled; not implemented | **T3** | do not invent Egypt; knobs stay on `fig4_experiment_params()` |
| Julia obtained; D.22 **matches** host (item 3 still open) | leave labelled | do not invent a decay knob |
| Tests would still pass a *non*-match | R8 may piggyback | do not weaken identities |

Hard stops do not adapt. L1–L8, 2006 pin, Bai αI=10, maize/rice
acceptance, G1/G2, FAO ΔS as stocks, and writing `freeze_q_oth` into
`wheat_params()` stay off.

## Shared preamble (prepend to every T-prompt)

```
You are continuing SHEAF Gate 0 wheat: an independent Agrimate copy
(Kuhla et al. 2025; sheaf/agrimate/). Read diagnostics/GATE0_CONTRACT.md,
diagnostics/DEVELOPMENT.md, diagnostics/GATE0_VALIDATION.md,
diagnostics/GATE0_REDTEAM.md, diagnostics/GATE0_DATA.md,
diagnostics/GATE0_CONTINUE.md, and this prompt's "Read first"
files before editing.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not restore L1–L8. Do not pin the unforced world price to 2006.
- Do not retune αI, p_sto, xmin, or λ to Pink Sheet or Bai α_foreign=10.
- Do not treat FAOSTAT FBSH element 5074 ΔS as a stock level.
- Do not copy author Julia into sheaf/agrimate/.
- Do not write freeze_q_oth into wheat_params().
- Author AgrimateParams stay the defaults.

Exit: pytest tests/agrimate. One prompt, one PR-sized change.
Rewrite diagnostics/GATE0_REPRO_DISPATCH.md from this run (≤20 lines).
Next session pastes that file's **Next paste**.
```

## Status

| ID | Prompt | Status |
|---|---|---|
| S1–S6 | Post-R development | **done** (G0-P **not accepted**) |
| **T1** | Obtain-or-leave 14022004 Julia (inspect D.22 / solver) | **done** (deltas exist; 0 `*.jl` in sheaf) |
| **T2** | Label sourced D.22/solver delta | **done** (labelled, not adopted) |
| **T3** | Obtain-or-leave FAO-since-2005 + EU28 inputs | **done** (labelled, not adopted; not C.1) |
| — | G1 / G2 | **blocked until G0-P accepted** |
| — | stay not-accepted | **next** (T-queue exhausted; G0-P still **not accepted**) |

---

## T1 — Obtain-or-leave Zenodo 14022004 Julia

```
[SHARED PREAMBLE]

Task T1 only. Obtain-or-leave Zenodo 14022004 author Julia *to inspect*
D.22 q_oth and the supplier solver versus this host. Do not copy Julia
into sheaf/agrimate/. Do not vendor a wholesale tree. Record sourced
deltas (or the failed obtain) in diagnostics/gate0_agrimate/.
Do not adopt freeze_q_oth. Do not pin 2006. Do not retune αI.
Do not start G1. wheat_params() stay 14022004 defaults.

Read first: item3.md, xi_split.md, solver.md, GATE0_DEPARTURES.md N5 / D.22.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste T2 if a sourced D.22
or solver delta exists; else leave labelled and do not start G1.
```

## T2 — Label sourced D.22 / solver delta

```
[SHARED PREAMBLE]

Task T2 only. If T1 obtained Julia and D.22 or the supplier programme
differs from sheaf/agrimate/, write the sourced delta (equation, file,
line). Do not implement a freeze, pin, or new law unless the author
wheat path does that. Do not copy Julia. Do not start G1.

Read first: T1 note, item3.md, optimize.py, model.py q_oth.

End: rewrite GATE0_REPRO_DISPATCH.md.
```

## T3 — Obtain-or-leave Fig. 4 FAO / EU28 inputs

```
[SHARED PREAMBLE]

Task T3 only. Obtain-or-leave FAO-since-2005 anomalies and
AgrimateEU28+Egypt arrays needed to run the published Fig. 4
*experiment* as a labelled comparison. Do not invent an Egypt node
on C.1. Do not put Fig. 4 knobs into wheat_params(). USDA stays
prepare_wheat default. Do not start G1.

Read first: GATE0_DEPARTURES.md A7, s4_a7.md, fig4_config.md.

End: rewrite GATE0_REPRO_DISPATCH.md. Next paste stay not-accepted
if the extract is labelled and not adopted; else retry T3. Do not start G1.
```
