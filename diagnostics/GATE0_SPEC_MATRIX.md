# Gate 0 specification-to-code matrix

Sources: Kuhla et al. 2025, *Ecol. Econ.* 231, 108546. Author code
https://doi.org/10.5281/zenodo.14022004 **retrieved 2026-09-16** as the
executable specification (not copied). Independent implementation, not a
bit-reproduction. Data 10688435 unpacked for Fig. 4 series (P7); not a
replication.

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
| Purchaser CES | D.30 + D.30a; wheat `determine_demands` | Armington | `purchaser_demand` nested | `test_d30a_*`; A_d=1 recovers D.30 |
| Consumer CES | D.35; εc=0.1 | isoelastic food | `consumption_ces` | `test_consumption_capped_and_price_response` |
| Nash init | §D.5; α=3 | none / twin pin | `nash_ibr` | not a price pin |
| World price | §5.2 international tx; XI-weighted lagged D.7 offers × p0 | blend + pin | `model.py` `volume_weighted_offer_index` | R3 host identity; not D.7 of world XI*; 14022004 `plot_wm_price_timeseries` still not in-tree; not a 2006 pin |
| Harvest shape | E.27 author raised-cosine | triangular | `harvest.py` | `test_harvest_profile_normalised` |
| Restrictions | E.4 / AMIS OECD columns PolicyMeasure_Name, CommodityClass_Name | extra AMIS types | `restrictions.py` | wheat Δ nonempty 2007/08 |
| Baseline quantities | FAOSTAT FB E.1 | USDA+E0 | USDA PSD + E0 rescale | A1; raw FBSH vendored; labelled `prepare_wheat_fbsh` not adopted (`fb_wheatdata.md`); USDA default |
| Storage cost | Tbl. D.8 p_sto=0.1 / Nyear | cover rule | `optimize.py` unit costs | G0-S |
| x_min | Tbl. D.8 0.2 even spread | n/a | quadratic penalty, ζ=0 | G0-S |
| Three-scenario validation | Agrimate Fig. 4 design; Bai/Wada/Puma copy workflow | Pink-Sheet only | `validation.py` / `run_agrimate_validation.py` | prices **and** USDA supply/stocks |
| Fig. 4 author series | Zenodo 10688435 main_output NetCDF (AgrimateEU28+Egypt, FAO, αI=3.5) | PDF digitisation (unused) | `fig4.py` / `score_agrimate_fig4.py` | P7 `fig4.md`; independent, not replication |
| G0-H hindcast note | Agrimate Fig. 4 + Pink Sheet levels and paths | price corr only | `hindcast.py` / `score_agrimate_hindcast.py` | P8 `hindcast.md`; sourced shortfall, no retune |
| Regional USDA | `psd_regional_annual()` vs named nodes | world PSD only | `regional.py` / `score_agrimate_regional.py` | P9 `regional.md`; A8 mean-of-members labelled, no xmin fit |
| OAT sensitivity | diagnostic around author params | n/a | `oat_settings()` | P6 2006–08: αI/p_sto/xmin move hike; εc/σ silent; Bai 10 listed, not adopted |
| Exporter pulse grid | prescribed Δ, G0-H/P | n/a | `restriction_pulse` / `pulse.py` | P11 `pulse.md`; 8-run 2008 clean; not 36; not G2 |
| Step accounting | D.6 / D.3 / consumer clip | n/a | `accounting.py` | `test_2006_harvest_amis_path_identities` |
| International delivery | E.1 T* to importers, Ndel lag | own-XI echo (bug) | `international_destination_shares` | `test_international_sales_are_not_echoed_to_the_exporter` |
| Local price β, τ_P | author `AgrimateParams`; `determine_target_price_adjustment_factor` | n/a | unused fields on `AgrimateParams` | P3: wheat `two_markets` pins P_loc=1; `test_beta_loc_does_not_enter_supplier_plan` |
| Unconverged L-BFGS-B | scipy `success=False` on feasible fraction plans | n/a | counted; `plan_maxiter=40` | P5 `solver.md`; not dropped |
| G0-P methods note | Agrimate wheat market section | n/a | `methods.py` / `score_agrimate_methods.py` | P12 `methods.md`; written; **not accepted** |
| Post-P12 red team | DEVELOPMENT items 1–6 vs live host | n/a | `GATE0_REDTEAM.md` / `GATE0_DATA.md` | R1 inventory; not a retune |
| Fig. 4-config comparison | NetCDF αI=3.5, ζ=1, N_for=6 | n/a | `fig4_experiment_params` / `fig4_config.py` | R2 labelled; not `wheat_params()` |
| World-price recipe | §5.2; host mix vs author `plot_wm_price_timeseries` | n/a | `volume_weighted_offer_index` / `world_price.md` | R3 host identity; Julia absent |
| Fig. 4 knobs vs author | R2 2006–08 run vs `author_fig4/` | n/a | `fig4_author_score.py` / `fig4_config_score.md` | R10 not a match; remaining A7 |
| N5 on Fig. 4 knobs | P5 unconverged split on R2 object | n/a | `fig4_solver.py` / `solver_fig4.md` | R9; `plan_maxiter=40` kept; next R4 |
| Undisturbed xd/xi | item 3 last/first 1.630 vs author 1.004 | n/a | `xi_split.py` / `xi_split.md` | R4; D.22 `q_oth` freeze 1.019 (not adopted); xmin/calendar overshoot |
| S4 x1=demand | author two-market x1 := D.30/D.30a requests | T*+domestic | `x1_from_demand` / `x1_demand.md` | R5 labelled, default off; p_w silent; not adopted |

Unresolved (labelled, not guessed): paper 28 vs code 27;
D.8 αI=3.5 vs code 3.2. FAOSTAT FB vs USDA is A1 (P10: arrays not in
`data/faostat_network/`; USDA default). Fig. 4 used the D.8 αI=3.5 / EU28+Egypt / FAO
executable (P7), not the 14022004 wheat defaults. β/τ_P unused on wheat
path (S3). D.30a formula wired; author x1=demand labelled, default off (S4/R5).
Unconverged plans labelled N5.
