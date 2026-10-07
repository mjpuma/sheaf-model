import numpy as np
from numpy.core.fromnumeric import var
import pandas as pd
from patsy import dmatrix
import statsmodels.api as sm


def find_knots(t_min, t_max, knot_interval):
    n_knots = round((t_max - t_min) / knot_interval) - 1
    knots = np.linspace(t_min, t_max, num=n_knots+2)[1:-1]
    return knots

def find_frac(t_min, t_max, knot_interval):
    frac = min(1, 2 * knot_interval / (t_max - t_min))
    return frac


def fit_bsplines(df, x_var, y_var, knots, degree=3, robust=False):
    print(f"Fitting B-splines of degree {degree} ({'RLM' if robust else 'OLS'})",
          f"Number of fitted parameters: {len(knots) + degree + 1}")

    def bspline_transform(x):
        return dmatrix(f"bs(x, knots=knots, degree={degree})", {"x": x, "knots": knots},
                       return_type="dataframe")

    regression = sm.RLM if robust else sm.OLS
    model = regression(df[y_var], bspline_transform(df[x_var])).fit()

    def trend_function(x):
        return model.predict(bspline_transform(x))

    return trend_function


def fit_nsplines(df, x_var, y_var, knots, robust=False):
    print(f"Fitting natural cubic splines ({'RLM' if robust else 'OLS'}).",
          f"Number of fitted parameters: {len(knots)}" )

    def nspline_transform(x):
        return dmatrix(f"cr(x, knots=knots)", {"x": x, "knots": knots},
                       return_type="dataframe")

    regression = sm.RLM if robust else sm.OLS
    model = regression(df[y_var], nspline_transform(df[x_var])).fit()

    def trend_function(x):
        return model.predict(nspline_transform(x))

    return trend_function


def fit_lowess(df, x_var, y_var, frac, robust=False):
    print(f"Fitting{' robust ' if robust else ' '}LOWESS with frac = {frac:.3f}")

    def trend_function(x):
        return sm.nonparametric.lowess(df[y_var], df[x_var], frac=frac, it=3 if robust else 0, xvals=x.values)

    return trend_function


fit_functions = {
    "bsplines": fit_bsplines,
    "nsplines": fit_nsplines,
    "lowess": fit_lowess,
}


def detrend_timeseries(df, var_col, year_col="Year", model="lowess", knot_interval=10, robust=True, fit_period=None):
    assert model in ["nsplines", "bsplines", "lowess"]

    df[year_col] = df[year_col].astype(float)
    for area in df["Area"].unique():
        area_sel = df["Area"] == area
        df_area = df[area_sel]
        t_min, t_max = df_area[year_col].min(), df_area[year_col].max()
        if fit_period:
            t_min, t_max = max(t_min, fit_period[0]), min(t_max, fit_period[1])
        year_sel = (t_min <= df_area[year_col]) & (df_area[year_col] <= t_max)
        if t_max == t_min:
            print(f"Only one datapoint for {area}")
            df.loc[area_sel, f"{var_col} Trend"] = df[var_col]
            continue
        print(f"Fitting {var_col} for {area}")
        fit_kwargs = {"robust": robust}
        if "splines" in model:
            fit_kwargs["knots"] = find_knots(t_min, t_max, knot_interval)
        if model == "lowess":
            fit_kwargs["frac"] = find_frac(t_min, t_max, knot_interval)
        fit_function = fit_functions[model]
        trend_function = fit_function(df_area[year_sel], year_col, var_col, **fit_kwargs)
        df.loc[area_sel, f"{var_col} Trend"] = np.maximum(trend_function(df_area[year_col]) , 0)
    df[year_col] = df[year_col].astype("Int64")

    df[f"{var_col} Anomaly"] = df[var_col] - df[f"{var_col} Trend"]
    var_cols = [col for col in df.columns if var_col in col]
    df[var_cols] = df[var_cols].round(3)

    return df
