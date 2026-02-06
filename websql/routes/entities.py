from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from websql.api import api_get
from websql.main import templates

router = APIRouter(prefix="/entities")

@router.get("", response_class=HTMLResponse)
def list_entities(request: Request):
    entities = api_get("/entities")
    return templates.TemplateResponse(
        "entities.html",
        {"request": request, "entities": entities},
    )

@router.get("/{entity_id}", response_class=HTMLResponse)
def entity_detail(entity_id: str, request: Request):
    entity = api_get(f"/entities/{entity_id}")
    trace = api_get(f"/trace/{entity_id}")

    return templates.TemplateResponse(
        "entity_detail.html",
        {
            "request": request,
            "entity": entity,
            "trace": trace,
        },
    )
