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


def zscore_reversion(
    prices: pd.Series,
    lookback: int = 20,
    entry_z: float = -1.0,
    exit_z: float = 0.0,
) -> pd.Series:
    """Long when price is unusually cheap vs its rolling mean, flat once it reverts.

    Between the entry and exit thresholds the previous position is held, which
    is what makes this a state machine rather than a simple threshold rule.
    """
    if entry_z >= exit_z:
        raise ValueError(f"entry_z ({entry_z}) must be below exit_z ({exit_z})")

    rolling_mean = prices.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = prices.rolling(window=lookback, min_periods=lookback).std(ddof=1)
    zscore = (prices - rolling_mean) / rolling_std

    # Mark only the bars where state actually changes; forward-fill between them.
    raw = pd.Series(float("nan"), index=prices.index)
    raw[zscore <= entry_z] = 1.0
    raw[zscore >= exit_z] = 0.0

    signal = raw.ffill().fillna(0.0)
    signal[rolling_std.isna()] = 0.0     # warmup stays flat
    signal[rolling_std == 0] = 0.0       # avoid divide-by-zero artifacts

    signal.name = f"zrev_{lookback}_{entry_z}_{exit_z}"
    return signal
