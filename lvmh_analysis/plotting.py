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

    # Shade named market-stress windows across both panels (no per-rect annotations to avoid overlap).
    for name, (start, end) in MARKET_EVENTS.items():
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor="red",
            opacity=0.07,
            line_width=0,
            row="all",
            col=1,
        )

    # Compute compact indicators to show at top-right (aligned with title)
    try:
        asset_total = aligned['Close'].iloc[-1] / aligned['Close'].iloc[0] - 1
        bench_total = aligned[benchmark_col].iloc[-1] / aligned[benchmark_col].iloc[0] - 1
        excess = asset_total - bench_total
    except Exception:
        asset_total = float('nan')
        bench_total = float('nan')
        excess = float('nan')

    try:
        latest_vol = vol_df[volatility_col].dropna().iloc[-1] * 100
    except Exception:
        latest_vol = float('nan')

    indicator_text = (
        f"LVMH TR: {asset_total*100:.1f}%<br>"
        f"{benchmark_name} TR: {bench_total*100:.1f}%<br>"
        f"Excess: {excess*100:.1f}%<br>"
        f"Latest vol (20d): {latest_vol:.1f}%"
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', y=0.98),
        height=750,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=0.9, xanchor="right", x=1),
        margin=dict(t=160),  # extra top margin so title and indicators have breathing room
    )

    # Add a compact annotation box at the top-right (paper coordinates) for indicators
    fig.add_annotation(
        xref='paper', yref='paper', x=1.0, y=1.02,
        xanchor='right', yanchor='top',
        text=indicator_text,
        showarrow=False,
        align='right',
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='rgba(0,0,0,0.2)',
        borderwidth=1,
        font=dict(size=11),
    )

    fig.update_yaxes(title_text="Index (start = 100)", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)

    return fig


def save_dashboard(fig: go.Figure, path: str = "dashboard.html") -> None:
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"[plotting] Dashboard saved to {path}")


def build_notebook_charts(data: pd.DataFrame, title: str = "Stock Price Analysis") -> go.Figure:
    """Reproduce the notebook's 2x2 mean±std charts for Open/High/Low/Close as a Plotly figure.

    Returns a Plotly Figure with 4 subplots matching the Examination.ipynb visuals.
    """
    data = data.copy()
    data = data.sort_values("Date").reset_index(drop=True)

    fig = make_subplots(rows=2, cols=2, subplot_titles=("Opening Prices", "High Prices", "Low Prices", "Closing Prices"))

    cols = ["Open", "High", "Low", "Close"]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]

    for i, col in enumerate(cols):
        mean_val = data[col].mean()
        std_val = data[col].std()
        row = i // 2 + 1
        col_idx = i % 2 + 1

        fig.add_trace(
            go.Scatter(
                x=list(range(len(data))),
                y=data[col],
                mode="lines+markers",
                marker=dict(size=4),
                name=col,
                line=dict(color=colors[i]),
                opacity=0.7,
            ),
            row=row,
            col=col_idx,
        )

        # mean line
        fig.add_trace(
            go.Scatter(x=[0, len(data) - 1], y=[mean_val, mean_val], mode="lines", line=dict(dash="dash", color="red"), showlegend=False),
            row=row,
            col=col_idx,
        )

        # shaded std band
        fig.add_trace(
            go.Scatter(
                x=list(range(len(data))) + list(range(len(data))[::-1]),
                y=list((mean_val + std_val) * np.ones(len(data))) + list((mean_val - std_val) * np.ones(len(data))[::-1]),
                fill="toself",
                fillcolor=colors[i] + "22",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=row,
            col=col_idx,
        )

        fig.update_yaxes(title_text="Price", row=row, col=col_idx)
        fig.update_xaxes(title_text="Date Index", row=row, col=col_idx)

    fig.update_layout(title=title, height=700, template="plotly_white")
    return fig


def export_figure_png(fig: go.Figure, path: str) -> None:
    """Export a Plotly figure to PNG using kaleido if available; otherwise warn."""
    try:
        fig.write_image(path)
        print(f"[plotting] Exported PNG to {path}")
    except Exception as e:
        print(f"[plotting] WARNING: failed to write PNG {path}. Install 'kaleido' to enable static exports. Error: {e}")


def build_cross_section_dashboard(
    aligned_map: dict,
    vol_map: dict,
    summary_df: pd.DataFrame,
    event_df: pd.DataFrame,
    benchmark_name: str = "Benchmark",
    volatility_col: str = "Volatility_20d",
    title: str = "Cross-Section: Assets vs. Benchmark",
) -> go.Figure:
    """Build a dashboard comparing multiple assets to a common benchmark.

    Panels:
    1) Normalized price overlay
    2) Rolling volatility lines per asset
    3) Event-window grouped bar chart (asset vs benchmark relative returns)
    4) Cross-sectional summary table with CIs
    """
    # 4-row layout
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.35, 0.2, 0.25, 0.2],
        vertical_spacing=0.04,
        specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "xy"}], [{"type": "table"}]],
        subplot_titles=(
            "Normalized Price (start = 100)",
            "Rolling Volatility",
            "Event-window Relative Returns",
            "Cross-sectional summary",
        ),
    )

    # Normalized prices
    for name, aligned in aligned_map.items():
        norm = aligned["Close"] / aligned["Close"].iloc[0] * 100
        fig.add_trace(
            go.Scatter(x=aligned["Date"], y=norm, name=name, mode="lines"),
            row=1,
            col=1,
        )

    # Volatility traces
    for name, vol in vol_map.items():
        if volatility_col in vol.columns:
            fig.add_trace(
                go.Scatter(
                    x=vol["Date"],
                    y=vol[volatility_col] * 100,
                    name=f"Vol {name}",
                    mode="lines",
                ),
                row=2,
                col=1,
            )

    # Event-window grouped bars: for each event, one bar per asset showing Relative_Return
    if not event_df.empty:
        # pivot so events on x-axis, assets as series
        pivot = event_df.pivot(index="Event", columns="Asset", values="Relative_Return")
        events = pivot.index.tolist()
        for asset in pivot.columns:
            fig.add_trace(
                go.Bar(x=events, y=pivot[asset].values * 100, name=asset),
                row=3,
                col=1,
            )
        fig.update_yaxes(title_text="Relative return (%)", row=3, col=1)

    # Summary table
    table_cols = [
        "Asset",
        "Asset total return",
        f"CI lower",
        f"CI upper",
        "Asset annual vol",
        "Benchmark annual vol",
        "Relative vol",
    ]

    # Ensure numeric columns exist
    def fmt(col, scale=1, prec=2):
        if col in summary_df.columns:
            return (summary_df[col] * scale).round(prec).astype(str).tolist()
        return ["N/A"] * len(summary_df)

    table_values = [
        summary_df.get("Asset", summary_df.index).tolist(),
        fmt("asset_total_return", 100),
        fmt("ci_lower", 100),
        fmt("ci_upper", 100),
        fmt("asset_annual_volatility", 100),
        fmt("benchmark_annual_volatility", 100),
        summary_df.get("relative_volatility", summary_df.get("relative_volatility", [])).round(2).astype(str).tolist(),
    ]

    fig.add_trace(
        go.Table(
            header=dict(values=table_cols, fill_color="lightgrey"),
            cells=dict(values=table_values),
        ),
        row=4,
        col=1,
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', y=0.985),
        height=1000,
        template="plotly_white",
        barmode="group",
        legend=dict(orientation='h', yanchor='top', y=0.92, xanchor='right', x=1),
        margin=dict(t=160),
    )
    fig.update_yaxes(title_text="Index (start = 100)", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)
    return fig
