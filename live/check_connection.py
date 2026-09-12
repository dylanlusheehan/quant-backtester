"""Verify Alpaca paper credentials. Run: python -m live.check_connection"""
import os

from alpaca.trading.client import TradingClient
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    client = TradingClient(
        os.environ["ALPACA_API_KEY"],
        os.environ["ALPACA_SECRET_KEY"],
        paper=True,
    )
    account = client.get_account()
    print(f"Account status : {account.status}")
    print(f"Account number : {account.account_number}")
    print(f"Cash           : ${float(account.cash):,.2f}")
    print(f"Portfolio value: ${float(account.portfolio_value):,.2f}")
    print(f"Open positions : {len(client.get_all_positions())}")


if __name__ == "__main__":
    main()
