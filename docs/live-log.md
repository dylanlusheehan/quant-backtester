# Live Paper Trading Log

Weekly check-in, ~20 min. Started 2026-09-12 (task scheduled; first real
trading-day run expected Monday 2026-09-14).

Strategy: SMA 50/200 on SPY. Same parameters as the backtest (`src/config.py`).
Live fills happen at the next day's open; the backtest assumes fills at the
signal day's close — a known, documented gap between the two.

## Template for each entry

```markdown
## Week of YYYY-MM-DD
- Portfolio value: $______ (started $100,000)
- Position: [long / flat]
- Trades this week: __
- Signal matched backtest expectation: [yes / no]
- Anything broken: ___
```

## What to watch for

| Observation | What it means |
|---|---|
| Live signal differs from backtest signal on the same date | Data revision or a bug — investigate immediately |
| Task didn't run | Machine was asleep. Task Scheduler can't wake a sleeping laptop by default |
| Many more trades than the backtest predicted | Drift-rebalancing crept back in — check the script only trades on 0↔1 state changes, never on share-count drift |
| Flat for weeks with no trades | Normal for SMA 50/200. Trend systems are boring by design |

---

## Week of 2026-09-12 (setup)
- Portfolio value: $100,000.00 (starting)
- Position: flat (0 open positions)
- Trades this week: 0
- Signal matched backtest expectation: n/a — no trading day has occurred yet
- Anything broken: no. Manual connection check and one manual + one scheduled
  dry run both succeeded; both correctly took no action since it's a weekend
  and the staleness guard blocked any stale-bar trading.
