# Resume Bullets

Three variants, pick based on the role. All numbers pulled directly from
`results/summary.md`, `docs/findings.md`, and the tables in `results/tables/`
— nothing here is rounded up or softened.

## Variant A — quant/finance roles (lead with rigor)

> **Quantitative Strategy Backtester** — Python, pandas, NumPy
> Built a vectorized backtesting engine from scratch to evaluate trend-following
> and mean-reversion strategies across 5 equities and SPY over 16 years (~4,190
> daily bars each), modelling commission and slippage at 7 bps per position
> change (~14 bps round trip).
> Prevented lookahead bias through a centralized one-bar signal lag, enforced by
> automated tests; validated robustness with a 26-combination parameter sweep,
> a 0-60 bps cost-sensitivity analysis, and a strict 2010-2019 / 2020-2026
> out-of-sample split.
> Found trend-following cut maximum drawdown by up to 20 percentage points on
> individual tickers (e.g. XOM: -62% to -42%) while trailing buy-and-hold on
> CAGR across the full 6-ticker sample, and that mean-reversion's edge
> disappeared above ~42 bps of trading friction — documenting that roughly
> two-thirds of its in-sample Sharpe did not survive out-of-sample testing.

## Variant B — consulting roles (lead with the analysis and conclusion)

> **Independent Quantitative Research Project** — Python, pandas
> Designed and executed a comparative study of two trading strategies across
> four distinct market regimes (2010-2026), building the full analytical
> pipeline — data ingestion, backtesting engine, performance metrics, and
> reporting.
> Concluded that the two approaches were complementary rather than competing:
> each outperformed the other in exactly the market regime its own investment
> thesis predicted (trend-following in 3 of 4 regimes, mean reversion in the
> one choppy, directionless regime), even though neither beat a simple
> buy-and-hold benchmark; quantified the return/drawdown trade-off and the
> cost-sensitivity gap between the two to inform strategy selection.

## Variant C — one-liner for a skills/projects section

> **quant-backtester** (Python, pandas) — Vectorized backtesting engine testing
> 2 strategies × 6 tickers × 16 years with cost modelling, lookahead-bias
> tests, cost-sensitivity analysis, and out-of-sample validation.
> [github.com/dylanlusheehan/quant-backtester]
