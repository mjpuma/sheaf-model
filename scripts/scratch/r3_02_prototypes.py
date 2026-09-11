#!/usr/bin/env python3
"""R3-02: prototype the expectation / scheduling fixes and score them.

Variants (all by in-memory recompilation; sheaf/*.py untouched):

  V0  baseline as shipped.
  V1  Agrimate Eq. (D.1) lag-decaying harvest expectation replacing the flat
      `foresight_phi` blend. Weight on the realised future harvest is
      w_k = 1/(1+exp((k - N_for)/(0.17 tau_for))) with N_for = N_year/3 = 6 and
      tau_for = 0.2 N_year = 4.8 (supplement Tbl. D.1 / F.1, N_year = 24 = the
      SHEAF clock). Applies to the pulse clock, the forward window, AND the
      lag-0 term, so the current step's harvest enters the lean gap at the
      same weight (w_0 = 0.9993) at which it already enters `avail`.
  V2  lag-0 coherence only: keep flat phi for the forward window but subtract
      the full realised H_t at lag 0. Isolates the within-step incoherence.
  V3  ask-timing parity: p^tr is computed from the PRE-update ask, i.e. the
      same ask that generated the allocation. README section 8 writes
      p^tr_t = sum_i q_{i,t} ship_{i,t} / sum_i ship_{i,t} while step 5 of
      "Method of solution" produces q_{i,t+1}; the code uses q_{i,t+1}.
      Agrimate Eq. (D.4): p^(t)_{r->s} = p^(t-1)_{off,r->s}.
  V4  restriction-duration knowledge: the preferred-block signal weights each
      in-force cut by min(1, (m+1)/N_for) where m is the known remaining
      length of the current restriction phase (Agrimate Eq. D.2 rule), so a
      one-step measure and a year-long ban of equal severity are no longer
      the same signal. N_for = 6 is imported, not fitted.
  V13 V1 + V3.

Scored with `_corr` / `_hike` imported from scripts/score_subannual_crop.py
and the four robustness asserts run per variant.
"""
from __future__ import annotations

import sys
import traceback
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from score_subannual_crop import _corr, _hike  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"
OUT = ROOT / "diagnostics" / "redteam" / "r3"

P1 = dict(use_amis=True, use_shocks=True, use_demand=False)

# ---------------------------------------------------------------- source edits

EXP_ORIG = """    if H_seasonal is None:
        H_exp = H
    else:
        H_exp = (params.foresight_phi * H
                 + (1.0 - params.foresight_phi) * H_seasonal)

    lean_h = steps_to_harvest_pulse(
        H_exp, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)"""

EXP_AGRI = """    _NFOR, _TAUFOR = 6.0, 4.8
    _Hs = H if H_seasonal is None else H_seasonal
    _kk = np.arange(0, MAX_LEAN_STEPS + 1, dtype=float)
    _w = 1.0 / (1.0 + np.exp((_kk - _NFOR) / (0.17 * _TAUFOR)))
    H_exp = _w[0] * H + (1.0 - _w[0]) * _Hs
    _wh = H.sum(axis=0)
    _ws = _Hs.sum(axis=0)
    _nyr = max(T // STEPS_PER_YEAR, 1)
    _thresh = max(params.harvest_pulse_frac
                  * float(_wh[: _nyr * STEPS_PER_YEAR].sum()) / _nyr, 1e-6)
    lean_h = np.full(T, MAX_LEAN_STEPS, dtype=int)
    for _t in range(T):
        _acc = 0.0
        for _k in range(1, MAX_LEAN_STEPS + 1):
            if _t + _k >= T:
                lean_h[_t] = max(_k - 1, 1)
                break
            _acc += _w[_k] * _wh[_t + _k] + (1.0 - _w[_k]) * _ws[_t + _k]
            if _acc >= _thresh:
                lean_h[_t] = _k
                break
    H_ahead = np.zeros((n, T))
    for _t in range(T):
        for _k in range(1, int(lean_h[_t]) + 1):
            if _t + _k >= T:
                break
            H_ahead[:, _t] += (_w[_k] * H[:, _t + _k]
                               + (1.0 - _w[_k]) * _Hs[:, _t + _k])
    C_ahead = rolling_ahead_variable(C_step, lean_h)"""

LEAN_ORIG = """            C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t],"""
LEAN_LAG0 = """            C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H[:, t],"""

PT_ORIG = """            p_trade = float(np.dot(ask, shipped) / shipped_sum)"""
PT_PRE = """            p_trade = float(np.dot(ask_path[:, t], shipped) / shipped_sum)"""

BLOCK_ORIG = """        preferred_block = float(
            (S * cuts[:, t][:, None] * demand[None, :]).sum())"""
BLOCK_DUR = """        _dw = _duration_weight(cuts, t, 6)
        preferred_block = float(
            (S * (cuts[:, t] * _dw)[:, None] * demand[None, :]).sum())"""

DUR_HELPER = '''

def _duration_weight(cuts: np.ndarray, t: int, n_for: int = 6) -> np.ndarray:
    """Agrimate Eq. (D.2): known remaining length of the current cut phase.

    Returns min(1, (m+1)/n_for) per exporter, where m is the number of
    consecutive future steps carrying exactly the current cut level. Zero
    where no cut is in force. No free parameter: n_for is Agrimate's
    N_for = N_year/3 = 6.
    """
    n, T = cuts.shape
    out = np.zeros(n)
    for i in range(n):
        c = cuts[i, t]
        if c <= 0.0:
            continue
        m = 0
        while t + m + 1 < T and cuts[i, t + m + 1] == c and m + 1 <= n_for:
            m += 1
        out[i] = min(1.0, (m + 1.0) / float(n_for))
    return out
'''

MARK = "\ndef _simulate_window("


def build(name: str, *, agri_exp=False, lag0=False, pre_ask=False,
          duration=False):
    src = SRC.read_text()
    if agri_exp:
        assert src.count(EXP_ORIG) == 1
        src = src.replace(EXP_ORIG, EXP_AGRI)
        assert src.count(LEAN_ORIG) == 1
        src = src.replace(LEAN_ORIG, LEAN_LAG0)
    elif lag0:
        assert src.count(LEAN_ORIG) == 1
        src = src.replace(LEAN_ORIG, LEAN_LAG0)
    if pre_ask:
        assert src.count(PT_ORIG) == 1
        src = src.replace(PT_ORIG, PT_PRE)
    if duration:
        assert src.count(BLOCK_ORIG) == 1
        src = src.replace(BLOCK_ORIG, BLOCK_DUR)
        assert src.count(MARK) == 1
        src = src.replace(MARK, DUR_HELPER + MARK)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


VARIANTS = {
    "V0_baseline": {},
    "V1_agrimate_exp": dict(agri_exp=True),
    "V2_lag0_only": dict(lag0=True),
    "V3_pre_update_ask": dict(pre_ask=True),
    "V4_cut_duration": dict(duration=True),
    "V13_agri_exp+pre_ask": dict(agri_exp=True, pre_ask=True),
}

ASSERTS = ("assert_twin_identity", "assert_amis_raises_price",
           "assert_amis_cuts_exports", "assert_no_spring_spike")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obs_all = load_price_series_monthly(deflated=True)
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# R3-02 - prototype scores and assertion impact\n")
    out("Baselines to validate the harness against (from the brief): "
        "wheat +0.720 / x2.27 / x1.45, maize +0.712 / x1.97 / x1.70, "
        "rice +0.678 / x1.72 / x0.82.\n")

    score_rows, assert_rows = [], []
    for vname, kw in VARIANTS.items():
        mod = build(f"dc_r3_{vname.split('_')[0].lower()}", **kw)
        out(f"## {vname}\n")
        out("| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |")
        out("|---|---|---|---|---|---|")
        for crop in CROPS:
            obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
                ["year", "month", crop]].rename(columns={crop: "obs_price"})
            res = mod.run_crop_dynamics(crop, **P1)
            m = mod.result_to_monthly(res).merge(obs, on=["year", "month"],
                                                 how="left")
            c = _corr(m.model_price, m.obs_price)
            h07 = _hike(m, "model_price", 2006, 6, 2008, 3)
            h10 = _hike(m, "model_price", 2009, 6, 2011, 2)
            o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
            o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
            out(f"| {crop} | {c:+.3f} | x{h07:.2f} | x{h10:.2f} | "
                f"x{o07:.2f} | x{o10:.2f} |")
            score_rows.append(dict(variant=vname, crop=crop, corr=c,
                                   hike_0708=h07, hike_1011=h10,
                                   obs_0708=o07, obs_1011=o10))
        out("")
        out("| crop | " + " | ".join(a.replace("assert_", "")
                                     for a in ASSERTS) + " |")
        out("|---|" + "---|" * len(ASSERTS))
        for crop in CROPS:
            cells = []
            for a in ASSERTS:
                try:
                    getattr(mod, a)(crop)
                    cells.append("PASS")
                    ok, msg = True, ""
                except AssertionError as e:
                    cells.append("**FAIL**")
                    ok, msg = False, str(e)
                except Exception as e:  # noqa: BLE001
                    cells.append("ERROR")
                    ok, msg = False, f"{type(e).__name__}: {e}"
                    traceback.print_exc()
                assert_rows.append(dict(variant=vname, crop=crop, check=a,
                                        passed=ok, message=msg))
            out(f"| {crop} | " + " | ".join(cells) + " |")
        out("")
        for r in assert_rows:
            if r["variant"] == vname and not r["passed"]:
                out(f"- {r['crop']} `{r['check']}`: {r['message']}")
        out("")

    sc = pd.DataFrame(score_rows)
    sc.to_csv(OUT / "r3_prototype_scores.csv", index=False)
    pd.DataFrame(assert_rows).to_csv(OUT / "r3_prototype_asserts.csv",
                                     index=False)

    out("## Deltas vs V0\n")
    base = sc[sc.variant == "V0_baseline"].set_index("crop")
    out("| variant | crop | d corr | d 2007/08 | d 2010/11 |")
    out("|---|---|---|---|---|")
    for vname in VARIANTS:
        if vname == "V0_baseline":
            continue
        for crop in CROPS:
            r = sc[(sc.variant == vname) & (sc.crop == crop)].iloc[0]
            b = base.loc[crop]
            out(f"| {vname} | {crop} | {r['corr'] - b['corr']:+.3f} | "
                f"{r['hike_0708'] - b['hike_0708']:+.2f} | "
                f"{r['hike_1011'] - b['hike_1011']:+.2f} |")
    out("")

    (OUT / "R3_02_PROTOTYPES.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT / 'R3_02_PROTOTYPES.md'}")


if __name__ == "__main__":
    main()
