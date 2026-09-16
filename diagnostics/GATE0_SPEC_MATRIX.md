# Gate 0 specification-to-code matrix

Sources: Kuhla et al. 2025, *Ecol. Econ.* 231, 108546. Author code
https://doi.org/10.5281/zenodo.14022004 was **not retrieved**. Independent
implementation, not a verified replication.

| Mechanism | Agrimate source | Legacy SHEAF | New code | Verification |
|---|---|---|---|---|
| 28 regions, 24-step year | §4.1; Tbl. C.1 | 18 SHEAF nodes | `regions.py` | `len(regions)==28` |
| Process order | §D.3 | sequential map | `model.py` | comments vs D.3 |
| Harvest expectation | Eq. D.1 | φ blend | `equations.expected_harvest` | `test_harvest_weights_d1a` |
| Restriction expectation | Eq. D.2 | current τ | `expected_restriction` | `test_restriction_expectation_d2` |
| Sales | Eq. D.3 | residual offers | `fulfill_sales` | `test_sales_domestic_priority_and_restriction` |
| Supplier plan | D.11–D.21 | fill-target ask | `optimize.solve_supplier_plan` | `test_supplier_plan_respects_availability`; G0-N: fractions + rolling horizon |
| Inverse demand | D.7; αI D.8=3.5 | scarcity blend | `inverse_demand` | world XI* scale (`test_international_inverse_demand_uses_world_scale`) |
| Rivals' expected XI | D.22; τ_exp D.8 | n/a | `model.py` `q_oth` | 2006 smoke: offer floor binds = 0 |
| αD,r | D.10 / D.9 | n/a | `wheat_data.py` | `test_alpha_d10_matches_export_share` |
| Purchaser CES | D.30 | Armington | `purchaser_demand` | `test_purchaser_demand_sums_when_prices_equal` |
| Consumer CES | D.35 | isoelastic food | `consumption_ces` | `test_consumption_capped_and_price_response` |
| Nash init | §D.5 | none / twin pin | `nash_ibr` | not a price pin |
| World price | §5.2 international tx | blend + pin | `model.py` | index O(1) |
| Harvest shape | E.27 | triangular | `harvest.py` | `test_harvest_profile_normalised` |
| Restrictions | E.4 / AMIS | extra AMIS types | `restrictions.py` | wheat matrix nonempty |
| Baseline quantities | FAOSTAT FB E.1 | USDA+E0 | USDA PSD + E0 rescale | labelled A1 |

Specification questions: D.8 vs F.1 (αI, τ); ζ0 wheat default; β in F.1 unimplemented; D.1b OCR; E.27 support; C.1 ISO list reconstructed from main-text named countries + UN M49.
