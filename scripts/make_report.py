"""Regenerate every figure and the summary table from scratch.

Run: python -m scripts.make_report
"""
from pathlib import Path

import pandas as pd

from src.config import SMA_PARAMS, STRATEGIES
from src.data import BENCHMARK, END, SPLIT_DATE, START, close_series
from src.plots import (
    metrics_to_markdown,
    plot_drawdown,
    plot_equity_curves,
    plot_param_heatmap,
    plot_signal_overlay,
    plot_ticker_comparison,
)
from src.strategies import sma_crossover
from src.validate import backtest_one

TABLES = Path("results/tables")
SUMMARY = Path("results/summary.md")


def main() -> None:
    print("Loading data...")
    spy = close_series(BENCHMARK)

    results = {
        label: backtest_one(spy, fn, params, name=label)
        for label, (fn, params) in STRATEGIES.items()
    }
    curves = {label: result.equity for label, result in results.items()}

    print("\nGenerating figures...")
    plot_equity_curves(curves, title=f"{BENCHMARK}: growth of $10,000 ({START[:4]}-{END[:4]})")
    plot_drawdown(curves, title=f"{BENCHMARK}: drawdown by strategy")

    sweep_path = TABLES / "03_param_sweep.csv"
    if sweep_path.exists():
        plot_param_heatmap(
            pd.read_csv(sweep_path),
            subtitle=f"{BENCHMARK}, {START[:4]}-{END[:4]}, net of 7 bps per position change",
        )
    else:
        print("  ! 03_param_sweep.csv missing — run scripts.run_validation first")

    comparison_path = TABLES / "06_strategy_comparison_tickers.csv"
    if comparison_path.exists():
        table = pd.read_csv(comparison_path)
        plot_ticker_comparison(
            table, metric="cagr",
            title=f"CAGR by ticker and strategy ({START[:4]}-{END[:4]}, net of costs)",
        )
    else:
        print("  ! 06_strategy_comparison_tickers.csv missing — run scripts.run_comparison first")

    fast, slow = SMA_PARAMS["fast"], SMA_PARAMS["slow"]
    plot_signal_overlay(
        spy,
        sma_crossover(spy, **SMA_PARAMS),
        overlays={
            f"SMA {fast}": spy.rolling(fast).mean(),
            f"SMA {slow}": spy.rolling(slow).mean(),
        },
        title=f"{BENCHMARK}: SMA {fast}/{slow} signal",
    )

    print("\nBuilding summary table...")
    summary = pd.DataFrame([
        {"Strategy": label, **result.metrics} for label, result in results.items()
    ])
    summary = summary[[
        "Strategy", "cagr", "ann_vol", "sharpe",
        "max_drawdown", "exposure", "n_trades", "win_rate",
    ]].rename(columns={
        "cagr": "CAGR", "ann_vol": "Ann. vol", "sharpe": "Sharpe",
        "max_drawdown": "Max DD", "exposure": "Exposure",
        "n_trades": "Trades", "win_rate": "Win rate",
    })

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(
        f"# Results Summary\n\n"
        f"Benchmark ticker: {BENCHMARK}. Costs: 5 bps + 2 bps slippage.\n"
        f"In-sample/out-of-sample split: {SPLIT_DATE}.\n\n"
        f"{metrics_to_markdown(summary)}\n",
        encoding="utf-8",
    )
    print(f"  saved {SUMMARY}")
    print("\n" + summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
