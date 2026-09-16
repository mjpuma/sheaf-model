"""Wheat defaults from Zenodo 14022004 AgrimateParams (conflicts with Tbl. D.8 recorded)."""
from __future__ import annotations

from dataclasses import dataclass

from sheaf.calendar24 import STEPS_PER_YEAR


@dataclass(frozen=True)
class AgrimateParams:
    n_year: int = STEPS_PER_YEAR
    n_del: int = 2  # Ndel = Nyear/12
    # Author code defaults (AgrimateModel.jl). Tbl. D.8 has αI=3.5, τ=0.2.
    alpha_i: float = 3.2
    alpha_nash: float = 3.0
    lam_demand: float = 0.0
    tau_storage: float = 0.1  # years; code uses tau_storage * n_year steps
    iota: float = 0.001
    rho_pref: float = 0.5
    sigma_ces: float = 2.0
    eps_c: float = 0.1
    eps_d: float = 1.0 / 3.0
    delta_loss: float = 0.0
    rho_interest: float = 0.0
    p_sto_annual: float = 0.1  # Tbl. D.8; producer uses p_sto/Nyear per step
    xmin_share: float = 0.2  # of total possible sales, spread over N×2 markets
    zeta_penalty: float = 0.0  # 0 = xmin penalty on; 1 = off
    tau_exp: float = 0.5
    n_for_months: int = 3
    tau_for: float = 0.2
    beta_loc: float = 0.05  # local price adjustment; not yet wired
    # inverse-demand argument floor (numerical; not Agrimate's world-price pin)
    demand_arg_floor: float = 0.05
    nash_max_iters: int = 20
    nash_tol: float = 1e-6
    plan_maxiter: int = 40

    @property
    def tau_steps(self) -> float:
        return self.tau_storage * self.n_year

    @property
    def n_for(self) -> int:
        return self.n_for_months * (self.n_year // 12)

    @property
    def p_sto_step(self) -> float:
        return self.p_sto_annual / self.n_year


def wheat_params() -> AgrimateParams:
    """Author-code wheat defaults (Zenodo 14022004)."""
    return AgrimateParams()


def wheat_table_d8_defaults() -> AgrimateParams:
    """Tbl. D.8 column (not the executable default): αI=3.5, τ=0.2 Nyear."""
    return AgrimateParams(alpha_i=3.5, alpha_nash=3.5, tau_storage=0.2)


def wheat_published_sensitivity_defaults() -> AgrimateParams:
    """Tbl. F.1 / author code: αI=3.2, τ=0.1 Nyear."""
    return AgrimateParams(alpha_i=3.2, alpha_nash=3.2, tau_storage=0.1)
