"""Generate PNG graphs (matplotlib) for each asset and cross-sectional charts, save in graphs/.
Creates:
 - graphs/{asset}_price_stats.png  (2x2 mean±std)
 - graphs/normalized_prices.png    (normalized overlay of assets)
 - graphs/event_relative_returns.png (bar chart of event relative returns)
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

from lvmh_analysis.data import load_prices, align_with_benchmark
from lvmh_analysis.metrics import add_returns, event_window_stats


def save_price_stats(df, out_path, title="Price Stats"):
    df = df.sort_values("Date").reset_index(drop=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    cols = ["Open", "High", "Low", "Close"]
    colors = ["tab:blue", "tab:green", "tab:orange", "tab:purple"]

    for i, col in enumerate(cols):
        ax = axes[i // 2, i % 2]
        mean_val = df[col].mean()
        std_val = df[col].std()
        ax.plot(df.index, df[col], marker='o', markersize=3, linestyle='-', color=colors[i], alpha=0.7)
        ax.axhline(mean_val, color='r', linestyle='--')
        ax.fill_between(df.index, mean_val - std_val, mean_val + std_val, color=colors[i], alpha=0.1)
        ax.set_title(f"{col} (mean={mean_val:.2f}, std={std_val:.2f})")
        ax.set_xlabel("Date Index")
        ax.set_ylabel("Price")
        ax.grid(alpha=0.3)

    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path)
    plt.close(fig)


def save_normalized_overlay(aligned_map, out_path, title="Normalized Prices"):
    plt.figure(figsize=(12, 6))
    for name, df in aligned_map.items():
        norm = df['Close'] / df['Close'].iloc[0] * 100
        plt.plot(df['Date'], norm, label=name)
    plt.legend()
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Index (start = 100)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def save_event_bars(event_df, out_path, title='Event-window relative returns'):
    if event_df.empty:
        return
    pivot = event_df.pivot(index='Event', columns='Asset', values='Relative_Return')
    ax = pivot.plot(kind='bar', figsize=(12, 6))
    ax.set_ylabel('Relative return')
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main(assets=None, benchmark='Data/CAC40.csv', out_dir='graphs'):
    os.makedirs(out_dir, exist_ok=True)
    if assets is None:
        assets = ['Data/LV.csv']

    benchmark_df = load_prices(benchmark)

    aligned_map = {}
    all_event_rows = []

    for asset_path in assets:
        name = os.path.splitext(os.path.basename(asset_path))[0]
        df = load_prices(asset_path)
        save_price_stats(df, os.path.join(out_dir, f"{name}_price_stats.png"), title=f"{name} Price Stats")

        aligned = align_with_benchmark(df, benchmark_df, benchmark_name='Benchmark')
        aligned_map[name] = aligned
        events = event_window_stats(aligned, benchmark_col='Benchmark_Close')
        if not events.empty:
            events['Asset'] = name
            all_event_rows.append(events)

    # normalized overlay
    save_normalized_overlay(aligned_map, os.path.join(out_dir, 'normalized_prices.png'))

    # event bars
    if all_event_rows:
        merged_events = pd.concat(all_event_rows, ignore_index=True)
    else:
        merged_events = pd.DataFrame()
    save_event_bars(merged_events, os.path.join(out_dir, 'event_relative_returns.png'))

    print(f"Saved graphs to {out_dir}")


if __name__ == '__main__':
    # default assets: LV and BENCHMARK copy if present
    asset_list = ['Data/LV.csv']
    if os.path.exists('Data/CAC40.csv'):
        asset_list.append('Data/CAC40.csv')
    main(assets=asset_list)
