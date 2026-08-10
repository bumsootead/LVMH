from .data import load_prices, align_with_benchmark
from .metrics import (
    add_returns,
    compute_volatility,
    yearly_volatility,
    compute_yearly_growth,
    benchmark_relative_stats,
    event_window_stats,
    MARKET_EVENTS,
    bootstrap_excess_return,
)
try:
    from .plotting import build_dashboard, save_dashboard, build_cross_section_dashboard
except ImportError:  # plotly not installed -- data/metrics still usable
    build_dashboard = save_dashboard = build_cross_section_dashboard = None

__all__ = [
    "load_prices",
    "align_with_benchmark",
    "add_returns",
    "compute_volatility",
    "yearly_volatility",
    "compute_yearly_growth",
    "benchmark_relative_stats",
    "event_window_stats",
    "MARKET_EVENTS",
    "bootstrap_excess_return",
    "build_dashboard",
    "save_dashboard",
    "build_cross_section_dashboard",
]
