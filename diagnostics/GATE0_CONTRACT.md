# Gate 0 modelling contract

Canonical scientific contract. `CLAUDE.md`, `AGENTS.md`, and
`.cursor/rules/gate0-agrimate.mdc` point here.

Gate 0 is the published Agrimate model (Kuhla, Kubiczek, Puma, and Otto,
*Ecological Economics* 231 (2025) 108546; ODD supplement §D; wheat §E),
run from the vendored source at `agrimate_julia/`.

- Code: `agrimate_julia/` (CC-BY 4.0; provenance in `agrimate_julia/UPSTREAM.md`)
- Reference command: `python drivers/run.py --anomalies --restrictions --t-max 312`
- Score: `python drivers/score.py`
- Evidence: `diagnostics/gate0_julia/` (J0–J10)

1. Every baseline mechanism cites paper / supplement section, equation, or table.
2. Do not edit Agrimate economics or `Params` defaults without an
   `UPSTREAM.md` entry and an explicit go-ahead.
3. Keep baseline (this host), reconstruction-from-public-data, and
   extension results labelled separately.
4. Nash initialisation ≠ dynamic baseline (§D.5).
5. **No Gate 1 or Gate 2 until Gate 0 wheat is accepted** (stage G0-P in
   `diagnostics/DEVELOPMENT.md`).

## What “reproduce Agrimate” means here

J10: the published code on the authors’ own calibration reproduces their
published wheat NetCDF (prices, stocks). That is the code-path bar.

J4/J8/J9: the same code on reconstructed USDA / FAOSTAT / AMIS inputs
does not reproduce those magnitudes. Do not retune to close that gap.
Do not treat J10 as a public-data reconstruction.
