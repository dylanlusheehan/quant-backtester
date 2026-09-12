"""Sanity tests for the backtest engine.

Run: python -m pytest tests -v
"""
import numpy as np
import pandas as pd

from src.backtest import run_backtest
from src.strategies import buy_and_hold, sma_crossover


def _straight_line_prices(n: int = 300, daily_return: float = 0.001) -> pd.Series:
    """Deterministic price series growing at a fixed rate."""
    index = pd.bdate_range("2020-01-01", periods=n)
    values = 100.0 * (1.0 + daily_return) ** np.arange(n)
    return pd.Series(values, index=index, name="TEST")


def _mean_reverting_prices(n: int = 400) -> pd.Series:
    """Deterministic oscillating series with a mild uptrend.

    A straight line only ever produces ONE trade that never closes, so it can
    never expose an entry/exit pairing bug. This fixture produces ~8 complete
    round trips under a 5/20 crossover, which is what the reconciliation test
    below actually needs.
    """
    index = pd.bdate_range("2020-01-01", periods=n)
    t = np.arange(n)
    values = 100.0 + 10.0 * np.sin(t / 8.0) + 0.02 * t
    return pd.Series(values, index=index, name="TEST")


def test_buy_and_hold_matches_underlying():
    """With zero costs, buy-and-hold must equal the asset's own total return.

    The shift costs nothing here: bar 0 has no return to capture anyway, and
    from bar 1 onward the position is already 1.0.
    """
    prices = _straight_line_prices()
    result = run_backtest(
        prices, buy_and_hold(prices), cost_bps=0.0, slippage_bps=0.0
    )
    expected = prices.iloc[-1] / prices.iloc[0] - 1.0
    actual = result.equity.iloc[-1] / result.equity.iloc[0] - 1.0
    assert abs(actual - expected) < 1e-9


def test_no_lookahead_bias():
    """Shifting the signal forward must change results — proving the shift exists.

    If run_backtest ignored the shift, a signal that knows tomorrow's price
    would score identically to one that doesn't. It must not.
    """
    prices = _straight_line_prices()
    honest = pd.Series(
        (prices.pct_change() > 0).astype(float).values, index=prices.index
    )
    cheating = honest.shift(-1).fillna(0.0)

    honest_result = run_backtest(prices, honest, cost_bps=0, slippage_bps=0)
    cheating_result = run_backtest(prices, cheating, cost_bps=0, slippage_bps=0)

    assert cheating_result.equity.iloc[-1] != honest_result.equity.iloc[-1]


def test_costs_reduce_returns():
    """A costed backtest must finish below an identical costless one."""
    prices = _straight_line_prices()
    signal = sma_crossover(prices, fast=5, slow=20)

    free = run_backtest(prices, signal, cost_bps=0.0, slippage_bps=0.0)
    costed = run_backtest(prices, signal, cost_bps=50.0, slippage_bps=20.0)

    assert costed.equity.iloc[-1] <= free.equity.iloc[-1]


def test_flat_signal_produces_flat_equity():
    """A never-invested strategy must never gain or lose money."""
    prices = _straight_line_prices()
    flat = pd.Series(0.0, index=prices.index)
    result = run_backtest(prices, flat)

    assert result.equity.nunique() == 1
    assert result.metrics["n_trades"] == 0


def test_trades_are_paired_and_ordered():
    """Every extracted trade must exit at or after it entered."""
    prices = _mean_reverting_prices()
    signal = sma_crossover(prices, fast=5, slow=20)
    result = run_backtest(prices, signal)

    trades = result.trades
    assert len(trades) >= 2, "fixture must produce multiple round trips"
    assert (trades["exit_date"] >= trades["entry_date"]).all()
    assert (trades["bars_held"] > 0).all()


def test_trade_log_reconciles_with_equity_curve():
    """Each trade's return_pct must equal the equity curve's move over that trade.

    This is the test that catches the classic entry/exit off-by-one. If
    _build_trade recorded close[i] instead of close[i-1], a trade could be
    reported as -18% while the equity curve booked +11% on it -- and win_rate,
    which goes straight into the README and the resume bullet, would be wrong.

    Costs are zeroed because return_pct is gross and the equity curve is net.
    """
    prices = _mean_reverting_prices()
    signal = sma_crossover(prices, fast=5, slow=20)
    result = run_backtest(prices, signal, cost_bps=0.0, slippage_bps=0.0)

    assert len(result.trades) >= 2

    for _, trade in result.trades.iterrows():
        equity_move = (
            result.equity.loc[trade["exit_date"]]
            / result.equity.loc[trade["entry_date"]]
            - 1.0
        ) * 100.0
        assert abs(equity_move - trade["return_pct"]) < 1e-6


def test_zscore_reversion_rejects_bad_thresholds():
    """entry_z must be below exit_z or the state machine is nonsense."""
    import pytest

    from src.strategies import zscore_reversion

    prices = _straight_line_prices()
    with pytest.raises(ValueError):
        zscore_reversion(prices, entry_z=1.0, exit_z=-1.0)


def test_zscore_reversion_is_binary_and_aligned():
    """Signal must contain only 0.0/1.0 and match the price index.

    Uses the oscillating fixture, NOT the straight line. On a monotonically
    rising series the price is always above its own rolling mean, so the
    z-score never reaches -1 and the signal is all zeros -- the test would pass
    without ever exercising the long branch. A green test that never runs the
    code it claims to test is worse than no test.
    """
    from src.strategies import zscore_reversion

    prices = _mean_reverting_prices()
    signal = zscore_reversion(prices)

    assert set(signal.unique()).issubset({0.0, 1.0})
    assert signal.index.equals(prices.index)
    assert signal.iloc[:19].eq(0.0).all()   # warmup is flat
    assert signal.sum() > 0, "fixture must actually trigger entries"


def test_zscore_reversion_holds_between_thresholds():
    """Between entry_z and exit_z the previous position must persist.

    This is what makes it a state machine rather than a threshold rule, and
    it's the part the forward-fill implementation could silently get wrong.
    """
    from src.strategies import zscore_reversion

    prices = _mean_reverting_prices()
    signal = zscore_reversion(prices, lookback=20, entry_z=-1.0, exit_z=0.0)

    rolling_mean = prices.rolling(20, min_periods=20).mean()
    rolling_std = prices.rolling(20, min_periods=20).std(ddof=1)
    zscore = (prices - rolling_mean) / rolling_std

    middle = (zscore > -1.0) & (zscore < 0.0)
    held = signal[middle] == signal.shift(1)[middle]
    assert held.all(), "position changed while z-score was between thresholds"
