"""Gate 1: three Gate 0 crops coupled by isoelastic cross-price demand.

``subst_scale=0`` must recover three independent ``run_crop_dynamics`` paths.
Industrial/ethanol use does not substitute. CropParams stay locked.
See diagnostics/GATE1_PLAN.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .calendar24 import STEPS_PER_YEAR
from .calibration import GRAINS, RHO
from .dynamic_crop import (
    MAX_LEAN_STEPS,
    CropPrep,
    CropSimResult,
    _ask_reweight_dest,
    _bilateral_clear,
    default_crop_params,
    prepare_crop_run,
)
from .seasonal import rolling_ahead_variable, steps_to_harvest_pulse

# Score order; RHO in calibration is wheat, rice, maize.
COUPLED_GRAINS = ("wheat", "rice", "maize")


def cross_price_eta(subst_scale: float,
                    grains: tuple[str, ...] = COUPLED_GRAINS) -> np.ndarray:
    """(G,G) isoelastic exponents. Own ε from Gate 0 CropParams; ρ from calibration."""
    G = len(grains)
    idx = {g: i for i, g in enumerate(GRAINS)}
    eta = np.zeros((G, G))
    elast = np.array([default_crop_params(g).elast for g in grains], float)
    for a, ga in enumerate(grains):
        eta[a, a] = elast[a]
        ia = idx[ga]
        for b, gb in enumerate(grains):
            if a == b:
                continue
            ib = idx[gb]
            eta[a, b] = float(subst_scale) * float(RHO[ia, ib]) * abs(elast[a])
    return eta


@dataclass
class CoupledSimResult:
    grains: tuple[str, ...]
    countries: list[str]
    start_year: int
    end_year: int
    subst_scale: float
    by_crop: dict[str, CropSimResult]


def _simulate_coupled(preps: list[CropPrep], eta: np.ndarray
                      ) -> list[CropSimResult]:
    """Jacobi step: all flex demands from p_t, then each Gate 0 market, then prices."""
    G = len(preps)
    n = len(preps[0].countries)
    T = preps[0].H.shape[1]
    p0 = np.array([pr.p0 for pr in preps], float)
    p = p0.copy()
    stock = [pr.stock0.copy() for pr in preps]
    ask = [np.full(n, float(pr.p0)) for pr in preps]

    price = [np.zeros(T) for _ in range(G)]
    stock_path = [np.zeros((n, T)) for _ in range(G)]
    cons_path = [np.zeros((n, T)) for _ in range(G)]
    exp_path = [np.zeros((n, T)) for _ in range(G)]
    free_path = [np.zeros(T) for _ in range(G)]
    unmet_path = [np.zeros(T) for _ in range(G)]
    offer_path = [np.zeros((n, T)) for _ in range(G)]
    demand_path = [np.zeros((n, T)) for _ in range(G)]
    ask_path = [np.zeros((n, T)) for _ in range(G)]
    recv_path = [np.zeros((n, T)) for _ in range(G)]
    trade_path = [np.zeros((n, n, T)) for _ in range(G)]

    H_exp, C_step, H_ahead, C_ahead = [], [], [], []
    carry_cap, food_step, safety_w = [], [], []
    for pr in preps:
        params = pr.params
        Cs = pr.C_flex + pr.C_ind
        Hx = (params.foresight_phi * pr.H
              + (1.0 - params.foresight_phi) * pr.H_seas)
        lh = steps_to_harvest_pulse(
            Hx, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
        H_exp.append(Hx)
        C_step.append(Cs)
        H_ahead.append(rolling_ahead_variable(Hx, lh))
        C_ahead.append(rolling_ahead_variable(Cs, lh))
        carry_cap.append(params.max_stu * pr.C_ann)
        food_step.append(pr.C_ann / STEPS_PER_YEAR)
        safety_w.append(float(max(pr.safety.sum(), 1.0)))

    for t in range(T):
        rel = np.maximum(p / p0, 1e-6)
        fac = np.exp(eta @ np.log(rel))
        new_p = np.zeros(G)
        new_ask = []
        new_stock = []
        for g, pr in enumerate(preps):
            params = pr.params
            avail = stock[g] + pr.H[:, t]
            desired_flex = np.maximum(pr.C_flex[:, t] * fac[g], 0.0)
            desired = desired_flex + pr.C_ind[:, t]
            lean_gap = np.maximum(
                0.0,
                C_ahead[g][:, t] + C_step[g][:, t]
                - H_ahead[g][:, t] - H_exp[g][:, t],
            )
            target = lean_gap + pr.safety
            after_food_stock = np.maximum(0.0, avail - desired)
            food_need = np.maximum(0.0, desired - avail)
            rebuild = params.rebuild_lambda * np.maximum(
                0.0, target - after_food_stock)
            demand = food_need + rebuild
            offers = np.maximum(0.0, avail - desired - target) * (
                1.0 - pr.cuts[:, t])
            offer_path[g][:, t] = offers
            demand_path[g][:, t] = demand
            ask_path[g][:, t] = ask[g]

            A_eff = _ask_reweight_dest(
                pr.A, ask[g], pr.p0, gamma=params.ask_comp_elast)
            shipped, received, ship = _bilateral_clear(
                offers, demand, A_eff, pr.S, subst=params.residual_subst)
            recv_path[g][:, t] = received
            trade_path[g][:, :, t] = ship

            consumption = np.minimum(
                desired, np.maximum(0.0, avail - shipped + received))
            st = np.maximum(0.0, avail - shipped - consumption + received)
            warehouse = (
                carry_cap[g]
                + food_step[g] * float(params.pipeline_max_steps)
                + (pr.H[:, t] if params.pipeline_max_steps > 0 else 0.0)
            )
            excess = np.maximum(0.0, st - warehouse)
            st = st - params.warehouse_lambda * excess

            fill = shipped / np.maximum(offers, 1e-9)
            fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
            total_d = float(demand.sum())
            preferred_block = float(
                (pr.S * pr.cuts[:, t][:, None] * demand[None, :]).sum())
            block_frac = preferred_block / max(total_d, 1e-9)
            rival = float(max(params.ask_rival, 0.0)) * block_frac
            ask_g = ask[g] * np.exp(
                params.ask_alpha * (fill - params.ask_target_fill)
                + np.where(offers > 1e-9, rival, 0.0))
            ask_g = (1.0 - params.ask_beta) * ask_g + params.ask_beta * p[g]
            ask_g = np.clip(ask_g, 0.45 * pr.p0, 2.8 * pr.p0)

            lean_need = float(lean_gap.sum())
            locked = float(
                (pr.cuts[:, t] * np.maximum(0.0, st - target)).sum())
            free = float(st.sum()) - lean_need - locked
            free_path[g][t] = free
            unmet = max(0.0, total_d - float(received.sum()))
            unmet_frac = unmet / max(total_d, 1e-9)
            unmet_path[g][t] = unmet_frac

            shipped_sum = float(shipped.sum())
            p_trade = (float(np.dot(ask_g, shipped) / shipped_sum)
                       if shipped_sum > 1e-12 else p[g])

            twin = float(pr.free_twin[t])
            floor0 = 0.05 * safety_w[g]
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)
            u0 = float(pr.unmet_twin[t])
            u_anom = max(0.0, unmet_frac - u0)
            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = pr.p0
            else:
                ratio = float(max(ratio, 1e-12))
                free_term = ratio ** params.inv_eta
                p_scar = (pr.p0 * free_term
                          * (1.0 + params.unmet_kappa * u_anom
                             + params.block_kappa * block_frac))
                p_star = (params.trade_w * p_trade
                          + (1.0 - params.trade_w) * p_scar)

            pg = float(params.smooth * p[g] + (1.0 - params.smooth) * p_star)
            pg = float(np.clip(pg, 60.0, 1200.0))
            new_p[g] = pg
            new_ask.append(ask_g)
            new_stock.append(st)
            price[g][t] = pg
            stock_path[g][:, t] = st
            cons_path[g][:, t] = consumption
            exp_path[g][:, t] = shipped

        p = new_p
        ask = new_ask
        stock = new_stock

    out = []
    for g, pr in enumerate(preps):
        out.append(CropSimResult(
            crop=pr.crop, countries=pr.countries,
            start_year=pr.start_year, end_year=pr.end_year,
            price=price[g], stock=stock_path[g], harvest=pr.H,
            consumption=cons_path[g], exports=exp_path[g],
            export_cut=pr.cuts, spin_up_years=pr.spin_up_years,
            free_liquid=free_path[g], free_twin=pr.free_twin,
            unmet_frac=unmet_path[g], offers=offer_path[g],
            purchase_demand=demand_path[g], ask=ask_path[g],
            received=recv_path[g], trade=trade_path[g],
            params=pr.params, industrial=pr.C_ind,
        ))
    return out


def run_coupled_dynamics(
        subst_scale: float = 0.0,
        grains: tuple[str, ...] = COUPLED_GRAINS,
        start_year: int = 2006,
        end_year: int = 2011,
        use_amis: bool = True,
        use_shocks: bool = True,
        use_demand: bool = False,
        use_industrial: bool | None = None,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
        trade_window: tuple[int, int] = (2006, 2007),
) -> CoupledSimResult:
    """Official P1 flags by default (mean flex; maize industrial on via params)."""
    preps = []
    countries = None
    for g in grains:
        pr = prepare_crop_run(
            g, countries=countries, start_year=start_year, end_year=end_year,
            use_amis=use_amis, use_shocks=use_shocks, use_demand=use_demand,
            use_industrial=use_industrial,
            stock_seed_year=stock_seed_year, spin_up_years=spin_up_years,
            trade_window=trade_window)
        countries = pr.countries
        preps.append(pr)
    eta = cross_price_eta(subst_scale, grains)
    results = _simulate_coupled(preps, eta)
    return CoupledSimResult(
        grains=grains, countries=preps[0].countries,
        start_year=start_year, end_year=end_year,
        subst_scale=float(subst_scale),
        by_crop={r.crop: r for r in results},
    )


def assert_subst0_matches_gate0(tol: float = 0.005) -> None:
    """Coupled σ=0 monthly prices match independent Gate 0 runs."""
    from .dynamic_crop import result_to_monthly, run_crop_dynamics

    coupled = run_coupled_dynamics(subst_scale=0.0, use_demand=False)
    for g in coupled.grains:
        solo = run_crop_dynamics(g, use_amis=True, use_shocks=True,
                                 use_demand=False)
        a = result_to_monthly(coupled.by_crop[g])["model_price"].to_numpy()
        b = result_to_monthly(solo)["model_price"].to_numpy()
        rel = float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))
        if rel > tol:
            raise AssertionError(
                f"Gate 1 identity fail {g}: max rel monthly |Δp|={rel:.3%} "
                f"> {tol:.3%}")
