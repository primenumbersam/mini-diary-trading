from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/glossary", response_class=HTMLResponse)
async def glossary_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="glossary.html",
        context={
            "page_title": "Glossary",
            "active_menu": "glossary",
        },
    )
