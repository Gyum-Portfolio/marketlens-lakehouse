import json
import os
from pathlib import Path
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

def get_api_key() -> str:
    api_key = os.getenv("TIINGO_API_KEY")
    if api_key is None or not api_key.strip():
        raise ValueError("TIINGO_API_KEY is missing or blank")
    return api_key.strip()

def check_connection(api_key: str) -> None:
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    response = requests.get(
        "https://api.tiingo.com/api/test",
        headers=headers,
        timeout=30,
    )
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()
    print(response.json())

def preview_price_json(prices: list[dict]) -> None:
    if not prices:
        raise ValueError("No price data to preview.")

    for price in prices[:5]:
        print(json.dumps(price, indent=2))

def fetch_price(api_key:str, ticker:str, start_date:str, end_date:str) -> list[dict]:
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "format": "json",
        "resampleFreq": "daily"
    }
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    price = response.json()
    if not isinstance(price, list):
        raise ValueError(f"Unexpected response format: {price}")
    if not price:
        raise ValueError(f"No price data returned for ticker {ticker} between {start_date} and {end_date}")
    return price

def summarize_price(prices: list[dict]) -> None:
    if not prices:
        raise ValueError("No entries in price data to summarize.")

    sorted_prices = sorted(prices, key=lambda row: datetime.fromisoformat(row["date"]))
    first_row = sorted_prices[0]
    last_row = sorted_prices[-1]

    first_date = datetime.fromisoformat(first_row["date"]).date()
    last_date = datetime.fromisoformat(last_row["date"]).date()

    print(f"Rows received: {len(prices)}")
    print(f"First date: {first_date}")
    print(f"Last date: {last_date}")
    print(f"latest trading day: {last_row['date']}")
    print(f"Latest closing price: {last_row['close']}")
    print(f"Latest adjClose price: {last_row['adjClose']}")

def save_price_json(prices: list[dict], output_dir:Path, ticker:str, start_date:str, end_date:str, collected_at:datetime) -> Path:
    if not prices:
        raise ValueError("No price data to save.")  

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = collected_at.strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{ticker}_{timestamp}.json"

    payload = {
        "metadata": {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "collected_at": collected_at.isoformat()
        },
        "prices": prices,
    }

    with output_path.open("x", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return output_path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    api_key = get_api_key()
    print("API KEY loaded")
    
    ticker = "SPY"
    start_date = "2025-11-23"
    end_date = "2026-11-23"

    price = fetch_price(
        api_key=api_key,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )
    collected_at = datetime.now(timezone.utc)

    saved_path = save_price_json(
        prices=price,
        output_dir=project_root / "data" / "raw" / "tiingo",
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        collected_at=collected_at,
    )
    print(f"Saved raw data to: {saved_path}")

    summarize_price(price)