# Gate 0 modelling contract (Agrimate baseline)

Canonical scientific contract. `CLAUDE.md`, `AGENTS.md`, and
`.cursor/rules/gate0-agrimate.mdc` point here.

Gate 0 is a source-faithful implementation of Agrimate (Kuhla, Kubiczek and
Otto, *Ecological Economics* 231 (2025) 108546; ODD supplement §D; wheat §E).

- Code: `sheaf/agrimate/` (`/agrimate/` at repo root is copyrighted PDF extracts only)
- Reference command: `python scripts/run_agrimate_wheat.py`
- Spec map: `diagnostics/GATE0_SPEC_MATRIX.md`
- Validation: `diagnostics/gate0_agrimate/validation.md`
- Legacy: `sheaf/legacy/`, `python scripts/score_legacy_crop.py --crop wheat`

1. Every baseline mechanism cites paper / supplement section, equation, or table.
2. No silent legacy fallback (fill-target 0.70, calm pin, scarcity blend, ask_rival).
3. Economic departures need an approved `diagnostics/GATE0_DEPARTURES.md` record
   *before* implementation.
4. Keep baseline, legacy, and extension results labelled separately.
5. Nash initialisation ≠ dynamic baseline (§D.5). Do not pin the unforced price.
7. **No Gate 1 or Gate 2 until Gate 0 wheat is publishable** against Agrimate
   (source fidelity, solver reliability, undisturbed dynamics, hindcast
   levels and paths). See `diagnostics/DEVELOPMENT.md`. Leftover Gate 1/2
   code is not a reason to open that work.
