"""
demo.py -- SHEAF prototype demonstration.

Runs a Black Sea wheat shock (Russia -40%, Ukraine -50% wheat) through the
three-grain model under two regimes:

    * substitution ON  -- the full SHEAF model; grain markets couple.
    * substitution OFF -- cross-price terms zeroed; the markets decouple into
      independent single-commodity problems (the TWIST/Agrimate-style limit).

The comparison is the headline result: with substitution, a wheat shock spills
into the rice and maize markets and the optimal wheat export restrictions change,
because buyers can escape into another grain. Without it, the wheat shock stays
walled off in the wheat market -- which is exactly what reviewers say is wrong
with single-commodity strategic-trade models.

Outputs: sheaf_results.csv and four PNG figures.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from sheaf import build_countries, SheafModel, GRAINS

PERIODS = 12
SHOCK_T = (5, 6, 7)
# Adjudicated coarse-grid fix: 13-point tax grid (~10 $/t steps to tau_max=120).
GAME_GRID = 13
GAME_ITERS = 3
OUT_DIR = "figures"


def wheat_shock(countries):
    """production_shock dict: Russia & Ukraine wheat cut during SHOCK_T."""
    idx = {c.name: i for i, c in enumerate(countries)}
    n, G = len(countries), len(GRAINS)
    s = {}
    for t in SHOCK_T:
        m = np.ones((n, G))
        m[idx["Russia"], 0] = 0.60
        m[idx["Ukraine"], 0] = 0.50
        s[t] = m
    return s


def run(substitution: bool):
    """Return (shocked_df, counterfactual_df, shocked_model).

    The counterfactual is the same model with no shock, so the shock-induced
    deviation (shocked - counterfactual) strips out the endogenous storage drift
    and isolates the effect of the wheat shock itself.
    """
    c1, transport, grains, fm = build_countries(substitution=substitution)
    model = SheafModel(c1, transport, grains, freight_mult=fm,
                       play_game=True, game_grid=GAME_GRID, game_iters=GAME_ITERS)
    df = model.run(PERIODS, shocks=wheat_shock(c1))
    df["substitution"] = substitution

    c0, transport0, _, _ = build_countries(substitution=substitution)
    base_model = SheafModel(c0, transport0, grains, freight_mult=fm,
                            play_game=True, game_grid=GAME_GRID, game_iters=GAME_ITERS)
    df0 = base_model.run(PERIODS, shocks={})       # no shock counterfactual
    return df, df0, model


def price_paths(df, grain, metric="importer_price"):
    d = df[df.grain == grain].groupby("period")[metric].first()
    return d.index.values, d.values


def deviation(df_shock, df_base, grain, metric="importer_price"):
    x, ys = price_paths(df_shock, grain, metric)
    _, yb = price_paths(df_base, grain, metric)
    return x, ys - yb


def fig_coupling(on, off):
    """Headline figure: shock-induced price deviation (shocked minus no-shock
    counterfactual). Wheat jumps in both regimes; rice and maize move ONLY with
    substitution -- without it they sit flat at zero (the decoupled limit)."""
    df_on, df0_on = on
    df_off, df0_off = off
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharex=True)
    band = (SHOCK_T[0] - 0.5, SHOCK_T[-1] + 0.5)
    for ax, grain in zip(axes, GRAINS):
        x, d_on = deviation(df_on, df0_on, grain)
        _, d_off = deviation(df_off, df0_off, grain)
        ax.axhline(0, color="0.7", lw=0.8)
        ax.axvspan(*band, color="0.9", label="Black Sea wheat shock")
        ax.plot(x, d_off, "o--", color="#888",
                label="no substitution (TWIST/Agrimate limit)")
        ax.plot(x, d_on, "o-", color="#c0392b", label="SHEAF (with substitution)")
        ax.set_title(f"{grain.capitalize()}")
        ax.set_xlabel("period")
        ax.set_ylabel("shock-induced price change ($/t)")
    axes[0].legend(fontsize=8, loc="upper left")
    fig.suptitle("A wheat shock spills into rice and maize ONLY when buyers can substitute",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig1_coupling.png", dpi=130)
    plt.close(fig)


def fig_restrictions(df_on, df_off):
    """Optimal wheat export taxes: substitution flattens residual demand, so the
    strategic restriction changes."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, df, title in zip(axes, (df_off, df_on),
                             ("No substitution", "With substitution (SHEAF)")):
        w = df[(df.grain == "wheat") & (df.period.isin(SHOCK_T))]
        piv = w.pivot_table(index="country", values="export_tax", aggfunc="max")
        piv = piv[piv.export_tax > 0.5].sort_values("export_tax", ascending=True)
        ax.barh(piv.index, piv.export_tax.values, color="#c0392b")
        ax.set_title(title)
        ax.set_xlabel("peak wheat export-tax equiv. ($/t)")
    fig.suptitle("Wheat export restrictions during the shock", fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig2_restrictions.png", dpi=130)
    plt.close(fig)


def fig_reserves(df_on, model_on):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharex=True)
    for ax, grain in zip(axes, GRAINS):
        d = df_on[df_on.grain == grain]
        gov = d.groupby("period")["gov_stock"].sum()
        mkt = d.groupby("period")["mkt_stock"].sum()
        ax.axvspan(SHOCK_T[0] - 0.5, SHOCK_T[-1] + 0.5, color="0.9")
        ax.plot(gov.index, gov.values, "o-", color="#2c3e50", label="gov reserves")
        ax.plot(mkt.index, mkt.values, "s-", color="#16a085", label="private reserves")
        ax.set_title(f"{grain.capitalize()} reserves")
        ax.set_xlabel("period"); ax.set_ylabel("MMT")
    axes[0].legend(fontsize=8)
    fig.suptitle("Reserves release into the shock", fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig3_reserves.png", dpi=130)
    plt.close(fig)


def fig_network(model_on):
    """Wheat trade network, baseline vs shock."""
    countries = model_on.countries
    lat = None
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    for ax, t, title in zip(axes, (0, SHOCK_T[1]),
                            ("Baseline wheat network (t=0)",
                             f"During shock (t={SHOCK_T[1]})")):
        F = model_on.flow_history[t][0]  # grain 0 = wheat
        G = nx.DiGraph()
        names = [c.name for c in countries]
        for nm in names:
            G.add_node(nm)
        for i in range(len(countries)):
            for j in range(len(countries)):
                if F[i, j] > 0.5:
                    G.add_edge(names[i], names[j], w=F[i, j])
        pos = nx.circular_layout(G)
        ne = model_on.results_frame()
        # colour: net exporter (blue) vs importer (red) of wheat at that period
        sub = ne[(ne.grain == "wheat") & (ne.period == t)].set_index("country")
        colors = ["#2874a6" if sub.loc[nm, "net_export"] > 0 else "#c0392b"
                  for nm in G.nodes()]
        widths = [0.4 + 3.5 * G[u][v]["w"] / max(F.max(), 1e-9) for u, v in G.edges()]
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=650, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)
        nx.draw_networkx_edges(G, pos, width=widths, edge_color="0.5",
                               alpha=0.7, arrowsize=8, ax=ax)
        ax.set_title(title); ax.axis("off")
    fig.suptitle("Wheat trade network: blue = net exporter, red = net importer; "
                 "edge width ~ flow", fontsize=12)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig4_network.png", dpi=130)
    plt.close(fig)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Running SHEAF prototype: 3 grains × countries "
          f"(game_grid={GAME_GRID}; shock + counterfactual, two regimes)...\n")
    df_on, df0_on, model_on = run(substitution=True)
    df_off, df0_off, model_off = run(substitution=False)

    df = pd.concat([df_on.assign(scenario="shock"),
                    df0_on.assign(scenario="counterfactual"),
                    df_off.assign(scenario="shock"),
                    df0_off.assign(scenario="counterfactual")], ignore_index=True)
    df.to_csv("sheaf_results.csv", index=False)

    fig_coupling((df_on, df0_on), (df_off, df0_off))
    fig_restrictions(df_on, df_off)
    fig_reserves(df_on, model_on)
    fig_network(model_on)

    def peak_dev(dfs, df0, grain):
        _, d = deviation(dfs, df0, grain)
        return float(np.max(d))

    print("Shock-induced price change (shocked minus no-shock counterfactual), peak $/t:")
    for grain in GRAINS:
        on = peak_dev(df_on, df0_on, grain)
        off = peak_dev(df_off, df0_off, grain)
        print(f"  {grain:6s}  SHEAF (substitution): {on:+6.1f}    "
              f"no-substitution: {off:+6.1f}")
    print("\n  -> The wheat shock alone moves rice and maize only under substitution;")
    print("     without it, those markets are walled off (deviation ~ 0).")

    nrest = df_on[(df_on.grain == "wheat") & (df_on.period.isin(SHOCK_T))]["n_restricting"].max()
    print(f"\nWheat exporters restricting during the shock (SHEAF): {nrest}")
    print(f"\nWrote sheaf_results.csv, {OUT_DIR}/fig1_coupling.png, "
          f"{OUT_DIR}/fig2_restrictions.png, {OUT_DIR}/fig3_reserves.png, "
          f"{OUT_DIR}/fig4_network.png")


if __name__ == "__main__":
    main()
