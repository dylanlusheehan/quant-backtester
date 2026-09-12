"""Headline parameter choices — the single source of truth.

Every script imports STRATEGIES from here. Nothing hardcodes parameters.
If you change a number in this file, every table, figure, and README claim
changes with it, consistently.

WHY THESE VALUES:
Both strategies use their UN-CHERRY-PICKED DEFAULTS, not their sweep-identified
best-Sharpe combos. This is deliberate, not an oversight:

- SMA 50/200: the Step 4 parameter sweep showed a robust plateau (26 valid
  combos, 100% beat Sharpe 0.5, best 0.89 vs median 0.71) — 50/200 sits
  comfortably inside that plateau without being the peak, so reporting it
  isn't curve-fitting.
- Z-rev 20/-1.0: the Step 5 in-sample sweep's actual best combo (lookback=30,
  entry_z=-1.5, IS Sharpe 0.75) degraded hard out-of-sample (OOS Sharpe 0.25,
  a ~67% drop — roughly double SMA's 33% degradation). Reporting that tuned
  combo as the headline would bake a demonstrably fragile parameter choice
  into the project's main numbers. The default keeps the overfitting finding
  as a clean, honest diagnostic instead.

Deliberately not reporting the best in-sample number is the most sophisticated
decision in this project — say so explicitly in the README.
"""
from src.strategies import buy_and_hold, sma_crossover, zscore_reversion

SMA_PARAMS = {"fast": 50, "slow": 200}
ZREV_PARAMS = {"lookback": 20, "entry_z": -1.0}

SMA_LABEL = f"SMA {SMA_PARAMS['fast']}/{SMA_PARAMS['slow']}"
ZREV_LABEL = f"Z-rev {ZREV_PARAMS['lookback']}/{ZREV_PARAMS['entry_z']}"

STRATEGIES = {
    SMA_LABEL: (sma_crossover, SMA_PARAMS),
    ZREV_LABEL: (zscore_reversion, ZREV_PARAMS),
    "Buy & hold": (buy_and_hold, {}),
}

REPORT_COLUMNS = [
    "cagr", "ann_vol", "sharpe", "max_drawdown", "exposure", "n_trades", "win_rate",
]
