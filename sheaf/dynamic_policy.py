"""Gate 2 beta: one exporter chooses export cuts on the Gate 0 24-step spine.

Types (who plays, buffer, intensity) are slow. Actions ``τ_t`` respond to
the crisis path. Not the annual SPE game in ``sheaf/core.py`` (TWIST-era
leftover). Headey (2011) is the clock. See diagnostics/GAME_CLOCK.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .calendar24 import STEPS_PER_YEAR
from .dynamic_crop import CropPrep, CropSimResult, prepare_crop_run, simulate_prep


@dataclass(frozen=True)
class PolicyKnobs:
    """Illustrative types. Not estimated from AMIS or crisis prices.

    ``gov_stu``, ``fs_stock_weight``, ``tau_on``, and
    ``stock_ratio_trigger`` were locked after the qualitative calm/shock
    flip was visible on this host. They are not AMIS estimates. Actions
    ``τ_t`` are implied by the path; these knobs do not change every
    fortnight.
    """
    crop: str = "wheat"
    exporter: str = "Russia"
    start_year: int = 2006
    end_year: int = 2008
    shock_year: int = 2007
    harvest_mult: float = 0.50
    tau_grid: tuple[float, ...] = (0.0, 0.3, 0.6, 0.9)
    # Government buffer as a fraction of annual domestic use. Distinct from
    # Gate 0 competitive safety (stu_target × C_ann ≈ 0.20 for wheat).
    gov_stu: float = 0.48
    # Scales (mean-stock gap)² vs export revenue (p $/t × MMT). Small enough
    # that shock BR stays interior (ToT); large enough that the shock path
    # carries a visible food-security penalty.
    fs_stock_weight: float = 12.0
    # Intensity applied on fortnights the Headey gate is on. Slow type;
    # locked from the year-open-loop nested BR (interior τ*=0.6).
    tau_on: float = 0.6
    # Cut when open-path S_t / climatology S_t falls below this. Absolute
    # stock floors fire every hungry season even in calm years.
    stock_ratio_trigger: float = 0.85


def year_slice(prep: CropPrep, year: int) -> slice:
    t0 = (year - prep.start_year) * STEPS_PER_YEAR
    return slice(t0, t0 + STEPS_PER_YEAR)


def exporter_index(prep: CropPrep, exporter: str) -> int:
    if exporter not in prep.countries:
        raise KeyError(f"{exporter!r} not in {prep.countries}")
    return prep.countries.index(exporter)


def gov_buffer(prep: CropPrep, knobs: PolicyKnobs) -> float:
    """Illustrative government buffer, not Gate 0 competitive safety."""
    i = exporter_index(prep, knobs.exporter)
    return float(knobs.gov_stu) * float(prep.C_ann[i])


def apply_year_tau(prep: CropPrep, exporter: str, year: int,
                   tau: float) -> np.ndarray:
    cuts = np.array(prep.cuts, float, copy=True)
    i = exporter_index(prep, exporter)
    sl = year_slice(prep, year)
    cuts[i, sl] = np.maximum(cuts[i, sl], float(tau))
    return cuts


def shock_year_harvest(prep: CropPrep, exporter: str, year: int,
                       mult: float) -> np.ndarray:
    H = np.array(prep.H, float, copy=True)
    i = exporter_index(prep, exporter)
    sl = year_slice(prep, year)
    H[i, sl] = H[i, sl] * float(mult)
    return H


def welfare(res: CropSimResult, exporter: str, year: int,
            knobs: PolicyKnobs, s_gov: float) -> dict:
    """Export revenue minus a year-mean stock-to-buffer penalty.

    Per-step ``max(0, safety − S_t)`` against Gate 0 competitive safety
    makes a climatology government restrict: the harvest calendar already
    drives the hungry-season trough below ``stu_target × C_ann``. That is
    a seasonal sawtooth, not a crisis. This objective uses the *annual
    mean* stock against an illustrative government buffer ``s_gov``.

    World ``p`` does not enter the food-security term. Gate 0 has one
    ask-dominated price; a ban does not create a cheaper domestic CPI,
    and a world-price penalty would punish the government for the spike
    the ban itself causes. Withheld grain stays as stock.
    """
    i = res.countries.index(exporter)
    t0 = (year - res.start_year) * STEPS_PER_YEAR
    sl = slice(t0, t0 + STEPS_PER_YEAR)
    p = np.asarray(res.price[sl], float)
    x = np.asarray(res.exports[i, sl], float)
    s = np.asarray(res.stock[i, sl], float)
    revenue = float(np.dot(p, x))
    mean_stock = float(s.mean())
    gap = max(0.0, float(s_gov) - mean_stock)
    penalty = float(knobs.fs_stock_weight) * gap * gap
    return dict(
        W=revenue - penalty, revenue=revenue, penalty=penalty,
        s_gov=float(s_gov), mean_stock=mean_stock,
        min_stock=float(s.min()),
        mean_price=float(p.mean()), sum_exports=float(x.sum()),
    )


def prepare_beta(knobs: PolicyKnobs | None = None) -> CropPrep:
    knobs = knobs or PolicyKnobs()
    return prepare_crop_run(
        knobs.crop, start_year=knobs.start_year, end_year=knobs.end_year,
        use_amis=False, use_shocks=False, use_demand=False,
        use_industrial=False)


def climatology_relative_cuts(prep: CropPrep, harvest: np.ndarray,
                              knobs: PolicyKnobs) -> tuple[np.ndarray, dict]:
    """State-contingent τ_t from stocks vs a normal year at the same step.

    Two-pass (open path, then cuts). Does not rewrite the Gate 0 market
    loop. Restricts to the shock year. Climatology harvest ⇒ ratio ≡ 1
    ⇒ τ_t = 0. Headey persistence (bans last months) is the on-path
    cluster, not a second estimated knob.
    """
    i = exporter_index(prep, knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    res_calm = simulate_prep(prep, harvest=prep.H)
    res_open = simulate_prep(prep, harvest=harvest)
    s_calm = np.asarray(res_calm.stock[i], float)
    s_open = np.asarray(res_open.stock[i], float)
    ratio = s_open / np.maximum(s_calm, 1e-9)
    on = np.zeros(ratio.shape[0], dtype=bool)
    on[sl] = ratio[sl] < float(knobs.stock_ratio_trigger)
    cuts = np.array(prep.cuts, float, copy=True)
    cuts[i] = np.maximum(cuts[i], np.where(on, float(knobs.tau_on), 0.0))
    meta = dict(
        n_on=int(on.sum()),
        n_year=int(np.sum(on[sl])),
        min_ratio=float(ratio[sl].min()),
        mean_ratio=float(ratio[sl].mean()),
        tau_on=float(knobs.tau_on),
        trigger=float(knobs.stock_ratio_trigger),
        ratio=ratio,
        on=on,
        open_exports=float(res_open.exports[i, sl].sum()),
        open_mean_stock=float(s_open[sl].mean()),
    )
    return cuts, meta


def simulate_headey(prep: CropPrep, harvest: np.ndarray,
                    knobs: PolicyKnobs) -> tuple[CropSimResult, np.ndarray, dict]:
    cuts, meta = climatology_relative_cuts(prep, harvest, knobs)
    res = simulate_prep(prep, cuts=cuts, harvest=harvest)
    i = exporter_index(prep, knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    meta["closed_exports"] = float(res.exports[i, sl].sum())
    meta["closed_mean_stock"] = float(res.stock[i, sl].mean())
    meta["max_tau"] = float(cuts[i, sl].max())
    return res, cuts, meta


def grid_best_response(prep: CropPrep, harvest: np.ndarray,
                       knobs: PolicyKnobs) -> tuple[float, list[dict]]:
    s_gov = gov_buffer(prep, knobs)
    rows = []
    best_tau, best_W = knobs.tau_grid[0], -np.inf
    for tau in knobs.tau_grid:
        cuts = apply_year_tau(prep, knobs.exporter, knobs.shock_year, tau)
        res = simulate_prep(prep, cuts=cuts, harvest=harvest)
        met = welfare(res, knobs.exporter, knobs.shock_year, knobs, s_gov)
        met.update(tau=float(tau))
        rows.append(met)
        if met["W"] > best_W:
            best_W, best_tau = met["W"], float(tau)
    return best_tau, rows
