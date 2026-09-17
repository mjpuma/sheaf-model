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
Pasteable one-prompt-per-session list: [`GATE0_PROMPTS.md`](GATE0_PROMPTS.md).
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

Gate 0 is **not** currently at the publication bar. **G0-N and G0-S are met**
against retrieved author code. **G0-U is the three-scenario validation
workflow** (`diagnostics/GATE0_VALIDATION.md`): undisturbed / harvest-only /
harvest+AMIS, scoring prices **and** supply/stocks. Pink-Sheet scoring stays
G0-H. G1/G2 stay blocked. The only SHEAF differentiator versus an Agrimate
copy (including the Bai/Wada/Puma copy) is that G1 substitution and G2
government games will be added **after** G0-P.

## Sequence (do not skip)

| Stage | Work | Exit |
|---|---|---|
| **G0-N** | Make the supplier programme numerically solvent on the 24-step wheat year. Record residual, runtime, and when the inverse-demand floor binds. | **Met on the 2003–11 reference run** (failed/fallback 0; residual 0; offer-floor 0; price index 0.0066–5.02 without a pin). Unconverged scipy 1043/6048 still feasible. Pink-Sheet scoring is G0-H. |
| **G0-S** | Close source gaps that change economics: C.1 ISO list, D.8 vs F.1, ζ0, D.1b, E.27 support, FAOSTAT Food Balance vs USDA (A1–A6). Retrieve Zenodo code/data if available. Unsent questions: `GATE0_AGRIMATE_BRIEF.md`. | **Met for retrieved code.** 27-region C.1 wheat list, author params, p_sto, x_min penalty, E.27, D.1 weights. Unresolved labelled (β, D.30a, FAOSTAT FB, data zip). |
| **G0-U** | Undisturbed / harvest-only / harvest+AMIS. Accounting identities. Score prices **and** USDA supply/stocks. Ukraine / Eastern Africa mechanism panels. OAT diagnostic without retuning. Protocol: `GATE0_VALIDATION.md`. | Three-scenario report in `diagnostics/gate0_agrimate/`; documented seasonal baseline; material balance. |
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

## Now (G0-U)

1. **G0-N (done).** Always-feasible supplier plan; reference run solvent.
2. **G0-S (done against retrieved code).** Zenodo 14022004 in hand. Wheat
   C.1 is 27 author names; params follow `AgrimateParams`; p_sto and x_min
   penalty; E.27 and D.1 from author. Unresolved labelled in
   `GATE0_AGRIMATE_BRIEF.md`. Data 10688435 not unpacked (G0-H).
3. **G0-U (this).** Three-scenario runner `scripts/run_agrimate_validation.py`.
   Bai/Wada/Puma workflow structure (scenarios, prices+stocks+supply,
   mechanism panels, OAT). Author defaults unchanged (αI=3.2, not Bai's 10).
   G1/G2 recorded as later recovery tests, not implemented.
   First 2003–11 run is in `diagnostics/gate0_agrimate/` (AMIS Δ now binds:
   491 region-steps; harvest vs harvest+AMIS no longer identical). Undisturbed
   still drifts (annual-mean ratio 1.63); Pink-Sheet corr remains negative.
   That is a G0-H score, not a reason to restore L1–L8. G0-U exit is the
   **workflow**, not publication-quality hindcast.
4. Single-scenario smoke remains `python scripts/run_agrimate_wheat.py`.
5. **Next session:** paste **P1** from [`GATE0_PROMPTS.md`](GATE0_PROMPTS.md)
   (accounting identities). One prompt per session after that.

Reference command:

```bash
python -m pytest tests/agrimate -q
PYTHONPATH=. python scripts/run_agrimate_validation.py
```

Solver smoke (one harvest+AMIS path):

```bash
PYTHONPATH=. python scripts/run_agrimate_wheat.py
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
