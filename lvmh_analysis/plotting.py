"""
Visualization for the LVMH analytics project.

One consolidated dashboard (Plotly, interactive, single HTML file) is
the centerpiece artifact instead of several static matplotlib subplot
grids -- easier to share, easier to explore, and it's what an analytics
reviewer expects to see linked from a README.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .metrics import MARKET_EVENTS


def build_dashboard(
    aligned: pd.DataFrame,
    vol_df: pd.DataFrame,
    benchmark_col: str = "Benchmark_Close",
    benchmark_name: str = "Benchmark",
    volatility_col: str = "Volatility_20d",
    title: str = "LVMH vs. Benchmark",
) -> go.Figure:
    """Build a single interactive dashboard: normalized price overlay
    (top) and rolling volatility (bottom), with named market-stress
    windows shaded on both panels.

    Parameters
    ----------
    aligned : DataFrame with Date, Close, and `benchmark_col`
        (output of data.align_with_benchmark)
    vol_df : DataFrame with Date and `volatility_col`
        (output of metrics.compute_volatility, on the asset)
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.06,
        subplot_titles=(
            "Normalized Price (rebased to 100 at start)",
            "Rolling 20-Day Annualized Volatility",
        ),
    )

    # Normalize both series to 100 at the first shared date so relative
    # performance is directly readable, independent of price scale.
    norm_asset = aligned["Close"] / aligned["Close"].iloc[0] * 100
    norm_bench = aligned[benchmark_col] / aligned[benchmark_col].iloc[0] * 100

    fig.add_trace(
        go.Scatter(x=aligned["Date"], y=norm_asset, name="LVMH", line=dict(color="#2c7a4b")),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=aligned["Date"], y=norm_bench, name=benchmark_name, line=dict(color="#888888")
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=vol_df["Date"],
            y=vol_df[volatility_col] * 100,
            name="Volatility (%)",
            line=dict(color="#7b3fa0"),
            fill="tozeroy",
        ),
        row=2,
        col=1,
    )

    # Shade named market-stress windows across both panels.
    for name, (start, end) in MARKET_EVENTS.items():
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor="red",
            opacity=0.07,
            line_width=0,
            annotation_text=name,
            annotation_position="top left",
            annotation_font_size=9,
            row="all",
            col=1,
        )

    fig.update_layout(
        title=title,
        height=750,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=90),
    )
    fig.update_yaxes(title_text="Index (start = 100)", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)

    return fig


def save_dashboard(fig: go.Figure, path: str = "dashboard.html") -> None:
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"[plotting] Dashboard saved to {path}")
