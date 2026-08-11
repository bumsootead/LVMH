# LVMH vs. Market: Does the Valuation Premium Hold Up?

**Business question:** LVMH has traded at a persistent premium to the broader
market, on the thesis that luxury demand is more resilient through downturns.
Does the stock's actual risk/return history support that thesis, or has its
risk profile shifted in a way that undercuts it?

This project analyzes LVMH price data (2000–2026) **relative to a benchmark**
(CAC 40 by default) rather than in isolation, and segments the comparison by
named market-stress events instead of calendar years alone.

## Key Findings

**26-year performance (2000–2026):**
- **LVMH total return:** 1,388% vs. **CAC-40 total return:** 130%
- **Excess return:** 1,258 percentage points — LVMH vastly outperformed the market.
- **LVMH annualized return:** ~13.5% vs. **CAC-40:** ~3.4%

**Risk comparison:**
- **LVMH annualized volatility:** 28.6% vs. **CAC-40:** 20.8% (1.37× higher risk)
- **Excess volatility:** The higher returns came with real extra risk.
- **Risk-adjusted verdict:** LVMH's excess return far outpaced the excess volatility, suggesting the luxury premium was *genuine*, not compensation for measurable risk alone.

**Bootstrap confidence interval (95% CI):**
- Excess return: [0.3%, 194%] — very wide due to 26-year compounding, but the lower bound is still significantly positive.
- **Interpretation:** We're 95% confident the true excess return is positive, but precise long-term estimates are inherently uncertain.

**Event-window performance:** See `graphs/top3_excess_ci.png` and `graphs/event_relative_returns.png`.
- LVMH typically outperformed CAC-40 during both crises and calm periods, though magnitude varied.
- Dot-com (2000–02), 2008, COVID (2020–21), 2022 rate-hike selloff all tracked.

## Methodology

### Why Bootstrap?

**Traditional statistical methods fail for financial returns because:**

1. **Returns aren't normally distributed** — they have "fat tails": extreme events (crashes, rallies) occur far more often than a bell curve predicts. Assuming normality gives wrong confidence intervals.

2. **Total return over 26 years is nonlinear** — it compounds: `Total Return = (1 + r₁) × (1 + r₂) × ... × (1 + r₆₅₀₀)`. No simple formula can compute uncertainty in this.

3. **Temporal structure matters** — daily returns are correlated (clustering in volatile and calm periods). A naive random shuffle destroys this and produces misleading confidence intervals.

**Bootstrap solution:**
- Resample paired daily returns (LVMH and CAC-40 on the same dates) *with replacement* 10,000 times.
- For each sample, compound the returns to get total return.
- Compute percentiles (2.5th and 97.5th) to get a 95% confidence interval.
- Result: confidence intervals built from *actual observed behavior*, not assumptions.

See `lvmh_analysis/metrics.py::bootstrap_excess_return()` for implementation.

### Data & Alignment

Adjusted close prices are used (not raw close) so returns and volatility aren't distorted by dividend payments or stock splits over a 26-year window. See `lvmh_analysis/data.py::load_prices`.

**Benchmark alignment:** When asset and benchmark have mismatched trading calendars (e.g., LVMH trades on Euronext, CAC-40 index data may have different coverage), an inner join on Date is performed to keep only matching dates. This may drop ~1–2% of rows but ensures apples-to-apples comparison.

### Volatility

Two measures are computed and kept separate on purpose:
- **Rolling 20-day annualized volatility** (`Volatility_20d`) — for time-series plots. Shows how risk *changes* over time. Not directly comparable across years because overlapping windows are autocorrelated, but useful for spotting crises.
- **True non-overlapping annualized volatility per calendar year** — the correct series for "was year X more volatile than year Y?" comparisons.

### Returns

**Excess return** = Asset total return − Benchmark total return.
- Measures outperformance net of market movement.
- Paired with volatility to assess whether extra return compensated for extra risk.

**Daily returns** are computed as log-returns (`ln(Price_today / Price_yesterday)`) for numerical stability when compounding over long periods.

### Event Windows

Instead of calendar-year bucketing, specific market-stress periods are tagged:
- **Dot-com crash** (2000–02-28): tech bubble burst.
- **2008 financial crisis** (2007-09-01 to 2009-03-31): subprime/credit crisis.
- **COVID crash & recovery** (2020-02-15 to 2021-03-31): pandemic shock and recovery.
- **2022 rate-hike selloff** (2022-01-01 to 2022-10-31): Fed tightening.

For each window, LVMH and CAC-40 returns are compared. See `MARKET_EVENTS` in `metrics.py` and `event_relative_returns.png`.

### Volume Forecasting (Time-Aware)

A secondary model trains on historical volume to forecast future trading volume. Key properties:
- **Chronological train/test split:** First 80% of dates for training, last 20% for testing (simulates real forecasting).
- **Walk-forward validation:** Model is retrained as time progresses, avoiding "future leakage."
- **Naive baseline:** Average historical volume. Any predictive model should beat this; if not, it's overfit.

See `scripts/train_volume_model.py` for details.


## Project Structure

```
LVMH/
├── Data/
│   ├── LV.csv                  # LVMH OHLCV (2000–2026)
│   └── CAC40.csv               # e.g. CAC 40 benchmark, same schema (Date,Open,High,Low,Close,Volume)
├── lvmh_analysis/
│   ├── data.py                 # loading, cleaning, benchmark alignment
│   ├── metrics.py              # returns, volatility, growth, event stats
│   └── plotting.py             # interactive dashboard (Plotly)
├── stock_analysis.py           # CLI entry point (main() guard)
├── tests/
│   └── test_metrics.py         # unit tests against known values
├── requirements.txt
└── README.md
```


## Running It

```bash
pip install -r requirements.txt
python stock_analysis.py --asset Data/LV.csv --benchmark /path/to/benchmark.csv \
    --benchmark-name "CAC 40" --window 20
```

## License

MIT

## Author

BumSoo Jeong — [GitHub Profile](https://github.com/bumsootead)
