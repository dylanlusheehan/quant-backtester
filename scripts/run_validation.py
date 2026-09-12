"""Full validation suite. Run: python -m scripts.run_validation"""
from pathlib import Path

import pandas as pd

from src.data import BENCHMARK, SPLIT_DATE, close_series, price_panel
from src.metrics import format_metrics
from src.strategies import sma_crossover
from src.validate import (
    cost_sensitivity,
    in_sample_out_of_sample,
    multi_ticker_table,
    parameter_sweep,
    period_table,
)

TABLES = Path("results/tables")
REPORT_COLUMNS = [
    "cagr", "ann_vol", "sharpe", "max_drawdown", "exposure", "n_trades", "win_rate",
]

SMA_GRID = {
    "fast": [10, 20, 30, 50, 75, 100],
    "slow": [50, 100, 150, 200, 250],
}


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    panel = price_panel()
    spy = close_series(BENCHMARK)

    # --- Test 1: across tickers -------------------------------------------
    print("\n=== 1. Across tickers (SMA 50/200) ===")
    tickers = multi_ticker_table(panel, sma_crossover)
    tickers.to_csv(TABLES / "01_multi_ticker.csv", index=False)
    print(tickers[["ticker", "variant"] + REPORT_COLUMNS].round(3).to_string(index=False))

    # --- Test 2: across market regimes ------------------------------------
    print("\n=== 2. Across regimes (SPY, SMA 50/200) ===")
    periods = period_table(spy, sma_crossover)
    periods.to_csv(TABLES / "02_periods.csv", index=False)
    print(periods[["period", "variant"] + REPORT_COLUMNS].round(3).to_string(index=False))

    # --- Test 3: parameter sensitivity ------------------------------------
    print("\n=== 3. Parameter sweep (SPY) ===")
    sweep = parameter_sweep(spy, sma_crossover, SMA_GRID)
    sweep.to_csv(TABLES / "03_param_sweep.csv", index=False)
    print(f"{len(sweep)} valid combinations")
    print("\nTop 5 by Sharpe:")
    print(sweep.nlargest(5, "sharpe")[["fast", "slow", "cagr", "sharpe", "max_drawdown"]]
          .round(3).to_string(index=False))
    print(f"\nSharpe across all combos — median {sweep['sharpe'].median():.2f}, "
          f"min {sweep['sharpe'].min():.2f}, max {sweep['sharpe'].max():.2f}")
    print(f"Combos beating Sharpe 0.5: {(sweep['sharpe'] > 0.5).mean():.0%}")

    # --- Test 4: cost sensitivity -----------------------------------------
    print("\n=== 4. Cost sensitivity (SPY, SMA 50/200) ===")
    costs = cost_sensitivity(spy, sma_crossover)
    costs.to_csv(TABLES / "04_cost_sensitivity.csv", index=False)
    print(costs[["scenario", "total_bps", "cagr", "sharpe", "max_drawdown", "n_trades"]]
          .round(3).to_string(index=False))
    print("\nRead this as: at what cost level does the edge stop existing?")

    # --- Test 5: out-of-sample --------------------------------------------
    print(f"\n=== 5. In-sample (<{SPLIT_DATE}) vs out-of-sample (>={SPLIT_DATE}) ===")
    split = in_sample_out_of_sample(spy, sma_crossover, SMA_GRID, SPLIT_DATE)
    print(f"Best in-sample params: {split['best_params']}")
    for key in ("in_sample", "out_of_sample"):
        print(f"\n{split[key].name}")
        print(format_metrics(split[key].metrics))

    pd.DataFrame([
        {"window": "in_sample", **split["in_sample"].metrics},
        {"window": "out_of_sample", **split["out_of_sample"].metrics},
    ]).to_csv(TABLES / "05_in_out_sample.csv", index=False)

    print(f"\nTables written to {TABLES}/")


if __name__ == "__main__":
    main()
