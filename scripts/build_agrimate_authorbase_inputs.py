"""Gate 0 J10: write `data/agrimate_input_authorbase/`.

This is the J9 input set (author region parameters + author export
restrictions) with every *quantity* input replaced by the author's own
calibrated numbers, read out of their published wheat NetCDF. Nothing is
fitted: each replaced CSV is the algebraic inverse of a published array.
The Julia source and the `Params` defaults are untouched.

Run order
---------
    # 1. dump the author arrays (needs the paper project's NCDatasets)
    cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
    arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
        --project=. /Users/mjp38/GitHub/sheaf-model/scripts/export_agrimate_baseline_arrays.jl

    # 2. build the input set
    python3 /Users/mjp38/GitHub/sheaf-model/scripts/build_agrimate_authorbase_inputs.py

    # 3. verify against the author file with a t_max = 0 run
    #    (see check_agrimate_authorbase_t0.jl)

What `simulate()` derives from which CSV
----------------------------------------
`simulate()` (src/simulation.jl 59-102) builds the whole baseline from three
quantity files plus the parameter file:

  trade-flows (country Origin/Destination/Trade Flow)
      -> aggregate_areas          : region x region off-diagonal flows
  food-balance (Consumption, Imports (harmonized/non-harmonized))
      -> infer_trade_flows        : the region's own internal flow, i.e. the
                                    diagonal, as Consumption - Imports
  both, divided by N_year         -> baseline_transactions
      -> baseline_production      = row sums   -> baseline harvest scale
      -> baseline_consumption     = column sums -> C_star
      -> sales_share_foreign_baseline, alpha_domestic, market_size,
         purchaser_share, the supplier sets, and the target of the baseline
         trade QP
  food-balance Production         -> aggregate_harvest_distributions country
                                    weights only
  harvest-distributions (365 daily shares)
      -> generate_baseline_harvests: baseline harvest (24 per producer)
  harvest-anomalies / harvest-trends
      -> harvest_forcings = 1 + anomaly/trend, both summed over the region's
         countries -> generate_forced_harvest_timeseries -> harvest (312)

Invertibility
-------------
Exactly invertible from the author's published arrays:

  * annual production per region   = sum_n `baseline harvest`
  * annual consumption per region  = sum_n `baseline demand`, rescaled by
    sum(production)/sum(demand) (the rescale factor is 1 - 5e-10 here)
  * the diagonal of the annual flow matrix = production * (1 - `baseline
    share foreign sales`)
  * `baseline harvest`  (24 x 28)  -> the daily harvest distribution
  * `harvest`           (312 x 28) -> the daily harvest forcing
  * `baseline share foreign sales` and `alpha domestic` follow from the three
    marginals above; `alpha domestic` is also an independent check on them

Over-determined / only approximately recoverable:

  * `baseline transaction quantity` (24 x 28 x 28). Its annual sums are the
    CSV-level bilateral flows in principle, but the array is the output of a
    COSMO QP solved to `baseline_tol = 1e-4` whose negative entries are then
    clipped to zero, so its marginals are off by up to 10% (demand side) and
    21% (sales side) from the exact `baseline demand` / `baseline sales`. It
    is therefore used only as the *prior* for the off-diagonal flows, which
    are then rescaled (iterative proportional fitting) onto the exact row and
    column marginals above.

Not recoverable at all:

  * the author's *pre-cutoff* trade network. `apply_cutoffs_to_trade_network`
    drops flows below `flow_cutoff = 1%` of both partners before anything is
    written out, and `aggregate_export_restrictions` reads the pre-cutoff
    network to compute each exporter's `export_fraction`. Nine of the ten
    regions the author restricted are reproduced regardless (see below), and
    three of them (Pakistan, Rest of Europe, Rest of Southern Asia) have zero
    post-cutoff foreign sales, so a 1e-6 kt pseudo-flow is added for them to
    keep their restriction rows alive. Those pseudo-flows are themselves
    removed by the cutoff and never enter the baseline.
  * `baseline price`, `baseline sales`, `baseline producer storage`,
    `baseline demand`, `baseline consumer storage`, `baseline consumption`,
    `baseline consumer price` and `baseline transaction quantity` are solver
    outputs (producer Nash equilibrium, consumer baseline fixed point,
    baseline trade QP). They cannot be set from the CSVs; they should follow
    once the inputs above match.

Construction choices
--------------------
Every region's quantities are carried by a single hub country, so that
aggregation is an identity rather than a sum. For the ten regions the author
restricted the hub is the country J9 used, so the restriction rows keep their
meaning and `export_fraction` becomes exactly 1. Middle Africa is given a
food-balance Consumption below its imports, which makes its inferred internal
flow negative; `infer_trade_flows` then skips it and the region has no
producer, as in the author's file.
"""
from __future__ import annotations

import csv
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agrimate_harvest_quadrature import (  # noqa: E402
    N_YEAR, baseline_matrix, forced_matrix, node_day_index,
)

AUTHOR = "/Users/mjp38/GitHub/agrimate-2025/j10_author_base/"
MAPFILE = "/Users/mjp38/GitHub/agrimate-2025/j8_author_params/area_region_map.csv"
ROOT = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/"
SRC = ROOT + "agrimate_input_authorrestr/"
DST = ROOT + "agrimate_input_authorbase/"
REPORT = AUTHOR + "j10_build_report.txt"

CROP = "wheat"
BASELINE = "2007-2009"
START_YEAR = 2000
T_MAX = 312
N_HOR = 24
N_STEPS = T_MAX + N_HOR                      # generate_harvests builds t_max + N_hor
LAST_FORCING_YEAR = 2014                     # columns run 2000-1 .. 2014-365
PSEUDO_FLOW = 1e-6                           # kt, removed by flow_cutoff = 1%

FB = f"food-balance_baseline={BASELINE}_crop={CROP}.csv"
TF = f"trade-flows_baseline={BASELINE}_crop={CROP}.csv"
HD = f"harvest-distributions_crop={CROP}.csv"
AN = f"harvest-anomalies_crop={CROP}_source=FAOsince-2005.csv"
TR = f"harvest-trends_crop={CROP}_source=FAOsince-2005.csv"
PA = f"parameters_baseline={BASELINE}_crop={CROP}_source=empirical.csv"
ER = f"export-restrictions_crop={CROP}_source=2007-2011.csv"

# hubs for the ten regions the author restricted; J9's choices, plus IRN for
# Rest of Southern Asia, which J9 could not restrict at all
FORCED_HUB = {
    "Ukraine": "UKR", "Argentina": "ARG", "Eastern Africa": "MUS",
    "Rest of Southern Asia": "IRN", "Kazakhstan": "KAZ", "Rest of Europe": "BLR",
    "Rest of Western Asia": "ARE", "Pakistan": "PAK", "Russia": "RUS",
    "China": "CHN",
}

log_lines: list[str] = []


def log(*args):
    line = " ".join(str(a) for a in args)
    print(line)
    log_lines.append(line)


def min_norm_nonneg(A, b, center, tol=1e-12):
    """Solve A x = b exactly with x >= 0, staying as close to `center` as possible.

    Both inversions below are wildly under-determined (24 or 336 equations
    against 365 or 336 unknowns with most of the mass free), so the issue is not
    existence but picking a solution that is non-negative and does not collapse
    onto a handful of days -- the harvest distribution's support caps what the
    forcing can later reproduce. `numpy.linalg.lstsq` returns the
    minimum-norm least-squares solution, so `center + lstsq(A, b - A @ center)`
    is the admissible point nearest `center`. Any component that still comes out
    negative is pinned at zero and the solve repeated, which keeps the equality
    constraints exact (unlike a bounded least-squares, which trades residual for
    feasibility).
    """
    n = A.shape[1]
    free = np.ones(n, dtype=bool)
    x = np.zeros(n)
    for _ in range(n):
        Af, c = A[:, free], center[free]
        corr, *_ = np.linalg.lstsq(Af, b - Af @ c, rcond=None)
        xf = c + corr
        if xf.min() >= -tol:
            x[:] = 0.0
            x[free] = np.maximum(xf, 0.0)
            return x, float(np.abs(A @ x - b).max())
        idx = np.flatnonzero(free)
        free[idx[xf < -tol]] = False
        if not free.any():
            raise RuntimeError("no admissible non-negative solution")
    raise RuntimeError("min_norm_nonneg did not converge")


# ---------------------------------------------------------------------------
# 1. author arrays
# ---------------------------------------------------------------------------
reg_tbl = pd.read_csv(AUTHOR + "baseline_region.csv")
regions = list(reg_tbl.Region)
reg_tbl = reg_tbl.set_index("Region")
step = pd.read_csv(AUTHOR + "baseline_step.csv")


def step_array(name):
    return step[step.variable == name].pivot(
        index="n", columns="Region", values="value").reindex(columns=regions)


bh_auth = step_array("baseline harvest")                 # 24 x 28
bd_auth = step_array("baseline demand")
h_auth = pd.read_csv(AUTHOR + "harvest.csv").pivot(
    index="t", columns="Region", values="value")[regions]
er_auth = pd.read_csv(AUTHOR + "export_restriction.csv").pivot(
    index="t", columns="Region", values="value")[regions].fillna(0.0)

ann = pd.read_csv(AUTHOR + "baseline_trade_annual.csv")  # Consumer, Producer, annual
obs = pd.DataFrame(np.nan, index=regions, columns=regions)   # obs[producer, consumer]
for r in ann.itertuples():
    obs.loc[r.Producer, r.Consumer] = r.annual
author_pairs = {(r.Producer, r.Consumer) for r in ann.itertuples()}
log(f"author post-cutoff network: {len(author_pairs)} (producer, consumer) pairs")

# ---------------------------------------------------------------------------
# 2. exact marginals
# ---------------------------------------------------------------------------
P = bh_auth.sum(axis=0, min_count=1)                     # annual production, kt
producers = [r for r in regions if not bh_auth[r].isna().all()]
non_producers = [r for r in regions if r not in producers]
P = P.fillna(0.0)
bd_sum = bd_auth.sum(axis=0, min_count=1).fillna(0.0)
# world production equals world consumption in the transaction matrix, so
# C_star[r] = bd_sum[r] / S with S = 24 * sum(bd) / sum(P)
C24 = bd_sum * (P.sum() / bd_sum.sum())
share_f = reg_tbl.share_foreign_sales.reindex(regions).fillna(0.0)

# `baseline share foreign sales` is stored at 4 digits, which is not tight
# enough for the regions that import nothing: there P * (1 - share) can exceed
# the region's whole consumption by a fraction of a kt. For those the exact
# identity exports = production - consumption pins the row sum instead, and the
# implied share still rounds back to the published 4 digits (asserted below).
has_exports = {r: any(p == r and c != r for (p, c) in author_pairs) for r in regions}
has_imports = {r: any(c == r and p != r for (p, c) in author_pairs) for r in regions}
row_off = pd.Series(0.0, index=regions)                  # exact off-diagonal row sums
for r in regions:
    if not has_exports[r]:
        row_off[r] = 0.0
    elif not has_imports[r]:
        row_off[r] = P[r] - C24[r]
    else:
        row_off[r] = P[r] * share_f[r]
diag = P - row_off                                       # the region's internal flow
col_off = C24 - diag                                     # exact off-diagonal col sums

log(f"world annual production  = {P.sum():,.4f} kt")
log(f"world annual consumption = {C24.sum():,.4f} kt "
    f"(rescale factor {P.sum() / bd_sum.sum():.12f})")
log(f"world international trade = {row_off.sum():,.4f} kt "
    f"(author output off-diagonal sum "
    f"{np.nansum(obs.values) - np.nansum(np.diag(obs.values)):,.4f}; the output "
    "matrix is a QP solution with its negatives clipped, so its marginals are "
    "not usable directly)")
log(f"non-producing regions: {non_producers}")
assert (row_off > -1e-9).all(), row_off[row_off <= -1e-9]
assert (col_off > -1e-9).all(), col_off[col_off <= -1e-9]
assert abs(row_off.sum() - col_off.sum()) < 1e-6
row_off, col_off = row_off.clip(lower=0.0), col_off.clip(lower=0.0)
implied = (row_off / P.replace(0.0, np.nan)).round(4).fillna(0.0)
bad = [(r, share_f[r], implied[r]) for r in producers if implied[r] != round(share_f[r], 4)]
assert not bad, f"implied share foreign sales does not round back: {bad}"
log("implied `baseline share foreign sales` rounds back to the published "
    "4 digits for every producer")

# alpha_domestic cross-check (initialization.jl 168-172)
alpha_calc = np.minimum(1.0, 3.2 * C24 * row_off / (row_off.sum() * diag.replace(0, np.nan)))
alpha_calc = alpha_calc.where((row_off > 0) & (diag > 0), 1.0)
alpha_auth = reg_tbl.alpha_domestic.reindex(regions)
amask = alpha_auth.notna()
log(f"alpha domestic check: max |calc - author| = "
    f"{(alpha_calc[amask] - alpha_auth[amask]).abs().max():.2e} over {amask.sum()} regions")

# ---------------------------------------------------------------------------
# 3. off-diagonal flow matrix: author values rescaled onto the exact marginals
# ---------------------------------------------------------------------------
sup = np.zeros((len(regions), len(regions)), dtype=bool)
prior = np.zeros_like(sup, dtype=float)
ri = {r: i for i, r in enumerate(regions)}
for (p, c) in author_pairs:
    if p == c:
        continue
    v = obs.loc[p, c]
    if np.isfinite(v) and v > 0:
        sup[ri[p], ri[c]] = True
        prior[ri[p], ri[c]] = v
# regions with no foreign sales in the author's baseline export nothing
for r in regions:
    if row_off[r] == 0.0:
        sup[ri[r], :] = False
        prior[ri[r], :] = 0.0
for r in regions:
    if col_off[r] == 0.0:
        sup[:, ri[r]] = False
        prior[:, ri[r]] = 0.0
log(f"off-diagonal support after dropping zero marginals: {sup.sum()} pairs")
for r in regions:
    if row_off[r] > 0:
        assert sup[ri[r], :].any(), f"{r} needs foreign sales but has no outbound pair"
    if col_off[r] > 0:
        assert sup[:, ri[r]].any(), f"{r} needs imports but has no inbound pair"

X = np.where(sup, prior, 0.0)
R = row_off.values
Kc = col_off.values
for it in range(20000):
    rs = X.sum(axis=1)
    X *= np.divide(R, rs, out=np.ones_like(R), where=rs > 0)[:, None]
    cs = X.sum(axis=0)
    X *= np.divide(Kc, cs, out=np.ones_like(Kc), where=cs > 0)[None, :]
    err = max(np.abs(X.sum(axis=1) - R).max(), np.abs(X.sum(axis=0) - Kc).max())
    if err < 1e-9:
        break
log(f"IPF on the off-diagonal flows: {it + 1} sweeps, max marginal error {err:.3e} kt")
assert err < 1e-6, err
OFF = pd.DataFrame(X, index=regions, columns=regions)

# ---------------------------------------------------------------------------
# 4. hubs
# ---------------------------------------------------------------------------
amap = pd.read_csv(MAPFILE)
area2reg = dict(zip(amap.Area, amap.Region))
reg2areas: dict[str, list[str]] = {}
for a, r in area2reg.items():
    reg2areas.setdefault(r, []).append(a)
assert set(reg2areas) == set(regions), set(reg2areas) ^ set(regions)

fb_src = pd.read_csv(SRC + FB)
# keep the J9 file's area order so the two input sets diff line for line
areas = list(fb_src.Area)
assert set(areas) == set(area2reg), set(areas) ^ set(area2reg)
src_prod = dict(zip(fb_src.Area, fb_src.Production))
hd_src_areas = set(pd.read_csv(SRC + HD, usecols=["Area"]).Area)
assert set(areas) == hd_src_areas, "harvest-distribution area list differs"
pa_areas = set(pd.read_csv(SRC + PA, usecols=["Area"]).Area)
assert pa_areas <= set(areas), "parameters file has areas missing from the food balance"

hub: dict[str, str] = {}
for r in regions:
    if r in FORCED_HUB:
        a = FORCED_HUB[r]
        assert area2reg[a] == r, f"{a} is not in {r}"
        hub[r] = a
    else:
        cand = sorted(reg2areas[r])
        hub[r] = max(cand, key=lambda a: (src_prod.get(a, 0.0), [-ord(ch) for ch in a]))
log("hub country per region: " + ", ".join(f"{r}={hub[r]}" for r in regions))

# ---------------------------------------------------------------------------
# 5. harvest distribution per producing region (inverts `baseline harvest`)
# ---------------------------------------------------------------------------
M = baseline_matrix()
W: dict[str, np.ndarray] = {}
dist_report = []
for r in producers:
    tau = (bh_auth[r].values / P[r])                      # sums to 1
    pos = tau > 0
    # a day may only carry mass if it contributes to no zero-harvest step
    allowed = ~(M[~pos] > 0).any(axis=0)
    Mr = M[np.ix_(pos, allowed)]
    # centre on a flat distribution over the admissible window, so the support
    # stays as wide as the author's array permits
    centre = np.full(int(allowed.sum()), tau.sum() / allowed.sum())
    w_red, resid = min_norm_nonneg(Mr, tau[pos], centre)
    w = np.zeros(365)
    w[allowed] = w_red
    W[r] = w
    got = M @ w
    got = got * P[r] / got.sum()
    dist_report.append((r, int(allowed.sum()), int((w > 0).sum()), resid,
                        float(np.abs(got - bh_auth[r].values).max())))
dr = pd.DataFrame(dist_report, columns=["region", "admissible days", "days > 0",
                                        "solve residual",
                                        "baseline harvest max abs err"])
log("\nharvest-distribution inversion:\n" + dr.to_string(index=False))
assert dr["baseline harvest max abs err"].max() < 1e-6, dr

# ---------------------------------------------------------------------------
# 6. harvest forcing per producing region (inverts `harvest`)
# ---------------------------------------------------------------------------
fcols = ([f"{y}-{d}" for y in range(START_YEAR, LAST_FORCING_YEAR)
          for d in range(1, 366)]
         + [f"{LAST_FORCING_YEAR}-{d}" for d in range(1, 366)])
n_nodes_used = (LAST_FORCING_YEAR - START_YEAR) * 365 + 1   # 2000-1 .. 2014-1
K = forced_matrix(N_STEPS, n_nodes_used)
day_idx = node_day_index(n_nodes_used)

F: dict[str, np.ndarray] = {}
force_report = []
for r in producers:
    m = P[r] * W[r][day_idx]                              # nodal mass at forcing 1
    # steps 313-336 are the N_hor tail that generate_harvests builds but the
    # output never records; they revert to the calibrated baseline
    target = np.concatenate([h_auth[r].values,
                             bh_auth[r].values[np.arange(T_MAX, N_STEPS) % N_YEAR]])
    live = m > 0                                          # a zero-mass day cannot carry forcing
    A = K[:, live] * m[live]
    # A step whose whole window has zero baseline mass cannot carry any harvest
    # at any forcing. `baseline harvest` and `harvest` are both stored at 4
    # digits, so a step that rounded to 0 in the first can still round to 1e-4
    # in the second; that is the only source of an irreducible residual here.
    unreachable = np.flatnonzero((~A.any(axis=1)) & (target != 0))
    # centre on forcing 1 (no anomaly), which is the author's own 2000-2004 state
    sol, resid = min_norm_nonneg(A, target, np.ones(int(live.sum())))
    f = np.ones(n_nodes_used)
    f[live] = sol
    F[r] = f
    got = K @ (m * f)
    force_report.append((r, resid,
                         float(np.abs(got[:T_MAX] - h_auth[r].values).max()),
                         float(f[live].min()), float(f[live].max()),
                         len(unreachable),
                         float(np.abs(target[unreachable]).max()) if len(unreachable) else 0.0))
fr = pd.DataFrame(force_report, columns=["region", "solve residual",
                                         "published 312 max abs err",
                                         "min forcing", "max forcing",
                                         "unreachable steps", "max unreachable kt"])
log("\nharvest-forcing inversion:\n" + fr.to_string(index=False))
assert fr["min forcing"].min() >= 0.0, fr
# 1e-4 kt is the output rounding of the author's own arrays, which is the floor
# that the unreachable steps above sit at
assert fr["published 312 max abs err"].max() <= 1.001e-4, fr
assert (fr["max unreachable kt"] <= 1.001e-4).all(), fr
exact = fr[fr["published 312 max abs err"] < 1e-6]
log(f"realized harvest reproduced to <1e-6 kt for {len(exact)} of {len(fr)} producers; "
    f"worst region {fr.loc[fr['published 312 max abs err'].idxmax(), 'region']} at "
    f"{fr['published 312 max abs err'].max():.1e} kt")

# ---------------------------------------------------------------------------
# 7. pseudo-flows so restricted regions keep a positive export fraction
# ---------------------------------------------------------------------------
restricted = [r for r in regions if (er_auth[r] > 0).any()]
pseudo: list[tuple[str, str]] = []                        # (origin region, dest region)
for r in restricted:
    if row_off[r] > 0:
        continue
    dest = next(c for c in regions if c != r and OFF.loc[r, c] == 0.0)
    pseudo.append((r, dest))
log(f"\nregions the author restricted: {len(restricted)}")
log(f"pseudo-export rows added (zero post-cutoff foreign sales): {pseudo}")

# ---------------------------------------------------------------------------
# 8. food balance: Consumption is chosen so that infer_trade_flows reproduces
#    the author's diagonal exactly
# ---------------------------------------------------------------------------
imports_h = OFF.sum(axis=0).copy()                        # off-diagonal inflow per region
for (o, d) in pseudo:
    imports_h[d] += PSEUDO_FLOW
cons_region = diag + imports_h                            # -> internal_flow == diag
for r in non_producers:
    # negative inferred internal flow: infer_trade_flows skips the row and the
    # region gets no producer, matching the author's file
    cons_region[r] = 0.5 * imports_h[r]
    log(f"{r}: Consumption set to {cons_region[r]:,.4f} kt against imports "
        f"{imports_h[r]:,.4f} kt so the inferred internal flow is negative")

fb_rows = []
for a in areas:
    r = area2reg[a]
    is_hub = a == hub[r]
    fb_rows.append({
        "Area": a,
        "Production": P[r] if is_hub else 0.0,
        "Consumption": cons_region[r] if is_hub else 0.0,
        "Exports (harmonized)": 0.0,
        "Imports (harmonized)": 0.0,
        "Imports (non-harmonized)": 0.0,
    })
fb_new = pd.DataFrame(fb_rows)

# ---------------------------------------------------------------------------
# 9. write
# ---------------------------------------------------------------------------
os.makedirs(DST, exist_ok=True)
shutil.copyfile(SRC + PA, DST + PA)                       # J8 author parameters, untouched

fb_new.to_csv(DST + FB, index=False, float_format="%.10g")

with open(DST + TF, "w", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["Origin", "Destination", "Trade Flow"])
    n_tf = 0
    for p in regions:
        for c in regions:
            if p == c or OFF.loc[p, c] == 0.0:
                continue
            wr.writerow([hub[p], hub[c], f"{OFF.loc[p, c]:.10g}"])
            n_tf += 1
    for (o, d) in pseudo:
        wr.writerow([hub[o], hub[d], f"{PSEUDO_FLOW:.10g}"])
        n_tf += 1
log(f"\ntrade-flows rows written: {n_tf}")

with open(DST + HD, "w", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["Area"] + [str(j) for j in range(1, 366)])
    for a in areas:
        r = area2reg[a]
        w = W[r] if (a == hub[r] and r in W) else np.zeros(365)
        wr.writerow([a] + [f"{x:.17g}" for x in w])

zero = "0.0"
for path, hubval in ((DST + AN, "anom"), (DST + TR, "trend")):
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["Area"] + fcols)
        for a in areas:
            r = area2reg[a]
            if a != hub[r] or r not in F:
                wr.writerow([a] + [zero] * len(fcols))
                continue
            if hubval == "trend":
                vals = ["1.0"] * len(fcols)
            else:
                f = F[r]
                tail = [zero] * (len(fcols) - n_nodes_used)
                vals = [f"{x - 1.0:.17g}" for x in f] + tail
            wr.writerow([a] + vals)
log(f"anomaly / trend columns written: {len(fcols)} "
    f"(2000-1 .. {LAST_FORCING_YEAR}-365; simulate() reads 2000-1 .. {LAST_FORCING_YEAR}-1)")

# ---------------------------------------------------------------------------
# 10. export restrictions: the author's series, now at export_fraction == 1
# ---------------------------------------------------------------------------
FEB29 = (2, 29)


def doy_2001(month, day):
    cum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    return cum[month - 1] + day


def date_to_timestep(d):
    y = d.year + (doy_2001(d.month, d.day) - 0.5) / 365.0
    frac = y - int(y)
    n = int(np.floor(frac * N_YEAR)) + 1
    return (int(y) - START_YEAR) * N_YEAR + n


import datetime as _dt  # noqa: E402

first_day: dict[int, _dt.date] = {}
last_day: dict[int, _dt.date] = {}
d = _dt.date(START_YEAR, 1, 1)
while d <= _dt.date(2013, 12, 31):
    if (d.month, d.day) != FEB29:
        t = date_to_timestep(d)
        first_day.setdefault(t, d)
        last_day[t] = d
    d += _dt.timedelta(days=1)

er_rows = []
er_summary = []
for r in restricted:
    v = er_auth[r].values
    runs = []
    for t in range(len(v)):
        if v[t] <= 0:
            continue
        if runs and runs[-1][1] == t and runs[-1][2] == v[t]:
            runs[-1] = (runs[-1][0], t + 1, v[t])
        else:
            runs.append((t, t + 1, v[t]))
    for (s, e, val) in runs:
        frm = first_day[s + 1]
        to = last_day[e] - _dt.timedelta(days=1)
        if (to.month, to.day) == FEB29:
            to -= _dt.timedelta(days=1)
        assert date_to_timestep(frm) == s + 1
        assert date_to_timestep(to) == e
        er_rows.append((hub[r], frm.isoformat(), to.isoformat(), repr(float(val))))
    er_summary.append((r, hub[r], float(v.max()), len(runs), int((v > 0).sum())))

with open(DST + ER, "w", newline="") as fh:
    fh.write("Exporter,From,To,Value\n")
    for row in er_rows:
        fh.write(",".join(row) + "\n")
log("\nexport restrictions (export_fraction is 1 by construction, so Value is "
    "the author's value):")
log(pd.DataFrame(er_summary, columns=["region", "hub", "author max", "rows",
                                      "steps > 0"]).to_string(index=False))

with open(DST + "README.txt", "w") as fh:
    fh.write(
        "J10 input set: the author's own calibrated wheat baseline, inverted out of\n"
        "their published NetCDF (Zenodo data v3, hindcasting_analysis/raw_data/).\n"
        "Not author input files -- the authors published output only.\n\n"
        "  parameters_*            byte copy of agrimate_input_authorparams (J8)\n"
        "  food-balance_*          region Consumption and Production from the author\n"
        "                          arrays, carried by one hub country per region\n"
        "  trade-flows_*           author off-diagonal annual flows, rescaled onto\n"
        "                          exact row/column marginals (IPF)\n"
        "  harvest-distributions_* daily shares that reproduce `baseline harvest`\n"
        "  harvest-anomalies_*     daily forcing that reproduces `harvest` (312)\n"
        "  harvest-trends_*        all ones, so forcing = 1 + anomaly\n"
        "  export-restrictions_*   the author's `export restriction` series (J9),\n"
        "                          now at export_fraction = 1\n\n"
        "Built by scripts/build_agrimate_authorbase_inputs.py in the sheaf-model\n"
        "repo. See diagnostics/gate0_julia/J10_authorbaseline.md.\n")

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    fh.write("\n".join(log_lines) + "\n")
print(f"\nwrote {DST}\nbuild report: {REPORT}")
