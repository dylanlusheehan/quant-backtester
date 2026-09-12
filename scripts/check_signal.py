"""Visual sanity check for a strategy signal.

Run: python -m scripts.check_signal
Temporary — Step 6 replaces this with src/plots.py.
"""
import matplotlib.pyplot as plt

from src.data import close_series
from src.strategies import sma_crossover


def main(ticker: str = "AAPL", fast: int = 50, slow: int = 200) -> None:
    prices = close_series(ticker)
    signal = sma_crossover(prices, fast=fast, slow=slow)

    print(f"{ticker}: {len(prices)} bars")
    print(f"Days long: {int(signal.sum())} ({signal.mean():.1%} of the sample)")
    print(f"Number of entries: {int((signal.diff() > 0).sum())}")
    print(f"First long date: {signal[signal == 1].index.min().date()}")

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 7), sharex=True, height_ratios=[3, 1]
    )

    ax1.plot(prices.index, prices, label="Close", linewidth=1)
    ax1.plot(prices.index, prices.rolling(fast).mean(), label=f"SMA {fast}", linewidth=1)
    ax1.plot(prices.index, prices.rolling(slow).mean(), label=f"SMA {slow}", linewidth=1)
    ax1.set_title(f"{ticker} — SMA {fast}/{slow} crossover signal")
    ax1.set_ylabel("Price ($)")
    ax1.legend()

    ax2.fill_between(signal.index, 0, signal, step="post", alpha=0.4)
    ax2.set_ylabel("Position")
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_xlabel("Date")

    plt.tight_layout()
    plt.savefig("results/figures/01_signal_check.png", dpi=150)
    print("Saved results/figures/01_signal_check.png")


if __name__ == "__main__":
    main()
