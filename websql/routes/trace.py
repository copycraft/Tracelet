# websql/routes/trace.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from websql.api import api_get
from websql.main import templates

router = APIRouter(prefix="/trace", tags=["Trace UI"])

@router.get("/{entity_id}", response_class=HTMLResponse)
def trace_view(entity_id: str, request: Request):
    try:
        trace = api_get(f"/trace/{entity_id}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return templates.TemplateResponse(
        "trace.html",
        {
            "request": request,
            "entity_id": entity_id,
            "trace": trace,
        },
    )
