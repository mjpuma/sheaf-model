"""Agrimate step (supplement §D.3) and wheat runner."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from sheaf.calendar24 import STEPS_PER_YEAR

from .equations import (
    consumption_ces,
    consumer_price_mix,
    expected_harvest,
    expected_restriction,
    extra_storage_demand,
    fulfill_sales,
    inverse_demand,
    inverse_of_inverse_demand,
    purchaser_demand,
    update_producer_storage,
)
from .optimize import nash_ibr, solve_supplier_plan
from .params import AgrimateParams, wheat_params
from .wheat_data import WheatData, prepare_wheat


@dataclass
class AgrimateResult:
    start_year: int
    end_year: int
    regions: list[str]
    price_index: np.ndarray
    price_usd: np.ndarray
    S_producer: np.ndarray
    S_consumer: np.ndarray
    failed_solves: int
    fallback_solves: int
    nash: dict
    notes: list[str] = field(default_factory=list)
    consumption: np.ndarray | None = None
    xi_ship: np.ndarray | None = None

    def to_monthly_price(self) -> np.ndarray:
        p = np.asarray(self.price_usd, float)
        n = (p.size // 2) * 2
        p = p[:n].reshape(-1, 2).mean(axis=1)
        return p


def _purchaser_baseline(H_star, p_wld, C_star, Psi, A_c, params: AgrimateParams) -> dict:
    n_r, n_y = H_star.shape
    n_del = params.n_del
    D_tot = inverse_of_inverse_demand(p_wld, params.alpha_nash, params.lam_demand)
    D_s = D_tot[None, :] * (C_star[:, None] / max(float(C_star.sum()), 1e-12) * n_r)
    I = np.roll(D_s, n_del, axis=1)
    C = np.repeat(C_star[:, None], n_y, axis=1)
    S = np.empty_like(C)
    p_c = np.repeat(p_wld[None, :], n_r, axis=0)
    for _ in range(20):
        for s in range(n_r):
            flow = I[s] - C[s]
            integ = np.cumsum(flow)
            S[s] = integ - integ.mean() + Psi[s] * n_y * C_star[s]
            S[s] = np.maximum(S[s], 0.0)
        p_new = np.empty_like(p_c)
        for s in range(n_r):
            p = p_c[s, -1]
            Ss = S[s, -1]
            for n in range(n_y):
                p = consumer_price_mix(p_wld[(n - n_del) % n_y], I[s, n], p, Ss)
                p_new[s, n] = p
                Ss = S[s, n]
            p_c[s] = p_new[s]
        C_new = np.empty_like(C)
        for s in range(n_r):
            C_new[s] = np.array([
                consumption_ces(p_c[s, n], A_c[s], params.eps_c, C_star[s])
                for n in range(n_y)
            ])
            mean = C_new[s].mean()
            if mean > 0:
                C_new[s] *= C_star[s] / mean
        if float(np.max(np.abs(C_new - C))) < 1e-6:
            C = C_new
            break
        C = 0.5 * C + 0.5 * C_new
    B_c = np.mean(p_c * C, axis=1) / np.maximum(A_c, 1e-8)
    B_d = np.mean(p_wld[None, :] * D_s, axis=1) / 0.2
    return {"C": C, "S": S, "p_c": p_c, "B_c": B_c, "B_d": B_d, "I": I}


class AgrimateSim:
    def __init__(self, data: WheatData, params: AgrimateParams | None = None,
                 use_restrictions: bool = True, use_anomalies: bool = True):
        self.data = data
        self.params = params or wheat_params()
        self.use_restrictions = use_restrictions
        self.use_anomalies = use_anomalies
        self.n_r = len(data.regions)
        self.n_y = self.params.n_year
        self.n_years = data.end_year - data.start_year + 1
        self.n_steps = self.n_years * self.n_y

    def harvest_at(self, t: int) -> np.ndarray:
        y, ys = divmod(t, self.n_y)
        H = self.data.H_star[:, ys]
        if self.use_anomalies:
            H = H * (1.0 + self.data.anomaly[:, y])
        return np.maximum(H, 0.0)

    def delta_at(self, t: int) -> np.ndarray:
        if not self.use_restrictions:
            return np.zeros(self.n_r)
        return self.data.delta[:, t]

    def run(self) -> AgrimateResult:
        p = self.params
        d = self.data
        n_r, n_y, T = self.n_r, self.n_y, self.n_steps
        nash = nash_ibr(d.H_star, d.alpha_d, d.XI_star, d.XD_star, p)
        # initial plans: Nash year, tiled
        plan_d = np.tile(nash["xd"], (1, self.n_years))
        plan_i = np.tile(nash["xi"], (1, self.n_years))
        if plan_d.shape[1] < T:
            pad = T - plan_d.shape[1]
            plan_d = np.concatenate([plan_d, plan_d[:, :pad]], axis=1)
            plan_i = np.concatenate([plan_i, plan_i[:, :pad]], axis=1)
        plan_d = plan_d[:, :T]
        plan_i = plan_i[:, :T]

        S_p = np.zeros(n_r)
        S_c = np.maximum(d.Psi * n_y * d.C_star, 0.0)
        offer = np.ones(n_r)
        p_c = np.ones(n_r)
        # delivery queue: length n_del, each slot (n_r, n_r) international + domestic vector
        q_i = [np.zeros(n_r) for _ in range(p.n_del)]
        q_p = [np.ones(n_r) for _ in range(p.n_del)]

        price_index = np.ones(T)
        S_p_path = np.zeros((n_r, T))
        S_c_path = np.zeros((n_r, T))
        C_path = np.zeros((n_r, T))
        xi_path = np.zeros((n_r, T))
        failed = 0
        fallback = 0

        shares = d.T_star.copy()
        rs = shares.sum(axis=0, keepdims=True)
        shares = np.divide(shares, np.maximum(rs, 1e-12))

        for t in range(T):
            # 1 harvest  2 policy
            H = self.harvest_at(t)
            delta = self.delta_at(t)
            # 3 sales (previous plan for this step)
            sold_d = np.zeros(n_r)
            sold_i = np.zeros(n_r)
            avail = S_p + H
            for r in range(n_r):
                sd, si = fulfill_sales(plan_d[r, t], plan_i[r, t], avail[r], delta[r])
                sold_d[r], sold_i[r] = sd, si
                S_p[r] = update_producer_storage(S_p[r], H[r], sd, si, p.delta_loss)
            xi_path[:, t] = sold_i
            # 4 plan for remaining year (re-solve each step; horizon = n_year)
            y, ys = divmod(t, n_y)
            H_year = np.stack([self.harvest_at(y * n_y + k) for k in range(n_y)], axis=1)
            for r in range(n_r):
                others = np.zeros(n_y)
                for k in range(n_y):
                    tt = min(y * n_y + k, T - 1)
                    others[k] = float(plan_i[:, tt].sum() - plan_i[r, tt])
                dhat = expected_restriction(float(delta[r]), n_y)
                Hhat = expected_harvest(d.H_star[r], H_year[r], n_y)
                x0 = np.concatenate([d.XD_star_path[r], d.XI_star_path[r]])
                sol = solve_supplier_plan(
                    Hhat, float(S_p[r]), others,
                    d.XI_star_path[r], d.XD_star_path[r],
                    p.alpha_i, float(d.alpha_d[r]), p,
                    delta_hat=dhat, x0=x0,
                )
                if not sol["success"]:
                    failed += 1
                if sol["fallback"]:
                    fallback += 1
                if sol["success"] and not sol["fallback"]:
                    for k in range(n_y):
                        tt = y * n_y + k
                        if tt < T:
                            plan_d[r, tt] = sol["xd"][k]
                            plan_i[r, tt] = sol["xi"][k]
                q_next = sol["xi"][(ys + 1) % n_y] if (sol["success"] and not sol["fallback"]) else plan_i[r, min(t + 1, T - 1)]
                oth_next = others[(ys + 1) % n_y]
                star_w = float(d.XI_star_path[:, (ys + 1) % n_y].sum())
                q_i_arg = (q_next + oth_next) / max(star_w, 1e-8)
                offer[r] = float(inverse_demand(q_i_arg, p.alpha_i, p.lam_demand,
                                                p.demand_arg_floor))
                if abs(offer[r] - 1.0) < p.iota:
                    offer[r] = 1.0
            # 6 delivery: push today's international sales, pop lag
            ship = sold_i.copy()
            ship_p = offer.copy()
            q_i.append(ship)
            q_p.append(ship_p)
            arrive = q_i.pop(0)
            arrive_p = q_p.pop(0)
            # 7–9 consume / account / procure
            world_vol = float(np.sum(arrive))
            if world_vol > 1e-12:
                p_w = float(np.dot(arrive, arrive_p) / world_vol)
            else:
                p_w = float(price_index[t - 1] if t else 1.0)
            price_index[t] = p_w
            for s in range(n_r):
                prices = np.maximum(offer * (1.0 + 0.0 * d.nu[s]), 1e-8)
                bud = max(d.A_d[s] * d.C_star[s] * n_y * max(p_w, 1e-8) / n_y, 1e-8)
                # extra storage demand
                S_star = d.Psi[s] * n_y * d.C_star[s]
                extra = extra_storage_demand(S_c[s], S_star, p.tau_steps)
                q = purchaser_demand(prices, bud + max(extra, 0.0) * p_w, p.sigma_ces, shares[:, s])
                inflow = float(arrive[s]) + float(sold_d[s])
                p_c[s] = consumer_price_mix(p_w, inflow, p_c[s], S_c[s])
                cons = consumption_ces(p_c[s], d.A_c[s], p.eps_c, d.C_star[s])
                cons = min(cons, S_c[s] + inflow)
                S_c[s] = max(S_c[s] + inflow - cons, 0.0)
                C_path[s, t] = cons
            S_p_path[:, t] = S_p
            S_c_path[:, t] = S_c

        notes = list(d.notes)
        notes.append(
            f"Nash IBR: {nash['iterations']} iters, err={nash['err']:.3e}, "
            f"success={nash['success']}.")
        notes.append(
            f"Supplier solves: failed={failed}, fallback={fallback} of {n_r * T}.")
        return AgrimateResult(
            start_year=d.start_year, end_year=d.end_year, regions=d.regions,
            price_index=price_index, price_usd=price_index * d.p0,
            S_producer=S_p_path, S_consumer=S_c_path,
            failed_solves=failed, fallback_solves=fallback, nash=nash,
            notes=notes, consumption=C_path, xi_ship=xi_path,
        )


def run_agrimate(data: WheatData | None = None, use_restrictions: bool = True,
                 use_anomalies: bool = True, start_year: int = 2003,
                 end_year: int = 2011, params: AgrimateParams | None = None
                 ) -> AgrimateResult:
    if data is None:
        data = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    return AgrimateSim(data, params=params, use_restrictions=use_restrictions,
                       use_anomalies=use_anomalies).run()


def run_wheat(**kwargs) -> AgrimateResult:
    return run_agrimate(**kwargs)
