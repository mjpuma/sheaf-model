# Development plan

**Current phase (2026-08-31):** return to **Gate 0**. The 24-step market is
the baseline we have to be happy with after coauthor consultation. Gate 1
and Gate 2 are paused on that spine. They are not the work now.

This file is the living queue. Paper-shaped questions stay in
[`PAPER_STACK.md`](PAPER_STACK.md). Clock (who chooses what, when) stays in
[`GAME_CLOCK.md`](GAME_CLOCK.md). Parameter table for the *current* map:
[`GATE0_PARAMETERIZATION.md`](GATE0_PARAMETERIZATION.md). Options after
the Agrimate sitting: [`GATE0_DISCUSSION.md`](GATE0_DISCUSSION.md).
Flow diagrams: [`GATE0_FLOWS.md`](GATE0_FLOWS.md) and
[`figures/gate0_flows/`](../figures/gate0_flows/). Overleaf note (symbols,
map \(F\), solution, four figures):
[`overleaf/gate0_discussion/`](../overleaf/gate0_discussion/).

## What “open baseline” means

`diagnostics/gate0_*_report.md` are **snapshots** of the map as scored.
They are not a freeze. Consultation can change the price law, storage
object, asks, or expectations. If it does, we re-score and relabel.

Still not allowed:

- Crisis dummies or 2008-only knobs
- Picking a preferred \(\sigma^\star\)
- Treating `sheaf.annual` as the 2007/08 host
- Silently mixing the yearly QP into `_simulate_window`

Headey (2011) still does **not**, by itself, force a Gate 0 re-run. Colleague
questions about *how \(p\) is formed* do.

## Now

1. **Discussion document** — [`GATE0_DISCUSSION.md`](GATE0_DISCUSSION.md).
   Walk the sitting questions as options (keep / characterize / change),
   with a complexity budget, **before** prompts and **before** equation
   changes. The point is a Gate 0 we will stand behind.
2. **Then write Cursor prompts** in this repository against
   `sheaf/dynamic_crop.py`, one surviving cluster at a time. Not the earlier
   pack aimed at Agrimate’s repo. Prompts force characterization of the
   current map first.
3. **Interrogate, then decide.** Named keep, or named change + re-score
   (official vs sensitivity). Do not skip characterize-the-current-law.

## Paused

| Layer | Status | Resume when |
|---|---|---|
| Gate 1 (`dynamic_coupled`, \(\sigma\in\{0,0.3,0.6\}\)) | Draft + snapshot scores | Gate 0 baseline is one we will stand behind |
| Gate 2 beta (`dynamic_policy`) | Mechanism check only | Same |
| Annual SPE (`sheaf.annual`) | Parked | A year-scale outer loop is actually wanted |
| `dynamic_grains.py` | Still paused | Do not unpause to chase Gate 0 |

## Consultation themes already on the table

These came out of the Agrimate sitting. They are questions for **our**
Gate 0 code, not a rewrite list yet.

- How \(p_t\) is formed (map, not a DE, not a per-step NLP)
- Whether FAO/economists need an optimization principle under that update
- What “baseline” names (twin, \(p_0\), climatology, spin-up)
- No commercial store-vs-sell agent; target \(T=L+s\) instead
- Export offers \(O\) vs FAOSTAT shares \(A,S\); one world \(p\) plus asks \(q_i\)
- No carrying cost \(r\); why grain is not dumped this step
- Adaptive harvest \(\phi\)-blend, not 10-year perfect foresight
- Too many reduced-form knobs vs hard bounds (\(W\), clips, AMIS \(\tau\))

## Identification (unchanged)

| Layer | Constraint |
|---|---|
| Gate 0 | Literature \(\varepsilon\), STU; reduced-form knobs shared across years; Agrimate official split (harvest ± AMIS, mean flex; USA maize industrial on) |
| Gate 1 | Band only; no \(\sigma^\star\) |
| Gate 2 | Types illustrative until a train/hold-out protocol exists |

## Smoke tests

```bash
python scripts/score_subannual_crop.py --crop wheat
python scripts/score_subannual_crop.py --crop maize
python scripts/score_subannual_crop.py --crop rice
```

Annual prototype (not Gate 0): `python scripts/annual/demo.py`.
