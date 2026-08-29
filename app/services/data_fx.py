from typing import Optional
import httpx
from app.database import get_db

FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v1"


async def fetch_usd_krw_rate(target_date: Optional[str] = None) -> Optional[float]:
    """
    Frankfurter API를 통해 USD/KRW 환율을 조회합니다.
    - target_date가 None이면 'latest'를 조회합니다.
    - target_date 형식: 'YYYY-MM-DD'
    """
    endpoint = f"{FRANKFURTER_BASE_URL}/{target_date}" if target_date else f"{FRANKFURTER_BASE_URL}/latest"
    params = {"base": "USD", "symbols": "KRW"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(endpoint, params=params)
            if response.status_code == 200:
                data = response.json()
                return float(data.get("rates", {}).get("KRW", 0.0))
    except Exception as e:
        print(f"Error fetching FX rate from Frankfurter: {e}")
    return None
