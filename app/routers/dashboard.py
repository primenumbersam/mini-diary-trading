from datetime import date
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.engine_position import calculate_positions_and_cash
from app.services.data_market import update_market_prices
from app.services.data_fx import fetch_usd_krw_rate
from app.services.engine_benchmark import get_daily_nav_history, calculate_and_save_daily_nav, fetch_benchmark_normalized_history

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    pos_data = calculate_positions_and_cash(user_id="default_user")
    open_positions = pos_data["open_positions"]
    cash_balance = pos_data["cash_balance"]

    asset_ids = [p["asset_id"] for p in open_positions]
    current_prices = update_market_prices(asset_ids)

    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    for p in open_positions:
        cur_p = current_prices.get(p["asset_id"], p["avg_price"])
        p["current_price"] = cur_p
        m_val = cur_p * p["qty"]
        p["market_value"] = m_val
        total_market_value += m_val

        unrealized = (cur_p - p["avg_price"]) * p["qty"] if p["position_side"] == "long" else (p["avg_price"] - cur_p) * p["qty"]
        p["unrealized_pnl"] = unrealized
        p["unrealized_pnl_pct"] = (unrealized / (p["avg_price"] * p["qty"]) * 100.0) if (p["avg_price"] * p["qty"]) > 0 else 0.0
        total_unrealized_pnl += unrealized

    total_nav = cash_balance + total_market_value
    cash_ratio = (cash_balance / total_nav * 100.0) if total_nav > 0 else 100.0

    fx_rate = await fetch_usd_krw_rate()
    if not fx_rate:
        fx_rate = 1350.0
    total_nav_krw = total_nav * fx_rate

    today = date.today()
    snapshot = calculate_and_save_daily_nav(
        nav_date=today,
        cash_balance=cash_balance,
        market_value=total_market_value,
        external_flow=0.0,
        usd_krw_rate=fx_rate,
        user_id="default_user",
    )
    twr_index = snapshot["cumulative_twr_index"]
    cumulative_twr = twr_index - 100.0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": "Dashboard",
            "active_menu": "dashboard",
            "total_nav": total_nav,
            "total_nav_krw": total_nav_krw,
            "fx_rate": fx_rate,
            "cash_balance": cash_balance,
            "cash_ratio": cash_ratio,
            "total_market_value": total_market_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "cumulative_twr": cumulative_twr,
            "twr_index": twr_index,
            "positions": open_positions,
        },
    )


@router.get("/api/benchmark/chart", response_class=JSONResponse)
async def get_benchmark_chart_data(ticker: str = Query("SPY")):
    nav_history = get_daily_nav_history(user_id="default_user")
    if not nav_history:
        return JSONResponse({"labels": [], "portfolio_data": [], "benchmark_data": []})

    start_date = nav_history[0]["nav_date"]
    bench_data = fetch_benchmark_normalized_history(ticker, start_date)

    labels = [r["nav_date"] for r in nav_history]
    portfolio_data = [round(r["cumulative_twr_index"], 2) for r in nav_history]

    bench_dict = dict(zip(bench_data["dates"], bench_data["indices"]))
    benchmark_series = [bench_dict.get(d, 100.0) for d in labels]

    return JSONResponse(
        {
            "labels": labels,
            "portfolio_data": portfolio_data,
            "benchmark_data": benchmark_series,
        }
    )
