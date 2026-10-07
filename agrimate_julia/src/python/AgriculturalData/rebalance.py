import pandas as pd


def rebalance_after_harmonization(df_fb):

    df_fb = df_fb.copy()

    df_fb["Production (rebalanced)"] = df_fb["Production"]

    for flow in ["Export", 'Import']:
        df_fb[f"{flow} Quantity (harmonized) (rebalanced)"] = df_fb[f"{flow} Quantity (harmonized)"]
        df_fb[f"{flow} Quantity (non-harmonized) (rebalanced)"] = df_fb[f"{flow} Quantity (non-harmonized)"]
        df_fb[f"{flow} Quantity (rebalanced)"] = (
            df_fb[f"{flow} Quantity (harmonized) (rebalanced)"] 
            + df_fb[f"{flow} Quantity (non-harmonized) (rebalanced)"]
        )

    df_fb["Stock Variation (rebalanced)"] = df_fb["Stock Variation"]

    df_fb["Domestic supply quantity (rebalanced)"] = (
        df_fb["Production (rebalanced)"] + df_fb["Import Quantity (rebalanced)"] 
        - df_fb["Export Quantity (rebalanced)"] - df_fb["Stock Variation"]
    )

    supply_negative = df_fb["Domestic supply quantity (rebalanced)"] < 0
    df_fb.loc[supply_negative, "Stock Variation (rebalanced)"] += df_fb["Domestic supply quantity (rebalanced)"]
    df_fb.loc[supply_negative, "Domestic supply quantity (rebalanced)"] = 0

    return df_fb


def rebalance_stock_variation(df_fb, df_t):

    df_fb = df_fb.copy()
    df_t = df_t.copy()

    # Initialize rebalanced trade flows
    df_t["Trade Flow (rebalanced)"] = df_t["Trade Flow (harmonized)"]

    n_iter = 8

    for n in range(n_iter):
        # The stock variation is distributed proportionally among other food balance variables
        delta = (
            df_fb["Stock Variation (rebalanced)"] /
            df_fb[[f"{var} (rebalanced)" for var in 
                ["Production", "Domestic supply quantity", "Export Quantity", "Import Quantity"]
            ]].sum(axis=1)
        )
        for var in ["Production", "Import Quantity", "Import Quantity (non-harmonized)"]:
            df_fb[f"{var} (rebalanced)"] *= 1 - delta
        for var in ["Domestic supply quantity", "Export Quantity", "Export Quantity (non-harmonized)"]:
            df_fb[f"{var} (rebalanced)"] *= 1 + delta
        # The change of exports/imports translate into changes of trade flows
        delta.name = "delta"
        delta = pd.concat([df_fb["Area"], delta], axis=1)
        df_t = df_t.merge(delta.rename(columns={"Area": "Origin", "delta": "delta Origin"}), on="Origin", how="left")
        df_t = df_t.merge(delta.rename(columns={"Area": "Destination", "delta": "delta Destination"}), on="Destination", how="left")
        df_t["Trade Flow (rebalanced)"] *= (1 + df_t["delta Origin"]) * (1 - df_t["delta Destination"])
        df_t = df_t.drop(columns=["delta Origin", "delta Destination"])
        # Changes in trade flows translate into changes in exports and imports
        trade_col = "Trade Flow (rebalanced)"
        df_e = df_t.groupby(by="Origin").agg({trade_col: "sum"}).reset_index().rename(columns={"Origin": "Area"})
        df_i = df_t.groupby(by="Destination").agg({trade_col: "sum"}).reset_index().rename(columns={"Destination": "Area"})
        for flow, df in zip(["Export", "Import"], [df_e, df_i]):
            df_fb = df_fb.drop(columns=f"{flow} Quantity (harmonized) (rebalanced)")
            df = df[["Area", trade_col]].rename(columns={trade_col: f"{flow} Quantity (harmonized) (rebalanced)"})
            df_fb = df_fb.merge(df, on="Area", how="left").fillna(0)
            df_fb[f"{flow} Quantity (rebalanced)"] = (
                df_fb[[f"{flow} Quantity (harmonized) (rebalanced)", f"{flow} Quantity (non-harmonized) (rebalanced)"]].sum(axis=1)
            )
        # Calculate the new stock variation
        df_fb["Stock Variation (rebalanced)"] = (
            df_fb[[f"{var} (rebalanced)" for var in ["Production", "Import Quantity"]]].sum(axis=1) 
            - df_fb[[f"{var} (rebalanced)" for var in ["Domestic supply quantity", "Export Quantity"]]].sum(axis=1)
        )

    assert abs(df_fb["Stock Variation (rebalanced)"]).max() < 1

    df_fb["Domestic supply quantity (rebalanced)"] += df_fb["Stock Variation (rebalanced)"]
    df_fb["Stock Variation (rebalanced)"] = 0   

    return df_fb, df_t


def verify_food_balance(df_fb, rebalanced=False):
    net = (
        df_fb[[(f"{var} (rebalanced)" if rebalanced else var) 
            for var in ["Production", "Import Quantity"]]].sum(axis=1)
        - df_fb[[(f"{var} (rebalanced)" if rebalanced else var) 
            for var in ["Domestic supply quantity", "Export Quantity", "Stock Variation"]]].sum(axis=1)
    )
    net.name = "Net"
    net = pd.concat([df_fb["Area"], net], axis=1)
    assert sum(abs(net["Net"]) > 0.1) == 0
    return net