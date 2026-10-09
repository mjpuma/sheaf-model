# Architecture

**Status:** Agrimate-SHEAF. Host is the vendored Julia Agrimate code
(`agrimate_julia/`).

## Scientific goal

Reproduce crisis shock dynamics (2007/08, 2010/11) on Agrimate’s own
terms, then add two extensions **in that code**: cross-commodity
substitution (Gate 1,
[`diagnostics/GATE1_DESIGN.md`](diagnostics/GATE1_DESIGN.md)) and an
endogenous restriction game (Gate 2). Wheat Gate 0 is accepted (G0-P).
Rice/maize smoke is met. Gate 1 is designed, not coded. Gate 2 stays off
until Gate 1 is accepted.

## Locked choices

| Axis | Choice |
|---|---|
| Host | Published Agrimate Julia (`agrimate_julia/`, CC-BY 4.0) |
| Time step | 24 steps / year (~15.2 days), exact month tiling |
| Dynamics | Agrimate agents: supplier NLP, consumer storage, trade QP |
| Forcing (Gate 0) | Harvest anomalies + prescribed AMIS-style restrictions |
| World price | Monthly export-weighted cross-border transaction price |
| Interpreter | Julia 1.6.5, Manifest pinned |

24 steps/year matches Agrimate §4.1. Validation targets are monthly, and
harvest calendars are monthly, so 24 = 2 × 12 is the lineage default.

## Layers

```
inputs/from_paper.py  ─┐
inputs/from_data.py   ─┴─► seven CSVs ─► agrimate_julia (simulate)
                                              │
                         drivers/score.py ◄───┘
                         plots/j10_vs_author.py
```

Parameterization of those CSVs into the model state is Agrimate’s
`src/preprocess.jl`.
