from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/widget", response_class=HTMLResponse)
async def widget_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="widget.html",
        context={
            "page_title": "Widgets & Live Data",
            "active_menu": "widget",
        },
    )
