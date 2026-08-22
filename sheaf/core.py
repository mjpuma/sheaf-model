"""
sheaf.core
==========
SHEAF -- Substitution, Heterogeneous agents, Equilibrium, And Fragility.

A country-level, multi-commodity network model of global grain trade that couples
a spatial price equilibrium with strategic government behaviour AND cross-commodity
substitution. It generalises the single-commodity strategic-trade model (in the
spirit of PIK's TWIST / Agrimate) along the dimension reviewers keep attacking:
there is more than one grain, and buyers substitute between them.

Three coupled ideas:

  * MARKET layer -- a Takayama–Judge / Samuelson spatial price equilibrium solved
    as one concave QP that clears ALL commodities jointly. The commodities are
    linked on the demand side by a symmetric, positive-definite cross-price
    demand system  D_i = a_i - M_i p_i . A wheat shortfall raises the wheat
    price; because maize/rice are substitutes, demand shifts and their prices
    move too -- the markets couple. Set the off-diagonals of M to zero and the
    markets decouple into independent single-commodity problems: that limit is
    exactly the class of models SHEAF is meant to improve on.

  * STRATEGIC layer -- exporters choose export-tax-equivalents tau (a ban ~ high
    tau), per commodity, to maximise national welfare. Nash is approximated by
    iterated best response over the market layer. Substitution flattens the
    residual demand each exporter faces (buyers can escape into another grain),
    which reshapes the optimal restriction -- an interaction neither a no-strategy
    model (TWIST) nor a no-substitution model (Agrimate) can produce.

  * STORAGE -- market-responsive (competitive) reserves and strategic government
    buffer stocks adjust available supply each period before the market clears.

Units: quantities in million tonnes (MMT); prices an index in $/tonne.
Dependencies: numpy, pandas, cvxpy (networkx/matplotlib only for the demo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np
import pandas as pd
import cvxpy as cp


# ----------------------------------------------------------------------------
# 1. Commodities and the cross-price demand system
# ----------------------------------------------------------------------------
@dataclass
class DemandSystem:
    """Per-country linear demand system over G grains:  D = a - M p.

    M is built symmetric positive-definite so the net-social-payoff QP stays
    concave and a consumer-surplus potential exists (Slutsky symmetry). The
    inverse demand is  p = Minv (a - D)  and the concave benefit potential whose
    gradient is that inverse demand is  W(D) = (Minv a).D - 0.5 D' Minv D .

    Off-diagonals of M are <= 0 for substitute grains (a higher price of grain h
    raises demand for grain g). Zeroing them recovers independent markets.
    """
    grains: tuple[str, ...]
    a: np.ndarray            # (G,) demand intercepts
    M: np.ndarray            # (G,G) symmetric PD slope matrix
    Minv: np.ndarray         # (G,G) precomputed inverse
    p0: np.ndarray           # (G,) reference prices (for diagnostics)
    D0: np.ndarray           # (G,) reference consumption

    @property
    def G(self) -> int:
        return len(self.grains)

    def price(self, D: np.ndarray) -> np.ndarray:
        return self.Minv @ (self.a - D)

    def surplus(self, D: np.ndarray) -> float:
        """Consumer surplus = benefit potential - expenditure (generalises the
        linear-demand triangle D^2/(2 beta) to the multi-good case)."""
        p = self.price(D)
        benefit = (self.Minv @ self.a) @ D - 0.5 * D @ (self.Minv @ D)
        return float(benefit - p @ D)


def build_demand_system(grains, D0, p0, own_elast, rho, subst_scale=0.6):
    """Construct a symmetric PD demand system from baseline data and elasticities.

    Parameters
    ----------
    grains       : tuple of grain names, length G
    D0           : (G,) baseline consumption per grain (MMT)
    p0           : (G,) reference price per grain ($/t)
    own_elast    : (G,) own-price elasticities (<0), e.g. wheat -0.25, maize -0.30
    rho          : (G,G) symmetric substitutability indices in [0,1), zero diagonal.
                   rho[g,h] = 0 -> grains g,h do not substitute.
    subst_scale  : global multiplier on substitution strength (0 = no substitution).

    Returns a DemandSystem with M = diag(b) - S, where b_g = -own_elast_g D0_g/p0_g
    (own slope) and S_gh = subst_scale * rho_gh * sqrt(b_g b_h). Rows of S are
    capped for diagonal dominance, then symmetrised by the geometric mean
    S <- sqrt(S ◦ Sᵀ). That ordering keeps ρ(D^{-1/2} S D^{-1/2}) ≤ 0.95, so M
    is positive-definite whenever every own slope b_g > 0.
    """
    D0 = np.asarray(D0, float); p0 = np.asarray(p0, float)
    own_elast = np.asarray(own_elast, float); rho = np.asarray(rho, float)
    G = len(grains)
    b = -own_elast * D0 / p0                      # own slopes (>0)
    if np.any(b <= 0):
        raise ValueError("build_demand_system requires strictly positive own "
                         "slopes b_g = -own_elast_g * D0_g / p0_g")
    S = np.zeros((G, G))
    for g in range(G):
        for h in range(G):
            if g != h:
                S[g, h] = subst_scale * rho[g, h] * np.sqrt(b[g] * b[h])
    # enforce strict diagonal dominance on rows, then geometric-mean symmetrise
    for g in range(G):
        off = S[g].sum()
        if off >= 0.95 * b[g]:
            S[g] *= (0.95 * b[g]) / off
    S = np.sqrt(S * S.T)                           # preserves dominance bound
    M = np.diag(b) - S
    Minv = np.linalg.inv(M)
    a = D0 + M @ p0
    return DemandSystem(tuple(grains), a, M, Minv, p0.copy(), D0.copy())


# ----------------------------------------------------------------------------
# 2. Country / agent definition
# ----------------------------------------------------------------------------
@dataclass
class Country:
    """A country-node carrying all four agent roles, across G grains.

    Per-grain quantities are length-G arrays aligned to `demand.grains`.
    """
    name: str
    region: str
    production: np.ndarray                  # (G,) baseline production per grain
    demand: DemandSystem                    # per-country demand system

    # --- role: strategic exporter ---
    export_grains: tuple[str, ...] = ()     # grains it strategically restricts

    # --- market-responsive (private) reserves, per grain ---
    mkt_stock: np.ndarray = None
    mkt_capacity: np.ndarray = None
    mkt_gamma: np.ndarray = None            # responsiveness to price gap (0 = none)
    mkt_cost: float = 8.0

    # --- strategic government reserves, per grain ---
    gov_stock: np.ndarray = None
    gov_target_ratio: np.ndarray = None     # target stock-to-use ratio per grain
    gov_price_trigger: np.ndarray = None    # release trigger price per grain
    gov_release_frac: float = 0.5
    gov_build_frac: float = 0.10

    # --- strategic-layer preferences, per grain ---
    fs_weight: np.ndarray = None            # weight on food-price penalty per grain
    p_target: np.ndarray = None             # tolerated price per grain
    tariff: np.ndarray = None               # import tariff per grain ($/t)

    # --- bookkeeping ---
    p_prev: np.ndarray = None               # last realised price vector

    def __post_init__(self):
        G = self.demand.G
        z = lambda v, d: (np.full(G, d, float) if v is None else np.asarray(v, float))
        self.production = np.asarray(self.production, float)
        self.mkt_stock = z(self.mkt_stock, 0.0)
        self.mkt_capacity = z(self.mkt_capacity, np.inf)
        self.mkt_gamma = z(self.mkt_gamma, 0.0)
        self.gov_stock = z(self.gov_stock, 0.0)
        self.gov_target_ratio = z(self.gov_target_ratio, 0.0)
        self.gov_price_trigger = z(self.gov_price_trigger, np.inf)
        self.fs_weight = z(self.fs_weight, 0.0)
        self.p_target = z(self.p_target, np.inf)
        self.tariff = z(self.tariff, 0.0)
        if self.p_prev is None:
            self.p_prev = self.demand.p0.copy()

    @property
    def is_exporter(self) -> bool:
        return len(self.export_grains) > 0


# ----------------------------------------------------------------------------
# 3. Storage behaviours (per grain)
# ----------------------------------------------------------------------------
def market_responsive_storage(c: Country, g: int, p_ref: float, p_expected: float,
                              r: float = 0.05) -> float:
    """Competitive storage for grain g (Wright-Williams / Deaton-Laroque flavour).
    Returns net accumulation (+build reduces availability, -release adds)."""
    if c.mkt_gamma[g] <= 0:
        return 0.0
    signal = p_expected / (1.0 + r) - p_ref
    deadband = c.mkt_cost
    if abs(signal) < deadband:
        return 0.0
    desired = c.mkt_gamma[g] * (signal - np.sign(signal) * deadband)
    return float(np.clip(desired, -c.mkt_stock[g], c.mkt_capacity[g] - c.mkt_stock[g]))


def strategic_storage(c: Country, g: int, p_ref: float, cons_baseline: float,
                      availability_wo_gov: float,
                      production0: Optional[float] = None) -> float:
    """Government buffer rule for grain g. Returns net accumulation (+build/-release).

    Quantity-leg shortfall is the gap after normal baseline trade (G2):
        Σ = D0 - A_pre - max(D0 - Q0, 0)
    so structural importers are calm at ξ=1, and exporters enter crisis only when
    pre-gov availability falls below domestic baseline consumption. Pass
    production0=Q0 (unshocked); if omitted, Q0 defaults to availability_wo_gov
    (legacy autarky behaviour — not used by SheafModel).
    """
    if c.gov_target_ratio[g] <= 0 and c.gov_stock[g] <= 0:
        return 0.0
    q0 = float(availability_wo_gov if production0 is None else production0)
    shortfall = cons_baseline - availability_wo_gov - max(cons_baseline - q0, 0.0)
    crisis = (p_ref > c.gov_price_trigger[g]) or (shortfall > 0)
    if crisis and c.gov_stock[g] > 0:
        if p_ref > c.gov_price_trigger[g] and shortfall <= 0:
            release = c.gov_stock[g] * c.gov_release_frac
        else:
            release = min(c.gov_stock[g] * c.gov_release_frac, max(shortfall, 0.0))
        return -float(release)
    if (not crisis) and p_ref <= c.gov_price_trigger[g]:
        target = c.gov_target_ratio[g] * cons_baseline
        gap = target - c.gov_stock[g]
        if gap > 0:
            return float(gap * c.gov_build_frac)
    return 0.0


# ----------------------------------------------------------------------------
# 4. Market layer: multi-commodity spatial price equilibrium
# ----------------------------------------------------------------------------
@dataclass
class MarketResult:
    prices: np.ndarray          # (n, G)
    consumption: np.ndarray     # (n, G)
    flows: np.ndarray           # (G, n, n)  flows[g,i,j] = grain g from i to j
    net_exports: np.ndarray     # (n, G)
    availability: np.ndarray    # (n, G)
    grains: tuple[str, ...] = ()


class SpatialEquilibriumError(RuntimeError):
    """Raised when the spatial-equilibrium QP is not accepted as solved."""


class SpatialEquilibrium:
    """Clear all commodities jointly as one concave QP.

        maximise  sum_i [ (Minv_i a_i).D_i - 0.5 D_i' Minv_i D_i ]
                  - sum_g sum_ij K^g_ij f^g_ij
        s.t.      A^g_i + imports^g_i - exports^g_i - D^g_i = 0   (per grain)
                  f >= 0, D >= 0, no self-trade.

    Commodities couple only through the cross terms of Minv_i (the demand system);
    with a diagonal Minv the problem separates into G independent markets.
    """

    def __init__(self, transport: np.ndarray, grains: tuple[str, ...],
                 freight_mult: Optional[np.ndarray] = None):
        self.C = np.asarray(transport, float)
        self.n = self.C.shape[0]
        np.fill_diagonal(self.C, 0.0)
        self.grains = tuple(grains)
        self.G = len(grains)
        # per-grain freight multiplier (rice ships dearer per tonne, etc.)
        self.freight_mult = (np.ones(self.G) if freight_mult is None
                             else np.asarray(freight_mult, float))

    def solve(self, systems: list[DemandSystem], availability: np.ndarray,
              export_tax: np.ndarray, tariff: np.ndarray,
              route_multiplier: Optional[np.ndarray] = None) -> MarketResult:
        n, G = self.n, self.G
        availability = np.asarray(availability, float)
        world = availability.sum(axis=0)
        if np.any(world < -1e-9):
            bad = [self.grains[g] for g in range(G) if world[g] < -1e-9]
            raise SpatialEquilibriumError(
                f"globally infeasible availability (sum A < 0) for {bad}; "
                f"world sums={world}")

        D = cp.Variable((n, G), nonneg=True)
        fg = [cp.Variable((n, n), nonneg=True) for _ in range(G)]

        benefit = 0
        for i, sysd in enumerate(systems):
            ca = sysd.Minv @ sysd.a
            benefit = benefit + ca @ D[i, :] - 0.5 * cp.quad_form(D[i, :], sysd.Minv)

        cost = 0
        constraints = []
        for g in range(G):
            Cg = self.C * self.freight_mult[g]
            if route_multiplier is not None:
                Cg = Cg * route_multiplier
            K = Cg + export_tax[:, g][:, None] + tariff[:, g][None, :]
            cost = cost + cp.sum(cp.multiply(K, fg[g]))
            imports = cp.sum(fg[g], axis=0)
            exports = cp.sum(fg[g], axis=1)
            constraints += [availability[:, g] + imports - exports - D[:, g] == 0,
                            cp.diag(fg[g]) == 0]

        prob = cp.Problem(cp.Maximize(benefit - cost), constraints)
        # Prefer a proven optimal solve. Retry the next solver on inaccurate /
        # failed statuses rather than accepting a numeric-but-untrusted value.
        accept = {"optimal"}
        retry = {"optimal_inaccurate", "user_limit", "infeasible_inaccurate",
                 "unbounded_inaccurate"}
        statuses: list[str] = []
        last_err: Optional[BaseException] = None
        for solver in (cp.CLARABEL, cp.SCS, cp.OSQP):
            try:
                prob.solve(solver=solver, verbose=False)
                status = str(prob.status)
                statuses.append(f"{solver}:{status}")
                if status in accept and D.value is not None:
                    break
                if status in retry:
                    continue
                # infeasible / unbounded / other — try next solver, then error
                continue
            except Exception as exc:
                last_err = exc
                statuses.append(f"{solver}:EXC:{type(exc).__name__}")
                continue
        else:
            hint = ("check demand PD / DCP, or world availability sums"
                    if last_err is not None else
                    "check feasibility (world availability) and solver install")
            raise SpatialEquilibriumError(
                f"spatial equilibrium not solved; attempted={statuses}; hint={hint}"
            ) from last_err

        Dv = np.clip(np.asarray(D.value), 0.0, None)
        flows = np.stack([np.clip(np.asarray(fg[g].value), 0.0, None)
                          for g in range(G)])
        prices = np.vstack([systems[i].price(Dv[i, :]) for i in range(n)])
        net_exports = availability - Dv
        return MarketResult(prices=prices, consumption=Dv, flows=flows,
                            net_exports=net_exports, availability=availability,
                            grains=self.grains)


# ----------------------------------------------------------------------------
# 5. Strategic layer: multi-commodity export-restriction game
# ----------------------------------------------------------------------------
class ExportRestrictionGame:
    """Exporters choose per-grain export taxes to maximise national welfare:

        W_i = consumer_surplus_i + producer_income_i - food_security_penalty_i
        CS_i        = sum over the demand-system surplus (cross-substitution aware)
        producer_i  = sum_g p_{i,g} * production_{i,g}
        penalty_i   = sum_g fs_weight_{i,g} * max(0, p_{i,g} - p_target_{i,g})^2

    Nash via iterated best response. To stay fast the game is only invoked when a
    market is stressed; in calm periods taxes are ~0 anyway.
    """

    def __init__(self, market: SpatialEquilibrium, tau_max: float = 120.0,
                 grid: int = 13, max_iters: int = 3, tol: float = 3.0,
                 revenue_weight: float = 0.0):
        self.market = market
        self.tau_max = tau_max
        self.grid = grid
        self.max_iters = max_iters
        self.tol = tol
        self.revenue_weight = revenue_weight

    def _welfare(self, i, res: MarketResult, systems, production, fs_weight,
                 p_target, tau) -> float:
        p = res.prices[i, :]
        D = res.consumption[i, :]
        X = np.clip(res.net_exports[i, :], 0, None)
        CS = systems[i].surplus(D)
        producer = float(p @ production[i, :])
        gov_rev = self.revenue_weight * float(tau[i, :] @ X)
        penalty = float((fs_weight[i, :] * np.clip(p - p_target[i, :], 0, None) ** 2).sum())
        return CS + producer + gov_rev - penalty

    def solve(self, systems, availability, production, tariff, exporters,
              export_grain_idx, fs_weight, p_target, route_multiplier=None,
              tau_init=None):
        n, G = self.market.n, self.market.G
        tau = np.zeros((n, G)) if tau_init is None else np.array(tau_init, float)
        grid = np.linspace(0.0, self.tau_max, self.grid)

        last = tau.copy()
        for _ in range(self.max_iters):
            for i in exporters:
                for g in export_grain_idx[i]:
                    best_tau, best_W = tau[i, g], -np.inf
                    for val in grid:
                        trial = tau.copy()
                        trial[i, g] = val
                        res = self.market.solve(systems, availability, trial,
                                                tariff, route_multiplier)
                        W = self._welfare(i, res, systems, production, fs_weight,
                                          p_target, trial)
                        if W > best_W:
                            best_W, best_tau = W, val
                    tau[i, g] = best_tau
            if np.max(np.abs(tau - last)) < self.tol:
                break
            last = tau.copy()

        res = self.market.solve(systems, availability, tau, tariff, route_multiplier)
        return tau, res


# ----------------------------------------------------------------------------
# 6. Dynamic orchestrator
# ----------------------------------------------------------------------------
class SheafModel:
    """Multi-period simulation coupling storage, the multi-commodity trade
    network, and the strategic export-restriction game.

    Set `substitution=False` to zero the cross-price terms and recover the
    independent single-commodity markets (the TWIST/Agrimate-style limit).
    """

    def __init__(self, countries: list[Country], transport: np.ndarray,
                 grains: tuple[str, ...], freight_mult=None,
                 discount_r: float = 0.05, tau_max: float = 120.0,
                 play_game: bool = True, p_norm=None, kappa: float = 0.5,
                 game_grid: int = 13, game_iters: int = 3,
                 stress_trigger: float = 1.12,
                 tol: float = 3.0, revenue_weight: float = 0.0):
        self.countries = countries
        self.n = len(countries)
        self.grains = tuple(grains)
        self.G = len(grains)
        self.market = SpatialEquilibrium(transport, grains, freight_mult)
        self.game = ExportRestrictionGame(self.market, tau_max=tau_max,
                                          grid=game_grid, max_iters=game_iters,
                                          tol=tol, revenue_weight=revenue_weight)
        self.r = discount_r
        self.play_game = play_game
        self.kappa = kappa
        self.p_norm = (np.array([c.demand.p0 for c in countries]).mean(axis=0)
                       if p_norm is None else np.asarray(p_norm, float))
        self.stress_trigger = stress_trigger      # price/normal ratio that turns the game on
        self.records: list[dict] = []
        self.flow_history: list[np.ndarray] = []
        self.last_tau = np.zeros((self.n, self.G))

        self.exporters = [i for i, c in enumerate(countries) if c.is_exporter]
        gi = {g: k for k, g in enumerate(grains)}
        self.export_grain_idx = {
            i: [gi[g] for g in countries[i].export_grains]
            for i in range(self.n)}
        self.tariff = np.array([c.tariff for c in countries])
        self.fs_weight = np.array([c.fs_weight for c in countries])
        self.p_target = np.array([c.p_target for c in countries])
        self.production0 = np.array([c.production for c in countries])
        self.cons_baseline = np.array([c.demand.D0 for c in countries])

    def _systems(self):
        return [c.demand for c in self.countries]

    def _expectation(self, p_ref, g):
        # Mean-revert toward a level whose storage rest point equals p_norm[g]
        # (typically mean p0): p* = κ/(κ+r)·target ⇒ target = p_norm·(κ+r)/κ.
        target = self.p_norm[g] * (self.kappa + self.r) / self.kappa
        return p_ref + self.kappa * (target - p_ref)

    def step(self, t, production_shock=None, route_multiplier=None,
             tau_forced=None):
        n, G = self.n, self.G
        shock = np.ones((n, G)) if production_shock is None else np.asarray(production_shock, float)
        availability = np.zeros((n, G))
        mkt_change = np.zeros((n, G))
        gov_change = np.zeros((n, G))

        for i, c in enumerate(self.countries):
            for g in range(G):
                prod = c.production[g] * shock[i, g]
                p_ref = c.p_prev[g]
                p_exp = self._expectation(p_ref, g)
                dm = market_responsive_storage(c, g, p_ref, p_exp, self.r)
                dg = strategic_storage(c, g, p_ref, self.cons_baseline[i, g],
                                       prod - dm, production0=c.production[g])
                mkt_change[i, g], gov_change[i, g] = dm, dg
                availability[i, g] = prod - dm - dg

        # Level-1 path: impose historical export restrictions (skip the game).
        if tau_forced is not None:
            tau = np.asarray(tau_forced, float)
            res = self.market.solve(self._systems(), availability, tau,
                                    self.tariff, route_multiplier)
            self.last_tau = tau.copy()
        else:
            # decide whether to run the strategic game this period (stress gate)
            tau0 = self.last_tau
            probe = self.market.solve(self._systems(), availability, np.zeros((n, G)),
                                      self.tariff, route_multiplier)
            stressed = np.any(probe.prices.max(axis=0) > self.stress_trigger * self.p_norm)

            if self.play_game and self.exporters and stressed:
                tau, res = self.game.solve(self._systems(), availability, self.production0,
                                           self.tariff, self.exporters, self.export_grain_idx,
                                           self.fs_weight, self.p_target, route_multiplier,
                                           tau_init=tau0)
                self.last_tau = tau.copy()
            else:
                tau = np.zeros((n, G))
                res = probe
                self.last_tau = np.zeros((n, G))

        for i, c in enumerate(self.countries):
            c.mkt_stock = np.maximum(0.0, c.mkt_stock + mkt_change[i])
            c.gov_stock = np.maximum(0.0, c.gov_stock + gov_change[i])
            c.p_prev = res.prices[i, :].copy()

        self._record(t, res, tau, mkt_change, gov_change, shock)
        self.flow_history.append(res.flows)
        return res

    def run(self, periods, shocks=None, route_multipliers=None, tau_schedule=None):
        shocks = shocks or {}
        route_multipliers = route_multipliers or {}
        tau_schedule = tau_schedule or {}
        for t in range(periods):
            self.step(t, shocks.get(t), route_multipliers.get(t),
                      tau_forced=tau_schedule.get(t))
        return self.results_frame()

    def _record(self, t, res, tau, mkt_change, gov_change, shock):
        ne = res.net_exports
        for g, grain in enumerate(self.grains):
            exp_share = np.clip(ne[:, g], 0, None)
            imp_share = np.clip(-ne[:, g], 0, None)
            te, ti = exp_share.sum(), imp_share.sum()
            exporter_price = float((res.prices[:, g] * exp_share).sum() / te) if te > 0 else float(res.prices[:, g].mean())
            importer_price = float((res.prices[:, g] * imp_share).sum() / ti) if ti > 0 else float(res.prices[:, g].mean())
            n_restrict = int((tau[:, g] > 1.0).sum())
            for i, c in enumerate(self.countries):
                self.records.append(dict(
                    period=t, grain=grain, country=c.name, region=c.region,
                    price=res.prices[i, g], consumption=res.consumption[i, g],
                    net_export=ne[i, g], availability=res.availability[i, g],
                    export_tax=tau[i, g], mkt_stock=c.mkt_stock[g],
                    gov_stock=c.gov_stock[g], prod_shock=shock[i, g],
                    exporter_price=exporter_price, importer_price=importer_price,
                    n_restricting=n_restrict,
                    total_trade=float(res.flows[g].sum())))

    def results_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.records)
