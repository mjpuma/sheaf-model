# Development plan

**Current phase:** wheat Gate 0 is **accepted** (G0-P, 2026-10-07). The
code path reproduces the published wheat run on the authors’ calibration
([`gate0_julia/J10_authorbaseline.md`](gate0_julia/J10_authorbaseline.md)).
Next: smoke rice and maize on the same host, then Gate 1 substitution.
Gate 2 stays blocked until Gate 1 is accepted.

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
| **G1-prep** | Rice and maize smoke on this host (`crops="rice"` / `"maize"`) | **Open** |
| **G1** | Cross-crop substitution. Disabled G1 recovers G0 | Blocked until G1-prep |
| **G2** | Government restriction game. Disabled G2 recovers AMIS | Blocked |

## Hard stops

- Do not implement substitution in `agrimate_julia/` until rice and maize
  smoke (G1-prep). Do not start Gate 2 until Gate 1 is accepted.
- Do not edit `agrimate_julia/` economics without an `UPSTREAM.md` line.
- Do not `Pkg.update()` / `Pkg.resolve()`. Julia 1.6.5.
- Do not retune to the Pink Sheet or to close the J4/J8/J9 gap.

## Next

1. Smoke rice and maize (`python inputs/from_data.py --crop rice` / `--crop maize`,
   then `python drivers/run.py --crop … --t-max 0`).
2. Gate 1 substitution in `agrimate_julia/`, listed in `UPSTREAM.md`.
   Disabled Gate 1 must recover the three independent single-crop runs.
