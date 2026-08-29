from datetime import datetime
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.services.id_generator import generate_trade_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/trades", response_class=HTMLResponse)
async def trades_page(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.trade_id, t.plan_id, t.asset_id, t.trade_datetime, t.position_side,
                   t.trade_action, t.trade_price, t.trade_qty, t.trade_amount, t.trade_fee,
                   t.trade_tp_price, t.trade_sl_price,
                   t.trade_status, t.trade_memo,
                   COALESCE(p.instrument_type, 'spot') as instrument_type
            FROM trades t
            LEFT JOIN plans p ON t.user_id = p.user_id AND t.plan_id = p.plan_id
            WHERE t.user_id = 'default_user'
            ORDER BY t.trade_datetime DESC, t.trade_id DESC
            """
        )
        trades = [dict(r) for r in cursor.fetchall()]

        # 등록된 asset 목록 (자동완성/선택용)
        cursor.execute("SELECT asset_id, asset_name FROM assets WHERE user_id = 'default_user' ORDER BY asset_id ASC")
        assets = [dict(r) for r in cursor.fetchall()]

        # 등록된 plans 목록 (asset_id별 plan_id 자동 연동 및 auto populate용)
        cursor.execute(
            """
            SELECT plan_id, asset_id, position_side, instrument_type, plan_entry_price, plan_tp_price, plan_sl_price, plan_qty, plan_memo
            FROM plans
            WHERE user_id = 'default_user'
            ORDER BY plan_date DESC, plan_id DESC
            """
        )
        plans = [dict(r) for r in cursor.fetchall()]

    return templates.TemplateResponse(
        request=request,
        name="trades.html",
        context={
            "page_title": "Trades",
            "active_menu": "trades",
            "trades": trades,
            "assets": assets,
            "plans": plans,
        },
    )


@router.post("/api/trades")
async def record_trade(
    asset_id: str = Form(...),
    position_side: str = Form(...),
    trade_action: str = Form(...),
    trade_price: float = Form(...),
    trade_qty: float = Form(...),
    trade_fee: float = Form(0.0),
    trade_tp_price: float = Form(None),
    trade_sl_price: float = Form(None),
    trade_datetime: str = Form(None),
    plan_id: str = Form(None),
    trade_memo: str = Form(None),
):
    asset_id = asset_id.strip().upper()
    if trade_datetime and trade_datetime.strip():
        # Handle formats like 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD HH:MM:SS'
        now_str = trade_datetime.strip().replace("T", " ")
        if len(now_str) == 16:  # 'YYYY-MM-DD HH:MM'
            now_str += ":00"
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trade_id = generate_trade_id(now_str, user_id="default_user")

    if trade_action in ("deposit", "withdraw"):
        trade_price = 1.0
        trade_tp_price = None
        trade_sl_price = None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO assets (asset_id, user_id, asset_class, asset_country, asset_name)
            VALUES (?, 'default_user', 'stock', 'US', ?)
            """,
            (asset_id, asset_id),
        )

        cursor.execute(
            """
            INSERT INTO trades (
                trade_id, user_id, plan_id, asset_id, trade_datetime, position_side,
                trade_action, trade_price, trade_qty, trade_fee, trade_tp_price, trade_sl_price, trade_status, trade_memo
            ) VALUES (?, 'default_user', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (
                trade_id,
                plan_id.strip() if plan_id else None,
                asset_id,
                now_str,
                position_side,
                trade_action,
                trade_price,
                trade_qty,
                trade_fee,
                trade_tp_price,
                trade_sl_price,
                trade_memo,
            ),
        )

    return RedirectResponse(url="/trades", status_code=303)


@router.post("/api/trades/update")
async def update_trade(
    trade_id: str = Form(...),
    trade_price: float = Form(...),
    trade_qty: float = Form(...),
    trade_fee: float = Form(0.0),
    trade_tp_price: float = Form(None),
    trade_sl_price: float = Form(None),
    trade_status: str = Form("active"),
    plan_id: str = Form(None),
    trade_memo: str = Form(None),
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE trades
            SET trade_price = ?,
                trade_qty = ?,
                trade_fee = ?,
                trade_tp_price = ?,
                trade_sl_price = ?,
                trade_status = ?,
                plan_id = ?,
                trade_memo = ?
            WHERE user_id = 'default_user' AND trade_id = ?
            """,
            (
                trade_price,
                trade_qty,
                trade_fee,
                trade_tp_price,
                trade_sl_price,
                trade_status,
                plan_id.strip() if plan_id else None,
                trade_memo,
                trade_id,
            ),
        )
    return RedirectResponse(url="/trades", status_code=303)


@router.delete("/api/trades/{trade_id}", response_class=HTMLResponse)
async def delete_trade(trade_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades WHERE user_id = 'default_user' AND trade_id = ?", (trade_id,))
    return Response(content="", status_code=200)
