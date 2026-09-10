#!/usr/bin/env python3
"""R1 red-team: Agrimate-style supplier FOC as an in-memory patch of Gate 0.

Read-only with respect to ``sheaf/*.py`` and ``scripts/*.py``: the module
source is recompiled in memory with string replacements applied, following
the technique in ``scripts/scratch/a1_equation_audit.py`` and
``scripts/scratch/a1b_calm_fixed_point.py``.

What the patch can replace
--------------------------
Gate 0 as shipped (``sheaf/dynamic_crop.py``):

    offers = max(0, avail - desired - target) * (1 - cut)            # L611
    ask   *= exp(a*(fill - theta) + rival); ask = (1-b)*ask + b*p    # L647-651

R1 replacements, independently switchable:

``R1["foc"]``  -- exporter store-vs-sell problem (Agrimate Eqs (1a)/(1b), (2);
Suppl. D.12-D.19), with rho = delta = 0 (Agrimate defaults, Tbl. D.8) and a
two-block sales plan over the lean horizon L = lean_h[t]:

    x_i = argmax_{0<=x<=xbar_i}  P_i(x)*x + L*P_i(y)*y + p_sto*(L+1)/2 * x
          with y = (xbar_i - x)/L
    xbar_i = max(0, avail - desired - target)   (== the shipped Gate 0 offer)

``R1["ask_law"]`` -- offer price.  ``"foc"`` makes it the inverse-demand
object of Agrimate Eq (5)/(D.24):

    ask_i = P_i(X_i + Q_oth_i),  P_i(u) = p0 * (u / X*)^(-alpha)

where X_i is either the exporter's post-restriction offer (``price_at =
"offers"``, closest to Agrimate's *planned sales*) or its realised shipment
(``price_at = "exports"``), Q_oth_i is an adaptive expectation of rivals'
international supply (Agrimate D.22, timescale tau_exp), and X* is a
reference sales level -- either a scalar year-average (Agrimate's X*_I,
``ref_mode = "scalar"``) or a 24-step seasonal path (``"season"``).
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")

# Agrimate Suppl. Tbl. D.8 (L2665-2720) + Sec. F per-crop notes (L4624/L4695).
# alpha_I = inverse price elasticity of international demand.
#   wheat 3.5 (Tbl D.8; Sec. F quotes "the default alpha_I = 3.2" for the same
#   parameter -- the paper is internally inconsistent, see R1_REPORT.md),
#   maize 2.7, rice 2.2.
ALPHA_I = {"wheat": 3.5, "maize": 2.7, "rice": 2.2}
# p_sto = 0.1 / N_year US$/tonne, "relative to commodity price" (Tbl D.8).
PSTO_REL = 0.1 / 24.0
# tau_exp = 0.5 * N_year (Tbl D.8); rho = 0, delta = 0 (Tbl D.8) -- confirmed.
TAU_EXP = 12.0

CALM_KW = dict(use_amis=False, use_shocks=False, use_demand=False,
               use_industrial=False)
FULL_KW = dict(use_amis=True, use_shocks=True, use_demand=False)


# --------------------------------------------------------------------------
# source patches
# --------------------------------------------------------------------------
CALM_ORIG = """            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:"""
CALM_OFF = """            calm = False
            if calm:
                p_star = p0
            else:"""

OFFER_ORIG = """        demand = food_need + rebuild
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts[:, t])
        offer_path[:, t] = offers"""
OFFER_R1 = """        demand = food_need + rebuild
        # --- R1: exporter problem (Agrimate Eqs 1a/1b, 2; Suppl. D.12-D.19)
        _xbar = np.maximum(0.0, avail - desired - target)
        _L = float(max(1, int(lean_h[t])))
        _sy = t % STEPS_PER_YEAR
        _Rref = _r1_ref(_R1, "xstar", _sy)
        _xrf = _r1_ref(_R1, "xref", _sy)
        if t == 0:
            _q_oth = np.maximum(_Rref - _xrf, 1e-9)
        if _R1.get("foc"):
            _xopt, _corner = _r1_solve(
                _xbar, _q_oth, _L, _Rref, p0,
                float(_R1["alpha"]), float(_R1["psto"]) * p0)
        else:
            _xopt, _corner = _xbar, 1.0
        offers = _xopt * (1.0 - cuts[:, t])
        _R1.setdefault("_trace", []).append(
            (float(_xbar.sum()), float(_xopt.sum()), float(_corner)))
        offer_path[:, t] = offers"""

ASK_ORIG = """        fill = shipped / np.maximum(offers, 1e-9)
        fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
        total_d = float(demand.sum())
        preferred_block = float(
            (S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)
        rival = float(max(params.ask_rival, 0.0)) * block_frac
        ask = ask * np.exp(
            params.ask_alpha * (fill - params.ask_target_fill)
            + np.where(offers > 1e-9, rival, 0.0))
        ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)"""
ASK_R1 = """        total_d = float(demand.sum())
        preferred_block = float(
            (S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)
        if str(_R1.get("ask_law", "foc")) == "foc":
            # --- R1: offer price = inverse demand at chosen sales
            #     (Agrimate Eq 5 / Suppl. D.24 with Eq D.9, lambda = 0)
            _Xi = offers if str(_R1["price_at"]) == "offers" else shipped
            _ask_raw = p0 * (np.maximum(_Xi + _q_oth, 1e-12)
                             / max(_Rref, 1e-9)) ** (-float(_R1["alpha"]))
            _lo, _hi = 0.45 * p0, 2.8 * p0
            _R1.setdefault("_clip", []).append(
                float(np.mean((_ask_raw < _lo) | (_ask_raw > _hi))))
            ask = np.clip(_ask_raw, _lo, _hi)
            _w = 1.0 / float(_R1["tau_exp"])
            _tot = float(_Xi.sum())
            if str(_R1["rival_mode"]) == "ref":
                _q_oth = np.maximum(_Rref - _xrf, 1e-9)
            else:
                _q_oth = np.maximum(
                    (1.0 - _w) * _q_oth + _w * np.maximum(_tot - _Xi, 0.0),
                    1e-9)
        else:
            fill = shipped / np.maximum(offers, 1e-9)
            fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
            rival = float(max(params.ask_rival, 0.0)) * block_frac
            ask = ask * np.exp(
                params.ask_alpha * (fill - params.ask_target_fill)
                + np.where(offers > 1e-9, rival, 0.0))
            ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
            ask = np.clip(ask, 0.45 * p0, 2.8 * p0)"""

PROBE_AT = "        p = float(smooth * p + (1.0 - smooth) * p_star)"
PROBE = """        _R1.setdefault("_px", []).append(
            (float(p_trade), float(p_star), float(block_frac)))
        p = float(smooth * p + (1.0 - smooth) * p_star)"""


# --------------------------------------------------------------------------
# helpers injected into the recompiled module
# --------------------------------------------------------------------------
def _r1_ref(R1, key, sy):
    a = np.asarray(R1[key], float)
    if a.ndim == 0:
        return float(a)
    if a.ndim == 1:
        if key == "xstar":
            return float(a[sy % a.shape[0]])
        return a
    return a[:, sy % a.shape[1]]


def _r1_profit(x, xbar, Q, L, Rref, p0, alpha, k):
    """Agrimate Eq (2) / Suppl. D.18 with rho = delta = 0, two sales blocks."""
    p_now = p0 * (np.maximum(x + Q, 1e-12) / Rref) ** (-alpha)
    y = np.maximum(xbar - x, 0.0) / L
    p_fut = p0 * (np.maximum(y + Q, 1e-12) / Rref) ** (-alpha)
    return p_now * x + L * p_fut * y + k * x


def _r1_solve(xbar, q_oth, L, Rref, p0, alpha, psto,
              ngrid: int = 33, nref: int = 40):
    """argmax of Eq (2) over [0, xbar]; returns (x, corner_fraction).

    Global search (grid + golden section), not a root find: the objective is
    not globally concave -- the linear storage-cost saving p_sto*(L+1)/2 * x
    dominates the isoelastic revenue term at large x, so the derivative
    changes sign twice.  See the falsification section of R1_REPORT.md.
    """
    n = xbar.shape[0]
    Q = np.maximum(np.asarray(q_oth, float), 1e-9)
    Rref = max(float(Rref), 1e-9)
    k = float(psto) * (L + 1.0) / 2.0

    def f(x):
        return _r1_profit(x, xbar, Q, L, Rref, p0, alpha, k)

    frac = np.linspace(0.0, 1.0, ngrid)
    vals = np.empty((n, ngrid))
    for j in range(ngrid):
        vals[:, j] = f(frac[j] * xbar)
    j = np.argmax(vals, axis=1)
    step = xbar / (ngrid - 1)
    x0 = frac[j] * xbar
    a = np.maximum(0.0, x0 - step)
    b = np.minimum(xbar, x0 + step)
    gr = 0.6180339887498949
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(nref):
        m = fc > fd
        b = np.where(m, d, b)
        a = np.where(m, a, c)
        c, d = b - gr * (b - a), a + gr * (b - a)
        fc, fd = f(c), f(d)
    x = np.clip(0.5 * (a + b), 0.0, xbar)
    pos = xbar > 1e-9
    corner = (float(np.mean(x[pos] > 0.999 * xbar[pos])) if np.any(pos)
              else 1.0)
    return x, corner


# --------------------------------------------------------------------------
# module builder
# --------------------------------------------------------------------------
_N = 0


def build(calm: bool = True, r1: bool = False, R1: dict | None = None,
          probe: bool = False):
    """Recompile ``sheaf.dynamic_crop`` in memory with the R1 patches."""
    global _N
    _N += 1
    name = f"r1_dc_{_N}"
    src = SRC.read_text()
    if not calm:
        assert CALM_ORIG in src
        src = src.replace(CALM_ORIG, CALM_OFF)
    if r1:
        assert OFFER_ORIG in src and ASK_ORIG in src
        src = src.replace(OFFER_ORIG, OFFER_R1)
        src = src.replace(ASK_ORIG, ASK_R1)
    if probe:
        src = src.replace(PROBE_AT, PROBE)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_R1"] = {} if R1 is None else R1
    mod.__dict__["_r1_ref"] = _r1_ref
    mod.__dict__["_r1_solve"] = _r1_solve
    mod.__dict__["_r1_profit"] = _r1_profit
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def default_R1(crop: str, **kw) -> dict:
    R1 = dict(alpha=ALPHA_I[crop], psto=PSTO_REL, tau_exp=TAU_EXP,
              rival_mode="ewma", ask_law="foc", price_at="offers",
              foc=True, ref_mode="scalar", xstar=1.0, xref=1.0)
    R1.update(kw)
    return R1


def refs_from(q: np.ndarray, mode: str = "scalar"):
    """Reference sales levels X* (world) and x*_i (own) from a calm path."""
    n, T = q.shape
    ny = max(T // 24, 1)
    blk = q[:, : ny * 24].reshape(n, ny, 24)
    xref_s = blk.mean(axis=1)                       # (n, 24)
    if mode == "season":
        return xref_s.sum(axis=0), xref_s
    xref = xref_s.mean(axis=1)                      # (n,)
    return float(xref.sum()), xref


def priced_q(res, price_at: str) -> np.ndarray:
    return res.offers if price_at == "offers" else res.exports


def calibrate_refs(crop: str, R1: dict, mech, r1_on, iters: int = 6,
                   verbose: bool = False):
    """Fixed point for X* under the R1 law itself.

    Agrimate builds its Nash baseline quasi-analytically (Suppl. D.7.4);
    the same job is done here by iterating the calm-path reference until the
    R1 law reproduces it.  The calm branch is ON during calibration, so the
    price is pinned at p0 and X* is a pure quantity object -- no crisis
    window enters.
    """
    mode = str(R1.get("ref_mode", "scalar"))
    res = mech.run_crop_dynamics(crop, **CALM_KW)
    xs, xr = refs_from(priced_q(res, str(R1["price_at"])), mode)
    hist = [float(np.mean(xs))]
    for _ in range(iters):
        R1["xstar"], R1["xref"] = xs, xr
        res = r1_on.run_crop_dynamics(crop, **CALM_KW)
        xs, xr = refs_from(priced_q(res, str(R1["price_at"])), mode)
        hist.append(float(np.mean(xs)))
    R1["xstar"], R1["xref"] = xs, xr
    if verbose:
        print(f"  {crop}: X* iterations {['%.4g' % h for h in hist]}")
    return hist


def drift(price: np.ndarray, p0: float) -> tuple[float, float, float]:
    """(max |p-p0|/p0, |mean p - p0|/p0, (max-min)/p0) after year 1."""
    from sheaf.calendar24 import STEPS_PER_YEAR
    tail = np.asarray(price, float)[STEPS_PER_YEAR:]
    return (float(np.max(np.abs(tail - p0)) / p0),
            float(abs(np.mean(tail) - p0) / p0),
            float((np.max(tail) - np.min(tail)) / p0))
