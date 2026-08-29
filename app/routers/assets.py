from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.services.data_market import update_market_prices

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        # asset_status 동적 산출:
        # 1. active: 현재 순보유수량(open/add - reduce/close) > 0
        # 2. inactive: 과거 active trade 이력이 있으나 현재 순보유수량 <= 0
        # 3. pending: active trade 이력이 한 번도 없는 관심종목
        cursor.execute(
            """
            SELECT 
                a.asset_id, a.asset_name, a.asset_class, a.asset_country, a.asset_description,
                m.current_price,
                COALESCE(SUM(
                    CASE 
                        WHEN t.trade_action IN ('open', 'add') THEN t.trade_qty
                        WHEN t.trade_action IN ('reduce', 'close') THEN -t.trade_qty
                        WHEN t.trade_action = 'deposit' THEN t.trade_qty
                        WHEN t.trade_action = 'withdraw' THEN -t.trade_qty
                        ELSE 0
                    END
                ), 0) as holding_qty,
                COUNT(t.trade_id) as trade_count,
                CASE 
                    WHEN COALESCE(SUM(
                        CASE 
                            WHEN t.trade_action IN ('open', 'add') THEN t.trade_qty
                            WHEN t.trade_action IN ('reduce', 'close') THEN -t.trade_qty
                            WHEN t.trade_action = 'deposit' THEN t.trade_qty
                            WHEN t.trade_action = 'withdraw' THEN -t.trade_qty
                            ELSE 0
                        END
                    ), 0) > 0 THEN 'active'
                    WHEN COUNT(t.trade_id) > 0 THEN 'inactive'
                    ELSE 'pending'
                END as asset_status
            FROM assets a
            LEFT JOIN external_data m ON a.asset_id = m.asset_id
            LEFT JOIN trades t ON a.user_id = t.user_id AND a.asset_id = t.asset_id AND t.trade_status = 'active'
            WHERE a.user_id = 'default_user'
            GROUP BY a.asset_id, a.asset_name, a.asset_class, a.asset_country, a.asset_description, m.current_price
            ORDER BY a.asset_class DESC, a.asset_id ASC
            """
        )
        assets = [dict(r) for r in cursor.fetchall()]

    return templates.TemplateResponse(
        request=request,
        name="assets.html",
        context={
            "page_title": "Assets",
            "active_menu": "assets",
            "assets": assets,
        },
    )


@router.post("/api/assets")
async def create_asset(
    asset_id: str = Form(...),
    asset_name: str = Form(...),
    asset_class: str = Form("cash"),
    asset_country: str = Form("US"),
    asset_description: str = Form(None),
):
    asset_id = asset_id.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assets (asset_id, user_id, asset_class, asset_country, asset_name, asset_description)
            VALUES (?, 'default_user', ?, ?, ?, ?)
            ON CONFLICT(user_id, asset_id) DO UPDATE SET
                asset_name = excluded.asset_name,
                asset_class = excluded.asset_class,
                asset_country = excluded.asset_country,
                asset_description = excluded.asset_description
            """,
            (asset_id, asset_class, asset_country, asset_name, asset_description),
        )
    
    if asset_class == "stock":
        update_market_prices([asset_id])

    return RedirectResponse(url="/assets", status_code=303)


@router.post("/api/assets/update")
async def update_asset(
    asset_id: str = Form(...),
    asset_name: str = Form(...),
    asset_class: str = Form(...),
    asset_country: str = Form(...),
    asset_description: str = Form(None),
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE assets
            SET asset_name = ?,
                asset_class = ?,
                asset_country = ?,
                asset_description = ?
            WHERE user_id = 'default_user' AND asset_id = ?
            """,
            (
                asset_name,
                asset_class,
                asset_country,
                asset_description,
                asset_id,
            ),
        )
    return RedirectResponse(url="/assets", status_code=303)


@router.delete("/api/assets/{asset_id}", response_class=HTMLResponse)
async def delete_asset(asset_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assets WHERE user_id = 'default_user' AND asset_id = ?", (asset_id,))
    return Response(content="", status_code=200)
