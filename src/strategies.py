"""Trading strategies.

Every function takes a price Series and returns an UNSHIFTED target position
Series aligned to the same index: 1.0 = long, 0.0 = flat.

Do NOT shift inside these functions. src/backtest.py applies exactly one
.shift(1) to convert signals into tradeable positions. Shifting here would
apply it twice and silently corrupt every result downstream.
"""
from __future__ import annotations

import pandas as pd


def buy_and_hold(prices: pd.Series) -> pd.Series:
    """Benchmark: always fully invested."""
    signal = pd.Series(1.0, index=prices.index)
    signal.name = "buy_and_hold"
    return signal


def sma_crossover(prices: pd.Series, fast: int = 50, slow: int = 200) -> pd.Series:
    """Long while the fast moving average is above the slow one, else flat."""
    if fast >= slow:
        raise ValueError(f"fast ({fast}) must be shorter than slow ({slow})")

    fast_ma = prices.rolling(window=fast, min_periods=fast).mean()
    slow_ma = prices.rolling(window=slow, min_periods=slow).mean()

    signal = (fast_ma > slow_ma).astype(float)
    # During warmup the slow MA is NaN, which compares False -> 0.0 already,
    # but we set it explicitly so the intent is obvious to a reader.
    signal[slow_ma.isna()] = 0.0

    signal.name = f"sma_{fast}_{slow}"
    return signal
