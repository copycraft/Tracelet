#websql / routes / entities
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from websql.api import api_get, api_post
from websql.main import templates

router = APIRouter(prefix="/entities")


@router.get("", response_class=HTMLResponse)
def list_entities(request: Request, type: str = None):
    params = f"?type={type}" if type else ""
    entities = api_get(f"/entities{params}")
    return templates.TemplateResponse("entities.html", {"request": request, "entities": entities, "filter_type": type})


@router.get("/create", response_class=HTMLResponse)
def create_entity_form(request: Request):
    return templates.TemplateResponse("entity_create.html", {"request": request, "error": None})


@router.post("/create", response_class=HTMLResponse)
def create_entity(request: Request, external_id: str = Form(...), type: str = Form(...), name: str = Form(None)):
    try:
        payload = {
            "external_id": external_id,  # match backend
            "type": type,
            "extra_data": {"label": name} if name else {}
        }
        api_post("/entities", payload)
        return RedirectResponse(url=f"/entities/{external_id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("entity_create.html", {"request": request, "error": str(e)})


@router.get("/{entity_id}", response_class=HTMLResponse)
def entity_detail(entity_id: str, request: Request):
    """
    entity_id here is the external_id shown in the UI. We first resolve it to the backend entity (UUID),
    then use that UUID when calling events/trace endpoints (they expect UUID).
    """
    try:
        entity = api_get(f"/entities/external/{entity_id}")
    except Exception as e:
        # entity not found or backend error
        return templates.TemplateResponse(
            "entity_detail.html",
            {"request": request, "entity": None, "events": [], "trace": None, "tree": None, "error": str(e)},
        )

    try:
        entity_uuid = entity.get("id")
        events = api_get(f"/events/entity/{entity_uuid}") if entity_uuid else []
    except Exception:
        events = []

    try:
        trace = api_get(f"/trace/{entity_uuid}") if entity_uuid else None
    except Exception:
        trace = None

    try:
        tree = api_get(f"/trace/{entity_uuid}/tree") if entity_uuid else None
    except Exception:
        tree = None

    return templates.TemplateResponse(
        "entity_detail.html",
        {"request": request, "entity": entity, "events": events, "trace": trace, "tree": tree, "error": None},
    )
