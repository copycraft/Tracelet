#websql / routes / dashboard

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from websql.api import api_get

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    from websql.main import templates

    health = api_get("/health")
    version = api_get("/version")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "health": health,
            "version": version,
            "create_entity_url": "/entities/create",
            "create_package_url": "/tracking/create",
        },
    )
