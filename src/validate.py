"""Bulk backtesting: across tickers, periods, and parameter grids."""
from __future__ import annotations

import itertools
from typing import Callable

import pandas as pd

from src.backtest import BacktestResult, run_backtest
from src.strategies import buy_and_hold

# Market regimes worth testing separately.
PERIODS: dict[str, tuple[str, str]] = {
    "2010-2014 (post-GFC recovery)": ("2010-01-01", "2014-12-31"),
    "2015-2019 (grinding bull)": ("2015-01-01", "2019-12-31"),
    "2020-2022 (COVID crash + 2022 bear)": ("2020-01-01", "2022-12-31"),
    "2023-2026 (AI-led rally)": ("2023-01-01", "2026-12-31"),
}


def backtest_one(
    prices: pd.Series,
    strategy_fn: Callable[..., pd.Series],
    params: dict | None = None,
    name: str | None = None,
    **bt_kwargs,
) -> BacktestResult:
    """Build a signal from a strategy function and backtest it."""
    params = params or {}
    signal = strategy_fn(prices, **params)
    label = name or getattr(signal, "name", strategy_fn.__name__)
    return run_backtest(prices, signal, name=label, **bt_kwargs)


def multi_ticker_table(
    panel: pd.DataFrame,
    strategy_fn: Callable[..., pd.Series],
    params: dict | None = None,
    **bt_kwargs,
) -> pd.DataFrame:
    """Run one strategy across every column of a price panel, vs buy-and-hold."""
    rows: list[dict] = []
    for ticker in panel.columns:
        prices = panel[ticker].dropna()

        strat = backtest_one(prices, strategy_fn, params, name=ticker, **bt_kwargs)
        rows.append({"ticker": ticker, "variant": "strategy", **strat.metrics})

        bench = backtest_one(prices, buy_and_hold, name=ticker, **bt_kwargs)
        rows.append({"ticker": ticker, "variant": "buy_and_hold", **bench.metrics})

    return pd.DataFrame(rows)


def period_table(
    prices: pd.Series,
    strategy_fn: Callable[..., pd.Series],
    periods: dict[str, tuple[str, str]] | None = None,
    params: dict | None = None,
    **bt_kwargs,
) -> pd.DataFrame:
    """Backtest the same strategy across separate date windows.

    The signal is computed ONCE on the full history, then sliced. Computing it
    per-window would force a fresh 200-day warmup inside each period, which
    isn't realistic — in live trading you'd already have that history.
    """
    # NOTE: the first window (2010-2014) starts at the very beginning of the
    # dataset, so its first ~200 bars are unavoidably flat warmup with no prior
    # history to inherit. That window is structurally handicapped -- say so when
    # you interpret it rather than concluding the strategy "failed" in 2010-2014.
    periods = periods or PERIODS
    params = params or {}
    full_signal = strategy_fn(prices, **params)

    rows: list[dict] = []
    for label, (start, end) in periods.items():
        window_prices = prices.loc[start:end]
        if len(window_prices) < 250:
            continue
        window_signal = full_signal.loc[start:end]

        strat = run_backtest(window_prices, window_signal, name=label, **bt_kwargs)
        rows.append({"period": label, "variant": "strategy", **strat.metrics})

        bench = run_backtest(
            window_prices, buy_and_hold(window_prices), name=label, **bt_kwargs
        )
        rows.append({"period": label, "variant": "buy_and_hold", **bench.metrics})

    return pd.DataFrame(rows)


def parameter_sweep(
    prices: pd.Series,
    strategy_fn: Callable[..., pd.Series],
    grid: dict[str, list],
    **bt_kwargs,
) -> pd.DataFrame:
    """Backtest every combination in a parameter grid. Invalid combos are skipped."""
    keys = list(grid)
    rows: list[dict] = []

    for combo in itertools.product(*(grid[k] for k in keys)):
        params = dict(zip(keys, combo))
        try:
            result = backtest_one(prices, strategy_fn, params, **bt_kwargs)
        except ValueError:
            continue  # e.g. fast >= slow
        rows.append({**params, **result.metrics})

    return pd.DataFrame(rows)


COST_SCENARIOS: dict[str, tuple[float, float]] = {
    "0 bps (frictionless)": (0.0, 0.0),
    "7 bps (baseline)": (5.0, 2.0),
    "15 bps": (10.0, 5.0),
    "30 bps": (20.0, 10.0),
    "60 bps (retail-hostile)": (40.0, 20.0),
}


def cost_sensitivity(
    prices: pd.Series,
    strategy_fn: Callable[..., pd.Series],
    params: dict | None = None,
    scenarios: dict[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Re-run one strategy under progressively worse cost assumptions.

    A strategy whose Sharpe barely moves from 0 to 60 bps is robust to friction.
    One that looks good at 7 bps and is dead at 15 was never tradeable -- it was
    an artifact of an optimistic cost assumption you chose yourself.

    This matters most for high-turnover strategies. Trend-following trades ~10
    times a decade and barely notices costs; mean reversion trades hundreds of
    times and can be killed by them entirely. Showing that contrast is a better
    finding than either strategy's raw return.
    """
    scenarios = scenarios or COST_SCENARIOS
    rows: list[dict] = []

    for label, (cost_bps, slippage_bps) in scenarios.items():
        result = backtest_one(
            prices, strategy_fn, params,
            cost_bps=cost_bps, slippage_bps=slippage_bps,
        )
        rows.append({
            "scenario": label,
            "total_bps": cost_bps + slippage_bps,
            **result.metrics,
        })

    return pd.DataFrame(rows)


def in_sample_out_of_sample(
    prices: pd.Series,
    strategy_fn: Callable[..., pd.Series],
    grid: dict[str, list],
    split_date: str,
    metric: str = "sharpe",
    **bt_kwargs,
) -> dict:
    """Tune on data before split_date, then test untouched data after it."""
    is_prices = prices[prices.index < split_date]
    oos_prices = prices[prices.index >= split_date]

    sweep = parameter_sweep(is_prices, strategy_fn, grid, **bt_kwargs)
    if sweep.empty:
        raise ValueError("Parameter sweep produced no valid combinations")

    best = sweep.sort_values(metric, ascending=False).iloc[0]
    best_params = {}
    for key in grid:
        value = best[key]
        best_params[key] = int(value) if float(value).is_integer() else float(value)

    # Signal computed on full history so the OOS window inherits its warmup.
    full_signal = strategy_fn(prices, **best_params)

    is_result = run_backtest(
        is_prices, full_signal.loc[is_prices.index], name="in-sample", **bt_kwargs
    )
    oos_result = run_backtest(
        oos_prices, full_signal.loc[oos_prices.index], name="out-of-sample", **bt_kwargs
    )

    return {
        "best_params": best_params,
        "sweep": sweep,
        "in_sample": is_result,
        "out_of_sample": oos_result,
    }
