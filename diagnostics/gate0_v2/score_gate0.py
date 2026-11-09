"""Score an Agrimate NetCDF on the J10 Gate 0 metrics, optionally against a reference run.

    python diagnostics/gate0_v2/score_gate0.py LOCAL.nc [REFERENCE.nc]

World price: monthly mean of cross-border transaction prices weighted by quantity
(diagonal skipped). Ratios are July-June window means over the 2000-2005 mean.
World stocks: producer/supplier storage plus consumer storage at the last step of
each complete 24-step year, in Mt. Regions are matched by name, so files whose
region order or storage names differ can be compared.
"""

import sys
from collections import OrderedDict

import netCDF4
import numpy as np

N_YEAR = 24


def _axis_first(var, first):
    data = np.ma.filled(var[:].astype(float), np.nan)
    order = [var.dimensions.index(first)] + [i for i, d in enumerate(var.dimensions) if d != first]
    return np.transpose(data, order)


def load(path):
    ds = netCDF4.Dataset(path)
    tvar = ds.variables["time"]
    times = netCDF4.num2date(tvar[:], units=tvar.units, calendar=getattr(tvar, "calendar", "standard"))
    regions = [str(r) for r in ds.variables["region"][:]]
    q = np.nan_to_num(_axis_first(ds.variables["transaction quantity"], "time"))
    p = np.nan_to_num(_axis_first(ds.variables["transaction price"], "time"))
    supplier = "supplier storage" if "supplier storage" in ds.variables else "producer storage"
    stock = np.nan_to_num(_axis_first(ds.variables[supplier], "time"))
    stock = stock + np.nan_to_num(_axis_first(ds.variables["consumer storage"], "time"))
    ds.close()
    return {"times": list(times), "regions": regions, "q": q, "p": p, "stock": stock}


def monthly_world_price(run, t_max):
    off = ~np.eye(run["q"].shape[1], dtype=bool)
    months = OrderedDict()
    for t in range(t_max):
        key = (run["times"][t].year, run["times"][t].month)
        v = float((run["q"][t] * run["p"][t])[off].sum())
        w = float(run["q"][t][off].sum())
        acc = months.setdefault(key, [0.0, 0.0])
        acc[0] += v
        acc[1] += w
    return OrderedDict((k, v / w if w > 0 else np.nan) for k, (v, w) in months.items())


def window(prices, start, end):
    vals = [v for k, v in prices.items() if start <= k <= end]
    return float(np.mean(vals)) if vals else np.nan


def price_metrics(prices):
    base = window(prices, (2000, 1), (2005, 12))
    peak_key = max(prices, key=lambda k: prices[k])
    return {
        "base": base,
        "r0708": window(prices, (2007, 7), (2008, 6)) / base,
        "r1011": window(prices, (2010, 7), (2011, 6)) / base,
        "peak": prices[peak_key],
        "peak_month": peak_key,
    }


def year_end_stocks(run, t_max, regions=None):
    out = OrderedDict()
    years = [t.year for t in run["times"][:t_max]]
    for y in sorted(set(years)):
        idx = [i for i, yy in enumerate(years) if yy == y]
        if len(idx) != N_YEAR:
            continue
        row = run["stock"][idx[-1]]
        if regions is None:
            out[y] = float(row.sum()) / 1e3
        else:
            out[y] = {r: float(row[run["regions"].index(r)]) / 1e3 for r in regions}
    return out


def main():
    local = load(sys.argv[1])
    ref = load(sys.argv[2]) if len(sys.argv) > 2 else None
    t_max = len(local["times"])
    if ref is not None:
        t_max = min(t_max, len(ref["times"]))
    print(f"steps scored: {t_max} (through {local['times'][t_max - 1]})")

    pl = price_metrics(monthly_world_price(local, t_max))
    pr = price_metrics(monthly_world_price(ref, t_max)) if ref is not None else None
    for key, label in (("base", "2000-2005 mean price"), ("r0708", "2007/08 ratio"),
                       ("r1011", "2010/11 ratio"), ("peak", "peak price")):
        line = f"{label:22s} local {pl[key]:.4f}"
        if pr is not None:
            line += f"  reference {pr[key]:.4f}  diff {pl[key] - pr[key]:+.4f}"
        print(line)
    print(f"peak month             local {pl['peak_month']}" +
          (f"  reference {pr['peak_month']}" if pr is not None else ""))

    sl = year_end_stocks(local, t_max)
    print("\nend-of-year world stocks (Mt): year, local" + (", reference, gap %" if ref else ""))
    if ref is None:
        for y, v in sl.items():
            print(f"  {y}  {v:9.2f}")
        return
    sr = year_end_stocks(ref, t_max)
    shared = [r for r in local["regions"] if r in ref["regions"]]
    missing = sorted(set(local["regions"]) ^ set(ref["regions"]))
    if missing:
        print(f"  regions not in both files: {missing}")
    rl = year_end_stocks(local, t_max, shared)
    rr = year_end_stocks(ref, t_max, shared)
    worst = (None, 0.0)
    for y in sl:
        gap = 100 * (sl[y] / sr[y] - 1)
        if abs(gap) > abs(worst[1]):
            worst = (y, gap)
        top = sorted(shared, key=lambda r: -abs(rl[y][r] - rr[y][r]))[:3]
        parts = ", ".join(f"{r} {100 * (rl[y][r] - rr[y][r]) / sr[y]:+.3f}pp" for r in top)
        print(f"  {y}  {sl[y]:9.2f}  {sr[y]:9.2f}  {gap:+7.3f} %   largest: {parts}")
    print(f"\nworst stock gap: {worst[1]:+.3f} % ({worst[0]})")


if __name__ == "__main__":
    main()
