# Domestic exponent — 14022004 α_adj

Live `prepare_wheat` sets

`α_d = min(1, α_f · C* · XI_r* / (XI*_world · XD_r*))`

when a region has both home sales and exports, and `α_d = 1` otherwise.
That is the wheat executable's `α_adj` (default on), including the cap at 1.
Tbl. D.9 (EU-27 2.2, USA 2.0, Russia 3.0) stays on the Fig. 4 path via
`fig4_config.apply_alpha_i` only. `wheat_params()` are unchanged
(αI=3.2, ζ=0, N_for months=3). No 2006 pin. No Julia copy.

`α_d > 1` makes domestic revenue fall as sales rise, so those exporters
sold the harvest abroad and held no stock. Home purchase shares then
collapsed. July–August world price was about $0.2/t.

## Undisturbed re-measure (2003–11, anomalies off, restrictions off; scores 2006–11)

| | α_adj | clearing (D.9 α_d) | Bar B Fig. 4 baseline |
|---|---:|---:|---:|
| last/first | 0.895 | 1.777 | 1.004 |
| 2006 mean USD | 498 | 286 | — |
| 2011 mean USD | 446 | 508 | — |
| moy max/min | 20.1× | 5713× | 1.32× |
| seas corr 2006 vs 2011 | 0.965 | 0.942 | 0.991 |
| unconverged / failed | 1890/5832 / 0 | 1180/5832 / 0 | — |
| runtime | 51.1s | 62.5s | — |

2006–11 month-of-year means, USD: Jan 2314, Feb 115, Mar–May about
570–630, Jun–Nov about 190–270, Dec 577. The harvest-month collapse is
gone (Jul 222, Aug 188). The remaining 20× is January versus February.
Unconverged solves rose. S1 CSVs and `prices_undisturbed_clearing.csv`
were not rewritten. Do not start G1.
