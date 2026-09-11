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
| A2 | Is `p^scar` already an optimisation principle? | **done** — yes for the scarcity term; the blend is not | [`gate0_prep/a2/`](gate0_prep/a2/) |
| A2b–f | Price flexibility; monotonicity; the pin's reach into the τ column and the sign test | **done** — the sweep's headline | `gate0_prep/a2/A2{B,C,D,E,F}_*.md` |
| A3 | Size of the contemporaneous-demand gap; is `p=G(p)` well posed? | **done** — gap 0.3–0.9%; well posed at the root, not globally contractive | `gate0_prep/a3/A3_REPORT.md` |
| A4 | Cover rule's implied shadow value; cause of the exporter floor | **done** — implied \(r\) sign is a coin-flip; uniform \(s_i\) is the floor | `gate0_prep/a4/A4_REPORT.md` |
| A5 | Channel ablation: which channel carries which crisis | **done** — 2007/08 restriction-carried; 2010/11 ask-dynamics for wheat/maize | `gate0_prep/a5/A5_REPORT.md` |
| RT | Agrimate red team: dead dest-reweight → CES source shares; exporter FOC prototyped | **done** — CES shipped (`929cec4`); exporter FOC tested and **rejected** (pre-CES maize +0.712 → +0.339; not shipped) | `gate0_prep/redteam/REDTEAM_SYNTHESIS.md`, `optimisation/REDTEAM_OPTIMISATION.md`, `clearing/REDTEAM_CLEARING.md`, `census/REDTEAM_CENSUS.md`, `VERIFICATION.md` |

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

**No code change recommended from A1 alone.** Removing the conditional
breaks two of four robustness assertions; re-targeting \(\theta\) leaves
19–20% drift and degrades maize corr +0.71 → +0.65. A1's fixes were to the
note (`overleaf/gate0_discussion/`, now 19 pp.).

### A2 findings — the sweep's headline

A1c's "no scored number depends on the conditional" was **too strong**. It
holds for the price correlation and the full/harvest-only hike ratios, not
for the τ column, whose base window *is* the pinned stretch.

1. **The restriction sign test was not like-for-like.** Its baseline leg is
   pinned at \(p_0\) at every step while the τ leg is priced by the ask law,
   whose quiet level is 0.66/0.71/0.96 × \(p_0\). Maize lift was biased down
   27 pp. Category **B**, confidence 95–100%.
2. **`ask_rival = 0.80` has lost its justification.** The comment claimed it
   was the smallest value clearing the maize sign condition; on the
   corrected test the condition holds at **0.0** for all three crops
   (+4.7% / +48.8% / +16.0%). Crossing bisected under both tests: **0.755**
   as written (A5 independently got 0.751), **clears at 0.0** corrected —
   though maize's corrected margin is only +4.7%, so nearly binding, not
   slack. It is *not* spurious — at 0.0, maize corr +0.712 → +0.414 and rice
   07/08 ×1.72 → ×1.01. So it is a reduced-form amplitude parameter with no
   external basis. Category **F**, 95–100%. **Open decision** (see
   `POTSDAM_RESPONSE.md` §2). This reclassifies A5's finding 1 from H;
   adjudication recorded in `gate0_prep/a5/ADJUDICATION_ASK_RIVAL.md`.
3. **Maize 2007/08 flips demand-led → restriction-led** (τ ×1.10 → ×1.69,
   observed ×1.84); wheat ×1.70 → ×1.99. A5 reached the same conclusion by
   ablation, independently. **Open decision: which is the headline.**

### Fixes applied (commit `cafb8ba`) — no equation changed, no score moved

- `prepare_crop_run` raises on unknown overrides (was silently dropping
  them, so typo'd sensitivities reported "no effect"). Category **B**.
- All four assertions take `**overrides`. Category **G**.
- `assert_amis_raises_price` perturbs the baseline harvest by 1e-6 to leave
  the matched regime. Maize lift +1.9% → +31.2%; all twelve still pass.
- `score_subannual_crop.py` prints both τ ratios until the headline is
  settled.

### A3 / A5 in one line each

- **A3** — the contemporaneous-demand gap is 0.3–0.9% of world desired use
  (max 4.0% outside the spin-up year); one-step propagated price move
  ≤ 4.11 $/t. The fixed point has exactly one root at all 432 steps,
  \(|G'(p^\*)|\le 0.117\), Picard converges in ≤13 iterations from bad
  starts — but \(G\) is **not** globally contractive (L_max 39.7) and has
  two real jumps: the calm branch (≤36.8 $/t) and an uncatalogued
  \(p^{\mathrm{tr}}\) fallback at L665–669 (≤11.7 $/t). So X1 needs a
  bracketed solve with a residual check, not a bare iteration. Inclination:
  record, do not adopt. The \(p^{\mathrm{tr}}\) fallback is now written
  into the note as eq (13) — it was missing from our own equations.
- **A5** — 2007/08 is restriction-carried in all three crops; 2010/11 is
  ask-dynamics-carried for wheat and maize. No globally inert parameter, but
  three exact conditional-inertness identities.

### Red team vs Agrimate — shipped one fix

Synthesis: [`gate0_prep/redteam/REDTEAM_SYNTHESIS.md`](gate0_prep/redteam/REDTEAM_SYNTHESIS.md).
Potsdam letter updated.

**Shipped:** CES source-share reweight (`_ask_reweight_src`). Destination
reweight was the identity (`ask_comp_elast` inert). All twelve asserts
pass. New official full-leg scores: wheat **+0.728 / ×2.28 / ×1.45**,
maize **+0.778 / ×2.20 / ×1.59**, rice **+0.678 / ×1.72 / ×0.82**.

**Prototyped, not shipped:** exporter FOC in place of the ask law.
Restores the quiet-market rest point without the pin and passes asserts;
destroys crisis amplitude. Like-for-like on the pre-CES ask law: maize
corr +0.712 → +0.339 (`foc_scores.csv`). Independent verification:
[`gate0_prep/redteam/VERIFICATION.md`](gate0_prep/redteam/VERIFICATION.md).

**Their hard-bounds claim is false.** All-three-hard-bounds maize corr
+0.71 → +0.22.

**Remaining gap vs Agrimate:** store-versus-sell. Rice residual pool 47%.

### Then

- **A4** — measurements are in `gate0_prep/a4/`; write-up still open.
  Storage is the remaining Agrimate contrast.
- **Three open decisions**, all in `POTSDAM_RESPONSE.md`: the basis for
  `ask_rival`; keep-and-document vs rebuild the offer-price law; which τ
  ratio is the headline. None should be settled unilaterally.
- **Deck** — `overleaf/sheaf_deck/` needs the A1/A2 corrections and the
  CES / maize-score update. **Still deferred** until the user asks.

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
