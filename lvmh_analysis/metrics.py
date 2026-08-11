"""
Pure calculation functions for the LVMH analytics project.

Every function here takes a DataFrame in, returns a DataFrame or dict
out, and has no side effects (no printing, no plotting, no file I/O).
That's what lets tests/test_metrics.py check known values, and lets
the CLI / notebooks reuse the same logic without re-implementing it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

# Named market-stress windows used for business-relevant segmentation,
# rather than segmenting purely by calendar year. Dates are approximate
# peak-to-trough stress windows -- adjust to taste.
MARKET_EVENTS = {
    "Dot-com crash": ("2000-03-01", "2002-10-31"),
    "2008 financial crisis": ("2008-09-01", "2009-03-31"),
    "COVID crash": ("2020-02-15", "2020-03-31"),
    "COVID recovery": ("2020-04-01", "2021-12-31"),
    "2022 rate-hike selloff": ("2022-01-01", "2022-10-31"),
}


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add a daily simple-return column. Does not mutate the input."""
    df = df.copy()
    df["Returns"] = df["Close"].pct_change()
    return df


def compute_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add rolling annualized volatility columns.

    NOTE ON METHODOLOGY: the rolling `window`-day std is itself
    autocorrelated (each window overlaps the next by window-1 days),
    so naively averaging it within a calendar year is NOT the same as
    that year's true annualized volatility -- the effective sample
    size is smaller than the row count suggests. We keep the rolling
    series here for the time-series plot, and compute a *separate*,
    non-overlapping per-year volatility in `yearly_volatility()` below
    for any year-over-year comparison claim.
    """
    df = df.copy()
    if "Returns" not in df.columns:
        df = add_returns(df)
    df[f"Volatility_{window}d"] = (
        df["Returns"].rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    )
    return df


def yearly_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Compute true (non-overlapping) annualized volatility per calendar year.

    This is std of *that year's* daily returns, annualized -- the
    statistically defensible version of "volatility by year," as
    opposed to averaging an overlapping rolling window.
    """
    df = df.copy()
    if "Returns" not in df.columns:
        df = add_returns(df)
    df["Year"] = df["Date"].dt.year
    yearly = (
        df.groupby("Year")["Returns"]
        .std()
        .mul(np.sqrt(TRADING_DAYS_PER_YEAR))
        .rename("Annual_Volatility")
        .reset_index()
    )
    return yearly


def compute_yearly_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly open-to-close return per calendar year."""
    df = df.copy()
    df["Year"] = df["Date"].dt.year
    yearly = df.groupby("Year").agg(
        Open=("Open", "first"), Close=("Close", "last"), Volume=("Volume", "mean")
    ).reset_index()
    yearly["Yearly_Return"] = (yearly["Close"] - yearly["Open"]) / yearly["Open"]
    return yearly


def benchmark_relative_stats(
    aligned: pd.DataFrame, benchmark_col: str = "Benchmark_Close"
) -> dict:
    """Compare asset vs. benchmark total return and volatility.

    `aligned` must have Date, Close, and `benchmark_col` (output of
    data.align_with_benchmark). This is the calculation that turns
    "880% total return" from an unsupported claim into a supported one.
    """
    aligned = aligned.copy()
    aligned["Asset_Return"] = aligned["Close"].pct_change()
    aligned["Benchmark_Return"] = aligned[benchmark_col].pct_change()

    asset_total = aligned["Close"].iloc[-1] / aligned["Close"].iloc[0] - 1
    bench_total = aligned[benchmark_col].iloc[-1] / aligned[benchmark_col].iloc[0] - 1

    asset_vol = aligned["Asset_Return"].std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    bench_vol = aligned["Benchmark_Return"].std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Simple excess-return / relative-vol framing -- not a full CAPM beta,
    # but enough to answer "did the extra risk pay off."
    excess_return = asset_total - bench_total
    relative_vol = asset_vol / bench_vol if bench_vol else float("nan")

    return {
        "asset_total_return": asset_total,
        "benchmark_total_return": bench_total,
        "excess_return": excess_return,
        "asset_annual_volatility": asset_vol,
        "benchmark_annual_volatility": bench_vol,
        "relative_volatility": relative_vol,
    }


def bootstrap_excess_return(
    aligned: pd.DataFrame,
    benchmark_col: str = "Benchmark_Close",
    n_boot: int = 1000,
    ci: float = 0.95,
    random_state: int | None = None,
    use_log_returns: bool = False,
    annualize: bool = False,
) -> dict:
    """Bootstrap a confidence interval for excess return.

    Options:
    - use_log_returns: resample log(1+r) and aggregate by summation (more stable for compounding).
    - annualize: return CI for annualized excess return instead of period total.

    Resamples paired daily returns with replacement and computes the
    distribution of excess returns (asset - benchmark) according to options.

    Returns a dict with point_estimate, ci_lower, ci_upper, and samples.
    """
    aligned = aligned.copy()
    aligned = add_returns(aligned)
    aligned["Benchmark_Return"] = aligned[benchmark_col].pct_change()

    # drop the first NaN return
    returns = aligned[["Returns", "Benchmark_Return"]].dropna().reset_index(drop=True)
    if returns.empty:
        return {"point_estimate": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan"), "samples": []}

    rng = np.random.RandomState(random_state)
    n = len(returns)
    samples = np.empty(n_boot)

    for i in range(n_boot):
        idx = rng.randint(0, n, size=n)
        ar = returns["Returns"].iloc[idx].to_numpy()
        br = returns["Benchmark_Return"].iloc[idx].to_numpy()

        if use_log_returns:
            # sum log returns then convert back
            lar = np.log1p(ar)
            lbr = np.log1p(br)
            asset_total = np.expm1(lar.sum())
            bench_total = np.expm1(lbr.sum())
        else:
            asset_total = np.prod(1 + ar) - 1
            bench_total = np.prod(1 + br) - 1

        if annualize:
            # convert period total to annualized rate based on number of trading days
            if n > 0:
                asset_ann = (1 + asset_total) ** (TRADING_DAYS_PER_YEAR / n) - 1
                bench_ann = (1 + bench_total) ** (TRADING_DAYS_PER_YEAR / n) - 1
                samples[i] = asset_ann - bench_ann
            else:
                samples[i] = 0.0
        else:
            samples[i] = asset_total - bench_total

    lower_p = (1 - ci) / 2 * 100
    upper_p = (1 + ci) / 2 * 100
    ci_lower = np.percentile(samples, lower_p)
    ci_upper = np.percentile(samples, upper_p)

    # point estimate using the full series, computed the same way as samples
    if use_log_returns:
        full_asset = np.expm1(np.log1p(aligned['Returns'].dropna()).sum()) if not aligned['Returns'].dropna().empty else float('nan')
        full_bench = np.expm1(np.log1p(aligned[benchmark_col].pct_change().dropna()).sum()) if not aligned[benchmark_col].pct_change().dropna().empty else float('nan')
    else:
        full_asset = aligned["Close"].iloc[-1] / aligned["Close"].iloc[0] - 1
        full_bench = aligned[benchmark_col].iloc[-1] / aligned[benchmark_col].iloc[0] - 1

    if annualize and not np.isnan(full_asset) and not np.isnan(full_bench):
        full_asset = (1 + full_asset) ** (TRADING_DAYS_PER_YEAR / n) - 1
        full_bench = (1 + full_bench) ** (TRADING_DAYS_PER_YEAR / n) - 1

    point = full_asset - full_bench

    return {
        "point_estimate": float(point),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "samples": samples.tolist(),
        "n_boot": n_boot,
        "use_log_returns": use_log_returns,
        "annualize": annualize,
    }


def event_window_stats(
    aligned: pd.DataFrame, benchmark_col: str = "Benchmark_Close"
) -> pd.DataFrame:
    """Return per-event asset vs. benchmark return, for MARKET_EVENTS.

    This replaces "volatility was high in 2008" with an actual
    comparison: how did the asset move relative to the benchmark
    during each named stress window.
    """
    rows = []
    for name, (start, end) in MARKET_EVENTS.items():
        window = aligned[(aligned["Date"] >= start) & (aligned["Date"] <= end)]
        if len(window) < 2:
            continue
        asset_ret = window["Close"].iloc[-1] / window["Close"].iloc[0] - 1
        bench_ret = window[benchmark_col].iloc[-1] / window[benchmark_col].iloc[0] - 1
        rows.append(
            {
                "Event": name,
                "Start": start,
                "End": end,
                "Asset_Return": asset_ret,
                "Benchmark_Return": bench_ret,
                "Relative_Return": asset_ret - bench_ret,
            }
        )
    return pd.DataFrame(rows)
