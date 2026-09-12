"""Performance metrics for a strategy return series.

All metrics assume daily bars and a 0% risk-free rate. That assumption is
stated explicitly in the README rather than hidden — a nonzero risk-free rate
would lower every Sharpe ratio here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Percentage below the running peak, as a negative number (-0.20 = -20%)."""
    running_max = equity.cummax()
    return equity / running_max - 1.0


def compute_metrics(
    returns: pd.Series,
    position: pd.Series,
    trades: pd.DataFrame | None = None,
    periods_per_year: int = TRADING_DAYS,
) -> dict:
    """Summary statistics for one backtest. Returns a flat dict of floats."""
    returns = returns.dropna()

    if returns.empty:
        return {
            "total_return": 0.0, "cagr": 0.0, "ann_vol": 0.0, "sharpe": 0.0,
            "max_drawdown": 0.0, "calmar": np.nan, "exposure": 0.0,
            "n_trades": 0, "win_rate": np.nan,
        }

    equity = (1.0 + returns).cumprod()
    total_return = float(equity.iloc[-1] - 1.0)

    years = len(returns) / periods_per_year
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else 0.0

    ann_vol = float(returns.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe = float(returns.mean() * periods_per_year / ann_vol) if ann_vol > 0 else 0.0

    max_dd = float(drawdown_series(equity).min())
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else np.nan

    exposure = float((position != 0).mean())

    if trades is not None and len(trades) > 0:
        n_trades = int(len(trades))
        win_rate = float((trades["return_pct"] > 0).mean())
    else:
        n_trades = int((position.diff() > 0).sum())
        win_rate = np.nan

    return {
        "total_return": total_return,
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "exposure": exposure,
        "n_trades": n_trades,
        "win_rate": win_rate,
    }


def format_metrics(metrics: dict) -> str:
    """Human-readable block for printing to console."""
    return "\n".join([
        f"  Total return    {metrics['total_return']:>10.1%}",
        f"  CAGR            {metrics['cagr']:>10.2%}",
        f"  Ann. volatility {metrics['ann_vol']:>10.2%}",
        f"  Sharpe ratio    {metrics['sharpe']:>10.2f}",
        f"  Max drawdown    {metrics['max_drawdown']:>10.1%}",
        f"  Calmar ratio    {metrics['calmar']:>10.2f}",
        f"  Time in market  {metrics['exposure']:>10.1%}",
        f"  Trades          {metrics['n_trades']:>10d}",
        f"  Win rate        {metrics['win_rate']:>10.1%}"
        if not np.isnan(metrics["win_rate"]) else "  Win rate               n/a",
    ])
