"""One-off data sanity check. Run: python -m scripts.inspect_data"""
import matplotlib.pyplot as plt

from src.data import price_panel


def main() -> None:
    panel = price_panel()

    print("Shape:", panel.shape)
    print("Date range:", panel.index.min().date(), "->", panel.index.max().date())
    print("\nMissing values per column:")
    print(panel.isna().sum())
    print("\nAny non-positive prices?")
    print((panel <= 0).sum())

    returns = panel.pct_change().dropna()
    print("\nLargest single-day move per ticker (%):")
    print((returns.abs().max() * 100).round(1))

    # Normalize each series to 100 at the start so they're visually comparable.
    (panel / panel.iloc[0] * 100).plot(figsize=(12, 6))
    plt.title("Normalized price history (start = 100)")
    plt.ylabel("Index level")
    plt.tight_layout()
    plt.savefig("results/figures/00_data_check.png", dpi=150)
    print("\nSaved results/figures/00_data_check.png")


if __name__ == "__main__":
    main()
