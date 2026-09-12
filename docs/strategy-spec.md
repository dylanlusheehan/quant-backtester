# Strategy Specifications

Convention: every strategy returns a target position for each day, computed from
data available at that day's close. 1.0 = fully long, 0.0 = flat. No shorting,
no leverage, no position sizing — those are deliberately out of scope for v1.

## Strategy A — SMA Crossover (trend following)

**Thesis:** trends persist. When short-term average price is above long-term
average price, the asset is in an uptrend and more likely to keep rising.

**Rules:**
- Compute a fast simple moving average (default 50 trading days) of adjusted close.
- Compute a slow simple moving average (default 200 trading days).
- If fast MA > slow MA at the close of day t: target position = 1.0 (long).
- Otherwise: target position = 0.0 (flat).
- Before the slow MA has enough history to exist (first 199 days): 0.0 (flat).

**Parameters:** fast (default 50), slow (default 200). Constraint: fast < slow.

**Expected behavior:** few trades (a handful per decade per ticker), long holding
periods, participates in sustained bull runs, sits out extended drawdowns, but
whipsaws badly in choppy sideways markets.

## Strategy B — Z-Score Mean Reversion

Specified in Step 5. Not built yet.

## Benchmark — Buy & Hold

Always 1.0, every day. This is the bar every strategy must clear. If a strategy
can't beat buy-and-hold after costs, it has no reason to exist.
