from typing import Dict, Any, List
from app.database import get_db


def get_confidence_analytics(user_id: str = "default_user") -> List[Dict[str, Any]]:
    """
    plan_confidence ('high', 'medium', 'low') 별로 통계를 집계합니다.
    """
    conf_stats = {
        "high": {"confidence": "High", "total_plans": set(), "rrr_list": [], "realized_pnl": 0.0, "wins": 0, "losses": 0},
        "medium": {"confidence": "Medium", "total_plans": set(), "rrr_list": [], "realized_pnl": 0.0, "wins": 0, "losses": 0},
        "low": {"confidence": "Low", "total_plans": set(), "rrr_list": [], "realized_pnl": 0.0, "wins": 0, "losses": 0},
    }

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT plan_id, plan_confidence, plan_rrr FROM plans WHERE user_id = ?", (user_id,))
        plan_rows = cursor.fetchall()
        for pr in plan_rows:
            conf = pr["plan_confidence"]
            if conf in conf_stats:
                conf_stats[conf]["total_plans"].add(pr["plan_id"])
                if pr["plan_rrr"] is not None:
                    conf_stats[conf]["rrr_list"].append(float(pr["plan_rrr"]))

    results = []
    for conf_key in ("high", "medium", "low"):
        data = conf_stats[conf_key]
        total_p = len(data["total_plans"])
        avg_rrr = sum(data["rrr_list"]) / len(data["rrr_list"]) if data["rrr_list"] else 0.0
        total_trades = data["wins"] + data["losses"]
        win_rate = (data["wins"] / total_trades * 100.0) if total_trades > 0 else 0.0

        results.append({
            "confidence": data["confidence"],
            "total_plans": total_p,
            "avg_rrr": round(avg_rrr, 2),
            "win_rate": round(win_rate, 1),
            "realized_pnl": round(data["realized_pnl"], 2),
        })

    return results
