# Figure Captions

One sentence per figure, for pasting directly under the images in the README.

## 00_data_check.png
Six tickers' normalized price histories (2010-2026), confirming no missing
values, no corrupted splits, and no data anomalies before any backtest ran.

## 02_equity_curves.png
Buy-and-hold outgrew both active strategies on SPY over the full 16-year
window — SMA 50/200 gave up return for shallower drawdowns, while
Z-rev 20/-1.0 spent most of its time flat and lagged both.

## 03_drawdown.png
SMA 50/200's drawdowns are consistently shallower than buy-and-hold's, except
in the 2020 COVID crash, where all three strategies bottomed at the same
-33.7% because the crash happened too fast for either active strategy to react.

## 04_param_heatmap.png
The SMA parameter surface is a smooth, stable plateau rather than an isolated
spike — 100% of the 26 valid fast/slow combinations beat Sharpe 0.5, meaning
50/200 wasn't cherry-picked to look good.

## 05_signal_overlay.png
The SMA 50/200 position band turns on and off exactly where the fast average
crosses the slow one, confirming the crossover logic fires where visually
expected across the full history.

## 06_ticker_comparison.png
Buy-and-hold beat both active strategies on CAGR across all 6 tickers with no
exceptions — the clearest single picture of this project's core finding. The
one notable detail underneath that: Z-rev edges out SMA specifically on KO, a
low-volatility staple where mean reversion's thesis fits best, even though
neither comes close to buy-and-hold there.
