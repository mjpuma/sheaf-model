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

## Now — Gate 0 characterization sweep

**Deliverable to Potsdam is no longer a prompt pack.** It is (a) the
corrected note, (b) measured results, (c) proposed next steps. Prompts stay
in the repo as the record of method:
[`audit_prompts/GATE0_MODEL_PROMPTS.md`](../audit_prompts/GATE0_MODEL_PROMPTS.md)
(Part A = read-only characterization, Part B = gated changes).

| ID | Activity | Status | Artifacts |
|---|---|---|---|
| A1 | Note equations vs `_simulate_window`, symbol by symbol | **done** — all four seeded hypotheses confirmed | [`gate0_prep/a1/`](gate0_prep/a1/) |
| A1b | Why the calm branch has work to do; is `θ` mis-set? | **done** — re-targeting `θ` rejected | `gate0_prep/a1/A1B_CALM_FIXED_POINT.md` |
| A1c | Does the calm branch touch a scored result? | **done** — no (0/144 in both scored legs) | `gate0_prep/a1/A1C_CALM_REACH.md` |
| A2 | Is `p^scar` already an optimisation principle? | not started | — |
| A3 | Size of the contemporaneous-demand gap; is `p=G(p)` well posed? | running | `gate0_prep/a3/` |
| A4 | Cover rule's implied shadow value; cause of the exporter floor | running | `gate0_prep/a4/` |
| A5 | Channel ablation: which channel carries which crisis | running | `gate0_prep/a5/` |

### A1 findings (all four confirmed; details in `gate0_prep/a1/`)

1. **Scarcity regulariser is not small or constant.** \(f_t=0.05\sum_i s_i
   +\max(0,-\min(F,F^{\mathrm{twin}}))\) = 6.4 / 6.5 / 3.9 MMT
   (wheat/maize/rice), i.e. 4.8% / 3.1% / **10.3%** of mean accessible
   stock. Bias vs the unregularised ratio: 2.2% / 3.4% / **35.4%** mean.
   Accessible stock goes **negative** at 58/144 steps for rice — the world
   holds less than its own lean cover — so for rice \(r_t\) is materially a
   regularised quantity. Category **G** on the note; the second term is
   defensible as implemented. Confidence 95–100% (reproduced).
2. **The reference identity is enforced, not derived.** An explicit
   conditional sets \(p^\star=p_0\) when the run matches the twin. Disable
   it and the matched run drifts **25% / 34% / 19%** against a 2% test
   tolerance. Root cause: realised matched-run fill is **0.54 / 0.32 /
   0.62** against \(\theta=0.70\), so the ask law pushes offers down every
   step with nothing happening — it has **no rest point at \(p_0\)**.
   Category **G** on the claim; the underlying property is a real design
   question (see A1b/A1c). Confidence 95–100%.
3. **Unmet-demand channel is one-sided.** \(\Delta u=\max(0,u-u^{twin})\),
   and the truncation binds at 92/59/100 of 144 steps. Category **G**.
4. **\(p^{\mathrm{tr}}\) uses this step's asks**, not the lagged asks that
   allocated the trade. Offer prices are updated twice in one causal chain.
   Category **G**. Median per-step ask move $7.58 (wheat) — not negligible.

**No code change recommended from A1.** Removing the conditional breaks two
of four robustness assertions and changes nothing scored; re-targeting
\(\theta\) leaves 19–20% drift and degrades maize corr +0.71 → +0.65. Fixes
applied were to the note (`overleaf/gate0_discussion/`, now 19 pp.).

### Then

- **A2** — the one Part A prompt not yet run.
- **Decide** each cluster: named keep, or named change + re-score (official
  vs sensitivity). Do not skip characterize-the-current-law.
- **Deck** — `overleaf/sheaf_deck/` needs the A1 corrections (slide 48
  wording, the twin-identity claim). **Deferred until the sweep closes.**

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
