import numpy as np
import pandas as pd

from AgriculturalData.config import data_dir
from AgriculturalData.item_groups import item_groups_fao

from icecream import ic


def convert_to_primary_equivalent(df, crop):
    conversion_factors = pd.Series(item_groups_fao[crop], name="Conversion Factor")
    df = df.join(conversion_factors, on="Item Code")
    df["Value"] /= df["Conversion Factor"]
    df = df.drop(columns="Conversion Factor")
    return df

def estimate_trade_flows(df):
    trade_columns = ["Trade Flow (by Origin)", "Trade Flow (by Destination)"]
    estimate_col = "Trade Flow (estimate)"

    missing_1 = df[trade_columns[0]].isna() | (df[trade_columns[0]] <= 0.001) 
    missing_2 = df[trade_columns[1]].isna() | (df[trade_columns[1]] <= 0.001)
    missing = missing_1 | missing_2 

    df[estimate_col] = np.nan
    df.loc[~missing, estimate_col] = df[trade_columns].mean(axis=1)
    df.loc[missing, estimate_col] = df[trade_columns].max(axis=1)

    return df



def impute_food_balance_fao(crop):

    df_fbs = pd.read_csv(data_dir("clean", "fao", f"{crop}_food_balance.csv")) # FBS
    df_prod = pd.read_csv(data_dir("clean", "fao", f"{crop}_production.csv")) # QCL
    df_trade = pd.read_csv(data_dir("clean", "fao", f"{crop}_trade.csv")) # TCL

    dfs = {"fbs": df_fbs, "prod": df_prod, "trade": df_trade}

    # Convert disagreggated trade date to primary equivalent
    df_trade = convert_to_primary_equivalent(df_trade, crop)

    # Convert units to 1000 tonnes
    for key in ["prod", "trade"]:
        dfs[key]["Value"] /= 1000

    # Create a column for each food balance variable
    for key in dfs.keys():
        dfs[key] = dfs[key].pivot_table(
            index=["Area Code", "Year"], 
            columns="Element", 
            values="Value", 
            aggfunc="sum",
            fill_value=0,
        )

    # Merge production (QCL) and trade (TCL) data
    df_prod_trade = pd.merge(dfs["prod"], dfs["trade"], left_index=True, right_index=True, how="outer")
    df_prod_trade = df_prod_trade.fillna(0)
    df_prod_trade = df_prod_trade[(df_prod_trade > 0.).any(axis=1)]

    # Impute domestic supply as max(production + imports - exports, 0)
    df_prod_trade["Domestic supply quantity"] = np.maximum(
        df_prod_trade["Production"] + df_prod_trade["Import Quantity"] - df_prod_trade["Export Quantity"],
        0
    )
    # Impute stock variation as min(production + imports - exports, 0)
    df_prod_trade["Stock Variation"] = np.minimum(
        df_prod_trade["Production"] + df_prod_trade["Import Quantity"] - df_prod_trade["Export Quantity"],
        0
    )
    # Round to 3 decimal places
    df_prod_trade = df_prod_trade.round(3)

    # Annotate data source
    dfs["fbs"]["Source"] = "FBS"
    df_prod_trade["Source"] = "QCL+TCL"

    # Merge FBS with QCL+TCL data
    df = pd.merge(dfs["fbs"], df_prod_trade, left_index=True, right_index=True, how="outer", suffixes=(None, " QCL+TCL"))

    # Fill missing FBS values with QCL+TCL values
    columns = ["Production", "Domestic supply quantity", "Import Quantity", "Export Quantity", "Stock Variation", "Source"]
    no_fbs = df[columns].isna().any(axis=1)
    for col in columns:
        df.loc[no_fbs, col] = df.loc[no_fbs, f"{col} QCL+TCL"]
    df = df.reset_index()

    # Fill area names and ISO3 codes
    area_codes = pd.read_csv(data_dir("clean", "fao", "area_codes_fao.csv"), usecols=["Area", "Area Code", "ISO3 Code"])
    df = pd.merge(df, area_codes, on="Area Code", how="left")

    # Keep only relevant columns and sort values
    index_columns = ["ISO3 Code", "Area", "Area Code", "Year"]
    df = df[index_columns + columns].sort_values(by=["ISO3 Code", "Year"])
    
    return df



def impute_trade_flows_fao(crop):

    df = pd.read_csv(data_dir("clean", "fao", f"{crop}_trade_detailed.csv"))

    df = convert_to_primary_equivalent(df, crop)
    df["Value"] /= 1000 # unit = 1000 tonnes of primary equivalent

    df = df.pivot_table(
        index=["Reporter Country Code", "Partner Country Code", "Item", "Item Code", "Year"],
        columns="Element",
        values="Value",
        aggfunc="sum",
    )

    df1 = df["Export Quantity"].reset_index()
    df1 = df1[~df1["Export Quantity"].isna()]
    df1 = df1.rename(columns={
        "Reporter Country Code": "Origin Code", 
        "Partner Country Code": "Destination Code",
        "Export Quantity": "Trade Flow (by Origin)" 
    })

    df2 = df["Import Quantity"].reset_index()
    df2 = df2[~df2["Import Quantity"].isna()]
    df2 = df2.rename(columns={
        "Reporter Country Code": "Destination Code", 
        "Partner Country Code": "Origin Code",
        "Import Quantity": "Trade Flow (by Destination)" 
    })

    index_columns = ["Origin Code", "Destination Code", "Item", "Item Code", "Year"]
    value_columns = ["Trade Flow (by Origin)", "Trade Flow (by Destination)"]

    df = pd.merge(df1, df2, on=index_columns, how="outer")

    area_codes = pd.read_csv(data_dir("clean", "fao", "area_codes_fao.csv"), usecols=["Area", "Area Code", "ISO3 Code"])
    origin_codes = area_codes.rename(columns={
        "Area": "Origin", 
        "Area Code": "Origin Code",
        "ISO3 Code": "Origin ISO3 Code",
    })
    destination_codes = area_codes.rename(columns={
        "Area": "Destination", 
        "Area Code": "Destination Code",
        "ISO3 Code": "Destination ISO3 Code",
    })
    df = pd.merge(df, origin_codes, on="Origin Code", how="left")
    df = pd.merge(df, destination_codes, on="Destination Code", how="left")

    index_columns = [
        "Origin ISO3 Code", "Origin", "Origin Code", 
        "Destination ISO3 Code", "Destination", "Destination Code",
        "Item", "Item Code", "Year"
    ]
    df = df[index_columns + value_columns].sort_values(by=["Origin ISO3 Code", "Destination ISO3 Code", "Item Code", "Year"])

    df = estimate_trade_flows(df)

    value_columns += ["Trade Flow (estimate)"]
    df[value_columns] = df[value_columns].round(3)
    df = df[df["Trade Flow (estimate)"] > 0]

    return df


def aggregate_trade_flows(df, over_items=False, over_years=False):

    trade_columns = ["Trade Flow (by Origin)", "Trade Flow (by Destination)"]
    index_cols = [
        "Origin ISO3 Code", "Origin", "Origin Code", 
        "Destination ISO3 Code", "Destination", "Destination Code",
    ]
        
    if over_years:
        df = df.groupby(by=index_cols + ["Item", "Item Code"]).agg({col: "mean" for col in trade_columns}).reset_index()
    
    # Estimate trade flows always at the item level
    df = estimate_trade_flows(df)

    if over_items:
        index_cols = index_cols if over_years else index_cols + ["Year"]
        trade_columns = trade_columns + ["Trade Flow (estimate)"]
        df = df.groupby(by=index_cols).agg({col: "sum" for col in trade_columns}).reset_index()

    df = df.round(3)

    return df

