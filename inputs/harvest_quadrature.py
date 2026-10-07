"""Agrimate's two harvest quadratures, re-implemented as explicit linear maps.

Gate 0 J10. Both maps are taken symbol-for-symbol from
`agrimate-equal-sales-penalty/src/preprocess.jl`; nothing is approximated
except that the piecewise-linear integrals are evaluated in closed form here
where the Julia code calls `quadgk` on the same piecewise-linear interpolant
(`quadgk`'s default is `rtol = sqrt(eps)`, so the two agree to ~1e-8 relative).

Baseline path -- `generate_baseline_harvest_timeseries` (lines 256-281):

    harvest_density = LinearInterpolation(0:366,
        [w[365]; w[1:365]; w[1]])
    d = 365 / N_year
    harvests[n] = integral of harvest_density over [(n-1)d + 0.5, n*d + 0.5]
    harvests .*= production / sum(harvests)

so knot k carries w[k] for k = 1..365, knot 0 carries w[365] and knot 366
carries w[1]. `baseline_matrix()` returns M with
`harvests_unnormalised = M @ w`. Because every column of M sums to 1, solving
`M @ w == H / production` reproduces `H` after the normalisation.

Forced path -- `generate_forced_harvest_timeseries` (lines 284-318):

    n_i = mod(floor(y_timeseries[i] * 365) + 1, 1:365)
    harvest_timeseries[i] = production * harvest_distribution[n_i] * forcing[i]
    harvest_density = LinearInterpolation(y_timeseries .* 365,
        harvest_timeseries, extrapolation_bc = Line())
    harvests[t] = integral over [y0*365 + (t-1)d, y0*365 + t*d]

With `start = 2000-01-01` the run has `year_start = 2000`, `n_start = 1`,
`y0 = 2000`, and `y_timeseries` is the uniform range
`date_to_fractional_year(2000-01-01) : 1/365 : date_to_fractional_year(date_end)`.
Measuring everything in days from `y0 * 365`, node i therefore sits at
`u_i = (i - 1) + 0.5` and step t covers `[(t-1)d, t*d]`; node i carries day
`n_i = ((i - 1) mod 365) + 1`. `forced_matrix()` returns K with
`harvests = K @ g`, `g_i = production * w[n_i] * forcing_i`.

Note the half-day offset between the two paths: day j sits at x = j in the
baseline quadrature and at u = j - 0.5 in the forced one. That is why a
forcing of exactly 1 does not reproduce the baseline harvest bit for bit.
"""
from __future__ import annotations

import numpy as np

N_YEAR = 24
D_STEP = 365.0 / N_YEAR


def _cell_weights(a: float, b: float, knots: np.ndarray):
    """Integrate a piecewise-linear interpolant over [a, b].

    `knots` is a sorted array of node positions. Returns (idx, coef) such that
    the integral equals `sum(coef * values[idx])` for nodal values `values`.
    Segments outside the knot range are handled by linear extrapolation off the
    first/last cell, which is what `Interpolations.Line()` does.
    """
    idx: list[int] = []
    coef: list[float] = []
    n = len(knots)
    for k in range(n - 1):
        lo, hi = knots[k], knots[k + 1]
        # extend the first and last cells to infinity (Line() extrapolation)
        seg_lo = -np.inf if k == 0 else lo
        seg_hi = np.inf if k == n - 2 else hi
        l, r = max(a, seg_lo), min(b, seg_hi)
        if r <= l:
            continue
        h = hi - lo
        mid = 0.5 * (l + r)
        s = (mid - lo) / h          # fractional position of the midpoint in the cell
        idx.extend((k, k + 1))
        coef.extend(((r - l) * (1.0 - s), (r - l) * s))
    return np.array(idx, dtype=int), np.array(coef, dtype=float)


def baseline_matrix() -> np.ndarray:
    """M (N_YEAR x 365) with `generate_baseline_harvest_timeseries` = M @ w."""
    knots = np.arange(0, 367, dtype=float)
    # knot k -> index into w (0-based): 0 -> 364, k -> k-1, 366 -> 0
    kmap = np.empty(367, dtype=int)
    kmap[0] = 364
    kmap[1:366] = np.arange(365)
    kmap[366] = 0
    M = np.zeros((N_YEAR, 365))
    for n in range(N_YEAR):
        a = n * D_STEP + 0.5
        b = (n + 1) * D_STEP + 0.5
        idx, coef = _cell_weights(a, b, knots)
        np.add.at(M[n], kmap[idx], coef)
    return M


def forced_matrix(n_steps: int, n_nodes: int):
    """K (n_steps x n_nodes) with `generate_forced_harvest_timeseries` = K @ g.

    `g_i = production * harvest_distribution[n_i] * forcing_i`. Returned as a
    dense array; n_steps x n_nodes is 336 x 5111 at the J10 settings.
    """
    knots = 0.5 + np.arange(n_nodes, dtype=float)
    K = np.zeros((n_steps, n_nodes))
    for t in range(n_steps):
        a = t * D_STEP
        b = (t + 1) * D_STEP
        idx, coef = _cell_weights(a, b, knots)
        np.add.at(K[t], idx, coef)
    return K


def node_day_index(n_nodes: int) -> np.ndarray:
    """0-based day-of-year index carried by each node of the forced path."""
    return np.arange(n_nodes) % 365
