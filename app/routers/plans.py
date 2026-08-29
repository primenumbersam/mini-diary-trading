from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.services.id_generator import generate_plan_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/plans", response_class=HTMLResponse)
async def plans_page(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        # plan_status 동적 산출:
        # 1. active: 해당 plan_id로 등록된 유효한 체결(trade_status = 'active')이 존재하는 경우
        # 2. pending: 아직 체결된 거래가 없는 대기 상태
        cursor.execute(
            """
            SELECT p.plan_id, p.user_id, p.asset_id, p.plan_date, p.position_side, p.instrument_type,
                   p.plan_entry_price, p.plan_tp_price, p.plan_sl_price, p.plan_qty,
                   p.plan_target_value, p.plan_rrr, p.plan_confidence, p.plan_memo, p.created_at,
                   CASE 
                       WHEN COUNT(t.trade_id) > 0 THEN 'active'
                       ELSE 'pending'
                   END as plan_status
            FROM plans p
            LEFT JOIN trades t ON p.user_id = t.user_id AND p.plan_id = t.plan_id AND t.trade_status = 'active'
            WHERE p.user_id = 'default_user' 
            GROUP BY p.plan_id, p.user_id, p.asset_id, p.plan_date, p.position_side, p.instrument_type,
                     p.plan_entry_price, p.plan_tp_price, p.plan_sl_price, p.plan_qty,
                     p.plan_target_value, p.plan_rrr, p.plan_confidence, p.plan_memo, p.created_at
            ORDER BY p.plan_date DESC, p.plan_id DESC
            """
        )
        plans = [dict(r) for r in cursor.fetchall()]

        # 등록된 asset 목록 (계획 등록 시 드롭다운/자동완성 지원용)
        cursor.execute("SELECT asset_id, asset_name FROM assets WHERE user_id = 'default_user' ORDER BY asset_id ASC")
        assets = [dict(r) for r in cursor.fetchall()]

    return templates.TemplateResponse(
        request=request,
        name="plans.html",
        context={
            "page_title": "Plans",
            "active_menu": "plans",
            "plans": plans,
            "assets": assets,
        },
    )


@router.post("/api/plans", response_class=HTMLResponse)
async def create_plan(
    request: Request,
    asset_id: str = Form(...),
    plan_date: str = Form(...),
    position_side: str = Form(...),
    instrument_type: str = Form("spot"),
    plan_entry_price: float = Form(...),
    plan_tp_price: float = Form(...),
    plan_sl_price: float = Form(...),
    plan_qty: float = Form(...),
    plan_confidence: str = Form(...),
    plan_memo: str = Form(None),
):
    asset_id = asset_id.strip().upper()
    plan_id = generate_plan_id(asset_id, plan_date, user_id="default_user")

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
            INSERT INTO plans (
                plan_id, user_id, asset_id, plan_date, position_side, instrument_type,
                plan_entry_price, plan_tp_price, plan_sl_price, plan_qty,
                plan_confidence, plan_memo
            ) VALUES (?, 'default_user', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                asset_id,
                plan_date,
                position_side,
                instrument_type,
                plan_entry_price,
                plan_tp_price,
                plan_sl_price,
                plan_qty,
                plan_confidence,
                plan_memo,
            ),
        )

    return RedirectResponse(url="/plans", status_code=303)


@router.post("/api/plans/update")
async def update_plan(
    plan_id: str = Form(...),
    instrument_type: str = Form("spot"),
    plan_entry_price: float = Form(...),
    plan_tp_price: float = Form(...),
    plan_sl_price: float = Form(...),
    plan_qty: float = Form(...),
    plan_confidence: str = Form(...),
    plan_memo: str = Form(None),
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE plans
            SET instrument_type = ?,
                plan_entry_price = ?,
                plan_tp_price = ?,
                plan_sl_price = ?,
                plan_qty = ?,
                plan_confidence = ?,
                plan_memo = ?
            WHERE user_id = 'default_user' AND plan_id = ?
            """,
            (
                instrument_type,
                plan_entry_price,
                plan_tp_price,
                plan_sl_price,
                plan_qty,
                plan_confidence,
                plan_memo,
                plan_id,
            ),
        )
    return RedirectResponse(url="/plans", status_code=303)


@router.delete("/api/plans/{plan_id}", response_class=HTMLResponse)
async def delete_plan(plan_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plans WHERE user_id = 'default_user' AND plan_id = ?", (plan_id,))
    return Response(content="", status_code=200)
