"""Chart generation. All functions save a PNG and return the output path."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from src.metrics import drawdown_series

FIGURES = Path("results/figures")
FIGSIZE = (13, 7)
DPI = 150


def _setup() -> None:
    """Consistent house style for every chart in the project."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "legend.frameon": False,
    })


def _save(fig, filename: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / filename
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")
    return path


def plot_equity_curves(
    curves: dict[str, pd.Series],
    title: str = "Growth of $10,000",
    filename: str = "02_equity_curves.png",
    log_scale: bool = True,
) -> Path:
    """Overlay multiple equity curves on one axis."""
    _setup()
    fig, ax = plt.subplots(figsize=FIGSIZE)

    for label, equity in curves.items():
        ax.plot(equity.index, equity.values, linewidth=1.6, label=label)

    dollars = mticker.FuncFormatter(lambda v, _: f"${v:,.0f}")

    if log_scale:
        ax.set_yscale("log")
        ax.set_ylabel("Portfolio value ($, log scale)")
        # $10k -> ~$70k is LESS THAN ONE DECADE, so matplotlib places exactly one
        # major tick (10^4). Formatting only the major ticks leaves an axis
        # labelled "$10,000" and nothing else, with minor ticks falling back to
        # "2x10^4" scientific notation. Both formatters must be set, and the
        # minor ticks need an explicit locator to exist at all.
        ax.yaxis.set_major_locator(mticker.LogLocator(base=10, numticks=12))
        ax.yaxis.set_minor_locator(
            mticker.LogLocator(base=10, subs=(0.2, 0.4, 0.6, 0.8), numticks=12)
        )
        ax.yaxis.set_major_formatter(dollars)
        ax.yaxis.set_minor_formatter(dollars)
        ax.tick_params(axis="y", which="minor", labelsize=9)
    else:
        ax.set_ylabel("Portfolio value ($)")
        ax.yaxis.set_major_formatter(dollars)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.legend(loc="upper left")
    return _save(fig, filename)


def plot_drawdown(
    curves: dict[str, pd.Series],
    title: str = "Drawdown from running peak",
    filename: str = "03_drawdown.png",
) -> Path:
    """Underwater chart — how far below its previous high each strategy sat."""
    _setup()
    fig, ax = plt.subplots(figsize=(13, 5))

    for label, equity in curves.items():
        drawdown = drawdown_series(equity) * 100
        ax.plot(drawdown.index, drawdown.values, linewidth=1.3, label=label)
        ax.fill_between(drawdown.index, drawdown.values, 0, alpha=0.12)

    ax.set_title(title)
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Date")
    ax.legend(loc="lower left")
    return _save(fig, filename)


def plot_param_heatmap(
    sweep: pd.DataFrame,
    x: str = "slow",
    y: str = "fast",
    metric: str = "sharpe",
    title: str | None = None,
    subtitle: str = "",
    filename: str = "04_param_heatmap.png",
) -> Path:
    """Parameter surface — the visual test for overfitting.

    A smooth gradient means a robust plateau. A single bright cell surrounded
    by dark ones means the 'best' parameters are fitted noise.
    """
    _setup()
    grid = sweep.pivot(index=y, columns=x, values=metric)

    fig, ax = plt.subplots(figsize=(10, 6))
    mesh = ax.imshow(grid.values, aspect="auto", origin="lower", cmap="RdYlGn")

    ax.set_xticks(range(len(grid.columns)), grid.columns)
    ax.set_yticks(range(len(grid.index)), grid.index)
    ax.set_xlabel(f"{x} window (days)")
    ax.set_ylabel(f"{y} window (days)")
    # Title gets extra top padding (pad=28 vs. matplotlib's default ~6) so the
    # subtitle, placed just above the axes at y=1.02, has clear room beneath
    # it instead of colliding with the title text.
    ax.set_title(title or f"{metric.title()} across parameter combinations", pad=28)
    if subtitle:
        # This figure goes into the README under "Guarding Against Overfitting".
        # The first question anyone asks is "on what data?" -- answer it on the
        # chart, not in a caption someone may not read.
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=10, color="0.35")
    ax.grid(False)

    for i in range(len(grid.index)):
        for j in range(len(grid.columns)):
            value = grid.values[i, j]
            if pd.notna(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=9)

    fig.colorbar(mesh, ax=ax, label=metric.title())
    return _save(fig, filename)


def plot_signal_overlay(
    prices: pd.Series,
    signal: pd.Series,
    overlays: dict[str, pd.Series] | None = None,
    title: str = "Price, moving averages, and position",
    filename: str = "05_signal_overlay.png",
) -> Path:
    """Price with indicator overlays on top, position band underneath.

    Replaces the throwaway scripts/check_signal.py from Step 2.
    """
    _setup()
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=FIGSIZE, sharex=True, height_ratios=[3, 1]
    )

    ax1.plot(prices.index, prices.values, linewidth=1.1, label="Close", color="black")
    for label, series in (overlays or {}).items():
        ax1.plot(series.index, series.values, linewidth=1.2, label=label)

    ax1.set_title(title)
    ax1.set_ylabel("Price ($)")
    ax1.legend(loc="upper left")

    ax2.fill_between(signal.index, 0, signal.values, step="post", alpha=0.5)
    ax2.set_ylabel("Position")
    ax2.set_yticks([0, 1], ["Flat", "Long"])
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_xlabel("Date")

    return _save(fig, filename)


def plot_ticker_comparison(
    table: pd.DataFrame,
    metric: str = "cagr",
    strategy_col: str = "strategy",
    title: str | None = None,
    filename: str = "06_ticker_comparison.png",
    as_percent: bool = True,
) -> Path:
    """Grouped bars: one cluster per ticker, one bar per strategy.

    Your README's first key finding is about behaviour ACROSS tickers, and
    without this chart there is no picture supporting it -- every other figure
    in the project shows SPY only. Reads straight from
    results/tables/06_strategy_comparison_tickers.csv.
    """
    _setup()
    grid = table.pivot(index="ticker", columns=strategy_col, values=metric)
    if as_percent:
        grid = grid * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    grid.plot(kind="bar", ax=ax, width=0.78, edgecolor="none")

    ax.set_title(title or f"{metric.upper()} by ticker and strategy")
    ax.set_ylabel(f"{metric.upper()} (%)" if as_percent else metric.upper())
    ax.set_xlabel("Ticker")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title=None, loc="best")
    return _save(fig, filename)


def metrics_to_markdown(df: pd.DataFrame, decimals: int = 3) -> str:
    """Markdown table for pasting into the README."""
    return df.to_markdown(index=False, floatfmt=f".{decimals}f")
