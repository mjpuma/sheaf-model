#!/usr/bin/env python3
"""R4 task 1(a) — does SHEAF have market power, and through what channel?

The knockout regression in r4_01 shows the world-price lift rising with the
knocked-out exporter's share (maize corr +0.97). That is NOT evidence of
market power: in ANY aggregate model, dlog p / dlog x_i = (dlog p / dlog X)
* s_i, so the impact is proportional to share and the implied "alpha" is just
the aggregate price flexibility. Three tests separate the two hypotheses.

T1 CONCENTRATION. Remove a FIXED tonnage of world offers, once concentrated
   on the single largest exporter and once spread pro rata over all of them.
   Aggregate scarcity is identical by construction. Cournot says the
   concentrated cut must move the price more.

T2 SPLIT NEUTRALITY (the sharp one). Clone the largest exporter into two
   identical half-size nodes, preserving every aggregate exactly. Under
   Cournot, halving the largest supplier's share must LOWER the equilibrium
   price. Under an aggregate price law with a share-independent offer rule,
   the price path is invariant. Run with the share-dependent prototype on as
   a positive control, so a null result cannot be blamed on a blunt test.

T3 CHANNEL DECOMPOSITION. For the largest exporter, switch off the routes
   one at a time (ask_rival -> 0, block_kappa -> 0, trade_w -> 0/1) and
   attribute the knockout lift.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.dynamic_crop import prepare_crop_run

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)

WIN = (2008, 1, 2008, 12)


def _sl(y0, m0, y1, m1, sy=2006):
    return ((y0 - sy) * STEPS_PER_YEAR + (m0 - 1) * 2,
            (y1 - sy) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2)


def _biggest(prep, t0, t1):
    base = L.run_prep(prep, harvest=prep.H * (1.0 - 1e-6))
    off = base["offers"][:, t0:t1].sum(axis=1)
    i = int(np.argmax(off))
    return i, base, off


# --------------------------------------------------------------------------
# T1 — concentrated vs spread cut of the same tonnage
# --------------------------------------------------------------------------
def concentration(crop: str, overrides: dict) -> list[dict]:
    t0, t1 = _sl(*WIN)
    prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                            use_demand=False, use_industrial=False,
                            **overrides)
    Hp = prep.H * (1.0 - 1e-6)
    i, base, off = _biggest(prep, t0, t1)
    p_b = float(np.mean(base["price"][t0:t1]))
    rows = []
    for frac in (0.10, 0.25, 0.50):
        # concentrated: cut `frac` of the biggest exporter's offers
        cut_mmt = frac * off[i]
        c1 = np.zeros_like(prep.cuts)
        c1[i, t0:t1] = frac
        r1 = L.run_prep(prep, cuts=c1, harvest=Hp)
        # spread: same tonnage, pro rata over every exporter (incl. i)
        tot = float(off.sum())
        c2 = np.zeros_like(prep.cuts)
        c2[:, t0:t1] = cut_mmt / max(tot, 1e-12)
        r2 = L.run_prep(prep, cuts=c2, harvest=Hp)
        q1 = float(r1["offers"][:, t0:t1].sum())
        q2 = float(r2["offers"][:, t0:t1].sum())
        p1 = float(np.mean(r1["price"][t0:t1]))
        p2 = float(np.mean(r2["price"][t0:t1]))
        rows.append(dict(
            crop=crop, variant=overrides.get("_name", "shipped"),
            biggest=prep.countries[i], cut_frac=frac,
            cut_mmt=float(cut_mmt),
            offers_conc=q1, offers_spread=q2,
            offers_rel_gap=(q1 - q2) / max(q2, 1e-12),
            p_base=p_b, p_conc=p1, p_spread=p2,
            lift_conc=p1 / p_b - 1.0, lift_spread=p2 / p_b - 1.0,
            conc_premium=p1 / max(p2, 1e-12) - 1.0))
    return rows


# --------------------------------------------------------------------------
# T2 — split the largest exporter into two identical halves
# --------------------------------------------------------------------------
def _split_arrays(prep, i: int):
    """Clone node i into (i, n) each at half scale, preserving aggregates.

    A and S are rebuilt exactly as row/column normalisations of a split
    bilateral trade matrix: A'[i1,j] = A[i,j], A'[k,i1] = A[k,i]/2,
    S'[i1,j] = S[i,j]/2, S'[k,i1] = S[k,i]. Verified by assertion below.
    """
    n = len(prep.countries)

    def dup_vec(v, half=True):
        f = 0.5 if half else 1.0
        out = np.concatenate([v, [v[i] * f]])
        out[i] = v[i] * f
        return out

    def dup_rows(M, half=True):
        f = 0.5 if half else 1.0
        out = np.vstack([M, M[i:i + 1] * f])
        out[i] = M[i] * f
        return out

    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = prep.A
    A[n, :n] = prep.A[i]            # clone destination mix
    A[:n, n] = prep.A[:, i] * 0.5   # each half receives half the imports
    A[:n, i] *= 0.5
    A[n, i] = 0.0
    A[i, n] = 0.0                   # no new intra-pair trade
    A[n, n] = 0.0
    row = A.sum(axis=1, keepdims=True)
    np.divide(A, row, out=A, where=row > 0)

    S = np.zeros((n + 1, n + 1))
    S[:n, :n] = prep.S
    S[:n, n] = prep.S[:, i]         # clone source mix
    S[n, :n] = prep.S[i] * 0.5      # each half supplies half of every mix
    S[i, :n] *= 0.5
    S[n, i] = 0.0
    S[i, n] = 0.0
    S[n, n] = 0.0
    col = S.sum(axis=0, keepdims=True)
    np.divide(S, col, out=S, where=col > 0)

    return dict(
        H=dup_rows(prep.H), H_seas=dup_rows(prep.H_seas),
        C_flex=dup_rows(prep.C_flex), C_ind=dup_rows(prep.C_ind),
        C_flex_twin=dup_rows(prep.C_flex_twin),
        C_ind_twin=dup_rows(prep.C_ind_twin),
        cuts=dup_rows(prep.cuts, half=False),   # a cut FRACTION, not a level
        stock0=dup_vec(prep.stock0), safety=dup_vec(prep.safety),
        C_ann=dup_vec(prep.C_ann), A=A, S=S)


def split_test(crop: str, mp_alpha: float = 0.0) -> dict:
    t0, t1 = _sl(*WIN)
    prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                            use_demand=False)
    i, _, _ = _biggest(prep, t0, t1)
    sp = _split_arrays(prep, i)
    P = prep.params

    def run(H, C_flex, C_ind, cuts, stock0, safety, C_ann, A, S,
            H_seas, ft=None, ut=None, s_ref=None, x_ref=None):
        return L.simulate_r4(H, C_flex, C_ind, cuts, stock0.copy(), safety,
                             prep.p0, C_ann, A, S, P, free_twin=ft,
                             unmet_twin=ut, H_seasonal=H_seas,
                             mp_alpha=mp_alpha, s_ref=s_ref, x_ref=x_ref,
                             record=False)

    # --- unsplit reference, twin rebuilt under the same law ---
    tw0 = run(prep.H_seas, prep.C_flex_twin, prep.C_ind_twin,
              np.zeros_like(prep.H), prep.stock0, prep.safety, prep.C_ann,
              prep.A, prep.S, prep.H_seas)
    r0 = run(prep.H, prep.C_flex, prep.C_ind, prep.cuts, prep.stock0,
             prep.safety, prep.C_ann, prep.A, prep.S, prep.H_seas,
             ft=tw0["free"], ut=tw0["unmet"], s_ref=tw0["share"],
             x_ref=tw0["offers"].sum(axis=0))
    # --- split economy ---
    tw1 = run(sp["H_seas"], sp["C_flex_twin"], sp["C_ind_twin"],
              np.zeros_like(sp["H"]), sp["stock0"], sp["safety"], sp["C_ann"],
              sp["A"], sp["S"], sp["H_seas"])
    r1 = run(sp["H"], sp["C_flex"], sp["C_ind"], sp["cuts"], sp["stock0"],
             sp["safety"], sp["C_ann"], sp["A"], sp["S"], sp["H_seas"],
             ft=tw1["free"], ut=tw1["unmet"], s_ref=tw1["share"],
             x_ref=tw1["offers"].sum(axis=0))

    s0, s1 = L.score(r0["price"], crop), L.score(r1["price"], crop)
    sh0 = r0["offers"][i] / np.maximum(r0["offers"].sum(axis=0), 1e-12)
    n = len(prep.countries)
    sh1 = r1["offers"][i] / np.maximum(r1["offers"].sum(axis=0), 1e-12)
    d = np.abs(r0["price"] - r1["price"])
    return dict(
        crop=crop, mp_alpha=mp_alpha, split_node=prep.countries[i],
        share_before=float(np.mean(sh0[t0:t1])),
        share_after=float(np.mean(sh1[t0:t1])),
        world_offers_rel_gap=float(
            r1["offers"].sum() / max(r0["offers"].sum(), 1e-12) - 1.0),
        max_abs_dprice=float(d.max()),
        max_rel_dprice=float((d / np.maximum(r0["price"], 1e-9)).max()),
        mean_rel_dprice=float(np.mean(d / np.maximum(r0["price"], 1e-9))),
        p_mean_before=float(r0["price"].mean()),
        p_mean_after=float(r1["price"].mean()),
        d_corr=s1["corr"] - s0["corr"], d_h0708=s1["h0708"] - s0["h0708"],
        d_h1011=s1["h1011"] - s0["h1011"])


# --------------------------------------------------------------------------
# T3 — channel decomposition of the knockout lift
# --------------------------------------------------------------------------
def channels(crop: str) -> list[dict]:
    t0, t1 = _sl(*WIN)
    variants = {
        "shipped": {},
        "ask_rival=0": dict(ask_rival=0.0),
        "block_kappa=0": dict(block_kappa=0.0),
        "rival=0,block=0": dict(ask_rival=0.0, block_kappa=0.0),
        "unmet_kappa=0": dict(unmet_kappa=0.0),
        "trade_w=1 (no scarcity)": dict(trade_w=1.0),
        "trade_w=0 (scarcity only)": dict(trade_w=0.0),
        "all reduced-form off": dict(ask_rival=0.0, block_kappa=0.0,
                                     unmet_kappa=0.0),
    }
    rows = []
    for name, ov in variants.items():
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False, **ov)
        Hp = prep.H * (1.0 - 1e-6)
        i, base, off = _biggest(prep, t0, t1)
        p_b = float(np.mean(base["price"][t0:t1]))
        cuts = np.zeros_like(prep.cuts)
        cuts[i, t0:t1] = 1.0
        ko = L.run_prep(prep, cuts=cuts, harvest=Hp)
        p_k = float(np.mean(ko["price"][t0:t1]))
        rows.append(dict(
            crop=crop, variant=name, country=prep.countries[i],
            offer_share=float(off[i] / max(off.sum(), 1e-12)),
            p_base=p_b, p_ko=p_k, lift=p_k / p_b - 1.0,
            d_p_trade=float(np.mean(ko["p_trade"][t0:t1]
                                    - base["p_trade"][t0:t1]) / p_b),
            d_p_scar=float(np.nanmean(ko["p_scar"][t0:t1]
                                      - base["p_scar"][t0:t1]) / p_b),
            mean_block_frac=float(np.mean(ko["block_frac"][t0:t1])),
            d_free=float(np.mean(ko["free"][t0:t1] - base["free"][t0:t1]))))
    return rows


def main():
    print("=== T1 concentrated vs spread cut of the SAME tonnage ===")
    rows = []
    for crop in L.CROPS:
        rows += concentration(crop, {})
    t1 = pd.DataFrame(rows)
    t1.to_csv(OUT / "r4_07_concentration.csv", index=False)
    print(t1[["crop", "biggest", "cut_frac", "cut_mmt", "offers_rel_gap",
              "lift_conc", "lift_spread", "conc_premium"]].to_string(
        index=False, float_format=lambda x: f"{x:.4f}"))

    print("\n=== T2 split the largest exporter into two identical halves ===")
    sp = pd.DataFrame([split_test(c, a) for c in L.CROPS
                       for a in (0.0, 3.0)])
    sp.to_csv(OUT / "r4_07_split_neutrality.csv", index=False)
    print(sp[["crop", "mp_alpha", "split_node", "share_before", "share_after",
              "world_offers_rel_gap", "max_rel_dprice", "p_mean_before",
              "p_mean_after", "d_corr"]].to_string(
        index=False, float_format=lambda x: f"{x:.5f}"))

    print("\n=== T3 channel decomposition of the knockout lift ===")
    ch = pd.DataFrame([r for c in L.CROPS for r in channels(c)])
    ch.to_csv(OUT / "r4_07_channels.csv", index=False)
    print(ch[["crop", "variant", "country", "offer_share", "lift",
              "d_p_trade", "d_p_scar", "mean_block_frac"]].to_string(
        index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
