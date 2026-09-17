"""R5 red-team, resumed: the adjudication measurements.

Four things the first R5 pass did not do:

1. Like-for-like Agrimate-vs-SHEAF on the wheat path, using LIVE SHEAF runs
   (the inherited CSVs predate two model changes), and scoring Agrimate's own
   full model by SHEAF's own metrics so the amplification bias can be
   compared in both directions.
2. Level bias: annual mean model price over annual mean observed price, for
   both models, since the hike ratio is blind to a path that sits high and
   flat.
3. Isolation of the US-maize industrial (RFS) channel. The official leg set
   has no industrial-only leg: `demand` is year-by-year flex *plus*
   industrial, so "maize 2008 was ethanol-led" is not identified by it.
   Adds industrial-only and flex-trend-only legs.
4. Diagnosis of the negative world-consumption correlation, and the
   reduced-form ("R-class") parameter count from
   diagnostics/GATE0_PARAMETERIZATION.md's own classification.

Read-only w.r.t. sheaf/ and scripts/*.py (imports only).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    default_crop_params,
    result_to_monthly,
    run_crop_dynamics,
)

DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"
CROPS = ("wheat", "maize", "rice")
START, END = 2006, 2011
WINDOWS = (("2007/08", 2006, 6, 2008, 3), ("2010/11", 2009, 6, 2011, 2))


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 6 else float("nan")


def _hike(df, col, y0, m0, y1, m1) -> float:
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


def _nrmse(m, o) -> float:
    m, o = np.asarray(m, float), np.asarray(o, float)
    return float(np.sqrt(np.nanmean((m / np.nanmean(m) - o / np.nanmean(o)) ** 2)))


def head_sha() -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


# --------------------------------------------------------------------------
def like_for_like() -> tuple[pd.DataFrame, pd.DataFrame]:
    ag = pd.read_csv(OUT / "agrimate_fig4a_digitised.csv")
    obs = load_price_series_monthly(deflated=True)
    obs = obs[obs.year.between(START, END)][["year", "month", "wheat"]].rename(
        columns={"wheat": "obs_price"})
    res = run_crop_dynamics("wheat", start_year=START, end_year=END,
                            use_amis=True, use_shocks=True, use_demand=False)
    sh = result_to_monthly(res).merge(obs, on=["year", "month"], how="left")
    sh = sh.sort_values(["year", "month"]).reset_index(drop=True)
    ag = ag.sort_values(["year", "month"]).reset_index(drop=True)

    rows = [
        dict(model="SHEAF Gate 0 wheat (full leg)",
             target="Pink Sheet US HRW, MUV-2010-real (its own paper's target)",
             corr=_corr(sh.model_price, sh.obs_price),
             nrmse_meanscaled=_nrmse(sh.model_price, sh.obs_price),
             hike_2007_08=_hike(sh, "model_price", 2006, 6, 2008, 3),
             hike_2010_11=_hike(sh, "model_price", 2009, 6, 2011, 2),
             obs_hike_2007_08=_hike(sh, "obs_price", 2006, 6, 2008, 3),
             obs_hike_2010_11=_hike(sh, "obs_price", 2009, 6, 2011, 2)),
        dict(model="Agrimate full model (digitised Fig. 4a)",
             target="US HRW, US-CPI-real (its own paper's target, digitised)",
             corr=_corr(ag.full_model, ag.observed),
             nrmse_meanscaled=_nrmse(ag.full_model, ag.observed),
             hike_2007_08=_hike(ag, "full_model", 2006, 6, 2008, 3),
             hike_2010_11=_hike(ag, "full_model", 2009, 6, 2011, 2),
             obs_hike_2007_08=_hike(ag, "observed", 2006, 6, 2008, 3),
             obs_hike_2010_11=_hike(ag, "observed", 2009, 6, 2011, 2)),
        dict(model="Agrimate production-anomalies only (digitised)",
             target="US HRW, US-CPI-real (digitised)",
             corr=_corr(ag.prod_anom, ag.observed),
             nrmse_meanscaled=_nrmse(ag.prod_anom, ag.observed),
             hike_2007_08=_hike(ag, "prod_anom", 2006, 6, 2008, 3),
             hike_2010_11=_hike(ag, "prod_anom", 2009, 6, 2011, 2),
             obs_hike_2007_08=_hike(ag, "observed", 2006, 6, 2008, 3),
             obs_hike_2010_11=_hike(ag, "observed", 2009, 6, 2011, 2)),
        dict(model="Agrimate unperturbed baseline (digitised)",
             target="US HRW, US-CPI-real (digitised)",
             corr=_corr(ag.baseline, ag.observed),
             nrmse_meanscaled=_nrmse(ag.baseline, ag.observed),
             hike_2007_08=_hike(ag, "baseline", 2006, 6, 2008, 3),
             hike_2010_11=_hike(ag, "baseline", 2009, 6, 2011, 2),
             obs_hike_2007_08=_hike(ag, "observed", 2006, 6, 2008, 3),
             obs_hike_2010_11=_hike(ag, "observed", 2009, 6, 2011, 2)),
        # cross-target robustness: each model against the other's target
        dict(model="SHEAF Gate 0 wheat (full leg)",
             target="US HRW, US-CPI-real (Agrimate's target, digitised)",
             corr=_corr(sh.model_price.values, ag.observed.values),
             nrmse_meanscaled=_nrmse(sh.model_price.values, ag.observed.values),
             hike_2007_08=np.nan, hike_2010_11=np.nan,
             obs_hike_2007_08=np.nan, obs_hike_2010_11=np.nan),
        dict(model="Agrimate full model (digitised)",
             target="Pink Sheet US HRW, MUV-2010-real (SHEAF's target)",
             corr=_corr(ag.full_model.values, sh.obs_price.values),
             nrmse_meanscaled=_nrmse(ag.full_model.values, sh.obs_price.values),
             hike_2007_08=np.nan, hike_2010_11=np.nan,
             obs_hike_2007_08=np.nan, obs_hike_2010_11=np.nan),
    ]
    lfl = pd.DataFrame(rows)
    for w in ("2007_08", "2010_11"):
        lfl[f"amp_err_{w}_pct"] = 100 * (lfl[f"hike_{w}"]
                                         / lfl[f"obs_hike_{w}"] - 1)

    # annual level bias, both models, each against its own target
    lev = []
    for y in range(START, END + 1):
        s = sh[sh.year == y]
        a = ag[ag.year == y]
        lev.append(dict(year=y,
                        sheaf_model=float(s.model_price.mean()),
                        sheaf_obs=float(s.obs_price.mean()),
                        sheaf_ratio=float(s.model_price.mean()
                                          / s.obs_price.mean()),
                        agri_model=float(a.full_model.mean()),
                        agri_obs=float(a.observed.mean()),
                        agri_ratio=float(a.full_model.mean()
                                         / a.observed.mean())))
    return lfl, pd.DataFrame(lev)


def level_bias_all_crops() -> pd.DataFrame:
    obs_all = load_price_series_monthly(deflated=True)
    obs_all = obs_all[obs_all.year.between(START, END)]
    rows = []
    for crop in CROPS:
        o = obs_all[["year", "month", crop]].rename(columns={crop: "obs_price"})
        res = run_crop_dynamics(crop, start_year=START, end_year=END,
                                use_amis=True, use_shocks=True,
                                use_demand=False)
        m = result_to_monthly(res).merge(o, on=["year", "month"], how="left")
        for y in range(START, END + 1):
            s = m[m.year == y]
            rows.append(dict(crop=crop, year=y,
                             model_usd=float(s.model_price.mean()),
                             obs_usd=float(s.obs_price.mean()),
                             ratio=float(s.model_price.mean()
                                         / s.obs_price.mean())))
        rows.append(dict(crop=crop, year=-1,
                         model_usd=float(m.model_price.mean()),
                         obs_usd=float(m.obs_price.mean()),
                         ratio=float(m.model_price.mean() / m.obs_price.mean())))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
def isolate_industrial() -> pd.DataFrame:
    """Is maize 2007/08 actually carried by the RFS residual?

    Official legs conflate industrial with year-by-year flex demand. These
    five legs separate them. All other settings are the defaults.
    """
    obs_all = load_price_series_monthly(deflated=True)
    obs_all = obs_all[obs_all.year.between(START, END)]
    legs = {
        "full (amis+harvest+mean flex+ind)":
            dict(use_amis=True, use_shocks=True, use_demand=False),
        "harvest+ind (official `shocks`)":
            dict(use_amis=False, use_shocks=True, use_demand=False),
        "harvest only, NO ind":
            dict(use_amis=False, use_shocks=True, use_demand=False,
                 use_industrial=False),
        "industrial only":
            dict(use_amis=False, use_shocks=False, use_demand=False,
                 use_industrial=True),
        "flex-trend only, NO ind":
            dict(use_amis=False, use_shocks=False, use_demand=True,
                 use_industrial=False),
        "flex-trend+ind (official `demand`)":
            dict(use_amis=False, use_shocks=False, use_demand=True),
        "amis only (official `tau`)":
            dict(use_amis=True, use_shocks=False, use_demand=False,
                 use_industrial=False),
        "nothing (unperturbed)":
            dict(use_amis=False, use_shocks=False, use_demand=False,
                 use_industrial=False),
    }
    rows = []
    for crop in CROPS:
        o = obs_all[["year", "month", crop]].rename(columns={crop: "obs_price"})
        for name, kw in legs.items():
            res = run_crop_dynamics(crop, start_year=START, end_year=END, **kw)
            m = result_to_monthly(res).merge(o, on=["year", "month"],
                                             how="left")
            rec = dict(crop=crop, leg=name,
                       corr=_corr(m.model_price, m.obs_price),
                       mean_usd=float(m.model_price.mean()))
            for label, y0, m0, y1, m1 in WINDOWS:
                rec[f"hike_{label}"] = _hike(m, "model_price", y0, m0, y1, m1)
            rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
def consumption_diagnosis() -> pd.DataFrame:
    """Why is corr(model world consumption, PSD world consumption) negative?

    Official `full` holds flex food/feed at the score-window mean and lets
    only the isoelastic price term move it, so modelled use is a monotone
    decreasing function of modelled price. PSD use trends up over 2006-11.
    A negative correlation is then close to an identity, not a coincidence.
    """
    obs_all = load_price_series_monthly(deflated=True)
    obs_all = obs_all[obs_all.year.between(START, END)]
    rows = []
    for crop in CROPS:
        cons = pd.read_csv(DIAG / f"gate0_{crop}_consumption.csv"
                           ).sort_values("year")
        o = obs_all[["year", "month", crop]].rename(columns={crop: "obs_price"})
        res = run_crop_dynamics(crop, start_year=START, end_year=END,
                                use_amis=True, use_shocks=True,
                                use_demand=False)
        m = result_to_monthly(res).merge(o, on=["year", "month"], how="left")
        ann_p = m.groupby("year").model_price.mean().reindex(cons.year.values)
        rows.append(dict(
            crop=crop,
            corr_modelcons_psdcons=float(np.corrcoef(cons.model_cons,
                                                     cons.psd_cons)[0, 1]),
            corr_modelcons_modelprice=float(np.corrcoef(cons.model_cons,
                                                        ann_p.values)[0, 1]),
            corr_psdcons_year=float(np.corrcoef(cons.psd_cons,
                                                cons.year)[0, 1]),
            corr_modelprice_year=float(np.corrcoef(ann_p.values,
                                                   cons.year)[0, 1]),
            psd_cons_2006=float(cons.psd_cons.iloc[0]),
            psd_cons_2011=float(cons.psd_cons.iloc[-1]),
            psd_trend_pct=100 * (float(cons.psd_cons.iloc[-1])
                                 / float(cons.psd_cons.iloc[0]) - 1),
            model_cons_2006=float(cons.model_cons.iloc[0]),
            model_cons_2011=float(cons.model_cons.iloc[-1]),
            model_trend_pct=100 * (float(cons.model_cons.iloc[-1])
                                   / float(cons.model_cons.iloc[0]) - 1),
        ))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Classification taken verbatim from diagnostics/GATE0_PARAMETERIZATION.md §3
CLASS = {
    "elast": "literature", "stu_target": "literature", "max_stu": "literature",
    "pipeline_max_steps": "structural", "seasonal_buffer_steps": "unused",
    "rebuild_lambda": "reduced-form", "warehouse_lambda": "reduced-form",
    "inv_eta": "reduced-form", "smooth": "reduced-form",
    "trade_w": "reduced-form", "unmet_kappa": "reduced-form",
    "block_kappa": "reduced-form", "ask_alpha": "reduced-form",
    "ask_target_fill": "reduced-form", "ask_beta": "reduced-form",
    "ask_comp_elast": "reduced-form", "ask_rival": "reduced-form",
    "foresight_phi": "reduced-form",
    # present in CropParams, absent from the §3 table
    "harvest_pulse_frac": "reduced-form (NOT in the §3 table)",
    "residual_subst": "reduced-form (NOT in the §3 table)",
    "twin_harvest": "structural", "shock_mode": "structural",
    "industrial_nodes": "structural", "ind_base_years": "structural",
}


def parameter_count() -> pd.DataFrame:
    ps = {c: default_crop_params(c) for c in CROPS}
    rows = []
    for f in ps["wheat"].__dataclass_fields__:
        if f == "crop":
            continue
        vals = {c: getattr(ps[c], f) for c in CROPS}
        distinct = len({repr(v) for v in vals.values()})
        rows.append(dict(param=f, klass=CLASS.get(f, "UNCLASSIFIED"),
                         wheat=vals["wheat"], maize=vals["maize"],
                         rice=vals["rice"], distinct_values=distinct,
                         crop_specific=int(distinct > 1)))
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"HEAD = {head_sha()}")

    lfl, lev = like_for_like()
    lfl.to_csv(OUT / "like_for_like_v2.csv", index=False)
    lev.to_csv(OUT / "level_bias_wheat_v2.csv", index=False)
    print("\n=== like-for-like, live SHEAF vs digitised Agrimate ===")
    print(lfl.round(3).to_string(index=False))
    print("\n=== annual level bias, wheat ===")
    print(lev.round(3).to_string(index=False))

    lb = level_bias_all_crops()
    lb.to_csv(OUT / "level_bias_all_crops.csv", index=False)
    print("\n=== annual level bias, all crops (year=-1 is the window mean) ===")
    print(lb.round(3).to_string(index=False))

    iso = isolate_industrial()
    iso.to_csv(OUT / "channel_isolation.csv", index=False)
    print("\n=== channel isolation (industrial separated from flex trend) ===")
    print(iso.round(3).to_string(index=False))

    cd = consumption_diagnosis()
    cd.to_csv(OUT / "consumption_diagnosis.csv", index=False)
    print("\n=== world consumption diagnosis ===")
    print(cd.round(3).to_string(index=False))

    pc = parameter_count()
    pc.to_csv(OUT / "parameter_classes.csv", index=False)
    print("\n=== parameter classification (per GATE0_PARAMETERIZATION §3) ===")
    print(pc.to_string(index=False))
    g = pc.groupby("klass").agg(n_params=("param", "size"),
                                n_distinct_values=("distinct_values", "sum"))
    print("\n", g.to_string())
    g.to_csv(OUT / "parameter_class_summary.csv")


if __name__ == "__main__":
    main()
