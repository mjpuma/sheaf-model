# Export-restriction typology (for next week)

Michael Puma, 8 October 2026. Source:
`SHEAFModel_docs/Export_Restriction_Typologyv2.docx`.

**Status.** Background for Gate 2. Discuss with colleagues next week.
Do **not** code from this note. Gate 2 stays blocked until Gate 1 is
accepted. This is not a clustering or Markov task.

## For now (keep this light)

When we impose an export restriction, **who** restricts may matter as
much as how much supply is withheld. Countries differ in market weight
and in how long they can sustain a restriction.

Optional, only if it fits existing runs: tag the main exporters of each
commodity on three yes/no questions.

1. **Big exporter?** Roughly 10% or more of world exports.
2. **Consumers sensitive?** A domestic price spike would hurt (staple,
   large poor or urban population).
3. **Farmers export-dependent?** A large share of production is
   exported, so farmers lose when exports stop (prices fall, stocks
   pile up).

Questions 1–2 say whether a restriction is plausible and consequential.
Question 3 says how long it could last. Indonesia’s palm-oil ban
(April–May 2022) was lifted after about a month because farm-gate
prices collapsed and storage filled.

A simple experiment later: withhold the **same volume** from two or
three exporters of different types; then short vs long duration for an
export-dependent exporter.

**What not to do now.** No clustering, regressions, or Markov models.
No claims about why countries restrict. The data cover only a few big
episodes (2007–08, 2010–11, 2022, 2023 India rice).

| Example (illustrative) | Big exporter? | Consumers sensitive? | Farmers export-dependent? | What happened |
|---|---|---|---|---|
| India, rice | Yes | Yes | Lower | Restrictions in 2007–08 and 2023 |
| Russia, wheat | Yes | Moderate | Yes | Ban in 2010; quotas and floating duty since 2021 |
| Indonesia, palm oil | Yes | Yes | Yes | Ban April–May 2022, lifted after ~1 month |
| United States, wheat | Yes | No | Yes | Rarely restricts |

## After the deadline

Classify **country × commodity**, not country. Three dimensions, kept
separate: **capacity** (export share, thinness, substitutes),
**vulnerability** (consumer side vs producer-side duration limit),
**objective** (inferred; weakest link). Methods from rule-based types
up to latent class only if a simpler step leaves a clear question.
Estimated behavioral rules are alternative scenarios, not the baseline.

Guardrails: “consistent with” / “in the episodes observed”; report how
many events support each category; hold out one episode when estimating;
keep experiment consequences separate from who actually restricted.

Starting references: Martin & Anderson (2012) *AJAE*; Giordani, Rocha
& Ruta (2016) *JIE*; Glauber, Laborde & Mamun (IFPRI tracker).
