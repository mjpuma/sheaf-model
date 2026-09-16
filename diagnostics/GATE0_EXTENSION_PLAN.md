# SHEAF extensions after Agrimate Gate 0

**Blocked** until wheat Gate 0 passes the publishable bar in
`diagnostics/DEVELOPMENT.md` (stage G0-P). Do not implement these in
`sheaf/agrimate/`.

Recorded SHEAF objectives, which are **different mechanisms**:

1. **E1 — Cross-crop substitution** (wheat/rice/maize on the demand side).
   This is not Agrimate’s origin CES σ over exporters of one grain.
2. **E2 — Endogenous export-restriction game** among governments.
   This is not Agrimate’s supplier oligopoly (αI / αD) and not AMIS/E.4.

## Sequence after G0-P only

0. Wheat Gate 0 accepted (G0-P). Maize/rice as Agrimate single-crop
   applications only after wheat is stable; do not score them with
   inherited parameters.
1. **E1 (proposed).** Second nest over grains on the same 24-step spine.
   Origin CES stays. Disabled E1 recovers the single-crop Agrimate run.
2. **E2 (proposed).** Governments choose Δ on the Headey clock. Market
   agents still take Δ as in D.2. Disabled E2 recovers E.4-prescribed
   Agrimate.
3. Only then couple E1+E2.

Existing `sheaf/dynamic_coupled.py` / `sheaf/dynamic_policy.py` are leftover
on the **legacy** spine. They are not approved implementations of E1/E2.

## Decision-record template (copy into GATE0_DEPARTURES.md)

1. Research objective and evidence it is an agreed SHEAF objective.
2. Agrimate mechanism and exact source it would extend or replace.
3. Why preserving that mechanism is insufficient (concrete limitation).
4. Alternatives, including “keep Agrimate” and the smallest compatible extension.
5. Agents, choices, objectives, constraints, information, expectations, timing.
6. Equations, units, parameter provenance, identification, new data.
7. Economic consequences and overlap/double-counting with existing mechanisms.
8. Limiting-case test: Agrimate recovery when disabled, or why recovery is impossible.
9. Controlled experiments that could reject the proposal.
10. Questions for the Agrimate team; approval status; implementation/validation status.

Statuses: proposed | approved | implemented | validated | rejected | deferred.
Assistant-generated ideas and legacy code are not approval.
