import numpy as np
import pandas as pd
from scipy import optimize


def select_data_to_harmonize(df_fb, df_t, min_flow):

    df_fb = df_fb.copy()
    df_t = df_t.copy()

    trade_col = "Trade Flow (estimate)"
    # Only trade flows larger than min_trade will be harmonized
    # Additionally the origin areas need to have non-zero exports and the destination areas non-zero imports
    exporting_areas = df_fb.loc[df_fb["Export Quantity"] > 0, "Area"].tolist()
    importing_areas = df_fb.loc[df_fb["Import Quantity"] > 0, "Area"].tolist()

    to_harmonize = (
        (df_t[trade_col] >= min_flow) & 
        df_t["Origin"].isin(exporting_areas) & 
        df_t["Destination"].isin(importing_areas)
    )
    df_t["to harmonize"] = to_harmonize
    df_t_h = df_t[to_harmonize]

    print(f"{len(df_t_h)} trade flows out of {len(df_t)} will be harmonized.")
    print(f"They correspond to {(df_t_h[trade_col].sum() / df_t[trade_col].sum()) * 100:.2f}% of the total trade volume.")

    # To be harmonized as well as non-harmonized trade flows should be noted in food balance data
    df_e = df_t.groupby(by=["Origin", "to harmonize"]).agg({trade_col: "sum"}).reset_index().rename(columns={"Origin": "Area"})
    df_i = df_t.groupby(by=["Destination", "to harmonize"]).agg({trade_col: "sum"}).reset_index().rename(columns={"Destination": "Area"})   

    for df, flow in zip([df_e, df_i], ["Export", "Import"]):
        df = df.pivot_table(index="Area", columns="to harmonize", values=trade_col, fill_value=0).reset_index()
        df = df.rename(columns={True: f"{flow} Quantity (agg, to harmonize)", False: f"{flow} Quantity (agg, non-harmonized)"})
        df_fb = pd.merge(df_fb, df, on="Area", how="left").fillna(0)
        df_fb[f"Share non-harmonized {flow} Quantity"] = (
            df_fb[f"{flow} Quantity (agg, non-harmonized)"]
            / (df_fb[f"{flow} Quantity (agg, to harmonize)"] + df_fb[f"{flow} Quantity (agg, non-harmonized)"])
        ).fillna(1)
        df_fb[f"{flow} Quantity (non-harmonized)"] =  (
            df_fb[f"Share non-harmonized {flow} Quantity"] * df_fb[f"{flow} Quantity"]
        )
        df_fb[f"{flow} Quantity (to harmonize)"] = df_fb[f"{flow} Quantity"] - df_fb[f"{flow} Quantity (non-harmonized)"]


    # Export/import quantity will by fully non-harmonized if no trade flows are found from/to a given area in df_t_h
    # areas_nh = {}
    # areas_nh["Export"] = set(exporting_areas) - set(df_t_h["Origin"].unique())
    # areas_nh["Import"] = set(importing_areas) - set(df_t_h["Destination"].unique())
    # for flow in ["Export", "Import"]:
    #     df_fb.loc[df_fb["Area"].isin(areas_nh[flow]), f"{flow} Quantity (non-harmonized)"] = df_fb[f"{flow} Quantity"]
    #     # The difference of FB flow and non-harmonized flow is the estimate of the flow to be harmonized
    #     df_fb[f"{flow} Quantity (to harmonize)"] = df_fb[f"{flow} Quantity"] - df_fb[f"{flow} Quantity (non-harmonized)"]

    return df_fb, df_t


def dfs_to_arrays(df_fb, df_t):

    df_e = df_fb.loc[df_fb["Export Quantity (to harmonize)"] > 0, ["Area", "Export Quantity (to harmonize)"]]
    df_i = df_fb.loc[df_fb["Import Quantity (to harmonize)"] > 0, ["Area", "Import Quantity (to harmonize)"]]
    origins = df_e["Area"].tolist()
    destinations = df_i["Area"].tolist()
    exports = df_e["Export Quantity (to harmonize)"].to_numpy()
    imports = df_i["Import Quantity (to harmonize)"].to_numpy()

    df_t = df_t.loc[df_t["to harmonize"], ["Origin", "Destination", "Trade Flow (estimate)"]]
    origin_id = {origin: i for i, origin in enumerate(origins)}
    destination_id = {destination: j for j, destination in enumerate(destinations)}
    trade = np.zeros((len(origins), len(destinations)))
    for row in df_t.itertuples(index=False, name=None):
        trade[origin_id[row[0]], destination_id[row[1]]] = row[2]

    return exports, imports, trade, origins, destinations


def numerical_harmonization(exports, imports, trade, pen_exports, pen_imports, pen_trade):

    indices_trade = np.nonzero(trade)

    n_origins = len(exports)
    n_destinations = len(imports)
    n_trade = len(indices_trade[0])

    loc_trade_rows = [np.nonzero(indices_trade[0] == i)[0] for i in range(n_origins)]
    loc_trade_cols = [np.nonzero(indices_trade[1] == j)[0] for j in range(n_destinations)]

    trade_corr = np.zeros(trade.shape)
    exports_corr = np.zeros(exports.shape)
    imports_corr = np.zeros(imports.shape)

    def get_harmonized_trade(X):
        trade_corr[indices_trade] = X[:n_trade]
        return (1 + trade_corr) * trade

    def get_harmonized_exports(X):
        exports_corr[:] = X[n_trade:n_trade+n_origins]
        return (1 + exports_corr) * exports

    def get_harmonized_imports(X):
        imports_corr[:] = X[n_trade+n_origins:]
        return (1 + imports_corr) * imports

    def constraint_exports(X, i):
        loc = loc_trade_rows[i]
        trade_corr[indices_trade[0][loc], indices_trade[1][loc]] = X[:n_trade][loc]
        exports_corr[i] = X[n_trade:n_trade+n_origins][i]
        return np.sum((1 + trade_corr[i,:]) * trade[i,:]) - (1 + exports_corr[i]) * exports[i]

    def constraint_exports_gradient(X, i):
        grad = np.zeros(n_trade + n_origins + n_destinations)
        loc = loc_trade_rows[i]
        grad[:n_trade][loc] = trade[indices_trade[0][loc], indices_trade[1][loc]]
        grad[n_trade:n_trade+n_origins][i] = -exports[i]
        return grad

    def constraint_imports(X, j):
        loc = loc_trade_cols[j]
        trade_corr[indices_trade[0][loc], indices_trade[1][loc]] = X[:n_trade][loc]
        imports_corr[j] = X[n_trade+n_origins:][j]
        return np.sum((1 + trade_corr[:,j]) * trade[:,j]) - (1 + imports_corr[j]) * imports[j]

    def constraint_imports_gradient(X, j):
        grad = np.zeros(n_trade + n_origins + n_destinations)
        loc = loc_trade_cols[j]
        grad[:n_trade][loc] = trade[indices_trade[0][loc], indices_trade[1][loc]]
        grad[n_trade+n_origins:][j] = -imports[j]
        return grad

    def penalty(X):
        return (
            pen_trade * np.sum(X[:n_trade]**2) / n_trade + 
            pen_exports * np.sum(X[n_trade:n_trade+n_origins]**2) / n_origins +
            pen_imports * np.sum(X[n_trade+n_origins:]**2) / n_destinations
        )

    def penalty_gradient(X):
        return np.concatenate([
            2 * pen_trade * X[:n_trade] / n_trade, 
            2 * pen_exports * X[n_trade:n_trade+n_origins] / n_origins,
            2 * pen_imports * X[n_trade+n_origins:] / n_destinations
        ])

    constraints = []
    constraints += [{"type": "eq", "fun": lambda X, i=i: constraint_exports(X, i),
                    "jac": lambda X, i=i: constraint_exports_gradient(X, i)}
                    for i in range(n_origins)]
    constraints += [{"type": "eq", "fun": lambda X, j=j: constraint_imports(X, j),
                     "jac": lambda X, j=j: constraint_imports_gradient(X, j)}
                    for j in range(n_destinations)]

    bounds = [(-1, None)] * (n_trade + n_origins + n_destinations)
    X_init = np.zeros(n_trade + n_origins + n_destinations)

    print("Initial trade:")
    print(get_harmonized_trade(X_init))
    print("Initial exports:")
    print(get_harmonized_exports(X_init))
    print("Initial imports:")
    print(get_harmonized_imports(X_init))
    print("Parameters to optimize:", n_trade + n_origins + n_destinations)

    res = optimize.minimize(fun=penalty, jac=penalty_gradient, constraints=constraints, bounds=bounds, x0=X_init,
                            options={"maxiter": 100, "disp": True})

    trade_har = get_harmonized_trade(res.x)
    exports_har = get_harmonized_exports(res.x)
    imports_har = get_harmonized_imports(res.x)

    print("Harmonized trade:")
    print(trade_har)
    print("Harmonized exports:")
    print(exports_har)
    print("Harmonized imports:")
    print(imports_har)

    return exports_har, imports_har, trade_har, indices_trade


def arrays_to_dfs(exports_har, imports_har, trade_har, origins, destinations, indices_trade, df_fb, df_t):

    df_fb = df_fb.copy()
    df_t = df_t.copy()
    
    df_e_h = pd.DataFrame({"Area": origins, "Export Quantity (harmonized)": exports_har})
    df_i_h = pd.DataFrame({"Area": destinations, "Import Quantity (harmonized)": imports_har})
    df_t_h = pd.DataFrame({
        "Origin": [origins[i] for i in indices_trade[0]],
        "Destination": [destinations[j] for j in indices_trade[1]],
        "Trade Flow (harmonized)": trade_har[indices_trade],
    })

    for df, flow in zip([df_e_h, df_i_h], ["Export", "Import"]):
        df_fb = pd.merge(df_fb, df, on="Area", how="outer")
        df_fb[f"{flow} Quantity (harmonized)"]= df_fb[f"{flow} Quantity (harmonized)"].fillna(0)
    
    df_t = pd.merge(df_t.drop(columns="to harmonize"), df_t_h, on=["Origin", "Destination"], how="outer")

    return df_fb, df_t


def harmonize_trade_data(df_fb, df_t, min_flow=40, pen_exports=10, pen_imports=5):

    # TODO: more efficient QP optimization, useful caching

    # os.makedirs(data_dir("cache"), exist_ok="True")

    df_fb, df_t = select_data_to_harmonize(df_fb, df_t, min_flow)
    exports, imports, trade, origins, destinations = dfs_to_arrays(df_fb, df_t)

    force = True
    if force:
        exports, imports, trade, indices_trade = numerical_harmonization(
            exports, imports, trade, 
            pen_exports=pen_exports, pen_imports=pen_imports, pen_trade=1
        )
    #     np.save(data_dir("cache", "exports_har.npy"), exports)
    #     np.save(data_dir("cache", "imports_har.npy"), imports)
    #     np.save(data_dir("cache", "trade_har.npy"), trade)
    # else:
    #     indices_trade = np.nonzero(trade)
    #     exports = np.load(data_dir("cache", "exports_har.npy"))
    #     imports = np.load(data_dir("cache", "imports_har.npy"))
    #     trade = np.load(data_dir("cache", "trade_har.npy"))

    df_fb, df_t = arrays_to_dfs(exports, imports, trade, origins, destinations, indices_trade, df_fb, df_t)

    return df_fb, df_t


def verify_harmonization(df_fb, df_t):

    df_fb = df_fb.copy()
    df_t = df_t.copy()

    trade_har_col = "Trade Flow (harmonized)"
    df_e = df_t.groupby(by=["Origin"]).agg({trade_har_col: "sum"}).reset_index().rename(columns={"Origin": "Area"})
    df_i = df_t.groupby(by=["Destination"]).agg({trade_har_col: "sum"}).reset_index().rename(columns={"Destination": "Area"})

    for df, flow in zip([df_e, df_i], ["Export", "Import"]):
        df = df.rename(columns={trade_har_col: f"{flow} Quantity (agg, harmonized)"})
        df_fb = pd.merge(df_fb, df, on="Area", how="left").fillna(0)   

    columns = [
        "Area", 
        "Export Quantity (harmonized)", "Export Quantity (agg, harmonized)",
        "Import Quantity (harmonized)", "Import Quantity (agg, harmonized)"
    ]

    df_fb = df_fb[columns]

    assert sum(abs(df_fb["Export Quantity (harmonized)"] - df_fb["Export Quantity (agg, harmonized)"]) > 0.1) == 0
    assert sum(abs(df_fb["Import Quantity (harmonized)"] - df_fb["Import Quantity (agg, harmonized)"]) > 0.1) == 0

    return df_fb


def summarize_harmonized_data(df_t):

    df_t = df_t.copy()

    har = df_t["Trade Flow (harmonized)"]
    est = df_t["Trade Flow (estimate)"]
    max = df_t[["Trade Flow (by Origin)", "Trade Flow (by Destination)"]].max(axis=1)
    min = df_t[["Trade Flow (by Origin)", "Trade Flow (by Destination)"]].min(axis=1)

    perc_out_of_range = df_t[(har > max) | (har < min)].count() / df_t.count() * 100
    perc_out_of_range = perc_out_of_range.iloc[0]
    print(f"{perc_out_of_range:.2f}% of harmonized flows lie outside of the range specified by reported flows.")

    rel_scaling = har / est
    print("Relative deviations of harmonized flows from estimates (summary):")
    print(rel_scaling[min != 0].describe())

    deviation = har - est
    print("Deviations of harmonized flows from estimates (summary):")
    print(deviation.describe())

    print("Top 30 deviations")
    df_t["Deviation"] = deviation
    df_t["Abs Deviation"] = abs(deviation)
    print(df_t.sort_values(by="Abs Deviation", ascending=False).drop(columns="Abs Deviation").iloc[:30])