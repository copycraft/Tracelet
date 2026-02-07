#websql / routes / trace
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from websql.api import api_get, api_post
from websql.main import templates

router = APIRouter(prefix="/trace", tags=["Trace UI"])


@router.get("/{entity_id}", response_class=HTMLResponse)
def trace_view(entity_id: str, request: Request):
    trace = api_get(f"/trace/{entity_id}")

    return templates.TemplateResponse(
        "trace.html",
        {
            "request": request,
            "entity_id": entity_id,
            "trace": trace,
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
    try:
        payload = {
            "source": entity_id,
            "target": target_id,
            "relation": relation,
        }

        api_post("/trace", payload)

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
