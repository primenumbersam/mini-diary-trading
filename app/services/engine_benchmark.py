from datetime import date
from typing import Dict, List, Any
import yfinance as yf
from app.database import get_db
from app.config import BENCHMARK_PRESETS


def get_daily_nav_history(user_id: str = "default_user") -> List[Dict[str, Any]]:
    """internal_pfo 테이블에서 일별 NAV 및 TWR 히스토리를 반환합니다."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT nav_date, cash_balance, market_value, total_nav,
                   external_flow, daily_twr, cumulative_twr_index, usd_krw_rate, total_nav_krw
            FROM internal_pfo
            WHERE user_id = ?
            ORDER BY nav_date ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def calculate_and_save_daily_nav(
    nav_date: date,
    cash_balance: float,
    market_value: float,
    external_flow: float = 0.0,
    usd_krw_rate: float = 1350.0,
    user_id: str = "default_user",
) -> Dict[str, Any]:
    """
    일별 NAV 스냅샷을 계산하고 저장합니다:
    R_t = (NAV_t - Flow_t) / NAV_{t-1} - 1
    I_t = I_{t-1} * (1 + R_t)
    """
    total_nav = cash_balance + market_value

    with get_db() as conn:
        cursor = conn.cursor()
        # 이전 날짜의 최신 NAV 스냅샷 조회
        cursor.execute(
            """
            SELECT total_nav, cumulative_twr_index
            FROM internal_pfo
            WHERE user_id = ? AND nav_date < ?
            ORDER BY nav_date DESC
            LIMIT 1
            """,
            (user_id, str(nav_date)),
        )
        prev_row = cursor.fetchone()

        if prev_row and prev_row["total_nav"] > 0:
            prev_nav = float(prev_row["total_nav"])
            prev_index = float(prev_row["cumulative_twr_index"]) if prev_row["cumulative_twr_index"] else 100.0
            daily_twr = (total_nav - external_flow) / prev_nav - 1.0
            cumulative_twr_index = prev_index * (1.0 + daily_twr)
        else:
            daily_twr = 0.0
            cumulative_twr_index = 100.0

        cursor.execute(
            """
            INSERT INTO internal_pfo (user_id, nav_date, cash_balance, market_value, total_nav, external_flow, daily_twr, cumulative_twr_index, usd_krw_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, nav_date) DO UPDATE SET
                cash_balance = excluded.cash_balance,
                market_value = excluded.market_value,
                total_nav = excluded.total_nav,
                external_flow = excluded.external_flow,
                daily_twr = excluded.daily_twr,
                cumulative_twr_index = excluded.cumulative_twr_index,
                usd_krw_rate = excluded.usd_krw_rate
            """,
            (user_id, str(nav_date), cash_balance, market_value, total_nav, external_flow, daily_twr, cumulative_twr_index, usd_krw_rate),
        )

    return {
        "nav_date": str(nav_date),
        "cash_balance": cash_balance,
        "market_value": market_value,
        "total_nav": total_nav,
        "daily_twr": daily_twr,
        "cumulative_twr_index": cumulative_twr_index,
        "usd_krw_rate": usd_krw_rate,
        "total_nav_krw": total_nav * usd_krw_rate,
    }


def fetch_benchmark_normalized_history(ticker: str, start_date: str) -> Dict[str, Any]:
    """
    선택된 벤치마크(SPY, DIA, QQQ)의 모의 정규화 지수 데이터를 반환합니다 (외부 네트워크 fetch 불필요).
    """
    if ticker not in BENCHMARK_PRESETS:
        ticker = "SPY"

    # Mock relative returns per day for each benchmark
    benchmark_profiles = {
        "SPY": [100.0, 100.35, 100.70, 100.45, 101.10, 101.60, 101.40, 102.05, 102.30, 102.85, 103.20, 103.05, 103.60, 104.10],
        "QQQ": [100.0, 100.60, 101.25, 100.80, 101.90, 102.80, 102.30, 103.40, 103.95, 104.80, 105.40, 105.10, 106.00, 106.85],
        "DIA": [100.0, 100.15, 100.40, 100.25, 100.60, 100.90, 100.85, 101.20, 101.45, 101.80, 102.00, 101.90, 102.25, 102.60],
    }

    # Retrieve active dates from internal_pfo
    nav_history = get_daily_nav_history()
    if nav_history:
        dates = [r["nav_date"] for r in nav_history if r["nav_date"] >= start_date]
    else:
        dates = ["2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24", "2026-07-25",
                 "2026-07-26", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31"]

    base_profile = benchmark_profiles.get(ticker, benchmark_profiles["SPY"])
    # Match length of dates
    indices = []
    for i in range(len(dates)):
        if i < len(base_profile):
            indices.append(base_profile[i])
        else:
            prev = indices[-1] if indices else 100.0
            indices.append(round(prev * 1.002, 2))

    return {"dates": dates, "indices": indices, "ticker": ticker}
