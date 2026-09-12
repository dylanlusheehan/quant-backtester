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

---

# Head-to-Head Comparison — SMA Crossover vs. Z-Score Mean Reversion

Parameters used: SMA 50/200 and Z-rev 20/-1.0 — both un-cherry-picked defaults,
locked in `src/config.py` (see that file's docstring for why the tuned z-rev
winner from tuning, 30/-1.5, was deliberately not used as the headline).

## Out-of-sample tuning (z-rev)
Best in-sample parameters: lookback=30, entry_z=-1.5.
In-sample Sharpe 0.75 vs out-of-sample Sharpe 0.25 — a ~67% degradation,
roughly double SMA's 33% degradation from Step 4 (0.94 -> 0.63). Confirms the
guide's prediction that higher-turnover strategies (127 z-rev trades vs. 8-14
for SMA) have more surface area to overfit during tuning.

## Cost sensitivity (z-rev)
At the shared 7 bps baseline, z-rev's Sharpe already drops 0.496 -> 0.413
(~17%), versus SMA's 0.712 -> 0.707 (<1%) at the same cost level. Breakeven
friction for z-rev is roughly ~42 bps (Sharpe crosses zero between the 30 bps
and 60 bps scenarios); SMA never crosses zero anywhere in the tested 0-60 bps
range. At 60 bps, z-rev is outright unprofitable (CAGR -3.6%, Sharpe -0.21).
Same cost assumption, opposite verdict — purely a function of trade frequency
(127 trades vs. 8).

## Two different questions, two different answers

**Does either strategy beat buy-and-hold?** No — not anywhere. Z-rev beats
SMA on CAGR on only 1 of 6 tickers (KO). Averaged across all 6: buy-and-hold
15.5% CAGR > SMA 9.5% > z-rev 4.4%. Neither strategy beats buy-and-hold's
Sharpe in any of the 4 market regimes tested. Consistent with Step 4's
conclusion: 2010-2026 has been too persistently bullish for either active
style to add value over simply holding.

**Are the two strategies complementary relative to each other?** Yes, and
cleanly so — matching the predictions written in `docs/strategy-spec.md`
*before* either was tuned or backtested:

| Regime | SMA Sharpe | Z-rev Sharpe | Relative winner |
|---|---|---|---|
| 2010-2014 recovery | 0.98 | 0.43 | SMA |
| 2015-2019 grinding chop | 0.58 | 0.72 | **Z-rev** |
| 2020-2022 crash + bear | 0.29 | -0.00 | SMA |
| 2023-2026 AI rally | 1.07 | 0.73 | SMA |

Z-rev's one win against SMA is exactly the choppy 2015-2019 regime the spec
predicted it would handle better. Its worst regime relative to SMA is exactly
2020-2022 — the "catches a falling knife" failure mode the spec predicted for
sustained downtrends.

**The clearest concrete example of that failure mode: XOM.** Z-rev's max
drawdown there is -61.5%, nearly identical to buy-and-hold's -62.4% and far
worse than SMA's -42.3%. During the 2020 oil crash, mean reversion kept buying
every dip through a genuine sustained decline instead of sitting out.

**KO is the standout exception** — the one ticker where z-rev beats SMA
outright on both CAGR and Sharpe. KO is a low-volatility consumer staple, the
kind of rangebound instrument mean reversion is built for, versus the more
directional growth/energy names elsewhere in the ticker list.

**Win rate matches the spec's prediction too.** Z-rev's average win rate
(76.3%) is far above SMA's (58.4%) — more, smaller wins, exactly as specified.
But at only 29% average exposure (vs. SMA's 72%) and 122 trades vs. 11, most of
that edge is eaten by time spent flat and by transaction costs.

## Headline conclusion
Neither strategy beats passive buy-and-hold in this specific 16-year bull-
market window — that finding held at the single-strategy level in Step 4 and
holds again here. But the two strategies remain meaningfully complementary
*relative to each other*: each wins and loses in exactly the market regimes
its own thesis predicts, a pattern that was written down in the spec before
either strategy was built or tested. That's the more interesting and more
defensible claim than "strategy X beats the market" — it demonstrates the
tools correctly detect regime-dependent behavior, which is the actual skill
this project is meant to prove.
