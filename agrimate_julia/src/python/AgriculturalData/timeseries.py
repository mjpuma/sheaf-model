
import numpy as np
import pandas as pd

from .config import data_dir
from .detrending import detrend_timeseries


def generate_timeseries_fao(crop, variable, detrend=True):

    # Load food balance dataset
    df = pd.read_csv(data_dir("clean", "food_balances", f"{crop}_food_balance_fao.csv"))
    df["Area"] = df["ISO3 Code"]
    df = df[["Area", "Year", variable]]
    areas = df.groupby(by="Area").agg({variable: lambda x: sum(abs(x))}).reset_index()
    areas = areas.loc[areas[variable] > 0, "Area"].tolist() 
    df = df[df["Area"].isin(areas)]

    # if variable == "Production":
    if True:
        # columns = list(df.columns)
        # # Load harvest distribution dataset
        # df_h = pd.read_csv(data_dir("clean", "harvest_distributions", f"harvest_distributions;crop={crop}.csv"))
        # df = determine_harvest_period_fao(df, df_h, crop)
        # df = df[columns + ["Harvest Start Year"]]

        # Corrections resulting from USDA / FAO comparison
        df["Year (FAO)"] = df["Year"]
        if crop == "wheat":
            # Harvest year attribution changed for some countries during the considered period;
            # there is extra evidence for that by comparing Production / Food Balance Sheet timeseries
            areas = [("ARG", 2014), ("AUS", 2010), ("BOL", 2011), ("PRY", 2001), ("URY", 2014)]
            for area, year in areas:
                df = df[~((df["Area"] == area) & (df["Year"] == year))]
                df.loc[(df["Area"] == area) & (df["Year"] > year), "Year"] -= 1
        if crop == "rice":
            pass
            # BOL, CHL needs a -1 shift

    if detrend:
        df = detrend_timeseries(
            df,
            var_col=variable, 
            year_col="Year",
            model="lowess",
            knot_interval=10,
        )

    # df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    return df


def generate_timeseries_usda(crop, variable, filename, year_min, detrend=True):

    usda_crops = {"wheat": "Wheat", "maize": "Corn", "rice": "Rice, Milled"}

    # Load USDA dataset
    df = pd.read_csv(data_dir("raw", "usda", filename))
    df = df[df["Commodity_Description"] == usda_crops[crop]]
    df = df[df["Attribute_Description"] == variable]
    df = df[(df["Market_Year"] >= year_min)]
    codes = pd.read_csv(data_dir("clean", "usda", "country_codes_usda.csv"))
    df = pd.merge(df, codes, how="left", left_on="Country_Code", right_on="USDA Code")
    df.loc[df["ISO3 Code"].isna(), "ISO3 Code"] = df["USDA Code"]

    df = df.rename(columns={"Value": variable, "ISO3 Code": "Area", "Market_Year": "Year"})
    df = df[["Area", "Year", variable]]
    areas = df.groupby(by="Area").agg({variable: lambda x : sum(abs(x))}).reset_index()
    areas = areas.loc[areas[variable] > 0, "Area"].tolist() 
    df = df[df["Area"].isin(areas)]

    df["Year (USDA)"] = df["Year"]
    if variable == "Production":
        # Load definitions of marketing years
        df_my = pd.read_csv(data_dir("clean", "usda", f"{crop}_marketing_years.csv"))
        df_my = df_my.astype(dtype={col: "Int64" for col in df_my.columns[3:]})
        print(f"No {crop} LMY for:", set(df["Area"].unique()) - set(df_my["Country Code"].unique()))
        df_my = df_my.rename(columns={"Country Code": "Area"})
        df = pd.merge(df, df_my, how='left', on="Area")
        # Keep only those marketing year definition that is valid for a given year
        df = df[(df["Start Year"] <= df["Year (USDA)"]) & (df["Year (USDA)"] <= df["End Year"])]
        df = df.drop(columns=["Start Year", "End Year"])
        df["Year"] += df["Start Month Year Shift"]

        # Exceptions!
        # Corrections resulting from USDA / FAO comparison
        if crop == "wheat":
            # LMY in CHL starts in Dec but the bulk harvest is in Jan
            for area in ["CHL"]:
                df.loc[df["Area"] == area, "Year"] += 1
            # USDA NPL data is perfectly cross-correlated with FAO data with lag 1; explanation needed
            # Explanation assumed is that the harvest takes place at the end of LMY (LMY: Jul-Jun, harvest: Mar-Jun)
            # Also assumed to apply for BGD
            for area in ["BGD", "NPL"]:
                df.loc[df["Area"] == area, "Year"] += 1
            # There are problems for MMR; timeseries are correlated but not perfectly - leave as they are
        if crop == "maize":
            # Those areas need a +1 shift
            for area in ["BOL", "NPL"]:
                df.loc[df["Area"] == area, "Year"] += 1
        if crop == "rice":
            # For those areas LMY defnition changed in 2001
            for area in ["PER"]:
                df.loc[(df["Area"] == area) & (df["Year (USDA)"] < 2001), "Year"] -= 1
            # For those areas LMY defnition changed in 2001
            for area in ["SDN"]:
                df.loc[(df["Area"] == area) & (df["Year (USDA)"] < 2001), "Year"] -= 1
            # For those areas LMY defnition changed in 2005
            for area in ["AGO", "BEN", "CMR", "EGY", "GHA", "GNB", "KEN", "MDG", "MLI", "MOZ", "MWI", "SLE", "SWZ", "TCD", "TGO"]:
                df.loc[(df["Area"] == area) & (df["Year (USDA)"] < 2005), "Year"] -= 1
            # For those areas LMY defnition changed in 2007
            for area in ["CHN", "CUB", "HTI", "IRN", "IRQ"]:
                df.loc[(df["Area"] == area) & (df["Year (USDA)"] < 2007), "Year"] -= 1
            # Those areas are NOT in Southern Hemisphere
            # Important: VNM is excluded as FAO matches USDA!
            for area in ["AZE", "KAZ", "RUS", "TJK", "TKM", "UKR", "UZB", "BRN", "KHM", "LAO", "MMR", "MYS", "PRK", "THA", "TWN"]:
                df.loc[df["Area"] == area, "Year"] -= 1
            # Those areas need a +1 shift
            for area in ["BOL", "CHL", "NPL"]:
                df.loc[df["Area"] == area, "Year"] += 1
    else:
        if crop == "wheat":
            for area in ["CHL"]:
                df.loc[df["Area"] == area, "Year"] += 1
        if crop == "maize":
            for area in ["ARG", "AUS", "BOL", "BRA", "CHL", "PRY", "URY", "ZAF"]:
                df.loc[df["Area"] == area, "Year"] += 1
        if crop == "rice":
            for area in ["ARG", "AUS", "BOL", "BRA", "CHL", "PRY", "URY"]: # THA?
                df.loc[df["Area"] == area, "Year"] += 1


    if detrend:
        df = detrend_timeseries(
            df,
            var_col=variable, 
            year_col="Year",
            model="lowess",
            knot_interval=10,
        )
    # df["Year"] = pd.to_datetime(df["Year"], format="%Y")

    return df


def find_harvest_start(harvest_dist):
    N_year = len(harvest_dist)
    # Look for the first non-zero harvest value after a zero harvest value
    for i in range(N_year):
        if harvest_dist[(i - 1) % N_year] == 0 and harvest_dist[i] > 0:
            return i + 1
    # If there are no zero harvest values choose the first value after the minimum value
    return (np.argmin(harvest_dist) + 1) % N_year + 1


def find_harvest_share(start_day, harvest_dist):
    harvest_this_year = np.sum(harvest_dist[start_day-1:])
    harvest_next_year = np.sum(harvest_dist[:start_day-1])
    total_harvest = harvest_this_year + harvest_next_year
    return harvest_this_year / total_harvest


def determine_harvest_period(df, df_h, crop):

    # Infer the start harvest days and shares in year n and n+1
    areas = []
    harvest_start_days = []
    harvest_shares = []
    for area, h in df_h.set_index("Area").iterrows():
        areas.append(area)
        harvest_start_days.append(start_day := find_harvest_start(h.to_numpy()))
        harvest_shares.append(find_harvest_share(start_day, h.to_numpy()))

    df_cal = pd.DataFrame({
        "Area": areas,
        "Harvest Share in Harvest Start Year": harvest_shares,
        "Harvest Start Day": harvest_start_days,
    })

    # Merge harvest calendar information with production data
    df = df.merge(df_cal, on="Area", how="left")
    if no_harvest_calendar := set(df.loc[df["Harvest Start Day"].isna(), "Area"]):
        print(f"No harvest calendar for {crop}:", no_harvest_calendar)
    df = df[~df["Area"].isin(no_harvest_calendar)]

    df["Harvest Start Year"] = df["Year"]
    df.loc[df["Harvest Share in Harvest Start Year"] < 0.5, "Harvest Start Year"] -= 1
    df["Harvest End Day"] = np.where(df["Harvest Start Day"] == 1, 365, df["Harvest Start Day"] - 1)
    df["Harvest End Year"] = df["Harvest Start Year"] + np.where(df["Harvest Start Day"] == 1, 0, 1)

    return df




def generate_daily_production_timeseries(crop, source):

    # Load detrended production timeseries
    df = pd.read_csv(data_dir("clean", "timeseries", f"production;crop={crop};source={source}.csv"))
    # Load harvest distribution data
    df_h = pd.read_csv(data_dir("clean", "harvest_distributions", f"harvest_distributions;crop={crop}.csv"))
    df = determine_harvest_period(df, df_h, crop)

    # Reshape harvest distribution data
    df_h = df_h.melt(id_vars="Area", var_name="Day of Year", value_name="Daily Harvest Share")
    df_h["Day of Year"] = df_h["Day of Year"].astype(int)

    # Generate lists of dates compatible with each row
    def list_of_dates(start_year, start_day, end_year, end_day):
        days = np.arange(start_day, (end_year - start_year) * 365 + end_day + 1, dtype=int)
        years = (days - 1) // 365 + int(start_year)
        days = (days - 1) % 365 + 1
        return [f"{year}-{day}" for year, day in zip(years, days)]

    df["Date"] = np.vectorize(list_of_dates, otypes=[list])(
        start_year=df["Harvest Start Year"],
        start_day=df["Harvest Start Day"],
        end_year=df["Harvest Start Year"] + np.where(df["Harvest Start Day"] == 1, 0, 1),
        end_day=np.where(df["Harvest Start Day"] == 1, 365, df["Harvest Start Day"] - 1),
    )
    # Make sure all the date lists are of length 365
    assert sum(np.vectorize(len)(df["Date"]) != 365) == 0

    # Rename Year to Bulk Harvest Year
    df = df.rename(columns={"Year": "Bulk Harvest Year"})

    # Explode the lists into rows
    df = df.explode("Date")

    # Convert dates into year / day of year
    df["Year"] = df["Date"].str[:4].astype(int)
    df["Day of Year"] = df["Date"].str[5:].astype(int)

    # Merge exploded timeseries data with production distributions
    df = pd.merge(df, df_h, how="left", on=["Area", "Day of Year"])

    # Remove days at which no harvesting takes place
    df = df[df["Daily Harvest Share"] > 0]

    # Finally calculate daily production
    for suffix in ["", " Trend", " Anomaly"]:
        df[f"Daily Production{suffix}"] = df[f"Production{suffix}"] * df["Daily Harvest Share"]
        df[f"Daily Production{suffix}"] = df[f"Daily Production{suffix}"].round(5)

    df = df[[
        "Area", "Year", "Day of Year", "Bulk Harvest Year", "Daily Harvest Share", 
        "Daily Production", "Daily Production Trend", "Daily Production Anomaly"
    ]]

    return df
