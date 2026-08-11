import os
import json
from lvmh_analysis.data import load_prices, align_with_benchmark
from lvmh_analysis.metrics import benchmark_relative_stats, bootstrap_excess_return, compute_volatility

repo_root = os.getcwd()
asset_path = 'Data/LV.csv'
benchmark_path = 'Data/CAC40.csv'

asset = load_prices(asset_path)
benchmark = load_prices(benchmark_path)
aligned = align_with_benchmark(asset, benchmark, benchmark_name='Benchmark')

stats = benchmark_relative_stats(aligned, benchmark_col='Benchmark_Close')
boot = bootstrap_excess_return(aligned, benchmark_col='Benchmark_Close', n_boot=2000, ci=0.95, random_state=1)

vol = compute_volatility(asset, window=20)
latest_vol = vol[f'Volatility_20d'].iloc[-1] if not vol.empty else None

out = {
    'asset_total_return': stats['asset_total_return'],
    'benchmark_total_return': stats['benchmark_total_return'],
    'excess_return': stats['excess_return'],
    'asset_annual_volatility': stats['asset_annual_volatility'],
    'benchmark_annual_volatility': stats['benchmark_annual_volatility'],
    'relative_volatility': stats['relative_volatility'],
    'bootstrap_point': boot['point_estimate'],
    'bootstrap_ci_lower': boot['ci_lower'],
    'bootstrap_ci_upper': boot['ci_upper'],
    'latest_rolling_volatility': float(latest_vol) if latest_vol is not None else None
}
print(json.dumps(out, indent=2))
