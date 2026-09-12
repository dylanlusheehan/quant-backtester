# Talking Points

Prepared answers to the questions this project is most likely to draw in an
interview. Written in my own words so I can actually say these out loud.

## 1. How did you prevent lookahead bias?

The whole guard is one line in `src/backtest.py`: `position = signal.shift(1)`.
Strategy functions compute an unshifted signal from data available at the
close of day *t* — they never see the future. The engine is the only place
that converts that signal into an actual traded position, shifted forward one
bar, so a signal computed from Tuesday's close can only be acted on starting
Wednesday. It's enforced by a test (`test_no_lookahead_bias`) that proves a
signal peeking one bar into the future produces different results from an
honest one — if the shift weren't working, they'd score identically.

## 2. Did it beat the market?

No, honestly — not on any of the 6 tickers, and not in any of the 4 market
regimes tested. Buy-and-hold's CAGR beat both active strategies everywhere.
But the more interesting result is *how* they lost: trend-following (SMA)
gave up return for shallower drawdowns on about a third of tickers, and the
two strategies were relatively complementary against each other — each one
winning in exactly the regime its own thesis predicted, even while both
trailed the passive benchmark.

## 3. How do you know you didn't overfit?

Three checks. First, the parameter sweep: 100% of 26 valid SMA combinations
beat Sharpe 0.5, with the best (0.89) not far off the median (0.71) — a
stable plateau, not an isolated spike, so the reported 50/200 wasn't
cherry-picked. Second, an out-of-sample split: parameters tuned only on
2010-2019 data were tested untouched on 2020-2026, and both strategies
degraded (SMA -33%, mean reversion -67%) rather than collapsing to zero,
which is the expected signature of a real, if modest, edge partially eroding
— not pure noise. Third, I deliberately reported both strategies' un-tuned
defaults rather than their sweep-identified best combos, specifically because
the mean-reversion "best" combo was the one that degraded hardest
out-of-sample.

## 4. What would you do differently?

Test the same two strategies on a window that actually contains a slow,
grinding bear market — 2010-2026 doesn't have one, which is the most likely
explanation for why trend-following's drawdown protection didn't show up
more consistently. Beyond that: portfolio-level backtesting with real capital
allocation instead of one ticker at a time, volatility-scaled position sizing
instead of binary long/flat, and walk-forward optimization instead of a
single train/test split.

## 5. Why build the engine instead of using a library like backtrader or vectorbt?

To actually understand the mechanics that libraries abstract away — cost
modelling, the exact mechanism that prevents lookahead bias, and how a trade
log reconciles with an equity curve. I hit a real bug during development
where the trade log recorded the wrong entry/exit price by one bar (an
off-by-one between the day a signal fires and the day the position actually
starts earning returns) — it would have turned a winning trade into a
reported loser. A library would have hidden that entirely; building it myself
meant I had to understand precisely why the fix was `entry_bar - 1`, not just
trust that a black box got it right.

## 6. How sensitive is this to your cost assumptions?

Very different between the two strategies, and that's one of the more
interesting findings. At the shared 7 bps baseline, trend-following's Sharpe
barely moved from a frictionless baseline (0.712 → 0.707), because it only
trades 8 times over 16 years. Mean reversion trades 127 times over the same
period, so the same 7 bps already cost it about 17% of its Sharpe
(0.496 → 0.413), and its breakeven friction level is around 42 bps — above
that, it's outright unprofitable. Same cost assumption, completely different
verdict, purely a function of trade frequency.
