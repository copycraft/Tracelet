# websql/routes/entities.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from websql.api import api_get
from websql.main import templates

router = APIRouter(prefix="/entities")


@router.get("", response_class=HTMLResponse)
def list_entities(request: Request, type: str = None):
    """List all entities, optionally filtered by type"""
    params = f"?type={type}" if type else ""
    entities = api_get(f"/entities{params}")

    return templates.TemplateResponse(
        "entities.html",
        {
            "request": request,
            "entities": entities,
            "filter_type": type,
        },
    )


@router.get("/{entity_id}", response_class=HTMLResponse)
def entity_detail(entity_id: str, request: Request):
    """Show entity details with events and trace"""
    entity = api_get(f"/entities/{entity_id}")

    # Get events for this entity
    events = api_get(f"/events/entity/{entity_id}")

    # Get trace (relationships)
    trace = api_get(f"/trace/{entity_id}")

    # Get tree view
    tree = api_get(f"/trace/{entity_id}/tree")

    return templates.TemplateResponse(
        "entity_detail.html",
        {
            "request": request,
            "entity": entity,
            "events": events,
            "trace": trace,
            "tree": tree,
        },
    )