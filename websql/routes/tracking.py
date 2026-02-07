#websql / routes / tracking

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from websql.api import api_get, api_post
from websql.main import templates

router = APIRouter(prefix="/tracking", tags=["Tracking UI"])


@router.get("", response_class=HTMLResponse)
def tracking_home(request: Request, status: str = None):
    try:
        params = f"?status={status}" if status else ""
        packages = api_get(f"/tracking/packages{params}")
        stats = api_get("/tracking/stats")

        return templates.TemplateResponse(
            "tracking.html",
            {"request": request, "packages": packages, "stats": stats, "filter_status": status},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_class=HTMLResponse)
def search_package(request: Request, q: str = ""):
    if not q:
        return templates.TemplateResponse("tracking_search.html", {"request": request, "query": q, "package": None, "error": None})
    try:
        package = api_get(f"/tracking/track/{q}")
        return templates.TemplateResponse("tracking_search.html", {"request": request, "query": q, "package": package, "error": None})
    except Exception as e:
        return templates.TemplateResponse("tracking_search.html", {"request": request, "query": q, "package": None, "error": str(e)})


@router.get("/create", response_class=HTMLResponse)
def create_package_form(request: Request):
    return templates.TemplateResponse("tracking_create.html", {"request": request, "error": None})


@router.post("/create", response_class=HTMLResponse)
def create_package(
    request: Request,
    tracking_number: str = Form(...),
    sender: str = Form(...),
    recipient: str = Form(...),
    destination: str = Form(...),
    weight_kg: float = Form(None),
):
    try:
        # ✅ Match backend schema: external_id, type, extra_data
        api_post("/entities", {
            "external_id": tracking_number,
            "type": "package",
            "extra_data": {
                "label": f"Package {tracking_number}"
            }
        })

        api_post(f"/events/{tracking_number}", {
            "event_type": "created",
            "data": {
                "sender": sender,
                "recipient": recipient,
                "destination": destination,
                "weight_kg": weight_kg,
            }
        })

        return RedirectResponse(url=f"/tracking/{tracking_number}", status_code=303)

    except Exception as e:
        return templates.TemplateResponse("tracking_create.html", {"request": request, "error": str(e)})


@router.get("/{tracking_number}", response_class=HTMLResponse)
def track_package(tracking_number: str, request: Request):
    try:
        package = api_get(f"/tracking/track/{tracking_number}")
        return templates.TemplateResponse("tracking_detail.html", {"request": request, "package": package})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{tracking_number}/add-event", response_class=HTMLResponse)
def add_event_form(tracking_number: str, request: Request):
    return templates.TemplateResponse("tracking_add_event.html", {"request": request, "tracking_number": tracking_number, "error": None})


@router.post("/{tracking_number}/add-event", response_class=HTMLResponse)
def add_event(tracking_number: str, request: Request, status: str = Form(...), location: str = Form(None), actor: str = Form(None), notes: str = Form(None)):
    try:
        api_post(f"/events/{tracking_number}", {
            "event_type": status,
            "data": {
                "location": location,
                "actor": actor,
                "notes": notes,
            }
        })
        return RedirectResponse(url=f"/tracking/{tracking_number}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("tracking_add_event.html", {"request": request, "tracking_number": tracking_number, "error": str(e)})
