from typing import Dict, List, Any
from app.database import get_db


def calculate_positions_and_cash(user_id: str = "default_user") -> Dict[str, Any]:
    """
    trades 원장을 기반으로 다음 항목들을 산출합니다:
    1. 현금 잔고 (Cash Balance)
    2. 종목별 포지션: 잔여 수량, 가중평균단가(Avg Price), 실현 손익(Realized PnL), 누적 수수료
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT trade_id, user_id, plan_id, asset_id, trade_datetime, position_side,
                   trade_action, trade_price, trade_qty, trade_amount, trade_fee, trade_status
            FROM trades
            WHERE user_id = ? AND trade_status = 'active'
            ORDER BY trade_datetime ASC, trade_id ASC
            """,
            (user_id,),
        )
        trades = cursor.fetchall()

    cash_balance = 0.0
    total_deposit = 0.0
    total_withdraw = 0.0
    total_fees = 0.0
    positions: Dict[str, Dict[str, Any]] = {}

    for t in trades:
        action = t["trade_action"]
        asset_id = t["asset_id"]
        price = float(t["trade_price"])
        qty = float(t["trade_qty"])
        amount = float(t["trade_amount"])
        fee = float(t["trade_fee"])
        side = t["position_side"]

        total_fees += fee

        if action == "deposit":
            cash_balance += qty
            total_deposit += qty
            cash_balance -= fee
        elif action == "withdraw":
            cash_balance -= qty
            total_withdraw += qty
            cash_balance -= fee
        elif action in ("open", "add"):
            if asset_id not in positions:
                positions[asset_id] = {
                    "asset_id": asset_id,
                    "position_side": side,
                    "qty": 0.0,
                    "total_cost": 0.0,
                    "avg_price": 0.0,
                    "realized_pnl": 0.0,
                    "total_fees": 0.0,
                }
            pos = positions[asset_id]
            pos["total_fees"] += fee

            if side == "long":
                cash_balance -= (amount + fee)
                pos["qty"] += qty
                pos["total_cost"] += amount
                pos["avg_price"] = pos["total_cost"] / pos["qty"] if pos["qty"] > 0 else 0.0
            elif side == "short":
                cash_balance += (amount - fee)
                pos["qty"] += qty
                pos["total_cost"] += amount
                pos["avg_price"] = pos["total_cost"] / pos["qty"] if pos["qty"] > 0 else 0.0

        elif action in ("reduce", "close"):
            if asset_id in positions:
                pos = positions[asset_id]
                pos["total_fees"] += fee
                current_avg = pos["avg_price"]

                if side == "long":
                    realized = (price - current_avg) * qty - fee
                    pos["realized_pnl"] += realized
                    cash_balance += (amount - fee)
                    pos["qty"] -= qty
                    pos["total_cost"] -= (current_avg * qty)
                elif side == "short":
                    realized = (current_avg - price) * qty - fee
                    pos["realized_pnl"] += realized
                    cash_balance += (amount + fee)
                    pos["qty"] -= qty
                    pos["total_cost"] -= (current_avg * qty)

                if pos["qty"] <= 1e-9:
                    pos["qty"] = 0.0
                    pos["total_cost"] = 0.0
                    pos["avg_price"] = 0.0

    open_positions = [p for p in positions.values() if p["qty"] > 0]

    return {
        "cash_balance": cash_balance,
        "total_deposit": total_deposit,
        "total_withdraw": total_withdraw,
        "total_fees": total_fees,
        "open_positions": open_positions,
        "all_positions": positions,
    }
