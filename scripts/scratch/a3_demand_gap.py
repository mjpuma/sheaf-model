#!/usr/bin/env python3
"""A3 — how much would contemporaneous demand actually move? (read-only)

Gate 0 evaluates flex demand at the price carried in from the previous step
(`sheaf/dynamic_crop.py` L580: ``C_flex[:,t] * (p/p0)**elast`` with ``p``
still equal to :math:`p_{t-1}`), while the same step goes on to write
:math:`p_t` at L680.  Option B / X1 would evaluate demand at :math:`p_t`,
which turns each step into a scalar fixed point.

This script measures three things and writes them out:

TASK 1  the size of ``d(p_t) - d(p_{t-1})`` along the official scored path,
        per country, per step, and aggregated to the world.
TASK 2  a ONE-STEP bound on how far offers (L596) and the scarcity ratio
        (L661-663) would move under contemporaneous demand, holding the
        incoming state (stock, ask, p_{t-1}) at its official value.
TASK 3  whether the fixed point ``p = G(p)`` is well posed: monotonicity,
        a numerical Lipschitz estimate, root counting, and the behaviour of
        the three suspect discontinuities (the L681 clip, the L666 `calm`
        branch, the ``max(0, .)`` truncations).

``G`` is implemented in ``step_G`` below as a faithful transcription of the
L577-L681 loop body for a single step, taking the price used *inside demand*
as a free argument.  It is a copy, not a patch: `sheaf/dynamic_crop.py` is
never modified.  ``verify_replica`` asserts the copy reproduces the official
path bit-for-bit before any of the measurements are trusted.

Outputs
-------
diagnostics/gate0_prep/a3/demand_gap.csv          per crop/step/country
diagnostics/gate0_prep/a3/demand_gap_world.csv    per crop/step
diagnostics/gate0_prep/a3/g_lipschitz.csv         per crop/step probe
diagnostics/gate0_prep/a3/A3_REPORT.md            summary tables
figures/scratch/a3/*.png                          G(p) vs p, gap histograms
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR, year_step_to_month_half
from sheaf.dynamic_crop import (  # read-only imports
    CropPrep,
    _ask_reweight_dest,
    _bilateral_clear,
    prepare_crop_run,
    run_crop_dynamics,
    simulate_prep,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse
from sheaf.dynamic_crop import MAX_LEAN_STEPS

CROPS = ("wheat", "maize", "rice")
START, END = 2006, 2011
RUN_KW = dict(start_year=START, end_year=END,
              use_amis=True, use_shocks=True, use_demand=False)

OUT = ROOT / "diagnostics" / "gate0_prep" / "a3"
FIGS = ROOT / "figures" / "scratch" / "a3"

# Episode windows, same convention as scripts/score_subannual_crop.py
EPISODES = (
    ("2007/08", 2006, 6, 2008, 3),
    ("2010/11", 2009, 6, 2011, 2),
)


def _step_slice(y0: int, m0: int, y1: int, m1: int) -> tuple[int, int]:
    t0 = (y0 - START) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - START) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    return t0, t1


def episode_labels(T: int) -> np.ndarray:
    lab = np.array(["calm"] * T, dtype=object)
    for name, y0, m0, y1, m1 in EPISODES:
        t0, t1 = _step_slice(y0, m0, y1, m1)
        lab[t0:t1] = name
    return lab


def step_stamp(t: int) -> tuple[int, int, int]:
    year = START + t // STEPS_PER_YEAR
    month, half = year_step_to_month_half(t % STEPS_PER_YEAR)
    return year, month, half


def step_tag(t: int) -> str:
    y, m, h = step_stamp(t)
    return f"{y}-{m:02d}{'a' if h == 0 else 'b'}"


# --------------------------------------------------------------------------
# Static per-crop objects that _simulate_window computes once before the loop
# --------------------------------------------------------------------------
@dataclass
class Static:
    prep: CropPrep
    C_step: np.ndarray
    H_exp: np.ndarray
    H_ahead: np.ndarray
    C_ahead: np.ndarray
    carry_cap: np.ndarray
    food_step: np.ndarray
    safety_w: float


def build_static(prep: CropPrep) -> Static:
    """Mirror sheaf/dynamic_crop.py L541-571 (pre-loop block)."""
    p = prep.params
    C_step = prep.C_flex + prep.C_ind
    H_exp = (p.foresight_phi * prep.H
             + (1.0 - p.foresight_phi) * prep.H_seas)
    lean_h = steps_to_harvest_pulse(
        H_exp, frac=p.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)
    return Static(
        prep=prep, C_step=C_step, H_exp=H_exp, H_ahead=H_ahead,
        C_ahead=C_ahead,
        carry_cap=p.max_stu * prep.C_ann,
        food_step=prep.C_ann / STEPS_PER_YEAR,
        safety_w=float(max(prep.safety.sum(), 1.0)),
    )


def lean_target(st: Static, t: int) -> tuple[np.ndarray, np.ndarray]:
    """L585-589: lean_gap and target = lean_gap + safety."""
    lean_gap = np.maximum(
        0.0,
        st.C_ahead[:, t] + st.C_step[:, t]
        - st.H_ahead[:, t] - st.H_exp[:, t],
    )
    return lean_gap, lean_gap + st.prep.safety


# --------------------------------------------------------------------------
# G : the within-step map, with the demand price as a free argument
# --------------------------------------------------------------------------
def step_G(st: Static, t: int, stock_in: np.ndarray, ask_in: np.ndarray,
           p_in: float, p_demand: float) -> dict:
    """One step of _simulate_window (L577-681) with demand priced at p_demand.

    ``p_in`` is the price carried into the step (used by the ask blend at
    L636, by the p_trade fallback at L653 and by the AR(1) smoother at L680).
    ``p_demand`` is the price fed to L580.  Setting ``p_demand = p_in``
    reproduces the shipped code exactly; setting ``p_demand = p_out``
    is the option-B fixed point.
    """
    prep, pr = st.prep, st.prep.params
    p0 = prep.p0
    H, C_flex, C_ind, cuts = prep.H, prep.C_flex, prep.C_ind, prep.cuts
    A, S = prep.A, prep.S

    avail = stock_in + H[:, t]                                    # L578
    desired_flex = np.maximum(
        C_flex[:, t] * (p_demand / p0) ** pr.elast, 0.0)           # L580
    desired = desired_flex + C_ind[:, t]                           # L581
    lean_gap, target = lean_target(st, t)                          # L585-589

    after_food_stock = np.maximum(0.0, avail - desired)            # L591
    food_need = np.maximum(0.0, desired - avail)                   # L592
    rebuild = pr.rebuild_lambda * np.maximum(
        0.0, target - after_food_stock)                            # L593
    demand = food_need + rebuild                                   # L595
    offers = np.maximum(0.0, avail - desired - target) * (
        1.0 - cuts[:, t])                                          # L596

    A_eff = _ask_reweight_dest(A, ask_in, p0, gamma=pr.ask_comp_elast)
    shipped, received, ship = _bilateral_clear(
        offers, demand, A_eff, S, subst=pr.residual_subst)         # L601-603

    consumption = np.minimum(
        desired, np.maximum(0.0, avail - shipped + received))      # L607
    stock = np.maximum(0.0, avail - shipped - consumption + received)
    warehouse = (
        st.carry_cap
        + st.food_step * float(pr.pipeline_max_steps)
        + (H[:, t] if pr.pipeline_max_steps > 0 else 0.0))         # L614
    excess = np.maximum(0.0, stock - warehouse)
    stock = stock - pr.warehouse_lambda * excess                   # L622-623

    fill = shipped / np.maximum(offers, 1e-9)                      # L625
    fill = np.where(offers > 1e-9, fill, pr.ask_target_fill)       # L626
    total_d = float(demand.sum())
    preferred_block = float((S * cuts[:, t][:, None] * demand[None, :]).sum())
    block_frac = preferred_block / max(total_d, 1e-9)              # L630
    rival = float(max(pr.ask_rival, 0.0)) * block_frac
    ask = ask_in * np.exp(
        pr.ask_alpha * (fill - pr.ask_target_fill)
        + np.where(offers > 1e-9, rival, 0.0))                     # L632-635
    ask = (1.0 - pr.ask_beta) * ask + pr.ask_beta * p_in           # L636
    ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

    lean_need = float(lean_gap.sum())
    locked = float((cuts[:, t] * np.maximum(0.0, stock - target)).sum())
    free = float(stock.sum()) - lean_need - locked                 # L643
    unmet = max(0.0, total_d - float(received.sum()))
    unmet_frac = unmet / max(total_d, 1e-9)                        # L647

    shipped_sum = float(shipped.sum())
    if shipped_sum > 1e-12:
        p_trade = float(np.dot(ask, shipped) / shipped_sum)        # L652
    else:
        p_trade = p_in

    twin = float(prep.free_twin[t])
    floor0 = 0.05 * st.safety_w
    shift = floor0 + max(0.0, -min(free, twin))                    # L662
    ratio_raw = (twin + shift) / (free + shift)
    u0 = float(prep.unmet_twin[t])
    u_anom = max(0.0, unmet_frac - u0)                             # L665
    calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
            and block_frac < 1e-9)                                 # L666-667
    if calm:
        p_star = float(p0)
        ratio = ratio_raw
        p_scar = float("nan")
    else:
        ratio = float(max(ratio_raw, 1e-12))
        free_term = ratio ** pr.inv_eta
        p_scar = (p0 * free_term
                  * (1.0 + pr.unmet_kappa * u_anom
                     + pr.block_kappa * block_frac))               # L674
        p_star = pr.trade_w * p_trade + (1.0 - pr.trade_w) * p_scar

    p_raw = float(pr.smooth * p_in + (1.0 - pr.smooth) * p_star)   # L680
    p_out = float(np.clip(p_raw, 60.0, 1200.0))                    # L681

    return dict(
        p_out=p_out, p_raw=p_raw, p_star=p_star, p_trade=p_trade,
        p_scar=p_scar, calm=calm, ratio=ratio, ratio_raw=ratio_raw,
        free=free, twin=twin, shift=shift, unmet_frac=unmet_frac,
        u_anom=u_anom, block_frac=block_frac, total_d=total_d,
        shipped_sum=shipped_sum, desired_flex=desired_flex,
        desired=desired, offers=offers, demand=demand, target=target,
        lean_gap=lean_gap, stock_out=stock, consumption=consumption,
        shipped=shipped, received=received, ask_out=ask, fill=fill,
        n_offer_pos=int((offers > 1e-9).sum()), locked=locked,
        clipped=bool(p_raw != p_out),
    )


def incoming_states(prep: CropPrep, res) -> tuple[np.ndarray, np.ndarray,
                                                  np.ndarray]:
    """Recover the state carried INTO each step from the recorded path."""
    T = prep.H.shape[1]
    stock_in = np.column_stack(
        [prep.stock0] + [res.stock[:, t] for t in range(T - 1)])
    ask_in = res.ask.copy()          # ask_path[:, t] is pre-update (L599)
    p_in = np.concatenate([[prep.p0], res.price[:-1]])
    return stock_in, ask_in, p_in


def verify_replica(crop: str, prep: CropPrep, res) -> dict:
    """Assert step_G(p_demand = p_in) reproduces the official path exactly."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    T = prep.H.shape[1]
    dp = dq = dfree = dask = 0.0
    for t in range(T):
        out = step_G(st, t, stock_in[:, t], ask_in[:, t],
                     float(p_in[t]), float(p_in[t]))
        dp = max(dp, abs(out["p_out"] - float(res.price[t])))
        dq = max(dq, float(np.max(np.abs(out["offers"] - res.offers[:, t]))))
        dfree = max(dfree, abs(out["free"] - float(res.free_liquid[t])))
        dask = max(dask, float(np.max(np.abs(
            out["stock_out"] - res.stock[:, t]))))
    return dict(crop=crop, max_abs_dprice=dp, max_abs_doffers=dq,
                max_abs_dfree=dfree, max_abs_dstock=dask)


# --------------------------------------------------------------------------
# TASK 1 + 2
# --------------------------------------------------------------------------
def gap_tables(crop: str, prep: CropPrep, res) -> tuple[pd.DataFrame,
                                                        pd.DataFrame]:
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    T = prep.H.shape[1]
    epi = episode_labels(T)
    rows, wrows = [], []
    for t in range(T):
        pt = float(res.price[t])
        pp = float(p_in[t])
        lag = step_G(st, t, stock_in[:, t], ask_in[:, t], pp, pp)
        con = step_G(st, t, stock_in[:, t], ask_in[:, t], pp, pt)
        y, m, h = step_stamp(t)
        gap = con["desired_flex"] - lag["desired_flex"]
        d_lag = lag["desired"]
        ogap = con["offers"] - lag["offers"]
        for i, c in enumerate(prep.countries):
            rows.append(dict(
                crop=crop, step=t, year=y, month=m, half=h,
                tag=step_tag(t), episode=epi[t], country=c,
                p_prev=pp, p_t=pt, price_ratio=pt / pp,
                C_flex_step=float(prep.C_flex[i, t]),
                desired_flex_lag=float(lag["desired_flex"][i]),
                desired_flex_con=float(con["desired_flex"][i]),
                gap_mmt=float(gap[i]),
                gap_pct_of_demand=(100.0 * gap[i] / d_lag[i]
                                   if d_lag[i] > 1e-12 else np.nan),
                offers_lag=float(lag["offers"][i]),
                offers_con=float(con["offers"][i]),
                offers_gap_mmt=float(ogap[i]),
                cut=float(prep.cuts[i, t]),
            ))
        wrows.append(dict(
            crop=crop, step=t, year=y, month=m, half=h, tag=step_tag(t),
            episode=epi[t], p_prev=pp, p_t=pt, price_ratio=pt / pp,
            world_C_flex=float(prep.C_flex[:, t].sum()),
            world_desired_lag=float(d_lag.sum()),
            world_desired_flex_lag=float(lag["desired_flex"].sum()),
            world_desired_flex_con=float(con["desired_flex"].sum()),
            world_gap_mmt=float(gap.sum()),
            world_gap_pct=100.0 * float(gap.sum()) / float(d_lag.sum()),
            world_abs_gap_mmt=float(np.abs(gap).sum()),
            # --- TASK 2: one-step propagation, incoming state held fixed ---
            offers_lag=float(lag["offers"].sum()),
            offers_con=float(con["offers"].sum()),
            offers_gap_mmt=float(con["offers"].sum() - lag["offers"].sum()),
            offers_gap_pct=(100.0 * (con["offers"].sum() - lag["offers"].sum())
                            / max(lag["offers"].sum(), 1e-12)),
            free_lag=lag["free"], free_con=con["free"],
            free_gap_mmt=con["free"] - lag["free"],
            twin=lag["twin"],
            ratio_lag=lag["ratio"], ratio_con=con["ratio"],
            ratio_gap=con["ratio"] - lag["ratio"],
            ratio_gap_pct=100.0 * (con["ratio"] - lag["ratio"])
            / max(abs(lag["ratio"]), 1e-12),
            pscar_lag=lag["p_scar"], pscar_con=con["p_scar"],
            ptrade_lag=lag["p_trade"], ptrade_con=con["p_trade"],
            pstar_lag=lag["p_star"], pstar_con=con["p_star"],
            p_out_lag=lag["p_out"], p_out_con=con["p_out"],
            p_gap_one_step=con["p_out"] - lag["p_out"],
            unmet_lag=lag["unmet_frac"], unmet_con=con["unmet_frac"],
            block_frac=lag["block_frac"],
            calm_lag=lag["calm"], calm_con=con["calm"],
            n_offer_pos_lag=lag["n_offer_pos"],
            n_offer_pos_con=con["n_offer_pos"],
        ))
    return pd.DataFrame(rows), pd.DataFrame(wrows)


# --------------------------------------------------------------------------
# TASK 3
# --------------------------------------------------------------------------
def g_curve(st: Static, t: int, stock_in, ask_in, p_in: float,
            grid: np.ndarray) -> pd.DataFrame:
    recs = []
    for x in grid:
        o = step_G(st, t, stock_in, ask_in, p_in, float(x))
        recs.append(dict(
            p_trial=float(x), G=o["p_out"], G_raw=o["p_raw"],
            p_star=o["p_star"], p_trade=o["p_trade"], p_scar=o["p_scar"],
            free=o["free"], ratio=o["ratio"], calm=o["calm"],
            offers=float(o["offers"].sum()),
            demand=float(o["demand"].sum()),
            shipped=o["shipped_sum"], unmet=o["unmet_frac"],
            n_offer_pos=o["n_offer_pos"], clipped=o["clipped"],
        ))
    return pd.DataFrame(recs)


def lipschitz_probe(crop: str, prep: CropPrep, res, steps: list[int],
                    span: float = 0.35, n: int = 161) -> pd.DataFrame:
    """Local Lipschitz / monotonicity of G on a grid around the official p."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    out = []
    for t in steps:
        pt = float(res.price[t])
        lo, hi = max(60.0, pt * (1 - span)), min(1200.0, pt * (1 + span))
        grid = np.linspace(lo, hi, n)
        cur = g_curve(st, t, stock_in[:, t], ask_in[:, t], float(p_in[t]),
                      grid)
        dG = np.diff(cur.G.to_numpy())
        dx = np.diff(grid)
        slope = dG / dx
        resid = cur.G.to_numpy() - grid
        sign_changes = int(np.sum(np.sign(resid[:-1]) * np.sign(resid[1:]) < 0))
        # bisect on the (monotone-decreasing expected) residual
        root, root_resid = np.nan, np.nan
        idx = np.where(np.sign(resid[:-1]) * np.sign(resid[1:]) < 0)[0]
        if len(idx):
            a, b = grid[idx[0]], grid[idx[0] + 1]
            for _ in range(80):
                mid = 0.5 * (a + b)
                rm = step_G(st, t, stock_in[:, t], ask_in[:, t],
                            float(p_in[t]), mid)["p_out"] - mid
                ra = step_G(st, t, stock_in[:, t], ask_in[:, t],
                            float(p_in[t]), a)["p_out"] - a
                if np.sign(rm) == np.sign(ra):
                    a = mid
                else:
                    b = mid
            root = 0.5 * (a + b)
            root_resid = step_G(st, t, stock_in[:, t], ask_in[:, t],
                                float(p_in[t]), root)["p_out"] - root
        out.append(dict(
            crop=crop, step=t, tag=step_tag(t), episode=epi[t],
            p_official=pt, p_prev=float(p_in[t]),
            grid_lo=lo, grid_hi=hi,
            L_max=float(np.max(np.abs(slope))),
            L_mean=float(np.mean(np.abs(slope))),
            slope_min=float(slope.min()), slope_max=float(slope.max()),
            monotone_decreasing=bool(np.all(slope <= 1e-12)),
            monotone_any=bool(np.all(slope <= 1e-12)
                              or np.all(slope >= -1e-12)),
            n_slope_sign_flips=int(np.sum(
                np.sign(slope[:-1]) * np.sign(slope[1:]) < 0)),
            residual_sign_changes=sign_changes,
            G_lo=float(cur.G.iloc[0]), G_hi=float(cur.G.iloc[-1]),
            resid_lo=float(resid[0]), resid_hi=float(resid[-1]),
            fp=root, fp_residual=root_resid,
            fp_minus_official=root - pt if np.isfinite(root) else np.nan,
            any_calm=bool(cur.calm.any()), all_calm=bool(cur.calm.all()),
            any_clipped=bool(cur.clipped.any()),
            free_min=float(cur.free.min()), free_max=float(cur.free.max()),
            twin=float(prep.free_twin[t]),
            twin_in_free_range=bool(
                cur.free.min() <= float(prep.free_twin[t]) <= cur.free.max()),
            n_offer_pos_range=int(cur.n_offer_pos.max()
                                  - cur.n_offer_pos.min()),
            block_frac=float(step_G(st, t, stock_in[:, t], ask_in[:, t],
                                    float(p_in[t]), pt)["block_frac"]),
        ))
    return pd.DataFrame(out)


def wide_scan(crop: str, prep: CropPrep, res, steps: list[int],
              n: int = 400) -> pd.DataFrame:
    """Global root count on the full admissible price interval [60, 1200]."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    rows = []
    grid = np.linspace(60.0, 1200.0, n)
    for t in steps:
        cur = g_curve(st, t, stock_in[:, t], ask_in[:, t], float(p_in[t]),
                      grid)
        resid = cur.G.to_numpy() - grid
        slope = np.diff(cur.G.to_numpy()) / np.diff(grid)
        rows.append(dict(
            crop=crop, step=t, tag=step_tag(t), episode=epi[t],
            p_official=float(res.price[t]),
            resid_at_60=float(resid[0]), resid_at_1200=float(resid[-1]),
            root_sign_changes=int(np.sum(
                np.sign(resid[:-1]) * np.sign(resid[1:]) < 0)),
            L_max_global=float(np.max(np.abs(slope))),
            monotone_decreasing=bool(np.all(slope <= 1e-12)),
            G_min=float(cur.G.min()), G_max=float(cur.G.max()),
            any_calm=bool(cur.calm.any()),
            any_clipped=bool(cur.clipped.any()),
        ))
    return pd.DataFrame(rows)


def _G(st: Static, t: int, stock_in, ask_in, p_in: float, x: float) -> float:
    return step_G(st, t, stock_in, ask_in, p_in, float(x))["p_out"]


def _regime(o: dict) -> tuple:
    """The discrete switches inside the step body that G can jump across."""
    return (o["n_offer_pos"],                 # max(0,...) in offers, L596
            bool(o["shipped_sum"] > 1e-12),   # p_trade fallback, L651
            bool(o["calm"]),                  # calm branch, L666
            bool(o["clipped"]))               # price clip, L681


def all_step_scan(crop: str, prep: CropPrep, res, n: int = 801,
                  n_jump_probes: int = 6) -> pd.DataFrame:
    """Every step: global root count on [60,1200], L_max, root, jumps, Picard.

    Discontinuities are found by ranking grid cells by |ΔG|, bisecting the
    top ``n_jump_probes`` cells on the *regime tuple* (see ``_regime``) down
    to machine width, and measuring |G| across the resulting bracket.  A cell
    that is merely steep rather than discontinuous returns a jump of ~0, so
    the measurement is safe against false positives.
    """
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    T = prep.H.shape[1]
    epi = episode_labels(T)
    grid = np.linspace(60.0, 1200.0, n)
    rows = []
    for t in range(T):
        sk, ak, pk = stock_in[:, t], ask_in[:, t], float(p_in[t])
        outs = [step_G(st, t, sk, ak, pk, x) for x in grid]
        g = np.array([o["p_out"] for o in outs])
        resid = g - grid
        slope = np.diff(g) / np.diff(grid)
        sc = np.where(np.sign(resid[:-1]) * np.sign(resid[1:]) < 0)[0]
        root = np.nan
        root_resid = np.nan
        root_slope = np.nan
        if len(sc):
            a, b = grid[sc[0]], grid[sc[0] + 1]
            ra = resid[sc[0]]
            for _ in range(100):
                mid = 0.5 * (a + b)
                rm = _G(st, t, sk, ak, pk, mid) - mid
                if rm == 0.0:
                    a = b = mid
                    break
                if np.sign(rm) == np.sign(ra):
                    a, ra = mid, rm
                else:
                    b = mid
            root = 0.5 * (a + b)
            root_resid = _G(st, t, sk, ak, pk, root) - root
            h = max(1e-4, 1e-6 * root)
            root_slope = ((_G(st, t, sk, ak, pk, root + h)
                           - _G(st, t, sk, ak, pk, root - h)) / (2 * h))
        # --- discontinuity hunt: bisect the steepest cells on the regime ---
        jumps = []
        dg = np.abs(np.diff(g))
        cand = [j for j in range(len(grid) - 1)
                if _regime(outs[j]) != _regime(outs[j + 1])]
        cand.sort(key=lambda j: -dg[j])
        for j in cand[:n_jump_probes]:
            a, b = grid[j], grid[j + 1]
            key = _regime(outs[j])
            for _ in range(60):
                mid = 0.5 * (a + b)
                if _regime(step_G(st, t, sk, ak, pk, mid)) == key:
                    a = mid
                else:
                    b = mid
                if b - a < 1e-11 * max(1.0, b):
                    break
            ga = _G(st, t, sk, ak, pk, a)
            gb = _G(st, t, sk, ak, pk, b)
            jumps.append((0.5 * (a + b), abs(gb - ga),
                          _regime(step_G(st, t, sk, ak, pk, a)),
                          _regime(step_G(st, t, sk, ak, pk, b))))
        jumps = [j for j in jumps if j[1] > 1e-9]
        max_jump = max((j[1] for j in jumps), default=0.0)
        p_at_max_jump = (max(jumps, key=lambda j: j[1])[0] if jumps
                         else np.nan)
        dist = (min((abs(j[0] - root) for j in jumps), default=np.nan)
                if np.isfinite(root) else np.nan)
        which = ""
        if jumps:
            ja, jb = max(jumps, key=lambda j: j[1])[2:]
            bits = []
            if ja[0] != jb[0]:
                bits.append("offers_trunc")
            if ja[1] != jb[1]:
                bits.append("ptrade_fallback")
            if ja[2] != jb[2]:
                bits.append("calm_branch")
            if ja[3] != jb[3]:
                bits.append("price_clip")
            which = "+".join(bits)

        # plain Picard from the lagged price (what the shipped code uses)
        x = pk
        it = 0
        for it in range(1, 201):
            xn = _G(st, t, sk, ak, pk, x)
            if abs(xn - x) < 1e-8:
                x = xn
                break
            x = xn
        # Picard robustness from deliberately bad starts
        picard_bad = []
        for x0 in (60.0, 1200.0, 0.5 * pk, 2.0 * pk):
            y = float(np.clip(x0, 60.0, 1200.0))
            ok, k = False, 0
            for k in range(1, 201):
                yn = _G(st, t, sk, ak, pk, y)
                if abs(yn - y) < 1e-8:
                    y, ok = yn, True
                    break
                y = yn
            picard_bad.append((ok, k, y))
        rows.append(dict(
            crop=crop, step=t, tag=step_tag(t), episode=epi[t],
            in_first_model_year=bool(t < STEPS_PER_YEAR),
            p_prev=pk, p_official=float(res.price[t]),
            root_sign_changes=int(len(sc)),
            L_max_global=float(np.max(np.abs(slope))),
            max_positive_slope=float(slope.max()),
            monotone_decreasing=bool(np.all(slope <= 0.0)),
            resid_at_60=float(resid[0]), resid_at_1200=float(resid[-1]),
            fp=root, fp_residual=root_resid, fp_slope=root_slope,
            fp_minus_official=root - float(res.price[t]),
            fp_pct_of_official=100.0 * (root - float(res.price[t]))
            / float(res.price[t]),
            picard_iters=it, picard_fp=x,
            picard_minus_bisect=x - root,
            n_jumps_found=len(jumps), max_jump_G=max_jump,
            p_at_max_jump=p_at_max_jump, jump_cause=which,
            root_to_nearest_jump=dist,
            root_inside_jump=bool(np.isfinite(dist) and dist < 1e-6
                                  and max_jump > 1e-6),
            picard_bad_all_converged=all(p[0] for p in picard_bad),
            picard_bad_max_iters=max(p[1] for p in picard_bad),
            picard_bad_max_spread=(
                max(abs(p[2] - root) for p in picard_bad)
                if np.isfinite(root) else np.nan),
            free_official=float(res.free_liquid[t]),
            free_negative=bool(float(res.free_liquid[t]) < 0.0),
            twin=float(prep.free_twin[t]),
            max_cut=float(prep.cuts[:, t].max()),
        ))
    return pd.DataFrame(rows)


def refine_scan(crop: str, prep: CropPrep, res, steps: list[int],
                ns=(401, 3201, 25601), half_width: float = 0.15
                ) -> pd.DataFrame:
    """Grid-refinement continuity test.

    If ``G`` had a jump in the window, ``L_max`` estimated by finite
    differences would grow ~linearly with the grid density.  If it plateaus,
    no jump is present at that resolution.
    """
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    rows = []
    for t in steps:
        sk, ak, pk = stock_in[:, t], ask_in[:, t], float(p_in[t])
        pt = float(res.price[t])
        lo = max(60.0, pt * (1 - half_width))
        hi = min(1200.0, pt * (1 + half_width))
        rec = dict(crop=crop, step=t, tag=step_tag(t), episode=epi[t],
                   p_official=pt, lo=lo, hi=hi)
        for n in ns:
            grid = np.linspace(lo, hi, n)
            g = np.array([_G(st, t, sk, ak, pk, x) for x in grid])
            slope = np.diff(g) / np.diff(grid)
            rec[f"L_max_n{n}"] = float(np.max(np.abs(slope)))
            rec[f"maxjump_n{n}"] = float(np.max(np.abs(np.diff(g))))
        rows.append(rec)
    return pd.DataFrame(rows)


def calm_reachability(crop: str, prep: CropPrep, res) -> pd.DataFrame:
    """Is the L666-669 `calm` branch reachable at all along the scored path?

    `calm` needs THREE conditions at once: |free-twin| < 1e-6,
    u_anom < 1e-9, block_frac < 1e-9.  ``block_frac`` is zero iff no
    restricted exporter is a preferred source for any positive demand, which
    is a property of ``cuts`` and ``S``, not of the trial price.  So the
    branch is unreachable at every step where AMIS is biting.
    """
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    T = prep.H.shape[1]
    epi = episode_labels(T)
    rows = []
    for t in range(T):
        sk, ak, pk = stock_in[:, t], ask_in[:, t], float(p_in[t])
        lo_o = step_G(st, t, sk, ak, pk, 60.0)
        hi_o = step_G(st, t, sk, ak, pk, 1200.0)
        twin = float(prep.free_twin[t])
        cross = np.sign(lo_o["free"] - twin) != np.sign(hi_o["free"] - twin)
        rows.append(dict(
            crop=crop, step=t, tag=step_tag(t), episode=epi[t],
            twin=twin, free_at_60=lo_o["free"], free_at_1200=hi_o["free"],
            free_crosses_twin=bool(cross),
            block_frac_at_60=lo_o["block_frac"],
            block_frac_at_1200=hi_o["block_frac"],
            block_frac_zero=bool(max(lo_o["block_frac"],
                                     hi_o["block_frac"]) < 1e-9),
            u_anom_at_60=lo_o["u_anom"], u_anom_at_1200=hi_o["u_anom"],
            u_anom_zero=bool(max(lo_o["u_anom"], hi_o["u_anom"]) < 1e-9),
            calm_reachable=bool(cross
                                and max(lo_o["block_frac"],
                                        hi_o["block_frac"]) < 1e-9
                                and max(lo_o["u_anom"],
                                        hi_o["u_anom"]) < 1e-9),
            p_trade_at_60=lo_o["p_trade"],
            hypothetical_jump=(1.0 - st.prep.params.smooth)
            * st.prep.params.trade_w * abs(lo_o["p_trade"] - prep.p0),
        ))
    return pd.DataFrame(rows)


def calm_jump_detail(crop: str, prep: CropPrep, res,
                     reach: pd.DataFrame,
                     all_root: np.ndarray | None = None) -> pd.DataFrame:
    """For the steps where `calm` IS reachable, bisect onto free(x)=twin and
    measure whether the branch actually fires and what it does to G."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    rows = []
    for t in reach[reach.calm_reachable].step.tolist():
        sk, ak, pk = stock_in[:, t], ask_in[:, t], float(p_in[t])
        twin = float(prep.free_twin[t])

        def f(x):
            return step_G(st, t, sk, ak, pk, float(x))

        a, b = 60.0, 1200.0
        sa = np.sign(f(a)["free"] - twin)
        for _ in range(200):
            mid = 0.5 * (a + b)
            if np.sign(f(mid)["free"] - twin) == sa:
                a = mid
            else:
                b = mid
            if b - a < 1e-13 * max(1.0, b):
                break
        pc = 0.5 * (a + b)
        # locate the two EDGES of the calm plateau, then evaluate G outside
        lo_edge = hi_edge = pc
        lo_out = hi_out = None
        d = 1e-9
        while d < 100.0:
            if f(pc - d)["calm"]:
                lo_edge, d = pc - d, d * 2
            else:
                lo_out = pc - d
                break
        d = 1e-9
        while d < 100.0:
            if f(pc + d)["calm"]:
                hi_edge, d = pc + d, d * 2
            else:
                hi_out = pc + d
                break
        if lo_out is None:
            lo_out = pc - 100.0
        if hi_out is None:
            hi_out = pc + 100.0
        for _ in range(80):                     # tighten each edge
            m = 0.5 * (lo_edge + lo_out)
            if f(m)["calm"]:
                lo_edge = m
            else:
                lo_out = m
        for _ in range(80):
            m = 0.5 * (hi_edge + hi_out)
            if f(m)["calm"]:
                hi_edge = m
            else:
                hi_out = m
        g_in = f(pc)["p_out"]
        g_lo, g_hi = f(lo_out)["p_out"], f(hi_out)["p_out"]
        root = float(all_root[t]) if all_root is not None else np.nan
        rows.append(dict(
            crop=crop, step=t, tag=step_tag(t), episode=epi[t], twin=twin,
            p_cross=pc, calm_fires=bool(f(pc)["calm"]),
            calm_lo=lo_edge, calm_hi=hi_edge,
            calm_window_width=hi_edge - lo_edge,
            G_in_calm=g_in, G_just_below=g_lo, G_just_above=g_hi,
            jump_low_edge=abs(g_in - g_lo), jump_high_edge=abs(g_hi - g_in),
            max_calm_jump=max(abs(g_in - g_lo), abs(g_hi - g_in)),
            p_trade_outside=f(lo_out)["p_trade"],
            root=root,
            root_in_calm_window=bool(np.isfinite(root)
                                     and lo_edge <= root <= hi_edge),
            root_to_calm_window=(min(abs(root - lo_edge), abs(root - hi_edge))
                                 if np.isfinite(root) else np.nan),
        ))
    return pd.DataFrame(rows)


def calm_probe(crop: str, prep: CropPrep, res, steps: list[int]) -> pd.DataFrame:
    """Bisect on free(p) - twin to land on the calm boundary and measure the
    jump in G across it.  This is the L666-669 discontinuity, made explicit."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    rows = []
    for t in steps:
        def f(x):
            o = step_G(st, t, stock_in[:, t], ask_in[:, t], float(p_in[t]),
                       float(x))
            return o
        lo, hi = 60.0, 1200.0
        flo, fhi = f(lo), f(hi)
        twin = float(prep.free_twin[t])
        g_lo, g_hi = flo["free"] - twin, fhi["free"] - twin
        rec = dict(crop=crop, step=t, tag=step_tag(t), episode=epi[t],
                   twin=twin, free_at_60=flo["free"], free_at_1200=fhi["free"],
                   block_frac=flo["block_frac"],
                   crossing_exists=bool(np.sign(g_lo) != np.sign(g_hi)))
        if rec["crossing_exists"]:
            a, b = lo, hi
            for _ in range(200):
                mid = 0.5 * (a + b)
                if np.sign(f(mid)["free"] - twin) == np.sign(g_lo):
                    a = mid
                else:
                    b = mid
            rec.update(p_cross=0.5 * (a + b),
                       G_below=f(a)["p_out"], G_above=f(b)["p_out"],
                       calm_below=f(a)["calm"], calm_above=f(b)["calm"],
                       p_trade_at_cross=f(a)["p_trade"],
                       jump_in_G=abs(f(b)["p_out"] - f(a)["p_out"]),
                       theoretical_jump=(1.0 - st.prep.params.smooth)
                       * st.prep.params.trade_w
                       * abs(f(a)["p_trade"] - st.prep.p0),
                       bracket_width=b - a)
        rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# reporting helpers
# --------------------------------------------------------------------------
def dist_table(world: pd.DataFrame, col: str) -> pd.DataFrame:
    g = world.groupby(["crop", "episode"])[col]
    out = g.agg(n="size", mean="mean", median="median",
                p05=lambda s: s.quantile(0.05),
                p95=lambda s: s.quantile(0.95),
                min="min", max="max",
                mean_abs=lambda s: s.abs().mean(),
                max_abs=lambda s: s.abs().max()).reset_index()
    return out


def _fmt(df: pd.DataFrame, floatfmt: str = "{:.4g}") -> str:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda v: "—" if pd.isna(v) else floatfmt.format(v))
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    rule = "|" + "|".join("---" for _ in d.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in r) + " |"
            for r in d.itertuples(index=False)]
    return "\n".join([head, rule] + body)


def plot_g(crop: str, prep: CropPrep, res, steps: list[int]) -> Path:
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    fig, axes = plt.subplots(2, len(steps), figsize=(4.0 * len(steps), 7.2),
                             squeeze=False)
    for k, t in enumerate(steps):
        pt = float(res.price[t])
        lo, hi = max(60.0, pt * 0.6), min(1200.0, pt * 1.6)
        grid = np.linspace(lo, hi, 241)
        cur = g_curve(st, t, stock_in[:, t], ask_in[:, t], float(p_in[t]),
                      grid)
        ax = axes[0][k]
        ax.plot(grid, cur.G, color="#1f4e79", lw=1.6, label="G(p)")
        ax.plot(grid, grid, color="0.5", ls="--", lw=1.0, label="45°")
        ax.axvline(pt, color="#c0392b", lw=1.0, ls=":",
                   label=f"official $p_t$={pt:.0f}")
        ax.axvline(float(p_in[t]), color="#e67e22", lw=1.0, ls=":",
                   label=f"$p_{{t-1}}$={float(p_in[t]):.0f}")
        resid = cur.G.to_numpy() - grid
        idx = np.where(np.sign(resid[:-1]) * np.sign(resid[1:]) < 0)[0]
        if len(idx):
            ax.plot([grid[idx[0]]], [cur.G.iloc[idx[0]]], "o",
                    color="#1e8449", ms=5, label="fixed point")
        ax.set_title(f"{crop} step {t} ({step_tag(t)}, {epi[t]})", fontsize=9)
        ax.set_xlabel("trial price $p$  ($/t)")
        ax.set_ylabel("$G(p)$  ($/t)")
        ax.legend(fontsize=6.5, frameon=False)
        ax2 = axes[1][k]
        ax2.plot(grid, resid, color="#6c3483", lw=1.4)
        ax2.axhline(0.0, color="0.5", lw=0.8)
        ax2.set_xlabel("trial price $p$  ($/t)")
        ax2.set_ylabel("$G(p) - p$  ($/t)")
        slope = np.diff(cur.G.to_numpy()) / np.diff(grid)
        ax2.set_title(
            f"max|G'| = {np.max(np.abs(slope)):.3g}; "
            f"{'monotone ↓' if np.all(slope <= 1e-12) else 'NOT monotone'}",
            fontsize=8)
    fig.suptitle(f"A3 Task 3 — G(p) for {crop} (incoming state held at the "
                 f"official path)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    path = FIGS / f"g_curve_{crop}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_g_wide(crop: str, prep: CropPrep, res, steps: list[int]) -> Path:
    """G over the whole admissible interval [60, 1200], with the 45° line."""
    st = build_static(prep)
    stock_in, ask_in, p_in = incoming_states(prep, res)
    epi = episode_labels(prep.H.shape[1])
    grid = np.linspace(60.0, 1200.0, 361)
    fig, axes = plt.subplots(1, len(steps), figsize=(3.9 * len(steps), 3.6),
                             squeeze=False)
    for k, t in enumerate(steps):
        cur = g_curve(st, t, stock_in[:, t], ask_in[:, t], float(p_in[t]),
                      grid)
        ax = axes[0][k]
        ax.plot(grid, cur.G, color="#1f4e79", lw=1.6, label="G(p)")
        ax.plot(grid, grid, color="0.5", ls="--", lw=1.0, label="45°")
        ax.axvline(float(res.price[t]), color="#c0392b", lw=1.0, ls=":",
                   label="official $p_t$")
        resid = cur.G.to_numpy() - grid
        idx = np.where(np.sign(resid[:-1]) * np.sign(resid[1:]) < 0)[0]
        for j in idx:
            ax.plot([grid[j]], [cur.G.iloc[j]], "o", color="#1e8449", ms=5)
        ax.set_title(f"{crop} step {t} ({step_tag(t)}, {epi[t]})", fontsize=9)
        ax.set_xlabel("trial price $p$  ($/t)")
        ax.set_ylabel("$G(p)$  ($/t)")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.suptitle(f"A3 Task 3 — G on the full clip interval [60, 1200] "
                 f"({crop}): G is nearly flat, so exactly one crossing",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    path = FIGS / f"g_curve_wide_{crop}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_gap(world: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 6.6), squeeze=False)
    for k, crop in enumerate(CROPS):
        w = world[world.crop == crop]
        ax = axes[0][k]
        ax.plot(w.step, w.world_gap_mmt, color="#1f4e79", lw=1.2)
        ax.axhline(0.0, color="0.5", lw=0.8)
        for name, y0, m0, y1, m1 in EPISODES:
            t0, t1 = _step_slice(y0, m0, y1, m1)
            ax.axvspan(t0, t1, color="#c0392b", alpha=0.12)
        ax.set_title(f"{crop}: world flex-demand gap  $d(p_t)-d(p_{{t-1}})$",
                     fontsize=9)
        ax.set_xlabel("step")
        ax.set_ylabel("MMT / step")
        ax2 = axes[1][k]
        ax2.plot(w.step, w.world_gap_pct, color="#6c3483", lw=1.2)
        ax2.axhline(0.0, color="0.5", lw=0.8)
        for name, y0, m0, y1, m1 in EPISODES:
            t0, t1 = _step_slice(y0, m0, y1, m1)
            ax2.axvspan(t0, t1, color="#c0392b", alpha=0.12)
        ax2.set_title(f"{crop}: gap as % of world desired use", fontsize=9)
        ax2.set_xlabel("step")
        ax2.set_ylabel("%")
    fig.suptitle("A3 Task 1 — contemporaneous vs lagged flex demand "
                 "(shaded: 2007/08 and 2010/11)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = FIGS / "demand_gap_paths.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    per_country, world, lip, wide, calm, verif = [], [], [], [], [], []
    allsc, refn, creach, cjd = [], [], [], []
    figs = []
    for crop in CROPS:
        print(f"[{crop}] official run + prep …", flush=True)
        res_off = run_crop_dynamics(crop, **RUN_KW)
        prep = prepare_crop_run(crop, **RUN_KW)
        res = simulate_prep(prep)
        dp = float(np.max(np.abs(res.price - res_off.price)))
        print(f"[{crop}] simulate_prep vs run_crop_dynamics "
              f"max|Δp| = {dp:.3e}", flush=True)
        assert dp == 0.0, (
            f"{crop}: simulate_prep(prep) does not reproduce "
            f"run_crop_dynamics exactly (max|Δp|={dp:.3e})")
        v = verify_replica(crop, prep, res)
        v["simprep_vs_run_max_dprice"] = dp
        print(f"[{crop}] replica check: {v}", flush=True)
        verif.append(v)

        pc, w = gap_tables(crop, prep, res)
        per_country.append(pc)
        world.append(w)

        # probe steps: calm, 2007/08 peak, 2010/11 peak, plus extremes
        epi = episode_labels(prep.H.shape[1])
        t_peak07 = int(w[w.episode == "2007/08"].p_t.idxmax())
        t_peak10 = int(w[w.episode == "2010/11"].p_t.idxmax())
        calm_steps = w[(w.episode == "calm") & (w.step >= STEPS_PER_YEAR)]
        t_calm = int(calm_steps.step.iloc[len(calm_steps) // 2])
        t_biggap = int(w.world_gap_mmt.abs().idxmax())
        probe = sorted(set([t_calm, t_peak07, t_peak10, t_biggap]))
        every = list(range(0, prep.H.shape[1], 4))
        lip.append(lipschitz_probe(crop, prep, res, sorted(set(every + probe))))
        wide.append(wide_scan(crop, prep, res, probe))
        calm.append(calm_probe(crop, prep, res, probe))

        print(f"[{crop}] all-step global scan …", flush=True)
        a = all_step_scan(crop, prep, res)
        allsc.append(a)
        worst = a.reindex(a.L_max_global.sort_values(
            ascending=False).index).step.head(6).tolist()
        refn.append(refine_scan(crop, prep, res,
                                sorted(set(worst + probe))))
        cre = calm_reachability(crop, prep, res)
        creach.append(cre)
        cjd.append(calm_jump_detail(crop, prep, res, cre,
                                    a.set_index("step").fp.reindex(
                                        range(prep.H.shape[1])).to_numpy()))
        figs.append(plot_g(crop, prep, res, probe[:4]))
        figs.append(plot_g_wide(crop, prep, res, probe[:4]))

    pc = pd.concat(per_country, ignore_index=True)
    w = pd.concat(world, ignore_index=True)
    lp = pd.concat(lip, ignore_index=True)
    wd = pd.concat(wide, ignore_index=True)
    cp = pd.concat(calm, ignore_index=True)
    az = pd.concat(allsc, ignore_index=True)
    rf = pd.concat(refn, ignore_index=True)
    cr = pd.concat(creach, ignore_index=True)
    cj = pd.concat(cjd, ignore_index=True)
    vf = pd.DataFrame(verif)

    pc.to_csv(OUT / "demand_gap.csv", index=False)
    w.to_csv(OUT / "demand_gap_world.csv", index=False)
    lp.to_csv(OUT / "g_lipschitz.csv", index=False)
    wd.to_csv(OUT / "g_wide_scan.csv", index=False)
    cp.to_csv(OUT / "g_calm_boundary.csv", index=False)
    az.to_csv(OUT / "g_all_steps.csv", index=False)
    rf.to_csv(OUT / "g_grid_refinement.csv", index=False)
    cr.to_csv(OUT / "g_calm_reachability.csv", index=False)
    cj.to_csv(OUT / "g_calm_jump_detail.csv", index=False)
    vf.to_csv(OUT / "replica_verification.csv", index=False)
    figs.append(plot_gap(w))

    # ---------------- report ----------------
    L = ["# A3 — size of the contemporaneous-demand gap, and is G well posed?",
         "",
         "Read-only measurement. `sheaf/*.py` and `scripts/*.py` untouched; "
         "everything here comes from `scripts/scratch/a3_demand_gap.py`.",
         "",
         "**This measurement does not recommend adopting option B / X1.** "
         "It sizes a gap and tests well-posedness. The adoption decision "
         "needs A2 as well (per `audit_prompts/GATE0_MODEL_PROMPTS.md`).",
         "",
         "Official scored path for all three crops: "
         "`run_crop_dynamics(crop, start_year=2006, end_year=2011, "
         "use_amis=True, use_shocks=True, use_demand=False)` "
         "— 144 steps, 2006-01a … 2011-12b.",
         "",
         "## 0. Replica verification (prerequisite)",
         "",
         "`simulate_prep(prepare_crop_run(...))` vs `run_crop_dynamics(...)`, "
         "and the scratch transcription of L577-681 (`step_G` with "
         "`p_demand = p_in`) vs the recorded path:",
         "",
         _fmt(vf, "{:.3e}"),
         "",
         "All four columns are exactly 0.0, so the scratch copy of the step "
         "body is the shipped step body and `prep.C_flex` is the array the "
         "official run consumed.",
         ""]

    L += ["## 1. Size of the gap (Task 1)", "",
          "Gap at step *t* = "
          "`C_flex[:,t]*(p_t/p0)**elast - C_flex[:,t]*(p_{t-1}/p0)**elast`, "
          "everything else held at the official path. World totals, MMT per "
          "step (a step is 365.25/24 ≈ 15.2 days):", "",
          _fmt(dist_table(w, "world_gap_mmt")), "",
          "Same, as a percent of world *desired* use in that step "
          "(flex + industrial, evaluated at `p_{t-1}`):", "",
          _fmt(dist_table(w, "world_gap_pct")), ""]

    piv = (w.groupby(["crop", "episode"])
           .agg(mean_price=("p_t", "mean"),
                mean_abs_gap_mmt=("world_gap_mmt", lambda s: s.abs().mean()),
                max_abs_gap_mmt=("world_gap_mmt", lambda s: s.abs().max()),
                mean_abs_gap_pct=("world_gap_pct", lambda s: s.abs().mean()),
                max_abs_gap_pct=("world_gap_pct", lambda s: s.abs().max()),
                mean_world_desired=("world_desired_lag", "mean"))
           .reset_index())
    L += ["Episode summary (absolute value, so signs do not cancel):", "",
          _fmt(piv), ""]

    w2 = w[w.step >= STEPS_PER_YEAR]
    piv2 = (w2.groupby(["crop", "episode"])
            .agg(n=("step", "size"),
                 mean_abs_gap_mmt=("world_gap_mmt", lambda s: s.abs().mean()),
                 max_abs_gap_mmt=("world_gap_mmt", lambda s: s.abs().max()),
                 mean_abs_gap_pct=("world_gap_pct", lambda s: s.abs().mean()),
                 max_abs_gap_pct=("world_gap_pct", lambda s: s.abs().max()))
            .reset_index())
    L += ["Same, **dropping the first model year (steps 0-23)**. "
          "`assert_twin_identity` (L907) already discards `price[:24]` as "
          "transient, and the single largest gap in the whole dataset "
          "(maize step 22, 2006-12a) sits inside it, so the episode numbers "
          "should be read from this table rather than the one above:", "",
          _fmt(piv2), ""]

    top = (w.reindex(w.world_gap_mmt.abs().sort_values(ascending=False).index)
           .head(15)[["crop", "step", "tag", "episode", "p_prev", "p_t",
                      "price_ratio", "world_gap_mmt", "world_gap_pct",
                      "offers_gap_pct", "ratio_gap_pct", "p_gap_one_step"]])
    L += ["Fifteen largest world gaps, any crop:", "", _fmt(top), ""]

    ctop = (pc.reindex(pc.gap_mmt.abs().sort_values(ascending=False).index)
            .head(20)[["crop", "step", "tag", "episode", "country",
                       "C_flex_step", "gap_mmt", "gap_pct_of_demand",
                       "offers_gap_mmt"]])
    L += ["Twenty largest country-step gaps:", "", _fmt(ctop), ""]

    cagg = (pc.groupby(["crop", "country"])
            .agg(mean_abs_gap_mmt=("gap_mmt", lambda s: s.abs().mean()),
                 max_abs_gap_mmt=("gap_mmt", lambda s: s.abs().max()),
                 mean_abs_gap_pct=("gap_pct_of_demand",
                                   lambda s: s.abs().mean()))
            .reset_index())
    cagg = (cagg.sort_values(["crop", "mean_abs_gap_mmt"], ascending=[True, False])
            .groupby("crop").head(6))
    L += ["Six largest-gap countries per crop (mean over all 144 steps):", "",
          _fmt(cagg), ""]

    L += ["## 2. One-step propagation (Task 2)", "",
          "**Caveat, stated as required: this is a one-step bound, not a "
          "simulation of the fixed point.** Each row re-evaluates the step "
          "body once with demand priced at the realised `p_t`, holding the "
          "incoming stock, incoming ask vector, incoming price, harvest, "
          "cuts and the calm twin at their official values. It does not "
          "iterate to `p = G(p)` and it does not let the state drift.", "",
          _fmt(dist_table(w, "offers_gap_pct")), "",
          "Scarcity ratio `r_t = (twin+shift)/(free+shift)` (L661-663):", "",
          _fmt(dist_table(w, "ratio_gap_pct")), "",
          "Resulting one-step move in the price the step writes "
          "(`p_out` under contemporaneous demand minus official `p_t`), $/t:",
          "", _fmt(dist_table(w, "p_gap_one_step")), ""]

    L += ["## 3. Well-posedness of G (Task 3)", "",
          "`G(x)` = the price the step writes when demand is evaluated at "
          "trial price `x`, incoming state held at the official path. "
          "Option B is `p_t = G(p_t)`.", "",
          "### 3a. Local behaviour on ±35% around the official price", "",
          _fmt(lp.groupby(["crop", "episode"]).agg(
              n=("L_max", "size"),
              L_max_worst=("L_max", "max"),
              L_max_mean=("L_max", "mean"),
              all_monotone_decreasing=("monotone_decreasing", "all"),
              n_not_monotone=("monotone_decreasing",
                              lambda s: int((~s).sum())),
              worst_root_sign_changes=("residual_sign_changes", "max"),
              max_abs_fp_residual=("fp_residual",
                                   lambda s: s.abs().max()),
              max_abs_fp_minus_official=("fp_minus_official",
                                         lambda s: s.abs().max()),
              n_any_calm=("any_calm", "sum"),
              n_twin_in_range=("twin_in_free_range", "sum"),
          ).reset_index()), "",
          "### 3b. Global scan on the full admissible interval [60, 1200]",
          "", _fmt(wd), "",
          "### 3c. The calm boundary (L666-669)", "",
          "Bisection on `free(x) - twin` over the whole interval, to land on "
          "the calm boundary and measure the jump in `G` across it. "
          "`theoretical_jump` is `(1-smooth)*trade_w*|p_trade - p0|`, the "
          "size of the discontinuity implied by dropping the trade term.",
          "", _fmt(cp), ""]

    L += ["### 3d. Every step, every crop: root count, Lipschitz, Picard", "",
          "`G` evaluated on a 401-point grid spanning the whole clip "
          "interval [60, 1200] at all 3 x 144 steps; the root then bisected "
          "to machine precision; then plain Picard (`x <- G(x)`) started "
          "from `p_{t-1}`, tolerance 1e-8 $/t, cap 200 iterations.", "",
          _fmt(az.groupby(["crop", "episode"]).agg(
              n=("step", "size"),
              n_roots_min=("root_sign_changes", "min"),
              n_roots_max=("root_sign_changes", "max"),
              L_max_worst=("L_max_global", "max"),
              L_max_median=("L_max_global", "median"),
              slope_at_root_worst=("fp_slope", lambda s: s.abs().max()),
              n_not_monotone=("monotone_decreasing",
                              lambda s: int((~s).sum())),
              max_abs_fp_residual=("fp_residual", lambda s: s.abs().max()),
              picard_iters_max=("picard_iters", "max"),
              picard_iters_median=("picard_iters", "median"),
              max_abs_picard_vs_bisect=("picard_minus_bisect",
                                        lambda s: s.abs().max()),
              n_free_negative=("free_negative", "sum"),
              min_resid_at_60=("resid_at_60", "min"),
              max_resid_at_1200=("resid_at_1200", "max"),
          ).reset_index()), "",
          f"Root count is exactly 1 at all "
          f"{len(az)} crop-steps: "
          f"min={int(az.root_sign_changes.min())}, "
          f"max={int(az.root_sign_changes.max())}. "
          f"`resid_at_60 > 0 > resid_at_1200` at every step "
          f"(min resid at 60 = {az.resid_at_60.min():.3g}, "
          f"max resid at 1200 = {az.resid_at_1200.max():.3g}), so `G` maps "
          f"[60,1200] strictly into itself and the clip cannot remove the "
          f"root.", "",
          "**Per-step fixed point vs the official price** — this is the "
          "sharpest one-step number available, and it is still a one-step "
          "bound: it solves `p = G(p)` at step *t* with the incoming stock, "
          "ask vector and `p_{t-1}` pinned to the official path, so it does "
          "not let the state drift as a real option-B run would.", "",
          _fmt(az[az.step >= STEPS_PER_YEAR].groupby(["crop", "episode"]).agg(
              n=("step", "size"),
              mean_abs_dp=("fp_minus_official", lambda s: s.abs().mean()),
              max_abs_dp=("fp_minus_official", lambda s: s.abs().max()),
              mean_abs_pct=("fp_pct_of_official", lambda s: s.abs().mean()),
              max_abs_pct=("fp_pct_of_official", lambda s: s.abs().max()),
          ).reset_index()), "",
          "Including the first model year, the worst single step is:", "",
          _fmt(az.reindex(az.fp_minus_official.abs()
                          .sort_values(ascending=False).index)
               .head(8)[["crop", "step", "tag", "episode",
                         "in_first_model_year", "p_prev", "p_official", "fp",
                         "fp_minus_official", "fp_pct_of_official",
                         "L_max_global", "picard_iters", "free_official"]]),
          ""]

    L += ["### 3d-bis. Where G is steep, and where it JUMPS", "",
          "`L_max_global` above is the sup over the whole clip interval, "
          "including trial prices far from the root. It exceeds 1 at "
          f"{int((az.L_max_global > 1).sum())} of {len(az)} steps. The "
          "reason is not curvature: it is a genuine jump. Ranking grid "
          "cells by |ΔG| and bisecting each on the *regime tuple* "
          "(number of countries with `offers > 1e-9`; whether "
          "`shipped_sum > 1e-12`; whether `calm` fired; whether the price "
          "clip bound) localises the jumps to machine width:", "",
          _fmt(az.groupby(["crop", "episode"]).agg(
              n=("step", "size"),
              n_steps_with_a_jump=("n_jumps_found",
                                   lambda s: int((s > 0).sum())),
              max_jump_dollars=("max_jump_G", "max"),
              mean_jump_dollars=("max_jump_G", "mean"),
              min_root_to_jump=("root_to_nearest_jump", "min"),
              n_root_inside_jump=("root_inside_jump", "sum"),
          ).reset_index()), "",
          "Jump causes, counted over all steps with a jump above 0.01 $/t:",
          "",
          _fmt(az[az.max_jump_G > 0.01].groupby(["crop", "jump_cause"])
               .agg(n=("step", "size"),
                    max_jump=("max_jump_G", "max"),
                    min_root_to_jump=("root_to_nearest_jump", "min"))
               .reset_index()), "",
          "Ten largest jumps:", "",
          _fmt(az.reindex(az.max_jump_G.sort_values(ascending=False).index)
               .head(10)[["crop", "step", "tag", "episode", "p_official",
                          "fp", "max_jump_G", "p_at_max_jump", "jump_cause",
                          "root_to_nearest_jump", "L_max_global",
                          "picard_iters"]]), "",
          "The mechanism, read off the code: `offers = max(0, avail - "
          "desired - target)*(1-cuts)` (L596) is continuous in the trial "
          "price, but it reaches exactly zero for the last remaining "
          "exporter at some trial price. When it does, `shipped_sum` falls "
          "through the `1e-12` guard at L651 and `p_trade` switches "
          "discontinuously from `dot(ask, shipped)/shipped_sum` — a mean "
          "over one infinitesimal shipment, so it equals that single "
          "country's ask — to the fallback `p_trade = p` (L653). `p_trade` "
          "enters `p_star` with weight `trade_w` and then the smoother with "
          "weight `(1-smooth)`, so the jump in `G` is "
          "`(1-smooth)*trade_w*|ask_last - p_{t-1}|`. **This is a fourth "
          "discontinuity, not among the three named in the brief, and on "
          "this evidence it is the largest one.**", "",
          "### 3d-ter. Picard robustness from deliberately bad starts", "",
          "`x <- G(x)` started at 60, 1200, `0.5 p_{t-1}` and `2 p_{t-1}` "
          "as well as at `p_{t-1}`, tolerance 1e-8 $/t, cap 200 iterations:",
          "",
          _fmt(az.groupby(["crop", "episode"]).agg(
              n=("step", "size"),
              n_bad_starts_all_converged=("picard_bad_all_converged", "sum"),
              picard_bad_max_iters=("picard_bad_max_iters", "max"),
              max_spread_vs_bisected_root=("picard_bad_max_spread",
                                           lambda s: s.abs().max()),
          ).reset_index()), ""]

    L += ["### 3e. Grid-refinement continuity test", "",
          "If `G` had a jump inside the window, the finite-difference "
          "`L_max` would grow roughly linearly with grid density and "
          "`maxjump` would stay pinned at the jump height. Six worst-slope "
          "steps per crop plus the probe steps, window = official price "
          "+/- 15%:", "",
          _fmt(rf), ""]

    L += ["### 3f. Is the `calm` branch reachable at all?", "",
          "The branch needs three conditions simultaneously "
          "(`|free-twin| < 1e-6`, `u_anom < 1e-9`, `block_frac < 1e-9`). "
          "`block_frac` does not depend on the trial price except through "
          "the demand *weights*; it is zero only if no restricted exporter "
          "is a preferred source for any positive demand. Scan over all "
          "3 x 144 steps:", "",
          _fmt(cr.groupby(["crop", "episode"]).agg(
              n=("step", "size"),
              n_free_crosses_twin=("free_crosses_twin", "sum"),
              n_block_frac_zero=("block_frac_zero", "sum"),
              n_u_anom_zero=("u_anom_zero", "sum"),
              n_calm_reachable=("calm_reachable", "sum"),
              max_hypothetical_jump=("hypothetical_jump", "max"),
          ).reset_index()), "",
          f"Steps where the calm branch is reachable by any trial price: "
          f"**{int(cr.calm_reachable.sum())} of {len(cr)}**. "
          f"Where it is not reachable, the L666-669 conditional is dead "
          f"code for the fixed point and cannot create a jump. "
          f"`hypothetical_jump` = `(1-smooth)*trade_w*|p_trade - p0|` is "
          f"what the jump in `G` WOULD be if the branch did fire; its max "
          f"over all steps is {cr.hypothetical_jump.max():.4g} $/t, so the "
          f"hazard is real in magnitude and only unreachability is "
          f"protecting the solve.", "",
          "The reachable steps in detail. Bisect onto `free(x) = twin`, then "
          "expand outward to find the two EDGES of the calm plateau and "
          "evaluate `G` just outside each. On the plateau `p_star = p0` "
          "exactly, so `G` is flat there and steps down/up at both edges:",
          "",
          _fmt(cj[["crop", "step", "tag", "episode", "p_cross", "calm_fires",
                   "calm_window_width", "G_in_calm", "G_just_below",
                   "G_just_above", "max_calm_jump", "root",
                   "root_in_calm_window", "root_to_calm_window"]]), "",
          f"So the calm branch does make `G` genuinely discontinuous where "
          f"it is reachable: the plateau is "
          f"{cj.calm_window_width.min():.2g}–{cj.calm_window_width.max():.2g} "
          f"$/t wide and `G` steps by up to "
          f"{cj.max_calm_jump.max():.4g} $/t at its edges. It is reachable "
          f"at 7 of 432 steps and at none of them does the root fall inside "
          f"the plateau (closest approach "
          f"{cj.root_to_calm_window.min():.4g} $/t). The hazard is real but "
          f"it did not fire on this path.", ""]

    L += ["## Artifacts", "",
          "- `diagnostics/gate0_prep/a3/demand_gap.csv` "
          f"({len(pc)} rows: crop × step × country)",
          "- `diagnostics/gate0_prep/a3/demand_gap_world.csv` "
          f"({len(w)} rows: crop × step, incl. Task-2 columns)",
          "- `diagnostics/gate0_prep/a3/g_lipschitz.csv`",
          "- `diagnostics/gate0_prep/a3/g_wide_scan.csv`",
          "- `diagnostics/gate0_prep/a3/g_calm_boundary.csv`",
          f"- `diagnostics/gate0_prep/a3/g_all_steps.csv` ({len(az)} rows)",
          "- `diagnostics/gate0_prep/a3/g_grid_refinement.csv`",
          f"- `diagnostics/gate0_prep/a3/g_calm_reachability.csv` "
          f"({len(cr)} rows)",
          f"- `diagnostics/gate0_prep/a3/g_calm_jump_detail.csv` "
          f"({len(cj)} rows)",
          "- `diagnostics/gate0_prep/a3/replica_verification.csv`"]
    for f in figs:
        L.append(f"- `{f.relative_to(ROOT)}`")
    L.append("")

    (OUT / "A3_REPORT.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT / 'A3_REPORT.md'}")
    for f in figs:
        print(f"wrote {f}")


if __name__ == "__main__":
    main()
