"""
Data loading utilities for the LVMH analytics project.

Handles:
- Loading and cleaning a single OHLCV CSV (LVMH or a benchmark)
- Aligning LVMH with a benchmark series on shared trading dates
- Flagging (not silently dropping) rows that need attention

Expected CSV schema (matches the original repo's Data/LV.csv):
    Date, Open, High, Low, Close, Volume

If your CSV has an "Adj Close" column (e.g. pulled via yfinance with
auto_adjust=False), pass adjusted=True and it will be used in place of
Close for return/volatility calculations. This matters a lot for a
26-year single-stock history: unadjusted Close through multiple
dividend payments will distort returns and volatility.
"""

from __future__ import annotations

import pandas as pd


def load_prices(path: str, adjusted: bool = True) -> pd.DataFrame:
    """Load a single OHLCV CSV and return a cleaned, sorted DataFrame.

    Parameters
    ----------
    path : str
        Path to the CSV file.
    adjusted : bool
        If True and an "Adj Close" column is present, use it as the
        `Close` column for downstream calculations (recommended for
        return/volatility work). If the column is absent, this is a
        no-op and a warning is printed, since unadjusted prices will
        understate volatility around ex-dividend dates and distort
        returns around any stock splits.

    Returns
    -------
    pd.DataFrame with columns: Date, Open, High, Low, Close, Volume
    (Close reflects adjusted price if available and requested).
    """
    df = pd.read_csv(path)

    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Flag rather than silently drop -- zero-volume rows can be holidays,
    # data errors, or (rarely) genuine no-trade days. Surface the count
    # so it's a documented decision, not a hidden one.
    zero_volume = (df["Volume"] == 0).sum()
    if zero_volume:
        print(f"[data] {path}: dropping {zero_volume} zero-volume rows")
    df = df[df["Volume"] > 0].reset_index(drop=True)

    if adjusted and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]
    elif adjusted:
        print(
            f"[data] WARNING: {path} has no 'Adj Close' column -- using "
            "raw Close. Returns/volatility will be distorted around "
            "dividend and split dates."
        )

    # Basic duplicate/gap sanity check -- surfaced, not silently fixed.
    dup_dates = df["Date"].duplicated().sum()
    if dup_dates:
        print(f"[data] WARNING: {path} has {dup_dates} duplicate dates")

    return df


def align_with_benchmark(
    asset: pd.DataFrame, benchmark: pd.DataFrame, benchmark_name: str = "Benchmark"
) -> pd.DataFrame:
    """Inner-join asset and benchmark on Date, keeping Close for each.

    Returns a DataFrame with columns: Date, Close, Benchmark_Close
    (asset's own columns are dropped down to Close for simplicity --
    re-merge on Date if you need OHLV for the asset too).
    """
    merged = pd.merge(
        asset[["Date", "Close"]],
        benchmark[["Date", "Close"]].rename(columns={"Close": f"{benchmark_name}_Close"}),
        on="Date",
        how="inner",
    )
    dropped = len(asset) - len(merged)
    if dropped:
        print(
            f"[data] Aligning to shared trading days dropped {dropped} "
            f"asset rows with no matching {benchmark_name} date"
        )
    return merged
