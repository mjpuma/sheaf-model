import pandas as pd

from .config import data_dir


def read_fao(filename, chunksize=None, encoding='latin-1'):
    print("Reading", filename)
    dtype = {
        "Area Code": "Int64", 
        "Item Code": "Int64", 
        "Months Code": "Int64", 
        "Year Code": "Int64", 
        "Element Code": "Int64", 
        "Reporter Country Code": "Int64",
        "Partner Country Code": "Int64",
        "Country Code": "Int64",
        "M49 Code": str,
        "ISO2 Code": str,
        "ISO3 Code": str,
        "Start Year": "Int64",
        "End Year": "Int64",
        "Area": str,
        "Item": str,
        "Months": str,
        "Year": str,
        "Unit": str,
        "Flag": str,
        "Note": str,
        "Element": str,
        "Reporter Countries": str,
        "Partner Countries": str,
        "Country": str,
        "Value": str,
    }
    return pd.read_csv(data_dir("raw", "fao", filename), dtype=dtype, encoding=encoding, chunksize=chunksize)


def clean_fao(filename, years=[], area_codes=[], item_codes=[], elements=[], columns=[], extra_funcs=[], encoding='latin-1'):
    df_list = []
    with read_fao(filename, chunksize=1e6, encoding=encoding) as reader:
        for df in reader:
            if years:
                filter = pd.DataFrame({"Year Code": years}, dtype="Int64")
                df = pd.merge(df, filter, on="Year Code", how="inner")
            if area_codes:
                if "Area Code" in df.columns:
                    filter = pd.DataFrame({"Area Code": area_codes}, dtype="Int64")
                    df = pd.merge(df, filter, on="Area Code", how="inner")
                elif "Reporter Countries" in df.columns:
                    dfs = []
                    for col in ["Reporter Countries", "Partner Countries"]:
                        filter = pd.DataFrame({col: area_codes}, dtype="Int64")
                        df_f = pd.merge(df, filter, on=col, how="inner")
                        dfs.append(df_f)
                    df = pd.concat(dfs)
                    df = df.drop_duplicates()
            if item_codes:
                filter = pd.DataFrame({"Item Code": item_codes}, dtype="Int64")
                df = pd.merge(df, filter, on="Item Code", how="inner")            
            if elements:
                filter = pd.DataFrame({"Element": elements})
                df = pd.merge(df, filter, on="Element", how="inner")              
            for func in extra_funcs:
                df = func(df)
            if columns:
                df = df[columns]
            df_list.append(df)
    df = pd.concat(df_list)
    return df


# Helper functions for cleaning FAO data
def remove_aggregate_areas(df):
    if "Area Code" in df.columns: 
        return df[(df["Area Code"] < 350) & ~((260 < df["Area Code"]) & (df["Area Code"] < 270))]
    if "Reporter Country Code" in df.columns and "Partner Country Code" in df.columns:
        return df[(df["Reporter Country Code"] < 350) & (df["Partner Country Code"] < 350)]
    print("Aggregate areas not removed.")
    return df

def reverse_stock_variation_sign(df):
    df["Value"] = df["Value"].astype(float)
    df.loc[df["Element"] == "Stock Variation", "Value"] *= -1
    return df

def convert_rice_milled_to_paddy(df):
    df["Item Code"] = df["Item Code"].astype("Int64")
    df["Item"] = df["Item"].astype(str)
    df["Value"] = df["Value"].astype(float)
    conversion_factor = 2 / 3
    df.loc[df["Item Code"] == 2805, "Value"] /= conversion_factor
    df["Item Code"] = df["Item Code"].replace({2805: 2807})
    df["Item"] = df["Item"].replace({"Rice (Milled Equivalent)": "Rice and products"})
    return df



def clean_usda_marketing_year_data(crop):
    df = pd.read_html(data_dir("raw", "usda", f"{crop}_availability.xls"), skiprows=0)
    df = df[0]
    df.columns = df.columns.get_level_values(1)
    df = df[["Country", "Years", "Market Year", "Note"]]

    # Fix for Liberia and wheat
    if crop == "wheat":
        filter = (df["Country"] == "Liberia") & (df["Years"] == "2014-2018")
        df.loc[filter, "Market Year"] = "JUL To JUN" # before: MAY to JUN - nonsense

    df["Start Year"] = df["Years"].str[:4].astype(int)
    df["End Year"] = df["Years"].str[-4:].astype(int)
    df["End Year"] = df["End Year"].replace(2018, 2022)
    df[f"MY Start Month"] = df["Market Year"].str[:3]
    df[f"MY End Month"] = df["Market Year"].str[-3:]
    for s in ["Start", "End"]:
        df[f"MY {s} Month"] = pd.to_datetime(df[f"MY {s} Month"], format='%b').dt.month.astype("Int64")

    # Infer the shift between the reported marketing year and the actual production
    # WARNING: there are clear mistakes in some shifts which are NOT yet fixed
    df["Start Month Year Shift"] = df["Note"].str[-12:-8].astype(int) - df["Note"].str[-26:-22].astype(int)

    df = df.drop(columns=["Years", "Market Year", "Note"])


    # Add ISO codes
    df_iso = pd.read_csv(data_dir("clean", "usda", "country_codes_usda.csv"))
    df_iso = df_iso.rename(columns={"ISO3 Code": "Country Code"})
    df = pd.merge(df, df_iso, how="left", on="Country")
    df["Country Code"] = df["Country Code"].fillna(df["USDA Code"])

    columns = ["Start Year", "End Year",
               "MY Start Month", "MY End Month", "Start Month Year Shift"]

    # Add EU
    eu_areas = [
        "AUT", "BEL", "BGR", "CYP", "CZE", "DEU", "DNK", "ESP", "EST", 
        "FIN", "FRA", "GRC", "HRV", "HUN", "IRL", "ITA", "LTU", "LUX", 
        "LVA", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "SWE",
        "GBR"
    ]
    df_eu = pd.DataFrame({
        **{"Country Code": eu_areas}, 
        **{col: [df.loc[df["Country Code"] == "E4", col].iloc[0]] * len(eu_areas) for col in columns}
    })
    df_eu = pd.merge(df_eu, df_iso, on="Country Code", how="left")
    df = pd.concat([df, df_eu])

    df["Country Code"] = df["Country Code"].replace("E4", "EU-27")
    df = df[["Country Code", "USDA Code", "Country"] + columns]
    df = df.sort_values(by=["Country Code", "Start Year"])

    # # Add world
    # df = df.set_index("Country")
    # df.loc["World"] = [1960, 2022, pd.NA, pd.NA, pd.NA]
    # df = df.reset_index()

    return df
        


