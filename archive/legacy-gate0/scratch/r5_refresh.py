"""R5 red-team, resumed: re-validate every inherited measurement against the
CURRENT Gate 0 baseline, and build the Agrimate-5.4-comparable annual
attribution table.

The baseline moved twice after the first R5 pass (2026-09-10 14:3x):
  d4830c8  bound the scarcity ratio in the asymmetric negative-F regime
  929cec4  restore CES origin competition (`_ask_reweight_src`)
so every SHEAF number in the inherited CSVs is re-derived here from live
runs of `sheaf.dynamic_crop` rather than read off disk.

Outputs (all under diagnostics/redteam/r5/):
  current_scores.csv          live corr / hike per crop per leg + disk drift
  node_coverage.csv           18-node geography, RoW share, vs 28 regions
  hike_bias_panel_v2.csv      over-amplification panel, live
  hike_bias_summary_v2.csv    sign test / geometric mean amplification
  sheaf_annual_uplift.csv     SHEAF annual mean price vs p0 baseline, by leg
  agrimate_vs_sheaf_54.csv    Agrimate 5.4 (published + digitised) vs SHEAF
  ablation_grid_r5.csv        channel ablations re-run at current code
  sheaf_quantity_v2.csv       quantity-side signs/levels off current CSVs

Read-only w.r.t. sheaf/ and scripts/*.py (imports only).
"""
from __future__ import annotations

import sys
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly, load_psd_country  # noqa: E402
from sheaf.data_faostat import SHEAF_NODE_MAP  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    result_to_monthly,
    run_crop_dynamics,
)

DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"

CROPS = ("wheat", "maize", "rice")
START, END = 2006, 2011
WINDOWS = (("2007/08", 2006, 6, 2008, 3), ("2010/11", 2009, 6, 2011, 2))

LEGS = {
    # Official P1 matched split, byte-for-byte scripts/score_subannual_crop.py
    "full":   dict(use_amis=True,  use_shocks=True,  use_demand=False),
    "shocks": dict(use_amis=False, use_shocks=True,  use_demand=False),
    "demand": dict(use_amis=False, use_shocks=False, use_demand=True),
    "tau":    dict(use_amis=True,  use_shocks=False, use_demand=False,
                   use_industrial=False),
    # Unperturbed reference: nothing on. Should be flat at p0 (twin identity).
    "none":   dict(use_amis=False, use_shocks=False, use_demand=False,
                   use_industrial=False),
}


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 6 else float("nan")


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
    """Byte-for-byte scripts/score_subannual_crop.py::_hike."""
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm, yy = mm + 12, yy - 1
            if mm > 12:
                mm, yy = mm - 12, yy + 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                vals.append(float(hit.iloc[0]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


# --------------------------------------------------------------------------
# 1. live scores, all legs, all crops; drift vs the on-disk score CSVs
# --------------------------------------------------------------------------
def live_runs():
    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= START) & (obs.year <= END)]
    out = {}
    for crop in CROPS:
        o = obs[["year", "month", crop]].rename(columns={crop: "obs_price"})
        legs = {}
        for name, kw in LEGS.items():
            res = run_crop_dynamics(crop, start_year=START, end_year=END, **kw)
            m = result_to_monthly(res)
            legs[name] = m.merge(o, on=["year", "month"], how="left")
        out[crop] = legs
    return out


def scores(runs) -> pd.DataFrame:
    rows = []
    for crop, legs in runs.items():
        disk = pd.read_csv(DIAG / f"gate0_{crop}_score.csv")
        for name, df in legs.items():
            rec = dict(crop=crop, leg=name, corr_live=_corr(df.model_price,
                                                            df.obs_price))
            for label, y0, m0, y1, m1 in WINDOWS:
                rec[f"hike_{label}_live"] = _hike(df, "model_price",
                                                  y0, m0, y1, m1)
                rec[f"obs_hike_{label}"] = _hike(df, "obs_price",
                                                 y0, m0, y1, m1)
            d = disk[disk.leg == name]
            if len(d):
                rec["corr_disk"] = _corr(d.model_price, d.obs_price)
                for label, y0, m0, y1, m1 in WINDOWS:
                    rec[f"hike_{label}_disk"] = _hike(d, "model_price",
                                                      y0, m0, y1, m1)
                rec["max_abs_price_drift"] = float(np.max(np.abs(
                    d.sort_values(["year", "month"]).model_price.values
                    - df.sort_values(["year", "month"]).model_price.values)))
            rec["mean_price"] = float(df.model_price.mean())
            rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 2. node geography: 18 nodes vs Agrimate's 28 regions
# --------------------------------------------------------------------------
def node_coverage() -> pd.DataFrame:
    named = sorted(SHEAF_NODE_MAP)
    rows = []
    for crop in CROPS:
        psd = load_psd_country(crop)
        psd = psd[psd.year.between(START, END)]
        # SHEAF's node map keys are node names; PSD is by USDA country label.
        # Use the Gate 0 country balance table, which is the model's own
        # aggregation, for the authoritative RoW share.
        cb = pd.read_csv(DIAG / f"gate0_{crop}_country_balance.csv")
        tot_c = cb.psd_cons.sum()
        row_c = cb[cb.country == "RestOfWorld"].psd_cons.sum()
        tot_s = cb.psd_stock.sum()
        row_s = cb[cb.country == "RestOfWorld"].psd_stock.sum()
        world_p = float(psd.production.sum())
        rows.append(dict(
            crop=crop, n_nodes=18, n_named=len(named), n_agrimate_regions=28,
            row_share_psd_consumption=float(row_c / tot_c),
            row_share_psd_stocks=float(row_s / tot_s),
            world_psd_production_mmt=world_p / 6.0,
        ))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 3. over-amplification panel (live)
# --------------------------------------------------------------------------
def bias_panel(runs) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for crop, legs in runs.items():
        full = legs["full"]
        for label, y0, m0, y1, m1 in WINDOWS:
            mh = _hike(full, "model_price", y0, m0, y1, m1)
            oh = _hike(full, "obs_price", y0, m0, y1, m1)
            rows.append(dict(
                crop=crop, window=label, model_hike=mh, obs_hike=oh,
                ratio=mh / oh, log_ratio=float(np.log(mh / oh)),
                pct_error=100.0 * (mh / oh - 1.0),
                corr_full=_corr(full.model_price, full.obs_price)))
    df = pd.DataFrame(rows)
    lr = df.log_ratio.values
    n_pos, n = int((lr > 0).sum()), len(lr)
    p_one = sum(comb(n, k) for k in range(n_pos, n + 1)) / 2 ** n
    summary = dict(
        n_cells=n, n_overshoot=n_pos,
        mean_log_ratio=float(lr.mean()),
        geometric_mean_amplification=float(np.exp(lr.mean())),
        median_pct_error=float(np.median(df.pct_error)),
        sd_log_ratio=float(lr.std(ddof=1)),
        t_stat=float(lr.mean() / (lr.std(ddof=1) / np.sqrt(n))),
        sign_test_p_one_sided=float(p_one),
        wheat_mean_pct_error=float(df[df.crop == "wheat"].pct_error.mean()),
        maize_mean_pct_error=float(df[df.crop == "maize"].pct_error.mean()),
        rice_mean_pct_error=float(df[df.crop == "rice"].pct_error.mean()),
    )
    return df, pd.DataFrame([summary])


# --------------------------------------------------------------------------
# 4. SHEAF annual uplift vs its own unperturbed baseline (Agrimate 5.4 design)
# --------------------------------------------------------------------------
def annual_uplift(runs) -> pd.DataFrame:
    rows = []
    for crop, legs in runs.items():
        base = legs["none"]
        p0 = float(base.model_price.iloc[0])
        flat = float(np.max(np.abs(base.model_price - p0)) / p0)
        for y in range(START, END + 1):
            rec = dict(crop=crop, year=y, p0=p0, baseline_flatness=flat)
            for name in ("none", "shocks", "tau", "demand", "full"):
                mp = float(legs[name][legs[name].year == y].model_price.mean())
                rec[f"{name}_usd"] = mp
                rec[f"{name}_pct_vs_base"] = 100.0 * (mp / p0 - 1.0)
            rec["restriction_increment_pp"] = (rec["full_pct_vs_base"]
                                               - rec["shocks_pct_vs_base"])
            ob = float(legs["full"][legs["full"].year == y].obs_price.mean())
            rec["obs_usd"] = ob
            rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. channel ablations, re-run at current code
# --------------------------------------------------------------------------
ABLATIONS = (
    ("baseline", {}),
    ("trade_w=1.0", dict(trade_w=1.0)),
    ("trade_w=0.0", dict(trade_w=0.0)),
    ("ask_rival=0.0", dict(ask_rival=0.0)),
    ("block_kappa=0.0", dict(block_kappa=0.0)),
    ("unmet_kappa=0.0", dict(unmet_kappa=0.0)),
    ("ask_comp_elast=0.0", dict(ask_comp_elast=0.0)),
    ("foresight_phi=0.0", dict(foresight_phi=0.0)),
    ("foresight_phi=1.0", dict(foresight_phi=1.0)),
    ("ask_alpha=0.0", dict(ask_alpha=0.0)),
    ("rebuild_lambda=0.0", dict(rebuild_lambda=0.0)),
)


def ablations() -> pd.DataFrame:
    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= START) & (obs.year <= END)]
    rows = []
    for crop in CROPS:
        o = obs[["year", "month", crop]].rename(columns={crop: "obs_price"})
        for label, ov in ABLATIONS:
            res = run_crop_dynamics(
                crop, start_year=START, end_year=END, use_amis=True,
                use_shocks=True, use_demand=False, **ov)
            m = result_to_monthly(res).merge(o, on=["year", "month"],
                                             how="left")
            rec = dict(crop=crop, ablation=label,
                       corr=_corr(m.model_price, m.obs_price))
            for label2, y0, m0, y1, m1 in WINDOWS:
                h = _hike(m, "model_price", y0, m0, y1, m1)
                oh = _hike(m, "obs_price", y0, m0, y1, m1)
                rec[f"hike_{label2}"] = h
                rec[f"err_{label2}_pct"] = 100.0 * (h / oh - 1.0)
            rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 6. quantity side off the CURRENT gate0 artifacts
# --------------------------------------------------------------------------
def quantity_side() -> tuple[pd.DataFrame, pd.DataFrame]:
    srows, lev = [], []
    for crop in CROPS:
        st = pd.read_csv(DIAG / f"gate0_{crop}_stocks.csv").sort_values("year")
        cons = pd.read_csv(DIAG / f"gate0_{crop}_consumption.csv"
                           ).sort_values("year")
        cb = pd.read_csv(DIAG / f"gate0_{crop}_country_balance.csv")
        base = float(cons.psd_cons.mean())
        dm = st.model_my_end_stock.diff()
        dp = st.psd_ending_stocks.diff()
        for y, a, b in zip(st.year[1:], dm[1:], dp[1:]):
            srows.append(dict(crop=crop, panel="stock_change", year=int(y),
                              psd_pct=100 * b / base, model_pct=100 * a / base,
                              sign_agree=int(np.sign(a) == np.sign(b))))
        for _, r in cons.dropna(subset=["model_dcons"]).iterrows():
            srows.append(dict(crop=crop, panel="consumption_change",
                              year=int(r.year),
                              psd_pct=100 * r.psd_dcons / base,
                              model_pct=100 * r.model_dcons / base,
                              sign_agree=int(np.sign(r.model_dcons) ==
                                             np.sign(r.psd_dcons))))
        big = cb[cb.psd_stock > 1]
        lev.append(dict(
            crop=crop,
            world_my_end_stock_ratio=float(
                (st.model_my_end_stock / st.psd_ending_stocks).mean()),
            world_my_end_stock_corr=float(np.corrcoef(
                st.model_my_end_stock, st.psd_ending_stocks)[0, 1]),
            world_dec_stock_ratio=float(
                (st.model_ending_stock / st.psd_ending_stocks).mean()),
            world_cons_ratio=float(cons.cons_ratio.mean()),
            world_cons_corr=float(np.corrcoef(cons.model_cons,
                                              cons.psd_cons)[0, 1]),
            country_stock_ratio_median=float(big.stock_ratio.median()),
            country_dstock_sign_agree=int(
                (np.sign(cb.model_dstock) == np.sign(cb.psd_dstock)).sum()),
            country_dstock_n=int(cb.dropna(subset=["psd_dstock"]).shape[0]),
        ))
    return pd.DataFrame(srows), pd.DataFrame(lev)


# --------------------------------------------------------------------------
# 7. Agrimate 5.4 published vs digitised vs SHEAF
# --------------------------------------------------------------------------
# Kuhla et al. 2025 §5.4 (Ecological Economics 231:108546), read from
# agrimate/Kuhla_2025_Agrimate.txt L764-782, with Fig. 9's caption fixing
# which bar each number is: blue = production anomalies vs baseline,
# orange = full model vs baseline, black = full minus production anomalies.
AGRIMATE_PUBLISHED = [
    # year, prod-anomaly uplift %, full-model uplift %, quoted absolutes
    dict(year=2007, prod_pct=13.2, full_pct=16.2,
         prod_usd=13.7, full_usd=16.7,
         quote="prices were driven much stronger by these production failures "
               "+13.7 US$/t (+13.2%) compared to the baseline scenario than "
               "by the export restrictions +16.7 US$/t (+16.2%)"),
    dict(year=2008, prod_pct=np.nan, full_pct=22.5,
         prod_usd=np.nan, full_usd=23.3,
         quote="These raised the world market price in 2008 to a similar "
               "extent as the production failures ... Combined both drivers "
               "increased the price by +23.3 US$/t (+22.5%)"),
    dict(year=2010, prod_pct=np.nan, full_pct=5.6, prod_usd=np.nan,
         full_usd=np.nan,
         quote="mainly driven by the export restrictions raising the price by "
               "+5.6% and +12.3% in 2010 and 2011"),
    dict(year=2011, prod_pct=np.nan, full_pct=12.3, prod_usd=np.nan,
         full_usd=np.nan, quote="(same sentence)"),
]


def agrimate_vs_sheaf(up: pd.DataFrame) -> pd.DataFrame:
    dig = pd.read_csv(OUT / "agrimate_annual_uplift.csv")
    pub = pd.DataFrame(AGRIMATE_PUBLISHED)
    rows = []
    for _, p in pub.iterrows():
        y = int(p.year)
        d = dig[dig.year == y].iloc[0]
        rec = dict(
            year=y,
            agri_pub_prod_pct=p.prod_pct, agri_pub_full_pct=p.full_pct,
            agri_dig_prod_pct=100 * (d.prod_over_baseline - 1),
            agri_dig_full_pct=100 * (d.full_over_baseline - 1),
            agri_dig_full_usd=d.full_minus_baseline_usd,
            agri_pub_full_usd=p.full_usd,
        )
        for crop in CROPS:
            r = up[(up.crop == crop) & (up.year == y)].iloc[0]
            rec[f"sheaf_{crop}_prod_pct"] = r.shocks_pct_vs_base
            rec[f"sheaf_{crop}_full_pct"] = r.full_pct_vs_base
            rec[f"sheaf_{crop}_tau_pct"] = r.tau_pct_vs_base
            rec[f"sheaf_{crop}_restr_incr_pp"] = r.restriction_increment_pp
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = live_runs()

    sc = scores(runs)
    sc.to_csv(OUT / "current_scores.csv", index=False)
    print("=== live scores vs on-disk gate0_*_score.csv ===")
    print(sc.round(4).to_string(index=False))

    nc = node_coverage()
    nc.to_csv(OUT / "node_coverage.csv", index=False)
    print("\n=== node coverage ===")
    print(nc.round(4).to_string(index=False))

    bp, bs = bias_panel(runs)
    bp.to_csv(OUT / "hike_bias_panel_v2.csv", index=False)
    bs.to_csv(OUT / "hike_bias_summary_v2.csv", index=False)
    print("\n=== over-amplification panel (live) ===")
    print(bp.round(4).to_string(index=False))
    print(bs.round(4).to_string(index=False))

    up = annual_uplift(runs)
    up.to_csv(OUT / "sheaf_annual_uplift.csv", index=False)
    print("\n=== SHEAF annual mean price vs unperturbed baseline ===")
    print(up.round(2).to_string(index=False))

    cmp = agrimate_vs_sheaf(up)
    cmp.to_csv(OUT / "agrimate_vs_sheaf_54.csv", index=False)
    print("\n=== Agrimate 5.4 vs SHEAF ===")
    print(cmp.round(2).to_string(index=False))

    ab = ablations()
    ab.to_csv(OUT / "ablation_grid_r5.csv", index=False)
    print("\n=== ablations at current code ===")
    print(ab.round(3).to_string(index=False))

    qs, ql = quantity_side()
    qs.to_csv(OUT / "sheaf_world_quantity_signs_v2.csv", index=False)
    ql.to_csv(OUT / "sheaf_quantity_levels_v2.csv", index=False)
    print("\n=== quantity side (current artifacts) ===")
    print(qs.groupby(["panel", "crop"]).sign_agree.agg(["sum", "count"]))
    print(ql.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
