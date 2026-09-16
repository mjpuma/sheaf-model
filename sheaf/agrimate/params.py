"""Wheat defaults from supplement Tbl. D.8 (conflicts with F.1 recorded)."""
from __future__ import annotations

from dataclasses import dataclass

from sheaf.calendar24 import STEPS_PER_YEAR


@dataclass(frozen=True)
class AgrimateParams:
    n_year: int = STEPS_PER_YEAR
    n_del: int = 2  # Ndel = Nyear/12
    # Tbl. D.8
    alpha_i: float = 3.5
    alpha_nash: float = 3.5
    lam_demand: float = 0.0
    tau_storage: float = 0.2  # in years; code uses tau_storage * n_year steps
    iota: float = 0.001
    rho_pref: float = 0.5
    sigma_ces: float = 6.0
    eps_c: float = 0.15
    eps_d: float = 0.2
    delta_loss: float = 0.0
    zeta0: float = 1.0  # wheat default missing from D.8; F text insensitive at 0.5/0
    xmin: float = 1e-6
    # inverse-demand argument floor (numerical; not Agrimate's world-price pin)
    demand_arg_floor: float = 0.05
    nash_max_iters: int = 20
    nash_tol: float = 1e-6
    plan_maxiter: int = 40

    @property
    def tau_steps(self) -> float:
        return self.tau_storage * self.n_year


def wheat_params() -> AgrimateParams:
    """Tbl. D.8 wheat defaults."""
    return AgrimateParams()


def wheat_published_sensitivity_defaults() -> AgrimateParams:
    """Tbl. F.1 column (not used). αI=3.2, τ=0.1 Nyear."""
    return AgrimateParams(alpha_i=3.2, alpha_nash=3.2, tau_storage=0.1)
