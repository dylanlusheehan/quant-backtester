"""Daily paper-trading executor.

Computes today's target position from the same strategy code used in the
backtest, compares it to the actual position at Alpaca, and trades the
difference. Designed to be run once per day after the close.

Run: python -m live.paper_trade
"""
from __future__ import annotations

import csv
import os
from datetime import date, timedelta
from pathlib import Path

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from dotenv import load_dotenv

from src.config import SMA_PARAMS
from src.data import fetch_prices
from src.strategies import sma_crossover

TICKER = "SPY"
TARGET_ALLOCATION = 0.95        # fraction of equity to deploy when long
LOG_PATH = Path("live/trade_log.csv")
LOG_FIELDS = [
    "date", "price", "signal", "current_qty",
    "target_qty", "action", "portfolio_value",
]


def get_client() -> TradingClient:
    load_dotenv()
    return TradingClient(
        os.environ["ALPACA_API_KEY"],
        os.environ["ALPACA_SECRET_KEY"],
        paper=True,
    )


def todays_signal() -> tuple[float, float, date]:
    """Return (latest close, target position, latest bar date) from fresh data.

    Uses the exact same sma_crossover function and the exact same parameters
    (src/config.py) as the backtest. If the two ever diverge, the live results
    stop being comparable to the backtest and this whole step loses its point.
    """
    slow = SMA_PARAMS["slow"]
    start = (date.today() - timedelta(days=slow * 2 + 200)).isoformat()
    end = (date.today() + timedelta(days=1)).isoformat()

    prices = fetch_prices(
        TICKER, start=start, end=end, use_cache=False, write_cache=False
    )["Close"]
    signal = sma_crossover(prices, **SMA_PARAMS)

    return (
        float(prices.iloc[-1]),
        float(signal.iloc[-1]),
        prices.index[-1].date(),
    )


def current_quantity(client: TradingClient) -> float:
    for position in client.get_all_positions():
        if position.symbol == TICKER:
            return float(position.qty)
    return 0.0


def log_row(row: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    price, signal, bar_date = todays_signal()

    # ---- STALENESS GUARD ------------------------------------------------
    # Holidays exist, and yfinance sometimes posts the daily bar late. If the
    # newest bar is not today's, there is no new information: trade nothing,
    # log nothing, exit clean. Without this, a holiday run re-reads the
    # previous session's bar and can fire a duplicate order.
    if bar_date != date.today():
        print(f"Latest bar is {bar_date}, not {date.today()} — market closed or "
              f"data not posted yet. No action taken.")
        return
    # ---------------------------------------------------------------------

    client = get_client()
    account = client.get_account()
    portfolio_value = float(account.portfolio_value)
    current_qty = current_quantity(client)

    holding = current_qty > 0
    want_long = signal > 0

    print(f"{bar_date}  {TICKER} @ ${price:,.2f}")
    print(f"  signal={signal:.0f}  holding={holding}  qty={current_qty:g}")

    # ---- TRADE ONLY ON A STATE CHANGE -----------------------------------
    # The backtest is strictly binary: 1.0 or 0.0, with costs charged only when
    # the position CHANGES. It never rebalances.
    #
    # The tempting version of this -- recompute target_qty from portfolio_value
    # every day and trade the difference -- drifts: as SPY moves, the target
    # share count moves with it and you trickle out small buys and sells that
    # the backtest never makes. Your live trade count then exceeds the backtest
    # for reasons that have nothing to do with the signal, and the comparison
    # you came here to make is ruined. Size once on entry; hold until exit.
    action = "hold"
    target_qty = 0

    if want_long and not holding:
        target_qty = int(portfolio_value * TARGET_ALLOCATION // price)
        if target_qty >= 1:
            client.submit_order(MarketOrderRequest(
                symbol=TICKER, qty=target_qty,
                side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
            ))
            action = f"buy {target_qty}"
            print(f"  ENTRY — submitted BUY {target_qty}")
    elif holding and not want_long:
        client.submit_order(MarketOrderRequest(
            symbol=TICKER, qty=current_qty,
            side=OrderSide.SELL, time_in_force=TimeInForce.DAY,
        ))
        action = f"sell {current_qty:g}"
        print(f"  EXIT — submitted SELL {current_qty:g}")
    else:
        target_qty = current_qty
        print("  No state change. Holding." if holding else "  No state change. Flat.")
    # ---------------------------------------------------------------------

    log_row({
        "date": bar_date.isoformat(),
        "price": round(price, 2),
        "signal": signal,
        "current_qty": current_qty,
        "target_qty": target_qty,
        "action": action,
        "portfolio_value": round(portfolio_value, 2),
    })
    print(f"  Logged to {LOG_PATH}")


if __name__ == "__main__":
    main()
