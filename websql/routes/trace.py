#websql / routes / trace
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from websql.api import api_get, api_post
from websql.main import templates

router = APIRouter(prefix="/trace", tags=["Trace UI"])


@router.get("/{entity_id}", response_class=HTMLResponse)
def trace_view(entity_id: str, request: Request):
    # entity_id is external_id in the UI — backend trace endpoints expect UUID
    try:
        entity = api_get(f"/entities/external/{entity_id}")
    except Exception as e:
        return templates.TemplateResponse("trace.html", {"request": request, "entity_id": entity_id, "trace": None, "error": str(e)})
    entity_uuid = entity.get("id")
    trace = api_get(f"/trace/{entity_uuid}") if entity_uuid else None

    return templates.TemplateResponse(
        "trace.html",
        {
            "request": request,
            "entity_id": entity_id,
            "trace": trace,
            "error": None,
        },
    )


@router.get("/{entity_id}/link", response_class=HTMLResponse)
def link_entity_form(entity_id: str, request: Request):
    return templates.TemplateResponse(
        "trace_link.html",
        {
            "request": request,
            "entity_id": entity_id,
            "error": None,
        },
    )


@router.post("/{entity_id}/link", response_class=HTMLResponse)
def link_entity(
    entity_id: str,
    request: Request,
    target_id: str = Form(...),
    relation: str = Form(...),
):
    """
    Create a parent->child link between two external IDs. Resolve external IDs to UUIDs first,
    then POST to /links with parent_id and child_id.
    """
    try:
        parent = api_get(f"/entities/external/{entity_id}")
        child = api_get(f"/entities/external/{target_id}")
    except Exception as e:
        return templates.TemplateResponse(
            "trace_link.html",
            {"request": request, "entity_id": entity_id, "error": f"Failed to resolve entities: {e}"},
        )

    if not parent or not child:
        return templates.TemplateResponse(
            "trace_link.html",
            {"request": request, "entity_id": entity_id, "error": "Parent or child entity not found"},
        )

    payload = {
        "parent_id": parent["id"],
        "child_id": child["id"],
        "relation": relation,
    }

    try:
        api_post("/links", payload)
        return RedirectResponse(
            url=f"/trace/{entity_id}",
            status_code=303,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "trace_link.html",
            {
                "request": request,
                "entity_id": entity_id,
                "error": str(e),
            },
        )
