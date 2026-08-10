"""
Unit tests for lvmh_analysis.metrics, using small synthetic DataFrames
with hand-computable answers -- not the full LV.csv. Run with:
    pytest tests/
"""

import numpy as np
import pandas as pd
import pytest

from lvmh_analysis.metrics import (
    add_returns,
    compute_yearly_growth,
    yearly_volatility,
    benchmark_relative_stats,
)


def make_prices(closes, start="2020-01-01"):
    dates = pd.bdate_range(start=start, periods=len(closes))
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": [1000] * len(closes),
        }
    )


def test_add_returns_known_values():
    df = make_prices([100, 110, 99])
    df = add_returns(df)
    assert df["Returns"].iloc[0] != df["Returns"].iloc[0]  # first is NaN
    assert df["Returns"].iloc[1] == pytest.approx(0.10)
    assert df["Returns"].iloc[2] == pytest.approx(-0.10, rel=1e-2)


def test_yearly_growth_open_to_close():
    # Two years: year 1 open 100 -> close 120 (+20%), year 2 open 120 -> close 90 (-25%)
    closes_2020 = [100] + [110] * 249 + [120]  # first Open=100, last Close=120
    closes_2021 = [120] + [100] * 249 + [90]
    df1 = make_prices(closes_2020, start="2020-01-01")
    df2 = make_prices(closes_2021, start="2021-01-01")
    df = pd.concat([df1, df2], ignore_index=True)
    growth = compute_yearly_growth(df)
    assert growth.loc[growth["Year"] == 2020, "Yearly_Return"].iloc[0] == pytest.approx(0.20)
    assert growth.loc[growth["Year"] == 2021, "Yearly_Return"].iloc[0] == pytest.approx(-0.25)


def test_yearly_volatility_matches_manual_std():
    # Deterministic small return series within a single year.
    closes = [100, 101, 99, 102, 98, 103]
    df = make_prices(closes)
    result = yearly_volatility(df)
    df_with_returns = add_returns(df)
    expected = df_with_returns["Returns"].std() * np.sqrt(252)
    assert result["Annual_Volatility"].iloc[0] == pytest.approx(expected)


def test_benchmark_relative_stats_excess_return():
    aligned = pd.DataFrame(
        {
            "Date": pd.bdate_range("2020-01-01", periods=3),
            "Close": [100, 110, 121],  # +21% total
            "Benchmark_Close": [100, 105, 110],  # +10% total
        }
    )
    stats = benchmark_relative_stats(aligned, benchmark_col="Benchmark_Close")
    assert stats["asset_total_return"] == pytest.approx(0.21)
    assert stats["benchmark_total_return"] == pytest.approx(0.10)
    assert stats["excess_return"] == pytest.approx(0.11)


def test_missing_columns_raises():
    from lvmh_analysis.data import load_prices
    import tempfile, os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("Date,Open,Close\n2020-01-01,100,101\n")
        path = f.name
    try:
        with pytest.raises(ValueError):
            load_prices(path)
    finally:
        os.remove(path)
