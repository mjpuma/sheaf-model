# Agent instructions — SHEAF

Crisis work uses the Agrimate-faithful Gate 0 host. Read
[`diagnostics/GATE0_CONTRACT.md`](diagnostics/GATE0_CONTRACT.md) before
changing `sheaf/agrimate/`, Gate 0 docs, or the default entry point.

- **Default run:** `python scripts/run_agrimate_wheat.py`
- **Legacy benchmark:** `python scripts/score_legacy_crop.py --crop wheat`
- **Do not** silently restore legacy Gate 0 economics if the new host fails.
- **Do not** implement substitution or the policy game inside the baseline.
- **Do not** start Gate 1 or Gate 2 work until `diagnostics/DEVELOPMENT.md`
  stage **G0-P** (publishable wheat Gate 0 vs Agrimate) is accepted.
