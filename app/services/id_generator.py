from datetime import datetime
from app.database import get_db


def generate_plan_id(asset_id: str, plan_date_str: str, user_id: str = "default_user") -> str:
    """
    Plan ID를 자동으로 생성합니다.
    포맷: {ASSET}_{YYYYMMDD}_{SEQ:02d} (e.g., NVDA_20260828_01)
    """
    clean_asset = asset_id.strip().upper()
    date_clean = plan_date_str.replace("-", "")
    prefix = f"{clean_asset}_{date_clean}_"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT plan_id FROM plans
            WHERE user_id = ? AND plan_id LIKE ?
            ORDER BY plan_id DESC
            """,
            (user_id, f"{prefix}%"),
        )
        existing_rows = cursor.fetchall()
        
        max_seq = 0
        for row in existing_rows:
            p_id = row["plan_id"]
            suffix = p_id[len(prefix):]
            if suffix.isdigit():
                max_seq = max(max_seq, int(suffix))

        new_seq = max_seq + 1
        return f"{prefix}{new_seq:02d}"


def generate_trade_id(trade_datetime_str: str, user_id: str = "default_user") -> str:
    """
    Trade ID를 자동으로 생성합니다.
    포맷: TR_{YYYYMMDD}_{SEQ:03d} (e.g., TR_20260828_001)
    """
    date_clean = trade_datetime_str[:10].replace("-", "")
    prefix = f"TR_{date_clean}_"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT trade_id FROM trades
            WHERE user_id = ? AND trade_id LIKE ?
            ORDER BY trade_id DESC
            """,
            (user_id, f"{prefix}%"),
        )
        existing_rows = cursor.fetchall()

        max_seq = 0
        for row in existing_rows:
            t_id = row["trade_id"]
            suffix = t_id[len(prefix):]
            if suffix.isdigit():
                max_seq = max(max_seq, int(suffix))

        new_seq = max_seq + 1
        return f"{prefix}{new_seq:03d}"
