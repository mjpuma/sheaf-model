"""Gate 0 three-scenario validation (Agrimate copy; G1/G2 later).

The workflow follows the Bai/Wada/Puma Agrimate-copy note (Sep 2026):
undisturbed / harvest-only / harvest+restrictions; score world prices *and*
global/regional supply and stocks; OAT sensitivity as a diagnostic; exporter-
and importer-side mechanism panels.

It does **not** adopt that note's fitted knobs (α_foreign=10), 2017–2025
window, FAO/USDA splice, or period-specific split calibration. Author
``AgrimateParams`` remain the defaults. The 36-run exporter grid is a
labelled G0-H experiment, not Gate 2.

SHEAF differentiators, blocked until G0-P (``GATE0_EXTENSION_PLAN.md``):

- **G1** cross-crop substitution. Disabled recovers this single-crop G0 run.
- **G2** government restriction game. Disabled recovers E.4 AMIS on this host.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_price_series_monthly

from .model import AgrimateResult, run_agrimate
from .params import AgrimateParams, wheat_params
from .wheat_data import WheatData, prepare_wheat, psd_regional_annual

ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "diagnostics" / "gate0_agrimate"
USDA_WORLD = ROOT / "data" / "usda_world" / "usda_psd_1961to2025_wheat.csv"

# Bai three scenarios, mapped onto Agrimate wheat 2006–11 (Kuhla et al. Fig. 4).
SCENARIOS: dict[str, dict] = {
    "undisturbed": {
        "use_anomalies": False,
        "use_restrictions": False,
        "label": "Undisturbed (repeating harvest, no AMIS)",
        "short": "undisturbed",
    },
    "harvest": {
        "use_anomalies": True,
        "use_restrictions": False,
        "label": "Harvest anomalies only",
        "short": "harvest-only",
    },
    "harvest_amis": {
        "use_anomalies": True,
        "use_restrictions": True,
        "label": "Harvest anomalies + AMIS restrictions (E.4)",
        "short": "harvest+AMIS",
    },
}

SCENARIO_ORDER = ("undisturbed", "harvest", "harvest_amis")

# Later SHEAF layers. Not implemented here; recorded so the Agrimate copy is
# scored as the host those layers will sit on.
G1G2_DIFFERENTIATORS = {
    "G1": (
        "Cross-crop substitution (wheat/rice/maize on the demand side). "
        "Disabled G1 recovers this single-crop G0 run."
    ),
    "G2": (
        "Endogenous export-restriction game among governments. "
        "Disabled G2 recovers E.4 AMIS on this host. Not the 36-run "
        "exporter-at-a-time grid, which is a prescribed-Δ experiment."
    ),
}

MECHANISM_EXPORTER = "Ukraine"
MECHANISM_IMPORTER = "Eastern Africa"

# OAT list: author defaults first. Bai's α_foreign=10 is an *alternative*,
# not a retune. β is listed only to record that it is unwired.
OAT_DEFAULT = (
    ("alpha_i", (3.2, 5.0, 10.0)),
    ("p_sto_annual", (0.05, 0.10, 0.15)),
    ("xmin_share", (0.10, 0.20)),
    ("eps_c", (0.10, 0.20)),
    ("sigma_ces", (2.0, 2.5)),
)

OAT_EXTENDED = OAT_DEFAULT + (
    ("tau_storage", (0.05, 0.10, 0.20)),
    ("tau_exp", (0.30, 0.50, 0.70)),
    ("tau_for", (0.10, 0.20, 0.40)),
    ("lam_demand", (0.0, 0.4)),
    ("n_for_months", (3, 6, 9)),
)


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    use_anomalies: bool
    use_restrictions: bool
    label: str


def scenario_specs() -> list[ScenarioSpec]:
    out = []
    for name in SCENARIO_ORDER:
        d = SCENARIOS[name]
        out.append(ScenarioSpec(
            name=name,
            use_anomalies=bool(d["use_anomalies"]),
            use_restrictions=bool(d["use_restrictions"]),
            label=str(d["label"]),
        ))
    return out


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def _hike(series: pd.Series, year0: int, year1: int) -> float:
    s = series[(series.index.year >= year0) & (series.index.year <= year1)]
    if s.empty:
        return float("nan")
    peak = float(s.rolling(3, min_periods=2).mean().max())
    ref = float(series[series.index.year == year0].mean())
    return peak / ref if ref and np.isfinite(ref) and ref > 0 else float("nan")


def _rmse(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 2:
        return float("nan")
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def monthly_price(result: AgrimateResult, field: str = "price_usd") -> pd.Series:
    y0 = result.start_year
    vals = result.to_monthly_price() if field == "price_usd" else None
    if field == "price_index":
        p = np.asarray(result.price_index, float)
        n = (p.size // 2) * 2
        vals = p[:n].reshape(-1, 2).mean(axis=1)
    idx = pd.period_range(f"{y0}-01", periods=len(vals), freq="M")
    return pd.Series(vals, index=idx, name=field)


def pink_sheet_monthly() -> pd.Series:
    pink = load_price_series_monthly()
    idx = [pd.Period(year=int(y), month=int(m), freq="M")
           for y, m in zip(pink["year"], pink["month"])]
    return pd.Series(pink["wheat"].to_numpy(float), index=idx, name="pink_usd")


def load_usda_world_wheat(path: Path | None = None) -> pd.DataFrame:
    """World-aggregate USDA PSD wheat, MMT / marketing year."""
    path = Path(path) if path else USDA_WORLD
    raw = pd.read_csv(path, header=None)
    attrs = [str(a).strip() for a in raw.iloc[1, 1:]]
    body = raw.iloc[3:].copy()
    df = pd.DataFrame(body.iloc[:, 1:].astype(float).values, columns=attrs)
    df["year"] = body.iloc[:, 0].astype(int).values
    rename = {
        "Beginning Stocks TY": "beginning_stocks",
        "Domestic Consumption TY": "consumption",
        "Ending Stocks TY": "ending_stocks",
        "Production TY": "production",
    }
    df = df.rename(columns=rename)
    for col in ("beginning_stocks", "consumption", "ending_stocks", "production"):
        df[col] = df[col] / 1000.0  # 1000 MT → MMT
    df["stock_to_use"] = df["ending_stocks"] / df["consumption"]
    return df[["year", "production", "consumption", "ending_stocks",
               "beginning_stocks", "stock_to_use"]]


def step_years(result: AgrimateResult) -> np.ndarray:
    n_y = STEPS_PER_YEAR
    T = result.price_index.size
    years = result.start_year + np.arange(T) // n_y
    return years


def annual_model_totals(result: AgrimateResult) -> pd.DataFrame:
    """Calendar-year sums / year-end stocks for the 27-node system (MMT)."""
    years = step_years(result)
    rows = []
    harvest = result.harvest
    cons = result.consumption
    xi = result.xi_ship
    sp = result.S_producer
    sc = result.S_consumer
    for y in range(result.start_year, result.end_year + 1):
        m = years == y
        last = int(np.where(m)[0][-1])
        h = float(harvest[:, m].sum()) if harvest is not None else float("nan")
        c = float(cons[:, m].sum()) if cons is not None else float("nan")
        x = float(xi[:, m].sum()) if xi is not None else float("nan")
        stocks = float(sp[:, last].sum() + sc[:, last].sum())
        rows.append({
            "year": y,
            "production": h,
            "consumption": c,
            "exports": x,
            "ending_stocks": stocks,
            "S_producer": float(sp[:, last].sum()),
            "S_consumer": float(sc[:, last].sum()),
            "stock_to_use": stocks / c if c and np.isfinite(c) and c > 0 else float("nan"),
            "price_index_mean": float(result.price_index[m].mean()),
        })
    return pd.DataFrame(rows)


def regional_annual(result: AgrimateResult, region: str) -> pd.DataFrame:
    i = result.regions.index(region)
    years = step_years(result)
    rows = []
    for y in range(result.start_year, result.end_year + 1):
        m = years == y
        last = int(np.where(m)[0][-1])
        h = result.harvest
        c = result.consumption
        x = result.xi_ship
        inf = result.inflow
        rows.append({
            "year": y,
            "production": float(h[i, m].sum()) if h is not None else float("nan"),
            "consumption": float(c[i, m].sum()) if c is not None else float("nan"),
            "exports": float(x[i, m].sum()) if x is not None else float("nan"),
            "inflow": float(inf[i, m].sum()) if inf is not None else float("nan"),
            "S_producer": float(result.S_producer[i, last]),
            "S_consumer": float(result.S_consumer[i, last]),
            "p_consumer_mean": (
                float(result.p_consumer[i, m].mean())
                if result.p_consumer is not None else float("nan")
            ),
            "price_index_mean": float(result.price_index[m].mean()),
        })
    return pd.DataFrame(rows)


def score_prices(
    results: dict[str, AgrimateResult],
    pink: pd.Series | None = None,
    score_start: int = 2006,
    score_end: int = 2011,
) -> pd.DataFrame:
    pink = pink if pink is not None else pink_sheet_monthly()
    rows = []
    for name in SCENARIO_ORDER:
        res = results[name]
        model = monthly_price(res)
        both = pd.concat([model.rename("model"), pink.rename("obs")], axis=1).dropna()
        both = both[(both.index.year >= score_start) & (both.index.year <= score_end)]
        m06 = float(both["model"][both.index.year == score_start].mean()) if not both.empty else float("nan")
        o06 = float(both["obs"][both.index.year == score_start].mean()) if not both.empty else float("nan")
        rows.append({
            "scenario": name,
            "label": SCENARIOS[name]["label"],
            "corr": _corr(both["model"], both["obs"]),
            "rmse_usd": _rmse(both["model"], both["obs"]),
            "hike_2008_model": _hike(both["model"], score_start, 2008),
            "hike_2008_obs": _hike(both["obs"], score_start, 2008),
            "mean_2006_model": m06,
            "mean_2006_obs": o06,
            "pidx_min": float(np.nanmin(res.price_index)),
            "pidx_max": float(np.nanmax(res.price_index)),
            "failed": res.failed_solves,
            "fallback": res.fallback_solves,
            "unconverged": res.unconverged_solves,
            "floor_binds": res.floor_binds,
            "plan_residual": res.plan_residual,
            "runtime_s": res.runtime_s,
        })
    return pd.DataFrame(rows)


def _join_model_obs(ann: pd.DataFrame, obs: pd.DataFrame) -> pd.DataFrame:
    a = ann.set_index("year")
    o = obs.set_index("year")
    cols = [c for c in ("production", "consumption", "ending_stocks", "stock_to_use")
            if c in a.columns and c in o.columns]
    return a[cols].add_suffix("_m").join(o[cols].add_suffix("_o"), how="inner")


def score_supply_stocks(
    results: dict[str, AgrimateResult],
    usda: pd.DataFrame | None = None,
    score_start: int = 2006,
    score_end: int = 2011,
) -> pd.DataFrame:
    usda = usda if usda is not None else load_usda_world_wheat()
    obs = usda[(usda["year"] >= score_start) & (usda["year"] <= score_end)]
    rows = []
    for name in SCENARIO_ORDER:
        ann = annual_model_totals(results[name])
        ann = ann[(ann["year"] >= score_start) & (ann["year"] <= score_end)]
        both = _join_model_obs(ann, obs)
        for field in ("production", "consumption", "ending_stocks", "stock_to_use"):
            mcol, ocol = f"{field}_m", f"{field}_o"
            if mcol not in both.columns or ocol not in both.columns:
                continue
            rows.append({
                "scenario": name,
                "field": field,
                "corr": _corr(both[mcol], both[ocol]),
                "rmse": _rmse(both[mcol], both[ocol]),
                "mean_model": float(both[mcol].mean()),
                "mean_obs": float(both[ocol].mean()),
            })
    return pd.DataFrame(rows)


def undisturbed_diagnostics(
    result: AgrimateResult,
    spinup_end: int = 2005,
) -> dict:
    """Seasonal repeating after spin-up: G0-U exit check, not a price pin."""
    years = step_years(result)
    post = years > spinup_end
    p = result.price_index[post]
    ypost = years[post]
    if p.size == 0:
        return {"n_steps": 0}
    annual_means = [float(p[ypost == y].mean()) for y in np.unique(ypost)]
    annual_means = np.asarray(annual_means, float)
    # reshape remaining complete years
    n_y = STEPS_PER_YEAR
    n_complete = p.size // n_y
    seasonal = p[: n_complete * n_y].reshape(n_complete, n_y) if n_complete else None
    out = {
        "n_steps": int(p.size),
        "price_mean": float(p.mean()),
        "price_cv": float(p.std() / p.mean()) if p.mean() else float("nan"),
        "annual_mean_min": float(np.nanmin(annual_means)) if annual_means.size else float("nan"),
        "annual_mean_max": float(np.nanmax(annual_means)) if annual_means.size else float("nan"),
        "annual_mean_drift": (
            float(annual_means[-1] / annual_means[0])
            if annual_means.size >= 2 and annual_means[0] > 0 else float("nan")
        ),
        "S_p_min": float(result.S_producer.min()),
        "S_c_min": float(result.S_consumer.min()),
    }
    if seasonal is not None and n_complete >= 2:
        # year-to-year RMS of the seasonal shape (should be small if repeating)
        out["seasonal_shape_rmse"] = float(np.sqrt(np.mean((seasonal[1:] - seasonal[:-1]) ** 2)))
    return out


def run_three_scenarios(
    data: WheatData | None = None,
    params: AgrimateParams | None = None,
    start_year: int = 2003,
    end_year: int = 2011,
) -> tuple[WheatData, dict[str, AgrimateResult]]:
    params = params or wheat_params()
    if data is None:
        data = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    results: dict[str, AgrimateResult] = {}
    for spec in scenario_specs():
        results[spec.name] = run_agrimate(
            data=data,
            params=params,
            use_anomalies=spec.use_anomalies,
            use_restrictions=spec.use_restrictions,
            start_year=start_year,
            end_year=end_year,
        )
    return data, results


def oat_settings(extended: bool = False) -> list[tuple[str, float, AgrimateParams]]:
    """(param, value, params) including the author default for each axis."""
    base = wheat_params()
    grid = OAT_EXTENDED if extended else OAT_DEFAULT
    out = []
    for name, values in grid:
        for v in values:
            out.append((name, float(v), replace(base, **{name: type(getattr(base, name))(v)})))
    return out


def write_tables(
    data: WheatData,
    results: dict[str, AgrimateResult],
    out: Path,
    score_start: int = 2006,
    score_end: int = 2011,
) -> dict[str, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    pink = pink_sheet_monthly()
    prices = score_prices(results, pink, score_start, score_end)
    qty = score_supply_stocks(results, score_start=score_start, score_end=score_end)
    prices.to_csv(out / "score_prices.csv", index=False)
    qty.to_csv(out / "score_supply_stocks.csv", index=False)

    # monthly world prices, all scenarios + Pink Sheet
    frames = []
    for name, res in results.items():
        s = monthly_price(res).rename(name)
        frames.append(s)
    price_wide = pd.concat(frames + [pink.rename("pink_usd")], axis=1)
    price_wide = price_wide[(price_wide.index.year >= score_start)
                            & (price_wide.index.year <= score_end)]
    price_wide.to_csv(out / "prices_three_scenarios.csv")

    for name, res in results.items():
        annual_model_totals(res).to_csv(out / f"annual_{name}.csv", index=False)
        if MECHANISM_EXPORTER in res.regions:
            regional_annual(res, MECHANISM_EXPORTER).to_csv(
                out / f"ukraine_{name}.csv", index=False)
        if MECHANISM_IMPORTER in res.regions:
            regional_annual(res, MECHANISM_IMPORTER).to_csv(
                out / f"eastern_africa_{name}.csv", index=False)

    # baseline trade (no sim)
    trade = pd.DataFrame(data.T_star, index=data.regions, columns=data.regions)
    trade.to_csv(out / "baseline_trade_mmt.csv")
    psd = psd_regional_annual(data.regions)
    base = psd[(psd["year"] >= 2007) & (psd["year"] <= 2009)]
    if not base.empty:
        cov = base.groupby("region")[["production", "consumption", "exports",
                                      "ending_stocks"]].mean()
        cov = cov.reindex(data.regions)
        cov["model_H_annual"] = data.H_annual
        cov.to_csv(out / "coverage_psd_vs_model.csv")
    return {"prices": prices, "supply_stocks": qty, "price_wide": price_wide}


def _setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 150,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })
    return plt


def write_figures(
    data: WheatData,
    results: dict[str, AgrimateResult],
    out: Path,
    score_start: int = 2006,
    score_end: int = 2011,
) -> list[Path]:
    plt = _setup_mpl()
    figdir = out / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    colors = {
        "undisturbed": "#7f7f7f",
        "harvest": "#1f77b4",
        "harvest_amis": "#d62728",
        "obs": "#000000",
    }
    pink = pink_sheet_monthly()

    # Fig 1 — coverage and baseline trade
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2))
    exports = np.asarray(data.T_star, float).copy()
    np.fill_diagonal(exports, 0.0)
    xshare = exports.sum(axis=1)
    order = np.argsort(xshare)[::-1]
    names = np.asarray(data.regions)
    ax = axes[0]
    ax.barh(np.arange(len(order)), xshare[order], color="#4c78a8")
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(names[order], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Baseline international exports (MMT / year)")
    ax.set_title("Fig. 1a  AgrimateRegionsWheat exporters")
    ax = axes[1]
    logt = np.log10(np.maximum(exports, 0.0) + 1e-6)
    im = ax.imshow(logt, cmap="YlOrBr", aspect="auto")
    ax.set_xticks(np.arange(len(names)))
    ax.set_yticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=90, fontsize=6)
    ax.set_yticklabels(names, fontsize=6)
    ax.set_title("Fig. 1b  Baseline T* (log10 MMT, international)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    p = figdir / "fig1_coverage_trade.png"
    fig.savefig(p)
    plt.close(fig)
    written.append(p)

    # Fig 2 — three-scenario world prices
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    p06 = float(pink[(pink.index.year == score_start)].mean())
    obs = pink[(pink.index.year >= score_start) & (pink.index.year <= score_end)]
    ax.plot([t.to_timestamp() for t in obs.index], obs / p06,
            color=colors["obs"], ls="--", lw=1.6, label="Pink Sheet (2006=1)")
    for name in SCENARIO_ORDER:
        s = monthly_price(results[name])
        s = s[(s.index.year >= score_start) & (s.index.year <= score_end)]
        m0 = float(s[s.index.year == score_start].mean())
        if not (m0 and np.isfinite(m0) and m0 > 0):
            m0 = float(s.mean())
        ax.plot([t.to_timestamp() for t in s.index], s / m0,
                color=colors[name], lw=1.4, label=SCENARIOS[name]["short"])
    ax.set_ylabel("World wheat price (2006 mean = 1)")
    ax.set_title("Fig. 2  Three-scenario world prices vs Pink Sheet")
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    p = figdir / "fig2_prices.png"
    fig.savefig(p)
    plt.close(fig)
    written.append(p)

    # Fig 3 — global supply and stocks vs USDA world
    usda = load_usda_world_wheat()
    usda = usda[(usda["year"] >= score_start) & (usda["year"] <= score_end)]
    fig, axes = plt.subplots(2, 2, figsize=(9.8, 6.6), sharex=True)
    fields = (
        ("production", "Production (MMT)"),
        ("ending_stocks", "Ending stocks (MMT)"),
        ("consumption", "Consumption (MMT)"),
        ("stock_to_use", "Stock-to-use"),
    )
    for ax, (field, ylab) in zip(axes.ravel(), fields):
        ax.plot(usda["year"], usda[field], color=colors["obs"], ls="--",
                lw=1.6, marker="o", ms=3.5, label="USDA world")
        for name in SCENARIO_ORDER:
            ann = annual_model_totals(results[name])
            ann = ann[(ann["year"] >= score_start) & (ann["year"] <= score_end)]
            ax.plot(ann["year"], ann[field], color=colors[name], lw=1.4,
                    marker="s", ms=3, label=SCENARIOS[name]["short"])
        ax.set_ylabel(ylab)
    axes[0, 0].set_title("Fig. 3  Global supply and stocks (27-node sum vs USDA world)")
    axes[0, 1].legend(loc="best", fontsize=7, frameon=False)
    axes[1, 0].set_xlabel("Year")
    axes[1, 1].set_xlabel("Year")
    fig.tight_layout()
    p = figdir / "fig3_supply_stocks.png"
    fig.savefig(p)
    plt.close(fig)
    written.append(p)

    # Fig 4 — Ukraine supplier mechanism
    if MECHANISM_EXPORTER in data.regions:
        fig, axes = plt.subplots(2, 2, figsize=(9.8, 6.4), sharex=True)
        fields = (
            ("production", "Harvest (MMT)"),
            ("S_producer", "Producer stocks, year-end (MMT)"),
            ("exports", "International sales (MMT)"),
            ("consumption", "Consumption (MMT)"),
        )
        for ax, (field, ylab) in zip(axes.ravel(), fields):
            for name in SCENARIO_ORDER:
                tab = regional_annual(results[name], MECHANISM_EXPORTER)
                tab = tab[(tab["year"] >= score_start) & (tab["year"] <= score_end)]
                ax.plot(tab["year"], tab[field], color=colors[name], lw=1.4,
                        marker="s", ms=3, label=SCENARIOS[name]["short"])
            ax.set_ylabel(ylab)
        axes[0, 0].set_title(f"Fig. 4  {MECHANISM_EXPORTER} supplier-side (AMIS vs harvest-only)")
        axes[0, 1].legend(loc="best", fontsize=7, frameon=False)
        fig.tight_layout()
        p = figdir / "fig4_ukraine_supplier.png"
        fig.savefig(p)
        plt.close(fig)
        written.append(p)

    # Fig 5 — Eastern Africa purchaser
    if MECHANISM_IMPORTER in data.regions:
        fig, axes = plt.subplots(2, 2, figsize=(9.8, 6.4), sharex=True)
        fields = (
            ("p_consumer_mean", "Consumer price (index)"),
            ("inflow", "Inflow / purchases (MMT)"),
            ("consumption", "Consumption (MMT)"),
            ("S_consumer", "Consumer stocks, year-end (MMT)"),
        )
        for ax, (field, ylab) in zip(axes.ravel(), fields):
            for name in SCENARIO_ORDER:
                tab = regional_annual(results[name], MECHANISM_IMPORTER)
                tab = tab[(tab["year"] >= score_start) & (tab["year"] <= score_end)]
                ax.plot(tab["year"], tab[field], color=colors[name], lw=1.4,
                        marker="s", ms=3, label=SCENARIOS[name]["short"])
            ax.set_ylabel(ylab)
        axes[0, 0].set_title(
            f"Fig. 5  {MECHANISM_IMPORTER} purchaser-side (AMIS vs harvest-only)")
        axes[0, 1].legend(loc="best", fontsize=7, frameon=False)
        fig.tight_layout()
        p = figdir / "fig5_eastern_africa_purchaser.png"
        fig.savefig(p)
        plt.close(fig)
        written.append(p)

    return written


def _fmt(x, nd=3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def write_report(
    data: WheatData,
    results: dict[str, AgrimateResult],
    tables: dict[str, pd.DataFrame],
    figures: list[Path],
    out: Path,
    start_year: int,
    end_year: int,
    score_start: int = 2006,
    score_end: int = 2011,
    sensitivity: pd.DataFrame | None = None,
) -> Path:
    prices = tables["prices"]
    qty = tables["supply_stocks"]
    und = undisturbed_diagnostics(results["undisturbed"])
    lines = [
        "# Agrimate Gate 0 — three-scenario validation",
        "",
        f"Command: `python scripts/run_agrimate_validation.py "
        f"--start-year {start_year} --end-year {end_year}`",
        "",
        "Independent Agrimate copy (Kuhla et al. 2025 §D; Zenodo 14022004 as",
        "executable spec, not copied). Workflow structure matches the Bai/Wada/Puma",
        "Agrimate-copy note (three scenarios; prices **and** supply/stocks;",
        "Ukraine / Eastern Africa mechanism panels; OAT diagnostic). Defaults",
        "remain author `AgrimateParams` (αI=3.2, not Bai's fitted α_foreign=10).",
        "Window is Agrimate wheat 2006–11, not that note's 2017–2025 paper.",
        "",
        "## SHEAF differentiators (later, blocked until G0-P)",
        "",
        f"- **G1** {G1G2_DIFFERENTIATORS['G1']}",
        f"- **G2** {G1G2_DIFFERENTIATORS['G2']}",
        "",
        "This run is G0: single crop, AMIS prescribed. Do not retune L1–L8.",
        "",
        f"- regions: {len(data.regions)}",
        f"- spin-up: {start_year}–{score_start - 1}; score: {score_start}–{score_end}",
        f"- data notes: {'; '.join(data.notes)}",
        "",
        "## Solver (each scenario)",
        "",
        "| scenario | failed | fallback | unconverged | floor | residual | runtime_s | pidx min/max |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in prices.iterrows():
        lines.append(
            f"| {r['scenario']} | {int(r['failed'])} | {int(r['fallback'])} | "
            f"{int(r['unconverged'])} | {int(r['floor_binds'])} | "
            f"{r['plan_residual']:.3e} | {_fmt(r['runtime_s'], 1)} | "
            f"{_fmt(r['pidx_min'], 4)} / {_fmt(r['pidx_max'], 4)} |"
        )
    lines += [
        "",
        "## Prices vs Pink Sheet (2006–11)",
        "",
        "Indexed comparison in `figures/fig2_prices.png`. A worse Pink-Sheet",
        "fit than the legacy host is not a reason to restore L1–L8.",
        "",
        "| scenario | corr | RMSE $/t | 2007/08 hike model | hike obs | 2006 mean model | 2006 obs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in prices.iterrows():
        lines.append(
            f"| {r['scenario']} | {_fmt(r['corr'])} | {_fmt(r['rmse_usd'], 1)} | "
            f"×{_fmt(r['hike_2008_model'], 2)} | ×{_fmt(r['hike_2008_obs'], 2)} | "
            f"{_fmt(r['mean_2006_model'], 1)} | {_fmt(r['mean_2006_obs'], 1)} |"
        )
    lines += [
        "",
        "## Supply and stocks vs USDA world (2006–11)",
        "",
        "Model sums 27 AgrimateRegionsWheat nodes; USDA is the world aggregate.",
        "Level bias from missing coverage is expected; **anomaly correlation**",
        "is the performance number. FAOSTAT Food Balances remain labelled A1",
        "(Bai found FAO anomalies closer to prices in 2020–24; we stay on USDA",
        "because FAOSTAT FB is not in this repository).",
        "",
        "| scenario | field | corr | RMSE | mean model | mean USDA |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in qty.iterrows():
        lines.append(
            f"| {r['scenario']} | {r['field']} | {_fmt(r['corr'])} | "
            f"{_fmt(r['rmse'], 2)} | {_fmt(r['mean_model'], 2)} | {_fmt(r['mean_obs'], 2)} |"
        )
    lines += [
        "",
        "## G0-U undisturbed dynamics (after 2003–05 spin-up)",
        "",
        "Repeating seasonal harvest, no AMIS. Not a world-price pin.",
        "",
        f"- post-spin-up price mean: {_fmt(und.get('price_mean'), 4)}",
        f"- within-window CV: {_fmt(und.get('price_cv'), 3)}",
        f"- annual-mean min/max: {_fmt(und.get('annual_mean_min'), 4)} / "
        f"{_fmt(und.get('annual_mean_max'), 4)}",
        f"- last/first annual-mean ratio (drift): {_fmt(und.get('annual_mean_drift'), 3)}",
        f"- year-to-year seasonal-shape RMSE: {_fmt(und.get('seasonal_shape_rmse'), 4)}",
        f"- min S_p / S_c: {_fmt(und.get('S_p_min'), 4)} / {_fmt(und.get('S_c_min'), 4)}",
        "",
        "## Mechanism panels",
        "",
        f"- Fig. 4 `{MECHANISM_EXPORTER}` supplier: harvest, producer stocks, exports, consumption.",
        f"- Fig. 5 `{MECHANISM_IMPORTER}` purchaser: consumer price, inflow, consumption, stocks.",
        "These compare harvest-only vs harvest+AMIS on the 2006–11 AMIS diary,",
        "not a synthetic 36-run exporter grid (that grid is G0-H/P; see",
        "`restriction_pulse` in `restrictions.py`).",
        "",
        "## Figures",
        "",
    ]
    for p in figures:
        try:
            lines.append(f"- `{p.relative_to(out)}`")
        except ValueError:
            lines.append(f"- `{p}`")
    lines += [
        "",
        "## What this does not do",
        "",
        "- Does not retune αI, p_sto, or x_min from Pink Sheet or from Bai's table.",
        "- Does not split-calibrate 2008 vs 2022 (Bai's finding that one set cannot",
        "  fit both crises is recorded as an open G0-H question).",
        "- Does not implement G1 substitution or G2 government best-response.",
        "- Does not unpack Zenodo 10688435 (Agrimate Fig. 4 author series still G0-H).",
        "",
    ]
    if sensitivity is not None and not sensitivity.empty:
        lines += [
            "## OAT sensitivity (diagnostic, author defaults unchanged)",
            "",
            "Each named parameter is varied individually. α_foreign=10 is Bai's",
            "fit, shown as an alternative, not adopted.",
            "",
            "| param | value | scenario | corr | hike_2008 | pidx_max | failed |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
        for _, r in sensitivity.iterrows():
            lines.append(
                f"| {r['param']} | {r['value']} | {r['scenario']} | "
                f"{_fmt(r.get('corr'))} | ×{_fmt(r.get('hike_2008_model'), 2)} | "
                f"{_fmt(r.get('pidx_max'), 3)} | {int(r.get('failed', 0))} |"
            )
        lines.append("")
    path = out / "validation.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_sensitivity(
    data: WheatData,
    start_year: int,
    end_year: int,
    extended: bool = False,
    scenarios: tuple[str, ...] = ("harvest_amis",),
) -> pd.DataFrame:
    rows = []
    pink = pink_sheet_monthly()
    for name, value, params in oat_settings(extended=extended):
        for sc in scenarios:
            spec = SCENARIOS[sc]
            res = run_agrimate(
                data=data, params=params,
                use_anomalies=spec["use_anomalies"],
                use_restrictions=spec["use_restrictions"],
                start_year=start_year, end_year=end_year,
            )
            model = monthly_price(res)
            both = pd.concat([model.rename("model"), pink.rename("obs")], axis=1).dropna()
            both = both[(both.index.year >= max(start_year, 2006))
                        & (both.index.year <= end_year)]
            rows.append({
                "param": name,
                "value": value,
                "scenario": sc,
                "corr": _corr(both["model"], both["obs"]) if not both.empty else float("nan"),
                "hike_2008_model": _hike(both["model"], 2006, 2008) if not both.empty else float("nan"),
                "pidx_min": float(np.nanmin(res.price_index)),
                "pidx_max": float(np.nanmax(res.price_index)),
                "failed": res.failed_solves,
                "unconverged": res.unconverged_solves,
                "runtime_s": res.runtime_s,
            })
    return pd.DataFrame(rows)
