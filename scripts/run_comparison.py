"""Compare both strategies across tickers and regimes.

Run: python -m scripts.run_comparison
"""
from pathlib import Path

import pandas as pd

from src.backtest import run_backtest
from src.config import REPORT_COLUMNS, STRATEGIES
from src.data import BENCHMARK, close_series, price_panel
from src.validate import PERIODS, backtest_one

TABLES = Path("results/tables")


def compare_across_tickers(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker in panel.columns:
        prices = panel[ticker].dropna()
        for label, (fn, params) in STRATEGIES.items():
            result = backtest_one(prices, fn, params, name=label)
            rows.append({"ticker": ticker, "strategy": label, **result.metrics})
    return pd.DataFrame(rows)


def compare_across_periods(prices: pd.Series) -> pd.DataFrame:
    rows = []
    for label, (fn, params) in STRATEGIES.items():
        full_signal = fn(prices, **params)
        for period_label, (start, end) in PERIODS.items():
            window = prices.loc[start:end]
            if len(window) < 250:
                continue
            result = run_backtest(window, full_signal.loc[start:end], name=label)
            rows.append({"period": period_label, "strategy": label, **result.metrics})
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    panel = price_panel()
    spy = close_series(BENCHMARK)

    print("\n=== Strategy comparison across tickers ===")
    tickers = compare_across_tickers(panel)
    tickers.to_csv(TABLES / "06_strategy_comparison_tickers.csv", index=False)
    print(tickers[["ticker", "strategy"] + REPORT_COLUMNS].round(3).to_string(index=False))

    print("\n=== Average metrics by strategy (across all 6 tickers) ===")
    averages = tickers.groupby("strategy")[REPORT_COLUMNS].mean().round(3)
    averages.to_csv(TABLES / "07_strategy_averages.csv")
    print(averages.to_string())

    print("\n=== Strategy comparison across regimes (SPY) ===")
    periods = compare_across_periods(spy)
    periods.to_csv(TABLES / "08_strategy_comparison_periods.csv", index=False)
    pivot = periods.pivot(index="period", columns="strategy", values="sharpe").round(2)
    print("\nSharpe by regime:")
    print(pivot.to_string())

    print(f"\nTables written to {TABLES}/")


if __name__ == "__main__":
    main()
