"""Price data loading with local CSV caching.

All prices are split- and dividend-adjusted (yfinance auto_adjust=True), so the
'Close' column is already the adjusted close. There is no separate 'Adj Close'.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path("data/cache")

DEFAULT_TICKERS = ["AAPL", "MSFT", "JNJ", "XOM", "KO"]
BENCHMARK = "SPY"
START = "2010-01-01"
END = "2026-09-01"

# Everything before this date is for building and tuning.
# Everything after is the untouched out-of-sample holdout (used in Step 4).
SPLIT_DATE = "2020-01-01"


def _cache_path(ticker: str, start: str, end: str) -> Path:
    return CACHE_DIR / f"{ticker}_{start}_{end}.csv"


def fetch_prices(
    ticker: str,
    start: str = START,
    end: str = END,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download OHLCV bars for one ticker, caching to CSV on first call."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(ticker, start, end)

    if use_cache and path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)

    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError(f"No data returned for {ticker} between {start} and {end}")

    # yfinance returns MultiIndex columns when given a list; flatten defensively.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index.name = "Date"
    df.to_csv(path)
    return df


def close_series(ticker: str, **kwargs) -> pd.Series:
    """Adjusted close for one ticker, named after the ticker."""
    series = fetch_prices(ticker, **kwargs)["Close"]
    series.name = ticker
    return series


def price_panel(tickers: list[str] | None = None, **kwargs) -> pd.DataFrame:
    """Wide DataFrame: rows = dates, columns = tickers, values = adjusted close.

    Rows with any missing ticker are dropped so every column shares one calendar.
    """
    tickers = tickers or (DEFAULT_TICKERS + [BENCHMARK])
    columns = [close_series(t, **kwargs) for t in tickers]
    return pd.concat(columns, axis=1).dropna(how="any")
