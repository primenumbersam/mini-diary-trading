from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.engine_analytics import get_confidence_analytics
from app.services.engine_position import calculate_positions_and_cash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/reviews", response_class=HTMLResponse)
async def reviews_page(request: Request):
    analytics = get_confidence_analytics(user_id="default_user")
    pos_data = calculate_positions_and_cash(user_id="default_user")
    all_positions = pos_data.get("all_positions", {})

    return templates.TemplateResponse(
        request=request,
        name="reviews.html",
        context={
            "page_title": "Reviews",
            "active_menu": "reviews",
            "analytics": analytics,
            "all_positions": all_positions,
        },
    )
