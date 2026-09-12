"""Vectorized daily backtester for long/flat strategies."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.metrics import compute_metrics

# Cost assumptions, in basis points of traded notional (1 bp = 0.01%).
DEFAULT_COST_BPS = 5.0        # commission / spread
DEFAULT_SLIPPAGE_BPS = 2.0    # adverse fill vs the close we assume we transact at


@dataclass
class BacktestResult:
    """Everything produced by one backtest run."""
    name: str
    equity: pd.Series
    returns: pd.Series
    position: pd.Series
    trades: pd.DataFrame
    metrics: dict


def run_backtest(
    prices: pd.Series,
    signal: pd.Series,
    name: str = "strategy",
    initial_capital: float = 10_000.0,
    cost_bps: float = DEFAULT_COST_BPS,
    slippage_bps: float = DEFAULT_SLIPPAGE_BPS,
) -> BacktestResult:
    """Run one strategy over one price series.

    `signal` is the UNSHIFTED target position from src/strategies.py. This
    function applies the single .shift(1) that prevents lookahead bias.
    """
    prices = prices.dropna()
    signal = signal.reindex(prices.index).fillna(0.0)

    # ---- THE LOOKAHEAD GUARD -------------------------------------------
    # A signal computed from the close of day t cannot be acted on until
    # day t+1. Everything downstream depends on this single line.
    position = signal.shift(1).fillna(0.0)
    # --------------------------------------------------------------------

    asset_returns = prices.pct_change().fillna(0.0)
    gross_returns = position * asset_returns

    # Costs are charged on the change in position, i.e. only when we trade.
    turnover = position.diff().abs().fillna(0.0)
    cost_rate = (cost_bps + slippage_bps) / 10_000.0
    costs = turnover * cost_rate

    net_returns = gross_returns - costs
    equity = (1.0 + net_returns).cumprod() * initial_capital

    trades = extract_trades(prices, position)
    metrics = compute_metrics(net_returns, position, trades)

    return BacktestResult(
        name=name,
        equity=equity,
        returns=net_returns,
        position=position,
        trades=trades,
        metrics=metrics,
    )


TRADE_COLUMNS = [
    "entry_date", "exit_date", "entry_price",
    "exit_price", "return_pct", "bars_held",
]


def extract_trades(prices: pd.Series, position: pd.Series) -> pd.DataFrame:
    """Pair each 0 -> long transition with its following long -> 0 transition.

    Signal bars are converted to TRANSACTION bars before being recorded, and
    getting that conversion wrong is the single easiest way to make this project
    quietly dishonest. See the note below _build_trade.
    """
    values = position.to_numpy()
    index = position.index
    rows: list[dict] = []
    entry_i: int | None = None

    for i in range(len(values)):
        prev = values[i - 1] if i > 0 else 0.0
        if prev == 0.0 and values[i] > 0.0:
            entry_i = i
        elif prev > 0.0 and values[i] == 0.0 and entry_i is not None:
            # Held bars i .. j-1, so the fills were close[i-1] and close[j-1].
            rows.append(_build_trade(index, prices, entry_i - 1, i - 1))
            entry_i = None

    # Still holding on the final bar: mark to market at the last close.
    if entry_i is not None:
        rows.append(_build_trade(index, prices, entry_i - 1, len(values) - 1))

    return pd.DataFrame(rows, columns=TRADE_COLUMNS)


def _build_trade(index, prices: pd.Series, entry_bar: int, exit_bar: int) -> dict:
    """Record one trade at the bars the equity curve actually transacted on.

    THE OFF-BY-ONE THAT MATTERS: `position[i] == 1` means you HOLD during bar i,
    which captures the return from close[i-1] to close[i]. So your entry fill is
    close[i-1], not close[i]. Likewise a 1 -> 0 flip at bar j means the last
    return you captured was bar j-1, so your exit fill is close[j-1].

    Record close[i] and close[j] instead and the trade log stops agreeing with
    the equity curve -- by enough to turn a winning trade into a losing one and
    corrupt `win_rate`, which is a headline number in your README. This is
    enforced by tests/test_backtest.py::test_trade_log_reconciles_with_equity_curve.

    `return_pct` is gross of costs; the equity curve is net. State that in the
    README rather than letting someone find it.
    """
    entry_bar = max(entry_bar, 0)
    exit_bar = max(exit_bar, entry_bar)
    entry_price = float(prices.iloc[entry_bar])
    exit_price = float(prices.iloc[exit_bar])
    return {
        "entry_date": index[entry_bar],
        "exit_date": index[exit_bar],
        "entry_price": entry_price,
        "exit_price": exit_price,
        "return_pct": (exit_price / entry_price - 1.0) * 100.0,
        "bars_held": exit_bar - entry_bar,
    }
