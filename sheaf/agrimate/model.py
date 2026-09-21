"""Agrimate step (supplement §D.3) and wheat runner."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import numpy as np

from sheaf.calendar24 import STEPS_PER_YEAR

from .equations import (
    ces_price_index,
    consumption_ces,
    consumer_price_mix,
    crop_budget_share,
    expected_harvest,
    expected_restriction,
    extra_storage_demand,
    foreign_request_quantity,
    fulfill_sales,
    inverse_demand,
    inverse_of_inverse_demand,
    purchaser_demand,
    update_producer_storage,
)
from .optimize import (
    baseline_ask_matrix,
    demand_x1_from_ask,
    nash_ibr,
    solve_supplier_plan,
)
from .params import AgrimateParams, wheat_params
from .wheat_data import WheatData, prepare_wheat, international_destination_shares

# D.22 helpers imported inside AgrimateSim.run to avoid a d22↔model cycle.

# Delivery-queue empty-volume floor. Matches the run-loop mix.
_VOL_FLOOR = 1e-12


def volume_weighted_offer_index(
    xi: np.ndarray,
    offer: np.ndarray,
    *,
    empty: float | None = None,
    vol_floor: float = _VOL_FLOOR,
) -> float:
    """World-price index as an XI-weighted mix of regional D.7 offers.

    This is **not** Eq. D.7 of world XI / XI*_world. Each region's offer
    is already D.7 of ``(XI_r + Q_{-r}) / XI*_world``; ``p_w`` is the
    volume-weighted mean of those offers. Empty volume returns ``empty``.
    """
    xi = np.asarray(xi, float).reshape(-1)
    offer = np.asarray(offer, float).reshape(-1)
    if xi.shape != offer.shape:
        raise ValueError("xi and offer must have the same length")
    vol = float(np.sum(xi))
    if vol > vol_floor:
        return float(np.dot(xi, offer) / vol)
    if empty is None:
        raise ValueError("empty international volume and no fallback price")
    return float(empty)


def lagged_offer_index(
    xi_path: np.ndarray,
    offer_path: np.ndarray,
    n_del: int,
    *,
    empty0: float = 1.0,
    vol_floor: float = _VOL_FLOOR,
) -> np.ndarray:
    """Replay the Ndel delivery queue used for ``price_index``.

    Initial frames are zeros (XI) and ones (offers), matching
    ``AgrimateSim.run``. Step ``t`` reports the mix of the XI and
    offers enqueued ``n_del`` steps earlier.
    """
    xi = np.asarray(xi_path, float)
    offer = np.asarray(offer_path, float)
    if xi.ndim != 2 or xi.shape != offer.shape:
        raise ValueError("xi_path and offer_path must be (R, T) and aligned")
    n_r, T = xi.shape
    n_del = int(n_del)
    if n_del < 0:
        raise ValueError("n_del must be nonnegative")
    q_i = [np.zeros(n_r) for _ in range(n_del)]
    q_p = [np.ones(n_r) for _ in range(n_del)]
    out = np.empty(T, dtype=float)
    prev = float(empty0)
    for t in range(T):
        q_i.append(xi[:, t].copy())
        q_p.append(offer[:, t].copy())
        xi_lag = q_i.pop(0)
        p_lag = q_p.pop(0)
        out[t] = volume_weighted_offer_index(
            xi_lag, p_lag, empty=(prev if t else float(empty0)),
            vol_floor=vol_floor)
        prev = out[t]
    return out


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
    harvest: np.ndarray | None = None
    sold_domestic: np.ndarray | None = None
    p_consumer: np.ndarray | None = None
    inflow: np.ndarray | None = None
    floor_binds: int = 0
    unconverged_solves: int = 0
    plan_residual: float = 0.0
    runtime_s: float = 0.0
    use_anomalies: bool = True
    use_restrictions: bool = True
    offer: np.ndarray | None = None
    x1_from_demand: bool = False

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
                 use_restrictions: bool = True, use_anomalies: bool = True,
                 replan_stride: int = 1, freeze_q_oth: bool = False,
                 x1_from_demand: bool = False):
        self.data = data
        self.params = params or wheat_params()
        self.use_restrictions = use_restrictions
        self.use_anomalies = use_anomalies
        # Diagnostic hooks (R4). Defaults recover the live host.
        # replan_stride=1: every step (N2 rolling year). 24 = January only.
        # freeze_q_oth: hold D.22 Q at seasonal init (no shift+EMA).
        self.replan_stride = max(int(replan_stride), 1)
        self.freeze_q_oth = bool(freeze_q_oth)
        # R5: S4 labelled experiment. Default off recovers T*+domestic.
        # True: Ndel-lagged international D.30/D.30a requests replace
        # dest.T @ XI_lag as arrive. Not a min(supply, demand) ration.
        self.x1_from_demand = bool(x1_from_demand)
        self.n_r = len(data.regions)
        self.n_y = self.params.n_year
        self.n_years = data.end_year - data.start_year + 1
        self.n_steps = self.n_years * self.n_y

    def harvest_at(self, t: int) -> np.ndarray:
        t = max(int(t), 0)
        y, ys = divmod(t, self.n_y)
        y = min(y, self.n_years - 1)
        H = self.data.H_star[:, ys]
        if self.use_anomalies:
            H = H * (1.0 + self.data.anomaly[:, y])
        return np.maximum(H, 0.0)

    def delta_at(self, t: int) -> np.ndarray:
        if not self.use_restrictions:
            return np.zeros(self.n_r)
        col = self.data.delta.shape[1]
        if t < 0 or t >= col:
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
        # delivery queue: Ndel steps of exporter-indexed XI and offer prices.
        # Arrivals to consumers are T* destination shares of that XI (E.1),
        # not the exporter's own lagged shipments.
        q_i = [np.zeros(n_r) for _ in range(p.n_del)]
        q_p = [np.ones(n_r) for _ in range(p.n_del)]
        # R5: Ndel queue of international D.30/D.30a requests (x1=demand).
        q_req = [np.zeros(n_r) for _ in range(p.n_del)]
        dest = international_destination_shares(d.T_star)

        price_index = np.ones(T)
        S_p_path = np.zeros((n_r, T))
        S_c_path = np.zeros((n_r, T))
        C_path = np.zeros((n_r, T))
        xi_path = np.zeros((n_r, T))
        H_path = np.zeros((n_r, T))
        sold_d_path = np.zeros((n_r, T))
        p_c_path = np.zeros((n_r, T))
        inflow_path = np.zeros((n_r, T))
        offer_path = np.zeros((n_r, T))
        failed = 0
        fallback = 0
        unconverged = 0
        floor_binds = 0
        floor_binds_plan = 0
        plan_residual = 0.0

        shares = d.T_star.copy()
        rs = shares.sum(axis=0, keepdims=True)
        shares = np.divide(shares, np.maximum(rs, 1e-12))
        # D.22 rivals: horizon vector + shift of planned foreign sales.
        # Sourced wheat law (T2); independent Python in d22.py. Not a freeze.
        from .d22 import (
            ema_weight,
            init_expected_others_foreign,
            observe_planned_foreign,
            pad_planned_foreign,
            shift_ema_expected_others,
        )
        Q = init_expected_others_foreign(d.XI_star_path, n_start=0)
        w_exp = ema_weight(p.tau_exp, n_y)
        last_ask = baseline_ask_matrix(d.XD_star, d.XI_star, d.T_star)

        t0 = perf_counter()
        for t in range(T):
            # 1 harvest  2 policy
            H = self.harvest_at(t)
            delta = self.delta_at(t)
            # Rolling forthcoming year [t, t+Nyear): D.1 weights from *now*,
            # not from January of the calendar year. S0 is start-of-step stock
            # (harvest of this step is H[0] of the horizon — no double count).
            H_roll = np.stack([self.harvest_at(t + k) for k in range(n_y)], axis=1)
            H_star_roll = np.stack([d.H_star[:, (t + k) % n_y] for k in range(n_y)], axis=1)
            # 4 plan then 3 sales: execute step 0 of the new programme.
            # Jacobi IBR: every region best-responds to last expected rivals
            # (D.22), not to 28 Gauss–Seidel replies inside the step.
            frozen_d = plan_d.copy()
            frozen_i = plan_i.copy()
            new_d = plan_d.copy()
            new_i = plan_i.copy()
            xi_ship0 = np.zeros(n_r)
            do_replan = (t % self.replan_stride) == 0
            if do_replan:
                for r in range(n_r):
                    others = Q[r]
                    x0_d = np.empty(n_y)
                    x0_i = np.empty(n_y)
                    for k in range(n_y):
                        tt = min(t + k, T - 1)
                        x0_d[k] = frozen_d[r, tt]
                        x0_i[k] = frozen_i[r, tt]
                    dhat = expected_restriction(float(delta[r]), n_y)
                    Hhat = expected_harvest(
                        H_star_roll[r], H_roll[r], n_y,
                        n_for=p.n_for, tau_for_steps=p.tau_for * n_y)
                    # D.7 international argument is world volume / world XI*
                    # (scalar year-average per step). Domestic uses own XD*.
                    # Current x1 is demand (clipped), not a free choice.
                    # Author X_avg is mean baseline harvest per step
                    # (initialization.jl); XD*+XI* is that identity here.
                    x_avg = float(d.XD_star[r]) + float(d.XI_star[r])
                    x1 = demand_x1_from_ask(
                        last_ask, r, float(S_p[r]), float(H[r]),
                        p.iota, x_avg, p.delta_loss)
                    sol = solve_supplier_plan(
                        Hhat, float(S_p[r]), others,
                        d.XI_world, d.XD_star[r],
                        p.alpha_i, float(d.alpha_d[r]), p,
                        delta_hat=dhat, x0=np.concatenate([x0_d, x0_i]),
                        x1=x1,
                    )
                    if not sol["success"]:
                        failed += 1
                    if sol["fallback"]:
                        fallback += 1
                    if not sol["converged"]:
                        unconverged += 1
                    floor_binds_plan += int(sol["floor_binds"])
                    plan_residual = max(plan_residual, float(sol["residual"]))
                    if sol["success"]:
                        for k in range(n_y):
                            tt = t + k
                            if tt < T:
                                new_d[r, tt] = sol["xd"][k]
                                new_i[r, tt] = sol["xi"][k]
                        xi_ship0[r] = float(sol["xi_ship"][0])
                    else:
                        xi_ship0[r] = frozen_i[r, t] * (1.0 - delta[r])
                plan_d, plan_i = new_d, new_i
            else:
                for r in range(n_r):
                    xi_ship0[r] = plan_i[r, t] * (1.0 - delta[r])
            star_w = max(float(d.XI_world), 1e-8)
            for r in range(n_r):
                q_i_arg = (xi_ship0[r] + Q[r, 0]) / star_w
                if q_i_arg <= p.demand_arg_floor:
                    floor_binds += 1
                offer[r] = float(inverse_demand(q_i_arg, p.alpha_i, p.lam_demand,
                                                p.demand_arg_floor))
                if abs(offer[r] - 1.0) < p.iota:
                    offer[r] = 1.0
            offer_path[:, t] = offer
            sold_d = np.zeros(n_r)
            sold_i = np.zeros(n_r)
            avail = S_p + H
            for r in range(n_r):
                sd, si = fulfill_sales(plan_d[r, t], plan_i[r, t], avail[r], delta[r])
                sold_d[r], sold_i[r] = sd, si
                S_p[r] = update_producer_storage(S_p[r], H[r], sd, si, p.delta_loss)
            xi_path[:, t] = sold_i
            sold_d_path[:, t] = sold_d
            H_path[:, t] = H
            # D.22: Jacobi then update Q from planned foreign sales, not sold XI.
            if not self.freeze_q_oth:
                pad = d.XI_star_path[:, t % n_y]
                padded = pad_planned_foreign(plan_i, t, n_y, pad)
                obs = observe_planned_foreign(padded, p.n_del)
                Q = shift_ema_expected_others(Q, obs, w_exp)
            # 6 delivery: queue exporter XI; world price on that lag; consumers
            # receive T* destination allocation of the same lag (E.1), not own XI.
            q_i.append(sold_i.copy())
            q_p.append(offer.copy())
            xi_lag = q_i.pop(0)
            p_lag = q_p.pop(0)
            p_w = volume_weighted_offer_index(
                xi_lag, p_lag,
                empty=(float(price_index[t - 1]) if t else 1.0),
            )
            price_index[t] = p_w
            arrive_tstar = dest.T @ xi_lag
            req_lag = q_req[0]
            arrive = req_lag if self.x1_from_demand else arrive_tstar
            req_now = np.zeros(n_r)
            for s in range(n_r):
                prices = np.maximum(offer * (1.0 + 0.0 * d.nu[s]), 1e-8)
                S_star = d.Psi[s] * n_y * d.C_star[s]
                extra = extra_storage_demand(S_c[s], S_star, p.tau_steps)
                # D.30a: B = C*/A_d at p*=1 (author mean(p* D*)/A_d*).
                # Default inflow is T*+domestic. x1_from_demand (R5, default
                # off) replaces international T* with lagged foreign requests.
                B = d.C_star[s] / max(float(d.A_d[s]), 1e-8)
                P_idx = ces_price_index(prices, shares[:, s], p.sigma_ces)
                A_t = crop_budget_share(d.A_d[s], P_idx, extra, B)
                q_ask = purchaser_demand(
                    prices, B, p.sigma_ces, shares[:, s],
                    A_d=A_t, eps_d=p.eps_d,
                )
                last_ask[:, s] = q_ask
                req_now[s] = foreign_request_quantity(q_ask, s)
                inflow = float(arrive[s]) + float(sold_d[s])
                p_c[s] = consumer_price_mix(p_w, inflow, p_c[s], S_c[s])
                cons = consumption_ces(p_c[s], d.A_c[s], p.eps_c, d.C_star[s])
                cons = min(cons, S_c[s] + inflow)
                S_c[s] = max(S_c[s] + inflow - cons, 0.0)
                C_path[s, t] = cons
                inflow_path[s, t] = inflow
                p_c_path[s, t] = p_c[s]
            q_req.append(req_now)
            q_req.pop(0)
            S_p_path[:, t] = S_p
            S_c_path[:, t] = S_c

        runtime_s = float(perf_counter() - t0)
        notes = list(d.notes)
        notes.append(
            f"Nash IBR: {nash['iterations']} iters, err={nash['err']:.3e}, "
            f"success={nash['success']}.")
        notes.append(
            f"Supplier solves: failed={failed}, fallback={fallback}, "
            f"unconverged={unconverged} of {n_r * T}.")
        notes.append(
            f"Inverse-demand floor binds: offer={floor_binds}, "
            f"plan-path={floor_binds_plan}; max plan residual={plan_residual:.3e}; "
            f"runtime={runtime_s:.1f}s.")
        return AgrimateResult(
            start_year=d.start_year, end_year=d.end_year, regions=d.regions,
            price_index=price_index, price_usd=price_index * d.p0,
            S_producer=S_p_path, S_consumer=S_c_path,
            failed_solves=failed, fallback_solves=fallback, nash=nash,
            notes=notes, consumption=C_path, xi_ship=xi_path,
            harvest=H_path, sold_domestic=sold_d_path,
            p_consumer=p_c_path, inflow=inflow_path,
            floor_binds=floor_binds, unconverged_solves=unconverged,
            plan_residual=plan_residual, runtime_s=runtime_s,
            use_anomalies=self.use_anomalies,
            use_restrictions=self.use_restrictions,
            offer=offer_path,
            x1_from_demand=self.x1_from_demand,
        )


def run_agrimate(data: WheatData | None = None, use_restrictions: bool = True,
                 use_anomalies: bool = True, start_year: int = 2003,
                 end_year: int = 2011, params: AgrimateParams | None = None,
                 replan_stride: int = 1, freeze_q_oth: bool = False,
                 x1_from_demand: bool = False
                 ) -> AgrimateResult:
    if data is None:
        data = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    return AgrimateSim(
        data, params=params, use_restrictions=use_restrictions,
        use_anomalies=use_anomalies, replan_stride=replan_stride,
        freeze_q_oth=freeze_q_oth, x1_from_demand=x1_from_demand,
    ).run()


def run_wheat(**kwargs) -> AgrimateResult:
    return run_agrimate(**kwargs)
