"""Backtest one strategy on one ticker against buy-and-hold.

Run: python -m scripts.run_backtest
"""
from src.backtest import run_backtest
from src.data import close_series
from src.metrics import format_metrics
from src.strategies import buy_and_hold, sma_crossover


def main(ticker: str = "AAPL", fast: int = 50, slow: int = 200) -> None:
    prices = close_series(ticker)

    strategy = run_backtest(
        prices,
        sma_crossover(prices, fast=fast, slow=slow),
        name=f"SMA {fast}/{slow}",
    )
    benchmark = run_backtest(
        prices,
        buy_and_hold(prices),
        name="Buy & hold",
    )

    print(f"\n{ticker}  |  {prices.index.min().date()} -> {prices.index.max().date()}")

    for result in (strategy, benchmark):
        print(f"\n{result.name}")
        print(format_metrics(result.metrics))

    print(f"\nFinal equity — strategy: ${strategy.equity.iloc[-1]:,.0f}"
          f"  |  benchmark: ${benchmark.equity.iloc[-1]:,.0f}")

    print(f"\nFirst 5 trades:\n{strategy.trades.head()}")


if __name__ == "__main__":
    main()
