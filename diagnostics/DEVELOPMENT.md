# Development plan

**Current phase:** Gate 0 wheat, Agrimate-faithful host (`sheaf/agrimate/`).
Gate 1 and Gate 2 are **blocked**. They stay blocked until Gate 0 is
vetted at a **publishable** level: source-faithful, numerically reliable,
and equal or better than Agrimate on Agrimate’s own wheat targets.

That sequencing is the lesson from the last cycle. Shipping substitution
and a policy sketch on an unpublishable market was a mistake. Do not
repeat it.

Canonical contract: [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md).
Spec map: [`GATE0_SPEC_MATRIX.md`](GATE0_SPEC_MATRIX.md).
This file is the living queue.

## What “publishable Gate 0” means

Agrimate (Kuhla, Kubiczek & Otto 2025, *Ecol. Econ.* 231:108546) is the
bar, not the legacy SHEAF ask/scarcity scores. For **wheat**:

1. **Source fidelity.** Supplier, purchaser, consumer, storage, restrictions,
   timing, and world-price *definition* match the paper/supplement (or an
   approved departure record). Equation-to-code review, not a prompt.
2. **Numerical reliability.** Supplier plans converge. Constraint residuals
   are small. Failed solves are counted and rare enough that they do not
   set the price path. No fill-target, calm pin, scarcity blend, or rival
   markup to make a test pass.
3. **Undisturbed dynamics.** After spin-up, seasonal repeating behaviour
   as Agrimate describes. Not a flat pinned world price.
4. **Reference reproduction.** Same wheat case, data vintage, parameters,
   and output definitions as closely as access allows. If Zenodo
   14022004 / 10688435 are in hand, compare to author series (Fig. 4 and
   regional supply/consumption/stocks). If they are not, say
   “independent implementation,” not “replication.”
5. **Historical performance.** Price *levels and seasonal paths*, not only
   a correlation. Crisis hike ratios *and* quiet-year levels. Stocks,
   consumption, and trade where Agrimate or USDA/FAO report them.
6. **Controlled experiments.** Harvest-only vs harvest+restrictions, as in
   Agrimate’s three scenarios. Domestic vs international responses.

**Pass rule:** items 1–3 must hold before we spend time judging 5.
Item 5 is judged against Agrimate’s published wheat results, not against
legacy SHEAF. A worse Pink-Sheet fit during debugging does **not** restore
L1–L8 (`GATE0_DEPARTURES.md`).

**Wheat only.** Maize and rice are later Agrimate-style single-crop
applications. Do not accept them with inherited wheat knobs, and do not
use them to wave Gate 0 through.

Gate 0 is **not** currently at this bar. The host runs; Nash sales = harvest;
12 unit tests pass; many dynamic supplier solves still fail. That is a
solver/specification gap, not a license to open Gate 1.

## Sequence (do not skip)

| Stage | Work | Exit |
|---|---|---|
| **G0-N** | Make the supplier programme numerically solvent on the 24-step wheat year. Record residual, runtime, and when the inverse-demand floor binds. | Failed/fallback solves rare; storage feasible; price index O(1) without a pin. |
| **G0-S** | Close source gaps that change economics: C.1 ISO list, D.8 vs F.1, ζ0, D.1b, E.27 support, FAOSTAT Food Balance vs USDA (A1–A6). Retrieve Zenodo code/data if available. Unsent questions: `GATE0_AGRIMATE_BRIEF.md`. | Spec matrix updated; unresolved items labelled, not guessed. |
| **G0-U** | Undisturbed / spin-up / restriction-off vs harvest-only vs full AMIS. Accounting identities each step. | Documented seasonal baseline; material balance. |
| **G0-H** | 2006–11 wheat hindcast vs Pink Sheet **and** vs Agrimate Fig. 4 / regional tables if author output exists. Report levels, paths, hike ratios, stocks, consumption, trade. | Written score in `diagnostics/gate0_agrimate/`. Comparable to Agrimate or an explicit, sourced shortfall. |
| **G0-P** | Gate 0 note at publication standard (methods, data, hindcast, limits). No substitution, no government game. | You accept wheat Gate 0 as the SHEAF market paper / section. **This is the only gate that unlocks G1.** |
| **G1** | Cross-crop substitution (wheat/rice/maize), distinct from Agrimate origin CES. Disabled G1 recovers G0. | Identity test + spillover experiments. No σ* fit to 2008. |
| **G2** | Government restriction game, distinct from supplier oligopoly and from AMIS/E.4. Disabled G2 recovers E.4 Agrimate. | Mechanism tests on the *accepted* G0 host. Train/hold-out if estimated. |

G1 and G2 each need an approved departure record before code
(`GATE0_DEPARTURES.md`, `GATE0_EXTENSION_PLAN.md`). Assistant-generated
ideas and leftover `dynamic_coupled` / `dynamic_policy` code are **not**
approval.

## Hard stops

- Do not implement or retune Gate 1 (`sheaf/dynamic_coupled.py`) or Gate 2
  (`sheaf/dynamic_policy.py`) while any G0-N…G0-P box is open.
- Do not treat legacy `diagnostics/gate0_*_report.md` or the Overleaf
  ask/scarcity deck as evidence about the new host.
- Do not move maize/rice onto the new host as an acceptance target.
- Do not “fix” unforced prices by pinning them to the 2006 mean.
- Dead-end artifacts (legacy red-team scratch, uncommitted Overleaf WIP
  on the old map) stay in `archive/` or uncommitted. Do not resurrect them
  as the market.

## Now (G0-N, then G0-S)

1. Diagnose why L-BFGS fails on the dynamic supplier plan (feasibility,
   scaling, seasonal starred quantities, horizon). Prefer a faithful
   constrained solve over a cheaper surrogate unless equivalence is shown.
2. Obtain or confirm absence of Zenodo 14022004 (code) and 10688435 (data).
   Until author binaries exist, keep the “independent implementation” label.
3. Keep `python scripts/run_agrimate_wheat.py` as the only default run.
4. Compare only under labelled configs: new host / Agrimate published /
   `sheaf/legacy`.

Reference command:

```bash
python -m pytest tests/agrimate -q
python scripts/run_agrimate_wheat.py
```

Legacy (labelled, not the bar):

```bash
python scripts/score_legacy_crop.py --crop wheat
```

## Prior cycle (legacy ask/scarcity host) — closed

The 2026-08 characterization (A1–A5, red-team, Potsdam note) documented the
**old** sequential map. It is useful as a record of why that map is not
Agrimate. It is not a Gate 0 publication path.

- Artifacts: `diagnostics/gate0_prep/`, `diagnostics/redteam/`,
  `archive/legacy-gate0/`, `overleaf/gate0_discussion/`
- Code: `sheaf/legacy/`, `sheaf/dynamic_crop.py` (Gate 1 still imports this
  copy; do not extend it)

Parked, not next:

| Layer | Status |
|---|---|
| Gate 1 isoelastic substitution | Blocked until G0-P |
| Gate 2 Headey-clock actions | Blocked until G0-P, then G1 identity |
| Annual SPE `sheaf.annual` | Parked |
| `dynamic_grains.py` | Paused |
