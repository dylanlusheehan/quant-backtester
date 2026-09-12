# Validation Findings — SMA Crossover

Data: 5 large-cap equities + SPY, 2010-01-01 to 2026-09-01, daily adjusted close.
Costs: 5 bps commission + 2 bps slippage = 7 bps per position change
(~14 bps per round trip), charged only on days the position actually changes.

## 1. Across tickers
Strategy beat buy-and-hold on CAGR for 0 of 6 tickers.
Strategy reduced max drawdown for 2 of 6 tickers (MSFT, XOM), tied on 2
(KO, SPY), and was worse on 2 (AAPL, JNJ).
Takeaway: the "loses return, wins drawdown protection almost everywhere"
story that trend-following is supposed to tell did not clearly hold on this
data. The drawdown benefit is real but inconsistent — present on roughly a
third of tickers, absent or negative on the rest.

## 2. Across regimes
Best regime: 2010-2014 (post-GFC recovery) — strategy Sharpe 0.976 vs
buy-and-hold's 0.959, a marginal win. Caveat: this window starts at the very
beginning of the dataset, so it's structurally handicapped by an unavoidable
~200-day warmup with no prior history to inherit — treat this "win" cautiously.
Worst regime: 2015-2019 (grinding bull) — Sharpe 0.581 vs 0.883. Matches the
strategy spec's own prediction that choppy, directionless markets cause
repeated whipsaws.
Takeaway: the strategy only edged out buy-and-hold in one of four regimes
(and that one is compromised by warmup), and lost clearly in the other three
— including 2020-2022, the exact kind of "sit out the decline" regime
trend-following is supposed to be built for. In that window it produced the
identical -33.7% max drawdown as buy-and-hold, because the COVID crash and
recovery both happened inside about five weeks — too fast for a 200-day
moving average to react to.

## 3. Parameter sensitivity
26 valid combinations tested. Median Sharpe 0.71, best 0.89, worst 0.57.
100% of combinations produced Sharpe > 0.5.
Verdict: robust plateau. The best combo (fast=10, slow=100) is not
dramatically better than the median, and the reported default (50/200) sits
comfortably inside the same stable range rather than being cherry-picked.

## 4. Cost sensitivity
Sharpe at 0 bps 0.712, at 7 bps (baseline) 0.707, at 30 bps 0.692, at 60 bps
0.672. Trade count stays fixed at 8 across every scenario.
Breakeven friction level: not reached within the tested range (0-60 bps) —
the strategy is essentially insensitive to costs at this trade frequency.
Takeaway: with only ~8 trades over 16 years, transaction costs are a
non-factor for this strategy. This is expected to look very different for
the higher-turnover mean-reversion strategy in Step 5.

## 5. Out-of-sample (tuned <2020, tested >=2020)
Best in-sample parameters: fast=50, slow=150
In-sample Sharpe 0.94 vs out-of-sample Sharpe 0.63 (a 33% decline). Max
drawdown also worsened out-of-sample, from -17.3% to -33.7%.
Verdict: normal degradation, not overfitting. The edge weakened but did not
collapse to zero or negative, and the worse out-of-sample drawdown is
consistent with the same COVID-crash blind spot found elsewhere in this
analysis rather than evidence the parameters were curve-fit to in-sample noise.

## Honest overall conclusion
The parameter selection process itself held up well — the sweep shows a
genuine stable plateau, not a lucky spike, and costs don't meaningfully erode
the edge at this trade frequency. The weak point isn't overfitting; it's the
underlying edge. Across 6 tickers and 4 market regimes, SMA 50/200 essentially
never clearly and reliably beat buy-and-hold — not on CAGR anywhere, not on
drawdown in most places, not on Sharpe in 3 of 4 regimes. The most likely
explanation is regime-specific: 2010-2026 has been an unusually strong, long
secular bull market with no slow grinding bear market in it. The two real
drawdowns that did occur (COVID 2020, the 2022 selloff) were either too fast
or too shallow for a 200-day crossover to meaningfully react to. Trend-following
is built to protect against a slow bleed like 2000-2002 or 2007-2009, and this
dataset doesn't contain one — which is a specific, testable claim rather than
a vague excuse, and the right honest conclusion to report rather than forcing
the textbook narrative onto data that didn't produce it.
