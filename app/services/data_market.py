from typing import Dict, List, Optional
import yfinance as yf
from app.database import get_db


def get_cached_prices() -> Dict[str, float]:
    """DB에 저장된 캐시된 현재가를 반환합니다."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT asset_id, current_price FROM external_data")
        rows = cursor.fetchall()
        return {r["asset_id"]: float(r["current_price"]) for r in rows}


def update_market_prices(asset_ids: List[str]) -> Dict[str, float]:
    """yfinance를 통해 asset_ids의 최신 가격을 조회하고 DB 캐시를 갱신합니다."""
    prices: Dict[str, float] = {}
    valid_tickers = [a for a in asset_ids if not a.endswith("_CASH")]

    if not valid_tickers:
        return prices

    try:
        tickers = yf.Tickers(" ".join(valid_tickers))
        for symbol in valid_tickers:
            ticker_obj = tickers.tickers.get(symbol)
            if ticker_obj:
                fast_info = getattr(ticker_obj, "fast_info", None)
                last_price = getattr(fast_info, "last_price", None)
                if last_price is None:
                    # fallback to regular history
                    hist = ticker_obj.history(period="1d")
                    if not hist.empty:
                        last_price = float(hist["Close"].iloc[-1])
                
                if last_price is not None:
                    prices[symbol] = float(last_price)
    except Exception as e:
        print(f"Error fetching market prices: {e}")

    # Fallback/Save to DB
    if prices:
        with get_db() as conn:
            cursor = conn.cursor()
            for asset_id, price in prices.items():
                cursor.execute(
                    """
                    INSERT INTO external_data (asset_id, current_price, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(asset_id) DO UPDATE SET
                        current_price = excluded.current_price,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (asset_id, price),
                )

    # Return merged with cache for missing ones
    cached = get_cached_prices()
    cached.update(prices)
    return cached
