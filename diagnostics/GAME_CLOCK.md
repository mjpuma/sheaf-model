# Crisis game clock (Headey 2011)

**Locked 2026-08-27.** Guiding paper: Headey, D. (2011). Rethinking the
global food crisis: The role of trade shocks. *Food Policy* 36: 136–146.

This file is the architecture lock for **who chooses what, on which
clock**. It is not a 2008/10 score. It is not an invitation to retune
Gate 0 because Headey exists. Returning to Gate 0 after coauthor
consultation on the *market* is [`DEVELOPMENT.md`](DEVELOPMENT.md).

**Headey does not, by itself, force a Gate 0 re-run.** Colleague
questions about how the *market* forms \(p\) do — see
[`DEVELOPMENT.md`](DEVELOPMENT.md). Headey is why the diary is
first-order and why the market is sub-annual. He does not pick
`CropParams`. Official `gate0_*_report.md` files are snapshots until
the baseline is revised.

| Layer | Substitution | Game | Headey alone |
|---|---|---|---|
| **Gate 0** | off | off (AMIS diary) | Not a reason to retune. Consultation on \(p\), storage, asks **is**. |
| **Gate 1** | on (`σ ∈ {0, 0.3, 0.6}`) | off | Not a reason to densify `σ` or pick `σ*`. Paused until Gate 0 is one we will stand behind. |

**What does not get a run right now:** Gate 2 beta. Pause until the
Gate 0 baseline is settled. `use_amis=True` paths still do not call
`sheaf/dynamic_policy.py`.

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

`sheaf.annual` `ExportRestrictionGame` + `scripts/annual/demo.py` is the
**TWIST-era annual SPE prototype**: one tax per year, node prices from a
Takayama–Judge QP, consumer surplus at `p_i`. It was the right game when
the market itself was annual. Gate 0 retired that market for crisis work
(`ARCHITECTURE.md`, `diagnostics/LEVEL1_INTERROGATION.md`). Agrimate
never had an endogenous game — AMIS is a diary — so there was no
template for “governments choose on the 24-step clock,” and the Nash
layer stayed on the annual host. That is parked in `sheaf/annual/`, not
the 2007/08 object.

`python scripts/annual/demo.py` still runs that prototype. Crisis
hindcasts and the crisis game do not.

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
- **Two players (in):** Russia (harvest shock) and Kazakhstan (neighbor,
  no own harvest cut), same types. The cascade is harvest diversion
  onto the leaner neighbor, not sequential ban-on-ban IBR. Ukraine is
  on the market but does not play (too fat to fire). **Not yet:**
  multi-country Nash, importer procurement, Japan-style reserve
  *announcements*, club-of-the-willing / tipping variants.

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

1. Climatology harvest ⇒ `τ_t = 0` every step, every player (ratio ≡ 1).
2. Russia harvest ×0.50 ⇒ Russia some `τ_t > 0`.
3. Kazakhstan some `τ_t > 0` with **no** Kazakh harvest cut.
4. Kazakhstan’s first on-step ≥ Russia’s (neighbor lags or ties).
5. Russia’s cuts reduce Russia’s shipments vs the open shock path.
6. `run_crop_dynamics` still defaults AMIS on when this module is not
   called.

Not scored against who banned in 2008. See `diagnostics/GATE2_PLAN.md`.
