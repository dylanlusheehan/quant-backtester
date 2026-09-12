# Metrics Notes

Short, in-my-own-words explanation of every number `compute_metrics` produces.
Written so I can defend these from memory without re-deriving them.

## CAGR (Compound Annual Growth Rate)
Total return isn't fair to compare across different time windows — 50% over 2
years and 50% over 10 years are very different outcomes. CAGR answers "if this
grew at one constant smooth rate every year, what would that rate be?" Good
means beating SPY's long-run ~10-12%/year.

## Ann. volatility
How much daily returns bounce around, scaled up to an annual number
(`std * sqrt(252)`, since variance scales with time and std scales with its
square root). Lower vol at a similar return is strictly better — it's a less
stressful ride to the same destination.

## Sharpe ratio
Return per unit of risk taken: `mean daily return * 252 / ann_vol`. Two
strategies can have the same CAGR, but if one got there smoothly and the other
via a 60% crash and a miracle recovery, Sharpe is what tells them apart — CAGR
alone can't. >1.0 is solid; >2.0 on a simple SMA crossover is a red flag for a
bug, not something to celebrate.

## Max drawdown
The single worst peak-to-trough loss anywhere in the backtest. The most human
metric on the list — it answers "could I have actually stomached holding this
at the worst possible moment?" A strategy with lower CAGR but much smaller max
drawdown can be the better real choice, because the high-CAGR/high-drawdown
strategy is the one people panic-sell at the bottom of.

## Calmar ratio
`CAGR / abs(max_drawdown)`. Sharpe's cousin — instead of dividing by everyday
volatility, it divides by the single worst moment. Answers "how much pain at
the worst point did I endure per unit of annual return?" >0.5 is respectable.

## Exposure
Fraction of days actually holding a position vs. sitting in cash
(`(position != 0).mean()`). This is the explainer metric: buy-and-hold is
always 100% exposed, so if a strategy is only 60% exposed and underperforms,
part of that gap is mechanical — missing 40% of the days — not necessarily bad
signal quality.

## Win rate
% of closed trades (not days) that were profitable. Counterintuitive part:
trend-following systems often win under 50% of trades and are still
profitable overall — lots of small losing whipsaws, offset by a few large
trend-following winners. If my real results show this, it's not a sign the
strategy is broken, it's often exactly what trend-following looks like.

## The one thing that matters most
A strategy with a lower return but a much smaller max drawdown can beat
buy-and-hold in practice, even while losing on CAGR — because it's the
strategy you can actually hold through a crash without panic-selling. That's
the real argument for trend-following, and it's the argument the README
should make if the numbers support it.
