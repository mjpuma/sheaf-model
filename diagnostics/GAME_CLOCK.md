# Crisis game clock (Headey 2011)

**Locked 2026-08-27.** Guiding paper: Headey, D. (2011). Rethinking the
global food crisis: The role of trade shocks. *Food Policy* 36: 136–146.

This file is the architecture lock for **who chooses what, on which
clock**. It is not a 2008/10 score and not an invitation to retune
Gate 0 or Gate 1.

## Do Gate 0 or Gate 1 need to be re-run?

**No.**

| Layer | Substitution | Game | Why a re-run would be wasted |
|---|---|---|---|
| **Gate 0 / P1** | off | off (AMIS diary) | Headey is why the diary is first-order and why the market is sub-annual. He does not change `CropParams`, harvest calendars, LOWESS shocks, Armington E0, or the AMIS→cut map. Official scores in `diagnostics/gate0_*_report.md` stay the scores. |
| **Gate 1 / P3** | on (`σ ∈ {0, 0.3, 0.6}`) | off | Headey’s wheat→rice demand surge is *motivation* that grains spill. It is not a reason to densify `σ`, pick `σ*`, graft annual Slutsky `M_i` onto the spine, or unpause `dynamic_grains.py`. The frozen claim in `overleaf/gate1_whitepaper/` stands. |

Re-running those scripts would reproduce the same tables. Do not treat
this clock note as a new P1 or P3 experiment.

**What does get a run:** the Gate 2 policy beta on the 24-step spine
(`python3 scripts/score_gate2_beta.py`). Official P1/P3 paths remain
`use_amis=True` and do not call `sheaf/dynamic_policy.py`.

## Two timescales

Headey’s events have **dates**, not marketing years. Vietnam and India
restrict rice in October 2007; Egypt and China in January 2008;
India/Vietnam/Cambodia tighten in March; Thailand’s new government
*discusses* a ban that same month; Japan is *allowed to re-export rice
stocks* in May (the grain reportedly never ships; the announcement is
the move); Argentina changes wheat export policy every few months
through 2007–08. Import surges (Philippines 1.3 MMT in four months;
Nigeria waiving a 100% tariff) sit on the same clock.

That is the object. Split it:

| Object | Clock | What it is |
|---|---|---|
| **Type** | years / regimes | How much a government cares about domestic food vs export revenue. Moves with elections, revolutions, fiscal crisis. `fs_weight`, `p_target`, open vs restrictive vs rice specialist, `gov_stu`. |
| **Action** | fortnights / months | Whether to cut offers, lift a ban, announce a stock release, do a government-to-government deal. Responds to **state**: stocks relative to a normal year, price, what others just did, weeks to harvest. |

Conflating them into one annual `τ_i` is what the leftover host does.

## Where the leftover is

`sheaf/core.py` `ExportRestrictionGame` + `demo.py` is the **TWIST-era
annual SPE prototype**: one tax per year, node prices from a Takayama–
Judge QP, consumer surplus at `p_i`. It was the right game when the
market itself was annual. Gate 0 retired that market for crisis work
(`ARCHITECTURE.md`, `diagnostics/LEVEL1_INTERROGATION.md`). Agrimate
never had an endogenous game — AMIS is a diary — so there was no
template for “governments choose on the 24-step clock,” and the Nash
layer stayed on `core.py`. That is a leftover, not the 2007/08 object.

`demo.py` may still run the annual prototype. Crisis hindcasts and the
crisis game do not.

## Where the live game sits

- **Market:** Gate 0 24-step spine (`sheaf/dynamic_crop.py`). One
  ask-dominated world price per crop. A ban does not create a cheaper
  domestic CPI; withheld grain stays as stock.
- **Types:** slow, illustrative until a train/hold-out protocol exists.
  Country archetypes in `sheaf/calibration.py` (`open` / `restrictive` /
  `rice` / `none`) are the preference layer for the annual prototype;
  the same *idea* (sticky type, not a fortnightly personality) applies
  on the spine.
- **Actions:** `sheaf/dynamic_policy.py` on that spine. The year-open-loop
  grid BR is a **nested mechanism check** (one intensity for a shock
  year). The Headey object is a **state-contingent** `τ_{i,t}` that can
  turn on and off inside the year.
- **Not yet:** multi-country Nash, importer procurement, Japan-style
  reserve *announcements*, cooperative club (P4 proper), tipping (P5).
  Headey has those; the beta does not.

## Trigger that does not fight the harvest calendar

Gate 0 competitive safety (`stu_target × C_ann`) and any absolute
stock floor sit *above* the hungry-season trough even in climatology.
A government that bans whenever `S_t < s` would restrict every year.
That is a seasonal sawtooth, not a crisis (Headey’s India trigger is
stocks vs **buffer norms plus** an export-demand / price surge).

On this host the object that separates a harvest failure from the
sawtooth is **stock relative to a normal year at the same calendar
step**: `S_{i,t} / S^{calm}_{i,t}`. The beta cuts when that ratio falls
below an illustrative trigger, at an illustrative intensity (`tau_on`),
in the shock year only. Types (`gov_stu`, `tau_on`, trigger) stay
fixed; the path of `τ_t` moves.

## Hard bars (beta)

1. Climatology harvest ⇒ `τ_t = 0` every step (ratio ≡ 1).
2. Synthetic harvest cut ⇒ `τ_t > 0` on some steps.
3. Those cuts reduce that exporter’s shipments vs the open shock path.
4. `run_crop_dynamics` still defaults AMIS on when this module is not
   called.

Not scored against who banned in 2008. See `diagnostics/GATE2_PLAN.md`.
