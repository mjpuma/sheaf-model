"""Build Agrimate simulate() input CSVs from SHEAF datasets.

These are not the author files. Zenodo 14870541 has model output only.
The published code asks for seven CSVs; this script fills that layout from:

- USDA PSD country-year wheat (1000 t), baseline mean 2007–2009
- FAOSTAT E0 wheat trade, 2006–07 window, rescaled to those USDA exports
- data/crop_calendars/wheat_harvest_months.csv, spread over days 1–365
- AMIS wheat measures (daily-max merge of overlapping intervals)
- stock-to-use, A_d, and A_c from the same PSD totals

USDA reports the European Union as one unit (code E4). Member states are not
in the PSD file, so that total is written on DEU. After AgrimateEU28
aggregation it is the EU-28 total.

Outputs land next to the unpacked paper code, where simulate() looks by
default. simulate() is not called.
"""
from __future__ import annotations

import calendar
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputs.pipelines.data_faostat import load_trade_matrix
from inputs.pipelines.data_usda import detrend_anomalies, load_amis_restrictions, load_psd_country
JULIA_REGIONS = ROOT / "agrimate_julia" / "src" / "regions.jl"
OUT = ROOT / "inputs" / "generated" / "agrimate_input"
CONV = ROOT / "data/faostat_network/country_conversion_table.csv"
CAL = ROOT / "data/crop_calendars/wheat_harvest_months.csv"

# Author scenario names (DrWatson savename, keys sorted, connector "_").
FILES = {
    "food": "food-balance_baseline=2007-2009_crop=wheat.csv",
    "trade": "trade-flows_baseline=2007-2009_crop=wheat.csv",
    "harvest": "harvest-distributions_crop=wheat.csv",
    "params": "parameters_baseline=2007-2009_crop=wheat_source=empirical.csv",
    "anom": "harvest-anomalies_crop=wheat_source=FAOsince-2005.csv",
    "trend": "harvest-trends_crop=wheat_source=FAOsince-2005.csv",
    "restrict": "export-restrictions_crop=wheat_source=2007-2011.csv",
}

# Agrimate supplement E.4-style cuts. Licensing is unused.
CUTS = (
    ("export prohibition", 0.95),
    ("export ban", 0.95),
    ("export quota", 0.70),
    ("export tax", 0.50),
)
HIGH_AC = {"USA", "Canada", "Australia", "EU-28", "Rest of Europe", "Rest of Oceania"}
UPPER_AC = {
    "Russia", "Kazakhstan", "Brazil", "Argentina", "China",
    "Rest of Eastern Asia", "Turkey",
}
SOUTH_REGIONS = {
    "Argentina", "Australia", "Brazil", "Rest of Oceania",
    "Southern Africa", "Rest of South America",
}
# USDA EU aggregate has no member rows. DEU is only a carrier so the
# AgrimateEU28 sum still equals the USDA European Union total.
EU_CARRIER = "DEU"
ANOMALY_YEARS = range(2000, 2017)  # columns "2000-1" .. "2016-365"
# simulate() applies every row in the file, whatever its "source=2007-2011" name says.
RESTRICT_WINDOW = (pd.Timestamp("2007-01-01"), pd.Timestamp("2011-12-31"))


def parse_regions(const_name: str) -> dict[str, list[str]]:
    text = JULIA_REGIONS.read_text()
    m = re.search(rf'const {const_name} = """(.*?)"""', text, re.S)
    if not m:
        raise RuntimeError(f"{const_name} not found in {JULIA_REGIONS}")
    regions: dict[str, list[str]] = {}
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        codes = re.findall(r"[A-Z]{3}", rest)
        if codes:
            regions[name.strip()] = codes
    return regions


def iso_lookup(psd: pd.DataFrame) -> dict[str, str]:
    conv = pd.read_csv(CONV, encoding="utf-8-sig")
    names = (
        psd.groupby("country_code")["country_psd"].agg(lambda s: s.iloc[0]).to_dict()
    )
    out: dict[str, str] = {}
    for code, g in conv.groupby("USDA PSD"):
        code = str(code).strip()
        if not code or code == "NULL":
            continue
        rows = []
        for _, r in g.iterrows():
            iso = r["ISO3 alpha"]
            if pd.isna(iso):
                if "Taiwan" in str(r["Country"]):
                    iso = "TWN"
                else:
                    continue
            rows.append((str(r["Country"]), str(iso).strip()))
        if not rows:
            continue
        if len(rows) == 1:
            out[code] = rows[0][1]
            continue
        psd_name = str(names.get(code, ""))
        match = [iso for country, iso in rows if country.lower() in psd_name.lower() or psd_name.lower() in country.lower()]
        if len(match) != 1:
            raise RuntimeError(f"ambiguous USDA code {code} -> {rows} (PSD name {psd_name!r})")
        out[code] = match[0]
    return out


def ac_for(region: str) -> float:
    if region in HIGH_AC:
        return 0.15
    if region in UPPER_AC:
        return 0.25
    return 0.40


def day_span(start_month: int, end_month: int) -> list[int]:
    def first(month: int) -> int:
        return int(pd.Timestamp(2001, month, 1).dayofyear)

    start = first(start_month)
    end = first(end_month) + calendar.monthrange(2001, end_month)[1] - 1
    if start <= end:
        return list(range(start, end + 1))
    return list(range(start, 366)) + list(range(1, end + 1))


def raised_cosine(days: list[int]) -> np.ndarray:
    n = len(days)
    if n == 1:
        w = np.ones(1)
    else:
        w = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n) / (n - 1)))
        if w.sum() <= 0:
            w = np.ones(n)
    w = w / w.sum()
    out = np.zeros(365)
    for day, weight in zip(days, w):
        out[day - 1] += weight
    total = out.sum()
    if total <= 0:
        out[:] = 1.0 / 365.0
    else:
        out /= total
    return out


def calendar_by_iso(regions: dict[str, list[str]]) -> dict[str, np.ndarray]:
    cal = pd.read_csv(CAL)
    by_name = {
        str(r.country): (int(r.harvest_start_month), int(r.harvest_end_month))
        for r in cal.itertuples()
    }
    named = {
        "USA": "USA", "RUS": "Russia", "UKR": "Ukraine", "KAZ": "Kazakhstan",
        "CAN": "Canada", "AUS": "Australia", "ARG": "Argentina", "BRA": "Brazil",
        "IND": "India", "CHN": "China", "EGY": "Egypt", "MEX": "Mexico",
        "THA": "Thailand", "VNM": "Vietnam", "IDN": "Indonesia", "NGA": "Nigeria",
    }
    eu = set(regions["EU-28"])
    profiles: dict[str, np.ndarray] = {}
    for region, isos in regions.items():
        for iso in isos:
            if iso in named:
                a, b = by_name[named[iso]]
            elif iso in eu:
                a, b = by_name["EU"]
            elif region in SOUTH_REGIONS:
                a, b = by_name["Argentina"]
            else:
                a, b = by_name["RestOfWorld"]
            profiles[iso] = raised_cosine(day_span(a, b))
    return profiles


def baseline_by_iso(psd: pd.DataFrame, code_to_iso: dict[str, str], region_isos: set[str]) -> pd.DataFrame:
    base = psd[psd["year"].between(2007, 2009)].copy()
    base["iso"] = base["country_code"].map(code_to_iso)
    base = base.dropna(subset=["iso"])
    # EU aggregate is not an ISO in AgrimateEU28. Park it on DEU.
    base.loc[base["country_code"] == "E4", "iso"] = EU_CARRIER
    base = base[base["iso"].isin(region_isos)]
    g = base.groupby("iso")[["production", "consumption", "exports", "imports", "ending_stocks"]].mean()
    # load_psd_country returns MMT. Author-style food balances are 1000 t.
    return g * 1000.0


def annual_production(psd: pd.DataFrame, code_to_iso: dict[str, str], region_isos: set[str]) -> pd.DataFrame:
    d = psd[psd["year"].between(1990, 2016)].copy()
    d["iso"] = d["country_code"].map(code_to_iso)
    d.loc[d["country_code"] == "E4", "iso"] = EU_CARRIER
    d = d.dropna(subset=["iso"])
    d = d[d["iso"].isin(region_isos)]
    tab = d.groupby(["iso", "year"])["production"].sum().unstack("year") * 1000.0
    return tab


def merge_restrictions(rows: list[tuple[str, pd.Timestamp, pd.Timestamp, float]]) -> pd.DataFrame:
    """One non-overlapping interval set per exporter, value = max cut that day.

    AMIS repeats a measure once per rate revision, so the raw rows overlap.
    The paper's aggregate_export_restrictions adds overlapping values (capped
    at 1), which would stack those repeats. This builder takes the daily
    maximum instead. Rows are clipped to RESTRICT_WINDOW first and rows
    outside it are dropped.
    """
    lo, hi = RESTRICT_WINDOW
    clipped = [(i, max(s, lo), min(e, hi), v) for i, s, e, v in rows]
    out = []
    for iso in sorted({r[0] for r in clipped}):
        spans = [(s, e, v) for i, s, e, v in clipped if i == iso and e >= s]
        if not spans:
            continue
        days = pd.date_range(min(s for s, _, _ in spans), max(e for _, e, _ in spans), freq="D")
        cut = pd.Series(0.0, index=days)
        for s, e, v in spans:
            cut.loc[s:e] = np.maximum(cut.loc[s:e].values, v)
        run_id = (cut != cut.shift()).cumsum()
        for _, run in cut.groupby(run_id):
            if run.iloc[0] <= 0:
                continue
            out.append({
                "Exporter": iso,
                "From": run.index[0].date().isoformat(),
                "To": run.index[-1].date().isoformat(),
                "Value": float(run.iloc[0]),
            })
    return pd.DataFrame(out, columns=["Exporter", "From", "To", "Value"])


def main() -> None:
    regions = parse_regions("AgrimateEU28Regions")
    region_isos = {iso for isos in regions.values() for iso in isos}
    iso_region = {iso: name for name, isos in regions.items() for iso in isos}
    if EU_CARRIER not in region_isos:
        raise RuntimeError(f"{EU_CARRIER} is not in AgrimateEU28")

    psd = load_psd_country("wheat")
    code_to_iso = iso_lookup(psd)
    base = baseline_by_iso(psd, code_to_iso, region_isos)

    food_rows = []
    for iso in sorted(region_isos):
        if iso in base.index:
            prod = float(base.loc[iso, "production"])
            cons = float(base.loc[iso, "consumption"])
            exp = float(base.loc[iso, "exports"])
            imp = float(base.loc[iso, "imports"])
            stocks = float(base.loc[iso, "ending_stocks"])
        else:
            prod = cons = exp = imp = stocks = 0.0
        food_rows.append({
            "Area": iso,
            "Production": prod,
            "Consumption": cons,
            "Exports (harmonized)": exp,
            "Imports (harmonized)": imp,
            "Imports (non-harmonized)": 0.0,
            "_stocks": stocks,
        })
    food = pd.DataFrame(food_rows)

    e0 = load_trade_matrix("wheat", window=(2006, 2007))
    e0 = e0.reindex(index=sorted(region_isos), columns=sorted(region_isos)).fillna(0.0)
    eu = set(regions["EU-28"])
    flows = []
    for iso in sorted(region_isos - eu):
        total = float(base.loc[iso, "exports"]) if iso in base.index else 0.0
        if total <= 0:
            continue
        row = e0.loc[iso].copy()
        row.loc[iso] = 0.0
        if row.sum() <= 0:
            continue
        row = row * (total / row.sum())
        for dest, val in row.items():
            if val > 0 and dest in region_isos:
                flows.append((iso, dest, float(val)))
    eu_row = e0.loc[list(eu)].sum(axis=0)
    eu_row.loc[list(eu)] = 0.0
    eu_total = float(base.loc[EU_CARRIER, "exports"]) if EU_CARRIER in base.index else 0.0
    if eu_row.sum() > 0 and eu_total > 0:
        eu_row = eu_row * (eu_total / eu_row.sum())
        for dest, val in eu_row.items():
            if val > 0 and dest in region_isos and dest not in eu:
                flows.append((EU_CARRIER, dest, float(val)))
    trade = pd.DataFrame(flows, columns=["Origin", "Destination", "Trade Flow"])

    profiles = calendar_by_iso(regions)
    day_cols = [str(i) for i in range(1, 366)]
    harvest = pd.DataFrame(
        [dict(Area=iso, **{str(i + 1): profiles[iso][i] for i in range(365)}) for iso in sorted(region_isos)]
    )
    harvest = harvest[["Area", *day_cols]]

    params_rows = []
    for _, r in food.iterrows():
        cons = float(r["Consumption"])
        stocks = float(r["_stocks"])
        imp = float(r["Imports (harmonized)"])
        if cons > 0:
            stu = stocks / cons
            ad = float(np.clip(0.05 + 0.4 * (imp / cons), 0.02, 0.9))
        else:
            stu = np.nan
            ad = np.nan
        params_rows.append({
            "Area": r["Area"],
            "STU": stu,
            "A_d": ad,
            "A_c": ac_for(iso_region[r["Area"]]),
        })
    params = pd.DataFrame(params_rows)

    prod_annual = annual_production(psd, code_to_iso, region_isos)
    areas = sorted(region_isos)
    years = list(ANOMALY_YEARS)
    day_names = [f"{year}-{day}" for year in years for day in range(1, 366)]
    n_a, n_y, n_d = len(areas), len(years), 365
    resid = np.zeros((n_a, n_y, n_d))
    level = np.zeros((n_a, n_y, n_d))
    area_index = {iso: i for i, iso in enumerate(areas)}
    year_index = {year: i for i, year in enumerate(years)}
    # simulate() sums these files over each region before forming
    # 1 + anomaly/trend, so one blank or NaN cell voids the whole region.
    # Non-producers must therefore carry exact zeros, never NaN.
    for iso in prod_annual.index:
        series = prod_annual.loc[iso].dropna()
        if len(series) < 8 or iso not in area_index or not (series > 0).any():
            continue
        fitted = detrend_anomalies(series, window_years=10)
        i = area_index[iso]
        for year, row in fitted.iterrows():
            if int(year) not in year_index:
                continue
            j = year_index[int(year)]
            trend_level = float(row["trend"])
            if not np.isfinite(trend_level) or trend_level <= 0:
                continue
            anomaly = 0.0 if int(year) < 2005 else float(row["anomaly"]) * trend_level
            resid[i, j, :] = anomaly
            level[i, j, :] = trend_level
    if not (np.isfinite(resid).all() and np.isfinite(level).all()):
        raise RuntimeError("non-finite harvest anomaly or trend")
    anom = pd.concat(
        [pd.Series(areas, name="Area"), pd.DataFrame(resid.reshape(n_a, n_y * n_d), columns=day_names)],
        axis=1,
    )
    trend = pd.concat(
        [pd.Series(areas, name="Area"), pd.DataFrame(level.reshape(n_a, n_y * n_d), columns=day_names)],
        axis=1,
    )

    amis = load_amis_restrictions()
    amis = amis[amis["CommodityClass_Name"].astype(str).str.contains("Wheat", case=False, na=False)]
    name_to_iso = {}
    conv = pd.read_csv(CONV, encoding="utf-8-sig")
    for _, r in conv.iterrows():
        iso = r["ISO3 alpha"]
        if pd.notna(iso):
            name_to_iso[str(r["Country"]).strip().lower()] = str(iso).strip()
    name_to_iso.update({
        "russian federation": "RUS",
        "viet nam": "VNM",
        "vietnam": "VNM",
        "china": "CHN",
        "egypt": "EGY",
        "united states": "USA",
        "european union": EU_CARRIER,
    })
    restrictions = []
    for _, row in amis.iterrows():
        meas = str(row["PolicyMeasure_Name"])
        cut = 0.0
        for key, val in CUTS:
            if key in meas.lower():
                cut = val
                break
        if cut <= 0:
            continue
        iso = name_to_iso.get(str(row["Country_Name"]).strip().lower())
        if iso not in region_isos:
            continue
        start = pd.to_datetime(row["Start_Date"], errors="coerce")
        end = pd.to_datetime(row["End_Date"], errors="coerce")
        if pd.isna(start):
            continue
        if pd.isna(end):
            end = start + pd.Timedelta(days=183)
        restrictions.append((iso, start.normalize(), end.normalize(), cut))
    restrict = merge_restrictions(restrictions)

    OUT.mkdir(parents=True, exist_ok=True)
    food.drop(columns="_stocks").to_csv(OUT / FILES["food"], index=False)
    trade.to_csv(OUT / FILES["trade"], index=False)
    harvest.to_csv(OUT / FILES["harvest"], index=False)
    params.to_csv(OUT / FILES["params"], index=False)
    anom.to_csv(OUT / FILES["anom"], index=False)
    trend.to_csv(OUT / FILES["trend"], index=False)
    restrict.to_csv(OUT / FILES["restrict"], index=False)

    readme = OUT / "README.txt"
    readme.write_text(
        "SHEAF reconstruction of the CSVs simulate() reads. Not author input.\n"
        "Quantities are thousand tonnes. See diagnostics/gate0_julia/INPUTS.md\n"
        "in the sheaf-model repo.\n"
    )
    print(f"wrote {OUT}")
    print(f"regions {len(regions)} isos {len(region_isos)}")
    print(f"production 1000t {food['Production'].sum():.0f}  consumption {food['Consumption'].sum():.0f}")
    print(f"trade rows {len(trade)}  sum {trade['Trade Flow'].sum():.0f}")
    print(f"restrictions {len(restrict)} exporters {sorted(restrict['Exporter'].unique()) if len(restrict) else []}")
    print(f"harvest row sums {harvest[day_cols].sum(axis=1).min():.6f} {harvest[day_cols].sum(axis=1).max():.6f}")
    print(f"anomaly cols {len(day_names)} first {day_names[0]} last {day_names[-1]}")


if __name__ == "__main__":
    main()
