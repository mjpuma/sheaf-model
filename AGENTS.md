# Agent instructions — SHEAF

Crisis work uses the Agrimate-faithful Gate 0 host. Read
[`diagnostics/GATE0_CONTRACT.md`](diagnostics/GATE0_CONTRACT.md) before
changing `sheaf/agrimate/`, Gate 0 docs, or the default entry point.

- **Default run:** `PYTHONPATH=. python scripts/run_agrimate_validation.py`
- **Solver smoke:** `PYTHONPATH=. python scripts/run_agrimate_wheat.py`
- **Protocol:** [`diagnostics/GATE0_VALIDATION.md`](diagnostics/GATE0_VALIDATION.md)
- **Prompt list (one per session):** [`diagnostics/GATE0_PROMPTS.md`](diagnostics/GATE0_PROMPTS.md)
  (P0–P12 done). Next paste: [`diagnostics/GATE0_REPRO_DISPATCH.md`](diagnostics/GATE0_REPRO_DISPATCH.md)
  (**S6 done**; G0-P **not accepted**; **T1–T3 done**; next **stay not-accepted**
  [`GATE0_CONTINUE.md`](diagnostics/GATE0_CONTINUE.md);
  S-queue [`GATE0_NEXT_PROMPTS.md`](diagnostics/GATE0_NEXT_PROMPTS.md)).
- **Legacy benchmark:** `python scripts/score_legacy_crop.py --crop wheat`
- **Do not** silently restore legacy Gate 0 economics if the new host fails.
- **Do not** implement substitution or the policy game inside the baseline.
- **Do not** start Gate 1 or Gate 2 work until `diagnostics/DEVELOPMENT.md`
  stage **G0-P** (publishable wheat Gate 0 vs Agrimate) is accepted.
