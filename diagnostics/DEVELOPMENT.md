# Development plan

**Current phase:** wheat Gate 0 is **accepted** (G0-P, 2026-10-07). The
code path reproduces the published wheat run on the authors’ calibration
([`gate0_julia/J10_authorbaseline.md`](gate0_julia/J10_authorbaseline.md)).
Rice and maize `t_max=0` smoke is **met** (2026-10-08). Next: Gate 1
substitution. Gate 2 stays blocked until Gate 1 is accepted.

Canonical contract: [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md).
This file is the living queue.

## What “publishable Gate 0” means

Agrimate (Kuhla, Kubiczek & Otto 2025, *Ecol. Econ.* 231:108546) is
the bar.

1. **Source fidelity.** We run the published source, not a rewrite.
2. **Numerical reliability.** 312-step wheat runs exit 0. (The published
   code is slow: serial NLopt, hours not minutes.)
3. **Undisturbed / harvest / harvest+restrictions.** The three scenarios
   the paper uses.
4. **Reference reproduction.** J10: published code + author calibration →
   published NetCDF. **Met.**
5. **Public-data reconstruction.** USDA / FAOSTAT / AMIS → same code does
   **not** match published magnitudes (J4/J8/J9). Open limitation, not a
   retune target.
6. **Historical performance vs Pink Sheet.** Not the J10 bar; optional
   later.

**G0-P:** accepted 2026-10-07. J10 is the evidence. Public-data
reconstruction remains a different experiment, not a retune target.

## Sequence

| Stage | Work | Status |
|---|---|---|
| **G0-N** | Supplier programme runs on the 24-step wheat year | **Met** (published code, exit 0) |
| **G0-S** | Source in hand (Zenodo 14022004), vendored | **Met** (`agrimate_julia/`) |
| **G0-U** | Three scenarios on that source | **Met** (J2, J3, J10) |
| **G0-H** | Match the author wheat NetCDF | **Met for the code path (J10).** Public-data reconstruction fails (J4/J8/J9) |
| **G0-P** | You accept wheat Gate 0 as the SHEAF market baseline | **Accepted 2026-10-07** |
| **G1-prep** | Rice and maize smoke on this host (`crops="rice"` / `"maize"`) | **Met** (2026-10-08, `t_max=0`) |
| **G1** | Cross-crop substitution. Disabled G1 recovers G0 | Open |
| **G2** | Government restriction game. Disabled G2 recovers AMIS | Blocked |

## Hard stops

- G1-prep is met. Substitution goes in `agrimate_julia/` with an
  `UPSTREAM.md` line. Do not start Gate 2 until Gate 1 is accepted.
- Do not edit `agrimate_julia/` economics without an `UPSTREAM.md` line.
- Do not `Pkg.update()` / `Pkg.resolve()`. Julia 1.6.5.
- Do not retune to the Pink Sheet or to close the J4/J8/J9 gap.

## Next

1. Gate 1 substitution in `agrimate_julia/`, listed in `UPSTREAM.md`.
   Disabled Gate 1 must recover the three independent single-crop runs.
   Rice smoke needed a 0/0 harvest guard (`G1prep_rice.md`); do not
   invent production to hide empty regions.

## Exit criteria by gate

Every gate must collapse back to the accepted previous gate when its new
terms are switched off. That nesting is the regression test and the
paper's argument.

**Gate 0.** See [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md). Wheat accepted
(G0-P) on the J10 reproduction.

**Gate 1 (cross-crop substitution).**
- Substitution off (σ = 0) recovers the three independent single-crop runs
  to solver tolerance.
- A wheat shock moves rice and maize prices with plausible sign and
  magnitude.
- Results reported at σ ∈ {0, 0.3, 0.6}; elasticity sources logged.
- Notation: Agrimate already uses σ for substitution between suppliers.
  Rename one of the two before coding.

**Gate 2 (endogenous export restrictions).** Design:
[`GATE2_FOUNDATIONS.md`](GATE2_FOUNDATIONS.md). Clock:
[`GAME_CLOCK.md`](GAME_CLOCK.md). Built in three steps, each tested
before the next.
- 2a. Reactive term only. Threshold rule on domestic price change, stocks
  relative to a normal year at the same calendar step, and the
  trade-weighted share of partners restricting. Russia and Kazakhstan
  beta with the six hard bars in `GAME_CLOCK.md`.
- 2b. Strategic term only. Myopic best response to the current state; no
  fixed-point solve.
- 2c. Blend. Per-country weight ω; prior from each region's strategic
  (purchaser) versus commercial (supplier) baseline stock balance, tested
  against AMIS restriction histories in `data/amis_policies/`.

Design constraints:
- No new stockholder. The purchaser is already Agrimate's strategic
  storage holder (processors, retailers, government stocks).
- A thin government layer per region reads supplier and purchaser state
  and outputs the restriction intensity, replacing the exogenous input
  read by `export_restriction_step!`. `policy_implementation_step!` is
  unchanged.
- The strategic term reuses the supplier's adaptive-expectations
  best-response structure.

Exit criteria:
- Feeding the observed AMIS restriction path in place of the rule
  reproduces the Gate 1 run, and with substitution off the accepted
  Gate 0 run.
- ω = 0 for all countries gives the pure threshold cascade; ω = 1 gives
  pure myopic best response.
- Hindcast of 2007/08 and 2010/11 gets the broad ordering of who
  restricted first and who followed (from step 2c on).
- Fragility map: probability of a restriction cascade as a function of
  shock size and ω.

**Gate 3 (later): great-power strategy.** A small block of major players
(for example US, Russia, China, Brazil, EU, India) whose strategic term is
solved to Nash equilibrium within the block (best responses iterated to
convergence); all other countries keep the Gate 2 rule.
- Iteration off reproduces Gate 2.
- Convergence is reached, or non-convergence is detected and reported.

## Deferred

- Full multi-agent architecture.
- Fertilizer and other input markets.
- Chokepoint shocks (Hormuz `route_multiplier` hook from the retired
  Python host; would need re-implementing on `agrimate_julia/`).
- Additional grains (barley, sorghum, rye).
- Government shift of the purchaser's storage target (the lever TWIST set
  by hand for China's drawdown and later restocking).
- State-dependent ω: governments shift toward reactive behavior under
  crisis pressure. A dual-process (Kahneman System 1 and System 2) framing
  belongs here, motivating a specific equation, not as a relabeling of
  the reactive and strategic terms.

## Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-08 | Three grains: wheat, rice, maize | Cover food-to-food and food-to-feed substitution |
| 2026-08 | Reserves from USDA PSD only in public-data inputs | FAOSTAT stocks are food-balance residuals |
| 2026-10 | Gate 2 uses a blended reactive and strategic rule, not a Nash game | 2007/08 restrictions were sequential and reactive; Nash assumptions (rationality, common knowledge, known payoffs) are weakest in crises |
| 2026-10 | Strategic term is myopic, one step ahead | Defensible under bounded rationality; computable |
| 2026-10 | Nash kept as a nested limit, used only for a great-power block in Gate 3 | Defensible for a few major players, not for dozens of exporters in a panic |
| 2026-10 | Government layer sets restrictions; no second strategic stockholder | Agrimate's purchaser already is the strategic storage holder, continuing TWIST's consumer-side holder |
| 2026-10 | Prior for ω from regional strategic versus commercial stock balance, tested on AMIS histories | Uses observed stockholding policy already in the model |
| 2026-10 | Development in Cursor, one gate at a time; Claude chat for theory, review and writing | Token and attention budget |
