#!/usr/bin/env python3
"""R3-01: how far ahead does Gate 0's lean-gap look, and with what information?

Question (a) of the R3 red-team brief: does any Gate 0 decision use
information it should not have?

Gate 0 builds ONE expected-harvest array before the time loop
(`_simulate_window`, L577-586):

    H_exp = phi * H + (1 - phi) * H_seasonal          # phi constant in lag
    lean_h  = steps_to_harvest_pulse(H_exp, ...)      # (T,) horizon
    H_ahead = rolling_ahead_variable(H_exp, lean_h)   # sum over t+1..t+h_t

So at step t the lean gap sees `phi` of the REALISED harvest at every lag
k = 1..h_t. Agrimate (Kuhla 2025, supplement Eq. D.1) does the same thing
but with a lag-DECAYING weight:

    w_n = 1 / (1 + exp((n - N_for) / (0.17 * tau_for)))
    Hhat^(t+n) = w_n * H^(t+n) + (1 - w_n) * H*^(t+n)

with N_for = N_year/3 = 6 and tau_for = 0.2 * N_year = 4.8 steps
(supplement Tbl. D.1, Tbl. F.1). So Agrimate's weight on the realised
future harvest is ~1.00 at n=1..4, 0.50 at n=6, ~0.02 at n=9, ~0 beyond.

This script measures the realised h_t distribution and the resulting
lag-weight comparison, so the (a) verdict is a number, not an opinion.

Read-only w.r.t. sheaf/*.py: the module is recompiled in memory.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import default_crop_params  # noqa: E402

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"
OUT = ROOT / "diagnostics" / "redteam" / "r3"

# Agrimate supplement Tbl. D.1 / Tbl. F.1 defaults, N_year = 24 (same clock).
AGRI_NFOR = 6.0
AGRI_TAUFOR = 0.2 * 24.0


def agri_w(n: np.ndarray | float) -> np.ndarray:
    """Agrimate Eq. (D.1a) weight on the ACCURATE (realised) harvest forecast."""
    n = np.asarray(n, float)
    return 1.0 / (1.0 + np.exp((n - AGRI_NFOR) / (0.17 * AGRI_TAUFOR)))


PROBE_AT = "    elast = params.elast"
PROBE = """    _DIAG.append(dict(lean_h=np.array(lean_h, dtype=int).copy(),
                      H=H.copy(), H_seas=(None if H_seasonal is None
                                          else H_seasonal.copy()),
                      H_exp=H_exp.copy(), C_step=C_step.copy(),
                      H_ahead=H_ahead.copy(), C_ahead=C_ahead.copy()))
    elast = params.elast"""


def build_probe():
    src = SRC.read_text()
    assert src.count(PROBE_AT) == 1
    src = src.replace(PROBE_AT, PROBE)
    mod = types.ModuleType("sheaf.dc_r3_probe")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_DIAG"] = []
    sys.modules["sheaf.dc_r3_probe"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


P1 = dict(use_amis=True, use_shocks=True, use_demand=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mod = build_probe()
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# R3-01 - Gate 0 look-ahead horizon and information content\n")
    out("Agrimate reference (supplement Eq. D.1, Tbl. D.1, Tbl. F.1): "
        f"N_year=24, N_for={AGRI_NFOR:.0f}, tau_for={AGRI_TAUFOR:.1f} steps.\n")
    out("Weight Agrimate puts on the REALISED future harvest by lag n:\n")
    ns = np.arange(0, 25)
    w = agri_w(ns)
    out("| lag n (steps) | " + " | ".join(f"{k}" for k in ns[::2]) + " |")
    out("|---|" + "---|" * len(ns[::2]))
    out("| Agrimate w_n | " + " | ".join(f"{v:.3f}" for v in w[::2]) + " |\n")

    rows = []
    lag_rows = []
    for crop in CROPS:
        mod.__dict__["_DIAG"].clear()
        res = mod.run_crop_dynamics(crop, **P1)
        # prepare_crop_run runs a spin-up pass and a twin pass first; the
        # treatment pass is last.
        d = mod.__dict__["_DIAG"][-1]
        T = len(res.price)
        assert d["H"].shape[1] == T, (d["H"].shape, T)
        h = d["lean_h"]
        phi = default_crop_params(crop).foresight_phi
        H, Hs, Hexp = d["H"], d["H_seas"], d["H_exp"]

        # How much of the forward window sits beyond Agrimate's forecast reach?
        beyond = np.array([(np.arange(1, hh + 1) > 8).sum() for hh in h])
        out(f"## {crop}  (phi = {phi:.2f})\n")
        out(f"- lean horizon h_t over T={T} steps: min {h.min()}, "
            f"median {int(np.median(h))}, mean {h.mean():.2f}, max {h.max()}")
        share_gt6 = float((h > 6).mean())
        share_gt9 = float((h > 9).mean())
        out(f"- share of steps with h_t > 6 (Agrimate N_for): {share_gt6:.1%}")
        out(f"- share of steps with h_t > 9 (Agrimate w<0.03): {share_gt9:.1%}")
        out(f"- mean number of forward lags per step beyond n=8: {beyond.mean():.2f}")

        # Information actually used: realised-vs-climatology harvest gap that
        # SHEAF reads at each lag, weighted by phi, versus Agrimate's w_n.
        dH = H - Hs  # realised anomaly in MMT/step
        sheaf_info = np.zeros(T)
        agri_info = np.zeros(T)
        for t in range(T):
            hh = int(h[t])
            k = np.arange(1, hh + 1)
            k = k[t + k < T]
            if len(k) == 0:
                continue
            g = dH[:, t + k].sum(axis=0)  # world anomaly at each forward lag
            sheaf_info[t] = float(np.abs(phi * g).sum())
            agri_info[t] = float(np.abs(agri_w(k) * g).sum())
        out(f"- |realised-anomaly information| inside the forward window, "
            f"MMT-equivalent per step:")
        out(f"    SHEAF (flat phi)      mean {sheaf_info.mean():7.3f}")
        out(f"    Agrimate (decaying w) mean {agri_info.mean():7.3f}")
        ratio = sheaf_info.mean() / max(agri_info.mean(), 1e-12)
        out(f"    ratio SHEAF/Agrimate  x{ratio:.3f}")

        # lag-0 coherence check: avail uses H_t at weight 1, lean gap at phi.
        lag0 = float(np.abs((1.0 - phi) * dH).sum(axis=0).mean())
        out(f"- lag-0 incoherence: avail_t uses H_t at weight 1.00 but the "
            f"lean gap subtracts H_exp_t = phi*H_t + (1-phi)*H_seas_t; "
            f"mean |(1-phi)*(H_t - H_seas_t)| = {lag0:.3f} MMT/step\n")

        rows.append(dict(crop=crop, phi=phi, T=T,
                         h_min=int(h.min()), h_med=int(np.median(h)),
                         h_mean=float(h.mean()), h_max=int(h.max()),
                         share_h_gt6=share_gt6, share_h_gt9=share_gt9,
                         mean_lags_beyond_8=float(beyond.mean()),
                         sheaf_info_mmt=float(sheaf_info.mean()),
                         agri_info_mmt=float(agri_info.mean()),
                         info_ratio=float(ratio),
                         lag0_incoherence_mmt=lag0))
        for k in range(0, 25):
            lag_rows.append(dict(crop=crop, lag=k,
                                 sheaf_weight=(1.0 if k == 0 else phi),
                                 agrimate_weight=float(agri_w(k)),
                                 share_steps_window_reaches_lag=float(
                                     (h >= k).mean()) if k > 0 else 1.0))

    pd.DataFrame(rows).to_csv(OUT / "r3_lookahead_summary.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(OUT / "r3_lookahead_lagweights.csv",
                                  index=False)
    (OUT / "R3_01_LOOKAHEAD.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT / 'R3_01_LOOKAHEAD.md'}")


if __name__ == "__main__":
    main()
