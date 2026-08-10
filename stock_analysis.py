"""
LVMH Analytics -- CLI entry point.

Runs the full pipeline: load data, align with benchmark, compute
returns/volatility/growth, run the event-window comparison, and save
a dashboard + summary stats. Importing this module no longer executes
anything -- run it directly (`python stock_analysis.py`) or call
`main()` yourself.

Usage:
    python stock_analysis.py --asset Data/LV.csv --benchmark Data/CAC40.csv \
        --benchmark-name "CAC 40" --window 20
"""

from __future__ import annotations

import argparse
import json

from lvmh_analysis import (
    load_prices,
    align_with_benchmark,
    add_returns,
    compute_volatility,
    yearly_volatility,
    compute_yearly_growth,
    benchmark_relative_stats,
    event_window_stats,
    build_dashboard,
    save_dashboard,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LVMH stock analytics pipeline")
    parser.add_argument("--asset", default="Data/LV.csv", help="Path to asset OHLCV CSV")
    parser.add_argument(
        "--benchmark", default="Data/BENCHMARK.csv", help="Path to benchmark OHLCV CSV"
    )
    parser.add_argument("--benchmark-name", default="CAC 40", help="Display name for benchmark")
    parser.add_argument("--window", type=int, default=20, help="Rolling volatility window (days)")
    parser.add_argument(
        "--output-dir", default=".", help="Directory to write dashboard.html and summary.json"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("LVMH ANALYTICS PIPELINE")
    print("=" * 60)

    asset = load_prices(args.asset)
    benchmark = load_prices(args.benchmark)

    asset = add_returns(asset)
    asset_vol = compute_volatility(asset, window=args.window)
    yearly_vol = yearly_volatility(asset)
    yearly_growth = compute_yearly_growth(asset)

    aligned = align_with_benchmark(asset, benchmark, benchmark_name=args.benchmark_name)
    rel_stats = benchmark_relative_stats(aligned, benchmark_col=f"{args.benchmark_name}_Close")
    event_stats = event_window_stats(aligned, benchmark_col=f"{args.benchmark_name}_Close")

    print("\n-- True (non-overlapping) annual volatility by year --")
    print(yearly_vol.to_string(index=False))

    print("\n-- Yearly growth --")
    print(yearly_growth.to_string(index=False))

    print(f"\n-- LVMH vs. {args.benchmark_name} --")
    for k, v in rel_stats.items():
        print(f"  {k}: {v:.2%}" if "return" in k or "vol" in k.lower() else f"  {k}: {v:.2f}")

    print("\n-- Named market-stress windows: asset vs. benchmark --")
    if not event_stats.empty:
        print(event_stats.to_string(index=False))
    else:
        print("  (no overlapping data for the defined event windows)")

    dashboard = build_dashboard(
        aligned,
        asset_vol,
        benchmark_col=f"{args.benchmark_name}_Close",
        benchmark_name=args.benchmark_name,
        volatility_col=f"Volatility_{args.window}d",
    )
    save_dashboard(dashboard, path=f"{args.output_dir}/dashboard.html")

    summary = {
        "benchmark_relative": rel_stats,
        "event_windows": event_stats.to_dict("records"),
        "yearly_volatility": yearly_vol.to_dict("records"),
        "yearly_growth": yearly_growth[["Year", "Yearly_Return"]].to_dict("records"),
    }
    with open(f"{args.output_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSummary saved to {args.output_dir}/summary.json")
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
