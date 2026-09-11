#!/usr/bin/env python3
"""R0h: SHEAF's price flexibility against Agrimate's stated inverse elasticity.

Agrimate's world price is an isoelastic inverse demand function evaluated on
a FLOW: p*_wld = P(sum_r X*_r / X*, alpha) with alpha = 3 the inverse price
elasticity of the single world market (Suppl. D.7.4.1), and alpha_I = 3.5
for the international market (Tbl. D.8). So a 1% shortfall in total sales
relative to baseline raises the world price by about 3%.

SHEAF's world price is isoelastic in a different state variable: a ratio of
twin to current accessible STOCK, p_scar = p0 * r^inv_eta, with inv_eta
0.90/0.85/0.95 for wheat/maize/rice.

These exponents are not comparable directly -- one is an elasticity with
respect to a flow, the other with respect to a stock, and world stock is
roughly thirty times a fortnight's consumption. The comparable quantity is
the reduced-form PRICE FLEXIBILITY d log p / d log H: how much the model's
price moves for a given proportional harvest shortfall. That can be
measured on SHEAF and compared against Agrimate's alpha and against the
flow reference 1/|elasticity| implied by SHEAF's own demand elasticities.

Read-only. Run after the R0f scarcity fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.dynamic_crop import prepare_crop_run, simulate_prep  # noqa: E402

CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)
# Agrimate: alpha = 3 (single world market, Suppl. D.7.4.1),
#           alpha_I = 3.5 (international market, Tbl. D.8).
AGRIMATE_ALPHA = 3.0
AGRIMATE_ALPHA_I = 3.5


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# R0h — price flexibility: SHEAF against Agrimate's alpha\n")
    out("Uniform proportional harvest shortfalls applied to the matched")
    out("(no-shock, no-AMIS) configuration, so the response is the model's")
    out("own transfer function rather than a crisis artefact. Flexibility is")
    out("measured as d log(mean price) / d log(harvest).\n")

    rows = []
    shortfalls = (0.01, 0.02, 0.05, 0.10)
    out("| crop | inv_eta | demand elast | flow reference 1/|elast| "
        "| measured flexibility at −1% | −2% | −5% | −10% |")
    out("|---|---|---|---|---|---|---|---|")
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        base = simulate_prep(prep)
        p_base = float(np.mean(base.price))
        el = prep.params.elast
        flex = []
        for s in shortfalls:
            r = simulate_prep(prep, harvest=prep.H * (1.0 - s))
            p = float(np.mean(r.price))
            flex.append(np.log(p / p_base) / np.log(1.0 - s))
        out(f"| {crop} | {prep.params.inv_eta:.2f} | {el:.2f} "
            f"| {1.0/abs(el):.1f} | " + " | ".join(f"{f:.2f}" for f in flex)
            + " |")
        rows.append(dict(crop=crop, inv_eta=prep.params.inv_eta, elast=el,
                         flow_ref=1.0 / abs(el),
                         **{f"flex_{int(s*100)}pct": f
                            for s, f in zip(shortfalls, flex)}))
    out("")
    out(f"Agrimate for comparison: alpha = {AGRIMATE_ALPHA:.1f} for the single")
    out(f"world market and alpha_I = {AGRIMATE_ALPHA_I:.1f} for the")
    out("international market. Both are elasticities with respect to a flow")
    out("(sales relative to baseline sales), so the like-for-like SHEAF")
    out("column is the measured flexibility, not inv_eta.\n")

    out("## Reading\n")
    out("Three numbers are on the table for each crop: what SHEAF's price")
    out("actually does (measured flexibility), what SHEAF's own demand")
    out("elasticity implies a competitive flow market should do (1/|elast|),")
    out("and what Agrimate uses (3.0 to 3.5).\n")
    out("If SHEAF's measured flexibility is far BELOW both references, the")
    out("model's price is structurally too insensitive to scarcity, and the")
    out("reduced-form markups -- ask_rival in particular, which A2 showed has")
    out("no surviving independent justification -- are supplying amplitude")
    out("that the price map should be generating itself. That would make the")
    out("principled repair a re-specification of the scarcity exponent or its")
    out("state variable, not a defence of ask_rival.\n")
    out("If instead the measured flexibility already sits in the 3 to 7 band,")
    out("SHEAF is in the same territory as Agrimate and the criticism does")
    out("not hold.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "price_flexibility.csv", index=False)
    (dest / "R0H_PRICE_FLEXIBILITY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0H_PRICE_FLEXIBILITY.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
