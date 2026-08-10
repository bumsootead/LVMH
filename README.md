# LVMH vs. Market: Does the Valuation Premium Hold Up?

**Business question:** LVMH has traded at a persistent premium to the broader
market, on the thesis that luxury demand is more resilient through downturns.
Does the stock's actual risk/return history support that thesis, or has its
risk profile shifted in a way that undercuts it?

This project analyzes LVMH price data (2000–2026) **relative to a benchmark**
(CAC 40 by default) rather than in isolation, and segments the comparison by
named market-stress events instead of calendar years alone.

## Key Findings

*(Populate this section after running the pipeline on your data — see
Methodology below for how each number is derived. Do not report a return or
volatility figure here without the paired benchmark number next to it.)*

- Total return vs. benchmark: `asset_total_return` vs. `benchmark_total_return`
  (`stock_analysis.py` output / `summary.json`)
- Relative volatility: `relative_volatility` — was the extra risk (if any)
  compensated by excess return?
- Event-window performance: how LVMH moved vs. the benchmark during the
  dot-com crash, 2008, COVID, and the 2022 rate-hike selloff
  (`event_window_stats` in `summary.json`)

## Methodology

**Data.** Adjusted close is used (not raw close) so returns and volatility
aren't distorted by dividend payments or stock splits over a 26-year window.
See `lvmh_analysis/data.py::load_prices`.

**Volatility.** Two measures are computed and kept separate on purpose:
- A rolling 20-day annualized volatility (`Volatility_20d`), for the
  time-series plot — this is *not* directly comparable across years, since
  overlapping windows are autocorrelated.
- A true non-overlapping annualized volatility per calendar year
  (`yearly_volatility()`), which is the correct series for any "was year X
  more volatile than year Y" comparison.

**Growth.** Simple open-to-close yearly return, plus total return over the
full period, both benchmarked against the comparison index rather than
reported standalone.

**Event segmentation.** Instead of "2001, 2002, 2008 were volatile years,"
the analysis tags specific market-stress windows (dot-com crash, 2008
crisis, COVID crash/recovery, 2022 rate-hike selloff) and compares asset vs.
benchmark return within each. See `MARKET_EVENTS` in `metrics.py`.

## Limitations

Stated explicitly, because a number without its limits is a claim, not a
finding:

- **Single asset, single benchmark.** No cross-sectional comparison to other
  luxury peers (Kering, Richemont, Hermès). "Typical for the sector" is not
  demonstrated here — only "different from one broad index."
- **No significance testing.** Return and volatility comparisons are point
  estimates, not accompanied by confidence intervals or hypothesis tests.
  Don't read a modest excess-return number as necessarily distinguishable
  from noise.
- **No causal claims.** Event-window returns are descriptive correlation
  with known stress periods, not an estimate of LVMH's causal sensitivity to
  those shocks (that would need a proper event-study or regression design).
- **Data quality.** Adjusted close corrects for dividends/splits but the
  underlying CSV's provenance (source, corporate-action accuracy) isn't
  independently verified here.

## Project Structure

```
LVMH/
├── Data/
│   ├── LV.csv                  # LVMH OHLCV (+ Adj Close if available)
│   └── BENCHMARK.csv           # e.g. CAC 40, same schema
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

Outputs `dashboard.html` (interactive price/volatility view with event
windows shaded) and `summary.json` (all computed stats).

Run tests with:

```bash
pytest tests/
```
## License

MIT

## Author

BumSoo Jeong — [GitHub Profile](https://github.com/bumsootead)
