# Gate 0 specification-to-code matrix

Sources: Kuhla et al. 2025, *Ecol. Econ.* 231, 108546. Author code
https://doi.org/10.5281/zenodo.14022004 **retrieved 2026-09-16** as the
executable specification (not copied). Independent implementation, not a
bit-reproduction. Data 10688435 not unpacked.

| Mechanism | Agrimate source | Legacy SHEAF | New code | Verification |
|---|---|---|---|---|
| 27 wheat regions | Zenodo `AgrimateRegionsWheat` (paper said 28) | 18 SHEAF nodes | `regions.py` | `len(regions)==27` |
| Process order | §D.3 | sequential map | `model.py` | comments vs D.3 |
| Harvest expectation | Eq. D.1; author `expected_harvests.jl` | φ blend | `equations.expected_harvest` | `test_harvest_weights_d1a` (near-term w high) |
| Restriction expectation | Eq. D.2 | current τ | `expected_restriction` | `test_restriction_expectation_d2` |
| Sales | Eq. D.3 | residual offers | `fulfill_sales` | `test_sales_domestic_priority_and_restriction` |
| Supplier plan | D.11–D.21; author `producer_optimization.jl` | fill-target ask | `optimize.solve_supplier_plan` | fractions + p_sto + x_min penalty |
| Inverse demand | D.7; code αI=3.2 | scarcity blend | `inverse_demand` | world XI* scale |
| Rivals' expected XI | D.22; τ_exp=0.5 | n/a | `model.py` `q_oth` | offer floor binds = 0 |
| αD,r | D.10 / D.9 | n/a | `wheat_data.py` | `test_alpha_d10_matches_export_share` |
| Purchaser CES | D.30 lower tier σ=2 | Armington | `purchaser_demand` | `test_purchaser_demand_sums_when_prices_equal` |
| Consumer CES | D.35; εc=0.1 | isoelastic food | `consumption_ces` | `test_consumption_capped_and_price_response` |
| Nash init | §D.5; α=3 | none / twin pin | `nash_ibr` | not a price pin |
| World price | §5.2 international tx | blend + pin | `model.py` | index O(1) |
| Harvest shape | E.27 author raised-cosine | triangular | `harvest.py` | `test_harvest_profile_normalised` |
| Restrictions | E.4 / AMIS | extra AMIS types | `restrictions.py` | wheat matrix nonempty |
| Baseline quantities | FAOSTAT FB E.1 | USDA+E0 | USDA PSD + E0 rescale | labelled A1 |
| Storage cost | Tbl. D.8 p_sto=0.1 / Nyear | cover rule | `optimize.py` unit costs | G0-S |
| x_min | Tbl. D.8 0.2 even spread | n/a | quadratic penalty, ζ=0 | G0-S |

Unresolved (labelled, not guessed): β/τ_P local price; D.30a upper-tier purchaser; FAOSTAT FB vs USDA; paper 28 vs code 27; D.8 αI=3.5 vs code 3.2.
