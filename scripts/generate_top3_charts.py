"""Generate three dashboard-style PNGs:
- normalized_overlay.png
- rolling_volatility.png
- cross_section_excess_ci.png

Saves files to graphs/.
"""
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd

from lvmh_analysis.data import load_prices, align_with_benchmark
from lvmh_analysis.metrics import compute_volatility, bootstrap_excess_return


def plot_normalized_overlay(aligned_asset, benchmark_col, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(12, 6))
    asset_norm = aligned_asset['Close'] / aligned_asset['Close'].iloc[0] * 100
    bench_norm = aligned_asset[benchmark_col] / aligned_asset[benchmark_col].iloc[0] * 100
    plt.plot(aligned_asset['Date'], asset_norm, label='Asset', lw=1.25)
    plt.plot(aligned_asset['Date'], bench_norm, label='Benchmark', lw=1.0, alpha=0.8)
    plt.title('Normalized cumulative returns (start = 100)')
    plt.xlabel('Date')
    plt.ylabel('Index (start = 100)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_rolling_volatility(df, window, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    vol_df = compute_volatility(df, window=window)
    plt.figure(figsize=(12, 5))
    plt.plot(vol_df['Date'], vol_df[f'Volatility_{window}d'] * 100, color='#7b3fa0')
    plt.fill_between(vol_df['Date'], 0, vol_df[f'Volatility_{window}d'] * 100, color='#7b3fa0', alpha=0.15)
    plt.title(f'Rolling {window}-day annualized volatility (%)')
    plt.xlabel('Date')
    plt.ylabel('Volatility (%)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_cross_section_excess(assets, benchmark_path, out_path, n_boot=2000):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bench_df = load_prices(benchmark_path)
    results = []
    for asset_path in assets:
        name = os.path.splitext(os.path.basename(asset_path))[0]
        df = load_prices(asset_path)
        aligned = align_with_benchmark(df, bench_df, benchmark_name='Benchmark')
        res = bootstrap_excess_return(aligned, benchmark_col='Benchmark_Close', n_boot=n_boot, ci=0.95, random_state=1)
        results.append({'Asset': name, 'point': res['point_estimate'] * 100, 'ci_lower': res['ci_lower'] * 100, 'ci_upper': res['ci_upper'] * 100})

    # Include benchmark as zero baseline
    bench_name = os.path.splitext(os.path.basename(benchmark_path))[0]
    results.append({'Asset': bench_name, 'point': 0.0, 'ci_lower': 0.0, 'ci_upper': 0.0})

    df_res = pd.DataFrame(results).set_index('Asset')
    df_res['err_low'] = df_res['point'] - df_res['ci_lower']
    df_res['err_high'] = df_res['ci_upper'] - df_res['point']

    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    df_res['point'].plot(kind='bar', yerr=[df_res['err_low'], df_res['err_high']], capsize=6, color=['#1f77b4' if i==len(df_res)-1 else '#ff7f0e' for i in range(len(df_res))])
    plt.axhline(0, color='k', linewidth=0.8)
    plt.ylabel('Excess total return (%)')
    plt.title('Cross-sectional excess total return vs. benchmark (95% CI)')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


if __name__ == '__main__':
    out_dir = 'graphs'
    os.makedirs(out_dir, exist_ok=True)

    # find asset files in Data/ (exclude CAC40.csv which is the benchmark)
    data_files = sorted(glob.glob('Data/*.csv'))
    benchmark = None
    assets = []
    for p in data_files:
        if os.path.basename(p).upper().startswith('CAC40') or os.path.basename(p).upper().startswith('BENCHMARK'):
            benchmark = p
        else:
            assets.append(p)

    if benchmark is None:
        # fallback to first CSV as benchmark
        if data_files:
            benchmark = data_files[0]
        else:
            raise SystemExit('No CSV files found in Data/')

    # pick first asset for time-series plots
    primary_asset = assets[0] if assets else benchmark

    # normalized overlay
    df_asset = load_prices(primary_asset)
    aligned = align_with_benchmark(df_asset, load_prices(benchmark), benchmark_name='Benchmark')
    plot_normalized_overlay(aligned, 'Benchmark_Close', os.path.join(out_dir, 'top3_normalized_overlay.png'))

    # rolling volatility
    plot_rolling_volatility(df_asset, window=20, out_path=os.path.join(out_dir, 'top3_rolling_volatility.png'))

    # cross-section CI bar
    plot_cross_section_excess(assets if assets else [primary_asset], benchmark, os.path.join(out_dir, 'top3_excess_ci.png'))

    print('Top-3 charts saved to', out_dir)
