# R0h — price flexibility: SHEAF against Agrimate's alpha

Uniform proportional harvest shortfalls applied to the matched
(no-shock, no-AMIS) configuration, so the response is the model's
own transfer function rather than a crisis artefact. Flexibility is
measured as d log(mean price) / d log(harvest).

| crop | inv_eta | demand elast | flow reference 1/|elast| | measured flexibility at −1% | −2% | −5% | −10% |
|---|---|---|---|---|---|---|---|
| wheat | 1.00 | -0.15 | 6.7 | 7.62 | 1.40 | -2.47 | -4.24 |
| maize | 0.85 | -0.25 | 4.0 | 24.19 | 10.71 | 2.54 | -0.28 |
| rice | 0.95 | -0.20 | 5.0 | -4.18 | -4.56 | -4.74 | -4.85 |

Agrimate for comparison: alpha = 3.0 for the single
world market and alpha_I = 3.5 for the
international market. Both are elasticities with respect to a flow
(sales relative to baseline sales), so the like-for-like SHEAF
column is the measured flexibility, not inv_eta.

## Reading

Three numbers are on the table for each crop: what SHEAF's price
actually does (measured flexibility), what SHEAF's own demand
elasticity implies a competitive flow market should do (1/|elast|),
and what Agrimate uses (3.0 to 3.5).

If SHEAF's measured flexibility is far BELOW both references, the
model's price is structurally too insensitive to scarcity, and the
reduced-form markups -- ask_rival in particular, which A2 showed has
no surviving independent justification -- are supplying amplitude
that the price map should be generating itself. That would make the
principled repair a re-specification of the scarcity exponent or its
state variable, not a defence of ask_rival.

If instead the measured flexibility already sits in the 3 to 7 band,
SHEAF is in the same territory as Agrimate and the criticism does
not hold.

