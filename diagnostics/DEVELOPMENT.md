# Development plan

**Current phase:** Gate 0 wheat on the vendored Julia Agrimate host
(`agrimate_julia/`). The code path **reproduces** the published wheat run
when given the authors’ calibration
([`gate0_julia/J10_authorbaseline.md`](gate0_julia/J10_authorbaseline.md)).
Gate 1 and Gate 2 stay **blocked** until you accept stage **G0-P**.

Canonical contract: [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md).
This file is the living queue.

## What “publishable Gate 0” means

Agrimate (Kuhla, Kubiczek, Puma & Otto 2025, *Ecol. Econ.* 231:108546) is
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

**Pass rule for unlocking G1:** you accept G0-P. J10 is necessary
evidence, not the acceptance itself.

## Sequence

| Stage | Work | Status |
|---|---|---|
| **G0-N** | Supplier programme runs on the 24-step wheat year | **Met** (published code, exit 0) |
| **G0-S** | Source in hand (Zenodo 14022004), vendored | **Met** (`agrimate_julia/`) |
| **G0-U** | Three scenarios on that source | **Met** (J2, J3, J10) |
| **G0-H** | Match the author wheat NetCDF | **Met for the code path (J10).** Public-data reconstruction fails (J4/J8/J9) |
| **G0-P** | You accept wheat Gate 0 as the SHEAF market baseline | **Open** |
| **G1** | Cross-crop substitution. Disabled G1 recovers G0 | Blocked |
| **G2** | Government restriction game. Disabled G2 recovers AMIS | Blocked |

## Hard stops

- Do not implement Gate 1 or Gate 2 while G0-P is open.
- Do not edit `agrimate_julia/` economics without an `UPSTREAM.md` line.
- Do not `Pkg.update()` / `Pkg.resolve()`. Julia 1.6.5.
- Do not restore the Python hosts except from tag `pre-reorg-20261007`.
- Do not retune to the Pink Sheet or to close the J4/J8/J9 gap.

## Next after G0-P

Gate 1 adjustments to the cloned Agrimate code, marked in
`agrimate_julia/UPSTREAM.md`. Input generation for new scenarios uses
`inputs/from_data.py` plus Agrimate `preprocess.jl`.
