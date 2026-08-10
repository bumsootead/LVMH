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
    bootstrap_excess_return,
    build_cross_section_dashboard,
)
import os
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LVMH stock analytics pipeline")
    parser.add_argument(
        "--asset",
        nargs="+",
        default=["Data/LV.csv"],
        help="Path(s) to asset OHLCV CSV(s). Provide multiple for cross-sectional comparison",
    )
    parser.add_argument(
        "--benchmark", default="Data/BENCHMARK.csv", help="Path to benchmark OHLCV CSV"
    )
    parser.add_argument("--benchmark-name", default="CAC 40", help="Display name for benchmark")
    parser.add_argument("--window", type=int, default=20, help="Rolling volatility window (days)")
    parser.add_argument(
        "--output-dir", default=".", help="Directory to write dashboard.html and summary.json"
    )
    parser.add_argument(
        "--bootstrap-iterations", type=int, default=1000, help="Bootstrap iterations for excess-return CI"
    )
    parser.add_argument(
        "--ci", type=float, default=0.95, help="Confidence level for bootstrap CI (e.g. 0.95)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("LVMH ANALYTICS PIPELINE")
    print("=" * 60)

    benchmark = load_prices(args.benchmark)

    aligned_map = {}
    vol_map = {}
    summaries = []
    all_event_rows = []
    yearly_vols = {}
    yearly_growths = {}

    for asset_path in args.asset:
        name = os.path.splitext(os.path.basename(asset_path))[0]
        asset = load_prices(asset_path)
        asset = add_returns(asset)
        asset_vol = compute_volatility(asset, window=args.window)
        yearly_vol = yearly_volatility(asset)
        yearly_growth = compute_yearly_growth(asset)

        aligned = align_with_benchmark(asset, benchmark, benchmark_name=args.benchmark_name)

        rel_stats = benchmark_relative_stats(aligned, benchmark_col=f"{args.benchmark_name}_Close")
        boot = bootstrap_excess_return(
            aligned, benchmark_col=f"{args.benchmark_name}_Close", n_boot=args.bootstrap_iterations, ci=args.ci
        )
        event_stats = event_window_stats(aligned, benchmark_col=f"{args.benchmark_name}_Close")

        # record per-asset summary
        summary_row = {
            "Asset": name,
            "asset_total_return": rel_stats["asset_total_return"],
            "benchmark_total_return": rel_stats["benchmark_total_return"],
            "excess_return_point": rel_stats["excess_return"],
            "ci_lower": boot.get("ci_lower"),
            "ci_upper": boot.get("ci_upper"),
            "asset_annual_volatility": rel_stats["asset_annual_volatility"],
            "benchmark_annual_volatility": rel_stats["benchmark_annual_volatility"],
            "relative_volatility": rel_stats["relative_volatility"],
        }
        summaries.append(summary_row)

        # attach asset name to event rows
        if not event_stats.empty:
            df = event_stats.copy()
            df["Asset"] = name
            all_event_rows.append(df)

        aligned_map[name] = aligned
        vol_map[name] = asset_vol
        yearly_vols[name] = yearly_vol
        yearly_growths[name] = yearly_growth

        # console output for each asset
        print(f"\n-- {name}: True (non-overlapping) annual volatility by year --")
        print(yearly_vol.to_string(index=False))

        print(f"\n-- {name}: Yearly growth --")
        print(yearly_growth.to_string(index=False))

        print(f"\n-- {name} vs. {args.benchmark_name} --")
        for k, v in rel_stats.items():
            print(f"  {k}: {v:.2%}" if "return" in k or "vol" in k.lower() else f"  {k}: {v:.2f}")

    # combine event windows
    if all_event_rows:
        event_df = pd.concat(all_event_rows, ignore_index=True)
    else:
        event_df = pd.DataFrame()

    summary_df = pd.DataFrame(summaries)

    # Build dashboard: cross-section if available
    if build_cross_section_dashboard is not None:
        dashboard = build_cross_section_dashboard(
            aligned_map,
            vol_map,
            summary_df,
            event_df,
            benchmark_name=args.benchmark_name,
            volatility_col=f"Volatility_{args.window}d",
            title="Assets vs. Benchmark (cross-sectional)",
        )
        save_dashboard(dashboard, path=f"{args.output_dir}/dashboard.html")
    else:
        # fall back to single-asset dashboard if plotting unavailable
        # pick first asset
        first = next(iter(aligned_map))
        dashboard = build_dashboard(
            aligned_map[first],
            vol_map[first],
            benchmark_col=f"{args.benchmark_name}_Close",
            benchmark_name=args.benchmark_name,
            volatility_col=f"Volatility_{args.window}d",
        )
        save_dashboard(dashboard, path=f"{args.output_dir}/dashboard.html")

    summary = {
        "cross_section_summary": summaries,
        "event_windows": event_df.to_dict("records"),
        "yearly_volatility": {k: v.to_dict("records") for k, v in yearly_vols.items()},
        "yearly_growth": {k: v[["Year", "Yearly_Return"]].to_dict("records") for k, v in yearly_growths.items()},
    }
    with open(f"{args.output_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSummary saved to {args.output_dir}/summary.json")
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
