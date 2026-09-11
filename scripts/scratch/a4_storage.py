#!/usr/bin/env python3
"""A4 — what the Gate 0 cover rule implies about intertemporal behaviour.

Read-only measurement. Nothing in ``sheaf/`` or ``scripts/`` is modified and
no new default is proposed; every parameter varied below is a labelled
diagnostic probe.

Structure
---------
Part 0  Reconstruct the per-step storage state (avail, desired, lean gap,
        target, cover) from the public result object and validate the
        reconstruction against ``res.offers`` to machine precision.
Part 1  Implied shadow value: on every (country, step) where the cover rule
        withholds grain while export demand is unfilled elsewhere, solve
        E_t[p_{t+1}] = (1+r) p_t + c for r, using the *realised* next-step
        price as a perfect-foresight proxy for the expectation.
Part 2  Descriptive scatter of offers against p_{t+1} - p_t, pooled and by
        episode, with a harvest-calendar control (step-of-year fixed
        effects, Frisch-Waugh-Lovell partialling).
Part 3  Exporter safety-floor leftover: model vs USDA PSD by country, where
        the floor actually sits, and three diagnostic probes separating
        (a) the cover rule level, (b) one world stu_target, (c) the offer
        equation selling the whole surplus above the target.

Outputs
-------
diagnostics/gate0_prep/a4/implied_carry.csv
diagnostics/gate0_prep/a4/implied_carry_summary.csv
diagnostics/gate0_prep/a4/offer_price_scatter_stats.csv
diagnostics/gate0_prep/a4/floor_country_table.csv
diagnostics/gate0_prep/a4/floor_probes.csv
diagnostics/gate0_prep/a4/reconstruction_check.csv
figures/scratch/a4/fig_a4_{crop}_offers_vs_dp.png
figures/scratch/a4/fig_a4_implied_r.png
figures/scratch/a4/fig_a4_floor.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.calibration import DATA  # noqa: E402
from sheaf.data_usda import load_psd_country  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    MAX_LEAN_STEPS,
    _simulate_window,
    prepare_crop_run,
    simulate_prep,
)
from sheaf.marketing_years import my_end_month  # noqa: E402
from sheaf.seasonal import (  # noqa: E402
    rolling_ahead_variable,
    steps_to_harvest_pulse,
)
from score_country_balance import _metrics, country_balance  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "a4"
FIGS = ROOT / "figures" / "scratch" / "a4"
CROPS = ("wheat", "maize", "rice")
START, END = 2006, 2011

# Withholding screen. MMT thresholds are deliberately loose: they only keep
# numerically-empty cells out of the ratio.
COVER_MIN_MMT = 0.05
UNMET_MIN_MMT = 0.05

# Illustrative reference values for the convenience-yield inversion. These
# are NOT model parameters and are NOT proposed as such.
R_REF_ANNUAL = 0.05
R_REF_STEP = R_REF_ANNUAL / STEPS_PER_YEAR
C_PHYS_STEP = 1.5  # $/t per half-month, ~ $3/t/month physical storage

# Episode windows are the ones scored in scripts/score_subannual_crop.py
# (L390-391), expressed as (year, month) inclusive bounds.
EPISODES = (
    ("2007/08", (2006, 6), (2008, 3)),
    ("2010/11", (2009, 6), (2011, 2)),
)


# ---------------------------------------------------------------- part 0
def reconstruct(prep, res) -> dict[str, np.ndarray]:
    """Recompute the storage state of ``_simulate_window`` (L577-596).

    Everything here is a re-derivation from public arrays; the returned
    ``offers_check`` is compared against ``res.offers`` by the caller.
    """
    p = prep.params
    H, H_seas = prep.H, prep.H_seas
    H_exp = p.foresight_phi * H + (1.0 - p.foresight_phi) * H_seas
    C_step = prep.C_flex + prep.C_ind

    lean_h = steps_to_harvest_pulse(
        H_exp, frac=p.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)
    lean_gap = np.maximum(0.0, C_ahead + C_step - H_ahead - H_exp)
    target = lean_gap + prep.safety[:, None]

    n, T = H.shape
    # Price in force when step t forms desired demand is the *previous*
    # realised price (p0 at t=0) — dynamic_crop L580.
    p_lag = np.concatenate([[prep.p0], res.price[:-1]])
    desired = (np.maximum(prep.C_flex * (p_lag / prep.p0) ** p.elast, 0.0)
               + prep.C_ind)

    stock_prev = np.concatenate([prep.stock0[:, None], res.stock[:, :-1]],
                                axis=1)
    avail = stock_prev + H
    surplus = np.maximum(0.0, avail - desired - target)
    offers_check = surplus * (1.0 - prep.cuts)
    # Grain the target actually keeps off the market this step.
    cover = np.minimum(target, np.maximum(0.0, avail - desired))
    return dict(H_exp=H_exp, lean_gap=lean_gap, target=target, avail=avail,
                desired=desired, surplus=surplus, cover=cover,
                offers_check=offers_check, stock_prev=stock_prev)


def step_labels(start_year: int, T: int):
    years = np.repeat(np.arange(start_year, start_year + T // STEPS_PER_YEAR),
                      STEPS_PER_YEAR)
    soy = np.tile(np.arange(STEPS_PER_YEAR), T // STEPS_PER_YEAR)
    months = soy // 2 + 1
    return years, months, soy


def episode_of(year: int, month: int) -> str:
    for name, (y0, m0), (y1, m1) in EPISODES:
        if (year, month) >= (y0, m0) and (year, month) <= (y1, m1):
            return name
    return "calm"


# ---------------------------------------------------------------- part 1
def implied_carry(crop: str, prep, res, st) -> pd.DataFrame:
    n, T = prep.H.shape
    years, months, soy = step_labels(prep.start_year, T)
    demand = res.purchase_demand
    received = res.received
    unmet_i = np.maximum(0.0, demand - received)
    unmet_tot = unmet_i.sum(axis=0)

    ask = res.ask                      # posted offer price used in step t
    price = res.price
    rows = []
    for t in range(T - 1):             # need t+1 to realise the return
        ep = episode_of(int(years[t]), int(months[t]))
        for i, c in enumerate(prep.countries):
            cov = float(st["cover"][i, t])
            if cov < COVER_MIN_MMT:
                continue
            unmet_other = float(unmet_tot[t] - unmet_i[i, t])
            if unmet_other < UNMET_MIN_MMT:
                continue
            q_t, q_n = float(ask[i, t]), float(ask[i, t + 1])
            p_t, p_n = float(price[t]), float(price[t + 1])
            # dynamic_crop L636 clips the ask to [0.45 p0, 2.8 p0]. Where
            # either end of the pair sits on a clip the return is an
            # artefact of the bound, not of the storage rule.
            lo, hi = 0.45 * prep.p0, 2.8 * prep.p0
            clipped = bool(min(abs(q_t - lo), abs(q_t - hi)) < 1e-6
                           or min(abs(q_n - lo), abs(q_n - hi)) < 1e-6)
            r_ask = q_n / q_t - 1.0
            r_world = p_n / p_t - 1.0
            r_ask_c = (q_n - C_PHYS_STEP) / q_t - 1.0
            cy = (1.0 + R_REF_STEP) * q_t + C_PHYS_STEP - q_n
            rows.append(dict(
                crop=crop, country=c, t=t, year=int(years[t]),
                month=int(months[t]), step_of_year=int(soy[t]), episode=ep,
                cut=float(prep.cuts[i, t]),
                cover_mmt=cov,
                target_mmt=float(st["target"][i, t]),
                lean_gap_mmt=float(st["lean_gap"][i, t]),
                safety_mmt=float(prep.safety[i]),
                surplus_mmt=float(st["surplus"][i, t]),
                offers_mmt=float(res.offers[i, t]),
                unmet_other_mmt=unmet_other,
                ask_t=q_t, ask_next=q_n, p_t=p_t, p_next=p_n,
                ask_at_clip=clipped,
                implied_r_step_ask=r_ask,
                implied_r_step_ask_carry=r_ask_c,
                implied_r_step_world=r_world,
                implied_r_annual_ask=(1.0 + r_ask) ** STEPS_PER_YEAR - 1.0,
                convenience_yield_usd_t=cy,
                convenience_yield_frac=cy / q_t,
            ))
    return pd.DataFrame(rows)


def carry_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (crop, country), g in df.groupby(["crop", "country"], sort=False):
        r = g.implied_r_step_ask.to_numpy(float)
        out.append(dict(
            crop=crop, country=country, n_withhold_steps=int(len(g)),
            n_no_cut=int((g.cut <= 0).sum()),
            n_ask_at_clip=int(g.ask_at_clip.sum()),
            median_r_step=float(np.median(r)),
            p10_r_step=float(np.percentile(r, 10)),
            p90_r_step=float(np.percentile(r, 90)),
            min_r_step=float(r.min()), max_r_step=float(r.max()),
            share_r_negative=float((r < 0).mean()),
            share_r_below_carry=float(
                (g.implied_r_step_ask_carry < 0).mean()),
            median_cy_usd_t=float(g.convenience_yield_usd_t.median()),
            median_cy_frac=float(g.convenience_yield_frac.median()),
            mean_cover_mmt=float(g.cover_mmt.mean()),
        ))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- part 2
def _resid_on(x: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Residual of x on group fixed effects (FWL partialling)."""
    x = np.asarray(x, float)
    out = x.copy()
    for g in np.unique(groups):
        m = groups == g
        out[m] = x[m] - x[m].mean()
    return out


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 6 or a[m].std() < 1e-12 or b[m].std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def scatter_stats(crop: str, prep, res) -> tuple[pd.DataFrame, pd.DataFrame]:
    n, T = prep.H.shape
    years, months, soy = step_labels(prep.start_year, T)
    dp = np.diff(res.price)                       # p_{t+1} - p_t, len T-1
    recs = []
    for t in range(T - 1):
        ep = episode_of(int(years[t]), int(months[t]))
        for i, c in enumerate(prep.countries):
            recs.append(dict(country=c, t=t, soy=int(soy[t]), episode=ep,
                             offers=float(res.offers[i, t]), dp=float(dp[t])))
    panel = pd.DataFrame(recs)
    panel["cs"] = panel.country + "|" + panel.soy.astype(str)

    rows = []
    for label, sub in [("pooled", panel)] + [
            (e, panel[panel.episode == e])
            for e in ("2007/08", "2010/11", "calm")]:
        if len(sub) < 12:
            continue
        o_r = _resid_on(sub.offers.to_numpy(float), sub.cs.to_numpy())
        d_r = _resid_on(sub.dp.to_numpy(float), sub.soy.to_numpy())
        # World-summed version on the same control.
        w = sub.groupby("t", as_index=False).agg(
            offers=("offers", "sum"), dp=("dp", "first"),
            soy=("soy", "first"))
        wo_r = _resid_on(w.offers.to_numpy(float), w.soy.to_numpy())
        wd_r = _resid_on(w.dp.to_numpy(float), w.soy.to_numpy())
        rows.append(dict(
            crop=crop, subset=label, n_country_steps=int(len(sub)),
            corr_raw_country=_corr(sub.offers, sub.dp),
            corr_seasadj_country=_corr(o_r, d_r),
            n_world_steps=int(len(w)),
            corr_raw_world=_corr(w.offers, w.dp),
            corr_seasadj_world=_corr(wo_r, wd_r),
        ))
    return pd.DataFrame(rows), panel


def fig_scatter(crop: str, panel: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.8))
    colours = {"calm": "#9bb7d4", "2007/08": "#c0392b", "2010/11": "#e67e22"}
    ax = axes[0]
    for ep, g in panel.groupby("episode"):
        ax.scatter(g.offers, g.dp, s=6, alpha=0.45,
                   color=colours.get(ep, "0.5"), label=ep)
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_xlabel("offers $O_{i,t}$ (MMT)")
    ax.set_ylabel(r"$p_{t+1}-p_t$  (\$/t)")
    ax.set_title(f"{crop.capitalize()}: country-step, raw")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    o_r = _resid_on(panel.offers.to_numpy(float), panel.cs.to_numpy())
    d_r = _resid_on(panel.dp.to_numpy(float), panel.soy.to_numpy())
    for ep in panel.episode.unique():
        m = (panel.episode == ep).to_numpy()
        ax.scatter(o_r[m], d_r[m], s=6, alpha=0.45,
                   color=colours.get(ep, "0.5"), label=ep)
    ax.axhline(0, color="0.6", lw=0.6)
    ax.axvline(0, color="0.6", lw=0.6)
    ax.set_xlabel("offers, country x step-of-year FE removed")
    ax.set_ylabel(r"$\Delta p$, step-of-year FE removed")
    ax.set_title("harvest-calendar control")

    ax = axes[2]
    w = panel.groupby("t", as_index=False).agg(
        offers=("offers", "sum"), dp=("dp", "first"),
        soy=("soy", "first"), episode=("episode", "first"))
    for ep, g in w.groupby("episode"):
        ax.scatter(g.offers, g.dp, s=18, alpha=0.8,
                   color=colours.get(ep, "0.5"), label=ep)
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_xlabel("world offers (MMT)")
    ax.set_ylabel(r"$p_{t+1}-p_t$  (\$/t)")
    ax.set_title("world-summed, raw")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------- part 3
def floor_table(crop: str, prep, res, st) -> pd.DataFrame:
    """Model MY-end stocks vs PSD, next to the target the rule imposes."""
    bal = country_balance(res, crop)
    idx = {c: i for i, c in enumerate(prep.countries)}
    extra = []
    for _, row in bal.iterrows():
        i = idx[row.country]
        y, my = int(row.year), int(row.my_month)
        t = (y - prep.start_year) * STEPS_PER_YEAR + (my - 1) * 2 + 1
        c_ann = float(prep.C_ann[i])
        s_i = float(prep.safety[i])
        tgt = float(st["target"][i, t])
        stk = float(res.stock[i, t])
        extra.append(dict(
            safety_mmt=s_i, target_mmt=tgt, c_ann_mmt=c_ann,
            model_stu=stk / c_ann if c_ann > 1e-9 else np.nan,
            psd_stu=row.psd_stock / row.psd_cons if row.psd_cons > 0.5
            else np.nan,
            stock_over_safety=stk / s_i if s_i > 1e-9 else np.nan,
            stock_over_target=stk / tgt if tgt > 1e-9 else np.nan,
            stock_minus_target_over_cann=(
                (stk - tgt) / c_ann if c_ann > 1e-9 else np.nan),
        ))
    return pd.concat([bal.reset_index(drop=True),
                      pd.DataFrame(extra)], axis=1)


def psd_means(crop: str, countries: list[str],
              years: list[int]) -> pd.DataFrame:
    """Mean 2006-11 PSD production / domestic use / exports / stocks per node.

    RestOfWorld is world minus named nodes, exactly as ``_psd_annual``
    (dynamic_crop L232-255) builds the residual node.
    """
    psd = load_psd_country(crop)
    named = [c for c in countries if c != "RestOfWorld"]
    rows = []
    for y in years:
        sub = psd[psd.year == y]
        tot = {k: float(sub[k].sum()) for k in
               ("production", "consumption", "exports", "ending_stocks")}
        acc = dict.fromkeys(tot, 0.0)
        for c in named:
            hit = sub[sub.country == c]
            rec = {k: (float(hit[k].iloc[0]) if len(hit) else 0.0)
                   for k in tot}
            for k in tot:
                acc[k] += rec[k]
            rows.append(dict(country=c, year=y, **rec))
        if "RestOfWorld" in countries:
            rows.append(dict(country="RestOfWorld", year=y,
                             **{k: max(tot[k] - acc[k], 0.0) for k in tot}))
    df = pd.DataFrame(rows).groupby("country", as_index=False).mean(
        numeric_only=True).drop(columns=["year"])
    df["total_use"] = df.consumption + df.exports
    df["export_share"] = np.where(df.total_use > 1e-9,
                                  df.exports / df.total_use, 0.0)
    df["psd_stu_dom"] = np.where(df.consumption > 1e-9,
                                 df.ending_stocks / df.consumption, np.nan)
    df["psd_stu_totuse"] = np.where(df.total_use > 1e-9,
                                    df.ending_stocks / df.total_use, np.nan)
    return df


def rebased_prep(crop: str, base_prep, new_safety: np.ndarray):
    """Copy of the prep with a different safety vector, twin rebuilt.

    The calm twin is re-derived with the same safety (mirroring
    dynamic_crop L802-806) so the scarcity reference stays path-matched.
    ``stock0`` is *not* re-seeded, which makes every lift below a lower
    bound on the effect. Diagnostic probe only.
    """
    from dataclasses import replace as dc_replace
    p = base_prep.params
    H_for_twin = (base_prep.H if p.twin_harvest == "realized"
                  else base_prep.H_seas)
    _, _, _, _, free_twin, unmet_twin, _, _, _, _, _ = _simulate_window(
        H_for_twin, base_prep.C_flex_twin, base_prep.C_ind_twin,
        np.zeros_like(H_for_twin), base_prep.stock0.copy(), new_safety,
        base_prep.p0, base_prep.C_ann, base_prep.A, base_prep.S, p,
        free_twin=None, H_seasonal=base_prep.H_seas)
    return dc_replace(base_prep, safety=new_safety, free_twin=free_twin,
                      unmet_twin=unmet_twin)


def probe_grid(crop: str, base_prep, base_res) -> pd.DataFrame:
    """Diagnostic probes only. None of these is a proposed default."""
    p = base_prep.params
    years = list(range(START, END + 1))
    pm = psd_means(crop, base_prep.countries, years).set_index("country")
    order = [pm.loc[c] if c in pm.index else None for c in base_prep.countries]
    total_use = np.array([r.total_use if r is not None else 0.0
                          for r in order], float)
    stu_dom = np.array([r.psd_stu_dom if r is not None else np.nan
                        for r in order], float)
    # (b1) same single world stu_target, but multiplying total use
    # (domestic + exports) instead of domestic use alone.
    safety_totuse = p.stu_target * np.maximum(total_use, base_prep.C_ann)
    # (b2) the S3 shape: country-specific ratios taken straight from PSD.
    stu_country = np.where(np.isfinite(stu_dom), stu_dom, p.stu_target)
    safety_country = stu_country * base_prep.C_ann

    probes = [
        ("baseline", {}, None, None),
        ("stu_target+0.10 (max_stu held)",
         dict(stu_target=p.stu_target + 0.10), None, None),
        ("stu_target+0.10 & max_stu+0.10",
         dict(stu_target=p.stu_target + 0.10,
              max_stu=p.max_stu + 0.10), None, None),
        ("stu_target x2 & max_stu x2",
         dict(stu_target=2 * p.stu_target, max_stu=2 * p.max_stu),
         None, None),
        ("offer damp 30% (uniform synthetic cut)", {}, 0.30, None),
        ("REBASE: s_i = stu_target x (dom use + exports)", {}, None,
         safety_totuse),
        ("S3 shape: s_i = PSD country STU x dom use", {}, None,
         safety_country),
    ]
    rows = []
    for label, over, damp, safety in probes:
        if over:
            prep = prepare_crop_run(
                crop, start_year=START, end_year=END, use_amis=True,
                use_shocks=True, use_demand=False, **over)
            res = simulate_prep(prep)
        elif damp is not None:
            prep = base_prep
            cuts = np.maximum(base_prep.cuts, damp)
            res = simulate_prep(prep, cuts=cuts)
        elif safety is not None:
            prep = rebased_prep(crop, base_prep, safety)
            res = simulate_prep(prep)
        else:
            prep, res = base_prep, base_res
        bal = country_balance(res, crop)
        met = _metrics(bal)
        big = bal[bal.psd_stock > 1.0]
        rows.append(dict(
            crop=crop, probe=label, is_probe_not_default=True,
            median_stock_ratio=met["median_stock_ratio"],
            n_country_years=met["n_country_years"],
            **{f"ratio_{c}": float(
                big[big.country == c].stock_ratio.median())
               if len(big[big.country == c]) else np.nan
               for c in FLOOR_WATCH.get(crop, ())},
            price_max=float(res.price.max()),
            price_mean=float(res.price.mean()),
            world_stock_mean=float(res.stock.sum(axis=0).mean()),
        ))
    return pd.DataFrame(rows)


def binding_table(crop: str, prep, res, st) -> pd.DataFrame:
    """Does the cover target actually bind, over all 144 steps?

    Three mutually exclusive regimes per country-step:
      offering  : avail - desired > T, so the rule sells the residual
      at_target : stock lands within 1% of T
      short     : stock below T, the rebuild lambda is the only way back
    """
    stock, target = res.stock, st["target"]
    n, T = stock.shape
    rel = np.where(target > 1e-9, stock / np.maximum(target, 1e-9), np.nan)
    offering = res.offers > 1e-6
    rows = []
    for i, c in enumerate(prep.countries):
        r = rel[i]
        rows.append(dict(
            crop=crop, country=c,
            share_offering=float(offering[i].mean()),
            share_at_or_above_target=float(np.nanmean(r >= 0.99)),
            share_short_of_target=float(np.nanmean(r < 0.99)),
            median_stock_over_target=float(np.nanmedian(r)),
            p90_stock_over_target=float(np.nanpercentile(r, 90)),
            median_target_mmt=float(np.median(target[i])),
            safety_mmt=float(prep.safety[i]),
            median_lean_over_safety=float(
                np.median(st["lean_gap"][i]) / max(prep.safety[i], 1e-9)),
        ))
    return pd.DataFrame(rows)


def floor_decomposition(crop: str, prep, floor_df: pd.DataFrame
                        ) -> pd.DataFrame:
    r"""Split log(model / PSD) at the scored month into additive pieces.

    log(S/S^{PSD}) = log(S/T)                      "never reaches the target"
                   + log(T/s)                      "lean term at that month"
                   + [log(sigma) - log(stu^{PSD,totuse})]  "target level"
                   + log(1 - export share)         "base is domestic use only"

    The last two sum to log(s / S^{PSD}) exactly, because
    s = sigma C^{ann} and stu^{PSD,dom} = stu^{PSD,totuse}/(1-export share).
    """
    p = prep.params
    pm = psd_means(crop, prep.countries,
                   list(range(START, END + 1))).set_index("country")
    g = floor_df[(floor_df.crop == crop) & (floor_df.psd_stock > 1.0)].copy()
    g = g[(g.model_stock > 0) & (g.target_mmt > 0) & (g.safety_mmt > 0)]
    rows = []
    for c, sub in g.groupby("country"):
        if c not in pm.index or not np.isfinite(pm.loc[c, "psd_stu_totuse"]):
            continue
        es = float(pm.loc[c, "export_share"])
        stu_tu = float(pm.loc[c, "psd_stu_totuse"])
        rows.append(dict(
            crop=crop, country=c,
            log_total=float(np.log(sub.model_stock / sub.psd_stock).mean()),
            log_below_target=float(
                np.log(sub.model_stock / sub.target_mmt).mean()),
            log_lean_term=float(
                np.log(sub.target_mmt / sub.safety_mmt).mean()),
            log_target_level=float(np.log(p.stu_target) - np.log(stu_tu)),
            log_domestic_base=float(np.log(max(1.0 - es, 1e-6))),
            export_share=es, psd_stu_totuse=stu_tu,
            psd_stu_dom=float(pm.loc[c, "psd_stu_dom"]),
            model_over_psd=float((sub.model_stock / sub.psd_stock).mean()),
        ))
    out = pd.DataFrame(rows)
    if len(out):
        out["log_recon"] = (out.log_below_target + out.log_lean_term
                            + out.log_target_level + out.log_domestic_base)
        out["recon_resid"] = out.log_total - out.log_recon
    return out.sort_values("log_total") if len(out) else out


FLOOR_WATCH = {
    "wheat": ("USA", "Canada", "Australia", "Russia", "EU", "China", "India"),
    "maize": ("USA", "Argentina", "Brazil", "China", "EU"),
    "rice": ("India", "Vietnam", "Thailand", "China", "Indonesia"),
}


# ---------------------------------------------------------------- driver
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    carry, summ, scat, floors, probes, checks = [], [], [], [], [], []
    binds: list[pd.DataFrame] = []
    preps = {}
    for crop in CROPS:
        print(f"[a4] {crop}: official leg (amis+shocks, mean flex)…")
        prep = prepare_crop_run(crop, start_year=START, end_year=END,
                                use_amis=True, use_shocks=True,
                                use_demand=False)
        res = simulate_prep(prep)
        preps[crop] = prep
        st = reconstruct(prep, res)
        err = float(np.max(np.abs(st["offers_check"] - res.offers)))
        checks.append(dict(crop=crop, max_abs_offer_recon_err_mmt=err,
                           n_countries=len(prep.countries),
                           n_steps=int(prep.H.shape[1]),
                           stu_target=prep.params.stu_target,
                           max_stu=prep.params.max_stu,
                           p0=prep.p0))
        print(f"      reconstruction max|Δoffers| = {err:.3e} MMT")

        df = implied_carry(crop, prep, res, st)
        carry.append(df)
        summ.append(carry_summary(df))
        print(f"      withholding country-steps: {len(df)}; "
              f"median implied r/step = "
              f"{df.implied_r_step_ask.median():+.4f}")

        s, panel = scatter_stats(crop, prep, res)
        scat.append(s)
        fig_scatter(crop, panel, FIGS / f"fig_a4_{crop}_offers_vs_dp.png")

        floors.append(floor_table(crop, prep, res, st))
        binds.append(binding_table(crop, prep, res, st))
        probes.append(probe_grid(crop, prep, res))

    carry_df = pd.concat(carry, ignore_index=True)
    carry_df.to_csv(OUT / "implied_carry.csv", index=False)
    pd.concat(summ, ignore_index=True).to_csv(
        OUT / "implied_carry_summary.csv", index=False)
    pd.concat(scat, ignore_index=True).to_csv(
        OUT / "offer_price_scatter_stats.csv", index=False)
    floor_df = pd.concat(floors, ignore_index=True)
    floor_df.to_csv(OUT / "floor_country_table.csv", index=False)
    pd.concat([floor_decomposition(c, p, floor_df)
               for c, p in preps.items()], ignore_index=True).to_csv(
        OUT / "floor_decomposition.csv", index=False)
    pd.concat(binds, ignore_index=True).to_csv(
        OUT / "target_binding.csv", index=False)
    pd.concat(probes, ignore_index=True).to_csv(
        OUT / "floor_probes.csv", index=False)
    pd.DataFrame(checks).to_csv(OUT / "reconstruction_check.csv", index=False)

    # ---- figures --------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.6), sharey=True)
    for ax, crop in zip(axes, CROPS):
        g = carry_df[carry_df.crop == crop]
        ax.hist(np.clip(g.implied_r_step_ask, -0.25, 0.25), bins=60,
                color="#1f4e79")
        ax.axvline(0, color="0.4", lw=0.8)
        ax.axvline(R_REF_STEP, color="#c0392b", lw=1.0,
                   label=f"r=5%/yr ({R_REF_STEP:.4f}/step)")
        ax.set_title(f"{crop.capitalize()} implied r per step")
        ax.set_xlabel("implied r (clipped to ±0.25)")
        ax.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("withholding country-steps")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_a4_implied_r.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    for ax, crop in zip(axes, CROPS):
        g = (floor_df[(floor_df.crop == crop) & (floor_df.psd_stock > 1.0)]
             .groupby("country", as_index=False)
             .agg(model_stu=("model_stu", "median"),
                  psd_stu=("psd_stu", "median"),
                  ratio=("stock_ratio", "median")))
        g = g.sort_values("psd_stu")
        y = np.arange(len(g))
        ax.barh(y + 0.18, g.psd_stu, 0.35, color="#1f4e79", label="PSD STU")
        ax.barh(y - 0.18, g.model_stu, 0.35, color="#e67e22",
                label="model STU")
        ax.set_yticks(y, g.country, fontsize=7)
        ax.axvline(0.20 if crop == "wheat" else
                   (0.16 if crop == "maize" else 0.18),
                   color="#c0392b", lw=1.0, ls="--",
                   label="world stu_target")
        ax.set_xlabel("stock / annual use (median 2006-11)")
        ax.set_title(crop.capitalize())
        ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_a4_floor.png", dpi=140)
    plt.close(fig)

    print(f"[a4] wrote {OUT} and {FIGS}")


if __name__ == "__main__":
    main()
